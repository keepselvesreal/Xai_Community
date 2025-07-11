"""
Sentry 설정 및 연동 모듈

에러 추적, 성능 모니터링, 사용자 컨텍스트 관리
"""
import os
import logging
from typing import Optional, Dict, Any, Callable
from urllib.parse import urlparse

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def get_sentry_config() -> Dict[str, Any]:
    """
    환경변수로부터 Sentry 설정을 로드합니다.
    
    Returns:
        Dict[str, Any]: Sentry 설정 딕셔너리
    """
    return {
        'dsn': os.getenv('SENTRY_DSN'),
        'environment': os.getenv('SENTRY_ENVIRONMENT', 'development'),
        'traces_sample_rate': float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0')),
        'send_default_pii': os.getenv('SENTRY_SEND_DEFAULT_PII', 'true').lower() == 'true',
        'debug': os.getenv('SENTRY_DEBUG', 'false').lower() == 'true'
    }


def validate_dsn(dsn: Optional[str]) -> bool:
    """
    Sentry DSN 형식을 검증합니다.
    
    Args:
        dsn: Sentry DSN 문자열
        
    Returns:
        bool: 유효한 DSN인지 여부
        
    Raises:
        ValueError: 잘못된 DSN 형식인 경우
    """
    if not dsn:
        return False
    
    try:
        parsed = urlparse(dsn)
        if not parsed.scheme or not parsed.hostname:
            raise ValueError("Invalid Sentry DSN format")
        return True
    except Exception:
        raise ValueError("Invalid Sentry DSN format")


def sentry_before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sentry 이벤트 전송 전 필터링 함수
    
    Args:
        event: Sentry 이벤트 데이터
        hint: 이벤트 힌트 정보
        
    Returns:
        Optional[Dict[str, Any]]: 전송할 이벤트 (None이면 전송 안함)
    """
    # HTTP 예외 필터링 (404, 403 등은 Sentry에 보내지 않음)
    if event.get('exception'):
        for exception_value in event['exception'].get('values', []):
            exception_type = exception_value.get('type', '')
            exception_message = exception_value.get('value', '')
            
            # HTTPException 필터링
            if exception_type == 'HTTPException':
                if '404' in exception_message or '403' in exception_message:
                    return None
    
    # 개발 환경에서는 모든 이벤트 전송
    if event.get('environment') == 'development':
        logger.debug(f"Sentry event: {event.get('message', 'No message')}")
    
    return event


def init_sentry(dsn: Optional[str] = None, environment: str = "development", **kwargs) -> None:
    """
    Sentry SDK를 초기화합니다.
    
    Args:
        dsn: Sentry DSN
        environment: 환경 (development, staging, production)
        **kwargs: 추가 Sentry 설정
    """
    if not dsn:
        logger.info("Sentry DSN not provided, skipping Sentry initialization")
        return
    
    # DSN 검증
    validate_dsn(dsn)
    
    # 기본 설정
    config = {
        'dsn': dsn,
        'environment': environment,
        'traces_sample_rate': kwargs.get('traces_sample_rate', 1.0),
        'send_default_pii': kwargs.get('send_default_pii', True),
        'before_send': sentry_before_send,
        'integrations': [
            FastApiIntegration(),
            AsyncioIntegration(),
        ],
        'debug': kwargs.get('debug', False)
    }
    
    # Sentry 초기화
    sentry_sdk.init(**config)
    
    logger.info(f"Sentry initialized for environment: {environment}")


def init_sentry_for_fastapi(app: FastAPI, dsn: Optional[str] = None, environment: str = "development") -> None:
    """
    FastAPI 앱을 위한 Sentry 초기화
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
        dsn: Sentry DSN
        environment: 환경
    """
    if not dsn:
        logger.info("Sentry DSN not provided for FastAPI, skipping initialization")
        return
    
    # 기본 Sentry 초기화
    init_sentry(dsn=dsn, environment=environment)
    
    # FastAPI 앱에 Sentry 정보 추가
    app.state.sentry_initialized = True
    app.state.sentry_environment = environment
    
    logger.info(f"Sentry initialized for FastAPI app in {environment} environment")


def capture_error(exception: Exception, user_id: Optional[str] = None, **extra_context) -> None:
    """
    Sentry에 에러를 수동으로 캡처합니다.
    
    Args:
        exception: 캡처할 예외
        user_id: 사용자 ID (선택적)
        **extra_context: 추가 컨텍스트 정보
    """
    # 현재 스코프에 정보 설정
    if user_id:
        sentry_sdk.set_user({"id": user_id})
    
    # 추가 컨텍스트 설정
    for key, value in extra_context.items():
        sentry_sdk.set_extra(key, value)
    
    # 에러 캡처
    sentry_sdk.capture_exception(exception)
    
    logger.error(f"Error captured in Sentry: {exception}")


def set_user_context(user_id: str, email: Optional[str] = None, **extra_data) -> None:
    """
    Sentry에 사용자 컨텍스트를 설정합니다.
    
    Args:
        user_id: 사용자 ID
        email: 사용자 이메일
        **extra_data: 추가 사용자 데이터
    """
    user_data = {"id": user_id}
    
    if email:
        user_data["email"] = email
    
    user_data.update(extra_data)
    
    sentry_sdk.set_user(user_data)
    sentry_sdk.set_tag("user.id", user_id)
    
    logger.debug(f"Sentry user context set for user: {user_id}")


def set_request_context(method: str, url: str, **extra_data) -> None:
    """
    Sentry에 요청 컨텍스트를 설정합니다.
    
    Args:
        method: HTTP 메서드
        url: 요청 URL
        **extra_data: 추가 요청 데이터
    """
    sentry_sdk.set_context("request", {
        "method": method,
        "url": url,
        **extra_data
    })
    
    sentry_sdk.set_tag("request.method", method)