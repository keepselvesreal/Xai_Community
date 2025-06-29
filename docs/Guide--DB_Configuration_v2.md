# 데이터베이스 연결 및 설정 v2 (실제 구현 반영)

**작성일**: 2025-06-29  
**업데이트**: nadle_backend 패키지 및 Beanie ODM 기반 실제 구현 반영

## 📋 목차

### 1. 환경 설정 (Environment Setup)
- **Pydantic Settings**: 설정 자동 탐지 및 타입 검증
- **환경 변수**: `.env` 파일 자동 발견 및 로드

### 2. Beanie ODM 연결 관리 (Database Connection)
- **비동기 ODM**: Beanie를 통한 타입 안전한 MongoDB 연동
- **연결 풀링**: Motor 기반 성능 최적화된 연결 관리

### 3. 인덱스 전략 (Index Strategy)
- **자동 인덱스**: Beanie Document 모델에서 자동 인덱스 생성
- **성능 최적화**: 실제 쿼리 패턴별 인덱스 설계

### 4. 데이터베이스 초기화 (Initialization)
- **전역 상태 관리**: Database 클래스를 통한 연결 대리 패턴
- **자동 설정**: Beanie 초기화 및 모델 등록

### 5. 설정 관리 (Configuration)
- **중앙 집중**: `nadle_backend/config.py`에서 모든 설정 관리
- **환경별 분리**: 개발/프로덕션 환경 설정

### 6. 파일 위치 및 접근 (File Locations)
- **환경 파일**: `backend/.env` (루트 디렉토리가 아닌 backend 디렉토리)
- **설정 모듈**: `nadle_backend/config.py` (패키지 내부)

## 📊 항목 간 관계

```
backend/.env → nadle_backend/config.py → Beanie ODM → MongoDB
    ↓                    ↓                  ↓
환경 변수 → Settings 클래스 → Document 모델 → 인덱스 자동 생성
```

- **환경 변수**가 Pydantic Settings로 자동 로드
- **Beanie ODM**이 MongoDB와 직접 연동
- **Document 모델**에서 인덱스 자동 생성

## 📝 각 항목 핵심 설명

### 환경 설정
Pydantic Settings로 타입 안전한 설정 관리 및 자동 `.env` 파일 탐지

### Beanie ODM 연결
Motor 기반 비동기 MongoDB 연동으로 성능과 타입 안전성 보장

### 인덱스 전략
Beanie Document 모델에서 직접 인덱스 정의로 자동 최적화

### 데이터베이스 초기화
Database 클래스를 통한 전역 연결 관리 및 Beanie 초기화 자동화

### 설정 관리
Pydantic Settings를 활용한 타입 안전한 설정 관리 및 환경별 구성

### 파일 위치
backend 디렉토리 기반 설정 파일 및 nadle_backend 패키지 구조

---

# 📖 본문

## 1. 실제 구현된 환경 설정

### 1.1 파일 위치 및 구조
```
v5/
├── backend/
│   ├── .env                          # 메인 환경 설정 파일
│   ├── .env.example                  # 환경 설정 템플릿
│   ├── nadle_backend/
│   │   ├── config.py                 # 설정 모듈 (자동 .env 탐지)
│   │   ├── database/
│   │   │   ├── connection.py         # 데이터베이스 연결 관리
│   │   │   └── manager.py            # 인덱스 관리
│   │   └── models/
│   │       └── core.py               # Beanie Document 모델
│   └── main.py                       # FastAPI 앱 설정
└── frontend/
```

