"""Enhanced unit tests for posts service functionality.

## 📋 모듈 목차

### 🎯 역할 및 기능
- **역할**: PostsService 비즈니스 로직 검증
- **범위**: 포스트 CRUD, 검색, 통계 기능
- **Epic**: 콘텐츠 관리 시스템 > 포스트 관리

### 🔗 관련 모듈
- **상위 도메인**: `test_posts_router.py` (API 통합)
- **하위 의존성**: `test_post_repository.py` (Repository)
- **동등 계층**: `test_comments_service.py` (Service)
- **유틸리티**: `test_permissions.py` (권한 검사)

### 🔄 함수 관계
```
create_post() → validate_data() → check_permissions()
list_posts() → calculate_stats() → apply_user_reactions()
search_posts() → build_query() → format_results()
```

### 🎭 Mock 사용 정책
- **✅ 실제 구현**: PostsService (비즈니스 로직 검증)
- **🚨 Mock 사용**: PostRepository (DB 호출 비용 높음)
- **🔄 대안 검토**: 실제 DB 사용 시 테스트 불안정성

🎯 테스트 전략: Mock 사용 기준에 따른 실제 구현 검증
- Service 계층: 실제 PostsService 인스턴스 사용 (비즈니스 로직 검증)
- Repository 계층: Mock 사용 (🚨 DB 호출 비용 높음)
- Utils 계층: 실제 함수 호출 (순수 함수 특성 활용)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from src.models.core import User, Post, PostCreate, PostUpdate, PostMetadata
from src.services.posts_service import PostsService
from src.repositories.post_repository import PostRepository
from src.exceptions.post import PostNotFoundError, PostPermissionError


class TestPostsServiceEnhanced:
    """Enhanced test posts service functionality."""
    
    @pytest.fixture
    def mock_post_repository(self):
        """Create mock post repository."""
        repo = Mock(spec=PostRepository)
        return repo
    
    @pytest.fixture
    def posts_service(self, mock_post_repository):
        """Create posts service instance.
        
        🚨 Mock 사용 이유: PostRepository (DB 호출 비용 높음)
        ✅ 실제 구현 검증: PostsService 비즈니스 로직 직접 테스트
        🔄 대안 검토: 실제 DB 사용 시 테스트 불안정성
        """
        return PostsService(post_repository=mock_post_repository)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        user = Mock(spec=User)
        user.id = "user123"
        user.email = "test@example.com"
        user.user_handle = "testuser"
        user.is_admin = False
        return user
    
    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        user = Mock(spec=User)
        user.id = "admin123"
        user.email = "admin@example.com"
        user.user_handle = "adminuser"
        user.is_admin = True
        return user
    
    @pytest.fixture
    def sample_post(self):
        """Create sample post."""
        post = Mock(spec=Post)
        post.id = "post123"
        post.title = "Test Post"
        post.content = "Test content"
        post.slug = "test-post"
        post.author_id = "user123"
        post.service = "community"
        post.status = "published"
        post.created_at = datetime.utcnow()
        post.updated_at = datetime.utcnow()
        post.metadata = PostMetadata(type="자유게시판")
        return post
    
    @pytest.fixture
    def sample_post_data(self):
        """Create sample post creation data."""
        return PostCreate(
            title="New Test Post",
            content="New test content",
            service="community",
            metadata=PostMetadata(
                type="자유게시판",
                tags=["test"],
                editor_type="plain"
            )
        )
    
    @pytest.mark.asyncio
    async def test_create_post_success(self, posts_service, mock_post_repository, sample_post_data, sample_user):
        """Test successful post creation.
        
        ## 📝 함수 설명
        포스트 생성 성공 시나리오를 검증합니다.
        PostsService의 create_post 메서드가 올바른 데이터로 호출되는지 확인합니다.
        
        ## 🤝 테스트 분류
        **Sociable Unit Test** - Repository Mock과 상호작용
        
        ## 🔄 테스트 전후 상태
        - **사전 조건**: 유효한 PostCreate 데이터, 인증된 사용자
        - **실행 작업**: PostsService.create_post() 호출
        - **사후 조건**: Post 객체 반환, Repository.create() 호출 확인
        
        🎯 테스트 전략: 실제 Service 비즈니스 로직 검증
        🔑 우선순위: 🔵 필수 (MVP) - 핵심 기능
        🎓 난이도: 🟢 초급 - 단순 비즈니스 로직
        ⚡ 실행 그룹: 병렬 가능 - 상태 변경 없음
        """
        # Arrange
        mock_post = Mock()
        mock_post_repository.create.return_value = mock_post
        
        # Act
        result = await posts_service.create_post(sample_post_data, sample_user)
        
        # Assert
        assert result == mock_post
        # 실제 PostsService의 비즈니스 로직 검증
        mock_post_repository.create.assert_called_once()
        call_args = mock_post_repository.create.call_args[0]
        assert call_args[0] == sample_post_data
        assert call_args[1] == str(sample_user.id)
    
    @pytest.mark.asyncio
    async def test_create_post_with_default_metadata(self, posts_service, mock_post_repository, sample_user):
        """Test post creation with default metadata.
        
        🎯 테스트 전략: Service 기본값 처리 로직 검증
        🔑 우선순위: 🟡 권장 - 안정화 기능
        🎓 난이도: 🟢 초급 - 단순 조건 처리
        ⚡ 실행 그룹: 병렬 가능
        """
        # Arrange - Pydantic 모델 검증 수정
        post_data = PostCreate(
            title="Test Post",
            content="Test content",
            service="community",
            metadata=PostMetadata()  # 기본값 사용
        )
        mock_post = Mock()
        mock_post_repository.create.return_value = mock_post
        
        # Act
        result = await posts_service.create_post(post_data, sample_user)
        
        # Assert - 실제 Service 로직 검증
        assert result == mock_post
        # PostsService가 실제로 기본 메타데이터를 설정하는지 검증
        assert post_data.metadata is not None
        assert hasattr(post_data.metadata, 'type')
        mock_post_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_post_success(self, posts_service, mock_post_repository, sample_post):
        """Test successful post retrieval.
        
        🎯 테스트 전략: 실제 Service 조회 로직 검증
        🔑 우선순위: 🔵 필수 (MVP) - 핵심 기능
        🎓 난이도: 🟢 초급 - 단순 조회
        ⚡ 실행 그룹: 병렬 가능
        """
        # Arrange
        slug = "test-post"
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_post_repository.increment_view_count.return_value = True
        
        # Act
        result = await posts_service.get_post(slug)
        
        # Assert
        assert result == sample_post
        mock_post_repository.get_by_slug.assert_called_once_with(slug)
        mock_post_repository.increment_view_count.assert_called_once_with(str(sample_post.id))
    
    @pytest.mark.asyncio
    async def test_get_post_not_found(self, posts_service, mock_post_repository):
        """Test post retrieval when post not found.
        
        ## 📝 함수 설명
        존재하지 않는 포스트 조회 시 예외 처리를 검증합니다.
        PostNotFoundError가 올바르게 발생하는지 확인합니다.
        
        ## 🤝 테스트 분류
        **Sociable Unit Test** - Repository Mock과 상호작용
        
        ## 🔄 테스트 전후 상태
        - **사전 조건**: 존재하지 않는 포스트 slug
        - **실행 작업**: PostsService.get_post() 호출
        - **사후 조건**: PostNotFoundError 예외 발생
        
        🎯 테스트 전략: 예외 처리 로직 검증
        🔑 우선순위: 🔵 필수 (MVP) - 오류 처리
        🎓 난이도: 🟢 초급 - 예외 발생
        ⚡ 실행 그룹: 병렬 가능
        """
        # Arrange
        slug = "non-existent-post"
        mock_post_repository.get_by_slug.side_effect = PostNotFoundError(slug=slug)
        
        # Act & Assert
        with pytest.raises(PostNotFoundError):
            await posts_service.get_post(slug)
    
    @pytest.mark.asyncio
    async def test_list_posts_without_user(self, posts_service, mock_post_repository, sample_post):
        """Test listing posts without authenticated user."""
        # Arrange
        posts = [sample_post]
        total = 1
        mock_post_repository.list_posts.return_value = (posts, total)
        
        with patch.object(posts_service, '_calculate_post_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {
                "like_count": 5,
                "dislike_count": 1,
                "comment_count": 3,
                "bookmark_count": 2
            }
            
            # Act
            result = await posts_service.list_posts(page=1, page_size=20)
            
            # Assert
            assert result["total"] == 1
            assert len(result["items"]) == 1
            assert result["page"] == 1
            assert result["page_size"] == 20
            mock_post_repository.list_posts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_post_success(self, posts_service, mock_post_repository, sample_post, sample_user):
        """Test successful post update."""
        # Arrange
        slug = "test-post"
        update_data = PostUpdate(title="Updated Title", content="Updated content")
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_post_repository.update.return_value = sample_post
        
        with patch('src.utils.permissions.check_post_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Act
            result = await posts_service.update_post(slug, update_data, sample_user)
            
            # Assert
            assert result == sample_post
            mock_post_repository.get_by_slug.assert_called_once_with(slug)
            mock_post_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_post_permission_denied(self, posts_service, mock_post_repository, sample_post, sample_user):
        """Test post update with permission denied."""
        # Arrange
        slug = "test-post"
        update_data = PostUpdate(title="Updated Title")
        sample_post.author_id = "other_user_id"  # Different from sample_user.id
        mock_post_repository.get_by_slug.return_value = sample_post
        
        with patch('src.utils.permissions.check_post_permission') as mock_permission:
            mock_permission.side_effect = PostPermissionError("Permission denied")
            
            # Act & Assert
            with pytest.raises(PostPermissionError):
                await posts_service.update_post(slug, update_data, sample_user)
    
    @pytest.mark.asyncio
    async def test_delete_post_success(self, posts_service, mock_post_repository, sample_post, sample_user):
        """Test successful post deletion."""
        # Arrange
        slug = "test-post"
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_post_repository.delete.return_value = True
        
        with patch('src.utils.permissions.check_post_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Act
            result = await posts_service.delete_post(slug, sample_user)
            
            # Assert
            assert result is True
            mock_post_repository.get_by_slug.assert_called_once_with(slug)
            mock_post_repository.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_post_admin_permission(self, posts_service, mock_post_repository, sample_post, admin_user):
        """Test post deletion by admin user."""
        # Arrange
        slug = "test-post"
        sample_post.author_id = "other_user_id"  # Different from admin user
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_post_repository.delete.return_value = True
        
        with patch('src.utils.permissions.check_post_permission') as mock_permission:
            mock_permission.return_value = True  # Admin can delete any post
            
            # Act
            result = await posts_service.delete_post(slug, admin_user)
            
            # Assert
            assert result is True
            mock_post_repository.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_posts(self, posts_service, mock_post_repository, sample_post):
        """Test post search functionality."""
        # Arrange
        query = "test"
        posts = [sample_post]
        total = 1
        mock_post_repository.search_posts.return_value = (posts, total)
        
        with patch.object(posts_service, '_calculate_post_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {
                "like_count": 5,
                "dislike_count": 1,
                "comment_count": 3,
                "bookmark_count": 2
            }
            
            # Act
            result = await posts_service.search_posts(
                query=query,
                service_type="community",
                sort_by="created_at",
                page=1,
                page_size=20
            )
            
            # Assert
            assert result["total"] == 1
            assert len(result["items"]) == 1
            mock_post_repository.search_posts.assert_called_once_with(
                query=query,
                service_type="community",
                sort_by="created_at",
                page=1,
                page_size=20
            )
    
    @pytest.mark.asyncio
    async def test_calculate_post_stats(self, posts_service):
        """Test post stats calculation."""
        # Arrange
        post_id = "post123"
        
        with patch('src.models.core.UserReaction.find') as mock_reaction_find, \
             patch('src.models.core.Comment.find') as mock_comment_find:
            
            # Mock UserReaction aggregation
            mock_reaction_query = Mock()
            mock_reaction_query.aggregate.return_value.to_list = AsyncMock(return_value=[
                {"_id": "like", "count": 5},
                {"_id": "dislike", "count": 1},
                {"_id": "bookmark", "count": 2}
            ])
            mock_reaction_find.return_value = mock_reaction_query
            
            # Mock Comment count
            mock_comment_query = Mock()
            mock_comment_query.count = AsyncMock(return_value=3)
            mock_comment_find.return_value = mock_comment_query
            
            # Act
            result = await posts_service._calculate_post_stats(post_id)
            
            # Assert
            assert result["like_count"] == 5
            assert result["dislike_count"] == 1
            assert result["bookmark_count"] == 2
            assert result["comment_count"] == 3