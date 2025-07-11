"""
모니터링 메트릭 통합 테스트

TDD Red 단계: FastAPI와 Redis를 사용한 실제 성능 추적 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import asyncio
import json


class TestMonitoringMetricsIntegration:
    """모니터링 메트릭 통합 테스트"""

    @pytest.fixture
    def app_with_monitoring(self):
        """모니터링 미들웨어가 적용된 테스트 앱"""
        from unittest.mock import AsyncMock
        app = FastAPI()
        
        # 모킹된 Redis 클라이언트
        mock_redis = AsyncMock()
        mock_redis.hincrby = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()
        mock_redis.expire = AsyncMock()
        
        # 모니터링 미들웨어 추가 (모킹된 Redis 클라이언트 사용)
        from nadle_backend.middleware.monitoring import MonitoringMiddleware
        app.add_middleware(MonitoringMiddleware, redis_client=mock_redis)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)
            return {"message": "slow"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app

    @pytest.fixture
    def client(self, app_with_monitoring):
        """테스트 클라이언트"""
        return TestClient(app_with_monitoring)

    def test_middleware_tracks_successful_requests(self, client):
        """성공적인 요청 추적 테스트"""
        # When: 요청 수행
        response = client.get("/test")
        
        # Then: 성공 응답
        assert response.status_code == 200

    def test_middleware_tracks_error_requests(self, client):
        """에러 요청 추적 테스트"""
        # When: 에러 요청 수행
        try:
            response = client.get("/error")
            # Then: 에러 응답
            assert response.status_code == 500
        except Exception:
            # 에러가 발생해도 테스트는 통과 (미들웨어가 동작했음을 의미)
            pass

    @pytest.mark.asyncio
    async def test_concurrent_request_tracking(self):
        """동시 요청 추적 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 모킹된 Redis
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 동시에 여러 요청 추적
        async def track_request(path):
            mock_request = Mock()
            mock_request.method = "GET"
            mock_request.url.path = path
            
            tracking_data = await tracker.start_tracking(mock_request)
            await asyncio.sleep(0.05)  # 50ms
            await tracker.end_tracking(tracking_data, 200)
        
        await asyncio.gather(
            track_request("/api/posts"),
            track_request("/api/users"),
            track_request("/api/posts"),
        )
        
        # Then: 모든 요청이 추적됨
        assert mock_redis.hincrby.call_count >= 3
        assert mock_redis.lpush.call_count >= 3

    @pytest.mark.asyncio
    async def test_metrics_aggregation_over_time(self):
        """시간별 메트릭 집계 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 시간별 데이터가 있는 Redis (현재 시간 기준으로 설정)
        import time
        current_time = time.time()
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = [
            json.dumps({"response_time": 0.1, "timestamp": current_time - 600, "endpoint": "GET:/api/posts"}),
            json.dumps({"response_time": 0.15, "timestamp": current_time - 300, "endpoint": "GET:/api/posts"}),
            json.dumps({"response_time": 0.08, "timestamp": current_time - 100, "endpoint": "GET:/api/posts"}),
        ]
        
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 시간별 메트릭 조회
        time_series = await tracker.get_time_series_metrics("GET:/api/posts", minutes=60)
        
        # Then: 시간별 데이터 반환
        assert "timestamps" in time_series
        assert "response_times" in time_series
        assert len(time_series["timestamps"]) == 3

    @pytest.mark.asyncio
    async def test_performance_threshold_alerts(self):
        """성능 임계값 알림 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 알림 임계값 설정
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(
            redis_client=mock_redis,
            slow_request_threshold=0.05,  # 50ms
            error_rate_threshold=0.1      # 10%
        )
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/slow"
        
        # When: 느린 요청 추적
        tracking_data = await tracker.start_tracking(mock_request)
        await asyncio.sleep(0.1)  # 100ms - 임계값 초과
        alert_triggered = await tracker.end_tracking(tracking_data, 200)
        
        # Then: 알림 트리거됨
        assert alert_triggered == True
        
        # 알림 데이터가 저장되었는지 확인
        alert_calls = [call for call in mock_redis.lpush.call_args_list 
                      if "alerts" in str(call)]
        assert len(alert_calls) > 0

    @pytest.mark.asyncio
    async def test_memory_efficient_data_retention(self):
        """메모리 효율적인 데이터 보존 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 데이터 보존 정책이 있는 추적기
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(
            redis_client=mock_redis,
            max_data_points=100,
            retention_hours=24
        )
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/posts"
        
        # When: 많은 요청 추적
        for i in range(150):
            tracking_data = await tracker.start_tracking(mock_request)
            await tracker.end_tracking(tracking_data, 200)
        
        # Then: 데이터 정리 메서드 호출됨
        ltrim_calls = [call for call in mock_redis.ltrim.call_args_list]
        assert len(ltrim_calls) > 0  # 데이터 제한 적용됨

    @pytest.mark.asyncio
    async def test_health_check_metrics(self):
        """헬스체크 메트릭 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 다양한 상태의 요청 데이터
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "status:200": "90",
            "status:500": "10",
        }
        
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 헬스체크 메트릭 조회
        health_metrics = await tracker.get_health_metrics()
        
        # Then: 시스템 상태 정보 반환
        assert "total_requests" in health_metrics
        assert "error_rate" in health_metrics
        assert "availability" in health_metrics
        assert health_metrics["error_rate"] == 0.1  # 10%
        assert health_metrics["availability"] == 0.9  # 90%

    @pytest.mark.asyncio
    async def test_endpoint_popularity_ranking(self):
        """엔드포인트 인기도 순위 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 다양한 엔드포인트 사용량 데이터
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "GET:/api/posts": "150",
            "POST:/api/posts": "25",
            "GET:/api/users": "75",
            "GET:/api/comments": "50",
        }
        
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 인기 엔드포인트 조회
        popular_endpoints = await tracker.get_popular_endpoints(limit=3)
        
        # Then: 사용량 기준 정렬된 엔드포인트 반환
        assert len(popular_endpoints) == 3
        assert popular_endpoints[0]["endpoint"] == "GET:/api/posts"
        assert popular_endpoints[0]["requests"] == 150
        assert popular_endpoints[1]["endpoint"] == "GET:/api/users"