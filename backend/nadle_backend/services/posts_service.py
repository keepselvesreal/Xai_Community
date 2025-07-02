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
        """List posts with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            service_type: Filter by service type
            metadata_type: Filter by metadata type
            author_id: Filter by author ID
            sort_by: Sort field
            current_user: Current user (optional)
            
        Returns:
            Paginated response with posts
        """
        # Get posts from repository
        posts, total = await self.post_repository.list_posts(
            page=page,
            page_size=page_size,
            service_type=service_type,
            metadata_type=metadata_type,
            author_id=author_id,
            sort_by=sort_by
        )
        
        # Get user reactions if authenticated
        user_reactions = {}
        if current_user:
            post_ids = [str(post.id) for post in posts]
            user_reactions = await self.post_repository.get_user_reactions(
                str(current_user.id), post_ids
            )
        
        # Get author information for all posts
        author_ids = list(set(str(post.author_id) for post in posts))
        authors = await self.post_repository.get_authors_by_ids(author_ids)
        authors_dict = {str(author.id): author for author in authors}
        
        # Add user reaction data and author info to posts
        posts_with_reactions = []
        for post in posts:
            post_dict = post.model_dump()
            
            # Convert ObjectIds to strings
            post_dict["_id"] = str(post.id)
            post_dict["author_id"] = str(post.author_id)
            
            # Add author information
            author = authors_dict.get(str(post.author_id))
            if author:
                post_dict["author"] = {
                    "id": str(author.id),
                    "email": author.email,
                    "user_handle": author.user_handle,
                    "display_name": author.display_name,
                    "created_at": author.created_at.isoformat() if author.created_at else None,
                    "updated_at": author.updated_at.isoformat() if author.updated_at else None
                }
            
            # Calculate real-time stats from UserReaction and Comment collections
            real_stats = await self._calculate_post_stats(str(post.id))
            post_dict["stats"] = real_stats
            
            # Add user reaction if available
            if str(post.id) in user_reactions:
                post_dict["user_reaction"] = user_reactions[str(post.id)]
                
            posts_with_reactions.append(post_dict)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": posts_with_reactions,
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
    
    async def _calculate_post_stats(self, post_id: str) -> Dict[str, int]:
        """Calculate real-time statistics for a post.
        
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
            from beanie import PydanticObjectId
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
            import traceback
            print(f"Error calculating post stats for {post_id}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            # Re-raise the exception to see the actual error
            raise e
    
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