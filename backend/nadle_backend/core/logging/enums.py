"""
Logging system enums and constants.

Standard enum definitions for the logging system using proper Python Enum classes
for type safety, IDE support, and maintainability.
"""

from enum import Enum


class LogLevel(str, Enum):
    """
    Log level enumeration.

    Inherits from str to ensure JSON serialization compatibility
    while maintaining enum benefits (IDE support, type safety).
    """

    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogServiceType(str, Enum):
    """
    Service type enumeration for identifying log sources.

    Note: This is separate from the existing ServiceType in models/core.py
    to avoid naming conflicts and maintain separation of concerns.
    """

    API = "api"
    WEB = "web"
    CLOUD_RUN = "cloud-run"
    DATABASE = "database"
    REDIS = "redis"
    VERCEL = "vercel"


class LogSource(str, Enum):
    """
    Log source enumeration for distinguishing internal vs external logs.
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


# Utility constants for easy access
LOG_LEVELS = [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG]
LOG_SERVICE_TYPES = [
    LogServiceType.API,
    LogServiceType.WEB,
    LogServiceType.CLOUD_RUN,
    LogServiceType.DATABASE,
    LogServiceType.REDIS,
    LogServiceType.VERCEL,
]
LOG_SOURCES = [LogSource.INTERNAL, LogSource.EXTERNAL]
