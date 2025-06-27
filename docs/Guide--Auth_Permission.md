# 인증/권한 처리 가이드 (프리랜서 최적화)

## 📋 목차

### 1. 사용자 모델 (User Model)
- **기본 사용자 구조**: 필수 인증 필드 정의
- **확장 가능성**: 추후 기능 확장을 위한 유연한 구조

### 2. JWT 토큰 시스템 (JWT Token System)
- **토큰 생성**: 로그인 시 JWT 토큰 발급
- **토큰 검증**: API 요청 시 토큰 유효성 확인

### 3. 인증 미들웨어 (Authentication Middleware)
- **자동 인증**: FastAPI Dependency로 간편한 인증 처리
- **선택적 인증**: 인증 필요/불필요 API 구분

### 4. 권한 관리 (Authorization)
- **리소스 권한**: 게시글/댓글 소유자 확인
- **역할 기반**: 관리자 권한 처리

### 5. 보안 강화 (Security Enhancement)
- **패스워드 해싱**: 안전한 비밀번호 저장
- **토큰 보안**: JWT 토큰 보안 설정

### 6. API 통합 (API Integration)
- **라우터 적용**: 실제 API에 인증 적용
- **에러 처리**: 인증 실패 시 적절한 응답

## 📊 항목 간 관계

```
사용자 모델 → JWT 토큰 → 인증 미들웨어 → 권한 관리 → API 통합
                ↓
              보안 강화
```

- **사용자 모델**이 인증 시스템의 기반
- **JWT 토큰**이 인증 상태 관리 도구
- **인증 미들웨어**가 자동 인증 처리 담당
- **권한 관리**로 리소스 접근 제어
- **보안 강화**가 전체 시스템 보안 보장
- **API 통합**으로 실제 서비스에 적용

## 📝 각 항목 핵심 설명

### 사용자 모델
최소 필수 필드로 구성된 실용적 사용자 모델과 MongoDB 연동

### JWT 토큰 시스템
python-jose 기반 안전한 토큰 생성 및 검증 시스템

### 인증 미들웨어
FastAPI Dependency Injection을 활용한 자동 인증 처리

### 권한 관리
소유자 기반 권한과 역할 기반 권한의 단순하고 효과적인 구현

### 보안 강화
bcrypt 해싱과 JWT 보안 설정으로 기본 보안 수준 확보

### API 통합
실제 게시글/댓글 API에 인증 시스템을 자연스럽게 통합

---

# 📖 본문

## 1. 사용자 모델

### User 모델 정의

#### models/user.py
```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# 사용자 기본 모델
class UserBase(BaseModel):
    email: EmailStr
    user_handle: str = Field(..., min_length=3, max_length=20)
    display_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    
    @validator('user_handle')
    def validate_user_handle(cls, v):
        # 영문, 숫자, 언더스코어만 허용
        import re
        if not re.match(r'^[a-zA-Z0-9_]+

# 토큰 관련 모델
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
```

### 사용자 저장소 (Repository)

#### repositories/user_repository.py
```python
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from models.user import User, UserCreate, UserUpdate
from database import get_users_collection
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.collection: AsyncIOMotorCollection = None
    
    async def get_collection(self):
        if not self.collection:
            self.collection = await get_users_collection()
        return self.collection
    
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """사용자 생성"""
        collection = await self.get_collection()
        
        user = User(
            **user_data.dict(exclude={'password'}),
            hashed_password=hashed_password
        )
        
        await collection.insert_one(user.dict())
        logger.info(f"사용자 생성 완료: {user.email}")
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        collection = await self.get_collection()
        user_data = await collection.find_one({"email": email})
        
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """ID로 사용자 조회"""
        collection = await self.get_collection()
        user_data = await collection.find_one({"id": user_id})
        
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_user_handle(self, user_handle: str) -> Optional[User]:
        """사용자 핸들로 조회"""
        collection = await self.get_collection()
        user_data = await collection.find_one({"user_handle": user_handle})
        
        if user_data:
            return User(**user_data)
        return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """사용자 정보 수정"""
        collection = await self.get_collection()
        
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id)
        
        return None
    
    async def update_last_login(self, user_id: str):
        """마지막 로그인 시간 업데이트"""
        collection = await self.get_collection()
        await collection.update_one(
            {"id": user_id},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
    
    async def email_exists(self, email: str) -> bool:
        """이메일 중복 확인"""
        collection = await self.get_collection()
        count = await collection.count_documents({"email": email})
        return count > 0
    
    async def user_handle_exists(self, user_handle: str) -> bool:
        """사용자 핸들 중복 확인"""
        collection = await self.get_collection()
        count = await collection.count_documents({"user_handle": user_handle})
        return count > 0

# 전역 저장소 인스턴스
user_repository = UserRepository()
```

