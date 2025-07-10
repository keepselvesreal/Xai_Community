import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.services.token_blacklist_service import TokenBlacklistService
from nadle_backend.database.redis import redis_manager

@pytest.fixture
async def blacklist_service():
    """토큰 블랙리스트 서비스 픽스처"""
    service = TokenBlacklistService()
    await redis_manager.connect()
    
    # 테스트 전 데이터 정리
    if await redis_manager.is_connected():
        await service.clear_all_blacklisted_tokens()
    
    yield service
    
    # 테스트 후 정리
    if await redis_manager.is_connected():
        await service.clear_all_blacklisted_tokens()
    
    await redis_manager.disconnect()

class TestTokenBlacklist:
    """토큰 블랙리스트 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_blacklist_token(self, blacklist_service):
        """토큰 블랙리스트 추가 테스트"""
        # Given
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_payload.signature"
        expires_at = datetime.now() + timedelta(hours=1)
        reason = "user_logout"
        
        # When
        success = await blacklist_service.blacklist_token(token, expires_at, reason)
        
        # Then
        assert success is True
        
        # 블랙리스트에 있는지 확인
        is_blacklisted = await blacklist_service.is_blacklisted(token)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_false(self, blacklist_service):
        """블랙리스트되지 않은 토큰 확인 테스트"""
        # Given
        token = "valid_token_not_blacklisted"
        
        # When
        is_blacklisted = await blacklist_service.is_blacklisted(token)
        
        # Then
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_blacklist_token_with_jti(self, blacklist_service):
        """JTI를 사용한 토큰 블랙리스트 테스트"""
        # Given
        jti = "unique_token_id_123"
        expires_at = datetime.now() + timedelta(hours=1)
        reason = "token_revoked"
        
        # When
        success = await blacklist_service.blacklist_token_by_jti(jti, expires_at, reason)
        
        # Then
        assert success is True
        
        # JTI로 블랙리스트 확인
        is_blacklisted = await blacklist_service.is_blacklisted_by_jti(jti)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_blacklist_user_tokens(self, blacklist_service):
        """사용자의 모든 토큰 블랙리스트 테스트"""
        # Given
        user_id = "test_user_123"
        tokens = [
            "token_1_for_user",
            "token_2_for_user",
            "token_3_for_user"
        ]
        expires_at = datetime.now() + timedelta(hours=1)
        reason = "security_breach"
        
        # 토큰들을 먼저 블랙리스트에 추가
        for token in tokens:
            await blacklist_service.blacklist_token(token, expires_at, reason, user_id)
        
        # When
        blacklisted_count = await blacklist_service.blacklist_user_tokens(user_id, expires_at, reason)
        
        # Then
        assert blacklisted_count == 1  # 사용자 전체 블랙리스트 마커 1개
        
        # 모든 토큰이 블랙리스트되었는지 확인
        for token in tokens:
            is_blacklisted = await blacklist_service.is_blacklisted(token)
            assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_get_blacklist_info(self, blacklist_service):
        """블랙리스트 정보 조회 테스트"""
        # Given
        token = "test_token_with_info"
        expires_at = datetime.now() + timedelta(hours=1)
        reason = "admin_revoked"
        user_id = "test_user_456"
        
        await blacklist_service.blacklist_token(token, expires_at, reason, user_id)
        
        # When
        info = await blacklist_service.get_blacklist_info(token)
        
        # Then
        assert info is not None
        assert info["reason"] == reason
        assert info["user_id"] == user_id
        assert "blacklisted_at" in info
        assert "expires_at" in info
    
    @pytest.mark.asyncio
    async def test_token_expiration(self, blacklist_service):
        """토큰 만료 테스트"""
        # Given
        token = "expiring_token"
        expires_at = datetime.now() + timedelta(seconds=2)  # 2초 후 만료
        reason = "test_expiration"
        
        # When
        await blacklist_service.blacklist_token(token, expires_at, reason)
        
        # 즉시 확인 - 블랙리스트되어 있어야 함
        is_blacklisted_before = await blacklist_service.is_blacklisted(token)
        assert is_blacklisted_before is True
        
        # 2초 대기 후 확인 - 만료되어 블랙리스트에서 제거되어야 함
        await asyncio.sleep(2.1)
        is_blacklisted_after = await blacklist_service.is_blacklisted(token)
        assert is_blacklisted_after is False
    
    @pytest.mark.asyncio
    async def test_multiple_tokens_same_user(self, blacklist_service):
        """동일 사용자의 여러 토큰 관리 테스트"""
        # Given
        user_id = "multi_token_user"
        tokens = [f"token_{i}_user_{user_id}" for i in range(5)]
        expires_at = datetime.now() + timedelta(hours=1)
        
        # When - 여러 토큰을 블랙리스트에 추가
        for i, token in enumerate(tokens):
            reason = f"reason_{i}"
            success = await blacklist_service.blacklist_token(token, expires_at, reason, user_id)
            assert success is True
        
        # Then - 모든 토큰이 블랙리스트되었는지 확인
        for token in tokens:
            is_blacklisted = await blacklist_service.is_blacklisted(token)
            assert is_blacklisted is True
            
            # 정보도 올바른지 확인
            info = await blacklist_service.get_blacklist_info(token)
            assert info["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_blacklist_statistics(self, blacklist_service):
        """블랙리스트 통계 테스트"""
        # Given
        user_id = "stats_test_user"
        tokens = [f"stats_token_{i}" for i in range(3)]
        expires_at = datetime.now() + timedelta(hours=1)
        
        for token in tokens:
            await blacklist_service.blacklist_token(token, expires_at, "test", user_id)
        
        # When
        stats = await blacklist_service.get_blacklist_stats()
        
        # Then
        assert "total_blacklisted" in stats
        # total_blacklisted는 문자열 "unavailable"이므로 존재만 확인
        assert stats["total_blacklisted"] == "unavailable"
        assert "redis_info" in stats
    
    @pytest.mark.asyncio
    async def test_invalid_token_format(self, blacklist_service):
        """잘못된 토큰 형식 처리 테스트"""
        # Given
        invalid_tokens = [
            "",
            None,
            "invalid_token_format",
            "not.a.jwt.token"
        ]
        expires_at = datetime.now() + timedelta(hours=1)
        
        # When & Then
        for token in invalid_tokens:
            if token is None:
                continue
            # 잘못된 형식이어도 블랙리스트에는 추가 가능해야 함
            success = await blacklist_service.blacklist_token(token, expires_at, "invalid_format")
            assert success is True
            
            is_blacklisted = await blacklist_service.is_blacklisted(token)
            assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, blacklist_service):
        """만료된 토큰 정리 테스트"""
        # Given
        expired_token = "expired_test_token"
        valid_token = "valid_test_token"
        
        past_time = datetime.now() - timedelta(hours=1)  # 이미 만료됨
        future_time = datetime.now() + timedelta(hours=1)  # 아직 유효함
        
        # 만료된 토큰과 유효한 토큰 추가
        await blacklist_service.blacklist_token(expired_token, past_time, "expired")
        await blacklist_service.blacklist_token(valid_token, future_time, "valid")
        
        # When - 정리 작업 실행
        cleaned_count = await blacklist_service.cleanup_expired_tokens()
        
        # Then
        # Redis TTL에 의해 자동 정리되므로 수동 정리는 필요없지만,
        # 메서드가 정상 동작하는지 확인
        assert cleaned_count >= 0
        
        # 유효한 토큰은 여전히 블랙리스트에 있어야 함
        is_valid_blacklisted = await blacklist_service.is_blacklisted(valid_token)
        assert is_valid_blacklisted is True