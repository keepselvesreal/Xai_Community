"""
통합 모니터링 API 테스트
환경별 대시보드 API 및 중복 API 제거 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import json
from datetime import datetime

from main import app
from nadle_backend.services.hetrix_monitoring import Monitor, UptimeStatus


class TestUnifiedMonitoringAPI:
    """통합 모니터링 API 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def mock_monitors_by_env(self):
        """환경별 Mock 모니터 데이터"""
        return {
            "dev": [
                Monitor(
                    id="dev-id-1",
                    name="development-xai-community",
                    url="https://dev.example.com/health",
                    status=UptimeStatus.UP,
                    uptime=99.8,
                    created_at=1752496648,
                    last_check=1752541294,
                    last_status_change=1752496723,
                    monitor_type="website",
                    response_time={"tokyo": 145, "singapore": 250},
                    locations={"tokyo": {"uptime_status": "up", "response_time": 145}}
                )
            ],
            "staging": [
                Monitor(
                    id="staging-id-1",
                    name="staging-xai-community",
                    url="https://staging.example.com/health",
                    status=UptimeStatus.UP,
                    uptime=99.9,
                    created_at=1752496648,
                    last_check=1752541294,
                    last_status_change=1752496723,
                    monitor_type="website",
                    response_time={"tokyo": 132, "singapore": 227},
                    locations={"tokyo": {"uptime_status": "up", "response_time": 132}}
                )
            ],
            "production": [
                Monitor(
                    id="prod-id-1",
                    name="production-xai-community",
                    url="https://prod.example.com/health",
                    status=UptimeStatus.UP,
                    uptime=99.95,
                    created_at=1752496680,
                    last_check=1752541350,
                    last_status_change=1752496778,
                    monitor_type="website",
                    response_time={"tokyo": 127, "singapore": 197},
                    locations={"tokyo": {"uptime_status": "up", "response_time": 127}}
                )
            ]
        }

    @pytest.fixture
    def mock_infrastructure_data(self):
        """Mock 인프라 모니터링 데이터"""
        return {
            "cloud_run": {
                "status": "healthy",
                "cpu_usage": 45.2,
                "memory_usage": 62.1,
                "instances": 3,
                "requests_per_second": 12.5,
                "latency_p95": 234
            },
            "vercel": {
                "status": "healthy",
                "deployment_status": "ready",
                "function_executions": 1542,
                "bandwidth_usage": 1.2,
                "core_web_vitals": {
                    "lcp": 1.2,
                    "fid": 45,
                    "cls": 0.08
                }
            },
            "atlas": {
                "status": "healthy",
                "connections": 15,
                "read_latency": 12.3,
                "write_latency": 18.7,
                "cpu_usage": 35.8,
                "memory_usage": 48.2
            },
            "upstash": {
                "status": "healthy",
                "hit_rate": 94.6,
                "memory_usage": 23.4,
                "connections": 8,
                "operations_per_second": 245
            }
        }

    def test_environments_list_api(self, client):
        """환경 목록 API 테스트"""
        # When: 환경 목록 조회
        response = client.get("/api/monitoring/environments")
        
        # Then: 성공 응답
        assert response.status_code == 200
        data = response.json()
        assert "environments" in data
        assert set(data["environments"]) == {"development", "staging", "production"}
        assert data["default"] == "production"

    def test_unified_dashboard_api_development(self, client, mock_monitors_by_env, mock_infrastructure_data):
        """개발 환경 통합 대시보드 API 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_hetrix, \
             patch('nadle_backend.routers.monitoring.get_unified_monitoring_service') as mock_unified, \
             patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            
            # Mock HetrixTools 서비스
            mock_hetrix_service = AsyncMock()
            mock_hetrix_service.__aenter__.return_value = mock_hetrix_service
            mock_hetrix_service.__aexit__.return_value = None
            mock_hetrix_service.client.get_monitors_by_environment.return_value = mock_monitors_by_env["dev"]
            mock_hetrix.return_value = mock_hetrix_service
            
            # Mock 인프라 모니터링 서비스
            mock_unified_service = AsyncMock()
            mock_unified_service.get_all_infrastructure_status.return_value = mock_infrastructure_data
            mock_unified.return_value = mock_unified_service
            
            # Mock 헬스 서비스
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy",
                "service": "nadle-backend-api",
                "timestamp": datetime.now().isoformat()
            }
            mock_health.return_value = mock_health_service

            # When: 개발 환경 대시보드 API 호출
            response = client.get("/api/monitoring/dashboard/development")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            
            # 환경 정보 확인
            assert data["environment"] == "development"
            assert "timestamp" in data
            
            # 외부 모니터링 (HetrixTools) 확인
            assert "external_monitoring" in data
            external = data["external_monitoring"]
            assert external["service"] == "hetrixtools"
            assert external["total_monitors"] == 1
            assert len(external["monitors"]) == 1
            assert external["monitors"][0]["name"] == "development-xai-community"
            assert external["monitors"][0]["uptime"] == 99.8
            
            # 애플리케이션 모니터링 (헬스체크) 확인
            assert "application_monitoring" in data
            application = data["application_monitoring"]
            assert application["health_status"] == "healthy"
            assert application["service"] == "nadle-backend-api"
            
            # 인프라 모니터링 확인
            assert "infrastructure_monitoring" in data
            infrastructure = data["infrastructure_monitoring"]
            assert "cloud_run" in infrastructure
            assert "vercel" in infrastructure
            assert "atlas" in infrastructure
            assert "upstash" in infrastructure
            
            # Cloud Run 데이터 확인
            assert infrastructure["cloud_run"]["status"] == "healthy"
            assert infrastructure["cloud_run"]["cpu_usage"] == 45.2

    def test_unified_dashboard_api_staging(self, client, mock_monitors_by_env, mock_infrastructure_data):
        """스테이징 환경 통합 대시보드 API 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_hetrix, \
             patch('nadle_backend.routers.monitoring.get_unified_monitoring_service') as mock_unified, \
             patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            
            # Mock 설정
            mock_hetrix_service = AsyncMock()
            mock_hetrix_service.__aenter__.return_value = mock_hetrix_service
            mock_hetrix_service.__aexit__.return_value = None
            mock_hetrix_service.client.get_monitors_by_environment.return_value = mock_monitors_by_env["staging"]
            mock_hetrix.return_value = mock_hetrix_service
            
            mock_unified_service = AsyncMock()
            mock_unified_service.get_all_infrastructure_status.return_value = mock_infrastructure_data
            mock_unified.return_value = mock_unified_service
            
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy",
                "service": "nadle-backend-api"
            }
            mock_health.return_value = mock_health_service

            # When: 스테이징 환경 대시보드 API 호출
            response = client.get("/api/monitoring/dashboard/staging")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            
            assert data["environment"] == "staging"
            assert data["external_monitoring"]["monitors"][0]["name"] == "staging-xai-community"
            assert data["external_monitoring"]["monitors"][0]["uptime"] == 99.9

    def test_unified_dashboard_api_production(self, client, mock_monitors_by_env, mock_infrastructure_data):
        """프로덕션 환경 통합 대시보드 API 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_hetrix, \
             patch('nadle_backend.routers.monitoring.get_unified_monitoring_service') as mock_unified, \
             patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            
            # Mock 설정
            mock_hetrix_service = AsyncMock()
            mock_hetrix_service.__aenter__.return_value = mock_hetrix_service
            mock_hetrix_service.__aexit__.return_value = None
            mock_hetrix_service.client.get_monitors_by_environment.return_value = mock_monitors_by_env["production"]
            mock_hetrix.return_value = mock_hetrix_service
            
            mock_unified_service = AsyncMock()
            mock_unified_service.get_all_infrastructure_status.return_value = mock_infrastructure_data
            mock_unified.return_value = mock_unified_service
            
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy",
                "service": "nadle-backend-api"
            }
            mock_health.return_value = mock_health_service

            # When: 프로덕션 환경 대시보드 API 호출
            response = client.get("/api/monitoring/dashboard/production")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            
            assert data["environment"] == "production"
            assert data["external_monitoring"]["monitors"][0]["name"] == "production-xai-community"
            assert data["external_monitoring"]["monitors"][0]["uptime"] == 99.95

    def test_unified_dashboard_api_invalid_environment(self, client):
        """잘못된 환경 파라미터 테스트"""
        # When: 잘못된 환경으로 API 호출
        response = client.get("/api/monitoring/dashboard/invalid")
        
        # Then: 400 오류 응답
        assert response.status_code == 400
        data = response.json()
        assert "유효하지 않은 환경" in data["detail"]

    def test_existing_apis_with_environment_filter(self, client, mock_monitors_by_env):
        """기존 API들에 환경 필터 파라미터 추가 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_hetrix:
            mock_hetrix_service = AsyncMock()
            mock_hetrix_service.__aenter__.return_value = mock_hetrix_service
            mock_hetrix_service.__aexit__.return_value = None
            mock_hetrix_service.client.get_monitors_by_environment.return_value = mock_monitors_by_env["staging"]
            mock_hetrix.return_value = mock_hetrix_service

            # When: 기존 API에 환경 필터 적용
            response = client.get("/api/monitoring/hetrix/monitors?environment=staging")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["environment"] == "staging"
            assert data["total"] == 1
            assert len(data["monitors"]) == 1
            assert data["monitors"][0]["name"] == "staging-xai-community"

    def test_infrastructure_monitoring_with_environment_filter(self, client, mock_infrastructure_data):
        """인프라 모니터링 환경별 필터링 테스트"""
        with patch('nadle_backend.routers.monitoring.get_unified_monitoring_service') as mock_unified:
            mock_unified_service = AsyncMock()
            mock_unified_service.get_all_infrastructure_status.return_value = mock_infrastructure_data
            mock_unified.return_value = mock_unified_service

            # When: 인프라 모니터링에 환경 필터 적용
            response = client.get("/api/monitoring/infrastructure/status?environment=production")

            # Then: 성공 응답
            assert response.status_code == 200
            data = response.json()
            assert data["environment"] == "production"
            assert "services" in data
            assert "cloud_run" in data["services"]
            assert "vercel" in data["services"]
            assert "atlas" in data["services"]
            assert "upstash" in data["services"]


