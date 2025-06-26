"""
File Metadata Module Unit Tests

Tests for file metadata functions including:
- File metadata extraction
- MongoDB document creation
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from src.services.file_metadata import (
    extract_file_metadata,
    create_file_document
)


class TestFileMetadata:
    """Test cases for file metadata functions"""

    def test_extract_file_metadata(self):
        """Test file metadata extraction"""
        # Create mock file object
        mock_file = Mock()
        mock_file.filename = "test_image.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 1024 * 1024  # 1MB
        
        metadata = extract_file_metadata(mock_file, "/uploads/2025/06/uuid.jpg")
        
        # Check required fields
        assert metadata["original_filename"] == "test_image.jpg"
        assert metadata["content_type"] == "image/jpeg"
        assert metadata["file_size"] == 1024 * 1024
        assert metadata["file_path"] == "/uploads/2025/06/uuid.jpg"
        assert "upload_timestamp" in metadata
        assert isinstance(metadata["upload_timestamp"], datetime)
        
        # Test with different file types
        test_cases = [
            ("photo.png", "image/png", 2048),
            ("animation.gif", "image/gif", 512000),
            ("modern.webp", "image/webp", 750000)
        ]
        
        for filename, content_type, size in test_cases:
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.size = size
            
            metadata = extract_file_metadata(mock_file, f"/path/{filename}")
            
            assert metadata["original_filename"] == filename
            assert metadata["content_type"] == content_type
            assert metadata["file_size"] == size
    
    def test_create_file_document(self):
        """Test MongoDB document creation"""
        # Test basic document creation
        metadata = {
            "original_filename": "test.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "file_path": "/uploads/2025/06/test.jpg",
            "upload_timestamp": datetime.now()
        }
        
        document = create_file_document(metadata)
        
        # Check required fields for MongoDB
        assert "file_id" in document
        assert "original_filename" in document
        assert "content_type" in document
        assert "file_size" in document
        assert "file_path" in document
        assert "upload_timestamp" in document
        assert "status" in document
        assert document["status"] == "active"
        
        # Check file_id is a string (UUID format)
        assert isinstance(document["file_id"], str)
        assert len(document["file_id"]) == 36  # UUID length with hyphens
        
        # Test with attachment info
        metadata_with_attachment = metadata.copy()
        metadata_with_attachment.update({
            "attachment_type": "post",
            "attachment_id": "post_123"
        })
        
        document = create_file_document(metadata_with_attachment)
        assert document["attachment_type"] == "post"
        assert document["attachment_id"] == "post_123"
    
    def test_create_file_document_uniqueness(self):
        """Test that each document gets unique file_id"""
        metadata = {
            "original_filename": "test.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "file_path": "/uploads/test.jpg",
            "upload_timestamp": datetime.now()
        }
        
        documents = [create_file_document(metadata) for _ in range(5)]
        file_ids = [doc["file_id"] for doc in documents]
        
        # All file_ids should be unique
        assert len(set(file_ids)) == 5