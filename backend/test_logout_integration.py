#!/usr/bin/env python3
"""로그아웃 및 토큰 무효화 통합 테스트"""

import asyncio
import sys
import os

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nadle_backend.services.auth_service import AuthService
from nadle_backend.services.session_service import get_session_service
from nadle_backend.services.token_blacklist_service import get_token_blacklist_service
from nadle_backend.database.redis import redis_manager
from nadle_backend.utils.jwt import JWTManager, TokenType
from nadle_backend.utils.password import PasswordManager
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.config import get_settings

async def test_logout_integration():
    """로그아웃 및 토큰 무효화 통합 테스트"""
    print("=== 로그아웃 및 토큰 무효화 통합 테스트 시작 ===")
    
    # Redis 연결
    await redis_manager.connect()
    
    # 서비스 초기화
    settings = get_settings()
    jwt_manager = JWTManager(
        secret_key=settings.secret_key,
        algorithm="HS256",
        access_token_expires=settings.access_token_expire,
        refresh_token_expires=settings.refresh_token_expire
    )
    password_manager = PasswordManager()
    user_repository = UserRepository()
    
    auth_service = AuthService(
        user_repository=user_repository,
        jwt_manager=jwt_manager,
        password_manager=password_manager
    )
    
    session_service = await get_session_service()
    blacklist_service = await get_token_blacklist_service()
    
    try:
        # 1. 가상 로그인 (토큰 생성)
        print("\n1. 가상 토큰 생성 테스트")
        
        # 테스트용 payload
        test_payload = {
            "sub": "test_user_12345",
            "email": "test@example.com"
        }
        
        access_token = jwt_manager.create_token(test_payload, TokenType.ACCESS)
        refresh_token = jwt_manager.create_token(test_payload, TokenType.REFRESH)
        
        print(f"Access Token 생성: {access_token[:30]}...")
        print(f"Refresh Token 생성: {refresh_token[:30]}...")
        
        # 2. 토큰 유효성 검증
        print("\n2. 토큰 유효성 검증 테스트")
        
        is_valid_before = await auth_service.verify_token_validity(access_token)
        print(f"로그아웃 전 토큰 유효성: {is_valid_before}")
        
        # 3. 로그아웃 수행
        print("\n3. 로그아웃 수행 테스트")
        
        logout_result = await auth_service.logout(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=test_payload["sub"]
        )
        
        print(f"로그아웃 결과: {logout_result}")
        
        # 4. 로그아웃 후 토큰 유효성 검증
        print("\n4. 로그아웃 후 토큰 유효성 검증 테스트")
        
        is_valid_after = await auth_service.verify_token_validity(access_token)
        print(f"로그아웃 후 토큰 유효성: {is_valid_after}")
        
        # 5. 블랙리스트 직접 확인
        print("\n5. 토큰 블랙리스트 직접 확인")
        
        is_access_blacklisted = await blacklist_service.is_blacklisted(access_token)
        is_refresh_blacklisted = await blacklist_service.is_blacklisted(refresh_token)
        
        print(f"Access Token 블랙리스트 여부: {is_access_blacklisted}")
        print(f"Refresh Token 블랙리스트 여부: {is_refresh_blacklisted}")
        
        # 6. 전체 세션 로그아웃 테스트
        print("\n6. 전체 세션 로그아웃 테스트")
        
        # 새로운 토큰 생성
        new_access_token = jwt_manager.create_token(test_payload, TokenType.ACCESS)
        new_refresh_token = jwt_manager.create_token(test_payload, TokenType.REFRESH)
        
        print(f"새 Access Token 생성: {new_access_token[:30]}...")
        
        # 전체 로그아웃 수행
        logout_all_result = await auth_service.logout_all_sessions(test_payload["sub"])
        print(f"전체 로그아웃 결과: {logout_all_result}")
        
        # 새 토큰도 무효화되었는지 확인
        is_new_token_valid = await auth_service.verify_token_validity(new_access_token)
        print(f"새 토큰 유효성 (전체 로그아웃 후): {is_new_token_valid}")
        
        # 7. 사용자 전체 블랙리스트 확인
        print("\n7. 사용자 전체 블랙리스트 확인")
        
        is_user_blacklisted = await blacklist_service.is_user_blacklisted(test_payload["sub"])
        print(f"사용자 전체 블랙리스트 여부: {is_user_blacklisted}")
        
        # 8. 결과 요약
        print("\n=== 테스트 결과 요약 ===")
        print(f"✅ 토큰 생성: 성공")
        print(f"✅ 로그아웃 전 토큰 유효성: {is_valid_before}")
        print(f"✅ 로그아웃 후 토큰 무효화: {not is_valid_after}")
        print(f"✅ 토큰 블랙리스트 등록: {is_access_blacklisted and is_refresh_blacklisted}")
        print(f"✅ 전체 세션 로그아웃: {logout_all_result['status'] == 'success'}")
        print(f"✅ 사용자 전체 블랙리스트: {is_user_blacklisted}")
        
        # 모든 테스트 통과 여부 확인
        all_tests_passed = (
            is_valid_before and 
            not is_valid_after and 
            is_access_blacklisted and 
            is_refresh_blacklisted and
            logout_all_result['status'] == 'success' and
            is_user_blacklisted
        )
        
        if all_tests_passed:
            print("\n🎉 모든 통합 테스트가 성공적으로 통과했습니다!")
        else:
            print("\n❌ 일부 테스트가 실패했습니다.")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 정리 작업
        await blacklist_service.clear_all_blacklisted_tokens()
        await session_service.delete_user_sessions(test_payload["sub"])
        await redis_manager.disconnect()
        print("\n정리 작업 완료")

async def main():
    """메인 함수"""
    success = await test_logout_integration()
    if success:
        print("\n✅ 로그아웃 및 토큰 무효화 기능이 정상적으로 작동합니다!")
    else:
        print("\n❌ 로그아웃 및 토큰 무효화 기능에 문제가 있습니다.")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)