"""User activity service for aggregating user's activity data."""

import logging
from typing import Dict, List, Any, Optional
from nadle_backend.models.core import Post, Comment, UserReaction
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository
from nadle_backend.services.post_stats_service import PostStatsService, normalize_post_type
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)


class UserActivityService:
    """Service for aggregating user activity data."""

    def __init__(
        self,
        post_repository: PostRepository,
        comment_repository: CommentRepository,
        user_reaction_repository: UserReactionRepository,
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
        # 공통 통계 서비스 초기화 (중복 로직 제거)
        self.post_stats_service = PostStatsService(comment_repository)

    def normalize_post_type(self, post_type: Optional[str]) -> Optional[str]:
        """Normalize post type - simplified to use DB types directly."""
        return normalize_post_type(post_type)

    async def get_user_activity_counts(self, user_id: str) -> Dict[str, int]:
        """Get user activity counts only (optimized for pagination).
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing total counts for each activity type
        """
        # 병렬로 빠르게 개수만 조회
        total_posts_count = await self.post_repository.count_by_author(user_id)
        total_comments_count = await self.comment_repository.count_by_author(user_id) 
        total_reactions_count = await self.user_reaction_repository.count_by_user(user_id)
        
        return {
            "posts": total_posts_count,
            "comments": total_comments_count,
            "reactions": total_reactions_count
        }

    async def get_user_activity_summary(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> Dict[str, Any]:
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

        # 진짜 서버 사이드 페이지네이션 적용
        posts_by_type = await self._get_user_posts_by_page_type_paginated(
            user_id, limit, skip
        )
        comments_with_subtype = await self._get_user_comments_with_subtype_paginated(
            user_id, limit, skip
        )
        reactions_grouped = await self._get_user_reactions_grouped_paginated(
            user_id, limit, skip
        )

        # Get total counts for pagination
        total_posts_count = await self.post_repository.count_by_author(user_id)
        total_comments_count = await self.comment_repository.count_by_author(user_id)
        total_reactions_count = await self.user_reaction_repository.count_by_user(
            user_id
        )

        # Calculate pagination info
        pagination_info = {
            "posts": {
                "total_count": total_posts_count,
                "page": page,
                "limit": limit,
                "has_more": skip + limit < total_posts_count,
            },
            "comments": {
                "total_count": total_comments_count,
                "page": page,
                "limit": limit,
                "has_more": skip + limit < total_comments_count,
            },
            "reactions": {
                "total_count": total_reactions_count,
                "page": page,
                "limit": limit,
                "has_more": skip + limit < total_reactions_count,
            },
        }

        return {
            "posts": posts_by_type,
            "comments": comments_with_subtype,
            "reactions": reactions_grouped,
            "pagination": pagination_info,
        }

    async def get_user_activity_summary_paginated(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> Dict[str, Any]:
        """Get comprehensive user activity summary with pagination (alias for backward compatibility).

        Args:
            user_id: User ID
            page: Page number (default: 1)
            limit: Items per page (default: 10)

        Returns:
            Dictionary containing user's activity data grouped by type with pagination info
        """
        return await self.get_user_activity_summary(user_id, page, limit)

    async def _get_user_posts_by_page_type(
        self, user_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get user posts grouped by page type (backward compatibility - uses pagination with high limit).

        Args:
            user_id: User ID

        Returns:
            Dictionary with page types as keys and post lists as values
        """
        return await self._get_user_posts_by_page_type_paginated(
            user_id, limit=1000, skip=0
        )

    async def _get_user_posts_by_page_type_paginated(
        self, user_id: str, limit: int = 10, skip: int = 0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get user posts grouped by page type with pagination.

        Args:
            user_id: User ID
            limit: Maximum number of posts to return
            skip: Number of posts to skip

        Returns:
            Dictionary with page types as keys and post lists as values
        """
        # Get paginated user posts with current statistics (same as PostsService)
        posts_data = await self.post_repository.find_by_author_with_current_stats(
            user_id, limit, skip
        )
        
        # Debug: Log posts retrieval (debug level)
        logger.debug(f"🔍 UserActivityService: Retrieved {len(posts_data)} posts for user {user_id}")

        # Initialize result with DB-native page types (Phase 5: unified)
        result = {
            "board": [],
            "property_information": [],  # DB 원시 타입 사용
            "expert_tips": [],  # DB 원시 타입 사용
            "moving_services": [],  # Phase 5: DB 원시 타입으로 통일
            "suggestions": [],  # 건의함
            "report": [],  # 신고함
            "moving-services-register-inquiry": [],  # 입주 서비스 업체 등록 문의
            "expert-tips-register-inquiry": [],  # 전문가 꿀정보 등록 문의
        }

        # 배치 처리를 위해 moving services 게시글들 식별 (공통 서비스 사용)
        moving_services_post_ids = self.post_stats_service.identify_moving_services_posts(posts_data)

        # 배치로 moving services 게시글들의 댓글 통계 조회 (공통 서비스 사용, N+1 쿼리 최적화)
        moving_services_bulk_stats = await self.post_stats_service.get_bulk_moving_services_stats(moving_services_post_ids)

        # Group posts by page type
        for post_dict in posts_data:
            # Skip deleted posts
            if post_dict.get("status") == "deleted":
                continue

            # Get the type from metadata (use DB type directly)
            metadata = post_dict.get("metadata", {})
            post_type = metadata.get("type") if metadata else None

            # Only normalize 'moving services' to 'services', keep others as-is
            normalized_type = self.normalize_post_type(post_type)

            # Skip posts with unrecognized types
            if normalized_type is None:
                continue

            # Generate route path using current post data (항상 최신 slug 사용)
            route_path = self._generate_route_path(normalized_type, post_dict.get("slug"))

            # Use current statistics from aggregation result (already calculated)
            post_data = {
                "id": str(post_dict["_id"]),
                "title": post_dict.get("title"),
                "slug": post_dict.get("slug"),
                "created_at": post_dict.get("created_at").isoformat() if post_dict.get("created_at") else None,
                "view_count": post_dict.get("view_count", 0),  # From aggregation
                "like_count": post_dict.get("like_count", 0),  # From aggregation
                "dislike_count": post_dict.get("dislike_count", 0),  # From aggregation
                "comment_count": post_dict.get("comment_count", 0),  # From aggregation
                "bookmark_count": post_dict.get("bookmark_count", 0),  # From aggregation
                "route_path": route_path,
            }
            
            # For moving services posts, use bulk statistics (공통 서비스, N+1 쿼리 최적화)
            if normalized_type == "moving_services":
                # 공통 서비스에서 가져온 배치 조회 결과 사용
                post_id_str = str(post_dict["_id"])
                bulk_stats = moving_services_bulk_stats.get(post_id_str, {"inquiry_count": 0, "review_count": 0})
                post_data["inquiry_count"] = bulk_stats["inquiry_count"]
                post_data["review_count"] = bulk_stats["review_count"]
                logger.debug(f"📊 Bulk moving service stats for {post_dict.get('title')}: inquiries={post_data['inquiry_count']}, reviews={post_data['review_count']}")
            else:
                post_data["inquiry_count"] = 0
                post_data["review_count"] = 0

            # Add to the appropriate normalized section
            result[normalized_type].append(post_data)

        return result

    async def _get_user_comments_with_subtype(
        self, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user comments with subtype information (backward compatibility - uses pagination with high limit).

        Args:
            user_id: User ID

        Returns:
            List of comment data with subtype and routing information
        """
        return await self._get_user_comments_with_subtype_paginated(
            user_id, limit=1000, skip=0
        )

    async def _get_user_comments_with_subtype_paginated(
        self, user_id: str, limit: int = 10, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user comments with subtype information with pagination.

        Args:
            user_id: User ID
            limit: Maximum number of comments to return
            skip: Number of comments to skip

        Returns:
            List of comment data with subtype and routing information
        """
        # Get paginated user comments
        comments = await self.comment_repository.find_by_author_paginated(
            user_id, limit, skip
        )

        # 배치 최적화: 모든 댓글의 게시글을 한 번에 조회
        result = []
        if not comments:
            return result

        # 1. 모든 parent_id 수집
        parent_ids = [comment.parent_id for comment in comments if comment.parent_id]
        
        # 2. 모든 게시글을 한 번에 조회 (배치 쿼리)
        posts_dict = {}
        if parent_ids:
            from beanie import PydanticObjectId
            from nadle_backend.models.core import Post
            
            # 배치로 모든 게시글 통계 조회 (메모리 최적화: 필요한 필드만 프로젝션)
            pipeline = [
                {"$match": {"_id": {"$in": [PydanticObjectId(pid) for pid in parent_ids]}}},
                {"$project": {
                    "_id": 1, 
                    "title": 1, 
                    "metadata.type": 1,  # 필요한 metadata 필드만
                    "view_count": {"$ifNull": ["$view_count", 0]},
                    "like_count": {"$ifNull": ["$like_count", 0]},
                    "dislike_count": {"$ifNull": ["$dislike_count", 0]},
                    "comment_count": {"$ifNull": ["$comment_count", 0]},
                    "bookmark_count": {"$ifNull": ["$bookmark_count", 0]},
                }}
            ]
            
            post_results = await Post.get_motor_collection().aggregate(pipeline).to_list(len(parent_ids))
            posts_dict = {str(post["_id"]): post for post in post_results}
        
        # 3. 입주 서비스 게시글들의 문의/후기 수 실시간 조회 (공통 서비스 사용)
        # moving_services 타입 게시글 식별 (공통 서비스 사용)
        moving_services_posts = self.post_stats_service.identify_moving_services_from_dict(posts_dict)
        
        # 디버깅: 댓글의 subtype과 parent_id도 확인 (debug level)
        service_comments = [c for c in comments if c.metadata.get("subtype") in ["service_inquiry", "service_review"]]
        logger.debug(f"📝 Found {len(service_comments)} service comments with parent_ids: {[(str(c.id), c.parent_id, c.metadata.get('subtype')) for c in service_comments]}")
        logger.debug(f"🔍 Found {len(moving_services_posts)} moving services posts in posts_dict: {moving_services_posts}")
        logger.debug(f"📋 All posts dict keys: {list(posts_dict.keys())}")
        logger.debug(f"📋 Posts dict metadata types: {[(k, v.get('metadata', {}).get('type')) for k, v in posts_dict.items()]}")
        
        # Service 댓글들의 parent_id 중에서 moving_services가 아닌 것들 확인  
        service_parent_ids = [c.parent_id for c in service_comments if c.parent_id]
        missing_parent_ids = [pid for pid in service_parent_ids if pid not in posts_dict]
        
        if missing_parent_ids:
            logger.warning(f"❌ posts_dict에서 찾을 수 없는 service 댓글 parent_ids: {missing_parent_ids}")
            # 누락된 parent_id들의 게시글을 추가로 조회
            try:
                additional_pipeline = [
                    {"$match": {"_id": {"$in": [PydanticObjectId(pid) for pid in missing_parent_ids]}}},
                    {"$project": {
                        "_id": 1, 
                        "title": 1, 
                        "metadata.type": 1,  # 메모리 최적화: 필요한 metadata 필드만
                        "view_count": {"$ifNull": ["$view_count", 0]},
                        "like_count": {"$ifNull": ["$like_count", 0]},
                        "dislike_count": {"$ifNull": ["$dislike_count", 0]},
                        "comment_count": {"$ifNull": ["$comment_count", 0]},
                        "bookmark_count": {"$ifNull": ["$bookmark_count", 0]},
                    }}
                ]
                
                additional_results = await Post.get_motor_collection().aggregate(additional_pipeline).to_list(len(missing_parent_ids))
                for post in additional_results:
                    posts_dict[str(post["_id"])] = post
                    logger.debug(f"✅ 추가 조회된 게시글: {post['_id']}, type: {post.get('metadata', {}).get('type')}")
                    
            except Exception as e:
                logger.error(f"❌ 추가 게시글 조회 실패: {e}")
        
        # 다시 moving_services 게시글 식별 (추가 조회된 것 포함, 공통 서비스 사용)
        moving_services_posts = self.post_stats_service.identify_moving_services_from_dict(posts_dict)
        
        logger.debug(f"🔍 Updated moving services posts count: {len(moving_services_posts)}")
        
        # 배치 처리로 N+1 쿼리 문제 해결 (공통 서비스 사용)
        moving_services_stats = await self.post_stats_service.get_bulk_moving_services_stats(moving_services_posts)
        
        # 4. 댓글 데이터 구성
        for comment in comments:
            # Extract routing information from metadata
            route_path = comment.metadata.get("route_path", "/")
            subtype = comment.metadata.get("subtype")
            post_title = comment.metadata.get("post_title", "게시글 정보 없음")

            # 기본 통계값
            post_stats = {
                "view_count": 0,
                "like_count": 0,
                "dislike_count": 0,
                "comment_count": 0,
                "bookmark_count": 0,
                "inquiry_count": 0,
                "review_count": 0,
            }
            
            # 배치 조회 결과에서 해당 게시글 통계 가져오기
            if comment.parent_id and comment.parent_id in posts_dict:
                post_dict = posts_dict[comment.parent_id]
                post_stats.update({
                    "view_count": post_dict.get("view_count", 0),
                    "like_count": post_dict.get("like_count", 0),
                    "dislike_count": post_dict.get("dislike_count", 0),
                    "comment_count": post_dict.get("comment_count", 0),
                    "bookmark_count": post_dict.get("bookmark_count", 0),
                })
                
                # 입주 서비스 통계 추가
                if comment.parent_id in moving_services_stats:
                    post_stats.update(moving_services_stats[comment.parent_id])
                    
                    # 디버깅: 문의/후기 통계 로깅 (debug level)
                    if subtype in ['service_inquiry', 'service_review']:
                        logger.debug(f"📊 문의/후기 통계 - 댓글 {comment.id}, subtype: {subtype}, "
                                  f"parent_id: {comment.parent_id}, "
                                  f"inquiry_count: {post_stats['inquiry_count']}, "
                                  f"review_count: {post_stats['review_count']}")
            else:
                # 디버깅: 게시글을 찾지 못한 경우
                if subtype in ['service_inquiry', 'service_review']:
                    logger.warning(f"❌ 문의/후기 댓글 {comment.id}의 게시글({comment.parent_id}) 통계 조회 실패")

            comment_data = {
                "id": str(comment.id),
                "content": comment.content,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at.isoformat(),
                "route_path": route_path,
                "subtype": subtype,
                "post_title": post_title,
                # Add post statistics
                **post_stats,
            }

            result.append(comment_data)

        return result

    async def _get_user_reactions_grouped(
        self, user_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get user reactions grouped by reaction type (backward compatibility - flattens page type grouping).

        Args:
            user_id: User ID

        Returns:
            Dictionary with reaction types as keys and reaction lists as values (legacy format)
        """
        # Get new page-type grouped reactions and return the same structure
        # for consistency with users.py expectations
        return await self._get_user_reactions_grouped_paginated(
            user_id, limit=1000, skip=0
        )

    async def _get_user_reactions_grouped_paginated(
        self, user_id: str, limit: int = 10, skip: int = 0
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Get user reactions grouped by reaction type and page type with pagination (similar to posts classification).

        Args:
            user_id: User ID
            limit: Maximum number of reactions to return
            skip: Number of reactions to skip

        Returns:
            Dictionary with reaction types as keys and page type dictionaries as values
        """
        # Get paginated user reactions
        reactions = await self.user_reaction_repository.find_by_user_paginated(
            user_id, limit, skip
        )

        # Initialize result with reaction-* prefix pattern and DB-native page types (Phase 5: unified)
        result = {
            "reaction-likes": {
                "board": [],
                "property_information": [],  # DB 원시 타입 사용
                "expert_tips": [],  # DB 원시 타입 사용
                "moving_services": [],  # Phase 5: DB 원시 타입으로 통일
                "suggestions": [],  # 건의함
                "report": [],  # 신고함
                "moving-services-register-inquiry": [],  # 입주 서비스 업체 등록 문의
                "expert-tips-register-inquiry": [],  # 전문가 꿀정보 등록 문의
            },
            "reaction-bookmarks": {
                "board": [],
                "property_information": [],
                "expert_tips": [],
                "moving_services": [],
                "suggestions": [],
                "report": [],
                "moving-services-register-inquiry": [],
                "expert-tips-register-inquiry": [],
            },
            "reaction-dislikes": {
                "board": [],
                "property_information": [],
                "expert_tips": [],
                "moving_services": [],
                "suggestions": [],
                "report": [],
                "moving-services-register-inquiry": [],
                "expert-tips-register-inquiry": [],
            },
        }

        # Group reactions by type and page (debug level logging)
        logger.debug(f"🔍 ANALYZING {len(reactions)} reactions for user {user_id}")

        for i, reaction in enumerate(reactions):
            logger.debug(
                f"Reaction {i+1}/{len(reactions)}: target_type='{reaction.target_type}', liked={reaction.liked}, disliked={reaction.disliked}, bookmarked={reaction.bookmarked}"
            )

            # For post reactions, get current post information directly
            if reaction.target_type == "post" and reaction.target_id:
                try:
                    # Get post with current statistics (same as user posts)
                    post_data_list = await self.post_repository.find_by_author_with_current_stats(
                        "", 1, 0  # We'll override the query with specific post ID
                    )
                    
                    # Actually, let's get the specific post with current stats
                    try:
                        from beanie import PydanticObjectId
                        pipeline = [
                            {"$match": {"_id": PydanticObjectId(reaction.target_id)}},
                            {"$project": {
                                "_id": 1, "title": 1, "slug": 1, "status": 1, "metadata": 1,
                                "view_count": {"$ifNull": ["$view_count", 0]},
                                "like_count": {"$ifNull": ["$like_count", 0]},
                                "dislike_count": {"$ifNull": ["$dislike_count", 0]},
                                "comment_count": {"$ifNull": ["$comment_count", 0]},
                                "bookmark_count": {"$ifNull": ["$bookmark_count", 0]},
                            }}
                        ]
                        from nadle_backend.models.core import Post
                        post_results = await Post.get_motor_collection().aggregate(pipeline).to_list(1)
                        
                        if not post_results:
                            logger.debug(f"❌ SKIPPING reaction {reaction.id} - post not found")
                            continue
                            
                        post_dict = post_results[0]
                        
                        # Skip deleted posts
                        if post_dict.get("status") == "deleted":
                            logger.debug(f"❌ SKIPPING reaction {reaction.id} - post is deleted")
                            continue

                        # Get page type and route path
                        metadata = post_dict.get("metadata", {})
                        raw_page_type = metadata.get("type", "board") if metadata else "board"
                        page_type = normalize_post_type(raw_page_type) or "board"
                        actual_route_path = self._generate_route_path(page_type, post_dict.get("slug"))
                        post_title = post_dict.get("title")
                        
                        # Current statistics from aggregation
                        current_stats = {
                            "view_count": post_dict.get("view_count", 0),
                            "like_count": post_dict.get("like_count", 0),
                            "dislike_count": post_dict.get("dislike_count", 0),
                            "comment_count": post_dict.get("comment_count", 0),
                            "bookmark_count": post_dict.get("bookmark_count", 0),
                        }
                        
                    except Exception as e:
                        logger.warning(f"❌ Error getting current stats for reaction post {reaction.target_id}: {e}")
                        continue

                    logger.debug(
                        f"✅ ADDING reaction {reaction.id} to {page_type} page_type with current route: {actual_route_path}"
                    )

                except Exception as e:
                    # If post is not found or deleted, skip this reaction
                    logger.warning(
                        f"❌ SKIPPING reaction {reaction.id} - post not found: {e}"
                    )
                    continue
            else:
                # Non-post reactions (comments, etc.) - skip for now
                logger.debug(f"❌ SKIPPING reaction {reaction.id} - not a post reaction")
                continue

            reaction_data = {
                "id": str(reaction.id),
                "target_type": reaction.target_type,
                "target_id": reaction.target_id,
                "created_at": reaction.created_at.isoformat(),
                "route_path": actual_route_path,  # 실제 현재 slug를 사용한 route_path
                "target_title": post_title,
                "title": post_title,  # 프론트엔드에서 사용할 제목
                # 게시글의 현재 통계 정보 추가 (aggregation에서 가져온 실시간 데이터)
                "view_count": current_stats["view_count"],
                "like_count": current_stats["like_count"],
                "dislike_count": current_stats["dislike_count"],
                "comment_count": current_stats["comment_count"],
                "bookmark_count": current_stats["bookmark_count"],
            }
            
            # For moving services posts, add real-time inquiry/review counts
            if page_type == "moving_services":
                try:
                    comment_stats = await self.comment_repository.get_comment_stats_by_post(reaction.target_id)
                    reaction_data["inquiry_count"] = comment_stats.get("service_inquiry", 0)
                    reaction_data["review_count"] = comment_stats.get("service_review", 0)
                except Exception as e:
                    logger.warning(f"Failed to get comment stats for reaction post {reaction.target_id}: {e}")
                    reaction_data["inquiry_count"] = 0
                    reaction_data["review_count"] = 0
            else:
                reaction_data["inquiry_count"] = 0
                reaction_data["review_count"] = 0

            # Add to appropriate category using reaction-* prefix pattern
            if reaction.liked:
                result["reaction-likes"][page_type].append(reaction_data)
            if reaction.disliked:
                result["reaction-dislikes"][page_type].append(reaction_data)
            if reaction.bookmarked:
                result["reaction-bookmarks"][page_type].append(reaction_data)

        return result

    def _generate_route_path(self, page_type: str, slug: str) -> str:
        """Generate route path based on page type and slug.

        posts_service와 동일한 매핑 방식 사용

        Args:
            page_type: Page type (DB raw type)
            slug: Post slug

        Returns:
            Route path string
        """
        # posts_service와 동일한 매핑 테이블 사용
        route_mapping = {
            "board": f"/board/{slug}",
            "property_information": f"/property-information/{slug}",
            "moving_services": f"/moving-services/{slug}",
            "expert_tips": f"/expert-tips/{slug}",
            "suggestions": f"/admin/suggestions/{slug}",
            "report": f"/admin/reports/{slug}",
            "moving-services-register-inquiry": f"/admin/inquiries/{slug}",
            "expert-tips-register-inquiry": f"/admin/inquiries/{slug}",
        }

        return route_mapping.get(page_type, f"/post/{slug}")
