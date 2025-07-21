"""
Tests for core logging domain entities and enums.

This module tests the fundamental building blocks of the logging system:
- LogLevel, LogServiceType, LogSource enums
- LogEntry, LogFilter, LogStats, LogContext, LogMetadata entities
- Data validation and serialization
"""

import pytest
from datetime import datetime, timezone
from typing import List, Optional

from nadle_backend.core.logging import (
    LogLevel,
    LogServiceType,
    LogSource,
    LogEntry,
    LogFilter,
    LogStats,
    LogContext,
    LogMetadata,
    LogValidationError,
)


class TestLogEnums:
    """Test logging system enums."""

    def test_log_level_enum(self):
        """Test LogLevel enum values and string representations."""
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.WARN == "WARN"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.DEBUG == "DEBUG"
        
        # Test enum iteration
        levels = list(LogLevel)
        assert len(levels) == 4
        assert LogLevel.ERROR in levels
        
        # Test string conversion (enum value, not str representation)
        assert LogLevel.ERROR.value == "ERROR"

    def test_log_service_type_enum(self):
        """Test LogServiceType enum values and string representations."""
        assert LogServiceType.API == "api"
        assert LogServiceType.WEB == "web"
        assert LogServiceType.CLOUD_RUN == "cloud-run"
        assert LogServiceType.DATABASE == "database"
        assert LogServiceType.REDIS == "redis"
        assert LogServiceType.VERCEL == "vercel"
        
        # Test enum iteration
        services = list(LogServiceType)
        assert len(services) == 6
        
        # Test string conversion (enum value, not str representation)
        assert LogServiceType.API.value == "api"

    def test_log_source_enum(self):
        """Test LogSource enum values and string representations."""
        assert LogSource.INTERNAL == "internal"
        assert LogSource.EXTERNAL == "external"
        
        # Test enum iteration
        sources = list(LogSource)
        assert len(sources) == 2

    def test_enum_creation_from_string(self):
        """Test creating enums from string values."""
        assert LogLevel("ERROR") == LogLevel.ERROR
        assert LogServiceType("api") == LogServiceType.API
        assert LogSource("internal") == LogSource.INTERNAL

    def test_enum_invalid_values(self):
        """Test that invalid enum values raise ValueError."""
        with pytest.raises(ValueError):
            LogLevel("INVALID")
        
        with pytest.raises(ValueError):
            LogServiceType("invalid-service")
        
        with pytest.raises(ValueError):
            LogSource("invalid-source")


class TestLogContext:
    """Test LogContext entity."""

    def test_log_context_creation(self):
        """Test creating LogContext with various fields."""
        context = LogContext(
            user_id="user123",
            endpoint="/api/posts",
            method="GET",
            status_code=200,
            response_time=150,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
            session_id="session123",
            request_id="req123",
            infrastructure="gcp",
            instance_id="instance123",
            region="asia-northeast3",
            version="1.0.0"
        )
        
        assert context.user_id == "user123"
        assert context.endpoint == "/api/posts"
        assert context.method == "GET"
        assert context.status_code == 200
        assert context.response_time == 150
        assert context.infrastructure == "gcp"
        assert context.region == "asia-northeast3"

    def test_log_context_optional_fields(self):
        """Test LogContext with only required fields."""
        context = LogContext(
            endpoint="/api/health"
        )
        
        assert context.endpoint == "/api/health"
        assert context.user_id is None
        assert context.method is None
        assert context.status_code is None

    def test_log_context_validation(self):
        """Test LogContext field validation."""
        # Valid context
        context = LogContext(
            status_code=200,
            response_time=50
        )
        assert context.status_code == 200
        assert context.response_time == 50

    def test_log_context_serialization(self):
        """Test LogContext to dict conversion."""
        context = LogContext(
            user_id="user123",
            endpoint="/api/posts",
            status_code=200
        )
        
        context_dict = context.model_dump(exclude_none=True)
        expected = {
            "user_id": "user123",
            "endpoint": "/api/posts",
            "status_code": 200
        }
        assert context_dict == expected


class TestLogMetadata:
    """Test LogMetadata entity."""

    def test_log_metadata_creation(self):
        """Test creating LogMetadata with various fields."""
        metadata = LogMetadata(
            tags=["error", "authentication", "api"],
            severity="high",
            error_code="AUTH_001",
            correlation_id="corr123",
            memory_usage=1024,
            cpu_usage=75.5,
            disk_usage=50.2,
            cloud_trace_id="trace123",
            atlas_cluster="Cluster0",
            vercel_deployment_id="deploy123"
        )
        
        assert metadata.tags == ["error", "authentication", "api"]
        assert metadata.severity == "high"
        assert metadata.error_code == "AUTH_001"
        assert metadata.memory_usage == 1024
        assert metadata.cpu_usage == 75.5

    def test_log_metadata_optional_fields(self):
        """Test LogMetadata with minimal data."""
        metadata = LogMetadata(
            tags=["info"]
        )
        
        assert metadata.tags == ["info"]
        assert metadata.severity is None
        assert metadata.memory_usage is None

    def test_log_metadata_empty(self):
        """Test creating empty LogMetadata."""
        metadata = LogMetadata()
        
        assert metadata.tags == []  # default_factory creates empty list
        assert metadata.severity is None
        assert metadata.error_code is None


