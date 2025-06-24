"""Tests for authentication service logic."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.auth_service import AuthService
from src.models.core import User, UserCreate, UserUpdate
from src.utils.jwt import JWTManager, TokenType
from src.utils.password import PasswordManager
from src.repositories.user_repository import UserRepository
from src.exceptions.auth import InvalidCredentialsError
from src.exceptions.user import UserNotFoundError, EmailAlreadyExistsError, HandleAlreadyExistsError


@pytest.fixture
def mock_user_repository():
    """Create mock user repository."""
    repo = MagicMock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_jwt_manager():
    """Create mock JWT manager."""
    manager = MagicMock(spec=JWTManager)
    return manager


@pytest.fixture
def mock_password_manager():
    """Create mock password manager."""
    manager = MagicMock(spec=PasswordManager)
    return manager


@pytest.fixture
def auth_service(mock_user_repository, mock_jwt_manager, mock_password_manager):
    """Create AuthService instance with mocked dependencies."""
    return AuthService(
        user_repository=mock_user_repository,
        jwt_manager=mock_jwt_manager,
        password_manager=mock_password_manager
    )


@pytest.fixture
def sample_user():
    """Create sample user."""
    user = MagicMock()
    user.id = "507f1f77bcf86cd799439011"
    user.email = "test@example.com"
    user.name = "Test User"
    user.handle = "testuser"
    user.status = "active"
    user.is_admin = False
    user.password_hash = "hashed_password"
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


@pytest.fixture
def user_create_data():
    """Create user creation data."""
    return UserCreate(
        name="Test User",
        email="test@example.com",
        handle="testuser",
        password="TestPassword123!"
    )


@pytest.fixture
def user_update_data():
    """Create user update data."""
    return UserUpdate(
        name="Updated User",
        bio="Updated bio"
    )


class TestUserRegistration:
    """Test user registration functionality."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_user_repository, 
                                       mock_password_manager, user_create_data, sample_user):
        """Test successful user registration."""
        # Mock no existing user
        mock_user_repository.get_by_email = AsyncMock(side_effect=UserNotFoundError("test@example.com"))
        mock_user_repository.get_by_handle = AsyncMock(side_effect=UserNotFoundError("testuser"))
        
        # Mock password hashing
        mock_password_manager.hash_password.return_value = "hashed_password"
        
        # Mock user creation
        mock_user_repository.create = AsyncMock(return_value=sample_user)
        
        # Test registration
        result = await auth_service.register_user(user_create_data)
        
        assert result == sample_user
        mock_password_manager.hash_password.assert_called_once_with("TestPassword123!")
        mock_user_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service, mock_user_repository, 
                                             user_create_data, sample_user):
        """Test registration with existing email."""
        # Mock existing user with same email
        mock_user_repository.get_by_email = AsyncMock(return_value=sample_user)
        
        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.register_user(user_create_data)
    
    @pytest.mark.asyncio
    async def test_register_user_handle_exists(self, auth_service, mock_user_repository, 
                                              user_create_data, sample_user):
        """Test registration with existing handle."""
        # Mock no existing email but existing handle
        mock_user_repository.get_by_email = AsyncMock(side_effect=UserNotFoundError("test@example.com"))
        mock_user_repository.get_by_handle = AsyncMock(return_value=sample_user)
        
        with pytest.raises(HandleAlreadyExistsError):
            await auth_service.register_user(user_create_data)
    
    @pytest.mark.asyncio
    async def test_register_user_without_handle(self, auth_service, mock_user_repository, 
                                               mock_password_manager, sample_user):
        """Test registration without handle."""
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="TestPassword123!"
        )
        
        # Mock no existing user
        mock_user_repository.get_by_email = AsyncMock(side_effect=UserNotFoundError("test@example.com"))
        
        # Mock password hashing
        mock_password_manager.hash_password.return_value = "hashed_password"
        
        # Mock user creation
        mock_user_repository.create = AsyncMock(return_value=sample_user)
        
        # Test registration
        result = await auth_service.register_user(user_data)
        
        assert result == sample_user
        # Should not check handle since it's None
        mock_user_repository.get_by_handle.assert_not_called()


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user_repository, 
                                            mock_password_manager, sample_user):
        """Test successful user authentication."""
        # Mock user exists
        mock_user_repository.get_by_email = AsyncMock(return_value=sample_user)
        
        # Mock password verification
        mock_password_manager.verify_password.return_value = True
        
        # Test authentication
        result = await auth_service.authenticate_user("test@example.com", "password")
        
        assert result == sample_user
        mock_password_manager.verify_password.assert_called_once_with("password", "hashed_password")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_user_repository):
        """Test authentication with non-existent user."""
        # Mock user not found
        mock_user_repository.get_by_email = AsyncMock(side_effect=UserNotFoundError("test@example.com"))
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user("test@example.com", "password")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_user_repository, 
                                                   mock_password_manager, sample_user):
        """Test authentication with wrong password."""
        # Mock user exists
        mock_user_repository.get_by_email = AsyncMock(return_value=sample_user)
        
        # Mock password verification failure
        mock_password_manager.verify_password.return_value = False
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user("test@example.com", "wrong_password")
    
    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service, mock_user_repository, 
                                             mock_password_manager, sample_user):
        """Test authentication with inactive user."""
        # Set user as inactive
        sample_user.status = "inactive"
        
        # Mock user exists
        mock_user_repository.get_by_email = AsyncMock(return_value=sample_user)
        
        # Mock password verification
        mock_password_manager.verify_password.return_value = True
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user("test@example.com", "password")


