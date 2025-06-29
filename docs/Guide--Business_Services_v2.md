# 비즈니스 서비스 가이드 v2 (실제 구현 반영)

**작성일**: 2025-06-29  
**업데이트**: 실제 구현된 nadle_backend 패키지 및 서비스 계층 반영

## 📋 목차

### 1. 서비스 계층 개요 (Service Layer Overview)
- **Beanie ODM 기반**: Repository와 API 사이의 비즈니스 로직 계층
- **단순한 의존성**: BaseService 추상화 없이 직접적 구현

### 2. 인증 서비스 (Auth Service)
- **사용자 관리**: 회원가입, 로그인, 프로필 관리
- **보안 처리**: 패스워드 해싱, JWT 토큰 생성 및 검증
- **관리자 기능**: 사용자 관리, 정지, 활성화

### 3. 게시글 서비스 (Posts Service)
- **CRUD 관리**: 게시글 생성, 수정, 삭제, 조회
- **고급 기능**: slug 생성, 검색, 필터링, 반응 시스템

### 4. 댓글 서비스 (Comments Service)
- **계층 관리**: 댓글과 대댓글의 계층 구조
- **상태 관리**: 활성/삭제 상태 처리 및 반응

### 5. 콘텐츠 서비스 (Content Service)
- **리치 텍스트 에디터**: 콘텐츠 처리 및 검증
- **미리보기 기능**: HTML 콘텐츠 처리 파이프라인

### 6. 파일 서비스 (File Services)
- **파일 업로드**: 파일 검증, 저장, 메타데이터 추출
- **저장소 관리**: 파일 시스템 조직 및 접근 제어

### 7. 공통 유틸리티 (Common Utilities)
- **JWT 처리**: 토큰 생성, 검증, 갱신
- **패스워드 관리**: 해싱, 검증, 보안 정책
- **권한 검증**: 사용자 및 리소스 접근 권한

## 📊 항목 간 관계

```
API Router (FastAPI 엔드포인트)
    ↓
Service Layer (비즈니스 로직)
    ↓
Repository Layer (Beanie ODM 데이터 접근)
    ↓
MongoDB Database (데이터 저장)
```

- **API Router**에서 Service 직접 호출
- **Service**에서 Repository와 Utils 활용
- **Repository**가 Beanie ODM을 통한 데이터 처리
- **Service간 협력**으로 복잡한 비즈니스 로직 구현

## 📝 각 항목 핵심 설명

### 서비스 계층 개요
비즈니스 로직을 캡슐화하여 API와 데이터 계층 사이의 중재자 역할, Beanie ODM과 완벽 통합

### 인증 서비스
사용자 생명주기 관리와 JWT 기반 보안 관련 모든 비즈니스 로직 처리

### 게시글 서비스
콘텐츠 관리의 핵심 비즈니스 로직과 복잡한 쿼리 처리, 반응 시스템 통합

### 댓글 서비스
계층적 댓글 시스템의 복잡한 관계와 상태 관리, 반응 기능 통합

### 콘텐츠 서비스
리치 텍스트 에디터와 콘텐츠 처리 파이프라인의 중심 비즈니스 로직

### 파일 서비스
파일 업로드, 검증, 저장, 메타데이터 추출의 종합적 관리

### 공통 유틸리티
모든 서비스에서 재사용 가능한 비즈니스 로직과 헬퍼 함수

---

# 📖 본문

## 1. 서비스 계층 기본 구조

### 1.1 실제 구현된 서비스 계층
현재 프로젝트는 **단순하고 실용적인 접근**을 채택하여, BaseService 추상화 없이 각 Service가 독립적으로 구현되어 있습니다. Beanie ODM과 함께 사용하여 복잡한 추상화 계층 없이 명확한 구조를 유지합니다.

```python
# nadle_backend/services/의 일반적인 서비스 패턴
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.utils.password import hash_password, verify_password
from nadle_backend.utils.jwt import create_token, verify_token
from nadle_backend.exceptions.auth import AuthenticationError

class AuthService:
    """Authentication service - 사용자 인증 및 관리 서비스"""
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    async def register_user(self, user_data: UserCreate) -> User:
        # 비즈니스 로직 구현
        pass
```

## 2. 인증 서비스 (AuthService)

