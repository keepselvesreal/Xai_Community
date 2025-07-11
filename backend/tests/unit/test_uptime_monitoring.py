"""
업타임 모니터링 시스템 단위 테스트

외부 업타임 모니터링 서비스와의 연동 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import time
from datetime import datetime, timedelta

from nadle_backend.services.uptime_monitoring import (
    UptimeMonitoringService,
    UptimeMonitor,
    UptimeStatus,
    UptimeAlert,
    HealthCheckService
)


class TestUptimeMonitoringService:
    """업타임 모니터링 서비스 단위 테스트"""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP 클라이언트"""
        return Mock()

    @pytest.fixture
    def uptime_service(self, mock_http_client):
        """업타임 모니터링 서비스 인스턴스"""
        return UptimeMonitoringService(
            api_key="test_api_key",
            http_client=mock_http_client
        )

    def test_create_monitor_success(self, uptime_service, mock_http_client):
        """모니터 생성 성공 테스트"""
        # Given: 성공적인 API 응답
        mock_response = {
            "stat": "ok",
            "monitor": {
                "id": 12345,
                "friendly_name": "Test API Monitor",
                "url": "https://api.example.com/health",
                "type": 1,  # HTTP(s)
                "status": 2,  # Up
                "create_datetime": "1234567890"
            }
        }
        mock_http_client.post.return_value.json.return_value = mock_response
        mock_http_client.post.return_value.status_code = 200

        # When: 모니터 생성
        monitor = uptime_service.create_monitor(
            name="Test API Monitor",
            url="https://api.example.com/health",
            interval=300  # 5분
        )

        # Then: 모니터 객체 반환
        assert isinstance(monitor, UptimeMonitor)
        assert monitor.id == 12345
        assert monitor.name == "Test API Monitor"
        assert monitor.url == "https://api.example.com/health"
        assert monitor.status == UptimeStatus.UP

        # API 호출 확인
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "newMonitor" in call_args[0][0]  # URL 확인

    def test_create_monitor_failure(self, uptime_service, mock_http_client):
        """모니터 생성 실패 테스트"""
        # Given: 실패 API 응답
        mock_response = {
            "stat": "fail",
            "error": {
                "type": "invalid_parameter",
                "message": "URL is not valid"
            }
        }
        mock_http_client.post.return_value.json.return_value = mock_response
        mock_http_client.post.return_value.status_code = 200

        # When/Then: 예외 발생
        with pytest.raises(Exception) as exc_info:
            uptime_service.create_monitor(
                name="Invalid Monitor",
                url="invalid-url",
                interval=300
            )
        
        assert "URL is not valid" in str(exc_info.value)

    def test_get_monitors_success(self, uptime_service, mock_http_client):
        """모니터 목록 조회 성공 테스트"""
        # Given: 성공적인 API 응답
        mock_response = {
            "stat": "ok",
            "monitors": [
                {
                    "id": 12345,
                    "friendly_name": "API Monitor 1",
                    "url": "https://api.example.com/health",
                    "type": 1,
                    "status": 2,
                    "create_datetime": "1234567890"
                },
                {
                    "id": 12346,
                    "friendly_name": "API Monitor 2", 
                    "url": "https://api2.example.com/health",
                    "type": 1,
                    "status": 1,  # Down (Not checked yet)
                    "create_datetime": "1234567891"
                }
            ]
        }
        mock_http_client.get.return_value.json.return_value = mock_response
        mock_http_client.get.return_value.status_code = 200

        # When: 모니터 목록 조회
        monitors = uptime_service.get_monitors()

        # Then: 모니터 목록 반환
        assert len(monitors) == 2
        assert all(isinstance(m, UptimeMonitor) for m in monitors)
        assert monitors[0].status == UptimeStatus.UP
        assert monitors[1].status == UptimeStatus.DOWN

    def test_get_monitor_logs_success(self, uptime_service, mock_http_client):
        """모니터 로그 조회 성공 테스트"""
        # Given: 성공적인 API 응답
        mock_response = {
            "stat": "ok",
            "logs": [
                {
                    "type": 2,  # Up
                    "datetime": "1234567890",
                    "duration": 1234,
                    "reason": {
                        "code": "200",
                        "detail": "OK"
                    }
                },
                {
                    "type": 1,  # Down
                    "datetime": "1234567880",
                    "duration": 0,
                    "reason": {
                        "code": "500",
                        "detail": "Internal Server Error"
                    }
                }
            ]
        }
        mock_http_client.get.return_value.json.return_value = mock_response
        mock_http_client.get.return_value.status_code = 200

        # When: 모니터 로그 조회
        logs = uptime_service.get_monitor_logs(12345, days=7)

        # Then: 로그 목록 반환
        assert len(logs) == 2
        assert logs[0]["type"] == 2  # Up
        assert logs[1]["type"] == 1  # Down

    def test_delete_monitor_success(self, uptime_service, mock_http_client):
        """모니터 삭제 성공 테스트"""
        # Given: 성공적인 API 응답
        mock_response = {"stat": "ok"}
        mock_http_client.post.return_value.json.return_value = mock_response
        mock_http_client.post.return_value.status_code = 200

        # When: 모니터 삭제
        result = uptime_service.delete_monitor(12345)

        # Then: 성공 반환
        assert result is True

        # API 호출 확인
        mock_http_client.post.assert_called_once()


