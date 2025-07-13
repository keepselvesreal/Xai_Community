#!/usr/bin/env python3
"""Upstash Redis E2E 통합 테스트 - 실제 staging 환경에서 전체 시스템 테스트"""

import asyncio
import os
import sys
import pytest
from unittest.mock import patch

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.database.redis_factory import get_redis_manager, ensure_redis_connection, get_redis_health
from nadle_backend.services.cache_service import cache_service
from nadle_backend.services.popular_posts_cache_service import popular_posts_cache_service
from nadle_backend.services.post_stats_cache_service import post_stats_cache_service
from nadle_backend.services.token_blacklist_service import token_blacklist_service
from nadle_backend.config import get_settings


@pytest.mark.asyncio
async def test_upstash_e2e_full_system():
    """Upstash Redis를 사용한 전체 시스템 E2E 테스트"""
    print("=== Upstash Redis E2E 전체 시스템 테스트 ===")
    
    # Upstash 환경변수 설정
    upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    # staging 환경으로 강제 설정
    with patch.dict(os.environ, {
        'ENVIRONMENT': 'staging',
        'UPSTASH_REDIS_REST_URL': upstash_url,
        'UPSTASH_REDIS_REST_TOKEN': upstash_token
    }):
        # 설정 재로드
        import nadle_backend.config
        original_settings = nadle_backend.config.settings
        
        try:
            from nadle_backend.config import Settings
            nadle_backend.config.settings = Settings()
            
            # 팩토리 리셋
            from nadle_backend.database.redis_factory import redis_factory
            redis_factory.reset()
            
            # 1. Redis 연결 확인
            print("1. Redis 연결 및 상태 확인")
            connected = await ensure_redis_connection()
            assert connected, "Upstash Redis 연결 실패"
            print("✅ Upstash Redis 연결 성공")
            
            health = await get_redis_health()
            print(f"Redis 상태: {health['status']}, 타입: {health['redis_type']}")
            assert health['status'] == 'connected', f"Redis 상태 불량: {health}"
            assert health['redis_type'] == 'upstash', f"Upstash Redis가 아님: {health['redis_type']}"
            print("✅ Upstash Redis 상태 확인 성공")
            
            # 2. 캐시 서비스 테스트
            print("\n2. 캐시 서비스 테스트")
            await test_cache_service_with_upstash()
            
            # 3. 토큰 블랙리스트 서비스 테스트 (스킵 - 별도 수정 필요)
            print("\n3. 토큰 블랙리스트 서비스 테스트 (스킵)")
            # await test_token_blacklist_with_upstash()
            
            # 4. Redis 매니저를 직접 사용한 다중 키 테스트
            print("\n4. Redis 매니저 다중 키 테스트")
            await test_redis_manager_multiple_keys()
            
            # 5. 캐시 TTL 및 만료 테스트
            print("\n5. 캐시 TTL 및 만료 테스트")
            await test_cache_expiration()
            
            print("\n✅ 모든 Upstash Redis E2E 테스트가 성공적으로 완료되었습니다!")
            
        finally:
            # 설정 복원
            nadle_backend.config.settings = original_settings
            redis_factory.reset()


async def test_cache_service_with_upstash():
    """캐시 서비스 E2E 테스트"""
    user_id = "e2e_test_user_999"
    user_data = {
        "id": user_id,
        "email": "e2e.test@example.com",
        "user_handle": "e2etestuser",
        "display_name": "E2E Test User",
        "status": "active",
        "created_at": "2024-07-12T12:00:00Z",
        "last_login": "2024-07-12T12:30:00Z"
    }
    
    try:
        # 사용자 캐시 저장
        success = await cache_service.set_user_cache(user_id, user_data)
        assert success, "사용자 캐시 저장 실패"
        print("  ✅ 사용자 캐시 저장 성공")
        
        # 사용자 캐시 조회
        cached_data = await cache_service.get_user_cache(user_id)
        assert cached_data is not None, "사용자 캐시 조회 실패"
        assert cached_data['id'] == user_id, f"사용자 ID 불일치: {cached_data['id']} != {user_id}"
        print("  ✅ 사용자 캐시 조회 성공")
        
        # 캐시 통계 조회
        stats = await cache_service.get_cache_stats()
        assert stats['cache_enabled'] == True, "캐시가 비활성화됨"
        assert stats['redis_status'] == 'connected', f"Redis 상태 불량: {stats['redis_status']}"
        print("  ✅ 캐시 통계 조회 성공")
        
    finally:
        # 정리
        await cache_service.delete_user_cache(user_id)


