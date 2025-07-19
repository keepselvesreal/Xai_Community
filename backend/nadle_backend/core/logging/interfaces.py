"""
Logging system interfaces and abstract base classes.

Defines the contracts for repositories and services that implement the logging functionality.
This enables dependency injection and makes the system testable and database-agnostic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import (
    LogEntry,
    LogFilter,
    LogStats,
    LogListResponse,
    LogDashboardResponse,
    ErrorGrouping,
    TimeSeriesData,
    TopEndpoint,
)


class LogRepositoryInterface(ABC):
    """
    Abstract interface for log repository implementations.
    
    This interface can be implemented for different databases:
    - MongoDB (using Motor)
    - PostgreSQL (using asyncpg + SQLAlchemy)
    - MySQL (using aiomysql + SQLAlchemy)
    - SQLite (using aiosqlite)
    """
    
    @abstractmethod
    async def setup_indexes(self) -> None:
        """
        Set up database indexes for optimal query performance.
        
        Should be called during application startup to ensure
        all necessary indexes are created.
        """
        pass
    
    @abstractmethod
    async def save_log(self, log_entry: LogEntry) -> LogEntry:
        """
        Save a single log entry to the database.
        
        Args:
            log_entry: The log entry to save
            
        Returns:
            The saved log entry with populated ID
            
        Raises:
            RepositoryError: If the save operation fails
        """
        pass
    
    @abstractmethod
    async def save_logs_batch(self, log_entries: List[LogEntry]) -> List[LogEntry]:
        """
        Save multiple log entries in a single batch operation.
        
        Args:
            log_entries: List of log entries to save
            
        Returns:
            List of saved log entries with populated IDs
            
        Raises:
            RepositoryError: If the batch save operation fails
        """
        pass
    
    @abstractmethod
    async def search_logs(self, filter_obj: LogFilter) -> LogListResponse:
        """
        Search logs with filtering and pagination.
        
        Args:
            filter_obj: Filter criteria and pagination parameters
            
        Returns:
            LogListResponse with logs and pagination info
            
        Raises:
            RepositoryError: If the search operation fails
        """
        pass
    
    @abstractmethod
    async def get_log_by_id(self, log_id: str) -> Optional[LogEntry]:
        """
        Retrieve a single log entry by ID.
        
        Args:
            log_id: The log entry ID
            
        Returns:
            The log entry if found, None otherwise
            
        Raises:
            RepositoryError: If the query operation fails
        """
        pass
    
    @abstractmethod
    async def get_stats(self, start_time: datetime, end_time: datetime) -> LogStats:
        """
        Get log statistics for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            LogStats with aggregated statistics
            
        Raises:
            RepositoryError: If the aggregation operation fails
        """
        pass
    
    @abstractmethod
    async def get_error_groupings(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10
    ) -> List[ErrorGrouping]:
        """
        Get top error groupings for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of error groupings to return
            
        Returns:
            List of error groupings sorted by frequency
            
        Raises:
            RepositoryError: If the aggregation operation fails
        """
        pass
    
    @abstractmethod
    async def get_time_series(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 60
    ) -> List[TimeSeriesData]:
        """
        Get time series data for charts.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            interval_minutes: Time interval in minutes for data points
            
        Returns:
            List of time series data points
            
        Raises:
            RepositoryError: If the aggregation operation fails
        """
        pass
    
    @abstractmethod
    async def get_top_endpoints(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10
    ) -> List[TopEndpoint]:
        """
        Get top endpoints by request count and error rate.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of endpoints to return
            
        Returns:
            List of top endpoints with statistics
            
        Raises:
            RepositoryError: If the aggregation operation fails
        """
        pass
    
    @abstractmethod
    async def delete_logs_before(self, cutoff_date: datetime, level: Optional[str] = None) -> int:
        """
        Delete logs older than the cutoff date.
        
        Args:
            cutoff_date: Delete logs older than this date
            level: Optional log level filter
            
        Returns:
            Number of deleted log entries
            
        Raises:
            RepositoryError: If the delete operation fails
        """
        pass
    
    @abstractmethod
    async def count_logs(self, filter_obj: LogFilter) -> int:
        """
        Count logs matching the filter criteria.
        
        Args:
            filter_obj: Filter criteria
            
        Returns:
            Number of matching logs
            
        Raises:
            RepositoryError: If the count operation fails
        """
        pass


class ExternalLogAdapterInterface(ABC):
    """
    Abstract interface for external log collection adapters.
    
    Each external service (Vercel, Upstash, Cloud Run, Atlas) 
    should implement this interface.
    """
    
    @abstractmethod
    async def collect_logs(self, hours: int = 1) -> List[LogEntry]:
        """
        Collect logs from the external service.
        
        Args:
            hours: Number of hours to look back for logs
            
        Returns:
            List of log entries collected from the external service
            
        Raises:
            AdapterError: If the collection operation fails
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the external service.
        
        Returns:
            True if connection is successful, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        Get the name of the external service.
        
        Returns:
            The service name (e.g., "vercel", "upstash")
        """
        pass


class CacheServiceInterface(ABC):
    """
    Abstract interface for caching operations.
    
    Allows the logging system to use different caching backends
    (Redis, Memcached, in-memory cache, etc.)
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache by key."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache with optional expiration."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache by key."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        """Clear all cache keys matching the pattern."""
        pass