"""
모니터링 API HTTP 엔드포인트 통합 테스트

실제 FastAPI HTTP 엔드포인트 테스트 (Redis Mock 사용)
"""
import pytest
import json
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock


@pytest.mark.integration
class TestMonitoringAPIHTTPIntegration:
    """모니터링 API HTTP 엔드포인트 통합 테스트"""

    @pytest.fixture
    def mock_monitoring_service(self):
        """모킹된 모니터링 서비스"""
        from unittest.mock import AsyncMock
        
        mock_service = AsyncMock()
        
        # get_system_metrics Mock
        mock_service.get_system_metrics.return_value = {
            "endpoints": {"GET:/api/posts": 150, "POST:/api/posts": 25},
            "status_codes": {"200": 120, "201": 25, "404": 5},
            "timestamp": time.time()
        }
        
        # get_health_status Mock
        mock_service.get_health_status.return_value = {
            "status": "healthy",
            "total_requests": 1000,
            "success_requests": 950,
            "error_requests": 50,
            "error_rate": 0.05,
            "availability": 0.95,
            "timestamp": time.time()
        }
        
        # get_endpoint_stats Mock
        mock_service.get_endpoint_stats.return_value = {
            "avg_response_time": 0.12,
            "min_response_time": 0.08,
            "max_response_time": 0.25,
            "request_count": 150
        }
        
        # get_slow_requests Mock
        mock_service.get_slow_requests.return_value = [
            {"endpoint": "GET:/api/posts", "response_time": 2.5, "timestamp": time.time()},
            {"endpoint": "POST:/api/users", "response_time": 3.1, "timestamp": time.time()}
        ]
        
        # get_time_series_data Mock
        mock_service.get_time_series_data.return_value = {
            "timestamps": [time.time() - 300, time.time() - 200, time.time() - 100],
            "response_times": [0.1, 0.15, 0.08]
        }
        
        # get_popular_endpoints Mock
        mock_service.get_popular_endpoints.return_value = [
            {"endpoint": "GET:/api/posts", "requests": 150},
            {"endpoint": "GET:/api/users", "requests": 75},
            {"endpoint": "POST:/api/posts", "requests": 25}
        ]
        
        # get_aggregated_metrics Mock
        mock_service.get_aggregated_metrics.return_value = {
            "total_requests": 150,
            "success_rate": 0.933,
            "endpoints_count": 2,
            "timestamp": time.time()
        }
        
        return mock_service

    @pytest.fixture
    def app_with_monitoring_api(self, mock_monitoring_service):
        """모니터링 API가 포함된 테스트 앱"""
        app = FastAPI()
        
        # 모니터링 API 라우터 추가 (의존성 오버라이드)
        from nadle_backend.routers.monitoring import router as monitoring_router
        from nadle_backend.services.monitoring_service import get_monitoring_service
        
        app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
        
        # 의존성 오버라이드
        app.dependency_overrides[get_monitoring_service] = lambda: mock_monitoring_service
        
        return app

    @pytest.fixture
    def client(self, app_with_monitoring_api):
        """테스트 클라이언트"""
        return TestClient(app_with_monitoring_api)

    def test_get_system_metrics_endpoint(self, client, mock_monitoring_service):
        """시스템 메트릭 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/metrics
        response = client.get("/api/monitoring/metrics")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoints" in data
        assert "status_codes" in data
        assert "timestamp" in data
        assert data["endpoints"]["GET:/api/posts"] == 150
        assert data["status_codes"]["200"] == 120
        
        # 서비스 메서드가 호출되었는지 확인
        mock_monitoring_service.get_system_metrics.assert_called_once()

    def test_get_health_status_endpoint(self, client, mock_monitoring_service):
        """헬스 상태 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/health
        response = client.get("/api/monitoring/health")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "total_requests" in data
        assert "error_rate" in data
        assert "availability" in data
        assert data["status"] == "healthy"
        assert data["error_rate"] == 0.05
        
        # 서비스 메서드가 호출되었는지 확인
        mock_monitoring_service.get_health_status.assert_called_once()

    def test_get_endpoint_stats_endpoint(self, client, mock_monitoring_service):
        """특정 엔드포인트 통계 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/endpoints/GET:/api/posts
        response = client.get("/api/monitoring/endpoints/GET:/api/posts")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "avg_response_time" in data
        assert "min_response_time" in data
        assert "max_response_time" in data
        assert "request_count" in data
        assert data["request_count"] == 150
        assert data["avg_response_time"] == 0.12
        
        # 서비스 메서드가 올바른 파라미터로 호출되었는지 확인
        mock_monitoring_service.get_endpoint_stats.assert_called_once_with("GET:/api/posts")

    def test_get_slow_requests_endpoint(self, client, mock_monitoring_service):
        """느린 요청 목록 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/slow-requests?limit=10
        response = client.get("/api/monitoring/slow-requests?limit=10")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "slow_requests" in data
        slow_requests = data["slow_requests"]
        assert len(slow_requests) == 2
        assert slow_requests[0]["endpoint"] == "GET:/api/posts"
        assert slow_requests[0]["response_time"] == 2.5
        
        # 서비스 메서드가 올바른 파라미터로 호출되었는지 확인
        mock_monitoring_service.get_slow_requests.assert_called_once_with(10)

    def test_get_time_series_endpoint(self, client, mock_monitoring_service):
        """시간별 시계열 데이터 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/timeseries/GET:/api/posts?minutes=60
        response = client.get("/api/monitoring/timeseries/GET:/api/posts?minutes=60")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamps" in data
        assert "response_times" in data
        assert len(data["timestamps"]) == 3
        assert len(data["response_times"]) == 3
        
        # 서비스 메서드가 올바른 파라미터로 호출되었는지 확인
        mock_monitoring_service.get_time_series_data.assert_called_once_with("GET:/api/posts", 60)

    def test_get_popular_endpoints_endpoint(self, client, mock_monitoring_service):
        """인기 엔드포인트 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/popular-endpoints?limit=5
        response = client.get("/api/monitoring/popular-endpoints?limit=5")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "popular_endpoints" in data
        popular_endpoints = data["popular_endpoints"]
        assert len(popular_endpoints) == 3
        assert popular_endpoints[0]["endpoint"] == "GET:/api/posts"
        assert popular_endpoints[0]["requests"] == 150
        
        # 서비스 메서드가 올바른 파라미터로 호출되었는지 확인
        mock_monitoring_service.get_popular_endpoints.assert_called_once_with(5)

    def test_get_monitoring_summary_endpoint(self, client, mock_monitoring_service):
        """모니터링 요약 대시보드 데이터 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/summary
        response = client.get("/api/monitoring/summary")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "health" in data
        assert "aggregated_metrics" in data
        assert "popular_endpoints" in data
        assert "recent_slow_requests" in data
        
        # 모든 관련 서비스 메서드들이 호출되었는지 확인
        mock_monitoring_service.get_health_status.assert_called()
        mock_monitoring_service.get_aggregated_metrics.assert_called()
        mock_monitoring_service.get_popular_endpoints.assert_called_with(5)
        mock_monitoring_service.get_slow_requests.assert_called_with(10)

    def test_get_dashboard_data_endpoint(self, client, mock_monitoring_service):
        """실시간 대시보드 데이터 조회 HTTP 엔드포인트 테스트"""
        # When: GET /api/monitoring/dashboard
        response = client.get("/api/monitoring/dashboard")
        
        # Then: 올바른 응답
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"
        
        dashboard_data = data["data"]
        assert "metrics" in dashboard_data
        assert "health" in dashboard_data
        assert "popular_endpoints" in dashboard_data
        assert "slow_requests" in dashboard_data

    def test_query_parameter_validation(self, client, mock_monitoring_service):
        """쿼리 파라미터 검증 테스트"""
        # When: 잘못된 limit 파라미터
        response = client.get("/api/monitoring/slow-requests?limit=300")  # 최대값 200 초과
        
        # Then: 검증 에러
        assert response.status_code == 422  # Validation Error
        
        # When: 음수 limit 파라미터
        response = client.get("/api/monitoring/slow-requests?limit=-1")
        
        # Then: 검증 에러
        assert response.status_code == 422

    def test_path_parameter_validation(self, client, mock_monitoring_service):
        """경로 파라미터 검증 테스트"""
        # When: 유효한 엔드포인트 경로
        response = client.get("/api/monitoring/endpoints/GET:/api/posts/123")
        
        # Then: 정상 처리
        assert response.status_code == 200
        
        # 경로에 특수 문자가 포함된 경우도 처리됨
        mock_monitoring_service.get_endpoint_stats.assert_called_with("GET:/api/posts/123")

    def test_service_error_handling(self, client, mock_monitoring_service):
        """서비스 에러 처리 테스트"""
        # Given: 서비스에서 예외 발생
        mock_monitoring_service.get_system_metrics.side_effect = Exception("Redis connection failed")
        
        # When: 메트릭 조회
        response = client.get("/api/monitoring/metrics")
        
        # Then: 500 에러 반환
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Failed to retrieve system metrics" in error_data["detail"]

    def test_endpoints_documentation_compliance(self, client):
        """API 엔드포인트 문서화 준수 테스트"""
        # When: OpenAPI 스키마 조회
        response = client.get("/openapi.json")
        
        # Then: 성공적으로 스키마 반환
        assert response.status_code == 200
        openapi_schema = response.json()
        
        # 모니터링 API 엔드포인트들이 스키마에 포함되었는지 확인
        paths = openapi_schema.get("paths", {})
        assert "/api/monitoring/metrics" in paths
        assert "/api/monitoring/health" in paths
        assert "/api/monitoring/endpoints/{endpoint}" in paths
        assert "/api/monitoring/slow-requests" in paths
        assert "/api/monitoring/timeseries/{endpoint}" in paths
        assert "/api/monitoring/popular-endpoints" in paths
        assert "/api/monitoring/summary" in paths
        assert "/api/monitoring/dashboard" in paths

    def test_cors_headers(self, client):
        """CORS 헤더 테스트"""
        # When: OPTIONS 요청 (preflight)
        response = client.options("/api/monitoring/metrics")
        
        # Then: 적절한 CORS 응답
        # FastAPI의 CORS 미들웨어가 설정되어 있다면 적절한 헤더들이 포함됨
        assert response.status_code in [200, 405]  # OPTIONS 허용 또는 미허용

    def test_response_format_consistency(self, client, mock_monitoring_service):
        """응답 형식 일관성 테스트"""
        endpoints_to_test = [
            ("/api/monitoring/metrics", ["endpoints", "status_codes", "timestamp"]),
            ("/api/monitoring/health", ["status", "total_requests", "error_rate"]),
            ("/api/monitoring/slow-requests", ["slow_requests"]),
            ("/api/monitoring/popular-endpoints", ["popular_endpoints"]),
        ]
        
        for endpoint, expected_keys in endpoints_to_test:
            # When: 각 엔드포인트 호출
            response = client.get(endpoint)
            
            # Then: 일관된 JSON 응답 형식
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Missing key '{key}' in response from {endpoint}"