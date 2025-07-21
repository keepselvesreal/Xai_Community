"""
Logging system exceptions.

Custom exception classes for the logging system to provide clear error handling
and debugging information.
"""


class LoggingSystemError(Exception):
    """Base exception for all logging system errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class RepositoryError(LoggingSystemError):
    """Raised when database operations fail."""

    pass


class AdapterError(LoggingSystemError):
    """Raised when external service adapter operations fail."""

    def __init__(self, service_name: str, message: str, details: dict = None):
        self.service_name = service_name
        super().__init__(f"[{service_name}] {message}", details)


class ValidationError(LoggingSystemError):
    """Raised when log entry validation fails."""

    pass


class LogValidationError(ValidationError):
    """Alias for ValidationError for backward compatibility."""

    pass


class ServiceError(LoggingSystemError):
    """Raised when service layer operations fail."""

    pass


class CacheError(LoggingSystemError):
    """Raised when cache operations fail."""

    pass


class ConfigurationError(LoggingSystemError):
    """Raised when logging system configuration is invalid."""

    pass