## 2. JWT 토큰 시스템

### JWT 유틸리티

#### utils/jwt.py
```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from config import settings
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TokenType(str, Enum):
    """토큰 타입 정의 - 타입 안전성과 확장성 보장"""
    ACCESS = "access"
    REFRESH = "refresh"

class JWTHandler:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
    
    def create_access_token(self, user_id: str, email: str) -> Dict[str, Any]:
        """액세스 토큰 생성"""
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value  # Enum 사용으로 타입 안전성 보장
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.expire_minutes * 60  # 초 단위
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 토큰 타입 확인
            if payload.get("type") != TokenType.ACCESS.value:
                return None
            
            # 필수 필드 확인
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            if not user_id or not email:
                return None
            
            return {
                "user_id": user_id,
                "email": email,
                "exp": payload.get("exp")
            }
            
        except JWTError as e:
            logger.warning(f"JWT 토큰 검증 실패: {e}")
            return None
    
    def is_token_expired(self, payload: Dict[str, Any]) -> bool:
        """토큰 만료 확인"""
        exp = payload.get("exp")
        if not exp:
            return True
        
        return datetime.utcnow() > datetime.fromtimestamp(exp)

# 전역 JWT 핸들러
jwt_handler = JWTHandler()
```

### 패스워드 해싱

#### utils/password.py
```python
from passlib.context import CryptContext
import secrets
import string

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHandler:
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """랜덤 비밀번호 생성 (임시 비밀번호용)"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

# 전역 패스워드 핸들러
password_handler = PasswordHandler()
```

## 3. 인증 미들웨어

### FastAPI Dependency

#### dependencies/auth.py
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from models.user import User, UserRole
from repositories.user_repository import user_repository
from utils.jwt import jwt_handler
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

class AuthDependency:
    def __init__(self, required: bool = True):
        self.required = required
    
    async def __call__(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[User]:
        """인증 의존성"""
        if not credentials:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증 토큰이 필요합니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # 토큰 검증
        payload = jwt_handler.verify_token(credentials.credentials)
        if not payload:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰입니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # 토큰 만료 확인
        if jwt_handler.is_token_expired(payload):
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="만료된 토큰입니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # 사용자 조회
        user = await user_repository.get_user_by_id(payload["user_id"])
        if not user:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="사용자를 찾을 수 없습니다",
                )
            return None
        
        # 사용자 상태 확인
        if user.status != "active":
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="비활성화된 계정입니다",
                )
            return None
        
        return user

# 자주 사용하는 의존성들
get_current_user = AuthDependency(required=True)
get_optional_current_active_user = AuthDependency(required=False)

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """관리자 권한 확인"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

async def get_admin_only(current_user: User = Depends(get_current_user)) -> User:
    """최고 관리자 권한만"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="최고 관리자 권한이 필요합니다"
        )
    return current_user
```

## 4. 권한 관리

### 리소스 권한 체크

#### utils/permissions.py
```python
from fastapi import HTTPException, status
from models.user import User, UserRole
from typing import Optional

