"""
Logging system core domain models and interfaces.

This module provides the foundational elements for the logging system
that are independent of specific implementations or frameworks.
"""

from .enums import LogLevel, LogServiceType, LogSource
from .entities import (
    LogEntry,
    LogContext,
    LogMetadata,
    LogFilter,
    LogStats,
    LogListResponse,
    LogDashboardResponse,
    ErrorGrouping,
    TimeSeriesData,
    TopEndpoint,
    PerformanceSummary,
)
from .interfaces import (
    LogRepositoryInterface,
    ExternalLogAdapterInterface,
    CacheServiceInterface,
)
from .exceptions import (
    LoggingSystemError,
    RepositoryError,
    AdapterError,
    ValidationError,
    LogValidationError,
    ServiceError,
    CacheError,
    ConfigurationError,
)

__all__ = [
    # Enums
    "LogLevel",
    "LogServiceType", 
    "LogSource",
    
    # Entities
    "LogEntry",
    "LogContext",
    "LogMetadata",
    "LogFilter",
    "LogStats",
    "LogListResponse",
    "LogDashboardResponse",
    "ErrorGrouping",
    "TimeSeriesData",
    "TopEndpoint",
    "PerformanceSummary",
    
    # Interfaces
    "LogRepositoryInterface",
    "ExternalLogAdapterInterface",
    "CacheServiceInterface",
    
    # Exceptions
    "LoggingSystemError",
    "RepositoryError",
    "AdapterError",
    "ValidationError",
    "LogValidationError",
    "ServiceError",
    "CacheError",
    "ConfigurationError",
]