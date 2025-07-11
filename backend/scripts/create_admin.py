#!/usr/bin/env python3
"""
관리자 계정 생성 스크립트

사용법:
    python scripts/create_admin.py
    
또는 환경변수로 설정:
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=your_password python scripts/create_admin.py
"""

import asyncio
import sys
import os
import getpass
from typing import Optional

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nadle_backend.config import settings
from nadle_backend.models.core import User
from nadle_backend.utils.password import PasswordManager
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import EmailStr, ValidationError


async def create_admin_user(
    email: str, 
    password: str,
    user_handle: Optional[str] = None,
    name: Optional[str] = None,
    display_name: Optional[str] = None
) -> bool:
    """
    관리자 계정을 생성합니다.
    
    Args:
        email: 관리자 이메일
        password: 관리자 비밀번호
        user_handle: 사용자 핸들 (선택적)
        name: 이름 (선택적)
        display_name: 표시 이름 (선택적)
    
    Returns:
        bool: 성공 여부
    """
    try:
        # MongoDB 연결
        client = AsyncIOMotorClient(settings.mongodb_url)
        
        # Beanie 초기화
        await init_beanie(
            database=client[settings.database_name],
            document_models=[User]
        )
        
        # 이메일 중복 확인
        existing_user = await User.find_one(User.email == email)
        if existing_user:
            print(f"❌ 이미 존재하는 이메일입니다: {email}")
            if existing_user.is_admin:
                print("   (이미 관리자 권한을 가지고 있습니다)")
                return False
            else:
                # 기존 사용자를 관리자로 승격
                existing_user.is_admin = True
                await existing_user.save()
                print(f"✅ 기존 사용자를 관리자로 승격했습니다: {email}")
                return True
        
        # 사용자 핸들 설정
        if not user_handle:
            user_handle = email.split('@')[0].lower()
        
        # 사용자 핸들 중복 확인
        existing_handle = await User.find_one(User.user_handle == user_handle)
        if existing_handle:
            user_handle = f"{user_handle}_admin"
            print(f"⚠️  사용자 핸들이 중복되어 '{user_handle}'로 변경됩니다")
        
        # 비밀번호 해시
        password_manager = PasswordManager()
        password_hash = password_manager.hash_password(password)
        
        # 관리자 계정 생성
        admin_user = User(
            email=email,
            user_handle=user_handle,
            name=name or "관리자",
            display_name=display_name or "시스템 관리자",
            password_hash=password_hash,
            is_admin=True,
            email_verified=True,  # 관리자는 자동으로 이메일 인증 완료
            status="active"
        )
        
        await admin_user.save()
        
        print(f"✅ 관리자 계정이 생성되었습니다!")
        print(f"   📧 이메일: {email}")
        print(f"   👤 사용자 핸들: {user_handle}")
        print(f"   🔑 비밀번호: {'*' * len(password)}")
        print(f"   👑 관리자 권한: 예")
        
        return True
        
    except ValidationError as e:
        print(f"❌ 입력 데이터 검증 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 관리자 계정 생성 실패: {e}")
        return False
    finally:
        # 연결 종료
        client.close()


def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    try:
        EmailStr._validate(email)
        return True
    except ValidationError:
        return False


def validate_password(password: str) -> bool:
    """비밀번호 검증"""
    if len(password) < 8:
        print("❌ 비밀번호는 최소 8자 이상이어야 합니다")
        return False
    
    if not any(c.isupper() for c in password):
        print("❌ 비밀번호는 대문자를 포함해야 합니다")
        return False
    
    if not any(c.islower() for c in password):
        print("❌ 비밀번호는 소문자를 포함해야 합니다")
        return False
    
    if not any(c.isdigit() for c in password):
        print("❌ 비밀번호는 숫자를 포함해야 합니다")
        return False
    
    return True


async def main():
    """메인 실행 함수"""
    print("🔧 관리자 계정 생성 도구")
    print("=" * 40)
    
    # 환경변수에서 값 가져오기
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    user_handle = os.getenv("ADMIN_HANDLE")
    name = os.getenv("ADMIN_NAME")
    display_name = os.getenv("ADMIN_DISPLAY_NAME")
    
    # 인터랙티브 입력
    if not email:
        while True:
            email = input("📧 관리자 이메일을 입력하세요: ").strip()
            if not email:
                print("❌ 이메일을 입력해주세요")
                continue
            if not validate_email(email):
                print("❌ 올바른 이메일 형식을 입력해주세요")
                continue
            break
    
    if not password:
        while True:
            password = getpass.getpass("🔑 관리자 비밀번호를 입력하세요: ").strip()
            if not password:
                print("❌ 비밀번호를 입력해주세요")
                continue
            if not validate_password(password):
                continue
            
            # 비밀번호 확인
            password_confirm = getpass.getpass("🔑 비밀번호를 다시 입력하세요: ").strip()
            if password != password_confirm:
                print("❌ 비밀번호가 일치하지 않습니다")
                continue
            break
    
    if not user_handle:
        user_handle = input(f"👤 사용자 핸들 (기본값: {email.split('@')[0]}): ").strip()
    
    if not name:
        name = input("👤 이름 (기본값: 관리자): ").strip()
    
    if not display_name:
        display_name = input("👤 표시 이름 (기본값: 시스템 관리자): ").strip()
    
    # 확인
    print("\n📋 입력 정보 확인:")
    print(f"   📧 이메일: {email}")
    print(f"   👤 사용자 핸들: {user_handle or email.split('@')[0]}")
    print(f"   👤 이름: {name or '관리자'}")
    print(f"   👤 표시 이름: {display_name or '시스템 관리자'}")
    print(f"   👑 관리자 권한: 예")
    
    confirm = input("\n생성하시겠습니까? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', '예']:
        print("❌ 관리자 계정 생성을 취소했습니다")
        return
    
    # 관리자 계정 생성
    print("\n🔄 관리자 계정을 생성하는 중...")
    success = await create_admin_user(
        email=email,
        password=password,
        user_handle=user_handle,
        name=name,
        display_name=display_name
    )
    
    if success:
        print("\n🎉 관리자 계정 생성이 완료되었습니다!")
        print("\n📝 다음 정보로 로그인하세요:")
        print(f"   URL: {settings.frontend_url}/auth/login")
        print(f"   이메일: {email}")
        print(f"   비밀번호: {'*' * len(password)}")
        print(f"   관리자 대시보드: {settings.frontend_url}/admin/monitoring")
    else:
        print("\n❌ 관리자 계정 생성에 실패했습니다")


if __name__ == "__main__":
    asyncio.run(main())