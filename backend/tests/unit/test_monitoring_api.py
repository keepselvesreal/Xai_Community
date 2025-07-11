"""
모니터링 API 엔드포인트 단위 테스트

TDD Red 단계: API 기능별 세부 동작 테스트 (Mock 기반)
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
import time


class TestMonitoringAPI:
    """모니터링 API 엔드포인트 단위 테스트"""

    def test_monitoring_service_initialization(self):
        """모니터링 서비스 초기화 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: Redis 클라이언트 모킹
        mock_redis = Mock()
        
        # When: 모니터링 서비스 초기화
        service = MonitoringService(redis_client=mock_redis)
        
        # Then: 올바르게 초기화됨
        assert service.redis_client == mock_redis
        assert service.tracker is not None

    @pytest.mark.asyncio
    async def test_get_system_metrics(self):
        """시스템 전체 메트릭 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock tracker의 get_metrics 메서드
        service.tracker.get_metrics = AsyncMock(return_value={
            "endpoints": {"GET:/api/posts": 150, "POST:/api/posts": 25},
            "status_codes": {"200": 120, "201": 25, "404": 5},
            "timestamp": time.time()
        })
        
        # When: 시스템 메트릭 조회
        metrics = await service.get_system_metrics()
        
        # Then: 메트릭 데이터 반환
        assert "endpoints" in metrics
        assert "status_codes" in metrics
        assert "timestamp" in metrics
        assert metrics["endpoints"]["GET:/api/posts"] == 150

    @pytest.mark.asyncio
    async def test_get_endpoint_stats(self):
        """특정 엔드포인트 통계 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock tracker의 get_realtime_stats 메서드
        service.tracker.get_realtime_stats = AsyncMock(return_value={
            "avg_response_time": 0.12,
            "min_response_time": 0.08,
            "max_response_time": 0.25,
            "request_count": 150
        })
        
        # When: 엔드포인트 통계 조회
        stats = await service.get_endpoint_stats("GET:/api/posts")
        
        # Then: 통계 데이터 반환
        assert "avg_response_time" in stats
        assert "request_count" in stats
        assert stats["avg_response_time"] == 0.12
        assert stats["request_count"] == 150

    @pytest.mark.asyncio
    async def test_get_health_status(self):
        """시스템 헬스 상태 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock tracker의 get_health_metrics와 calculate_error_rate 메서드
        service.tracker.get_health_metrics = AsyncMock(return_value={
            "total_requests": 1000,
            "success_requests": 950,
            "error_requests": 50,
            "error_rate": 0.05,
            "availability": 0.95
        })
        
        # When: 헬스 상태 조회
        health = await service.get_health_status()
        
        # Then: 헬스 데이터 반환
        assert "total_requests" in health
        assert "error_rate" in health
        assert "availability" in health
        assert "status" in health
        assert health["error_rate"] == 0.05
        # 에러율 5%이므로 경고 상태
        assert health["status"] in ["healthy", "warning", "critical"]

    @pytest.mark.asyncio
    async def test_get_slow_requests(self):
        """느린 요청 목록 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[
            '{"endpoint": "GET:/api/posts", "response_time": 2.5, "timestamp": 1640995200}',
            '{"endpoint": "POST:/api/users", "response_time": 3.1, "timestamp": 1640995260}'
        ])
        
        service = MonitoringService(redis_client=mock_redis)
        
        # When: 느린 요청 목록 조회
        slow_requests = await service.get_slow_requests(limit=10)
        
        # Then: 느린 요청 목록 반환
        assert len(slow_requests) == 2
        assert slow_requests[0]["endpoint"] == "GET:/api/posts"
        assert slow_requests[0]["response_time"] == 2.5
        assert slow_requests[1]["endpoint"] == "POST:/api/users"

    @pytest.mark.asyncio
    async def test_get_time_series_data(self):
        """시간별 시계열 데이터 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock tracker의 get_time_series_metrics 메서드
        service.tracker.get_time_series_metrics = AsyncMock(return_value={
            "timestamps": [1640995200, 1640995260, 1640995320],
            "response_times": [0.1, 0.15, 0.08]
        })
        
        # When: 시간별 데이터 조회
        time_series = await service.get_time_series_data("GET:/api/posts", minutes=60)
        
        # Then: 시계열 데이터 반환
        assert "timestamps" in time_series
        assert "response_times" in time_series
        assert len(time_series["timestamps"]) == 3
        assert len(time_series["response_times"]) == 3

    @pytest.mark.asyncio
    async def test_get_popular_endpoints(self):
        """인기 엔드포인트 조회 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock tracker의 get_popular_endpoints 메서드
        service.tracker.get_popular_endpoints = AsyncMock(return_value=[
            {"endpoint": "GET:/api/posts", "requests": 150},
            {"endpoint": "GET:/api/users", "requests": 75},
            {"endpoint": "POST:/api/posts", "requests": 25}
        ])
        
        # When: 인기 엔드포인트 조회
        popular = await service.get_popular_endpoints(limit=5)
        
        # Then: 인기 엔드포인트 목록 반환
        assert len(popular) == 3
        assert popular[0]["endpoint"] == "GET:/api/posts"
        assert popular[0]["requests"] == 150

    @pytest.mark.asyncio
    async def test_service_error_handling(self):
        """서비스 에러 처리 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: Redis 연결 실패 시뮬레이션
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock tracker 메서드가 예외 발생
        service.tracker.get_metrics = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        # When/Then: 예외가 적절히 처리됨
        with pytest.raises(Exception):
            await service.get_system_metrics()

    @pytest.mark.asyncio
    async def test_health_status_classification(self):
        """헬스 상태 분류 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Test Case 1: Healthy (에러율 1% 미만)
        service.tracker.get_health_metrics = AsyncMock(return_value={
            "error_rate": 0.005,  # 0.5%
            "availability": 0.995
        })
        health = await service.get_health_status()
        assert health["status"] == "healthy"
        
        # Test Case 2: Warning (에러율 1-5%)
        service.tracker.get_health_metrics = AsyncMock(return_value={
            "error_rate": 0.03,  # 3%
            "availability": 0.97
        })
        health = await service.get_health_status()
        assert health["status"] == "warning"
        
        # Test Case 3: Critical (에러율 5% 초과)
        service.tracker.get_health_metrics = AsyncMock(return_value={
            "error_rate": 0.08,  # 8%
            "availability": 0.92
        })
        health = await service.get_health_status()
        assert health["status"] == "critical"

    @pytest.mark.asyncio
    async def test_metrics_aggregation(self):
        """메트릭 집계 및 계산 테스트"""
        from nadle_backend.services.monitoring_service import MonitoringService
        
        # Given: 모킹된 Redis와 서비스
        mock_redis = AsyncMock()
        service = MonitoringService(redis_client=mock_redis)
        
        # Mock 메서드들
        service.tracker.get_metrics = AsyncMock(return_value={
            "endpoints": {"GET:/api/posts": 100, "POST:/api/posts": 50},
            "status_codes": {"200": 120, "201": 20, "500": 10}
        })
        
        # When: 집계된 메트릭 조회
        aggregated = await service.get_aggregated_metrics()
        
        # Then: 집계 데이터 포함
        assert "total_requests" in aggregated
        assert "success_rate" in aggregated
        assert aggregated["total_requests"] == 150  # 100 + 50
        assert aggregated["success_rate"] == pytest.approx(0.933, rel=1e-2)  # 140/150