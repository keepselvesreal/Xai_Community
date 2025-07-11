"""
실제 이메일 서비스 연동 테스트

SMTP 서버에 실제로 연결하여 이메일 알림을 전송하는 테스트
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
import smtplib
from email.mime.multipart import MIMEMultipart

from nadle_backend.services.notification_service import NotificationService
from nadle_backend.config import settings


class TestEmailNotificationReal:
    """실제 이메일 서비스 연동 테스트"""

    @pytest.fixture
    def notification_service_with_real_config(self):
        """실제 이메일 설정을 가진 알림 서비스"""
        service = NotificationService()
        
        # 실제 환경변수나 테스트 SMTP 설정 사용
        service.smtp_host = getattr(settings, 'smtp_server', "smtp.gmail.com")
        service.smtp_port = getattr(settings, 'smtp_port', 587)
        service.smtp_user = getattr(settings, 'smtp_username', "")
        service.smtp_password = getattr(settings, 'smtp_password', "")
        service.smtp_use_tls = getattr(settings, 'smtp_use_tls', True)
        
        return service

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not getattr(settings, 'smtp_username', None) or not getattr(settings, 'smtp_password', None),
        reason="실제 SMTP 설정이 필요합니다 (SMTP_USERNAME, SMTP_PASSWORD 환경변수)"
    )
    async def test_send_real_email_notification(self, notification_service_with_real_config):
        """실제 이메일 전송 테스트 (실제 SMTP 서버 사용)"""
        # Given: 실제 SMTP 설정이 있는 알림 서비스
        service = notification_service_with_real_config
        
        # 테스트 이메일 주소 (자기 자신에게 전송)
        test_email = service.smtp_user
        
        # When: 실제 이메일 전송
        result = await service.send_email_notification(
            to_email=test_email,
            subject="[TEST] 지능형 알림 시스템 테스트",
            message="이것은 지능형 알림 시스템의 실제 이메일 전송 테스트입니다.",
            html_message="<h2>테스트 알림</h2><p>이것은 지능형 알림 시스템의 실제 이메일 전송 테스트입니다.</p>"
        )
        
        # Then: 전송 성공
        assert result is True

    @pytest.mark.asyncio
    async def test_smtp_connection_with_mock_server(self, notification_service_with_real_config):
        """Mock SMTP 서버를 사용한 연결 테스트"""
        # Given: Mock SMTP 서버
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            service = notification_service_with_real_config
            
            # When: 이메일 전송 시도
            result = await service.send_email_notification(
                to_email="test@example.com",
                subject="Mock SMTP 테스트",
                message="Mock SMTP 서버 연결 테스트"
            )
            
            # Then: SMTP 연결 및 전송 과정 확인
            assert result is True
            
            # SMTP 서버 연결 확인
            mock_smtp_class.assert_called_once_with(service.smtp_host, service.smtp_port)
            
            # TLS 시작 확인
            if service.smtp_use_tls:
                mock_smtp.starttls.assert_called_once()
            
            # 로그인 확인
            mock_smtp.login.assert_called_once_with(service.smtp_user, service.smtp_password)
            
            # 메시지 전송 확인
            mock_smtp.send_message.assert_called_once()
            
            # 연결 종료 확인
            mock_smtp.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_smtp_authentication_failure(self, notification_service_with_real_config):
        """SMTP 인증 실패 테스트"""
        # Given: 잘못된 인증 정보로 설정된 서비스
        service = notification_service_with_real_config
        original_password = service.smtp_password
        service.smtp_password = "wrong_password"
        
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            # SMTP 인증 오류 시뮬레이션
            mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
            
            # When: 잘못된 인증 정보로 이메일 전송 시도
            result = await service.send_email_notification(
                to_email="test@example.com",
                subject="인증 실패 테스트",
                message="이 메시지는 전송되지 않아야 합니다."
            )
            
            # Then: 전송 실패
            assert result is False
        
        # 원래 비밀번호 복원
        service.smtp_password = original_password

    @pytest.mark.asyncio
    async def test_smtp_connection_timeout(self, notification_service_with_real_config):
        """SMTP 연결 타임아웃 테스트"""
        # Given: 연결 타임아웃이 발생하는 Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = smtplib.SMTPConnectError(421, "Connection timeout")
            
            service = notification_service_with_real_config
            
            # When: 연결 타임아웃 상황에서 이메일 전송 시도
            result = await service.send_email_notification(
                to_email="test@example.com",
                subject="연결 타임아웃 테스트",
                message="이 메시지는 전송되지 않아야 합니다."
            )
            
            # Then: 전송 실패
            assert result is False

    @pytest.mark.asyncio
    async def test_email_content_encoding(self, notification_service_with_real_config):
        """이메일 콘텐츠 인코딩 테스트 (한글 포함)"""
        # Given: 한글이 포함된 이메일 내용
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            service = notification_service_with_real_config
            
            korean_subject = "🚨 [긴급] 시스템 알림 - CPU 사용률 초과"
            korean_message = """
안녕하세요,

시스템에서 다음과 같은 이상 상황이 감지되었습니다:

• 메트릭: CPU 사용률
• 현재 값: 85.5%
• 임계값: 80.0%
• 감지 시간: 2024-12-21 15:30:00

즉시 확인이 필요합니다.

감사합니다.
모니터링 시스템
"""
            
            korean_html = """
