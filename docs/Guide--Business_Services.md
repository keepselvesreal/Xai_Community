# 비즈니스 서비스 가이드 (Business Services Guide)

## 📋 목차

### 1. 서비스 계층 개요 (Service Layer Overview)
- **비즈니스 로직 중앙화**: Repository와 API 사이의 로직 계층
- **트랜잭션 관리**: 복잡한 비즈니스 규칙과 데이터 일관성

### 2. 인증 서비스 (Auth Service)
- **사용자 관리**: 회원가입, 로그인, 프로필 관리
- **보안 처리**: 패스워드 해싱, JWT 토큰 생성

### 3. 게시글 서비스 (Post Service)
- **CRUD 관리**: 게시글 생성, 수정, 삭제, 조회
- **고급 기능**: slug 생성, 검색, 필터링

### 4. 댓글 서비스 (Comment Service)
- **계층 관리**: 댓글과 대댓글의 계층 구조
- **상태 관리**: 활성/삭제 상태 처리

### 5. 통계 서비스 (Stats Service)
- **실시간 업데이트**: 조회수, 좋아요, 댓글 수 관리
- **사용자 반응**: 좋아요/싫어요/북마크 토글

### 6. 공통 유틸리티 (Common Utilities)
- **slug 생성**: SEO 친화적 URL 생성
- **검증 로직**: 비즈니스 규칙 검증
- **에러 처리**: 비즈니스 예외 관리

## 📊 항목 간 관계

```
API Router (요청/응답)
    ↓
Service Layer (비즈니스 로직)
    ↓
Repository Layer (데이터 접근)
    ↓
Database (데이터 저장)
```

- **API Router**에서 Service 호출
- **Service**에서 Repository와 Utils 활용
- **Repository**가 실제 데이터 처리
- **Service간 협력**으로 복잡한 비즈니스 로직 구현

## 📝 각 항목 핵심 설명

### 서비스 계층 개요
비즈니스 로직을 캡슐화하여 API와 데이터 계층 사이의 중재자 역할

### 인증 서비스
사용자 생명주기 관리와 보안 관련 모든 비즈니스 로직 처리

### 게시글 서비스
콘텐츠 관리의 핵심 비즈니스 로직과 복잡한 쿼리 처리

### 댓글 서비스
계층적 댓글 시스템의 복잡한 관계와 상태 관리

### 통계 서비스
실시간 통계 업데이트와 사용자 상호작용 처리

### 공통 유틸리티
모든 서비스에서 재사용 가능한 비즈니스 로직과 헬퍼 함수

---

# 📖 본문

## 1. 서비스 계층 기본 구조

### 1.1 기본 서비스 클래스
```python
# services/base_service.py
from abc import ABC
import logging
from typing import Any, Dict

"""
현재 프로젝트는 BaseService 추상화 없이 각 Service가 독립적으로 구현됩니다.
Beanie ODM과 함께 사용하여 복잡한 추상화 계층 없이 단순하고 명확한 구조를 유지합니다.
"""
```

## 2. 인증 서비스 (AuthService)

