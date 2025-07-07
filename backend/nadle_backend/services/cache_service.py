from typing import Optional, Dict, Any
import logging
from ..database.redis import get_redis_manager
from ..config import get_settings

logger = logging.getLogger(__name__)

class CacheService:
    """Redis 캐싱 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def get_user_cache(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 정보를 캐시에서 가져오기"""
        redis_manager = await get_redis_manager()
        cache_key = f"user:{user_id}"
        
        try:
            cached_data = await redis_manager.get(cache_key)
            if cached_data:
                logger.debug(f"캐시에서 사용자 정보 반환: {user_id}")
                return cached_data
            
            logger.debug(f"캐시에 사용자 정보 없음: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"사용자 캐시 조회 오류: {e}")
            return None
    
    async def set_user_cache(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """사용자 정보를 캐시에 저장"""
        redis_manager = await get_redis_manager()
        cache_key = f"user:{user_id}"
        
        try:
            # 민감한 정보는 캐시에서 제외
            safe_data = {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "user_handle": user_data.get("user_handle"),
                "display_name": user_data.get("display_name"),
                "status": user_data.get("status"),
                "created_at": user_data.get("created_at"),
                "last_login": user_data.get("last_login")
            }
            
            success = await redis_manager.set(
                cache_key, 
                safe_data, 
                ttl=self.settings.cache_ttl_user
            )
            
            if success:
                logger.debug(f"사용자 정보 캐시 저장 성공: {user_id}")
            else:
                logger.warning(f"사용자 정보 캐시 저장 실패: {user_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"사용자 캐시 저장 오류: {e}")
            return False
    
    async def delete_user_cache(self, user_id: str) -> bool:
        """사용자 캐시 삭제"""
        redis_manager = await get_redis_manager()
        cache_key = f"user:{user_id}"
        
        try:
            result = await redis_manager.delete(cache_key)
            if result:
                logger.debug(f"사용자 캐시 삭제 성공: {user_id}")
            else:
                logger.debug(f"삭제할 사용자 캐시가 없음: {user_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"사용자 캐시 삭제 오류: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        redis_manager = await get_redis_manager()
        
        try:
            stats = await redis_manager.health_check()
            return {
                "cache_enabled": self.settings.cache_enabled,
                "redis_status": stats.get("status"),
                "redis_info": stats
            }
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 오류: {e}")
            return {
                "cache_enabled": self.settings.cache_enabled,
                "redis_status": "error",
                "error": str(e)
            }

# 글로벌 캐시 서비스 인스턴스
cache_service = CacheService()

async def get_cache_service() -> CacheService:
    """캐시 서비스 인스턴스 반환"""
    return cache_service