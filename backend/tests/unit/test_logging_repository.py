"""
Tests for MongoDB logging repository implementation.

This module tests the MongoLogRepository class which implements the 
LogRepositoryInterface using Motor native MongoDB driver.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from nadle_backend.core.logging import (
    LogLevel,
    LogServiceType,
    LogSource,
    LogEntry,
    LogFilter,
    LogStats,
    LogContext,
    LogMetadata,
    RepositoryError,
)
from nadle_backend.logging.repositories.mongo_log_repository import MongoLogRepository


# Global fixtures for MongoDB repository tests
@pytest.fixture
def mock_database():
    """Create mock MongoDB database."""
    db = Mock()
    collection = Mock(spec=AsyncIOMotorCollection)
    db.__getitem__ = Mock(return_value=collection)
    db.logs = collection  # Add direct attribute access
    return db

@pytest.fixture
def mock_collection(mock_database):
    """Get mock collection from database."""
    return mock_database.logs

@pytest.fixture
def repository(mock_database):
    """Create MongoLogRepository instance with mock database."""
    return MongoLogRepository(mock_database)

@pytest.fixture
def sample_log_entry():
    """Create sample log entry for testing."""
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
            status_code=500
        ),
        metadata=LogMetadata(
            tags=["error", "api"],
            error_code="TEST_001"
        ),
        stack_trace="Traceback..."
    )


class TestMongoLogRepository:
    """Test MongoLogRepository implementation."""


class TestRepositoryInitialization:
    """Test repository initialization and setup."""

    def test_repository_creation(self, mock_database):
        """Test creating repository instance."""
        repo = MongoLogRepository(mock_database)
        assert repo.database == mock_database
        assert repo.logs_collection == mock_database.logs

    @pytest.mark.asyncio
    async def test_setup_indexes(self, repository, mock_collection):
        """Test index creation on setup."""
        mock_collection.create_indexes = AsyncMock()
        
        await repository.setup_indexes()
        
        # Verify index creation was called
        mock_collection.create_indexes.assert_called_once()
        
        # Check that indexes list was passed
        call_args = mock_collection.create_indexes.call_args[0][0]
        assert isinstance(call_args, list)
        assert len(call_args) >= 5  # Should have multiple indexes

    @pytest.mark.asyncio
    async def test_setup_indexes_error_handling(self, repository, mock_collection):
        """Test index creation error handling."""
        mock_collection.create_indexes = AsyncMock(side_effect=Exception("Index creation failed"))
        
        with pytest.raises(RepositoryError):
            await repository.setup_indexes()


class TestLogCreation:
    """Test log entry creation operations."""

    @pytest.mark.asyncio
    async def test_save_log_success(self, repository, mock_collection, sample_log_entry):
        """Test successful log creation."""
        mock_result = Mock()
        mock_result.inserted_id = "507f1f77bcf86cd799439011"
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        result = await repository.save_log(sample_log_entry)
        
        assert result.id == sample_log_entry.id
        mock_collection.insert_one.assert_called_once()
        
        # Verify the data passed to MongoDB
        call_args = mock_collection.insert_one.call_args[0][0]
        # ID should be excluded in the document
        assert "id" not in call_args
        assert "timestamp" in call_args
        assert "level" in call_args
        assert "service" in call_args
        assert "source" in call_args
        assert "message" in call_args

    @pytest.mark.asyncio
    async def test_save_log_with_context(self, repository, mock_collection, sample_log_entry):
        """Test log creation with context data."""
        mock_result = Mock()
        mock_result.inserted_id = sample_log_entry.id
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        await repository.save_log(sample_log_entry)
        
        call_args = mock_collection.insert_one.call_args[0][0]
        assert "context" in call_args
        assert call_args["context"]["user_id"] == "user123"
        assert call_args["context"]["endpoint"] == "/api/test"
        assert call_args["context"]["status_code"] == 500

    @pytest.mark.asyncio
    async def test_save_log_with_metadata(self, repository, mock_collection, sample_log_entry):
        """Test log creation with metadata."""
        mock_result = Mock()
        mock_result.inserted_id = sample_log_entry.id
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        await repository.save_log(sample_log_entry)
        
        call_args = mock_collection.insert_one.call_args[0][0]
        assert "metadata" in call_args
        assert call_args["metadata"]["tags"] == ["error", "api"]
        assert call_args["metadata"]["error_code"] == "TEST_001"

    @pytest.mark.asyncio
    async def test_save_log_minimal_data(self, repository, mock_collection):
        """Test log creation with minimal required data."""
        minimal_entry = LogEntry(
            id="507f1f77bcf86cd799439012",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            service=LogServiceType.WEB,
            source=LogSource.EXTERNAL,
            message="Minimal log entry"
        )
        
        mock_result = Mock()
        mock_result.inserted_id = minimal_entry.id
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        result = await repository.save_log(minimal_entry)
        
        assert result.id == minimal_entry.id
        call_args = mock_collection.insert_one.call_args[0][0]
        assert "context" not in call_args
        assert "metadata" not in call_args
        assert "stack_trace" not in call_args

    @pytest.mark.asyncio
    async def test_save_log_database_error(self, repository, mock_collection, sample_log_entry):
        """Test log creation database error handling."""
        mock_collection.insert_one = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError) as exc_info:
            await repository.save_log(sample_log_entry)
        
        assert "Failed to save log" in str(exc_info.value)


class TestLogRetrieval:
    """Test log entry retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_log_by_id_success(self, repository, mock_collection):
        """Test successful log retrieval by ID."""
        log_doc = {
            "_id": "507f1f77bcf86cd799439011",
            "timestamp": datetime.now(timezone.utc),
            "level": "ERROR",
            "service": "api",
            "source": "internal",
            "message": "Test error",
            "context": {
                "user_id": "user123",
                "endpoint": "/api/test"
            }
        }
        
        mock_collection.find_one = AsyncMock(return_value=log_doc)
        
        result = await repository.get_log_by_id("507f1f77bcf86cd799439011")
        
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.level == LogLevel.ERROR
        assert result.service == LogServiceType.API
        assert result.source == LogSource.INTERNAL
        assert result.message == "Test error"
        assert result.context.user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(self, repository, mock_collection):
        """Test log retrieval when ID not found."""
        mock_collection.find_one = AsyncMock(return_value=None)
        
        result = await repository.get_log_by_id("507f1f77bcf86cd799439013")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_log_by_id_database_error(self, repository, mock_collection):
        """Test log retrieval database error handling."""
        mock_collection.find_one = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await repository.get_log_by_id("507f1f77bcf86cd799439011")