### 2.1 사용자 관리 서비스
```python
# services/auth_service.py
from typing import Optional
from fastapi import HTTPException, status
from models.user import User, UserCreate, UserLogin, UserUpdate, Token
from repositories.user_repository import UserRepository
from utils.password import PasswordHandler
from utils.jwt import JWTHandler
from services.base_service import BaseService
import uuid

class AuthService:
    """Authentication service for handling user authentication and management."""
    
    def __init__(
        self, 
        user_repository: UserRepository = None,
        jwt_manager: JWTManager = None,
        password_manager: PasswordManager = None
    ):
        """Initialize auth service with dependencies."""
        self.user_repository = user_repository or UserRepository()
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager or PasswordManager()
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user."""
        # 1. 중복 검증
        if await self.user_repository.email_exists(user_data.email):
            raise EmailAlreadyExistsError("이미 등록된 이메일입니다")
            
        if await self.user_repository.user_handle_exists(user_data.user_handle):
            raise HandleAlreadyExistsError("이미 사용 중인 사용자 핸들입니다")
        
        # 2. 비밀번호 해싱
        password_hash = self.password_manager.hash_password(user_data.password)
        
        # 3. 사용자 생성
        user = await self.user_repository.create(user_data, password_hash)
        
        return user
    
    async def authenticate_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Authenticate user and return token."""
        # 1. 사용자 조회
        user = await self.user_repository.get_by_email(login_data.email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # 2. 비밀번호 검증
        if not self.password_manager.verify_password(login_data.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # 3. 계정 상태 확인
        if user.status != "active":
            raise UserNotActiveError("Account is not active")
        
        # 4. 토큰 생성
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "user_handle": user.user_handle
        }
        
        access_token = self.jwt_manager.create_token(
            data=token_data,
            token_type=TokenType.ACCESS
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def verify_access_token(self, token: str) -> Dict[str, Any]:
        """액세스 토큰 검증 (type 필드 포함)"""
        payload = self.jwt_handler.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다"
            )
        
        # type 필드 검증 추가
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 토큰 타입입니다"
            )
        
        return payload
    
    async def get_user_profile(self, user_id: str) -> User:
        """사용자 프로필 조회"""
        user_repo = await self.get_user_repository()
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        return user
    
    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> User:
        """사용자 프로필 수정"""
        self.log_operation("user_profile_update", {"user_id": user_id})
        
        user_repo = await self.get_user_repository()
        
        # 기존 사용자 존재 확인
        existing_user = await user_repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 프로필 업데이트
        updated_user = await user_repo.update(user_id, update_data.dict(exclude_unset=True))
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="프로필 업데이트에 실패했습니다"
            )
        
        return updated_user
    
    async def _validate_user_uniqueness(self, user_data: UserCreate):
        """사용자 중복성 검증"""
        user_repo = await self.get_user_repository()
        
        # 이메일 중복 확인
        if await user_repo.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 등록된 이메일입니다"
            )
        
        # 사용자 핸들 중복 확인
        if await user_repo.user_handle_exists(user_data.user_handle):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 사용자 핸들입니다"
            )
    
    async def _validate_user_status(self, user: User):
        """사용자 상태 검증"""
        if user.status != "active":
            status_messages = {
                "inactive": "비활성화된 계정입니다",
                "suspended": "정지된 계정입니다"
            }
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=status_messages.get(user.status, "사용할 수 없는 계정입니다")
            )
```

## 3. 게시글 서비스 (PostService)

