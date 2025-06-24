"""User-related exceptions."""

from src.exceptions.base import BaseAppException


class UserError(BaseAppException):
    """Base exception for user-related errors."""
    pass


class UserNotFoundError(UserError):
    """Exception raised when a user is not found."""
    
    def __init__(self, identifier: str = None):
        if identifier:
            message = f"User not found: {identifier}"
        else:
            message = "User not found"
        super().__init__(message)


class DuplicateUserError(UserError):
    """Exception raised when attempting to create a user with duplicate unique fields."""
    
    def __init__(self, field: str, value: str):
        message = f"User with {field} '{value}' already exists"
        super().__init__(message)


class InvalidCredentialsError(UserError):
    """Exception raised when login credentials are invalid."""
    
    def __init__(self):
        super().__init__("Invalid email or password")


class UserNotActiveError(UserError):
    """Exception raised when attempting to authenticate an inactive user."""
    
    def __init__(self):
        super().__init__("User account is not active")


class UserSuspendedError(UserError):
    """Exception raised when attempting to authenticate a suspended user."""
    
    def __init__(self):
        super().__init__("User account is suspended")


class EmailAlreadyExistsError(UserError):
    """Exception raised when email already exists."""
    
    def __init__(self, email: str):
        super().__init__(f"Email '{email}' already exists")


class HandleAlreadyExistsError(UserError):
    """Exception raised when handle already exists."""
    
    def __init__(self, handle: str):
        super().__init__(f"Handle '{handle}' already exists")