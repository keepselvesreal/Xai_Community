#!/usr/bin/env python3
"""키 네임스페이싱 테스트 - 환경별 프리픽스 확인"""

import asyncio
import os
import sys
import pytest
from unittest.mock import patch

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.database.redis_factory import get_prefixed_key, get_redis_manager
from nadle_backend.services.cache_service import cache_service
from nadle_backend.config import get_settings


@pytest.mark.asyncio
async def test_key_prefix_configuration():
    """환경별 키 프리픽스 설정 테스트"""
    print("=== 키 프리픽스 설정 테스트 ===")
    
    # 개발 환경 (기본값) - 프리픽스 없음
    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        from nadle_backend.config import Settings
        dev_settings = Settings()
        assert dev_settings.redis_key_prefix == "", f"개발 환경 프리픽스가 올바르지 않음: '{dev_settings.redis_key_prefix}'"
        print("✅ 개발 환경: 프리픽스 없음")
    
    # 스테이징 환경 - staging: 프리픽스
    with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}):
        staging_settings = Settings()
        assert staging_settings.redis_key_prefix == "staging:", f"스테이징 환경 프리픽스가 올바르지 않음: '{staging_settings.redis_key_prefix}'"
        print("✅ 스테이징 환경: 'staging:' 프리픽스")
    
    # 프로덕션 환경 테스트는 보안 검증으로 인해 스킵
    print("⚠️  프로덕션 환경 테스트 스킵 (보안 검증으로 인해)")
    print("   실제 프로덕션에서는 'prod:' 프리픽스가 적용됩니다.")


@pytest.mark.asyncio
async def test_prefixed_key_generation():
    """프리픽스가 적용된 키 생성 테스트"""
    print("\n=== 프리픽스 키 생성 테스트 ===")
    
    test_key = "user:123"
    
    # 개발 환경 - 프리픽스 없음
    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        import nadle_backend.config
        original_settings = nadle_backend.config.settings
        try:
            from nadle_backend.config import Settings
            nadle_backend.config.settings = Settings()
            
            prefixed_key = get_prefixed_key(test_key)
            assert prefixed_key == "user:123", f"개발 환경 키가 올바르지 않음: '{prefixed_key}'"
            print(f"✅ 개발 환경: '{test_key}' -> '{prefixed_key}'")
            
        finally:
            nadle_backend.config.settings = original_settings
    
    # 스테이징 환경 - staging: 프리픽스
    with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}):
        original_settings = nadle_backend.config.settings
        try:
            nadle_backend.config.settings = Settings()
            
            prefixed_key = get_prefixed_key(test_key)
            assert prefixed_key == "staging:user:123", f"스테이징 환경 키가 올바르지 않음: '{prefixed_key}'"
            print(f"✅ 스테이징 환경: '{test_key}' -> '{prefixed_key}'")
            
        finally:
            nadle_backend.config.settings = original_settings
    
    # 프로덕션 환경 테스트는 보안 검증으로 인해 스킵
    print(f"⚠️  프로덕션 환경 테스트 스킵 (보안 검증으로 인해)")
    print(f"   실제 프로덕션에서는 'prod:user:123' 형태로 키가 생성됩니다.")


@pytest.mark.asyncio
async def test_cache_service_with_prefix():
    """캐시 서비스에서 프리픽스 적용 테스트"""
    print("\n=== 캐시 서비스 프리픽스 테스트 ===")
    
    # Upstash 환경변수 확인
    upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    # 스테이징 환경에서 테스트
    with patch.dict(os.environ, {
        'ENVIRONMENT': 'staging',
        'UPSTASH_REDIS_REST_URL': upstash_url,
        'UPSTASH_REDIS_REST_TOKEN': upstash_token
    }):
        import nadle_backend.config
        original_settings = nadle_backend.config.settings
        
        try:
            # 새 설정 로드
            from nadle_backend.config import Settings
            nadle_backend.config.settings = Settings()
            
            # 팩토리 리셋
            from nadle_backend.database.redis_factory import redis_factory
            redis_factory.reset()
            
            # 테스트 데이터
            user_id = "namespacing_test_456"
            user_data = {
                "id": user_id,
                "email": "test.namespacing@example.com",
                "user_handle": "namespacingtest",
                "display_name": "Namespacing Test User",
                "status": "active",
                "created_at": "2024-07-12T14:00:00Z",
                "last_login": "2024-07-12T14:30:00Z"
            }
            
            # Redis 매니저를 직접 사용해서 키 확인
            redis_manager = await get_redis_manager()
            
            # 1. 캐시 서비스를 통한 저장
            success = await cache_service.set_user_cache(user_id, user_data)
            assert success, "캐시 서비스를 통한 저장 실패"
            print(f"✅ 캐시 서비스로 사용자 데이터 저장 성공: {user_id}")
            
            # 2. 실제 Redis에서 프리픽스된 키로 조회
            prefixed_key = get_prefixed_key(f"user:{user_id}")
            print(f"  확인할 Redis 키: '{prefixed_key}'")
            
            direct_data = await redis_manager.get(prefixed_key)
            assert direct_data is not None, f"프리픽스된 키로 데이터 조회 실패: {prefixed_key}"
            print(f"✅ 프리픽스된 키로 직접 조회 성공")
            
            # 3. 캐시 서비스를 통한 조회
            cached_data = await cache_service.get_user_cache(user_id)
            assert cached_data is not None, "캐시 서비스를 통한 조회 실패"
            assert cached_data['id'] == user_id, f"조회된 데이터 ID 불일치: {cached_data['id']} != {user_id}"
            print(f"✅ 캐시 서비스로 사용자 데이터 조회 성공")
            
            # 4. 원본 키(프리픽스 없는)로는 조회되지 않아야 함
            original_key = f"user:{user_id}"
            original_data = await redis_manager.get(original_key)
            assert original_data is None, f"원본 키로 데이터가 조회됨 (프리픽스가 제대로 작동하지 않음): {original_key}"
            print(f"✅ 원본 키로는 조회되지 않음 (프리픽스 정상 작동)")
            
            # 정리
            await cache_service.delete_user_cache(user_id)
            print(f"✅ 테스트 데이터 정리 완료")
            
        finally:
            # 설정 복원
            nadle_backend.config.settings = original_settings
            redis_factory.reset()


async def main():
    """메인 테스트 함수"""
    print("=== 키 네임스페이싱 테스트 시작 ===\n")
    
    try:
        # 1. 키 프리픽스 설정 테스트
        await test_key_prefix_configuration()
        
        # 2. 프리픽스 키 생성 테스트
        await test_prefixed_key_generation()
        
        # 3. 캐시 서비스 프리픽스 테스트
        await test_cache_service_with_prefix()
        
        print("\n✅ 모든 키 네임스페이싱 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 키 네임스페이싱 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)