### 3.1 게시글 관리 서비스
```python
# services/post_service.py
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from models.post import Post, PostCreate, PostUpdate, PostListItem
from models.common import PaginationResponse
from repositories.post_repository import PostRepository
from repositories.stats_repository import StatsRepository
from utils.slug import SlugGenerator
from services.base_service import BaseService

class PostService(BaseService):
    def __init__(self, post_repo: PostRepository, stats_repo: StatsRepository):
        super().__init__()
        self.post_repo = post_repo
        self.stats_repo = stats_repo
        self.slug_generator = SlugGenerator()
    
    async def create_post(self, post_data: PostCreate, author_id: str) -> Post:
        """게시글 생성"""
        self.log_operation("post_creation", {
            "author_id": author_id,
            "title": post_data.title[:50]
        })
        
        # 1. 비즈니스 규칙 검증
        await self._validate_post_creation(post_data, author_id)
        
        # 2. 게시글 생성 (slug는 ID 기반으로 나중에 설정)
        post = await self.post_repo.create_post(post_data, author_id)
        
        # 3. ID 기반 slug 생성 및 업데이트
        slug = self.slug_generator.generate_from_id(post.id)
        updated_post = await self.post_repo.update(post.id, {"slug": slug})
        
        # 4. 초기 통계 생성 (선택사항)
        # await self.stats_repo.create_initial_stats(post.id)
        
        self.logger.info(f"게시글 생성 완료: {updated_post.slug}")
        return updated_post
    
    async def get_post_by_slug(self, slug: str, user_id: Optional[str] = None) -> Post:
        """게시글 상세 조회"""
        # 게시글 조회
        post = await self.post_repo.get_by_slug(slug)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        # 조회수 증가 (비동기로 처리)
        await self.stats_repo.increment_view_count(post.id)
        
        # 사용자별 반응 정보 포함 (로그인한 경우)
        if user_id:
            user_reaction = await self.stats_repo.get_user_reaction(post.id, user_id)
            post.user_reaction = user_reaction
        
        return post
    
    async def update_post(self, slug: str, update_data: PostUpdate, user_id: str) -> Post:
        """게시글 수정"""
        self.log_operation("post_update", {"slug": slug, "user_id": user_id})
        
        # 1. 기존 게시글 조회 및 권한 확인
        existing_post = await self.post_repo.get_by_slug(slug)
        if not existing_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        await self._validate_post_ownership(existing_post, user_id)
        
        # 2. 업데이트 데이터 준비 (slug는 변경하지 않음)
        update_dict = update_data.dict(exclude_unset=True)
        
        # 3. 게시글 업데이트
        updated_post = await self.post_repo.update(existing_post.id, update_dict)
        if not updated_post:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게시글 수정에 실패했습니다"
            )
        
        return updated_post
    
    async def delete_post(self, slug: str, user_id: str) -> bool:
        """게시글 삭제"""
        self.log_operation("post_deletion", {"slug": slug, "user_id": user_id})
        
        # 1. 게시글 조회 및 권한 확인
        existing_post = await self.post_repo.get_by_slug(slug)
        if not existing_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        await self._validate_post_ownership(existing_post, user_id)
        
        # 2. 관련 데이터 정리 (댓글, 통계 등)
        await self._cleanup_post_related_data(existing_post.id)
        
        # 3. 게시글 삭제
        deleted = await self.post_repo.delete(existing_post.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게시글 삭제에 실패했습니다"
            )
        
        return True
    
    async def get_posts_list(
        self,
        page: int = 1,
        limit: int = 20,
        post_type: Optional[str] = None,
        author_handle: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginationResponse[PostListItem]:
        """게시글 목록 조회"""
        # 필터 구성
        filters = {}
        if post_type:
            filters["metadata.type"] = post_type
        if author_handle:
            # author_handle을 author_id로 변환 필요
            pass
        
        return await self.post_repo.get_posts_list(
            page=page,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def search_posts(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        post_type: Optional[str] = None
    ) -> PaginationResponse[PostListItem]:
        """게시글 검색"""
        self.log_operation("post_search", {"query": query[:50]})
        
        # 검색 필터 구성
        filters = {}
        if post_type:
            filters["metadata.type"] = post_type
        
        return await self.post_repo.search_posts(
            query=query,
            page=page,
            limit=limit,
            filters=filters
        )
    
    async def _validate_post_creation(self, post_data: PostCreate, author_id: str):
        """게시글 생성 유효성 검증"""
        # 비즈니스 규칙 검증 (예: 일일 게시글 제한 등)
        daily_posts = await self.post_repo.count_user_posts_today(author_id)
        if daily_posts >= 10:  # 일일 게시글 제한
            raise ValueError("하루 최대 10개까지 게시글을 작성할 수 있습니다")
    
    async def _validate_post_ownership(self, post: Post, user_id: str):
        """게시글 소유권 확인"""
        if post.author_id != user_id:
            # 관리자 권한 확인 로직 추가 가능
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="게시글을 수정/삭제할 권한이 없습니다"
            )
    
    async def _cleanup_post_related_data(self, post_id: str):
        """게시글 삭제 시 관련 데이터 정리"""
        # 댓글, 통계, 반응 등 관련 데이터 정리
        # 실제 구현에서는 다른 서비스들과 협력
        pass
```

## 4. 댓글 서비스 (CommentService)