### 2.1 실제 구현된 인증 서비스
```python
# nadle_backend/services/auth_service.py
from typing import Optional, Dict, Any
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.models.core import User, UserCreate, UserUpdate
from nadle_backend.utils.password import hash_password, verify_password
from nadle_backend.utils.jwt import create_token, verify_token
from nadle_backend.exceptions.auth import (
    EmailAlreadyExistsError,
    UserHandleAlreadyExistsError,
    InvalidCredentialsError,
    UserNotActiveError
)

class AuthService:
    """Authentication service for handling user auth and management."""
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    async def register_user(self, user_data: UserCreate) -> User:
        """사용자 회원가입"""
        # 1. 중복 검증
        if await self.user_repository.email_exists(user_data.email):
            raise EmailAlreadyExistsError("이미 등록된 이메일입니다")
            
        if await self.user_repository.user_handle_exists(user_data.user_handle):
            raise UserHandleAlreadyExistsError("이미 사용 중인 사용자 핸들입니다")
        
        # 2. 비밀번호 해싱
        password_hash = hash_password(user_data.password)
        
        # 3. 사용자 생성
        user = await self.user_repository.create(user_data, password_hash)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """사용자 로그인 인증"""
        # 1. 사용자 조회
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("잘못된 이메일 또는 비밀번호입니다")
        
        # 2. 비밀번호 검증
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("잘못된 이메일 또는 비밀번호입니다")
        
        # 3. 계정 상태 확인
        if not user.is_active:
            raise UserNotActiveError("비활성화된 계정입니다")
        
        # 4. 토큰 생성
        access_token = create_token(
            data={"user_id": str(user.id), "email": user.email},
            token_type="access"
        )
        refresh_token = create_token(
            data={"user_id": str(user.id)},
            token_type="refresh"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """리프레시 토큰으로 액세스 토큰 갱신"""
        # 리프레시 토큰 검증
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise InvalidCredentialsError("잘못된 리프레시 토큰입니다")
        
        # 사용자 존재 확인
        user = await self.user_repository.get_by_id(payload["user_id"])
        if not user or not user.is_active:
            raise InvalidCredentialsError("사용자를 찾을 수 없습니다")
        
        # 새 토큰 생성
        new_access_token = create_token(
            data={"user_id": str(user.id), "email": user.email},
            token_type="access"
        )
        new_refresh_token = create_token(
            data={"user_id": str(user.id)},
            token_type="refresh"
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    async def get_user_profile(self, user_id: str) -> User:
        """사용자 프로필 조회"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("사용자를 찾을 수 없습니다")
        return user
    
    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> User:
        """사용자 프로필 수정"""
        # 기존 사용자 존재 확인
        existing_user = await self.user_repository.get_by_id(user_id)
        if not existing_user:
            raise UserNotFoundError("사용자를 찾을 수 없습니다")
        
        # 사용자 핸들 중복 확인 (변경하는 경우)
        if (update_data.user_handle and 
            update_data.user_handle != existing_user.user_handle):
            if await self.user_repository.user_handle_exists(update_data.user_handle):
                raise UserHandleAlreadyExistsError("이미 사용 중인 사용자 핸들입니다")
        
        # 프로필 업데이트
        updated_user = await self.user_repository.update(user_id, update_data)
        return updated_user
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """비밀번호 변경"""
        # 사용자 조회
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("사용자를 찾을 수 없습니다")
        
        # 현재 비밀번호 검증
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError("현재 비밀번호가 올바르지 않습니다")
        
        # 새 비밀번호 해싱 및 업데이트
        new_password_hash = hash_password(new_password)
        update_data = UserUpdate(password_hash=new_password_hash)
        await self.user_repository.update(user_id, update_data)
        
        return True
    
    async def deactivate_account(self, user_id: str, password: str) -> bool:
        """계정 비활성화"""
        # 사용자 조회 및 비밀번호 검증
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("사용자를 찾을 수 없습니다")
        
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("비밀번호가 올바르지 않습니다")
        
        # 계정 비활성화
        update_data = UserUpdate(is_active=False)
        await self.user_repository.update(user_id, update_data)
        
        return True
```