### 1.2 실제 환경 설정 파일 (backend/.env)
```env
# Database Configuration
MONGODB_URL=mongodb+srv://nadle:miQXsXpzayvMQAzE@cluster0.bh7mhfi.mongodb.net/
DATABASE_NAME=app_database

# Collection Configuration (Standard names)
USERS_COLLECTION=users
POSTS_COLLECTION=posts
COMMENTS_COLLECTION=comments
POST_STATS_COLLECTION=post_stats
USER_REACTIONS_COLLECTION=user_reactions
FILES_COLLECTION=files
STATS_COLLECTION=stats

# API Configuration
API_TITLE=Xai Community API
API_VERSION=1.0.0
API_DESCRIPTION=Content Management API for Xai Community

# JWT Configuration
SECRET_KEY=84652003587112af53d791e5e02cc4f33e8f0c0da1ca8b60bcc7a00a98031f69
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]

# Environment Configuration
ENVIRONMENT=development

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

### 1.3 실제 설정 모듈 (nadle_backend/config.py)
```python
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal, Optional, Union
from datetime import timedelta
import os
from pathlib import Path

def find_env_file() -> Optional[str]:
    """
    Find environment file with priority order:
    1. ENV_FILE_PATH environment variable (explicit override)
    2. .env.local (local development overrides)
    3. .env (main environment file)
    4. .env.example (template/example file)
    
    Returns:
        Path to the first found environment file, or None if none found
    """
    # Check for explicit path override
    explicit_path = os.getenv("ENV_FILE_PATH")
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    
    # Priority order for automatic discovery
    env_file_candidates = [
        ".env.local",      # Local overrides (git ignored)
        ".env",            # Main environment file (git ignored)
        ".env.example",    # Template file (git tracked)
    ]
    
    for candidate in env_file_candidates:
        env_path = Path(candidate)
        if env_path.exists():
            return str(env_path)
    
    return None

