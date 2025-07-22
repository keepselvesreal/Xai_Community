import time
import hashlib
from typing import Optional, Protocol, runtime_checkable
from redis.asyncio import Redis
from fastapi import Request
import logging

from ..database.redis_factory import RedisFactory, get_redis_manager
from ..models.rate_limit_config import (
    RateLimitConfig,
    RateLimitResult,
    RateLimitStrategy,
    RateLimitConfigRegistry
)
from ..config import get_settings

logger = logging.getLogger(__name__)


@runtime_checkable
class RateLimitingServiceProtocol(Protocol):
    """Rate limiting 서비스 프로토콜"""
    
    async def check_rate_limit(
        self, 
        request: Request, 
        config: RateLimitConfig,
        user_id: Optional[str] = None
    ) -> RateLimitResult:
        """Rate limit 확인"""
        ...
    
    async def reset_rate_limit(self, key: str) -> bool:
        """Rate limit 리셋"""
        ...


class RateLimitingService:
    """
    Redis 기반 Rate Limiting 서비스
    
    기존 Redis 아키텍처를 활용하여 분산 환경에서 
    일관된 Rate Limiting을 제공합니다.
    """
    
    def __init__(self, redis_factory: Optional[RedisFactory] = None):
        """
        Args:
            redis_factory: RedisFactory 인스턴스 (선택적, 없으면 기본 팩토리 사용)
        """
        self.redis_factory = redis_factory
        self.settings = get_settings()
        self._redis_client: Optional[Redis] = None
        self._redis_manager = None
        self._key_prefix = ""
        
    async def initialize(self):
        """Redis 클라이언트 초기화"""
        try:
            # Redis 매니저 가져오기
            self._redis_manager = await get_redis_manager()
            
            # 연결 확인 및 연결
            if not await self._redis_manager.is_connected():
                await self._redis_manager.connect()
            
            # 실제 Redis 클라이언트 가져오기 (RedisManager의 redis_client 속성 사용)
            if hasattr(self._redis_manager, 'redis_client'):
                self._redis_client = self._redis_manager.redis_client
            else:
                raise Exception("Redis manager does not have redis_client attribute")
            
            self._key_prefix = f"{self.settings.redis_key_prefix}{self.settings.rate_limiting_key_prefix}"
            logger.info(f"Rate limiting service initialized with prefix: {self._key_prefix}")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiting service: {e}")
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 환경)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 첫 번째 IP가 실제 클라이언트 IP
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인 (Nginx 등)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # 직접 연결 IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        # 폴백
        return "unknown"
    
    def _generate_rate_limit_key(
        self, 
        request: Request, 
        config: RateLimitConfig, 
        user_id: Optional[str] = None
    ) -> str:
        """Rate limiting 키 생성"""
        current_window = int(time.time() // config.window)
        
        if config.key_strategy == RateLimitStrategy.IP:
            client_ip = self._get_client_ip(request)
            identifier = client_ip
        elif config.key_strategy == RateLimitStrategy.USER:
            if not user_id:
                # 사용자 ID가 없으면 IP로 폴백
                identifier = self._get_client_ip(request)
            else:
                identifier = f"user:{user_id}"
        elif config.key_strategy == RateLimitStrategy.COMPOSITE:
            client_ip = self._get_client_ip(request)
            if user_id:
                identifier = f"{client_ip}:user:{user_id}"
            else:
                identifier = client_ip
        else:
            # 기본값은 IP
            identifier = self._get_client_ip(request)
        
        # 엔드포인트 이름 해시화 (키 길이 최적화)
        endpoint_hash = hashlib.md5(config.endpoint.encode()).hexdigest()[:8]
        
        return f"{self._key_prefix}{endpoint_hash}:{identifier}:{current_window}"
    
    async def check_rate_limit(
        self, 
        request: Request, 
        config: RateLimitConfig,
        user_id: Optional[str] = None
    ) -> RateLimitResult:
        """
        Rate limit 확인
        
        Args:
            request: FastAPI Request 객체
            config: Rate limiting 설정
            user_id: 사용자 ID (선택적)
            
        Returns:
            RateLimitResult: Rate limiting 결과
        """
        if not self.settings.rate_limiting_enabled or not config.enabled:
            # Rate limiting이 비활성화된 경우 항상 허용
            return RateLimitResult(
                allowed=True,
                limit=config.limit,
                remaining=config.limit,
                reset_time=int(time.time() + config.window),
                key="disabled"
            )
        
        if not self._redis_client:
            await self.initialize()
        
        key = self._generate_rate_limit_key(request, config, user_id)
        current_time = int(time.time())
        current_window = current_time // config.window
        reset_time = (current_window + 1) * config.window
        
        try:
            # Redis INCR을 사용한 원자적 카운터 증가
            current_count = await self._redis_client.incr(key)
            
            # 첫 번째 요청인 경우 TTL 설정
            if current_count == 1:
                await self._redis_client.expire(key, config.window)
            
            remaining = max(0, config.limit - current_count)
            allowed = current_count <= config.limit
            
            # Rate limit 초과 시 재시도 가능 시간 계산
            retry_after = None
            if not allowed:
                retry_after = reset_time - current_time
            
            result = RateLimitResult(
                allowed=allowed,
                limit=config.limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
                key=key
            )
            
            logger.debug(
                f"Rate limit check: {key} -> {current_count}/{config.limit} "
                f"(allowed={allowed}, remaining={remaining})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Rate limit check failed for key {key}: {e}")
            # Redis 오류 시 요청 허용 (fail-open)
            return RateLimitResult(
                allowed=True,
                limit=config.limit,
                remaining=config.limit,
                reset_time=reset_time,
                key=key
            )
    
    async def reset_rate_limit(self, key: str) -> bool:
        """
        특정 키의 Rate limit 리셋
        
        Args:
            key: Rate limiting 키
            
        Returns:
            bool: 리셋 성공 여부
        """
        if not self._redis_client:
            await self.initialize()
        
        try:
            deleted = await self._redis_client.delete(key)
            logger.info(f"Rate limit reset for key: {key} (deleted: {deleted})")
            return deleted > 0
        except Exception as e:
            logger.error(f"Failed to reset rate limit for key {key}: {e}")
            return False
    
    async def get_rate_limit_status(
        self, 
        request: Request, 
        config: RateLimitConfig,
        user_id: Optional[str] = None
    ) -> RateLimitResult:
        """
        Rate limit 상태 조회 (카운터 증가 없이)
        
        Args:
            request: FastAPI Request 객체
            config: Rate limiting 설정
            user_id: 사용자 ID (선택적)
            
        Returns:
            RateLimitResult: 현재 Rate limiting 상태
        """
        if not self.settings.rate_limiting_enabled or not config.enabled:
            return RateLimitResult(
                allowed=True,
                limit=config.limit,
                remaining=config.limit,
                reset_time=int(time.time() + config.window),
                key="disabled"
            )
        
        if not self._redis_client:
            await self.initialize()
        
        key = self._generate_rate_limit_key(request, config, user_id)
        current_time = int(time.time())
        current_window = current_time // config.window
        reset_time = (current_window + 1) * config.window
        
        try:
            # GET을 사용하여 현재 값만 조회
            current_count = await self._redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            remaining = max(0, config.limit - current_count)
            allowed = current_count < config.limit
            
            retry_after = None
            if not allowed:
                retry_after = reset_time - current_time
            
            return RateLimitResult(
                allowed=allowed,
                limit=config.limit,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
                key=key
            )
            
        except Exception as e:
            logger.error(f"Rate limit status check failed for key {key}: {e}")
            return RateLimitResult(
                allowed=True,
                limit=config.limit,
                remaining=config.limit,
                reset_time=reset_time,
                key=key
            )
    
    async def cleanup_expired_keys(self) -> int:
        """
        만료된 Rate limiting 키 정리
        
        Returns:
            int: 정리된 키 개수
        """
        if not self._redis_client:
            await self.initialize()
        
        try:
            pattern = f"{self._key_prefix}*"
            cursor = 0
            cleaned_count = 0
            
            while True:
                cursor, keys = await self._redis_client.scan(
                    cursor=cursor, 
                    match=pattern, 
                    count=100
                )
                
                if keys:
                    # TTL이 -1 (영구) 또는 -2 (존재하지 않음)인 키들 확인
                    pipe = self._redis_client.pipeline()
                    for key in keys:
                        pipe.ttl(key)
                    
                    ttls = await pipe.execute()
                    
                    # TTL이 없는 키들 삭제
                    expired_keys = [
                        keys[i] for i, ttl in enumerate(ttls) 
                        if ttl == -1  # TTL이 설정되지 않은 키
                    ]
                    
                    if expired_keys:
                        deleted = await self._redis_client.delete(*expired_keys)
                        cleaned_count += deleted
                        logger.info(f"Cleaned {deleted} expired rate limiting keys")
                
                if cursor == 0:
                    break
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired rate limiting keys: {e}")
            return 0


# 전역 Rate Limiting 서비스 인스턴스
_rate_limiting_service: Optional[RateLimitingService] = None


async def get_rate_limiting_service() -> RateLimitingService:
    """Rate Limiting 서비스 의존성 주입 함수"""
    global _rate_limiting_service
    
    if _rate_limiting_service is None:
        _rate_limiting_service = RateLimitingService()
        await _rate_limiting_service.initialize()
    
    return _rate_limiting_service