### 2.2 관리자 기능 서비스
```python
# 관리자 전용 기능들 (AuthService 내에 포함)
async def get_users_list(self, page: int = 1, limit: int = 20, 
                        is_active: Optional[bool] = None) -> Dict[str, Any]:
    """사용자 목록 조회 (관리자 전용)"""
    return await self.user_repository.get_users_paginated(
        page=page, limit=limit, is_active=is_active
    )

async def suspend_user(self, admin_id: str, user_id: str, reason: str) -> bool:
    """사용자 정지 (관리자 전용)"""
    # 관리자 권한 확인
    admin = await self.user_repository.get_by_id(admin_id)
    if not admin or admin.role != UserRole.ADMIN:
        raise PermissionError("관리자 권한이 필요합니다")
    
    # 사용자 정지
    update_data = UserUpdate(is_active=False)
    await self.user_repository.update(user_id, update_data)
    
    return True

async def activate_user(self, admin_id: str, user_id: str) -> bool:
    """사용자 활성화 (관리자 전용)"""
    # 관리자 권한 확인 등 동일한 패턴
    pass

async def delete_user(self, admin_id: str, user_id: str) -> bool:
    """사용자 삭제 (관리자 전용)"""
    # 관리자 권한 확인 등 동일한 패턴
    pass
```

## 3. 게시글 서비스 (PostsService)

### 3.1 실제 구현된 게시글 서비스
```python
# nadle_backend/services/posts_service.py
from typing import Optional, List, Dict, Any
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.models.core import Post, PostCreate, PostUpdate
from nadle_backend.exceptions.post import PostNotFoundError, SlugAlreadyExistsError
from nadle_backend.utils.permissions import check_post_permission
import uuid

class PostsService:
    """Posts service for handling post operations."""
    
    def __init__(self):
        self.post_repository = PostRepository()
    
    async def create_post(self, post_data: PostCreate, author_id: str) -> Post:
        """게시글 생성"""
        # 1. slug 생성 (ID 기반)
        slug = str(uuid.uuid4())
        
        # 2. 게시글 생성
        post = await self.post_repository.create(post_data, author_id, slug)
        return post
    
    async def get_post_by_slug(self, slug: str, user_id: Optional[str] = None) -> Post:
        """게시글 상세 조회"""
        post = await self.post_repository.get_by_slug(slug)
        if not post:
            raise PostNotFoundError(f"게시글을 찾을 수 없습니다: {slug}")
        
        # 조회수 증가 (비동기로 처리)
        # await self._increment_view_count(post.id)
        
        return post
    
    async def update_post(self, slug: str, update_data: PostUpdate, user_id: str) -> Post:
        """게시글 수정"""
        # 1. 기존 게시글 조회
        existing_post = await self.post_repository.get_by_slug(slug)
        if not existing_post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        # 2. 권한 확인
        if not check_post_permission(existing_post, user_id):
            raise PermissionError("게시글을 수정할 권한이 없습니다")
        
        # 3. 게시글 업데이트
        updated_post = await self.post_repository.update(existing_post.id, update_data)
        return updated_post
    
    async def delete_post(self, slug: str, user_id: str) -> bool:
        """게시글 삭제"""
        # 게시글 조회 및 권한 확인
        existing_post = await self.post_repository.get_by_slug(slug)
        if not existing_post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        if not check_post_permission(existing_post, user_id):
            raise PermissionError("게시글을 삭제할 권한이 없습니다")
        
        # 관련 데이터 정리 (댓글, 좋아요 등)
        await self._cleanup_post_data(existing_post.id)
        
        # 게시글 삭제
        return await self.post_repository.delete(existing_post.id)
    
    async def get_posts_list(self, page: int = 1, limit: int = 20, 
                           service_filter: Optional[str] = None) -> Dict[str, Any]:
        """게시글 목록 조회"""
        return await self.post_repository.get_posts_list(
            page=page, limit=limit, service_filter=service_filter
        )
    
    async def search_posts(self, search_term: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """게시글 검색"""
        return await self.post_repository.search_posts(
            search_term=search_term, page=page, limit=limit
        )
    
    async def like_post(self, slug: str, user_id: str) -> Dict[str, Any]:
        """게시글 좋아요 토글"""
        post = await self.post_repository.get_by_slug(slug)
        if not post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        # 좋아요 토글 로직 (UserReaction 모델 사용)
        result = await self._toggle_reaction(post.id, user_id, "like")
        return result
    
    async def dislike_post(self, slug: str, user_id: str) -> Dict[str, Any]:
        """게시글 싫어요 토글"""
        # 좋아요와 동일한 패턴
        pass
    
    async def bookmark_post(self, slug: str, user_id: str) -> Dict[str, Any]:
        """게시글 북마크 토글"""
        # 좋아요와 동일한 패턴
        pass
    
    async def get_post_stats(self, slug: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """게시글 통계 조회"""
        post = await self.post_repository.get_by_slug(slug)
        if not post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        # PostStats 모델에서 통계 조회
        stats = await self._get_post_statistics(post.id)
        
        # 사용자별 반응 정보 추가
        if user_id:
            user_reaction = await self._get_user_reaction(post.id, user_id)
            stats["user_reaction"] = user_reaction
        
        return stats
    
    async def _cleanup_post_data(self, post_id: str):
        """게시글 삭제 시 관련 데이터 정리"""
        # 댓글, 좋아요, 조회수 등 관련 데이터 정리
        pass
    
    async def _toggle_reaction(self, post_id: str, user_id: str, reaction_type: str) -> Dict[str, Any]:
        """반응 토글 공통 로직"""
        # UserReaction 모델을 사용한 반응 처리
        pass
```