class PermissionChecker:
    @staticmethod
    def check_post_owner(user: User, post_author_id: str) -> bool:
        """게시글 소유자 확인"""
        # 관리자는 모든 게시글 접근 가능
        if user.role in [UserRole.ADMIN, UserRole.MODERATOR]:
            return True
        
        # 작성자 본인만 접근 가능
        return user.id == post_author_id
    
    @staticmethod
    def check_comment_owner(user: User, comment_author_id: str) -> bool:
        """댓글 소유자 확인"""
        # 관리자는 모든 댓글 접근 가능
        if user.role in [UserRole.ADMIN, UserRole.MODERATOR]:
            return True
        
        # 작성자 본인만 접근 가능
        return user.id == comment_author_id
    
    @staticmethod
    def validate_post_ownership(user: User, post_author_id: str):
        """게시글 소유자 권한 검증"""
        if not PermissionChecker.check_post_owner(user, post_author_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게시글 작성자만 접근할 수 있습니다"
            )
    
    @staticmethod
    def validate_comment_ownership(user: User, comment_author_id: str):
        """댓글 소유자 권한 검증"""
        if not PermissionChecker.check_comment_owner(user, comment_author_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="댓글 작성자만 접근할 수 있습니다"
            )
    
    @staticmethod
    def can_moderate_content(user: User) -> bool:
        """콘텐츠 관리 권한 확인"""
        return user.role in [UserRole.ADMIN, UserRole.MODERATOR]
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """사용자 관리 권한 확인"""
        return user.role == UserRole.ADMIN

# 전역 권한 체커
permission_checker = PermissionChecker()
```

## 5. 인증 서비스

### 인증 관련 비즈니스 로직

#### services/auth_service.py
```python
from fastapi import HTTPException, status
from models.user import User, UserCreate, UserLogin, Token
from repositories.user_repository import user_repository
from utils.jwt import jwt_handler
from utils.password import password_handler
import logging

logger = logging.getLogger(__name__)

class AuthService:
    async def register_user(self, user_data: UserCreate) -> User:
        """사용자 회원가입"""
        # 이메일 중복 확인
        if await user_repository.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 등록된 이메일입니다"
            )
        
        # 사용자 핸들 중복 확인
        if await user_repository.user_handle_exists(user_data.user_handle):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 사용자 핸들입니다"
            )
        
        # 비밀번호 해싱
        hashed_password = password_handler.hash_password(user_data.password)
        
        # 사용자 생성
        user = await user_repository.create_user(user_data, hashed_password)
        logger.info(f"새 사용자 등록: {user.email}")
        
        return user
    
    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """사용자 로그인"""
        # 사용자 조회
        user = await user_repository.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )
        
        # 비밀번호 확인
        if not password_handler.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )
        
        # 계정 상태 확인
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다"
            )
        
        # 마지막 로그인 시간 업데이트
        await user_repository.update_last_login(user.id)
        
        # 토큰 생성
        token_data = jwt_handler.create_access_token(user.id, user.email)
        
        logger.info(f"사용자 로그인: {user.email}")
        return Token(**token_data)
    
    async def get_user_profile(self, user_id: str) -> User:
        """사용자 프로필 조회"""
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        return user

# 전역 인증 서비스
auth_service = AuthService()
```

## 6. API 통합

### 인증 API 라우터

#### routers/auth.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from models.user import UserCreate, UserLogin, UserResponse, Token, User
from services.auth_service import auth_service
from dependencies.auth import get_current_user
from typing import List

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """회원가입"""
    user = await auth_service.register_user(user_data)
    return UserResponse(**user.dict())

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """로그인"""
    return await auth_service.authenticate_user(login_data)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """현재 사용자 프로필 조회"""
    return UserResponse(**current_user.dict())

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """로그아웃 (토큰 무효화는 클라이언트에서 처리)"""
    return {"message": "로그아웃되었습니다"}

@router.get("/check-email/{email}")
async def check_email_availability(email: str):
    """이메일 중복 확인"""
    from repositories.user_repository import user_repository
    exists = await user_repository.email_exists(email)
    return {"available": not exists}

@router.get("/check-user-handle/{user_handle}")
async def check_user_handle_availability(user_handle: str):
    """사용자 핸들 중복 확인"""
    from repositories.user_repository import user_repository
    exists = await user_repository.user_handle_exists(user_handle)
    return {"available": not exists}
```

### 게시글 API에 인증 적용

#### routers/posts.py (인증 적용 예시)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependencies.auth import get_current_user, get_optional_current_active_user
from utils.permissions import permission_checker
from models.user import User
from typing import Optional

router = APIRouter(prefix="/posts", tags=["게시글"])

