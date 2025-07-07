"""Simplified unit tests for post repository functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from beanie import PydanticObjectId
from nadle_backend.models.core import Post, PostCreate, PostUpdate, PostMetadata
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.exceptions.post import PostNotFoundError


class TestPostRepositorySimple:
    """Test post repository core functionality."""
    
    @pytest.fixture
    def post_repo(self):
        """Create post repository instance."""
        return PostRepository()
    
    @pytest.fixture
    def sample_post_data(self):
        """Create sample post creation data."""
        return PostCreate(
            title="Test Post",
            content="This is test content for the post.",
            service="residential_community",
            metadata=PostMetadata(
                type="자유게시판",
                tags=["test", "sample"],
                editor_type="plain"
            )
        )
    
    @pytest.mark.asyncio
    async def test_create_post_success(self, post_repo, sample_post_data):
        """Test successful post creation."""
        # Arrange
        author_id = "user123"
        
        with patch('nadle_backend.models.core.Post') as MockPost, \
             patch.object(post_repo, '_generate_slug', return_value="test-post"), \
             patch.object(post_repo, '_ensure_unique_slug', new_callable=AsyncMock, return_value="test-post"):
            
            mock_post = Mock()
            mock_post.save = AsyncMock()
            MockPost.return_value = mock_post
            
            # Act
            result = await post_repo.create(sample_post_data, author_id)
            
            # Assert
            assert result == mock_post
            MockPost.assert_called_once()
            mock_post.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, post_repo):
        """Test successful post retrieval by ID."""
        # Arrange
        post_id = str(PydanticObjectId())
        mock_post = Mock()
        
        with patch('src.repositories.post_repository.Post.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_post
            
            # Act
            result = await post_repo.get_by_id(post_id)
            
            # Assert
            assert result == mock_post
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, post_repo):
        """Test post retrieval when post not found."""
        # Arrange
        post_id = str(PydanticObjectId())
        
        with patch('src.repositories.post_repository.Post.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Act & Assert
            with pytest.raises(PostNotFoundError):
                await post_repo.get_by_id(post_id)
    
    def test_generate_slug_basic(self, post_repo):
        """Test basic slug generation."""
        # Act
        result = post_repo._generate_slug("Test Post Title")
        
        # Assert
        assert result == "test-post-title"
    
    def test_generate_slug_with_special_chars(self, post_repo):
        """Test slug generation with special characters."""
        # Act
        result = post_repo._generate_slug("Test! Post@ Title# 123")
        
        # Assert
        assert result == "test-post-title-123"