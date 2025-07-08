import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
from ..config import get_settings

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis 연결 및 캐싱 관리 클래스"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.settings = get_settings()
        self._connected = False
    
    async def connect(self) -> bool:
        """Redis 서버에 연결"""
        if not self.settings.cache_enabled:
            logger.info("Redis 캐시가 비활성화되어 있습니다.")
            return False
        
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                db=self.settings.redis_db,
                password=self.settings.redis_password,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            
            # 연결 테스트
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"Redis 연결 성공: {self.settings.redis_url}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis 연결 실패: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Redis 연결 종료"""
        if self.redis_client:
            await self.redis_client.aclose()
            self._connected = False
            logger.info("Redis 연결 종료")
    
    async def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self._connected or not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except:
            self._connected = False
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if not await self.is_connected():
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # JSON 파싱 시도
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Redis GET 오류 - key: {key}, error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 값 저장"""
        if not await self.is_connected():
            return False
        
        try:
            # 값을 JSON으로 직렬화
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            await self.redis_client.setex(key, ttl, value)
            return True
            
        except Exception as e:
            logger.error(f"Redis SET 오류 - key: {key}, error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        if not await self.is_connected():
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis DELETE 오류 - key: {key}, error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """캐시에 키가 존재하는지 확인"""
        if not await self.is_connected():
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis EXISTS 오류 - key: {key}, error: {e}")
            return False
    
    async def health_check(self) -> dict:
        """Redis 상태 확인"""
        if not self.settings.cache_enabled:
            return {
                "status": "disabled",
                "message": "Redis 캐시가 비활성화되어 있습니다."
            }
        
        try:
            if await self.is_connected():
                info = await self.redis_client.info()
                return {
                    "status": "connected",
                    "redis_version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            else:
                return {
                    "status": "disconnected",
                    "message": "Redis 서버에 연결할 수 없습니다."
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis 상태 확인 중 오류: {str(e)}"
            }

# 글로벌 Redis 매니저 인스턴스
redis_manager = RedisManager()

async def get_redis_manager() -> RedisManager:
    """Redis 매니저 인스턴스 반환"""
    return redis_manager