@router.get("/{slug}")
async def get_post_detail(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user)
):
    """게시글 상세 조회 (로그인 선택)"""
    # 게시글 조회 로직
    post = await posts_service.get_post_by_slug(slug)
    
    # 사용자별 반응 정보 포함 (로그인한 경우)
    if current_user:
        user_reaction = await get_user_reaction(post.id, current_user.id)
        post.user_reaction = user_reaction
    
    return post

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: CreatePostRequest,
    current_user: User = Depends(get_current_user)  # 인증 필수
):
    """게시글 생성"""
    # authorId를 현재 사용자로 설정
    post_data.authorId = current_user.id
    
    post = await posts_service.create_post(post_data)
    return post

@router.put("/{slug}")
async def update_post(
    slug: str,
    post_data: UpdatePostRequest,
    current_user: User = Depends(get_current_user)
):
    """게시글 수정"""
    # 기존 게시글 조회
    existing_post = await posts_service.get_post_by_slug(slug)
    
    # 소유자 권한 확인
    permission_checker.validate_post_ownership(current_user, existing_post.authorId)
    
    # 게시글 수정
    updated_post = await posts_service.update_post(slug, post_data)
    return updated_post

@router.delete("/{slug}")
async def delete_post(
    slug: str,
    current_user: User = Depends(get_current_user)
):
    """게시글 삭제"""
    # 기존 게시글 조회
    existing_post = await posts_service.get_post_by_slug(slug)
    
    # 소유자 권한 확인
    permission_checker.validate_post_ownership(current_user, existing_post.authorId)
    
    # 게시글 삭제
    await posts_service.delete_post(slug)
    return {"message": "게시글이 삭제되었습니다"}

@router.post("/{slug}/like")
async def like_post(
    slug: str,
    current_user: User = Depends(get_current_user)
):
    """게시글 좋아요 토글"""
    result = await posts_service.toggle_like(slug, current_user.id)
    return result

@router.post("/{slug}/bookmark")
async def bookmark_post(
    slug: str,
    current_user: User = Depends(get_current_user)
):
    """게시글 북마크 토글"""
    result = await posts_service.toggle_bookmark(slug, current_user.id)
    return result
```

### 댓글 API에 인증 적용

#### routers/comments.py (인증 적용 예시)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from dependencies.auth import get_current_user, get_optional_current_active_user
from utils.permissions import permission_checker
from models.user import User
from typing import Optional

router = APIRouter(prefix="/posts/{post_slug}/comments", tags=["댓글"])

@router.get("/")
async def get_comments(
    post_slug: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_active_user)
):
    """댓글 목록 조회 (로그인 선택)"""
    comments = await comments_service.get_comments_by_post_slug(
        post_slug, page, limit, current_user.id if current_user else None
    )
    return comments

@router.post("/")
async def create_comment(
    post_slug: str,
    comment_data: CreateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """댓글 생성"""
    # authorId를 현재 사용자로 설정
    comment_data.authorId = current_user.id
    
    comment = await comments_service.create_comment(post_slug, comment_data)
    return comment

@router.put("/{comment_id}")
async def update_comment(
    post_slug: str,
    comment_id: str,
    comment_data: UpdateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """댓글 수정"""
    # 기존 댓글 조회
    existing_comment = await comments_service.get_comment_by_id(comment_id)
    
    # 소유자 권한 확인
    permission_checker.validate_comment_ownership(current_user, existing_comment.authorId)
    
    # 댓글 수정
    updated_comment = await comments_service.update_comment(comment_id, comment_data)
    return updated_comment

@router.delete("/{comment_id}")
async def delete_comment(
    post_slug: str,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """댓글 삭제"""
    # 기존 댓글 조회
    existing_comment = await comments_service.get_comment_by_id(comment_id)
    
    # 소유자 권한 확인
    permission_checker.validate_comment_ownership(current_user, existing_comment.authorId)
    
    # 댓글 삭제 (상태만 변경)
    await comments_service.delete_comment(comment_id)
    return {"message": "댓글이 삭제되었습니다"}
```

## 7. 에러 처리

### 인증 관련 예외 처리

