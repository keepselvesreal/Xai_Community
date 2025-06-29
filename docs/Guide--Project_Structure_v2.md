# 프로젝트 구조 가이드 v2 (실제 구현 반영)

**작성일**: 2025-06-29  
**업데이트**: 실제 구현된 nadle_backend 패키지 구조 반영

## 📋 목차

### 1. 전체 구조 개요 (Project Overview)
- **패키지 기반 아키텍처**: 표준 Python 패키지 구조
- **계층형 설계**: 역할별 명확한 계층 분리
- **의존성 방향**: 상위 계층이 하위 계층 의존

### 2. 디렉토리 구조 (Directory Structure)
- **nadle_backend 패키지**: 메인 백엔드 패키지
- **기능별 분리**: models, repositories, services, routers
- **공통 모듈**: utils, dependencies, exceptions

### 3. 계층별 역할 (Layer Responsibilities)
- **API 계층**: 요청/응답 처리 (routers)
- **서비스 계층**: 비즈니스 로직 (services)
- **데이터 계층**: 데이터 접근 (repositories)

### 4. 파일 명명 규칙 (Naming Conventions)
- **일관성**: 모든 파일과 클래스의 명명 규칙
- **가독성**: 역할이 명확히 드러나는 이름

### 5. 모듈 간 의존성 (Module Dependencies)
- **단방향 의존**: 순환 의존성 방지
- **Beanie ODM 활용**: 직접적이고 실용적인 데이터 접근

### 6. 개발 워크플로우 (Development Workflow)
- **구현 순서**: 모델 → Repository → Service → Router
- **테스트 전략**: 각 계층별 테스트 방법

## 📊 항목 간 관계

```
API 계층 (routers) 
    ↓
서비스 계층 (services) 
    ↓
Repository 계층 (repositories) 
    ↓
모델 계층 (models) + Beanie ODM
    ↓
데이터베이스 (MongoDB)
```

- **API 계층**이 서비스 계층만 의존
- **서비스 계층**이 Repository와 모델 의존
- **Repository 계층**이 Beanie ODM을 통해 모델과 데이터베이스 연동
- **공통 모듈**들은 모든 계층에서 사용 가능

## 📝 각 항목 핵심 설명

### 전체 구조 개요
표준 Python 패키지 구조를 적용한 계층형 아키텍처로 유지보수성과 확장성 확보

### 디렉토리 구조
nadle_backend 패키지 중심의 명확한 기능별 분리로 개발자 친화적 구조

### 계층별 역할
각 계층의 단일 책임 원칙으로 코드 변경 시 영향 범위 최소화

### 파일 명명 규칙
일관된 명명 규칙으로 코드 가독성과 팀 협업 효율성 향상

### 모듈 간 의존성
Beanie ODM을 활용한 직접적이고 실용적인 데이터 접근 패턴

### 개발 워크플로우
체계적인 개발 순서로 안정적이고 일관된 코드 품질 보장

---

# 📖 본문

## 1. 실제 프로젝트 구조

### 디렉토리 트리
```
content-management-api/
├── backend/
│   ├── nadle_backend/          # 메인 백엔드 패키지
│   │   ├── __init__.py
│   │   ├── cli.py              # CLI 인터페이스
│   │   ├── config.py           # 설정 관리
│   │   │
│   │   ├── models/             # 데이터 모델 (Beanie ODM)
│   │   │   ├── __init__.py
│   │   │   ├── core.py         # 핵심 모델 (User, Post, Comment 등)
│   │   │   └── content.py      # 콘텐츠 처리 모델
│   │   │
│   │   ├── repositories/       # 데이터 접근 계층
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── post_repository.py
│   │   │   ├── comment_repository.py
│   │   │   └── file_repository.py
│   │   │
│   │   ├── services/           # 비즈니스 로직 계층
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── posts_service.py
│   │   │   ├── comments_service.py
│   │   │   ├── content_service.py
│   │   │   ├── file_validator.py
│   │   │   ├── file_storage.py
│   │   │   └── file_metadata.py
│   │   │
│   │   ├── routers/            # API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── posts.py
│   │   │   ├── comments.py
│   │   │   ├── file_upload.py
│   │   │   └── content.py
│   │   │
│   │   ├── dependencies/       # FastAPI 의존성
│   │   │   ├── __init__.py
│   │   │   └── auth.py         # 인증 의존성
│   │   │
│   │   ├── utils/              # 유틸리티 함수
│   │   │   ├── __init__.py
│   │   │   ├── jwt.py          # JWT 토큰 처리
│   │   │   ├── password.py     # 패스워드 해싱
│   │   │   └── permissions.py  # 권한 검증
│   │   │
│   │   ├── exceptions/         # 커스텀 예외
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── base.py
│   │   │   ├── comment.py
│   │   │   ├── post.py
│   │   │   └── user.py
│   │   │
│   │   └── database/           # DB 연결 및 설정
│   │       ├── __init__.py
│   │       ├── connection.py   # MongoDB 연결
│   │       └── manager.py      # 인덱스 관리
│   │
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── pyproject.toml          # 패키지 설정
│   ├── .env                    # 환경 변수 (backend/.env)
│   ├── .env.example            # 환경 변수 템플릿
│   │
│   ├── tests/                  # 테스트 코드
│   │   ├── unit/               # 단위 테스트
│   │   ├── integration/        # 통합 테스트
│   │   ├── contract/           # 계약 테스트
│   │   ├── security/           # 보안 테스트
│   │   └── conftest.py         # 테스트 설정
│   │
│   └── uploads/                # 파일 업로드 저장소
│       └── [년도]/[월]/[타입]/
│
├── frontend/                   # Remix React 앱 (개발 도구)
├── frontend-prototypes/        # HTML UI (프로덕션)
│   └── UI.html                # 완전한 대시보드 인터페이스
├── docs/                       # 문서
├── tasks/                      # 작업 관리
└── README.md
```

