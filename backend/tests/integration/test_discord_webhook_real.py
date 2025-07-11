"""
실제 디스코드 웹훅 연동 테스트

실제 디스코드 웹훅 URL에 연결하여 알림을 전송하는 테스트
"""
import pytest
import asyncio
import aiohttp
from unittest.mock import patch, AsyncMock
import json
from datetime import datetime

from nadle_backend.services.notification_service import NotificationService
from nadle_backend.config import settings


class TestDiscordWebhookReal:
    """실제 디스코드 웹훅 연동 테스트"""

    @pytest.fixture
    def notification_service_with_webhook(self):
        """실제 웹훅 설정을 가진 알림 서비스"""
        service = NotificationService()
        
        # 실제 디스코드 웹훅 URL 사용 (환경변수에서)
        service.discord_webhook_url = getattr(settings, 'discord_webhook_url', None)
        
        return service

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not getattr(settings, 'discord_webhook_url', None),
        reason="실제 Discord 웹훅 URL이 필요합니다 (DISCORD_WEBHOOK_URL 환경변수)"
    )
    async def test_send_real_discord_notification(self, notification_service_with_webhook):
        """실제 디스코드 웹훅 전송 테스트"""
        # Given: 실제 웹훅 URL이 설정된 알림 서비스
        service = notification_service_with_webhook
        
        # When: 실제 디스코드 알림 전송
        result = await service.send_discord_notification(
            message="🚨 **[TEST]** 지능형 알림 시스템 실제 테스트",
            title="시스템 테스트 알림",
            color=0xFF9900,  # 주황색
            username="Alert Test Bot"
        )
        
        # Then: 전송 성공
        assert result is True

    @pytest.mark.asyncio
    async def test_discord_webhook_with_mock_http(self, notification_service_with_webhook):
        """Mock HTTP 클라이언트를 사용한 디스코드 웹훅 테스트"""
        # Given: Mock HTTP 응답
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204  # Discord 웹훅 성공 응답
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            # When: 디스코드 알림 전송
            result = await service.send_discord_notification(
                message="Mock HTTP 테스트 메시지",
                title="테스트 알림",
                color=0x00FF00,
                username="Test Bot"
            )
            
            # Then: 전송 성공 및 HTTP 호출 확인
            assert result is True
            
            # HTTP POST 호출 확인
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # URL 확인
            assert call_args[0][0] == service.discord_webhook_url
            
            # 요청 데이터 확인
            request_data = call_args[1]["json"]
            assert request_data["username"] == "Test Bot"
            assert "embeds" in request_data
            assert request_data["embeds"][0]["title"] == "테스트 알림"
            assert request_data["embeds"][0]["description"] == "Mock HTTP 테스트 메시지"
            assert request_data["embeds"][0]["color"] == 0x00FF00
            assert "timestamp" in request_data["embeds"][0]

    @pytest.mark.asyncio
    async def test_discord_simple_message(self, notification_service_with_webhook):
        """디스코드 단순 메시지 전송 테스트"""
        # Given: Mock HTTP 응답
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            # When: 제목과 색상 없이 단순 메시지 전송
            result = await service.send_discord_notification(
                message="단순한 텍스트 메시지입니다."
            )
            
            # Then: 전송 성공 및 콘텐츠 확인
            assert result is True
            
            # 요청 데이터 확인
            request_data = mock_post.call_args[1]["json"]
            assert request_data["content"] == "단순한 텍스트 메시지입니다."
            assert "embeds" not in request_data

    @pytest.mark.asyncio
    async def test_discord_webhook_error_responses(self, notification_service_with_webhook):
        """디스코드 웹훅 오류 응답 테스트"""
        error_scenarios = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (404, "Webhook not found"),
            (429, "Rate limit exceeded"),
            (500, "Internal Server Error")
        ]
        
        service = notification_service_with_webhook
        service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
        
        for status_code, description in error_scenarios:
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status = status_code
                mock_post.return_value.__aenter__.return_value = mock_response
                
                # When: 오류 상황에서 디스코드 알림 전송
                result = await service.send_discord_notification(
                    message=f"오류 테스트: {description}"
                )
                
                # Then: 전송 실패
                assert result is False

    @pytest.mark.asyncio
    async def test_discord_webhook_network_errors(self, notification_service_with_webhook):
        """디스코드 웹훅 네트워크 오류 테스트"""
        network_errors = [
            aiohttp.ClientTimeout(),
            aiohttp.ClientConnectorError(connection_key=None, os_error=None),
            aiohttp.ClientError("Network error"),
            asyncio.TimeoutError()
        ]
        
        service = notification_service_with_webhook
        service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
        
        for error in network_errors:
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_post.side_effect = error
                
                # When: 네트워크 오류 상황에서 디스코드 알림 전송
                result = await service.send_discord_notification(
                    message=f"네트워크 오류 테스트: {type(error).__name__}"
                )
                
                # Then: 전송 실패
                assert result is False

    @pytest.mark.asyncio
    async def test_discord_embed_formatting(self, notification_service_with_webhook):
        """디스코드 임베드 포맷팅 테스트"""
        # Given: Mock HTTP 응답
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            test_message = """
🚨 **긴급 알림**

시스템에서 이상 상황이 감지되었습니다:

• **메트릭:** CPU 사용률
• **현재 값:** 85.5%
• **임계값:** 80.0%
• **서버:** web-server-01

즉시 확인이 필요합니다!
"""
            
            # When: 복잡한 메시지 포맷으로 디스코드 알림 전송
            result = await service.send_discord_notification(
                message=test_message,
                title="🔥 시스템 경고",
                color=0xFF0000,  # 빨간색
                username="Monitoring Bot"
            )
            
            # Then: 전송 성공 및 포맷팅 확인
            assert result is True
            
            request_data = mock_post.call_args[1]["json"]
            embed = request_data["embeds"][0]
            
            assert embed["title"] == "🔥 시스템 경고"
            assert embed["description"] == test_message
            assert embed["color"] == 0xFF0000
            assert request_data["username"] == "Monitoring Bot"

    @pytest.mark.asyncio
    async def test_discord_webhook_rate_limiting(self, notification_service_with_webhook):
        """디스코드 웹훅 요청 제한 테스트"""
        # Given: 요청 제한 응답을 반환하는 Mock
        with patch('aiohttp.ClientSession.post') as mock_post:
            # 첫 번째 요청은 요청 제한, 두 번째는 성공
            responses = [
                AsyncMock(status=429),  # Rate limited
                AsyncMock(status=204)   # Success
            ]
            mock_post.return_value.__aenter__.side_effect = responses
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            # When: 첫 번째 요청 (요청 제한)
            result1 = await service.send_discord_notification(
                message="첫 번째 메시지 (요청 제한)"
            )
            
            # When: 두 번째 요청 (성공)
            result2 = await service.send_discord_notification(
                message="두 번째 메시지 (성공)"
            )
            
            # Then: 첫 번째는 실패, 두 번째는 성공
            assert result1 is False  # 요청 제한으로 실패
            assert result2 is True   # 성공
            
            # 두 번의 호출이 있었는지 확인
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_discord_webhook_large_message(self, notification_service_with_webhook):
        """디스코드 웹훅 대용량 메시지 테스트"""
        # Given: Mock HTTP 응답
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            # 디스코드 메시지 길이 제한에 가까운 메시지 생성 (2000자 제한)
            large_message = "알림 내용: " + "데이터 항목 " * 180  # 약 1800자
            
            # When: 대용량 메시지로 디스코드 알림 전송
            result = await service.send_discord_notification(
                message=large_message,
                title="대용량 메시지 테스트",
                color=0x0099FF
            )
            
            # Then: 전송 성공
            assert result is True
            
            # 메시지 길이 확인
            request_data = mock_post.call_args[1]["json"]
            embed = request_data["embeds"][0]
            assert len(embed["description"]) < 2000  # 디스코드 제한 확인

    @pytest.mark.asyncio
    async def test_concurrent_discord_notifications(self, notification_service_with_webhook):
        """동시 디스코드 알림 전송 테스트"""
        # Given: Mock HTTP 응답
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            # When: 여러 알림을 동시에 전송
            tasks = []
            for i in range(5):
                task = service.send_discord_notification(
                    message=f"동시 전송 테스트 메시지 #{i}",
                    title=f"테스트 #{i}",
                    color=0x00FF00 + (i * 0x100000)  # 색상 변화
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Then: 모든 알림 전송 성공
            assert all(results)
            assert len(results) == 5
            
            # 각 알림마다 HTTP 요청이 생성되었는지 확인
            assert mock_post.call_count == 5

    @pytest.mark.asyncio
    async def test_discord_webhook_json_serialization(self, notification_service_with_webhook):
        """디스코드 웹훅 JSON 직렬화 테스트"""
        # Given: JSON 직렬화가 가능한 데이터
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 204
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = notification_service_with_webhook
            service.discord_webhook_url = "https://discord.com/api/webhooks/test/webhook"
            
            # 특수 문자와 이모지가 포함된 메시지
            special_message = """
🚨 긴급 상황 발생! 🚨

서버 상태:
• CPU: 85% ⬆️
• 메모리: 92% 🔴
• 디스크: 78% 🟡

경고: "위험" 수준에 도달했습니다!
문의: admin@example.com
"""
            
            # When: 특수 문자가 포함된 메시지로 디스코드 알림 전송
            result = await service.send_discord_notification(
                message=special_message,
                title="🔥 긴급 시스템 알림 🔥",
                color=0xFF0000,
                username="시스템 모니터링 봇"
            )
            
            # Then: 전송 성공 및 JSON 직렬화 확인
            assert result is True
            
            # JSON 데이터가 올바르게 직렬화되었는지 확인
            request_data = mock_post.call_args[1]["json"]
            
            # JSON 직렬화 테스트
            json_str = json.dumps(request_data, ensure_ascii=False)
            assert isinstance(json_str, str)
            
            # 특수 문자 유지 확인
            assert "🚨" in json_str
            assert "시스템 모니터링 봇" in json_str


class TestDiscordWebhookConfiguration:
    """디스코드 웹훅 설정 테스트"""

    @pytest.mark.asyncio
    async def test_missing_webhook_url(self):
        """웹훅 URL 누락 테스트"""
        # Given: 웹훅 URL이 없는 서비스
        service = NotificationService()
        service.discord_webhook_url = None
        
        # When: 웹훅 URL 없이 디스코드 알림 전송 시도
        result = await service.send_discord_notification(
            message="이 메시지는 전송되지 않아야 합니다."
        )
        
        # Then: 전송 실패
        assert result is False

    @pytest.mark.asyncio
    async def test_invalid_webhook_url(self):
        """잘못된 웹훅 URL 테스트"""
        # Given: 잘못된 형식의 웹훅 URL
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientConnectorError(connection_key=None, os_error=None)
            
            service = NotificationService()
            service.discord_webhook_url = "https://invalid-discord-webhook-url.com/webhook"
            
            # When: 잘못된 URL로 디스코드 알림 전송 시도
            result = await service.send_discord_notification(
                message="잘못된 URL 테스트"
            )
            
            # Then: 전송 실패
            assert result is False

    def test_discord_webhook_configuration_from_settings(self):
        """설정에서 디스코드 웹훅 구성 확인 테스트"""
        # Given: 설정에서 웹훅 정보를 읽는 서비스
        service = NotificationService()
        
        # Then: 웹훅 URL 설정이 올바르게 로드되었는지 확인
        assert hasattr(service, 'discord_webhook_url')
        
        # 환경변수에서 로드된 값 확인
        expected_webhook_url = getattr(settings, 'discord_webhook_url', None)
        assert service.discord_webhook_url == expected_webhook_url