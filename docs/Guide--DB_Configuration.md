# 데이터베이스 연결 및 설정

## 📋 목차

### 1. 환경 설정 (Environment Setup)
- **환경 변수**: MongoDB 연결 정보 및 시스템 설정 중앙화

### 2. 데이터베이스 연결 관리 (Database Connection)
- **연결 풀링**: 성능 최적화된 MongoDB 연결 관리
- **컬렉션 접근**: 각 데이터 모델별 컬렉션 추상화

### 3. 인덱스 전략 (Index Strategy)
- **성능 최적화**: 쿼리 패턴별 최적화된 인덱스 설계
- **확장성**: 대용량 데이터 처리를 위한 인덱스 구조

### 4. 초기화 및 관리 (Initialization)
- **자동화**: 데이터베이스 초기 설정 자동화
- **개발 도구**: 데이터베이스 리셋 및 관리 유틸리티

### 5. 설정 관리 (Configuration)
- **중앙 집중**: 모든 설정을 하나의 파일에서 관리
- **환경별 분리**: 개발/테스트/프로덕션 환경 설정

### 6. TDD 테스트 전략 (Test Strategy)
- **연결 검증**: 데이터베이스 연결 상태 및 기능 테스트
- **인덱스 검증**: 인덱스 생성 및 성능 테스트
- **설정 검증**: 환경 설정 및 구성 테스트

## 📊 항목 간 관계

```
환경 설정 → 데이터베이스 연결 → 인덱스 생성 → 초기화
    ↓              ↓              ↓           ↓
설정 관리 ←→ TDD 테스트 전략
```

- **환경 설정**이 모든 구성요소의 기반
- **데이터베이스 연결**과 **인덱스 전략**이 핵심 성능 요소
- **TDD 테스트**가 모든 구성요소의 품질 보장

## 📝 각 항목 핵심 설명

### 환경 설정
환경 변수로 시스템 설정을 중앙화하여 환경별 배포 용이성 확보

### 데이터베이스 연결
Motor(비동기 MongoDB 드라이버)를 사용한 효율적인 연결 풀링과 컬렉션별 접근 추상화

### 인덱스 전략  
실제 쿼리 패턴을 분석하여 설계된 복합 인덱스로 읽기/쓰기 성능 최적화

### 초기화 및 관리
데이터베이스 생성부터 인덱스 설정까지 자동화된 초기화 프로세스

### 설정 관리
Pydantic을 활용한 타입 안전한 설정 관리 및 환경별 구성 분리

### TDD 테스트 전략
Mock을 활용한 격리된 테스트 환경에서 모든 구성요소의 동작 검증

---

# 📖 본문

## 1. 환경 설정

### .env 파일
```env
# MongoDB Atlas 설정
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/content_management?retryWrites=true&w=majority
DB_NAME=content_management

# JWT 설정 (나중에 사용)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 환경 설정
ENVIRONMENT=development
DEBUG=true
```

## 2. 데이터베이스 연결 설정

### database.py
```python
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# MongoDB 연결
async def connect_to_mongo():
    """MongoDB Atlas에 연결하고 데이터베이스 인스턴스를 생성합니다."""
    try:
        Database.client = AsyncIOMotorClient(
            os.getenv("MONGODB_URI"),
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            serverSelectionTimeoutMS=5000,  # Atlas 연결 타임아웃
            retryWrites=True,               # Atlas 권장 설정
        )
        Database.database = Database.client[os.getenv("DB_NAME", "content_management")]
        
        # Atlas 연결 테스트
        await Database.client.admin.command('ping')
        logger.info("MongoDB Atlas 연결 성공")
        
        # 인덱스 생성
        await create_indexes()
        logger.info("인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"MongoDB Atlas 연결 실패: {e}")
        raise

async def close_mongo_connection():
    """MongoDB Atlas 연결을 종료합니다."""
    if Database.client:
        Database.client.close()
        logger.info("MongoDB Atlas 연결 종료")

async def get_database():
    """데이터베이스 인스턴스를 반환합니다."""
    return Database.database

# 컬렉션 접근 함수들
async def get_posts_collection():
    db = await get_database()
    return db.posts

async def get_comments_collection():
    db = await get_database()
    return db.comments

async def get_post_stats_collection():
    db = await get_database()
    return db.post_stats

async def get_user_reactions_collection():
    db = await get_database()
    return db.user_reactions

async def get_users_collection():
    db = await get_database()
    return db.users
```

## 3. 인덱스 설정

