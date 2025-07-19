"""
Logging system domain entities.

Pydantic models representing the core business entities for the logging system.
These models are framework-agnostic and can be used with any database or ORM.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from .enums import LogLevel, LogServiceType, LogSource
from .exceptions import LogValidationError


class LogContext(BaseModel):
    """
    Contextual information for a log entry.
    
    Contains request-specific, user-specific, and infrastructure-specific
    information that helps with debugging and analysis.
    """
    # Request context
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None  # milliseconds
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Infrastructure context
    infrastructure: Optional[str] = None  # "vercel", "gcp", "atlas"
    instance_id: Optional[str] = None
    region: Optional[str] = None
    deployment_id: Optional[str] = None
    version: Optional[str] = None


class LogMetadata(BaseModel):
    """
    Additional metadata for log entries.
    
    Contains performance metrics, error details, and other structured data
    that can be used for analysis and monitoring.
    """
    # Performance metrics
    memory_usage: Optional[float] = None  # bytes
    cpu_usage: Optional[float] = None     # percentage
    disk_usage: Optional[float] = None    # bytes
    
    # Error details
    error_code: Optional[str] = None
    error_type: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # External service details
    cloud_trace_id: Optional[str] = None
    atlas_cluster: Optional[str] = None
    vercel_deployment_id: Optional[str] = None
    
    # Tags and custom data
    tags: Optional[List[str]] = Field(default_factory=list)
    severity: Optional[str] = None
    custom: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LogEntry(BaseModel):
    """
    Core log entry entity.
    
    Represents a single log event with all associated context and metadata.
    This is the primary entity for the logging system.
    """
    id: Optional[str] = None
    timestamp: datetime
    level: LogLevel
    service: LogServiceType
    source: LogSource
    message: str = Field(..., min_length=1)
    context: Optional[LogContext] = None
    metadata: Optional[LogMetadata] = None
    stack_trace: Optional[str] = None
    
    @validator('message')
    def validate_message(cls, v):
        """Validate log message is not empty."""
        if not v or not v.strip():
            raise LogValidationError("Log message cannot be empty")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class LogFilter(BaseModel):
    """
    Filter criteria for log searches.
    
    Supports complex filtering across all log attributes with pagination.
    """
    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Basic filters
    levels: Optional[List[LogLevel]] = None
    services: Optional[List[LogServiceType]] = None
    sources: Optional[List[LogSource]] = None
    
    # Text search
    search_query: Optional[str] = None
    
    # Context filters
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    status_codes: Optional[List[int]] = None
    
    # Infrastructure filters
    regions: Optional[List[str]] = None
    instance_ids: Optional[List[str]] = None
    deployment_ids: Optional[List[str]] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries."""
        return (self.page - 1) * self.page_size


class LogStats(BaseModel):
    """
    Log statistics and aggregations.
    
    Provides summary statistics for dashboard displays and monitoring.
    """
    # Count statistics
    total_count: int = 0
    error_count: int = 0
    warn_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    
    # Service breakdown
    service_stats: Dict[str, int] = Field(default_factory=dict)
    
    # Source breakdown
    source_stats: Dict[str, int] = Field(default_factory=dict)
    
    # Time range
    start_time: datetime
    end_time: datetime
    
    # Performance stats
    avg_response_time: Optional[float] = None
    max_response_time: Optional[float] = None
    
    # Error rate
    error_rate: float = 0.0  # percentage
    
    @classmethod
    def calculate_error_rate(cls, error_count: int, total_count: int) -> float:
        """Calculate error rate percentage."""
        if total_count == 0:
            return 0.0
        return (error_count / total_count) * 100


class ErrorGrouping(BaseModel):
    """
    Error grouping for similar errors.
    
    Groups similar errors together for better analysis and resolution tracking.
    """
    id: str
    error_hash: str  # Hash of error message + stack trace
    service: LogServiceType
    endpoint: Optional[str] = None
    error_type: Optional[str] = None
    count: int = 1
    first_seen: datetime
    last_seen: datetime
    sample_message: str
    sample_stack_trace: Optional[str] = None
    severity: Optional[str] = None
    is_resolved: bool = False
    resolution_notes: Optional[str] = None


class LogListResponse(BaseModel):
    """
    Response model for log list API endpoints.
    
    Includes logs with pagination information.
    """
    logs: List[LogEntry]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        logs: List[LogEntry],
        total_count: int,
        page: int,
        page_size: int
    ) -> "LogListResponse":
        """Create a log list response with calculated pagination."""
        return cls(
            logs=logs,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total_count,
            has_prev=page > 1
        )


class TimeSeriesData(BaseModel):
    """
    Time series data for charts and graphs.
    """
    timestamp: datetime
    error: int = 0
    warn: int = 0
    info: int = 0
    debug: int = 0


class TopEndpoint(BaseModel):
    """
    Top endpoint statistics.
    """
    endpoint: str
    total_requests: int
    error_count: int
    error_rate: float
    avg_response_time: float


class PerformanceSummary(BaseModel):
    """
    Performance summary across services.
    """
    services: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    overall: Dict[str, Any] = Field(default_factory=dict)


class LogDashboardResponse(BaseModel):
    """
    Complete dashboard response with all necessary data.
    """
    stats: LogStats
    recent_errors: List[ErrorGrouping]
    time_series: List[TimeSeriesData]
    top_endpoints: List[TopEndpoint]
    performance_summary: PerformanceSummary