class TestLogSearch:
    """Test log search and filtering operations."""

    @pytest.fixture
    def sample_filter(self):
        """Create sample log filter."""
        return LogFilter(
            start_time=datetime.now(timezone.utc) - timedelta(hours=24),
            end_time=datetime.now(timezone.utc),
            levels=[LogLevel.ERROR, LogLevel.WARN],
            services=[LogServiceType.API],
            sources=[LogSource.INTERNAL],
            search_query="authentication",
            user_id="user123",
            page=1,
            page_size=50
        )

    @pytest.mark.asyncio
    async def test_search_logs_success(self, repository, mock_collection, sample_filter):
        """Test successful log search."""
        sample_docs = [
            {
                "_id": "507f1f77bcf86cd799439011",
                "timestamp": datetime.now(timezone.utc),
                "level": "ERROR",
                "service": "api",
                "source": "internal",
                "message": "Authentication failed"
            },
            {
                "_id": "507f1f77bcf86cd799439012",
                "timestamp": datetime.now(timezone.utc),
                "level": "WARN",
                "service": "api", 
                "source": "internal",
                "message": "Authentication retry"
            }
        ]
        
        # Mock cursor for find operation
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=sample_docs)
        
        mock_collection.find = Mock(return_value=mock_cursor)
        mock_collection.count_documents = AsyncMock(return_value=2)
        
        result = await repository.search_logs(sample_filter)
        
        assert result.total_count == 2
        assert len(result.logs) == 2
        assert result.page == 1
        assert result.page_size == 50
        assert result.has_next == False
        assert result.has_prev == False
        
        # Verify filter was applied
        mock_collection.find.assert_called_once()
        find_query = mock_collection.find.call_args[0][0]
        
        # Check timestamp range
        assert "$gte" in find_query["timestamp"]
        assert "$lte" in find_query["timestamp"]
        
        # Check level filter
        assert find_query["level"]["$in"] == ["ERROR", "WARN"]
        
        # Check service filter
        assert find_query["service"]["$in"] == ["api"]
        
        # Check text search
        assert "$text" in find_query
        assert find_query["$text"]["$search"] == "authentication"

    @pytest.mark.asyncio
    async def test_search_logs_empty_result(self, repository, mock_collection, sample_filter):
        """Test search with no matching logs."""
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        mock_collection.find = Mock(return_value=mock_cursor)
        mock_collection.count_documents = AsyncMock(return_value=0)
        
        result = await repository.search_logs(sample_filter)
        
        assert result.total_count == 0
        assert len(result.logs) == 0
        assert result.has_next == False
        assert result.has_prev == False

    @pytest.mark.asyncio
    async def test_search_logs_pagination(self, repository, mock_collection):
        """Test search with pagination."""
        filter_obj = LogFilter(
            page=2,
            page_size=10
        )
        
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        mock_collection.find = Mock(return_value=mock_cursor)
        mock_collection.count_documents = AsyncMock(return_value=25)
        
        result = await repository.search_logs(filter_obj)
        
        assert result.page == 2
        assert result.page_size == 10
        assert result.has_next == True  # 25 total, page 2 of 10, so more pages
        assert result.has_prev == True  # page 2, so previous page exists
        
        # Verify skip and limit
        mock_cursor.skip.assert_called_with(10)  # Skip first 10 (page 2)
        mock_cursor.limit.assert_called_with(10)

    @pytest.mark.asyncio
    async def test_search_logs_complex_filter(self, repository, mock_collection):
        """Test search with complex filter conditions."""
        filter_obj = LogFilter(
            levels=[LogLevel.ERROR],
            services=[LogServiceType.API, LogServiceType.DATABASE],
            endpoint="/api/auth",
            status_codes=[401, 403],
            regions=["asia-northeast3"],
            search_query="failed login"
        )
        
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        mock_collection.find = Mock(return_value=mock_cursor)
        mock_collection.count_documents = AsyncMock(return_value=0)
        
        await repository.search_logs(filter_obj)
        
        find_query = mock_collection.find.call_args[0][0]
        
        # Check complex filter conditions
        assert find_query["level"]["$in"] == ["ERROR"]
        assert set(find_query["service"]["$in"]) == {"api", "database"}
        # Endpoint uses regex search, so check for regex pattern
        assert "$regex" in find_query["context.endpoint"]
        assert "/api/auth" in find_query["context.endpoint"]["$regex"]
        assert set(find_query["context.status_code"]["$in"]) == {401, 403}
        assert find_query["context.region"]["$in"] == ["asia-northeast3"]

    @pytest.mark.asyncio
    async def test_search_logs_database_error(self, repository, mock_collection, sample_filter):
        """Test search database error handling."""
        mock_collection.find = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await repository.search_logs(sample_filter)


