"""
Vercel 모니터링 서비스

Vercel REST API를 사용하여 프로젝트 배포 상태, 
함수 성능, Web Vitals 등을 모니터링
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
import aiohttp
import json

from ...config import get_settings
from ...models.monitoring.monitoring_models import VercelMetrics, ServiceStatus, MonitoringError


logger = logging.getLogger(__name__)


class VercelMonitoringService:
    """Vercel 모니터링 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self._api_token = self.settings.vercel_api_token
        self._team_id = self.settings.vercel_team_id
        self._project_id = self.settings.vercel_project_id
        self._base_url = "https://api.vercel.com"
        self._session = None
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        if self._session is None:
            headers = {
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json"
            }
            self._session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def get_project_status(self) -> ServiceStatus:
        """Vercel 프로젝트 상태 확인"""
        try:
            if not self._project_id:
                logger.warning("Vercel 프로젝트 ID가 설정되지 않음")
                return ServiceStatus.UNKNOWN
            
            async with self as service:
                # 최신 배포 정보 조회
                deployment = await service._get_latest_deployment()
                
                if not deployment:
                    return ServiceStatus.UNKNOWN
                
                state = deployment.get('state', '').lower()
                
                if state == 'ready':
                    return ServiceStatus.HEALTHY
                elif state in ['building', 'queued']:
                    return ServiceStatus.DEGRADED
                elif state in ['error', 'canceled']:
                    return ServiceStatus.UNHEALTHY
                else:
                    return ServiceStatus.UNKNOWN
                    
        except Exception as e:
            logger.error(f"Vercel 프로젝트 상태 확인 실패: {e}")
            return ServiceStatus.UNKNOWN
    
    async def _get_latest_deployment(self) -> Optional[Dict[str, Any]]:
        """최신 배포 정보 조회"""
        try:
            url = f"{self._base_url}/v6/deployments"
            params = {
                "projectId": self._project_id,
                "limit": 1
            }
            
            if self._team_id:
                params["teamId"] = self._team_id
            
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    deployments = data.get('deployments', [])
                    return deployments[0] if deployments else None
                else:
                    logger.error(f"배포 정보 조회 실패: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"최신 배포 정보 조회 실패: {e}")
            return None
    
    async def _get_project_info(self) -> Optional[Dict[str, Any]]:
        """프로젝트 정보 조회"""
        try:
            url = f"{self._base_url}/v9/projects/{self._project_id}"
            params = {}
            
            if self._team_id:
                params["teamId"] = self._team_id
            
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"프로젝트 정보 조회 실패: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"프로젝트 정보 조회 실패: {e}")
            return None
    
    async def _get_deployment_functions(self, deployment_id: str) -> List[Dict[str, Any]]:
        """배포의 함수 목록 조회"""
        try:
            url = f"{self._base_url}/v1/deployments/{deployment_id}/functions"
            params = {}
            
            if self._team_id:
                params["teamId"] = self._team_id
            
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('functions', [])
                else:
                    logger.debug(f"함수 정보 조회 실패: {response.status}")
                    return []
                    
        except Exception as e:
            logger.debug(f"함수 정보 조회 실패: {e}")
            return []
    
    async def _get_analytics_data(self) -> Dict[str, Any]:
        """애널리틱스 데이터 조회 (Web Analytics API)"""
        analytics_data = {}
        
        try:
            # Web Analytics API는 Pro 플랜 이상에서 사용 가능
            # 여기서는 기본적인 메트릭만 수집
            url = f"{self._base_url}/v1/analytics"
            params = {
                "projectId": self._project_id,
                "from": int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000),
                "until": int(datetime.utcnow().timestamp() * 1000)
            }
            
            if self._team_id:
                params["teamId"] = self._team_id
            
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    analytics_data = data
                elif response.status == 403:
                    logger.debug("Web Analytics API 접근 권한 없음 (Pro 플랜 필요)")
                else:
                    logger.debug(f"애널리틱스 데이터 조회 실패: {response.status}")
                    
        except Exception as e:
            logger.debug(f"애널리틱스 데이터 조회 실패: {e}")
        
        return analytics_data
    
    async def get_metrics(self) -> VercelMetrics:
        """Vercel 메트릭 수집"""
        try:
            async with self as service:
                status = await service.get_project_status()
                
                # 기본 메트릭 데이터 수집
                metrics_data = {
                    "project_id": self._project_id or "unknown",
                    "status": status
                }
                
                # 최신 배포 정보
                deployment = await service._get_latest_deployment()
                if deployment:
                    metrics_data.update({
                        "deployment_id": deployment.get('uid'),
                        "deployment_status": deployment.get('state'),
                        "deployment_url": deployment.get('url'),
                        "deployment_created_at": self._parse_timestamp(deployment.get('createdAt'))
                    })
                    
                    # 배포 함수 정보
                    functions = await service._get_deployment_functions(deployment.get('uid', ''))
                    if functions:
                        total_invocations = 0
                        total_duration = 0.0
                        total_errors = 0
                        
                        for func in functions:
                            # 함수별 메트릭 집계 (실제 API에서 제공되는 경우)
                            invocations = func.get('invocations', 0)
                            duration = func.get('duration', 0)
                            errors = func.get('errors', 0)
                            
                            total_invocations += invocations
                            total_duration += duration
                            total_errors += errors
                        
                        metrics_data.update({
                            "function_invocations": total_invocations,
                            "function_duration_ms": total_duration,
                            "function_errors": total_errors
                        })
                
                # 프로젝트 정보
                project_info = await service._get_project_info()
                if project_info:
                    # 대역폭 정보 (제한적)
                    analytics = project_info.get('analytics', {})
                    if analytics:
                        metrics_data["bandwidth_bytes"] = analytics.get('bandwidth', 0)
                
                # 애널리틱스 데이터
                analytics_data = await service._get_analytics_data()
                if analytics_data:
                    # Web Vitals 데이터 추출 (사용 가능한 경우)
                    vitals = analytics_data.get('vitals', {})
                    if vitals:
                        metrics_data.update({
                            "first_contentful_paint": vitals.get('fcp'),
                            "largest_contentful_paint": vitals.get('lcp'),
                            "cumulative_layout_shift": vitals.get('cls')
                        })
                        
                        # Core Web Vitals 점수 계산 (간단한 버전)
                        if all(v is not None for v in [vitals.get('fcp'), vitals.get('lcp'), vitals.get('cls')]):
                            score = self._calculate_web_vitals_score(vitals)
                            metrics_data["core_web_vitals_score"] = score
                
                # 응답 시간 측정 (배포 URL 핑)
                if deployment and deployment.get('url'):
                    response_time = await service._measure_response_time(deployment['url'])
                    if response_time:
                        metrics_data["response_time_ms"] = response_time
                
                metrics = VercelMetrics(**metrics_data)
                logger.info(f"Vercel 메트릭 수집 완료: {self._project_id}")
                return metrics
                
        except Exception as e:
            logger.error(f"Vercel 메트릭 수집 실패: {e}")
            return VercelMetrics(
                project_id=self._project_id or "unknown",
                status=ServiceStatus.UNKNOWN,
                error_message=str(e)
            )
    
    async def _measure_response_time(self, url: str) -> Optional[float]:
        """배포 URL 응답 시간 측정"""
        try:
            if not url.startswith('http'):
                url = f"https://{url}"
            
            start_time = asyncio.get_event_loop().time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    await response.read()  # 응답 본문까지 읽기
                    
            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000
            
            return response_time_ms
            
        except Exception as e:
            logger.debug(f"응답 시간 측정 실패 ({url}): {e}")
            return None
    
    def _calculate_web_vitals_score(self, vitals: Dict[str, float]) -> float:
        """Core Web Vitals 점수 계산 (간단한 버전)"""
        try:
            fcp = vitals.get('fcp', 0)  # First Contentful Paint (ms)
            lcp = vitals.get('lcp', 0)  # Largest Contentful Paint (ms)
            cls = vitals.get('cls', 0)  # Cumulative Layout Shift
            
            # 점수 계산 (0-100 스케일)
            fcp_score = max(0, 100 - (fcp / 20))  # 2초 이하면 100점
            lcp_score = max(0, 100 - (lcp / 25))  # 2.5초 이하면 100점
            cls_score = max(0, 100 - (cls * 1000))  # 0.1 이하면 100점
            
            # 가중 평균
            total_score = (fcp_score * 0.3 + lcp_score * 0.4 + cls_score * 0.3)
            return min(100, max(0, total_score))
            
        except Exception:
            return 0.0
    
    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[datetime]:
        """타임스탬프 파싱"""
        if not timestamp:
            return None
        
        try:
            # Vercel API는 ISO 8601 형식 또는 Unix timestamp 사용
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp / 1000)  # milliseconds
            else:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception:
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Vercel 헬스체크"""
        try:
            async with self as service:
                status = await service.get_project_status()
                
                return {
                    "service": "vercel",
                    "status": status.value,
                    "project_id": self._project_id,
                    "team_id": self._team_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Vercel 헬스체크 실패: {e}")
            return {
                "service": "vercel",
                "status": ServiceStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def is_configured(self) -> bool:
        """Vercel 모니터링 설정 여부 확인"""
        return all([
            self._api_token,
            self._project_id
        ])