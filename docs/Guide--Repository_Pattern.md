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

## 1. 기본 Repository 구조

### 1.1 추상 베이스 Repository
```python
# repositories/base.py
from abc import ABC, abstractmethod
from typing import Optional, List, Generic, TypeVar, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from datetime import datetime
import logging

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """모든 Repository의 기본 클래스"""
    
    def __init__(self, collection: AsyncIOMotorCollection, model_class: type):
        self.collection = collection
        self.model_class = model_class
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def create(self, entity: T) -> T:
        """엔티티 생성"""
        try:
            entity_dict = entity.dict() if hasattr(entity, 'dict') else entity
            result = await self.collection.insert_one(entity_dict)
            
            if result.inserted_id:
                self.logger.info(f"엔티티 생성 성공: {result.inserted_id}")
                return entity
            
            raise Exception("엔티티 생성 실패")
            
        except Exception as e:
            self.logger.error(f"엔티티 생성 오류: {e}")
            raise
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """ID로 엔티티 조회"""
        try:
            document = await self.collection.find_one({"id": entity_id})
            return self.model_class(**document) if document else None
            
        except Exception as e:
            self.logger.error(f"엔티티 조회 오류: {e}")
            return None
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """엔티티 업데이트"""
        try:
            # 업데이트 시간 자동 추가
            update_data["updated_at"] = datetime.utcnow()
            
            document = await self.collection.find_one_and_update(
                {"id": entity_id},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
            
            return self.model_class(**document) if document else None
            
        except Exception as e:
            self.logger.error(f"엔티티 업데이트 오류: {e}")
            return None
    
    async def delete(self, entity_id: str) -> bool:
        """엔티티 삭제"""
        try:
            result = await self.collection.delete_one({"id": entity_id})
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"엔티티 삭제 오류: {e}")
            return False
    
    async def exists(self, entity_id: str) -> bool:
        """엔티티 존재 확인"""
        count = await self.collection.count_documents({"id": entity_id})
        return count > 0
    
    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """엔티티 개수 조회"""
        filter_dict = filter_dict or {}
        return await self.collection.count_documents(filter_dict)
```

## 2. User Repository

### 2.1 User Repository 구현
```python
# repositories/user_repository.py
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from models.user import User, UserCreate, UserUpdate
from repositories.base import BaseRepository
from database.connection import get_users_collection
from datetime import datetime

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(None, User)
        
    async def get_collection(self) -> AsyncIOMotorCollection:
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
        self.logger.info(f"사용자 생성: {user.email}")
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        collection = await self.get_collection()
        document = await collection.find_one({"email": email})
        return User(**document) if document else None
    
    async def get_by_user_handle(self, user_handle: str) -> Optional[User]:
        """사용자 핸들로 조회"""
        collection = await self.get_collection()
        document = await collection.find_one({"user_handle": user_handle})
        return User(**document) if document else None
    
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
    
    async def update_last_login(self, user_id: str) -> bool:
        """마지막 로그인 시간 업데이트"""
        collection = await self.get_collection()
        result = await collection.update_one(
            {"id": user_id},
            {"$set": {"last_login_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def get_active_users(self, page: int = 1, limit: int = 20) -> List[User]:
        """활성 사용자 목록 조회"""
        collection = await self.get_collection()
        skip = (page - 1) * limit
        
        cursor = collection.find(
            {"status": "active"}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        return [User(**doc) for doc in documents]
```

## 3. Post Repository

