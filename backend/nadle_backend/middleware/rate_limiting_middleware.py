# Rate Limiting 미들웨어
# 최종 수정시간: 2025-07-21 오후 3:15 (KST)
# 주요 컴포넌트: FastAPI Rate Limiting 미들웨어
# 함수:
#   - RateLimitingMiddleware: 메인 Rate Limiting 미들웨어 클래스 (라인 25-120)
#   - get_rate_limit_config_for_path: 경로별 Rate Limiting 설정 반환 (라인 122-150)
#   - extract_user_id_from_request: 요청에서 사용자 ID 추출 (라인 152-170)
# 관련 파일:
#   - nadle_backend.services.rate_limiting_service: Rate Limiting 서비스
#   - nadle_backend.models.rate_limit_config: Rate Limiting 설정 모델
#   - nadle_backend.dependencies.auth: 사용자 인증 의존성

import time
import logging
from typing import Optional, Callable, Dict
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..services.rate_limiting_service import get_rate_limiting_service
from ..models.rate_limit_config import (
    RateLimitConfig,
    RateLimitConfigRegistry,
    RateLimitStrategy
)
from ..config import get_settings

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Rate Limiting 미들웨어
    
    요청이 들어올 때마다 Rate Limiting을 확인하고,
    제한을 초과한 경우 429 응답을 반환합니다.
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        enabled: bool = True,
        exempt_paths: Optional[list] = None,
        custom_error_handler: Optional[Callable] = None
    ):
        """
        Args:
            app: FastAPI 애플리케이션
            enabled: Rate limiting 활성화 여부
            exempt_paths: Rate limiting 제외 경로 목록
            custom_error_handler: 커스텀 에러 핸들러
        """
        super().__init__(app)
        self.enabled = enabled
        
        # 기본 제외 경로
        default_exempt_paths = [
            "/health",
            "/docs", 
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        if exempt_paths is None:
            self.exempt_paths = default_exempt_paths
        else:
            # 커스텀 경로와 기본 경로 합치기
            self.exempt_paths = list(set(exempt_paths + default_exempt_paths))
        
        self.custom_error_handler = custom_error_handler
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next):
        """미들웨어 메인 로직"""
        # Rate limiting 비활성화된 경우 바로 통과
        if not self.enabled or not self.settings.rate_limiting_enabled:
            return await call_next(request)
        
        # 제외 경로 확인
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        try:
            # Rate limiting 확인
            should_limit, rate_result = await self._check_rate_limit(request)
            
            if should_limit and not rate_result.allowed:
                # Rate limiting 메트릭 수집
                await self._collect_rate_limit_metrics(request, rate_result)
                
                # Rate limit 초과 시 429 응답
                return await self._create_rate_limit_response(rate_result)
            
            # 요청 처리
            response = await call_next(request)
            
            # 성공 응답에 Rate limit 헤더 추가
            if rate_result:
                self._add_rate_limit_headers(response, rate_result)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # 에러 발생 시 fail-open (요청 허용)
            return await call_next(request)
    
    def _is_exempt_path(self, path: str) -> bool:
        """경로가 Rate limiting 제외 대상인지 확인"""
        return any(exempt in path for exempt in self.exempt_paths)
    
    async def _check_rate_limit(self, request: Request):
        """Rate limiting 확인"""
        # 경로별 설정 가져오기
        config = get_rate_limit_config_for_path(request.url.path, request.method)
        
        if not config or not config.enabled:
            return False, None
        
        # 사용자 ID 추출 (인증된 요청의 경우)
        user_id = await extract_user_id_from_request(request)
        
        # Rate limiting 서비스 확인
        service = await get_rate_limiting_service()
        result = await service.check_rate_limit(request, config, user_id)
        
        return True, result
    
    async def _create_rate_limit_response(self, rate_result):
        """Rate limit 초과 시 429 응답 생성"""
        error_detail = {
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": rate_result.retry_after
        }
        
        # 커스텀 에러 핸들러 사용
        if self.custom_error_handler:
            return await self.custom_error_handler(rate_result)
        
        return JSONResponse(
            status_code=429,
            content=error_detail,
            headers={
                "X-RateLimit-Limit": str(rate_result.limit),
                "X-RateLimit-Remaining": str(rate_result.remaining),
                "X-RateLimit-Reset": str(rate_result.reset_time),
                "Retry-After": str(rate_result.retry_after) if rate_result.retry_after else "60"
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, rate_result):
        """응답에 Rate limit 헤더 추가"""
        response.headers["X-RateLimit-Limit"] = str(rate_result.limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_result.remaining)
        response.headers["X-RateLimit-Reset"] = str(rate_result.reset_time)
    
    async def _collect_rate_limit_metrics(self, request: Request, rate_result):
        """Rate limiting 메트릭 수집"""
        try:
            from ..database.redis_factory import get_redis_manager
            from datetime import datetime
            
            # Redis 클라이언트 가져오기
            redis_manager = await get_redis_manager()
            
            # Redis 연결 확인
            if not await redis_manager.is_connected():
                await redis_manager.connect()
                
            redis_client = getattr(redis_manager, 'redis_client', None)
            
            if not redis_client:
                logger.error("Redis client not available for metrics collection")
                return
            
            # 환경별 키 프리픽스 가져오기
            key_prefix = ""
            if self.settings.environment == "development":
                key_prefix = "dev:"
            elif self.settings.environment == "test":
                key_prefix = "test:"
            elif self.settings.environment == "staging":
                key_prefix = "stage:"
            elif self.settings.environment == "production":
                key_prefix = "prod:"
            
            # 엔드포인트 키 생성
            endpoint_key = f"{request.method}:{request.url.path}"
            
            # Rate limiting 메트릭 저장
            rate_limit_blocks_key = f"{key_prefix}api:metrics:rate_limit_blocks" if key_prefix else "api:metrics:rate_limit_blocks"
            await redis_client.hincrby(rate_limit_blocks_key, endpoint_key, 1)
            
            # 시간별 통계
            hour_key = f"{key_prefix}rate_limit_blocks:{datetime.now().strftime('%Y%m%d%H')}" if key_prefix else f"rate_limit_blocks:{datetime.now().strftime('%Y%m%d%H')}"
            await redis_client.hincrby(hour_key, endpoint_key, 1)
            await redis_client.expire(hour_key, 86400)  # 24시간 보존
            
            # 상태코드 메트릭도 업데이트
            status_codes_redis_key = f"{key_prefix}api:metrics:status_codes" if key_prefix else "api:metrics:status_codes"
            await redis_client.hincrby(status_codes_redis_key, "status:429", 1)
            
            logger.debug(f"Rate limiting metrics collected for {endpoint_key}")
            
        except Exception as e:
            logger.error(f"Failed to collect rate limit metrics: {e}")


def get_rate_limit_config_for_path(path: str, method: str) -> Optional[RateLimitConfig]:
    """
    경로와 HTTP 메소드에 따른 Rate Limiting 설정 반환
    
    Args:
        path: 요청 경로
        method: HTTP 메소드
        
    Returns:
        RateLimitConfig: 해당 경로의 Rate Limiting 설정
    """
    # 경로별 설정 매핑 (API prefix 포함)
    path_config_mapping = {
        # 인증 관련
        ("/api/auth/login", "POST"): "auth_login",
        ("/api/auth/register", "POST"): "auth_register",
        ("/api/auth/send-verification-email", "POST"): "email_verification",
        
        # 게시글 관련
        ("/api/posts", "POST"): "posts_create",
        ("/api/posts/list", "GET"): "posts_list",
        
        # 댓글 관련
        ("/api/posts/comments", "POST"): "comments_create",
        
        # 파일 업로드
        ("/api/files/upload", "POST"): "files_upload",
    }
    
    # 정확한 경로 매칭
    config_key = path_config_mapping.get((path, method))
    if config_key:
        return RateLimitConfigRegistry.get_config(config_key)
    
    # 경로 패턴 매칭 (예: /posts/{id}, /users/{id})
    for (pattern_path, pattern_method), pattern_config_key in path_config_mapping.items():
        if method == pattern_method and path.startswith(pattern_path.split('/')[1]):
            return RateLimitConfigRegistry.get_config(pattern_config_key)
    
    return None


async def extract_user_id_from_request(request: Request) -> Optional[str]:
    """
    요청에서 사용자 ID 추출
    
    Args:
        request: FastAPI Request 객체
        
    Returns:
        str: 사용자 ID (인증된 경우), None (비인증 요청)
    """
    try:
        # JWT 토큰에서 사용자 정보 추출 시도
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        
        # JWT 토큰 검증 및 사용자 ID 추출
        from ..utils.jwt import decode_token
        payload = decode_token(token)
        
        if payload and "user_id" in payload:
            return str(payload["user_id"])
            
    except Exception as e:
        logger.debug(f"Failed to extract user ID from request: {e}")
    
    return None


# 미들웨어 설정 헬퍼 함수
def create_rate_limiting_middleware(
    enabled: bool = None,
    exempt_paths: Optional[list] = None,
    custom_error_handler: Optional[Callable] = None
) -> type:
    """
    Rate Limiting 미들웨어 생성 헬퍼
    
    Args:
        enabled: Rate limiting 활성화 여부 (None이면 설정값 사용)
        exempt_paths: 제외 경로 목록
        custom_error_handler: 커스텀 에러 핸들러
        
    Returns:
        RateLimitingMiddleware 클래스
    """
    settings = get_settings()
    
    if enabled is None:
        enabled = settings.rate_limiting_enabled
    
    def middleware_factory(app: ASGIApp):
        return RateLimitingMiddleware(
            app=app,
            enabled=enabled,
            exempt_paths=exempt_paths,
            custom_error_handler=custom_error_handler
        )
    
    return middleware_factory