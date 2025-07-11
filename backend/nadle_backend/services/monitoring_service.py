"""
모니터링 서비스

API 성능 모니터링 데이터를 조회하고 분석하는 서비스
"""
import json
import logging
from typing import Dict, Any, List, Optional
import redis.asyncio as redis

from nadle_backend.middleware.monitoring import PerformanceTracker

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    모니터링 데이터 서비스
    
    PerformanceTracker를 활용하여 모니터링 데이터를 조회하고 분석합니다.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        모니터링 서비스 초기화
        
        Args:
            redis_client: Redis 클라이언트 (선택적)
        """
        self.redis_client = redis_client or self._get_default_redis_client()
        self.tracker = PerformanceTracker(self.redis_client) if self.redis_client else None
    
    def _get_default_redis_client(self) -> Optional[redis.Redis]:
        """기본 Redis 클라이언트 생성"""
        try:
            from nadle_backend.config import settings
            return redis.from_url(settings.redis_url)
        except Exception as e:
            logger.warning(f"Failed to create Redis client: {e}")
            return None
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        시스템 전체 메트릭 조회
        
        Returns:
            Dict[str, Any]: 시스템 메트릭 데이터
        """
        if not self.tracker:
            raise Exception("Performance tracker not available")
        
        try:
            return await self.tracker.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            raise
    
    async def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """
        특정 엔드포인트 통계 조회
        
        Args:
            endpoint: 엔드포인트 (예: "GET:/api/posts")
            
        Returns:
            Dict[str, Any]: 엔드포인트 통계 데이터
        """
        if not self.tracker:
            raise Exception("Performance tracker not available")
        
        try:
            return await self.tracker.get_realtime_stats(endpoint)
        except Exception as e:
            logger.error(f"Failed to get endpoint stats for {endpoint}: {e}")
            # 에러 시 기본값 반환
            return {
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "request_count": 0
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        시스템 헬스 상태 조회
        
        Returns:
            Dict[str, Any]: 헬스 상태 데이터
        """
        if not self.tracker:
            raise Exception("Performance tracker not available")
        
        try:
            health_metrics = await self.tracker.get_health_metrics()
            
            # 헬스 상태 분류
            error_rate = health_metrics.get("error_rate", 0)
            if error_rate < 0.01:  # 1% 미만
                status = "healthy"
            elif error_rate < 0.05:  # 1-5%
                status = "warning"
            else:  # 5% 초과
                status = "critical"
            
            health_metrics["status"] = status
            return health_metrics
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            raise
    
    async def get_slow_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        느린 요청 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            
        Returns:
            List[Dict[str, Any]]: 느린 요청 목록
        """
        if not self.redis_client:
            return []
        
        try:
            raw_data = await self.redis_client.lrange("api:alerts:slow_requests", 0, limit - 1)
            
            slow_requests = []
            for data in raw_data:
                try:
                    # data가 bytes인지 string인지 확인 (Mock vs Real Redis)
                    data_str = data.decode() if hasattr(data, 'decode') else data
                    parsed = json.loads(data_str)
                    slow_requests.append(parsed)
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            return slow_requests
            
        except Exception as e:
            logger.error(f"Failed to get slow requests: {e}")
            return []
    
    async def get_time_series_data(self, endpoint: str, minutes: int = 60) -> Dict[str, List]:
        """
        시간별 시계열 데이터 조회
        
        Args:
            endpoint: 엔드포인트
            minutes: 조회할 시간 범위 (분)
            
        Returns:
            Dict[str, List]: 시계열 데이터
        """
        if not self.tracker:
            return {"timestamps": [], "response_times": []}
        
        try:
            return await self.tracker.get_time_series_metrics(endpoint, minutes)
        except Exception as e:
            logger.error(f"Failed to get time series data for {endpoint}: {e}")
            return {"timestamps": [], "response_times": []}
    
    async def get_popular_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        인기 엔드포인트 조회
        
        Args:
            limit: 조회할 최대 개수
            
        Returns:
            List[Dict[str, Any]]: 인기 엔드포인트 목록
        """
        if not self.tracker:
            return []
        
        try:
            return await self.tracker.get_popular_endpoints(limit)
        except Exception as e:
            logger.error(f"Failed to get popular endpoints: {e}")
            return []
    
    async def get_aggregated_metrics(self) -> Dict[str, Any]:
        """
        집계된 메트릭 조회
        
        Returns:
            Dict[str, Any]: 집계 메트릭 데이터
        """
        if not self.tracker:
            raise Exception("Performance tracker not available")
        
        try:
            metrics = await self.tracker.get_metrics()
            
            # 전체 요청 수 계산
            total_requests = sum(metrics["endpoints"].values()) if metrics["endpoints"] else 0
            
            # 성공률 계산 (2xx 상태코드)
            success_requests = sum(
                count for status, count in metrics["status_codes"].items() 
                if status.startswith('2')
            ) if metrics["status_codes"] else 0
            
            success_rate = success_requests / total_requests if total_requests > 0 else 0
            
            return {
                "total_requests": total_requests,
                "success_rate": success_rate,
                "endpoints_count": len(metrics["endpoints"]),
                "timestamp": metrics.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            raise


def get_monitoring_service() -> MonitoringService:
    """모니터링 서비스 팩토리 함수"""
    return MonitoringService()