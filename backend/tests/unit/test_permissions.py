import pytest
from unittest.mock import MagicMock
from src.utils.permissions import PermissionChecker, ResourcePermission
from src.models.core import User
from src.exceptions.auth import InsufficientPermissionsError, ResourceOwnershipError


@pytest.fixture
def permission_checker():
    """Create PermissionChecker instance for testing."""
    return PermissionChecker()


@pytest.fixture
def regular_user():
    """Create regular user mock."""
    user = MagicMock()
    user.id = "507f1f77bcf86cd799439011"
    user.email = "user@example.com"
    user.handle = "user"
    user.status = "active"
    user.is_admin = False
    return user


@pytest.fixture
def admin_user():
    """Create admin user mock."""
    user = MagicMock()
    user.id = "507f1f77bcf86cd799439012"
    user.email = "admin@example.com"
    user.handle = "admin"
    user.status = "active"
    user.is_admin = True
    return user


@pytest.fixture
def sample_post():
    """Create sample post mock."""
    post = MagicMock()
    post.id = "507f1f77bcf86cd799439013"
    post.author_id = "507f1f77bcf86cd799439011"  # belongs to regular_user
    post.title = "Sample Post"
    post.status = "published"
    return post


@pytest.fixture
def sample_comment():
    """Create sample comment mock."""
    comment = MagicMock()
    comment.id = "507f1f77bcf86cd799439014"
    comment.author_id = "507f1f77bcf86cd799439011"  # belongs to regular_user
    comment.post_id = "507f1f77bcf86cd799439013"
    comment.content = "Sample comment"
    return comment


class TestResourceOwnership:
    """Test resource ownership validation."""
    
    def test_check_resource_ownership_success(self, permission_checker, regular_user, sample_post):
        """Test successful resource ownership check."""
        # User owns the post
        result = permission_checker.check_resource_ownership(regular_user, sample_post)
        assert result is True
    
    def test_check_resource_ownership_failure(self, permission_checker, regular_user, sample_post):
        """Test failed resource ownership check."""
        # Change post owner to different user
        sample_post.author_id = "different_user_id"
        
        result = permission_checker.check_resource_ownership(regular_user, sample_post)
        assert result is False
    
    def test_check_resource_ownership_admin_override(self, permission_checker, admin_user, sample_post):
        """Test admin can access any resource."""
        # Admin user accessing post owned by another user
        sample_post.author_id = "different_user_id"
        
        result = permission_checker.check_resource_ownership(admin_user, sample_post)
        assert result is True
    
    def test_require_resource_ownership_success(self, permission_checker, regular_user, sample_post):
        """Test successful resource ownership requirement."""
        # Should not raise exception
        permission_checker.require_resource_ownership(regular_user, sample_post)
    
    def test_require_resource_ownership_failure(self, permission_checker, regular_user, sample_post):
        """Test failed resource ownership requirement."""
        sample_post.author_id = "different_user_id"
        
        with pytest.raises(ResourceOwnershipError):
            permission_checker.require_resource_ownership(regular_user, sample_post)
    
    def test_require_resource_ownership_admin_success(self, permission_checker, admin_user, sample_post):
        """Test admin can access any resource via ownership requirement."""
        sample_post.author_id = "different_user_id"
        
        # Should not raise exception for admin
        permission_checker.require_resource_ownership(admin_user, sample_post)


class TestAdminPermissions:
    """Test admin permission validation."""
    
    def test_check_admin_permission_success(self, permission_checker, admin_user):
        """Test successful admin permission check."""
        result = permission_checker.check_admin_permission(admin_user)
        assert result is True
    
    def test_check_admin_permission_failure(self, permission_checker, regular_user):
        """Test failed admin permission check."""
        result = permission_checker.check_admin_permission(regular_user)
        assert result is False
    
    def test_check_admin_permission_no_attribute(self, permission_checker):
        """Test admin permission check with user missing is_admin attribute."""
        user_no_admin = MagicMock()
        user_no_admin.id = "507f1f77bcf86cd799439015"
        del user_no_admin.is_admin  # Remove attribute
        
        result = permission_checker.check_admin_permission(user_no_admin)
        assert result is False
    
    def test_require_admin_permission_success(self, permission_checker, admin_user):
        """Test successful admin permission requirement."""
        # Should not raise exception
        permission_checker.require_admin_permission(admin_user)
    
    def test_require_admin_permission_failure(self, permission_checker, regular_user):
        """Test failed admin permission requirement."""
        with pytest.raises(InsufficientPermissionsError):
            permission_checker.require_admin_permission(regular_user)


