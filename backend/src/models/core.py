from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr
from beanie import Document, Indexed
from pymongo import ASCENDING, DESCENDING


# Enums and Types
ServiceType = Literal["X", "Threads", "Bluesky", "Mastodon"]
PostStatus = Literal["draft", "published", "archived", "deleted"]
UserStatus = Literal["active", "inactive", "suspended"]
ReactionType = Literal["like", "love", "laugh", "wow", "sad", "angry"]
TargetType = Literal["post", "comment"]


# Pydantic Models for Requests/Responses
class UserBase(BaseModel):
    """Base user model for shared fields."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    handle: Optional[str] = Field(None, min_length=3, max_length=30)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    
    @field_validator("handle")
    @classmethod
    def validate_handle(cls, v: Optional[str]) -> Optional[str]:
        """Validate user handle format."""
        if v is None:
            return v
        
        # Handle should be alphanumeric with underscores
        if not v.replace("_", "").isalnum():
            raise ValueError("Handle must contain only letters, numbers, and underscores")
        
        return v.lower()


class PostBase(BaseModel):
    """Base post model for shared fields."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    service: ServiceType
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        # Remove duplicates and empty tags
        unique_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
        
        # Limit number of tags
        if len(unique_tags) > 10:
            raise ValueError("Maximum 10 tags allowed")
        
        return unique_tags


class CommentBase(BaseModel):
    """Base comment model for shared fields."""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[str] = None


# Beanie Document Models (ODM)
class User(Document, UserBase):
    """User document model for MongoDB."""
    status: UserStatus = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Password hash (not included in UserBase for security)
    password_hash: str
    
    # Social media profiles
    social_profiles: Dict[ServiceType, str] = Field(default_factory=dict)
    
    class Settings:
        name = "users"
        indexes = [
            [("email", ASCENDING)],
            [("handle", ASCENDING)],
            [("status", ASCENDING), ("created_at", DESCENDING)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "handle": "johndoe",
                "bio": "Software developer and tech enthusiast",
                "status": "active"
            }
        }


class Post(Document, PostBase):
    """Post document model for MongoDB."""
    slug: str = Indexed(unique=True)
    author_id: str
    status: PostStatus = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    # Engagement metrics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    
    class Settings:
        name = "posts"
        indexes = [
            [("slug", ASCENDING)],
            [("author_id", ASCENDING), ("created_at", DESCENDING)],
            [("service", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)]
        ]
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate URL slug format."""
        if not v:
            raise ValueError("Slug cannot be empty")
        
        # Slug should be lowercase with hyphens
        if not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("Slug must contain only letters, numbers, and hyphens")
        
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Getting Started with FastAPI",
                "slug": "getting-started-with-fastapi",
                "content": "FastAPI is a modern web framework...",
                "service": "X",
                "tags": ["python", "fastapi", "tutorial"],
                "status": "published"
            }
        }


class Comment(Document, CommentBase):
    """Comment document model for MongoDB."""
    post_id: str
    author_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Engagement
    like_count: int = 0
    reply_count: int = 0
    
    # Moderation
    is_edited: bool = False
    is_deleted: bool = False
    
    class Settings:
        name = "comments"
        indexes = [
            [("post_id", ASCENDING), ("created_at", ASCENDING)],
            [("author_id", ASCENDING), ("created_at", DESCENDING)],
            [("parent_id", ASCENDING)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Great article! Very helpful.",
                "post_id": "507f1f77bcf86cd799439011",
                "author_id": "507f1f77bcf86cd799439012"
            }
        }


class Reaction(Document):
    """Reaction document model for MongoDB."""
    user_id: str
    target_id: str  # ID of post or comment
    target_type: TargetType
    reaction_type: ReactionType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "reactions"
        indexes = [
            [("user_id", ASCENDING), ("target_id", ASCENDING), ("target_type", ASCENDING)],
            [("target_id", ASCENDING), ("target_type", ASCENDING)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "target_id": "507f1f77bcf86cd799439012",
                "target_type": "post",
                "reaction_type": "like"
            }
        }


class Stats(Document):
    """Statistics document model for tracking metrics."""
    entity_id: str  # ID of user, post, etc.
    entity_type: str  # "user", "post", etc.
    
    # Metrics
    view_count: int = 0
    unique_view_count: int = 0
    engagement_rate: float = 0.0
    
    # Time-based metrics
    daily_views: Dict[str, int] = Field(default_factory=dict)
    hourly_distribution: Dict[int, int] = Field(default_factory=dict)
    
    # Metadata
    last_calculated: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "stats"
        indexes = [
            [("entity_id", ASCENDING), ("entity_type", ASCENDING)],
            [("entity_type", ASCENDING), ("view_count", DESCENDING)]
        ]


# Request/Response Models
class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        return v


class UserUpdate(BaseModel):
    """Model for updating user information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Model for user API responses."""
    id: str = Field(alias="_id")
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class PostCreate(PostBase):
    """Model for creating a new post."""
    pass


class PostUpdate(BaseModel):
    """Model for updating post information."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    status: Optional[PostStatus] = None


class PostResponse(PostBase):
    """Model for post API responses."""
    id: str = Field(alias="_id")
    slug: str
    author_id: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    view_count: int
    like_count: int
    comment_count: int
    
    class Config:
        populate_by_name = True


class CommentCreate(CommentBase):
    """Model for creating a new comment."""
    post_id: str


class CommentResponse(CommentBase):
    """Model for comment API responses."""
    id: str = Field(alias="_id")
    post_id: str
    author_id: str
    created_at: datetime
    updated_at: datetime
    like_count: int
    reply_count: int
    is_edited: bool
    
    class Config:
        populate_by_name = True


# Pagination Models
class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database query."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Generic paginated response model."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, page_size: int) -> "PaginatedResponse":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )