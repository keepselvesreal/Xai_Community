from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
import json
import logging
from ..database.redis_factory import get_redis_manager, get_prefixed_key
from ..config import get_settings

logger = logging.getLogger(__name__)

class SessionData(BaseModel):
    """세션 데이터 모델"""
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    ip_address: str
    user_agent: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)

class SessionService:
    """Redis 기반 세션 관리 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return str(uuid.uuid4())
    
    def _get_session_key(self, session_id: str) -> str:
        """세션 Redis 키 생성"""
        return get_prefixed_key(f"{self.session_prefix}{session_id}")
    
    def _get_user_sessions_key(self, user_id: str) -> str:
        """사용자 세션 목록 Redis 키 생성"""
        return get_prefixed_key(f"{self.user_sessions_prefix}{user_id}")
    
    async def create_session(
        self, 
        session_data: SessionData, 
        ttl: Optional[int] = None,
        max_concurrent_sessions: Optional[int] = None
    ) -> str:
        """세션 생성"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            logger.warning("Redis 연결 없음 - 세션 생성 불가")
            return None
        
        try:
            session_id = self._generate_session_id()
            session_key = self._get_session_key(session_id)
            user_sessions_key = self._get_user_sessions_key(session_data.user_id)
            
            # TTL 설정 (기본값: refresh token 만료 시간)
            if ttl is None:
                ttl = int((session_data.expires_at - datetime.now()).total_seconds())
                if ttl <= 0:
                    ttl = self.settings.refresh_token_expire_days * 24 * 3600
            
            # 세션 데이터 저장
            session_dict = session_data.model_dump(mode='json')
            success = await redis_manager.set(session_key, session_dict, ttl=ttl)
            
            if not success:
                logger.error(f"세션 저장 실패: {session_id}")
                return None
            
            # 사용자 세션 목록에 추가
            user_sessions = await self._get_user_sessions_list(session_data.user_id)
            
            # 새 세션 정보 추가
            session_info = {
                "session_id": session_id,
                "created_at": session_data.created_at.isoformat(),
                "ip_address": session_data.ip_address,
                "user_agent": session_data.user_agent
            }
            user_sessions.append(session_info)
            
            # 동시 세션 제한 적용
            if max_concurrent_sessions and len(user_sessions) > max_concurrent_sessions:
                # 오래된 세션 삭제
                sessions_to_remove = user_sessions[:-max_concurrent_sessions]
                for old_session in sessions_to_remove:
                    await self._delete_session_by_id(old_session["session_id"])
                user_sessions = user_sessions[-max_concurrent_sessions:]
            
            # 사용자 세션 목록 업데이트
            await redis_manager.set(
                user_sessions_key, 
                user_sessions, 
                ttl=ttl
            )
            
            logger.info(f"세션 생성 성공: {session_id} (사용자: {session_data.user_id})")
            return session_id
            
        except Exception as e:
            logger.error(f"세션 생성 오류: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """세션 조회"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return None
        
        try:
            session_key = self._get_session_key(session_id)
            session_dict = await redis_manager.get(session_key)
            
            if not session_dict:
                return None
            
            # 세션 만료 확인
            session_data = SessionData(**session_dict)
            if session_data.expires_at < datetime.now():
                # 만료된 세션 삭제
                await self.delete_session(session_id)
                return None
            
            # 마지막 활동 시간 업데이트
            session_data.last_activity = datetime.now()
            await self.update_session(session_id, session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"세션 조회 오류: {e}")
            return None
    
    async def update_session(self, session_id: str, session_data: SessionData) -> bool:
        """세션 업데이트"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            session_key = self._get_session_key(session_id)
            
            # 현재 TTL 확인
            current_data = await redis_manager.get(session_key)
            if not current_data:
                return False
            
            # TTL 계산
            ttl = int((session_data.expires_at - datetime.now()).total_seconds())
            if ttl <= 0:
                await self.delete_session(session_id)
                return False
            
            # 세션 데이터 업데이트
            session_dict = session_data.model_dump(mode='json')
            success = await redis_manager.set(session_key, session_dict, ttl=ttl)
            
            if success:
                logger.debug(f"세션 업데이트 성공: {session_id}")
            else:
                logger.error(f"세션 업데이트 실패: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"세션 업데이트 오류: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # 세션 데이터 조회 (사용자 정보 얻기 위함)
            session_data = await self.get_session(session_id)
            
            # 세션 삭제
            success = await self._delete_session_by_id(session_id)
            
            # 사용자 세션 목록에서 제거
            if session_data:
                await self._remove_from_user_sessions(session_data.user_id, session_id)
            
            return success
            
        except Exception as e:
            logger.error(f"세션 삭제 오류: {e}")
            return False
    
    async def _delete_session_by_id(self, session_id: str) -> bool:
        """세션 ID로 직접 삭제 (내부 메서드)"""
        redis_manager = await get_redis_manager()
        session_key = self._get_session_key(session_id)
        return await redis_manager.delete(session_key)
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션 조회"""
        return await self._get_user_sessions_list(user_id)
    
    async def _get_user_sessions_list(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 세션 목록 조회 (내부 메서드)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return []
        
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            sessions = await redis_manager.get(user_sessions_key)
            return sessions or []
            
        except Exception as e:
            logger.error(f"사용자 세션 목록 조회 오류: {e}")
            return []
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """사용자의 모든 세션 삭제"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 사용자 세션 목록 조회
            user_sessions = await self.get_user_sessions(user_id)
            
            deleted_count = 0
            for session_info in user_sessions:
                session_id = session_info.get("session_id")
                if session_id:
                    success = await self._delete_session_by_id(session_id)
                    if success:
                        deleted_count += 1
            
            # 사용자 세션 목록 삭제
            user_sessions_key = self._get_user_sessions_key(user_id)
            await redis_manager.delete(user_sessions_key)
            
            logger.info(f"사용자 세션 삭제 완료: {user_id}, 삭제된 세션 수: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"사용자 세션 삭제 오류: {e}")
            return 0
    
    async def _remove_from_user_sessions(self, user_id: str, session_id: str):
        """사용자 세션 목록에서 특정 세션 제거"""
        redis_manager = await get_redis_manager()
        
        try:
            user_sessions = await self._get_user_sessions_list(user_id)
            updated_sessions = [
                session for session in user_sessions 
                if session.get("session_id") != session_id
            ]
            
            user_sessions_key = self._get_user_sessions_key(user_id)
            if updated_sessions:
                await redis_manager.set(user_sessions_key, updated_sessions)
            else:
                await redis_manager.delete(user_sessions_key)
                
        except Exception as e:
            logger.error(f"사용자 세션 목록 업데이트 오류: {e}")
    
    async def cleanup_expired_sessions(self) -> int:
        """만료된 세션 정리 (배치 작업용)"""
        # Redis TTL에 의해 자동으로 정리되므로 별도 구현 불필요
        # 필요시 사용자 세션 목록의 유효하지 않은 항목 정리 가능
        pass

# 글로벌 세션 서비스 인스턴스
session_service = SessionService()

async def get_session_service() -> SessionService:
    """세션 서비스 인스턴스 반환"""
    return session_service