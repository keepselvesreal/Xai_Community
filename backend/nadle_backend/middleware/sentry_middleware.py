"""
Sentry 미들웨어

요청별 컨텍스트 설정, 성능 추적, 사용자 식별
"""

import time
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from sentry_sdk import set_user, set_tag, set_context

from nadle_backend.monitoring.sentry_config import set_user_context, set_request_context

logger = logging.getLogger(__name__)


class SentryRequestMiddleware(BaseHTTPMiddleware):
    """
    Sentry 요청 컨텍스트 미들웨어

    각 요청에 대해 Sentry 컨텍스트를 설정합니다.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 및 Sentry 컨텍스트 설정

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response: HTTP 응답
        """
        start_time = time.time()

        # 요청 컨텍스트 설정
        set_request_context(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            client_ip=request.client.host if request.client else None,
        )

        # 요청 ID 설정 (있다면)
        request_id = request.headers.get("X-Request-ID")
        if request_id:
            set_tag("request.id", request_id)

        try:
            # 다음 미들웨어/핸들러 호출
            response = await call_next(request)

            # 응답 시간 계산
            duration = time.time() - start_time
            set_tag("request.duration", f"{duration:.3f}s")
            set_tag("response.status_code", response.status_code)

            return response

        except Exception as e:
            # 에러 발생 시 추가 컨텍스트 설정
            duration = time.time() - start_time
            set_tag("request.duration", f"{duration:.3f}s")
            set_tag("error.occurred", True)
            
            # 네트워크 에러 타입 분류 및 태그 추가
            error_category = self._categorize_error(e)
            set_tag("error.category", error_category)
            set_tag("error.type", type(e).__name__)

            # 에러를 Sentry에 자동 전송 (FastAPI integration에서 처리)
            logger.error(f"Request failed: {request.method} {request.url} - {e}")
            
            # LogService에 직접 에러 기록 (통합 관리)
            try:
                from ..core.logging import LogLevel, LogServiceType, LogSource, LogContext, LogMetadata
                from ..logging.dependencies import get_log_repository, get_cache_service
                from ..logging.services.log_service import LogService
                from ..database.connection import get_database
                import traceback
                
                # LogService 인스턴스 생성 (미들웨어에서는 직접 생성)
                database = await get_database()
                
                # 간단한 LogRepository 생성
                from ..logging.repositories.mongo_log_repository import MongoLogRepository
                log_repository = MongoLogRepository(database)
                
                # LogService 생성
                log_service = LogService(log_repository=log_repository)
                
                # 스택 트레이스에서 파일 정보 추출
                tb = traceback.extract_tb(e.__traceback__)
                file_path = tb[-1].filename if tb else None
                line_number = tb[-1].lineno if tb else None
                
                # LogEntry 생성하여 DB에 저장
                log_context = LogContext(
                    endpoint=str(request.url),
                    method=request.method,
                    ip_address=request.client.host if request.client else None,
                    infrastructure="api_middleware"
                )
                
                log_metadata = LogMetadata(
                    error_type=e.__class__.__name__,
                    tags=["api_error", "middleware", "sentry", error_category],
                    custom={
                        "file_path": file_path,
                        "line_number": line_number,
                        "request_method": request.method,
                        "request_url": str(request.url),
                        "error_category": error_category,
                        "is_network_error": error_category in ["network", "timeout", "connection"]
                    }
                )
                
                await log_service.log_internal(
                    level=LogLevel.ERROR,
                    service=LogServiceType.API,
                    message=f"[API] {request.method} {request.url} - {str(e)}",
                    context=log_context,
                    metadata=log_metadata,
                    stack_trace=traceback.format_exc(),
                    timestamp=datetime.utcnow()
                )
                
                logger.info(f"✅ API 에러가 LogService에 기록됨: {e.__class__.__name__}")
                
            except Exception as record_error:
                logger.warning(f"⚠️ API 에러 LogService 기록 실패: {record_error}")
            
            raise


