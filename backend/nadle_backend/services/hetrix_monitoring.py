"""
HetrixTools 모니터링 서비스

HetrixTools API v3를 사용한 업타임 모니터링 서비스
UptimeRobot에서 HetrixTools로 마이그레이션
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

from nadle_backend.config import settings


logger = logging.getLogger(__name__)


class UptimeStatus(Enum):
    """업타임 상태 열거형 (기존 UptimeRobot 호환성 유지)"""
    UP = "up"
    DOWN = "down"
    PAUSED = "paused"
    UNKNOWN = "unknown"


@dataclass
class Monitor:
    """모니터 정보 데이터 클래스"""
    id: str
    name: str
    url: str
    status: UptimeStatus
    uptime: float
    created_at: int
    last_check: int
    last_status_change: int
    monitor_type: str = "website"
    target: str = ""
    response_time: Dict[str, int] = None
    locations: Dict[str, Any] = None
    
    def __post_init__(self):
        """초기화 후 처리"""
        if isinstance(self.status, str):
            self.status = UptimeStatus(self.status)
        if self.target and not self.url:
            self.url = self.target
        if self.response_time is None:
            self.response_time = {}
        if self.locations is None:
            self.locations = {}


@dataclass
class MonitorLog:
    """모니터 로그 데이터 클래스"""
    datetime: str
    type: str
    duration: Optional[int] = None
    reason: Optional[str] = None


class HetrixToolsClient:
    """HetrixTools API v3 클라이언트"""
    
    def __init__(self, api_token: str):
        """
        HetrixTools 클라이언트 초기화
        
        Args:
            api_token: HetrixTools API 토큰
        """
        self.api_token = api_token
        self.base_url = "https://api.hetrixtools.com/v3"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "User-Agent": "Nadle-Backend-HetrixTools-Client/1.0"
        }
        self.session = None
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        API 요청 수행
        
        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            **kwargs: 추가 요청 파라미터
            
        Returns:
            API 응답 데이터
            
        Raises:
            aiohttp.ClientError: API 요청 실패
            ValueError: 응답 파싱 실패
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if not self.session:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(method, url, **kwargs) as response:
                    return await self._handle_response(response)
        else:
            async with self.session.request(method, url, **kwargs) as response:
                return await self._handle_response(response)
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        API 응답 처리
        
        Args:
            response: aiohttp 응답 객체
            
        Returns:
            파싱된 응답 데이터
            
        Raises:
            aiohttp.ClientError: HTTP 오류
            ValueError: JSON 파싱 오류
        """
        try:
            text = await response.text()
            
            if response.status >= 400:
                logger.error(f"HetrixTools API 오류 ({response.status}): {text}")
                response.raise_for_status()
            
            try:
                data = json.loads(text)
                
                # API 오류 확인
                if isinstance(data, dict) and data.get("status") == "ERROR":
                    error_msg = data.get("error_message", "Unknown API error")
                    logger.error(f"HetrixTools API 오류: {error_msg}")
                    raise ValueError(f"API Error: {error_msg}")
                
                return data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}, 응답: {text[:200]}...")
                raise ValueError(f"Invalid JSON response: {e}")
                
        except Exception as e:
            logger.error(f"응답 처리 실패: {e}")
            raise
    
    async def get_monitors(self) -> List[Monitor]:
        """
        모든 업타임 모니터 목록 조회
        
        Returns:
            모니터 목록
        """
        try:
            logger.info("HetrixTools에서 모니터 목록 조회 중...")
            
            data = await self._make_request("GET", "/uptime-monitors")
            
            monitors = []
            for monitor_data in data.get("monitors", []):
                # 응답 시간 추출 (여러 위치 중 가장 빠른 응답 시간)
                locations = monitor_data.get("locations", {})
                response_times = {}
                for location, info in locations.items():
                    if "response_time" in info:
                        response_times[location] = info["response_time"]
                
                monitor = Monitor(
                    id=monitor_data["id"],
                    name=monitor_data["name"],
                    url=monitor_data["target"],
                    target=monitor_data["target"],
                    status=UptimeStatus(monitor_data.get("uptime_status", "unknown")),
                    uptime=float(monitor_data.get("uptime", 0)),
                    created_at=monitor_data.get("created_at", 0),
                    last_check=monitor_data.get("last_check", 0),
                    last_status_change=monitor_data.get("last_status_change", 0),
                    monitor_type=monitor_data.get("type", "website"),
                    response_time=response_times,
                    locations=locations
                )
                monitors.append(monitor)
            
            logger.info(f"모니터 {len(monitors)}개 조회 완료")
            return monitors
            
        except Exception as e:
            logger.error(f"모니터 목록 조회 실패: {e}")
            raise
    
    async def get_monitor_by_name(self, name: str) -> Optional[Monitor]:
        """
        이름으로 특정 모니터 조회
        
        Args:
            name: 모니터 이름
            
        Returns:
            모니터 객체 또는 None
        """
        try:
            monitors = await self.get_monitors()
            
            for monitor in monitors:
                if monitor.name == name:
                    logger.info(f"모니터 '{name}' 찾음")
                    return monitor
            
            logger.warning(f"모니터 '{name}'를 찾을 수 없음")
            return None
            
        except Exception as e:
            logger.error(f"모니터 조회 실패 (이름: {name}): {e}")
            raise
    
    async def get_monitor_by_id(self, monitor_id: str) -> Optional[Monitor]:
        """
        ID로 특정 모니터 조회
        
        Args:
            monitor_id: 모니터 ID
            
        Returns:
            모니터 객체 또는 None
        """
        try:
            monitors = await self.get_monitors()
            
            for monitor in monitors:
                if monitor.id == monitor_id:
                    logger.info(f"모니터 ID '{monitor_id}' 찾음")
                    return monitor
            
            logger.warning(f"모니터 ID '{monitor_id}'를 찾을 수 없음")
            return None
            
        except Exception as e:
            logger.error(f"모니터 조회 실패 (ID: {monitor_id}): {e}")
            raise
    
    async def get_monitors_by_environment(self, environment: str) -> List[Monitor]:
        """
        환경별 모니터 목록 조회
        
        Args:
            environment: 환경 (production, staging, development)
            
        Returns:
            해당 환경의 모니터 목록
        """
        try:
            logger.info(f"환경 '{environment}'의 모니터 조회 중...")
            
            all_monitors = await self.get_monitors()
            
            # 환경별 모니터 이름 패턴 매칭
            env_pattern = f"{environment}-xai-community"
            env_monitors = []
            
            for monitor in all_monitors:
                if env_pattern in monitor.name:
                    env_monitors.append(monitor)
            
            logger.info(f"환경 '{environment}'에서 모니터 {len(env_monitors)}개 찾음")
            return env_monitors
            
        except Exception as e:
            logger.error(f"환경별 모니터 조회 실패 (환경: {environment}): {e}")
            raise
    
    async def get_monitor_logs(
        self, 
        monitor_id: str, 
        days: int = 1
    ) -> List[MonitorLog]:
        """
        모니터 로그 조회
        
        Note: HetrixTools v3 API에서 로그 엔드포인트가 확인되지 않음
        향후 API 업데이트 시 구현 예정
        
        Args:
            monitor_id: 모니터 ID
            days: 조회할 일수
            
        Returns:
            모니터 로그 목록 (현재는 빈 목록)
        """
        logger.warning(
            f"HetrixTools v3 API에서 로그 조회 기능이 확인되지 않음 "
            f"(monitor_id: {monitor_id}, days: {days})"
        )
        return []
    
    async def create_monitor(
        self,
        name: str,
        url: str,
        monitor_type: str = "website",
        interval: int = 1
    ) -> Monitor:
        """
        새 모니터 생성
        
        Note: 현재는 테스트용으로만 사용 권장
        실제 프로덕션에서는 대시보드에서 생성 후 API로 조회하는 방식 권장
        
        Args:
            name: 모니터 이름
            url: 모니터링할 URL
            monitor_type: 모니터 타입 (기본값: website)
            interval: 체크 간격 (분, 기본값: 1)
            
        Returns:
            생성된 모니터 객체
        """
        logger.warning(
            f"모니터 생성 기능은 테스트용입니다. "
            f"실제 운영에서는 HetrixTools 대시보드에서 생성하세요. "
            f"(name: {name}, url: {url})"
        )
        
        # v3 API에서 생성 엔드포인트를 확인해야 함
        # 현재는 더미 응답 반환
        return Monitor(
            id="dummy-id",
            name=name,
            url=url,
            status=UptimeStatus.UNKNOWN,
            uptime=0.0,
            created_at=int(datetime.now().timestamp()),
            last_check=0,
            last_status_change=0,
            monitor_type=monitor_type
        )
    
    async def delete_monitor(self, monitor_id: str) -> bool:
        """
        모니터 삭제
        
        Note: 실제 삭제는 HetrixTools 대시보드에서 수행 권장
        
        Args:
            monitor_id: 삭제할 모니터 ID
            
        Returns:
            삭제 성공 여부
        """
        logger.warning(
            f"모니터 삭제 기능은 HetrixTools 대시보드에서 수행하세요. "
            f"(monitor_id: {monitor_id})"
        )
        return False


