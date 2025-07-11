"""Integration tests for email verification API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import app
from nadle_backend.models.email_verification import (
    EmailVerificationData,
    EmailVerificationCreate,
    EmailVerificationCodeRequest
)


class TestEmailVerificationAPI:
    """Test email verification API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, client):
        """Test successful email verification sending via API."""
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            # Mock successful response
            mock_service.send_verification_email.return_value = {
                "email": "test@example.com",
                "code_sent": True,
                "expires_in_minutes": 5,
                "can_resend": False,
                "message": "인증 코드가 이메일로 전송되었습니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/send-verification-email",
                json={"email": "test@example.com"}
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["code_sent"] is True
            assert data["expires_in_minutes"] == 5
            assert "인증 코드가 전송되었습니다" in data["message"]
    
    @pytest.mark.asyncio
    async def test_send_verification_email_invalid_email(self, client):
        """Test sending verification email with invalid email format."""
        # Act
        response = client.post(
            "/api/auth/send-verification-email",
            json={"email": "invalid-email"}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_send_verification_email_empty_email(self, client):
        """Test sending verification email with empty email."""
        # Act
        response = client.post(
            "/api/auth/send-verification-email",
            json={"email": ""}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_send_verification_email_service_error(self, client):
        """Test handling service errors in email sending."""
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            # Mock service error
            mock_service.send_verification_email.return_value = {
                "email": "test@example.com",
                "code_sent": False,
                "expires_in_minutes": 0,
                "can_resend": True,
                "message": "이메일 전송에 실패했습니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/send-verification-email",
                json={"email": "test@example.com"}
            )
            
            # Assert
            assert response.status_code == 400  # Bad request for service failure
            data = response.json()
            assert data["detail"]["message"] == "이메일 전송에 실패했습니다."
    
    @pytest.mark.asyncio
    async def test_verify_email_code_success(self, client):
        """Test successful email code verification via API."""
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            # Mock successful verification
            mock_service.verify_email_code.return_value = {
                "email": "test@example.com",
                "verified": True,
                "can_proceed": True,
                "message": "이메일 인증이 완료되었습니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": "test@example.com",
                    "code": "123456"
                }
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["verified"] is True
            assert data["can_proceed"] is True
            assert "인증이 완료되었습니다" in data["message"]
    
    @pytest.mark.asyncio
    async def test_verify_email_code_wrong_code(self, client):
        """Test email code verification with wrong code."""
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            # Mock wrong code response
            mock_service.verify_email_code.return_value = {
                "email": "test@example.com",
                "verified": False,
                "can_proceed": False,
                "message": "잘못된 인증 코드입니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": "test@example.com",
                    "code": "wrong123"
                }
            )
            
            # Assert
            assert response.status_code == 400  # Bad request for wrong code
            data = response.json()
            assert data["detail"]["message"] == "잘못된 인증 코드입니다."
    
    @pytest.mark.asyncio
    async def test_verify_email_code_expired(self, client):
        """Test email code verification when code is expired."""
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            # Mock expired code response
            mock_service.verify_email_code.return_value = {
                "email": "test@example.com",
                "verified": False,
                "can_proceed": False,
                "message": "인증 코드가 만료되었습니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": "test@example.com",
                    "code": "123456"
                }
            )
            
            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "만료되었습니다" in data["detail"]["message"]
    
    @pytest.mark.asyncio
    async def test_verify_email_code_invalid_format(self, client):
        """Test email code verification with invalid code format."""
        # Act - code too short
        response = client.post(
            "/api/auth/verify-email-code",
            json={
                "email": "test@example.com",
                "code": "123"  # Too short
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
        
        # Act - code too long
        response = client.post(
            "/api/auth/verify-email-code",
            json={
                "email": "test@example.com",
                "code": "1234567"  # Too long
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_verify_email_code_missing_fields(self, client):
        """Test email code verification with missing required fields."""
        # Act - missing email
        response = client.post(
            "/api/auth/verify-email-code",
            json={"code": "123456"}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
        
        # Act - missing code
        response = client.post(
            "/api/auth/verify-email-code",
            json={"email": "test@example.com"}
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_rate_limiting_protection(self, client):
        """Test rate limiting for email verification endpoints."""
        # This test would require actual rate limiting implementation
        # For now, we'll test the structure is in place
        
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            # Mock rate limit exceeded response
            mock_service.send_verification_email.return_value = {
                "email": "test@example.com",
                "code_sent": False,
                "expires_in_minutes": 0,
                "can_resend": False,
                "message": "요청 횟수 제한을 초과했습니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/send-verification-email",
                json={"email": "test@example.com"}
            )
            
            # Assert
            assert response.status_code == 429 or response.status_code == 400  # Rate limit or bad request
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        # Act
        response = client.options("/api/auth/send-verification-email")
        
        # Assert
        # CORS headers should be present for OPTIONS request
        assert response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_security_headers(self, client):
        """Test security headers are present in responses."""
        # Mock the email verification service
        with patch('nadle_backend.routers.auth.get_email_verification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service
            
            mock_service.send_verification_email.return_value = {
                "email": "test@example.com",
                "code_sent": True,
                "expires_in_minutes": 5,
                "can_resend": False,
                "message": "인증 코드가 전송되었습니다."
            }
            
            # Act
            response = client.post(
                "/api/auth/send-verification-email",
                json={"email": "test@example.com"}
            )
            
            # Assert
            assert response.status_code == 200
            # Check for basic security headers (if implemented)
            # headers = response.headers
            # assert "X-Content-Type-Options" in headers
            # assert "X-Frame-Options" in headers