class SentryUserMiddleware(BaseHTTPMiddleware):
    """
    Sentry 사용자 식별 미들웨어

    JWT 토큰으로부터 사용자 정보를 추출하여 Sentry에 설정합니다.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        사용자 식별 및 Sentry 사용자 컨텍스트 설정

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어/핸들러

        Returns:
            Response: HTTP 응답
        """
        # Authorization 헤더에서 JWT 토큰 추출
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]

                # JWT 토큰 디코딩 (실제 구현에서는 JWT 유틸리티 사용)
                # 현재는 모킹을 위해 기본 구현
                user_info = self._decode_jwt_token(token)

                if user_info:
                    # Sentry에 사용자 정보 설정
                    set_user_context(
                        user_id=user_info.get("sub") or user_info.get("user_id"),
                        email=user_info.get("email"),
                    )

                    # 요청 객체에도 사용자 정보 저장
                    request.state.user = user_info

            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {e}")

        return await call_next(request)

    def _decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWT 토큰 디코딩 (모킹용 구현)

        Args:
            token: JWT 토큰

        Returns:
            Optional[Dict[str, Any]]: 사용자 정보
        """
        try:
            # 실제 구현에서는 nadle_backend.utils.jwt.decode_token 사용
            from nadle_backend.utils.jwt import decode_token

            return decode_token(token)
        except ImportError:
            # 테스트용 기본 구현
            return None

    def _categorize_error(self, exception: Exception) -> str:
        """
        예외를 카테고리별로 분류
        
        Args:
            exception: 발생한 예외
            
        Returns:
            str: 에러 카테고리
        """
        exception_name = exception.__class__.__name__.lower()
        exception_message = str(exception).lower()
        
        # 네트워크 관련 에러
        if any(keyword in exception_name for keyword in [
            "connection", "network", "timeout", "socket"
        ]):
            return "network"
        
        # 타임아웃 에러
        if any(keyword in exception_name for keyword in [
            "timeout", "asyncio.timeout"
        ]) or "timeout" in exception_message:
            return "timeout"
        
        # 연결 에러
        if any(keyword in exception_name for keyword in [
            "connection", "connect", "disconnect"
        ]):
            return "connection"
        
        # 인증/권한 에러
        if any(keyword in exception_name for keyword in [
            "auth", "permission", "forbidden", "unauthorized"
        ]):
            return "auth"
        
        # 검증 에러
        if any(keyword in exception_name for keyword in [
            "validation", "value", "type", "attribute"
        ]):
            return "validation"
        
        # HTTP 관련 에러
        if any(keyword in exception_name for keyword in [
            "http", "status", "response"
        ]):
            return "http"
        
        # 데이터베이스 에러
        if any(keyword in exception_name for keyword in [
            "mongo", "database", "db", "collection"
        ]):
            return "database"
        
        # 기타
        return "other"


def track_performance(operation_name: str):
    """
    성능 추적 데코레이터

    Args:
        operation_name: 작업 이름
    """

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            with sentry_sdk.start_transaction(
                op="function", name=operation_name
            ) as transaction:
                try:
                    result = await func(*args, **kwargs)
                    transaction.set_status("ok")
                    return result
                except Exception as e:
                    transaction.set_status("internal_error")
                    transaction.set_data("error", str(e))
                    raise
                finally:
                    duration = time.time() - start_time
                    transaction.set_data("duration", duration)

        return wrapper

    return decorator


@asynccontextmanager
async def async_sentry_context(user_id: Optional[str] = None, **context_data):
    """
    비동기 컨텍스트에서 Sentry 정보 보존

    Args:
        user_id: 사용자 ID
        **context_data: 추가 컨텍스트 데이터
    """
    # Sentry Hub를 사용한 격리된 스코프 생성
    with sentry_sdk.push_scope() as scope:
        try:
            if user_id:
                sentry_sdk.set_user({"id": user_id})

            for key, value in context_data.items():
                sentry_sdk.set_extra(key, value)

            yield scope
        finally:
            # push_scope 컨텍스트에서 자동으로 정리됨
            pass
