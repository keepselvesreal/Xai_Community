"""Exception package for the application."""

from .base import BaseAppException, AuthenticationError, AuthorizationError
from .user import (
    UserError, UserNotFoundError, DuplicateUserError, InvalidCredentialsError,
    UserNotActiveError, UserSuspendedError, EmailAlreadyExistsError, HandleAlreadyExistsError
)
from .auth import (
    InvalidTokenError, ExpiredTokenError, InvalidTokenTypeError,
    MissingTokenError, InsufficientPermissionsError, ResourceOwnershipError
)
from .post import (
    PostNotFoundError, PostPermissionError, PostSlugAlreadyExistsError,
    PostValidationError, PostCreateError, PostUpdateError, PostDeleteError
)
from .comment import (
    CommentNotFoundError,
    CommentPermissionError,
    CommentValidationError,
    CommentDepthExceededError,
    CommentStatusError
)

__all__ = [
    # Base
    "BaseAppException",
    "AuthenticationError",
    "AuthorizationError",
    
    # User
    "UserError",
    "UserNotFoundError",
    "DuplicateUserError",
    "InvalidCredentialsError",
    "UserNotActiveError",
    "UserSuspendedError",
    "EmailAlreadyExistsError",
    "HandleAlreadyExistsError",
    
    # Auth
    "InvalidTokenError",
    "ExpiredTokenError",
    "InvalidTokenTypeError",
    "MissingTokenError",
    "InsufficientPermissionsError",
    "ResourceOwnershipError",
    
    # Post
    "PostNotFoundError",
    "PostPermissionError",
    "PostSlugAlreadyExistsError",
    "PostValidationError",
    "PostCreateError",
    "PostUpdateError",
    "PostDeleteError",
    
    # Comment
    "CommentNotFoundError",
    "CommentPermissionError",
    "CommentValidationError",
    "CommentDepthExceededError",
    "CommentStatusError"
]