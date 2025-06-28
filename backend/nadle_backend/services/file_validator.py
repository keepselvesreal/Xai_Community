"""
File Validator Module

Provides validation functions for file uploads including:
- File type validation (MIME type checking)
- File size validation (maximum size limits)
- File extension and MIME type consistency validation
"""

import os
from typing import Any, Protocol


class FileProtocol(Protocol):
    """Protocol defining the interface for file objects"""
    content_type: str
    size: int
    filename: str


# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
ALLOWED_MIME_TYPES = frozenset({
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/gif',
    'image/webp'
})

# Extension to MIME type mapping
EXTENSION_MIME_MAP = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp'
}


def validate_file_type(file: Any) -> bool:
    """
    Validate if file type is allowed based on MIME type
    
    Args:
        file: File object with content_type attribute
        
    Returns:
        bool: True if file type is allowed, False otherwise
    """
    try:
        return file.content_type in ALLOWED_MIME_TYPES
    except AttributeError:
        return False


def validate_file_size(file: Any) -> bool:
    """
    Validate if file size is within allowed limit (5MB)
    
    Args:
        file: File object with size attribute
        
    Returns:
        bool: True if file size is acceptable, False otherwise
    """
    try:
        return file.size < MAX_FILE_SIZE
    except AttributeError:
        return False


def validate_file_extension(file: Any) -> bool:
    """
    Validate if file extension matches MIME type
    
    Args:
        file: File object with filename and content_type attributes
        
    Returns:
        bool: True if extension matches MIME type, False otherwise
    """
    try:
        if not file.filename:
            return False
        
        # Extract extension (case insensitive)
        _, extension = os.path.splitext(file.filename.lower())
        
        # Check if extension exists and is valid
        if not extension or extension not in EXTENSION_MIME_MAP:
            return False
        
        # Check if extension matches MIME type
        expected_mime = EXTENSION_MIME_MAP[extension]
        return file.content_type == expected_mime
        
    except AttributeError:
        return False