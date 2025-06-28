"""
File Storage Module

Provides file storage functions including:
- UUID-based file path generation with date structure
- File saving to disk with error handling
- Directory structure creation and management
"""

import os
import uuid
from datetime import datetime
from typing import Union
import logging

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_BASE_DIR = "uploads"


def generate_file_path(filename: str) -> str:
    """
    Generate unique file path with date-based directory structure
    
    Args:
        filename: Original filename with extension
        
    Returns:
        str: Generated path in format: uploads/YYYY/MM/uuid.extension
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Extract extension
    _, extension = os.path.splitext(filename)
    if not extension:
        raise ValueError("Filename must have an extension")
    
    # Generate UUID-based filename
    unique_id = str(uuid.uuid4())
    new_filename = f"{unique_id}{extension}"
    
    # Create date-based directory structure
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    
    # Construct full path
    file_path = os.path.join(UPLOAD_BASE_DIR, year, month, new_filename)
    
    return file_path


def save_file_to_disk(file_content: bytes, file_path: str) -> bool:
    """
    Save file content to disk
    
    Args:
        file_content: Binary file content
        file_path: Target file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not create_directory_structure(directory):
            return False
        
        # Write file content
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"File saved successfully: {file_path}")
        return True
        
    except (OSError, IOError) as e:
        logger.error(f"Failed to save file {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving file {file_path}: {e}")
        return False


def create_directory_structure(path: str) -> bool:
    """
    Create directory structure for given path
    
    Args:
        path: Directory path or file path (will create parent directories)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # If path looks like a file (has extension), get directory
        if os.path.splitext(path)[1]:
            directory = os.path.dirname(path)
        else:
            directory = path
        
        if directory:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Directory structure created: {directory}")
        
        return True
        
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to create directory structure {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating directory {path}: {e}")
        return False