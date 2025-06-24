"""Authentication and authorization related exceptions."""

from src.exceptions.base import AuthenticationError, AuthorizationError


class InvalidTokenError(AuthenticationError):
    """Exception raised when a JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class ExpiredTokenError(AuthenticationError):
    """Exception raised when a JWT token is expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenTypeError(AuthenticationError):
    """Exception raised when token type doesn't match expected type."""
    
    def __init__(self, expected: str, actual: str):
        message = f"Expected {expected} token, got {actual}"
        super().__init__(message)


class MissingTokenError(AuthenticationError):
    """Exception raised when required token is missing."""
    
    def __init__(self, message: str = "Authentication token is required"):
        super().__init__(message)


class InsufficientPermissionsError(AuthorizationError):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, resource: str = None):
        if resource:
            message = f"Insufficient permissions to access {resource}"
        else:
            message = "Insufficient permissions"
        super().__init__(message)


class ResourceOwnershipError(AuthorizationError):
    """Exception raised when user is not the owner of a resource."""
    
    def __init__(self, message: str = None, resource_type: str = None, resource_id: str = None):
        if message:
            super().__init__(message)
        elif resource_type and resource_id:
            message = f"User is not the owner of {resource_type} {resource_id}"
            super().__init__(message)
        else:
            super().__init__("User is not the owner of this resource")


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when login credentials are invalid."""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)