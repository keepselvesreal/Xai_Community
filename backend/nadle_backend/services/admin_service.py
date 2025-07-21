"""Admin service layer for administrative functions."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from nadle_backend.models.core import User, Post
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.exceptions.post import PostNotFoundError


class AdminService:
    """Service layer for admin-related business logic."""

    def __init__(self, post_repository: PostRepository = None):
        """Initialize admin service with dependencies.

        Args:
            post_repository: Post repository instance
        """
        self.post_repository = post_repository or PostRepository()

    def _check_admin_permission(self, user: User) -> None:
        """Check if user has admin privileges.

        Args:
            user: User to check

        Raises:
            PermissionError: If user is not admin
        """
        if not user.is_admin:
            raise PermissionError("Admin privileges required")

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """Validate if status transition is allowed.

        Args:
            current_status: Current post status
            new_status: New status to transition to

        Raises:
            ValueError: If transition is not allowed
        """
        # Define allowed transitions
        allowed_transitions = {
            "pending": ["resolved", "rejected"],
            "published": ["archived", "deleted"],
            "draft": ["published", "deleted"],
            "archived": ["published", "deleted"],
        }

        if current_status not in allowed_transitions:
            raise ValueError(f"Cannot transition from status: {current_status}")

        if new_status not in allowed_transitions[current_status]:
            raise ValueError(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    async def get_inquiries_list(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        inquiry_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get list of inquiries/reports for admin management.

        Args:
            current_user: Current admin user
            page: Page number
            page_size: Items per page
            inquiry_type: Filter by inquiry type
            status: Filter by status

        Returns:
            Paginated list of inquiries

        Raises:
            PermissionError: If user is not admin
        """
        self._check_admin_permission(current_user)

        # Get inquiries from repository
        inquiries, total = await self.post_repository.get_inquiries_list(
            inquiry_type=inquiry_type, status=status, page=page, page_size=page_size
        )

        return {
            "items": inquiries,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def get_inquiry_by_id(self, inquiry_id: str, current_user: User) -> Post:
        """Get specific inquiry by ID.

        Args:
            inquiry_id: Inquiry post ID
            current_user: Current admin user

        Returns:
            Inquiry post instance

        Raises:
            PermissionError: If user is not admin
            PostNotFoundError: If inquiry not found
        """
        self._check_admin_permission(current_user)

        post = await self.post_repository.get_by_id(inquiry_id)
        if not post:
            raise PostNotFoundError(f"Inquiry with ID {inquiry_id} not found")

        return post

    async def update_inquiry_status(
        self, inquiry_id: str, new_status: str, current_user: User
    ) -> Post:
        """Update inquiry status.

        Args:
            inquiry_id: Inquiry post ID
            new_status: New status to set
            current_user: Current admin user

        Returns:
            Updated post instance

        Raises:
            PermissionError: If user is not admin
            PostNotFoundError: If inquiry not found
            ValueError: If status transition is invalid
        """
        self._check_admin_permission(current_user)

        # Get current post
        post = await self.post_repository.get_by_id(inquiry_id)
        if not post:
            raise PostNotFoundError(f"Inquiry with ID {inquiry_id} not found")

        # Validate status transition
        self._validate_status_transition(post.status, new_status)

        # Set resolved_at timestamp for resolved/rejected status
        resolved_at = None
        if new_status in ["resolved", "rejected"]:
            resolved_at = datetime.utcnow()

        # Update status in repository
        updated_post = await self.post_repository.update_status(
            post_id=inquiry_id, new_status=new_status, resolved_at=resolved_at
        )

        return updated_post

    async def get_all_posts(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get all posts for admin management (including deleted ones).

        Args:
            current_user: Current admin user
            page: Page number
            page_size: Items per page
            status: Filter by status

        Returns:
            Paginated list of all posts

        Raises:
            PermissionError: If user is not admin
        """
        self._check_admin_permission(current_user)

        # Get all posts from repository
        posts, total = await self.post_repository.get_all_posts_for_admin(
            status=status, page=page, page_size=page_size
        )

        return {
            "items": posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def get_user_by_id(self, user_id: str, current_user: User) -> User:
        """Get user information by ID for admin management.

        Args:
            user_id: User ID to get
            current_user: Current admin user

        Returns:
            User instance

        Raises:
            PermissionError: If user is not admin
            Exception: If user not found
        """
        self._check_admin_permission(current_user)

        # Get user by ID
        user = await User.get(user_id)
        if not user:
            raise Exception(f"User with ID {user_id} not found")

        return user

    async def update_user_permissions(
        self,
        user_id: str,
        permission_update,  # UserPermissionUpdate 타입 (import 순환 방지)
        current_user: User,
    ) -> User:
        """Update user permissions for specific pages.

        Args:
            user_id: User ID to update
            permission_update: Permission update data
            current_user: Current admin user

        Returns:
            Updated user instance

        Raises:
            PermissionError: If user is not admin
            Exception: If user not found
        """
        self._check_admin_permission(current_user)

        # Get user by ID
        user = await User.get(user_id)
        if not user:
            raise Exception(f"User with ID {user_id} not found")

        # Update permissions only if provided
        update_data = {}
        if permission_update.can_write_moving_services is not None:
            update_data["can_write_moving_services"] = (
                permission_update.can_write_moving_services
            )
        if permission_update.can_write_expert_tips is not None:
            update_data["can_write_expert_tips"] = (
                permission_update.can_write_expert_tips
            )

        # Update user permissions
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await user.update({"$set": update_data})

        # Return updated user
        return await User.get(user_id)