class TestResourcePermissions:
    """Test resource-specific permission validation."""
    
    def test_check_post_permission_owner(self, permission_checker, regular_user, sample_post):
        """Test post permission check for owner."""
        result = permission_checker.check_post_permission(
            regular_user, sample_post, ResourcePermission.READ
        )
        assert result is True
        
        result = permission_checker.check_post_permission(
            regular_user, sample_post, ResourcePermission.WRITE
        )
        assert result is True
        
        result = permission_checker.check_post_permission(
            regular_user, sample_post, ResourcePermission.DELETE
        )
        assert result is True
    
    def test_check_post_permission_non_owner_read(self, permission_checker, regular_user, sample_post):
        """Test post read permission for non-owner."""
        sample_post.author_id = "different_user_id"
        sample_post.status = "published"
        
        result = permission_checker.check_post_permission(
            regular_user, sample_post, ResourcePermission.READ
        )
        assert result is True  # Anyone can read published posts
    
    def test_check_post_permission_non_owner_write(self, permission_checker, regular_user, sample_post):
        """Test post write permission for non-owner."""
        sample_post.author_id = "different_user_id"
        
        result = permission_checker.check_post_permission(
            regular_user, sample_post, ResourcePermission.WRITE
        )
        assert result is False  # Only owner can edit
    
    def test_check_post_permission_draft_non_owner(self, permission_checker, regular_user, sample_post):
        """Test draft post access for non-owner."""
        sample_post.author_id = "different_user_id"
        sample_post.status = "draft"
        
        result = permission_checker.check_post_permission(
            regular_user, sample_post, ResourcePermission.READ
        )
        assert result is False  # Can't read draft posts of others
    
    def test_check_post_permission_admin_override(self, permission_checker, admin_user, sample_post):
        """Test admin can access any post."""
        sample_post.author_id = "different_user_id"
        sample_post.status = "draft"
        
        for permission in [ResourcePermission.READ, ResourcePermission.WRITE, ResourcePermission.DELETE]:
            result = permission_checker.check_post_permission(admin_user, sample_post, permission)
            assert result is True
    
    def test_check_comment_permission_owner(self, permission_checker, regular_user, sample_comment):
        """Test comment permission check for owner."""
        result = permission_checker.check_comment_permission(
            regular_user, sample_comment, ResourcePermission.READ
        )
        assert result is True
        
        result = permission_checker.check_comment_permission(
            regular_user, sample_comment, ResourcePermission.WRITE
        )
        assert result is True
        
        result = permission_checker.check_comment_permission(
            regular_user, sample_comment, ResourcePermission.DELETE
        )
        assert result is True
    
    def test_check_comment_permission_non_owner(self, permission_checker, regular_user, sample_comment):
        """Test comment permission check for non-owner."""
        sample_comment.author_id = "different_user_id"
        
        # Anyone can read comments
        result = permission_checker.check_comment_permission(
            regular_user, sample_comment, ResourcePermission.READ
        )
        assert result is True
        
        # Only owner can edit/delete
        result = permission_checker.check_comment_permission(
            regular_user, sample_comment, ResourcePermission.WRITE
        )
        assert result is False
        
        result = permission_checker.check_comment_permission(
            regular_user, sample_comment, ResourcePermission.DELETE
        )
        assert result is False


