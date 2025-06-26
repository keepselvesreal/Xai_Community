"""
File Validator Module Unit Tests

Tests for file validation functions including:
- File type validation (MIME type and extension)
- File size validation
- File extension and MIME type consistency validation
"""

import pytest
from unittest.mock import Mock
from src.services.file_validator import (
    validate_file_type,
    validate_file_size,
    validate_file_extension
)


class TestFileValidator:
    """Test cases for file validation functions"""

    def test_validate_file_type(self):
        """Test file type validation for allowed image formats"""
        # Test valid image types
        valid_types = [
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/webp'
        ]
        
        for mime_type in valid_types:
            mock_file = Mock()
            mock_file.content_type = mime_type
            assert validate_file_type(mock_file) is True, f"Should accept {mime_type}"
        
        # Test invalid types
        invalid_types = [
            'application/pdf',
            'text/plain',
            'video/mp4',
            'audio/mp3',
            'application/exe',
            'text/html'
        ]
        
        for mime_type in invalid_types:
            mock_file = Mock()
            mock_file.content_type = mime_type
            assert validate_file_type(mock_file) is False, f"Should reject {mime_type}"
    
    def test_validate_file_size(self):
        """Test file size validation with 5MB limit"""
        # Test valid sizes (under 5MB)
        valid_sizes = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            1024 * 1024 * 3,  # 3MB
            1024 * 1024 * 5 - 1  # Just under 5MB
        ]
        
        for size in valid_sizes:
            mock_file = Mock()
            mock_file.size = size
            assert validate_file_size(mock_file) is True, f"Should accept size {size}"
            
        # Test invalid sizes (5MB and over)
        invalid_sizes = [
            1024 * 1024 * 5,  # Exactly 5MB
            1024 * 1024 * 6,  # 6MB
            1024 * 1024 * 10,  # 10MB
            1024 * 1024 * 50   # 50MB
        ]
        
        for size in invalid_sizes:
            mock_file = Mock()
            mock_file.size = size
            assert validate_file_size(mock_file) is False, f"Should reject size {size}"
    
    def test_validate_file_extension(self):
        """Test file extension and MIME type consistency validation"""
        # Test valid extension-MIME combinations
        valid_combinations = [
            ('image.jpg', 'image/jpeg'),
            ('image.jpeg', 'image/jpeg'),
            ('image.png', 'image/png'),
            ('image.gif', 'image/gif'),
            ('image.webp', 'image/webp'),
            ('photo.JPG', 'image/jpeg'),  # Case insensitive
            ('picture.PNG', 'image/png')   # Case insensitive
        ]
        
        for filename, mime_type in valid_combinations:
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = mime_type
            assert validate_file_extension(mock_file) is True, \
                f"Should accept {filename} with {mime_type}"
        
        # Test invalid extension-MIME combinations
        invalid_combinations = [
            ('image.jpg', 'image/png'),  # Wrong MIME for extension
            ('image.png', 'image/jpeg'), # Wrong MIME for extension
            ('document.pdf', 'application/pdf'),  # Non-image file
            ('image.txt', 'text/plain'),  # Text file with image name
            ('image.exe', 'application/exe')  # Executable disguised as image
        ]
        
        for filename, mime_type in invalid_combinations:
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = mime_type
            assert validate_file_extension(mock_file) is False, \
                f"Should reject {filename} with {mime_type}"
        
        # Test edge cases
        mock_file = Mock()
        mock_file.filename = "no_extension"
        mock_file.content_type = "image/jpeg"
        assert validate_file_extension(mock_file) is False, \
            "Should reject file without extension"
        
        mock_file = Mock()
        mock_file.filename = ".hidden_file"
        mock_file.content_type = "image/png"
        assert validate_file_extension(mock_file) is False, \
            "Should reject hidden file without proper extension"