"""
모니터링 API 실제 Redis 통합 테스트

서비스와 Redis의 직접적인 통합을 테스트
"""
import pytest
import json
import time
import redis.asyncio as redis


@pytest.mark.integration
@pytest.mark.redis
class TestMonitoringAPIRedisIntegration:
    """모니터링 API와 실제 Redis 통합 테스트"""

    @pytest.fixture
    async def redis_client(self):
        """실제 Redis 클라이언트 (테스트용)"""
        try:
            # 테스트용 Redis 인스턴스에 연결
            client = redis.from_url("redis://localhost:6379/13")  # DB 13는 API Redis 테스트 전용
            await client.ping()
            
            # 테스트 시작 전 DB 정리
            await client.flushdb()
            
            yield client
            
            # 테스트 완료 후 정리
            await client.flushdb()
            await client.aclose()
            
        except Exception as e:
            pytest.skip(f"Redis server not available for API integration testing: {e}")

    @pytest.mark.asyncio
    async def test_monitoring_service_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 모니터링 서비스 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 테스트 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:endpoints", "GET:/api/posts", 150)
        await redis_client.hset("api:metrics:endpoints", "POST:/api/posts", 25)
        await redis_client.hset("api:metrics:status_codes", "status:200", 120)
        await redis_client.hset("api:metrics:status_codes", "status:201", 25)
        await redis_client.hset("api:metrics:status_codes", "status:500", 5)
        
        # When: 서비스를 통해 메트릭 조회
        metrics = await service.get_system_metrics()
        
        # Then: 실제 데이터가 올바르게 조회됨
        assert "endpoints" in metrics
        assert "status_codes" in metrics
        assert metrics["endpoints"]["GET:/api/posts"] == 150
        assert metrics["endpoints"]["POST:/api/posts"] == 25
        assert metrics["status_codes"]["200"] == 120
        assert metrics["status_codes"]["201"] == 25
        assert metrics["status_codes"]["500"] == 5

    @pytest.mark.asyncio
    async def test_health_status_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 헬스 상태 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 상태코드 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:status_codes", "status:200", 90)
        await redis_client.hset("api:metrics:status_codes", "status:201", 5)
        await redis_client.hset("api:metrics:status_codes", "status:500", 5)  # 5% 에러율
        
        # When: 헬스 상태 조회
        health = await service.get_health_status()
        
        # Then: 올바른 헬스 상태 반환
        assert "status" in health
        assert "error_rate" in health
        assert "availability" in health
        assert health["error_rate"] == 0.05  # 5/100 = 5%
        assert health["status"] == "critical"  # 5% > 5% 임계값

    @pytest.mark.asyncio
    async def test_slow_requests_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 느린 요청 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 느린 요청 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        slow_request_data = [
            {"endpoint": "GET:/api/posts", "response_time": 2.5, "timestamp": time.time(), "status_code": 200},
            {"endpoint": "POST:/api/users", "response_time": 3.1, "timestamp": time.time(), "status_code": 201}
        ]
        
        for data in slow_request_data:
            await redis_client.lpush("api:alerts:slow_requests", json.dumps(data))
        
        # When: 느린 요청 목록 조회
        slow_requests = await service.get_slow_requests(limit=10)
        
        # Then: 느린 요청 데이터 반환 (lpush로 인해 역순)
        assert len(slow_requests) == 2
        assert slow_requests[0]["endpoint"] == "POST:/api/users"  # 마지막에 추가된 것이 첫 번째
        assert slow_requests[0]["response_time"] == 3.1
        assert slow_requests[1]["endpoint"] == "GET:/api/posts"  # 먼저 추가된 것이 두 번째
        assert slow_requests[1]["response_time"] == 2.5

    @pytest.mark.asyncio
    async def test_time_series_data_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 시간별 데이터 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 시간별 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        current_time = time.time()
        timing_data = [
            {"response_time": 0.1, "timestamp": current_time - 300, "status_code": 200},
            {"response_time": 0.15, "timestamp": current_time - 200, "status_code": 200},
            {"response_time": 0.08, "timestamp": current_time - 100, "status_code": 200}
        ]
        
        for data in timing_data:
            await redis_client.lpush("api:timing:GET:/api/posts", json.dumps(data))
        
        # When: 시간별 데이터 조회
        time_series = await service.get_time_series_data("GET:/api/posts", minutes=60)
        
        # Then: 시간별 데이터 반환
        assert "timestamps" in time_series
        assert "response_times" in time_series
        assert len(time_series["timestamps"]) == 3
        assert len(time_series["response_times"]) == 3

    @pytest.mark.asyncio
    async def test_popular_endpoints_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 인기 엔드포인트 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 엔드포인트 사용량 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:endpoints", "GET:/api/posts", 150)
        await redis_client.hset("api:metrics:endpoints", "POST:/api/posts", 25)
        await redis_client.hset("api:metrics:endpoints", "GET:/api/users", 75)
        await redis_client.hset("api:metrics:endpoints", "GET:/api/comments", 50)
        
        # When: 인기 엔드포인트 조회
        popular = await service.get_popular_endpoints(limit=3)
        
        # Then: 사용량 기준으로 정렬된 엔드포인트 반환
        assert len(popular) == 3
        assert popular[0]["endpoint"] == "GET:/api/posts"
        assert popular[0]["requests"] == 150
        assert popular[1]["endpoint"] == "GET:/api/users"
        assert popular[1]["requests"] == 75
        assert popular[2]["endpoint"] == "GET:/api/comments"
        assert popular[2]["requests"] == 50

    @pytest.mark.asyncio
    async def test_aggregated_metrics_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 집계 메트릭 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 메트릭 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        await redis_client.hset("api:metrics:endpoints", "GET:/api/posts", 100)
        await redis_client.hset("api:metrics:endpoints", "POST:/api/posts", 50)
        await redis_client.hset("api:metrics:status_codes", "status:200", 120)
        await redis_client.hset("api:metrics:status_codes", "status:201", 20)
        await redis_client.hset("api:metrics:status_codes", "status:500", 10)
        
        # When: 집계 메트릭 조회
        aggregated = await service.get_aggregated_metrics()
        
        # Then: 올바른 집계 데이터 반환
        assert "total_requests" in aggregated
        assert "success_rate" in aggregated
        assert "endpoints_count" in aggregated
        assert aggregated["total_requests"] == 150  # 100 + 50
        assert aggregated["success_rate"] == pytest.approx(0.933, rel=1e-2)  # 140/150
        assert aggregated["endpoints_count"] == 2

    @pytest.mark.asyncio
    async def test_endpoint_stats_with_real_redis(self, redis_client):
        """실제 Redis를 사용한 엔드포인트 통계 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 실제 Redis에 응답시간 데이터 삽입
        service = MonitoringService(redis_client=redis_client)
        
        timing_data = [
            {"response_time": 0.1, "timestamp": time.time()},
            {"response_time": 0.15, "timestamp": time.time()},
            {"response_time": 0.08, "timestamp": time.time()}
        ]
        
        for data in timing_data:
            await redis_client.lpush("api:timing:GET:/api/posts", json.dumps(data))
        
        # When: 엔드포인트 통계 조회
        stats = await service.get_endpoint_stats("GET:/api/posts")
        
        # Then: 올바른 통계 데이터 반환
        assert "avg_response_time" in stats
        assert "min_response_time" in stats
        assert "max_response_time" in stats
        assert "request_count" in stats
        assert stats["request_count"] == 3
        assert stats["avg_response_time"] == pytest.approx(0.11, rel=1e-2)
        assert stats["min_response_time"] == 0.08
        assert stats["max_response_time"] == 0.15

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, redis_client):
        """Redis 연결 에러 처리 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: Redis 연결 종료
        await redis_client.aclose()
        service = MonitoringService(redis_client=redis_client)
        
        # When/Then: 에러 처리 확인
        slow_requests = await service.get_slow_requests()  # 빈 리스트 반환
        assert slow_requests == []
        
        time_series = await service.get_time_series_data("GET:/api/posts")  # 빈 데이터 반환
        assert time_series == {"timestamps": [], "response_times": []}
        
        popular = await service.get_popular_endpoints()  # 빈 리스트 반환
        assert popular == []
        
        # 엔드포인트 통계는 기본값 반환
        stats = await service.get_endpoint_stats("GET:/api/posts")
        assert stats["request_count"] == 0
        assert stats["avg_response_time"] == 0

    @pytest.mark.asyncio
    async def test_health_status_classification_edge_cases(self, redis_client):
        """헬스 상태 분류 경계값 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        service = MonitoringService(redis_client=redis_client)
        
        # Test Case 1: 정확히 1% 에러율
        await redis_client.flushdb()
        await redis_client.hset("api:metrics:status_codes", "status:200", 99)
        await redis_client.hset("api:metrics:status_codes", "status:500", 1)
        
        health = await service.get_health_status()
        assert health["error_rate"] == 0.01
        assert health["status"] == "warning"  # 1% >= 1%이므로 warning
        
        # Test Case 2: 정확히 5% 에러율
        await redis_client.flushdb()
        await redis_client.hset("api:metrics:status_codes", "status:200", 95)
        await redis_client.hset("api:metrics:status_codes", "status:500", 5)
        
        health = await service.get_health_status()
        assert health["error_rate"] == 0.05
        assert health["status"] == "critical"  # 5% >= 5%이므로 critical

    @pytest.mark.asyncio
    async def test_concurrent_redis_operations(self, redis_client):
        """동시 Redis 작업 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        import asyncio
        
        # Given: 여러 서비스 인스턴스
        services = [MonitoringService(redis_client=redis_client) for _ in range(5)]
        
        # 동시에 Redis에 데이터 삽입
        async def insert_data(index):
            await redis_client.hset("api:metrics:endpoints", f"GET:/api/test{index}", index * 10)
            await redis_client.hset("api:metrics:status_codes", f"status:{200 + index}", index * 5)
        
        await asyncio.gather(*[insert_data(i) for i in range(5)])
        
        # When: 동시에 메트릭 조회
        metrics_tasks = [service.get_system_metrics() for service in services]
        all_metrics = await asyncio.gather(*metrics_tasks)
        
        # Then: 모든 서비스가 동일한 데이터 조회
        for metrics in all_metrics:
            assert len(metrics["endpoints"]) == 5
            assert len(metrics["status_codes"]) == 5
            
        # 데이터 일관성 확인
        first_metrics = all_metrics[0]
        for other_metrics in all_metrics[1:]:
            assert first_metrics["endpoints"] == other_metrics["endpoints"]
            assert first_metrics["status_codes"] == other_metrics["status_codes"]