### indexes.py
```python
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

async def create_indexes():
    """모든 컬렉션에 필요한 인덱스를 생성합니다."""
    from database import get_database
    
    db = await get_database()
    
    try:
        # posts 컬렉션 인덱스
        await create_posts_indexes(db)
        
        # comments 컬렉션 인덱스  
        await create_comments_indexes(db)
        
        # post_stats 컬렉션 인덱스
        await create_post_stats_indexes(db)
        
        # user_reactions 컬렉션 인덱스
        await create_user_reactions_indexes(db)
        
        # users 컬렉션 인덱스
        await create_users_indexes(db)
        
        logger.info("모든 인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

async def create_posts_indexes(db):
    """posts 컬렉션 인덱스 생성"""
    posts_indexes = [
        # slug는 unique 인덱스 (URL 식별자)
        IndexModel([("slug", ASCENDING)], unique=True, name="idx_posts_slug"),
        
        # 게시글 타입별 조회 (서비스별 분리 후 주로 사용)
        IndexModel([("metadata.type", ASCENDING)], name="idx_posts_type"),
        
        # 최신순 정렬 (기본 정렬)
        IndexModel([("createdAt", DESCENDING)], name="idx_posts_created_desc"),
        
        # 작성자별 게시글 조회
        IndexModel([("authorId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_posts_author_created"),
        
        # 텍스트 검색 인덱스 (제목과 내용)
        IndexModel([("title", TEXT), ("content", TEXT)], 
                  weights={"title": 10, "content": 1},
                  name="idx_posts_text_search"),
        
        # 공개/비공개 필터링
        IndexModel([("metadata.visibility", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_posts_visibility_created"),
    ]
    
    await db.posts.create_indexes(posts_indexes)
    logger.info("posts 인덱스 생성 완료")

async def create_comments_indexes(db):
    """comments 컬렉션 인덱스 생성"""
    comments_indexes = [
        # 게시글별 댓글 조회 (가장 많이 사용)
        IndexModel([("parentId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_comments_parent_created"),
        
        # 대댓글 조회
        IndexModel([("parentCommentId", ASCENDING)], name="idx_comments_parent_comment"),
        
        # 작성자별 댓글 조회
        IndexModel([("authorId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_comments_author_created"),
        
        # 댓글 상태별 조회 (active/deleted/hidden)
        IndexModel([("status", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_comments_status_created"),
        
        # 게시글별 활성 댓글만 조회 (성능 최적화)
        IndexModel([("parentId", ASCENDING), ("status", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_comments_parent_status_created"),
    ]
    
    await db.comments.create_indexes(comments_indexes)
    logger.info("comments 인덱스 생성 완료")

async def create_post_stats_indexes(db):
    """post_stats 컬렉션 인덱스 생성"""
    post_stats_indexes = [
        # postId로 통계 조회 (unique)
        IndexModel([("postId", ASCENDING)], unique=True, name="idx_post_stats_post_id"),
        
        # 인기 게시글 조회 (좋아요순)
        IndexModel([("likeCount", DESCENDING)], name="idx_post_stats_like_desc"),
        
        # 조회수 순 정렬
        IndexModel([("viewCount", DESCENDING)], name="idx_post_stats_view_desc"),
        
        # 댓글 많은 순
        IndexModel([("commentCount", DESCENDING)], name="idx_post_stats_comment_desc"),
        
        # 최근 조회된 게시글
        IndexModel([("lastViewedAt", DESCENDING)], name="idx_post_stats_last_viewed"),
    ]
    
    await db.post_stats.create_indexes(post_stats_indexes)
    logger.info("post_stats 인덱스 생성 완료")

async def create_user_reactions_indexes(db):
    """user_reactions 컬렉션 인덱스 생성"""
    user_reactions_indexes = [
        # 사용자-게시글별 반응 (unique)
        IndexModel([("userId", ASCENDING), ("postId", ASCENDING)], 
                  unique=True, name="idx_user_reactions_user_post"),
        
        # 게시글별 반응 집계
        IndexModel([("postId", ASCENDING)], name="idx_user_reactions_post"),
        
        # 사용자별 반응 조회
        IndexModel([("userId", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_user_reactions_user_created"),
        
        # 좋아요한 게시글 조회
        IndexModel([("userId", ASCENDING), ("liked", ASCENDING)],
                  name="idx_user_reactions_user_liked"),
        
        # 북마크한 게시글 조회
        IndexModel([("userId", ASCENDING), ("bookmarked", ASCENDING)],
                  name="idx_user_reactions_user_bookmarked"),
    ]
    
    await db.user_reactions.create_indexes(user_reactions_indexes)
    logger.info("user_reactions 인덱스 생성 완료")

async def create_users_indexes(db):
    """users 컬렉션 인덱스 생성 (나중에 확장)"""
    users_indexes = [
        # 이메일로 사용자 조회 (unique)
        IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email"),
        
        # 사용자 핸들로 조회 (unique)
        IndexModel([("user_handle", ASCENDING)], unique=True, name="idx_users_user_handle"),
        
        # 가입일순 정렬
        IndexModel([("createdAt", DESCENDING)], name="idx_users_created"),
    ]
    
    await db.users.create_indexes(users_indexes)
    logger.info("users 인덱스 생성 완료")
```

## 4. 컬렉션 초기화

### init_db.py
```python
import asyncio
import os
from dotenv import load_dotenv
from database import connect_to_mongo, close_mongo_connection, get_database
from indexes import create_indexes
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """MongoDB Atlas 데이터베이스를 초기화합니다."""
    # 환경 변수 로드
    load_dotenv()
    
    try:
        # MongoDB Atlas 연결
        await connect_to_mongo()
        
        # 데이터베이스 및 컬렉션 생성 확인
        db = await get_database()
        
        # 컬렉션 생성 (Atlas에서 문서가 없어도 인덱스 생성을 위해)
        collections = ['posts', 'comments', 'post_stats', 'user_reactions', 'users']
        
        for collection_name in collections:
            collection = db[collection_name]
            # 컬렉션이 존재하지 않으면 생성
            if collection_name not in await db.list_collection_names():
                await collection.insert_one({"_temp": True})
                await collection.delete_one({"_temp": True})
                logger.info(f"{collection_name} 컬렉션 생성 완료")
        
        # 인덱스 생성
        await create_indexes()
        
        logger.info("MongoDB Atlas 데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"MongoDB Atlas 데이터베이스 초기화 실패: {e}")
        raise
    finally:
        await close_mongo_connection()

async def drop_database():
    """개발용: MongoDB Atlas 데이터베이스를 완전히 삭제합니다."""
    load_dotenv()
    
    try:
        await connect_to_mongo()
        db = await get_database()
        
        # 데이터베이스 삭제
        await db.client.drop_database(db.name)
        logger.info(f"MongoDB Atlas 데이터베이스 '{db.name}' 삭제 완료")
        
    except Exception as e:
        logger.error(f"MongoDB Atlas 데이터베이스 삭제 실패: {e}")
        raise
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    # 사용법:
    # python init_db.py init - 데이터베이스 초기화
    # python init_db.py drop - 데이터베이스 삭제 (개발용)
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            asyncio.run(init_database())
        elif sys.argv[1] == "drop":
            confirm = input("정말로 데이터베이스를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == "yes":
                asyncio.run(drop_database())
        else:
            print("사용법: python init_db.py [init|drop]")
    else:
        asyncio.run(init_database())
```

## 5. 설정 관리

### config.py
```python
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB 설정
    mongodb_uri: str
    db_name: str = "content_management"
    
    # JWT 설정
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # 환경 설정
    environment: str = "development"
    debug: bool = True
    
    # API 설정
    api_title: str = "콘텐츠 관리 API"
    api_version: str = "1.0.0"
    api_description: str = "멀티 서비스 지원 콘텐츠 관리 시스템"
    
    # 페이지네이션 설정
    default_page_size: int = 20
    max_page_size: int = 100
    default_comment_page_size: int = 50
    max_comment_page_size: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스
settings = Settings()
```

## 6. TDD 테스트 코드