#### exceptions/auth_exceptions.py
```python
from fastapi import HTTPException, status

class AuthException(HTTPException):
    """기본 인증 예외"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class TokenExpiredException(AuthException):
    def __init__(self):
        super().__init__("토큰이 만료되었습니다")

class InvalidTokenException(AuthException):
    def __init__(self):
        super().__init__("유효하지 않은 토큰입니다")

class UserNotFoundException(AuthException):
    def __init__(self):
        super().__init__("사용자를 찾을 수 없습니다")

class InactiveUserException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

class PermissionDeniedException(HTTPException):
    def __init__(self, detail: str = "권한이 없습니다"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
```

## 8. 사용 예시

### main.py에 라우터 등록

```python
from fastapi import FastAPI
from routers import auth, posts, comments

app = FastAPI(title="콘텐츠 관리 API")

# 라우터 등록
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)

@app.get("/")
async def root():
    return {"message": "API 서버가 실행 중입니다"}
```

### 클라이언트 사용 예시

```javascript
// 회원가입
const registerResponse = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        user_handle: 'testuser',
        password: 'securepassword123',
        display_name: '테스트 사용자'
    })
});

// 로그인
const loginResponse = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'securepassword123'
    })
});

const { access_token } = await loginResponse.json();

// 인증이 필요한 API 호출
const postResponse = await fetch('/posts', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({
        title: '새 게시글',
        content: '게시글 내용',
        service: 'community',
        metadata: { type: '자유게시판' }
    })
});
```

이 구성으로 **안전하고 확장 가능한** 인증/권한 시스템을 구축할 수 있습니다., v):
            raise ValueError('사용자 핸들은 영문, 숫자, 언더스코어만 사용 가능합니다')
        return v.lower()

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    status: Optional[UserStatus] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# API 응답용 모델 (비밀번호 제외)
class UserResponse(BaseModel):
    id: str
    email: str
    user_handle: str
    display_name: Optional[str]
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login_at: Optional[datetime]

# 토큰 관련 모델
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
```

### 사용자 저장소 (Repository)

#### repositories/user_repository.py
```python
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from models.user import User, UserCreate, UserUpdate
from database import get_users_collection
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.collection: AsyncIOMotorCollection = None
    
    async def get_collection(self):
        if not self.collection:
            self.collection = await get_users_collection()
        return self.collection
    
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """사용자 생성"""
        collection = await self.get_collection()
        
        user = User(
            **user_data.dict(exclude={'password'}),
            hashed_password=hashed_password
        )
        
        await collection.insert_one(user.dict())
        logger.info(f"사용자 생성 완료: {user.email}")
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        collection = await self.get_collection()
        user_data = await collection.find_one({"email": email})
        
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """ID로 사용자 조회"""
        collection = await self.get_collection()
        user_data = await collection.find_one({"id": user_id})
        
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 조회"""
        collection = await self.get_collection()
        user_data = await collection.find_one({"username": username})
        
        if user_data:
            return User(**user_data)
        return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """사용자 정보 수정"""
        collection = await self.get_collection()
        
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id)
        
        return None
    
    async def update_last_login(self, user_id: str):
        """마지막 로그인 시간 업데이트"""
        collection = await self.get_collection()
        await collection.update_one(
            {"id": user_id},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
    
    async def email_exists(self, email: str) -> bool:
        """이메일 중복 확인"""
        collection = await self.get_collection()
        count = await collection.count_documents({"email": email})
        return count > 0
    
    async def username_exists(self, username: str) -> bool:
        """사용자명 중복 확인"""
        collection = await self.get_collection()
        count = await collection.count_documents({"username": username})
        return count > 0

# 전역 저장소 인스턴스
user_repository = UserRepository()
```

## 2. JWT 토큰 시스템

### JWT 유틸리티

#### utils/jwt.py
```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from config import settings
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TokenType(str, Enum):
    """토큰 타입 정의 - 타입 안전성과 확장성 보장"""
    ACCESS = "access"
    REFRESH = "refresh"

class JWTHandler:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
    
    def create_access_token(self, user_id: str, email: str) -> Dict[str, Any]:
        """액세스 토큰 생성"""
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": TokenType.ACCESS.value  # Enum 사용으로 타입 안전성 보장
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.expire_minutes * 60  # 초 단위
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 토큰 타입 확인
            if payload.get("type") != TokenType.ACCESS.value:
                return None
            
            # 필수 필드 확인
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            if not user_id or not email:
                return None
            
            return {
                "user_id": user_id,
                "email": email,
                "exp": payload.get("exp")
            }
            
        except JWTError as e:
            logger.warning(f"JWT 토큰 검증 실패: {e}")
            return None
    
    def is_token_expired(self, payload: Dict[str, Any]) -> bool:
        """토큰 만료 확인"""
        exp = payload.get("exp")
        if not exp:
            return True
        
        return datetime.utcnow() > datetime.fromtimestamp(exp)

# 전역 JWT 핸들러
jwt_handler = JWTHandler()
```

### 패스워드 해싱

#### utils/password.py
```python
from passlib.context import CryptContext
import secrets
import string

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHandler:
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """랜덤 비밀번호 생성 (임시 비밀번호용)"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

