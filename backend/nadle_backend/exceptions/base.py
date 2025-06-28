"""Base exception classes for the application."""


class BaseAppException(Exception):
    """Base exception class for application-specific exceptions."""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAppException):
    """Exception raised for validation errors."""
    pass


class AuthenticationError(BaseAppException):
    """Exception raised for authentication errors."""
    pass


class AuthorizationError(BaseAppException):
    """Exception raised for authorization errors."""
    pass


class DatabaseError(BaseAppException):
    """Exception raised for database-related errors."""
    pass