### tests/test_database_connection.py
```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from database import (
    connect_to_mongo, 
    close_mongo_connection, 
    get_database,
    get_posts_collection,
    get_comments_collection,
    Database
)

class TestDatabaseConnection:
    """데이터베이스 연결 기능 테스트"""
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_success(self):
        """MongoDB Atlas 연결 성공 테스트"""
        # Given: 올바른 Atlas 연결 정보가 설정되어 있음
        # When: MongoDB Atlas 연결 시도
        # Then: 연결이 성공하고 ping 명령이 작동해야 함
        pass  # 실제 구현에서는 mock을 사용하여 연결 성공 시나리오 테스트
    
    @pytest.mark.asyncio 
    async def test_connect_to_mongo_failure(self):
        """MongoDB Atlas 연결 실패 테스트"""
        # Given: 잘못된 Atlas 연결 정보
        # When: MongoDB Atlas 연결 시도
        # Then: 적절한 예외가 발생해야 함
        pass
    
    @pytest.mark.asyncio
    async def test_get_database_returns_instance(self):
        """데이터베이스 인스턴스 반환 테스트"""
        # Given: 연결된 데이터베이스
        # When: get_database() 호출
        # Then: 유효한 데이터베이스 인스턴스 반환
        pass
    
    @pytest.mark.asyncio
    async def test_get_collections_return_valid_instances(self):
        """컬렉션 접근 함수들 테스트"""
        # Given: 연결된 데이터베이스
        # When: 각 컬렉션 접근 함수 호출
        # Then: 유효한 컬렉션 인스턴스들 반환
        pass
    
    @pytest.mark.asyncio
    async def test_close_connection_properly(self):
        """Atlas 연결 종료 테스트"""
        # Given: 활성화된 MongoDB Atlas 연결
        # When: close_mongo_connection() 호출
        # Then: 연결이 정상적으로 종료되어야 함
        pass

### tests/test_indexes.py
```python
import pytest
from indexes import (
    create_indexes,
    create_posts_indexes,
    create_comments_indexes,
    create_post_stats_indexes,
    create_user_reactions_indexes,
    create_users_indexes
)

class TestDatabaseIndexes:
    """데이터베이스 인덱스 생성 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_posts_indexes(self):
        """posts 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 posts 컬렉션
        # When: create_posts_indexes() 호출
        # Then: 모든 필요한 인덱스가 생성되어야 함
        # - slug unique 인덱스
        # - metadata.type 인덱스
        # - createdAt 내림차순 인덱스
        # - authorId, createdAt 복합 인덱스
        # - 텍스트 검색 인덱스 (title, content)
        # - visibility, createdAt 복합 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_comments_indexes(self):
        """comments 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 comments 컬렉션
        # When: create_comments_indexes() 호출
        # Then: 댓글 조회에 필요한 모든 인덱스 생성
        # - parentId, createdAt 복합 인덱스 (게시글별 댓글)
        # - parentCommentId 인덱스 (대댓글)
        # - authorId, createdAt 복합 인덱스
        # - status, createdAt 복합 인덱스
        # - parentId, status, createdAt 복합 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_post_stats_indexes(self):
        """post_stats 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 post_stats 컬렉션
        # When: create_post_stats_indexes() 호출
        # Then: 통계 조회 및 정렬에 필요한 인덱스 생성
        # - postId unique 인덱스
        # - likeCount 내림차순 인덱스
        # - viewCount 내림차순 인덱스
        # - commentCount 내림차순 인덱스
        # - lastViewedAt 내림차순 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_user_reactions_indexes(self):
        """user_reactions 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 user_reactions 컬렉션
        # When: create_user_reactions_indexes() 호출
        # Then: 사용자 반응 조회에 필요한 인덱스 생성
        # - userId, postId unique 복합 인덱스
        # - postId 인덱스 (게시글별 반응 집계)
        # - userId, createdAt 복합 인덱스
        # - userId, liked 복합 인덱스
        # - userId, bookmarked 복합 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_users_indexes(self):
        """users 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 users 컬렉션
        # When: create_users_indexes() 호출
        # Then: 사용자 조회에 필요한 인덱스 생성
        # - email unique 인덱스
        # - user_handle unique 인덱스
        # - createdAt 내림차순 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_all_indexes_successfully(self):
        """전체 인덱스 생성 통합 테스트"""
        # Given: 초기화된 데이터베이스
        # When: create_indexes() 호출
        # Then: 모든 컬렉션의 인덱스가 성공적으로 생성되어야 함
        pass
    
    @pytest.mark.asyncio
    async def test_index_creation_idempotent(self):
        """인덱스 생성 멱등성 테스트"""
        # Given: 이미 인덱스가 생성된 컬렉션
        # When: 동일한 인덱스 생성 재시도
        # Then: 오류 없이 처리되어야 함 (이미 존재하는 인덱스 무시)
        pass

### tests/test_config.py
```python
import pytest
from unittest.mock import patch
from config import Settings, settings

class TestConfiguration:
    """설정 관리 테스트"""
    
    def test_default_settings_values(self):
        """기본 설정값 테스트"""
        # Given: 환경 변수가 설정되지 않은 상태
        # When: Settings 인스턴스 생성
        # Then: 기본값들이 올바르게 설정되어야 함
        # - db_name: "content_management"
        # - jwt_algorithm: "HS256"
        # - jwt_expire_minutes: 30
        # - default_page_size: 20
        # - max_page_size: 100
        pass
    
    @patch.dict('os.environ', {
        'MONGODB_URI': 'mongodb://test:27017',
        'DB_NAME': 'test_db',
        'JWT_SECRET_KEY': 'test_secret'
    })
    def test_environment_variable_override(self):
        """환경 변수로 설정 오버라이드 테스트"""
        # Given: 환경 변수가 설정된 상태
        # When: Settings 인스턴스 생성
        # Then: 환경 변수 값이 기본값을 오버라이드해야 함
        pass
    
    def test_required_settings_validation(self):
        """필수 설정 검증 테스트"""
        # Given: 필수 환경 변수가 누락된 상태
        # When: Settings 인스턴스 생성 시도
        # Then: 적절한 검증 오류가 발생해야 함
        pass

### tests/test_init_db.py  
```python
import pytest
from unittest.mock import AsyncMock, patch
from init_db import init_database, drop_database

