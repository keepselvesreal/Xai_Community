"""Unit tests for comment repository functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from beanie import PydanticObjectId
from nadle_backend.models.core import Comment, CommentCreate, CommentDetail
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.exceptions.comment import CommentNotFoundError, CommentDepthExceededError


class TestCommentRepository:
    """Test comment repository functionality."""
    
    @pytest.fixture
    def comment_repo(self):
        """Create comment repository instance."""
        return CommentRepository()
    
    @pytest.fixture
    def sample_comment_data(self):
        """Create sample comment data."""
        return CommentCreate(
            content="Test comment content",
            parent_comment_id=None
        )
    
    @pytest.fixture
    def sample_comment(self):
        """Create sample comment instance."""
        comment = Mock(spec=Comment)
        comment.id = PydanticObjectId()
        comment.content = "Test comment content"
        comment.author_id = "user123"
        comment.parent_type = "post"
        comment.parent_id = "post123"
        comment.parent_comment_id = None
        comment.status = "active"
        comment.created_at = datetime.utcnow()
        comment.updated_at = datetime.utcnow()
        comment.metadata = {}
        return comment
    
    @pytest.mark.asyncio
    async def test_create_comment_success(self, comment_repo, sample_comment_data):
        """Test successful comment creation."""
        # Arrange
        author_id = "user123"
        parent_id = "post123"
        
        with patch('src.repositories.comment_repository.Comment') as MockComment:
            mock_comment = Mock()
            mock_comment.save = AsyncMock()
            MockComment.return_value = mock_comment
            
            # Act
            result = await comment_repo.create(sample_comment_data, author_id, parent_id)
            
            # Assert
            assert result == mock_comment
            MockComment.assert_called_once()
            mock_comment.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_reply_comment_success(self, comment_repo):
        """Test successful reply comment creation."""
        # Arrange
        comment_data = CommentCreate(
            content="Reply comment",
            parent_comment_id="comment123"
        )
        author_id = "user123"
        parent_id = "post123"
        
        with patch('src.repositories.comment_repository.Comment') as MockComment, \
             patch.object(comment_repo, '_validate_reply_depth', new_callable=AsyncMock) as mock_validate:
            
            mock_comment = Mock()
            mock_comment.save = AsyncMock()
            MockComment.return_value = mock_comment
            
            # Act
            result = await comment_repo.create(comment_data, author_id, parent_id)
            
            # Assert
            assert result == mock_comment
            mock_validate.assert_called_once_with("comment123")
            MockComment.assert_called_once()
            mock_comment.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_reply_depth_exceeded(self, comment_repo):
        """Test reply creation with depth exceeded."""
        # Arrange
        comment_data = CommentCreate(
            content="Deep reply",
            parent_comment_id="comment123"
        )
        author_id = "user123"
        parent_id = "post123"
        
        with patch.object(comment_repo, '_validate_reply_depth', 
                         side_effect=CommentDepthExceededError(max_depth=3)):
            
            # Act & Assert
            with pytest.raises(CommentDepthExceededError):
                await comment_repo.create(comment_data, author_id, parent_id)
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, comment_repo, sample_comment):
        """Test successful comment retrieval by ID."""
        # Arrange
        comment_id = str(sample_comment.id)
        
        with patch('src.repositories.comment_repository.Comment.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_comment
            
            # Act
            result = await comment_repo.get_by_id(comment_id)
            
            # Assert
            assert result == sample_comment
            mock_get.assert_called_once_with(PydanticObjectId(comment_id))
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, comment_repo):
        """Test comment retrieval when comment not found."""
        # Arrange
        comment_id = str(PydanticObjectId())
        
        with patch('src.repositories.comment_repository.Comment.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Act & Assert
            with pytest.raises(CommentNotFoundError):
                await comment_repo.get_by_id(comment_id)
    
    @pytest.mark.asyncio
    async def test_get_by_id_invalid_id(self, comment_repo):
        """Test comment retrieval with invalid ID."""
        # Arrange
        invalid_id = "invalid_id"
        
        # Act & Assert
        with pytest.raises(CommentNotFoundError):
            await comment_repo.get_by_id(invalid_id)
    
    @pytest.mark.asyncio
    async def test_update_comment_success(self, comment_repo, sample_comment):
        """Test successful comment update."""
        # Arrange
        comment_id = str(sample_comment.id)
        new_content = "Updated comment content"
        
        with patch.object(comment_repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [sample_comment, sample_comment]
            sample_comment.update = AsyncMock()
            
            # Act
            result = await comment_repo.update(comment_id, new_content)
            
            # Assert
            assert result == sample_comment
            assert mock_get.call_count == 2
            sample_comment.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_comment_not_found(self, comment_repo):
        """Test comment update when comment not found."""
        # Arrange
        comment_id = str(PydanticObjectId())
        new_content = "Updated content"
        
        with patch.object(comment_repo, 'get_by_id', 
                         side_effect=CommentNotFoundError(comment_id=comment_id)):
            
            # Act & Assert
            with pytest.raises(CommentNotFoundError):
                await comment_repo.update(comment_id, new_content)
    
    @pytest.mark.asyncio
    async def test_delete_comment_success(self, comment_repo, sample_comment):
        """Test successful comment soft deletion."""
        # Arrange
        comment_id = str(sample_comment.id)
        
        with patch.object(comment_repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_comment
            sample_comment.update = AsyncMock()
            
            # Act
            result = await comment_repo.delete(comment_id)
            
            # Assert
            assert result is True
            mock_get.assert_called_once_with(comment_id)
            sample_comment.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_comment_not_found(self, comment_repo):
        """Test comment deletion when comment not found."""
        # Arrange
        comment_id = str(PydanticObjectId())
        
        with patch.object(comment_repo, 'get_by_id', 
                         side_effect=CommentNotFoundError(comment_id=comment_id)):
            
            # Act & Assert
            with pytest.raises(CommentNotFoundError):
                await comment_repo.delete(comment_id)
    
    