## 4. 댓글 서비스 (CommentsService)

### 4.1 실제 구현된 댓글 서비스
```python
# nadle_backend/services/comments_service.py
from typing import Optional, List, Dict, Any
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.models.core import Comment, CommentCreate, CommentUpdate
from nadle_backend.exceptions.comment import CommentNotFoundError
from nadle_backend.exceptions.post import PostNotFoundError
from nadle_backend.utils.permissions import check_comment_permission

class CommentsService:
    """Comments service for handling comment operations."""
    
    def __init__(self):
        self.comment_repository = CommentRepository()
        self.post_repository = PostRepository()
    
    async def create_comment(self, post_slug: str, comment_data: CommentCreate, 
                           author_id: str) -> Comment:
        """댓글 생성"""
        # 1. 게시글 존재 확인
        post = await self.post_repository.get_by_slug(post_slug)
        if not post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        # 2. 댓글 생성
        comment = await self.comment_repository.create(comment_data, author_id, post_slug)
        
        # 3. 게시글 댓글 수 증가
        # await self._increment_comment_count(post.id)
        
        return comment
    
    async def create_reply(self, post_slug: str, parent_id: str, 
                         reply_data: CommentCreate, author_id: str) -> Comment:
        """대댓글 생성"""
        # 1. 게시글 존재 확인
        post = await self.post_repository.get_by_slug(post_slug)
        if not post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        # 2. 부모 댓글 존재 확인
        parent_comment = await self.comment_repository.get_by_id(parent_id)
        if not parent_comment:
            raise CommentNotFoundError("부모 댓글을 찾을 수 없습니다")
        
        # 3. 댓글 계층 제한 확인 (2단계만 허용)
        if parent_comment.parent_id:
            raise ValueError("대댓글에는 답글을 달 수 없습니다")
        
        # 4. 대댓글 생성
        reply_data.parent_id = parent_id
        reply = await self.comment_repository.create(reply_data, author_id, post_slug)
        
        return reply
    
    async def get_comments_by_post(self, post_slug: str, page: int = 1, 
                                 limit: int = 50) -> Dict[str, Any]:
        """게시글별 댓글 목록 조회"""
        # 게시글 존재 확인
        post = await self.post_repository.get_by_slug(post_slug)
        if not post:
            raise PostNotFoundError("게시글을 찾을 수 없습니다")
        
        # 댓글 목록 조회
        return await self.comment_repository.get_by_post(post_slug, page, limit)
    
    async def update_comment(self, comment_id: str, update_data: CommentUpdate, 
                           user_id: str) -> Comment:
        """댓글 수정"""
        # 1. 기존 댓글 조회
        existing_comment = await self.comment_repository.get_by_id(comment_id)
        if not existing_comment:
            raise CommentNotFoundError("댓글을 찾을 수 없습니다")
        
        # 2. 권한 확인
        if not check_comment_permission(existing_comment, user_id):
            raise PermissionError("댓글을 수정할 권한이 없습니다")
        
        # 3. 댓글 업데이트
        updated_comment = await self.comment_repository.update(comment_id, update_data)
        return updated_comment
    
    async def delete_comment(self, comment_id: str, user_id: str) -> bool:
        """댓글 삭제 (소프트 삭제)"""
        # 댓글 조회 및 권한 확인
        existing_comment = await self.comment_repository.get_by_id(comment_id)
        if not existing_comment:
            raise CommentNotFoundError("댓글을 찾을 수 없습니다")
        
        if not check_comment_permission(existing_comment, user_id):
            raise PermissionError("댓글을 삭제할 권한이 없습니다")
        
        # 대댓글 존재 여부에 따른 삭제 방식 결정
        replies = await self.comment_repository.get_replies(comment_id)
        
        if replies:
            # 대댓글이 있으면 소프트 삭제 (내용만 변경)
            soft_delete_data = CommentUpdate(
                content="삭제된 댓글입니다",
                status=CommentStatus.DELETED
            )
            await self.comment_repository.update(comment_id, soft_delete_data)
        else:
            # 대댓글이 없으면 완전 삭제
            await self.comment_repository.delete(comment_id)
        
        return True
    
    async def like_comment(self, comment_id: str, user_id: str) -> Dict[str, Any]:
        """댓글 좋아요 토글"""
        comment = await self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("댓글을 찾을 수 없습니다")
        
        # 댓글 좋아요 토글 로직
        result = await self._toggle_comment_reaction(comment_id, user_id, "like")
        return result
    
    async def dislike_comment(self, comment_id: str, user_id: str) -> Dict[str, Any]:
        """댓글 싫어요 토글"""
        # 댓글 좋아요와 동일한 패턴
        pass
    
    async def _toggle_comment_reaction(self, comment_id: str, user_id: str, 
                                     reaction_type: str) -> Dict[str, Any]:
        """댓글 반응 토글 공통 로직"""
        # Comment에 대한 UserReaction 처리
        pass
```