# 전역 패스워드 핸들러
password_handler = PasswordHandler()
```

## 3. 인증 미들웨어

### FastAPI Dependency

#### dependencies/auth.py
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from models.user import User, UserRole
from repositories.user_repository import user_repository
from utils.jwt import jwt_handler
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

class AuthDependency:
    def __init__(self, required: bool = True):
        self.required = required
    
    async def __call__(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[User]:
        """인증 의존성"""
        if not credentials:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증 토큰이 필요합니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # 토큰 검증
        payload = jwt_handler.verify_token(credentials.credentials)
        if not payload:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰입니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # 토큰 만료 확인
        if jwt_handler.is_token_expired(payload):
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="만료된 토큰입니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # 사용자 조회
        user = await user_repository.get_user_by_id(payload["user_id"])
        if not user:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="사용자를 찾을 수 없습니다",
                )
            return None
        
        # 사용자 상태 확인
        if user.status != "active":
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="비활성화된 계정입니다",
                )
            return None
        
        return user

# 자주 사용하는 의존성들
get_current_user = AuthDependency(required=True)
get_optional_current_active_user = AuthDependency(required=False)

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """관리자 권한 확인"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

async def get_admin_only(current_user: User = Depends(get_current_user)) -> User:
    """최고 관리자 권한만"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="최고 관리자 권한이 필요합니다"
        )
    return current_user
```

## 4. 권한 관리

### 리소스 권한 체크

#### utils/permissions.py
```python
from fastapi import HTTPException, status
from models.user import User, UserRole
from typing import Optional

class PermissionChecker:
    @staticmethod
    def check_post_owner(user: User, post_author_id: str) -> bool:
        """게시글 소유자 확인"""
        # 관리자는 모든 게시글 접근 가능
        if user.role in [UserRole.ADMIN, UserRole.MODERATOR]:
            return True
        
        # 작성자 본인만 접근 가능
        return user.id == post_author_id
    
    @staticmethod
    def check_comment_owner(user: User, comment_author_id: str) -> bool:
        """댓글 소유자 확인"""
        # 관리자는 모든 댓글 접근 가능
        if user.role in [UserRole.ADMIN, UserRole.MODERATOR]:
            return True
        
        # 작성자 본인만 접근 가능
        return user.id == comment_author_id
    
    @staticmethod
    def validate_post_ownership(user: User, post_author_id: str):
        """게시글 소유자 권한 검증"""
        if not PermissionChecker.check_post_owner(user, post_author_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게시글 작성자만 접근할 수 있습니다"
            )
    
    @staticmethod
    def validate_comment_ownership(user: User, comment_author_id: str):
        """댓글 소유자 권한 검증"""
        if not PermissionChecker.check_comment_owner(user, comment_author_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="댓글 작성자만 접근할 수 있습니다"
            )
    
    @staticmethod
    def can_moderate_content(user: User) -> bool:
        """콘텐츠 관리 권한 확인"""
        return user.role in [UserRole.ADMIN, UserRole.MODERATOR]
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """사용자 관리 권한 확인"""
        return user.role == UserRole.ADMIN

# 전역 권한 체커
permission_checker = PermissionChecker()
```

## 5. 인증 서비스

### 인증 관련 비즈니스 로직