<html>
<body>
    <h2>🚨 시스템 알림</h2>
    <p>시스템에서 이상 상황이 감지되었습니다:</p>
    <ul>
        <li><strong>메트릭:</strong> CPU 사용률</li>
        <li><strong>현재 값:</strong> 85.5%</li>
        <li><strong>임계값:</strong> 80.0%</li>
    </ul>
    <p style="color: red;">즉시 확인이 필요합니다.</p>
</body>
</html>
"""
            
            # When: 한글 콘텐츠로 이메일 전송
            result = await service.send_email_notification(
                to_email="test@example.com",
                subject=korean_subject,
                message=korean_message,
                html_message=korean_html
            )
            
            # Then: 전송 성공
            assert result is True
            
            # 메시지 전송 호출 확인
            mock_smtp.send_message.assert_called_once()
            
            # 전송된 메시지 객체 확인
            sent_message_call = mock_smtp.send_message.call_args[0][0]
            assert isinstance(sent_message_call, MIMEMultipart)
            assert sent_message_call['Subject'] == korean_subject

    @pytest.mark.asyncio
    async def test_email_performance_large_content(self, notification_service_with_real_config):
        """대용량 이메일 콘텐츠 성능 테스트"""
        # Given: 대용량 콘텐츠
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            service = notification_service_with_real_config
            
            # 큰 메시지 생성 (10KB 정도)
            large_message = "알림 내용: " + "데이터 " * 1000
            large_html = "<html><body>" + "<p>데이터 항목</p>" * 500 + "</body></html>"
            
            # When: 대용량 콘텐츠로 이메일 전송
            import time
            start_time = time.time()
            
            result = await service.send_email_notification(
                to_email="test@example.com",
                subject="대용량 콘텐츠 테스트",
                message=large_message,
                html_message=large_html
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Then: 전송 성공 및 성능 확인
            assert result is True
            assert processing_time < 5.0  # 5초 이내 처리
            
            # 메시지 전송 확인
            mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_retry_mechanism(self, notification_service_with_real_config):
        """이메일 전송 재시도 메커니즘 테스트 (향후 구현용)"""
        # 현재는 재시도 로직이 없지만, 향후 추가할 수 있는 테스트
        # Given: 일시적 오류 후 성공하는 Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            # 첫 번째 호출에서는 일시적 오류, 두 번째에서는 성공
            mock_smtp.send_message.side_effect = [
                smtplib.SMTPRecipientsRefused({"test@example.com": (450, "Mailbox temporarily unavailable")}),
                None  # 성공
            ]
            
            service = notification_service_with_real_config
            
            # When: 일시적 오류 상황에서 이메일 전송
            result = await service.send_email_notification(
                to_email="test@example.com",
                subject="재시도 테스트",
                message="재시도 메커니즘 테스트"
            )
            
            # Then: 현재는 재시도 없이 실패 (향후 재시도 로직 추가 시 수정)
            assert result is False
            
            # 향후 재시도 로직 추가 시:
            # assert result is True
            # assert mock_smtp.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_email_sending(self, notification_service_with_real_config):
        """동시 이메일 전송 테스트"""
        # Given: 여러 이메일을 동시에 전송
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp
            
            service = notification_service_with_real_config
            
            # When: 여러 이메일을 병렬로 전송
            tasks = []
            for i in range(5):
                task = service.send_email_notification(
                    to_email=f"test{i}@example.com",
                    subject=f"동시 전송 테스트 {i}",
                    message=f"이것은 {i}번째 테스트 메시지입니다."
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Then: 모든 이메일 전송 성공
            assert all(results)
            assert len(results) == 5
            
            # 각 이메일마다 SMTP 연결이 생성되었는지 확인
            assert mock_smtp_class.call_count == 5


class TestEmailNotificationConfiguration:
    """이메일 알림 설정 테스트"""

    @pytest.mark.asyncio
    async def test_missing_smtp_configuration(self):
        """SMTP 설정 누락 테스트"""
        # Given: SMTP 설정이 없는 서비스
        service = NotificationService()
        service.smtp_host = None
        service.smtp_user = None
        service.smtp_password = None
        
        # When: SMTP 설정 없이 이메일 전송 시도
        result = await service.send_email_notification(
            to_email="test@example.com",
            subject="설정 누락 테스트",
            message="이 메시지는 전송되지 않아야 합니다."
        )
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.asyncio
    async def test_partial_smtp_configuration(self):
        """부분적 SMTP 설정 테스트"""
        # Given: 불완전한 SMTP 설정
        service = NotificationService()
        service.smtp_host = "smtp.gmail.com"
        service.smtp_user = "user@example.com"
        service.smtp_password = None  # 비밀번호 누락
        
        # When: 불완전한 설정으로 이메일 전송 시도
        result = await service.send_email_notification(
            to_email="test@example.com",
            subject="불완전한 설정 테스트",
            message="이 메시지는 전송되지 않아야 합니다."
        )
        
        # Then: 전송 실패
        assert result is False

    def test_smtp_configuration_from_settings(self):
        """설정에서 SMTP 구성 확인 테스트"""
        # Given: 설정에서 SMTP 정보를 읽는 서비스
        service = NotificationService()
        
        # Then: 설정 값이 올바르게 로드되었는지 확인
        assert hasattr(service, 'smtp_host')
        assert hasattr(service, 'smtp_port')
        assert hasattr(service, 'smtp_user')
        assert hasattr(service, 'smtp_password')
        assert hasattr(service, 'smtp_use_tls')
        
        # 기본값 확인
        assert service.smtp_port == getattr(settings, 'smtp_port', 587)
        assert service.smtp_use_tls == getattr(settings, 'smtp_use_tls', True)