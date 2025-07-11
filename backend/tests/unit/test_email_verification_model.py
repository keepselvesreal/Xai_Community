"""Tests for email verification model."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from nadle_backend.models.email_verification import (
    EmailVerification,
    EmailVerificationData,
    EmailVerificationCreate,
    EmailVerificationResponse,
    EmailVerificationCodeRequest,
    EmailVerificationCodeResponse
)


class TestEmailVerificationCreate:
    """Test EmailVerificationCreate model."""
    
    def test_valid_email_verification_create(self):
        """Test creating valid email verification request."""
        data = {
            "email": "test@example.com",
        }
        verification = EmailVerificationCreate(**data)
        assert verification.email == "test@example.com"
    
    def test_invalid_email_format(self):
        """Test invalid email format raises validation error."""
        with pytest.raises(ValidationError):
            EmailVerificationCreate(email="invalid-email")
    
    def test_empty_email(self):
        """Test empty email raises validation error."""
        with pytest.raises(ValidationError):
            EmailVerificationCreate(email="")


class TestEmailVerificationData:
    """Test EmailVerificationData model methods."""
    
    def test_create_verification_class_method(self):
        """Test EmailVerificationData.create_verification class method."""
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456",
            expire_minutes=5
        )
        
        assert verification.email == "test@example.com"
        assert verification.code == "123456"
        assert verification.attempt_count == 0
        assert verification.is_verified is False
        assert verification.created_at is not None
        assert verification.expires_at > datetime.utcnow()
    
    def test_is_expired_method(self):
        """Test is_expired method."""
        # Not expired
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456",
            expire_minutes=5
        )
        assert not verification.is_expired()
        
        # Expired
        verification_expired = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456",
            expire_minutes=-1  # Past expiry
        )
        assert verification_expired.is_expired()
    
    def test_can_attempt_method(self):
        """Test can_attempt method for rate limiting."""
        # Can attempt (under limit)
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456"
        )
        verification.attempt_count = 2
        assert verification.can_attempt()
        
        # Cannot attempt (at limit)
        verification_max = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456"
        )
        verification_max.attempt_count = 5
        assert not verification_max.can_attempt()
    
    def test_increment_attempt_method(self):
        """Test increment_attempt method."""
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456"
        )
        
        verification.increment_attempt()
        assert verification.attempt_count == 1
        assert verification.last_attempt_at is not None
    
    def test_mark_verified_method(self):
        """Test mark_verified method."""
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456"
        )
        
        verification.mark_verified()
        assert verification.is_verified is True
        assert verification.last_attempt_at is not None
    
    def test_time_until_expiry_method(self):
        """Test time_until_expiry method."""
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456",
            expire_minutes=5
        )
        
        # Should return approximately 5 minutes
        minutes = verification.time_until_expiry()
        assert 4 <= minutes <= 5
        
        # Expired verification should return 0
        verification_expired = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456",
            expire_minutes=-1
        )
        assert verification_expired.time_until_expiry() == 0


class TestEmailVerificationResponse:
    """Test EmailVerificationResponse model."""
    
    def test_email_verification_response(self):
        """Test EmailVerificationResponse creation."""
        response = EmailVerificationResponse(
            email="test@example.com",
            code_sent=True,
            expires_in_minutes=5,
            can_resend=True,
            message="인증 코드가 전송되었습니다."
        )
        
        assert response.email == "test@example.com"
        assert response.code_sent is True
        assert response.expires_in_minutes == 5
        assert response.can_resend is True
        assert "인증 코드가 전송되었습니다" in response.message


class TestEmailVerificationCodeRequest:
    """Test EmailVerificationCodeRequest model."""
    
    def test_valid_code_request(self):
        """Test valid verification code request."""
        request = EmailVerificationCodeRequest(
            email="test@example.com",
            code="123456"
        )
        assert request.email == "test@example.com"
        assert request.code == "123456"
    
    def test_invalid_code_length(self):
        """Test invalid code length raises validation error."""
        with pytest.raises(ValidationError):
            EmailVerificationCodeRequest(
                email="test@example.com",
                code="12345"  # Too short
            )
        
        with pytest.raises(ValidationError):
            EmailVerificationCodeRequest(
                email="test@example.com",
                code="1234567"  # Too long
            )


class TestEmailVerificationCodeResponse:
    """Test EmailVerificationCodeResponse model."""
    
    def test_code_response_success(self):
        """Test successful verification response."""
        response = EmailVerificationCodeResponse(
            email="test@example.com",
            verified=True,
            can_proceed=True,
            message="이메일 인증이 완료되었습니다."
        )
        assert response.verified is True
        assert response.can_proceed is True
        
    def test_code_response_failure(self):
        """Test failed verification response."""
        response = EmailVerificationCodeResponse(
            email="test@example.com",
            verified=False,
            can_proceed=False,
            message="잘못된 인증 코드입니다."
        )
        assert response.verified is False
        assert response.can_proceed is False


class TestEmailVerificationValidation:
    """Test email verification code validation."""
    
    def test_valid_verification_code(self):
        """Test valid 6-digit verification code."""
        verification = EmailVerificationData.create_verification(
            email="test@example.com",
            code="123456"
        )
        assert len(verification.code) == 6
        assert verification.code.isdigit()
    
    def test_email_verification_with_korean_domain(self):
        """Test email verification with internationalized domain."""
        verification = EmailVerificationData.create_verification(
            email="test@한국.kr",
            code="123456"
        )
        assert verification.email == "test@한국.kr"


@pytest.mark.asyncio
class TestEmailVerificationDatabase:
    """Test EmailVerification database operations."""
    
    async def test_email_verification_collection_name(self):
        """Test that EmailVerification uses correct collection name."""
        # This will be tested when we implement the actual model
        # For now, we're just defining the expected behavior
        assert hasattr(EmailVerification, 'Settings')
        # The actual collection name should be 'email_verifications'
    
    async def test_email_verification_indexes(self):
        """Test that proper indexes are created."""
        # Test that email and expires_at fields should be indexed
        # This ensures efficient querying and automatic cleanup
        pass  # Will be implemented when model is created