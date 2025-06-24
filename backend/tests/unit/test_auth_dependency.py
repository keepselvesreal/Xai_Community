import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from src.dependencies.auth import (
    get_jwt_manager,
    get_password_manager,
    get_user_repository,
    extract_token_from_header,
    get_current_user,
    get_current_active_user,
    get_optional_current_user,
    require_admin_user
)
from src.models.core import User
from src.utils.jwt import JWTManager, TokenType
from src.utils.password import PasswordManager
from src.repositories.user_repository import UserRepository
from src.exceptions.auth import InvalidTokenError, ExpiredTokenError


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
def mock_user_repository():
    """Create mock user repository."""
    repo = MagicMock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = MagicMock()
    user.id = "507f1f77bcf86cd799439011"
    user.email = "test@example.com"
    user.handle = "testuser"
    user.status = "active"
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    """Create mock admin user."""
    user = MagicMock()
    user.id = "507f1f77bcf86cd799439012"
    user.email = "admin@example.com"
    user.handle = "admin"
    user.status = "active"
    user.is_admin = True
    return user


class TestDependencyProviders:
    """Test dependency provider functions."""
    
    def test_get_jwt_manager(self):
        """Test JWT manager dependency provider."""
        manager = get_jwt_manager()
        assert isinstance(manager, JWTManager)
        assert manager.algorithm == "HS256"
    
    def test_get_password_manager(self):
        """Test password manager dependency provider."""
        manager = get_password_manager()
        assert isinstance(manager, PasswordManager)
    
    def test_get_user_repository(self):
        """Test user repository dependency provider."""
        repo = get_user_repository()
        assert isinstance(repo, UserRepository)


class TestTokenExtraction:
    """Test token extraction from HTTP headers."""
    
    def test_extract_token_from_header_valid_bearer(self):
        """Test extracting valid bearer token."""
        credentials = MagicMock()
        credentials.credentials = "valid_jwt_token_here"
        
        token = extract_token_from_header(credentials)
        assert token == "valid_jwt_token_here"
    
    def test_extract_token_from_header_none_credentials(self):
        """Test extracting token when credentials is None."""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(None)
        
        assert exc_info.value.status_code == 401
        assert "Authorization header is required" in str(exc_info.value.detail)
    
    def test_extract_token_from_header_no_credentials(self):
        """Test extracting token when no credentials provided."""
        credentials = MagicMock()
        credentials.credentials = None
        
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header" in str(exc_info.value.detail)


class TestCurrentUserDependency:
    """Test current user dependency functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_jwt_manager, mock_user_repository, mock_user):
        """Test successful current user retrieval."""
        token = "valid_jwt_token"
        
        # Mock JWT verification
        mock_jwt_manager.verify_token.return_value = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "type": TokenType.ACCESS.value
        }
        
        # Mock user repository
        mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)
        
        # Test dependency
        user = await get_current_user(token, mock_jwt_manager, mock_user_repository)
        
        assert user == mock_user
        mock_jwt_manager.verify_token.assert_called_once_with(token, expected_type=TokenType.ACCESS)
        mock_user_repository.get_by_id.assert_called_once_with(mock_user.id)
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_jwt_manager, mock_user_repository):
        """Test current user retrieval with invalid token."""
        token = "invalid_jwt_token"
        
        # Mock JWT verification failure
        mock_jwt_manager.verify_token.side_effect = InvalidTokenError("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_jwt_manager, mock_user_repository)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, mock_jwt_manager, mock_user_repository):
        """Test current user retrieval with expired token."""
        token = "expired_jwt_token"
        
        # Mock JWT verification failure
        mock_jwt_manager.verify_token.side_effect = ExpiredTokenError("Token expired")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_jwt_manager, mock_user_repository)
        
        assert exc_info.value.status_code == 401
        assert "Token expired" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_jwt_manager, mock_user_repository):
        """Test current user retrieval when user not found."""
        token = "valid_jwt_token"
        user_id = "nonexistent_user_id"
        
        # Mock JWT verification success
        mock_jwt_manager.verify_token.return_value = {
            "sub": user_id,
            "email": "test@example.com",
            "type": TokenType.ACCESS.value
        }
        
        # Mock user not found
        from src.exceptions.user import UserNotFoundError
        mock_user_repository.get_by_id = AsyncMock(side_effect=UserNotFoundError(user_id))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_jwt_manager, mock_user_repository)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_wrong_token_type(self, mock_jwt_manager, mock_user_repository):
        """Test current user retrieval with refresh token instead of access token."""
        token = "refresh_jwt_token"
        
        # Mock JWT verification with wrong token type
        from src.exceptions.auth import InvalidTokenTypeError
        mock_jwt_manager.verify_token.side_effect = InvalidTokenTypeError("access", "refresh")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_jwt_manager, mock_user_repository)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)


class TestActiveUserDependency:
    """Test active user dependency functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, mock_user):
        """Test successful active user retrieval."""
        mock_user.status = "active"
        
        user = await get_current_active_user(mock_user)
        assert user == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, mock_user):
        """Test active user retrieval with inactive user."""
        mock_user.status = "inactive"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_suspended(self, mock_user):
        """Test active user retrieval with suspended user."""
        mock_user.status = "suspended"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_user)
        
        assert exc_info.value.status_code == 400
        assert "User account is suspended" in str(exc_info.value.detail)


