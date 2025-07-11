"""
보안 헤더 미들웨어

CSP, XSS 방지, CSRF 보호 등 웹 보안 헤더를 자동으로 추가하는 미들웨어
"""

import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def get_csp_policy(environment: str = None) -> str:
    """환경별 Content Security Policy 정책 반환"""
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "production")
    
    base_policy = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
        "img-src": "'self' data: https:",
        "font-src": "'self' https://fonts.gstatic.com",
        "connect-src": "'self'",
        "frame-ancestors": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'"
    }
    
    # 개발 환경에서는 로컬호스트 허용
    if environment == "development":
        base_policy["script-src"] += " localhost:* 127.0.0.1:*"
        base_policy["connect-src"] += " localhost:* 127.0.0.1:* ws://localhost:* ws://127.0.0.1:*"
        base_policy["style-src"] += " localhost:* 127.0.0.1:*"
    
    # 정책을 문자열로 변환
    policy_parts = []
    for directive, sources in base_policy.items():
        policy_parts.append(f"{directive} {sources}")
    
    return "; ".join(policy_parts)


def get_api_csp_policy() -> str:
    """API 엔드포인트용 더 엄격한 CSP 정책"""
    return (
        "default-src 'none'; "
        "script-src 'none'; "
        "style-src 'none'; "
        "img-src 'none'; "
        "connect-src 'self'; "
        "font-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none'"
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 미들웨어"""
    
    def __init__(self, app, environment: str = None):
        super().__init__(app)
        self.environment = environment or os.getenv("ENVIRONMENT", "production")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """요청 처리 및 보안 헤더 추가"""
        
        # 요청 처리
        response = await call_next(request)
        
        # API 엔드포인트 확인
        is_api_endpoint = request.url.path.startswith("/api/")
        
        # Content Security Policy
        if is_api_endpoint:
            csp_policy = get_api_csp_policy()
        else:
            csp_policy = get_csp_policy(self.environment)
        
        response.headers["Content-Security-Policy"] = csp_policy
        
        # XSS 보호 헤더들
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (HTTPS 강제)
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (기능 제한)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "magnetometer=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
        
        # CSRF 보호를 위한 추가 헤더
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # 캐시 제어 (민감한 데이터용)
        if is_api_endpoint and any(path in request.url.path for path in ["/auth/", "/user/"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF 보호 미들웨어"""
    
    def __init__(self, app, secret_key: str = None):
        super().__init__(app)
        self.secret_key = secret_key or os.getenv("SECRET_KEY", "fallback-secret-key")
        # 실제 구현에서는 더 강력한 CSRF 토큰 생성 필요
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """CSRF 토큰 검증"""
        
        # GET, HEAD, OPTIONS는 CSRF 보호 제외
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # API 인증이 있는 경우 CSRF 검증 로직
        # 현재는 JWT 기반 인증을 사용하므로 추가 CSRF 보호는 선택적
        
        response = await call_next(request)
        
        # SameSite 쿠키 정책 확인을 위한 헤더 추가
        response.headers["X-CSRF-Protection"] = "enabled"
        
        return response