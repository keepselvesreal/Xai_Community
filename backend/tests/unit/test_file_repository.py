"""
File Repository Module Unit Tests

Tests for file repository functions including:
- File record saving to MongoDB
- File record retrieval by ID
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from src.repositories.file_repository import (
    save_file_record,
    find_file_by_id
)


class TestFileRepository:
    """Test cases for file repository functions"""

    @pytest.mark.asyncio
    async def test_save_file_record(self):
        """Test saving file record to MongoDB"""
        # Mock file document
        file_document = {
            "file_id": "test-uuid-123",
            "original_filename": "test.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "file_path": "/uploads/2025/06/test.jpg",
            "upload_timestamp": datetime.now(),
            "status": "active"
        }
        
        # Mock database operations
        with patch('src.repositories.file_repository.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_get_db.return_value = mock_db
            
            # Mock successful insert
            mock_result = Mock()
            mock_result.inserted_id = "mongo_object_id"
            mock_collection.insert_one.return_value = mock_result
            
            # Test successful save
            result = await save_file_record(file_document)
            
            assert result is True
            mock_collection.insert_one.assert_called_once_with(file_document)
        
        # Test save failure
        with patch('src.repositories.file_repository.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_get_db.return_value = mock_db
            
            # Mock insert failure
            mock_collection.insert_one.side_effect = Exception("Database error")
            
            result = await save_file_record(file_document)
            assert result is False

    @pytest.mark.asyncio
    async def test_find_file_by_id(self):
        """Test finding file record by ID"""
        file_id = "test-uuid-123"
        expected_document = {
            "file_id": file_id,
            "original_filename": "test.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "file_path": "/uploads/2025/06/test.jpg",
            "upload_timestamp": datetime.now(),
            "status": "active"
        }
        
        # Mock successful find
        with patch('src.repositories.file_repository.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_get_db.return_value = mock_db
            
            mock_collection.find_one.return_value = expected_document
            
            result = await find_file_by_id(file_id)
            
            assert result == expected_document
            mock_collection.find_one.assert_called_once_with({"file_id": file_id})
        
        # Test file not found
        with patch('src.repositories.file_repository.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_get_db.return_value = mock_db
            
            mock_collection.find_one.return_value = None
            
            result = await find_file_by_id("nonexistent-id")
            assert result is None
        
        # Test database error
        with patch('src.repositories.file_repository.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_get_db.return_value = mock_db
            
            mock_collection.find_one.side_effect = Exception("Database error")
            
            result = await find_file_by_id(file_id)
            assert result is None