class TestPermissionRequirements:
    """Test permission requirement enforcement."""
    
    def test_require_post_permission_success(self, permission_checker, regular_user, sample_post):
        """Test successful post permission requirement."""
        # Should not raise exception for owner
        permission_checker.require_post_permission(
            regular_user, sample_post, ResourcePermission.WRITE
        )
    
    def test_require_post_permission_failure(self, permission_checker, regular_user, sample_post):
        """Test failed post permission requirement."""
        sample_post.author_id = "different_user_id"
        
        with pytest.raises(InsufficientPermissionsError):
            permission_checker.require_post_permission(
                regular_user, sample_post, ResourcePermission.WRITE
            )
    
    def test_require_comment_permission_success(self, permission_checker, regular_user, sample_comment):
        """Test successful comment permission requirement."""
        # Should not raise exception for owner
        permission_checker.require_comment_permission(
            regular_user, sample_comment, ResourcePermission.DELETE
        )
    
    def test_require_comment_permission_failure(self, permission_checker, regular_user, sample_comment):
        """Test failed comment permission requirement."""
        sample_comment.author_id = "different_user_id"
        
        with pytest.raises(InsufficientPermissionsError):
            permission_checker.require_comment_permission(
                regular_user, sample_comment, ResourcePermission.DELETE
            )


class TestPermissionHelpers:
    """Test permission helper methods."""
    
    def test_can_user_access_resource_owner(self, permission_checker, regular_user, sample_post):
        """Test resource access check for owner."""
        result = permission_checker.can_user_access_resource(
            regular_user, sample_post, ResourcePermission.WRITE
        )
        assert result is True
    
    def test_can_user_access_resource_admin(self, permission_checker, admin_user, sample_post):
        """Test resource access check for admin."""
        sample_post.author_id = "different_user_id"
        
        result = permission_checker.can_user_access_resource(
            admin_user, sample_post, ResourcePermission.DELETE
        )
        assert result is True
    
    def test_can_user_access_resource_denied(self, permission_checker, regular_user, sample_post):
        """Test resource access check denied."""
        sample_post.author_id = "different_user_id"
        
        result = permission_checker.can_user_access_resource(
            regular_user, sample_post, ResourcePermission.DELETE
        )
        assert result is False
    
    def test_get_user_permissions_owner(self, permission_checker, regular_user, sample_post):
        """Test getting user permissions for owned resource."""
        permissions = permission_checker.get_user_permissions(regular_user, sample_post)
        
        assert ResourcePermission.READ in permissions
        assert ResourcePermission.WRITE in permissions
        assert ResourcePermission.DELETE in permissions
    
    def test_get_user_permissions_non_owner_published(self, permission_checker, regular_user, sample_post):
        """Test getting user permissions for non-owned published resource."""
        sample_post.author_id = "different_user_id"
        sample_post.status = "published"
        
        permissions = permission_checker.get_user_permissions(regular_user, sample_post)
        
        assert ResourcePermission.READ in permissions
        assert ResourcePermission.WRITE not in permissions
        assert ResourcePermission.DELETE not in permissions
    
    def test_get_user_permissions_admin(self, permission_checker, admin_user, sample_post):
        """Test getting admin permissions for any resource."""
        sample_post.author_id = "different_user_id"
        
        permissions = permission_checker.get_user_permissions(admin_user, sample_post)
        
        assert ResourcePermission.READ in permissions
        assert ResourcePermission.WRITE in permissions
        assert ResourcePermission.DELETE in permissions


class TestPermissionEdgeCases:
    """Test permission system edge cases."""
    
    def test_none_user_permissions(self, permission_checker, sample_post):
        """Test permission check with None user."""
        result = permission_checker.check_resource_ownership(None, sample_post)
        assert result is False
        
        result = permission_checker.check_admin_permission(None)
        assert result is False
    
    def test_none_resource_permissions(self, permission_checker, regular_user):
        """Test permission check with None resource."""
        result = permission_checker.check_resource_ownership(regular_user, None)
        assert result is False
    
    def test_invalid_permission_type(self, permission_checker, regular_user, sample_post):
        """Test permission check with invalid permission type."""
        # Should handle gracefully and return False
        result = permission_checker.can_user_access_resource(
            regular_user, sample_post, "invalid_permission"
        )
        assert result is False
    
    def test_user_without_id(self, permission_checker, sample_post):
        """Test permission check with user missing ID."""
        user_no_id = MagicMock()
        del user_no_id.id
        
        result = permission_checker.check_resource_ownership(user_no_id, sample_post)
        assert result is False
    
    def test_resource_without_author_id(self, permission_checker, regular_user):
        """Test permission check with resource missing author_id."""
        resource_no_author = MagicMock()
        del resource_no_author.author_id
        
        result = permission_checker.check_resource_ownership(regular_user, resource_no_author)
        assert result is False