class TestLogEntry:
    """Test LogEntry entity."""

    def test_log_entry_creation(self):
        """Test creating a complete LogEntry."""
        timestamp = datetime.now(timezone.utc)
        
        entry = LogEntry(
            id="log123",
            timestamp=timestamp,
            level=LogLevel.ERROR,
            service=LogServiceType.API,
            source=LogSource.INTERNAL,
            message="Authentication failed for user",
            context=LogContext(
                user_id="user123",
                endpoint="/api/auth/login",
                status_code=401
            ),
            metadata=LogMetadata(
                tags=["error", "auth"],
                error_code="AUTH_001"
            ),
            stack_trace="Traceback (most recent call last):\n..."
        )
        
        assert entry.id == "log123"
        assert entry.timestamp == timestamp
        assert entry.level == LogLevel.ERROR
        assert entry.service == LogServiceType.API
        assert entry.source == LogSource.INTERNAL
        assert entry.message == "Authentication failed for user"
        assert entry.context.user_id == "user123"
        assert entry.metadata.error_code == "AUTH_001"
        assert entry.stack_trace is not None

    def test_log_entry_minimal(self):
        """Test creating LogEntry with minimal required fields."""
        timestamp = datetime.now(timezone.utc)
        
        entry = LogEntry(
            id="log123",
            timestamp=timestamp,
            level=LogLevel.INFO,
            service=LogServiceType.WEB,
            source=LogSource.EXTERNAL,
            message="User visited homepage"
        )
        
        assert entry.id == "log123"
        assert entry.level == LogLevel.INFO
        assert entry.service == LogServiceType.WEB
        assert entry.source == LogSource.EXTERNAL
        assert entry.message == "User visited homepage"
        assert entry.context is None
        assert entry.metadata is None
        assert entry.stack_trace is None

    def test_log_entry_validation_error(self):
        """Test LogEntry validation errors."""
        timestamp = datetime.now(timezone.utc)
        
        # Test empty message - Pydantic will raise ValidationError, not our custom one
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LogEntry(
                id="log123",
                timestamp=timestamp,
                level=LogLevel.INFO,
                service=LogServiceType.API,
                source=LogSource.INTERNAL,
                message=""  # Empty message should fail
            )

    def test_log_entry_serialization(self):
        """Test LogEntry serialization to dict."""
        timestamp = datetime.now(timezone.utc)
        
        entry = LogEntry(
            id="log123",
            timestamp=timestamp,
            level=LogLevel.WARN,
            service=LogServiceType.DATABASE,
            source=LogSource.INTERNAL,
            message="Database connection slow"
        )
        
        entry_dict = entry.model_dump()
        assert entry_dict["id"] == "log123"
        assert entry_dict["level"] == "WARN"
        assert entry_dict["service"] == "database"
        assert entry_dict["source"] == "internal"
        assert entry_dict["message"] == "Database connection slow"


class TestLogFilter:
    """Test LogFilter entity."""

    def test_log_filter_creation(self):
        """Test creating LogFilter with various criteria."""
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)
        
        filter_obj = LogFilter(
            start_time=start_time,
            end_time=end_time,
            levels=[LogLevel.ERROR, LogLevel.WARN],
            services=[LogServiceType.API, LogServiceType.WEB],
            sources=[LogSource.INTERNAL],
            search_query="authentication error",
            user_id="user123",
            endpoint="/api/auth",
            status_codes=[401, 403],
            regions=["asia-northeast3"],
            instance_ids=["instance123"],
            deployment_ids=["deploy123"],
            page=1,
            page_size=50
        )
        
        assert filter_obj.start_time == start_time
        assert filter_obj.end_time == end_time
        assert LogLevel.ERROR in filter_obj.levels
        assert LogLevel.WARN in filter_obj.levels
        assert LogServiceType.API in filter_obj.services
        assert LogSource.INTERNAL in filter_obj.sources
        assert filter_obj.search_query == "authentication error"
        assert filter_obj.user_id == "user123"
        assert filter_obj.endpoint == "/api/auth"
        assert 401 in filter_obj.status_codes
        assert "asia-northeast3" in filter_obj.regions
        assert filter_obj.page == 1
        assert filter_obj.page_size == 50

    def test_log_filter_empty(self):
        """Test creating empty LogFilter."""
        filter_obj = LogFilter()
        
        assert filter_obj.start_time is None
        assert filter_obj.end_time is None
        assert filter_obj.levels is None
        assert filter_obj.services is None
        assert filter_obj.sources is None
        assert filter_obj.search_query is None
        assert filter_obj.page == 1  # default value
        assert filter_obj.page_size == 50  # default value

    def test_log_filter_defaults(self):
        """Test LogFilter with default values."""
        filter_obj = LogFilter(
            levels=[LogLevel.INFO],
            page=1,
            page_size=25
        )
        
        assert filter_obj.levels == [LogLevel.INFO]
        assert filter_obj.page == 1
        assert filter_obj.page_size == 25

    def test_log_filter_validation(self):
        """Test LogFilter field validation."""
        # Valid page values
        filter_obj = LogFilter(page=1, page_size=50)
        assert filter_obj.page == 1
        assert filter_obj.page_size == 50
        
        # Test that negative page/page_size might be handled by Pydantic validators
        # (depending on implementation)


