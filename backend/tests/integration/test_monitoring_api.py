"""
HetrixTools 모니터링 API 통합 테스트

FastAPI 엔드포인트를 통한 HetrixTools 모니터링 기능 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from main import app
from nadle_backend.services.hetrix_monitoring import Monitor, UptimeStatus


class TestMonitoringAPI:
    """모니터링 API 통합 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def mock_monitors(self):
        """Mock 모니터 데이터"""
        return [
            Monitor(
                id="staging-id",
                name="staging-xai-community",
                url="https://staging.example.com/health",
                status=UptimeStatus.UP,
                uptime=100.0,
                created_at=1752496648,
                last_check=1752541294,
                last_status_change=1752496723,
                monitor_type="website",
                response_time={"tokyo": 132, "singapore": 227},
                locations={"tokyo": {"uptime_status": "up", "response_time": 132}}
            ),
            Monitor(
                id="prod-id",
                name="production-xai-community",
                url="https://production.example.com/health",
                status=UptimeStatus.UP,
                uptime=99.9,
                created_at=1752496680,
                last_check=1752541350,
                last_status_change=1752496778,
                monitor_type="website",
                response_time={"tokyo": 127, "singapore": 197},
                locations={"tokyo": {"uptime_status": "up", "response_time": 127}}
            )
        ]

    def test_monitoring_status_success(self, client):
        """모니터링 상태 조회 성공 테스트"""
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_get_health:
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy",
                "service": "nadle-backend-api"
            }
            mock_health_service._check_hetrix_monitoring.return_value = {
                "status": "healthy",
                "total_monitors": 2,
                "active_monitors": 2
            }
            mock_get_health.return_value = mock_health_service

            # When: 모니터링 상태 조회
            response = client.get("/api/monitoring/status")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "operational"
            assert data["monitoring_service"] == "hetrixtools"
            assert "timestamp" in data
            assert "api_health" in data
            assert "hetrix_monitoring" in data

    def test_get_monitors_all(self, client, mock_monitors):
        """전체 모니터 목록 조회 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.get_monitors_async.return_value = mock_monitors
            mock_get_service.return_value = mock_service

            # When: 전체 모니터 목록 조회
            response = client.get("/api/monitoring/hetrix/monitors")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["environment"] == "all"
            assert len(data["monitors"]) == 2
            
            # 첫 번째 모니터 검증
            monitor1 = data["monitors"][0]
            assert monitor1["id"] == "staging-id"
            assert monitor1["name"] == "staging-xai-community"
            assert monitor1["status"] == "up"
            assert monitor1["uptime"] == 100.0

    def test_get_monitors_by_environment(self, client, mock_monitors):
        """환경별 모니터 조회 테스트"""
        staging_monitors = [mock_monitors[0]]  # staging 모니터만
        
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.client.get_monitors_by_environment.return_value = staging_monitors
            mock_get_service.return_value = mock_service

            # When: 스테이징 환경 모니터 조회
            response = client.get("/api/monitoring/hetrix/monitors?environment=staging")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["environment"] == "staging"
            assert len(data["monitors"]) == 1
            assert data["monitors"][0]["name"] == "staging-xai-community"

    def test_get_monitor_by_id_success(self, client, mock_monitors):
        """ID로 모니터 조회 성공 테스트"""
        mock_monitor = mock_monitors[0]
        
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.client.get_monitor_by_id.return_value = mock_monitor
            mock_get_service.return_value = mock_service

            # When: 특정 ID로 모니터 조회
            response = client.get("/api/monitoring/hetrix/monitors/staging-id")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert "monitor" in data
            assert data["monitor"]["id"] == "staging-id"
            assert data["monitor"]["name"] == "staging-xai-community"

    def test_get_monitor_by_id_not_found(self, client):
        """ID로 모니터 조회 실패 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.client.get_monitor_by_id.return_value = None
            mock_get_service.return_value = mock_service

            # When: 존재하지 않는 ID로 모니터 조회
            response = client.get("/api/monitoring/hetrix/monitors/non-existent-id")

            # Then: 404 응답
            assert response.status_code == 404
            data = response.json()
            assert "찾을 수 없습니다" in data["detail"]

    def test_get_monitor_by_name_success(self, client, mock_monitors):
        """이름으로 모니터 조회 성공 테스트"""
        mock_monitor = mock_monitors[0]
        
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.client.get_monitor_by_name.return_value = mock_monitor
            mock_get_service.return_value = mock_service

            # When: 이름으로 모니터 조회
            response = client.get("/api/monitoring/hetrix/monitors/name/staging-xai-community")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert "monitor" in data
            assert data["monitor"]["name"] == "staging-xai-community"

    def test_get_current_environment_monitors(self, client, mock_monitors):
        """현재 환경 모니터 조회 테스트"""
        current_monitors = [mock_monitors[1]]  # production 모니터
        
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service, \
             patch('nadle_backend.routers.monitoring.get_settings') as mock_get_settings:
            
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.get_current_environment_monitors.return_value = current_monitors
            mock_get_service.return_value = mock_service
            
            mock_settings = AsyncMock()
            mock_settings.environment = "production"
            mock_get_settings.return_value = mock_settings

            # When: 현재 환경 모니터 조회
            response = client.get("/api/monitoring/hetrix/current-environment")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["environment"] == "production"
            assert data["total"] == 1
            assert len(data["monitors"]) == 1

    def test_get_monitor_logs(self, client):
        """모니터 로그 조회 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.client.get_monitor_logs.return_value = []  # HetrixTools v3는 로그 미지원
            mock_get_service.return_value = mock_service

            # When: 모니터 로그 조회
            response = client.get("/api/monitoring/hetrix/logs/test-monitor-id?days=7")

            # Then: 성공 응답 (빈 로그)
            assert response.status_code == 200
            data = response.json()
            assert data["monitor_id"] == "test-monitor-id"
            assert data["days"] == 7
            assert data["logs"] == []
            assert "미지원" in data["note"]

    def test_comprehensive_health_check(self, client):
        """종합 헬스체크 테스트"""
        mock_health_result = {
            "status": "healthy",
            "overall_health": "healthy",
            "checks": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "hetrix_monitoring": {"status": "healthy"}
            },
            "monitoring_service": "hetrixtools"
        }
        
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_get_health:
            mock_health_service = AsyncMock()
            mock_health_service.comprehensive_health_check.return_value = mock_health_result
            mock_get_health.return_value = mock_health_service

            # When: 종합 헬스체크
            response = client.get("/api/monitoring/health/comprehensive")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "checks" in data
            assert data["monitoring_service"] == "hetrixtools"

    def test_simple_health_check(self, client):
        """간단한 헬스체크 테스트"""
        mock_health_result = {
            "status": "healthy",
            "service": "nadle-backend-api",
            "monitoring_service": "hetrixtools"
        }
        
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_get_health:
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = mock_health_result
            mock_get_health.return_value = mock_health_service

            # When: 간단한 헬스체크
            response = client.get("/api/monitoring/health/simple")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "nadle-backend-api"
            assert data["monitoring_service"] == "hetrixtools"

    def test_monitoring_summary(self, client, mock_monitors):
        """모니터링 요약 정보 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service, \
             patch('nadle_backend.routers.monitoring.get_health_service') as mock_get_health:
            
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.get_monitors_async.return_value = mock_monitors
            mock_get_service.return_value = mock_service
            
            mock_health_service = AsyncMock()
            mock_health_service._check_hetrix_monitoring.return_value = {
                "status": "healthy"
            }
            mock_get_health.return_value = mock_health_service

            # When: 모니터링 요약 조회
            response = client.get("/api/monitoring/summary")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["total_monitors"] == 2
            assert data["average_uptime"] == 99.95  # (100.0 + 99.9) / 2
            assert "status_breakdown" in data
            assert data["monitoring_service"] == "hetrixtools_v3"

    def test_legacy_uptime_monitors_endpoint(self, client, mock_monitors):
        """레거시 UptimeRobot 호환 엔드포인트 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.__aenter__.return_value = mock_service
            mock_service.__aexit__.return_value = None
            mock_service.get_monitors_async.return_value = mock_monitors
            mock_get_service.return_value = mock_service

            # When: 레거시 엔드포인트 호출
            response = client.get("/api/monitoring/uptime/monitors")

            # Then: UptimeRobot 형식으로 응답
            assert response.status_code == 200
            data = response.json()
            assert data["stat"] == "ok"
            assert "monitors" in data
            assert len(data["monitors"]) == 2
            
            # UptimeRobot 형식 확인
            monitor = data["monitors"][0]
            assert "friendly_name" in monitor
            assert monitor["status"] == 2  # UptimeRobot UP 상태
            assert monitor["type"] == 1  # HTTP(s)

    def test_api_error_handling(self, client):
        """API 오류 처리 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            # HetrixTools API 토큰 없음 시뮬레이션
            mock_get_service.side_effect = Exception("HetrixTools API 토큰이 설정되지 않았습니다")

            # When: 토큰 없이 API 호출
            response = client.get("/api/monitoring/hetrix/monitors")

            # Then: 500 오류 응답
            assert response.status_code == 500
            data = response.json()
            assert "오류" in data["detail"] or "실패" in data["detail"]

    def test_api_service_unavailable(self, client):
        """HetrixTools 서비스 사용 불가 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_get_service:
            # 서비스 사용 불가 시뮬레이션 (HTTPException 503)
            from fastapi import HTTPException
            mock_get_service.side_effect = HTTPException(
                status_code=503, 
                detail="HetrixTools API 토큰이 설정되지 않았습니다"
            )

            # When: 서비스 불가 상태에서 API 호출
            response = client.get("/api/monitoring/hetrix/monitors")

            # Then: 503 오류 응답
            assert response.status_code == 503
            data = response.json()
            assert "설정되지 않았습니다" in data["detail"]


class TestMonitoringAPIPerformance:
    """모니터링 API 성능 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    def test_api_response_time(self, client):
        """API 응답 시간 테스트"""
        import time
        
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_get_health:
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy",
                "service": "nadle-backend-api"
            }
            mock_health_service._check_hetrix_monitoring.return_value = {
                "status": "healthy"
            }
            mock_get_health.return_value = mock_health_service

            # When: API 응답시간 측정
            start_time = time.time()
            response = client.get("/api/monitoring/status")
            end_time = time.time()

            response_time = end_time - start_time

            # Then: 응답시간이 합리적인 범위
            assert response.status_code == 200
            assert response_time < 1.0  # 1초 미만

    def test_concurrent_api_requests(self, client):
        """동시 API 요청 처리 테스트"""
        import concurrent.futures
        
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_get_health:
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy"
            }
            mock_health_service._check_hetrix_monitoring.return_value = {
                "status": "healthy"
            }
            mock_get_health.return_value = mock_health_service

            def make_request():
                return client.get("/api/monitoring/status")

            # When: 동시에 여러 요청
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                responses = [future.result() for future in futures]

            # Then: 모든 요청이 성공
            assert len(responses) == 5
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "operational"