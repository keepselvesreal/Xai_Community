from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, HttpUrl
from beanie import Document, Indexed
from pymongo import ASCENDING, DESCENDING
import mimetypes


# File-related Types and Enums
AttachmentType = Literal["post", "comment", "profile"]
FileStatus = Literal["active", "deleted", "pending"]

# Allowed file types for validation
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"], 
    "image/gif": [".gif"],
    "image/webp": [".webp"]
}

# File size limits (in bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES_PER_POST = 5
MAX_FILES_PER_COMMENT = 1
MAX_FILES_PER_PROFILE = 1


# Pydantic Models for File Operations
class FileBase(BaseModel):
    """Base file model for shared fields."""
    original_filename: str = Field(..., min_length=1, max_length=255)
    stored_filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0, le=MAX_FILE_SIZE)
    file_type: str = Field(..., min_length=1)  # MIME type
    attachment_type: AttachmentType
    attached_to_id: Optional[str] = None  # Can be null during upload
    uploaded_by: str  # User ID
    
    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate MIME type is in allowed list."""
        if v not in ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Unsupported file type. Allowed types: {list(ALLOWED_IMAGE_TYPES.keys())}")
        return v
    
    @field_validator("original_filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename doesn't contain path traversal characters."""
        # Remove any path separators for security
        filename = v.replace("/", "").replace("\\", "").replace("..", "")
        if not filename:
            raise ValueError("Invalid filename")
        return filename


class FileUploadRequest(BaseModel):
    """Model for file upload request data (form fields)."""
    attachment_type: AttachmentType
    attached_to_id: Optional[str] = None  # Optional during upload
    
    class Config:
        json_schema_extra = {
            "example": {
                "attachment_type": "post",
                "attached_to_id": "507f1f77bcf86cd799439011"
            }
        }


class FileUploadResponse(FileBase):
    """Model for file upload API response."""
    file_id: str = Field(alias="_id")
    file_url: str  # Access URL: /api/files/{file_id}
    created_at: datetime
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "file_id": "507f1f77bcf86cd799439011",
                "original_filename": "sunset.jpg",
                "stored_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_1640995200.jpg",
                "file_path": "/uploads/2024/01/posts/a1b2c3d4-e5f6-7890-abcd-ef1234567890_1640995200.jpg",
                "file_size": 1024000,
                "file_type": "image/jpeg",
                "attachment_type": "post",
                "attached_to_id": "507f1f77bcf86cd799439011",
                "uploaded_by": "507f1f77bcf86cd799439012",
                "file_url": "/api/files/507f1f77bcf86cd799439011",
                "created_at": "2024-01-01T10:00:00Z"
            }
        }


class FileInfoResponse(FileBase):
    """Model for file metadata API response."""
    file_id: str = Field(alias="_id")
    file_url: str
    status: FileStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class FileDeleteResponse(BaseModel):
    """Model for file deletion API response."""
    message: str
    deleted_file_id: str
    cleaned_references: Dict[str, List[str]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "파일이 삭제되었습니다",
                "deleted_file_id": "507f1f77bcf86cd799439011",
                "cleaned_references": {
                    "posts": ["507f1f77bcf86cd799439013"],
                    "comments": []
                }
            }
        }


class PostFilesResponse(BaseModel):
    """Model for post files list response."""
    post_id: str
    files: List[FileInfoResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "507f1f77bcf86cd799439011",
                "files": [
                    {
                        "file_id": "507f1f77bcf86cd799439012",
                        "original_filename": "image1.jpg",
                        "file_url": "/api/files/507f1f77bcf86cd799439012"
                    }
                ]
            }
        }


class CommentFilesResponse(BaseModel):
    """Model for comment files list response."""
    comment_id: str
    files: List[FileInfoResponse]


class ProfileImageResponse(BaseModel):
    """Model for profile image response."""
    user_id: str
    profile_image: Optional[FileInfoResponse] = None


# Beanie Document Model for MongoDB
class FileDocument(Document, FileBase):
    """File document model for MongoDB."""
    status: FileStatus = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional metadata
    alt_text: Optional[str] = Field(None, max_length=200)  # For accessibility
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(default_factory=list, max_items=5)
    
    # Technical metadata
    width: Optional[int] = None  # Image width in pixels
    height: Optional[int] = None  # Image height in pixels
    hash_md5: Optional[str] = None  # For duplicate detection
    
    class Settings:
        name = "files"
        indexes = [
            [("uploaded_by", ASCENDING), ("created_at", DESCENDING)],
            [("attachment_type", ASCENDING), ("attached_to_id", ASCENDING)],
            [("status", ASCENDING), ("created_at", DESCENDING)],
            [("file_type", ASCENDING)],
            [("hash_md5", ASCENDING)]  # For duplicate detection
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_filename": "vacation_photo.jpg",
                "stored_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_1640995200.jpg",
                "file_path": "/uploads/2024/01/posts/a1b2c3d4-e5f6-7890-abcd-ef1234567890_1640995200.jpg",
                "file_size": 2048000,
                "file_type": "image/jpeg",
                "attachment_type": "post",
                "attached_to_id": "507f1f77bcf86cd799439011",
                "uploaded_by": "507f1f77bcf86cd799439012",
                "status": "active",
                "alt_text": "Beautiful sunset at the beach",
                "width": 1920,
                "height": 1080
            }
        }