### 3.1 Post Repository 구현
```python
# repositories/post_repository.py
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from models.post import Post, PostCreate, PostListItem
from models.common import PaginationResponse
from repositories.base import BaseRepository
from database.connection import get_posts_collection
from datetime import datetime, timedelta

class PostRepository(BaseRepository[Post]):
    def __init__(self):
        super().__init__(None, Post)
    
    async def get_collection(self) -> AsyncIOMotorCollection:
        if not self.collection:
            self.collection = await get_posts_collection()
        return self.collection
    
    async def create_post(self, post_data: PostCreate, author_id: str) -> Post:
        """게시글 생성 (ID 기반 slug)"""
        collection = await self.get_collection()
        
        # 1. 먼저 임시 slug로 게시글 생성
        post = Post(
            **post_data.dict(),
            author_id=author_id,
            slug="temp"  # 임시 slug
        )
        
        # 2. 데이터베이스에 저장
        result = await collection.insert_one(post.dict())
        
        # 3. ID 기반 slug 생성 및 업데이트
        id_based_slug = str(post.id)
        await collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"slug": id_based_slug}}
        )
        
        # 4. 업데이트된 게시글 반환
        post.slug = id_based_slug
        self.logger.info(f"게시글 생성: {post.slug}")
        return post
    
    async def get_by_slug(self, slug: str) -> Optional[Post]:
        """slug로 게시글 조회"""
        collection = await self.get_collection()
        document = await collection.find_one({"slug": slug})
        return Post(**document) if document else None
    
    async def slug_exists(self, slug: str) -> bool:
        """slug 중복 확인 (ID 기반이므로 항상 고유하지만 검증용)"""
        collection = await self.get_collection()
        count = await collection.count_documents({"slug": slug})
        return count > 0
    
    async def count_user_posts_today(self, author_id: str) -> int:
        """사용자의 오늘 게시글 수 조회"""
        collection = await self.get_collection()
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        count = await collection.count_documents({
            "author_id": author_id,
            "created_at": {
                "$gte": today_start,
                "$lt": today_end
            }
        })
        return count
    
    async def get_posts_list(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Dict[str, Any] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginationResponse[PostListItem]:
        """게시글 목록 조회 (페이지네이션)"""
        collection = await self.get_collection()
        filters = filters or {}
        
        # 총 개수 조회
        total = await collection.count_documents(filters)
        
        # 정렬 설정
        sort_direction = -1 if sort_order == "desc" else 1
        
        # 페이지네이션 계산
        skip = (page - 1) * limit
        
        # 집계 파이프라인으로 stats 포함해서 조회
        pipeline = [
            {"$match": filters},
            {"$lookup": {
                "from": "post_stats",
                "localField": "id",
                "foreignField": "postId", 
                "as": "stats"
            }},
            {"$addFields": {
                "stats": {
                    "$ifNull": [
                        {"$arrayElemAt": ["$stats", 0]},
                        {
                            "viewCount": 0,
                            "likeCount": 0,
                            "dislikeCount": 0,
                            "commentCount": 0
                        }
                    ]
                }
            }},
            {"$sort": {sort_by: sort_direction}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {
                "id": 1,
                "title": 1,
                "slug": 1,
                "author_id": 1,
                "service": 1,
                "metadata": 1,
                "stats": {
                    "viewCount": "$stats.viewCount",
                    "likeCount": "$stats.likeCount", 
                    "dislikeCount": "$stats.dislikeCount",
                    "commentCount": "$stats.commentCount"
                },
                "created_at": 1,
                "updated_at": 1
            }}
        ]
        
        cursor = collection.aggregate(pipeline)
        documents = await cursor.to_list(length=limit)
        
        posts = [PostListItem(**doc) for doc in documents]
        
        return PaginationResponse(
            items=posts,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit
        )
    
    async def search_posts(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        filters: Dict[str, Any] = None
    ) -> PaginationResponse[PostListItem]:
        """게시글 검색"""
        collection = await self.get_collection()
        filters = filters or {}
        
        # 텍스트 검색 조건 추가
        search_filter = {
            "$text": {"$search": query},
            **filters
        }
        
        return await self.get_posts_list(
            page=page,
            limit=limit,
            filters=search_filter,
            sort_by="score",  # 검색 점수순 정렬
            sort_order="desc"
        )
    
    async def get_posts_by_author(
        self,
        author_id: str,
        page: int = 1,
        limit: int = 20
    ) -> PaginationResponse[PostListItem]:
        """작성자별 게시글 조회"""
        return await self.get_posts_list(
            page=page,
            limit=limit,
            filters={"author_id": author_id}
        )
    
    async def get_posts_by_type(
        self,
        post_type: str,
        page: int = 1,
        limit: int = 20
    ) -> PaginationResponse[PostListItem]:
        """타입별 게시글 조회"""
        return await self.get_posts_list(
            page=page,
            limit=limit,
            filters={"metadata.type": post_type}
        )
```

