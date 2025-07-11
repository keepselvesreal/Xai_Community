"""
구조화된 로깅 시스템

Sentry 대체용 자체 구조화된 로깅 및 에러 추적 시스템
"""
import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

# Google Cloud Logging 
try:
    import google.cloud.logging
    from google.cloud import logging as gcp_logging
    GCP_LOGGING_AVAILABLE = True
except ImportError:
    GCP_LOGGING_AVAILABLE = False

# Discord 알림용
import asyncio
import aiohttp
from nadle_backend.config import settings


class LogLevel(Enum):
    """로그 레벨 열거형"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorType(Enum):
    """에러 유형 분류"""
    SYSTEM_ERROR = "system_error"
    BUSINESS_ERROR = "business_error"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    EXTERNAL_API_ERROR = "external_api_error"
    DATABASE_ERROR = "database_error"
    PERFORMANCE_ERROR = "performance_error"


@dataclass
class LogContext:
    """로그 컨텍스트 정보"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    environment: Optional[str] = None


@dataclass
class ErrorInfo:
    """에러 정보"""
    error_type: ErrorType
    message: str
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceInfo:
    """성능 정보"""
    duration: float
    operation: str
    endpoint: Optional[str] = None
    slow_query: bool = False
    memory_usage: Optional[int] = None


