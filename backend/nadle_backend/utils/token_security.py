"""
토큰 보안 유틸리티

HttpOnly 쿠키 기반 JWT 토큰 관리 및 보안 강화
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import logging

logger = logging.getLogger(__name__)


class SecureTokenManager:
    """보안 토큰 관리자"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.cookie_secure = os.getenv("ENVIRONMENT", "development") == "production"
        self.cookie_domain = os.getenv("COOKIE_DOMAIN")
    
    def set_secure_cookie(
        self,
        response: Response,
        token: str,
        cookie_name: str = "access_token",
        max_age: int = 1800,  # 30분
        path: str = "/",
        domain: Optional[str] = None
    ) -> None:
        """보안 쿠키 설정"""
        
        response.set_cookie(
            key=cookie_name,
            value=token,
            max_age=max_age,
            path=path,
            domain=domain or self.cookie_domain,
            secure=self.cookie_secure,  # HTTPS에서만 전송
            httponly=True,              # JavaScript 접근 차단
            samesite="strict"           # CSRF 공격 방지
        )
        
        logger.info(f"보안 쿠키 설정: {cookie_name} (만료: {max_age}초)")
    
    def extract_token_from_cookie(
        self,
        request: Request,
        cookie_name: str = "access_token"
    ) -> Optional[str]:
        """쿠키에서 토큰 추출"""
        return request.cookies.get(cookie_name)
    
    def clear_secure_cookie(
        self,
        response: Response,
        cookie_name: str = "access_token",
        path: str = "/",
        domain: Optional[str] = None
    ) -> None:
        """보안 쿠키 삭제"""
        
        response.set_cookie(
            key=cookie_name,
            value="",
            max_age=0,
            path=path,
            domain=domain or self.cookie_domain,
            secure=self.cookie_secure,
            httponly=True,
            samesite="strict"
        )
        
        logger.info(f"보안 쿠키 삭제: {cookie_name}")
    
    def rotate_token(
        self,
        response: Response,
        old_token: str,
        new_token: str,
        cookie_name: str = "access_token"
    ) -> None:
        """토큰 로테이션 (기존 토큰 무효화 후 새 토큰 설정)"""
        
        # 기존 토큰 블랙리스트 추가
        if self.redis_client:
            self._blacklist_token(old_token)
        
        # 새 토큰 설정
        self.set_secure_cookie(response, new_token, cookie_name)
        
        logger.info("토큰 로테이션 완료")
    
    def _blacklist_token(self, token: str, expiry_seconds: int = 3600) -> None:
        """토큰을 블랙리스트에 추가"""
        if self.redis_client:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.redis_client.setex(
                f"blacklist:{token_hash}",
                expiry_seconds,
                "1"
            )


class TokenExpirationManager:
    """토큰 만료 관리자"""
    
    def __init__(self):
        self.access_token_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    def get_access_token_expiry(self) -> timedelta:
        """Access Token 만료 시간 반환"""
        return timedelta(minutes=self.access_token_minutes)
    
    def get_refresh_token_expiry(self) -> timedelta:
        """Refresh Token 만료 시간 반환"""
        return timedelta(days=self.refresh_token_days)
    
    def get_cookie_max_age(self, token_type: str = "access") -> int:
        """쿠키 Max-Age 값 반환 (초 단위)"""
        if token_type == "access":
            return self.access_token_minutes * 60
        elif token_type == "refresh":
            return self.refresh_token_days * 24 * 60 * 60
        else:
            return 3600  # 1시간 기본값


class TokenBlacklistManager:
    """토큰 블랙리스트 관리자"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_blacklist: Set[str] = set()  # Redis가 없을 때 메모리 폴백
    
    def blacklist_token(self, token: str, expiry_seconds: int = 3600) -> None:
        """토큰을 블랙리스트에 추가"""
        token_hash = self._hash_token(token)
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"blacklist:{token_hash}",
                    expiry_seconds,
                    "1"
                )
                logger.info(f"토큰 블랙리스트 추가 (Redis): {token_hash[:8]}...")
            except Exception as e:
                logger.error(f"Redis 블랙리스트 추가 실패: {e}")
                self._add_to_memory_blacklist(token_hash)
        else:
            self._add_to_memory_blacklist(token_hash)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """토큰이 블랙리스트에 있는지 확인"""
        token_hash = self._hash_token(token)
        
        if self.redis_client:
            try:
                result = self.redis_client.get(f"blacklist:{token_hash}")
                return result is not None
            except Exception as e:
                logger.error(f"Redis 블랙리스트 확인 실패: {e}")
                return self._is_in_memory_blacklist(token_hash)
        else:
            return self._is_in_memory_blacklist(token_hash)
    
    def _hash_token(self, token: str) -> str:
        """토큰 해시화"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _add_to_memory_blacklist(self, token_hash: str) -> None:
        """메모리 블랙리스트에 추가"""
        self.memory_blacklist.add(token_hash)
        logger.info(f"토큰 블랙리스트 추가 (메모리): {token_hash[:8]}...")
        
        # 메모리 사용량 제한 (최대 1000개)
        if len(self.memory_blacklist) > 1000:
            # 가장 오래된 항목 제거 (FIFO)
            self.memory_blacklist.pop()
    
    def _is_in_memory_blacklist(self, token_hash: str) -> bool:
        """메모리 블랙리스트 확인"""
        return token_hash in self.memory_blacklist


