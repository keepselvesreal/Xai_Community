"""Posts service layer for business logic."""

from typing import List, Dict, Any, Optional
from nadle_backend.models.core import User, Post, PostCreate, PostUpdate, PostResponse, PaginatedResponse, PostMetadata, UserReaction, Comment
from nadle_backend.repositories.post_repository import PostRepository
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
            metadata_type: Filter by metadata type (property-info, moving-service, expert-tip)
            author_id: Filter by author ID (현재 미사용, 호환성 유지)
            sort_by: Sort field
            current_user: Current user (optional, 사용자 반응 조회용)
            
        Returns:
            Paginated response with posts
        """
        # 🚀 단일 aggregation 쿼리로 모든 데이터 조회
        posts_data, total = await self.post_repository.list_posts_optimized(
            page=page,
            page_size=page_size,
            metadata_type=metadata_type,
            sort_by=sort_by
        )
        
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
                "comment_count": post_data.get("comment_count", 0)
            }
            
            # ✅ 이미 $lookup으로 조인된 작성자 정보 사용 (별도 쿼리 없음)
            if "author" in post_data and post_data["author"]:
                author = post_data["author"]
                post_dict["author"] = {
                    "id": str(author["_id"]),
                    "email": author["email"],
                    "user_handle": author["user_handle"],
                    "display_name": author["display_name"],
                    "created_at": author["created_at"].isoformat() if author.get("created_at") else None,
                    "updated_at": author["updated_at"].isoformat() if author.get("updated_at") else None
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
        # Search posts
        posts, total = await self.post_repository.search_posts(
            query=query,
            service_type=service_type,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
        
        # Format posts with stats
        formatted_posts = []
        for post in posts:
            post_dict = post.model_dump()
            
            # Convert ObjectIds to strings
            post_dict["_id"] = str(post.id)
            post_dict["author_id"] = str(post.author_id)
            
            # Calculate real-time stats from UserReaction and Comment collections
            real_stats = await self._calculate_post_stats(str(post.id))
            post_dict["stats"] = real_stats
            
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
    
    # 🔥 DEPRECATED: 비효율적인 실시간 통계 계산 함수 (52개 쿼리 원인)
    # 최적화로 인해 더 이상 사용하지 않음. Post 모델의 기존 통계 데이터 활용.
    # async def _calculate_post_stats(self, post_id: str) -> Dict[str, int]:
    #     """Calculate real-time statistics for a post.
    #     
    #     🚨 PERFORMANCE WARNING: 이 함수는 각 게시글마다 5개의 개별 쿼리를 실행하여
    #     N+1 쿼리 문제를 일으킴. 10개 게시글 조회시 50개 추가 쿼리 발생.
    #     
    #     ✅ 대신 Post 모델의 기존 통계 데이터(view_count, like_count 등) 사용.
    #     
    #     Args:
    #         post_id: Post ID
    #         
    #     Returns:
    #         Dictionary with current stats
    #     """
    #     try:
    #         # Get like count from UserReaction
    #         like_count = await UserReaction.find({
    #             "target_type": "post",
    #             "target_id": post_id,
    #             "liked": True
    #         }).count()
    #         
    #         # Get dislike count from UserReaction
    #         dislike_count = await UserReaction.find({
    #             "target_type": "post",
    #             "target_id": post_id,
    #             "disliked": True
    #         }).count()
    #         
    #         # Get bookmark count from UserReaction
    #         bookmark_count = await UserReaction.find({
    #             "target_type": "post",
    #             "target_id": post_id,
    #             "bookmarked": True
    #         }).count()
    #         
    #         # Get total comment count (including replies) from Comment
    #         comment_count = await Comment.find({
    #             "parent_id": post_id,
    #             "status": "active"
    #         }).count()
    #         
    #         # Get view count from Post document (maintained in post model)
    #         from beanie import PydanticObjectId
    #         post = await Post.find_one({"_id": PydanticObjectId(post_id)})
    #         view_count = post.view_count if post else 0
    #         
    #         return {
    #             "view_count": view_count,
    #             "like_count": like_count,
    #             "dislike_count": dislike_count,
    #             "comment_count": comment_count,
    #             "bookmark_count": bookmark_count
    #         }
    #         
    #     except Exception as e:
    #         import traceback
    #         print(f"Error calculating post stats for {post_id}: {e}")
    #         print(f"Traceback: {traceback.format_exc()}")
    #         # Re-raise the exception to see the actual error
    #         raise e
    
    async def toggle_post_reaction(
        self,
        slug_or_id: str,
        reaction_type: str,  # "like" or "dislike"
        current_user: User
    ) -> Dict[str, Any]:
        """Toggle post reaction (like/dislike) for a user.
        
        Args:
            slug_or_id: Post slug or ID
            reaction_type: "like" or "dislike"
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
        
        # Get updated stats
        updated_stats = await self._calculate_post_stats(post_id)
        
        return {
            "like_count": updated_stats["like_count"],
            "dislike_count": updated_stats["dislike_count"],
            "bookmark_count": updated_stats["bookmark_count"],
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