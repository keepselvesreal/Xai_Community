from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import json
import logging
from ..database.redis import get_redis_manager
from ..config import get_settings

logger = logging.getLogger(__name__)

class TokenBlacklistService:
    """Redis 기반 토큰 블랙리스트 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.blacklist_prefix = "blacklist:token:"
        self.jti_blacklist_prefix = "blacklist:jti:"
        self.user_blacklist_prefix = "blacklist:user:"
        
    def _get_token_hash(self, token: str) -> str:
        """토큰을 해시로 변환 (보안 및 저장 효율성)"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _get_token_key(self, token: str) -> str:
        """토큰 블랙리스트 Redis 키 생성"""
        token_hash = self._get_token_hash(token)
        return f"{self.blacklist_prefix}{token_hash}"
    
    def _get_jti_key(self, jti: str) -> str:
        """JTI 블랙리스트 Redis 키 생성"""
        return f"{self.jti_blacklist_prefix}{jti}"
    
    def _get_user_blacklist_key(self, user_id: str) -> str:
        """사용자별 블랙리스트 Redis 키 생성"""
        return f"{self.user_blacklist_prefix}{user_id}"
    
    async def blacklist_token(
        self, 
        token: str, 
        expires_at: datetime, 
        reason: str = "revoked",
        user_id: Optional[str] = None
    ) -> bool:
        """토큰을 블랙리스트에 추가"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            logger.warning("Redis 연결 없음 - 토큰 블랙리스트 불가")
            return False
        
        try:
            token_key = self._get_token_key(token)
            
            # 블랙리스트 정보
            blacklist_info = {
                "reason": reason,
                "blacklisted_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
                "user_id": user_id
            }
            
            # TTL 계산 (토큰 만료 시간까지)
            ttl = int((expires_at - datetime.now()).total_seconds())
            if ttl <= 0:
                logger.warning(f"토큰이 이미 만료됨: {token[:20]}...")
                return False
            
            # Redis에 저장
            success = await redis_manager.set(token_key, blacklist_info, ttl=ttl)
            
            if success:
                logger.info(f"토큰 블랙리스트 추가 성공: {token[:20]}... (이유: {reason})")
                
                # 사용자별 블랙리스트에도 추가 (선택적)
                if user_id:
                    await self._add_to_user_blacklist(user_id, token, expires_at)
            else:
                logger.error(f"토큰 블랙리스트 추가 실패: {token[:20]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"토큰 블랙리스트 추가 오류: {e}")
            return False
    
    async def blacklist_token_by_jti(
        self, 
        jti: str, 
        expires_at: datetime, 
        reason: str = "revoked"
    ) -> bool:
        """JTI로 토큰을 블랙리스트에 추가"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            jti_key = self._get_jti_key(jti)
            
            blacklist_info = {
                "reason": reason,
                "blacklisted_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat()
            }
            
            ttl = int((expires_at - datetime.now()).total_seconds())
            if ttl <= 0:
                return False
            
            success = await redis_manager.set(jti_key, blacklist_info, ttl=ttl)
            
            if success:
                logger.info(f"JTI 블랙리스트 추가 성공: {jti} (이유: {reason})")
            
            return success
            
        except Exception as e:
            logger.error(f"JTI 블랙리스트 추가 오류: {e}")
            return False
    
    async def is_blacklisted(self, token: str) -> bool:
        """토큰이 블랙리스트에 있는지 확인"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            token_key = self._get_token_key(token)
            exists = await redis_manager.exists(token_key)
            return exists
            
        except Exception as e:
            logger.error(f"토큰 블랙리스트 확인 오류: {e}")
            return False
    
    async def is_blacklisted_by_jti(self, jti: str) -> bool:
        """JTI가 블랙리스트에 있는지 확인"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            jti_key = self._get_jti_key(jti)
            exists = await redis_manager.exists(jti_key)
            return exists
            
        except Exception as e:
            logger.error(f"JTI 블랙리스트 확인 오류: {e}")
            return False
    
    async def get_blacklist_info(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰의 블랙리스트 정보 조회"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return None
        
        try:
            token_key = self._get_token_key(token)
            info = await redis_manager.get(token_key)
            return info
            
        except Exception as e:
            logger.error(f"블랙리스트 정보 조회 오류: {e}")
            return None
    
    async def _add_to_user_blacklist(
        self, 
        user_id: str, 
        token: str, 
        expires_at: datetime
    ):
        """사용자별 블랙리스트에 토큰 추가"""
        redis_manager = await get_redis_manager()
        
        try:
            user_key = self._get_user_blacklist_key(user_id)
            
            # 현재 사용자 블랙리스트 조회
            user_blacklist = await redis_manager.get(user_key) or []
            
            # 새 토큰 정보 추가
            token_info = {
                "token_hash": self._get_token_hash(token),
                "blacklisted_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat()
            }
            
            user_blacklist.append(token_info)
            
            # TTL은 가장 늦게 만료되는 토큰 기준
            ttl = int((expires_at - datetime.now()).total_seconds())
            await redis_manager.set(user_key, user_blacklist, ttl=max(ttl, 3600))
            
        except Exception as e:
            logger.error(f"사용자 블랙리스트 업데이트 오류: {e}")
    
    async def blacklist_user_tokens(
        self, 
        user_id: str, 
        expires_at: datetime, 
        reason: str = "user_logout"
    ) -> int:
        """사용자의 모든 토큰을 블랙리스트에 추가"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 사용자별 블랙리스트 키에 마커 추가
            user_key = self._get_user_blacklist_key(user_id)
            
            blacklist_info = {
                "reason": reason,
                "blacklisted_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
                "all_tokens": True  # 모든 토큰 무효화 마커
            }
            
            ttl = int((expires_at - datetime.now()).total_seconds())
            if ttl <= 0:
                ttl = 3600  # 최소 1시간
            
            success = await redis_manager.set(user_key, blacklist_info, ttl=ttl)
            
            if success:
                logger.info(f"사용자 모든 토큰 블랙리스트: {user_id} (이유: {reason})")
                return 1  # 마커 1개 추가
            
            return 0
            
        except Exception as e:
            logger.error(f"사용자 토큰 블랙리스트 오류: {e}")
            return 0
    
    async def is_user_blacklisted(self, user_id: str) -> bool:
        """사용자의 모든 토큰이 블랙리스트되었는지 확인"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            user_key = self._get_user_blacklist_key(user_id)
            info = await redis_manager.get(user_key)
            
            if info and isinstance(info, dict):
                return info.get("all_tokens", False)
            
            return False
            
        except Exception as e:
            logger.error(f"사용자 블랙리스트 확인 오류: {e}")
            return False
    
    async def get_blacklist_stats(self) -> Dict[str, Any]:
        """블랙리스트 통계 정보"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return {"status": "disconnected"}
        
        try:
            # Redis 정보 조회
            health_info = await redis_manager.health_check()
            
            # 간단한 통계 (정확한 카운트는 성능상 부담)
            stats = {
                "status": "connected",
                "total_blacklisted": "unavailable",  # 정확한 카운트는 비용이 높음
                "redis_info": health_info.get("redis_info", {})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"블랙리스트 통계 조회 오류: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup_expired_tokens(self) -> int:
        """만료된 토큰 정리 (Redis TTL이 자동 처리하므로 수동 정리 불필요)"""
        # Redis TTL에 의해 자동 정리되므로 실제 구현 불필요
        # 메서드는 인터페이스 호환성을 위해 유지
        logger.info("만료된 토큰은 Redis TTL에 의해 자동 정리됩니다.")
        return 0
    
    async def clear_all_blacklisted_tokens(self) -> int:
        """모든 블랙리스트 토큰 삭제 (테스트용)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 개발/테스트 환경에서만 사용
            if self.settings.environment not in ["development", "test"]:
                logger.warning("프로덕션 환경에서는 전체 블랙리스트 삭제 불가")
                return 0
            
            # 패턴 매칭으로 블랙리스트 키들 찾아서 삭제
            # 실제 구현에서는 Redis SCAN 명령어 사용 권장
            logger.info("테스트 환경: 블랙리스트 데이터 정리")
            return 0
            
        except Exception as e:
            logger.error(f"블랙리스트 전체 삭제 오류: {e}")
            return 0

# 글로벌 토큰 블랙리스트 서비스 인스턴스
token_blacklist_service = TokenBlacklistService()

async def get_token_blacklist_service() -> TokenBlacklistService:
    """토큰 블랙리스트 서비스 인스턴스 반환"""
    return token_blacklist_service