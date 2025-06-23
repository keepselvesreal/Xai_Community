# 프로젝트 구조 가이드 (Project Structure Guide)

## 📋 목차

### 1. 전체 구조 개요 (Project Overview)
- **계층형 아키텍처**: 역할별 명확한 계층 분리
- **의존성 방향**: 상위 계층이 하위 계층 의존

### 2. 디렉토리 구조 (Directory Structure)
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
- **인터페이스 활용**: 느슨한 결합

### 6. 개발 워크플로우 (Development Workflow)
- **구현 순서**: 모델 → Repository → Service → Router
- **테스트 전략**: 각 계층별 테스트 방법

## 📊 항목 간 관계

```
API 계층 (routers) 
    ↓
서비스 계층 (services) 
    ↓
데이터 계층 (repositories) 
    ↓
모델 계층 (models)
    ↓
데이터베이스 (MongoDB)
```

- **API 계층**이 서비스 계층만 의존
- **서비스 계층**이 Repository와 모델 의존
- **Repository 계층**이 모델과 데이터베이스 의존
- **공통 모듈**들은 모든 계층에서 사용 가능

## 📝 각 항목 핵심 설명

### 전체 구조 개요
클린 아키텍처 원칙을 적용한 계층형 구조로 유지보수성과 테스트 용이성 확보

### 디렉토리 구조
기능별로 명확히 분리된 폴더 구조로 개발자가 쉽게 코드 위치 파악 가능

### 계층별 역할
각 계층의 단일 책임 원칙으로 코드 변경 시 영향 범위 최소화

### 파일 명명 규칙
일관된 명명 규칙으로 코드 가독성과 팀 협업 효율성 향상

### 모듈 간 의존성
의존성 역전 원칙 적용으로 느슨한 결합과 높은 응집도 달성

### 개발 워크플로우
체계적인 개발 순서로 안정적이고 일관된 코드 품질 보장

---

# 📖 본문

## 1. 전체 프로젝트 구조

### 디렉토리 트리
```
content-management-api/
├── src/
│   ├── models/             # 데이터 모델 (Pydantic)
│   │   ├── __init__.py
│   │   ├── user.py         # 사용자 모델
│   │   ├── post.py         # 게시글 모델
│   │   ├── comment.py      # 댓글 모델
│   │   └── common.py       # 공통 모델 (페이지네이션 등)
│   │
│   ├── repositories/       # 데이터 접근 계층
│   │   ├── __init__.py
│   │   ├── base.py         # 기본 Repository
│   │   ├── user_repository.py
│   │   ├── post_repository.py
│   │   ├── comment_repository.py
│   │   └── stats_repository.py
│   │
│   ├── services/           # 비즈니스 로직 계층
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   └── stats_service.py
│   │
│   ├── routers/            # API 라우터
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── posts.py
│   │   ├── comments.py
│   │   └── stats.py
│   │
│   ├── dependencies/       # FastAPI 의존성
│   │   ├── __init__.py
│   │   ├── auth.py         # 인증 의존성
│   │   └── database.py     # DB 의존성
│   │
│   ├── utils/              # 유틸리티 함수
│   │   ├── __init__.py
│   │   ├── jwt.py          # JWT 토큰 처리
│   │   ├── password.py     # 패스워드 해싱
│   │   ├── slug.py         # URL slug 생성
│   │   └── validators.py   # 커스텀 검증기
│   │
│   ├── exceptions/         # 커스텀 예외
│   │   ├── __init__.py
│   │   ├── auth_exceptions.py
│   │   ├── post_exceptions.py
│   │   └── base_exceptions.py
│   │
│   ├── database/           # DB 연결 및 설정
│   │   ├── __init__.py
│   │   ├── connection.py   # MongoDB 연결
│   │   └── indexes.py      # 인덱스 설정
│   │
│   ├── config.py           # 설정 관리
│   └── main.py             # FastAPI 앱
│
├── tests/                  # 테스트 코드
│   ├── unit/               # 단위 테스트
│   ├── integration/        # 통합 테스트
│   └── conftest.py         # 테스트 설정
│
├── .env.example            # 환경 변수 템플릿
├── .gitignore
└── README.md
```

## 2. 계층별 상세 역할