class TestDatabaseInitialization:
    """데이터베이스 초기화 테스트"""
    
    @pytest.mark.asyncio
    async def test_init_database_success(self):
        """MongoDB Atlas 데이터베이스 초기화 성공 테스트"""
        # Given: 올바른 Atlas 환경 설정
        # When: init_database() 호출
        # Then: 다음이 순서대로 실행되어야 함
        # 1. MongoDB Atlas 연결
        # 2. 컬렉션 생성 확인
        # 3. 인덱스 생성
        # 4. 연결 종료
        pass
    
    @pytest.mark.asyncio
    async def test_init_database_creates_missing_collections(self):
        """누락된 컬렉션 생성 테스트"""
        # Given: 일부 컬렉션이 존재하지 않는 Atlas 데이터베이스
        # When: init_database() 호출  
        # Then: 누락된 컬렉션들이 생성되어야 함
        # - posts, comments, post_stats, user_reactions, users
        pass
    
    @pytest.mark.asyncio
    async def test_drop_database_success(self):
        """Atlas 데이터베이스 삭제 테스트"""
        # Given: 존재하는 Atlas 데이터베이스
        # When: drop_database() 호출
        # Then: 데이터베이스가 완전히 삭제되어야 함
        pass
    
    @pytest.mark.asyncio
    async def test_init_database_handles_connection_failure(self):
        """Atlas 연결 실패 시 예외 처리 테스트"""
        # Given: 연결할 수 없는 MongoDB Atlas URI
        # When: init_database() 호출
        # Then: 적절한 예외가 발생하고 정리 작업이 수행되어야 함
        pass

### tests/conftest.py
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.fixture(scope="session")
def event_loop():
    """세션 스코프 이벤트 루프"""
    # Given: 테스트 세션용 이벤트 루프
    # When: 비동기 테스트 실행
    # Then: 모든 테스트가 동일한 루프에서 실행
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_database():
    """목 데이터베이스 인스턴스"""
    # Given: 실제 MongoDB 연결 없이 테스트 진행
    # When: 데이터베이스 관련 테스트 실행
    # Then: 목 객체로 데이터베이스 동작 시뮬레이션
    with patch('database.Database') as mock_db:
        mock_db.database = AsyncMock()
        mock_db.client = AsyncMock()
        yield mock_db

@pytest.fixture
async def test_collections():
    """테스트용 컬렉션 목 객체들"""
    # Given: 각 컬렉션의 목 객체
    # When: 컬렉션 관련 테스트 실행
    # Then: 실제 MongoDB 없이 컬렉션 동작 테스트
    collections = {
        'posts': AsyncMock(),
        'comments': AsyncMock(), 
        'post_stats': AsyncMock(),
        'user_reactions': AsyncMock(),
        'users': AsyncMock()
    }
    yield collections
```

## 7. 실행 및 테스트

### 환경 변수 설정
```bash
# .env 파일 생성 후 MongoDB Atlas URI 설정
cp .env.example .env
# .env 파일에서 MONGODB_URI를 Atlas 클러스터 정보로 수정
```

### 테스트 실행
```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src --cov-report=html

# 특정 테스트 파일 실행
pytest tests/test_database_connection.py -v
```

### 데이터베이스 초기화
```bash
python init_db.py init
```

### FastAPI 앱에서 사용
```python
# main.py
from fastapi import FastAPI
from database import connect_to_mongo, close_mongo_connection

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()  # MongoDB Atlas 연결

@app.on_event("shutdown") 
async def shutdown_event():
    await close_mongo_connection()  # MongoDB Atlas 연결 종료