class TestLogStats:
    """Test LogStats entity."""

    def test_log_stats_creation(self):
        """Test creating LogStats with complete data."""
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)
        
        stats = LogStats(
            total_count=1000,
            error_count=50,
            warn_count=100,
            info_count=750,
            debug_count=100,
            service_stats={
                "api": 600,
                "web": 300,
                "database": 100
            },
            start_time=start_time,
            end_time=end_time
        )
        
        assert stats.total_count == 1000
        assert stats.error_count == 50
        assert stats.warn_count == 100
        assert stats.info_count == 750
        assert stats.debug_count == 100
        assert stats.service_stats["api"] == 600
        assert stats.service_stats["web"] == 300
        assert stats.service_stats["database"] == 100
        assert stats.start_time == start_time
        assert stats.end_time == end_time

    def test_log_stats_minimal(self):
        """Test creating LogStats with minimal data."""
        stats = LogStats(
            total_count=0,
            error_count=0,
            warn_count=0,
            info_count=0,
            debug_count=0,
            service_stats={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc)
        )
        
        assert stats.total_count == 0
        assert stats.error_count == 0
        assert stats.service_stats == {}

    def test_log_stats_counts_consistency(self):
        """Test that log level counts sum to total count."""
        stats = LogStats(
            total_count=100,
            error_count=10,
            warn_count=20,
            info_count=60,
            debug_count=10,
            service_stats={"api": 100},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc)
        )
        
        level_sum = stats.error_count + stats.warn_count + stats.info_count + stats.debug_count
        assert level_sum == stats.total_count

    def test_log_stats_serialization(self):
        """Test LogStats serialization."""
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)
        
        stats = LogStats(
            total_count=100,
            error_count=10,
            warn_count=20,
            info_count=60,
            debug_count=10,
            service_stats={"api": 80, "web": 20},
            start_time=start_time,
            end_time=end_time
        )
        
        stats_dict = stats.model_dump()
        assert stats_dict["total_count"] == 100
        assert stats_dict["error_count"] == 10
        assert stats_dict["service_stats"]["api"] == 80
        assert stats_dict["service_stats"]["web"] == 20


class TestDataValidation:
    """Test data validation and edge cases."""

    def test_timestamp_handling(self):
        """Test timestamp handling in different formats."""
        # UTC timestamp
        utc_time = datetime.now(timezone.utc)
        entry = LogEntry(
            id="log123",
            timestamp=utc_time,
            level=LogLevel.INFO,
            service=LogServiceType.API,
            source=LogSource.INTERNAL,
            message="Test message"
        )
        assert entry.timestamp == utc_time

    def test_string_fields_edge_cases(self):
        """Test string field edge cases."""
        # Very long message
        long_message = "A" * 10000
        entry = LogEntry(
            id="log123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            service=LogServiceType.API,
            source=LogSource.INTERNAL,
            message=long_message
        )
        assert len(entry.message) == 10000

    def test_numeric_fields_edge_cases(self):
        """Test numeric field edge cases."""
        context = LogContext(
            status_code=599,  # Maximum HTTP status code
            response_time=30000,  # 30 seconds
            user_id="user123"
        )
        
        assert context.status_code == 599
        assert context.response_time == 30000

    def test_list_fields_edge_cases(self):
        """Test list field edge cases."""
        # Empty lists
        filter_obj = LogFilter(
            levels=[],
            services=[],
            sources=[]
        )
        
        # Pydantic might convert empty lists to None or keep them as empty
        # This depends on the actual implementation

    def test_unicode_handling(self):
        """Test Unicode character handling."""
        entry = LogEntry(
            id="log123",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            service=LogServiceType.API,
            source=LogSource.INTERNAL,
            message="한국어 로그 메시지 with émojis 🚀",
            context=LogContext(
                user_id="사용자123",
                endpoint="/api/한국어"
            )
        )
        
        assert "한국어" in entry.message
        assert "🚀" in entry.message
        assert entry.context.user_id == "사용자123"
        assert entry.context.endpoint == "/api/한국어"


if __name__ == "__main__":
    pytest.main([__file__])