## 2. 계층별 상세 역할

### 2.1 모델 계층 (models/)
**역할**: Beanie ODM을 활용한 데이터 구조 정의 및 검증

```python
# models/core.py 예시
from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(Document):
    email: str = Field(..., unique=True)
    user_handle: str = Field(..., unique=True)
    password_hash: str
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"  # MongoDB 컬렉션명
        
class Post(Document):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    author_id: str
    slug: str = Field(..., unique=True)
    service: ServiceType
    metadata: PostMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "posts"
```

### 2.2 Repository 계층 (repositories/)
**역할**: Beanie ODM을 직접 활용한 데이터 접근

```python
# repositories/user_repository.py 예시
from nadle_backend.models.core import User, UserCreate, UserUpdate
from nadle_backend.exceptions.user import UserNotFoundError
from typing import Optional

class UserRepository:
    """사용자 데이터 접근 Repository"""
    
    async def create(self, user_create: UserCreate, password_hash: str) -> User:
        """사용자 생성"""
        user_data = user_create.model_dump(exclude={"password"})
        user_data["password_hash"] = password_hash
        
        user = User(**user_data)
        await user.insert()  # Beanie ODM 내장 메서드
        return user
    
    async def get_by_id(self, user_id: str) -> User:
        """ID로 사용자 조회"""
        user = await User.get(user_id)
        if not user:
            raise UserNotFoundError(f"User not found: {user_id}")
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return await User.find_one({"email": email})
    
    async def email_exists(self, email: str) -> bool:
        """이메일 중복 확인"""
        count = await User.find({"email": email}).count()
        return count > 0
```

### 2.3 서비스 계층 (services/)
**역할**: 비즈니스 로직 구현

```python
# services/auth_service.py 예시
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.models.core import User, UserCreate
from nadle_backend.utils.password import hash_password, verify_password

class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    async def register_user(self, user_data: UserCreate) -> User:
        """사용자 회원가입"""
        # 1. 중복 검증
        if await self.user_repository.email_exists(user_data.email):
            raise EmailAlreadyExistsError("이미 등록된 이메일입니다")
            
        # 2. 비밀번호 해싱
        password_hash = hash_password(user_data.password)
        
        # 3. 사용자 생성
        return await self.user_repository.create(user_data, password_hash)
```

### 2.4 API 계층 (routers/)
**역할**: HTTP 요청/응답 처리

```python
# routers/auth.py 예시
from fastapi import APIRouter, Depends, HTTPException
from nadle_backend.models.core import UserCreate, UserResponse
from nadle_backend.services.auth_service import AuthService
from nadle_backend.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """회원가입"""
    auth_service = AuthService()
    user = await auth_service.register_user(user_data)
    return UserResponse(**user.model_dump())
```

## 3. 실제 구현된 API 구조

### 3.1 라우터 등록 (main.py)
```python
from fastapi import FastAPI
from nadle_backend.routers import auth, posts, comments, file_upload, content

app = FastAPI(title="Xai Community API")

# 실제 등록된 라우터들
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(posts.router, tags=["Posts"])  # /api/posts prefix 내장
app.include_router(comments.router, tags=["Comments"])  # /api/posts/{slug}/comments
app.include_router(file_upload.router, prefix="/api/files", tags=["Files"])
app.include_router(content.router, tags=["Content"])  # /api/content prefix 내장
```