class TestLogStatistics:
    """Test log statistics operations."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, repository, mock_collection):
        """Test successful statistics calculation."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        end_time = datetime.now(timezone.utc)
        
        # Mock aggregation pipeline results
        stats_result = [
            {
                "_id": None,
                "total_count": 1000,
                "error_count": 50,
                "warn_count": 150,
                "info_count": 700,
                "debug_count": 100
            }
        ]
        
        service_result = [
            {"_id": "api", "count": 600},
            {"_id": "web", "count": 300},
            {"_id": "database", "count": 100}
        ]
        
        source_result = [
            {"_id": "internal", "count": 800},
            {"_id": "external", "count": 200}
        ]
        
        # Create mock aggregate cursors with different return values based on call count
        call_count = 0
        def mock_aggregate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_cursor = Mock()
            
            if call_count == 1:
                # First call: main stats
                mock_cursor.to_list = AsyncMock(return_value=stats_result)
                # Mock async iteration (not used in first call but needed for interface)
                async def async_iter_stats():
                    for item in stats_result:
                        yield item
                mock_cursor.__aiter__ = Mock(return_value=async_iter_stats())
            elif call_count == 2:
                # Second call: service stats
                async def async_iter_service():
                    for item in service_result:
                        yield item
                mock_cursor.__aiter__ = Mock(return_value=async_iter_service())
            else:
                # Third call: source stats
                async def async_iter_source():
                    for item in source_result:
                        yield item
                mock_cursor.__aiter__ = Mock(return_value=async_iter_source())
            
            return mock_cursor
        
        mock_collection.aggregate = Mock(side_effect=mock_aggregate)
        
        result = await repository.get_stats(start_time, end_time)
        
        assert result.total_count == 1000
        assert result.error_count == 50
        assert result.warn_count == 150
        assert result.info_count == 700
        assert result.debug_count == 100
        assert result.service_stats["api"] == 600
        assert result.service_stats["web"] == 300
        assert result.service_stats["database"] == 100
        assert result.start_time == start_time
        assert result.end_time == end_time

    @pytest.mark.asyncio
    async def test_get_stats_no_data(self, repository, mock_collection):
        """Test statistics with no data."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        mock_aggregate_cursor = Mock()
        mock_aggregate_cursor.to_list = AsyncMock(return_value=[])
        mock_collection.aggregate = Mock(return_value=mock_aggregate_cursor)
        
        result = await repository.get_stats(start_time, end_time)
        
        assert result.total_count == 0
        assert result.error_count == 0
        assert result.warn_count == 0
        assert result.info_count == 0
        assert result.debug_count == 0
        assert result.service_stats == {}

    @pytest.mark.asyncio
    async def test_get_stats_database_error(self, repository, mock_collection):
        """Test statistics database error handling."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        end_time = datetime.now(timezone.utc)
        
        mock_collection.aggregate = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await repository.get_stats(start_time, end_time)