# Updated Models for Existing Collections
class UpdatedPostMetadata(BaseModel):
    """Updated post metadata model with file_ids instead of attachments."""
    type: Optional[str] = None  # Service-specific post type
    tags: Optional[List[str]] = Field(default_factory=list, max_items=3)
    file_ids: Optional[List[str]] = Field(default_factory=list, max_items=MAX_FILES_PER_POST)  # File IDs instead of URLs
    thumbnail: Optional[str] = None
    visibility: Literal["public", "private"] = "public"
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags."""
        if v is None:
            return []
        validated_tags = []
        for tag in v[:3]:
            tag = tag.strip()[:10]
            if tag:
                validated_tags.append(tag)
        return validated_tags
    
    @field_validator("file_ids")
    @classmethod
    def validate_file_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate file IDs list."""
        if v is None:
            return []
        return v[:MAX_FILES_PER_POST]  # Limit to max files per post


class UpdatedCommentBase(BaseModel):
    """Updated comment base model with file_ids."""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[str] = None
    file_ids: Optional[List[str]] = Field(default_factory=list, max_items=MAX_FILES_PER_COMMENT)
    
    @field_validator("file_ids")
    @classmethod
    def validate_file_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate file IDs list for comments."""
        if v is None:
            return []
        return v[:MAX_FILES_PER_COMMENT]  # Limit to max files per comment


class UpdatedUserBase(BaseModel):
    """Updated user base model with profile_image_id."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: str  # EmailStr removed for simplicity, add back if needed
    user_handle: str = Field(..., min_length=3, max_length=30)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None  # Keep for backward compatibility
    profile_image_id: Optional[str] = None  # New field for file reference


# Request Models for API Operations
class PostCreateWithFiles(BaseModel):
    """Model for creating a post with file attachments."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    service: str  # ServiceType from your original model
    metadata: UpdatedPostMetadata


class PostUpdateWithFiles(BaseModel):
    """Model for updating post with file management."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[UpdatedPostMetadata] = None


class CommentCreateWithFiles(BaseModel):
    """Model for creating a comment with file attachments."""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[str] = None
    file_ids: Optional[List[str]] = Field(default_factory=list, max_items=MAX_FILES_PER_COMMENT)


class CommentUpdateWithFiles(BaseModel):
    """Model for updating comment with file management."""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    file_ids: Optional[List[str]] = Field(None, max_items=MAX_FILES_PER_COMMENT)


# Helper Models for File Validation
class FileValidationResult(BaseModel):
    """Model for file validation results."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    file_info: Optional[Dict[str, Any]] = None


class FileBatch(BaseModel):
    """Model for batch file operations."""
    file_ids: List[str]
    operation: Literal["delete", "move", "update"]
    parameters: Optional[Dict[str, Any]] = None


class FileStorageConfig(BaseModel):
    """Model for file storage configuration."""
    base_path: str = "/uploads"
    max_file_size: int = MAX_FILE_SIZE
    allowed_types: Dict[str, List[str]] = Field(default_factory=lambda: ALLOWED_IMAGE_TYPES.copy())
    create_thumbnails: bool = False  # For future use
    storage_backend: Literal["local", "s3", "gcs"] = "local"


# Error Models
class FileError(BaseModel):
    """Model for file-related errors."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    file_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "FILE_TOO_LARGE",
                "message": "파일 크기가 5MB를 초과합니다",
                "details": {
                    "max_size": 5242880,
                    "actual_size": 6291456,
                    "filename": "large_image.jpg"
                }
            }
        }


# Utility functions for validation
def validate_file_extension(filename: str, mime_type: str) -> bool:
    """Validate file extension matches MIME type."""
    if mime_type not in ALLOWED_IMAGE_TYPES:
        return False
    
    allowed_extensions = ALLOWED_IMAGE_TYPES[mime_type]
    filename_lower = filename.lower()
    
    return any(filename_lower.endswith(ext) for ext in allowed_extensions)


def get_file_type_from_extension(filename: str) -> Optional[str]:
    """Get MIME type from file extension."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type if mime_type in ALLOWED_IMAGE_TYPES else None


def validate_attachment_count(attachment_type: AttachmentType, current_count: int) -> bool:
    """Validate if attachment count is within limits."""
    limits = {
        "post": MAX_FILES_PER_POST,
        "comment": MAX_FILES_PER_COMMENT, 
        "profile": MAX_FILES_PER_PROFILE
    }
    return current_count < limits.get(attachment_type, 0)