from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr
from beanie import Document, Indexed
from pymongo import ASCENDING, DESCENDING

# Import settings for dynamic collection names
from ..config import settings


# Enums and Types
ServiceType = Literal["shopping", "apartment", "community", "X", "Threads", "Bluesky", "Mastodon"]
PostStatus = Literal["draft", "published", "archived", "deleted"]
UserStatus = Literal["active", "inactive", "suspended"]
CommentStatus = Literal["active", "deleted", "hidden", "pending"]
TargetType = Literal["post", "comment"]
ContentType = Literal["text", "markdown", "html"]
EditorType = Literal["plain", "markdown", "wysiwyg"]

# Service-specific post types
ShoppingPostType = Literal["상품 문의", "배송 문의", "교환/환불", "기타"]
ApartmentPostType = Literal["입주 정보", "생활 정보", "이야기"]
CommunityPostType = Literal["자유게시판", "질문답변", "공지사항", "후기"]


# Pydantic Models for Requests/Responses
class UserBase(BaseModel):
    """Base user model for shared fields."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: EmailStr
    user_handle: str = Field(..., min_length=3, max_length=30)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    
    @field_validator("user_handle")
    @classmethod
    def validate_user_handle(cls, v: str) -> str:
        """Validate user handle format."""
        # Handle should be alphanumeric with underscores
        if not v.replace("_", "").isalnum():
            raise ValueError("Handle must contain only letters, numbers, and underscores")
        
        return v.lower()


class PostMetadata(BaseModel):
    """Post metadata model."""
    type: Optional[str] = None  # Service-specific post type
    tags: Optional[List[str]] = Field(default_factory=list, max_items=3)
    attachments: Optional[List[str]] = Field(default_factory=list)  # Image URLs
    file_ids: Optional[List[str]] = Field(default_factory=list)  # File upload IDs
    inline_images: Optional[List[str]] = Field(default_factory=list)  # Inline image file_ids
    editor_type: EditorType = "plain"
    thumbnail: Optional[str] = None
    visibility: Literal["public", "private"] = "public"
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags."""
        if v is None:
            return []
        # Limit each tag to 10 characters
        validated_tags = []
        for tag in v[:3]:  # Max 3 tags
            tag = tag.strip()[:10]
            if tag:
                validated_tags.append(tag)
        return validated_tags


