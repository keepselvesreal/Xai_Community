#!/usr/bin/env python3
"""
관리자 계정 관리 스크립트

사용법:
    python scripts/manage_admin.py list              # 모든 관리자 목록
    python scripts/manage_admin.py create            # 새 관리자 생성
    python scripts/manage_admin.py promote <email>   # 사용자를 관리자로 승격
    python scripts/manage_admin.py demote <email>    # 관리자 권한 해제
    python scripts/manage_admin.py reset <email>     # 관리자 비밀번호 재설정
"""

import asyncio
import sys
import os
import getpass
from typing import List, Optional

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nadle_backend.config import settings
from nadle_backend.models.core import User
from nadle_backend.utils.password import PasswordManager
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import EmailStr, ValidationError


async def init_database():
    """데이터베이스 초기화"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    await init_beanie(
        database=client[settings.database_name],
        document_models=[User]
    )
    return client


async def list_admins():
    """모든 관리자 목록 조회"""
    client = await init_database()
    
    try:
        admins = await User.find(User.is_admin == True).to_list()
        
        if not admins:
            print("❌ 관리자 계정이 없습니다")
            return
        
        print(f"👑 관리자 계정 목록 ({len(admins)}명)")
        print("=" * 60)
        
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin.email}")
            print(f"   👤 핸들: {admin.user_handle}")
            print(f"   📝 이름: {admin.name or 'N/A'}")
            print(f"   🏷️  표시명: {admin.display_name or 'N/A'}")
            print(f"   📅 생성일: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📧 이메일 인증: {'✅' if admin.email_verified else '❌'}")
            print(f"   🔄 상태: {admin.status}")
            print()
        
    finally:
        client.close()


async def create_admin(email: str, password: str, user_handle: Optional[str] = None):
    """새 관리자 계정 생성"""
    client = await init_database()
    
    try:
        # 이메일 중복 확인
        existing_user = await User.find_one(User.email == email)
        if existing_user:
            print(f"❌ 이미 존재하는 이메일입니다: {email}")
            return False
        
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
            name="관리자",
            display_name="시스템 관리자",
            password_hash=password_hash,
            is_admin=True,
            email_verified=True,
            status="active"
        )
        
        await admin_user.save()
        
        print(f"✅ 관리자 계정이 생성되었습니다!")
        print(f"   📧 이메일: {email}")
        print(f"   👤 사용자 핸들: {user_handle}")
        return True
        
    except Exception as e:
        print(f"❌ 관리자 계정 생성 실패: {e}")
        return False
    finally:
        client.close()


async def promote_user(email: str):
    """사용자를 관리자로 승격"""
    client = await init_database()
    
    try:
        user = await User.find_one(User.email == email)
        if not user:
            print(f"❌ 사용자를 찾을 수 없습니다: {email}")
            return False
        
        if user.is_admin:
            print(f"⚠️  이미 관리자 권한을 가지고 있습니다: {email}")
            return False
        
        user.is_admin = True
        await user.save()
        
        print(f"✅ 사용자를 관리자로 승격했습니다: {email}")
        return True
        
    except Exception as e:
        print(f"❌ 관리자 승격 실패: {e}")
        return False
    finally:
        client.close()


async def demote_admin(email: str):
    """관리자 권한 해제"""
    client = await init_database()
    
    try:
        user = await User.find_one(User.email == email)
        if not user:
            print(f"❌ 사용자를 찾을 수 없습니다: {email}")
            return False
        
        if not user.is_admin:
            print(f"⚠️  관리자 권한이 없습니다: {email}")
            return False
        
        # 마지막 관리자 확인
        admin_count = await User.count_documents(User.is_admin == True)
        if admin_count <= 1:
            print(f"❌ 마지막 관리자이므로 권한을 해제할 수 없습니다")
            return False
        
        user.is_admin = False
        await user.save()
        
        print(f"✅ 관리자 권한을 해제했습니다: {email}")
        return True
        
    except Exception as e:
        print(f"❌ 관리자 권한 해제 실패: {e}")
        return False
    finally:
        client.close()


async def reset_password(email: str, new_password: str):
    """관리자 비밀번호 재설정"""
    client = await init_database()
    
    try:
        user = await User.find_one(User.email == email)
        if not user:
            print(f"❌ 사용자를 찾을 수 없습니다: {email}")
            return False
        
        if not user.is_admin:
            print(f"❌ 관리자 권한이 없습니다: {email}")
            return False
        
        # 비밀번호 해시
        password_manager = PasswordManager()
        password_hash = password_manager.hash_password(new_password)
        
        user.password_hash = password_hash
        await user.save()
        
        print(f"✅ 비밀번호가 재설정되었습니다: {email}")
        return True
        
    except Exception as e:
        print(f"❌ 비밀번호 재설정 실패: {e}")
        return False
    finally:
        client.close()


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
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python scripts/manage_admin.py list")
        print("  python scripts/manage_admin.py create")
        print("  python scripts/manage_admin.py promote <email>")
        print("  python scripts/manage_admin.py demote <email>")
        print("  python scripts/manage_admin.py reset <email>")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        await list_admins()
    
    elif command == "create":
        print("🔧 새 관리자 계정 생성")
        print("=" * 30)
        
        while True:
            email = input("📧 관리자 이메일: ").strip()
            if not email:
                print("❌ 이메일을 입력해주세요")
                continue
            try:
                EmailStr._validate(email)
                break
            except ValidationError:
                print("❌ 올바른 이메일 형식을 입력해주세요")
        
        while True:
            password = getpass.getpass("🔑 비밀번호: ").strip()
            if not password:
                print("❌ 비밀번호를 입력해주세요")
                continue
            if not validate_password(password):
                continue
            
            password_confirm = getpass.getpass("🔑 비밀번호 확인: ").strip()
            if password != password_confirm:
                print("❌ 비밀번호가 일치하지 않습니다")
                continue
            break
        
        user_handle = input("👤 사용자 핸들 (선택적): ").strip()
        
        await create_admin(email, password, user_handle or None)
    
    elif command == "promote":
        if len(sys.argv) < 3:
            print("❌ 이메일을 입력해주세요")
            print("사용법: python scripts/manage_admin.py promote <email>")
            return
        
        email = sys.argv[2]
        await promote_user(email)
    
    elif command == "demote":
        if len(sys.argv) < 3:
            print("❌ 이메일을 입력해주세요")
            print("사용법: python scripts/manage_admin.py demote <email>")
            return
        
        email = sys.argv[2]
        confirm = input(f"정말로 '{email}'의 관리자 권한을 해제하시겠습니까? (y/N): ").strip().lower()
        if confirm in ['y', 'yes', '예']:
            await demote_admin(email)
        else:
            print("❌ 취소되었습니다")
    
    elif command == "reset":
        if len(sys.argv) < 3:
            print("❌ 이메일을 입력해주세요")
            print("사용법: python scripts/manage_admin.py reset <email>")
            return
        
        email = sys.argv[2]
        
        while True:
            password = getpass.getpass("🔑 새 비밀번호: ").strip()
            if not password:
                print("❌ 비밀번호를 입력해주세요")
                continue
            if not validate_password(password):
                continue
            
            password_confirm = getpass.getpass("🔑 비밀번호 확인: ").strip()
            if password != password_confirm:
                print("❌ 비밀번호가 일치하지 않습니다")
                continue
            break
        
        await reset_password(email, password)
    
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print("사용 가능한 명령어: list, create, promote, demote, reset")


if __name__ == "__main__":
    asyncio.run(main())