### 3.2 실제 API 엔드포인트 구조
```
Authentication:
├── POST   /auth/register
├── POST   /auth/login
├── POST   /auth/refresh
├── GET    /auth/profile
├── PUT    /auth/profile
├── POST   /auth/change-password
├── POST   /auth/deactivate
├── GET    /auth/admin/users
├── POST   /auth/admin/users/{id}/suspend
├── POST   /auth/admin/users/{id}/activate
└── DELETE /auth/admin/users/{id}

Posts:
├── GET    /api/posts/search
├── GET    /api/posts
├── GET    /api/posts/{slug}
├── POST   /api/posts
├── PUT    /api/posts/{slug}
├── DELETE /api/posts/{slug}
├── POST   /api/posts/{slug}/like
├── POST   /api/posts/{slug}/dislike
├── POST   /api/posts/{slug}/bookmark
└── GET    /api/posts/{slug}/stats

Comments:
├── GET    /api/posts/{slug}/comments
├── POST   /api/posts/{slug}/comments
├── POST   /api/posts/{slug}/comments/{id}/replies
├── PUT    /api/posts/{slug}/comments/{id}
├── DELETE /api/posts/{slug}/comments/{id}
├── POST   /api/posts/{slug}/comments/{id}/like
└── POST   /api/posts/{slug}/comments/{id}/dislike

Files:
├── POST   /api/files/upload
├── GET    /api/files/{file_id}
├── GET    /api/files/{file_id}/info
└── GET    /api/files/health

Content:
├── POST   /api/content/preview
└── GET    /api/content/test
```

## 4. 환경 설정 및 파일 구조

### 4.1 설정 파일 위치
```
backend/
├── .env                    # 메인 환경 설정 파일
├── .env.example           # 환경 설정 템플릿
└── nadle_backend/
    └── config.py          # 설정 클래스 (자동으로 .env 파일 탐지)
```

### 4.2 환경 변수 구조 (backend/.env)
```bash
# Database Configuration
MONGODB_URL=mongodb+srv://...
DATABASE_NAME=app_database

# Collection Configuration
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
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]

# Environment Configuration
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0
```

## 5. Import 규칙 및 패키지 구조

### 5.1 Import 순서
```python
# 1. 표준 라이브러리
import os
from datetime import datetime
from typing import List, Optional

# 2. 서드파티 라이브러리  
from fastapi import APIRouter, Depends
from beanie import Document
from pydantic import BaseModel

# 3. 로컬 패키지 모듈
from nadle_backend.models.core import User
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.utils.jwt import create_token
```

### 5.2 패키지 구조 활용
```python
# nadle_backend 패키지 내에서의 절대 import
from nadle_backend.models.core import User, Post, Comment
from nadle_backend.services.auth_service import AuthService
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.exceptions.user import UserNotFoundError
```

## 6. 개발 워크플로우

### 6.1 새 기능 개발 순서
1. **모델 정의** (`nadle_backend/models/`)
2. **Repository 구현** (`nadle_backend/repositories/`)
3. **Service 로직 구현** (`nadle_backend/services/`)
4. **API 라우터 구현** (`nadle_backend/routers/`)
5. **의존성 설정** (`nadle_backend/dependencies/`)
6. **테스트 작성** (`tests/`)

### 6.2 패키지 빌드 및 설치
```bash
# 개발용 설치
cd backend && uv install

# 패키지 빌드
uv build

# 배포용 설치
pip install dist/nadle_backend-*.whl
```

## 7. 프로덕션 배포 구조

### 7.1 패키지 구조의 장점
- ✅ **표준 Python 패키지**: pip로 설치 가능
- ✅ **CLI 지원**: `nadle-backend` 명령어 제공
- ✅ **의존성 관리**: pyproject.toml로 체계적 관리
- ✅ **배포 용이성**: Docker, systemd 등 다양한 배포 방식 지원

### 7.2 실제 배포 시 구조
```
/opt/nadle_backend/
├── bin/nadle-backend          # CLI 실행 파일
├── lib/python3.x/site-packages/nadle_backend/  # 패키지
├── uploads/                   # 파일 저장소
├── .env                       # 프로덕션 환경 설정
└── logs/                      # 로그 파일
```

이 구조는 **현재 실제 구현된 백엔드 시스템**을 정확히 반영하며, 표준 Python 패키지 구조의 장점을 최대한 활용한 설계입니다.