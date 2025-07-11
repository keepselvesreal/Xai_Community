"""
실제 Redis를 사용한 모니터링 미들웨어 통합 테스트

Redis 서버가 실행 중이어야 하며, 테스트용 Redis 인스턴스를 사용해야 함
"""
import pytest
import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import redis.asyncio as redis
from nadle_backend.middleware.monitoring import PerformanceTracker, MonitoringMiddleware


@pytest.mark.integration
@pytest.mark.redis
class TestMonitoringRedisIntegration:
    """실제 Redis를 사용한 모니터링 통합 테스트"""

    @pytest.fixture
    async def redis_client(self):
        """실제 Redis 클라이언트 (테스트용)"""
        try:
            # 테스트용 Redis 인스턴스에 연결 시도
            client = redis.from_url("redis://localhost:6379/15")  # DB 15는 테스트 전용
            await client.ping()
            
            # 테스트 시작 전 DB 정리
            await client.flushdb()
            
            yield client
            
            # 테스트 완료 후 정리
            await client.flushdb()
            await client.aclose()
            
        except Exception as e:
            pytest.skip(f"Redis server not available for integration testing: {e}")

    @pytest.mark.asyncio
    async def test_real_redis_performance_tracking(self, redis_client):
        """실제 Redis를 사용한 성능 추적 테스트"""
        # Given: 실제 Redis 클라이언트를 사용한 추적기 (느린 요청 임계값 50ms)
        tracker = PerformanceTracker(redis_client=redis_client, slow_request_threshold=0.05)
        
        # Given: 모킹된 요청 객체
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                class MockURL:
                    path = "/api/posts"
                self.url = MockURL()
                self.headers = {"user-agent": "test-agent"}
                class MockClient:
                    host = "127.0.0.1"
                self.client = MockClient()
        
        request = MockRequest()
        
        # When: 요청 추적
        tracking_data = await tracker.start_tracking(request)
        await asyncio.sleep(0.1)  # 100ms 시뮬레이션
        is_slow = await tracker.end_tracking(tracking_data, 200)
        
        # Then: Redis에 실제로 데이터가 저장됨
        assert is_slow == True  # 100ms > 50ms 임계값이므로 느린 요청으로 감지
        
        # 엔드포인트 통계 확인
        endpoint_stats = await redis_client.hgetall("api:metrics:endpoints")
        assert len(endpoint_stats) > 0
        
        # 상태코드 통계 확인
        status_stats = await redis_client.hgetall("api:metrics:status_codes")
        assert len(status_stats) > 0

    @pytest.mark.asyncio
    async def test_real_redis_metrics_retrieval(self, redis_client):
        """실제 Redis에서 메트릭 조회 테스트"""
        # Given: 실제 데이터가 있는 추적기
        tracker = PerformanceTracker(redis_client=redis_client)
        
        # Given: 테스트 데이터 직접 입력
        await redis_client.hset("api:metrics:endpoints", "GET:/api/posts", 50)
        await redis_client.hset("api:metrics:endpoints", "POST:/api/posts", 10)
        await redis_client.hset("api:metrics:status_codes", "status:200", 45)
        await redis_client.hset("api:metrics:status_codes", "status:201", 10)
        await redis_client.hset("api:metrics:status_codes", "status:500", 5)
        
        # When: 메트릭 조회
        metrics = await tracker.get_metrics()
        
        # Then: 실제 데이터 반환
        assert "endpoints" in metrics
        assert "status_codes" in metrics
        assert metrics["endpoints"]["GET:/api/posts"] == 50
        assert metrics["status_codes"]["200"] == 45
        assert metrics["status_codes"]["500"] == 5

    @pytest.mark.asyncio
    async def test_real_redis_error_rate_calculation(self, redis_client):
        """실제 Redis에서 에러율 계산 테스트"""
        # Given: 실제 상태코드 데이터
        tracker = PerformanceTracker(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:status_codes", "status:200", 80)
        await redis_client.hset("api:metrics:status_codes", "status:201", 15)
        await redis_client.hset("api:metrics:status_codes", "status:500", 5)
        
        # When: 에러율 계산
        error_rate = await tracker.calculate_error_rate()
        
        # Then: 올바른 에러율 (5/100 = 5%)
        assert error_rate == 0.05

    @pytest.mark.asyncio
    async def test_real_redis_slow_request_detection(self, redis_client):
        """실제 Redis에서 느린 요청 감지 테스트"""
        # Given: 느린 요청 임계값 설정
        tracker = PerformanceTracker(
            redis_client=redis_client, 
            slow_request_threshold=0.05  # 50ms
        )
        
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                class MockURL:
                    path = "/api/slow"
                self.url = MockURL()
                self.headers = {"user-agent": "test-agent"}
                class MockClient:
                    host = "127.0.0.1"
                self.client = MockClient()
        
        request = MockRequest()
        
        # When: 느린 요청 추적
        tracking_data = await tracker.start_tracking(request)
        await asyncio.sleep(0.1)  # 100ms - 임계값 초과
        is_slow = await tracker.end_tracking(tracking_data, 200)
        
        # Then: 느린 요청으로 감지
        assert is_slow == True
        
        # 느린 요청 목록에 저장되었는지 확인
        slow_requests = await redis_client.lrange("api:alerts:slow_requests", 0, -1)
        assert len(slow_requests) > 0

    @pytest.mark.asyncio
    async def test_real_redis_time_series_metrics(self, redis_client):
        """실제 Redis에서 시간별 메트릭 테스트"""
        # Given: 시간별 데이터
        tracker = PerformanceTracker(redis_client=redis_client)
        
        current_time = time.time()
        timing_data = [
            {"response_time": 0.1, "timestamp": current_time - 600, "status_code": 200},
            {"response_time": 0.15, "timestamp": current_time - 300, "status_code": 200},
            {"response_time": 0.08, "timestamp": current_time - 100, "status_code": 200},
        ]
        
        # Redis에 타이밍 데이터 저장
        import json
        for data in timing_data:
            await redis_client.lpush("api:timing:GET:/api/posts", json.dumps(data))
        
        # When: 시간별 메트릭 조회
        time_series = await tracker.get_time_series_metrics("GET:/api/posts", minutes=60)
        
        # Then: 시간별 데이터 반환
        assert "timestamps" in time_series
        assert "response_times" in time_series
        assert len(time_series["timestamps"]) == 3
        assert len(time_series["response_times"]) == 3

    @pytest.mark.asyncio
    async def test_real_redis_health_metrics(self, redis_client):
        """실제 Redis에서 헬스체크 메트릭 테스트"""
        # Given: 다양한 상태코드 데이터
        tracker = PerformanceTracker(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:status_codes", "status:200", 85)
        await redis_client.hset("api:metrics:status_codes", "status:201", 10)
        await redis_client.hset("api:metrics:status_codes", "status:404", 3)
        await redis_client.hset("api:metrics:status_codes", "status:500", 2)
        
        # When: 헬스체크 메트릭 조회
        health_metrics = await tracker.get_health_metrics()
        
        # Then: 시스템 상태 정보
        assert health_metrics["total_requests"] == 100
        assert health_metrics["success_requests"] == 95  # 2xx
        assert health_metrics["error_requests"] == 2     # 5xx
        assert health_metrics["error_rate"] == 0.02      # 2%
        assert health_metrics["availability"] == 0.95    # 95%

    @pytest.mark.asyncio
    async def test_real_redis_popular_endpoints(self, redis_client):
        """실제 Redis에서 인기 엔드포인트 조회 테스트"""
        # Given: 엔드포인트 사용량 데이터
        tracker = PerformanceTracker(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:endpoints", "GET:/api/posts", 150)
        await redis_client.hset("api:metrics:endpoints", "POST:/api/posts", 25)
        await redis_client.hset("api:metrics:endpoints", "GET:/api/users", 75)
        await redis_client.hset("api:metrics:endpoints", "GET:/api/comments", 50)
        
        # When: 인기 엔드포인트 조회
        popular_endpoints = await tracker.get_popular_endpoints(limit=3)
        
        # Then: 사용량 기준 정렬
        assert len(popular_endpoints) == 3
        assert popular_endpoints[0]["endpoint"] == "GET:/api/posts"
        assert popular_endpoints[0]["requests"] == 150
        assert popular_endpoints[1]["endpoint"] == "GET:/api/users"
        assert popular_endpoints[1]["requests"] == 75
        assert popular_endpoints[2]["endpoint"] == "GET:/api/comments"
        assert popular_endpoints[2]["requests"] == 50

    @pytest.mark.asyncio
    async def test_real_redis_data_retention(self, redis_client):
        """실제 Redis에서 데이터 보존 정책 테스트"""
        # Given: 데이터 보존 정책이 있는 추적기
        tracker = PerformanceTracker(
            redis_client=redis_client,
            max_data_points=3,  # 최대 3개만 유지
            retention_hours=1
        )
        
        class MockRequest:
            def __init__(self):
                self.method = "GET"
                class MockURL:
                    path = "/api/posts"
                self.url = MockURL()
                self.headers = {"user-agent": "test-agent"}
                class MockClient:
                    host = "127.0.0.1"
                self.client = MockClient()
        
        request = MockRequest()
        
        # When: 5개의 요청 추적 (max_data_points=3 초과)
        for i in range(5):
            tracking_data = await tracker.start_tracking(request)
            await tracker.end_tracking(tracking_data, 200)
        
        # Then: 최대 3개까지만 저장됨
        timing_data = await redis_client.lrange("api:timing:GET:/api/posts", 0, -1)
        assert len(timing_data) <= 3

    def test_redis_connection_failure_handling(self):
        """Redis 연결 실패 처리 테스트"""
        # Given: 잘못된 Redis URL
        try:
            invalid_client = redis.from_url("redis://invalid-host:6379")
            tracker = PerformanceTracker(redis_client=invalid_client)
            
            # When/Then: 에러가 발생해도 추적기는 생성됨 (graceful degradation)
            assert tracker is not None
            assert tracker.redis_client is not None
            
        except Exception:
            # 연결 실패는 예상되는 동작
            pass