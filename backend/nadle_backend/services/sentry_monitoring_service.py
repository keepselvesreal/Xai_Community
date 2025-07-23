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
from ..core.logging import (
    LogLevel,
    LogServiceType, 
    LogSource,
    LogContext,
    LogMetadata,
    LogEntry,
    LogFilter
)


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
    """Sentry 에러 모니터링 서비스 - DB 기반 통합 관리"""

    def __init__(self, log_service=None):
        """
        Sentry 모니터링 서비스 초기화
        
        Args:
            log_service: LogService 인스턴스 (의존성 주입)
        """
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.log_service = log_service  # LogService 의존성 주입

        # Sentry 클라이언트 설정 상태 확인
        self.sentry_configured = (
            SENTRY_AVAILABLE
            and self.settings.sentry_dsn
            and len(self.settings.sentry_dsn.strip()) > 0
        )

        if not self.sentry_configured:
            logger.warning("Sentry가 설정되지 않았습니다.")
        else:
            logger.info("SentryMonitoringService 초기화 완료 - DB 기반 통계 사용")

    async def get_error_statistics(self) -> SentryErrorStats:
        """
        DB에서 직접 Sentry 에러 통계를 조회합니다.
        LogService를 통해 MongoDB에서 실시간 통계를 가져옵니다.
        """
        try:
            if not self.sentry_configured:
                logger.warning("Sentry가 설정되지 않았습니다.")
                return SentryErrorStats(
                    last_hour_errors=0,
                    last_24h_errors=0,
                    last_3d_errors=0,
                    error_rate_per_hour=0.0,
                    status="unconfigured",
                    last_error_time=None,
                    environment=self.settings.environment,
                    total_events=0,
                    recent_errors=[],
                )

            if not self.log_service:
                logger.warning("LogService가 주입되지 않았습니다. 기본값을 반환합니다.")
                return self._get_default_stats()

            # DB에서 직접 통계 조회
            stats = await self._collect_db_statistics()
            return stats

        except Exception as e:
            logger.error(f"Sentry 에러 통계 조회 실패: {e}")
            return SentryErrorStats(
                last_hour_errors=0,
                last_24h_errors=0,
                last_3d_errors=0,
                error_rate_per_hour=0.0,
                status="error",
                last_error_time=None,
                environment=self.settings.environment,
                total_events=0,
                recent_errors=[],
            )

    async def _collect_db_statistics(self) -> SentryErrorStats:
        """
        LogService를 통해 DB에서 직접 Sentry 에러 통계를 수집합니다.
        """
        try:
            current_time = datetime.utcnow()
            
            # 1시간, 24시간, 3일 전 시간 계산
            hour_ago = current_time - timedelta(hours=1)
            day_ago = current_time - timedelta(days=1) 
            three_days_ago = current_time - timedelta(days=3)
            
            # 각 시간대별 에러 통계 조회
            hour_stats = await self.log_service.get_stats(1)  # 1시간
            day_stats = await self.log_service.get_stats(24)  # 24시간
            three_day_stats = await self.log_service.get_stats(72)  # 3일(72시간)
            
            # 최근 5개 에러 조회 
            recent_errors_filter = LogFilter(
                levels=[LogLevel.ERROR],
                start_time=three_days_ago,
                page_size=5,
                page=1
            )
            recent_logs_response = await self.log_service.search_logs(recent_errors_filter)
            
            # LogEntry를 SentryErrorInfo로 변환
            recent_errors = []
            for log_entry in recent_logs_response.logs:
                error_type = "UnknownError"
                if log_entry.metadata and hasattr(log_entry.metadata, 'error_type') and log_entry.metadata.error_type:
                    error_type = log_entry.metadata.error_type
                elif "Exception" in log_entry.message:
                    error_type = "Exception"
                    
                recent_errors.append(SentryErrorInfo(
                    message=log_entry.message,
                    timestamp=log_entry.timestamp.isoformat() + "Z",
                    error_type=error_type,
                    file_path=None,  # MongoDB 로그에서는 추출하기 어려움
                    line_number=None
                ))
            
            # 마지막 에러 시간 찾기
            last_error_time = None
            if recent_errors:
                last_error_time = recent_errors[0].timestamp  # 최신순으로 정렬되어 있음
            
            logger.info(f"DB 기반 통계 수집 완료: {hour_stats.error_count}개(1h), {day_stats.error_count}개(24h), {three_day_stats.error_count}개(3d)")
            
            return SentryErrorStats(
                last_hour_errors=hour_stats.error_count,
                last_24h_errors=day_stats.error_count,
                last_3d_errors=three_day_stats.error_count,
                error_rate_per_hour=float(hour_stats.error_count),  # 시간당 에러 개수
                status=self._determine_status(hour_stats.error_count),
                last_error_time=last_error_time,
                environment=self.settings.environment,
                total_events=day_stats.total_count,  # 24시간 전체 이벤트 수
                recent_errors=recent_errors
            )
            
        except Exception as e:
            logger.error(f"DB 통계 수집 중 오류: {e}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return self._get_default_stats()

    def _get_default_stats(self) -> SentryErrorStats:
        """기본 에러 통계를 반환합니다."""
        return SentryErrorStats(
            last_hour_errors=0,
            last_24h_errors=0,
            last_3d_errors=0,
            error_rate_per_hour=0.0,
            status="healthy",
            last_error_time=None,
            environment=self.settings.environment,
            total_events=0,
            recent_errors=[],
        )

    def _determine_status(self, hourly_errors: int) -> str:
        """
        시간당 에러 개수를 기반으로 상태를 결정합니다.
        """
        if hourly_errors == 0:
            return "healthy"
        elif hourly_errors <= 5:
            return "warning"
        else:
            return "critical"

    def _determine_service_status(self, is_configured: bool, has_error: bool) -> str:
        """
        서비스 설정 상태와 에러 여부를 기반으로 전체 상태를 결정합니다.
        """
        if not is_configured:
            return "unconfigured"
        elif has_error:
            return "error"
        else:
            return "no_data"  # 설정되어 있지만 데이터 없음

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
                    "status": "unavailable",
                    "message": "Sentry SDK가 설치되지 않았습니다",
                    "configured": False,
                }

            if not self.sentry_configured:
                return {
                    "status": "unconfigured",
                    "message": "Sentry DSN이 설정되지 않았습니다",
                    "configured": False,
                }

            # Sentry 클라이언트 상태 확인
            current_hub = sentry_sdk.Hub.current
            client = current_hub.client

            if client and client.dsn:
                return {
                    "status": "healthy",
                    "message": "Sentry 연결 정상",
                    "configured": True,
                    "dsn_configured": True,
                    "environment": self.settings.sentry_environment or "default",
                }
            else:
                return {
                    "status": "error",
                    "message": "Sentry 클라이언트 초기화 실패",
                    "configured": False,
                }

        except Exception as e:
            logger.error(f"Sentry 상태 확인 실패: {e}")
            return {
                "status": "error",
                "message": f"Sentry 상태 확인 중 오류: {str(e)}",
                "configured": False,
            }

    async def capture_test_error(self) -> Dict[str, Any]:
        """
        테스트용 에러를 Sentry와 LogService에 전송합니다.
        """
        try:
            if not self.sentry_configured:
                return {"success": False, "message": "Sentry가 설정되지 않았습니다"}

            # 테스트 에러 생성 및 전송
            try:
                raise ValueError("테스트 에러 - 모니터링 시스템에서 생성됨")
            except ValueError as e:
                # capture_application_error를 통해 통합 전송
                result = await self.capture_application_error(e, {
                    "test_context": "capture_test_error",
                    "test_type": "manual_test"
                })
                
                if result["success"]:
                    return {
                        "success": True,
                        "message": "테스트 에러가 Sentry와 LogService에 전송되었습니다",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    return result

        except Exception as e:
            logger.error(f"테스트 에러 전송 실패: {e}")
            return {"success": False, "message": f"테스트 에러 전송 실패: {str(e)}"}


    async def capture_application_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        실제 애플리케이션 에러를 Sentry와 LogService에 동시 전송
        """
        try:
            if not self.sentry_configured:
                return {"success": False, "message": "Sentry가 설정되지 않았습니다"}

            # 컨텍스트 정보 설정
            if context:
                with sentry_sdk.configure_scope() as scope:
                    for key, value in context.items():
                        scope.set_extra(key, value)

            # Sentry에 에러 전송
            sentry_sdk.capture_exception(error)
            
            # LogService에도 동시 기록 (DB 기반 통합 관리)
            if self.log_service:
                import traceback
                tb = traceback.extract_tb(error.__traceback__)
                file_path = tb[-1].filename if tb else None
                line_number = tb[-1].lineno if tb else None
                
                # LogEntry 생성하여 DB에 저장
                log_context = LogContext(
                    infrastructure="sentry",
                    **context if context else {}
                )
                
                log_metadata = LogMetadata(
                    error_type=error.__class__.__name__,
                    tags=["sentry", "application_error"],
                    custom={
                        "file_path": file_path,
                        "line_number": line_number,
                        "error_class": error.__class__.__name__
                    }
                )
                
                await self.log_service.log_internal(
                    level=LogLevel.ERROR,
                    service=LogServiceType.API,
                    message=f"[Sentry] {str(error)}",
                    context=log_context,
                    metadata=log_metadata,
                    stack_trace=traceback.format_exc(),
                    timestamp=datetime.utcnow()
                )
                
                logger.info(f"✅ Sentry 에러가 LogService에도 기록됨: {error.__class__.__name__}")

            return {
                "success": True,
                "message": "애플리케이션 에러가 Sentry와 LogService에 전송되었습니다",
                "error_type": error.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"애플리케이션 에러 전송 실패: {e}")
            return {"success": False, "message": f"에러 전송 실패: {str(e)}"}

    async def capture_multiple_test_errors(self, count: int = 3) -> Dict[str, Any]:
        """
        다양한 타입의 테스트 에러를 생성하여 통계 테스트
        """
        try:
            if not self.sentry_configured:
                return {"success": False, "message": "Sentry가 설정되지 않았습니다"}

            errors_sent = []
            
            # 다양한 타입의 테스트 에러 생성
            test_errors = [
                (ValueError, "테스트 ValueError - 잘못된 값 입력"),
                (TypeError, "테스트 TypeError - 타입 불일치"),
                (KeyError, "테스트 KeyError - 존재하지 않는 키 접근"),
                (IndexError, "테스트 IndexError - 인덱스 범위 초과"),
                (RuntimeError, "테스트 RuntimeError - 런타임 오류")
            ]
            
            for i in range(min(count, len(test_errors))):
                error_class, error_message = test_errors[i]
                
                try:
                    raise error_class(error_message)
                except error_class as e:
                    # Sentry에 전송
                    with sentry_sdk.configure_scope() as scope:
                        scope.set_tag("test_error", True)
                        scope.set_extra("test_sequence", i + 1)
                    
                    result = await self.capture_application_error(e, {
                        "test_context": "multiple_test_errors",
                        "error_sequence": i + 1
                    })
                    
                    if result["success"]:
                        errors_sent.append({
                            "type": error_class.__name__,
                            "message": error_message,
                            "sequence": i + 1
                        })

            return {
                "success": True,
                "message": f"{len(errors_sent)}개의 테스트 에러가 전송되었습니다",
                "errors_sent": errors_sent,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"다중 테스트 에러 전송 실패: {e}")
            return {"success": False, "message": f"다중 테스트 에러 전송 실패: {str(e)}"}

    def __del__(self):
        """리소스 정리"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)