class TestOptionalUserDependency:
    """Test optional user dependency functions."""
    
    @pytest.mark.asyncio
    async def test_get_optional_current_user_with_valid_token(self, mock_jwt_manager, mock_user_repository, mock_user):
        """Test optional user retrieval with valid token."""
        token = "valid_jwt_token"
        
        # Mock successful token verification and user retrieval
        mock_jwt_manager.verify_token.return_value = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "type": TokenType.ACCESS.value
        }
        mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)
        
        user = await get_optional_current_user(token, mock_jwt_manager, mock_user_repository)
        assert user == mock_user
    
    @pytest.mark.asyncio
    async def test_get_optional_current_user_with_invalid_token(self, mock_jwt_manager, mock_user_repository):
        """Test optional user retrieval with invalid token."""
        token = "invalid_jwt_token"
        
        # Mock token verification failure
        mock_jwt_manager.verify_token.side_effect = InvalidTokenError("Invalid token")
        
        # Should return None instead of raising exception
        user = await get_optional_current_user(token, mock_jwt_manager, mock_user_repository)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_optional_current_user_with_no_token(self, mock_jwt_manager, mock_user_repository):
        """Test optional user retrieval with no token."""
        token = None
        
        user = await get_optional_current_user(token, mock_jwt_manager, mock_user_repository)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_optional_current_user_user_not_found(self, mock_jwt_manager, mock_user_repository):
        """Test optional user retrieval when user not found."""
        token = "valid_jwt_token"
        
        # Mock successful token verification but user not found
        mock_jwt_manager.verify_token.return_value = {
            "sub": "nonexistent_user_id",
            "email": "test@example.com",
            "type": TokenType.ACCESS.value
        }
        
        from src.exceptions.user import UserNotFoundError
        mock_user_repository.get_by_id = AsyncMock(side_effect=UserNotFoundError("user_id"))
        
        # Should return None instead of raising exception
        user = await get_optional_current_user(token, mock_jwt_manager, mock_user_repository)
        assert user is None


class TestAdminUserDependency:
    """Test admin user dependency functions."""
    
    @pytest.mark.asyncio
    async def test_require_admin_user_success(self, mock_admin_user):
        """Test successful admin user requirement."""
        mock_admin_user.is_admin = True
        
        user = await require_admin_user(mock_admin_user)
        assert user == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_require_admin_user_not_admin(self, mock_user):
        """Test admin user requirement with regular user."""
        mock_user.is_admin = False
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin_user(mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_require_admin_user_no_admin_attribute(self, mock_user):
        """Test admin user requirement with user missing is_admin attribute."""
        # Remove is_admin attribute to simulate old user model
        del mock_user.is_admin
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin_user(mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)


class TestDependencyIntegration:
    """Test dependency integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_auth_flow_success(self, mock_jwt_manager, mock_user_repository, mock_user):
        """Test complete authentication flow."""
        # Create HTTP Bearer token
        credentials = MagicMock()
        credentials.credentials = "valid_jwt_token"
        
        # Mock JWT verification
        mock_jwt_manager.verify_token.return_value = {
            "sub": mock_user.id,
            "email": mock_user.email,
            "type": TokenType.ACCESS.value
        }
        
        # Mock user repository
        mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)
        mock_user.status = "active"
        
        # Test flow: extract token -> get current user -> verify active
        token = extract_token_from_header(credentials)
        current_user = await get_current_user(token, mock_jwt_manager, mock_user_repository)
        active_user = await get_current_active_user(current_user)
        
        assert active_user == mock_user
    
    @pytest.mark.asyncio
    async def test_admin_auth_flow_success(self, mock_jwt_manager, mock_user_repository, mock_admin_user):
        """Test complete admin authentication flow."""
        # Create HTTP Bearer token
        credentials = MagicMock()
        credentials.credentials = "admin_jwt_token"
        
        # Mock JWT verification
        mock_jwt_manager.verify_token.return_value = {
            "sub": mock_admin_user.id,
            "email": mock_admin_user.email,
            "type": TokenType.ACCESS.value
        }
        
        # Mock user repository
        mock_user_repository.get_by_id = AsyncMock(return_value=mock_admin_user)
        mock_admin_user.status = "active"
        mock_admin_user.is_admin = True
        
        # Test flow: extract token -> get current user -> verify active -> verify admin
        token = extract_token_from_header(credentials)
        current_user = await get_current_user(token, mock_jwt_manager, mock_user_repository)
        active_user = await get_current_active_user(current_user)
        admin_user = await require_admin_user(active_user)
        
        assert admin_user == mock_admin_user
    
    @pytest.mark.asyncio
    async def test_optional_auth_flow_no_auth(self, mock_jwt_manager, mock_user_repository):
        """Test optional authentication flow with no authentication."""
        # Test optional user dependency with no token
        user = await get_optional_current_user(None, mock_jwt_manager, mock_user_repository)
        assert user is None