#### services/auth_service.py
```python
from fastapi import HTTPException, status
from models.user import User, UserCreate, UserLogin, Token
from repositories.user_repository import user_repository
from utils.jwt import jwt_handler
from utils.password import password_handler
import logging

logger = logging.getLogger(__name__)

class AuthService:
    async def register_user(self, user_data: UserCreate) -> User:
        """사용자 회원가입"""
        # 이메일 중복 확인
        if await user_repository.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 등록된 이메일입니다"
            )
        
        # 사용자명 중복 확인
        if await user_repository.username_exists(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 사용자명입니다"
            )
        
        # 비밀번호 해싱
        hashed_password = password_handler.hash_password(user_data.password)
        
        # 사용자 생성
        user = await user_repository.create_user(user_data, hashed_password)
        logger.info(f"새 사용자 등록: {user.email}")
        
        return user
    
    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """사용자 로그인"""
        # 사용자 조회
        user = await user_repository.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )
        
        # 비밀번호 확인
        if not password_handler.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )
        
        # 계정 상태 확인
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다"
            )
        
        # 마지막 로그인 시간 업데이트
        await user_repository.update_last_login(user.id)
        
        # 토큰 생성
        token_data = jwt_handler.create_access_token(user.id, user.email)
        
        logger.info(f"사용자 로그인: {user.email}")
        return Token(**token_data)
    
    async def get_user_profile(self, user_id: str) -> User:
        """사용자 프로필 조회"""
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        return user

# 전역 인증 서비스
auth_service = AuthService()
```

## 6. API 통합

### 인증 API 라우터

#### routers/auth.py
```python
from fastapi import APIRouter, Depends, HTTPException, status
from models.user import UserCreate, UserLogin, UserResponse, Token, User
from services.auth_service import auth_service
from dependencies.auth import get_current_user
from typing import List

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """회원가입"""
    user = await auth_service.register_user(user_data)
    return UserResponse(**user.dict())

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """로그인"""
    return await auth_service.authenticate_user(login_data)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """현재 사용자 프로필 조회"""
    return UserResponse(**current_user.dict())

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """로그아웃 (토큰 무효화는 클라이언트에서 처리)"""
    return {"message": "로그아웃되었습니다"}

@router.get("/check-email/{email}")
async def check_email_availability(email: str):
    """이메일 중복 확인"""
    from repositories.user_repository import user_repository
    exists = await user_repository.email_exists(email)
    return {"available": not exists}

@router.get("/check-username/{username}")
async def check_username_availability(username: str):
    """사용자명 중복 확인"""
    from repositories.user_repository import user_repository
    exists = await user_repository.username_exists(username)
    return {"available": not exists}
```

### 게시글 API에 인증 적용

#### routers/posts.py (인증 적용 예시)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependencies.auth import get_current_user, get_optional_current_active_user
from utils.permissions import permission_checker
from models.user import User
from typing import Optional

router = APIRouter(prefix="/posts", tags=["게시글"])

@router.get("/{slug}")
async def get_post_detail(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user)
):
    """게시글 상세 조회 (로그인 선택)"""
    # 게시글 조회 로직
    post = await posts_service.get_post_by_slug(slug)
    
    # 사용자별 반응 정보 포함 (로그인한 경우)
    if current_user:
        user_reaction = await get_user_reaction(post.id, current_user.id)
        post.user_reaction = user_reaction
    
    return post

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: CreatePostRequest,
    current_user: User = Depends(get_current_user)  # 인증 필수
):
    """게시글 생성"""
    # authorId를 현재 사용자로 설정
    post_data.authorId = current_user.id
    
    post = await posts_service.create_post(post_data)
    return post

@router.put("/{slug}")
async def update_post(
    slug: str,
    post_data: UpdatePostRequest,
    current_user: User = Depends(get_current_user)
):
    """게시글 수정"""
    # 기존 게시글 조회
    existing_post = await posts_service.get_post_by_slug(slug)
    
    # 소유자 권한 확인
    permission_checker.validate_post_ownership(current_user, existing_post.authorId)
    
    # 게시글 수정
    updated_post = await posts_service.update_post(slug, post_data)
    return updated_post

@router.delete("/{slug}")
async def delete_post(
    slug: str,
    current_user: User = Depends(get_current_user)
):
    """게시글 삭제"""
    # 기존 게시글 조회
    existing_post = await posts_service.get_post_by_slug(slug)
    
    # 소유자 권한 확인
    permission_checker.validate_post_ownership(current_user, existing_post.authorId)
    
    # 게시글 삭제
    await posts_service.delete_post(slug)
    return {"message": "게시글이 삭제되었습니다"}

