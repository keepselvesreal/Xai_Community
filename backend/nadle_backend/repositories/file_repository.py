"""
File Repository Module

Provides data access layer for file operations including:
- Saving file records to MongoDB
- Retrieving file records by ID
- Managing file metadata in database
"""

from typing import Dict, Any, Optional
import logging
from nadle_backend.database.connection import get_database
from nadle_backend.models.core import FileRecord

logger = logging.getLogger(__name__)


async def save_file_record(file_document: Dict[str, Any]) -> bool:
    """
    Save file record to MongoDB using Beanie
    
    Args:
        file_document: File document to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create FileRecord instance from dictionary
        file_record = FileRecord(**file_document)
        
        # Save to database using Beanie
        await file_record.save()
        
        logger.info(f"File record saved: {file_document.get('file_id')}")
        return True
            
    except Exception as e:
        logger.error(f"Error saving file record: {e}")
        logger.error(f"File document: {file_document}")
        return False


async def find_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Find file record by file ID using Beanie
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Optional[Dict]: File document if found, None otherwise
    """
    try:
        # Find by file_id field using Beanie
        file_record = await FileRecord.find_one(FileRecord.file_id == file_id)
        
        if file_record:
            logger.debug(f"File record found: {file_id}")
            # Convert to dict for compatibility
            return file_record.model_dump()
        else:
            logger.debug(f"File record not found: {file_id}")
            return None
        
    except Exception as e:
        logger.error(f"Error finding file record {file_id}: {e}")
        return None


async def get_file_record(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file record by file ID (alias for find_file_by_id)
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Optional[Dict]: File document if found, None otherwise
    """
    return await find_file_by_id(file_id)


async def find_files_by_attachment(attachment_type: str, attachment_id: str) -> list:
    """
    Find all files attached to a specific entity
    
    Args:
        attachment_type: Type of attachment (post, comment, profile)
        attachment_id: ID of the attached entity
        
    Returns:
        list: List of file documents
    """
    try:
        db = await get_database()
        collection = db[FILES_COLLECTION]
        
        query = {
            "attachment_type": attachment_type,
            "attachment_id": attachment_id,
            "status": "active"
        }
        
        cursor = collection.find(query)
        documents = await cursor.to_list(length=None)
        
        logger.debug(f"Found {len(documents)} files for {attachment_type}:{attachment_id}")
        return documents
        
    except Exception as e:
        logger.error(f"Error finding files for {attachment_type}:{attachment_id}: {e}")
        return []