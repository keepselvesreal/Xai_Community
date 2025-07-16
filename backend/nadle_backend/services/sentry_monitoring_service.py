"""
Sentry 에러 모니터링 서비스

Sentry SDK를 사용하여 에러 통계를 수집하고 분석하는 서비스
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from ..config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class SentryErrorInfo:
    """개별 에러 정보"""
    message: str
    timestamp: str
    error_type: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class SentryErrorStats:
    """Sentry 에러 통계 데이터 클래스"""
    last_hour_errors: int
    last_24h_errors: int
    last_3d_errors: int
    error_rate_per_hour: float
    status: str  # 'healthy', 'warning', 'critical'
    last_error_time: Optional[str]
    environment: str
    total_events: int
    recent_errors: List[SentryErrorInfo]  # 최근 에러 목록
    

class SentryMonitoringService:
    """Sentry 에러 모니터링 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Sentry 클라이언트 설정 상태 확인
        self.sentry_configured = (
            SENTRY_AVAILABLE and 
            self.settings.sentry_dsn and 
            len(self.settings.sentry_dsn.strip()) > 0
        )
        
        if not self.sentry_configured:
            logger.warning("Sentry가 설정되지 않았습니다. 모의 데이터를 사용합니다.")
    
    async def get_error_statistics(self) -> SentryErrorStats:
        """
        Sentry 에러 통계를 조회합니다.
        1시간/24시간/3일 단위로 에러 개수를 집계합니다.
        """
        try:
            if not self.sentry_configured:
                logger.warning("Sentry가 설정되지 않았습니다.")
                return SentryErrorStats(
                    last_hour_errors=0,
                    last_24h_errors=0,
                    last_3d_errors=0,
                    error_rate_per_hour=0.0,
                    status='unconfigured',
                    last_error_time=None,
                    environment=self.settings.environment,
                    total_events=0,
                    recent_errors=[]
                )
            
            # 실제 Sentry 데이터 수집
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                self.executor, 
                self._collect_sentry_statistics
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Sentry 에러 통계 조회 실패: {e}")
            # 오류 발생 시 에러 상태 반환
            return SentryErrorStats(
                last_hour_errors=0,
                last_24h_errors=0,
                last_3d_errors=0,
                error_rate_per_hour=0.0,
                status='error',
                last_error_time=None,
                environment=self.settings.environment,
                total_events=0,
                recent_errors=[]
            )
    
    def _collect_sentry_statistics(self) -> SentryErrorStats:
        """
        실제 Sentry SDK를 사용하여 통계를 수집합니다.
        
        주의: 현재 Sentry SDK는 에러 통계 조회 기능을 제공하지 않으므로,
        실제 에러 통계는 Sentry Web API를 사용하여 구현해야 합니다.
        """
        try:
            # 현재 Sentry 설정 정보 확인
            current_hub = sentry_sdk.Hub.current
            client = current_hub.client
            
            if not client:
                logger.warning("Sentry 클라이언트가 초기화되지 않았습니다.")
                return self._get_default_stats()
            
            # Sentry 연결 상태 확인
            is_connected = client.dsn is not None
            
            if is_connected:
                logger.info("Sentry 클라이언트 연결됨, 실제 에러 통계 수집 필요")
                
                # TODO: 실제 Sentry Web API 호출 구현 필요
                # 현재는 Sentry가 연결되어 있지만 실제 에러 통계를 가져올 수 없음을 표시
                
                return SentryErrorStats(
                    last_hour_errors=0,
                    last_24h_errors=0,
                    last_3d_errors=0,
                    error_rate_per_hour=0.0,
                    status='no_data',  # 연결되었지만 데이터 없음
                    last_error_time=None,
                    environment=self.settings.environment,
                    total_events=0,
                    recent_errors=[]
                )
            else:
                logger.warning("Sentry 클라이언트 연결 실패")
                return self._get_default_stats()
                
        except Exception as e:
            logger.error(f"Sentry 통계 수집 중 오류: {e}")
            return SentryErrorStats(
                last_hour_errors=0,
                last_24h_errors=0,
                last_3d_errors=0,
                error_rate_per_hour=0.0,
                status='error',
                last_error_time=None,
                environment=self.settings.environment,
                total_events=0,
                recent_errors=[]
            )
    
    
    def _get_default_stats(self) -> SentryErrorStats:
        """기본 에러 통계를 반환합니다."""
        return SentryErrorStats(
            last_hour_errors=0,
            last_24h_errors=0,
            last_3d_errors=0,
            error_rate_per_hour=0.0,
            status='healthy',
            last_error_time=None,
            environment=self.settings.environment,
            total_events=0,
            recent_errors=[]
        )
    
    def _determine_status(self, hourly_errors: int) -> str:
        """
        시간당 에러 개수를 기반으로 상태를 결정합니다.
        """
        if hourly_errors == 0:
            return 'healthy'
        elif hourly_errors <= 5:
            return 'warning'
        else:
            return 'critical'
    
    def _determine_service_status(self, is_configured: bool, has_error: bool) -> str:
        """
        서비스 설정 상태와 에러 여부를 기반으로 전체 상태를 결정합니다.
        """
        if not is_configured:
            return 'unconfigured'
        elif has_error:
            return 'error'
        else:
            return 'no_data'  # 설정되어 있지만 데이터 없음
    
    async def get_error_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        지정된 시간 동안의 에러 트렌드를 조회합니다.
        
        현재는 Sentry Web API 구현이 없으므로 빈 배열을 반환합니다.
        """
        try:
            logger.info(f"에러 트렌드 조회 요청: {hours}시간")
            
            if not self.sentry_configured:
                logger.warning("Sentry가 설정되지 않았습니다.")
                return []
            
            # TODO: Sentry Web API를 사용하여 실제 트렌드 데이터 조회 구현 필요
            logger.warning("에러 트렌드 데이터 수집이 구현되지 않았습니다.")
            
            return []
            
        except Exception as e:
            logger.error(f"에러 트렌드 조회 실패: {e}")
            return []
    
    async def check_sentry_health(self) -> Dict[str, Any]:
        """
        Sentry 연결 상태를 확인합니다.
        """
        try:
            if not SENTRY_AVAILABLE:
                return {
                    'status': 'unavailable',
                    'message': 'Sentry SDK가 설치되지 않았습니다',
                    'configured': False
                }
            
            if not self.sentry_configured:
                return {
                    'status': 'unconfigured',
                    'message': 'Sentry DSN이 설정되지 않았습니다',
                    'configured': False
                }
            
            # Sentry 클라이언트 상태 확인
            current_hub = sentry_sdk.Hub.current
            client = current_hub.client
            
            if client and client.dsn:
                return {
                    'status': 'healthy',
                    'message': 'Sentry 연결 정상',
                    'configured': True,
                    'dsn_configured': True,
                    'environment': self.settings.sentry_environment or 'default'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Sentry 클라이언트 초기화 실패',
                    'configured': False
                }
                
        except Exception as e:
            logger.error(f"Sentry 상태 확인 실패: {e}")
            return {
                'status': 'error',
                'message': f'Sentry 상태 확인 중 오류: {str(e)}',
                'configured': False
            }
    
    async def capture_test_error(self) -> Dict[str, Any]:
        """
        테스트용 에러를 Sentry에 전송합니다.
        """
        try:
            if not self.sentry_configured:
                return {
                    'success': False,
                    'message': 'Sentry가 설정되지 않았습니다'
                }
            
            # 테스트 에러 전송
            try:
                raise ValueError("테스트 에러 - 모니터링 시스템에서 생성됨")
            except ValueError as e:
                sentry_sdk.capture_exception(e)
                
            return {
                'success': True,
                'message': '테스트 에러가 Sentry에 전송되었습니다',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"테스트 에러 전송 실패: {e}")
            return {
                'success': False,
                'message': f'테스트 에러 전송 실패: {str(e)}'
            }
    
    def __del__(self):
        """리소스 정리"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)