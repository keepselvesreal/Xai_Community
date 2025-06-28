"""
File Storage Module Unit Tests

Tests for file storage functions including:
- File path generation (UUID-based with date structure)
- File saving to disk
- Directory structure creation
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch
from nadle_backend.services.file_storage import (
    generate_file_path,
    save_file_to_disk,
    create_directory_structure
)


class TestFileStorage:
    """Test cases for file storage functions"""

    def test_generate_file_path(self):
        """Test UUID-based file path generation with date structure"""
        # Test basic path generation
        filename = "test_image.jpg"
        file_path = generate_file_path(filename)
        
        # Check path structure: uploads/YYYY/MM/uuid.extension
        parts = file_path.split('/')
        assert len(parts) == 4
        assert parts[0] == 'uploads'
        assert len(parts[1]) == 4  # Year (YYYY)
        assert len(parts[2]) == 2  # Month (MM)
        
        # Check file extension preserved
        assert file_path.endswith('.jpg')
        
        # Test different extensions
        test_files = [
            ("image.png", ".png"),
            ("photo.jpeg", ".jpeg"),
            ("animation.gif", ".gif"),
            ("modern.webp", ".webp")
        ]
        
        for filename, expected_ext in test_files:
            path = generate_file_path(filename)
            assert path.endswith(expected_ext)
        
        # Test uniqueness
        paths = [generate_file_path("test.jpg") for _ in range(10)]
        assert len(set(paths)) == 10, "All generated paths should be unique"
    
    def test_save_file_to_disk(self):
        """Test saving file data to disk"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test successful file save
            file_content = b"test image data"
            file_path = os.path.join(temp_dir, "test.jpg")
            
            # Create directory structure
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file
            result = save_file_to_disk(file_content, file_path)
            
            assert result is True
            assert os.path.exists(file_path)
            
            # Verify content
            with open(file_path, 'rb') as f:
                saved_content = f.read()
            assert saved_content == file_content
        
        # Test save failure (invalid path)
        invalid_path = "/nonexistent/directory/file.jpg"
        result = save_file_to_disk(b"data", invalid_path)
        assert result is False
    
    def test_create_directory_structure(self):
        """Test directory structure creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test creating nested directory structure
            target_path = os.path.join(temp_dir, "uploads", "2025", "06", "images")
            
            result = create_directory_structure(target_path)
            
            assert result is True
            assert os.path.exists(target_path)
            assert os.path.isdir(target_path)
            
            # Test creating already existing directory
            result = create_directory_structure(target_path)
            assert result is True  # Should still succeed
            
            # Test with file path (should create parent directories)
            file_path = os.path.join(temp_dir, "uploads", "2025", "07", "test.jpg")
            result = create_directory_structure(file_path)
            
            assert result is True
            assert os.path.exists(os.path.dirname(file_path))
        
        # Test creation failure (permission denied simulation)
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            result = create_directory_structure("/restricted/path")
            assert result is False