import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.services.session_service import SessionService, SessionData
from nadle_backend.database.redis import redis_manager

@pytest.fixture
async def session_service():
    """세션 서비스 픽스처"""
    service = SessionService()
    await redis_manager.connect()
    
    # 테스트 전 데이터 정리
    if await redis_manager.is_connected():
        # 테스트 사용자의 기존 세션 정리
        await service.delete_user_sessions("test_user_123")
    
    yield service
    
    # 테스트 후 정리
    if await redis_manager.is_connected():
        await service.delete_user_sessions("test_user_123")
    
    await redis_manager.disconnect()

@pytest.fixture
def mock_user_data():
    """테스트용 사용자 데이터"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "user_handle": "testuser"
    }

@pytest.fixture
def mock_session_data():
    """테스트용 세션 데이터"""
    return SessionData(
        user_id="test_user_123",
        email="test@example.com",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0 Test Browser",
        expires_at=datetime.now() + timedelta(hours=1)
    )

class TestSessionStore:
    """세션 스토어 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_service, mock_session_data):
        """세션 생성 테스트"""
        # Given
        session_data = mock_session_data
        
        # When
        session_id = await session_service.create_session(session_data)
        
        # Then
        assert session_id is not None
        assert len(session_id) > 0
        
        # 세션이 실제로 저장되었는지 확인
        retrieved = await session_service.get_session(session_id)
        assert retrieved is not None
        assert retrieved.user_id == session_data.user_id
        assert retrieved.email == session_data.email
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_service, mock_session_data):
        """세션 조회 테스트"""
        # Given
        session_id = await session_service.create_session(mock_session_data)
        
        # When
        retrieved = await session_service.get_session(session_id)
        
        # Then
        assert retrieved is not None
        assert retrieved.user_id == mock_session_data.user_id
        assert retrieved.email == mock_session_data.email
        assert retrieved.access_token == mock_session_data.access_token
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_service):
        """존재하지 않는 세션 조회 테스트"""
        # When
        retrieved = await session_service.get_session("nonexistent_session_id")
        
        # Then
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_update_session(self, session_service, mock_session_data):
        """세션 업데이트 테스트"""
        # Given
        session_id = await session_service.create_session(mock_session_data)
        new_access_token = "new_access_token"
        
        # When
        mock_session_data.access_token = new_access_token
        success = await session_service.update_session(session_id, mock_session_data)
        
        # Then
        assert success is True
        
        # 업데이트된 데이터 확인
        retrieved = await session_service.get_session(session_id)
        assert retrieved.access_token == new_access_token
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_service, mock_session_data):
        """세션 삭제 테스트"""
        # Given
        session_id = await session_service.create_session(mock_session_data)
        
        # When
        success = await session_service.delete_session(session_id)
        
        # Then
        assert success is True
        
        # 삭제된 세션 조회 시 None 반환 확인
        retrieved = await session_service.get_session(session_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, session_service):
        """사용자별 세션 목록 조회 테스트"""
        # Given
        user_id = "test_user_123"
        session_data_1 = SessionData(
            user_id=user_id,
            email="test@example.com",
            access_token="token1",
            refresh_token="refresh1",
            ip_address="127.0.0.1",
            user_agent="Browser 1",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        session_data_2 = SessionData(
            user_id=user_id,
            email="test@example.com",
            access_token="token2",
            refresh_token="refresh2",
            ip_address="192.168.1.1",
            user_agent="Browser 2",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # When
        session_id_1 = await session_service.create_session(session_data_1)
        session_id_2 = await session_service.create_session(session_data_2)
        
        user_sessions = await session_service.get_user_sessions(user_id)
        
        # Then
        assert len(user_sessions) == 2
        session_ids = [session["session_id"] for session in user_sessions]
        assert session_id_1 in session_ids
        assert session_id_2 in session_ids
    
    @pytest.mark.asyncio
    async def test_delete_user_sessions(self, session_service):
        """사용자의 모든 세션 삭제 테스트"""
        # Given
        user_id = "test_user_123"
        session_data_1 = SessionData(
            user_id=user_id,
            email="test@example.com",
            access_token="token1",
            refresh_token="refresh1",
            ip_address="127.0.0.1",
            user_agent="Browser 1",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        session_data_2 = SessionData(
            user_id=user_id,
            email="test@example.com",
            access_token="token2",
            refresh_token="refresh2",
            ip_address="192.168.1.1",
            user_agent="Browser 2",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        await session_service.create_session(session_data_1)
        await session_service.create_session(session_data_2)
        
        # When
        deleted_count = await session_service.delete_user_sessions(user_id)
        
        # Then
        assert deleted_count == 2
        
        # 모든 세션이 삭제되었는지 확인
        user_sessions = await session_service.get_user_sessions(user_id)
        assert len(user_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_session_expiration(self, session_service):
        """세션 만료 테스트"""
        # Given
        expired_session_data = SessionData(
            user_id="test_user_123",
            email="test@example.com",
            access_token="expired_token",
            refresh_token="expired_refresh",
            ip_address="127.0.0.1",
            user_agent="Test Browser",
            expires_at=datetime.now() - timedelta(hours=1)  # 이미 만료됨
        )
        
        # When
        session_id = await session_service.create_session(expired_session_data, ttl=1)  # 1초 TTL
        
        # 1초 대기
        await asyncio.sleep(1.1)
        
        # Then
        retrieved = await session_service.get_session(session_id)
        assert retrieved is None  # 만료되어 자동 삭제됨
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions_limit(self, session_service):
        """동시 세션 제한 테스트"""
        # Given
        user_id = "test_user_123"
        max_sessions = 3
        
        # When - 제한보다 많은 세션 생성 시도
        session_ids = []
        for i in range(max_sessions + 2):  # 5개 세션 생성 시도
            session_data = SessionData(
                user_id=user_id,
                email="test@example.com",
                access_token=f"token_{i}",
                refresh_token=f"refresh_{i}",
                ip_address=f"192.168.1.{i}",
                user_agent=f"Browser {i}",
                expires_at=datetime.now() + timedelta(hours=1)
            )
            session_id = await session_service.create_session(
                session_data, 
                max_concurrent_sessions=max_sessions
            )
            session_ids.append(session_id)
        
        # Then
        user_sessions = await session_service.get_user_sessions(user_id)
        assert len(user_sessions) <= max_sessions  # 최대 세션 수 제한 준수
        
        # 가장 최근 세션들만 유지되었는지 확인
        recent_session_ids = [session["session_id"] for session in user_sessions]
        for session_id in session_ids[-max_sessions:]:  # 마지막 3개 세션
            assert session_id in recent_session_ids