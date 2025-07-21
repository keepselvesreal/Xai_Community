"""
Tests for logging service implementation.

This module tests the LogService class which provides business logic
for the logging system including caching, statistics, and dashboard data.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock
from typing import List, Dict, Any, Optional

from nadle_backend.core.logging import (
    LogLevel,
    LogServiceType,
    LogSource,
    LogEntry,
    LogFilter,
    LogStats,
    LogListResponse,
    LogDashboardResponse,
    LogContext,
    LogMetadata,
    PerformanceSummary,
    LogRepositoryInterface,
    CacheServiceInterface,
    RepositoryError,
)
from nadle_backend.logging.services.log_service import LogService


# Global fixtures for service tests
@pytest.fixture
def mock_repository():
    """Create mock log repository."""
    return Mock(spec=LogRepositoryInterface)

@pytest.fixture
def mock_cache():
    """Create mock cache service."""
    return Mock(spec=CacheServiceInterface)

@pytest.fixture
def log_service(mock_repository, mock_cache):
    """Create LogService instance with mocks."""
    return LogService(
        log_repository=mock_repository,
        cache_service=mock_cache,
        cache_ttl=300
    )

@pytest.fixture
def log_service_no_cache(mock_repository):
    """Create LogService instance without cache."""
    return LogService(
        log_repository=mock_repository,
        cache_service=None,
        cache_ttl=300
    )

@pytest.fixture
def sample_log_entry():
    """Create sample log entry."""
    return LogEntry(
        id="507f1f77bcf86cd799439011",
        timestamp=datetime.now(timezone.utc),
        level=LogLevel.ERROR,
        service=LogServiceType.API,
        source=LogSource.INTERNAL,
        message="Test error message",
        context=LogContext(
            user_id="user123",
            endpoint="/api/test",
            status_code=500,
            response_time=250
        ),
        metadata=LogMetadata(
            tags=["error", "api"],
            error_code="TEST_001"
        )
    )

@pytest.fixture
def sample_filter():
    """Create sample log filter."""
    return LogFilter(
        start_time=datetime.now(timezone.utc) - timedelta(hours=24),
        end_time=datetime.now(timezone.utc),
        levels=[LogLevel.ERROR],
        services=[LogServiceType.API],
        page=1,
        page_size=50
    )


class TestLogService:
    """Test LogService implementation."""


class TestServiceInitialization:
    """Test service initialization and setup."""

    def test_service_creation_with_cache(self, mock_repository, mock_cache):
        """Test creating service with cache."""
        service = LogService(
            log_repository=mock_repository,
            cache_service=mock_cache,
            cache_ttl=600
        )
        
        assert service.log_repository == mock_repository
        assert service.cache_service == mock_cache
        assert service.cache_ttl == 600

    def test_service_creation_without_cache(self, mock_repository):
        """Test creating service without cache."""
        service = LogService(
            log_repository=mock_repository,
            cache_service=None,
            cache_ttl=300
        )
        
        assert service.log_repository == mock_repository
        assert service.cache_service is None
        assert service.cache_ttl == 300

    @pytest.mark.asyncio
    async def test_service_setup(self, log_service, mock_repository):
        """Test service setup."""
        mock_repository.setup_indexes = AsyncMock()
        
        await log_service.setup()
        
        mock_repository.setup_indexes.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_setup_repository_error(self, log_service, mock_repository):
        """Test service setup with repository error."""
        mock_repository.setup_indexes = AsyncMock(side_effect=Exception("Setup failed"))
        
        with pytest.raises(Exception):
            await log_service.setup()


class TestLogOperations:
    """Test basic log operations."""

    @pytest.mark.asyncio
    async def test_log_internal_success(self, log_service, mock_repository):
        """Test successful internal log creation."""
        created_log = LogEntry(
            id="507f1f77bcf86cd799439011",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.ERROR,
            service=LogServiceType.API,
            source=LogSource.INTERNAL,
            message="Internal test message"
        )
        mock_repository.save_log = AsyncMock(return_value=created_log)
        
        result = await log_service.log_internal(
            level=LogLevel.ERROR,
            service=LogServiceType.API,
            message="Internal test message"
        )
        
        assert result == created_log
        mock_repository.save_log.assert_called_once()
        call_args = mock_repository.save_log.call_args[0][0]
        assert call_args.level == LogLevel.ERROR
        assert call_args.service == LogServiceType.API
        assert call_args.message == "Internal test message"
        assert call_args.source == LogSource.INTERNAL

    @pytest.mark.asyncio
    async def test_log_internal_repository_error(self, log_service, mock_repository):
        """Test internal log creation with repository error."""
        mock_repository.save_log = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service.log_internal(
                level=LogLevel.ERROR,
                service=LogServiceType.API,
                message="Test message"
            )

    @pytest.mark.asyncio
    async def test_save_external_logs_success(self, log_service, mock_repository, mock_cache):
        """Test successful external logs batch save."""
        external_logs = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                service=LogServiceType.WEB,
                source=LogSource.EXTERNAL,
                message="External log 1"
            ),
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.WARN,
                service=LogServiceType.API,
                source=LogSource.EXTERNAL,
                message="External log 2"
            )
        ]
        
        mock_repository.save_logs_batch = AsyncMock(return_value=external_logs)
        mock_cache.clear_pattern = AsyncMock()
        
        result = await log_service.save_external_logs(external_logs)
        
        assert result == external_logs
        mock_repository.save_logs_batch.assert_called_once_with(external_logs)
        # Should clear stats cache
        assert mock_cache.clear_pattern.call_count == 2

    @pytest.mark.asyncio
    async def test_save_external_logs_empty(self, log_service):
        """Test external logs save with empty list."""
        result = await log_service.save_external_logs([])
        assert result == []

    @pytest.mark.asyncio
    async def test_save_external_logs_repository_error(self, log_service, mock_repository, sample_log_entry):
        """Test external logs save with repository error."""
        mock_repository.save_logs_batch = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service.save_external_logs([sample_log_entry])

    @pytest.mark.asyncio
    async def test_get_log_by_id_success(self, log_service, mock_repository, sample_log_entry):
        """Test successful log retrieval."""
        mock_repository.get_log_by_id = AsyncMock(return_value=sample_log_entry)
        
        result = await log_service.get_log_by_id(sample_log_entry.id)
        
        assert result == sample_log_entry
        mock_repository.get_log_by_id.assert_called_once_with(sample_log_entry.id)

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(self, log_service, mock_repository):
        """Test log retrieval when not found."""
        mock_repository.get_log_by_id = AsyncMock(return_value=None)
        
        result = await log_service.get_log_by_id("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_log_by_id_repository_error(self, log_service, mock_repository):
        """Test log retrieval with repository error."""
        mock_repository.get_log_by_id = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service.get_log_by_id("log_id")


class TestLogSearch:
    """Test log search functionality."""

    @pytest.mark.asyncio
    async def test_search_logs_success(self, log_service_no_cache, mock_repository, sample_filter, sample_log_entry):
        """Test successful log search."""
        search_result = LogListResponse(
            logs=[sample_log_entry],
            total_count=1,
            page=1,
            page_size=50,
            has_next=False,
            has_prev=False
        )
        
        mock_repository.search_logs = AsyncMock(return_value=search_result)
        
        result = await log_service_no_cache.search_logs(sample_filter)
        
        assert result == search_result
        assert len(result.logs) == 1
        assert result.total_count == 1
        mock_repository.search_logs.assert_called_once_with(sample_filter)

    @pytest.mark.asyncio
    async def test_search_logs_empty_result(self, log_service_no_cache, mock_repository, sample_filter):
        """Test search with no results."""
        empty_result = LogListResponse(
            logs=[],
            total_count=0,
            page=1,
            page_size=50,
            has_next=False,
            has_prev=False
        )
        
        mock_repository.search_logs = AsyncMock(return_value=empty_result)
        
        result = await log_service_no_cache.search_logs(sample_filter)
        
        assert result == empty_result
        assert len(result.logs) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_logs_with_cache(self, log_service, mock_repository, mock_cache, sample_filter):
        """Test search with cache hit."""
        cached_result = LogListResponse(
            logs=[],
            total_count=0,
            page=1,
            page_size=50,
            has_next=False,
            has_prev=False
        )
        
        mock_cache.get = AsyncMock(return_value=cached_result.model_dump())
        
        result = await log_service.search_logs(sample_filter)
        
        assert result.total_count == cached_result.total_count
        mock_cache.get.assert_called_once()
        mock_repository.search_logs.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_logs_cache_miss(self, log_service, mock_repository, mock_cache, sample_filter, sample_log_entry):
        """Test search with cache miss."""
        search_result = LogListResponse(
            logs=[sample_log_entry],
            total_count=1,
            page=1,
            page_size=50,
            has_next=False,
            has_prev=False
        )
        
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_repository.search_logs = AsyncMock(return_value=search_result)
        
        result = await log_service.search_logs(sample_filter)
        
        assert result == search_result
        mock_cache.get.assert_called_once()
        mock_repository.search_logs.assert_called_once_with(sample_filter)
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_logs_repository_error(self, log_service_no_cache, mock_repository, sample_filter):
        """Test search with repository error."""
        mock_repository.search_logs = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service_no_cache.search_logs(sample_filter)


class TestLogStatistics:
    """Test log statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, log_service_no_cache, mock_repository):
        """Test successful statistics retrieval."""
        stats = LogStats(
            total_count=1000,
            error_count=50,
            warn_count=150,
            info_count=700,
            debug_count=100,
            service_stats={"api": 600, "web": 400},
            start_time=datetime.now(timezone.utc) - timedelta(hours=24),
            end_time=datetime.now(timezone.utc)
        )
        
        mock_repository.get_stats = AsyncMock(return_value=stats)
        
        result = await log_service_no_cache.get_stats(24)
        
        assert result == stats
        assert result.total_count == 1000
        assert result.error_count == 50
        mock_repository.get_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats_with_cache(self, log_service, mock_repository, mock_cache):
        """Test statistics with cache hit."""
        cached_stats = {
            "total_count": 500,
            "error_count": 25,
            "warn_count": 75,
            "info_count": 350,
            "debug_count": 50,
            "service_stats": {"api": 300, "web": 200},
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat()
        }
        
        mock_cache.get = AsyncMock(return_value=cached_stats)
        
        result = await log_service.get_stats(24)
        
        assert result.total_count == 500
        assert result.error_count == 25
        mock_cache.get.assert_called_once()
        mock_repository.get_stats.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_stats_cache_miss(self, log_service, mock_repository, mock_cache):
        """Test statistics with cache miss."""
        stats = LogStats(
            total_count=1000,
            error_count=50,
            warn_count=150,
            info_count=700,
            debug_count=100,
            service_stats={"api": 600, "web": 400},
            start_time=datetime.now(timezone.utc) - timedelta(hours=24),
            end_time=datetime.now(timezone.utc)
        )
        
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_repository.get_stats = AsyncMock(return_value=stats)
        
        result = await log_service.get_stats(24)
        
        assert result == stats
        mock_cache.get.assert_called_once()
        mock_repository.get_stats.assert_called_once()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats_repository_error(self, log_service_no_cache, mock_repository):
        """Test statistics with repository error."""
        mock_repository.get_stats = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service_no_cache.get_stats(24)


