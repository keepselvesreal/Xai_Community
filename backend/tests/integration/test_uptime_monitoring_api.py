"""
업타임 모니터링 API 엔드포인트 테스트

실제 FastAPI 서버를 통한 API 엔드포인트 통합 테스트
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from main import app


@pytest.mark.integration
@pytest.mark.asyncio
class TestUptimeMonitoringAPI:
    """업타임 모니터링 API 엔드포인트 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """비동기 테스트 클라이언트"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    def test_simple_health_check_endpoint(self, client):
        """간단한 헬스체크 엔드포인트 테스트"""
        # When: 헬스체크 엔드포인트 호출
        response = client.get("/api/monitoring/health/simple")
        
        # Then: 정상 응답
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
        assert data["service"] == "nadle-backend-api"

    def test_comprehensive_health_check_endpoint(self, client):
        """종합 헬스체크 엔드포인트 테스트"""
        # When: 종합 헬스체크 엔드포인트 호출
        response = client.get("/api/monitoring/health/comprehensive")
        
        # Then: 정상 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "overall_health" in data
        assert "checks" in data
        assert "total_response_time" in data
        assert "timestamp" in data
        assert "version" in data
        
        # 각 체크 항목 확인
        checks = data["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "external_apis" in checks

    def test_monitoring_system_status_endpoint(self, client):
        """모니터링 시스템 상태 엔드포인트 테스트"""
        # When: 모니터링 시스템 상태 엔드포인트 호출
        response = client.get("/api/monitoring/status")
        
        # Then: 정상 응답
        assert response.status_code == 200
        data = response.json()
        
        assert data["monitoring_system"] == "operational"
        assert "timestamp" in data
        assert "configurations" in data
        assert "endpoints" in data
        
        # 설정 정보 확인
        config = data["configurations"]
        assert "uptimerobot_configured" in config
        assert "discord_webhook_configured" in config
        assert "smtp_configured" in config
        assert "redis_configured" in config
        assert "sentry_configured" in config
        
        # 엔드포인트 정보 확인
        endpoints = data["endpoints"]
        assert endpoints["health_check"] == "/monitoring/health/simple"
        assert endpoints["comprehensive_health"] == "/monitoring/health/comprehensive"

    def test_notification_test_endpoint(self, client):
        """알림 테스트 엔드포인트 테스트"""
        # Given: 테스트 알림 요청 데이터
        test_data = {
            "message": "업타임 모니터링 API 테스트 메시지",
            "title": "API 테스트",
            "notification_type": "info"
        }
        
        # When: 알림 테스트 엔드포인트 호출
        response = client.post("/api/monitoring/notifications/test", json=test_data)
        
        # Then: 정상 응답 (알림 설정이 없어도 API는 작동해야 함)
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["message"] == "Notification test completed"
        assert "results" in data

    def test_uptime_alert_endpoint(self, client):
        """업타임 알림 엔드포인트 테스트"""
        # Given: 업타임 알림 요청 파라미터
        params = {
            "monitor_name": "Test API Monitor",
            "status": "down",
            "url": "https://api.example.com",
            "duration": 300
        }
        
        # When: 업타임 알림 엔드포인트 호출
        response = client.post("/api/monitoring/alerts/uptime", params=params)
        
        # Then: 정상 응답
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["message"] == "Uptime alert sent"
        assert "results" in data

    @pytest.mark.asyncio
    async def test_health_check_performance(self, async_client):
        """헬스체크 성능 테스트"""
        import time
        
        # When: 헬스체크 엔드포인트 응답시간 측정
        start_time = time.time()
        response = await async_client.get("/api/monitoring/health/simple")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Then: 응답시간이 합리적인 범위 내
        assert response.status_code == 200
        assert response_time < 1.0  # 1초 미만
        
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, async_client):
        """동시 헬스체크 요청 처리 테스트"""
        # When: 동시에 여러 헬스체크 요청
        tasks = [
            async_client.get("/api/monitoring/health/simple") 
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Then: 모든 요청이 성공적으로 처리됨
        assert len(responses) == 5
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_api_documentation_access(self, client):
        """API 문서 접근 테스트 (개발 환경)"""
        # When: OpenAPI 스키마 조회
        response = client.get("/openapi.json")
        
        # Then: 스키마에 업타임 모니터링 엔드포인트가 포함됨
        assert response.status_code == 200
        schema = response.json()
        
        # 업타임 모니터링 관련 경로가 있는지 확인
        paths = schema.get("paths", {})
        monitoring_paths = [
            path for path in paths.keys() 
            if "/monitoring/" in path
        ]
        
        assert len(monitoring_paths) > 0
        assert "/api/monitoring/health/simple" in paths
        assert "/api/monitoring/health/comprehensive" in paths
        assert "/api/monitoring/status" in paths

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client):
        """에러 처리 테스트"""
        # When: 존재하지 않는 모니터 로그 조회
        response = await async_client.get("/api/monitoring/monitors/99999/logs")
        
        # Then: 적절한 에러 응답 (UptimeRobot API 키가 없어서 400 에러 예상)
        assert response.status_code in [400, 503]  # Bad Request 또는 Service Unavailable
        
        data = response.json()
        assert "detail" in data


@pytest.mark.integration 
class TestUptimeMonitoringHealthEndpoints:
    """업타임 모니터링 헬스체크 엔드포인트 성능 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    def test_health_endpoint_external_monitoring(self, client):
        """외부 모니터링 서비스용 헬스체크 테스트"""
        # Given: UptimeRobot 등 외부 모니터링 서비스가 호출하는 상황 시뮬레이션
        headers = {
            "User-Agent": "UptimeRobot/2.0",
            "Accept": "application/json"
        }
        
        # When: 외부 모니터링 서비스가 헬스체크 호출
        response = client.get("/api/monitoring/health/simple", headers=headers)
        
        # Then: 정상 응답
        assert response.status_code == 200
        data = response.json()
        
        # 외부 모니터링에 필요한 최소 정보 포함
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "nadle-backend-api"

    def test_health_endpoint_load_testing(self, client):
        """헬스체크 엔드포인트 부하 테스트"""
        import time
        
        # When: 연속으로 여러 요청 전송
        response_times = []
        for _ in range(10):
            start = time.time()
            response = client.get("/api/monitoring/health/simple")
            end = time.time()
            
            assert response.status_code == 200
            response_times.append(end - start)
        
        # Then: 모든 요청이 성공하고 응답시간이 일정함
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 0.5  # 평균 0.5초 미만
        assert max_response_time < 1.0  # 최대 1초 미만

    def test_comprehensive_health_detailed_info(self, client):
        """종합 헬스체크 상세 정보 테스트"""
        # When: 종합 헬스체크 호출
        response = client.get("/api/monitoring/health/comprehensive")
        
        # Then: 상세한 시스템 정보 포함
        assert response.status_code == 200
        data = response.json()
        
        # 전체 상태
        assert data["status"] in ["healthy", "unhealthy"]
        assert isinstance(data["overall_health"], bool)
        assert isinstance(data["total_response_time"], float)
        
        # 개별 체크 결과
        checks = data["checks"]
        for check_name in ["database", "redis", "external_apis"]:
            assert check_name in checks
            check_result = checks[check_name]
            assert "status" in check_result
            assert check_result["status"] in ["healthy", "unhealthy"]