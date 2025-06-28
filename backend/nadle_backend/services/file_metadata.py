"""
File Metadata Module

Provides file metadata functions including:
- File metadata extraction from uploaded files
- MongoDB document creation for file records
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def extract_file_metadata(file: Any, file_path: str) -> Dict[str, Any]:
    """
    Extract metadata from uploaded file
    
    Args:
        file: File object with filename, content_type, size attributes
        file_path: Path where file will be stored
        
    Returns:
        Dict containing file metadata
    """
    metadata = {
        "original_filename": getattr(file, 'filename', 'unknown'),
        "content_type": getattr(file, 'content_type', 'application/octet-stream'),
        "file_size": getattr(file, 'size', 0),
        "file_path": file_path,
        "upload_timestamp": datetime.now()
    }
    
    logger.debug(f"Extracted metadata for file: {metadata['original_filename']}")
    return metadata


def create_file_document(metadata: Dict[str, Any], 
                        attachment_type: Optional[str] = None,
                        attachment_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create MongoDB document structure from file metadata
    
    Args:
        metadata: File metadata dictionary
        attachment_type: Type of attachment (post, comment, profile)
        attachment_id: ID of the attached entity
        
    Returns:
        Dict containing MongoDB document structure
    """
    document = {
        "file_id": str(uuid.uuid4()),
        "original_filename": metadata.get("original_filename"),
        "content_type": metadata.get("content_type"),
        "file_size": metadata.get("file_size"),
        "file_path": metadata.get("file_path"),
        "upload_timestamp": metadata.get("upload_timestamp"),
        "status": "active"
    }
    
    # Add attachment information if provided
    if attachment_type:
        document["attachment_type"] = attachment_type
    if attachment_id:
        document["attachment_id"] = attachment_id
    
    # Add any additional metadata
    for key, value in metadata.items():
        if key not in document and key.startswith(("attachment_", "meta_")):
            document[key] = value
    
    logger.debug(f"Created file document with ID: {document['file_id']}")
    return document