class TestLogCount:
    """Test log counting functionality."""

    @pytest.mark.asyncio
    async def test_count_logs_success(self, log_service, mock_repository, sample_filter):
        """Test successful log counting."""
        mock_repository.count_logs = AsyncMock(return_value=42)
        
        result = await log_service.count_logs(sample_filter)
        
        assert result == 42
        mock_repository.count_logs.assert_called_once_with(sample_filter)

    @pytest.mark.asyncio
    async def test_count_logs_zero(self, log_service, mock_repository, sample_filter):
        """Test counting with zero results."""
        mock_repository.count_logs = AsyncMock(return_value=0)
        
        result = await log_service.count_logs(sample_filter)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_logs_repository_error(self, log_service, mock_repository, sample_filter):
        """Test counting with repository error."""
        mock_repository.count_logs = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service.count_logs(sample_filter)


class TestDashboardData:
    """Test dashboard data aggregation."""

    @pytest.mark.asyncio
    async def test_get_dashboard_data_success(self, log_service_no_cache, mock_repository):
        """Test successful dashboard data retrieval."""
        # Mock all repository methods that dashboard data needs
        stats = LogStats(
            total_count=1000,
            error_count=50,
            warn_count=150,
            info_count=700,
            debug_count=100,
            service_stats={"api": 600, "web": 400},
            start_time=datetime.now(timezone.utc) - timedelta(hours=24),
            end_time=datetime.now(timezone.utc)
        )
        
        mock_repository.get_stats = AsyncMock(return_value=stats)
        mock_repository.get_error_groupings = AsyncMock(return_value=[])
        mock_repository.get_time_series = AsyncMock(return_value=[])
        mock_repository.get_top_endpoints = AsyncMock(return_value=[])
        
        result = await log_service_no_cache.get_dashboard_data(24)
        
        assert result.stats == stats
        assert result.recent_errors == []
        assert result.time_series == []
        assert result.top_endpoints == []
        assert isinstance(result.performance_summary, PerformanceSummary)
        mock_repository.get_stats.assert_called_once()
        mock_repository.get_error_groupings.assert_called_once()
        mock_repository.get_time_series.assert_called_once()
        mock_repository.get_top_endpoints.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dashboard_data_with_cache(self, log_service, mock_cache):
        """Test dashboard data with cache hit."""
        cached_data = {
            "stats": {
                "total_count": 500,
                "error_count": 25,
                "warn_count": 75,
                "info_count": 350,
                "debug_count": 50,
                "service_stats": {"api": 300, "web": 200},
                "start_time": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat()
            },
            "recent_errors": [],
            "time_series": [],
            "top_endpoints": [],
            "performance_summary": {
                "services": {},
                "overall": {"avg_response_time": 200, "max_response_time": 800, "total_requests": 500}
            }
        }
        
        mock_cache.get = AsyncMock(return_value=cached_data)
        
        result = await log_service.get_dashboard_data(24)
        
        assert result.stats.total_count == 500
        assert result.performance_summary.overall["total_requests"] == 500
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_dashboard_data_with_cache_miss(self, log_service, mock_repository, mock_cache):
        """Test dashboard data with cache miss and subsequent caching."""
        stats = LogStats(
            total_count=500,
            error_count=25,
            warn_count=75,
            info_count=350,
            debug_count=50,
            service_stats={"api": 300, "web": 200},
            start_time=datetime.now(timezone.utc) - timedelta(hours=24),
            end_time=datetime.now(timezone.utc)
        )
        
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_repository.get_stats = AsyncMock(return_value=stats)
        mock_repository.get_error_groupings = AsyncMock(return_value=[])
        mock_repository.get_time_series = AsyncMock(return_value=[])
        mock_repository.get_top_endpoints = AsyncMock(return_value=[])
        
        result = await log_service.get_dashboard_data(24)
        
        assert result.stats == stats
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
        mock_repository.get_stats.assert_called_once()


