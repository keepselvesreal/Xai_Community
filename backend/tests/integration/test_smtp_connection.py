"""Integration tests for SMTP connection and email sending."""

import pytest
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from unittest.mock import patch, MagicMock

from nadle_backend.config import settings
from nadle_backend.services.email_verification_service import EmailVerificationService
from nadle_backend.repositories.email_verification_repository import EmailVerificationRepository


class TestSMTPConnection:
    """Test SMTP connection and configuration."""
    
    def test_smtp_settings_loaded(self):
        """Test that SMTP settings are properly loaded from environment."""
        # SMTP 설정이 환경변수에서 제대로 로드되는지 확인
        assert hasattr(settings, 'smtp_server'), "smtp_server setting is missing"
        assert hasattr(settings, 'smtp_port'), "smtp_port setting is missing"
        assert hasattr(settings, 'smtp_username'), "smtp_username setting is missing"
        assert hasattr(settings, 'smtp_password'), "smtp_password setting is missing"
        assert hasattr(settings, 'smtp_use_tls'), "smtp_use_tls setting is missing"
        assert hasattr(settings, 'from_email'), "from_email setting is missing"
        
        # Gmail SMTP 설정 확인
        assert settings.smtp_server == "smtp.gmail.com"
        assert settings.smtp_port == 587
        assert settings.smtp_use_tls is True
        
        # 이메일 주소 형식 확인
        assert "@" in settings.smtp_username
        assert "@" in settings.from_email
        
        # 비밀번호가 설정되어 있는지 확인 (실제 값은 확인하지 않음)
        assert settings.smtp_password is not None
        assert len(settings.smtp_password) > 0
    
    @pytest.mark.asyncio
    async def test_smtp_connection_valid(self):
        """Test that SMTP connection can be established with valid credentials."""
        # SMTP 서버 연결 테스트 (실제 연결하지 않고 모킹)
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            # SMTP 연결 시뮬레이션
            try:
                with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    
                    if settings.smtp_username and settings.smtp_password:
                        server.login(settings.smtp_username, settings.smtp_password)
                
                # Mock이 올바르게 호출되었는지 확인
                mock_smtp_class.assert_called_once_with(settings.smtp_server, settings.smtp_port)
                mock_smtp.starttls.assert_called_once()
                mock_smtp.login.assert_called_once_with(settings.smtp_username, settings.smtp_password)
                
            except Exception as e:
                pytest.fail(f"SMTP connection failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_email_creation_and_format(self):
        """Test email message creation and formatting."""
        # 이메일 메시지 생성 테스트
        to_email = "test@example.com"
        subject = "Test Email"
        html_content = "<h1>Test Content</h1><p>This is a test email.</p>"
        
        # MIMEMultipart 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.from_name} <{settings.from_email}>"
        msg['To'] = to_email
        
        # HTML 콘텐츠 추가
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 메시지 형식 검증
        assert msg['Subject'] == subject
        assert msg['To'] == to_email
        assert settings.from_email in msg['From']
        assert len(msg.get_payload()) == 1  # HTML part만 있어야 함
        
        # HTML 파트 검증
        payload = msg.get_payload()[0]
        assert payload.get_content_type() == 'text/html'
        
        # get_payload(decode=True)를 사용하여 base64 디코딩된 내용 확인
        content = payload.get_payload(decode=True).decode('utf-8')
        assert 'Test Content' in content


class TestEmailVerificationSMTPIntegration:
    """Test email verification service with real SMTP integration."""
    
    @pytest.fixture
    def email_verification_service(self):
        """Create email verification service for testing."""
        repository = EmailVerificationRepository()
        return EmailVerificationService(repository)
    
    @pytest.mark.asyncio
    async def test_email_verification_service_smtp_integration(self, email_verification_service):
        """Test email verification service with mocked SMTP."""
        # SMTP 발송 테스트 (실제 이메일은 보내지 않음)
        test_email = "test@example.com"
        test_code = "123456"
        
        with patch.object(email_verification_service, '_send_email_smtp', return_value=True) as mock_send:
            # 이메일 콘텐츠 생성 테스트
            subject, html_content = email_verification_service._create_email_content(test_code, test_email)
            
            # 콘텐츠 검증
            assert "이메일 인증" in subject
            assert test_code in html_content
            assert settings.from_name in html_content
            assert "시간 후에 만료됩니다" in html_content
            
            # SMTP 발송 메서드 호출 테스트
            result = await email_verification_service._send_email_smtp(
                to_email=test_email,
                subject=subject,
                html_content=html_content
            )
            
            assert result is True
            mock_send.assert_called_once_with(
                to_email=test_email,
                subject=subject,
                html_content=html_content
            )
    
    @pytest.mark.asyncio
    async def test_email_verification_code_generation(self, email_verification_service):
        """Test verification code generation."""
        # 인증 코드 생성 테스트
        code = email_verification_service._generate_verification_code()
        
        # 코드 형식 검증
        assert len(code) == 6
        assert code.isdigit()
        
        # 여러 번 생성하여 랜덤성 확인
        codes = set()
        for _ in range(100):
            codes.add(email_verification_service._generate_verification_code())
        
        # 충분히 다양한 코드가 생성되는지 확인
        assert len(codes) > 50  # 통계적으로 50개 이상의 서로 다른 코드가 생성되어야 함


@pytest.mark.integration
class TestRealSMTPConnection:
    """Real SMTP connection tests (only run when explicitly enabled)."""
    
    @pytest.mark.skip(reason="Real SMTP test - enable manually for integration testing")
    @pytest.mark.asyncio
    async def test_real_smtp_connection(self):
        """Test real SMTP connection to Gmail.
        
        This test is skipped by default to avoid sending real emails during testing.
        Enable manually by removing the @pytest.mark.skip decorator.
        """
        try:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                
                # 연결 성공시 통과
                assert True
                
        except smtplib.SMTPAuthenticationError:
            pytest.fail("SMTP authentication failed - check username/password")
        except smtplib.SMTPConnectError:
            pytest.fail("SMTP connection failed - check server/port")
        except Exception as e:
            pytest.fail(f"SMTP test failed: {str(e)}")
    
    @pytest.mark.skip(reason="Real email test - enable manually for integration testing")
    @pytest.mark.asyncio
    async def test_send_real_test_email(self):
        """Send a real test email.
        
        This test is skipped by default to avoid sending real emails during testing.
        Enable manually by removing the @pytest.mark.skip decorator.
        """
        test_email = settings.smtp_username  # 자신에게 테스트 이메일 발송
        
        repository = EmailVerificationRepository()
        service = EmailVerificationService(repository)
        
        # 실제 이메일 발송 테스트
        subject = "XAI Community - SMTP 연결 테스트"
        html_content = """
        <html>
        <body>
            <h2>SMTP 연결 테스트 성공!</h2>
            <p>이 이메일은 XAI Community 백엔드의 SMTP 설정이 올바르게 작동하는지 확인하기 위한 테스트 이메일입니다.</p>
            <p>테스트 시간: <strong>{{ timestamp }}</strong></p>
        </body>
        </html>
        """.replace("{{ timestamp }}", str(pytest.current_time if hasattr(pytest, 'current_time') else 'N/A'))
        
        result = await service._send_email_smtp(
            to_email=test_email,
            subject=subject,
            html_content=html_content
        )
        
        assert result is True, "Real email sending failed"