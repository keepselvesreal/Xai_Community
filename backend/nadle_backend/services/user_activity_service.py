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
    
    async def get_user_activity_summary(self, user_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get comprehensive user activity summary with pagination.
        
        Args:
            user_id: User ID
            page: Page number (default: 1)
            limit: Items per page (default: 10)
            
        Returns:
            Dictionary containing user's activity data grouped by type with pagination info
        """
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get paginated user activity data and counts in parallel
        posts_by_type = await self._get_user_posts_by_page_type_paginated(user_id, limit, skip)
        comments_with_subtype = await self._get_user_comments_with_subtype_paginated(user_id, limit, skip)
        reactions_grouped = await self._get_user_reactions_grouped_paginated(user_id, limit, skip)
        
        # Get total counts for pagination
        total_posts_count = await self.post_repository.count_by_author(user_id)
        total_comments_count = await self.comment_repository.count_by_author(user_id)
        total_reactions_count = await self.user_reaction_repository.count_by_user(user_id)
        
        # Calculate pagination info
        pagination_info = {
            "posts": {
                "total_count": total_posts_count,
                "page": page,
                "limit": limit,
                "has_more": skip + limit < total_posts_count
            },
            "comments": {
                "total_count": total_comments_count,
                "page": page,
                "limit": limit,
                "has_more": skip + limit < total_comments_count
            },
            "reactions": {
                "total_count": total_reactions_count,
                "page": page,
                "limit": limit,
                "has_more": skip + limit < total_reactions_count
            }
        }
        
        return {
            "posts": posts_by_type,
            "comments": comments_with_subtype,
            "reactions": reactions_grouped,
            "pagination": pagination_info
        }
    
    async def get_user_activity_summary_paginated(self, user_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get comprehensive user activity summary with pagination (alias for backward compatibility).
        
        Args:
            user_id: User ID
            page: Page number (default: 1)
            limit: Items per page (default: 10)
            
        Returns:
            Dictionary containing user's activity data grouped by type with pagination info
        """
        return await self.get_user_activity_summary(user_id, page, limit)
    
    async def _get_user_posts_by_page_type(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get user posts grouped by page type (backward compatibility - uses pagination with high limit).
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with page types as keys and post lists as values
        """
        return await self._get_user_posts_by_page_type_paginated(user_id, limit=1000, skip=0)
    
    async def _get_user_posts_by_page_type_paginated(self, user_id: str, limit: int = 10, skip: int = 0) -> Dict[str, List[Dict[str, Any]]]:
        """Get user posts grouped by page type with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of posts to return
            skip: Number of posts to skip
            
        Returns:
            Dictionary with page types as keys and post lists as values
        """
        # Get paginated user posts
        posts = await self.post_repository.find_by_author_paginated(user_id, limit, skip)
        
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
            
            # Use model fields directly instead of real-time calculation
            post_data = {
                "id": str(post.id),
                "title": post.title,
                "slug": post.slug,
                "created_at": post.created_at.isoformat(),
                "view_count": post.view_count,      # Direct from model
                "like_count": post.like_count,      # Direct from model
                "dislike_count": post.dislike_count, # Direct from model
                "comment_count": post.comment_count, # Direct from model
                "route_path": route_path
            }
            
            # Add to the appropriate normalized section
            result[normalized_type].append(post_data)
        
        return result
    
    async def _get_user_comments_with_subtype(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user comments with subtype information (backward compatibility - uses pagination with high limit).
        
        Args:
            user_id: User ID
            
        Returns:
            List of comment data with subtype and routing information
        """
        return await self._get_user_comments_with_subtype_paginated(user_id, limit=1000, skip=0)
    
    async def _get_user_comments_with_subtype_paginated(self, user_id: str, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """Get user comments with subtype information with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of comments to return
            skip: Number of comments to skip
            
        Returns:
            List of comment data with subtype and routing information
        """
        # Get paginated user comments
        comments = await self.comment_repository.find_by_author_paginated(user_id, limit, skip)
        
        result = []
        for comment in comments:
            # Extract routing information from metadata
            route_path = comment.metadata.get("route_path", "/")
            subtype = comment.metadata.get("subtype")
            post_title = comment.metadata.get("post_title", "게시글 정보 없음")
            
            comment_data = {
                "id": str(comment.id),
                "content": comment.content,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at.isoformat(),
                "route_path": route_path,
                "subtype": subtype,
                "post_title": post_title
            }
            
            result.append(comment_data)
        
        return result
    
    async def _get_user_reactions_grouped(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get user reactions grouped by reaction type (backward compatibility - uses pagination with high limit).
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with reaction types as keys and reaction lists as values
        """
        return await self._get_user_reactions_grouped_paginated(user_id, limit=1000, skip=0)
    
    async def _get_user_reactions_grouped_paginated(self, user_id: str, limit: int = 10, skip: int = 0) -> Dict[str, List[Dict[str, Any]]]:
        """Get user reactions grouped by reaction type with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of reactions to return
            skip: Number of reactions to skip
            
        Returns:
            Dictionary with reaction types as keys and reaction lists as values
        """
        # Get paginated user reactions
        reactions = await self.user_reaction_repository.find_by_user_paginated(user_id, limit, skip)
        
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
            
            if reaction.target_type == "post" and reaction.target_id:
                try:
                    post = await self.post_repository.get_by_id(reaction.target_id)
                    # 삭제된 게시글 스킵
                    if post.status == "deleted":
                        continue
                    post_title = post.title
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
                "title": post_title  # 프론트엔드에서 사용할 제목
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
    
