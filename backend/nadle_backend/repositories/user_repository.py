"""User repository for data access layer."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from beanie.operators import In
from nadle_backend.models.core import User, UserCreate, UserUpdate
from nadle_backend.exceptions.user import UserNotFoundError, DuplicateUserError


class UserRepository:
    """Repository for user data access operations."""
    
    async def create(self, user_create: UserCreate, password_hash: str) -> User:
        """Create a new user.
        
        Args:
            user_create: User creation data
            password_hash: Hashed password
            
        Returns:
            Created user
            
        Raises:
            DuplicateUserError: If email or handle already exists
        """
        # Note: Duplicate checks are handled in service layer
        
        # Create user
        user_data = user_create.model_dump(exclude={"password"})
        user_data["password_hash"] = password_hash
        
        user = User(**user_data)
        await user.insert()
        
        return user
    
    async def get_by_id(self, user_id: str) -> User:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await User.get(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User instance or None if not found
        """
        return await User.find_one({"email": email})
    
    async def get_by_user_handle(self, user_handle: str) -> Optional[User]:
        """Get user by user_handle.
        
        Args:
            user_handle: User handle
            
        Returns:
            User instance or None if not found
        """
        return await User.find_one({"user_handle": user_handle})
    
    async def update(self, user_id: str, user_update: UserUpdate) -> User:
        """Update user information.
        
        Args:
            user_id: User ID
            user_update: Updated user data
            
        Returns:
            Updated user
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await user.save()
        
        return user
    
    async def delete(self, user_id: str) -> None:
        """Delete user.
        
        Args:
            user_id: User ID
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        await user.delete()
    
    async def update_last_login(self, user_id: str) -> User:
        """Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        user.last_login = datetime.utcnow()
        await user.save()
        return user
    
    async def list_users(
        self, 
        page: int = 1, 
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List users with pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of users per page
            status: Filter by user status
            
        Returns:
            Dictionary with users list and pagination info
        """
        skip = (page - 1) * page_size
        
        # Build query
        query_filter = {}
        if status:
            query_filter["status"] = status
        
        query = User.find(query_filter)
        
        # Get total count
        total = await query.count()
        
        # Get users for current page
        users = await query.skip(skip).limit(page_size).to_list()
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def check_email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        user = await User.find_one({"email": email})
        return user is not None
    
    async def check_user_handle_exists(self, user_handle: str) -> bool:
        """Check if user_handle already exists.
        
        Args:
            user_handle: Handle to check
            
        Returns:
            True if user_handle exists, False otherwise
        """
        user = await User.find_one({"user_handle": user_handle})
        return user is not None
    
    async def update_status(self, user_id: str, status: str) -> User:
        """Update user status.
        
        Args:
            user_id: User ID
            status: New status
            
        Returns:
            Updated user
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        user.status = status
        user.updated_at = datetime.utcnow()
        await user.save()
        return user
    
    async def update_password(self, user_id: str, password_hash: str) -> User:
        """Update user password hash.
        
        Args:
            user_id: User ID
            password_hash: New password hash
            
        Returns:
            Updated user
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.get_by_id(user_id)
        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()
        await user.save()
        return user
    
    async def list_all(self) -> List[User]:
        """List all users (admin operation).
        
        Returns:
            List of all users
        """
        return await User.find_all().to_list()