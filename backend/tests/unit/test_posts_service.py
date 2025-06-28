"""Unit tests for posts service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from nadle_backend.models.core import User, Post, PostCreate, PostUpdate, PostResponse
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
            service="X",
            tags=["test", "python"]
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
        posts_list = [sample_post]
        mock_post_repository.list_posts.return_value = (posts_list, 1)
        
        # Act
        result = await posts_service.list_posts(page=1, page_size=20, current_user=sample_user)
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 1
        assert result["total"] == 1
        
        # Verify repository calls
        mock_post_repository.list_posts.assert_called_once()
    
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
            service_type="X",
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
            service_type="X",
            sort_by="created_at",
            page=1,
            page_size=20
        )