"""Posts service layer for business logic."""

from typing import List, Dict, Any, Optional
from src.models.core import User, Post, PostCreate, PostUpdate, PostResponse, PaginatedResponse, PostMetadata
from src.repositories.post_repository import PostRepository
from src.exceptions.post import PostNotFoundError, PostPermissionError
from src.utils.permissions import check_post_permission


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
            post_data.metadata = PostMetadata(type="자유게시판")
        elif not post_data.metadata.type:
            post_data.metadata.type = "자유게시판"
            
        # Create post with current user as author
        post = await self.post_repository.create(post_data, str(current_user.id))
        return post
    
    async def get_post(self, slug: str, current_user: Optional[User] = None) -> Post:
        """Get post by slug.
        
        Args:
            slug: Post slug
            current_user: Current user (optional)
            
        Returns:
            Post instance
            
        Raises:
            PostNotFoundError: If post not found
        """
        # Get post
        post = await self.post_repository.get_by_slug(slug)
        
        # Increment view count
        await self.post_repository.increment_view_count(str(post.id))
        
        return post
    
    async def list_posts(
        self,
        page: int = 1,
        page_size: int = 20,
        service_type: Optional[str] = None,
        author_id: Optional[str] = None,
        sort_by: str = "created_at",
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """List posts with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            service_type: Filter by service type
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
        
        # Add user reaction data to posts
        posts_with_reactions = []
        for post in posts:
            post_dict = post.model_dump()
            
            # Convert ObjectIds to strings
            post_dict["_id"] = str(post.id)
            post_dict["author_id"] = str(post.author_id)
            
            # Add stats
            post_dict["stats"] = {
                "view_count": post.view_count,
                "like_count": post.like_count,
                "dislike_count": post.dislike_count,
                "comment_count": post.comment_count
            }
            
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
            
            # Add stats
            post_dict["stats"] = {
                "view_count": post.view_count,
                "like_count": post.like_count,
                "dislike_count": post.dislike_count,
                "comment_count": post.comment_count
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