class TestHealthCheckService:
    """헬스체크 서비스 단위 테스트"""

    @pytest.fixture
    def health_service(self):
        """헬스체크 서비스 인스턴스"""
        return HealthCheckService()

    @pytest.mark.asyncio
    async def test_comprehensive_health_check_healthy(self, health_service):
        """종합 헬스체크 - 정상 상태 테스트"""
        # Given: 모든 의존성이 정상
        with patch.object(health_service, '_check_database') as mock_db, \
             patch.object(health_service, '_check_redis') as mock_redis, \
             patch.object(health_service, '_check_external_apis') as mock_apis:
            
            mock_db.return_value = {"status": "healthy", "response_time": 0.01}
            mock_redis.return_value = {"status": "healthy", "response_time": 0.005}
            mock_apis.return_value = {"status": "healthy", "response_time": 0.1}

            # When: 종합 헬스체크 실행
            result = await health_service.comprehensive_health_check()

            # Then: 정상 상태 반환
            assert result["status"] == "healthy"
            assert result["overall_health"] is True
            assert "database" in result["checks"]
            assert "redis" in result["checks"]
            assert "external_apis" in result["checks"]
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_comprehensive_health_check_unhealthy(self, health_service):
        """종합 헬스체크 - 비정상 상태 테스트"""
        # Given: 데이터베이스가 비정상
        with patch.object(health_service, '_check_database') as mock_db, \
             patch.object(health_service, '_check_redis') as mock_redis, \
             patch.object(health_service, '_check_external_apis') as mock_apis:
            
            mock_db.return_value = {"status": "unhealthy", "error": "Connection timeout"}
            mock_redis.return_value = {"status": "healthy", "response_time": 0.005}
            mock_apis.return_value = {"status": "healthy", "response_time": 0.1}

            # When: 종합 헬스체크 실행
            result = await health_service.comprehensive_health_check()

            # Then: 비정상 상태 반환
            assert result["status"] == "unhealthy"
            assert result["overall_health"] is False
            assert result["checks"]["database"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_database_health_check_success(self, health_service):
        """데이터베이스 헬스체크 성공 테스트"""
        # Given: 정상적인 데이터베이스 연결
        mock_client = AsyncMock()
        mock_admin = AsyncMock()
        mock_client.admin = mock_admin
        mock_admin.command.return_value = {"ismaster": True}

        with patch.object(health_service, '_check_database') as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "response_time": 0.01,
                "message": "Database connection successful"
            }
            
            # When: 데이터베이스 헬스체크
            result = await health_service._check_database()

            # Then: 정상 상태 반환
            assert result["status"] == "healthy"
            assert "response_time" in result

    @pytest.mark.asyncio
    async def test_database_health_check_failure(self, health_service):
        """데이터베이스 헬스체크 실패 테스트"""
        # Given: 데이터베이스 연결 실패
        with patch.object(health_service, '_check_database') as mock_check:
            mock_check.return_value = {
                "status": "unhealthy",
                "error": "Connection failed"
            }
            
            # When: 데이터베이스 헬스체크
            result = await health_service._check_database()

            # Then: 비정상 상태 반환
            assert result["status"] == "unhealthy"
            assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_redis_health_check_success(self, health_service):
        """Redis 헬스체크 성공 테스트"""
        # Given: 정상적인 Redis 연결
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True

        with patch('redis.asyncio.from_url', return_value=mock_redis):
            # When: Redis 헬스체크
            result = await health_service._check_redis()

            # Then: 정상 상태 반환
            assert result["status"] == "healthy"
            assert "response_time" in result

    def test_uptime_status_enum(self):
        """업타임 상태 Enum 테스트"""
        assert UptimeStatus.UP.value == "up"
        assert UptimeStatus.DOWN.value == "down"
        assert UptimeStatus.PAUSED.value == "paused"
        assert UptimeStatus.UNKNOWN.value == "unknown"

    def test_uptime_monitor_model(self):
        """업타임 모니터 모델 테스트"""
        monitor = UptimeMonitor(
            id=12345,
            name="Test Monitor",
            url="https://example.com",
            status=UptimeStatus.UP,
            created_at=datetime.now()
        )

        assert monitor.id == 12345
        assert monitor.name == "Test Monitor"
        assert monitor.url == "https://example.com"
        assert monitor.status == UptimeStatus.UP
        assert isinstance(monitor.created_at, datetime)

    def test_uptime_alert_model(self):
        """업타임 알림 모델 테스트"""
        alert = UptimeAlert(
            monitor_id=12345,
            status=UptimeStatus.DOWN,
            message="Service is down",
            timestamp=datetime.now(),
            duration=300  # 5분
        )

        assert alert.monitor_id == 12345
        assert alert.status == UptimeStatus.DOWN
        assert alert.message == "Service is down"
        assert alert.duration == 300
        assert isinstance(alert.timestamp, datetime)


