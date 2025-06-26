"""
File Upload API Router

Provides REST API endpoints for file upload functionality including:
- Single file upload with validation
- Request validation and error handling
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Dict, Any, Optional
import logging

# Import all required services
from src.services.file_validator import (
    validate_file_type,
    validate_file_size, 
    validate_file_extension
)
from src.services.file_storage import (
    generate_file_path,
    save_file_to_disk
)
from src.services.file_metadata import (
    extract_file_metadata,
    create_file_document
)
from src.repositories.file_repository import save_file_record

logger = logging.getLogger(__name__)
router = APIRouter(tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    attachment_type: Optional[str] = None,
    attachment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a single file with validation
    
    Args:
        file: Uploaded file
        attachment_type: Type of attachment (post, comment, profile)
        attachment_id: ID of the attached entity
        
    Returns:
        Dict containing upload result and file information
    """
    try:
        # Validate file type
        if not validate_file_type(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only image files (jpg, jpeg, png, gif, webp) are allowed."
            )
        
        # Validate file size
        if not validate_file_size(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size is 5MB."
            )
        
        # Validate file extension consistency
        if not validate_file_extension(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File extension does not match the file type."
            )
        
        # Generate unique file path
        file_path = generate_file_path(file.filename)
        
        # Read file content
        file_content = await file.read()
        
        # Save file to disk
        if not save_file_to_disk(file_content, file_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file to disk."
            )
        
        # Extract metadata
        metadata = extract_file_metadata(file, file_path)
        
        # Create document for database
        file_document = create_file_document(
            metadata, 
            attachment_type=attachment_type,
            attachment_id=attachment_id
        )
        
        # Save to database
        if not await save_file_record(file_document):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file record to database."
            )
        
        logger.info(f"File uploaded successfully: {file_document['file_id']}")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_id": file_document["file_id"],
            "filename": file_document["original_filename"],
            "file_path": file_document["file_path"],
            "file_size": file_document["file_size"],
            "content_type": file_document["content_type"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file upload."
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for file upload service"""
    return {"status": "healthy", "service": "file_upload"}