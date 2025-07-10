"""Posts service layer for business logic."""

from typing import List, Dict, Any, Optional
from nadle_backend.models.core import User, Post, PostCreate, PostUpdate, PostResponse, PaginatedResponse, PostMetadata, UserReaction, Comment
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.exceptions.post import PostNotFoundError, PostPermissionError
from nadle_backend.utils.permissions import check_post_permission


class PostsService:
    """Service layer for post-related business logic."""
    
    def __init__(self, post_repository: PostRepository = None, comment_repository: CommentRepository = None):
        """Initialize posts service with dependencies.
        
        Args:
            post_repository: Post repository instance
            comment_repository: Comment repository instance
        """
        self.post_repository = post_repository or PostRepository()
        self.comment_repository = comment_repository or CommentRepository()
    
    async def create_post(self, post_data: PostCreate, current_user: User) -> Post:
        """Create a new post.
        
        Args:
            post_data: Post creation data
            current_user: Current authenticated user
            
        Returns:
            Created post instance
        """
        # Ensure metadata has type field
        if not post_data.metadata:
            post_data.metadata = PostMetadata(type="board", category="입주 정보")
        elif not post_data.metadata.type:
            post_data.metadata.type = "board"
            if not post_data.metadata.category:
                post_data.metadata.category = "입주 정보"
            
        # Create post with current user as author
        post = await self.post_repository.create(post_data, str(current_user.id))
        return post
    
    async def get_post(self, slug_or_id: str, current_user: Optional[User] = None) -> Post:
        """Get post by slug or post ID with Redis caching.
        
        Args:
            slug_or_id: Post slug or post ID
            current_user: Current user (optional)
            
        Returns:
            Post instance
            
        Raises:
            PostNotFoundError: If post not found
        """
        # 🚀 Redis 캐시 확인
        from nadle_backend.database.redis import get_redis_manager
        redis_manager = await get_redis_manager()
        
        cache_key = f"post_detail:{slug_or_id}"
        cached_post = await redis_manager.get(cache_key)
        
        if cached_post:
            print(f"📦 Redis 캐시 적중 - {slug_or_id}")
            # 캐시된 데이터에서 Post 객체 재구성
            try:
                from nadle_backend.models.core import Post, PostMetadata, PostStatus, ServiceType
                from datetime import datetime
                from bson import ObjectId
                
                # 캐시된 딕셔너리에서 Post 객체 재구성
                metadata = None
                if cached_post.get("metadata"):
                    metadata = PostMetadata(**cached_post["metadata"])
                
                post = Post(
                    id=ObjectId(cached_post["id"]),
                    title=cached_post["title"],
                    content=cached_post["content"],
                    slug=cached_post["slug"],
                    author_id=ObjectId(cached_post["author_id"]),
                    service=ServiceType(cached_post["service"]),
                    metadata=metadata,
                    status=PostStatus(cached_post["status"]),
                    view_count=cached_post["view_count"],
                    like_count=cached_post["like_count"],
                    dislike_count=cached_post["dislike_count"],
                    comment_count=cached_post["comment_count"],
                    bookmark_count=cached_post["bookmark_count"],
                    created_at=datetime.fromisoformat(cached_post["created_at"]),
                    updated_at=datetime.fromisoformat(cached_post["updated_at"]) if cached_post.get("updated_at") else None,
                    published_at=datetime.fromisoformat(cached_post["published_at"]) if cached_post.get("published_at") else None
                )
                
                # 조회수만 증가 (캐시는 유지)
                await self.post_repository.increment_view_count(str(post.id))
                post.view_count += 1  # 메모리상 객체도 업데이트
                
                return post
                
            except Exception as e:
                print(f"⚠️ 캐시 데이터 파싱 실패: {e}, DB에서 조회")
                # 캐시 파싱 실패 시 캐시 삭제하고 DB에서 조회
                await redis_manager.delete(cache_key)
        
        # 캐시 미스 - DB에서 조회
        print(f"💾 DB에서 조회 - {slug_or_id}")
        try:
            post = await self.post_repository.get_by_slug(slug_or_id)
        except PostNotFoundError:
            # If slug lookup fails, try by ID
            try:
                post = await self.post_repository.get_by_id(slug_or_id)
            except PostNotFoundError:
                raise PostNotFoundError(f"Post not found with slug or ID: {slug_or_id}")
        
        # Increment view count
        print(f"Incrementing view count for post {post.id}")
        result = await self.post_repository.increment_view_count(str(post.id))
        print(f"View count increment result: {result}")
        
        # 🚀 Redis에 캐싱 (5분 TTL)
        try:
            cache_data = {
                "id": str(post.id),
                "title": post.title,
                "content": post.content,
                "slug": post.slug,
                "author_id": str(post.author_id),
                "service": post.service.value if post.service else "content",
                "metadata": post.metadata.model_dump() if post.metadata else {},
                "status": post.status.value if post.status else "published",
                "view_count": post.view_count + 1,  # 증가된 조회수 반영
                "like_count": post.like_count,
                "dislike_count": post.dislike_count,
                "comment_count": post.comment_count,
                "bookmark_count": post.bookmark_count,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                "published_at": post.published_at.isoformat() if post.published_at else None
            }
            
            success = await redis_manager.set(cache_key, cache_data, ttl=600)  # 10분 캐시 (Phase 2 개선)
            if success:
                print(f"📦 Redis 캐시 저장 성공 - {slug_or_id}")
            else:
                print(f"⚠️ Redis 캐시 저장 실패 - {slug_or_id}")
                
        except Exception as e:
            print(f"⚠️ Redis 캐시 저장 오류: {e}")
        
        return post
    
    async def list_posts(
        self,
        page: int = 1,
        page_size: int = 20,
        service_type: Optional[str] = None,
        metadata_type: Optional[str] = None,
        author_id: Optional[str] = None,
        sort_by: str = "created_at",
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """최적화된 게시글 목록 조회 (52개 쿼리 → 1개 쿼리).
        
        Args:
            page: Page number
            page_size: Items per page
            service_type: Filter by service type (현재 미사용, 호환성 유지)
            metadata_type: Filter by metadata type (property_information, moving services, expert_tips, board)
            author_id: Filter by author ID (현재 미사용, 호환성 유지)
            sort_by: Sort field
            current_user: Current user (optional, 사용자 반응 조회용)
            
        Returns:
            Paginated response with posts
        """
        # 디버깅을 위한 로그 추가
        print(f"📋 List posts request - metadata_type: '{metadata_type}', page: {page}, page_size: {page_size}")
        
        # 🚀 단일 aggregation 쿼리로 모든 데이터 조회
        posts_data, total = await self.post_repository.list_posts_optimized(
            page=page,
            page_size=page_size,
            metadata_type=metadata_type,
            sort_by=sort_by
        )
        
        print(f"📊 List posts results - found {total} posts, returned {len(posts_data)} items")
        
        # 🔥 기존 비효율적인 코드 완전 제거:
        # - get_authors_by_ids() 호출 제거 (이미 $lookup으로 조인됨)
        # - _calculate_post_stats() 호출 제거 (Post 모델의 기존 데이터 사용)
        # - UserReaction.find().count() 등 실시간 계산 제거
        
        # 사용자 반응 정보 조회 (필요한 경우에만)
        user_reactions = {}
        if current_user and posts_data:
            post_ids = [str(post_data["_id"]) for post_data in posts_data]
            user_reactions = await self.post_repository.get_user_reactions(
                str(current_user.id), post_ids
            )
        
        # ✅ 최적화된 데이터 변환 (이미 조인된 데이터 활용)
        formatted_posts = []
        for post_data in posts_data:
            print(f"📋 처리 중인 게시글: {post_data.get('title', 'Unknown')}")
            if "author" in post_data:
                print(f"👤 작성자 정보 있음: {post_data['author']}")
            else:
                print(f"❌ 작성자 정보 없음 - author_id: {post_data.get('author_id')}")
            # 기본 데이터 변환
            post_dict = {
                "_id": str(post_data["_id"]),
                "title": post_data["title"],
                "content": post_data["content"],
                "slug": post_data["slug"],
                "author_id": str(post_data["author_id"]),
                "created_at": post_data["created_at"].isoformat() if post_data.get("created_at") else None,
                "updated_at": post_data["updated_at"].isoformat() if post_data.get("updated_at") else None,
                "metadata": post_data.get("metadata", {}),
            }
            
            # ✅ Post 모델의 기존 통계 데이터 사용 (별도 계산 없음)
            post_dict["stats"] = {
                "view_count": post_data.get("view_count", 0),
                "like_count": post_data.get("like_count", 0),
                "dislike_count": post_data.get("dislike_count", 0),
                "comment_count": post_data.get("comment_count", 0),
                "bookmark_count": post_data.get("bookmark_count", 0)
            }
            
            # 🚀 moving services 타입의 경우 문의/후기 통계 추가
            if metadata_type == "moving services":
                try:
                    comment_stats = await self.comment_repository.get_comment_stats_by_post(str(post_data["_id"]))
                    post_dict["service_stats"] = {
                        "views": post_data.get("view_count", 0),
                        "bookmarks": post_data.get("bookmark_count", 0),
                        "inquiries": comment_stats.get("service_inquiry", 0),
                        "reviews": comment_stats.get("service_review", 0)
                    }
                    print(f"📊 Service stats for {post_data.get('title')}: {post_dict['service_stats']}")
                except Exception as e:
                    print(f"⚠️ Error getting comment stats: {e}")
                    # 에러 발생 시 기본값 사용
                    post_dict["service_stats"] = {
                        "views": post_data.get("view_count", 0),
                        "bookmarks": post_data.get("bookmark_count", 0),
                        "inquiries": 0,
                        "reviews": 0
                    }
            
            # ✅ 이미 $lookup으로 조인된 작성자 정보 사용 (별도 쿼리 없음)
            if "author" in post_data and post_data["author"]:
                author = post_data["author"]
                # 작성자 정보에서 표시명을 우선순위에 따라 결정
                display_name = author.get("display_name") or author.get("name") or author.get("user_handle") or "익명 사용자"
                user_handle = author.get("user_handle") or "익명"
                name = author.get("name") or "익명"
                
                post_dict["author"] = {
                    "id": str(author["_id"]),
                    "email": author.get("email", ""),
                    "user_handle": user_handle,
                    "display_name": display_name,
                    "name": name,
                    "created_at": author["created_at"].isoformat() if author.get("created_at") else None,
                    "updated_at": author["updated_at"].isoformat() if author.get("updated_at") else None
                }
                print(f"✅ 작성자 정보 설정됨: {display_name} ({user_handle})")
            else:
                # 작성자 정보가 없는 경우 기본 정보 제공
                print(f"⚠️ 작성자 정보 없음 - author_id: {post_data.get('author_id')}")
                post_dict["author"] = {
                    "id": str(post_data.get("author_id", "")),
                    "email": "",
                    "user_handle": "익명",
                    "display_name": "익명 사용자",
                    "name": "익명",
                    "created_at": None,
                    "updated_at": None
                }
            
            # 사용자 반응 추가 (있는 경우)
            post_id = str(post_data["_id"])
            if post_id in user_reactions:
                post_dict["user_reaction"] = user_reactions[post_id]
                
            formatted_posts.append(post_dict)
        
        # 페이지네이션 정보 계산
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": formatted_posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def update_post(
        self, 
        slug: str, 
        update_data: PostUpdate, 
        current_user: User
    ) -> Post:
        """Update post.
        
        Args:
            slug: Post slug
            update_data: Update data
            current_user: Current authenticated user
            
        Returns:
            Updated post instance
            
        Raises:
            PostNotFoundError: If post not found
            PostPermissionError: If user doesn't have permission
        """
        # Get post
        post = await self.post_repository.get_by_slug(slug)
        
        # Check permissions
        if not check_post_permission(current_user, post, "update"):
            raise PostPermissionError("You don't have permission to update this post")
        
        # Update post
        updated_post = await self.post_repository.update(str(post.id), update_data)
        return updated_post
    
    async def delete_post(self, slug: str, current_user: User) -> bool:
        """Delete post.
        
        Args:
            slug: Post slug
            current_user: Current authenticated user
            
        Returns:
            True if deletion successful
            
        Raises:
            PostNotFoundError: If post not found
            PostPermissionError: If user doesn't have permission
        """
        # Get post
        post = await self.post_repository.get_by_slug(slug)
        
        # Check permissions
        if not check_post_permission(current_user, post, "delete"):
            raise PostPermissionError("You don't have permission to delete this post")
        
        # Delete post
        result = await self.post_repository.delete(str(post.id))
        return result
    
    async def search_posts(
        self,
        query: str,
        service_type: Optional[str] = None,
        metadata_type: Optional[str] = None,
        sort_by: str = "created_at",
        page: int = 1,
        page_size: int = 20,
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Search posts.
        
        Args:
            query: Search query
            service_type: Filter by service type
            sort_by: Sort field
            page: Page number
            page_size: Items per page
            current_user: Current user (optional)
            
        Returns:
            Paginated search results
        """
        # 디버깅을 위한 로그 추가
        print(f"🔍 Search request - query: '{query}', metadata_type: '{metadata_type}', service_type: '{service_type}'")
        
        # Search posts
        posts, total = await self.post_repository.search_posts(
            query=query,
            service_type=service_type,
            metadata_type=metadata_type,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
        
        print(f"📊 Search results - found {total} posts, returned {len(posts)} items")
        
        # Format posts with stats
        formatted_posts = []
        for post in posts:
            post_dict = post.model_dump()
            
            # Convert ObjectIds to strings
            post_dict["_id"] = str(post.id)
            post_dict["author_id"] = str(post.author_id)
            
            # ✅ Use denormalized stats from Post model (no real-time calculation)
            post_dict["stats"] = {
                "view_count": post.view_count,
                "like_count": post.like_count,
                "dislike_count": post.dislike_count,
                "comment_count": post.comment_count,
                "bookmark_count": post.bookmark_count
            }
            
            formatted_posts.append(post_dict)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": formatted_posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    
    async def toggle_post_reaction(
        self,
        slug_or_id: str,
        reaction_type: str,  # "like", "dislike", or "bookmark"
        current_user: User
    ) -> Dict[str, Any]:
        """Toggle post reaction (like/dislike/bookmark) for a user.
        
        Args:
            slug_or_id: Post slug or ID
            reaction_type: "like", "dislike", or "bookmark"
            current_user: Authenticated user
            
        Returns:
            Dict with reaction counts and user reaction state
            
        Raises:
            PostNotFoundError: If post not found
        """
        # Get post by slug or ID (using same logic as get_post method)
        try:
            post = await self.post_repository.get_by_slug(slug_or_id)
        except PostNotFoundError:
            # If slug lookup fails, try by ID
            try:
                post = await self.post_repository.get_by_id(slug_or_id)
            except PostNotFoundError:
                raise PostNotFoundError(f"Post not found with slug or ID: {slug_or_id}")
        post_id = str(post.id)
        
        # Find or create user reaction
        user_reaction = await UserReaction.find_one({
            "user_id": str(current_user.id),
            "target_type": "post",
            "target_id": post_id
        })
        
        # 이전 반응 상태 저장 (Post 카운트 업데이트용)
        old_liked = user_reaction.liked if user_reaction else False
        old_disliked = user_reaction.disliked if user_reaction else False
        old_bookmarked = user_reaction.bookmarked if user_reaction else False
        
        if not user_reaction:
            # Generate route path for the post
            raw_page_type = getattr(post.metadata, "type", "board") if post.metadata else "board"
            # Normalize page type before generating route
            from nadle_backend.services.user_activity_service import normalize_post_type
            normalized_page_type = normalize_post_type(raw_page_type) or "board"
            route_path = self._generate_route_path(normalized_page_type, post.slug)
            
            user_reaction = UserReaction(
                user_id=str(current_user.id),
                target_type="post",
                target_id=post_id,
                metadata={
                    "route_path": route_path,
                    "target_title": post.title
                }
            )
        
        # Toggle reaction
        if reaction_type == "like":
            # Toggle like, clear dislike if setting like
            was_liked = user_reaction.liked
            user_reaction.liked = not was_liked
            if user_reaction.liked:
                user_reaction.disliked = False
        elif reaction_type == "dislike":
            # Toggle dislike, clear like if setting dislike
            was_disliked = user_reaction.disliked
            user_reaction.disliked = not was_disliked
            if user_reaction.disliked:
                user_reaction.liked = False
        elif reaction_type == "bookmark":
            # Toggle bookmark (independent of like/dislike)
            user_reaction.bookmarked = not user_reaction.bookmarked
        
        # Save user reaction
        await user_reaction.save()
        
        # Post 모델의 카운트 필드 업데이트
        count_updates = {}
        
        # 좋아요 카운트 변경 계산
        if old_liked != user_reaction.liked:
            count_updates["like_count"] = 1 if user_reaction.liked else -1
        
        # 싫어요 카운트 변경 계산
        if old_disliked != user_reaction.disliked:
            count_updates["dislike_count"] = 1 if user_reaction.disliked else -1
        
        # 북마크 카운트 변경 계산
        if old_bookmarked != user_reaction.bookmarked:
            count_updates["bookmark_count"] = 1 if user_reaction.bookmarked else -1
        
        # Post 모델의 카운트 필드 업데이트
        if count_updates:
            await self.post_repository.update_post_counts(post_id, count_updates)
        
        # 업데이트된 Post 데이터 다시 조회
        updated_post = await self.post_repository.get_by_id(post_id)
        
        return {
            "like_count": updated_post.like_count or 0,
            "dislike_count": updated_post.dislike_count or 0,
            "bookmark_count": updated_post.bookmark_count or 0,
            "user_reaction": {
                "liked": user_reaction.liked,
                "disliked": user_reaction.disliked,
                "bookmarked": user_reaction.bookmarked
            }
        }
    
    def _generate_route_path(self, page_type: str, slug: str) -> str:
        """Generate route path based on page type and slug.
        
        Args:
            page_type: Page type (can be raw DB type or normalized type)
            slug: Post slug
            
        Returns:
            Route path string
        """
        # Normalize page type first
        from nadle_backend.services.user_activity_service import normalize_post_type
        normalized_type = normalize_post_type(page_type) or "board"
        
        route_mapping = {
            "board": f"/board/{slug}",
            "property_information": f"/property-information/{slug}",
            "moving_services": f"/moving-services/{slug}",
            "expert_tips": f"/expert-tips/{slug}"
        }
        
        return route_mapping.get(normalized_type, f"/post/{slug}")
    
    async def get_service_post_with_extended_stats(
        self, 
        slug_or_id: str, 
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """입주 서비스 업체 게시글을 확장 통계와 함께 조회.
        
        Args:
            slug_or_id: 게시글 slug 또는 ID
            current_user: 현재 사용자 (선택적)
            
        Returns:
            확장된 통계 정보를 포함한 게시글 데이터
            
        Raises:
            PostNotFoundError: 게시글을 찾을 수 없거나 입주 서비스 업체 게시글이 아닌 경우
        """
        # 기본 게시글 정보 조회
        post = await self.get_post(slug_or_id, current_user)
        
        return await self.get_service_post_with_extended_stats_from_post(post, current_user)
    
    async def get_service_post_with_extended_stats_from_post(
        self, 
        post: Post, 
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """이미 조회된 Post 객체로부터 입주 서비스 업체 게시글을 확장 통계와 함께 반환.
        
        Args:
            post: 이미 조회된 Post 객체
            current_user: 현재 사용자 (선택적)
            
        Returns:
            확장된 통계 정보를 포함한 게시글 데이터
            
        Raises:
            PostNotFoundError: 입주 서비스 업체 게시글이 아닌 경우
        """
        
        # 입주 서비스 업체 게시글인지 확인
        if not (post.metadata and post.metadata.type == "moving services"):
            raise PostNotFoundError("입주 서비스 업체 게시글이 아닙니다")
        
        # 댓글 통계 조회
        comment_repository = CommentRepository()
        comment_stats = await comment_repository.get_comment_stats_by_post(str(post.id))
        
        # 기본 stats에 확장 통계 추가
        extended_stats = {
            # 기존 통계 유지
            "view_count": post.view_count or 0,
            "like_count": post.like_count or 0,
            "dislike_count": post.dislike_count or 0,
            "comment_count": post.comment_count or 0,
            "bookmark_count": post.bookmark_count or 0,
            
            # 확장 통계 추가
            "inquiry_count": comment_stats["service_inquiry"],
            "review_count": comment_stats["service_review"],
            "general_comment_count": comment_stats["general"]
        }
        
        # Get user reaction if authenticated
        user_reaction = None
        if current_user:
            from nadle_backend.models.core import UserReaction
            reaction = await UserReaction.find_one({
                "user_id": str(current_user.id),
                "target_type": "post",
                "target_id": str(post.id)
            })
            if reaction:
                user_reaction = {
                    "liked": reaction.liked,
                    "disliked": reaction.disliked,
                    "bookmarked": reaction.bookmarked
                }

        # Get author information
        author_info = None
        try:
            author = await User.get(post.author_id)
            if author:
                author_info = {
                    "id": str(author.id),
                    "user_handle": author.user_handle,
                    "display_name": author.display_name,
                    "name": author.name
                }
        except Exception as e:
            print(f"Failed to get author info: {e}")
            author_info = {
                "id": str(post.author_id),
                "user_handle": "익명",
                "display_name": "익명",
                "name": "익명"
            }

        # Post 객체를 딕셔너리로 수동 변환 (ObjectId 직렬화 문제 해결)
        post_dict = {
            "_id": str(post.id),
            "id": str(post.id),  # 프론트엔드 호환성을 위한 id 필드 추가
            "title": post.title,
            "content": post.content,
            "slug": post.slug,
            "service": post.service,
            "metadata": post.metadata.model_dump() if post.metadata else None,
            "file_ids": post.metadata.file_ids if post.metadata else [],  # 파일 IDs 추가
            "author_id": str(post.author_id),
            "author": author_info,  # 작성자 정보 추가
            "status": post.status,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "stats": extended_stats,
            # 기본 통계 필드들 추가 (프론트엔드 convertPostToService 함수 호환성을 위해)
            "view_count": post.view_count or 0,
            "like_count": post.like_count or 0,
            "dislike_count": post.dislike_count or 0,
            "comment_count": post.comment_count or 0,
            "bookmark_count": post.bookmark_count or 0
        }

        if user_reaction:
            post_dict["user_reaction"] = user_reaction
        
        return post_dict

    async def list_service_posts_with_extended_stats(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """입주 서비스 업체 게시글 목록을 확장 통계와 함께 조회.
        
        Args:
            page: 페이지 번호
            page_size: 페이지당 항목 수
            sort_by: 정렬 기준
            current_user: 현재 사용자 (선택적)
            
        Returns:
            확장된 통계 정보를 포함한 게시글 목록
        """
        print(f"📋 List service posts with extended stats - page: {page}, page_size: {page_size}")
        
        # 서비스 게시글 목록 조회
        result = await self.list_posts(
            page=page,
            page_size=page_size,
            metadata_type="moving services",
            sort_by=sort_by,
            current_user=current_user
        )
        
        if not result.get("items"):
            print("⚠️ No service posts found")
            return result
        
        # 각 게시글에 대해 확장 통계 추가
        comment_repository = CommentRepository()
        enhanced_items = []
        
        for post_dict in result["items"]:
            try:
                # 게시글 ID 추출
                post_id = post_dict.get("_id") or post_dict.get("id")
                if not post_id:
                    print(f"⚠️ Post ID not found in: {post_dict}")
                    enhanced_items.append(post_dict)
                    continue
                
                # 댓글 통계 조회
                comment_stats = await comment_repository.get_comment_stats_by_post(str(post_id))
                
                # 확장 통계 추가
                post_dict["extended_stats"] = {
                    "view_count": post_dict.get("view_count", 0),
                    "like_count": post_dict.get("like_count", 0),
                    "dislike_count": post_dict.get("dislike_count", 0),
                    "comment_count": post_dict.get("comment_count", 0),
                    "bookmark_count": post_dict.get("bookmark_count", 0),
                    "inquiry_count": comment_stats["service_inquiry"],
                    "review_count": comment_stats["service_review"],
                    "general_comment_count": comment_stats["general"]
                }
                
                enhanced_items.append(post_dict)
                print(f"✅ Enhanced post {post_id} with extended stats: {comment_stats}")
                
            except Exception as e:
                print(f"❌ Error adding extended stats for post: {e}")
                enhanced_items.append(post_dict)  # 오류 발생 시 기본 데이터라도 반환
        
        # 결과 업데이트
        result["items"] = enhanced_items
        print(f"📊 Enhanced {len(enhanced_items)} service posts with extended stats")
        
        return result
    
    # ================================
    # 🚀 1단계: 스마트 캐싱 메서드들
    # ================================
    
    async def get_author_info_cached(self, author_id: str) -> Optional[Dict[str, Any]]:
        """작성자 정보 캐시된 조회
        
        Args:
            author_id: 작성자 ID
            
        Returns:
            작성자 정보 딕셔너리 또는 None
        """
        from nadle_backend.database.redis import get_redis_manager
        from nadle_backend.models.core import User
        
        redis_manager = await get_redis_manager()
        cache_key = f"author_info:{author_id}"
        
        # 캐시에서 조회
        cached_author = await redis_manager.get(cache_key)
        if cached_author:
            print(f"📦 작성자 정보 캐시 적중 - {author_id}")
            return cached_author
        
        # DB에서 조회 후 캐싱
        try:
            from bson import ObjectId
            # ObjectId 형식으로 변환
            if len(author_id) == 24:
                author = await User.get(ObjectId(author_id))
            else:
                author = await User.find_one({"user_handle": author_id})
            
            if author:
                author_info = {
                    "id": str(author.id),
                    "user_handle": author.user_handle,
                    "display_name": author.display_name,
                    "name": author.name,
                    "email": author.email if hasattr(author, 'email') else ""
                }
                
                # 캐시에 저장 (TTL: 1시간)
                await redis_manager.set(cache_key, author_info, ttl=3600)
                print(f"💾 작성자 정보 캐시 저장 - {author_id}")
                return author_info
        except Exception as e:
            print(f"❌ 작성자 정보 조회 실패: {e}")
            # 기본값 반환
            return {
                "id": str(author_id),
                "user_handle": "익명",
                "display_name": "익명",
                "name": "익명",
                "email": ""
            }
        
        return None
    
    async def get_user_reaction_cached(self, user_id: str, post_id: str) -> Optional[Dict[str, bool]]:
        """사용자 반응 정보 캐시된 조회
        
        Args:
            user_id: 사용자 ID
            post_id: 게시글 ID
            
        Returns:
            사용자 반응 정보 딕셔너리 또는 None
        """
        from nadle_backend.database.redis import get_redis_manager
        from nadle_backend.models.core import UserReaction
        
        redis_manager = await get_redis_manager()
        cache_key = f"user_reaction:{user_id}:{post_id}"
        
        # 캐시에서 조회
        cached_reaction = await redis_manager.get(cache_key)
        if cached_reaction:
            print(f"📦 사용자 반응 캐시 적중 - {user_id}:{post_id}")
            return cached_reaction
        
        # DB에서 조회 후 캐싱
        try:
            reaction = await UserReaction.find_one({
                "user_id": user_id,
                "target_type": "post",
                "target_id": post_id
            })
            
            if reaction:
                reaction_info = {
                    "liked": reaction.liked,
                    "disliked": reaction.disliked,
                    "bookmarked": reaction.bookmarked
                }
            else:
                reaction_info = {
                    "liked": False,
                    "disliked": False,
                    "bookmarked": False
                }
            
            # 캐시에 저장 (TTL: 30분)
            await redis_manager.set(cache_key, reaction_info, ttl=1800)
            print(f"💾 사용자 반응 캐시 저장 - {user_id}:{post_id}")
            return reaction_info
            
        except Exception as e:
            print(f"❌ 사용자 반응 조회 실패: {e}")
            return {
                "liked": False,
                "disliked": False,
                "bookmarked": False
            }
    
    async def invalidate_author_cache(self, author_id: str) -> None:
        """작성자 정보 캐시 무효화
        
        Args:
            author_id: 작성자 ID
        """
        from nadle_backend.database.redis import get_redis_manager
        
        redis_manager = await get_redis_manager()
        cache_key = f"author_info:{author_id}"
        
        await redis_manager.delete(cache_key)
        print(f"🗑️ 작성자 정보 캐시 무효화 - {author_id}")
    
    async def invalidate_user_reaction_cache(self, user_id: str, post_id: str) -> None:
        """사용자 반응 캐시 무효화
        
        Args:
            user_id: 사용자 ID
            post_id: 게시글 ID
        """
        from nadle_backend.database.redis import get_redis_manager
        
        redis_manager = await get_redis_manager()
        cache_key = f"user_reaction:{user_id}:{post_id}"
        
        await redis_manager.delete(cache_key)
        print(f"🗑️ 사용자 반응 캐시 무효화 - {user_id}:{post_id}")
    
    # ================================
    # 🚀 2단계: 배치 조회 메서드들
    # ================================
    
    async def get_authors_info_batch(self, author_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """작성자 정보 배치 조회
        
        Args:
            author_ids: 작성자 ID 목록
            
        Returns:
            {author_id: author_info} 딕셔너리
        """
        from nadle_backend.database.redis import get_redis_manager
        from nadle_backend.models.core import User
        from bson import ObjectId
        
        redis_manager = await get_redis_manager()
        result = {}
        uncached_ids = []
        
        # 1. 캐시에서 먼저 조회
        for author_id in author_ids:
            cache_key = f"author_info:{author_id}"
            cached_author = await redis_manager.get(cache_key)
            
            if cached_author:
                result[author_id] = cached_author
                print(f"📦 작성자 정보 캐시 적중 - {author_id}")
            else:
                uncached_ids.append(author_id)
        
        # 2. 캐시되지 않은 것들을 배치로 DB 조회
        if uncached_ids:
            try:
                # ObjectId 형식으로 변환
                object_ids = []
                for author_id in uncached_ids:
                    if len(author_id) == 24:
                        try:
                            object_ids.append(ObjectId(author_id))
                        except:
                            print(f"❌ 잘못된 ObjectId 형식: {author_id}")
                            continue
                
                if object_ids:
                    # 배치 조회
                    authors = await User.find({"_id": {"$in": object_ids}}).to_list()
                    print(f"🔄 배치 조회: {len(object_ids)}개 요청 → {len(authors)}개 결과")
                    
                    # 결과 처리 및 캐싱
                    for author in authors:
                        author_id = str(author.id)
                        author_info = {
                            "id": author_id,
                            "user_handle": author.user_handle,
                            "display_name": author.display_name,
                            "name": author.name,
                            "email": author.email if hasattr(author, 'email') else ""
                        }
                        
                        result[author_id] = author_info
                        
                        # 개별 캐싱 (TTL: 1시간)
                        cache_key = f"author_info:{author_id}"
                        await redis_manager.set(cache_key, author_info, ttl=3600)
                        print(f"💾 작성자 정보 캐시 저장 - {author_id}")
                
            except Exception as e:
                print(f"❌ 배치 작성자 조회 실패: {e}")
        
        return result
    
    async def get_user_reactions_batch(self, user_id: str, post_ids: List[str]) -> Dict[str, Dict[str, bool]]:
        """사용자 반응 배치 조회
        
        Args:
            user_id: 사용자 ID
            post_ids: 게시글 ID 목록
            
        Returns:
            {post_id: reaction_info} 딕셔너리
        """
        from nadle_backend.database.redis import get_redis_manager
        from nadle_backend.models.core import UserReaction
        
        redis_manager = await get_redis_manager()
        result = {}
        uncached_post_ids = []
        
        # 1. 캐시에서 먼저 조회
        for post_id in post_ids:
            cache_key = f"user_reaction:{user_id}:{post_id}"
            cached_reaction = await redis_manager.get(cache_key)
            
            if cached_reaction:
                result[post_id] = cached_reaction
                print(f"📦 사용자 반응 캐시 적중 - {user_id}:{post_id}")
            else:
                uncached_post_ids.append(post_id)
        
        # 2. 캐시되지 않은 것들을 배치로 DB 조회
        if uncached_post_ids:
            try:
                # 배치 조회
                reactions = await UserReaction.find({
                    "user_id": user_id,
                    "target_type": "post",
                    "target_id": {"$in": uncached_post_ids}
                }).to_list()
                
                print(f"🔄 사용자 반응 배치 조회: {len(uncached_post_ids)}개 요청 → {len(reactions)}개 결과")
                
                # 존재하는 반응들 처리
                found_post_ids = set()
                for reaction in reactions:
                    post_id = reaction.target_id
                    reaction_info = {
                        "liked": reaction.liked,
                        "disliked": reaction.disliked,
                        "bookmarked": reaction.bookmarked
                    }
                    
                    result[post_id] = reaction_info
                    found_post_ids.add(post_id)
                    
                    # 캐싱 (TTL: 30분)
                    cache_key = f"user_reaction:{user_id}:{post_id}"
                    await redis_manager.set(cache_key, reaction_info, ttl=1800)
                    print(f"💾 사용자 반응 캐시 저장 - {user_id}:{post_id}")
                
                # 반응이 없는 게시글들은 기본값으로 처리
                for post_id in uncached_post_ids:
                    if post_id not in found_post_ids:
                        default_reaction = {
                            "liked": False,
                            "disliked": False,
                            "bookmarked": False
                        }
                        result[post_id] = default_reaction
                        
                        # 기본값도 캐싱 (TTL: 30분)
                        cache_key = f"user_reaction:{user_id}:{post_id}"
                        await redis_manager.set(cache_key, default_reaction, ttl=1800)
                        print(f"💾 기본 사용자 반응 캐시 저장 - {user_id}:{post_id}")
                
            except Exception as e:
                print(f"❌ 배치 사용자 반응 조회 실패: {e}")
                # 실패 시 기본값으로 채우기
                for post_id in uncached_post_ids:
                    result[post_id] = {
                        "liked": False,
                        "disliked": False,
                        "bookmarked": False
                    }
        
        return result
    
    async def get_comments_with_batch_authors(self, post_slug: str) -> List[Dict[str, Any]]:
        """댓글 목록과 작성자 정보를 배치로 조회 (Phase 2: 하이브리드 캐싱 적용)
        
        Args:
            post_slug: 게시글 slug
            
        Returns:
            작성자 정보가 포함된 댓글 목록
        """
        from nadle_backend.repositories.comment_repository import CommentRepository
        from nadle_backend.database.redis import get_redis_manager
        
        # 🚀 Phase 2: 댓글 캐싱 확인
        redis_manager = await get_redis_manager()
        cache_key = f"comments_batch_v2:{post_slug}"  # 캐시 키 버전 업
        
        # 캐시에서 조회 시도
        cached_comments = await redis_manager.get(cache_key)
        if cached_comments:
            print(f"📦 댓글 캐시 적중 - {post_slug}")
            return cached_comments
        
        print(f"🔍 댓글 캐시 미스 - DB에서 조회: {post_slug}")
        comment_repository = CommentRepository()
        
        # 1. 게시글 ID 조회
        post = await self.post_repository.get_by_slug(post_slug)
        if not post:
            return []
        
        # 2. 댓글 목록 조회 (답글 포함)
        from nadle_backend.config import get_settings
        settings = get_settings()
        comments_with_replies, _ = await comment_repository.get_comments_with_replies(
            post_id=str(post.id),
            page=1,
            page_size=100,  # 충분히 큰 값으로 설정
            status="active",
            max_depth=settings.max_comment_depth
        )
        
        if not comments_with_replies:
            return []
        
        # 2. 모든 댓글 ID 수집 (최상위 댓글 + 답글들)
        all_comments = []
        def collect_all_comments(item):
            comment = item["comment"]
            replies = item["replies"]
            all_comments.append(comment)
            for reply_item in replies:
                collect_all_comments(reply_item)
        
        for item in comments_with_replies:
            collect_all_comments(item)
        
        # 3. 작성자 ID 목록 추출
        author_ids = list(set([str(comment.author_id) for comment in all_comments if comment.author_id]))
        
        # 4. 작성자 정보 배치 조회
        authors_info = await self.get_authors_info_batch(author_ids)
        
        # 5. 댓글에 작성자 정보 결합 (재귀적으로 처리)
        def add_author_info_recursive(item):
            comment = item["comment"]
            replies = item["replies"]
            
            # 작성자 정보 추가
            comment_dict = {
                "id": str(comment.id),
                "content": comment.content,
                "author_id": comment.author_id,
                "parent_comment_id": comment.parent_comment_id,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
                "status": comment.status,
                "like_count": comment.like_count,
                "dislike_count": comment.dislike_count,
                "reply_count": comment.reply_count,
                "metadata": comment.metadata or {},
                "author": authors_info.get(str(comment.author_id)),
                "replies": [add_author_info_recursive(reply_item) for reply_item in replies]
            }
            return comment_dict
        
        # 6. 최상위 댓글들에 작성자 정보와 답글 구조 결합
        result = []
        for item in comments_with_replies:
            comment_with_author = add_author_info_recursive(item)
            result.append(comment_with_author)
        
        print(f"📊 배치 조회로 {len(all_comments)}개 댓글에 {len(authors_info)}명의 작성자 정보 결합 완료")
        
        # 🚀 Phase 2: 댓글 결과를 캐시에 저장 (TTL: 5분)
        try:
            await redis_manager.set(cache_key, result, ttl=300)  # 5분 TTL
            print(f"💾 댓글 배치 결과 캐시 저장 완료 - {post_slug}")
        except Exception as cache_error:
            print(f"⚠️ 댓글 캐시 저장 실패 (계속 진행): {cache_error}")
        
        return result
    
    # ================================
    # 🚀 3단계: MongoDB Aggregation Pipeline
    # ================================
    
    async def get_post_with_author_aggregated(self, post_slug: str) -> Optional[Dict[str, Any]]:
        """MongoDB Aggregation으로 게시글 + 작성자 정보 한 번에 조회
        
        Args:
            post_slug: 게시글 slug
            
        Returns:
            작성자 정보가 포함된 게시글 데이터
        """
        from nadle_backend.models.core import Post
        from nadle_backend.config import get_settings
        from bson import ObjectId
        
        try:
            settings = get_settings()
            
            # MongoDB Aggregation Pipeline - 단순화된 버전
            pipeline = [
                # 1. 해당 slug의 게시글 매칭
                {"$match": {"slug": post_slug, "status": {"$ne": "deleted"}}},
                
                # 2. author_id를 ObjectId로 변환 후 작성자 정보 JOIN (단순 조인)
                {"$lookup": {
                    "from": settings.users_collection,
                    "localField": "author_id", 
                    "foreignField": "_id",
                    "as": "author_info"
                }},
                
                # 3. 작성자 정보 단일 객체로 변환
                {"$addFields": {
                    "author": {"$arrayElemAt": ["$author_info", 0]}
                }},
                
                # 4. 필요한 필드만 선택 (단순화)
                {"$project": {
                    "_id": {"$toString": "$_id"},
                    "id": {"$toString": "$_id"},
                    "title": 1,
                    "content": 1,
                    "slug": 1,
                    "service": 1,
                    "metadata": 1,
                    "author_id": {"$toString": "$author_id"},
                    "author": {
                        "id": {"$toString": "$author._id"},
                        "user_handle": "$author.user_handle",
                        "display_name": "$author.display_name", 
                        "name": "$author.name",
                        "email": "$author.email"
                    },
                    "status": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "published_at": 1,
                    "view_count": 1,
                    "like_count": 1,
                    "dislike_count": 1,
                    "comment_count": 1,
                    "bookmark_count": 1
                }},
                
                # 5. 불필요한 필드 제거
                {"$unset": "author_info"}
            ]
            
            print(f"🔍 Aggregation Pipeline 실행 중: {post_slug}")
            
            # Aggregation 실행
            results = await Post.aggregate(pipeline).to_list()
            
            if results:
                result = results[0]
                print(f"🔄 Aggregation으로 게시글 + 작성자 정보 한 번에 조회 완료 - {post_slug}")
                return result
            else:
                print(f"❌ Aggregation: 게시글을 찾을 수 없음 - {post_slug}")
                return None
                
        except Exception as e:
            print(f"❌ Aggregation 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_post_with_comments_aggregated(self, post_slug: str) -> Optional[Dict[str, Any]]:
        """MongoDB Aggregation으로 게시글 + 댓글 + 작성자 정보 모두 한 번에 조회
        
        Args:
            post_slug: 게시글 slug
            
        Returns:
            댓글과 작성자 정보가 포함된 게시글 데이터
        """
        # 우선 단순한 방법으로 게시글만 먼저 조회해보자
        post_data = await self.get_post_with_author_aggregated(post_slug)
        if not post_data:
            return None
        
        # 댓글은 기존 배치 조회 방식 사용 (안정적)
        try:
            comments = await self.get_comments_with_batch_authors(post_slug)
            post_data["comments"] = comments
            
            print(f"🔄 Aggregation + 배치 조회로 게시글 + 댓글 + 작성자 정보 조회 완료 - {post_slug}")
            print(f"📊 조회된 댓글 수: {len(comments)}")
            return post_data
            
        except Exception as e:
            print(f"❌ 댓글 배치 조회 실패: {e}")
            # 댓글 없이라도 게시글 데이터는 반환
            post_data["comments"] = []
            return post_data
    
    async def get_post_with_everything_aggregated(self, post_slug: str, current_user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """MongoDB Aggregation으로 게시글 + 작성자 + 댓글 + 댓글작성자 + 사용자반응을 모두 한 번의 쿼리로 조회
        
        Args:
            post_slug: 게시글 slug
            current_user_id: 현재 사용자 ID (사용자 반응 조회용)
            
        Returns:
            모든 정보가 포함된 게시글 데이터
        """
        from nadle_backend.models.core import Post
        from nadle_backend.config import get_settings
        from bson import ObjectId
        
        try:
            settings = get_settings()
            
            print(f"🚀 완전 통합 Aggregation 파이프라인 실행 중: {post_slug}")
            
            # MongoDB Aggregation Pipeline - 기본 파이프라인
            pipeline = [
                # 1. 해당 slug의 게시글 매칭
                {"$match": {"slug": post_slug, "status": {"$ne": "deleted"}}},
                
                # 2. 게시글 작성자 정보 JOIN (author_id를 ObjectId로 변환 후 매칭)
                {"$lookup": {
                    "from": settings.users_collection,
                    "let": {"author_id": {"$toObjectId": "$author_id"}},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$author_id"]}}}
                    ],
                    "as": "author_info"
                }},
                
                # 3. 해당 게시글의 댓글들 JOIN
                {"$lookup": {
                    "from": settings.comments_collection,
                    "let": {"post_id": "$_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$post_id", "$$post_id"]},
                            "status": {"$ne": "deleted"}
                        }},
                        {"$sort": {"created_at": 1}}  # 댓글을 생성일순으로 정렬
                    ],
                    "as": "comments_raw"
                }},
                
                # 4. 각 댓글의 작성자 정보 JOIN
                {"$lookup": {
                    "from": settings.users_collection,
                    "localField": "comments_raw.author_id",
                    "foreignField": "_id",
                    "as": "comment_authors"
                }}
            ]
            
            # 5. 사용자 반응 정보 JOIN (현재 사용자가 있는 경우만)
            if current_user_id:
                pipeline.append({
                    "$lookup": {
                        "from": "user_reactions",  # UserReaction 컬렉션
                        "let": {"post_id": "$_id"},
                        "pipeline": [
                            {"$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$target_id", {"$toString": "$$post_id"}]},
                                        {"$eq": ["$target_type", "post"]},
                                        {"$eq": ["$user_id", current_user_id]}
                                    ]
                                }
                            }}
                        ],
                        "as": "user_reaction_raw"
                    }
                })
            
            # 6. 데이터 정리 및 구조화
            addfields_stage = {
                "$addFields": {
                    # 게시글 작성자 정보
                    "author": {"$arrayElemAt": ["$author_info", 0]},
                    
                    # 댓글과 댓글 작성자 정보 매핑
                    "comments": {
                        "$map": {
                            "input": "$comments_raw",
                            "as": "comment",
                            "in": {
                                "id": {"$toString": "$$comment._id"},
                                "_id": {"$toString": "$$comment._id"},
                                "content": "$$comment.content", 
                                "author_id": {"$toString": "$$comment.author_id"},
                                "post_id": {"$toString": "$$comment.post_id"},
                                "parent_id": {"$toString": "$$comment.parent_id"},
                                "status": "$$comment.status",
                                "created_at": "$$comment.created_at",
                                "updated_at": "$$comment.updated_at",
                                "like_count": "$$comment.like_count",
                                "dislike_count": "$$comment.dislike_count",
                                # 댓글 작성자 정보 매핑
                                "author": {
                                    "$let": {
                                        "vars": {
                                            "author": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$comment_authors",
                                                            "cond": {"$eq": ["$$this._id", "$$comment.author_id"]}
                                                        }
                                                    }, 0
                                                ]
                                            }
                                        },
                                        "in": {
                                            "id": {"$toString": "$$author._id"},
                                            "user_handle": "$$author.user_handle",
                                            "display_name": "$$author.display_name",
                                            "name": "$$author.name",
                                            "email": "$$author.email"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            # 사용자 반응 정보 추가 (있는 경우만)
            if current_user_id:
                addfields_stage["$addFields"]["user_reaction"] = {
                    "$let": {
                        "vars": {"reaction": {"$arrayElemAt": ["$user_reaction_raw", 0]}},
                        "in": {
                            "$cond": {
                                "if": {"$ne": ["$$reaction", None]},
                                "then": {
                                    "liked": "$$reaction.liked",
                                    "disliked": "$$reaction.disliked", 
                                    "bookmarked": "$$reaction.bookmarked"
                                },
                                "else": {
                                    "liked": False,
                                    "disliked": False,
                                    "bookmarked": False
                                }
                            }
                        }
                    }
                }
            
            pipeline.append(addfields_stage)
            
            # 7. 최종 출력 형태 정리
            project_stage = {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "id": {"$toString": "$_id"},
                    "title": 1,
                    "content": 1,
                    "slug": 1,
                    "service": 1,
                    "metadata": 1,
                    "author_id": {"$toString": "$author_id"},
                    "author": {
                        "id": {"$toString": "$author._id"},
                        "user_handle": "$author.user_handle",
                        "display_name": "$author.display_name", 
                        "name": "$author.name",
                        "email": "$author.email"
                    },
                    "status": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "published_at": 1,
                    "view_count": 1,
                    "like_count": 1,
                    "dislike_count": 1,
                    "comment_count": 1,
                    "bookmark_count": 1,
                    "stats": {
                        "view_count": "$view_count",
                        "like_count": "$like_count",
                        "dislike_count": "$dislike_count",
                        "comment_count": "$comment_count",
                        "bookmark_count": "$bookmark_count"
                    },
                    "comments": 1
                }
            }
            
            # 사용자 반응 필드 추가 (있는 경우만)
            if current_user_id:
                project_stage["$project"]["user_reaction"] = 1
            
            pipeline.append(project_stage)
            
            # 8. 불필요한 필드 제거
            pipeline.append({"$unset": ["author_info", "comments_raw", "comment_authors", "user_reaction_raw"]})
            
            print(f"🔍 완전 통합 Aggregation Pipeline 단계 수: {len(pipeline)}")
            
            # Aggregation 실행
            results = await Post.aggregate(pipeline).to_list()
            
            if results:
                result = results[0]
                print(f"✅ 완전 통합 Aggregation으로 모든 데이터 한 번에 조회 완료 - {post_slug}")
                print(f"📊 조회된 댓글 수: {len(result.get('comments', []))}")
                print(f"👤 게시글 작성자: {result.get('author', {}).get('user_handle', 'N/A')}")
                print(f"🎯 사용자 반응 포함: {'user_reaction' in result}")
                
                # 조회수 증가 (별도 처리)
                try:
                    await self.post_repository.increment_view_count(str(result["id"]))
                    result["view_count"] = result.get("view_count", 0) + 1
                    # stats 필드도 동시에 업데이트
                    if "stats" in result:
                        result["stats"]["view_count"] = result["view_count"]
                except Exception as e:
                    print(f"⚠️ 조회수 증가 실패: {e}")
                
                return result
            else:
                print(f"❌ 완전 통합 Aggregation: 게시글을 찾을 수 없음 - {post_slug}")
                return None
                
        except Exception as e:
            print(f"❌ 완전 통합 Aggregation 실패: {e}")
            import traceback
            traceback.print_exc()
            return None