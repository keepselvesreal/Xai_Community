"""
API 성능 모니터링 미들웨어 단위 테스트

TDD Red 단계: 응답시간, 상태코드, 엔드포인트별 통계 추적 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import time
from fastapi import Request, Response


class TestMonitoringMiddleware:
    """API 성능 모니터링 미들웨어 테스트"""

    def test_performance_tracker_initialization(self):
        """성능 추적기 초기화 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: Redis 클라이언트 모킹
        mock_redis = Mock()
        
        # When: 성능 추적기 초기화
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # Then: 올바르게 초기화됨
        assert tracker.redis_client == mock_redis
        assert tracker.enabled == True

    @pytest.mark.asyncio
    async def test_request_timing_tracking(self):
        """요청 처리 시간 추적 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 모킹된 Redis와 요청
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/posts"
        
        # When: 요청 추적 시작 및 종료
        tracking_data = await tracker.start_tracking(mock_request)
        await asyncio.sleep(0.1)  # 100ms 시뮬레이션
        await tracker.end_tracking(tracking_data, 200)
        
        # Then: Redis에 성능 데이터 저장됨
        mock_redis.hincrby.assert_called()
        mock_redis.lpush.assert_called()
        
        # 응답시간이 기록되었는지 확인
        call_args = mock_redis.lpush.call_args[0]
        assert "response_time" in str(call_args)
        assert "GET:/api/posts" in str(call_args)

    @pytest.mark.asyncio
    async def test_endpoint_statistics_aggregation(self):
        """엔드포인트별 통계 집계 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 모킹된 Redis
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 여러 요청 추적
        endpoints = [
            ("GET", "/api/posts", 200),
            ("GET", "/api/posts", 200),
            ("POST", "/api/posts", 201),
            ("GET", "/api/users", 404),
        ]
        
        for method, path, status in endpoints:
            mock_request = Mock()
            mock_request.method = method
            mock_request.url.path = path
            
            tracking_data = await tracker.start_tracking(mock_request)
            await tracker.end_tracking(tracking_data, status)
        
        # Then: 각 엔드포인트별로 통계가 기록됨
        assert mock_redis.hincrby.call_count >= 4
        assert mock_redis.lpush.call_count >= 4

    @pytest.mark.asyncio
    async def test_status_code_tracking(self):
        """HTTP 상태코드별 추적 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 모킹된 Redis
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/posts"
        
        # When: 다양한 상태코드로 추적
        status_codes = [200, 201, 400, 404, 500]
        
        for status_code in status_codes:
            tracking_data = await tracker.start_tracking(mock_request)
            await tracker.end_tracking(tracking_data, status_code)
        
        # Then: 상태코드별 통계가 기록됨
        hincrby_calls = [call[0] for call in mock_redis.hincrby.call_args_list]
        
        # Redis의 hincrby 호출에서 해시 키와 필드 분리
        status_calls = [call for call in hincrby_calls if call[0] == "api:metrics:status_codes"]
        
        assert any(call[1] == "status:200" for call in status_calls)
        assert any(call[1] == "status:404" for call in status_calls)
        assert any(call[1] == "status:500" for call in status_calls)

    @pytest.mark.asyncio
    async def test_slow_request_detection(self):
        """느린 요청 감지 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 모킹된 Redis와 느린 요청 시뮬레이션
        mock_redis = AsyncMock()
        tracker = PerformanceTracker(redis_client=mock_redis, slow_request_threshold=0.05)  # 50ms
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/slow-endpoint"
        
        # When: 느린 요청 추적
        tracking_data = await tracker.start_tracking(mock_request)
        await asyncio.sleep(0.1)  # 100ms - 임계값보다 느림
        slow_detected = await tracker.end_tracking(tracking_data, 200)
        
        # Then: 느린 요청으로 감지됨
        assert slow_detected == True
        
        # 느린 요청 목록에 추가되었는지 확인
        slow_request_calls = [call for call in mock_redis.lpush.call_args_list 
                             if "slow_requests" in str(call)]
        assert len(slow_request_calls) > 0

    def test_metrics_key_generation(self):
        """메트릭 키 생성 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 추적기
        tracker = PerformanceTracker(redis_client=Mock())
        
        # When: 메트릭 키 생성
        endpoint_key = tracker._generate_endpoint_key("GET", "/api/posts")
        status_key = tracker._generate_status_key(200)
        timing_key = tracker._generate_timing_key("GET", "/api/posts")
        
        # Then: 올바른 키 형식
        assert endpoint_key == "GET:/api/posts"
        assert status_key == "status:200"
        assert timing_key == "api:metrics:timing:GET:/api/posts"

    @pytest.mark.asyncio
    async def test_metrics_retrieval(self):
        """메트릭 조회 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 메트릭 데이터가 있는 Redis
        mock_redis = AsyncMock()
        mock_redis.hgetall.side_effect = [
            # 첫 번째 호출 (endpoints)
            {
                "GET:/api/posts": "150",
                "POST:/api/posts": "25",
            },
            # 두 번째 호출 (status_codes)
            {
                "status:200": "120",
                "status:201": "25",
                "status:404": "5",
            }
        ]
        
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 메트릭 조회
        metrics = await tracker.get_metrics()
        
        # Then: 올바른 메트릭 반환
        assert "endpoints" in metrics
        assert "status_codes" in metrics
        assert metrics["endpoints"]["GET:/api/posts"] == 150
        assert metrics["status_codes"]["200"] == 120

    @pytest.mark.asyncio
    async def test_realtime_statistics(self):
        """실시간 통계 계산 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 응답시간 데이터가 있는 Redis
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = [
            '{"response_time": 0.1, "timestamp": 1640995200}',
            '{"response_time": 0.15, "timestamp": 1640995201}',
            '{"response_time": 0.08, "timestamp": 1640995202}',
        ]
        
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 실시간 통계 계산
        stats = await tracker.get_realtime_stats("GET:/api/posts")
        
        # Then: 올바른 통계 계산됨
        assert "avg_response_time" in stats
        assert "min_response_time" in stats
        assert "max_response_time" in stats
        assert stats["avg_response_time"] == pytest.approx(0.11, rel=1e-2)
        assert stats["min_response_time"] == 0.08
        assert stats["max_response_time"] == 0.15

    @pytest.mark.asyncio
    async def test_error_rate_calculation(self):
        """에러율 계산 테스트"""
        from nadle_backend.middleware.monitoring import PerformanceTracker
        
        # Given: 상태코드 통계가 있는 Redis
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {
            "status:200": "80",
            "status:201": "15",
            "status:404": "3",
            "status:500": "2",
        }
        
        tracker = PerformanceTracker(redis_client=mock_redis)
        
        # When: 에러율 계산
        error_rate = await tracker.calculate_error_rate()
        
        # Then: 올바른 에러율 계산됨 (5xx errors / total requests)
        assert error_rate == pytest.approx(0.02, rel=1e-2)  # 2/100 = 2%