### 2.1 모델 계층 (models/)
**역할**: 데이터 구조 정의 및 검증
```python
# models/post.py 예시
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    service: ServiceType
    metadata: PostMetadata

class PostCreate(PostBase):
    pass  # 생성 시 필요한 필드만

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    # 업데이트 가능한 필드만

class Post(PostBase):
    id: str
    slug: str
    author_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 2.2 Repository 계층 (repositories/)
**역할**: 데이터베이스 접근 추상화
```python
# repositories/base.py 예시
from abc import ABC, abstractmethod
from typing import Optional, List, Generic, TypeVar
from motor.motor_asyncio import AsyncIOMotorCollection

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, update_data: dict) -> Optional[T]:
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        pass
```

### 2.3 서비스 계층 (services/)
**역할**: 비즈니스 로직 구현
```python
# services/post_service.py 예시
from typing import List, Optional
from models.post import Post, PostCreate, PostUpdate
from repositories.post_repository import PostRepository
from utils.slug import generate_slug

class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo
    
    async def create_post(self, post_data: PostCreate, author_id: str) -> Post:
        # 1. slug 생성
        slug = await self._generate_unique_slug(post_data.title)
        
        # 2. 게시글 생성
        post = Post(
            **post_data.dict(),
            author_id=author_id,
            slug=slug
        )
        
        # 3. 저장
        return await self.post_repo.create(post)
    
    async def _generate_unique_slug(self, title: str) -> str:
        # slug 중복 확인 로직
        pass
```

### 2.4 API 계층 (routers/)
**역할**: HTTP 요청/응답 처리
```python
# routers/posts.py 예시
from fastapi import APIRouter, Depends, HTTPException
from models.post import PostCreate, PostResponse
from services.post_service import PostService
from dependencies.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["게시글"])

@router.post("/", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """게시글 생성"""
    return await post_service.create_post(post_data, current_user.id)
```

## 3. 의존성 주입 패턴

### 3.1 Service 의존성
```python
# dependencies/services.py
from fastapi import Depends
from repositories.post_repository import PostRepository
from services.post_service import PostService

async def get_post_repository() -> PostRepository:
    # Repository 인스턴스 반환
    pass

async def get_post_service(
    repo: PostRepository = Depends(get_post_repository)
) -> PostService:
    return PostService(repo)
```

### 3.2 Router에서 사용
```python
@router.post("/")
async def create_post(
    post_service: PostService = Depends(get_post_service)
):
    # Service 사용
    pass
```

## 4. 파일 명명 규칙

### 4.1 Python 파일
```python
# 스네이크 케이스 사용
user_repository.py      # ✅ 올바름
userRepository.py       # ❌ 잘못됨
UserRepository.py       # ❌ 잘못됨
```

### 4.2 클래스명
```python
# 파스칼 케이스 사용
class UserRepository:   # ✅ 올바름
class userRepository:   # ❌ 잘못됨
class user_repository:  # ❌ 잘못됨
```

### 4.3 함수/변수명
```python
# 스네이크 케이스 사용
async def get_user_by_id():     # ✅ 올바름
async def getUserById():        # ❌ 잘못됨

user_handle = "test"            # ✅ 올바름
userHandle = "test"             # ❌ 잘못됨
```

## 5. Import 규칙

### 5.1 Import 순서
```python
# 1. 표준 라이브러리
import os
from datetime import datetime
from typing import List, Optional

# 2. 서드파티 라이브러리  
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. 로컬 모듈
from models.user import User
from repositories.user_repository import UserRepository
from utils.jwt import create_token
```

### 5.2 상대 import vs 절대 import
```python
# 절대 import 권장
from repositories.user_repository import UserRepository  # ✅ 권장
from ..repositories.user_repository import UserRepository  # ❌ 비권장
```

## 6. 개발 워크플로우

### 6.1 새 기능 개발 순서
1. **모델 정의** (models/)
2. **Repository 구현** (repositories/)
3. **Service 로직 구현** (services/)
4. **API 라우터 구현** (routers/)
5. **의존성 설정** (dependencies/)
6. **테스트 작성** (tests/)

### 6.2 코드 리뷰 체크리스트
- [ ] 의존성 방향이 올바른가?
- [ ] 단일 책임 원칙을 지키는가?
- [ ] 에러 처리가 적절한가?
- [ ] 타입 힌트가 명확한가?
- [ ] 테스트가 작성되었는가?

## 7. 설정 및 초기화

### 7.1 main.py 구조
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, posts, comments
from database.connection import connect_to_mongo, close_mongo_connection
from config import settings

# FastAPI 앱 생성
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라이프사이클 이벤트
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# 라우터 등록
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)

# 헬스체크
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## 8. 환경별 설정

### 8.1 개발 환경 실행
```bash
# 개발 서버 실행
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 특정 환경 변수로 실행
ENVIRONMENT=development uvicorn src.main:app --reload
```

### 8.2 프로덕션 환경 고려사항
```python
# main.py에서 환경별 설정
if settings.environment == "production":
    # 프로덕션 전용 설정
    app.docs_url = None  # Swagger 비활성화
    app.redoc_url = None
```