## 4. Comment Repository

### 4.1 Comment Repository 구현  
```python
# repositories/comment_repository.py
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from models.comment import Comment, CommentCreate, CommentDetail
from models.common import PaginationResponse
from repositories.base import BaseRepository
from database.connection import get_comments_collection

class CommentRepository(BaseRepository[Comment]):
    def __init__(self):
        super().__init__(None, Comment)
    
    async def get_collection(self) -> AsyncIOMotorCollection:
        if not self.collection:
            self.collection = await get_comments_collection()
        return self.collection
    
    async def create_comment(
        self, 
        comment_data: CommentCreate, 
        author_id: str, 
        parent_id: str
    ) -> Comment:
        """댓글 생성"""
        collection = await self.get_collection()
        
        comment = Comment(
            **comment_data.dict(),
            author_id=author_id,
            parent_id=parent_id,
            parent_type="post"
        )
        
        await collection.insert_one(comment.dict())
        self.logger.info(f"댓글 생성: {comment.id}")
        return comment
    
    async def get_comments_by_post(
        self,
        post_id: str,
        page: int = 1,
        limit: int = 50,
        include_replies: bool = True
    ) -> PaginationResponse[CommentDetail]:
        """게시글별 댓글 조회"""
        collection = await self.get_collection()
        
        # 활성 댓글만 조회
        base_filter = {
            "parent_id": post_id,
            "parent_type": "post",
            "status": "active"
        }
        
        if not include_replies:
            base_filter["parent_comment_id"] = {"$exists": False}
        
        # 총 개수
        total = await collection.count_documents(base_filter)
        
        # 페이지네이션
        skip = (page - 1) * limit
        
        # 댓글 조회 (대댓글 포함)
        pipeline = [
            {"$match": base_filter},
            {"$sort": {"created_at": 1}},  # 시간순 정렬
            {"$skip": skip},
            {"$limit": limit},
            # 대댓글 조회를 위한 lookup (필요시)
            {"$lookup": {
                "from": "comments",
                "let": {"comment_id": "$id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$parent_comment_id", "$$comment_id"]},
                        "status": "active"
                    }},
                    {"$sort": {"created_at": 1}},
                    {"$limit": 10}  # 대댓글 최대 10개
                ],
                "as": "replies"
            }}
        ]
        
        cursor = collection.aggregate(pipeline)
        documents = await cursor.to_list(length=limit)
        
        comments = [CommentDetail(**doc) for doc in documents]
        
        return PaginationResponse(
            items=comments,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit
        )
    
    async def get_comment_with_replies(self, comment_id: str) -> Optional[CommentDetail]:
        """댓글과 대댓글 함께 조회"""
        collection = await self.get_collection()
        
        pipeline = [
            {"$match": {"id": comment_id, "status": "active"}},
            {"$lookup": {
                "from": "comments",
                "let": {"comment_id": "$id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$parent_comment_id", "$$comment_id"]},
                        "status": "active"
                    }},
                    {"$sort": {"created_at": 1}}
                ],
                "as": "replies"
            }}
        ]
        
        cursor = collection.aggregate(pipeline)
        documents = await cursor.to_list(length=1)
        
        return CommentDetail(**documents[0]) if documents else None
    
    async def soft_delete_comment(self, comment_id: str) -> bool:
        """댓글 소프트 삭제"""
        collection = await self.get_collection()
        result = await collection.update_one(
            {"id": comment_id},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def get_comments_by_author(
        self,
        author_id: str,
        page: int = 1,
        limit: int = 20
    ) -> PaginationResponse[Comment]:
        """작성자별 댓글 조회"""
        collection = await self.get_collection()
        
        filters = {
            "author_id": author_id,
            "status": "active"
        }
        
        total = await collection.count_documents(filters)
        skip = (page - 1) * limit
        
        cursor = collection.find(filters).sort("created_at", -1).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        comments = [Comment(**doc) for doc in documents]
        
        return PaginationResponse(
            items=comments,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit
        )
```

## 5. Stats Repository

