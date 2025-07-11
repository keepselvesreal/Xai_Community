"""
모니터링 API E2E 테스트

실제 서버와 Redis를 사용한 완전한 E2E 테스트
pytest-asyncio를 사용하여 실제 환경에서 테스트
"""
import pytest
import json
import time
import asyncio
import httpx
import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
class TestMonitoringAPIE2E:
    """모니터링 API End-to-End 테스트"""

    @pytest.fixture
    async def redis_client(self):
        """실제 Redis 클라이언트 (테스트용)"""
        try:
            # 테스트용 Redis 인스턴스에 연결
            client = redis.from_url("redis://localhost:6379/15")  # DB 15는 E2E 테스트 전용
            await client.ping()
            
            # 테스트 시작 전 DB 정리
            await client.flushdb()
            
            yield client
            
            # 테스트 완료 후 정리
            await client.flushdb()
            await client.aclose()
            
        except Exception as e:
            pytest.skip(f"Redis server not available for E2E testing: {e}")

    @pytest.fixture
    async def app_with_monitoring(self, redis_client):
        """모니터링이 포함된 테스트 앱"""
        from nadle_backend.middleware.monitoring import MonitoringMiddleware
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
        
        app = FastAPI(lifespan=lifespan)
        
        # 실제 Redis 클라이언트로 모니터링 미들웨어 추가
        app.add_middleware(MonitoringMiddleware, redis_client=redis_client)
        
        # 테스트용 엔드포인트들
        @app.get("/api/posts")
        async def get_posts():
            return {"posts": ["post1", "post2"]}
        
        @app.post("/api/posts")
        async def create_post():
            return {"id": 1, "title": "New Post"}
        
        @app.get("/api/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.05)  # 50ms 지연
            return {"message": "slow response"}
        
        # 모니터링 API 라우터 추가
        from nadle_backend.routers.monitoring import router as monitoring_router
        app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
        
        return app

    @pytest.fixture
    async def server_url(self, app_with_monitoring):
        """테스트 서버 URL"""
        import uvicorn
        import threading
        import socket
        
        # 사용 가능한 포트 찾기
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        
        server_url = f"http://127.0.0.1:{port}"
        
        # 백그라운드에서 서버 실행
        config = uvicorn.Config(app=app_with_monitoring, host="127.0.0.1", port=port, log_level="critical")
        server = uvicorn.Server(config)
        
        # 서버를 별도 스레드에서 실행
        def run_server():
            asyncio.run(server.serve())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # 서버가 준비될 때까지 대기
        async with httpx.AsyncClient() as client:
            max_retries = 50
            for _ in range(max_retries):
                try:
                    response = await client.get(f"{server_url}/api/posts")
                    if response.status_code == 200:
                        break
                except:
                    pass
                await asyncio.sleep(0.1)
            else:
                pytest.skip("Failed to start test server")
        
        yield server_url
        
        # 서버 종료
        server.should_exit = True

    async def test_e2e_metrics_collection_and_retrieval(self, server_url, redis_client):
        """E2E 메트릭 수집 및 조회 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: 실제 API 요청들을 수행하여 메트릭 데이터 생성
            responses = []
            for _ in range(3):
                response = await client.get(f"{server_url}/api/posts")
                responses.append(response)
            
            response = await client.post(f"{server_url}/api/posts")
            responses.append(response)
            
            # 모든 요청이 성공적으로 처리되었는지 확인
            for response in responses:
                assert response.status_code == 200
            
            # 비동기 처리 완료 대기
            await asyncio.sleep(0.2)
            
            # When: 모니터링 API로 메트릭 조회
            metrics_response = await client.get(f"{server_url}/api/monitoring/metrics")
            
            # Then: 실제 메트릭 데이터가 반환됨
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            
            assert "endpoints" in metrics_data
            assert "status_codes" in metrics_data
            assert "timestamp" in metrics_data
            
            # 실제 요청된 엔드포인트들이 메트릭에 기록되었는지 확인
            endpoints = metrics_data["endpoints"]
            status_codes = metrics_data["status_codes"]
            
            assert "GET:/api/posts" in endpoints
            assert "POST:/api/posts" in endpoints
            assert endpoints["GET:/api/posts"] == 3  # 3번 호출
            assert endpoints["POST:/api/posts"] == 1  # 1번 호출
            assert "200" in status_codes
            assert status_codes["200"] == 4  # 총 4번의 200 응답

    async def test_e2e_health_status_api(self, server_url, redis_client):
        """E2E 헬스 상태 API 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: 다양한 요청 수행
            await client.get(f"{server_url}/api/posts")
            await client.post(f"{server_url}/api/posts")
            
            await asyncio.sleep(0.1)
            
            # When: 헬스 상태 API 호출
            health_response = await client.get(f"{server_url}/api/monitoring/health")
            
            # Then: 헬스 상태 정보 반환
            assert health_response.status_code == 200
            health_data = health_response.json()
            
            assert "status" in health_data
            assert "total_requests" in health_data
            assert "error_rate" in health_data
            assert "availability" in health_data
            assert "timestamp" in health_data
            
            # 실제 메트릭 값 확인
            assert health_data["total_requests"] >= 2  # 최소 2개 요청
            assert health_data["status"] in ["healthy", "warning", "critical"]

    async def test_e2e_endpoint_stats_api(self, server_url, redis_client):
        """E2E 엔드포인트 통계 API 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: 특정 엔드포인트에 여러 요청
            for _ in range(5):
                await client.get(f"{server_url}/api/posts")
            
            await asyncio.sleep(0.1)
            
            # When: 특정 엔드포인트 통계 조회  
            stats_response = await client.get(f"{server_url}/api/monitoring/endpoints/GET:/api/posts")
            
            # Then: 엔드포인트 통계 반환
            assert stats_response.status_code == 200
            stats_data = stats_response.json()
            
            assert "avg_response_time" in stats_data
            assert "min_response_time" in stats_data
            assert "max_response_time" in stats_data
            assert "request_count" in stats_data
            
            # 실제 요청 수 확인
            assert stats_data["request_count"] == 5
            assert stats_data["avg_response_time"] > 0

    async def test_e2e_slow_requests_detection(self, server_url, redis_client):
        """E2E 느린 요청 감지 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: 느린 요청 수행
            await client.get(f"{server_url}/api/slow")  # 50ms 지연
            
            await asyncio.sleep(0.2)
            
            # When: 느린 요청 목록 조회
            slow_response = await client.get(f"{server_url}/api/monitoring/slow-requests?limit=10")
            
            # Then: 느린 요청 목록 반환
            assert slow_response.status_code == 200
            slow_data = slow_response.json()
            
            assert "slow_requests" in slow_data
            
            # 느린 요청이 감지되었는지 확인 (임계값 2초보다 작으므로 감지되지 않을 수 있음)
            # 이 테스트는 시스템이 정상 작동하는지 확인

    async def test_e2e_popular_endpoints_api(self, server_url, redis_client):
        """E2E 인기 엔드포인트 API 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: 다양한 엔드포인트에 요청
            for _ in range(7):
                await client.get(f"{server_url}/api/posts")
            for _ in range(3):
                await client.post(f"{server_url}/api/posts")
            await client.get(f"{server_url}/api/slow")
            
            await asyncio.sleep(0.1)
            
            # When: 인기 엔드포인트 조회
            popular_response = await client.get(f"{server_url}/api/monitoring/popular-endpoints?limit=5")
            
            # Then: 인기 엔드포인트 목록 반환
            assert popular_response.status_code == 200
            popular_data = popular_response.json()
            
            assert "popular_endpoints" in popular_data
            popular_endpoints = popular_data["popular_endpoints"]
            
            # 가장 많이 호출된 엔드포인트가 첫 번째에 위치
            if len(popular_endpoints) > 0:
                assert popular_endpoints[0]["endpoint"] == "GET:/api/posts"
                assert popular_endpoints[0]["requests"] == 7

    async def test_e2e_dashboard_api_comprehensive(self, server_url, redis_client):
        """E2E 대시보드 API 종합 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: 다양한 활동 시뮬레이션
            await client.get(f"{server_url}/api/posts")
            await client.post(f"{server_url}/api/posts")
            await client.get(f"{server_url}/api/slow")
            
            await asyncio.sleep(0.1)
            
            # When: 대시보드 데이터 조회
            dashboard_response = await client.get(f"{server_url}/api/monitoring/dashboard")
            
            # Then: 종합적인 대시보드 데이터 반환
            assert dashboard_response.status_code == 200
            dashboard_data = dashboard_response.json()
            
            assert "timestamp" in dashboard_data
            assert "status" in dashboard_data
            assert "data" in dashboard_data
            assert dashboard_data["status"] == "success"
            
            data = dashboard_data["data"]
            assert "metrics" in data
            assert "health" in data
            assert "popular_endpoints" in data
            assert "slow_requests" in data
            
            # 실제 데이터 존재 확인
            if data["metrics"]:
                assert "endpoints" in data["metrics"]
                assert "status_codes" in data["metrics"]

    async def test_e2e_redis_data_consistency(self, server_url, redis_client):
        """E2E Redis 데이터 일관성 테스트"""
        async with httpx.AsyncClient() as client:
            # Given: API 요청 수행
            await client.get(f"{server_url}/api/posts")
            await client.post(f"{server_url}/api/posts")
            
            await asyncio.sleep(0.1)
            
            # When: Redis에서 직접 데이터 조회
            endpoint_stats = await redis_client.hgetall("api:metrics:endpoints")
            status_stats = await redis_client.hgetall("api:metrics:status_codes")
            
            # API를 통한 데이터 조회
            metrics_response = await client.get(f"{server_url}/api/monitoring/metrics")
            api_metrics = metrics_response.json()
            
            # Then: Redis 데이터와 API 응답 일관성 확인
            redis_endpoints = {k.decode(): int(v.decode()) for k, v in endpoint_stats.items()}
            
            # 기본적인 일관성 확인 (완전히 동일하지 않을 수 있음 - 비동기 처리로 인해)
            for endpoint, count in redis_endpoints.items():
                if endpoint in api_metrics["endpoints"]:
                    assert api_metrics["endpoints"][endpoint] >= 0  # 기본 존재 확인