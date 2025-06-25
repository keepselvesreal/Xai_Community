"""Permission utilities for resource access control."""

from enum import Enum
from typing import List, Optional, Any, Union
from src.exceptions.auth import InsufficientPermissionsError, ResourceOwnershipError


class ResourcePermission(Enum):
    """Enumeration of resource permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class PermissionChecker:
    """Utility class for checking user permissions on resources."""
    
    def check_resource_ownership(self, user: Optional[Any], resource: Optional[Any]) -> bool:
        """Check if user owns the resource.
        
        Args:
            user: User object with id and is_admin attributes
            resource: Resource object with author_id attribute
            
        Returns:
            True if user owns resource or is admin, False otherwise
        """
        if user is None or resource is None:
            return False
        
        try:
            # Check if user is admin (admins can access any resource)
            is_admin = getattr(user, 'is_admin', False)
            if is_admin is True:  # Explicitly check for True to avoid MagicMock issues
                return True
            
            # Check resource ownership
            # Handle case where attributes don't exist by checking hasattr first
            if not hasattr(user, 'id') or not hasattr(resource, 'author_id'):
                return False
                
            user_id = getattr(user, 'id', None)
            resource_author_id = getattr(resource, 'author_id', None)
            
            if user_id is None or resource_author_id is None:
                return False
            
            return user_id == resource_author_id
            
        except (AttributeError, TypeError):
            return False
    
    def require_resource_ownership(self, user: Optional[Any], resource: Optional[Any]) -> None:
        """Require user to own the resource.
        
        Args:
            user: User object
            resource: Resource object
            
        Raises:
            ResourceOwnershipError: If user doesn't own the resource
        """
        if not self.check_resource_ownership(user, resource):
            raise ResourceOwnershipError(
                f"User does not have ownership of this resource"
            )
    
    def check_admin_permission(self, user: Optional[Any]) -> bool:
        """Check if user has admin permissions.
        
        Args:
            user: User object with is_admin attribute
            
        Returns:
            True if user is admin, False otherwise
        """
        if user is None:
            return False
        
        try:
            is_admin = getattr(user, 'is_admin', False)
            return is_admin is True  # Explicitly check for True to avoid MagicMock issues
        except (AttributeError, TypeError):
            return False
    
    def require_admin_permission(self, user: Optional[Any]) -> None:
        """Require user to have admin permissions.
        
        Args:
            user: User object
            
        Raises:
            InsufficientPermissionsError: If user is not admin
        """
        if not self.check_admin_permission(user):
            raise InsufficientPermissionsError(
                "Admin privileges required for this operation"
            )
    
    def check_post_permission(
        self, 
        user: Optional[Any], 
        post: Optional[Any], 
        permission: ResourcePermission
    ) -> bool:
        """Check if user has specific permission on a post.
        
        Args:
            user: User object
            post: Post object with author_id and status attributes
            permission: Required permission level
            
        Returns:
            True if user has permission, False otherwise
        """
        if user is None or post is None:
            return False
        
        try:
            # Admin can do anything
            is_admin = getattr(user, 'is_admin', False)
            if is_admin is True:  # Explicitly check for True to avoid MagicMock issues
                return True
            
            # Check if required attributes exist
            if not hasattr(user, 'id') or not hasattr(post, 'author_id'):
                return False
            
            # Check resource ownership
            user_id = getattr(user, 'id', None)
            post_author_id = getattr(post, 'author_id', None)
            post_status = getattr(post, 'status', 'draft')
            
            if user_id is None or post_author_id is None:
                return False
            
            # Owner can do anything with their post
            # Convert both to strings for comparison (to handle ObjectId)
            user_id_str = str(user_id)
            post_author_id_str = str(post_author_id)
            
            print(f"Permission check: user_id={user_id_str}, post_author_id={post_author_id_str}")
            print(f"Type of user_id: {type(user_id)}, Type of post_author_id: {type(post_author_id)}")
            
            if user_id_str == post_author_id_str:
                return True
            
            # Non-owners have limited permissions
            if permission == ResourcePermission.READ:
                # Can read published posts only
                return post_status == "published"
            elif permission in [ResourcePermission.WRITE, ResourcePermission.DELETE]:
                # Only owner can edit/delete
                return False
            
            return False
            
        except (AttributeError, TypeError):
            return False
    
    def check_comment_permission(
        self, 
        user: Optional[Any], 
        comment: Optional[Any], 
        permission: ResourcePermission
    ) -> bool:
        """Check if user has specific permission on a comment.
        
        Args:
            user: User object
            comment: Comment object with author_id attribute
            permission: Required permission level
            
        Returns:
            True if user has permission, False otherwise
        """
        if user is None or comment is None:
            return False
        
        try:
            # Admin can do anything
            is_admin = getattr(user, 'is_admin', False)
            if is_admin is True:  # Explicitly check for True to avoid MagicMock issues
                return True
            
            # Check if required attributes exist
            if not hasattr(user, 'id') or not hasattr(comment, 'author_id'):
                # For read permission, allow if user exists but comment lacks author_id
                if permission == ResourcePermission.READ and hasattr(user, 'id'):
                    return True
                return False
            
            # Check resource ownership
            user_id = getattr(user, 'id', None)
            comment_author_id = getattr(comment, 'author_id', None)
            
            if user_id is None or comment_author_id is None:
                # For read permission, allow if we have user but no comment author
                if permission == ResourcePermission.READ and user_id is not None:
                    return True
                return False
            
            # Owner can do anything with their comment
            if user_id == comment_author_id:
                return True
            
            # Non-owners have limited permissions
            if permission == ResourcePermission.READ:
                # Anyone can read comments
                return True
            elif permission in [ResourcePermission.WRITE, ResourcePermission.DELETE]:
                # Only owner can edit/delete
                return False
            
            return False
            
        except (AttributeError, TypeError):
            return False
    
    def require_post_permission(
        self, 
        user: Optional[Any], 
        post: Optional[Any], 
        permission: ResourcePermission
    ) -> None:
        """Require user to have specific permission on a post.
        
        Args:
            user: User object
            post: Post object
            permission: Required permission level
            
        Raises:
            InsufficientPermissionsError: If user doesn't have permission
        """
        if not self.check_post_permission(user, post, permission):
            raise InsufficientPermissionsError(
                f"User does not have {permission.value} permission on this post"
            )
    
    def require_comment_permission(
        self, 
        user: Optional[Any], 
        comment: Optional[Any], 
        permission: ResourcePermission
    ) -> None:
        """Require user to have specific permission on a comment.
        
        Args:
            user: User object
            comment: Comment object
            permission: Required permission level
            
        Raises:
            InsufficientPermissionsError: If user doesn't have permission
        """
        if not self.check_comment_permission(user, comment, permission):
            raise InsufficientPermissionsError(
                f"User does not have {permission.value} permission on this comment"
            )
    
    def can_user_access_resource(
        self, 
        user: Optional[Any], 
        resource: Optional[Any], 
        permission: Union[ResourcePermission, str]
    ) -> bool:
        """Generic method to check if user can access resource with given permission.
        
        Args:
            user: User object
            resource: Resource object (post or comment)
            permission: Required permission level
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Convert string permission to enum if needed
            if isinstance(permission, str):
                try:
                    permission = ResourcePermission(permission)
                except ValueError:
                    return False
            
            # Determine resource type and check permission
            if hasattr(resource, 'title'):  # Assume it's a post
                return self.check_post_permission(user, resource, permission)
            elif hasattr(resource, 'content') and hasattr(resource, 'post_id'):  # Assume it's a comment
                return self.check_comment_permission(user, resource, permission)
            else:
                # Generic resource ownership check
                if permission == ResourcePermission.READ:
                    return True  # Allow read by default
                else:
                    return self.check_resource_ownership(user, resource)
                    
        except (AttributeError, TypeError, ValueError):
            return False
    
    def get_user_permissions(
        self, 
        user: Optional[Any], 
        resource: Optional[Any]
    ) -> List[ResourcePermission]:
        """Get list of permissions user has on a resource.
        
        Args:
            user: User object
            resource: Resource object
            
        Returns:
            List of permissions user has on the resource
        """
        permissions = []
        
        for permission in ResourcePermission:
            if self.can_user_access_resource(user, resource, permission):
                permissions.append(permission)
        
        return permissions


# Convenience functions for direct usage
permission_checker = PermissionChecker()

def check_post_permission(user, post, action: str) -> bool:
    """Convenience function to check post permissions.
    
    Args:
        user: User object
        post: Post object
        action: Action string ('read', 'update', 'delete')
        
    Returns:
        True if user has permission
    """
    if action == "read":
        return permission_checker.check_post_permission(user, post, ResourcePermission.READ)
    elif action in ["update", "write"]:
        return permission_checker.check_post_permission(user, post, ResourcePermission.WRITE)
    elif action == "delete":
        return permission_checker.check_post_permission(user, post, ResourcePermission.DELETE)
    else:
        return False