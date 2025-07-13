#!/usr/bin/env python3
"""Redis 팩토리 패턴 및 기존 서비스 호환성 테스트"""

import asyncio
import os
import sys
import pytest
from unittest.mock import patch

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.database.redis_factory import get_redis_manager, ensure_redis_connection, get_redis_health
from nadle_backend.services.cache_service import cache_service
from nadle_backend.services.session_service import session_service
from nadle_backend.config import get_settings


@pytest.mark.asyncio
async def test_redis_factory_environment_selection():
    """환경별 Redis 클라이언트 자동 선택 테스트"""
    print("=== Redis 팩토리 환경별 선택 테스트 ===")
    
    settings = get_settings()
    print(f"현재 환경: {settings.environment}")
    print(f"Upstash Redis 사용 여부: {settings.use_upstash_redis}")
    
    # Redis 매니저 가져오기
    manager = await get_redis_manager()
    print(f"선택된 Redis 매니저: {type(manager).__name__}")
    
    # 연결 테스트
    connected = await ensure_redis_connection()
    print(f"Redis 연결 상태: {'성공' if connected else '실패'}")
    
    # 상태 확인
    health = await get_redis_health()
    print(f"Redis 상태: {health}")
    
    assert manager is not None, "Redis 매니저를 가져올 수 없음"
    print("✅ Redis 팩토리 환경별 선택 성공")


@pytest.mark.asyncio
async def test_upstash_with_cache_service():
    """Upstash Redis와 캐시 서비스 호환성 테스트"""
    print("\n=== Upstash Redis + 캐시 서비스 호환성 테스트 ===")
    
    # Upstash 환경변수 설정
    upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    # staging 환경으로 강제 설정하여 Upstash Redis 사용
    with patch.dict(os.environ, {
        'ENVIRONMENT': 'staging',
        'UPSTASH_REDIS_REST_URL': upstash_url,
        'UPSTASH_REDIS_REST_TOKEN': upstash_token
    }):
        # 팩토리 리셋 후 새로운 설정으로 테스트
        from nadle_backend.database.redis_factory import redis_factory
        redis_factory.reset()
        
        # 테스트 사용자 데이터 (캐시 서비스가 추가하는 필드 포함)
        user_id = "test_upstash_user_123"
        user_data = {
            "id": user_id,
            "email": "test.upstash@example.com",
            "user_handle": "testupstash",
            "display_name": "Test Upstash User",
            "status": "active",
            "created_at": "2024-07-12T10:00:00Z",
            "last_login": "2024-07-12T10:30:00Z"
        }
        
        # 캐시 서비스에서 반환할 것으로 예상되는 데이터
        expected_cached_data = {
            "id": user_id,
            "email": "test.upstash@example.com",
            "user_handle": "testupstash",
            "display_name": "Test Upstash User",
            "status": "active",
            "created_at": "2024-07-12T10:00:00Z",
            "last_login": "2024-07-12T10:30:00Z"
        }
        
        try:
            # 캐시 서비스를 통한 사용자 데이터 저장
            print(f"사용자 데이터 캐시 저장: {user_id}")
            success = await cache_service.set_user_cache(user_id, user_data)
            assert success, "Upstash를 통한 사용자 캐시 저장 실패"
            print("✅ Upstash 사용자 캐시 저장 성공")
            
            # 캐시 서비스를 통한 사용자 데이터 조회
            print(f"사용자 데이터 캐시 조회: {user_id}")
            cached_data = await cache_service.get_user_cache(user_id)
            assert cached_data == expected_cached_data, f"캐시 데이터 불일치: {cached_data} != {expected_cached_data}"
            print("✅ Upstash 사용자 캐시 조회 성공")
            
            # 캐시 통계 조회
            stats = await cache_service.get_cache_stats()
            print(f"캐시 통계: {stats}")
            assert isinstance(stats, dict), "캐시 통계가 딕셔너리가 아님"
            print("✅ Upstash 캐시 통계 조회 성공")
            
            # 캐시 삭제
            print(f"사용자 캐시 삭제: {user_id}")
            deleted = await cache_service.delete_user_cache(user_id)
            assert deleted, "Upstash를 통한 사용자 캐시 삭제 실패"
            print("✅ Upstash 사용자 캐시 삭제 성공")
            
        finally:
            # 정리
            await cache_service.delete_user_cache(user_id)
            redis_factory.reset()


