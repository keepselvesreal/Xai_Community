"""
Log service implementation for business logic and caching.

Provides high-level operations for log management including search,
statistics, dashboard data, and internal logging.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ...core.logging import (
    LogRepositoryInterface,
    CacheServiceInterface,
    LogEntry,
    LogFilter,
    LogStats,
    LogListResponse,
    LogDashboardResponse,
    ErrorGrouping,
    TimeSeriesData,
    TopEndpoint,
    PerformanceSummary,
    LogLevel,
    LogServiceType,
    LogSource,
    LogContext,
    LogMetadata,
    RepositoryError,
    CacheError,
)

logger = logging.getLogger(__name__)


class LogService:
    """
    Log service for business logic and caching operations.

    Provides high-level operations for log management while maintaining
    separation of concerns between business logic and data access.
    """

    def __init__(
        self,
        log_repository: LogRepositoryInterface,
        cache_service: Optional[CacheServiceInterface] = None,
        cache_ttl: int = 300,  # 5 minutes default
    ):
        """
        Initialize log service.

        Args:
            log_repository: Repository for log data access
            cache_service: Optional cache service for performance
            cache_ttl: Cache time-to-live in seconds
        """
        self.log_repository = log_repository
        self.cache_service = cache_service
        self.cache_ttl = cache_ttl

    async def setup(self) -> None:
        """
        Set up the log service (create indexes, etc.).
        """
        try:
            await self.log_repository.setup_indexes()
            logger.info("Log service setup completed")
        except Exception as e:
            logger.error(f"Failed to setup log service: {e}")
            raise

    async def log_internal(
        self,
        level: LogLevel,
        service: LogServiceType,
        message: str,
        context: Optional[LogContext] = None,
        metadata: Optional[LogMetadata] = None,
        stack_trace: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> LogEntry:
        """
        Create an internal log entry.

        Args:
            level: Log level
            service: Service that generated the log
            message: Log message
            context: Optional context information
            metadata: Optional metadata
            stack_trace: Optional stack trace for errors
            timestamp: Optional timestamp (defaults to UTC now if not provided)

        Returns:
            The created log entry

        Raises:
            RepositoryError: If log creation fails
        """
        try:
            log_entry = LogEntry(
                timestamp=timestamp or datetime.utcnow(),
                level=level,
                service=service,
                source=LogSource.INTERNAL,
                message=message,
                context=context,
                metadata=metadata,
                stack_trace=stack_trace,
            )

            return await self.log_repository.save_log(log_entry)

        except Exception as e:
            logger.error(f"Failed to create internal log: {e}")
            raise RepositoryError(f"Failed to create internal log: {str(e)}")

    async def save_external_logs(self, log_entries: List[LogEntry]) -> List[LogEntry]:
        """
        Save external log entries in batch.

        Args:
            log_entries: List of external log entries

        Returns:
            List of saved log entries

        Raises:
            RepositoryError: If batch save fails
        """
        try:
            if not log_entries:
                return []

            saved_logs = await self.log_repository.save_logs_batch(log_entries)

            # Clear related caches
            if self.cache_service:
                await self._clear_stats_cache()

            logger.info(f"Saved {len(saved_logs)} external log entries")
            return saved_logs

        except Exception as e:
            logger.error(f"Failed to save external logs: {e}")
            raise RepositoryError(f"Failed to save external logs: {str(e)}")

    async def search_logs(self, filter_obj: LogFilter) -> LogListResponse:
        """
        Search logs with filtering and pagination.

        Args:
            filter_obj: Filter criteria and pagination

        Returns:
            LogListResponse with logs and pagination info

        Raises:
            RepositoryError: If search fails
        """
        try:
            # Try cache first for read-heavy operations
            cache_key = None
            if self.cache_service:
                cache_key = self._generate_search_cache_key(filter_obj)
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    return LogListResponse(**cached_result)

            # Perform search
            result = await self.log_repository.search_logs(filter_obj)

            # Cache the result
            if self.cache_service and cache_key:
                await self._cache_result(cache_key, result.model_dump())

            return result

        except Exception as e:
            logger.error(f"Failed to search logs: {e}")
            raise RepositoryError(f"Failed to search logs: {str(e)}")

    async def get_log_by_id(self, log_id: str) -> Optional[LogEntry]:
        """
        Get a single log entry by ID.

        Args:
            log_id: Log entry ID

        Returns:
            LogEntry if found, None otherwise

        Raises:
            RepositoryError: If retrieval fails
        """
        try:
            return await self.log_repository.get_log_by_id(log_id)
        except Exception as e:
            logger.error(f"Failed to get log by ID: {e}")
            raise RepositoryError(f"Failed to get log: {str(e)}")

    async def get_stats(self, hours: int = 24) -> LogStats:
        """
        Get log statistics for a time range.

        Args:
            hours: Number of hours to look back

        Returns:
            LogStats with aggregated statistics

        Raises:
            RepositoryError: If stats retrieval fails
        """
        try:
            # Try cache first
            cache_key = None
            if self.cache_service:
                cache_key = f"log_stats:{hours}h"
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    return LogStats(**cached_result)

            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Get stats from repository
            stats = await self.log_repository.get_stats(start_time, end_time)

            # Cache the result with shorter TTL for frequently updated data
            if self.cache_service and cache_key:
                await self._cache_result(
                    cache_key, stats.model_dump(), ttl=60
                )  # 1 minute

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise RepositoryError(f"Failed to get stats: {str(e)}")

    async def get_dashboard_data(self, hours: int = 24) -> LogDashboardResponse:
        """
        Get comprehensive dashboard data.

        Args:
            hours: Number of hours to look back

        Returns:
            LogDashboardResponse with all dashboard data

        Raises:
            RepositoryError: If dashboard data retrieval fails
        """
        try:
            # Try cache first
            cache_key = None
            if self.cache_service:
                cache_key = f"log_dashboard:{hours}h"
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    return LogDashboardResponse(**cached_result)

            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Gather all dashboard data concurrently
            stats_task = self.log_repository.get_stats(start_time, end_time)
            errors_task = self.log_repository.get_error_groupings(
                start_time, end_time, 5
            )
            time_series_task = self.log_repository.get_time_series(
                start_time, end_time, 60
            )
            endpoints_task = self.log_repository.get_top_endpoints(
                start_time, end_time, 10
            )

            # Wait for all tasks
            stats, recent_errors, time_series, top_endpoints = await asyncio.gather(
                stats_task, errors_task, time_series_task, endpoints_task
            )

            # Calculate performance summary
            performance_summary = self._calculate_performance_summary(
                stats, top_endpoints
            )

            dashboard_data = LogDashboardResponse(
                stats=stats,
                recent_errors=recent_errors,
                time_series=time_series,
                top_endpoints=top_endpoints,
                performance_summary=performance_summary,
            )

            # Cache the result with shorter TTL for dashboard data
            if self.cache_service and cache_key:
                await self._cache_result(
                    cache_key, dashboard_data.model_dump(), ttl=120
                )  # 2 minutes

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            raise RepositoryError(f"Failed to get dashboard data: {str(e)}")

    async def cleanup_old_logs(self, retention_days: int = 30) -> Dict[str, int]:
        """
        Clean up old logs based on retention policy.

        Args:
            retention_days: Number of days to retain logs

        Returns:
            Dictionary with cleanup results

        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Different retention for different levels
            retention_policy = {
                LogLevel.ERROR.value: cutoff_date,  # Keep errors longer
                LogLevel.WARN.value: cutoff_date
                + timedelta(days=7),  # Keep warnings a bit longer
                LogLevel.INFO.value: cutoff_date
                + timedelta(days=23),  # Standard retention
                LogLevel.DEBUG.value: cutoff_date
                + timedelta(days=29),  # Keep debug logs shortest
            }

            cleanup_results = {}
            for level, level_cutoff in retention_policy.items():
                deleted_count = await self.log_repository.delete_logs_before(
                    level_cutoff, level
                )
                cleanup_results[level] = deleted_count

            # Clear caches after cleanup
            if self.cache_service:
                await self._clear_all_caches()

            total_deleted = sum(cleanup_results.values())
            logger.info(f"Cleaned up {total_deleted} old log entries")

            return cleanup_results

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            raise RepositoryError(f"Failed to cleanup old logs: {str(e)}")

    async def count_logs(self, filter_obj: LogFilter) -> int:
        """
        Count logs matching filter criteria.

        Args:
            filter_obj: Filter criteria

        Returns:
            Number of matching logs

        Raises:
            RepositoryError: If count fails
        """
        try:
            return await self.log_repository.count_logs(filter_obj)
        except Exception as e:
            logger.error(f"Failed to count logs: {e}")
            raise RepositoryError(f"Failed to count logs: {str(e)}")

    def _generate_search_cache_key(self, filter_obj: LogFilter) -> str:
        """
        Generate cache key for search operations.

        Args:
            filter_obj: Filter object

        Returns:
            Cache key string
        """
        # Create a deterministic hash of the filter
        filter_data = filter_obj.model_dump(exclude_none=True)
        filter_str = str(sorted(filter_data.items()))
        return f"log_search:{hash(filter_str)}"

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result if available.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None
        """
        try:
            if self.cache_service:
                return await self.cache_service.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None

    async def _cache_result(
        self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        """
        Cache result data.

        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Optional time-to-live override
        """
        try:
            if self.cache_service:
                cache_ttl = ttl or self.cache_ttl
                await self.cache_service.set(cache_key, data, expire=cache_ttl)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    async def _clear_stats_cache(self) -> None:
        """Clear statistics-related caches."""
        try:
            if self.cache_service:
                await self.cache_service.clear_pattern("log_stats:*")
                await self.cache_service.clear_pattern("log_dashboard:*")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    async def _clear_all_caches(self) -> None:
        """Clear all logging-related caches."""
        try:
            if self.cache_service:
                await self.cache_service.clear_pattern("log_*")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    def _calculate_performance_summary(
        self, stats: LogStats, top_endpoints: List[TopEndpoint]
    ) -> PerformanceSummary:
        """
        Calculate performance summary from stats and endpoints.

        Args:
            stats: Log statistics
            top_endpoints: Top endpoint statistics

        Returns:
            PerformanceSummary with calculated metrics
        """
        # Calculate service-level performance
        services = {}
        for service, count in stats.service_stats.items():
            # Calculate metrics for each service
            service_endpoints = [
                ep for ep in top_endpoints if service.lower() in ep.endpoint.lower()
            ]

            if service_endpoints:
                avg_response_time = sum(
                    ep.avg_response_time for ep in service_endpoints
                ) / len(service_endpoints)
                max_response_time = max(
                    ep.avg_response_time for ep in service_endpoints
                )
                total_requests = sum(ep.total_requests for ep in service_endpoints)
            else:
                avg_response_time = stats.avg_response_time or 0
                max_response_time = stats.max_response_time or 0
                total_requests = count

            services[service] = {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "request_count": total_requests,
            }

        # Calculate overall performance
        overall = {
            "avg_response_time": stats.avg_response_time or 0,
            "max_response_time": stats.max_response_time or 0,
            "total_requests": stats.total_count,
            "error_rate": stats.error_rate,
        }

        return PerformanceSummary(
            services=services,
            overall=overall,
        )