class PostBase(BaseModel):
    """Base post model for shared fields."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)  # min 30 is recommended but not enforced
    service: ServiceType
    metadata: PostMetadata


class CommentBase(BaseModel):
    """Base comment model for shared fields."""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[str] = None  # For replies


# Beanie Document Models (ODM)
class User(Document, UserBase):
    """User document model for MongoDB."""
    status: UserStatus = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Password hash (not included in UserBase for security)
    password_hash: str
    
    # Admin privileges
    is_admin: bool = False
    
    # Social media profiles
    social_profiles: Dict[ServiceType, str] = Field(default_factory=dict)
    
    class Settings:
        name = settings.users_collection
        indexes = [
            [("email", ASCENDING)],
            [("user_handle", ASCENDING)],
            [("status", ASCENDING), ("created_at", DESCENDING)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "user_handle": "johndoe",
                "display_name": "John Doe",
                "bio": "Software developer and tech enthusiast",
                "status": "active"
            }
        }


class Post(Document, PostBase):
    """Post document model for MongoDB."""
    slug: str = Indexed(unique=True)
    author_id: str
    status: PostStatus = "published"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    # Content processing fields
    content_type: ContentType = "text"
    content_rendered: Optional[str] = None  # Rendered HTML
    content_text: Optional[str] = None  # Plain text for search
    word_count: Optional[int] = None
    reading_time: Optional[int] = None  # Minutes
    
    # Basic stats (denormalized for performance)
    view_count: int = 0
    like_count: int = 0
    dislike_count: int = 0
    comment_count: int = 0
    
    class Settings:
        name = settings.posts_collection
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
    parent_type: Literal["post"] = "post"  # For extensibility
    parent_id: str  # Post ID (not slug)
    author_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: CommentStatus = "active"
    like_count: int = 0  # Aggregated count from UserReaction
    dislike_count: int = 0  # Aggregated count from UserReaction
    reply_count: int = 0  # Count of replies to this comment
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Settings:
        name = settings.comments_collection
        indexes = [
            [("parent_id", ASCENDING), ("created_at", ASCENDING)],
            [("author_id", ASCENDING), ("created_at", DESCENDING)],
            [("parent_comment_id", ASCENDING)]
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Great article! Very helpful.",
                "post_id": "507f1f77bcf86cd799439011",
                "author_id": "507f1f77bcf86cd799439012"
            }
        }


class PostStats(Document):
    """Post statistics document model."""
    post_id: str = Indexed(unique=True)
    view_count: int = 0
    like_count: int = 0
    dislike_count: int = 0
    comment_count: int = 0
    bookmark_count: int = 0
    last_viewed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = settings.post_stats_collection
        indexes = [
            [("post_id", ASCENDING)]
        ]


class UserReaction(Document):
    """User reaction document model for posts and comments."""
    user_id: str
    target_type: Literal["post", "comment"] = "post"  # Type of target (post or comment)
    target_id: str  # ID of the post or comment
    liked: bool = False
    disliked: bool = False
    bookmarked: bool = False  # Only applicable for posts
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = settings.user_reactions_collection
        indexes = [
            [("user_id", ASCENDING), ("target_type", ASCENDING), ("target_id", ASCENDING)],
            [("target_type", ASCENDING), ("target_id", ASCENDING)]
        ]


class FileRecord(Document):
    """File upload record document model."""
    file_id: str = Indexed(unique=True)
    original_filename: str
    stored_filename: Optional[str] = None
    file_path: str
    file_size: int
    content_type: str
    attachment_type: Optional[str] = None
    attachment_id: Optional[str] = None
    uploaded_by: Optional[str] = None
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"
    
    class Settings:
        name = settings.files_collection
        indexes = [
            [("file_id", ASCENDING)],
            [("attachment_type", ASCENDING), ("attachment_id", ASCENDING)],
            [("uploaded_by", ASCENDING), ("created_at", DESCENDING)]
        ]


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
        name = settings.stats_collection
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


class PostListItem(BaseModel):
    """Post list item for API responses."""
    id: str = Field(alias="_id")
    title: str
    slug: str
    author_id: str
    service: ServiceType
    metadata: PostMetadata
    stats: Dict[str, int]  # view_count, like_count, dislike_count, comment_count
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class PostDetailResponse(BaseModel):
    """Post detail response model."""
    id: str = Field(alias="_id")
    title: str
    slug: str
    author_id: str
    content: str
    service: ServiceType
    metadata: PostMetadata
    stats: Dict[str, int]  # All stats including bookmark_count
    user_reaction: Optional[Dict[str, bool]] = None  # liked, disliked, bookmarked
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class PostResponse(PostBase):
    """Model for post API responses."""
    id: str = Field(alias="_id")
    slug: str
    author_id: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        populate_by_name = True


class CommentCreate(BaseModel):
    """Model for creating a new comment."""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[str] = None


class CommentUpdate(BaseModel):
    """Model for updating comment information."""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)


class CommentDetail(BaseModel):
    """Comment detail model for API responses."""
    id: str = Field(alias="_id")
    author_id: str
    content: str
    parent_comment_id: Optional[str]
    status: CommentStatus
    like_count: int = 0  # Calculated from UserReaction
    dislike_count: int = 0  # Calculated from UserReaction
    reply_count: int = 0  # Calculated from child comments
    user_reaction: Optional[Dict[str, bool]] = None  # liked, disliked
    created_at: datetime
    updated_at: datetime
    replies: Optional[List["CommentDetail"]] = None  # 1 level only
    
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


class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PostListResponse(BaseModel):
    """Post list response with pagination."""
    posts: List[PostListItem]
    pagination: PaginationInfo


class CommentListResponse(BaseModel):
    """Comment list response with pagination."""
    comments: List[CommentDetail]
    pagination: PaginationInfo


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