class TestLogCleanup:
    """Test log cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_success(self, log_service_no_cache, mock_repository):
        """Test successful log cleanup."""
        # Mock delete_logs_before for each level
        mock_repository.delete_logs_before = AsyncMock(side_effect=[25, 50, 100, 200])
        
        result = await log_service_no_cache.cleanup_old_logs(30)
        
        assert result["ERROR"] == 25
        assert result["WARN"] == 50
        assert result["INFO"] == 100
        assert result["DEBUG"] == 200
        assert mock_repository.delete_logs_before.call_count == 4
        # No cache service, so no clear_pattern call

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_nothing_to_clean(self, log_service_no_cache, mock_repository):
        """Test cleanup with no old logs."""
        mock_repository.delete_logs_before = AsyncMock(side_effect=[0, 0, 0, 0])
        
        result = await log_service_no_cache.cleanup_old_logs(30)
        
        assert sum(result.values()) == 0
        assert mock_repository.delete_logs_before.call_count == 4

    @pytest.mark.asyncio
    async def test_cleanup_old_logs_repository_error(self, log_service_no_cache, mock_repository):
        """Test cleanup with repository error."""
        mock_repository.delete_logs_before = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await log_service_no_cache.cleanup_old_logs(30)


class TestCacheIntegration:
    """Test cache integration functionality."""

    def test_cache_key_generation(self, log_service):
        """Test cache key generation for different operations."""
        # Test search cache key
        filter_obj = LogFilter(
            levels=[LogLevel.ERROR],
            services=[LogServiceType.API],
            page=1,
            page_size=50
        )
        
        search_key = log_service._generate_search_cache_key(filter_obj)
        assert isinstance(search_key, str)
        assert "log_search:" in search_key

    @pytest.mark.asyncio
    async def test_cache_error_handling(self, log_service_no_cache, mock_repository, sample_filter):
        """Test service functionality without cache."""
        search_result = LogListResponse(
            logs=[],
            total_count=0,
            page=1,
            page_size=50,
            has_next=False,
            has_prev=False
        )
        
        mock_repository.search_logs = AsyncMock(return_value=search_result)
        
        result = await log_service_no_cache.search_logs(sample_filter)
        
        assert result == search_result
        mock_repository.search_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_service_error_fallback(self, log_service, mock_repository, mock_cache, sample_filter):
        """Test fallback when cache service fails."""
        search_result = LogListResponse(
            logs=[],
            total_count=0,
            page=1,
            page_size=50,
            has_next=False,
            has_prev=False
        )
        
        mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
        mock_repository.search_logs = AsyncMock(return_value=search_result)
        
        result = await log_service.search_logs(sample_filter)
        
        assert result == search_result
        mock_repository.search_logs.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_service_error_wrapping(self, log_service, mock_repository):
        """Test that repository errors are wrapped in ServiceError."""
        mock_repository.get_log_by_id = AsyncMock(side_effect=Exception("Database connection failed"))
        
        with pytest.raises(RepositoryError) as exc_info:
            await log_service.get_log_by_id("log_id")
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, log_service_no_cache, mock_repository):
        """Test handling of validation errors."""
        # Test with valid filter but repository validation error
        valid_filter = LogFilter(page=1, page_size=50)
        mock_repository.search_logs = AsyncMock(side_effect=ValueError("Invalid page"))
        
        with pytest.raises(RepositoryError):
            await log_service_no_cache.search_logs(valid_filter)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, log_service_no_cache, mock_repository):
        """Test concurrent service operations."""
        # Mock multiple repository calls
        mock_repository.get_stats = AsyncMock(return_value=LogStats(
            total_count=100, error_count=10, warn_count=20, info_count=60, debug_count=10,
            service_stats={}, start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc)
        ))
        mock_repository.count_logs = AsyncMock(return_value=50)
        
        # Run concurrent operations
        tasks = [
            log_service_no_cache.get_stats(24),
            log_service_no_cache.count_logs(LogFilter()),
            log_service_no_cache.get_stats(12)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert results[0].total_count == 100
        assert results[1] == 50
        assert results[2].total_count == 100


if __name__ == "__main__":
    pytest.main([__file__])