```

## 2. 데이터베이스 연결 설정

### database.py
```python
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# MongoDB 연결
async def connect_to_mongo():
    """MongoDB에 연결하고 데이터베이스 인스턴스를 생성합니다."""
    try:
        Database.client = AsyncIOMotorClient(
            os.getenv("MONGODB_URI"),
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        Database.database = Database.client[os.getenv("DB_NAME", "content_management")]
        
        # 연결 테스트
        await Database.client.admin.command('ping')
        logger.info("MongoDB 연결 성공")
        
        # 인덱스 생성
        await create_indexes()
        logger.info("인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"MongoDB 연결 실패: {e}")
        raise

async def close_mongo_connection():
    """MongoDB 연결을 종료합니다."""
    if Database.client:
        Database.client.close()
        logger.info("MongoDB 연결 종료")

async def get_database():
    """데이터베이스 인스턴스를 반환합니다."""
    return Database.database

# 컬렉션 접근 함수들
async def get_posts_collection():
    db = await get_database()
    return db.posts

async def get_comments_collection():
    db = await get_database()
    return db.comments

async def get_post_stats_collection():
    db = await get_database()
    return db.post_stats

async def get_user_reactions_collection():
    db = await get_database()
    return db.user_reactions

async def get_users_collection():
    db = await get_database()
    return db.users
```

## 3. 인덱스 설정

### indexes.py
```python
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

async def create_indexes():
    """모든 컬렉션에 필요한 인덱스를 생성합니다."""
    from database import get_database
    
    db = await get_database()
    
    try:
        # posts 컬렉션 인덱스
        await create_posts_indexes(db)
        
        # comments 컬렉션 인덱스  
        await create_comments_indexes(db)
        
        # post_stats 컬렉션 인덱스
        await create_post_stats_indexes(db)
        
        # user_reactions 컬렉션 인덱스
        await create_user_reactions_indexes(db)
        
        # users 컬렉션 인덱스
        await create_users_indexes(db)
        
        logger.info("모든 인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

async def create_posts_indexes(db):
    """posts 컬렉션 인덱스 생성"""
    posts_indexes = [
        # slug는 unique 인덱스 (URL 식별자)
        IndexModel([("slug", ASCENDING)], unique=True, name="idx_posts_slug"),
        
        # 게시글 타입별 조회 (서비스별 분리 후 주로 사용)
        IndexModel([("metadata.type", ASCENDING)], name="idx_posts_type"),
        
        # 최신순 정렬 (기본 정렬)
        IndexModel([("createdAt", DESCENDING)], name="idx_posts_created_desc"),
        
        # 작성자별 게시글 조회
        IndexModel([("authorId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_posts_author_created"),
        
        # 텍스트 검색 인덱스 (제목과 내용)
        IndexModel([("title", TEXT), ("content", TEXT)], 
                  weights={"title": 10, "content": 1},
                  name="idx_posts_text_search"),
        
        # 공개/비공개 필터링
        IndexModel([("metadata.visibility", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_posts_visibility_created"),
    ]
    
    await db.posts.create_indexes(posts_indexes)
    logger.info("posts 인덱스 생성 완료")

async def create_comments_indexes(db):
    """comments 컬렉션 인덱스 생성"""
    comments_indexes = [
        # 게시글별 댓글 조회 (가장 많이 사용)
        IndexModel([("parentId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_comments_parent_created"),
        
        # 대댓글 조회
        IndexModel([("parentCommentId", ASCENDING)], name="idx_comments_parent_comment"),
        
        # 작성자별 댓글 조회
        IndexModel([("authorId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_comments_author_created"),
        
        # 댓글 상태별 조회 (active/deleted/hidden)
        IndexModel([("status", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_comments_status_created"),
        
        # 게시글별 활성 댓글만 조회 (성능 최적화)
        IndexModel([("parentId", ASCENDING), ("status", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_comments_parent_status_created"),
    ]
    
    await db.comments.create_indexes(comments_indexes)
    logger.info("comments 인덱스 생성 완료")

async def create_post_stats_indexes(db):
    """post_stats 컬렉션 인덱스 생성"""
    post_stats_indexes = [
        # postId로 통계 조회 (unique)
        IndexModel([("postId", ASCENDING)], unique=True, name="idx_post_stats_post_id"),
        
        # 인기 게시글 조회 (좋아요순)
        IndexModel([("likeCount", DESCENDING)], name="idx_post_stats_like_desc"),
        
        # 조회수 순 정렬
        IndexModel([("viewCount", DESCENDING)], name="idx_post_stats_view_desc"),
        
        # 댓글 많은 순
        IndexModel([("commentCount", DESCENDING)], name="idx_post_stats_comment_desc"),
        
        # 최근 조회된 게시글
        IndexModel([("lastViewedAt", DESCENDING)], name="idx_post_stats_last_viewed"),
    ]
    
    await db.post_stats.create_indexes(post_stats_indexes)
    logger.info("post_stats 인덱스 생성 완료")

async def create_user_reactions_indexes(db):
    """user_reactions 컬렉션 인덱스 생성"""
    user_reactions_indexes = [
        # 사용자-게시글별 반응 (unique)
        IndexModel([("userId", ASCENDING), ("postId", ASCENDING)], 
                  unique=True, name="idx_user_reactions_user_post"),
        
        # 게시글별 반응 집계
        IndexModel([("postId", ASCENDING)], name="idx_user_reactions_post"),
        
        # 사용자별 반응 조회
        IndexModel([("userId", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_user_reactions_user_created"),
        
        # 좋아요한 게시글 조회
        IndexModel([("userId", ASCENDING), ("liked", ASCENDING)],
                  name="idx_user_reactions_user_liked"),
        
        # 북마크한 게시글 조회
        IndexModel([("userId", ASCENDING), ("bookmarked", ASCENDING)],
                  name="idx_user_reactions_user_bookmarked"),
    ]
    
    await db.user_reactions.create_indexes(user_reactions_indexes)
    logger.info("user_reactions 인덱스 생성 완료")

async def create_users_indexes(db):
    """users 컬렉션 인덱스 생성 (나중에 확장)"""
    users_indexes = [
        # 이메일로 사용자 조회 (unique)
        IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email"),
        
        # 사용자 핸들로 조회 (unique)
        IndexModel([("user_handle", ASCENDING)], unique=True, name="idx_users_user_handle"),
        
        # 가입일순 정렬
        IndexModel([("createdAt", DESCENDING)], name="idx_users_created"),
    ]
    
    await db.users.create_indexes(users_indexes)
    logger.info("users 인덱스 생성 완료")
```

## 4. 컬렉션 초기화

### init_db.py
```python
import asyncio
import os
from dotenv import load_dotenv
from database import connect_to_mongo, close_mongo_connection, get_database
from indexes import create_indexes
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """데이터베이스를 초기화합니다."""
    # 환경 변수 로드
    load_dotenv()
    
    try:
        # MongoDB 연결
        await connect_to_mongo()
        
        # 데이터베이스 및 컬렉션 생성 확인
        db = await get_database()
        
        # 컬렉션 생성 (문서가 없어도 인덱스 생성을 위해)
        collections = ['posts', 'comments', 'post_stats', 'user_reactions', 'users']
        
        for collection_name in collections:
            collection = db[collection_name]
            # 컬렉션이 존재하지 않으면 생성
            if collection_name not in await db.list_collection_names():
                await collection.insert_one({"_temp": True})
                await collection.delete_one({"_temp": True})
                logger.info(f"{collection_name} 컬렉션 생성 완료")
        
        # 인덱스 생성
        await create_indexes()
        
        logger.info("데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise
    finally:
        await close_mongo_connection()

async def drop_database():
    """개발용: 데이터베이스를 완전히 삭제합니다."""
    load_dotenv()
    
    try:
        await connect_to_mongo()
        db = await get_database()
        
        # 데이터베이스 삭제
        await db.client.drop_database(db.name)
        logger.info(f"데이터베이스 '{db.name}' 삭제 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 삭제 실패: {e}")
        raise
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    # 사용법:
    # python init_db.py init - 데이터베이스 초기화
    # python init_db.py drop - 데이터베이스 삭제 (개발용)
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            asyncio.run(init_database())
        elif sys.argv[1] == "drop":
            confirm = input("정말로 데이터베이스를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == "yes":
                asyncio.run(drop_database())
        else:
            print("사용법: python init_db.py [init|drop]")
    else:
        asyncio.run(init_database())
```

## 5. 설정 관리

### config.py
```python
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB 설정
    mongodb_uri: str
    db_name: str = "content_management"
    
    # JWT 설정
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # 환경 설정
    environment: str = "development"
    debug: bool = True
    
    # API 설정
    api_title: str = "콘텐츠 관리 API"
    api_version: str = "1.0.0"
    api_description: str = "멀티 서비스 지원 콘텐츠 관리 시스템"
    
    # 페이지네이션 설정
    default_page_size: int = 20
    max_page_size: int = 100
    default_comment_page_size: int = 50
    max_comment_page_size: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스
settings = Settings()
```

## 6. TDD 테스트 코드

### tests/test_database_connection.py
```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from database import (
    connect_to_mongo, 
    close_mongo_connection, 
    get_database,
    get_posts_collection,
    get_comments_collection,
    Database
)

class TestDatabaseConnection:
    """데이터베이스 연결 기능 테스트"""
    
    @pytest.mark.asyncio
    async def test_connect_to_mongo_success(self):
        """MongoDB 연결 성공 테스트"""
        # Given: 올바른 환경 변수가 설정되어 있음
        # When: MongoDB 연결 시도
        # Then: 연결이 성공하고 ping 명령이 작동해야 함
        pass  # 실제 구현에서는 mock을 사용하여 연결 성공 시나리오 테스트
    
    @pytest.mark.asyncio 
    async def test_connect_to_mongo_failure(self):
        """MongoDB 연결 실패 테스트"""
        # Given: 잘못된 연결 정보
        # When: MongoDB 연결 시도
        # Then: 적절한 예외가 발생해야 함
        pass
    
    @pytest.mark.asyncio
    async def test_get_database_returns_instance(self):
        """데이터베이스 인스턴스 반환 테스트"""
        # Given: 연결된 데이터베이스
        # When: get_database() 호출
        # Then: 유효한 데이터베이스 인스턴스 반환
        pass
    
    @pytest.mark.asyncio
    async def test_get_collections_return_valid_instances(self):
        """컬렉션 접근 함수들 테스트"""
        # Given: 연결된 데이터베이스
        # When: 각 컬렉션 접근 함수 호출
        # Then: 유효한 컬렉션 인스턴스들 반환
        pass
    
    @pytest.mark.asyncio
    async def test_close_connection_properly(self):
        """연결 종료 테스트"""
        # Given: 활성화된 데이터베이스 연결
        # When: close_mongo_connection() 호출
        # Then: 연결이 정상적으로 종료되어야 함
        pass

### tests/test_indexes.py
```python
import pytest
from indexes import (
    create_indexes,
    create_posts_indexes,
    create_comments_indexes,
    create_post_stats_indexes,
    create_user_reactions_indexes,
    create_users_indexes
)

class TestDatabaseIndexes:
    """데이터베이스 인덱스 생성 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_posts_indexes(self):
        """posts 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 posts 컬렉션
        # When: create_posts_indexes() 호출
        # Then: 모든 필요한 인덱스가 생성되어야 함
        # - slug unique 인덱스
        # - metadata.type 인덱스
        # - createdAt 내림차순 인덱스
        # - authorId, createdAt 복합 인덱스
        # - 텍스트 검색 인덱스 (title, content)
        # - visibility, createdAt 복합 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_comments_indexes(self):
        """comments 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 comments 컬렉션
        # When: create_comments_indexes() 호출
        # Then: 댓글 조회에 필요한 모든 인덱스 생성
        # - parentId, createdAt 복합 인덱스 (게시글별 댓글)
        # - parentCommentId 인덱스 (대댓글)
        # - authorId, createdAt 복합 인덱스
        # - status, createdAt 복합 인덱스
        # - parentId, status, createdAt 복합 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_post_stats_indexes(self):
        """post_stats 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 post_stats 컬렉션
        # When: create_post_stats_indexes() 호출
        # Then: 통계 조회 및 정렬에 필요한 인덱스 생성
        # - postId unique 인덱스
        # - likeCount 내림차순 인덱스
        # - viewCount 내림차순 인덱스
        # - commentCount 내림차순 인덱스
        # - lastViewedAt 내림차순 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_user_reactions_indexes(self):
        """user_reactions 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 user_reactions 컬렉션
        # When: create_user_reactions_indexes() 호출
        # Then: 사용자 반응 조회에 필요한 인덱스 생성
        # - userId, postId unique 복합 인덱스
        # - postId 인덱스 (게시글별 반응 집계)
        # - userId, createdAt 복합 인덱스
        # - userId, liked 복합 인덱스
        # - userId, bookmarked 복합 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_users_indexes(self):
        """users 컬렉션 인덱스 생성 테스트"""
        # Given: 빈 users 컬렉션
        # When: create_users_indexes() 호출
        # Then: 사용자 조회에 필요한 인덱스 생성
        # - email unique 인덱스
        # - user_handle unique 인덱스
        # - createdAt 내림차순 인덱스
        pass
    
    @pytest.mark.asyncio
    async def test_create_all_indexes_successfully(self):
        """전체 인덱스 생성 통합 테스트"""
        # Given: 초기화된 데이터베이스
        # When: create_indexes() 호출
        # Then: 모든 컬렉션의 인덱스가 성공적으로 생성되어야 함
        pass
    
    @pytest.mark.asyncio
    async def test_index_creation_idempotent(self):
        """인덱스 생성 멱등성 테스트"""
        # Given: 이미 인덱스가 생성된 컬렉션
        # When: 동일한 인덱스 생성 재시도
        # Then: 오류 없이 처리되어야 함 (이미 존재하는 인덱스 무시)
        pass

### tests/test_config.py
```python
import pytest
from unittest.mock import patch
from config import Settings, settings

class TestConfiguration:
    """설정 관리 테스트"""
    
    def test_default_settings_values(self):
        """기본 설정값 테스트"""
        # Given: 환경 변수가 설정되지 않은 상태
        # When: Settings 인스턴스 생성
        # Then: 기본값들이 올바르게 설정되어야 함
        # - db_name: "content_management"
        # - jwt_algorithm: "HS256"
        # - jwt_expire_minutes: 30
        # - default_page_size: 20
        # - max_page_size: 100
        pass
    
    @patch.dict('os.environ', {
        'MONGODB_URI': 'mongodb://test:27017',
        'DB_NAME': 'test_db',
        'JWT_SECRET_KEY': 'test_secret'
    })
    def test_environment_variable_override(self):
        """환경 변수로 설정 오버라이드 테스트"""
        # Given: 환경 변수가 설정된 상태
        # When: Settings 인스턴스 생성
        # Then: 환경 변수 값이 기본값을 오버라이드해야 함
        pass
    
    def test_required_settings_validation(self):
        """필수 설정 검증 테스트"""
        # Given: 필수 환경 변수가 누락된 상태
        # When: Settings 인스턴스 생성 시도
        # Then: 적절한 검증 오류가 발생해야 함
        pass

### tests/test_init_db.py  
```python
import pytest
from unittest.mock import AsyncMock, patch
from init_db import init_database, drop_database

class TestDatabaseInitialization:
    """데이터베이스 초기화 테스트"""
    
    @pytest.mark.asyncio
    async def test_init_database_success(self):
        """데이터베이스 초기화 성공 테스트"""
        # Given: 올바른 환경 설정
        # When: init_database() 호출
        # Then: 다음이 순서대로 실행되어야 함
        # 1. MongoDB 연결
        # 2. 컬렉션 생성 확인
        # 3. 인덱스 생성
        # 4. 연결 종료
        pass
    
    @pytest.mark.asyncio
    async def test_init_database_creates_missing_collections(self):
        """누락된 컬렉션 생성 테스트"""
        # Given: 일부 컬렉션이 존재하지 않는 데이터베이스
        # When: init_database() 호출  
        # Then: 누락된 컬렉션들이 생성되어야 함
        # - posts, comments, post_stats, user_reactions, users
        pass
    
    @pytest.mark.asyncio
    async def test_drop_database_success(self):
        """데이터베이스 삭제 테스트"""
        # Given: 존재하는 데이터베이스
        # When: drop_database() 호출
        # Then: 데이터베이스가 완전히 삭제되어야 함
        pass
    
    @pytest.mark.asyncio
    async def test_init_database_handles_connection_failure(self):
        """연결 실패 시 예외 처리 테스트"""
        # Given: 연결할 수 없는 MongoDB URI
        # When: init_database() 호출
        # Then: 적절한 예외가 발생하고 정리 작업이 수행되어야 함
        pass

### tests/conftest.py
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.fixture(scope="session")
def event_loop():
    """세션 스코프 이벤트 루프"""
    # Given: 테스트 세션용 이벤트 루프
    # When: 비동기 테스트 실행
    # Then: 모든 테스트가 동일한 루프에서 실행
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_database():
    """목 데이터베이스 인스턴스"""
    # Given: 실제 MongoDB 연결 없이 테스트 진행
    # When: 데이터베이스 관련 테스트 실행
    # Then: 목 객체로 데이터베이스 동작 시뮬레이션
    with patch('database.Database') as mock_db:
        mock_db.database = AsyncMock()
        mock_db.client = AsyncMock()
        yield mock_db

@pytest.fixture
async def test_collections():
    """테스트용 컬렉션 목 객체들"""
    # Given: 각 컬렉션의 목 객체
    # When: 컬렉션 관련 테스트 실행
    # Then: 실제 MongoDB 없이 컬렉션 동작 테스트
    collections = {
        'posts': AsyncMock(),
        'comments': AsyncMock(), 
        'post_stats': AsyncMock(),
        'user_reactions': AsyncMock(),
        'users': AsyncMock()
    }
    yield collections
```

## 7. 사용 방법

### 1. 프로젝트 설정
```bash
# uv를 사용한 프로젝트 초기화
uv init content-management-api
cd content-management-api

# 의존성 설치
uv add fastapi uvicorn motor pymongo pydantic python-jose passlib python-multipart python-dotenv pydantic-settings

# 테스트 의존성 설치
uv add --group test pytest pytest-asyncio pytest-mock httpx pytest-cov
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성 후 MongoDB URI 설정
cp .env.example .env
# .env 파일에서 MONGODB_URI 수정
```

### 3. 테스트 실행
```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 포함 테스트
uv run pytest --cov=src --cov-report=html

# 특정 테스트 파일 실행
uv run pytest tests/test_database_connection.py -v
```

### 4. 데이터베이스 초기화
```bash
uv run python init_db.py init
```

### 5. FastAPI 앱에서 사용
```python
# main.py
from fastapi import FastAPI
from database import connect_to_mongo, close_mongo_connection

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown") 
async def shutdown_event():
    await close_mongo_connection()
```

## 2. 데이터베이스 연결 설정

### database.py
```python
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# MongoDB 연결
async def connect_to_mongo():
    """MongoDB에 연결하고 데이터베이스 인스턴스를 생성합니다."""
    try:
        Database.client = AsyncIOMotorClient(
            os.getenv("MONGODB_URI"),
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        Database.database = Database.client[os.getenv("DB_NAME", "content_management")]
        
        # 연결 테스트
        await Database.client.admin.command('ping')
        logger.info("MongoDB 연결 성공")
        
        # 인덱스 생성
        await create_indexes()
        logger.info("인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"MongoDB 연결 실패: {e}")
        raise

async def close_mongo_connection():
    """MongoDB 연결을 종료합니다."""
    if Database.client:
        Database.client.close()
        logger.info("MongoDB 연결 종료")

async def get_database():
    """데이터베이스 인스턴스를 반환합니다."""
    return Database.database

# 컬렉션 접근 함수들
async def get_posts_collection():
    db = await get_database()
    return db.posts

async def get_comments_collection():
    db = await get_database()
    return db.comments

async def get_post_stats_collection():
    db = await get_database()
    return db.post_stats

async def get_user_reactions_collection():
    db = await get_database()
    return db.user_reactions

async def get_users_collection():
    db = await get_database()
    return db.users
```

## 3. 인덱스 설정

### indexes.py
```python
from pymongo import IndexModel, TEXT, ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)

async def create_indexes():
    """모든 컬렉션에 필요한 인덱스를 생성합니다."""
    from database import get_database
    
    db = await get_database()
    
    try:
        # posts 컬렉션 인덱스
        await create_posts_indexes(db)
        
        # comments 컬렉션 인덱스  
        await create_comments_indexes(db)
        
        # post_stats 컬렉션 인덱스
        await create_post_stats_indexes(db)
        
        # user_reactions 컬렉션 인덱스
        await create_user_reactions_indexes(db)
        
        # users 컬렉션 인덱스
        await create_users_indexes(db)
        
        logger.info("모든 인덱스 생성 완료")
        
    except Exception as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

async def create_posts_indexes(db):
    """posts 컬렉션 인덱스 생성"""
    posts_indexes = [
        # slug는 unique 인덱스 (URL 식별자)
        IndexModel([("slug", ASCENDING)], unique=True, name="idx_posts_slug"),
        
        # 게시글 타입별 조회 (서비스별 분리 후 주로 사용)
        IndexModel([("metadata.type", ASCENDING)], name="idx_posts_type"),
        
        # 최신순 정렬 (기본 정렬)
        IndexModel([("createdAt", DESCENDING)], name="idx_posts_created_desc"),
        
        # 작성자별 게시글 조회
        IndexModel([("authorId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_posts_author_created"),
        
        # 텍스트 검색 인덱스 (제목과 내용)
        IndexModel([("title", TEXT), ("content", TEXT)], 
                  weights={"title": 10, "content": 1},
                  name="idx_posts_text_search"),
        
        # 공개/비공개 필터링
        IndexModel([("metadata.visibility", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_posts_visibility_created"),
    ]
    
    await db.posts.create_indexes(posts_indexes)
    logger.info("posts 인덱스 생성 완료")

async def create_comments_indexes(db):
    """comments 컬렉션 인덱스 생성"""
    comments_indexes = [
        # 게시글별 댓글 조회 (가장 많이 사용)
        IndexModel([("parentId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_comments_parent_created"),
        
        # 대댓글 조회
        IndexModel([("parentCommentId", ASCENDING)], name="idx_comments_parent_comment"),
        
        # 작성자별 댓글 조회
        IndexModel([("authorId", ASCENDING), ("createdAt", DESCENDING)], 
                  name="idx_comments_author_created"),
        
        # 댓글 상태별 조회 (active/deleted/hidden)
        IndexModel([("status", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_comments_status_created"),
        
        # 게시글별 활성 댓글만 조회 (성능 최적화)
        IndexModel([("parentId", ASCENDING), ("status", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_comments_parent_status_created"),
    ]
    
    await db.comments.create_indexes(comments_indexes)
    logger.info("comments 인덱스 생성 완료")

async def create_post_stats_indexes(db):
    """post_stats 컬렉션 인덱스 생성"""
    post_stats_indexes = [
        # postId로 통계 조회 (unique)
        IndexModel([("postId", ASCENDING)], unique=True, name="idx_post_stats_post_id"),
        
        # 인기 게시글 조회 (좋아요순)
        IndexModel([("likeCount", DESCENDING)], name="idx_post_stats_like_desc"),
        
        # 조회수 순 정렬
        IndexModel([("viewCount", DESCENDING)], name="idx_post_stats_view_desc"),
        
        # 댓글 많은 순
        IndexModel([("commentCount", DESCENDING)], name="idx_post_stats_comment_desc"),
        
        # 최근 조회된 게시글
        IndexModel([("lastViewedAt", DESCENDING)], name="idx_post_stats_last_viewed"),
    ]
    
    await db.post_stats.create_indexes(post_stats_indexes)
    logger.info("post_stats 인덱스 생성 완료")

async def create_user_reactions_indexes(db):
    """user_reactions 컬렉션 인덱스 생성"""
    user_reactions_indexes = [
        # 사용자-게시글별 반응 (unique)
        IndexModel([("userId", ASCENDING), ("postId", ASCENDING)], 
                  unique=True, name="idx_user_reactions_user_post"),
        
        # 게시글별 반응 집계
        IndexModel([("postId", ASCENDING)], name="idx_user_reactions_post"),
        
        # 사용자별 반응 조회
        IndexModel([("userId", ASCENDING), ("createdAt", DESCENDING)],
                  name="idx_user_reactions_user_created"),
        
        # 좋아요한 게시글 조회
        IndexModel([("userId", ASCENDING), ("liked", ASCENDING)],
                  name="idx_user_reactions_user_liked"),
        
        # 북마크한 게시글 조회
        IndexModel([("userId", ASCENDING), ("bookmarked", ASCENDING)],
                  name="idx_user_reactions_user_bookmarked"),
    ]
    
    await db.user_reactions.create_indexes(user_reactions_indexes)
    logger.info("user_reactions 인덱스 생성 완료")

async def create_users_indexes(db):
    """users 컬렉션 인덱스 생성 (나중에 확장)"""
    users_indexes = [
        # 이메일로 사용자 조회 (unique)
        IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email"),
        
        # 사용자 핸들로 조회 (unique)
        IndexModel([("user_handle", ASCENDING)], unique=True, name="idx_users_user_handle"),
        
        # 가입일순 정렬
        IndexModel([("createdAt", DESCENDING)], name="idx_users_created"),
    ]
    
    await db.users.create_indexes(users_indexes)
    logger.info("users 인덱스 생성 완료")
```

## 4. 컬렉션 초기화

### init_db.py
```python
import asyncio
import os
from dotenv import load_dotenv
from database import connect_to_mongo, close_mongo_connection, get_database
from indexes import create_indexes
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """데이터베이스를 초기화합니다."""
    # 환경 변수 로드
    load_dotenv()
    
    try:
        # MongoDB 연결
        await connect_to_mongo()
        
        # 데이터베이스 및 컬렉션 생성 확인
        db = await get_database()
        
        # 컬렉션 생성 (문서가 없어도 인덱스 생성을 위해)
        collections = ['posts', 'comments', 'post_stats', 'user_reactions', 'users']
        
        for collection_name in collections:
            collection = db[collection_name]
            # 컬렉션이 존재하지 않으면 생성
            if collection_name not in await db.list_collection_names():
                await collection.insert_one({"_temp": True})
                await collection.delete_one({"_temp": True})
                logger.info(f"{collection_name} 컬렉션 생성 완료")
        
        # 인덱스 생성
        await create_indexes()
        
        logger.info("데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise
    finally:
        await close_mongo_connection()

async def drop_database():
    """개발용: 데이터베이스를 완전히 삭제합니다."""
    load_dotenv()
    
    try:
        await connect_to_mongo()
        db = await get_database()
        
        # 데이터베이스 삭제
        await db.client.drop_database(db.name)
        logger.info(f"데이터베이스 '{db.name}' 삭제 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 삭제 실패: {e}")
        raise
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    # 사용법:
    # python init_db.py init - 데이터베이스 초기화
    # python init_db.py drop - 데이터베이스 삭제 (개발용)
    
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            asyncio.run(init_database())
        elif sys.argv[1] == "drop":
            confirm = input("정말로 데이터베이스를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == "yes":
                asyncio.run(drop_database())
        else:
            print("사용법: python init_db.py [init|drop]")
    else:
        asyncio.run(init_database())
```

## 5. 설정 관리

### config.py
```python
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB 설정
    mongodb_uri: str
    db_name: str = "content_management"
    
    # JWT 설정
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # 환경 설정
    environment: str = "development"
    debug: bool = True
    
    # API 설정
    api_title: str = "콘텐츠 관리 API"
    api_version: str = "1.0.0"
    api_description: str = "멀티 서비스 지원 콘텐츠 관리 시스템"
    
    # 페이지네이션 설정
    default_page_size: int = 20
    max_page_size: int = 100
    default_comment_page_size: int = 50
    max_comment_page_size: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스
settings = Settings()
```

## 6. 사용 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성 후 MongoDB URI 설정
cp .env.example .env
# .env 파일에서 MONGODB_URI 수정
```

### 3. 데이터베이스 초기화
```bash
python init_db.py init
```

### 4. FastAPI 앱에서 사용
```python
# main.py
from fastapi import FastAPI
from database import connect_to_mongo, close_mongo_connection

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown") 
async def shutdown_event():
    await close_mongo_connection()
```

이 설정으로 MongoDB 연결과 최적화된 인덱스가 준비됩니다. 다음 단계로 **기본 프로젝트 구조**를 작성해드릴까요?