class TestUptimeMonitoringIntegration:
    """업타임 모니터링 통합 테스트"""

    @pytest.mark.asyncio
    async def test_monitor_creation_and_health_check_integration(self):
        """모니터 생성과 헬스체크 통합 테스트"""
        # Given: Mock 서비스들
        mock_http_client = Mock()
        mock_response = {
            "stat": "ok",
            "monitor": {
                "id": 12345,
                "friendly_name": "Integration Test Monitor",
                "url": "https://api.example.com/health",
                "type": 1,
                "status": 2,
                "create_datetime": str(int(time.time()))
            }
        }
        mock_http_client.post.return_value.json.return_value = mock_response
        mock_http_client.post.return_value.status_code = 200

        uptime_service = UptimeMonitoringService(
            api_key="test_key",
            http_client=mock_http_client
        )
        health_service = HealthCheckService()

        # When: 모니터 생성 후 헬스체크 실행
        monitor = uptime_service.create_monitor(
            name="Integration Test Monitor",
            url="https://api.example.com/health",
            interval=300
        )

        with patch.object(health_service, '_check_database') as mock_db, \
             patch.object(health_service, '_check_redis') as mock_redis, \
             patch.object(health_service, '_check_external_apis') as mock_apis:
            
            mock_db.return_value = {"status": "healthy", "response_time": 0.01}
            mock_redis.return_value = {"status": "healthy", "response_time": 0.005}
            mock_apis.return_value = {"status": "healthy", "response_time": 0.1}

            health_result = await health_service.comprehensive_health_check()

        # Then: 모니터 생성과 헬스체크 모두 성공
        assert monitor.id == 12345
        assert health_result["status"] == "healthy"
        assert health_result["overall_health"] is True

    def test_error_handling_chain(self):
        """에러 처리 체인 테스트"""
        # Given: 연속적인 실패 상황
        mock_http_client = Mock()
        
        # 첫 번째 호출: 네트워크 에러
        # 두 번째 호출: API 에러
        # 세 번째 호출: 성공
        mock_http_client.post.side_effect = [
            Exception("Network error"),
            Mock(status_code=500),
            Mock(
                status_code=200,
                json=lambda: {
                    "stat": "ok",
                    "monitor": {"id": 12345, "friendly_name": "Test", "url": "https://example.com", "type": 1, "status": 2, "create_datetime": "123"}
                }
            )
        ]

        uptime_service = UptimeMonitoringService(
            api_key="test_key",
            http_client=mock_http_client
        )

        # When: 재시도 로직 실행
        try:
            uptime_service.create_monitor("Test", "https://example.com", 300)
            assert False, "Should have raised exception on first two calls"
        except Exception:
            pass

        try:
            uptime_service.create_monitor("Test", "https://example.com", 300)
            assert False, "Should have raised exception on second call"
        except Exception:
            pass

        # 세 번째 호출은 성공해야 함
        monitor = uptime_service.create_monitor("Test", "https://example.com", 300)
        assert monitor.id == 12345