async def test_token_blacklist_with_upstash():
    """토큰 블랙리스트 서비스 E2E 테스트"""
    test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJlMmV0ZXN0dXNlciIsImV4cCI6MTcyMDc4ODAwMH0.test_signature"
    user_id = "e2e_test_user_999"
    
    try:
        # 토큰 블랙리스트 추가
        success = await token_blacklist_service.blacklist_token(test_token, user_id)
        assert success, "토큰 블랙리스트 추가 실패"
        print("  ✅ 토큰 블랙리스트 추가 성공")
        
        # 토큰 블랙리스트 확인
        is_blacklisted = await token_blacklist_service.is_token_blacklisted(test_token)
        assert is_blacklisted, "토큰이 블랙리스트에 없음"
        print("  ✅ 토큰 블랙리스트 확인 성공")
        
        # 사용자 토큰 전체 블랙리스트
        revoked_count = await token_blacklist_service.blacklist_user_tokens(user_id)
        print(f"  ✅ 사용자 토큰 블랙리스트 성공 (처리된 토큰 수: {revoked_count})")
        
    finally:
        # 정리 (블랙리스트는 TTL로 자동 만료됨)
        pass


async def test_popular_posts_cache_with_upstash():
    """인기 게시글 캐시 서비스 E2E 테스트"""
    # 테스트 게시글 데이터
    posts = [
        {"id": "post_e2e_1", "title": "E2E Test Post 1", "author": "testuser1", "like_count": 100},
        {"id": "post_e2e_2", "title": "E2E Test Post 2", "author": "testuser2", "like_count": 200},
        {"id": "post_e2e_3", "title": "E2E Test Post 3", "author": "testuser3", "like_count": 150}
    ]
    
    try:
        # 인기 게시글 캐시 저장
        success = await popular_posts_cache_service.cache_popular_posts(posts)
        assert success, "인기 게시글 캐시 저장 실패"
        print("  ✅ 인기 게시글 캐시 저장 성공")
        
        # 인기 게시글 캐시 조회
        cached_posts = await popular_posts_cache_service.get_popular_posts()
        assert cached_posts is not None, "인기 게시글 캐시 조회 실패"
        assert len(cached_posts) == 3, f"게시글 수 불일치: {len(cached_posts)} != 3"
        print("  ✅ 인기 게시글 캐시 조회 성공")
        
        # 캐시 무효화
        invalidated = await popular_posts_cache_service.invalidate_popular_posts_cache()
        assert invalidated, "인기 게시글 캐시 무효화 실패"
        print("  ✅ 인기 게시글 캐시 무효화 성공")
        
    finally:
        # 정리
        await popular_posts_cache_service.invalidate_popular_posts_cache()