class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database Configuration
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL (Atlas or local)"
    )
    database_name: str = Field(
        default="app_database",
        description="Database name for the application"
    )
    
    # Collection Configuration
    users_collection: str = Field(default="users")
    posts_collection: str = Field(default="posts")
    comments_collection: str = Field(default="comments")
    post_stats_collection: str = Field(default="post_stats")
    user_reactions_collection: str = Field(default="user_reactions")
    files_collection: str = Field(default="files")
    stats_collection: str = Field(default="stats")
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production-32-characters",
        min_length=32
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    
    # API Configuration
    api_title: str = Field(default="Content Management API")
    api_version: str = Field(default="1.0.0")
    api_description: str = Field(default="FastAPI backend for content management system")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", 
                "http://localhost:5173", "http://127.0.0.1:5173"]
    )
    
    # Environment Configuration
    environment: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    
    # Server Configuration
    port: int = Field(default=8000, ge=1, le=65535)
    host: str = Field(default="0.0.0.0")
    
    # Feature Flags
    enable_docs: bool = Field(default=True)
    enable_cors: bool = Field(default=True)
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length and production safety."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @field_validator("mongodb_url")
    @classmethod
    def validate_mongodb_url(cls, v: str) -> str:
        """Validate MongoDB connection URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = find_env_file()  # Use auto-discovery
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings
```

## 2. Beanie ODM 데이터베이스 연결

### 2.1 실제 구현된 데이터베이스 연결 (nadle_backend/database/connection.py)
```python
from typing import Optional, List
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import asyncio

from nadle_backend.config import get_settings
from nadle_backend.models.core import (
    User, Post, Comment, PostStats, UserReaction, Stats, FileRecord
)

logger = logging.getLogger(__name__)

class Database:
    """Database connection and state management."""
    client: Optional[AsyncIOMotorClient] = None
    database = None
    
    @classmethod
    async def connect_to_mongo(cls) -> None:
        """Connect to MongoDB using Beanie ODM."""
        settings = get_settings()
        
        try:
            # Create MongoDB client with optimized settings
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=45000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
            )
            
            # Get database instance
            cls.database = cls.client[settings.database_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.database_name}")
            
            # Initialize Beanie with document models
            await init_beanie(
                database=cls.database,
                document_models=[
                    User,
                    Post, 
                    Comment,
                    PostStats,
                    UserReaction,
                    Stats,
                    FileRecord
                ]
            )
            
            logger.info("Beanie ODM initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_mongo_connection(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.database = None
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_client(cls) -> Optional[AsyncIOMotorClient]:
        """Get MongoDB client."""
        return cls.client
    
    @classmethod
    def get_database(cls):
        """Get database instance."""
        return cls.database

# Convenience functions for global access
async def connect_to_mongo() -> None:
    """Connect to MongoDB."""
    await Database.connect_to_mongo()

async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    await Database.close_mongo_connection()

def get_database():
    """Get database instance."""
    return Database.get_database()

def get_client() -> Optional[AsyncIOMotorClient]:
    """Get MongoDB client."""
    return Database.get_client()
```

### 2.2 인덱스 관리 (nadle_backend/database/manager.py)
```python
from typing import List, Dict, Any
import logging
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING

from nadle_backend.database.connection import get_database

logger = logging.getLogger(__name__)

class IndexManager:
    """Database index management."""
    
    @staticmethod
    async def create_all_indexes() -> None:
        """Create all required indexes for optimal query performance."""
        try:
            db = get_database()
            if not db:
                raise RuntimeError("Database not connected")
            
            # Create indexes for each collection
            await IndexManager._create_users_indexes(db)
            await IndexManager._create_posts_indexes(db)
            await IndexManager._create_comments_indexes(db)
            await IndexManager._create_post_stats_indexes(db)
            await IndexManager._create_user_reactions_indexes(db)
            await IndexManager._create_files_indexes(db)
            
            logger.info("All database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    @staticmethod
    async def _create_users_indexes(db) -> None:
        """Create indexes for users collection."""
        indexes = [
            # Unique indexes for authentication
            IndexModel(["email"], unique=True, name="idx_users_email_unique"),
            IndexModel(["user_handle"], unique=True, name="idx_users_handle_unique"),
            
            # Query optimization indexes
            IndexModel(["role"], name="idx_users_role"),
            IndexModel(["is_active"], name="idx_users_active"),
            IndexModel(["created_at"], name="idx_users_created"),
        ]
        
        await db.users.create_indexes(indexes)
        logger.info("Users collection indexes created")
    
    @staticmethod
    async def _create_posts_indexes(db) -> None:
        """Create indexes for posts collection."""
        indexes = [
            # Unique slug for URL routing
            IndexModel(["slug"], unique=True, name="idx_posts_slug_unique"),
            
            # Query optimization indexes
            IndexModel(["author_id"], name="idx_posts_author"),
            IndexModel(["service"], name="idx_posts_service"),
            IndexModel(["created_at"], name="idx_posts_created"),
            
            # Compound indexes for common queries
            IndexModel(
                [("service", ASCENDING), ("created_at", DESCENDING)],
                name="idx_posts_service_created"
            ),
            IndexModel(
                [("author_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_posts_author_created"
            ),
            
            # Text search index
            IndexModel(
                [("title", TEXT), ("content", TEXT)],
                weights={"title": 10, "content": 1},
                name="idx_posts_text_search"
            ),
        ]
        
        await db.posts.create_indexes(indexes)
        logger.info("Posts collection indexes created")
    
    @staticmethod
    async def _create_comments_indexes(db) -> None:
        """Create indexes for comments collection."""
        indexes = [
            # Post-comment relationship
            IndexModel(["post_slug"], name="idx_comments_post_slug"),
            
            # Comment hierarchy
            IndexModel(["parent_id"], name="idx_comments_parent"),
            
            # Query optimization
            IndexModel(["author_id"], name="idx_comments_author"),
            IndexModel(["status"], name="idx_comments_status"),
            IndexModel(["created_at"], name="idx_comments_created"),
            
            # Compound indexes for efficient queries
            IndexModel(
                [("post_slug", ASCENDING), ("created_at", ASCENDING)],
                name="idx_comments_post_created"
            ),
            IndexModel(
                [("post_slug", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)],
                name="idx_comments_post_status_created"
            ),
        ]
        
        await db.comments.create_indexes(indexes)
        logger.info("Comments collection indexes created")
    
    @staticmethod
    async def _create_post_stats_indexes(db) -> None:
        """Create indexes for post_stats collection."""
        indexes = [
            # Unique post reference
            IndexModel(["post_id"], unique=True, name="idx_post_stats_post_unique"),
            
            # Sorting indexes for popular content
            IndexModel([("view_count", DESCENDING)], name="idx_post_stats_views"),
            IndexModel([("like_count", DESCENDING)], name="idx_post_stats_likes"),
            IndexModel([("comment_count", DESCENDING)], name="idx_post_stats_comments"),
            IndexModel([("updated_at", DESCENDING)], name="idx_post_stats_updated"),
        ]
        
        await db.post_stats.create_indexes(indexes)
        logger.info("Post stats collection indexes created")
    
    @staticmethod
    async def _create_user_reactions_indexes(db) -> None:
        """Create indexes for user_reactions collection."""
        indexes = [
            # Unique user-post reaction
            IndexModel(
                [("user_id", ASCENDING), ("post_id", ASCENDING)],
                unique=True,
                name="idx_user_reactions_user_post_unique"
            ),
            
            # Query optimization
            IndexModel(["user_id"], name="idx_user_reactions_user"),
            IndexModel(["post_id"], name="idx_user_reactions_post"),
            IndexModel(["liked"], name="idx_user_reactions_liked"),
            IndexModel(["bookmarked"], name="idx_user_reactions_bookmarked"),
            IndexModel(["created_at"], name="idx_user_reactions_created"),
        ]
        
        await db.user_reactions.create_indexes(indexes)
        logger.info("User reactions collection indexes created")
    
    @staticmethod
    async def _create_files_indexes(db) -> None:
        """Create indexes for files collection."""
        indexes = [
            # File identification
            IndexModel(["filename"], name="idx_files_filename"),
            IndexModel(["content_type"], name="idx_files_content_type"),
            
            # File management
            IndexModel(["uploader_id"], name="idx_files_uploader"),
            IndexModel(["size"], name="idx_files_size"),
            IndexModel(["created_at"], name="idx_files_created"),
            
            # Compound indexes
            IndexModel(
                [("uploader_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_files_uploader_created"
            ),
        ]
        
        await db.files.create_indexes(indexes)
        logger.info("Files collection indexes created")

# Convenience function
async def create_indexes() -> None:
    """Create all database indexes."""
    await IndexManager.create_all_indexes()
```

## 3. Beanie Document 모델에서의 인덱스 정의

### 3.1 실제 구현된 모델 예시 (nadle_backend/models/core.py 일부)
```python
from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, List
from datetime import datetime
import pymongo

class User(Document):
    """User document model with automatic indexing."""
    email: Indexed(str, unique=True)  # 자동 고유 인덱스
    user_handle: Indexed(str, unique=True)  # 자동 고유 인덱스
    password_hash: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: Indexed(bool) = True  # 자동 인덱스
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"  # MongoDB collection name
        indexes = [
            # 추가 복합 인덱스 정의
            [("role", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]

class Post(Document):
    """Post document model with optimized indexing."""
    title: str = Field(..., min_length=1, max_length=200)
    slug: Indexed(str, unique=True)  # 자동 고유 인덱스
    content: str = Field(..., min_length=1)
    author_id: Indexed(str)  # 자동 인덱스
    service: Indexed(ServiceType)  # 자동 인덱스
    metadata: PostMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "posts"
        indexes = [
            # 복합 인덱스 정의
            [("service", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            [("author_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            
            # 텍스트 검색 인덱스
            [("title", pymongo.TEXT), ("content", pymongo.TEXT)],
        ]

class Comment(Document):
    """Comment document model with hierarchy support."""
    content: str = Field(..., min_length=1, max_length=1000)
    author_id: Indexed(str)  # 자동 인덱스
    post_slug: Indexed(str)  # 자동 인덱스
    parent_id: Optional[Indexed(str)] = None  # 자동 인덱스
    status: Indexed(CommentStatus) = CommentStatus.ACTIVE  # 자동 인덱스
    like_count: int = 0
    dislike_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "comments"
        indexes = [
            # 계층형 댓글 인덱스
            [("post_slug", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)],
            [("post_slug", pymongo.ASCENDING), ("status", pymongo.ASCENDING), 
             ("created_at", pymongo.ASCENDING)],
            [("parent_id", pymongo.ASCENDING)],
        ]
```

## 4. 실제 FastAPI 앱 연결

### 4.1 실제 구현된 main.py
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nadle_backend.config import get_settings
from nadle_backend.database.connection import connect_to_mongo, close_mongo_connection
from nadle_backend.database.manager import create_indexes
from nadle_backend.routers import auth, posts, comments, file_upload, content

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    await connect_to_mongo()
    await create_indexes()  # Create indexes after Beanie initialization
    
    yield
    
    # Shutdown
    await close_mongo_connection()

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    lifespan=lifespan
)

# Configure CORS
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(posts.router, tags=["Posts"])
app.include_router(comments.router, tags=["Comments"])
app.include_router(file_upload.router, prefix="/api/files", tags=["Files"])
app.include_router(content.router, tags=["Content"])

@app.get("/", tags=["Health"])
async def root():
    """API health check endpoint."""
    return {
        "message": "Xai Community API",
        "version": settings.api_version,
        "environment": settings.environment
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.environment
    }
```

## 5. 개발 및 테스트 사용법

### 5.1 프로젝트 설정
```bash
# backend 디렉토리로 이동
cd backend

# 의존성 설치
uv install

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 MONGODB_URL 수정
```

### 5.2 애플리케이션 실행
```bash
# 개발 서버 시작
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 Makefile 사용
make dev
```

### 5.3 테스트 실행
```bash
# 전체 테스트
make test

# 커버리지 포함 테스트
make test-cov

# 특정 테스트 파일
uv run pytest tests/unit/test_database_connection.py -v
```

### 5.4 데이터베이스 상태 확인
```bash
# API 상태 확인
curl http://localhost:8000/health

# Swagger UI 접속
# http://localhost:8000/docs
```

## 6. 실제 구현 특징 요약

### ✅ 구현 완료된 기능
1. **Pydantic Settings**: 자동 `.env` 파일 탐지 및 타입 검증
2. **Beanie ODM**: 비동기 MongoDB 연동 및 Document 모델
3. **자동 인덱스**: Document 모델에서 직접 인덱스 정의
4. **연결 관리**: Database 클래스로 전역 연결 상태 관리
5. **FastAPI 통합**: lifespan 관리로 자동 연결/종료

### 🔧 아키텍처 특징
1. **타입 안전성**: Pydantic과 Beanie로 완벽한 타입 검증
2. **성능 최적화**: Motor 기반 비동기 연결 풀링
3. **세련한 설정**: 환경별 설정 분리 및 자동 탐지
4. **인덱스 자동화**: 모델 정의에서 인덱스 자동 생성
5. **오류 처리**: 체계적인 예외 처리 및 로깅

### 📍 파일 위치 요약
- **환경 설정**: `backend/.env` (루트가 아닌 backend 디렉토리)
- **설정 모듈**: `nadle_backend/config.py` (패키지 내부)
- **DB 연결**: `nadle_backend/database/connection.py`
- **인덱스 관리**: `nadle_backend/database/manager.py`
- **모델 정의**: `nadle_backend/models/core.py`

이 구성은 **실제 구현된 데이터베이스 연결 및 설정 시스템**의 정확한 반영이며, Beanie ODM과 Pydantic Settings의 강력한 기능을 최대한 활용한 현대적이고 안정적인 설계입니다.