class StructuredLogger:
    """구조화된 로거 클래스"""
    
    def __init__(self, name: str = "nadle_backend"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.gcp_client = None
        self.discord_webhook_url = getattr(settings, 'discord_webhook_url', None)
        
        # 로거 설정
        self._setup_logger()
        
        # Google Cloud Logging 초기화
        if GCP_LOGGING_AVAILABLE:
            self._setup_gcp_logging()
    
    def _setup_logger(self):
        """로거 기본 설정"""
        self.logger.setLevel(logging.INFO)
        
        # 핸들러가 이미 있으면 제거
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # JSON 형식 포맷터
        formatter = JsonFormatter()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # 파일 핸들러 추가
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # 에러 전용 파일 핸들러
        error_handler = logging.FileHandler(log_dir / "errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(error_handler)
    
    def _setup_gcp_logging(self):
        """Google Cloud Logging 설정"""
        try:
            self.gcp_client = gcp_logging.Client()
            self.gcp_client.setup_logging()
            self.logger.info("Google Cloud Logging initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Google Cloud Logging: {e}")
    
    def log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        error_info: Optional[ErrorInfo] = None,
        performance_info: Optional[PerformanceInfo] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """구조화된 로그 기록"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "message": message,
            "service": "nadle_backend",
            "version": "1.0.0"
        }
        
        if context:
            log_entry["context"] = asdict(context)
        
        if error_info:
            log_entry["error"] = asdict(error_info)
        
        if performance_info:
            log_entry["performance"] = asdict(performance_info)
        
        if additional_data:
            log_entry["additional_data"] = additional_data
        
        # 로그 레벨에 따른 기록
        if level == LogLevel.DEBUG:
            self.logger.debug(json.dumps(log_entry, ensure_ascii=False))
        elif level == LogLevel.INFO:
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        elif level == LogLevel.WARNING:
            self.logger.warning(json.dumps(log_entry, ensure_ascii=False))
        elif level == LogLevel.ERROR:
            self.logger.error(json.dumps(log_entry, ensure_ascii=False))
            # 에러 시 Discord 알림
            if self.discord_webhook_url:
                asyncio.create_task(self._send_discord_notification(log_entry))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(json.dumps(log_entry, ensure_ascii=False))
            # 치명적 에러 시 Discord 알림
            if self.discord_webhook_url:
                asyncio.create_task(self._send_discord_notification(log_entry))
    
    def info(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """INFO 레벨 로그"""
        self.log(LogLevel.INFO, message, context, additional_data=kwargs)
    
    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """WARNING 레벨 로그"""
        self.log(LogLevel.WARNING, message, context, additional_data=kwargs)
    
    def error(
        self,
        message: str,
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        exception: Optional[Exception] = None,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """ERROR 레벨 로그"""
        error_info = ErrorInfo(
            error_type=error_type,
            message=message,
            stack_trace=traceback.format_exc() if exception else None,
            additional_data=kwargs
        )
        
        self.log(LogLevel.ERROR, message, context, error_info=error_info)
    
    def critical(
        self,
        message: str,
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        exception: Optional[Exception] = None,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """CRITICAL 레벨 로그"""
        error_info = ErrorInfo(
            error_type=error_type,
            message=message,
            stack_trace=traceback.format_exc() if exception else None,
            additional_data=kwargs
        )
        
        self.log(LogLevel.CRITICAL, message, context, error_info=error_info)
    
    def performance(
        self,
        operation: str,
        duration: float,
        endpoint: Optional[str] = None,
        context: Optional[LogContext] = None,
        **kwargs
    ):
        """성능 로그"""
        performance_info = PerformanceInfo(
            duration=duration,
            operation=operation,
            endpoint=endpoint,
            slow_query=duration > 1.0,  # 1초 이상이면 느린 쿼리
            **kwargs
        )
        
        level = LogLevel.WARNING if duration > 2.0 else LogLevel.INFO
        self.log(level, f"Performance: {operation}", context, performance_info=performance_info)
    
    async def _send_discord_notification(self, log_entry: Dict[str, Any]):
        """Discord 알림 전송"""
        if not self.discord_webhook_url:
            return
        
        try:
            # Discord 임베드 메시지 생성
            embed = {
                "title": "🚨 Backend Error Alert",
                "description": log_entry["message"],
                "color": 0xFF0000,  # 빨간색
                "timestamp": log_entry["timestamp"],
                "fields": []
            }
            
            # 에러 정보 추가
            if "error" in log_entry:
                error_info = log_entry["error"]
                embed["fields"].append({
                    "name": "Error Type",
                    "value": error_info.get("error_type", "Unknown"),
                    "inline": True
                })
                
                if error_info.get("stack_trace"):
                    # 스택 트레이스는 길어질 수 있으므로 축약
                    stack_trace = error_info["stack_trace"][:1000] + "..." if len(error_info["stack_trace"]) > 1000 else error_info["stack_trace"]
                    embed["fields"].append({
                        "name": "Stack Trace",
                        "value": f"```{stack_trace}```",
                        "inline": False
                    })
            
            # 컨텍스트 정보 추가
            if "context" in log_entry:
                context_info = log_entry["context"]
                if context_info.get("endpoint"):
                    embed["fields"].append({
                        "name": "Endpoint",
                        "value": f"{context_info.get('method', 'GET')} {context_info['endpoint']}",
                        "inline": True
                    })
                
                if context_info.get("user_id"):
                    embed["fields"].append({
                        "name": "User ID",
                        "value": context_info["user_id"],
                        "inline": True
                    })
            
            # 환경 정보 추가
            embed["fields"].append({
                "name": "Environment",
                "value": settings.environment,
                "inline": True
            })
            
            # Discord 웹훅으로 전송
            payload = {
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 204:
                        print("Discord notification sent successfully")
                    else:
                        print(f"Failed to send Discord notification: {response.status}")
        
        except Exception as e:
            # Discord 알림 실패해도 메인 로깅에는 영향 없음
            print(f"Failed to send Discord notification: {e}")


class JsonFormatter(logging.Formatter):
    """JSON 형식 로그 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 변환"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 추가 속성 추가
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


# 전역 로거 인스턴스
structured_logger = StructuredLogger()


# 편의 함수들
def log_info(message: str, context: Optional[LogContext] = None, **kwargs):
    """INFO 로그 기록"""
    structured_logger.info(message, context, **kwargs)


def log_warning(message: str, context: Optional[LogContext] = None, **kwargs):
    """WARNING 로그 기록"""
    structured_logger.warning(message, context, **kwargs)


def log_error(
    message: str,
    error_type: ErrorType = ErrorType.SYSTEM_ERROR,
    exception: Optional[Exception] = None,
    context: Optional[LogContext] = None,
    **kwargs
):
    """ERROR 로그 기록"""
    structured_logger.error(message, error_type, exception, context, **kwargs)


def log_performance(
    operation: str,
    duration: float,
    endpoint: Optional[str] = None,
    context: Optional[LogContext] = None,
    **kwargs
):
    """성능 로그 기록"""
    structured_logger.performance(operation, duration, endpoint, context, **kwargs)


def get_request_context(request) -> LogContext:
    """FastAPI Request 객체로부터 LogContext 생성"""
    return LogContext(
        request_id=request.headers.get("X-Request-ID"),
        endpoint=str(request.url.path),
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        environment=settings.environment
    )