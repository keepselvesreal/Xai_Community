"""Tests for email verification service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from nadle_backend.services.email_verification_service import EmailVerificationService
from nadle_backend.models.email_verification import (
    EmailVerificationData,
    EmailVerificationCreate,
    EmailVerificationResponse,
    EmailVerificationCodeRequest,
    EmailVerificationCodeResponse
)
from nadle_backend.repositories.email_verification_repository import EmailVerificationRepository


class TestEmailVerificationService:
    """Test EmailVerificationService class."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock email verification repository."""
        return Mock(spec=EmailVerificationRepository)
    
    @pytest.fixture
    def email_service(self, mock_repository):
        """Create EmailVerificationService instance with mocked dependencies."""
        return EmailVerificationService(repository=mock_repository)
    
    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, email_service, mock_repository):
        """Test successful email verification sending."""
        # Arrange
        email = "test@example.com"
        request = EmailVerificationCreate(email=email)
        
        # Mock repository methods
        mock_repository.get_by_email = AsyncMock(return_value=None)  # No existing verification
        created_verification = EmailVerificationData.create_verification(
            email=email,
            code="123456"
        )
        mock_repository.create = AsyncMock(return_value=created_verification)
        
        # Mock email sending
        with patch.object(email_service, '_send_email_smtp', new_callable=AsyncMock, return_value=True) as mock_smtp:
            # Act
            result = await email_service.send_verification_email(request)
            
            # Assert
            assert isinstance(result, EmailVerificationResponse)
            assert result.email == email
            assert result.code_sent is True
            assert result.expires_in_minutes == 5
            assert result.can_resend is False
            assert "인증 코드가 전송되었습니다" in result.message
            
            # Verify repository interactions
            mock_repository.get_by_email.assert_called_once_with(email)
            mock_repository.create.assert_called_once()
            mock_smtp.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_verification_email_existing_not_expired(self, email_service, mock_repository):
        """Test sending verification email when existing code is not expired."""
        # Arrange
        email = "test@example.com"
        request = EmailVerificationCreate(email=email)
        
        existing_verification = EmailVerificationData.create_verification(
            email=email,
            code="654321",
            expire_minutes=3  # Still valid
        )
        
        mock_repository.get_by_email = AsyncMock(return_value=existing_verification)
        
        # Act
        result = await email_service.send_verification_email(request)
        
        # Assert
        assert isinstance(result, EmailVerificationResponse)
        assert result.email == email
        assert result.code_sent is False
        assert result.can_resend is False
        assert "이미 전송된 인증 코드가 있습니다" in result.message
        
        # Should not create new verification
        mock_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_verification_email_existing_expired(self, email_service, mock_repository):
        """Test sending verification email when existing code is expired."""
        # Arrange
        email = "test@example.com"
        request = EmailVerificationCreate(email=email)
        
        expired_verification = EmailVerificationData.create_verification(
            email=email,
            code="654321",
            expire_minutes=-1  # Expired
        )
        
        mock_repository.get_by_email = AsyncMock(return_value=expired_verification)
        new_verification = EmailVerificationData.create_verification(
            email=email,
            code="123456"
        )
        mock_repository.create = AsyncMock(return_value=new_verification)
        
        # Mock email sending
        with patch.object(email_service, '_send_email_smtp', new_callable=AsyncMock, return_value=True):
            # Act
            result = await email_service.send_verification_email(request)
            
            # Assert
            assert result.code_sent is True
            mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_verification_email_smtp_failure(self, email_service, mock_repository):
        """Test email verification when SMTP sending fails."""
        # Arrange
        email = "test@example.com"
        request = EmailVerificationCreate(email=email)
        
        mock_repository.get_by_email = AsyncMock(return_value=None)
        
        # Mock email sending failure
        with patch.object(email_service, '_send_email_smtp', new_callable=AsyncMock, return_value=False):
            # Act
            result = await email_service.send_verification_email(request)
            
            # Assert
            assert result.code_sent is False
            assert "이메일 전송에 실패했습니다" in result.message
    
    @pytest.mark.asyncio
    async def test_verify_email_code_success(self, email_service, mock_repository):
        """Test successful email code verification."""
        # Arrange
        email = "test@example.com"
        code = "123456"
        request = EmailVerificationCodeRequest(email=email, code=code)
        
        verification = EmailVerificationData.create_verification(
            email=email,
            code=code,
            expire_minutes=5
        )
        
        mock_repository.get_by_email = AsyncMock(return_value=verification)
        mock_repository.update = AsyncMock(return_value=None)
        
        # Act
        result = await email_service.verify_email_code(request)
        
        # Assert
        assert isinstance(result, EmailVerificationCodeResponse)
        assert result.email == email
        assert result.verified is True
        assert result.can_proceed is True
        assert "이메일 인증이 완료되었습니다" in result.message
        
        # Verify repository interactions
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_email_code_not_found(self, email_service, mock_repository):
        """Test email code verification when verification not found."""
        # Arrange
        email = "test@example.com"
        code = "123456"
        request = EmailVerificationCodeRequest(email=email, code=code)
        
        mock_repository.get_by_email = AsyncMock(return_value=None)
        
        # Act
        result = await email_service.verify_email_code(request)
        
        # Assert
        assert result.verified is False
        assert result.can_proceed is False
        assert "인증 요청을 찾을 수 없습니다" in result.message
    
    @pytest.mark.asyncio
    async def test_verify_email_code_expired(self, email_service, mock_repository):
        """Test email code verification when code is expired."""
        # Arrange
        email = "test@example.com"
        code = "123456"
        request = EmailVerificationCodeRequest(email=email, code=code)
        
        expired_verification = EmailVerificationData.create_verification(
            email=email,
            code=code,
            expire_minutes=-1  # Expired
        )
        
        mock_repository.get_by_email = AsyncMock(return_value=expired_verification)
        
        # Act
        result = await email_service.verify_email_code(request)
        
        # Assert
        assert result.verified is False
        assert result.can_proceed is False
        assert "인증 코드가 만료되었습니다" in result.message
    
    @pytest.mark.asyncio
    async def test_verify_email_code_wrong_code(self, email_service, mock_repository):
        """Test email code verification with wrong code."""
        # Arrange
        email = "test@example.com"
        correct_code = "123456"
        wrong_code = "654321"
        request = EmailVerificationCodeRequest(email=email, code=wrong_code)
        
        verification = EmailVerificationData.create_verification(
            email=email,
            code=correct_code,
            expire_minutes=5
        )
        
        mock_repository.get_by_email = AsyncMock(return_value=verification)
        mock_repository.update = AsyncMock(return_value=None)
        
        # Act
        result = await email_service.verify_email_code(request)
        
        # Assert
        assert result.verified is False
        assert result.can_proceed is False
        assert "잘못된 인증 코드입니다" in result.message
        
        # Should increment attempt count
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_email_code_max_attempts_exceeded(self, email_service, mock_repository):
        """Test email code verification when max attempts exceeded."""
        # Arrange
        email = "test@example.com"
        code = "123456"
        request = EmailVerificationCodeRequest(email=email, code="wrong")
        
        verification = EmailVerificationData.create_verification(
            email=email,
            code=code,
            expire_minutes=5
        )
        verification.attempt_count = 5  # Max attempts reached
        
        mock_repository.get_by_email.return_value = verification
        
        # Act
        result = await email_service.verify_email_code(request)
        
        # Assert
        assert result.verified is False
        assert result.can_proceed is False
        assert "최대 시도 횟수를 초과했습니다" in result.message
    
    @pytest.mark.asyncio
    async def test_resend_verification_email_success(self, email_service, mock_repository):
        """Test successful resending of verification email."""
        # Arrange
        email = "test@example.com"
        request = EmailVerificationCreate(email=email)
        
        # Mock existing expired verification
        expired_verification = EmailVerificationData.create_verification(
            email=email,
            code="654321",
            expire_minutes=-1
        )
        
        mock_repository.get_by_email = AsyncMock(return_value=expired_verification)
        new_verification = EmailVerificationData.create_verification(
            email=email,
            code="123456"
        )
        mock_repository.create = AsyncMock(return_value=new_verification)
        
        # Mock email sending
        with patch.object(email_service, '_send_email_smtp', new_callable=AsyncMock, return_value=True):
            # Act
            result = await email_service.send_verification_email(request)
            
            # Assert
            assert result.code_sent is True
            assert "인증 코드가 전송되었습니다" in result.message
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_verifications(self, email_service, mock_repository):
        """Test cleanup of expired verification codes."""
        # Arrange
        mock_repository.delete_expired = AsyncMock(return_value=5)  # 5 expired records deleted
        
        # Act
        deleted_count = await email_service.cleanup_expired_verifications()
        
        # Assert
        assert deleted_count == 5
        mock_repository.delete_expired.assert_called_once()
    
    def test_generate_verification_code(self, email_service):
        """Test verification code generation."""
        # Act
        code = email_service._generate_verification_code()
        
        # Assert
        assert len(code) == 6
        assert code.isdigit()
        
        # Test uniqueness (run multiple times)
        codes = set()
        for _ in range(100):
            codes.add(email_service._generate_verification_code())
        
        # Should generate diverse codes (not all the same)
        assert len(codes) > 50  # Statistical expectation
    
    def test_create_email_content(self, email_service):
        """Test email content creation."""
        # Act
        subject, html_content = email_service._create_email_content(
            code="123456",
            email="test@example.com"
        )
        
        # Assert
        assert "이메일 인증" in subject
        assert "123456" in html_content
        assert "test@example.com" not in html_content  # Email should not be in content for security
        assert "시간" in html_content  # Expiry time mentioned
    
    @pytest.mark.asyncio
    async def test_send_email_smtp_success(self, email_service):
        """Test SMTP email sending success."""
        # Mock SMTP
        with patch('nadle_backend.services.email_verification_service.smtplib.SMTP') as mock_smtp_class:
            mock_smtp = Mock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            # Act
            result = await email_service._send_email_smtp(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<html>Test</html>"
            )
            
            # Assert
            assert result is True
            mock_smtp.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_smtp_failure(self, email_service):
        """Test SMTP email sending failure."""
        # Mock SMTP to raise exception
        with patch('nadle_backend.services.email_verification_service.smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = Exception("SMTP connection failed")
            
            # Act
            result = await email_service._send_email_smtp(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<html>Test</html>"
            )
            
            # Assert
            assert result is False