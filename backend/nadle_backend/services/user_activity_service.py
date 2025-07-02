"""User activity service for aggregating user's activity data."""

import logging
from typing import Dict, List, Any, Optional
from nadle_backend.models.core import Post, Comment, UserReaction
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)


def normalize_post_type(post_type: Optional[str]) -> Optional[str]:
    """Normalize post type to match expected page types.
    
    Maps database stored types to frontend page types:
    - expert_tips -> tips
    - property_information -> info  
    - board -> board
    - services -> services
    - Unknown types -> None (with logging)
    
    Args:
        post_type: The post type from database
        
    Returns:
        Normalized page type or None for unknown types
    """
    if not post_type:
        return None
        
    # Type mapping from DB to frontend
    type_mapping = {
        "expert_tips": "tips",
        "property_information": "info", 
        "board": "board",
        "services": "services",
        "moving services": "services"  # 입주 업체 서비스
    }
    
    normalized = type_mapping.get(post_type)
    
    if normalized is None:
        logger.warning(f"Unrecognized post type: '{post_type}'. This type will be ignored.")
        
    return normalized


class UserActivityService:
    """Service for aggregating user activity data."""
    
    def __init__(
        self, 
        post_repository: PostRepository,
        comment_repository: CommentRepository,
        user_reaction_repository: UserReactionRepository
    ):
        """Initialize user activity service with repositories.
        
        Args:
            post_repository: Post repository instance
            comment_repository: Comment repository instance
            user_reaction_repository: User reaction repository instance
        """
        self.post_repository = post_repository
        self.comment_repository = comment_repository
        self.user_reaction_repository = user_reaction_repository
    
    def normalize_post_type(self, post_type: Optional[str]) -> Optional[str]:
        """Normalize post type to match expected page types."""
        return normalize_post_type(post_type)
    
    async def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user activity summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing user's activity data grouped by type
        """
        # Get all user activity data in parallel
        posts_by_type = await self._get_user_posts_by_page_type(user_id)
        comments_with_subtype = await self._get_user_comments_with_subtype(user_id)
        reactions_grouped = await self._get_user_reactions_grouped(user_id)
        
        # Calculate summary statistics
        total_posts = sum(len(posts) for posts in posts_by_type.values())
        total_comments = len(comments_with_subtype)
        total_reactions = sum(len(reactions) for reactions in reactions_grouped.values())
        
        # Find most active page type
        most_active_page_type = None
        if posts_by_type:
            most_active_page_type = max(
                posts_by_type.keys(), 
                key=lambda k: len(posts_by_type[k])
            ) if any(posts_by_type.values()) else None
        
        return {
            "posts": posts_by_type,
            "comments": comments_with_subtype,
            "reactions": reactions_grouped,
            "summary": {
                "total_posts": total_posts,
                "total_comments": total_comments,
                "total_reactions": total_reactions,
                "most_active_page_type": most_active_page_type
            }
        }
    
    async def _get_user_posts_by_page_type(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get user posts grouped by page type.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with page types as keys and post lists as values
        """
        # Get all user posts
        posts = await self.post_repository.find_by_author(user_id)
        
        # Initialize result with all page types
        result = {
            "board": [],
            "info": [],
            "services": [],
            "tips": []
        }
        
        # Group posts by page type
        for post in posts:
            # Get the original type from metadata
            original_type = getattr(post.metadata, "type", None) if post.metadata else None
            
            # Normalize the post type
            normalized_type = self.normalize_post_type(original_type)
            
            # Skip posts with unrecognized types (they are already logged)
            if normalized_type is None:
                continue
                
            # Generate route path using original type for routing
            route_path = self._generate_route_path(original_type or "board", post.slug)
            
            # Calculate real-time stats (same as PostsService)
            real_stats = await self._calculate_post_stats(str(post.id))
            
            post_data = {
                "id": str(post.id),
                "title": post.title,
                "slug": post.slug,
                "created_at": post.created_at.isoformat(),
                "view_count": real_stats["view_count"],
                "like_count": real_stats["like_count"],
                "dislike_count": real_stats["dislike_count"],
                "comment_count": real_stats["comment_count"],
                "route_path": route_path
            }
            
            # Add to the appropriate normalized section
            result[normalized_type].append(post_data)
        
        return result
    
    async def _get_user_comments_with_subtype(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user comments with subtype information.
        
        Args:
            user_id: User ID
            
        Returns:
            List of comment data with subtype and routing information
        """
        # Get all user comments
        comments = await self.comment_repository.find_by_author(user_id)
        
        result = []
        for comment in comments:
            # Extract routing information from metadata
            route_path = comment.metadata.get("route_path", "/")
            subtype = comment.metadata.get("subtype")
            post_title = comment.metadata.get("post_title", "게시글 정보 없음")
            
            # Get post statistics for the comment
            post_view_count = 0
            post_like_count = 0
            post_dislike_count = 0
            post_comment_count = 0
            
            if comment.parent_id:
                try:
                    # Calculate real-time stats for the post
                    real_stats = await self._calculate_post_stats(comment.parent_id)
                    post_view_count = real_stats["view_count"]
                    post_like_count = real_stats["like_count"]
                    post_dislike_count = real_stats["dislike_count"]
                    post_comment_count = real_stats["comment_count"]
                except Exception:
                    # If post is not found, use default values
                    pass
            
            comment_data = {
                "id": str(comment.id),
                "content": comment.content,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at.isoformat(),
                "route_path": route_path,
                "subtype": subtype,
                "post_title": post_title,
                "view_count": post_view_count,
                "like_count": post_like_count,
                "dislike_count": post_dislike_count,
                "comment_count": post_comment_count
            }
            
            result.append(comment_data)
        
        return result
    
    async def _get_user_reactions_grouped(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get user reactions grouped by reaction type.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with reaction types as keys and reaction lists as values
        """
        # Get all user reactions
        reactions = await self.user_reaction_repository.find_by_user(user_id)
        
        # Initialize result
        result = {
            "likes": [],
            "bookmarks": [],
            "dislikes": []
        }
        
        # Group reactions by type
        for reaction in reactions:
            # Extract routing information from metadata
            route_path = reaction.metadata.get("route_path", "/")
            target_title = reaction.metadata.get("target_title", "")
            
            # Get post information for reactions (only for post reactions)
            post_title = target_title
            post_view_count = 0
            post_like_count = 0
            post_dislike_count = 0
            post_comment_count = 0
            
            if reaction.target_type == "post" and reaction.target_id:
                try:
                    post = await self.post_repository.get_by_id(reaction.target_id)
                    # 삭제된 게시글 스킵
                    if post.status == "deleted":
                        continue
                    post_title = post.title
                    # Calculate real-time stats for the post
                    real_stats = await self._calculate_post_stats(reaction.target_id)
                    post_view_count = real_stats["view_count"]
                    post_like_count = real_stats["like_count"]
                    post_dislike_count = real_stats["dislike_count"]
                    post_comment_count = real_stats["comment_count"]
                except Exception:
                    # If post is not found or deleted, skip this reaction
                    continue
            
            reaction_data = {
                "id": str(reaction.id),
                "target_type": reaction.target_type,
                "target_id": reaction.target_id,
                "created_at": reaction.created_at.isoformat(),
                "route_path": route_path,
                "target_title": post_title,
                "title": post_title,  # 프론트엔드에서 사용할 제목
                "view_count": post_view_count,
                "like_count": post_like_count,
                "dislike_count": post_dislike_count,
                "comment_count": post_comment_count
            }
            
            # Add to appropriate category (각 반응은 독립적이므로 elif 대신 if 사용)
            if reaction.liked:
                result["likes"].append(reaction_data)
            if reaction.disliked:
                result["dislikes"].append(reaction_data)
            if reaction.bookmarked:
                result["bookmarks"].append(reaction_data)
        
        return result
    
    def _generate_route_path(self, page_type: str, slug: str) -> str:
        """Generate route path based on page type and slug.
        
        Args:
            page_type: Page type (including both normalized and original DB types)
            slug: Post slug
            
        Returns:
            Route path string
        """
        route_mapping = {
            # Normalized types (for backward compatibility)
            "board": f"/board-post/{slug}",
            "info": f"/property-info/{slug}",
            "services": f"/moving-services-post/{slug}",
            "tips": f"/expert-tips/{slug}",
            # Original DB types
            "property_information": f"/property-info/{slug}",
            "expert_tips": f"/expert-tips/{slug}"
        }
        
        return route_mapping.get(page_type, f"/post/{slug}")
    
    async def _calculate_post_stats(self, post_id: str) -> Dict[str, int]:
        """Calculate real-time statistics for a post (same as PostsService).
        
        Args:
            post_id: Post ID
            
        Returns:
            Dictionary with current stats
        """
        try:
            # Get like count from UserReaction
            like_count = await UserReaction.find({
                "target_type": "post",
                "target_id": post_id,
                "liked": True
            }).count()
            
            # Get dislike count from UserReaction
            dislike_count = await UserReaction.find({
                "target_type": "post",
                "target_id": post_id,
                "disliked": True
            }).count()
            
            # Get bookmark count from UserReaction
            bookmark_count = await UserReaction.find({
                "target_type": "post",
                "target_id": post_id,
                "bookmarked": True
            }).count()
            
            # Get total comment count (including replies) from Comment
            comment_count = await Comment.find({
                "parent_id": post_id,
                "status": "active"
            }).count()
            
            # Get view count from Post document (maintained in post model)
            post = await Post.find_one({"_id": PydanticObjectId(post_id)})
            view_count = post.view_count if post else 0
            
            return {
                "view_count": view_count,
                "like_count": like_count,
                "dislike_count": dislike_count,
                "comment_count": comment_count,
                "bookmark_count": bookmark_count
            }
            
        except Exception as e:
            logger.error(f"Error calculating post stats for {post_id}: {e}")
            return {
                "view_count": 0,
                "like_count": 0,
                "dislike_count": 0,
                "comment_count": 0,
                "bookmark_count": 0
            }