class TestDuplicateAPIConsolidation:
    """중복 API 통합 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    def test_health_api_consolidation(self, client):
        """헬스 API 통합 테스트"""
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            mock_health_service = AsyncMock()
            mock_health_service.simple_health_check.return_value = {
                "status": "healthy",
                "service": "nadle-backend-api"
            }
            mock_health.return_value = mock_health_service

            # When: 기존 /health 엔드포인트 호출
            response_old = client.get("/health")
            # When: 새로운 /api/monitoring/health/simple 엔드포인트 호출
            response_new = client.get("/api/monitoring/health/simple")

            # Then: 둘 다 동일한 응답 구조
            assert response_old.status_code == 200
            assert response_new.status_code == 200
            
            # 응답 구조가 일치하는지 확인
            old_data = response_old.json()
            new_data = response_new.json()
            
            assert old_data["status"] == new_data["status"]
            assert old_data["service"] == new_data["service"]

    def test_comprehensive_health_api_consolidation(self, client):
        """종합 헬스 API 통합 테스트"""
        mock_health_result = {
            "status": "healthy",
            "overall_health": "healthy",
            "checks": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "hetrix_monitoring": {"status": "healthy"}
            }
        }
        
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            mock_health_service = AsyncMock()
            mock_health_service.comprehensive_health_check.return_value = mock_health_result
            mock_health.return_value = mock_health_service

            # When: 기존 /health/full 엔드포인트 호출
            response_old = client.get("/health/full")
            # When: 새로운 /api/monitoring/health/comprehensive 엔드포인트 호출
            response_new = client.get("/api/monitoring/health/comprehensive")

            # Then: 둘 다 성공
            assert response_old.status_code == 200
            assert response_new.status_code == 200
            
            # 응답 구조가 일치하는지 확인
            old_data = response_old.json()
            new_data = response_new.json()
            
            assert old_data["status"] == new_data["status"]
            assert old_data["overall_health"] == new_data["overall_health"]
            assert "checks" in old_data
            assert "checks" in new_data

    def test_redis_cache_api_consolidation(self, client):
        """Redis 캐시 API 통합 테스트"""
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            mock_health_service = AsyncMock()
            mock_health_service._check_redis_cache.return_value = {
                "status": "healthy",
                "redis_type": "local",
                "key_prefix": "dev:"
            }
            mock_health.return_value = mock_health_service

            # When: 기존 /health/redis 엔드포인트 호출
            response_old = client.get("/health/redis")
            # When: 새로운 /api/monitoring/health/cache 엔드포인트 호출 (통합 후)
            response_new = client.get("/api/monitoring/health/cache")

            # Then: 둘 다 성공
            assert response_old.status_code == 200
            assert response_new.status_code == 200
            
            # 응답 구조가 일치하는지 확인
            old_data = response_old.json()
            new_data = response_new.json()
            
            assert old_data["status"] == new_data["status"]
            assert old_data["redis_type"] == new_data["redis_type"]
            assert old_data["key_prefix"] == new_data["key_prefix"]

    def test_version_api_consolidation(self, client):
        """버전 API 통합 테스트"""
        with patch('nadle_backend.routers.monitoring.get_health_service') as mock_health:
            mock_health_service = AsyncMock()
            mock_health_service.get_version_info.return_value = {
                "version": "1.0.0",
                "build_date": "2024-01-15",
                "commit_hash": "abc123"
            }
            mock_health.return_value = mock_health_service

            # When: 기존 /version 엔드포인트 호출
            response_old = client.get("/version")
            # When: 새로운 /api/monitoring/version 엔드포인트 호출 (통합 후)
            response_new = client.get("/api/monitoring/version")

            # Then: 둘 다 성공
            assert response_old.status_code == 200
            assert response_new.status_code == 200
            
            # 응답 구조가 일치하는지 확인
            old_data = response_old.json()
            new_data = response_new.json()
            
            assert old_data["version"] == new_data["version"]
            assert old_data["build_date"] == new_data["build_date"]
            assert old_data["commit_hash"] == new_data["commit_hash"]


class TestEnvironmentFiltering:
    """환경별 필터링 로직 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    def test_environment_parameter_validation(self, client):
        """환경 파라미터 검증 테스트"""
        # When: 유효하지 않은 환경 파라미터 사용
        response = client.get("/api/monitoring/hetrix/monitors?environment=invalid")
        
        # Then: 400 오류 응답
        assert response.status_code == 400
        data = response.json()
        assert "유효하지 않은 환경" in data["detail"]

    def test_environment_default_behavior(self, client):
        """환경 파라미터 기본값 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_hetrix:
            mock_hetrix_service = AsyncMock()
            mock_hetrix_service.__aenter__.return_value = mock_hetrix_service
            mock_hetrix_service.__aexit__.return_value = None
            mock_hetrix_service.get_monitors_async.return_value = []
            mock_hetrix.return_value = mock_hetrix_service

            # When: 환경 파라미터 없이 API 호출
            response = client.get("/api/monitoring/hetrix/monitors")

            # Then: 성공 응답 (기본값 사용)
            assert response.status_code == 200
            data = response.json()
            assert data["environment"] == "all"

    def test_environment_filtering_consistency(self, client):
        """환경별 필터링 일관성 테스트"""
        with patch('nadle_backend.routers.monitoring.get_hetrix_service') as mock_hetrix:
            mock_hetrix_service = AsyncMock()
            mock_hetrix_service.__aenter__.return_value = mock_hetrix_service
            mock_hetrix_service.__aexit__.return_value = None
            mock_hetrix_service.client.get_monitors_by_environment.return_value = []
            mock_hetrix.return_value = mock_hetrix_service

            # When: 동일한 환경으로 여러 API 호출
            response1 = client.get("/api/monitoring/hetrix/monitors?environment=staging")
            response2 = client.get("/api/monitoring/dashboard/staging")

            # Then: 모두 동일한 환경 응답
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            data1 = response1.json()
            data2 = response2.json()
            
            assert data1["environment"] == "staging"
            assert data2["environment"] == "staging"