class TestLogCount:
    """Test log counting operations."""

    @pytest.mark.asyncio
    async def test_count_logs_success(self, repository, mock_collection):
        """Test successful log counting."""
        filter_obj = LogFilter(
            levels=[LogLevel.ERROR],
            services=[LogServiceType.API]
        )
        
        mock_collection.count_documents = AsyncMock(return_value=42)
        
        result = await repository.count_logs(filter_obj)
        
        assert result == 42
        mock_collection.count_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_logs_zero(self, repository, mock_collection):
        """Test counting with zero results."""
        filter_obj = LogFilter(
            levels=[LogLevel.DEBUG]
        )
        
        mock_collection.count_documents = AsyncMock(return_value=0)
        
        result = await repository.count_logs(filter_obj)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_count_logs_database_error(self, repository, mock_collection):
        """Test count database error handling."""
        filter_obj = LogFilter()
        
        mock_collection.count_documents = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await repository.count_logs(filter_obj)


class TestLogCleanup:
    """Test log cleanup operations."""

    @pytest.mark.asyncio
    async def test_delete_logs_before_success(self, repository, mock_collection):
        """Test successful log cleanup."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        mock_result = Mock()
        mock_result.deleted_count = 150
        mock_collection.delete_many = AsyncMock(return_value=mock_result)
        
        result = await repository.delete_logs_before(cutoff_date)
        
        assert result == 150
        mock_collection.delete_many.assert_called_once()
        
        # Verify the delete query uses correct timestamp filter
        delete_query = mock_collection.delete_many.call_args[0][0]
        assert "timestamp" in delete_query
        assert "$lt" in delete_query["timestamp"]

    @pytest.mark.asyncio
    async def test_delete_logs_before_nothing_to_delete(self, repository, mock_collection):
        """Test cleanup when no old logs exist."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        mock_result = Mock()
        mock_result.deleted_count = 0
        mock_collection.delete_many = AsyncMock(return_value=mock_result)
        
        result = await repository.delete_logs_before(cutoff_date)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_delete_logs_before_database_error(self, repository, mock_collection):
        """Test cleanup database error handling."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        mock_collection.delete_many = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(RepositoryError):
            await repository.delete_logs_before(cutoff_date)


class TestDataConversion:
    """Test data conversion between MongoDB documents and domain entities."""

    @pytest.mark.asyncio
    async def test_save_log_data_structure(self, repository, mock_collection, sample_log_entry):
        """Test that save_log uses correct data structure for MongoDB."""
        mock_result = Mock()
        mock_result.inserted_id = "507f1f77bcf86cd799439011"
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        await repository.save_log(sample_log_entry)
        
        # Verify the data structure passed to MongoDB
        call_args = mock_collection.insert_one.call_args[0][0]
        
        # Basic fields should be present
        assert "timestamp" in call_args
        assert "level" in call_args
        assert "service" in call_args
        assert "source" in call_args
        assert "message" in call_args
        
        # Context should be properly structured
        if "context" in call_args:
            assert isinstance(call_args["context"], dict)
        
        # Metadata should be properly structured
        if "metadata" in call_args:
            assert isinstance(call_args["metadata"], dict)

    @pytest.mark.asyncio
    async def test_save_log_minimal_data_structure(self, repository, mock_collection):
        """Test that save_log handles minimal data correctly."""
        minimal_entry = LogEntry(
            id="507f1f77bcf86cd799439012",
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            service=LogServiceType.WEB,
            source=LogSource.EXTERNAL,
            message="Minimal log"
        )
        
        mock_result = Mock()
        mock_result.inserted_id = minimal_entry.id
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        await repository.save_log(minimal_entry)
        
        call_args = mock_collection.insert_one.call_args[0][0]
        
        # Basic fields should be present
        assert "timestamp" in call_args
        assert "level" in call_args
        assert "service" in call_args
        assert "source" in call_args
        assert "message" in call_args
        
        # Optional fields should not be present (due to exclude_none=True)
        assert "id" not in call_args  # Excluded explicitly


if __name__ == "__main__":
    pytest.main([__file__])