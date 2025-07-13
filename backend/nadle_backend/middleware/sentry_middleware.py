"""
Sentry 미들웨어

요청별 컨텍스트 설정, 성능 추적, 사용자 식별
"""
import time
import logging
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
            client_ip=request.client.host if request.client else None
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
            
            # 에러를 Sentry에 자동 전송 (FastAPI integration에서 처리)
            logger.error(f"Request failed: {request.method} {request.url} - {e}")
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
                        email=user_info.get("email")
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
                op="function",
                name=operation_name
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