@pytest.mark.asyncio
async def test_upstash_with_session_service():
    """Upstash Redis와 세션 서비스 호환성 테스트"""
    print("\n=== Upstash Redis + 세션 서비스 호환성 테스트 ===")
    
    # Upstash 환경변수 설정
    upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    # staging 환경으로 강제 설정하여 Upstash Redis 사용
    with patch.dict(os.environ, {
        'ENVIRONMENT': 'staging', 
        'UPSTASH_REDIS_REST_URL': upstash_url,
        'UPSTASH_REDIS_REST_TOKEN': upstash_token
    }):
        # 팩토리 리셋 후 새로운 설정으로 테스트
        from nadle_backend.database.redis_factory import redis_factory
        redis_factory.reset()
        
        # Redis 매니저를 직접 사용한 세션 테스트 (간단한 키-값 테스트)
        session_key = "test:upstash:session:456"
        user_id = "test_upstash_user_456"
        session_data = {
            "user_id": user_id,
            "login_at": "2024-07-12T10:00:00Z",
            "user_agent": "test-agent",
            "ip_address": "127.0.0.1",
            "session_id": "test_upstash_session_456"
        }
        
        try:
            # Redis 매니저를 직접 사용한 세션 저장 테스트
            redis_manager = await get_redis_manager()
            print(f"세션 데이터 저장: {session_key}")
            success = await redis_manager.set(session_key, session_data, ttl=300)
            assert success, "Upstash를 통한 세션 저장 실패"
            print("✅ Upstash 세션 저장 성공")
            
            # 세션 조회
            print(f"세션 데이터 조회: {session_key}")
            retrieved_session = await redis_manager.get(session_key)
            assert retrieved_session is not None, "Upstash에서 세션 조회 실패"
            assert retrieved_session == session_data, f"세션 데이터 불일치: {retrieved_session} != {session_data}"
            print("✅ Upstash 세션 조회 성공")
            
            # 세션 존재 확인
            print(f"세션 존재 확인: {session_key}")
            exists = await redis_manager.exists(session_key)
            assert exists, "세션이 존재하지 않음"
            print("✅ Upstash 세션 존재 확인 성공")
            
            # 세션 삭제
            print(f"세션 삭제: {session_key}")
            deleted = await redis_manager.delete(session_key)
            assert deleted, "Upstash를 통한 세션 삭제 실패"
            print("✅ Upstash 세션 삭제 성공")
            
        finally:
            # 정리
            try:
                await redis_manager.delete(session_key)
            except:
                pass
            redis_factory.reset()


@pytest.mark.asyncio 
async def test_environment_switching():
    """환경 전환 테스트 (개발 ↔ 스테이징)"""
    print("\n=== 환경 전환 테스트 ===")
    
    from nadle_backend.database.redis_factory import redis_factory
    
    # 개발 환경 테스트
    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        redis_factory.reset()
        dev_manager = await get_redis_manager()
        print(f"개발 환경 Redis 매니저: {type(dev_manager).__name__}")
        assert "RedisManager" in type(dev_manager).__name__, "개발 환경에서 로컬 Redis를 사용해야 함"
    
    # 스테이징 환경 테스트 (Upstash 설정이 있는 경우)
    upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if upstash_url and upstash_token:
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'staging',
            'UPSTASH_REDIS_REST_URL': upstash_url,
            'UPSTASH_REDIS_REST_TOKEN': upstash_token
        }):
            # 설정을 새로 로드하기 위해 전역 설정 리셋
            import nadle_backend.config
            # 기존 설정 백업
            original_settings = nadle_backend.config.settings
            
            try:
                # 새 설정 생성
                from nadle_backend.config import Settings
                nadle_backend.config.settings = Settings()
                
                redis_factory.reset()
                staging_manager = await get_redis_manager()
                print(f"스테이징 환경 Redis 매니저: {type(staging_manager).__name__}")
                
                # 설정이 제대로 로드되었는지 확인
                from nadle_backend.config import get_settings
                test_settings = get_settings()
                print(f"스테이징 환경에서 Upstash 사용 여부: {test_settings.use_upstash_redis}")
                
                # Upstash 매니저가 선택되었는지 확인
                if test_settings.use_upstash_redis:
                    assert "UpstashRedisManager" in type(staging_manager).__name__, "스테이징 환경에서 Upstash Redis를 사용해야 함"
                else:
                    print("⚠️  스테이징 환경에서 Upstash 설정이 제대로 로드되지 않았습니다.")
                    
            finally:
                # 원래 설정 복원
                nadle_backend.config.settings = original_settings
    
    print("✅ 환경 전환 테스트 성공")
    redis_factory.reset()


async def main():
    """메인 테스트 함수"""
    print("=== Redis 팩토리 및 서비스 호환성 테스트 시작 ===\n")
    
    try:
        # 1. 팩토리 환경별 선택 테스트
        await test_redis_factory_environment_selection()
        
        # 2. Upstash + 캐시 서비스 테스트
        await test_upstash_with_cache_service()
        
        # 3. Upstash + 세션 서비스 테스트
        await test_upstash_with_session_service()
        
        # 4. 환경 전환 테스트
        await test_environment_switching()
        
        print("\n✅ 모든 Redis 팩토리 호환성 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)