@router.post("/{slug}/like")
async def like_post(
    slug: str,
    current_user: User = Depends(get_current_user)
):
    """게시글 좋아요 토글"""
    result = await posts_service.toggle_like(slug, current_user.id)
    return result

@router.post("/{slug}/bookmark")
async def bookmark_post(
    slug: str,
    current_user: User = Depends(get_current_user)
):
    """게시글 북마크 토글"""
    result = await posts_service.toggle_bookmark(slug, current_user.id)
    return result
```

### 댓글 API에 인증 적용

#### routers/comments.py (인증 적용 예시)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from dependencies.auth import get_current_user, get_optional_current_active_user
from utils.permissions import permission_checker
from models.user import User
from typing import Optional

router = APIRouter(prefix="/posts/{post_slug}/comments", tags=["댓글"])

@router.get("/")
async def get_comments(
    post_slug: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_active_user)
):
    """댓글 목록 조회 (로그인 선택)"""
    comments = await comments_service.get_comments_by_post_slug(
        post_slug, page, limit, current_user.id if current_user else None
    )
    return comments

@router.post("/")
async def create_comment(
    post_slug: str,
    comment_data: CreateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """댓글 생성"""
    # authorId를 현재 사용자로 설정
    comment_data.authorId = current_user.id
    
    comment = await comments_service.create_comment(post_slug, comment_data)
    return comment

@router.put("/{comment_id}")
async def update_comment(
    post_slug: str,
    comment_id: str,
    comment_data: UpdateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """댓글 수정"""
    # 기존 댓글 조회
    existing_comment = await comments_service.get_comment_by_id(comment_id)
    
    # 소유자 권한 확인
    permission_checker.validate_comment_ownership(current_user, existing_comment.authorId)
    
    # 댓글 수정
    updated_comment = await comments_service.update_comment(comment_id, comment_data)
    return updated_comment

@router.delete("/{comment_id}")
async def delete_comment(
    post_slug: str,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """댓글 삭제"""
    # 기존 댓글 조회
    existing_comment = await comments_service.get_comment_by_id(comment_id)
    
    # 소유자 권한 확인
    permission_checker.validate_comment_ownership(current_user, existing_comment.authorId)
    
    # 댓글 삭제 (상태만 변경)
    await comments_service.delete_comment(comment_id)
    return {"message": "댓글이 삭제되었습니다"}
```

## 7. 에러 처리

### 인증 관련 예외 처리

#### exceptions/auth_exceptions.py
```python
from fastapi import HTTPException, status

class AuthException(HTTPException):
    """기본 인증 예외"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class TokenExpiredException(AuthException):
    def __init__(self):
        super().__init__("토큰이 만료되었습니다")

class InvalidTokenException(AuthException):
    def __init__(self):
        super().__init__("유효하지 않은 토큰입니다")

class UserNotFoundException(AuthException):
    def __init__(self):
        super().__init__("사용자를 찾을 수 없습니다")

class InactiveUserException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

class PermissionDeniedException(HTTPException):
    def __init__(self, detail: str = "권한이 없습니다"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
```

## 8. 사용 예시

### main.py에 라우터 등록

```python
from fastapi import FastAPI
from routers import auth, posts, comments

app = FastAPI(title="콘텐츠 관리 API")

# 라우터 등록
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)

@app.get("/")
async def root():
    return {"message": "API 서버가 실행 중입니다"}
```

### 클라이언트 사용 예시

```javascript
// 회원가입
const registerResponse = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        username: 'testuser',
        password: 'securepassword123',
        full_name: '테스트 사용자'
    })
});

// 로그인
const loginResponse = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'securepassword123'
    })
});

const { access_token } = await loginResponse.json();

// 인증이 필요한 API 호출
const postResponse = await fetch('/posts', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({
        title: '새 게시글',
        content: '게시글 내용',
        service: 'community',
        metadata: { type: '자유게시판' }
    })
});
```

이 구성으로 **안전하고 확장 가능한** 인증/권한 시스템을 구축할 수 있습니다.