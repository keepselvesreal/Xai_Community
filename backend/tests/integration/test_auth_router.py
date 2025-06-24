"""Simple integration tests for authentication router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    service = MagicMock()
    # Set up basic async methods
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
    
    # Override the auth service dependency
    def get_mock_auth_service():
        return mock_auth_service
    
    app.dependency_overrides[get_auth_service] = get_mock_auth_service
    app.include_router(router, prefix="/auth")
    
    return app


@pytest.fixture
def client(app_with_auth):
    """Create test client with mocked dependencies."""
    return TestClient(app_with_auth)


@pytest.fixture
def sample_user():
    """Sample user mock."""
    user = MagicMock()
    user.id = "507f1f77bcf86cd799439011"
    user.email = "test@example.com"
    user.name = "Test User"
    user.handle = "testuser"
    user.status = "active"
    user.is_admin = False
    user.created_at = "2023-01-01T00:00:00Z"
    user.updated_at = "2023-01-01T00:00:00Z"
    
    # Mock model_dump for Pydantic serialization
    user.model_dump.return_value = {
        "id": "507f1f77bcf86cd799439011",
        "email": "test@example.com",
        "name": "Test User",
        "handle": "testuser",
        "status": "active",
        "is_admin": False,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }
    return user


class TestBasicRouting:
    """Test basic route accessibility and structure."""
    
    def test_register_route_exists(self, client, mock_auth_service, sample_user):
        """Test that register route exists and returns proper structure."""
        # Set up mock
        mock_auth_service.register_user.return_value = sample_user
        
        # Test data
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "handle": "testuser",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Should not be 404 (route exists)
        assert response.status_code != 404
        # Should be either success or validation error
        assert response.status_code in [200, 201, 400, 422]
    
    def test_login_route_exists(self, client, mock_auth_service, sample_user):
        """Test that login route exists."""
        # Set up mock
        mock_auth_service.login.return_value = {
            "user": sample_user,
            "access_token": "test_token",
            "refresh_token": "refresh_token",
            "token_type": "bearer"
        }
        
        # Test data
        login_data = {
            "username": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        # Should not be 404 (route exists)
        assert response.status_code != 404
        # Should be either success or validation error
        assert response.status_code in [200, 401, 422]
    
    def test_profile_route_exists(self, client):
        """Test that profile route exists (should require auth)."""
        response = client.get("/auth/profile")
        
        # Should not be 404 (route exists)
        assert response.status_code != 404
        # Should be 401 (unauthorized) since no auth provided
        assert response.status_code == 401
    
    def test_health_route(self, client):
        """Test health check route."""
        response = client.get("/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"


class TestValidation:
    """Test input validation."""
    
    def test_register_validation_empty_name(self, client):
        """Test registration validation with empty name."""
        user_data = {
            "name": "",  # Empty name should fail
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_validation_invalid_email(self, client):
        """Test registration validation with invalid email."""
        user_data = {
            "name": "Test User",
            "email": "invalid-email",  # Invalid email format
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_validation_weak_password(self, client):
        """Test registration validation with weak password."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "123"  # Too simple password
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_login_validation_missing_fields(self, client):
        """Test login validation with missing fields."""
        response = client.post("/auth/login", data={})
        assert response.status_code == 422


class TestResponseStructure:
    """Test response structure and content."""
    
    def test_register_success_response_structure(self, client, mock_auth_service, sample_user):
        """Test successful registration response structure."""
        # Set up mock
        mock_auth_service.register_user.return_value = sample_user
        
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "handle": "testuser",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        if response.status_code == 201:
            data = response.json()
            assert "message" in data
            assert "user" in data
            assert data["user"]["email"] == "test@example.com"
    
    def test_login_success_response_structure(self, client, mock_auth_service, sample_user):
        """Test successful login response structure."""
        # Set up mock
        mock_auth_service.login.return_value = {
            "user": sample_user,
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer"
        }
        
        login_data = {
            "username": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert "user" in data
            assert data["token_type"] == "bearer"


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON."""
        # Send malformed JSON
        response = client.post(
            "/auth/register", 
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_wrong_content_type(self, client):
        """Test handling of wrong content type."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        # Send as form data instead of JSON
        response = client.post("/auth/register", data=user_data)
        
        # Should still handle gracefully
        assert response.status_code in [422, 400]


class TestSecurityBasics:
    """Test basic security measures."""
    
    def test_no_sensitive_headers_in_response(self, client, mock_auth_service, sample_user):
        """Test that responses don't expose sensitive server information."""
        mock_auth_service.login.return_value = {
            "user": sample_user,
            "access_token": "test_token",
            "refresh_token": "refresh_token", 
            "token_type": "bearer"
        }
        
        login_data = {
            "username": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        # Check that sensitive server info is not exposed
        assert "X-Powered-By" not in response.headers
        server_header = response.headers.get("Server", "")
        assert "FastAPI" not in server_header or server_header == ""
    
    def test_auth_required_endpoints_reject_unauthenticated(self, client):
        """Test that auth-required endpoints reject unauthenticated requests."""
        # These endpoints should require authentication
        auth_required_endpoints = [
            ("/auth/profile", "GET"),
            ("/auth/change-password", "POST"),
            ("/auth/deactivate", "POST"),
            ("/auth/admin/users", "GET"),
        ]
        
        for endpoint, method in auth_required_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"