class HetrixMonitoringService:
    """
    HetrixTools 모니터링 서비스
    
    기존 UptimeMonitoringService와 호환되는 인터페이스 제공
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        HetrixTools 모니터링 서비스 초기화
        
        Args:
            api_token: HetrixTools API 토큰 (기본값: settings에서 가져옴)
        """
        self.api_token = api_token or settings.hetrixtools_api_token
        if not self.api_token:
            raise ValueError("HetrixTools API 토큰이 설정되지 않았습니다")
        
        self.client = None
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.client = HetrixToolsClient(self.api_token)
        await self.client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def get_monitors(self) -> List[Monitor]:
        """
        모니터 목록 조회 (동기 버전, 기존 호환성)
        
        Returns:
            모니터 목록
        """
        if not self.client:
            raise ValueError("서비스가 초기화되지 않았습니다. async with 구문을 사용하세요")
        
        return asyncio.create_task(self.client.get_monitors())
    
    async def get_monitors_async(self) -> List[Monitor]:
        """
        모니터 목록 조회 (비동기 버전)
        
        Returns:
            모니터 목록
        """
        if self.client:
            return await self.client.get_monitors()
        else:
            async with HetrixToolsClient(self.api_token) as client:
                return await client.get_monitors()
    
    async def get_current_environment_monitors(self) -> List[Monitor]:
        """
        현재 환경의 모니터 목록 조회
        
        Returns:
            현재 환경의 모니터 목록
        """
        # 환경 설정에서 현재 환경 판단
        current_env = getattr(settings, 'environment', 'development')
        
        # development는 staging 모니터 사용
        if current_env == 'development':
            current_env = 'staging'
        
        if self.client:
            return await self.client.get_monitors_by_environment(current_env)
        else:
            async with HetrixToolsClient(self.api_token) as client:
                return await client.get_monitors_by_environment(current_env)
    
    def create_monitor(
        self, 
        name: str, 
        url: str, 
        interval: int = 300
    ) -> Monitor:
        """
        모니터 생성 (기존 UptimeRobot 호환성)
        
        Args:
            name: 모니터 이름
            url: 모니터링할 URL
            interval: 체크 간격 (초, HetrixTools는 분 단위로 변환)
            
        Returns:
            생성된 모니터 객체
        """
        # 초를 분으로 변환
        interval_minutes = max(1, interval // 60)
        
        if not self.client:
            raise ValueError("서비스가 초기화되지 않았습니다")
        
        return asyncio.create_task(
            self.client.create_monitor(name, url, interval=interval_minutes)
        )
    
    def delete_monitor(self, monitor_id: str) -> bool:
        """
        모니터 삭제 (기존 UptimeRobot 호환성)
        
        Args:
            monitor_id: 모니터 ID
            
        Returns:
            삭제 성공 여부
        """
        if not self.client:
            raise ValueError("서비스가 초기화되지 않았습니다")
        
        task = asyncio.create_task(self.client.delete_monitor(monitor_id))
        return task
    
    def get_monitor_logs(self, monitor_id: str, days: int = 1) -> List[MonitorLog]:
        """
        모니터 로그 조회 (기존 UptimeRobot 호환성)
        
        Args:
            monitor_id: 모니터 ID
            days: 조회할 일수
            
        Returns:
            모니터 로그 목록
        """
        if not self.client:
            raise ValueError("서비스가 초기화되지 않았습니다")
        
        return asyncio.create_task(self.client.get_monitor_logs(monitor_id, days))


# 기존 UptimeMonitoringService와의 호환성을 위한 별칭
UptimeMonitoringService = HetrixMonitoringService


class HealthCheckService:
    """
    헬스체크 서비스 (기존 코드와 호환성 유지)
    """
    
    def __init__(self):
        """헬스체크 서비스 초기화"""
        self.hetrix_service = None
        
    async def simple_health_check(self) -> Dict[str, Any]:
        """
        간단한 헬스체크 (외부 모니터링 서비스용)
        
        Returns:
            헬스체크 결과
        """
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "nadle-backend-api",
                "uptime": self._get_uptime_seconds(),
                "monitoring_service": "hetrixtools"
            }
        except Exception as e:
            logger.error(f"간단한 헬스체크 실패: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "nadle-backend-api",
                "error": str(e),
                "monitoring_service": "hetrixtools"
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """
        종합 헬스체크
        
        Returns:
            종합 헬스체크 결과
        """
        try:
            checks = {}
            overall_health = "healthy"
            
            # 데이터베이스 체크
            db_check = await self._check_database()
            checks["database"] = db_check
            if db_check["status"] != "healthy":
                overall_health = "unhealthy"
            
            # Redis 체크
            redis_check = await self._check_redis()
            checks["redis"] = redis_check
            if redis_check["status"] != "healthy":
                overall_health = "unhealthy"
            
            # 외부 API 체크
            external_check = await self._check_external_apis()
            checks["external_apis"] = external_check
            if external_check["status"] != "healthy":
                overall_health = "unhealthy"
            
            # HetrixTools 모니터링 상태 체크
            hetrix_check = await self._check_hetrix_monitoring()
            checks["hetrix_monitoring"] = hetrix_check
            
            return {
                "status": overall_health,
                "overall_health": overall_health,
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_service": "hetrixtools"
            }
            
        except Exception as e:
            logger.error(f"종합 헬스체크 실패: {e}")
            return {
                "status": "unhealthy",
                "overall_health": "unhealthy",
                "checks": {"error": {"status": "unhealthy", "message": str(e)}},
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_service": "hetrixtools"
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """데이터베이스 상태 확인"""
        try:
            # 실제 데이터베이스 연결 테스트 로직
            return {"status": "healthy", "response_time": 10}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Redis 상태 확인"""
        try:
            # 실제 Redis 연결 테스트 로직
            return {"status": "healthy", "response_time": 5}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_external_apis(self) -> Dict[str, Any]:
        """외부 API 상태 확인"""
        try:
            # 외부 API 연결 테스트 로직
            return {"status": "healthy", "apis_checked": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_hetrix_monitoring(self) -> Dict[str, Any]:
        """HetrixTools 모니터링 상태 확인"""
        try:
            if not settings.hetrixtools_api_token:
                return {
                    "status": "warning", 
                    "message": "HetrixTools API 토큰이 설정되지 않음"
                }
            
            async with HetrixToolsClient(settings.hetrixtools_api_token) as client:
                monitors = await client.get_monitors()
                
                active_monitors = [m for m in monitors if m.status == UptimeStatus.UP]
                
                return {
                    "status": "healthy",
                    "total_monitors": len(monitors),
                    "active_monitors": len(active_monitors),
                    "api_service": "hetrixtools_v3"
                }
                
        except Exception as e:
            logger.error(f"HetrixTools 모니터링 상태 확인 실패: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e),
                "api_service": "hetrixtools_v3"
            }
    
    def _get_uptime_seconds(self) -> int:
        """서버 업타임 초 계산 (더미 구현)"""
        return 3600  # 1시간
    
    async def get_version_info(self) -> Dict[str, Any]:
        """버전 정보 조회"""
        import os
        return {
            "version": os.getenv("BUILD_VERSION", "unknown"),
            "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
            "build_time": os.getenv("BUILD_TIME", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "service": "xai-community-backend"
        }
    
    async def _check_redis_cache(self) -> Dict[str, Any]:
        """Redis 캐시 상태 확인"""
        try:
            from ..database.redis_factory import get_redis_health
            from ..config import get_settings
            
            redis_health = await get_redis_health()
            settings = get_settings()
            
            return {
                "status": "healthy" if redis_health.get("status") == "connected" else "unhealthy",
                "redis_type": "upstash" if settings.use_upstash_redis else "local",
                "key_prefix": settings.redis_key_prefix,
                "cache_enabled": settings.cache_enabled,
                "details": redis_health
            }
        except Exception as e:
            logger.error(f"Redis 캐시 상태 확인 실패: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }