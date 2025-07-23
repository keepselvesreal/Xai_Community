"""
Sentry 로그 어댑터 구현

2025-07-23 작업 버전: v1.0
주요 컴포넌트:
- SentryLogAdapter: ExternalLogAdapterInterface 구현
- collect_logs: Sentry에서 에러 데이터 수집하여 LogEntry로 변환
- test_connection: Sentry 연결 상태 확인
- _convert_sentry_error_to_log_entry: Sentry 에러를 LogEntry로 변환

관련 파일:
- ../services/sentry_monitoring_service.py: SentryMonitoringService와 연계
- ../core/logging/interfaces.py: ExternalLogAdapterInterface 정의
- ./external_log_collector.py: 외부 로그 수집 서비스에서 사용
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from ...core.logging import (
    ExternalLogAdapterInterface,
    LogEntry,
    LogLevel,
    LogServiceType,
    LogSource,
    LogContext,
    LogMetadata,
    AdapterError,
)

logger = logging.getLogger(__name__)


class SentryLogAdapter(ExternalLogAdapterInterface):
    """
    Sentry 에러 로그를 수집하는 어댑터
    
    SentryMonitoringService와 연계하여 Sentry 에러 데이터를 
    표준 LogEntry 형식으로 변환하여 수집합니다.
    """
    
    # 클래스 속성으로 service_name 정의
    service_name: str = "sentry"

    def __init__(self, sentry_monitoring_service=None, use_mock: bool = False):
        """
        Sentry 로그 어댑터 초기화
        
        Args:
            sentry_monitoring_service: SentryMonitoringService 인스턴스
            use_mock: 모의 데이터 사용 여부
        """
        self.sentry_monitoring_service = sentry_monitoring_service
        self.use_mock = use_mock or not SENTRY_AVAILABLE
        
        if self.use_mock:
            logger.info("Sentry adapter initialized with mock data")
        else:
            logger.info("Sentry adapter initialized with real Sentry connection")

    async def collect_logs(self, hours: int = 1) -> List[LogEntry]:
        """
        Sentry에서 에러 로그를 수집합니다.
        
        Args:
            hours: 수집할 시간 범위 (시간 단위)
            
        Returns:
            LogEntry 리스트
            
        Raises:
            AdapterError: 수집 실패 시
        """
        try:
            if self.use_mock:
                return await self._collect_mock_logs(hours)
            
            if not self.sentry_monitoring_service:
                logger.warning("SentryMonitoringService가 제공되지 않았습니다. 빈 리스트 반환")
                return []
                
            # SentryMonitoringService를 통해 에러 통계 수집
            error_stats = await self.sentry_monitoring_service.get_error_statistics()
            
            # SentryErrorInfo를 LogEntry로 변환
            log_entries = []
            for sentry_error in error_stats.recent_errors:
                log_entry = self._convert_sentry_error_to_log_entry(sentry_error)
                log_entries.append(log_entry)
                
            logger.info(f"Sentry에서 {len(log_entries)}개 에러 로그 수집 완료")
            return log_entries
            
        except Exception as e:
            logger.error(f"Sentry 로그 수집 실패: {e}")
            raise AdapterError("sentry", f"Log collection failed: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Sentry 연결 상태를 확인합니다.
        
        Returns:
            연결 성공 여부
        """
        try:
            if self.use_mock:
                return True
                
            if not SENTRY_AVAILABLE:
                logger.warning("Sentry SDK가 설치되지 않았습니다")
                return False
                
            if not self.sentry_monitoring_service:
                logger.warning("SentryMonitoringService가 제공되지 않았습니다")
                return False
                
            # Sentry 상태 확인
            health_status = await self.sentry_monitoring_service.check_sentry_health()
            is_healthy = health_status.get("status") in ["healthy", "no_data"]
            
            logger.info(f"Sentry 연결 테스트 결과: {is_healthy}")
            return is_healthy
            
        except Exception as e:
            logger.error(f"Sentry 연결 테스트 실패: {e}")
            return False

    def _convert_sentry_error_to_log_entry(self, sentry_error) -> LogEntry:
        """
        SentryErrorInfo를 LogEntry로 변환합니다.
        
        Args:
            sentry_error: SentryErrorInfo 인스턴스
            
        Returns:
            변환된 LogEntry
        """
        try:
            # 타임스탬프 파싱
            timestamp_str = sentry_error.timestamp
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1]
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # LogContext 생성
            log_context = LogContext(
                infrastructure="sentry",
                instance_id="sentry-monitor"
            )
            
            # LogMetadata 생성
            log_metadata = LogMetadata(
                error_type=sentry_error.error_type,
                tags=["sentry", "external", "error"],
                custom={
                    "file_path": sentry_error.file_path,
                    "line_number": sentry_error.line_number,
                    "source": "sentry_adapter"
                }
            )
            
            # LogEntry 생성
            log_entry = LogEntry(
                timestamp=timestamp,
                level=LogLevel.ERROR,
                service=LogServiceType.API,  # Sentry는 대부분 API 에러
                source=LogSource.EXTERNAL,
                message=f"[Sentry] {sentry_error.message}",
                context=log_context,
                metadata=log_metadata
            )
            
            return log_entry
            
        except Exception as e:
            logger.error(f"SentryError → LogEntry 변환 실패: {e}")
            # 기본 LogEntry 반환
            return LogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.ERROR,
                service=LogServiceType.API,
                source=LogSource.EXTERNAL,
                message=f"[Sentry] Error conversion failed: {str(sentry_error)}",
                context=LogContext(infrastructure="sentry"),
                metadata=LogMetadata(
                    error_type="ConversionError",
                    tags=["sentry", "external", "conversion_error"]
                )
            )

    async def _collect_mock_logs(self, hours: int) -> List[LogEntry]:
        """
        개발/테스트용 모의 Sentry 로그를 생성합니다.
        """
        mock_logs = []
        current_time = datetime.utcnow()
        
        # 모의 에러 데이터 생성
        mock_errors = [
            ("ValueError", "Invalid input parameter for user authentication"),
            ("TypeError", "Expected string but got None in request handler"),
            ("KeyError", "Missing required field 'user_id' in request"),
            ("RuntimeError", "Database connection timeout in user service"),
            ("AttributeError", "'NoneType' object has no attribute 'id'")
        ]
        
        for i, (error_type, message) in enumerate(mock_errors):
            # 지난 시간 범위 내의 랜덤 시간 생성
            error_time = current_time - timedelta(
                minutes=i * 15,  # 15분 간격으로 에러 생성
                seconds=i * 30
            )
            
            log_entry = LogEntry(
                timestamp=error_time,
                level=LogLevel.ERROR,
                service=LogServiceType.API,
                source=LogSource.EXTERNAL,
                message=f"[Sentry Mock] {message}",
                context=LogContext(
                    infrastructure="sentry",
                    instance_id="mock-sentry"
                ),
                metadata=LogMetadata(
                    error_type=error_type,
                    tags=["sentry", "external", "mock"],
                    custom={
                        "mock_data": True,
                        "sequence": i + 1
                    }
                )
            )
            
            mock_logs.append(log_entry)
            
        logger.info(f"모의 Sentry 로그 {len(mock_logs)}개 생성")
        return mock_logs