"""Enhanced integration tests for authentication router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from src.exceptions.auth import InvalidCredentialsError
from src.exceptions.user import EmailAlreadyExistsError, HandleAlreadyExistsError, UserNotFoundError


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    service = MagicMock()
    service.register_user = AsyncMock()
    service.login = AsyncMock()
    service.refresh_access_token = AsyncMock()
    service.get_user_profile = AsyncMock()
    service.update_user_profile = AsyncMock()
    service.change_password = AsyncMock()
    service.deactivate_user = AsyncMock()
    service.list_users = AsyncMock()
    service.suspend_user = AsyncMock()
    service.activate_user = AsyncMock()
    service.delete_user = AsyncMock()
    return service


@pytest.fixture
def app_with_auth(mock_auth_service):
    """Create test app with mocked auth service."""
    from src.routers.auth import router, get_auth_service
    
    app = FastAPI()
    
    def get_mock_auth_service():
        return mock_auth_service
    
    app.dependency_overrides[get_auth_service] = get_mock_auth_service
    app.include_router(router, prefix="/auth")
    
    return app


@pytest.fixture
def client(app_with_auth):
    """Create test client."""
    return TestClient(app_with_auth)


class TestUserRegistration:
    """Test user registration endpoints."""
    
    def test_register_user_success(self, client, mock_auth_service):
        """Test successful user registration."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "user_handle": "testuser",
            "password": "testpass123",
            "display_name": "Test User"
        }
        
        mock_auth_service.register_user.return_value = {
            "id": "user123",
            "email": "test@example.com",
            "user_handle": "testuser",
            "display_name": "Test User",
            "status": "active"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["user_handle"] == "testuser"
        assert "password" not in data  # Password should not be returned
        mock_auth_service.register_user.assert_called_once()
    
    def test_register_user_email_exists(self, client, mock_auth_service):
        """Test registration with existing email."""
        # Arrange
        user_data = {
            "email": "existing@example.com",
            "user_handle": "newuser",
            "password": "testpass123"
        }
        
        mock_auth_service.register_user.side_effect = EmailAlreadyExistsError("existing@example.com")
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"].lower()
    
    def test_register_user_handle_exists(self, client, mock_auth_service):
        """Test registration with existing user handle."""
        # Arrange
        user_data = {
            "email": "new@example.com",
            "user_handle": "existinguser",
            "password": "testpass123"
        }
        
        mock_auth_service.register_user.side_effect = HandleAlreadyExistsError("existinguser")
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 400
        assert "handle already exists" in response.json()["detail"].lower()
    
    def test_register_user_invalid_data(self, client, mock_auth_service):
        """Test registration with invalid data."""
        # Arrange
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "user_handle": "ab",       # Too short
            "password": "123"          # Too short
        }
        
        # Act
        response = client.post("/auth/register", json=invalid_data)
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login endpoints."""
    
    def test_login_success(self, client, mock_auth_service):
        """Test successful login."""
        # Arrange
        login_data = {
            "username": "test@example.com",
            "password": "testpass123"
        }
        
        mock_auth_service.login.return_value = {
            "user": {
                "id": "user123",
                "email": "test@example.com",
                "user_handle": "testuser"
            },
            "access_token": "access_token_value",
            "refresh_token": "refresh_token_value",
            "token_type": "bearer"
        }
        
        # Act
        response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token_value"
        assert data["token_type"] == "bearer"
        assert "user" in data
        mock_auth_service.login.assert_called_once_with("test@example.com", "testpass123")
    
    def test_login_invalid_credentials(self, client, mock_auth_service):
        """Test login with invalid credentials."""
        # Arrange
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        
        mock_auth_service.login.side_effect = InvalidCredentialsError()
        
        # Act
        response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
    
    def test_login_missing_data(self, client, mock_auth_service):
        """Test login with missing data."""
        # Arrange
        login_data = {
            "username": "test@example.com"
            # Missing password
        }
        
        # Act
        response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestTokenRefresh:
    """Test token refresh endpoints."""
    
    def test_refresh_token_success(self, client, mock_auth_service):
        """Test successful token refresh."""
        # Arrange
        refresh_data = {"refresh_token": "valid_refresh_token"}
        
        mock_auth_service.refresh_access_token.return_value = {
            "access_token": "new_access_token",
            "token_type": "bearer"
        }
        
        # Act
        response = client.post("/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["token_type"] == "bearer"
        mock_auth_service.refresh_access_token.assert_called_once_with("valid_refresh_token")
    
    def test_refresh_token_invalid(self, client, mock_auth_service):
        """Test token refresh with invalid token."""
        # Arrange
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        
        mock_auth_service.refresh_access_token.side_effect = InvalidCredentialsError()
        
        # Act
        response = client.post("/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 401


class TestUserProfile:
    """Test user profile endpoints."""
    
    def test_get_profile_success(self, client, mock_auth_service):
        """Test successful profile retrieval."""
        # Arrange
        headers = {"Authorization": "Bearer valid_access_token"}
        
        with client as c:
            # Mock the get_current_active_user dependency
            from src.dependencies.auth import get_current_active_user
            
            mock_user = MagicMock()
            mock_user.id = "user123"
            mock_user.email = "test@example.com"
            mock_user.user_handle = "testuser"
            
            def get_mock_current_user():
                return mock_user
            
            c.app.dependency_overrides[get_current_active_user] = get_mock_current_user
            
            mock_auth_service.get_user_profile.return_value = {
                "id": "user123",
                "email": "test@example.com",
                "user_handle": "testuser",
                "display_name": "Test User",
                "bio": "Test bio"
            }
            
            # Act
            response = c.get("/auth/profile", headers=headers)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["user_handle"] == "testuser"
    
    def test_get_profile_unauthorized(self, client, mock_auth_service):
        """Test profile retrieval without authentication."""
        # Act
        response = client.get("/auth/profile")
        
        # Assert
        assert response.status_code == 401
    
    def test_update_profile_success(self, client, mock_auth_service):
        """Test successful profile update."""
        # Arrange
        headers = {"Authorization": "Bearer valid_access_token"}
        update_data = {
            "display_name": "Updated Name",
            "bio": "Updated bio"
        }
        
        with client as c:
            from src.dependencies.auth import get_current_active_user
            
            mock_user = MagicMock()
            mock_user.id = "user123"
            
            def get_mock_current_user():
                return mock_user
            
            c.app.dependency_overrides[get_current_active_user] = get_mock_current_user
            
            mock_auth_service.update_user_profile.return_value = {
                "id": "user123",
                "email": "test@example.com",
                "user_handle": "testuser",
                "display_name": "Updated Name",
                "bio": "Updated bio"
            }
            
            # Act
            response = c.put("/auth/profile", json=update_data, headers=headers)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Name"
            assert data["bio"] == "Updated bio"


class TestPasswordChange:
    """Test password change endpoints."""
    
    def test_change_password_success(self, client, mock_auth_service):
        """Test successful password change."""
        # Arrange
        headers = {"Authorization": "Bearer valid_access_token"}
        password_data = {
            "current_password": "oldpass123",
            "new_password": "newpass123"
        }
        
        with client as c:
            from src.dependencies.auth import get_current_active_user
            
            mock_user = MagicMock()
            mock_user.id = "user123"
            
            def get_mock_current_user():
                return mock_user
            
            c.app.dependency_overrides[get_current_active_user] = get_mock_current_user
            
            mock_auth_service.change_password.return_value = True
            
            # Act
            response = c.post("/auth/change-password", json=password_data, headers=headers)
            
            # Assert
            assert response.status_code == 200
            assert response.json()["message"] == "Password changed successfully"
            mock_auth_service.change_password.assert_called_once()
    
    def test_change_password_wrong_current(self, client, mock_auth_service):
        """Test password change with wrong current password."""
        # Arrange
        headers = {"Authorization": "Bearer valid_access_token"}
        password_data = {
            "current_password": "wrongpass",
            "new_password": "newpass123"
        }
        
        with client as c:
            from src.dependencies.auth import get_current_active_user
            
            mock_user = MagicMock()
            mock_user.id = "user123"
            
            def get_mock_current_user():
                return mock_user
            
            c.app.dependency_overrides[get_current_active_user] = get_mock_current_user
            
            mock_auth_service.change_password.side_effect = InvalidCredentialsError()
            
            # Act
            response = c.post("/auth/change-password", json=password_data, headers=headers)
            
            # Assert
            assert response.status_code == 401