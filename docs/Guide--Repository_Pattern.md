# Repository 패턴 가이드 (Repository Pattern Guide)

## 📋 목차

### 1. Repository 패턴 개요 (Pattern Overview)
- **추상화 계층**: 데이터 접근 로직의 비즈니스 로직 분리
- **테스트 용이성**: Mock을 통한 단위 테스트 지원

### 2. 기본 Repository 구조 (Base Repository)
- **공통 인터페이스**: 모든 Repository의 기본 CRUD 연산
- **제네릭 타입**: 타입 안전성 보장

### 3. 콘텐츠 관리 Repository들 (Content Repositories)
- **UserRepository**: 사용자 관리 및 인증
- **PostRepository**: 게시글 CRUD 및 검색
- **CommentRepository**: 댓글 계층 구조 관리

### 4. 고급 쿼리 패턴 (Advanced Query Patterns)
- **페이지네이션**: 효율적인 대용량 데이터 처리
- **검색 및 필터링**: MongoDB 텍스트 검색 활용
- **집계 쿼리**: 통계 데이터 생성

### 5. 성능 최적화 (Performance Optimization)
- **인덱스 활용**: 쿼리 성능 향상
- **배치 처리**: 대량 데이터 처리
- **캐싱 전략**: 반복 쿼리 최적화

### 6. 에러 처리 및 트랜잭션 (Error Handling & Transactions)
- **예외 변환**: MongoDB 예외를 비즈니스 예외로 변환
- **트랜잭션 관리**: 데이터 일관성 보장

## 📊 항목 간 관계

```
BaseRepository (추상 클래스)
    ↓
구체적 Repository들 (User, Post, Comment)
    ↓
MongoDB 컬렉션 (users, posts, comments)
    ↓
실제 데이터베이스
```

- **BaseRepository**가 공통 인터페이스 제공
- **구체적 Repository**들이 도메인별 특화 로직 구현
- **MongoDB 컬렉션**과 직접 상호작용
- **Service 계층**에서 Repository 의존성 주입으로 사용

## 📝 각 항목 핵심 설명

### Repository 패턴 개요
데이터 접근 로직을 캡슐화하여 비즈니스 로직과 분리, 테스트 가능성 향상

### 기본 Repository 구조
모든 도메인 Repository가 상속받는 공통 인터페이스로 일관성 보장

### 콘텐츠 관리 Repository들
각 도메인별 특화된 쿼리와 비즈니스 로직을 캡슐화

### 고급 쿼리 패턴
MongoDB의 강력한 쿼리 기능을 활용한 효율적인 데이터 처리

### 성능 최적화
인덱스와 캐싱을 통한 대용량 데이터 처리 성능 향상

### 에러 처리 및 트랜잭션
데이터 일관성과 안정성을 보장하는 견고한 에러 처리

---

# 📖 본문

## 1. 실제 Repository 구조 (Beanie ODM 활용)

### 1.1 단순하고 실용적인 Repository 패턴
현재 프로젝트는 Beanie ODM을 사용하여 MongoDB와 연동하므로, 복잡한 BaseRepository 추상화 없이 도메인별 Repository를 직접 구현합니다.

```python
# repositories/user_repository.py
from typing import Optional, List
from src.models.core import User, UserCreate, UserUpdate
from src.exceptions.user import UserNotFoundError, DuplicateUserError

class UserRepository:
    """Repository for user data access operations."""
    
    async def create(self, user_create: UserCreate, password_hash: str) -> User:
        """Create a new user."""
        # Beanie ODM을 사용한 단순한 생성
        user_data = user_create.model_dump(exclude={"password"})
        user_data["password_hash"] = password_hash
        
        user = User(**user_data)
        await user.insert()  # Beanie의 내장 메서드 사용
        
        return user
    
    async def get_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        user = await User.get(user_id)  # Beanie의 내장 메서드
        if not user:
            raise UserNotFoundError(f"User not found: {user_id}")
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await User.find_one({"email": email})  # Beanie 쿼리
    
    async def update(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = await User.get(user_id)
        if not user:
            raise UserNotFoundError(f"User not found: {user_id}")
            
        # Beanie의 업데이트 방식
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
            
        await user.save()  # Beanie의 내장 저장 메서드
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Delete user."""
        user = await User.get(user_id)
        if not user:
            return False
            
        await user.delete()  # Beanie의 내장 삭제 메서드
        return True
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        count = await User.find({"email": email}).count()
        return count > 0
    
    async def user_handle_exists(self, user_handle: str) -> bool:
        """Check if user handle already exists."""
        count = await User.find({"user_handle": user_handle}).count()
        return count > 0
```

