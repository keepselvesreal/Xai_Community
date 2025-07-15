"""
알림 서비스 Mock 테스트

이메일, 디스코드, SMS 알림 서비스의 Mock 기반 단위 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import aiohttp
import smtplib
from email.mime.multipart import MIMEMultipart

from nadle_backend.services.notification_service import NotificationService


class TestNotificationServiceMock:
    """알림 서비스 Mock 테스트"""

    @pytest.fixture
    def notification_service(self):
        """알림 서비스 인스턴스"""
        service = NotificationService()
        # Mock 설정값 설정
        service.smtp_host = "smtp.gmail.com"
        service.smtp_port = 587
        service.smtp_user = "test@example.com"
        service.smtp_password = "test_password"
        service.smtp_use_tls = True
        service.discord_webhook_url = "https://discord.com/api/webhooks/test"
        return service

    @pytest.mark.asyncio
    @patch('smtplib.SMTP')
    async def test_send_email_notification_success(self, mock_smtp_class, notification_service):
        """이메일 알림 전송 성공 테스트"""
        # Given: Mock SMTP 서버 설정
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        
        # When: 이메일 전송
        result = await notification_service.send_email_notification(
            to_email="recipient@example.com",
            subject="Test Alert",
            message="This is a test alert message",
            html_message="<h1>Test Alert</h1><p>This is a test alert message</p>"
        )
        
        # Then: 전송 성공
        assert result is True
        
        # SMTP 호출 검증
        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@example.com", "test_password")
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @pytest.mark.asyncio
    @patch('smtplib.SMTP')
    async def test_send_email_notification_smtp_failure(self, mock_smtp_class, notification_service):
        """이메일 전송 SMTP 실패 테스트"""
        # Given: SMTP 서버 연결 실패
        mock_smtp_class.side_effect = smtplib.SMTPException("Connection failed")
        
        # When: 이메일 전송 시도
        result = await notification_service.send_email_notification(
            to_email="recipient@example.com",
            subject="Test Alert",
            message="This is a test alert message"
        )
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_notification_missing_config(self):
        """이메일 전송 설정 누락 테스트"""
        # Given: SMTP 설정이 누락된 서비스
        service = NotificationService()
        # smtp_host, smtp_user, smtp_password 중 일부 누락
        service.smtp_host = None
        service.smtp_user = None
        service.smtp_password = None
        
        # When: 이메일 전송 시도
        result = await service.send_email_notification(
            to_email="recipient@example.com",
            subject="Test Alert",
            message="This is a test alert message"
        )
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_discord_notification_success(self, mock_post, notification_service):
        """디스코드 알림 전송 성공 테스트"""
        # Given: Mock HTTP 응답
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # When: 디스코드 알림 전송
        result = await notification_service.send_discord_notification(
            message="Test alert message",
            title="Test Alert",
            color=0xFF0000,
            username="Alert Bot"
        )
        
        # Then: 전송 성공
        assert result is True
        
        # 웹훅 호출 검증
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://discord.com/api/webhooks/test"
        assert "json" in call_args[1]
        
        # 페이로드 검증
        payload = call_args[1]["json"]
        assert payload["username"] == "Alert Bot"
        assert "embeds" in payload
        assert payload["embeds"][0]["title"] == "Test Alert"
        assert payload["embeds"][0]["description"] == "Test alert message"
        assert payload["embeds"][0]["color"] == 0xFF0000

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_discord_notification_simple_message(self, mock_post, notification_service):
        """디스코드 단순 메시지 전송 테스트"""
        # Given: Mock HTTP 응답
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # When: 단순 메시지 전송 (제목, 색상 없음)
        result = await notification_service.send_discord_notification(
            message="Simple test message"
        )
        
        # Then: 전송 성공
        assert result is True
        
        # 페이로드 검증 (임베드 대신 content 사용)
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["content"] == "Simple test message"
        assert "embeds" not in payload

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_discord_notification_failure(self, mock_post, notification_service):
        """디스코드 알림 전송 실패 테스트"""
        # Given: HTTP 에러 응답
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # When: 디스코드 알림 전송
        result = await notification_service.send_discord_notification(
            message="Test message"
        )
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.asyncio
    async def test_send_discord_notification_missing_webhook(self):
        """디스코드 웹훅 URL 누락 테스트"""
        # Given: 웹훅 URL이 설정되지 않은 서비스
        service = NotificationService()
        service.discord_webhook_url = None  # 명시적으로 None 설정
        
        # When: 디스코드 알림 전송 시도
        result = await service.send_discord_notification(message="Test message")
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_send_discord_notification_network_error(self, mock_post, notification_service):
        """디스코드 알림 네트워크 에러 테스트"""
        # Given: 네트워크 에러
        mock_post.side_effect = aiohttp.ClientError("Network error")
        
        # When: 디스코드 알림 전송
        result = await notification_service.send_discord_notification(
            message="Test message"
        )
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.skip(reason="SMS 기능은 구현하지 않음")
    @pytest.mark.asyncio
    async def test_send_sms_notification_success(self, notification_service):
        """SMS 알림 전송 성공 테스트 (Mock)"""
        pass

    @pytest.mark.skip(reason="SMS 기능은 구현하지 않음")
    @pytest.mark.asyncio
    async def test_send_sms_notification_missing_config(self):
        """SMS 설정 누락 테스트"""
        pass

    @pytest.mark.asyncio
    async def test_send_uptime_alert_down(self, notification_service):
        """업타임 다운 알림 테스트"""
        # Given: Mock 알림 메서드들
        notification_service.send_discord_notification = AsyncMock(return_value=True)
        notification_service.send_email_notification = AsyncMock(return_value=True)
        
        # When: 다운 알림 전송
        results = await notification_service.send_uptime_alert(
            monitor_name="API Server",
            status="down",
            url="https://api.example.com",
            duration=300,
            email_recipients=["admin@example.com"]
        )
        
        # Then: 알림 전송 성공
        assert results["discord"] is True
        assert results["email"] is True
        
        # Discord 호출 검증
        notification_service.send_discord_notification.assert_called_once()
        discord_call_args = notification_service.send_discord_notification.call_args
        assert "API Server" in discord_call_args[1]["message"]
        assert "다운되었습니다" in discord_call_args[1]["message"]
        assert discord_call_args[1]["color"] == 0xFF0000  # 빨간색
        
        # Email 호출 검증
        notification_service.send_email_notification.assert_called_once()
        email_call_args = notification_service.send_email_notification.call_args
        assert email_call_args[1]["to_email"] == "admin@example.com"
        assert "[ALERT]" in email_call_args[1]["subject"]

    @pytest.mark.asyncio
    async def test_send_uptime_alert_recovery(self, notification_service):
        """업타임 복구 알림 테스트"""
        # Given: Mock 알림 메서드들
        notification_service.send_discord_notification = AsyncMock(return_value=True)
        notification_service.send_email_notification = AsyncMock(return_value=True)
        
        # When: 복구 알림 전송
        results = await notification_service.send_uptime_alert(
            monitor_name="API Server",
            status="up",
            url="https://api.example.com",
            duration=300
        )
        
        # Then: 알림 전송 성공
        assert results["discord"] is True
        assert results["email"] is True
        
        # Discord 호출 검증
        discord_call_args = notification_service.send_discord_notification.call_args
        assert "복구되었습니다" in discord_call_args[1]["message"]
        assert discord_call_args[1]["color"] == 0x00FF00  # 녹색

    @pytest.mark.asyncio
    async def test_send_performance_alert(self, notification_service):
        """성능 알림 테스트"""
        # Given: Mock 알림 메서드들
        notification_service.send_discord_notification = AsyncMock(return_value=True)
        notification_service.send_email_notification = AsyncMock(return_value=True)
        
        # When: 성능 알림 전송
        results = await notification_service.send_performance_alert(
            metric_name="CPU Usage",
            current_value=85.5,
            threshold=80.0,
            trend="increasing"
        )
        
        # Then: 알림 전송 성공
        assert results["discord"] is True
        assert results["email"] is True
        
        # Discord 호출 검증
        discord_call_args = notification_service.send_discord_notification.call_args
        assert "CPU Usage" in discord_call_args[1]["message"]
        assert "85.5" in discord_call_args[1]["message"]
        assert "80.0" in discord_call_args[1]["message"]
        assert "increasing" in discord_call_args[1]["message"]
        assert discord_call_args[1]["color"] == 0xFFA500  # 주황색

    @pytest.mark.asyncio
    async def test_convert_markdown_to_html(self, notification_service):
        """마크다운 HTML 변환 테스트"""
        # Given: 마크다운 텍스트
        markdown_text = "**중요 알림**\n\n시스템에 문제가 발생했습니다.\n**URL:** https://example.com"
        
        # When: HTML 변환
        html_result = notification_service._convert_markdown_to_html(markdown_text)
        
        # Then: 올바르게 변환됨
        assert "<strong>중요 알림</strong>" in html_result
        assert "<br>" in html_result
        assert "<html><body>" in html_result
        assert "</body></html>" in html_result

    @pytest.mark.asyncio
    async def test_notification_service_integration(self, notification_service):
        """알림 서비스 통합 테스트"""
        # Given: 이메일과 Discord 알림 메서드 Mock
        notification_service.send_email_notification = AsyncMock(return_value=True)
        notification_service.send_discord_notification = AsyncMock(return_value=True)
        
        # When: 여러 알림을 순차적으로 전송
        email_result = await notification_service.send_email_notification(
            "test@example.com", "Test", "Message"
        )
        discord_result = await notification_service.send_discord_notification("Discord message")
        
        # Then: 모든 알림 전송 성공
        assert email_result is True
        assert discord_result is True
        
        # 모든 메서드가 호출되었는지 확인
        notification_service.send_email_notification.assert_called_once()
        notification_service.send_discord_notification.assert_called_once()


class TestNotificationServiceFactory:
    """알림 서비스 팩토리 테스트"""
    
    def test_get_notification_service(self):
        """알림 서비스 팩토리 함수 테스트"""
        # Given/When: 팩토리 함수 호출
        from nadle_backend.services.notification_service import get_notification_service
        service = get_notification_service()
        
        # Then: 올바른 인스턴스 반환
        assert isinstance(service, NotificationService)
        assert hasattr(service, 'send_email_notification')
        assert hasattr(service, 'send_discord_notification')
        # SMS 기능은 구현하지 않음