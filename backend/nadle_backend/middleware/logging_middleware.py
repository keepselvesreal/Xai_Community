"""
구조화된 로깅 미들웨어

Sentry 대체용 요청 추적 및 에러 로깅 미들웨어
"""
import time
import logging
from typing import Callable, Optional, Dict, Any
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from nadle_backend.logging.structured_logger import (
    structured_logger,
    LogContext,
    ErrorType,
    get_request_context,
    log_info,
    log_error,
    log_performance
)

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    구조화된 로깅 미들웨어
    
    모든 요청에 대해 구조화된 로깅을 수행합니다.
    """
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 및 로깅
        """
        # 요청 ID 생성
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # 시작 시간 기록
        start_time = time.time()
        
        # 요청 컨텍스트 생성
        context = get_request_context(request)
        context.request_id = request_id
        
        # 사용자 정보 추가 (JWT 토큰이 있는 경우)
        user_info = await self._extract_user_info(request)
        if user_info:
            context.user_id = user_info.get("user_id")
            context.session_id = user_info.get("session_id")
        
        # 요청 시작 로깅
        if self.log_requests:
            log_info(
                f"Request started: {request.method} {request.url.path}",
                context=context,
                query_params=dict(request.query_params),
                headers=dict(request.headers)
            )
        
        try:
            # 다음 미들웨어/핸들러 호출
            response = await call_next(request)
            
            # 응답 시간 계산
            duration = time.time() - start_time
            
            # 성공 응답 로깅
            if self.log_responses:
                log_info(
                    f"Request completed: {request.method} {request.url.path}",
                    context=context,
                    status_code=response.status_code,
                    duration=duration
                )
            
            # 성능 로깅 (느린 요청)
            if duration > 1.0:  # 1초 이상
                log_performance(
                    operation=f"{request.method} {request.url.path}",
                    duration=duration,
                    endpoint=request.url.path,
                    context=context,
                    status_code=response.status_code
                )
            
            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # 에러 발생 시간 계산
            duration = time.time() - start_time
            
            # 에러 유형 분류
            error_type = self._classify_error(e)
            
            # 에러 로깅
            log_error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                error_type=error_type,
                exception=e,
                context=context,
                duration=duration,
                request_body=await self._get_request_body(request)
            )
            
            # 에러 재발생 (FastAPI가 처리하도록)
            raise
    
    async def _extract_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """JWT 토큰에서 사용자 정보 추출"""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        try:
            token = auth_header.split(" ")[1]
            
            # JWT 토큰 디코딩
            from nadle_backend.utils.jwt import decode_token
            return decode_token(token)
        except Exception as e:
            logger.debug(f"Failed to decode JWT token: {e}")
            return None
    
    def _classify_error(self, exception: Exception) -> ErrorType:
        """예외 유형에 따른 에러 타입 분류"""
        exception_name = exception.__class__.__name__
        
        if "HTTPException" in exception_name:
            # HTTP 예외는 비즈니스 에러로 분류
            return ErrorType.BUSINESS_ERROR
        elif "ValidationError" in exception_name:
            return ErrorType.VALIDATION_ERROR
        elif "Unauthorized" in exception_name or "401" in str(exception):
            return ErrorType.AUTHENTICATION_ERROR
        elif "Forbidden" in exception_name or "403" in str(exception):
            return ErrorType.AUTHORIZATION_ERROR
        elif "ConnectionError" in exception_name or "TimeoutError" in exception_name:
            return ErrorType.EXTERNAL_API_ERROR
        elif "DatabaseError" in exception_name or "MongoDB" in str(exception):
            return ErrorType.DATABASE_ERROR
        else:
            return ErrorType.SYSTEM_ERROR
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """요청 본문 추출 (에러 로깅용)"""
        try:
            if hasattr(request, '_body'):
                return request._body.decode('utf-8')
            return None
        except Exception:
            return None


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    에러 추적 미들웨어
    
    심각한 에러를 추적하고 알림을 전송합니다.
    """
    
    def __init__(self, app, track_4xx: bool = False, track_5xx: bool = True):
        super().__init__(app)
        self.track_4xx = track_4xx
        self.track_5xx = track_5xx
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """에러 추적 및 알림"""
        try:
            response = await call_next(request)
            
            # 4xx 에러 추적
            if self.track_4xx and 400 <= response.status_code < 500:
                context = get_request_context(request)
                context.request_id = getattr(request.state, 'request_id', None)
                
                log_error(
                    f"Client error: {response.status_code} {request.method} {request.url.path}",
                    error_type=ErrorType.BUSINESS_ERROR,
                    context=context,
                    status_code=response.status_code
                )
            
            # 5xx 에러 추적
            elif self.track_5xx and response.status_code >= 500:
                context = get_request_context(request)
                context.request_id = getattr(request.state, 'request_id', None)
                
                log_error(
                    f"Server error: {response.status_code} {request.method} {request.url.path}",
                    error_type=ErrorType.SYSTEM_ERROR,
                    context=context,
                    status_code=response.status_code
                )
            
            return response
            
        except Exception as e:
            # 처리되지 않은 예외는 StructuredLoggingMiddleware에서 처리
            raise


class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    """
    성능 추적 미들웨어
    
    느린 요청과 리소스 사용량을 추적합니다.
    """
    
    def __init__(self, app, slow_request_threshold: float = 2.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """성능 추적"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            # 느린 요청 추적
            if duration > self.slow_request_threshold:
                context = get_request_context(request)
                context.request_id = getattr(request.state, 'request_id', None)
                
                log_performance(
                    operation=f"Slow request: {request.method} {request.url.path}",
                    duration=duration,
                    endpoint=request.url.path,
                    context=context,
                    status_code=response.status_code,
                    threshold=self.slow_request_threshold
                )
            
            return response
            
        except Exception as e:
            # 에러 발생 시에도 성능 추적
            duration = time.time() - start_time
            
            context = get_request_context(request)
            context.request_id = getattr(request.state, 'request_id', None)
            
            log_performance(
                operation=f"Failed request: {request.method} {request.url.path}",
                duration=duration,
                endpoint=request.url.path,
                context=context,
                error=str(e)
            )
            
            raise