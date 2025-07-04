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
    """Normalize post type - simplified to use DB types directly.
    
    Only normalizes 'moving services' to 'services' for consistency.
    All other DB types are used as-is in frontend.
    
    Args:
        post_type: The post type from database
        
    Returns:
        DB post type or 'services' for moving services
    """
    if not post_type:
        return None
        
    # Only normalize inconsistent naming
    if post_type == "moving services":
        return "services"
        
    # Use DB types directly (expert_tips, property_information, board, services)
    return post_type


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
        """Normalize post type - simplified to use DB types directly."""
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
        
        # Initialize result with DB-native page types
        result = {
            "board": [],
            "property_information": [],  # DB 원시 타입 사용
            "expert_tips": [],           # DB 원시 타입 사용
            "services": []
        }
        
        # Group posts by page type
        for post in posts:
            # Get the type from metadata (use DB type directly)
            post_type = getattr(post.metadata, "type", None) if post.metadata else None
            
            # Only normalize 'moving services' to 'services', keep others as-is
            normalized_type = self.normalize_post_type(post_type)
            
            # Skip posts with unrecognized types
            if normalized_type is None:
                continue
                
            # Generate route path using normalized type
            route_path = self._generate_route_path(normalized_type, post.slug)
            
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
        """Get user reactions grouped by reaction type (backward compatibility - flattens page type grouping).
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with reaction types as keys and reaction lists as values (legacy format)
        """
        # Get new page-type grouped reactions
        page_grouped_reactions = await self._get_user_reactions_grouped_paginated(user_id, limit=1000, skip=0)
        
        # Flatten page grouping for backward compatibility
        result = {
            "likes": [],
            "bookmarks": [],
            "dislikes": []
        }
        
        for reaction_type in ["likes", "bookmarks", "dislikes"]:
            reaction_key = f"reaction-{reaction_type}"
            for page_type in ["board", "property_information", "expert_tips", "services"]:
                result[reaction_type].extend(page_grouped_reactions[reaction_key][page_type])
        
        return result
    
    async def _get_user_reactions_grouped_paginated(self, user_id: str, limit: int = 10, skip: int = 0) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Get user reactions grouped by reaction type and page type with pagination (similar to posts classification).
        
        Args:
            user_id: User ID
            limit: Maximum number of reactions to return
            skip: Number of reactions to skip
            
        Returns:
            Dictionary with reaction types as keys and page type dictionaries as values
        """
        # Get paginated user reactions
        reactions = await self.user_reaction_repository.find_by_user_paginated(user_id, limit, skip)
        
        # Initialize result with reaction-* prefix pattern and DB-native page types
        result = {
            "reaction-likes": {
                "board": [],
                "property_information": [],  # DB 원시 타입 사용
                "expert_tips": [],           # DB 원시 타입 사용
                "services": []
            },
            "reaction-bookmarks": {
                "board": [],
                "property_information": [],
                "expert_tips": [],
                "services": []
            },
            "reaction-dislikes": {
                "board": [],
                "property_information": [],
                "expert_tips": [],
                "services": []
            }
        }
        
        # Group reactions by type and page
        logger.info(f"🔍 ANALYZING {len(reactions)} reactions for user {user_id}")
        
        # 모든 route_path 패턴 수집
        all_route_paths = set()
        for reaction in reactions:
            route_path = reaction.metadata.get("route_path", "/")
            all_route_paths.add(route_path)
        
        logger.info(f"📋 ALL UNIQUE ROUTE PATHS FOUND: {sorted(list(all_route_paths))}")
        
        for i, reaction in enumerate(reactions):
            # Extract routing information from metadata
            route_path = reaction.metadata.get("route_path", "/")
            target_title = reaction.metadata.get("target_title", "")
            
            logger.info(f"Reaction {i+1}/{len(reactions)}: route_path='{route_path}', target_type='{reaction.target_type}', liked={reaction.liked}, disliked={reaction.disliked}, bookmarked={reaction.bookmarked}")
            
            # Extract page type from route_path (similar to posts classification)
            page_type = self._extract_page_type_from_reaction(route_path)
            
            # Skip reactions with unknown page types (already logged)
            if page_type is None:
                logger.warning(f"❌ SKIPPING reaction {reaction.id} due to unknown page_type for route_path '{route_path}'")
                continue
                
            logger.info(f"✅ ADDING reaction {reaction.id} to {page_type} page_type")
            
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
            
            # Add to appropriate category using reaction-* prefix pattern
            if reaction.liked:
                result["reaction-likes"][page_type].append(reaction_data)
            if reaction.disliked:
                result["reaction-dislikes"][page_type].append(reaction_data)
            if reaction.bookmarked:
                result["reaction-bookmarks"][page_type].append(reaction_data)
        
        return result
    
    def _extract_page_type_from_reaction(self, route_path: str) -> Optional[str]:
        """Extract page type from reaction route_path (similar to posts classification).
        
        Args:
            route_path: Route path from reaction metadata
            
        Returns:
            Page type (board, info, services, tips) or None for unknown routes
        """
        if not route_path:
            logger.warning("Empty route_path detected in reaction")
            return None
            
        logger.info(f"Processing reaction route_path: '{route_path}'")
            
        # 현재 올바른 패턴들 (DB 원시 타입 사용)
        route_to_page_mapping = {
            "/board-post/": "board",
            "/property-info/": "property_information",  # DB 원시 타입 사용
            "/moving-services-post/": "services",
            "/expert-tips/": "expert_tips"             # DB 원시 타입 사용
        }
        
        # 기존 데이터에 있을 수 있는 다른 패턴들 (DB 원시 타입으로 매핑)
        legacy_patterns = {
            "/board/": "board",
            "/post/": "board",  # 기본 패턴이 board일 가능성
            "/property/": "property_information",
            "/info/": "property_information",
            "/services/": "services",
            "/tips/": "expert_tips",
            "/expert/": "expert_tips"
        }
        
        # 현재 패턴 먼저 확인
        for route_prefix, page_type in route_to_page_mapping.items():
            if route_path.startswith(route_prefix):
                logger.info(f"✅ CURRENT PATTERN MATCHED: route_path '{route_path}' → page_type '{page_type}' (prefix: '{route_prefix}')")
                return page_type
        
        # 레거시 패턴 확인
        for route_prefix, page_type in legacy_patterns.items():
            if route_path.startswith(route_prefix):
                logger.info(f"✅ LEGACY PATTERN MATCHED: route_path '{route_path}' → page_type '{page_type}' (prefix: '{route_prefix}')")
                return page_type
                
        logger.warning(f"Unrecognized reaction route_path: '{route_path}'. This reaction will be ignored.")
        return None

    def _generate_route_path(self, page_type: str, slug: str) -> str:
        """Generate route path based on page type and slug.
        
        Args:
            page_type: Page type (including both normalized and original DB types)
            slug: Post slug
            
        Returns:
            Route path string
        """
        route_mapping = {
            # DB types to route paths
            "board": f"/board-post/{slug}",
            "property_information": f"/property-info/{slug}",
            "expert_tips": f"/expert-tips/{slug}",
            "services": f"/moving-services-post/{slug}"
        }
        
        return route_mapping.get(page_type, f"/post/{slug}")
    