### 5.1 통계 관리 Repository
```python
# repositories/stats_repository.py
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from models.stats import PostStats, UserReaction
from repositories.base import BaseRepository
from database.connection import get_post_stats_collection, get_user_reactions_collection
from datetime import datetime
import logging

class StatsRepository:
    def __init__(self):
        self.stats_collection = None
        self.reactions_collection = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_stats_collection(self) -> AsyncIOMotorCollection:
        if not self.stats_collection:
            self.stats_collection = await get_post_stats_collection()
        return self.stats_collection
    
    async def get_reactions_collection(self) -> AsyncIOMotorCollection:
        if not self.reactions_collection:
            self.reactions_collection = await get_user_reactions_collection()
        return self.reactions_collection
    
    async def get_post_stats(self, post_id: str) -> Optional[PostStats]:
        """게시글 통계 조회"""
        collection = await self.get_stats_collection()
        document = await collection.find_one({"postId": post_id})
        return PostStats(**document) if document else None
    
    async def increment_view_count(self, post_id: str) -> bool:
        """조회수 증가"""
        collection = await self.get_stats_collection()
        result = await collection.update_one(
            {"postId": post_id},
            {
                "$inc": {"viewCount": 1},
                "$set": {"lastViewedAt": datetime.utcnow()}
            },
            upsert=True
        )
        return result.acknowledged
    
    async def toggle_user_reaction(
        self,
        user_id: str,
        post_id: str,
        reaction_type: str  # "like", "dislike", "bookmark"
    ) -> Dict[str, Any]:
        """사용자 반응 토글"""
        reactions_collection = await self.get_reactions_collection()
        stats_collection = await self.get_stats_collection()
        
        # 현재 반응 상태 조회
        current_reaction = await reactions_collection.find_one({
            "userId": user_id,
            "postId": post_id
        })
        
        if not current_reaction:
            # 새 반응 생성
            new_reaction = UserReaction(
                userId=user_id,
                postId=post_id,
                liked=(reaction_type == "like"),
                disliked=(reaction_type == "dislike"),
                bookmarked=(reaction_type == "bookmark")
            )
            await reactions_collection.insert_one(new_reaction.dict())
            action = f"{reaction_type}d"
            increment_value = 1
        else:
            # 기존 반응 토글
            current_value = current_reaction.get(reaction_type, False)
            new_value = not current_value
            
            # 상호 배타적 처리 (좋아요 <-> 싫어요)
            update_data = {reaction_type: new_value}
            if reaction_type == "like" and new_value:
                update_data["disliked"] = False
            elif reaction_type == "dislike" and new_value:
                update_data["liked"] = False
            
            await reactions_collection.update_one(
                {"userId": user_id, "postId": post_id},
                {"$set": update_data}
            )
            
            action = f"{reaction_type}d" if new_value else f"un{reaction_type}d"
            increment_value = 1 if new_value else -1
        
        # 통계 업데이트
        stats_field = f"{reaction_type}Count"
        await stats_collection.update_one(
            {"postId": post_id},
            {"$inc": {stats_field: increment_value}},
            upsert=True
        )
        
        # 업데이트된 반응 정보 반환
        updated_reaction = await reactions_collection.find_one({
            "userId": user_id,
            "postId": post_id
        })
        
        return {
            "action": action,
            "userReaction": UserReaction(**updated_reaction) if updated_reaction else None
        }
```

## 6. Repository 의존성 주입

### 6.1 의존성 제공자
```python
# dependencies/repositories.py
from repositories.user_repository import UserRepository
from repositories.post_repository import PostRepository
from repositories.comment_repository import CommentRepository
from repositories.stats_repository import StatsRepository

# 전역 인스턴스
_user_repo = None
_post_repo = None
_comment_repo = None
_stats_repo = None

async def get_user_repository() -> UserRepository:
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepository()
    return _user_repo

async def get_post_repository() -> PostRepository:
    global _post_repo
    if _post_repo is None:
        _post_repo = PostRepository()
    return _post_repo

async def get_comment_repository() -> CommentRepository:
    global _comment_repo
    if _comment_repo is None:
        _comment_repo = CommentRepository()
    return _comment_repo

async def get_stats_repository() -> StatsRepository:
    global _stats_repo
    if _stats_repo is None:
        _stats_repo = StatsRepository()
    return _stats_repo
```
