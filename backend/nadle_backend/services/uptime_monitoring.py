"""
업타임 모니터링 서비스

외부 업타임 모니터링 서비스(UptimeRobot 등)와 연동하는 서비스
"""
import time
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

import redis.asyncio as redis
from nadle_backend.config import settings

logger = logging.getLogger(__name__)


class UptimeStatus(Enum):
    """업타임 상태 열거형"""
    UP = "up"
    DOWN = "down"
    PAUSED = "paused"
    UNKNOWN = "unknown"


@dataclass
class UptimeMonitor:
    """업타임 모니터 모델"""
    id: int
    name: str
    url: str
    status: UptimeStatus
    created_at: datetime
    interval: int = 300  # 5분 기본값
    monitor_type: str = "http"


@dataclass
class UptimeAlert:
    """업타임 알림 모델"""
    monitor_id: int
    status: UptimeStatus
    message: str
    timestamp: datetime
    duration: int = 0  # 다운타임 지속 시간 (초)


class HealthCheckService:
    """종합 헬스체크 서비스"""

    def __init__(self):
        self.redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """
        종합적인 헬스체크 수행
        
        Returns:
            Dict: 전체 시스템 상태 정보
        """
        start_time = time.time()
        
        try:
            # 병렬로 모든 헬스체크 실행
            checks = await asyncio.gather(
                self._check_database(),
                self._check_redis(),
                self._check_external_apis(),
                return_exceptions=True
            )
            
            db_check, redis_check, api_check = checks
            
            # 예외 처리
            if isinstance(db_check, Exception):
                db_check = {"status": "unhealthy", "error": str(db_check)}
            if isinstance(redis_check, Exception):
                redis_check = {"status": "unhealthy", "error": str(redis_check)}
            if isinstance(api_check, Exception):
                api_check = {"status": "unhealthy", "error": str(api_check)}
            
            # 전체 상태 판단
            all_healthy = all(
                check.get("status") == "healthy" 
                for check in [db_check, redis_check, api_check]
            )
            
            overall_status = "healthy" if all_healthy else "unhealthy"
            
            end_time = time.time()
            
            return {
                "status": overall_status,
                "overall_health": all_healthy,
                "checks": {
                    "database": db_check,
                    "redis": redis_check,
                    "external_apis": api_check
                },
                "total_response_time": round(end_time - start_time, 3),
                "timestamp": datetime.now().isoformat(),
                "version": getattr(settings, 'api_version', '1.0.0')
            }
            
        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            return {
                "status": "unhealthy",
                "overall_health": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _check_database(self) -> Dict[str, Any]:
        """데이터베이스 연결 상태 확인"""
        start_time = time.time()
        
        try:
            from nadle_backend.database.connection import database
            
            # 데이터베이스 ping 테스트
            if hasattr(database, 'client') and database.client:
                await database.client.admin.command('ping')
                
                end_time = time.time()
                return {
                    "status": "healthy",
                    "response_time": round(end_time - start_time, 3),
                    "message": "Database connection successful"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Database client not initialized"
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Redis 연결 상태 확인"""
        start_time = time.time()
        
        try:
            redis_client = redis.from_url(self.redis_url)
            
            # Redis ping 테스트
            await redis_client.ping()
            await redis_client.aclose()
            
            end_time = time.time()
            return {
                "status": "healthy",
                "response_time": round(end_time - start_time, 3),
                "message": "Redis connection successful"
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def _check_external_apis(self) -> Dict[str, Any]:
        """외부 API 연결 상태 확인"""
        start_time = time.time()
        
        try:
            # 간단한 HTTP 요청으로 외부 연결 테스트
            async with aiohttp.ClientSession() as session:
                async with session.get('https://httpbin.org/status/200', timeout=5) as response:
                    if response.status == 200:
                        end_time = time.time()
                        return {
                            "status": "healthy",
                            "response_time": round(end_time - start_time, 3),
                            "message": "External API connectivity successful"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"External API returned status {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"External API health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def simple_health_check(self) -> Dict[str, Any]:
        """간단한 헬스체크 (외부 모니터링용)"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time(),
            "service": "nadle-backend-api"
        }


class UptimeMonitoringService:
    """업타임 모니터링 서비스 (UptimeRobot 연동)"""

    def __init__(self, api_key: Optional[str] = None, http_client=None):
        self.api_key = api_key or getattr(settings, 'uptimerobot_api_key', None)
        self.base_url = "https://api.uptimerobot.com/v2"
        self.http_client = http_client or self._get_default_http_client()

    def _get_default_http_client(self):
        """기본 HTTP 클라이언트 반환"""
        try:
            import requests
            return requests
        except ImportError:
            logger.warning("requests library not available")
            return None

    def create_monitor(self, name: str, url: str, interval: int = 300) -> UptimeMonitor:
        """
        새로운 업타임 모니터 생성
        
        Args:
            name: 모니터 이름
            url: 모니터링할 URL
            interval: 체크 간격 (초)
            
        Returns:
            UptimeMonitor: 생성된 모니터 정보
        """
        if not self.api_key:
            raise ValueError("UptimeRobot API key not configured")

        payload = {
            "api_key": self.api_key,
            "format": "json",
            "type": 1,  # HTTP(s)
            "friendly_name": name,
            "url": url,
            "interval": interval
        }

        try:
            response = self.http_client.post(
                f"{self.base_url}/newMonitor",
                data=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: Failed to create monitor")

            result = response.json()
            
            if result.get("stat") != "ok":
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"UptimeRobot API error: {error_msg}")

            monitor_data = result["monitor"]
            
            return UptimeMonitor(
                id=monitor_data["id"],
                name=monitor_data["friendly_name"],
                url=monitor_data["url"],
                status=self._parse_status(monitor_data["status"]),
                created_at=datetime.fromtimestamp(int(monitor_data["create_datetime"])),
                interval=interval
            )
            
        except Exception as e:
            logger.error(f"Failed to create monitor: {e}")
            raise

    def get_monitors(self) -> List[UptimeMonitor]:
        """
        모든 모니터 목록 조회
        
        Returns:
            List[UptimeMonitor]: 모니터 목록
        """
        if not self.api_key:
            raise ValueError("UptimeRobot API key not configured")

        payload = {
            "api_key": self.api_key,
            "format": "json"
        }

        try:
            response = self.http_client.get(
                f"{self.base_url}/getMonitors",
                params=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: Failed to get monitors")

            result = response.json()
            
            if result.get("stat") != "ok":
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"UptimeRobot API error: {error_msg}")

            monitors = []
            for monitor_data in result.get("monitors", []):
                monitors.append(UptimeMonitor(
                    id=monitor_data["id"],
                    name=monitor_data["friendly_name"],
                    url=monitor_data["url"],
                    status=self._parse_status(monitor_data["status"]),
                    created_at=datetime.fromtimestamp(int(monitor_data["create_datetime"]))
                ))
            
            return monitors
            
        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            raise

    def get_monitor_logs(self, monitor_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """
        특정 모니터의 로그 조회
        
        Args:
            monitor_id: 모니터 ID
            days: 조회할 일수
            
        Returns:
            List[Dict]: 로그 목록
        """
        if not self.api_key:
            raise ValueError("UptimeRobot API key not configured")

        # 시작 날짜 계산
        start_date = datetime.now() - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())

        payload = {
            "api_key": self.api_key,
            "format": "json",
            "monitors": monitor_id,
            "logs": 1,
            "logs_start_date": start_timestamp
        }

        try:
            response = self.http_client.get(
                f"{self.base_url}/getMonitors",
                params=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: Failed to get monitor logs")

            result = response.json()
            
            if result.get("stat") != "ok":
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"UptimeRobot API error: {error_msg}")

            return result.get("logs", [])
            
        except Exception as e:
            logger.error(f"Failed to get monitor logs: {e}")
            raise

    def delete_monitor(self, monitor_id: int) -> bool:
        """
        모니터 삭제
        
        Args:
            monitor_id: 삭제할 모니터 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        if not self.api_key:
            raise ValueError("UptimeRobot API key not configured")

        payload = {
            "api_key": self.api_key,
            "format": "json",
            "id": monitor_id
        }

        try:
            response = self.http_client.post(
                f"{self.base_url}/deleteMonitor",
                data=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: Failed to delete monitor")

            result = response.json()
            
            if result.get("stat") != "ok":
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"UptimeRobot API error: {error_msg}")

            return True
            
        except Exception as e:
            logger.error(f"Failed to delete monitor: {e}")
            raise

    def _parse_status(self, status_code: int) -> UptimeStatus:
        """UptimeRobot 상태 코드를 UptimeStatus로 변환"""
        status_map = {
            0: UptimeStatus.PAUSED,
            1: UptimeStatus.DOWN,    # Not checked yet
            2: UptimeStatus.UP,
            8: UptimeStatus.UNKNOWN,  # Seems down
            9: UptimeStatus.DOWN
        }
        return status_map.get(status_code, UptimeStatus.UNKNOWN)


# 서비스 의존성 주입을 위한 팩토리 함수들
def get_health_check_service() -> HealthCheckService:
    """헬스체크 서비스 인스턴스 반환"""
    return HealthCheckService()


def get_uptime_monitoring_service() -> UptimeMonitoringService:
    """업타임 모니터링 서비스 인스턴스 반환"""
    return UptimeMonitoringService()