class TestTokenManagement:
    """Test token management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service, mock_jwt_manager, sample_user):
        """Test access token creation."""
        # Mock token creation
        mock_jwt_manager.create_token.return_value = "access_token"
        
        # Test token creation
        token = await auth_service.create_access_token(sample_user)
        
        assert token == "access_token"
        mock_jwt_manager.create_token.assert_called_once_with(
            {"sub": sample_user.id, "email": sample_user.email},
            TokenType.ACCESS
        )
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, auth_service, mock_jwt_manager, sample_user):
        """Test refresh token creation."""
        # Mock token creation
        mock_jwt_manager.create_token.return_value = "refresh_token"
        
        # Test token creation
        token = await auth_service.create_refresh_token(sample_user)
        
        assert token == "refresh_token"
        mock_jwt_manager.create_token.assert_called_once_with(
            {"sub": sample_user.id, "email": sample_user.email},
            TokenType.REFRESH
        )
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repository, 
                                mock_password_manager, mock_jwt_manager, sample_user):
        """Test successful login with token creation."""
        # Mock authentication
        mock_user_repository.get_by_email = AsyncMock(return_value=sample_user)
        mock_password_manager.verify_password.return_value = True
        
        # Mock token creation
        mock_jwt_manager.create_token.side_effect = ["access_token", "refresh_token"]
        
        # Test login
        result = await auth_service.login("test@example.com", "password")
        
        assert result["user"] == sample_user
        assert result["access_token"] == "access_token"
        assert result["refresh_token"] == "refresh_token"
        assert result["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_jwt_manager, 
                                        mock_user_repository, sample_user):
        """Test successful token refresh."""
        # Mock token verification
        mock_jwt_manager.verify_token.return_value = {
            "sub": sample_user.id,
            "email": sample_user.email
        }
        
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock new token creation
        mock_jwt_manager.create_token.return_value = "new_access_token"
        
        # Test token refresh
        result = await auth_service.refresh_access_token("refresh_token")
        
        assert result["access_token"] == "new_access_token"
        assert result["token_type"] == "bearer"
        mock_jwt_manager.verify_token.assert_called_once_with("refresh_token", TokenType.REFRESH)


class TestProfileManagement:
    """Test user profile management functionality."""
    
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, auth_service, mock_user_repository, sample_user):
        """Test successful user profile retrieval."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Test profile retrieval
        result = await auth_service.get_user_profile(sample_user.id)
        
        assert result == sample_user
        mock_user_repository.get_by_id.assert_called_once_with(sample_user.id)
    
    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, auth_service, mock_user_repository):
        """Test user profile retrieval when user not found."""
        # Mock user not found
        mock_user_repository.get_by_id = AsyncMock(side_effect=UserNotFoundError("user_id"))
        
        with pytest.raises(UserNotFoundError):
            await auth_service.get_user_profile("user_id")
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, auth_service, mock_user_repository, 
                                              sample_user, user_update_data):
        """Test successful user profile update."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock user update
        updated_user = MagicMock()
        updated_user.id = sample_user.id
        updated_user.name = "Updated User"
        updated_user.bio = "Updated bio"
        mock_user_repository.update = AsyncMock(return_value=updated_user)
        
        # Test profile update
        result = await auth_service.update_user_profile(sample_user.id, user_update_data)
        
        assert result == updated_user
        mock_user_repository.update.assert_called_once_with(sample_user.id, user_update_data)
    
    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, auth_service, mock_user_repository, 
                                                 user_update_data):
        """Test user profile update when user not found."""
        # Mock user not found
        mock_user_repository.get_by_id = AsyncMock(side_effect=UserNotFoundError("user_id"))
        
        with pytest.raises(UserNotFoundError):
            await auth_service.update_user_profile("user_id", user_update_data)
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_user_repository, 
                                          mock_password_manager, sample_user):
        """Test successful password change."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock password verification and hashing
        mock_password_manager.verify_password.return_value = True
        mock_password_manager.hash_password.return_value = "new_hashed_password"
        
        # Mock user update
        updated_user = MagicMock()
        updated_user.id = sample_user.id
        mock_user_repository.update_password = AsyncMock(return_value=updated_user)
        
        # Test password change
        result = await auth_service.change_password(sample_user.id, "old_password", "new_password")
        
        assert result == updated_user
        mock_password_manager.verify_password.assert_called_once_with("old_password", sample_user.password_hash)
        mock_password_manager.hash_password.assert_called_once_with("new_password")
        mock_user_repository.update_password.assert_called_once_with(sample_user.id, "new_hashed_password")
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, auth_service, mock_user_repository, 
                                                     mock_password_manager, sample_user):
        """Test password change with wrong old password."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock password verification failure
        mock_password_manager.verify_password.return_value = False
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.change_password(sample_user.id, "wrong_old_password", "new_password")


class TestUserStatus:
    """Test user status management functionality."""
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, auth_service, mock_user_repository, sample_user):
        """Test successful user deactivation."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock user update
        deactivated_user = MagicMock()
        deactivated_user.id = sample_user.id
        deactivated_user.status = "inactive"
        mock_user_repository.update_status = AsyncMock(return_value=deactivated_user)
        
        # Test user deactivation
        result = await auth_service.deactivate_user(sample_user.id)
        
        assert result == deactivated_user
        mock_user_repository.update_status.assert_called_once_with(sample_user.id, "inactive")
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, auth_service, mock_user_repository, sample_user):
        """Test successful user activation."""
        # Set user as inactive
        sample_user.status = "inactive"
        
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock user update
        activated_user = MagicMock()
        activated_user.id = sample_user.id
        activated_user.status = "active"
        mock_user_repository.update_status = AsyncMock(return_value=activated_user)
        
        # Test user activation
        result = await auth_service.activate_user(sample_user.id)
        
        assert result == activated_user
        mock_user_repository.update_status.assert_called_once_with(sample_user.id, "active")


