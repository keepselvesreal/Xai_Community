"""Authentication service layer for business logic."""

from typing import Dict, Any, List
from datetime import datetime
from src.models.core import User, UserCreate, UserUpdate
from src.repositories.user_repository import UserRepository
from src.utils.jwt import JWTManager, TokenType
from src.utils.password import PasswordManager
from src.exceptions.auth import InvalidCredentialsError
from src.exceptions.user import (
    UserNotFoundError, 
    EmailAlreadyExistsError, 
    HandleAlreadyExistsError,
    UserNotActiveError,
    UserSuspendedError
)


class AuthService:
    """Authentication service for handling user authentication and management."""
    
    def __init__(
        self, 
        user_repository: UserRepository = None,
        jwt_manager: JWTManager = None,
        password_manager: PasswordManager = None
    ):
        """Initialize auth service with dependencies.
        
        Args:
            user_repository: User repository instance
            jwt_manager: JWT manager instance  
            password_manager: Password manager instance
        """
        self.user_repository = user_repository or UserRepository()
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager or PasswordManager()
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            EmailAlreadyExistsError: If email already exists
            HandleAlreadyExistsError: If handle already exists
        """
        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise EmailAlreadyExistsError(user_data.email)
        
        # Check if user_handle already exists
        existing_user = await self.user_repository.get_by_user_handle(user_data.user_handle)
        if existing_user:
            raise HandleAlreadyExistsError(user_data.user_handle)
        
        # Hash password
        password_hash = self.password_manager.hash_password(user_data.password)
        
        # Create user using repository
        user = await self.user_repository.create(user_data, password_hash)
        
        # Return user data without sensitive fields
        return {
            "id": str(user.id),
            "email": user.email,
            "user_handle": user.user_handle,
            "display_name": user.display_name,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authenticated user
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        try:
            user = await self.user_repository.get_by_email(email)
        except UserNotFoundError:
            raise InvalidCredentialsError()
        
        # Verify password
        if not self.password_manager.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        
        # Check user status
        if user.status != "active":
            raise InvalidCredentialsError("Account is not active")
        
        return user
    
    async def create_access_token(self, user: User) -> str:
        """Create access token for user.
        
        Args:
            user: User instance
            
        Returns:
            JWT access token
        """
        payload = {
            "sub": user.id,
            "email": user.email
        }
        return self.jwt_manager.create_token(payload, TokenType.ACCESS)
    
    async def create_refresh_token(self, user: User) -> str:
        """Create refresh token for user.
        
        Args:
            user: User instance
            
        Returns:
            JWT refresh token
        """
        payload = {
            "sub": user.id,
            "email": user.email
        }
        return self.jwt_manager.create_token(payload, TokenType.REFRESH)
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and return tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dictionary with user, access_token, refresh_token, and token_type
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        # Authenticate user
        user = await self.authenticate_user(email, password)
        
        # Update last login
        await self.user_repository.update_last_login(user.id)
        
        # Create tokens
        access_token = await self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access_token and token_type
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            UserNotFoundError: If user not found
        """
        # Verify refresh token
        payload = self.jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
        user_id = payload.get("sub")
        
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        
        # Create new access token
        access_token = await self.create_access_token(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    async def get_user_profile(self, user_id: str) -> User:
        """Get user profile by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        return await self.user_repository.get_by_id(user_id)
    
    async def update_user_profile(self, user_id: str, user_update: UserUpdate) -> User:
        """Update user profile.
        
        Args:
            user_id: User ID
            user_update: Updated user data
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update user
        return await self.user_repository.update(user_id, user_update)
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> User:
        """Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
            InvalidCredentialsError: If old password is wrong
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Hash new password
        new_password_hash = self.password_manager.hash_password(new_password)
        
        # Update password
        return await self.user_repository.update_password(user_id, new_password_hash)
    
    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update status
        return await self.user_repository.update_status(user_id, "inactive")
    
    async def activate_user(self, user_id: str) -> User:
        """Activate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update status
        return await self.user_repository.update_status(user_id, "active")
    
    async def suspend_user(self, user_id: str) -> User:
        """Suspend user account (admin operation).
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update status
        return await self.user_repository.update_status(user_id, "suspended")
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account (admin operation).
        
        Args:
            user_id: User ID
            
        Returns:
            True if deletion successful
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Delete user
        await self.user_repository.delete(user_id)
        return True
    
    async def list_users(self) -> List[User]:
        """List all users (admin operation).
        
        Returns:
            List of all users
        """
        return await self.user_repository.list_all()
    
    async def check_email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        try:
            await self.user_repository.get_by_email(email)
            return True
        except UserNotFoundError:
            return False
    
    async def check_user_handle_exists(self, user_handle: str) -> bool:
        """Check if user_handle already exists.
        
        Args:
            user_handle: Handle to check
            
        Returns:
            True if user_handle exists, False otherwise
        """
        try:
            await self.user_repository.get_by_user_handle(user_handle)
            return True
        except UserNotFoundError:
            return False