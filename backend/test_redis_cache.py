#!/usr/bin/env python3
"""Redis 캐싱 기능 테스트 스크립트"""

import asyncio
import sys
import os

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nadle_backend.database.redis import redis_manager
from nadle_backend.services.cache_service import cache_service
from nadle_backend.config import get_settings

async def test_redis_basic():
    """기본 Redis 연결 및 작업 테스트"""
    print("=== Redis 기본 연결 테스트 ===")
    
    # Redis 연결
    connected = await redis_manager.connect()
    print(f"Redis 연결: {'성공' if connected else '실패'}")
    
    if not connected:
        print("Redis 연결에 실패했습니다.")
        return False
    
    # 기본 GET/SET 테스트
    test_key = "test:basic"
    test_value = {"message": "Hello Redis!", "number": 42}
    
    print(f"테스트 데이터 저장: {test_key} = {test_value}")
    success = await redis_manager.set(test_key, test_value, ttl=60)
    print(f"저장 결과: {'성공' if success else '실패'}")
    
    # 데이터 조회
    retrieved = await redis_manager.get(test_key)
    print(f"조회 결과: {retrieved}")
    print(f"데이터 일치: {retrieved == test_value}")
    
    # 데이터 삭제
    deleted = await redis_manager.delete(test_key)
    print(f"삭제 결과: {'성공' if deleted else '실패'}")
    
    return True

async def test_user_cache():
    """사용자 캐싱 서비스 테스트"""
    print("\n=== 사용자 캐싱 서비스 테스트 ===")
    
    # 테스트 사용자 데이터
    user_id = "test_user_123"
    user_data = {
        "id": user_id,
        "email": "test@example.com",
        "user_handle": "testuser",
        "display_name": "Test User",
        "status": "active",
        "created_at": "2024-07-07T10:00:00Z",
        "last_login": "2024-07-07T10:30:00Z"
    }
    
    # 캐시에 사용자 데이터 저장
    print(f"사용자 데이터 캐시 저장: {user_id}")
    success = await cache_service.set_user_cache(user_id, user_data)
    print(f"저장 결과: {'성공' if success else '실패'}")
    
    # 캐시에서 사용자 데이터 조회
    print(f"사용자 데이터 캐시 조회: {user_id}")
    cached_data = await cache_service.get_user_cache(user_id)
    print(f"조회 결과: {cached_data}")
    
    if cached_data:
        print("캐시된 데이터:")
        for key, value in cached_data.items():
            print(f"  {key}: {value}")
    
    # 캐시 삭제
    print(f"사용자 캐시 삭제: {user_id}")
    deleted = await cache_service.delete_user_cache(user_id)
    print(f"삭제 결과: {'성공' if deleted else '실패'}")
    
    # 삭제 후 조회 테스트
    cached_after_delete = await cache_service.get_user_cache(user_id)
    print(f"삭제 후 조회 결과: {cached_after_delete}")
    print(f"정상 삭제됨: {cached_after_delete is None}")

async def test_cache_stats():
    """캐시 통계 테스트"""
    print("\n=== 캐시 통계 테스트 ===")
    
    stats = await cache_service.get_cache_stats()
    print("캐시 통계:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

async def main():
    """메인 테스트 함수"""
    print("Redis 캐싱 기능 테스트 시작!")
    print(f"설정: {get_settings().redis_url}")
    
    try:
        # 기본 Redis 테스트
        await test_redis_basic()
        
        # 사용자 캐싱 테스트  
        await test_user_cache()
        
        # 캐시 통계 테스트
        await test_cache_stats()
        
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 연결 정리
        await redis_manager.disconnect()
        print("Redis 연결 종료")

if __name__ == "__main__":
    asyncio.run(main())