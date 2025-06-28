"""Unit tests for comments service."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from nadle_backend.services.comments_service import CommentsService
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.models.core import Comment, CommentCreate, CommentDetail, User, Post
from nadle_backend.exceptions.comment import CommentNotFoundError, CommentPermissionError, CommentValidationError
from nadle_backend.exceptions.post import PostNotFoundError


@pytest.fixture
def mock_comment_repo():
    """Create mock comment repository."""
    return AsyncMock(spec=CommentRepository)


@pytest.fixture
def mock_post_repo():
    """Create mock post repository."""
    return AsyncMock(spec=PostRepository)


@pytest.fixture
def comments_service(mock_comment_repo, mock_post_repo):
    """Create comments service with mock repositories."""
    return CommentsService(mock_comment_repo, mock_post_repo)


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = Mock(spec=User)
    user.id = "user123"
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = Mock(spec=User)
    user.id = "admin123"
    user.is_admin = True
    return user


@pytest.fixture
def mock_post():
    """Create mock post."""
    post = Mock(spec=Post)
    post.id = "post123"
    post.slug = "test-post"
    post.title = "Test Post"
    post.author_id = "author123"
    return post


@pytest.fixture
def mock_comment():
    """Create mock comment."""
    comment = Mock(spec=Comment)
    comment.id = "comment123"
    comment.content = "Test comment content"
    comment.author_id = "user123"
    comment.parent_id = "post123"
    comment.parent_comment_id = None
    comment.status = "active"
    comment.like_count = 0
    comment.dislike_count = 0
    comment.reply_count = 0
    comment.created_at = datetime.utcnow()
    comment.updated_at = datetime.utcnow()
    return comment


@pytest.mark.asyncio
async def test_create_comment_with_auth(comments_service, mock_comment_repo, mock_post_repo, mock_user, mock_post):
    """Test creating a comment with authentication - Subtask 1."""
    # Arrange
    comment_data = CommentCreate(content="This is a test comment")
    post_slug = "test-post"
    
    # Create mock comment with matching content
    mock_comment = Mock(spec=Comment)
    mock_comment.id = "comment123"
    mock_comment.content = "This is a test comment"  # Match the input
    mock_comment.author_id = "user123"
    mock_comment.parent_id = "post123"
    mock_comment.parent_comment_id = None
    mock_comment.status = "active"
    mock_comment.like_count = 0
    mock_comment.dislike_count = 0
    mock_comment.reply_count = 0
    mock_comment.created_at = datetime.utcnow()
    mock_comment.updated_at = datetime.utcnow()
    
    # Mock repository calls
    mock_post_repo.get_by_slug.return_value = mock_post
    mock_comment_repo.create.return_value = mock_comment
    
    # Mock the post comment count increment (using AsyncMock for async operations)
    mock_increment = AsyncMock()
    comments_service._increment_post_comment_count = mock_increment
    
    # Act
    result = await comments_service.create_comment(post_slug, comment_data, mock_user)
    
    # Assert
    assert isinstance(result, CommentDetail)
    assert result.content == "This is a test comment"
    assert result.author_id == "user123"
    
    # Verify repository calls
    mock_post_repo.get_by_slug.assert_called_once_with(post_slug)
    mock_comment_repo.create.assert_called_once()
    
    # Verify comment creation was called with correct parameters
    create_call = mock_comment_repo.create.call_args
    assert create_call is not None
    
    # Check keyword arguments
    kwargs = create_call.kwargs if hasattr(create_call, 'kwargs') else create_call[1]
    assert kwargs["author_id"] == str(mock_user.id)
    assert kwargs["parent_id"] == str(mock_post.id)
    
    # Verify post comment count increment
    mock_increment.assert_called_once_with(str(mock_post.id))


@pytest.mark.asyncio
async def test_get_comments_with_user_data(comments_service, mock_comment_repo, mock_post_repo, mock_user, mock_post, mock_comment):
    """Test getting comments with user data - Subtask 2."""
    # Arrange
    post_slug = "test-post"
    page = 1
    page_size = 20
    
    # Create mock comment structure with replies
    mock_reply = Mock(spec=Comment)
    mock_reply.id = "reply123"
    mock_reply.content = "Reply content"
    mock_reply.author_id = "user456"
    mock_reply.parent_comment_id = "comment123"
    mock_reply.status = "active"
    mock_reply.like_count = 0
    mock_reply.dislike_count = 0
    mock_reply.reply_count = 0
    mock_reply.created_at = datetime.utcnow()
    mock_reply.updated_at = datetime.utcnow()
    
    comments_with_replies = [
        {
            "comment": mock_comment,
            "replies": [mock_reply]
        }
    ]
    total_count = 1
    
    # Mock repository calls
    mock_post_repo.get_by_slug.return_value = mock_post
    mock_comment_repo.get_comments_with_replies.return_value = (comments_with_replies, total_count)
    
    # Act
    result, total = await comments_service.get_comments_with_user_data(
        post_slug, page, page_size, "created_at", mock_user
    )
    
    # Assert
    assert len(result) == 1
    assert total == 1
    assert isinstance(result[0], CommentDetail)
    assert result[0].content == "Test comment content"
    assert result[0].author_id == "user123"
    assert result[0].replies is not None
    assert len(result[0].replies) == 1
    assert result[0].replies[0].content == "Reply content"
    
    # Verify repository calls
    mock_post_repo.get_by_slug.assert_called_once_with(post_slug)
    mock_comment_repo.get_comments_with_replies.assert_called_once_with(
        post_id=str(mock_post.id),
        page=page,
        page_size=page_size,
        status="active"
    )


@pytest.mark.asyncio
async def test_reply_comments(comments_service, mock_comment_repo, mock_post_repo, mock_user, mock_post, mock_comment):
    """Test reply comments functionality - Subtask 3."""
    # Arrange
    post_slug = "test-post"
    parent_comment_id = "comment123"
    reply_data = CommentCreate(content="This is a reply")
    
    # Create mock reply comment
    mock_reply = Mock(spec=Comment)
    mock_reply.id = "reply123"
    mock_reply.content = "This is a reply"
    mock_reply.author_id = "user123"
    mock_reply.parent_id = "post123"
    mock_reply.parent_comment_id = parent_comment_id
    mock_reply.status = "active"
    mock_reply.like_count = 0
    mock_reply.dislike_count = 0
    mock_reply.reply_count = 0
    mock_reply.created_at = datetime.utcnow()
    mock_reply.updated_at = datetime.utcnow()
    
    # Mock repository calls
    mock_post_repo.get_by_slug.return_value = mock_post
    mock_comment_repo.get_by_id.return_value = mock_comment  # Parent comment exists
    mock_comment_repo.create.return_value = mock_reply
    mock_comment_repo.increment_reply_count.return_value = True
    
    # Mock the post comment count increment
    mock_increment = AsyncMock()
    comments_service._increment_post_comment_count = mock_increment
    
    # Act
    result = await comments_service.create_reply(post_slug, parent_comment_id, reply_data, mock_user)
    
    # Assert
    assert isinstance(result, CommentDetail)
    assert result.content == "This is a reply"
    assert result.author_id == "user123"
    assert result.parent_comment_id == parent_comment_id
    
    # Verify repository calls
    mock_post_repo.get_by_slug.assert_called_once_with(post_slug)
    mock_comment_repo.get_by_id.assert_called_once_with(parent_comment_id)
    mock_comment_repo.create.assert_called_once()
    mock_comment_repo.increment_reply_count.assert_called_once_with(parent_comment_id)
    mock_increment.assert_called_once_with(str(mock_post.id))
    
    # Verify that create was called (the service logic validates the parent_comment_id is set)
    create_call = mock_comment_repo.create.call_args
    assert create_call is not None


@pytest.mark.asyncio
async def test_update_comment_with_permission(comments_service, mock_comment_repo, mock_user, mock_comment):
    """Test updating comment with permission check - Subtask 4."""
    # Arrange
    comment_id = "comment123"
    new_content = "Updated comment content"
    
    # Mock repository calls
    mock_comment_repo.get_by_id.return_value = mock_comment
    mock_comment_repo.update.return_value = mock_comment
    
    # Act
    result = await comments_service.update_comment_with_permission(comment_id, new_content, mock_user)
    
    # Assert
    assert isinstance(result, CommentDetail)
    assert result.content == "Test comment content"  # Original content from mock
    assert result.author_id == "user123"
    
    # Verify repository calls
    mock_comment_repo.get_by_id.assert_called_once_with(comment_id)
    mock_comment_repo.update.assert_called_once_with(comment_id, new_content)


@pytest.mark.asyncio
async def test_update_comment_permission_denied(comments_service, mock_comment_repo, mock_user):
    """Test updating comment with permission denied."""
    # Arrange
    comment_id = "comment123"
    new_content = "Updated content"
    
    # Create comment owned by different user
    other_comment = Mock(spec=Comment)
    other_comment.id = "comment123"
    other_comment.author_id = "other_user"
    other_comment.content = "Original content"
    other_comment.parent_comment_id = None
    other_comment.like_count = 0
    other_comment.dislike_count = 0
    other_comment.reply_count = 0
    
    mock_comment_repo.get_by_id.return_value = other_comment
    
    # Act & Assert
    with pytest.raises(CommentPermissionError) as exc_info:
        await comments_service.update_comment_with_permission(comment_id, new_content, mock_user)
    
    assert exc_info.value.action == "update"
    assert exc_info.value.comment_id == comment_id


@pytest.mark.asyncio
async def test_delete_comment_with_permission(comments_service, mock_comment_repo, mock_post_repo, mock_user, mock_comment, mock_post):
    """Test deleting comment with permission check - Subtask 4."""
    # Arrange
    comment_id = "comment123"
    
    # Mock repository calls
    mock_comment_repo.get_by_id.return_value = mock_comment
    mock_post_repo.get_by_id.return_value = mock_post
    mock_comment_repo.delete.return_value = True
    
    # Mock the post comment count decrement
    mock_decrement = AsyncMock()
    comments_service._decrement_post_comment_count = mock_decrement
    
    # Act
    result = await comments_service.delete_comment_with_permission(comment_id, mock_user)
    
    # Assert
    assert result is True
    
    # Verify repository calls
    mock_comment_repo.get_by_id.assert_called_once_with(comment_id)
    mock_post_repo.get_by_id.assert_called_once_with(mock_comment.parent_id)
    mock_comment_repo.delete.assert_called_once_with(comment_id)
    mock_decrement.assert_called_once_with(str(mock_post.id))


@pytest.mark.asyncio
async def test_delete_comment_permission_denied(comments_service, mock_comment_repo, mock_user):
    """Test deleting comment with permission denied."""
    # Arrange
    comment_id = "comment123"
    
    # Create comment owned by different user
    other_comment = Mock(spec=Comment)
    other_comment.id = "comment123"
    other_comment.author_id = "other_user"
    other_comment.parent_comment_id = None
    other_comment.like_count = 0
    other_comment.dislike_count = 0
    other_comment.reply_count = 0
    
    mock_comment_repo.get_by_id.return_value = other_comment
    
    # Act & Assert
    with pytest.raises(CommentPermissionError) as exc_info:
        await comments_service.delete_comment_with_permission(comment_id, mock_user)
    
    assert exc_info.value.action == "delete"
    assert exc_info.value.comment_id == comment_id


@pytest.mark.asyncio
async def test_admin_can_update_any_comment(comments_service, mock_comment_repo, mock_admin_user):
    """Test that admin can update any comment."""
    # Arrange
    comment_id = "comment123"
    new_content = "Admin updated content"
    
    # Create comment owned by different user
    other_comment = Mock(spec=Comment)
    other_comment.id = "comment123"
    other_comment.author_id = "other_user"
    other_comment.content = "Original content"
    other_comment.parent_comment_id = None
    other_comment.status = "active"
    other_comment.like_count = 0
    other_comment.dislike_count = 0
    other_comment.reply_count = 0
    other_comment.created_at = "2024-01-01T00:00:00"
    other_comment.updated_at = "2024-01-01T00:00:00"
    
    mock_comment_repo.get_by_id.return_value = other_comment
    mock_comment_repo.update.return_value = other_comment
    
    # Act
    result = await comments_service.update_comment_with_permission(comment_id, new_content, mock_admin_user)
    
    # Assert
    assert isinstance(result, CommentDetail)
    mock_comment_repo.update.assert_called_once_with(comment_id, new_content)


@pytest.mark.asyncio
async def test_admin_can_delete_any_comment(comments_service, mock_comment_repo, mock_post_repo, mock_admin_user, mock_post):
    """Test that admin can delete any comment."""
    # Arrange
    comment_id = "comment123"
    
    # Create comment owned by different user
    other_comment = Mock(spec=Comment)
    other_comment.id = "comment123"
    other_comment.author_id = "other_user"
    other_comment.parent_id = "post123"
    other_comment.parent_comment_id = None
    other_comment.like_count = 0
    other_comment.dislike_count = 0
    other_comment.reply_count = 0
    
    mock_comment_repo.get_by_id.return_value = other_comment
    mock_post_repo.get_by_id.return_value = mock_post
    mock_comment_repo.delete.return_value = True
    
    # Mock the post comment count decrement
    mock_decrement = AsyncMock()
    comments_service._decrement_post_comment_count = mock_decrement
    
    # Act
    result = await comments_service.delete_comment_with_permission(comment_id, mock_admin_user)
    
    # Assert
    assert result is True
    mock_comment_repo.delete.assert_called_once_with(comment_id)


@pytest.mark.asyncio
async def test_create_comment_validation_error(comments_service, mock_user):
    """Test comment creation with validation error."""
    # Arrange - This should raise ValidationError at Pydantic level
    # since empty content violates min_length=1 constraint
    with pytest.raises(ValueError):  # Pydantic raises ValueError for validation
        comment_data = CommentCreate(content="")  # Empty content


@pytest.mark.asyncio
async def test_create_comment_content_too_long(comments_service, mock_user):
    """Test comment creation with content too long."""
    # Arrange - This should raise ValidationError at Pydantic level
    # since long content violates max_length=1000 constraint
    long_content = "x" * 1001  # Exceeds 1000 character limit
    with pytest.raises(ValueError):  # Pydantic raises ValueError for validation
        comment_data = CommentCreate(content=long_content)


@pytest.mark.asyncio
async def test_create_comment_post_not_found(comments_service, mock_post_repo, mock_user):
    """Test comment creation when post not found."""
    # Arrange
    comment_data = CommentCreate(content="Test comment")
    post_slug = "nonexistent-post"
    
    mock_post_repo.get_by_slug.side_effect = PostNotFoundError(slug=post_slug)
    
    # Act & Assert
    with pytest.raises(PostNotFoundError):
        await comments_service.create_comment(post_slug, comment_data, mock_user)