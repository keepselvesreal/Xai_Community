"""
모니터링 API 실제 시스템 통합 테스트

실제 Redis + FastAPI + HTTP 요청으로 완전한 통합 테스트
"""
import pytest
import json
import time
import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
import redis.asyncio as redis


@pytest.mark.integration
@pytest.mark.redis
class TestMonitoringAPIIntegration:
    """모니터링 API 실제 시스템 통합 테스트"""

    @pytest.fixture
    async def redis_client(self):
        """실제 Redis 클라이언트 (테스트용)"""
        try:
            # 테스트용 Redis 인스턴스에 연결
            client = redis.from_url("redis://localhost:6379/14")  # DB 14는 API 테스트 전용
            await client.ping()
            
            # 테스트 시작 전 DB 정리
            await client.flushdb()
            
            yield client
            
            # 테스트 완료 후 정리
            await client.flushdb()
            await client.aclose()
            
        except Exception as e:
            pytest.skip(f"Redis server not available for API integration testing: {e}")

    @pytest.fixture
    def app_with_monitoring_api(self, redis_client):
        """모니터링 API가 포함된 테스트 앱"""
        from nadle_backend.middleware.monitoring import MonitoringMiddleware
        
        app = FastAPI()
        
        # 실제 Redis 클라이언트로 모니터링 미들웨어 추가
        app.add_middleware(MonitoringMiddleware, redis_client=redis_client)
        
        # 테스트용 일반 엔드포인트들
        @app.get("/api/posts")
        async def get_posts():
            return {"posts": ["post1", "post2"]}
        
        @app.post("/api/posts")
        async def create_post():
            return {"id": 1, "title": "New Post"}
        
        @app.get("/api/slow")
        async def slow_endpoint():
            import asyncio
            await asyncio.sleep(0.1)  # 100ms 지연
            return {"message": "slow response"}
        
        @app.get("/api/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        # 모니터링 API 라우터 추가
        from nadle_backend.routers.monitoring import router as monitoring_router
        app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
        
        return app

    @pytest.fixture
    def client(self, app_with_monitoring_api):
        """테스트 클라이언트"""
        return TestClient(app_with_monitoring_api)

    @pytest.mark.asyncio
    async def test_real_api_metrics_collection_and_retrieval(self, client, redis_client):
        """실제 API 요청으로 메트릭 수집 후 조회 테스트"""
        # Given: 실제 API 요청들을 수행하여 메트릭 데이터 생성
        
        # 다양한 요청 수행
        responses = [
            client.get("/api/posts"),
            client.get("/api/posts"),
            client.post("/api/posts"),
            client.get("/api/slow"),
        ]
        
        # 모든 요청이 성공적으로 처리되었는지 확인
        assert responses[0].status_code == 200
        assert responses[1].status_code == 200
        assert responses[2].status_code == 200
        assert responses[3].status_code == 200
        
        # 약간의 대기 시간 (비동기 처리 완료 대기)
        import asyncio
        await asyncio.sleep(0.1)
        
        # When: 모니터링 API로 메트릭 조회
        metrics_response = client.get("/api/monitoring/metrics")
        
        # Then: 실제 메트릭 데이터가 반환됨
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        
        assert "endpoints" in metrics_data
        assert "status_codes" in metrics_data
        assert "timestamp" in metrics_data
        
        # 실제 요청된 엔드포인트들이 메트릭에 기록되었는지 확인
        endpoints = metrics_data["endpoints"]
        assert "GET:/api/posts" in endpoints
        assert "POST:/api/posts" in endpoints
        assert "GET:/api/slow" in endpoints
        
        # 요청 횟수 확인
        assert endpoints["GET:/api/posts"] == 2  # 2번 호출
        assert endpoints["POST:/api/posts"] == 1  # 1번 호출
        assert endpoints["GET:/api/slow"] == 1    # 1번 호출

    @pytest.mark.asyncio
    async def test_real_health_status_api(self, client, redis_client):
        """실제 헬스 상태 API 테스트"""
        # Given: 다양한 상태코드로 요청 수행
        client.get("/api/posts")  # 200
        client.post("/api/posts")  # 200
        
        # 에러 요청 (try-except로 처리)
        try:
            client.get("/api/error")
        except:
            pass  # 에러는 예상됨
        
        await asyncio.sleep(0.1)  # 비동기 처리 완료 대기
        
        # When: 헬스 상태 API 호출
        health_response = client.get("/api/monitoring/health")
        
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

    @pytest.mark.asyncio
    async def test_real_endpoint_stats_api(self, client, redis_client):
        """실제 엔드포인트 통계 API 테스트"""
        # Given: 특정 엔드포인트에 여러 요청
        for _ in range(3):
            client.get("/api/posts")
        
        await asyncio.sleep(0.1)  # 비동기 처리 완료 대기
        
        # When: 특정 엔드포인트 통계 조회
        stats_response = client.get("/api/monitoring/endpoints/GET:/api/posts")
        
        # Then: 엔드포인트 통계 반환
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        
        assert "avg_response_time" in stats_data
        assert "min_response_time" in stats_data
        assert "max_response_time" in stats_data
        assert "request_count" in stats_data
        
        # 실제 요청 수 확인
        assert stats_data["request_count"] == 3

    @pytest.mark.asyncio
    async def test_real_slow_requests_api(self, client, redis_client):
        """실제 느린 요청 API 테스트"""
        # Given: 느린 요청 수행
        client.get("/api/slow")  # 100ms 지연
        
        await asyncio.sleep(0.2)  # 비동기 처리 완료 대기
        
        # When: 느린 요청 목록 조회
        slow_response = client.get("/api/monitoring/slow-requests?limit=10")
        
        # Then: 느린 요청 목록 반환
        assert slow_response.status_code == 200
        slow_data = slow_response.json()
        
        assert "slow_requests" in slow_data
        slow_requests = slow_data["slow_requests"]
        
        # 느린 요청이 감지되었는지 확인 (임계값에 따라)
        if len(slow_requests) > 0:
            assert "endpoint" in slow_requests[0]
            assert "response_time" in slow_requests[0]
            assert slow_requests[0]["endpoint"] == "GET:/api/slow"

    @pytest.mark.asyncio
    async def test_real_time_series_api(self, client, redis_client):
        """실제 시간별 데이터 API 테스트"""
        # Given: Redis에 시간별 데이터 직접 삽입
        current_time = time.time()
        timing_data = [
            {"response_time": 0.1, "timestamp": current_time - 300, "status_code": 200},
            {"response_time": 0.15, "timestamp": current_time - 200, "status_code": 200},
            {"response_time": 0.08, "timestamp": current_time - 100, "status_code": 200}
        ]
        
        for data in timing_data:
            await redis_client.lpush("api:timing:GET:/api/posts", json.dumps(data))
        
        # When: 시간별 데이터 조회
        timeseries_response = client.get("/api/monitoring/timeseries/GET:/api/posts?minutes=60")
        
        # Then: 시간별 데이터 반환
        assert timeseries_response.status_code == 200
        timeseries_data = timeseries_response.json()
        
        assert "timestamps" in timeseries_data
        assert "response_times" in timeseries_data
        assert len(timeseries_data["timestamps"]) == 3
        assert len(timeseries_data["response_times"]) == 3

    @pytest.mark.asyncio
    async def test_real_popular_endpoints_api(self, client, redis_client):
        """실제 인기 엔드포인트 API 테스트"""
        # Given: 다양한 엔드포인트에 요청
        for _ in range(5):
            client.get("/api/posts")
        for _ in range(2):
            client.post("/api/posts")
        client.get("/api/slow")
        
        await asyncio.sleep(0.1)  # 비동기 처리 완료 대기
        
        # When: 인기 엔드포인트 조회
        popular_response = client.get("/api/monitoring/popular-endpoints?limit=5")
        
        # Then: 인기 엔드포인트 목록 반환
        assert popular_response.status_code == 200
        popular_data = popular_response.json()
        
        assert "popular_endpoints" in popular_data
        popular_endpoints = popular_data["popular_endpoints"]
        
        # 가장 많이 호출된 엔드포인트가 첫 번째에 위치
        if len(popular_endpoints) > 0:
            assert popular_endpoints[0]["endpoint"] == "GET:/api/posts"
            assert popular_endpoints[0]["requests"] == 5

    @pytest.mark.asyncio
    async def test_real_api_error_handling(self, client, redis_client):
        """실제 API 에러 처리 테스트"""
        # When: 존재하지 않는 엔드포인트 통계 조회
        response = client.get("/api/monitoring/endpoints/INVALID:/nonexistent")
        
        # Then: 적절한 에러 응답 또는 빈 데이터 반환
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # 데이터가 없는 경우 기본값 반환
            assert data["request_count"] == 0

    @pytest.mark.asyncio
    async def test_real_api_performance_under_load(self, client, redis_client):
        """실제 API 부하 테스트"""
        import asyncio
        
        # Given: 동시에 여러 요청 수행
        async def make_request():
            return client.get("/api/posts")
        
        # 동시에 10개 요청
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 모든 요청이 성공적으로 처리되었는지 확인
        successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        assert len(successful_responses) == 10
        
        await asyncio.sleep(0.2)  # 비동기 처리 완료 대기
        
        # When: 메트릭 조회
        metrics_response = client.get("/api/monitoring/metrics")
        
        # Then: 모든 요청이 메트릭에 기록됨
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        
        # GET:/api/posts 요청이 10회 기록되었는지 확인
        assert metrics_data["endpoints"]["GET:/api/posts"] >= 10

    @pytest.mark.asyncio
    async def test_real_redis_data_consistency(self, client, redis_client):
        """실제 Redis 데이터 일관성 테스트"""
        # Given: API 요청 수행
        client.get("/api/posts")
        client.post("/api/posts")
        
        await asyncio.sleep(0.1)  # 비동기 처리 완료 대기
        
        # When: Redis에서 직접 데이터 조회
        endpoint_stats = await redis_client.hgetall("api:metrics:endpoints")
        status_stats = await redis_client.hgetall("api:metrics:status_codes")
        
        # Then: Redis 데이터와 API 응답 일관성 확인
        metrics_response = client.get("/api/monitoring/metrics")
        api_metrics = metrics_response.json()
        
        # Redis 원본 데이터와 API 응답 비교
        redis_endpoints = {k.decode(): int(v.decode()) for k, v in endpoint_stats.items()}
        assert api_metrics["endpoints"] == redis_endpoints
        
        # 상태코드 데이터 비교 (prefix 처리 고려)
        redis_status = {}
        for k, v in status_stats.items():
            key = k.decode()
            if key.startswith("status:"):
                status_code = key[len("status:"):]
                redis_status[status_code] = int(v.decode())
        
        assert api_metrics["status_codes"] == redis_status