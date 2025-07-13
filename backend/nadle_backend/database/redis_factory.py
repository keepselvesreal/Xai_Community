"""Redis 팩토리 패턴 - 환경에 따른 Redis 클라이언트 자동 선택"""

import logging
from typing import Union, Protocol
from ..config import get_settings

logger = logging.getLogger(__name__)


class RedisManagerProtocol(Protocol):
    """Redis 매니저 인터페이스 프로토콜"""
    
    async def connect(self) -> bool:
        """Redis 연결"""
        ...
    
    async def disconnect(self):
        """Redis 연결 종료"""
        ...
    
    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        ...
    
    async def get(self, key: str):
        """값 조회"""
        ...
    
    async def set(self, key: str, value, ttl: int = 3600) -> bool:
        """값 저장"""
        ...
    
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        ...
    
    async def exists(self, key: str) -> bool:
        """키 존재 확인"""
        ...
    
    async def health_check(self) -> dict:
        """상태 확인"""
        ...


class RedisFactory:
    """Redis 클라이언트 팩토리 클래스"""
    
    _instance = None
    _manager: Union[RedisManagerProtocol, None] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisFactory, cls).__new__(cls)
        return cls._instance
    
    def get_redis_manager(self) -> RedisManagerProtocol:
        """환경에 따른 적절한 Redis 매니저 반환"""
        if self._manager is not None:
            return self._manager
        
        settings = get_settings()
        
        # 환경별 Redis 클라이언트 선택
        if settings.use_upstash_redis:
            logger.info(f"Upstash Redis 클라이언트 사용 (환경: {settings.environment})")
            # Upstash도 싱글톤으로 유지 (모니터링 지표 연속성 보장)
            from .upstash_redis import upstash_redis_manager
            self._manager = upstash_redis_manager
        else:
            logger.info(f"로컬 Redis 클라이언트 사용 (환경: {settings.environment})")
            from .redis import redis_manager
            self._manager = redis_manager
        
        return self._manager
    
    def reset(self):
        """팩토리 상태 리셋 (테스트용)"""
        self._manager = None


# 전역 팩토리 인스턴스
redis_factory = RedisFactory()


async def get_redis_manager() -> RedisManagerProtocol:
    """Redis 매니저 인스턴스 반환 (팩토리를 통해)
    
    환경에 따라 자동으로 적절한 Redis 클라이언트를 선택합니다:
    - development/test: 로컬 Redis (redis://localhost:6379)
    - staging/production: Upstash Redis (REST API)
    
    Returns:
        RedisManagerProtocol: 환경에 맞는 Redis 매니저
    """
    return redis_factory.get_redis_manager()


async def ensure_redis_connection() -> bool:
    """Redis 연결 확인 및 자동 연결"""
    manager = await get_redis_manager()
    
    if await manager.is_connected():
        return True
    
    logger.info("Redis 연결 시도 중...")
    connected = await manager.connect()
    
    if connected:
        logger.info("Redis 연결 성공")
    else:
        logger.warning("Redis 연결 실패")
    
    return connected


def get_prefixed_key(key: str) -> str:
    """환경별 프리픽스가 적용된 Redis 키 반환
    
    Args:
        key: 원본 키
        
    Returns:
        프리픽스가 적용된 키 (예: "staging:user:123" 또는 "user:123")
    """
    settings = get_settings()
    prefix = settings.redis_key_prefix
    return f"{prefix}{key}" if prefix else key


async def get_redis_health() -> dict:
    """Redis 상태 정보 반환"""
    try:
        manager = await get_redis_manager()
        
        # 먼저 연결 시도
        connected = await ensure_redis_connection()
        
        # 상태 확인
        health = await manager.health_check()
        
        # 환경 정보 추가
        settings = get_settings()
        health["environment"] = settings.environment
        health["redis_type"] = "upstash" if settings.use_upstash_redis else "local"
        health["key_prefix"] = settings.redis_key_prefix
        health["connection_ensured"] = connected
        
        return health
        
    except Exception as e:
        logger.error(f"Redis 상태 확인 중 오류: {e}")
        return {
            "status": "error",
            "message": f"Redis 상태 확인 실패: {str(e)}",
            "environment": get_settings().environment,
            "redis_type": "unknown"
        }