### 4.1 댓글 관리 서비스
```python
# services/comment_service.py
from typing import Optional, List
from fastapi import HTTPException, status
from models.comment import Comment, CommentCreate, CommentUpdate, CommentDetail
from models.common import PaginationResponse
from repositories.comment_repository import CommentRepository
from repositories.post_repository import PostRepository
from services.base_service import BaseService

class CommentService(BaseService):
    def __init__(self, comment_repo: CommentRepository, post_repo: PostRepository):
        super().__init__()
        self.comment_repo = comment_repo
        self.post_repo = post_repo
    
    async def create_comment(
        self, 
        post_slug: str, 
        comment_data: CommentCreate, 
        author_id: str
    ) -> Comment:
        """댓글 생성"""
        self.log_operation("comment_creation", {
            "post_slug": post_slug,
            "author_id": author_id
        })
        
        # 1. 게시글 존재 확인
        post = await self.post_repo.get_by_slug(post_slug)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        # 2. 대댓글인 경우 부모 댓글 확인
        if comment_data.parent_comment_id:
            await self._validate_parent_comment(comment_data.parent_comment_id, post.id)
        
        # 3. 댓글 생성
        comment = await self.comment_repo.create_comment(
            comment_data, author_id, post.id
        )
        
        # 4. 게시글 댓글 수 증가 (통계 업데이트)
        # await self.stats_repo.increment_comment_count(post.id)
        
        self.logger.info(f"댓글 생성 완료: {comment.id}")
        return comment
    
    async def get_comments_by_post(
        self,
        post_slug: str,
        page: int = 1,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> PaginationResponse[CommentDetail]:
        """게시글별 댓글 목록 조회"""
        # 게시글 존재 확인
        post = await self.post_repo.get_by_slug(post_slug)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        # 댓글 목록 조회
        comments_response = await self.comment_repo.get_comments_by_post(
            post_id=post.id,
            page=page,
            limit=limit,
            include_replies=True
        )
        
        # 사용자별 반응 정보 포함 (로그인한 경우)
        if user_id:
            for comment in comments_response.items:
                # 댓글별 사용자 반응 조회 로직 추가
                pass
        
        return comments_response
    
    async def update_comment(
        self, 
        comment_id: str, 
        update_data: CommentUpdate, 
        user_id: str
    ) -> Comment:
        """댓글 수정"""
        self.log_operation("comment_update", {
            "comment_id": comment_id,
            "user_id": user_id
        })
        
        # 1. 기존 댓글 조회 및 권한 확인
        existing_comment = await self.comment_repo.get_by_id(comment_id)
        if not existing_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="댓글을 찾을 수 없습니다"
            )
        
        await self._validate_comment_ownership(existing_comment, user_id)
        
        # 2. 댓글 업데이트
        updated_comment = await self.comment_repo.update(
            comment_id, 
            update_data.dict(exclude_unset=True)
        )
        
        if not updated_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="댓글 수정에 실패했습니다"
            )
        
        return updated_comment
    
    async def delete_comment(self, comment_id: str, user_id: str) -> bool:
        """댓글 삭제 (소프트 삭제)"""
        self.log_operation("comment_deletion", {
            "comment_id": comment_id,
            "user_id": user_id
        })
        
        # 1. 댓글 조회 및 권한 확인
        existing_comment = await self.comment_repo.get_by_id(comment_id)
        if not existing_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="댓글을 찾을 수 없습니다"
            )
        
        await self._validate_comment_ownership(existing_comment, user_id)
        
        # 2. 대댓글이 있는 경우 처리 로직
        await self._handle_comment_deletion_with_replies(comment_id)
        
        # 3. 소프트 삭제 실행
        deleted = await self.comment_repo.soft_delete_comment(comment_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="댓글 삭제에 실패했습니다"
            )
        
        # 4. 게시글 댓글 수 감소
        # await self.stats_repo.decrement_comment_count(existing_comment.parent_id)
        
        return True
    
    async def _validate_parent_comment(self, parent_comment_id: str, post_id: str):
        """부모 댓글 유효성 검증"""
        parent_comment = await self.comment_repo.get_by_id(parent_comment_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="부모 댓글을 찾을 수 없습니다"
            )
        
        # 같은 게시글의 댓글인지 확인
        if parent_comment.parent_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="다른 게시글의 댓글에는 답글을 달 수 없습니다"
            )
        
        # 이미 대댓글인 경우 더 이상 대댓글 금지 (2단계 제한)
        if parent_comment.parent_comment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대댓글에는 더 이상 답글을 달 수 없습니다"
            )
    
    async def _validate_comment_ownership(self, comment: Comment, user_id: str):
        """댓글 소유권 확인"""
        if comment.author_id != user_id:
            # 관리자 권한 확인 로직 추가 가능
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="댓글을 수정/삭제할 권한이 없습니다"
            )
    
    async def _handle_comment_deletion_with_replies(self, comment_id: str):
        """대댓글이 있는 댓글 삭제 처리"""
        # 대댓글이 있는 경우의 처리 로직
        # 예: 대댓글이 있으면 내용만 "삭제된 댓글입니다"로 변경
        pass
```

## 5. 통계 서비스 (StatsService)

### 5.1 통계 및 반응 관리 서비스
```python
# services/stats_service.py
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from models.stats import PostStats, UserReaction
from repositories.stats_repository import StatsRepository
from repositories.post_repository import PostRepository
from services.base_service import BaseService

class StatsService(BaseService):
    def __init__(self, stats_repo: StatsRepository, post_repo: PostRepository):
        super().__init__()
        self.stats_repo = stats_repo
        self.post_repo = post_repo
    
    async def get_post_stats(
        self, 
        post_slug: str, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """게시글 통계 조회"""
        # 게시글 존재 확인
        post = await self.post_repo.get_by_slug(post_slug)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        # 통계 정보 조회
        stats = await self.stats_repo.get_post_stats(post.id)
        if not stats:
            # 통계가 없으면 기본값 생성
            stats = PostStats(
                postId=post.id,
                viewCount=0,
                likeCount=0,
                dislikeCount=0,
                commentCount=0,
                bookmarkCount=0
            )
        
        response = {
            "viewCount": stats.viewCount,
            "likeCount": stats.likeCount,
            "dislikeCount": stats.dislikeCount,
            "commentCount": stats.commentCount,
            "bookmarkCount": stats.bookmarkCount
        }
        
        # 사용자별 반응 정보 추가 (로그인한 경우)
        if user_id:
            user_reaction = await self.stats_repo.get_user_reaction(post.id, user_id)
            if user_reaction:
                response["userReaction"] = {
                    "liked": user_reaction.liked,
                    "disliked": user_reaction.disliked,
                    "bookmarked": user_reaction.bookmarked
                }
        
        return response
    
    async def toggle_like(self, post_slug: str, user_id: str) -> Dict[str, Any]:
        """좋아요 토글"""
        return await self._toggle_reaction(post_slug, user_id, "like")
    
    async def toggle_dislike(self, post_slug: str, user_id: str) -> Dict[str, Any]:
        """싫어요 토글"""
        return await self._toggle_reaction(post_slug, user_id, "dislike")
    
    async def toggle_bookmark(self, post_slug: str, user_id: str) -> Dict[str, Any]:
        """북마크 토글"""
        return await self._toggle_reaction(post_slug, user_id, "bookmark")
    
    async def _toggle_reaction(
        self, 
        post_slug: str, 
        user_id: str, 
        reaction_type: str
    ) -> Dict[str, Any]:
        """반응 토글 공통 로직"""
        self.log_operation(f"toggle_{reaction_type}", {
            "post_slug": post_slug,
            "user_id": user_id
        })
        
        # 게시글 존재 확인
        post = await self.post_repo.get_by_slug(post_slug)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )
        
        # 반응 토글 실행
        result = await self.stats_repo.toggle_user_reaction(
            user_id, post.id, reaction_type
        )
        
        # 업데이트된 통계 조회
        updated_stats = await self.stats_repo.get_post_stats(post.id)
        
        return {
            "action": result["action"],
            f"{reaction_type}Count": getattr(updated_stats, f"{reaction_type}Count", 0),
            "userReaction": {
                "liked": result["userReaction"].liked if result["userReaction"] else False,
                "disliked": result["userReaction"].disliked if result["userReaction"] else False,
                "bookmarked": result["userReaction"].bookmarked if result["userReaction"] else False
            }
        }
    
    async def increment_view_count(self, post_id: str) -> bool:
        """조회수 증가"""
        return await self.stats_repo.increment_view_count(post_id)
```

## 6. 공통 유틸리티

### 6.1 Slug 생성기 (ID 기반)
```python
# utils/slug.py
from typing import Optional
from datetime import datetime
import uuid

class SlugGenerator:
    """ID 기반 slug 생성기 (한국 서비스 표준)"""
    
    def generate_from_id(self, post_id: str) -> str:
        """ID 기반 slug 생성"""
        return str(post_id)
    
    def generate_with_date(self, post_id: str, created_at: datetime) -> str:
        """날짜 + ID 형식 slug 생성"""
        date_str = created_at.strftime("%Y/%m/%d")
        return f"{date_str}/{post_id}"
    
    def generate_simple_slug(self, post_id: str) -> str:
        """단순 ID slug (가장 일반적)"""
        return str(post_id)
```