## 5. 콘텐츠 서비스 (ContentService)

### 5.1 실제 구현된 콘텐츠 서비스
```python
# nadle_backend/services/content_service.py
from typing import Dict, Any
from nadle_backend.models.content import ContentPreviewRequest, ContentPreviewResponse
import re
import html
from bs4 import BeautifulSoup

class ContentService:
    """Content processing service for rich text editor."""
    
    def __init__(self):
        self.allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 's', 'a', 'ul', 'ol', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
        ]
        self.allowed_attributes = {
            'a': ['href', 'title'],
            'blockquote': ['cite']
        }
    
    async def preview_content(self, request: ContentPreviewRequest) -> ContentPreviewResponse:
        """콘텐츠 미리보기 처리"""
        content = request.content
        
        # 1. HTML 살균 및 정리
        sanitized_content = self._sanitize_html(content)
        
        # 2. 콘텐츠 분석
        analysis = self._analyze_content(sanitized_content)
        
        return ContentPreviewResponse(
            processed_content=sanitized_content,
            word_count=analysis['word_count'],
            estimated_read_time=analysis['read_time'],
            has_images=analysis['has_images'],
            has_links=analysis['has_links']
        )
    
    def _sanitize_html(self, content: str) -> str:
        """백리스트 기반 HTML 살균"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # 허용되지 않는 태그 제거
        for tag in soup.find_all():
            if tag.name not in self.allowed_tags:
                tag.decompose()
            else:
                # 허용되지 않는 속성 제거
                allowed_attrs = self.allowed_attributes.get(tag.name, [])
                attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attrs]
                for attr in attrs_to_remove:
                    del tag[attr]
        
        return str(soup)
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """콘텐츠 분석"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # 텍스트 추출
        text = soup.get_text()
        word_count = len(text.replace(' ', ''))
        
        # 읽기 시간 추정 (한글 기준: 분당 500자)
        read_time = max(1, word_count // 500)
        
        # 이미지 및 링크 존재 여부
        has_images = bool(soup.find('img'))
        has_links = bool(soup.find('a'))
        
        return {
            'word_count': word_count,
            'read_time': read_time,
            'has_images': has_images,
            'has_links': has_links
        }
    
    async def get_test_status(self) -> Dict[str, Any]:
        """콘텐츠 처리 시스템 상태 확인"""
        return {
            "status": "ok",
            "processor_version": "1.0.0",
            "supported_formats": ["html", "markdown"]
        }
```

## 6. 파일 서비스 (File Services)

### 6.1 파일 관리 서비스 계층
파일 관리는 3개의 전문 서비스로 구성:

```python
# nadle_backend/services/file_validator.py - 파일 검증 서비스
class FileValidationService:
    """File validation and security service."""
    
    def __init__(self):
        self.allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.dangerous_types = ['application/x-executable', 'text/x-shellscript']
    
    async def validate_file(self, file) -> bool:
        """파일 유효성 검증"""
        # 파일 크기 검증
        if file.size > self.max_file_size:
            raise ValueError(f"파일 크기가 초과되었습니다. 최대: {self.max_file_size//1024//1024}MB")
        
        # 파일 확장자 검증
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise ValueError(f"지원되지 않는 파일 형식입니다: {file_ext}")
        
        # MIME 타입 검증
        if file.content_type in self.dangerous_types:
            raise ValueError("위험한 파일 타입입니다")
        
        return True

# nadle_backend/services/file_storage.py - 파일 저장 서비스
class FileStorageService:
    """File storage management service."""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def store_file(self, file, file_id: str) -> str:
        """파일 저장"""
        # 날짜별 디렉토리 생성
        today = datetime.now()
        date_path = self.upload_dir / str(today.year) / f"{today.month:02d}"
        date_path.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_ext}"
        file_path = date_path / filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return str(file_path)

# nadle_backend/services/file_metadata.py - 메타데이터 서비스
class FileMetadataService:
    """File metadata extraction service."""
    
    async def extract_metadata(self, file_path: str, content_type: str) -> Dict[str, Any]:
        """파일 메타데이터 추출"""
        metadata = {}
        
        # 이미지 메타데이터 추출
        if content_type.startswith('image/'):
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    metadata['width'] = img.width
                    metadata['height'] = img.height
                    metadata['format'] = img.format
            except Exception:
                pass
        
        return metadata
```

## 7. 공통 유틸리티 (Utils)

### 7.1 JWT 처리 유틸리티
```python
# nadle_backend/utils/jwt.py
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from nadle_backend.config import settings

def create_token(data: Dict[str, Any], token_type: str = "access") -> str:
    """토큰 생성"""
    to_encode = data.copy()
    
    # 만료 시간 설정
    if token_type == "access":
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    else:  # refresh
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": token_type
    })
    
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """토큰 검증"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.PyJWTError:
        return None
```

### 7.2 비밀번호 처리 유틸리티
```python
# nadle_backend/utils/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 7.3 권한 검증 유틸리티
```python
# nadle_backend/utils/permissions.py
from nadle_backend.models.core import User, Post, Comment, UserRole

def check_post_permission(post: Post, user_id: str) -> bool:
    """게시글 수정/삭제 권한 확인"""
    return post.author_id == user_id

def check_comment_permission(comment: Comment, user_id: str) -> bool:
    """댓글 수정/삭제 권한 확인"""
    return comment.author_id == user_id

def check_admin_permission(user: User) -> bool:
    """관리자 권한 확인"""
    return user.role == UserRole.ADMIN
```

## 8. 실제 import 경로와 사용법

### 8.1 Router에서 서비스 사용
```python
# nadle_backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from nadle_backend.services.auth_service import AuthService
from nadle_backend.models.core import UserCreate, UserLogin, UserResponse
from nadle_backend.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Signup new user"""
    auth_service = AuthService()
    user = await auth_service.register_user(user_data)
    return UserResponse(**user.model_dump())

@router.post("/login")
async def login(login_data: UserLogin):
    """User login"""
    auth_service = AuthService()
    return await auth_service.authenticate_user(login_data.email, login_data.password)

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    auth_service = AuthService()
    return await auth_service.refresh_token(refresh_token)
```

### 8.2 의존성 주입 패턴
```python
# nadle_backend/dependencies/services.py
from nadle_backend.services.auth_service import AuthService
from nadle_backend.services.posts_service import PostsService
from nadle_backend.services.comments_service import CommentsService
from nadle_backend.services.content_service import ContentService

def get_auth_service() -> AuthService:
    return AuthService()

def get_posts_service() -> PostsService:
    return PostsService()

def get_comments_service() -> CommentsService:
    return CommentsService()

def get_content_service() -> ContentService:
    return ContentService()
```

## 9. 실제 구현 특징 요약

### ✅ 구현 완료된 서비스
1. **AuthService**: 전체 인증 사이클 + 관리자 기능
2. **PostsService**: CRUD + 검색 + 반응 시스템
3. **CommentsService**: 계층형 댓글 + 반응
4. **ContentService**: 리치 텍스트 에디터 처리
5. **File Services**: 전문 파일 처리 (validator, storage, metadata)

### 🔧 아키텍처 특징
1. **단순한 의존성**: BaseService 추상화 없이 직접 구현
2. **Beanie 통합**: Repository와 ODM의 완벽한 연동
3. **비즈니스 로직 중심**: 복잡한 비즈니스 규칙 처리
4. **에러 처리**: 도메인별 커스텀 예외 활용
5. **매개변수 간소화**: 의존성 주입 패턴 적용

이 서비스 계층은 **실제 구현된 비즈니스 로직**의 정확한 반영이며, 현재 프로젝트의 요구사항과 규모에 완벽하게 부합합니다.