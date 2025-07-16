"""
API 엔드포인트 모니터링 서비스

주요 API 엔드포인트들의 상태를 체크하고 응답시간을 측정하는 서비스
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import aiohttp
from urllib.parse import urljoin

from ..config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class EndpointStatus:
    """API 엔드포인트 상태 정보"""
    endpoint: str
    name: str
    status: str  # 'healthy', 'degraded', 'down'
    response_time: float  # milliseconds
    status_code: Optional[int]
    last_check: str
    error_message: Optional[str] = None


@dataclass
class EndpointMonitoringResult:
    """전체 엔드포인트 모니터링 결과"""
    overall_status: str
    total_endpoints: int
    healthy_count: int
    degraded_count: int
    down_count: int
    average_response_time: float
    endpoints: List[EndpointStatus]
    last_check: str


class EndpointMonitoringService:
    """API 엔드포인트 모니터링 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self._get_base_url()
        
        # 모니터링할 엔드포인트 정의
        self.endpoints = [
            # Health API
            {
                'endpoint': '/api/health',
                'name': 'Health Check',
                'method': 'GET',
                'timeout': 5.0,
                'expected_status': [200]
            },
            {
                'endpoint': '/api/monitoring/health/simple',
                'name': 'Simple Health',
                'method': 'GET',
                'timeout': 5.0,
                'expected_status': [200]
            },
            
            # Auth API
            {
                'endpoint': '/api/auth/health',
                'name': 'Auth Health',
                'method': 'GET',
                'timeout': 10.0,
                'expected_status': [200, 404]  # 404도 정상 (엔드포인트 존재 확인)
            },
            
            # Posts API
            {
                'endpoint': '/api/posts/health',
                'name': 'Posts Health',
                'method': 'GET',
                'timeout': 10.0,
                'expected_status': [200, 404]
            },
            
            # Comments API
            {
                'endpoint': '/api/comments/health',
                'name': 'Comments Health',
                'method': 'GET',
                'timeout': 10.0,
                'expected_status': [200, 404]
            },
            
            # 실제 데이터 엔드포인트 (인증 없이 접근 가능한 것들)
            {
                'endpoint': '/api/posts?limit=1',
                'name': 'Posts List',
                'method': 'GET',
                'timeout': 15.0,
                'expected_status': [200]
            }
        ]
    
    def _get_base_url(self) -> str:
        """기본 URL을 환경에 따라 결정합니다."""
        if self.settings.environment == 'development':
            return 'http://localhost:8000'
        elif self.settings.environment == 'staging':
            return 'https://staging-api.example.com'  # 실제 스테이징 URL로 변경
        else:
            return 'https://api.example.com'  # 실제 프로덕션 URL로 변경
    
    async def check_all_endpoints(self) -> EndpointMonitoringResult:
        """모든 엔드포인트를 병렬로 체크합니다."""
        try:
            logger.info("API 엔드포인트 상태 체크 시작")
            
            # 모든 엔드포인트를 병렬로 체크
            tasks = []
            for endpoint_config in self.endpoints:
                task = asyncio.create_task(
                    self._check_endpoint(endpoint_config)
                )
                tasks.append(task)
            
            # 모든 체크 완료 대기
            endpoint_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            valid_results = []
            for result in endpoint_results:
                if isinstance(result, EndpointStatus):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"엔드포인트 체크 중 오류: {result}")
                    # 오류 발생 시 기본 실패 상태 추가
                    valid_results.append(EndpointStatus(
                        endpoint='unknown',
                        name='Unknown',
                        status='down',
                        response_time=0.0,
                        status_code=None,
                        last_check=datetime.utcnow().isoformat(),
                        error_message=str(result)
                    ))
            
            # 전체 결과 집계
            result = self._aggregate_results(valid_results)
            
            logger.info(f"API 엔드포인트 체크 완료: {result.healthy_count}/{result.total_endpoints} 정상")
            return result
            
        except Exception as e:
            logger.error(f"엔드포인트 모니터링 실패: {e}")
            # 오류 발생 시 기본 결과 반환
            return EndpointMonitoringResult(
                overall_status='unknown',
                total_endpoints=0,
                healthy_count=0,
                degraded_count=0,
                down_count=0,
                average_response_time=0.0,
                endpoints=[],
                last_check=datetime.utcnow().isoformat()
            )
    
    async def _check_endpoint(self, endpoint_config: Dict[str, Any]) -> EndpointStatus:
        """개별 엔드포인트를 체크합니다."""
        endpoint_url = urljoin(self.base_url, endpoint_config['endpoint'])
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=endpoint_config['timeout'])
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=endpoint_config['method'],
                    url=endpoint_url,
                    headers={'User-Agent': 'Nadle-Monitoring/1.0'}
                ) as response:
                    response_time = (time.time() - start_time) * 1000  # ms
                    
                    # 상태 판단
                    status = self._determine_endpoint_status(
                        response.status,
                        response_time,
                        endpoint_config['expected_status']
                    )
                    
                    return EndpointStatus(
                        endpoint=endpoint_config['endpoint'],
                        name=endpoint_config['name'],
                        status=status,
                        response_time=round(response_time, 2),
                        status_code=response.status,
                        last_check=datetime.utcnow().isoformat(),
                        error_message=None
                    )
        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return EndpointStatus(
                endpoint=endpoint_config['endpoint'],
                name=endpoint_config['name'],
                status='down',
                response_time=round(response_time, 2),
                status_code=None,
                last_check=datetime.utcnow().isoformat(),
                error_message='요청 시간 초과'
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return EndpointStatus(
                endpoint=endpoint_config['endpoint'],
                name=endpoint_config['name'],
                status='down',
                response_time=round(response_time, 2),
                status_code=None,
                last_check=datetime.utcnow().isoformat(),
                error_message=str(e)
            )
    
    def _determine_endpoint_status(
        self, 
        status_code: int, 
        response_time: float, 
        expected_statuses: List[int]
    ) -> str:
        """응답 코드와 응답 시간을 기반으로 엔드포인트 상태를 결정합니다."""
        
        # 상태 코드 확인
        if status_code not in expected_statuses:
            return 'down'
        
        # 응답 시간 기준 (ms)
        if response_time > 5000:  # 5초 초과
            return 'down'
        elif response_time > 2000:  # 2초 초과
            return 'degraded'
        else:
            return 'healthy'
    
    def _aggregate_results(self, endpoints: List[EndpointStatus]) -> EndpointMonitoringResult:
        """엔드포인트 체크 결과를 집계합니다."""
        total_endpoints = len(endpoints)
        healthy_count = sum(1 for ep in endpoints if ep.status == 'healthy')
        degraded_count = sum(1 for ep in endpoints if ep.status == 'degraded')
        down_count = sum(1 for ep in endpoints if ep.status == 'down')
        
        # 평균 응답 시간 계산
        if endpoints:
            average_response_time = sum(ep.response_time for ep in endpoints) / len(endpoints)
        else:
            average_response_time = 0.0
        
        # 전체 상태 결정
        if down_count == 0 and degraded_count == 0:
            overall_status = 'healthy'
        elif down_count == 0:
            overall_status = 'degraded'
        elif down_count < total_endpoints:
            overall_status = 'degraded'
        else:
            overall_status = 'down'
        
        return EndpointMonitoringResult(
            overall_status=overall_status,
            total_endpoints=total_endpoints,
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            down_count=down_count,
            average_response_time=round(average_response_time, 2),
            endpoints=endpoints,
            last_check=datetime.utcnow().isoformat()
        )
    
    async def check_specific_endpoint(self, endpoint_name: str) -> Optional[EndpointStatus]:
        """특정 엔드포인트만 체크합니다."""
        try:
            endpoint_config = next(
                (ep for ep in self.endpoints if ep['name'] == endpoint_name),
                None
            )
            
            if not endpoint_config:
                return None
            
            return await self._check_endpoint(endpoint_config)
            
        except Exception as e:
            logger.error(f"특정 엔드포인트 체크 실패 ({endpoint_name}): {e}")
            return None
    
    async def get_endpoint_history(self, endpoint_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        특정 엔드포인트의 히스토리를 조회합니다.
        실제 구현에서는 데이터베이스나 캐시에서 히스토리 데이터를 조회해야 합니다.
        
        현재는 히스토리 데이터를 저장하지 않으므로 빈 배열을 반환합니다.
        """
        try:
            logger.info(f"엔드포인트 히스토리 조회 요청: {endpoint_name} ({hours}시간)")
            logger.warning("엔드포인트 히스토리 데이터가 구현되지 않았습니다.")
            
            # 히스토리 데이터 저장 시스템이 없으므로 빈 배열 반환
            return []
            
        except Exception as e:
            logger.error(f"엔드포인트 히스토리 조회 실패: {e}")
            return []
    
    def get_monitored_endpoints(self) -> List[Dict[str, Any]]:
        """모니터링 대상 엔드포인트 목록을 반환합니다."""
        return [
            {
                'endpoint': ep['endpoint'],
                'name': ep['name'],
                'method': ep['method'],
                'timeout': ep['timeout']
            }
            for ep in self.endpoints
        ]