### 6.2 비즈니스 검증기
```python
# utils/validators.py
from typing import Any, Dict, List
from fastapi import HTTPException, status

class BusinessValidator:
    """비즈니스 규칙 검증기"""
    
    @staticmethod
    def validate_content_length(content: str, min_length: int = 1, max_length: int = 10000):
        """콘텐츠 길이 검증"""
        content_length = len(content.strip())
        if content_length < min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"내용은 최소 {min_length}자 이상이어야 합니다"
            )
        if content_length > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"내용은 최대 {max_length}자까지 입력 가능합니다"
            )
    
    @staticmethod
    def validate_tags(tags: List[str], max_count: int = 3, max_length: int = 10):
        """태그 검증"""
        if len(tags) > max_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"태그는 최대 {max_count}개까지 입력 가능합니다"
            )
        
        for tag in tags:
            if len(tag.strip()) > max_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"각 태그는 최대 {max_length}자까지 입력 가능합니다"
                )
    
    @staticmethod
    def validate_file_extensions(file_urls: List[str], allowed_extensions: List[str]):
        """파일 확장자 검증"""
        for url in file_urls:
            if not any(url.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"지원되지 않는 파일 형식입니다. 허용 형식: {', '.join(allowed_extensions)}"
                )
```

## 7. 서비스 의존성 주입

### 7.1 서비스 제공자
```python
# dependencies/services.py
from fastapi import Depends
from repositories.user_repository import UserRepository
from repositories.post_repository import PostRepository
from repositories.comment_repository import CommentRepository
from repositories.stats_repository import StatsRepository
from services.auth_service import AuthService
from services.post_service import PostService
from services.comment_service import CommentService
from services.stats_service import StatsService
from dependencies.repositories import (
    get_user_repository,
    get_post_repository,
    get_comment_repository,
    get_stats_repository
)

# 서비스 인스턴스 캐싱
_auth_service = None
_post_service = None
_comment_service = None
_stats_service = None

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(user_repo)
    return _auth_service

async def get_post_service(
    post_repo: PostRepository = Depends(get_post_repository),
    stats_repo: StatsRepository = Depends(get_stats_repository)
) -> PostService:
    global _post_service
    if _post_service is None:
        _post_service = PostService(post_repo, stats_repo)
    return _post_service

async def get_comment_service(
    comment_repo: CommentRepository = Depends(get_comment_repository),
    post_repo: PostRepository = Depends(get_post_repository)
) -> CommentService:
    global _comment_service
    if _comment_service is None:
        _comment_service = CommentService(comment_repo, post_repo)
    return _comment_service

async def get_stats_service(
    stats_repo: StatsRepository = Depends(get_stats_repository),
    post_repo: PostRepository = Depends(get_post_repository)
) -> StatsService:
    global _stats_service
    if _stats_service is None:
        _stats_service = StatsService(stats_repo, post_repo)
    return _stats_service
```

## 8. 서비스 사용 예시

### 8.1 Router에서 서비스 사용
```python
# routers/posts.py
from fastapi import APIRouter, Depends, Query
from services.post_service import PostService
from services.stats_service import StatsService
from dependencies.services import get_post_service, get_stats_service
from dependencies.auth import get_current_user, get_current_user_optional
from models.user import User
from models.post import PostCreate, PostUpdate

router = APIRouter(prefix="/posts", tags=["게시글"])

@router.post("/")
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service)
):
    """게시글 생성"""
    return await post_service.create_post(post_data, current_user.id)

@router.get("/{slug}")
async def get_post_detail(
    slug: str,
    current_user: User = Depends(get_current_user_optional),
    post_service: PostService = Depends(get_post_service)
):
    """게시글 상세 조회"""
    user_id = current_user.id if current_user else None
    return await post_service.get_post_by_slug(slug, user_id)

@router.post("/{slug}/like")
async def toggle_like_post(
    slug: str,
    current_user: User = Depends(get_current_user),
    stats_service: StatsService = Depends(get_stats_service)
):
    """게시글 좋아요 토글"""
    return await stats_service.toggle_like(slug, current_user.id)
```