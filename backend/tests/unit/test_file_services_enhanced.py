"""Enhanced unit tests for file services functionality."""

import pytest
from unittest.mock import MagicMock
from nadle_backend.services.file_validator import validate_file_type, validate_file_size, validate_file_extension


class TestFileValidator:
    """Test file validation functionality."""
    
    def test_validate_file_type_success(self):
        """Test successful file type validation."""
        # Arrange
        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        
        # Act & Assert
        assert validate_file_type(mock_file) is True
        
        mock_file.content_type = "image/png"
        assert validate_file_type(mock_file) is True
    
    def test_validate_file_type_failure(self):
        """Test file type validation failure."""
        # Arrange
        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"
        
        # Act & Assert
        assert validate_file_type(mock_file) is False
        
        mock_file.content_type = "text/plain"
        assert validate_file_type(mock_file) is False
    
    def test_validate_file_size_success(self):
        """Test successful file size validation."""
        # Arrange
        mock_file = MagicMock()
        mock_file.size = 1024 * 1024  # 1MB
        
        # Act & Assert
        assert validate_file_size(mock_file) is True
    
    def test_validate_file_size_failure(self):
        """Test file size validation failure."""
        # Arrange
        mock_file = MagicMock()
        mock_file.size = 6 * 1024 * 1024  # 6MB (over limit)
        
        # Act & Assert
        assert validate_file_size(mock_file) is False
    
    def test_validate_file_extension_success(self):
        """Test successful file extension validation."""
        # Arrange
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        
        # Act & Assert
        assert validate_file_extension(mock_file) is True
        
        mock_file.filename = "test.png"
        mock_file.content_type = "image/png"
        assert validate_file_extension(mock_file) is True
    
    def test_validate_file_extension_failure(self):
        """Test file extension validation failure."""
        # Arrange - wrong extension for content type
        mock_file = MagicMock()
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/png"  # mismatch
        
        # Act & Assert
        assert validate_file_extension(mock_file) is False