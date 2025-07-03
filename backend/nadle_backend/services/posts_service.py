"""Posts service layer for business logic."""

from typing import List, Dict, Any, Optional
from nadle_backend.models.core import User, Post, PostCreate, PostUpdate, PostResponse, PaginatedResponse, PostMetadata, UserReaction, Comment
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.exceptions.post import PostNotFoundError, PostPermissionError
from nadle_backend.utils.permissions import check_post_permission


class PostsService:
    """Service layer for post-related business logic."""
    
    def __init__(self, post_repository: PostRepository = None):
        """Initialize posts service with dependencies.
        
        Args:
            post_repository: Post repository instance
        """
        self.post_repository = post_repository or PostRepository()
    
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
        """Get post by slug or post ID.
        
        Args:
            slug_or_id: Post slug or post ID
            current_user: Current user (optional)
            
        Returns:
            Post instance
            
        Raises:
            PostNotFoundError: If post not found
        """
        # Try to get post by slug first, then by ID if that fails
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
            
            # ✅ 이미 $lookup으로 조인된 작성자 정보 사용 (별도 쿼리 없음)
            if "author" in post_data and post_data["author"]:
                author = post_data["author"]
                post_dict["author"] = {
                    "id": str(author["_id"]),
                    "email": author.get("email", ""),
                    "user_handle": author.get("user_handle", "익명"),
                    "display_name": author.get("display_name", ""),
                    "name": author.get("name", ""),
                    "created_at": author["created_at"].isoformat() if author.get("created_at") else None,
                    "updated_at": author["updated_at"].isoformat() if author.get("updated_at") else None
                }
            else:
                # 작성자 정보가 없는 경우 기본 정보 제공
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
            page_type = getattr(post.metadata, "type", "board") if post.metadata else "board"
            route_path = self._generate_route_path(page_type, post.slug)
            
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
            page_type: Page type (board, info, services, tips)
            slug: Post slug
            
        Returns:
            Route path string
        """
        route_mapping = {
            "board": f"/board-post/{slug}",
            "info": f"/property-info/{slug}",
            "services": f"/moving-services-post/{slug}",
            "tips": f"/expert-tips/{slug}"
        }
        
        return route_mapping.get(page_type, f"/post/{slug}")
    
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
        
        # Post 객체를 딕셔너리로 수동 변환 (ObjectId 직렬화 문제 해결)
        post_dict = {
            "_id": str(post.id),
            "id": str(post.id),  # 프론트엔드 호환성을 위한 id 필드 추가
            "title": post.title,
            "content": post.content,
            "slug": post.slug,
            "service": post.service,
            "metadata": post.metadata.model_dump() if post.metadata else None,
            "author_id": str(post.author_id),
            "status": post.status,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            # 기본 통계 필드들 추가 (프론트엔드 convertPostToService 함수 호환성을 위해)
            "view_count": post.view_count or 0,
            "like_count": post.like_count or 0,
            "dislike_count": post.dislike_count or 0,
            "comment_count": post.comment_count or 0,
            "bookmark_count": post.bookmark_count or 0,
            "extended_stats": extended_stats
        }
        
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