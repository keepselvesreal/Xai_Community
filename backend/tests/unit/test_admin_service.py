"""Unit tests for admin service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from nadle_backend.models.core import User, Post, PostCreate, PostUpdate, PostMetadata
from nadle_backend.services.admin_service import AdminService
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.exceptions.post import PostNotFoundError
from nadle_backend.exceptions.user import UserNotFoundError


class TestAdminService:
    """Test suite for AdminService."""
    
    @pytest.fixture
    def mock_post_repository(self):
        """Mock post repository."""
        return AsyncMock(spec=PostRepository)
    
    @pytest.fixture
    def admin_service(self, mock_post_repository):
        """Admin service instance with mocked dependencies."""
        return AdminService(post_repository=mock_post_repository)
    
    @pytest.fixture
    def sample_admin_user(self):
        """Sample admin user fixture."""
        user = Mock()
        user.id = "507f1f77bcf86cd799439011"
        user.email = "admin@example.com"
        user.user_handle = "admin"
        user.is_admin = True
        user.status = "active"
        user.created_at = datetime.utcnow()
        return user
    
    @pytest.fixture
    def sample_inquiry_post(self):
        """Sample inquiry post fixture."""
        post = Mock()
        post.id = "507f1f77bcf86cd799439012"
        post.title = "입주 서비스 업체 등록 문의"
        post.content = '{"content": "저희 업체를 등록하고 싶습니다", "contact": "010-1234-5678", "website_url": "https://example.com"}'
        post.slug = "inquiry-test-slug"
        post.author_id = "anonymous_1234567890abcdef"
        post.status = "pending"
        post.service = "residential_community"
        post.metadata = Mock()
        post.metadata.type = "moving-services-register-inquiry"
        post.created_at = datetime.utcnow()
        post.updated_at = datetime.utcnow()
        post.resolved_at = None
        return post

    async def test_get_inquiries_list(self, admin_service, mock_post_repository, sample_admin_user):
        """Test getting list of inquiries for admin."""
        # Arrange
        inquiries_data = [
            {
                "_id": "507f1f77bcf86cd799439012",
                "title": "입주 서비스 업체 등록 문의",
                "content": '{"content": "저희 업체를 등록하고 싶습니다"}',
                "slug": "inquiry-1",
                "author_id": "anonymous_1234",
                "status": "pending",
                "service": "residential_community",
                "metadata": {"type": "moving-services-register-inquiry"},
                "created_at": datetime(2023, 1, 1),
                "updated_at": datetime(2023, 1, 1),
                "resolved_at": None
            }
        ]
        mock_post_repository.get_inquiries_list.return_value = (inquiries_data, 1)
        
        # Act
        result = await admin_service.get_inquiries_list(
            current_user=sample_admin_user,
            page=1,
            page_size=20,
            inquiry_type="moving-services-register-inquiry",
            status="pending"
        )
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 1
        assert result["total"] == 1
        assert result["items"][0]["status"] == "pending"
        assert result["items"][0]["metadata"]["type"] == "moving-services-register-inquiry"
        
        # Verify repository calls
        mock_post_repository.get_inquiries_list.assert_called_once_with(
            inquiry_type="moving-services-register-inquiry",
            status="pending",
            page=1,
            page_size=20
        )

    async def test_update_inquiry_status_to_resolved(self, admin_service, mock_post_repository, sample_admin_user, sample_inquiry_post):
        """Test updating inquiry status from pending to resolved."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_inquiry_post
        
        resolved_post = Mock()
        resolved_post.id = sample_inquiry_post.id
        resolved_post.status = "resolved"
        resolved_post.resolved_at = datetime.utcnow()
        mock_post_repository.update_status.return_value = resolved_post
        
        # Act
        result = await admin_service.update_inquiry_status(
            inquiry_id=sample_inquiry_post.id,
            new_status="resolved",
            current_user=sample_admin_user
        )
        
        # Assert
        assert result is not None
        assert result.status == "resolved"
        assert result.resolved_at is not None
        
        # Verify repository calls
        mock_post_repository.get_by_id.assert_called_once_with(sample_inquiry_post.id)
        mock_post_repository.update_status.assert_called_once()

    async def test_update_inquiry_status_to_rejected(self, admin_service, mock_post_repository, sample_admin_user, sample_inquiry_post):
        """Test updating inquiry status from pending to rejected."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_inquiry_post
        
        rejected_post = Mock()
        rejected_post.id = sample_inquiry_post.id
        rejected_post.status = "rejected"
        rejected_post.resolved_at = datetime.utcnow()
        mock_post_repository.update_status.return_value = rejected_post
        
        # Act
        result = await admin_service.update_inquiry_status(
            inquiry_id=sample_inquiry_post.id,
            new_status="rejected",
            current_user=sample_admin_user
        )
        
        # Assert
        assert result is not None
        assert result.status == "rejected"
        assert result.resolved_at is not None
        
        # Verify repository calls
        mock_post_repository.get_by_id.assert_called_once_with(sample_inquiry_post.id)
        mock_post_repository.update_status.assert_called_once()

    async def test_update_inquiry_status_invalid_transition(self, admin_service, mock_post_repository, sample_admin_user, sample_inquiry_post):
        """Test invalid status transition."""
        # Arrange
        sample_inquiry_post.status = "resolved"  # Already resolved
        mock_post_repository.get_by_id.return_value = sample_inquiry_post
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot transition from status"):
            await admin_service.update_inquiry_status(
                inquiry_id=sample_inquiry_post.id,
                new_status="pending",  # Cannot go back to pending
                current_user=sample_admin_user
            )

    async def test_update_inquiry_status_non_admin_user(self, admin_service, mock_post_repository, sample_inquiry_post):
        """Test that non-admin user cannot update inquiry status."""
        # Arrange
        non_admin_user = Mock()
        non_admin_user.is_admin = False
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Admin privileges required"):
            await admin_service.update_inquiry_status(
                inquiry_id=sample_inquiry_post.id,
                new_status="resolved",
                current_user=non_admin_user
            )

    async def test_get_inquiry_by_id(self, admin_service, mock_post_repository, sample_admin_user, sample_inquiry_post):
        """Test getting a specific inquiry by ID."""
        # Arrange
        mock_post_repository.get_by_id.return_value = sample_inquiry_post
        
        # Act
        result = await admin_service.get_inquiry_by_id(
            inquiry_id=sample_inquiry_post.id,
            current_user=sample_admin_user
        )
        
        # Assert
        assert result is not None
        assert result.id == sample_inquiry_post.id
        assert result.metadata.type == "moving-services-register-inquiry"
        assert result.status == "pending"
        
        # Verify repository calls
        mock_post_repository.get_by_id.assert_called_once_with(sample_inquiry_post.id)

    async def test_get_inquiry_by_id_not_found(self, admin_service, mock_post_repository, sample_admin_user):
        """Test getting non-existent inquiry."""
        # Arrange
        mock_post_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(PostNotFoundError):
            await admin_service.get_inquiry_by_id(
                inquiry_id="nonexistent_id",
                current_user=sample_admin_user
            )

    async def test_get_all_posts_for_admin(self, admin_service, mock_post_repository, sample_admin_user):
        """Test getting all posts including archived and deleted ones for admin."""
        # Arrange
        posts_data = [
            {
                "_id": "507f1f77bcf86cd799439013",
                "title": "일반 게시글",
                "content": "일반 게시글 내용",
                "slug": "normal-post",
                "author_id": "507f1f77bcf86cd799439014",
                "status": "published",
                "service": "residential_community",
                "metadata": {"type": "board"},
                "created_at": datetime(2023, 1, 1),
                "updated_at": datetime(2023, 1, 1)
            },
            {
                "_id": "507f1f77bcf86cd799439015",
                "title": "삭제된 게시글",
                "content": "삭제된 게시글 내용",
                "slug": "deleted-post",
                "author_id": "507f1f77bcf86cd799439016",
                "status": "deleted",
                "service": "residential_community",
                "metadata": {"type": "board"},
                "created_at": datetime(2023, 1, 1),
                "updated_at": datetime(2023, 1, 1)
            }
        ]
        mock_post_repository.get_all_posts_for_admin.return_value = (posts_data, 2)
        
        # Act
        result = await admin_service.get_all_posts(
            current_user=sample_admin_user,
            page=1,
            page_size=20,
            status=None
        )
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 2
        assert result["total"] == 2
        
        # Should include both published and deleted posts
        statuses = [item["status"] for item in result["items"]]
        assert "published" in statuses
        assert "deleted" in statuses
        
        # Verify repository calls
        mock_post_repository.get_all_posts_for_admin.assert_called_once_with(
            status=None,
            page=1,
            page_size=20
        )