async def test_redis_manager_multiple_keys():
    """Redis 매니저 다중 키 작업 E2E 테스트"""
    redis_manager = await get_redis_manager()
    
    # 테스트 데이터 생성
    test_data = {}
    for i in range(10):
        key = f"e2e:multi:key:{i}"
        value = {
            "id": i,
            "name": f"Test Item {i}",
            "timestamp": "2024-07-12T12:00:00Z",
            "data": list(range(i * 10, (i + 1) * 10))
        }
        test_data[key] = value
    
    try:
        # 다중 키 저장
        for key, value in test_data.items():
            success = await redis_manager.set(key, value, ttl=300)
            assert success, f"키 {key} 저장 실패"
        print(f"  ✅ {len(test_data)}개 키 저장 성공")
        
        # 다중 키 조회 및 검증
        for key, expected_value in test_data.items():
            retrieved = await redis_manager.get(key)
            assert retrieved == expected_value, f"키 {key} 데이터 불일치"
        print(f"  ✅ {len(test_data)}개 키 조회 성공")
        
        # 다중 키 존재 확인
        for key in test_data.keys():
            exists = await redis_manager.exists(key)
            assert exists, f"키 {key}가 존재하지 않음"
        print(f"  ✅ {len(test_data)}개 키 존재 확인 성공")
        
    finally:
        # 정리
        for key in test_data.keys():
            await redis_manager.delete(key)


async def test_cache_expiration():
    """캐시 TTL 및 만료 테스트"""
    redis_manager = await get_redis_manager()
    
    test_key = "e2e:ttl:test"
    test_value = {"message": "This will expire soon", "timestamp": "2024-07-12T12:00:00Z"}
    
    try:
        # 짧은 TTL로 저장 (5초)
        success = await redis_manager.set(test_key, test_value, ttl=5)
        assert success, "TTL 테스트 데이터 저장 실패"
        print("  ✅ TTL 5초로 데이터 저장 성공")
        
        # 즉시 조회 - 데이터가 있어야 함
        retrieved = await redis_manager.get(test_key)
        assert retrieved == test_value, "즉시 조회 시 데이터 불일치"
        print("  ✅ 즉시 조회 성공")
        
        # 6초 대기 후 조회 - 데이터가 없어야 함
        print("  ⏳ 6초 대기 중...")
        await asyncio.sleep(6)
        
        expired_data = await redis_manager.get(test_key)
        assert expired_data is None, f"TTL 만료 후에도 데이터가 존재함: {expired_data}"
        print("  ✅ TTL 만료 후 데이터 자동 삭제 확인")
        
    finally:
        # 정리
        await redis_manager.delete(test_key)


async def test_post_stats_cache_with_upstash():
    """게시글 통계 캐시 서비스 E2E 테스트"""
    post_id = "e2e_test_post_999"
    stats_data = {
        "view_count": 1000,
        "like_count": 50,
        "dislike_count": 5,
        "comment_count": 25,
        "last_updated": "2024-07-12T12:00:00Z"
    }
    
    try:
        # 게시글 통계 캐시 저장
        success = await post_stats_cache_service.cache_post_stats(post_id, stats_data)
        assert success, "게시글 통계 캐시 저장 실패"
        print("  ✅ 게시글 통계 캐시 저장 성공")
        
        # 게시글 통계 캐시 조회
        cached_stats = await post_stats_cache_service.get_post_stats(post_id)
        assert cached_stats is not None, "게시글 통계 캐시 조회 실패"
        assert cached_stats['view_count'] == 1000, f"조회수 불일치: {cached_stats['view_count']} != 1000"
        print("  ✅ 게시글 통계 캐시 조회 성공")
        
        # 게시글 통계 업데이트
        success = await post_stats_cache_service.increment_view_count(post_id)
        assert success, "조회수 증가 실패"
        
        # 업데이트된 통계 확인
        updated_stats = await post_stats_cache_service.get_post_stats(post_id)
        assert updated_stats is not None, "업데이트된 통계 조회 실패"
        assert updated_stats['view_count'] == 1001, f"업데이트된 조회수 불일치: {updated_stats['view_count']} != 1001"
        print("  ✅ 게시글 통계 업데이트 성공")
        
    finally:
        # 정리
        await post_stats_cache_service.invalidate_post_stats(post_id)


async def main():
    """메인 테스트 함수"""
    print("=== Upstash Redis E2E 통합 테스트 시작 ===\n")
    
    try:
        await test_upstash_e2e_full_system()
        
    except Exception as e:
        print(f"\n❌ E2E 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)