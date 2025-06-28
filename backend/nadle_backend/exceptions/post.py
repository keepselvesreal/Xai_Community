"""Post-related exception definitions."""

from .base import BaseAppException


class PostNotFoundError(BaseAppException):
    """Raised when a post is not found."""
    
    def __init__(self, post_id: str = None, slug: str = None):
        if slug:
            message = f"Post with slug '{slug}' not found"
        elif post_id:
            message = f"Post with ID '{post_id}' not found"
        else:
            message = "Post not found"
        super().__init__(message)


class PostPermissionError(BaseAppException):
    """Raised when user doesn't have permission to perform post operation."""
    
    def __init__(self, message: str = "Insufficient permissions for this post operation"):
        super().__init__(message)


class PostSlugAlreadyExistsError(BaseAppException):
    """Raised when trying to create a post with an existing slug."""
    
    def __init__(self, slug: str):
        message = f"Post with slug '{slug}' already exists"
        super().__init__(message)


class PostValidationError(BaseAppException):
    """Raised when post data validation fails."""
    
    def __init__(self, message: str = "Post data validation failed"):
        super().__init__(message)


class PostCreateError(BaseAppException):
    """Raised when post creation fails."""
    
    def __init__(self, message: str = "Failed to create post"):
        super().__init__(message)


class PostUpdateError(BaseAppException):
    """Raised when post update fails."""
    
    def __init__(self, message: str = "Failed to update post"):
        super().__init__(message)


class PostDeleteError(BaseAppException):
    """Raised when post deletion fails."""
    
    def __init__(self, message: str = "Failed to delete post"):
        super().__init__(message)