class SecureAuthBearer(HTTPBearer):
    """보안 강화된 Bearer 토큰 인증"""
    
    def __init__(
        self,
        auto_error: bool = True,
        token_manager: Optional[SecureTokenManager] = None,
        blacklist_manager: Optional[TokenBlacklistManager] = None
    ):
        super().__init__(auto_error=auto_error)
        self.token_manager = token_manager or SecureTokenManager()
        self.blacklist_manager = blacklist_manager or TokenBlacklistManager()
    
    async def __call__(self, request: Request) -> Optional[str]:
        """토큰 추출 및 검증"""
        
        # 1순위: HttpOnly 쿠키에서 토큰 추출
        token = self.token_manager.extract_token_from_cookie(request)
        
        if not token:
            # 2순위: Authorization 헤더에서 토큰 추출
            credentials = await super().__call__(request)
            if credentials:
                token = credentials.credentials
        
        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=401,
                    detail="토큰이 제공되지 않았습니다"
                )
            return None
        
        # 블랙리스트 확인
        if self.blacklist_manager.is_token_blacklisted(token):
            if self.auto_error:
                raise HTTPException(
                    status_code=401,
                    detail="무효화된 토큰입니다"
                )
            return None
        
        return token


class CSRFProtectionManager:
    """CSRF 보호 관리자"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")
    
    def generate_csrf_token(self, session_id: str) -> str:
        """CSRF 토큰 생성"""
        # 세션 ID와 현재 시간을 조합하여 CSRF 토큰 생성
        timestamp = str(int(datetime.now().timestamp()))
        data = f"{session_id}:{timestamp}:{self.secret_key}"
        
        csrf_token = hashlib.sha256(data.encode()).hexdigest()
        return f"{timestamp}.{csrf_token}"
    
    def verify_csrf_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """CSRF 토큰 검증"""
        try:
            if not token or "." not in token:
                return False
            
            timestamp_str, token_hash = token.split(".", 1)
            timestamp = int(timestamp_str)
            
            # 토큰 만료 확인
            if datetime.now().timestamp() - timestamp > max_age:
                return False
            
            # 토큰 재생성 및 비교
            expected_data = f"{session_id}:{timestamp_str}:{self.secret_key}"
            expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
            
            return secrets.compare_digest(token_hash, expected_hash)
            
        except (ValueError, TypeError):
            return False
    
    def set_csrf_cookie(self, response: Response, csrf_token: str) -> None:
        """CSRF 토큰을 쿠키에 설정 (JavaScript에서 읽을 수 있도록)"""
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=3600,  # 1시간
            path="/",
            secure=os.getenv("ENVIRONMENT") == "production",
            httponly=False,  # JavaScript에서 읽어야 함
            samesite="strict"
        )


class TokenSecurityMiddleware:
    """토큰 보안 미들웨어"""
    
    def __init__(
        self,
        token_manager: Optional[SecureTokenManager] = None,
        blacklist_manager: Optional[TokenBlacklistManager] = None
    ):
        self.token_manager = token_manager or SecureTokenManager()
        self.blacklist_manager = blacklist_manager or TokenBlacklistManager()
    
    async def verify_token_security(self, request: Request) -> Dict[str, Any]:
        """토큰 보안 상태 검증"""
        result = {
            "token_source": None,
            "token_valid": False,
            "security_warnings": []
        }
        
        # 토큰 소스 확인
        cookie_token = self.token_manager.extract_token_from_cookie(request)
        auth_header = request.headers.get("authorization")
        
        if cookie_token:
            result["token_source"] = "cookie"
            token = cookie_token
        elif auth_header and auth_header.startswith("Bearer "):
            result["token_source"] = "header"
            token = auth_header[7:]
            result["security_warnings"].append("Bearer 토큰은 XSS에 취약할 수 있습니다")
        else:
            return result
        
        # 블랙리스트 확인
        if self.blacklist_manager.is_token_blacklisted(token):
            result["security_warnings"].append("블랙리스트된 토큰입니다")
            return result
        
        result["token_valid"] = True
        return result


def create_secure_token_response(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: Optional[str] = None
) -> Dict[str, Any]:
    """보안 토큰 응답 생성"""
    
    token_manager = SecureTokenManager()
    expiration_manager = TokenExpirationManager()
    
    # Access Token 쿠키 설정
    token_manager.set_secure_cookie(
        response=response,
        token=access_token,
        cookie_name="access_token",
        max_age=expiration_manager.get_cookie_max_age("access")
    )
    
    # Refresh Token 쿠키 설정
    token_manager.set_secure_cookie(
        response=response,
        token=refresh_token,
        cookie_name="refresh_token",
        max_age=expiration_manager.get_cookie_max_age("refresh")
    )
    
    # CSRF 토큰 설정 (필요한 경우)
    if csrf_token:
        csrf_manager = CSRFProtectionManager()
        csrf_manager.set_csrf_cookie(response, csrf_token)
    
    # 응답에는 토큰을 포함하지 않음 (쿠키에만 저장)
    return {
        "message": "인증 성공",
        "authentication": "secure_cookies",
        "expires_in": expiration_manager.get_cookie_max_age("access"),
        "csrf_token": csrf_token if csrf_token else None
    }