## 2. Repository 패턴의 장점

### 2.1 Beanie ODM 활용의 이점
- **타입 안전성**: Pydantic 모델과 완벽 통합
- **단순성**: 복잡한 추상화 계층 없이 직관적 사용
- **성능**: MongoDB 네이티브 기능 직접 활용
- **유지보수성**: 보일러플레이트 코드 최소화

### 2.2 실제 프로젝트 적용 현황

**구현된 Repository 클래스들**:
- `UserRepository`: 사용자 데이터 관리
- `PostRepository`: 게시글 CRUD 및 검색  
- `CommentRepository`: 댓글 계층 구조 관리
- `FileRepository`: 파일 메타데이터 관리

## 3. 핵심 패턴 특징

### 3.1 Beanie ODM 직접 활용
```python
# 복잡한 BaseRepository 대신 Beanie 직접 사용
async def get_by_email(self, email: str) -> Optional[User]:
    return await User.find_one({"email": email})

async def create_post(self, post_data: PostCreate, author_id: str) -> Post:
    post = Post(**post_data.model_dump(), author_id=author_id)
    await post.insert()  # Beanie 내장 메서드
    return post

# 페이지네이션과 검색
async def get_posts_list(self, page: int = 1, limit: int = 20) -> List[Post]:
    skip = (page - 1) * limit
    return await Post.find().skip(skip).limit(limit).to_list()
```

### 3.2 도메인별 특화 메서드
각 Repository는 해당 도메인의 비즈니스 요구사항에 맞는 특화된 메서드를 제공합니다.

```python
# UserRepository 특화 메서드
async def email_exists(self, email: str) -> bool:
    count = await User.find({"email": email}).count()
    return count > 0

# PostRepository 특화 메서드  
async def get_posts_by_author(self, author_id: str) -> List[Post]:
    return await Post.find({"author_id": author_id}).to_list()

# CommentRepository 특화 메서드
async def get_comments_by_post(self, post_id: str) -> List[Comment]:
    return await Comment.find({"parent_id": post_id}).to_list()
```

## 4. Repository 패턴 적용 시 고려사항

### 4.1 현재 패턴의 장점
- **개발 속도**: 빠른 프로토타이핑과 구현
- **가독성**: 코드가 직관적이고 이해하기 쉬움
- **유지보수**: Beanie ODM 업데이트만 따라가면 됨
- **테스트**: Mock 없이도 테스트 가능

### 4.2 향후 확장 고려사항
프로젝트가 10개 이상의 Repository를 가지게 되면 다음을 고려할 수 있습니다:
- 공통 인터페이스 추상화
- 트랜잭션 관리 통합
- 캐싱 레이어 추가
- 감사(Audit) 로깅 통합

### 4.3 현재 프로젝트 규모에 최적화됨
현재 4개의 Repository로는 복잡한 추상화보다 단순하고 명확한 구현이 더 효율적입니다.

## 5. Repository 사용 예시

### 5.1 Service Layer에서의 활용
```python
class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    async def register_user(self, user_data: UserCreate) -> User:
        # 중복 체크
        if await self.user_repository.email_exists(user_data.email):
            raise EmailAlreadyExistsError()
            
        # 사용자 생성
        password_hash = hash_password(user_data.password)
        return await self.user_repository.create(user_data, password_hash)
```

이 패턴은 현재 프로젝트 규모에 적합하며, 향후 확장 시에도 점진적으로 개선할 수 있는 유연성을 제공합니다.