class TestAdminOperations:
    """Test admin-specific operations."""
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, auth_service, mock_user_repository):
        """Test successful user listing for admin."""
        users = [MagicMock(), MagicMock(), MagicMock()]
        mock_user_repository.list_all = AsyncMock(return_value=users)
        
        result = await auth_service.list_users()
        
        assert result == users
        mock_user_repository.list_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_suspend_user_success(self, auth_service, mock_user_repository, sample_user):
        """Test successful user suspension."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock user update
        suspended_user = MagicMock()
        suspended_user.id = sample_user.id
        suspended_user.status = "suspended"
        mock_user_repository.update_status = AsyncMock(return_value=suspended_user)
        
        # Test user suspension
        result = await auth_service.suspend_user(sample_user.id)
        
        assert result == suspended_user
        mock_user_repository.update_status.assert_called_once_with(sample_user.id, "suspended")
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, auth_service, mock_user_repository, sample_user):
        """Test successful user deletion."""
        # Mock user retrieval
        mock_user_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        # Mock user deletion
        mock_user_repository.delete = AsyncMock(return_value=True)
        
        # Test user deletion
        result = await auth_service.delete_user(sample_user.id)
        
        assert result is True
        mock_user_repository.delete.assert_called_once_with(sample_user.id)


class TestHelperMethods:
    """Test helper methods."""
    
    @pytest.mark.asyncio
    async def test_check_email_exists_true(self, auth_service, mock_user_repository, sample_user):
        """Test email existence check returns True."""
        mock_user_repository.get_by_email = AsyncMock(return_value=sample_user)
        
        result = await auth_service.check_email_exists("test@example.com")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_email_exists_false(self, auth_service, mock_user_repository):
        """Test email existence check returns False."""
        mock_user_repository.get_by_email = AsyncMock(side_effect=UserNotFoundError("test@example.com"))
        
        result = await auth_service.check_email_exists("test@example.com")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_handle_exists_true(self, auth_service, mock_user_repository, sample_user):
        """Test handle existence check returns True."""
        mock_user_repository.get_by_handle = AsyncMock(return_value=sample_user)
        
        result = await auth_service.check_handle_exists("testuser")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_handle_exists_false(self, auth_service, mock_user_repository):
        """Test handle existence check returns False."""
        mock_user_repository.get_by_handle = AsyncMock(side_effect=UserNotFoundError("testuser"))
        
        result = await auth_service.check_handle_exists("testuser")
        
        assert result is False