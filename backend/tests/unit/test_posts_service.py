"""Unit tests for posts service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from nadle_backend.models.core import User, Post, PostCreate, PostUpdate, PostResponse, PostMetadata
from nadle_backend.services.posts_service import PostsService
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.exceptions.user import UserNotFoundError
from nadle_backend.exceptions.post import PostNotFoundError, PostPermissionError


class TestPostsService:
    """Test suite for PostsService."""
    
    @pytest.fixture
    def mock_post_repository(self):
        """Mock post repository."""
        return AsyncMock(spec=PostRepository)
    
    @pytest.fixture
    def posts_service(self, mock_post_repository):
        """Posts service instance with mocked dependencies."""
        return PostsService(post_repository=mock_post_repository)
    
    @pytest.fixture
    def sample_user(self):
        """Sample user fixture."""
        user = Mock()
        user.id = "507f1f77bcf86cd799439011"
        user.email = "john@example.com"
        user.user_handle = "johndoe"
        user.password_hash = "hashed_password"
        user.status = "active"
        user.created_at = datetime.utcnow()
        user.is_admin = False
        return user
    
    @pytest.fixture
    def sample_post_create(self):
        """Sample post creation data."""
        return PostCreate(
            title="Test Post",
            content="This is a test post content",
            service="residential_community",
            metadata=PostMetadata(
                tags=["test", "python"],
                editor_type="plain"
            )
        )
    
    @pytest.fixture
    def sample_post(self):
        """Sample post fixture."""
        post = Mock()
        post.id = "507f1f77bcf86cd799439012"
        post.title = "Test Post"
        post.content = "This is a test post content"
        post.service = "X"
        post.tags = ["test", "python"]
        post.slug = "test-post"
        post.author_id = "507f1f77bcf86cd799439011"
        post.status = "published"
        post.created_at = datetime.utcnow()
        post.updated_at = datetime.utcnow()
        post.view_count = 0
        post.like_count = 0
        post.comment_count = 0
        post.share_count = 0
        
        # Mock the model_dump method
        post.model_dump.return_value = {
            "id": "507f1f77bcf86cd799439012",
            "title": "Test Post",
            "content": "This is a test post content",
            "service": "X",
            "tags": ["test", "python"],
            "slug": "test-post",
            "author_id": "507f1f77bcf86cd799439011",
            "status": "published",
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0
        }
        return post
    
    async def test_create_post_with_auth(self, posts_service, mock_post_repository, sample_user, sample_post_create, sample_post):
        """Test creating a post with authenticated user."""
        # Arrange
        mock_post_repository.create.return_value = sample_post
        
        # Act
        result = await posts_service.create_post(sample_post_create, sample_user)
        
        # Assert
        assert result is not None
        assert result.title == "Test Post"
        assert result.author_id == sample_user.id
        assert result.slug == "test-post"
        assert result.status == "published"
        assert result.view_count == 0
        assert result.like_count == 0
        
        # Verify repository was called with correct parameters
        mock_post_repository.create.assert_called_once()
        create_call_args = mock_post_repository.create.call_args[0]
        assert create_call_args[0].title == sample_post_create.title
        assert create_call_args[0].content == sample_post_create.content
        assert create_call_args[1] == sample_user.id  # author_id
    
    async def test_get_post(self, posts_service, mock_post_repository, sample_post):
        """Test retrieving a post by slug."""
        # Arrange
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_post_repository.increment_view_count.return_value = True
        
        # Act
        result = await posts_service.get_post("test-post")
        
        # Assert
        assert result is not None
        assert result.slug == "test-post"
        assert result.title == "Test Post"
        
        # Verify repository calls
        mock_post_repository.get_by_slug.assert_called_once_with("test-post")
        mock_post_repository.increment_view_count.assert_called_once_with(sample_post.id)
    
    async def test_list_posts_with_user_data(self, posts_service, mock_post_repository, sample_post, sample_user):
        """Test listing posts with user-specific data."""
        # Arrange
        from datetime import datetime
        posts_data = [{
            "_id": "507f1f77bcf86cd799439011",
            "title": "Test Post",
            "content": "Test content",
            "slug": "test-post",
            "author_id": "507f1f77bcf86cd799439012",
            "service": "residential_community",
            "metadata": {"type": "board"},
            "status": "published",
            "created_at": datetime(2023, 1, 1),
            "updated_at": datetime(2023, 1, 1)
        }]
        mock_post_repository.list_posts_optimized.return_value = (posts_data, 1)
        
        # Act
        result = await posts_service.list_posts(page=1, page_size=20, current_user=sample_user)
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 1
        assert result["total"] == 1
        
        # Verify repository calls
        mock_post_repository.list_posts_optimized.assert_called_once()
    
    async def test_update_post_with_permission(self, posts_service, mock_post_repository, sample_post, sample_user):
        """Test updating a post with proper permissions."""
        # Arrange
        update_data = PostUpdate(
            title="Updated Test Post",
            content="Updated content"
        )
        mock_post_repository.get_by_slug.return_value = sample_post
        updated_post = sample_post.copy()
        updated_post.title = "Updated Test Post"
        updated_post.content = "Updated content"
        mock_post_repository.update.return_value = updated_post
        
        # Act
        result = await posts_service.update_post("test-post", update_data, sample_user)
        
        # Assert
        assert result is not None
        assert result.title == "Updated Test Post"
        assert result.content == "Updated content"
        
        # Verify repository calls
        mock_post_repository.get_by_slug.assert_called_once_with("test-post")
        mock_post_repository.update.assert_called_once()
    
    async def test_delete_post_with_permission(self, posts_service, mock_post_repository, sample_post, sample_user):
        """Test deleting a post with proper permissions."""
        # Arrange
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_post_repository.delete.return_value = True
        
        # Act
        result = await posts_service.delete_post("test-post", sample_user)
        
        # Assert
        assert result is True
        
        # Verify repository calls
        mock_post_repository.get_by_slug.assert_called_once_with("test-post")
        mock_post_repository.delete.assert_called_once_with(sample_post.id)
    
    async def test_search_posts(self, posts_service, mock_post_repository, sample_post):
        """Test searching posts with filters."""
        # Arrange
        posts_list = [sample_post]
        mock_post_repository.search_posts.return_value = (posts_list, 1)
        
        # Act
        result = await posts_service.search_posts(
            query="test",
            service_type="residential_community",
            sort_by="created_at",
            page=1,
            page_size=20
        )
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 1
        assert result["total"] == 1
        
        # Verify repository calls
        mock_post_repository.search_posts.assert_called_once_with(
            query="test",
            service_type="residential_community",
            metadata_type=None,
            sort_by="created_at",
            page=1,
            page_size=20
        )
    
    # 새로운 문의/신고 타입들에 대한 TDD 테스트
    async def test_create_moving_services_inquiry(self, posts_service, mock_post_repository, sample_user):
        """Test creating moving services inquiry post."""
        # Arrange
        inquiry_data = PostCreate(
            title="입주 서비스 업체 등록 문의",
            content='{"content": "저희 업체를 등록하고 싶습니다", "contact": "010-1234-5678", "website_url": "https://example.com"}',
            service="residential_community",
            metadata=PostMetadata(
                type="moving-services-register-inquiry",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.id = "507f1f77bcf86cd799439013"
        created_post.title = inquiry_data.title
        created_post.content = inquiry_data.content
        created_post.metadata = inquiry_data.metadata
        created_post.author_id = sample_user.id
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(inquiry_data, sample_user)
        
        # Assert
        assert result is not None
        assert result.title == "입주 서비스 업체 등록 문의"
        assert '"contact": "010-1234-5678"' in result.content
        assert '"website_url": "https://example.com"' in result.content
        assert result.metadata.type == "moving-services-register-inquiry"
        
        # Verify repository was called
        mock_post_repository.create.assert_called_once()
    
    async def test_create_expert_tips_inquiry(self, posts_service, mock_post_repository, sample_user):
        """Test creating expert tips inquiry post."""
        # Arrange
        inquiry_data = PostCreate(
            title="전문가 꿀정보 등록 문의",
            content='{"content": "전문가로 등록하고 싶습니다", "contact": "010-9876-5432", "website_url": "https://expert.com"}',
            service="residential_community",
            metadata=PostMetadata(
                type="expert-tips-register-inquiry",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.id = "507f1f77bcf86cd799439014"
        created_post.title = inquiry_data.title
        created_post.content = inquiry_data.content
        created_post.metadata = inquiry_data.metadata
        created_post.author_id = sample_user.id
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(inquiry_data, sample_user)
        
        # Assert
        assert result is not None
        assert result.title == "전문가 꿀정보 등록 문의"
        assert '"contact": "010-9876-5432"' in result.content
        assert '"website_url": "https://expert.com"' in result.content
        assert result.metadata.type == "expert-tips-register-inquiry"
        
        # Verify repository was called
        mock_post_repository.create.assert_called_once()
    
    async def test_create_suggestions(self, posts_service, mock_post_repository, sample_user):
        """Test creating suggestions post."""
        # Arrange
        suggestion_data = PostCreate(
            title="건의사항",
            content='{"content": "앱에 다크모드를 추가해주세요"}',
            service="residential_community",
            metadata=PostMetadata(
                type="suggestions",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.id = "507f1f77bcf86cd799439015"
        created_post.title = suggestion_data.title
        created_post.content = suggestion_data.content
        created_post.metadata = suggestion_data.metadata
        created_post.author_id = sample_user.id
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(suggestion_data, sample_user)
        
        # Assert
        assert result is not None
        assert result.title == "건의사항"
        assert '"content": "앱에 다크모드를 추가해주세요"' in result.content
        assert result.metadata.type == "suggestions"
        
        # Verify repository was called
        mock_post_repository.create.assert_called_once()
    
    async def test_create_report(self, posts_service, mock_post_repository, sample_user):
        """Test creating report post."""
        # Arrange
        report_data = PostCreate(
            title="신고",
            content='{"content": "부적절한 게시물을 신고합니다"}',
            service="residential_community",
            metadata=PostMetadata(
                type="report",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.id = "507f1f77bcf86cd799439016"
        created_post.title = report_data.title
        created_post.content = report_data.content
        created_post.metadata = report_data.metadata
        created_post.author_id = sample_user.id
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(report_data, sample_user)
        
        # Assert
        assert result is not None
        assert result.title == "신고"
        assert '"content": "부적절한 게시물을 신고합니다"' in result.content
        assert result.metadata.type == "report"
        
        # Verify repository was called
        mock_post_repository.create.assert_called_once()
    
    async def test_create_inquiry_anonymous_user(self, posts_service, mock_post_repository):
        """Test creating inquiry post with anonymous user (None user)."""
        # Arrange
        inquiry_data = PostCreate(
            title="익명 문의",
            content='{"content": "비회원 문의입니다", "contact": "010-1111-2222", "website_url": "https://test.com"}',
            service="residential_community",
            metadata=PostMetadata(
                type="moving-services-register-inquiry",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.id = "507f1f77bcf86cd799439017"
        created_post.title = inquiry_data.title
        created_post.content = inquiry_data.content
        created_post.metadata = inquiry_data.metadata
        # 익명 사용자의 경우 임시 ID가 생성되어야 함
        created_post.author_id = "anonymous_507f1f77bcf86cd799439017"
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(inquiry_data, None)  # None user for anonymous
        
        # Assert
        assert result is not None
        assert result.title == "익명 문의"
        assert result.author_id.startswith("anonymous_")
        assert len(result.author_id) > 10  # Should be a valid anonymous ID
        
        # Verify repository was called
        mock_post_repository.create.assert_called_once()
    
    async def test_anonymous_author_id_generation(self, posts_service, mock_post_repository):
        """Test that anonymous author IDs are properly generated."""
        # Arrange
        inquiry_data = PostCreate(
            title="테스트 문의",
            content='{"content": "테스트 내용"}',
            service="residential_community",
            metadata=PostMetadata(
                type="suggestions",
                editor_type="plain"
            )
        )
        
        # Mock the create method to capture the author_id being passed
        captured_author_ids = []
        def capture_author_id(post_data, author_id):
            captured_author_ids.append(author_id)
            # Return a mock post object
            mock_post = Mock()
            mock_post.author_id = author_id
            return mock_post
        
        mock_post_repository.create.side_effect = capture_author_id
        
        # Act
        await posts_service.create_post(inquiry_data, None)
        
        # Assert
        assert len(captured_author_ids) == 1
        author_id = captured_author_ids[0]
        assert author_id.startswith("anonymous_")
        # 익명 ID는 'anonymous_' + UUID 형태여야 함
        anonymous_part = author_id.replace("anonymous_", "")
        assert len(anonymous_part) >= 8  # UUID 형태의 최소 길이
    
    async def test_content_field_json_validation_for_inquiries(self, posts_service, mock_post_repository, sample_user):
        """Test that inquiry posts have proper JSON structure in content field."""
        # Arrange - Valid JSON content for inquiry
        valid_inquiry = PostCreate(
            title="유효한 문의",
            content='{"content": "문의 내용", "contact": "010-1234-5678", "website_url": "https://example.com"}',
            service="residential_community",
            metadata=PostMetadata(
                type="moving-services-register-inquiry",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.content = valid_inquiry.content
        created_post.metadata = valid_inquiry.metadata
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(valid_inquiry, sample_user)
        
        # Assert
        import json
        content_data = json.loads(result.content)
        assert "content" in content_data
        assert "contact" in content_data
        assert "website_url" in content_data
        assert content_data["content"] == "문의 내용"
        assert content_data["contact"] == "010-1234-5678"
        assert content_data["website_url"] == "https://example.com"
    
    async def test_content_field_json_validation_for_suggestions_and_reports(self, posts_service, mock_post_repository, sample_user):
        """Test that suggestions and reports have simpler JSON structure in content field."""
        # Arrange - Valid JSON content for suggestions/reports
        valid_suggestion = PostCreate(
            title="유효한 건의",
            content='{"content": "건의 내용입니다"}',
            service="residential_community",
            metadata=PostMetadata(
                type="suggestions",
                editor_type="plain"
            )
        )
        
        created_post = Mock()
        created_post.content = valid_suggestion.content
        created_post.metadata = valid_suggestion.metadata
        mock_post_repository.create.return_value = created_post
        
        # Act
        result = await posts_service.create_post(valid_suggestion, sample_user)
        
        # Assert
        import json
        content_data = json.loads(result.content)
        assert "content" in content_data
        assert content_data["content"] == "건의 내용입니다"
        # 건의/신고는 contact, website_url 필드가 없어야 함
        assert "contact" not in content_data
        assert "website_url" not in content_data