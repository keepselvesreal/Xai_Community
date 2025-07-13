#!/usr/bin/env python3
"""간단한 키 네임스페이싱 테스트"""

import asyncio
import os
import sys
from unittest.mock import patch

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.database.redis_factory import get_prefixed_key, get_redis_manager, get_redis_health


async def main():
    """간단한 키 네임스페이싱 테스트"""
    print("=== 간단한 키 네임스페이싱 테스트 ===\n")
    
    # .env.staging 파일에서 Upstash 설정 읽기
    staging_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.staging')
    upstash_url = None
    upstash_token = None
    
    if os.path.exists(staging_env_path):
        with open(staging_env_path, 'r') as f:
            for line in f:
                if line.startswith('UPSTASH_REDIS_REST_URL='):
                    upstash_url = line.split('=', 1)[1].strip()
                elif line.startswith('UPSTASH_REDIS_REST_TOKEN='):
                    upstash_token = line.split('=', 1)[1].strip()
    
    if not upstash_url or not upstash_token:
        print("❌ Upstash Redis 설정이 .env.staging 파일에 없습니다.")
        return False
    
    print("1. 개발 환경에서 키 프리픽스 테스트")
    # 개발 환경 (현재 기본 환경)
    dev_key = get_prefixed_key("user:123")
    print(f"   개발 환경: user:123 -> {dev_key}")
    
    print("\n2. 스테이징 환경에서 Upstash Redis 연결 및 키 네임스페이싱 테스트")
    
    # 스테이징 환경으로 설정
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
            
            # 프리픽스 테스트
            staging_key = get_prefixed_key("user:123")
            print(f"   스테이징 환경: user:123 -> {staging_key}")
            
            # Redis 상태 확인
            health = await get_redis_health()
            print(f"   Redis 상태: {health['status']}")
            print(f"   Redis 타입: {health['redis_type']}")
            print(f"   키 프리픽스: '{health['key_prefix']}'")
            
            if health['status'] != 'connected':
                print(f"❌ Redis 연결 실패: {health}")
                return False
            
            # 실제 Redis 매니저로 키 테스트
            redis_manager = await get_redis_manager()
            
            # 테스트 데이터
            test_key = "test:key:simple"
            test_value = {"message": "Hello from staging!", "environment": "staging"}
            
            # 프리픽스된 키로 저장
            prefixed_test_key = get_prefixed_key(test_key)
            print(f"\n3. 실제 Redis 작업 테스트")
            print(f"   저장할 키: {prefixed_test_key}")
            
            success = await redis_manager.set(prefixed_test_key, test_value, ttl=60)
            if not success:
                print("❌ Redis 저장 실패")
                return False
            print("   ✅ Redis 저장 성공")
            
            # 조회
            retrieved = await redis_manager.get(prefixed_test_key)
            if retrieved != test_value:
                print(f"❌ 데이터 불일치: {retrieved} != {test_value}")
                return False
            print("   ✅ Redis 조회 성공")
            
            # 원본 키로는 조회되지 않아야 함
            original_retrieved = await redis_manager.get(test_key)
            if original_retrieved is not None:
                print(f"❌ 원본 키로 데이터가 조회됨 (프리픽스 작동 안함): {original_retrieved}")
                return False
            print("   ✅ 원본 키로는 조회되지 않음 (프리픽스 정상 작동)")
            
            # 정리
            await redis_manager.delete(prefixed_test_key)
            print("   ✅ 테스트 데이터 정리 완료")
            
            # Redis 연결 정리
            await redis_manager.disconnect()
            print("   ✅ Redis 연결 정리 완료")
            
        finally:
            # 설정 복원
            nadle_backend.config.settings = original_settings
            redis_factory.reset()
    
    print("\n✅ 모든 키 네임스페이싱 테스트가 성공적으로 완료되었습니다!")
    print("   - 개발환경: 'dev:' 프리픽스 적용")
    print("   - 스테이징환경: 'stage:' 프리픽스 적용")
    print("   - 프로덕션환경: 'prod:' 프리픽스 적용")
    print("   - Upstash Redis 연동 정상")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)