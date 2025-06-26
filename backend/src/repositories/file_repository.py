"""
File Repository Module

Provides data access layer for file operations including:
- Saving file records to MongoDB
- Retrieving file records by ID
- Managing file metadata in database
"""

from typing import Dict, Any, Optional
import logging
from src.database.connection import get_database

logger = logging.getLogger(__name__)

# Collection name
FILES_COLLECTION = "files"


async def save_file_record(file_document: Dict[str, Any]) -> bool:
    """
    Save file record to MongoDB
    
    Args:
        file_document: File document to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = await get_database()
        collection = db[FILES_COLLECTION]
        
        result = await collection.insert_one(file_document)
        
        if result.inserted_id:
            logger.info(f"File record saved: {file_document.get('file_id')}")
            return True
        else:
            logger.warning(f"Failed to save file record: {file_document.get('file_id')}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving file record: {e}")
        return False


async def find_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Find file record by file ID
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Optional[Dict]: File document if found, None otherwise
    """
    try:
        db = await get_database()
        collection = db[FILES_COLLECTION]
        
        document = await collection.find_one({"file_id": file_id})
        
        if document:
            logger.debug(f"File record found: {file_id}")
        else:
            logger.debug(f"File record not found: {file_id}")
            
        return document
        
    except Exception as e:
        logger.error(f"Error finding file record {file_id}: {e}")
        return None


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