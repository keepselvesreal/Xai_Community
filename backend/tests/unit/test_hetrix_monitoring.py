"""
HetrixTools 모니터링 시스템 단위 테스트

HetrixTools API v3를 사용한 업타임 모니터링 서비스 테스트
기존 UptimeRobot 테스트를 HetrixTools로 마이그레이션
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import time
from datetime import datetime, timedelta

from nadle_backend.services.hetrix_monitoring import (
    HetrixMonitoringService,
    HetrixToolsClient,
    Monitor,
    UptimeStatus,
    MonitorLog,
    HealthCheckService
)


class TestHetrixToolsClient:
    """HetrixTools API 클라이언트 단위 테스트"""


    @pytest.fixture
    def hetrix_client(self):
        """HetrixTools 클라이언트 인스턴스"""
        return HetrixToolsClient(api_token="test_api_token")

    @pytest.mark.asyncio
    async def test_get_monitors_success(self, hetrix_client):
        """모니터 목록 조회 성공 테스트"""
        # Given: 성공적인 API 응답
        mock_api_response = {
            "monitors": [
                {
                    "id": "e3519dd0083b3e49780501bccd599142",
                    "name": "staging-xai-community",
                    "type": "website",
                    "target": "https://api.staging.example.com/health",
                    "uptime_status": "up",
                    "uptime": "100.0000",
                    "created_at": 1752496648,
                    "last_check": 1752541294,
                    "last_status_change": 1752496723,
                    "locations": {
                        "tokyo": {"uptime_status": "up", "response_time": 132},
                        "singapore": {"uptime_status": "up", "response_time": 227}
                    }
                },
                {
                    "id": "c9029520a5481f55312020c1ecf0503b",
                    "name": "production-xai-community",
                    "type": "website",
                    "target": "https://api.example.com/health",
                    "uptime_status": "up",
                    "uptime": "99.9000",
                    "created_at": 1752496680,
                    "last_check": 1752541350,
                    "last_status_change": 1752496778,
                    "locations": {
                        "tokyo": {"uptime_status": "up", "response_time": 127},
                        "singapore": {"uptime_status": "up", "response_time": 197}
                    }
                }
            ],
            "meta": {
                "total": 2,
                "returned": 2
            }
        }
        
        with patch.object(hetrix_client, '_make_request', return_value=mock_api_response):
            # When: 모니터 목록 조회
            monitors = await hetrix_client.get_monitors()

            # Then: 모니터 목록 반환
            assert len(monitors) == 2
            assert all(isinstance(m, Monitor) for m in monitors)
            
            # 첫 번째 모니터 검증
            monitor1 = monitors[0]
            assert monitor1.id == "e3519dd0083b3e49780501bccd599142"
            assert monitor1.name == "staging-xai-community"
            assert monitor1.url == "https://api.staging.example.com/health"
            assert monitor1.status == UptimeStatus.UP
            assert monitor1.uptime == 100.0
            assert monitor1.response_time["tokyo"] == 132
            assert monitor1.response_time["singapore"] == 227
            
            # 두 번째 모니터 검증
            monitor2 = monitors[1]
            assert monitor2.id == "c9029520a5481f55312020c1ecf0503b"
            assert monitor2.name == "production-xai-community"
            assert monitor2.status == UptimeStatus.UP
            assert monitor2.uptime == 99.9

    @pytest.mark.asyncio
    async def test_get_monitors_api_error(self, hetrix_client):
        """모니터 목록 조회 API 오류 테스트"""
        # Given: API 오류 응답 - _make_request에서 ValueError 발생
        with patch.object(hetrix_client, '_make_request', side_effect=ValueError("API Error: Invalid API Token")):
            # When/Then: 예외 발생
            with pytest.raises(ValueError) as exc_info:
                await hetrix_client.get_monitors()
            
            assert "Invalid API Token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_monitor_by_name_success(self, hetrix_client):
        """이름으로 모니터 조회 성공 테스트"""
        # Given: get_monitors가 성공 응답을 반환하도록 Mock
        mock_monitors = [
            Monitor(
                id="test-id-1",
                name="staging-xai-community",
                url="https://staging.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            ),
            Monitor(
                id="test-id-2",
                name="production-xai-community",
                url="https://production.example.com",
                status=UptimeStatus.UP,
                uptime=99.9,
                created_at=1752496680,
                last_check=1752541350,
                last_status_change=1752496778
            )
        ]
        
        with patch.object(hetrix_client, 'get_monitors', return_value=mock_monitors):
            # When: 특정 이름으로 모니터 조회
            monitor = await hetrix_client.get_monitor_by_name("staging-xai-community")

            # Then: 해당 모니터 반환
            assert monitor is not None
            assert monitor.name == "staging-xai-community"
            assert monitor.id == "test-id-1"

    @pytest.mark.asyncio
    async def test_get_monitor_by_name_not_found(self, hetrix_client):
        """이름으로 모니터 조회 실패 테스트"""
        # Given: 빈 모니터 목록
        with patch.object(hetrix_client, 'get_monitors', return_value=[]):
            # When: 존재하지 않는 모니터 조회
            monitor = await hetrix_client.get_monitor_by_name("non-existent-monitor")

            # Then: None 반환
            assert monitor is None

    @pytest.mark.asyncio
    async def test_get_monitors_by_environment_production(self, hetrix_client):
        """환경별 모니터 조회 - 프로덕션 테스트"""
        # Given: 다양한 환경의 모니터들
        mock_monitors = [
            Monitor(
                id="staging-id",
                name="staging-xai-community",
                url="https://staging.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            ),
            Monitor(
                id="prod-id",
                name="production-xai-community",
                url="https://production.example.com",
                status=UptimeStatus.UP,
                uptime=99.9,
                created_at=1752496680,
                last_check=1752541350,
                last_status_change=1752496778
            )
        ]
        
        with patch.object(hetrix_client, 'get_monitors', return_value=mock_monitors):
            # When: 프로덕션 환경 모니터 조회
            prod_monitors = await hetrix_client.get_monitors_by_environment("production")

            # Then: 프로덕션 모니터만 반환
            assert len(prod_monitors) == 1
            assert prod_monitors[0].name == "production-xai-community"
            assert prod_monitors[0].id == "prod-id"

    @pytest.mark.asyncio
    async def test_get_monitors_by_environment_staging(self, hetrix_client):
        """환경별 모니터 조회 - 스테이징 테스트"""
        # Given: 다양한 환경의 모니터들
        mock_monitors = [
            Monitor(
                id="staging-id",
                name="staging-xai-community",
                url="https://staging.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            ),
            Monitor(
                id="prod-id",
                name="production-xai-community",
                url="https://production.example.com",
                status=UptimeStatus.UP,
                uptime=99.9,
                created_at=1752496680,
                last_check=1752541350,
                last_status_change=1752496778
            )
        ]
        
        with patch.object(hetrix_client, 'get_monitors', return_value=mock_monitors):
            # When: 스테이징 환경 모니터 조회
            staging_monitors = await hetrix_client.get_monitors_by_environment("staging")

            # Then: 스테이징 모니터만 반환
            assert len(staging_monitors) == 1
            assert staging_monitors[0].name == "staging-xai-community"
            assert staging_monitors[0].id == "staging-id"

    @pytest.mark.asyncio
    async def test_get_monitor_logs_not_implemented(self, hetrix_client):
        """모니터 로그 조회 미구현 테스트"""
        # When: 로그 조회 시도
        logs = await hetrix_client.get_monitor_logs("test-id", days=1)

        # Then: 빈 로그 목록 반환
        assert logs == []

    @pytest.mark.asyncio
    async def test_create_monitor_test_mode(self, hetrix_client):
        """모니터 생성 테스트 모드"""
        # When: 모니터 생성 (테스트 모드)
        monitor = await hetrix_client.create_monitor(
            name="Test Monitor",
            url="https://test.example.com",
            monitor_type="website",
            interval=1
        )

        # Then: 더미 모니터 반환
        assert monitor.name == "Test Monitor"
        assert monitor.url == "https://test.example.com"
        assert monitor.status == UptimeStatus.UNKNOWN
        assert monitor.id == "dummy-id"

    @pytest.mark.asyncio
    async def test_delete_monitor_test_mode(self, hetrix_client):
        """모니터 삭제 테스트 모드"""
        # When: 모니터 삭제 (테스트 모드)
        result = await hetrix_client.delete_monitor("test-id")

        # Then: False 반환 (테스트 모드)
        assert result is False


class TestHetrixMonitoringService:
    """HetrixMonitoringService 단위 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock HetrixToolsClient"""
        return AsyncMock(spec=HetrixToolsClient)

    @pytest.fixture
    def hetrix_service(self):
        """HetrixMonitoringService 인스턴스"""
        return HetrixMonitoringService(api_token="test_api_token")

    @pytest.mark.asyncio
    async def test_get_monitors_async_success(self, hetrix_service, mock_client):
        """모니터 목록 조회 비동기 성공 테스트"""
        # Given: Mock 클라이언트가 모니터 목록 반환
        mock_monitors = [
            Monitor(
                id="test-id",
                name="test-monitor",
                url="https://test.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            )
        ]
        mock_client.get_monitors.return_value = mock_monitors

        with patch('nadle_backend.services.hetrix_monitoring.HetrixToolsClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # When: 모니터 목록 조회
            monitors = await hetrix_service.get_monitors_async()

            # Then: 모니터 목록 반환
            assert len(monitors) == 1
            assert monitors[0].name == "test-monitor"

    @pytest.mark.asyncio
    async def test_get_current_environment_monitors_development(self, hetrix_service):
        """현재 환경 모니터 조회 - 개발환경 테스트"""
        # Given: 개발환경은 스테이징 모니터 사용
        mock_monitors = [
            Monitor(
                id="staging-id",
                name="staging-xai-community",
                url="https://staging.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            )
        ]

        with patch('nadle_backend.services.hetrix_monitoring.HetrixToolsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_monitors_by_environment.return_value = mock_monitors
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            with patch('nadle_backend.services.hetrix_monitoring.settings') as mock_settings:
                mock_settings.environment = 'development'
                
                # When: 현재 환경 모니터 조회
                current_monitors = await hetrix_service.get_current_environment_monitors()

                # Then: 스테이징 모니터 반환
                assert len(current_monitors) == 1
                assert current_monitors[0].name == "staging-xai-community"

    @pytest.mark.asyncio
    async def test_get_current_environment_monitors_production(self, hetrix_service):
        """현재 환경 모니터 조회 - 프로덕션 테스트"""
        # Given: 프로덕션 모니터
        mock_monitors = [
            Monitor(
                id="prod-id",
                name="production-xai-community",
                url="https://production.example.com",
                status=UptimeStatus.UP,
                uptime=99.9,
                created_at=1752496680,
                last_check=1752541350,
                last_status_change=1752496778
            )
        ]

        with patch('nadle_backend.services.hetrix_monitoring.HetrixToolsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_monitors_by_environment.return_value = mock_monitors
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            with patch('nadle_backend.services.hetrix_monitoring.settings') as mock_settings:
                mock_settings.environment = 'production'
                
                # When: 현재 환경 모니터 조회
                current_monitors = await hetrix_service.get_current_environment_monitors()

                # Then: 프로덕션 모니터 반환
                assert len(current_monitors) == 1
                assert current_monitors[0].name == "production-xai-community"

    def test_service_initialization_error(self):
        """서비스 초기화 오류 테스트"""
        # When/Then: API 토큰 없이 초기화 시 예외 발생
        with pytest.raises(ValueError) as exc_info:
            HetrixMonitoringService(api_token=None)
        
        assert "HetrixTools API 토큰이 설정되지 않았습니다" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, hetrix_service):
        """컨텍스트 매니저 사용 테스트"""
        # Given: Mock 클라이언트
        mock_client = AsyncMock()
        
        with patch.object(HetrixToolsClient, '__new__', return_value=mock_client):
            # When: 컨텍스트 매니저로 사용
            async with hetrix_service as service:
                assert service.client is not None
                
            # Then: 클라이언트가 정리됨
            mock_client.__aexit__.assert_called_once()


class TestHealthCheckService:
    """HealthCheckService 단위 테스트 (HetrixTools 통합)"""

    @pytest.fixture
    def health_service(self):
        """헬스체크 서비스 인스턴스"""
        return HealthCheckService()

    @pytest.mark.asyncio
    async def test_simple_health_check_success(self, health_service):
        """간단한 헬스체크 성공 테스트"""
        # When: 간단한 헬스체크 실행
        result = await health_service.simple_health_check()

        # Then: 정상 응답
        assert result["status"] == "healthy"
        assert result["service"] == "nadle-backend-api"
        assert result["monitoring_service"] == "hetrixtools"
        assert "timestamp" in result
        assert "uptime" in result

    @pytest.mark.asyncio
    async def test_comprehensive_health_check_healthy(self, health_service):
        """종합 헬스체크 - 정상 상태 테스트"""
        # Given: 모든 의존성이 정상
        with patch.object(health_service, '_check_database') as mock_db, \
             patch.object(health_service, '_check_redis') as mock_redis, \
             patch.object(health_service, '_check_external_apis') as mock_apis, \
             patch.object(health_service, '_check_hetrix_monitoring') as mock_hetrix:
            
            mock_db.return_value = {"status": "healthy", "response_time": 10}
            mock_redis.return_value = {"status": "healthy", "response_time": 5}
            mock_apis.return_value = {"status": "healthy", "apis_checked": 0}
            mock_hetrix.return_value = {
                "status": "healthy", 
                "total_monitors": 2, 
                "active_monitors": 2,
                "api_service": "hetrixtools_v3"
            }

            # When: 종합 헬스체크 실행
            result = await health_service.comprehensive_health_check()

            # Then: 정상 상태 반환
            assert result["status"] == "healthy"
            assert result["overall_health"] == "healthy"
            assert "database" in result["checks"]
            assert "redis" in result["checks"]
            assert "external_apis" in result["checks"]
            assert "hetrix_monitoring" in result["checks"]
            assert result["monitoring_service"] == "hetrixtools"
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_comprehensive_health_check_unhealthy(self, health_service):
        """종합 헬스체크 - 비정상 상태 테스트"""
        # Given: HetrixTools 모니터링이 비정상
        with patch.object(health_service, '_check_database') as mock_db, \
             patch.object(health_service, '_check_redis') as mock_redis, \
             patch.object(health_service, '_check_external_apis') as mock_apis, \
             patch.object(health_service, '_check_hetrix_monitoring') as mock_hetrix:
            
            mock_db.return_value = {"status": "healthy", "response_time": 10}
            mock_redis.return_value = {"status": "healthy", "response_time": 5}
            mock_apis.return_value = {"status": "healthy", "apis_checked": 0}
            mock_hetrix.return_value = {
                "status": "unhealthy", 
                "error": "API connection failed",
                "api_service": "hetrixtools_v3"
            }

            # When: 종합 헬스체크 실행
            result = await health_service.comprehensive_health_check()

            # Then: 정상 상태 (HetrixTools 오류는 전체 상태에 영향 없음)
            assert result["status"] == "healthy"
            assert result["overall_health"] == "healthy"
            assert result["checks"]["hetrix_monitoring"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_hetrix_monitoring_success(self, health_service):
        """HetrixTools 모니터링 상태 확인 성공 테스트"""
        # Given: 정상적인 HetrixTools API 응답
        mock_monitors = [
            Monitor(
                id="test-id-1",
                name="monitor-1",
                url="https://test1.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            ),
            Monitor(
                id="test-id-2",
                name="monitor-2",
                url="https://test2.example.com",
                status=UptimeStatus.UP,
                uptime=99.9,
                created_at=1752496680,
                last_check=1752541350,
                last_status_change=1752496778
            )
        ]

        with patch('nadle_backend.services.hetrix_monitoring.settings') as mock_settings, \
             patch('nadle_backend.services.hetrix_monitoring.HetrixToolsClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.get_monitors.return_value = mock_monitors
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            mock_settings.hetrixtools_api_token = "test_token"
            
            # When: HetrixTools 모니터링 상태 확인
            result = await health_service._check_hetrix_monitoring()

            # Then: 정상 상태 반환
            assert result["status"] == "healthy"
            assert result["total_monitors"] == 2
            assert result["active_monitors"] == 2
            assert result["api_service"] == "hetrixtools_v3"

    @pytest.mark.asyncio
    async def test_check_hetrix_monitoring_no_token(self, health_service):
        """HetrixTools 토큰 없음 테스트"""
        # Given: API 토큰이 설정되지 않음
        with patch('nadle_backend.services.hetrix_monitoring.settings') as mock_settings:
            mock_settings.hetrixtools_api_token = None
            
            # When: HetrixTools 모니터링 상태 확인
            result = await health_service._check_hetrix_monitoring()

            # Then: 경고 상태 반환
            assert result["status"] == "warning"
            assert "HetrixTools API 토큰이 설정되지 않음" in result["message"]

    @pytest.mark.asyncio
    async def test_check_hetrix_monitoring_api_error(self, health_service):
        """HetrixTools API 오류 테스트"""
        # Given: API 호출 실패
        with patch('nadle_backend.services.hetrix_monitoring.settings') as mock_settings, \
             patch('nadle_backend.services.hetrix_monitoring.HetrixToolsClient') as mock_client_class:
            
            mock_client = AsyncMock()
            mock_client.get_monitors.side_effect = Exception("API Error")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            mock_settings.hetrixtools_api_token = "test_token"
            
            # When: HetrixTools 모니터링 상태 확인
            result = await health_service._check_hetrix_monitoring()

            # Then: 비정상 상태 반환
            assert result["status"] == "unhealthy"
            assert "API Error" in result["error"]
            assert result["api_service"] == "hetrixtools_v3"


class TestDataModels:
    """데이터 모델 테스트"""

    def test_uptime_status_enum(self):
        """UptimeStatus Enum 테스트"""
        assert UptimeStatus.UP.value == "up"
        assert UptimeStatus.DOWN.value == "down"
        assert UptimeStatus.PAUSED.value == "paused"
        assert UptimeStatus.UNKNOWN.value == "unknown"

    def test_monitor_model_creation(self):
        """Monitor 모델 생성 테스트"""
        monitor = Monitor(
            id="test-id",
            name="Test Monitor",
            url="https://example.com",
            status=UptimeStatus.UP,
            uptime=99.5,
            created_at=1752496648,
            last_check=1752541294,
            last_status_change=1752496723,
            monitor_type="website",
            target="https://example.com/health"
        )

        assert monitor.id == "test-id"
        assert monitor.name == "Test Monitor"
        assert monitor.url == "https://example.com"
        assert monitor.status == UptimeStatus.UP
        assert monitor.uptime == 99.5
        assert monitor.monitor_type == "website"
        assert monitor.target == "https://example.com/health"

    def test_monitor_model_status_conversion(self):
        """Monitor 모델 상태 변환 테스트"""
        # String으로 상태 전달
        monitor = Monitor(
            id="test-id",
            name="Test Monitor",
            url="https://example.com",
            status="up",  # String
            uptime=100.0,
            created_at=1752496648,
            last_check=1752541294,
            last_status_change=1752496723
        )

        # UptimeStatus Enum으로 변환됨
        assert isinstance(monitor.status, UptimeStatus)
        assert monitor.status == UptimeStatus.UP

    def test_monitor_model_post_init(self):
        """Monitor 모델 초기화 후 처리 테스트"""
        monitor = Monitor(
            id="test-id",
            name="Test Monitor",
            url="",  # 빈 URL
            target="https://example.com/health",  # target은 설정
            status=UptimeStatus.UP,
            uptime=100.0,
            created_at=1752496648,
            last_check=1752541294,
            last_status_change=1752496723
        )

        # target이 url로 복사됨
        assert monitor.url == "https://example.com/health"
        assert isinstance(monitor.response_time, dict)
        assert isinstance(monitor.locations, dict)

    def test_monitor_log_model(self):
        """MonitorLog 모델 테스트"""
        log = MonitorLog(
            datetime="2025-07-15T01:00:00Z",
            type="up",
            duration=1234,
            reason="HTTP 200 OK"
        )

        assert log.datetime == "2025-07-15T01:00:00Z"
        assert log.type == "up"
        assert log.duration == 1234
        assert log.reason == "HTTP 200 OK"


class TestHetrixMonitoringIntegration:
    """HetrixTools 모니터링 통합 테스트"""

    @pytest.mark.asyncio
    async def test_service_and_health_check_integration(self):
        """서비스와 헬스체크 통합 테스트"""
        # Given: Mock 서비스들
        mock_monitors = [
            Monitor(
                id="integration-test-id",
                name="integration-test-monitor",
                url="https://integration.example.com",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723
            )
        ]

        hetrix_service = HetrixMonitoringService(api_token="test_token")
        health_service = HealthCheckService()

        with patch('nadle_backend.services.hetrix_monitoring.HetrixToolsClient') as mock_client_class, \
             patch.object(health_service, '_check_database') as mock_db, \
             patch.object(health_service, '_check_redis') as mock_redis, \
             patch.object(health_service, '_check_external_apis') as mock_apis, \
             patch.object(health_service, '_check_hetrix_monitoring') as mock_hetrix:
            
            mock_client = AsyncMock()
            mock_client.get_monitors.return_value = mock_monitors
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            mock_db.return_value = {"status": "healthy", "response_time": 10}
            mock_redis.return_value = {"status": "healthy", "response_time": 5}
            mock_apis.return_value = {"status": "healthy", "apis_checked": 0}
            mock_hetrix.return_value = {
                "status": "healthy", 
                "total_monitors": 1, 
                "active_monitors": 1,
                "api_service": "hetrixtools_v3"
            }

            # When: 서비스 조회와 헬스체크 실행
            monitors = await hetrix_service.get_monitors_async()
            health_result = await health_service.comprehensive_health_check()

        # Then: 모두 정상 작동
        assert len(monitors) == 1
        assert monitors[0].name == "integration-test-monitor"
        assert health_result["status"] == "healthy"
        assert health_result["checks"]["hetrix_monitoring"]["status"] == "healthy"

    def test_error_handling_chain(self):
        """에러 처리 체인 테스트"""
        # Given: 잘못된 토큰으로 서비스 초기화 시도
        with pytest.raises(ValueError):
            HetrixMonitoringService(api_token="")

        with pytest.raises(ValueError):
            HetrixMonitoringService(api_token=None)

        # Given: 정상 토큰으로 서비스 생성
        service = HetrixMonitoringService(api_token="valid_token")
        assert service.api_token == "valid_token"

    @pytest.mark.asyncio
    async def test_backward_compatibility(self):
        """기존 UptimeRobot 인터페이스 호환성 테스트"""
        # Given: UptimeMonitoringService 별칭 사용
        from nadle_backend.services.hetrix_monitoring import UptimeMonitoringService
        
        # UptimeMonitoringService는 HetrixMonitoringService의 별칭
        service = UptimeMonitoringService(api_token="test_token")
        assert isinstance(service, HetrixMonitoringService)
        
        # 기존 메서드들이 여전히 작동
        assert hasattr(service, 'get_monitors')
        assert hasattr(service, 'create_monitor')
        assert hasattr(service, 'delete_monitor')
        assert hasattr(service, 'get_monitor_logs')