"""
모니터링 API 실제 시스템 통합 테스트

실제 FastAPI 서버 + Redis + HTTP 요청으로 완전한 E2E 테스트
subprocess를 사용하여 실제 서버 프로세스를 분리하여 이벤트 루프 충돌 해결
"""
import pytest
import json
import time
import asyncio
import subprocess
import requests
import redis.asyncio as redis
import signal
import os
from pathlib import Path


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.e2e
class TestMonitoringRealSystemIntegration:
    """모니터링 API 실제 시스템 통합 테스트"""
    
    @pytest.fixture(scope="function")
    async def redis_client(self):
        """실제 Redis 클라이언트 (테스트용)"""
        try:
            # 테스트용 Redis 인스턴스에 연결
            client = redis.from_url("redis://localhost:6379/15")  # DB 15는 실제 시스템 테스트 전용
            await client.ping()
            
            # 테스트 시작 전 DB 정리
            await client.flushdb()
            
            yield client
            
            # 테스트 완료 후 정리
            await client.flushdb()
            await client.aclose()
            
        except Exception as e:
            pytest.skip(f"Redis server not available for real system testing: {e}")

    @pytest.fixture(scope="function")
    def backend_server(self):
        """실제 백엔드 서버 프로세스"""
        # 백엔드 디렉토리 경로
        backend_dir = Path(__file__).parent.parent.parent
        
        # 환경변수 설정
        env = os.environ.copy()
        env.update({
            'ENVIRONMENT': 'test',
            'REDIS_URL': 'redis://localhost:6379/15',
            'DATABASE_URL': 'mongodb://localhost:27017/test_db',
            'PORT': '8001',  # 테스트용 포트
        })
        
        # 서버 시작 명령
        cmd = [
            'python', '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8001',
            '--log-level', 'error'  # 로그 최소화
        ]
        
        # 서버 프로세스 시작
        try:
            process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # 프로세스 그룹 생성
            )
            
            # 서버 준비까지 대기
            server_url = "http://localhost:8001"
            max_retries = 30
            for i in range(max_retries):
                try:
                    response = requests.get(f"{server_url}/health", timeout=1)
                    if response.status_code == 200:
                        break
                except requests.RequestException:
                    pass
                time.sleep(1)
                if i == max_retries - 1:
                    process.terminate()
                    pytest.skip("Failed to start backend server for testing")
            
            yield server_url
            
        except Exception as e:
            pytest.skip(f"Failed to start backend server: {e}")
        
        finally:
            # 서버 프로세스 종료
            try:
                # 프로세스 그룹 전체 종료
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_real_system_health_check(self, backend_server):
        """실제 시스템 헬스체크 테스트"""
        # When: 헬스체크 엔드포인트 호출
        response = requests.get(f"{backend_server}/health")
        
        # Then: 정상 응답
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_real_system_api_metrics_collection(self, backend_server):
        """실제 시스템 API 메트릭 수집 테스트"""
        # Given: 실제 API 요청을 수행하여 메트릭 생성
        test_endpoints = [
            "/",
            "/health",
            "/api/monitoring/metrics",
        ]
        
        # 여러 요청 수행
        for endpoint in test_endpoints:
            for _ in range(3):  # 각 엔드포인트에 3번씩 요청
                response = requests.get(f"{backend_server}{endpoint}")
                assert response.status_code == 200
        
        # 약간의 대기 시간 (비동기 처리 완료)
        time.sleep(1)
        
        # When: 모니터링 API로 메트릭 조회
        response = requests.get(f"{backend_server}/api/monitoring/metrics")
        
        # Then: 실제 메트릭 데이터 반환
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoints" in data
        assert "status_codes" in data
        assert "timestamp" in data
        
        # 실제 요청이 메트릭에 기록되었는지 확인
        endpoints = data["endpoints"]
        status_codes = data["status_codes"]
        
        # 최소한의 요청이 기록되었는지 확인
        total_requests = sum(endpoints.values()) if endpoints else 0
        assert total_requests >= 9  # 3개 엔드포인트 * 3번 = 최소 9개
        
        # 상태코드 확인
        assert "200" in status_codes
        assert status_codes["200"] >= 9

    def test_real_system_health_status_api(self, backend_server):
        """실제 시스템 헬스 상태 API 테스트"""
        # Given: 일부 요청 수행
        for _ in range(5):
            requests.get(f"{backend_server}/")
        
        time.sleep(0.5)
        
        # When: 헬스 상태 API 호출
        response = requests.get(f"{backend_server}/api/monitoring/health")
        
        # Then: 헬스 상태 정보 반환
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "total_requests" in data
        assert "error_rate" in data
        assert "availability" in data
        assert "timestamp" in data
        
        # 실제 요청이 반영되었는지 확인
        assert data["total_requests"] >= 5
        assert data["status"] in ["healthy", "warning", "critical"]

    def test_real_system_popular_endpoints_api(self, backend_server):
        """실제 시스템 인기 엔드포인트 API 테스트"""
        # Given: 다양한 엔드포인트에 요청
        endpoints_to_test = [
            ("/", 10),  # 10번 요청
            ("/health", 7),  # 7번 요청
            ("/api/monitoring/metrics", 5),  # 5번 요청
        ]
        
        for endpoint, count in endpoints_to_test:
            for _ in range(count):
                response = requests.get(f"{backend_server}{endpoint}")
                assert response.status_code == 200
        
        time.sleep(1)
        
        # When: 인기 엔드포인트 조회
        response = requests.get(f"{backend_server}/api/monitoring/popular-endpoints?limit=10")
        
        # Then: 인기 엔드포인트 목록 반환
        assert response.status_code == 200
        data = response.json()
        
        assert "popular_endpoints" in data
        popular_endpoints = data["popular_endpoints"]
        
        # 데이터가 있는지 확인
        assert len(popular_endpoints) > 0
        
        # 첫 번째 엔드포인트가 가장 많은 요청을 받았는지 확인 (정렬 확인)
        if len(popular_endpoints) >= 2:
            assert popular_endpoints[0]["requests"] >= popular_endpoints[1]["requests"]

    def test_real_system_dashboard_api_comprehensive(self, backend_server):
        """실제 시스템 대시보드 API 종합 테스트"""
        # Given: 다양한 활동 시뮬레이션
        for _ in range(15):
            requests.get(f"{backend_server}/")
        for _ in range(8):
            requests.get(f"{backend_server}/health")
        for _ in range(3):
            requests.get(f"{backend_server}/api/monitoring/metrics")
        
        time.sleep(1)
        
        # When: 대시보드 데이터 조회
        response = requests.get(f"{backend_server}/api/monitoring/dashboard")
        
        # Then: 종합적인 대시보드 데이터 반환
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
        
        # 실제 데이터 존재 확인
        if dashboard_data["metrics"]:
            assert "endpoints" in dashboard_data["metrics"]
            assert "status_codes" in dashboard_data["metrics"]
            
            # 실제 요청 수가 반영되었는지 확인
            total_requests = sum(dashboard_data["metrics"]["endpoints"].values())
            assert total_requests >= 26  # 15 + 8 + 3 = 최소 26개

    @pytest.mark.asyncio
    async def test_real_system_redis_data_consistency(self, backend_server, redis_client):
        """실제 시스템 Redis 데이터 일관성 테스트"""
        # Given: API 요청 수행
        for _ in range(10):
            response = requests.get(f"{backend_server}/")
            assert response.status_code == 200
        
        time.sleep(1)
        
        # When: Redis에서 직접 데이터 조회
        endpoint_stats = await redis_client.hgetall("api:metrics:endpoints")
        status_stats = await redis_client.hgetall("api:metrics:status_codes")
        
        # API를 통한 데이터 조회
        response = requests.get(f"{backend_server}/api/monitoring/metrics")
        assert response.status_code == 200
        api_metrics = response.json()
        
        # Then: Redis 데이터와 API 응답 일관성 확인
        redis_endpoints = {k.decode(): int(v.decode()) for k, v in endpoint_stats.items()}
        
        # 기본적인 일관성 확인
        for endpoint, count in redis_endpoints.items():
            if endpoint in api_metrics["endpoints"]:
                # Redis와 API 응답이 일치하거나 API가 더 최신이어야 함
                assert api_metrics["endpoints"][endpoint] >= count * 0.9  # 10% 오차 허용 (비동기 처리)

    def test_real_system_error_handling(self, backend_server):
        """실제 시스템 에러 처리 테스트"""
        # When: 존재하지 않는 엔드포인트 요청
        response = requests.get(f"{backend_server}/nonexistent")
        
        # Then: 404 에러
        assert response.status_code == 404
        
        # When: 잘못된 파라미터로 모니터링 API 호출
        response = requests.get(f"{backend_server}/api/monitoring/slow-requests?limit=999")
        
        # Then: 검증 에러
        assert response.status_code == 422  # Validation Error

    def test_real_system_performance_under_load(self, backend_server):
        """실제 시스템 부하 테스트"""
        import concurrent.futures
        import threading
        
        # Given: 동시에 여러 요청 수행
        def make_request():
            try:
                response = requests.get(f"{backend_server}/", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # 동시에 20개 요청
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 대부분의 요청이 성공해야 함
        success_count = sum(results)
        assert success_count >= 18  # 90% 성공률
        
        time.sleep(2)  # 메트릭 처리 대기
        
        # When: 메트릭 조회
        response = requests.get(f"{backend_server}/api/monitoring/metrics")
        
        # Then: 모든 요청이 메트릭에 기록됨
        assert response.status_code == 200
        data = response.json()
        
        # GET:/ 요청이 대부분 기록되었는지 확인
        root_requests = data["endpoints"].get("GET:/", 0)
        assert root_requests >= success_count * 0.9  # 10% 오차 허용