"""
API 성능 모니터링 미들웨어

요청별 응답시간, 상태코드, 엔드포인트 통계 추적
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    API 성능 추적 클래스

    Redis를 사용하여 실시간 성능 메트릭을 저장하고 분석합니다.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        slow_request_threshold: float = 2.0,  # 2초
        error_rate_threshold: float = 0.05,  # 5%
        max_data_points: int = 1000,
        retention_hours: int = 24,
        enabled: bool = True,
        key_prefix: str = "",
    ):
        """
        성능 추적기 초기화

        Args:
            redis_client: Redis 클라이언트
            slow_request_threshold: 느린 요청 임계값 (초)
            error_rate_threshold: 에러율 임계값
            max_data_points: 최대 데이터 포인트 수
            retention_hours: 데이터 보존 시간 (시간)
            enabled: 추적 활성화 여부
        """
        self.redis_client = redis_client
        self.slow_request_threshold = slow_request_threshold
        self.error_rate_threshold = error_rate_threshold
        self.max_data_points = max_data_points
        self.retention_hours = retention_hours
        self.enabled = enabled
        self.key_prefix = key_prefix

    async def start_tracking(self, request: Request) -> Dict[str, Any]:
        """
        요청 추적 시작

        Args:
            request: FastAPI 요청 객체

        Returns:
            Dict[str, Any]: 추적 데이터
        """
        if not self.enabled:
            return {}

        tracking_data = {
            "start_time": time.time(),
            "method": request.method,
            "path": request.url.path,
            "endpoint": f"{request.method}:{request.url.path}",
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": request.client.host if request.client else None,
        }

        return tracking_data

    async def end_tracking(
        self, tracking_data: Dict[str, Any], status_code: int
    ) -> bool:
        """
        요청 추적 종료 및 메트릭 저장

        Args:
            tracking_data: 추적 시작 시 반환된 데이터
            status_code: HTTP 응답 상태코드

        Returns:
            bool: 느린 요청 여부
        """
        if not self.enabled or not tracking_data:
            return False

        end_time = time.time()
        response_time = end_time - tracking_data["start_time"]

        # 메트릭 데이터 구성
        metric_data = {
            "endpoint": tracking_data["endpoint"],
            "method": tracking_data["method"],
            "path": tracking_data["path"],
            "status_code": status_code,
            "response_time": response_time,
            "timestamp": end_time,
            "user_agent": tracking_data.get("user_agent"),
            "client_ip": tracking_data.get("client_ip"),
        }

        # Redis에 메트릭 저장
        await self._store_metrics(metric_data)

        # 느린 요청 감지
        is_slow = response_time > self.slow_request_threshold
        if is_slow:
            await self._store_slow_request(metric_data)

        return is_slow

    async def _store_metrics(self, metric_data: Dict[str, Any]) -> None:
        """메트릭 데이터 저장"""
        try:
            # 엔드포인트별 요청 수 증가
            endpoint_key = self._generate_endpoint_key(
                metric_data["method"], metric_data["path"]
            )
            endpoints_redis_key = f"{self.key_prefix}api:metrics:endpoints" if self.key_prefix else "api:metrics:endpoints"
            await self.redis_client.hincrby(endpoints_redis_key, endpoint_key, 1)

            # 상태코드별 요청 수 증가
            status_key = self._generate_status_key(metric_data["status_code"])
            status_codes_redis_key = f"{self.key_prefix}api:metrics:status_codes" if self.key_prefix else "api:metrics:status_codes"
            await self.redis_client.hincrby(status_codes_redis_key, status_key, 1)
            
            # Rate Limiting 메트릭 저장
            if metric_data["status_code"] == 429:
                # Rate limit 차단 횟수 증가
                rate_limit_blocks_key = f"{self.key_prefix}api:metrics:rate_limit_blocks" if self.key_prefix else "api:metrics:rate_limit_blocks"
                await self.redis_client.hincrby(rate_limit_blocks_key, endpoint_key, 1)
                
                # 시간별 Rate limit 차단 통계
                hour_key = f"{self.key_prefix}rate_limit_blocks:{datetime.now().strftime('%Y%m%d%H')}" if self.key_prefix else f"rate_limit_blocks:{datetime.now().strftime('%Y%m%d%H')}"
                await self.redis_client.hincrby(hour_key, endpoint_key, 1)
                await self.redis_client.expire(hour_key, 86400)  # 24시간 보존

            # 응답시간 데이터 저장 (최근 데이터만 유지)
            timing_key = self._generate_timing_key(
                metric_data["method"], metric_data["path"]
            )
            timing_data = json.dumps(
                {
                    "response_time": metric_data["response_time"],
                    "timestamp": metric_data["timestamp"],
                    "status_code": metric_data["status_code"],
                }
            )

            await self.redis_client.lpush(f"api:timing:{timing_key}", timing_data)
            await self.redis_client.ltrim(
                f"api:timing:{timing_key}", 0, self.max_data_points - 1
            )

            # 데이터 만료 시간 설정
            await self.redis_client.expire(
                f"api:timing:{timing_key}", self.retention_hours * 3600
            )

        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

    async def _store_slow_request(self, metric_data: Dict[str, Any]) -> None:
        """느린 요청 데이터 저장"""
        try:
            # JSON 직렬화 가능한 데이터만 저장 (Mock 객체 제외)
            slow_request_data = {
                "endpoint": metric_data["endpoint"],
                "response_time": metric_data["response_time"],
                "timestamp": metric_data["timestamp"],
                "status_code": metric_data["status_code"],
            }

            # user_agent와 client_ip가 실제 값이면 추가 (Mock 객체가 아닌 경우)
            user_agent = metric_data.get("user_agent")
            if user_agent and isinstance(user_agent, str):
                slow_request_data["user_agent"] = user_agent

            client_ip = metric_data.get("client_ip")
            if client_ip and isinstance(client_ip, str):
                slow_request_data["client_ip"] = client_ip

            slow_request_json = json.dumps(slow_request_data)

            await self.redis_client.lpush("api:alerts:slow_requests", slow_request_json)
            await self.redis_client.ltrim(
                "api:alerts:slow_requests", 0, 99
            )  # 최근 100개만 유지

            logger.warning(
                f"Slow request detected: {metric_data['endpoint']} "
                f"took {metric_data['response_time']:.3f}s"
            )

        except Exception as e:
            logger.error(f"Failed to store slow request alert: {e}")

    def _generate_endpoint_key(self, method: str, path: str) -> str:
        """엔드포인트 키 생성"""
        return f"{method}:{path}"

    def _generate_status_key(self, status_code: int) -> str:
        """상태코드 키 생성"""
        return f"status:{status_code}"

    def _generate_timing_key(self, method: str, path: str) -> str:
        """타이밍 키 생성"""
        return f"api:metrics:timing:{method}:{path}"

    async def get_metrics(self) -> Dict[str, Any]:
        """전체 메트릭 조회"""
        try:
            # 엔드포인트별 통계
            endpoints_redis_key = f"{self.key_prefix}api:metrics:endpoints" if self.key_prefix else "api:metrics:endpoints"
            endpoint_stats = await self.redis_client.hgetall(endpoints_redis_key)
            endpoints = {}
            if endpoint_stats:
                for k, v in endpoint_stats.items():
                    # k와 v가 bytes인지 string인지 확인 (Mock vs Real Redis)
                    key = k.decode() if hasattr(k, "decode") else k
                    value = int(v.decode() if hasattr(v, "decode") else v)
                    # 이미 "method:path" 형식이므로 그대로 사용
                    endpoints[key] = value

            # 상태코드별 통계
            status_codes_redis_key = f"{self.key_prefix}api:metrics:status_codes" if self.key_prefix else "api:metrics:status_codes"
            status_stats = await self.redis_client.hgetall(status_codes_redis_key)
            status_codes = {}
            if status_stats:
                for k, v in status_stats.items():
                    # k와 v가 bytes인지 string인지 확인 (Mock vs Real Redis)
                    key = k.decode() if hasattr(k, "decode") else k
                    value = int(v.decode() if hasattr(v, "decode") else v)
                    # "status:" prefix 제거하고 상태코드만 추출
                    if key.startswith("status:"):
                        status_code = key[len("status:") :]
                        status_codes[status_code] = value
                    else:
                        status_codes[key] = value

            return {
                "endpoints": endpoints,
                "status_codes": status_codes,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"endpoints": {}, "status_codes": {}, "timestamp": time.time()}

    async def get_realtime_stats(self, endpoint: str) -> Dict[str, Any]:
        """실시간 통계 계산"""
        try:
            timing_key = f"api:timing:{endpoint}"
            raw_data = await self.redis_client.lrange(timing_key, 0, -1)

            if not raw_data:
                return {
                    "avg_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "request_count": 0,
                }

            response_times = []
            for data in raw_data:
                try:
                    # data가 bytes인지 string인지 확인 (Mock vs Real Redis)
                    data_str = data.decode() if hasattr(data, "decode") else data
                    parsed = json.loads(data_str)
                    response_times.append(parsed["response_time"])
                except (json.JSONDecodeError, KeyError):
                    continue

            if not response_times:
                return {
                    "avg_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "request_count": 0,
                }

            return {
                "avg_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "request_count": len(response_times),
            }

        except Exception as e:
            logger.error(f"Failed to get realtime stats: {e}")
            return {
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "request_count": 0,
            }

    async def calculate_error_rate(self) -> float:
        """전체 에러율 계산"""
        try:
            status_codes_redis_key = f"{self.key_prefix}api:metrics:status_codes" if self.key_prefix else "api:metrics:status_codes"
            status_stats = await self.redis_client.hgetall(status_codes_redis_key)
            if not status_stats:
                return 0.0

            total_requests = 0
            error_requests = 0

            for status_code_bytes, count_bytes in status_stats.items():
                # bytes인지 string인지 확인 (Mock vs Real Redis)
                status_code_key = (
                    status_code_bytes.decode()
                    if hasattr(status_code_bytes, "decode")
                    else status_code_bytes
                )
                count = int(
                    count_bytes.decode()
                    if hasattr(count_bytes, "decode")
                    else count_bytes
                )

                # "status:" prefix 제거하고 실제 상태코드 추출
                if status_code_key.startswith("status:"):
                    status_code = status_code_key[len("status:") :]
                else:
                    status_code = status_code_key

                total_requests += count

                # 5xx 에러를 에러로 계산
                if status_code.startswith("5"):
                    error_requests += count

            if total_requests == 0:
                return 0.0

            return error_requests / total_requests

        except Exception as e:
            logger.error(f"Failed to calculate error rate: {e}")
            return 0.0

    async def get_time_series_metrics(
        self, endpoint: str, minutes: int = 60
    ) -> Dict[str, List]:
        """시간별 메트릭 조회"""
        try:
            timing_key = f"api:timing:{endpoint}"
            raw_data = await self.redis_client.lrange(timing_key, 0, -1)

            timestamps = []
            response_times = []

            cutoff_time = time.time() - (minutes * 60)

            for data in raw_data:
                try:
                    # data가 bytes인지 string인지 확인 (Mock vs Real Redis)
                    data_str = data.decode() if hasattr(data, "decode") else data
                    parsed = json.loads(data_str)
                    if parsed["timestamp"] >= cutoff_time:
                        timestamps.append(parsed["timestamp"])
                        response_times.append(parsed["response_time"])
                except (json.JSONDecodeError, KeyError):
                    continue

            return {"timestamps": timestamps, "response_times": response_times}

        except Exception as e:
            logger.error(f"Failed to get time series metrics: {e}")
            return {"timestamps": [], "response_times": []}

    async def get_health_metrics(self) -> Dict[str, Any]:
        """헬스체크 메트릭 조회"""
        try:
            status_stats = await self.redis_client.hgetall("api:metrics:status_codes")

            total_requests = 0
            success_requests = 0
            error_requests = 0

            for status_code_bytes, count_bytes in status_stats.items():
                # bytes인지 string인지 확인 (Mock vs Real Redis)
                status_code_key = (
                    status_code_bytes.decode()
                    if hasattr(status_code_bytes, "decode")
                    else status_code_bytes
                )
                count = int(
                    count_bytes.decode()
                    if hasattr(count_bytes, "decode")
                    else count_bytes
                )

                # "status:" prefix 제거하고 실제 상태코드 추출
                if status_code_key.startswith("status:"):
                    status_code = status_code_key[len("status:") :]
                else:
                    status_code = status_code_key

                total_requests += count

                if status_code.startswith("2"):  # 2xx 성공
                    success_requests += count
                elif status_code.startswith("5"):  # 5xx 에러
                    error_requests += count

            error_rate = error_requests / total_requests if total_requests > 0 else 0
            availability = (
                success_requests / total_requests if total_requests > 0 else 1
            )

            return {
                "total_requests": total_requests,
                "success_requests": success_requests,
                "error_requests": error_requests,
                "error_rate": error_rate,
                "availability": availability,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Failed to get health metrics: {e}")
            return {
                "total_requests": 0,
                "success_requests": 0,
                "error_requests": 0,
                "error_rate": 0,
                "availability": 1,
                "timestamp": time.time(),
            }

    async def get_popular_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """인기 엔드포인트 조회"""
        try:
            endpoints_redis_key = f"{self.key_prefix}api:metrics:endpoints" if self.key_prefix else "api:metrics:endpoints"
            endpoint_stats = await self.redis_client.hgetall(endpoints_redis_key)

            if not endpoint_stats:
                return []

            # bytes인지 string인지 확인하고 요청 수 기준으로 정렬
            sorted_endpoints = sorted(
                [
                    (
                        k.decode() if hasattr(k, "decode") else k,
                        int(v.decode() if hasattr(v, "decode") else v),
                    )
                    for k, v in endpoint_stats.items()
                ],
                key=lambda x: x[1],
                reverse=True,
            )

            return [
                {"endpoint": endpoint, "requests": count}
                for endpoint, count in sorted_endpoints[:limit]
            ]

        except Exception as e:
            logger.error(f"Failed to get popular endpoints: {e}")
            return []

    async def get_rate_limit_metrics(self) -> Dict[str, Any]:
        """Rate Limiting 메트릭 조회"""
        try:
            # Rate limit 차단 통계 조회
            rate_limit_blocks_key = f"{self.key_prefix}api:metrics:rate_limit_blocks" if self.key_prefix else "api:metrics:rate_limit_blocks"
            rate_limit_blocks = await self.redis_client.hgetall(rate_limit_blocks_key)
            
            # 전체 요청 수 조회
            endpoints_redis_key = f"{self.key_prefix}api:metrics:endpoints" if self.key_prefix else "api:metrics:endpoints"
            total_requests = await self.redis_client.hgetall(endpoints_redis_key)
            
            metrics = {
                "total_blocks": 0,
                "endpoints": [],
                "block_rate": 0.0,
                "hourly_blocks": []
            }
            
            if rate_limit_blocks:
                # 엔드포인트별 차단 통계
                for endpoint_bytes, block_count_bytes in rate_limit_blocks.items():
                    endpoint = endpoint_bytes.decode() if hasattr(endpoint_bytes, "decode") else endpoint_bytes
                    block_count = int(block_count_bytes.decode() if hasattr(block_count_bytes, "decode") else block_count_bytes)
                    
                    # 해당 엔드포인트의 전체 요청 수
                    total_for_endpoint = 0
                    if total_requests and endpoint in [k.decode() if hasattr(k, "decode") else k for k in total_requests.keys()]:
                        for k, v in total_requests.items():
                            key = k.decode() if hasattr(k, "decode") else k
                            if key == endpoint:
                                total_for_endpoint = int(v.decode() if hasattr(v, "decode") else v)
                                break
                    
                    block_rate = (block_count / total_for_endpoint * 100) if total_for_endpoint > 0 else 0
                    
                    metrics["endpoints"].append({
                        "endpoint": endpoint,
                        "blocks": block_count,
                        "total_requests": total_for_endpoint,
                        "block_rate": round(block_rate, 2)
                    })
                    metrics["total_blocks"] += block_count
                
                # 전체 차단율 계산
                total_all_requests = sum(int(v.decode() if hasattr(v, "decode") else v) for v in total_requests.values()) if total_requests else 0
                metrics["block_rate"] = round((metrics["total_blocks"] / total_all_requests * 100), 2) if total_all_requests > 0 else 0
            
            # 시간별 차단 통계 (최근 24시간)
            current_hour = datetime.now()
            for i in range(24):
                hour = current_hour - timedelta(hours=i)
                hour_key = f"{self.key_prefix}rate_limit_blocks:{hour.strftime('%Y%m%d%H')}" if self.key_prefix else f"rate_limit_blocks:{hour.strftime('%Y%m%d%H')}"
                hour_blocks = await self.redis_client.hgetall(hour_key)
                
                hour_total = sum(int(v.decode() if hasattr(v, "decode") else v) for v in hour_blocks.values()) if hour_blocks else 0
                metrics["hourly_blocks"].append({
                    "hour": hour.strftime('%H:00'),
                    "blocks": hour_total
                })
            
            # 최신 시간순으로 정렬
            metrics["hourly_blocks"].reverse()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get rate limit metrics: {e}")
            return {
                "total_blocks": 0,
                "endpoints": [],
                "block_rate": 0.0,
                "hourly_blocks": []
            }

    async def get_rate_limit_summary(self) -> Dict[str, Any]:
        """Rate Limiting 요약 정보"""
        try:
            metrics = await self.get_rate_limit_metrics()
            
            # 상위 차단된 엔드포인트
            top_blocked = sorted(metrics["endpoints"], key=lambda x: x["blocks"], reverse=True)[:5]
            
            # 최근 1시간 차단 수
            recent_hour_blocks = metrics["hourly_blocks"][-1]["blocks"] if metrics["hourly_blocks"] else 0
            
            return {
                "total_blocks_24h": metrics["total_blocks"],
                "recent_hour_blocks": recent_hour_blocks,
                "overall_block_rate": metrics["block_rate"],
                "top_blocked_endpoints": top_blocked,
                "status": "critical" if metrics["block_rate"] > 10 else "warning" if metrics["block_rate"] > 5 else "normal"
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit summary: {e}")
            return {
                "total_blocks_24h": 0,
                "recent_hour_blocks": 0,
                "overall_block_rate": 0.0,
                "top_blocked_endpoints": [],
                "status": "unknown"
            }


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 성능 모니터링 미들웨어

    모든 요청에 대해 성능 메트릭을 수집합니다.
    """

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        """
        미들웨어 초기화

        Args:
            app: FastAPI 애플리케이션
            redis_client: Redis 클라이언트 (선택적)
        """
        super().__init__(app)
        self.redis_client = redis_client or self._get_default_redis_client()
        
        # 환경별 키 프리픽스 가져오기
        key_prefix = self._get_key_prefix()
        
        self.tracker = (
            PerformanceTracker(self.redis_client, key_prefix=key_prefix) if self.redis_client else None
        )

    def _get_key_prefix(self) -> str:
        """환경별 키 프리픽스 가져오기"""
        try:
            from nadle_backend.config import settings
            
            # development 환경의 경우 "dev:" 프리픽스 사용
            if settings.environment == "development":
                return "dev:"
            elif settings.environment == "test":
                return "test:"
            elif settings.environment == "staging":
                return "stage:"
            elif settings.environment == "production":
                return "prod:"
            else:
                return ""
        except Exception as e:
            logger.warning(f"Failed to get key prefix: {e}")
            return ""

    def _get_default_redis_client(self) -> Optional[redis.Redis]:
        """기본 Redis 클라이언트 생성"""
        try:
            from nadle_backend.config import settings

            return redis.from_url(settings.redis_url)
        except Exception as e:
            logger.warning(f"Failed to create Redis client: {e}")
            return None

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        요청 처리 및 성능 추적

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response: HTTP 응답
        """
        # 추적 시작
        tracking_data = {}
        if self.tracker:
            tracking_data = await self.tracker.start_tracking(request)

        try:
            # 다음 미들웨어/핸들러 호출
            response = await call_next(request)

            # 추적 종료
            if self.tracker and tracking_data:
                await self.tracker.end_tracking(tracking_data, response.status_code)

            return response

        except Exception as e:
            # 에러 발생 시에도 추적
            if self.tracker and tracking_data:
                await self.tracker.end_tracking(tracking_data, 500)

            # 에러 재발생
            raise


def get_redis_client() -> Optional[redis.Redis]:
    """Redis 클라이언트 팩토리 함수"""
    try:
        from nadle_backend.config import settings

        return redis.from_url(settings.redis_url)
    except Exception as e:
        logger.warning(f"Failed to create Redis client: {e}")
        return None
