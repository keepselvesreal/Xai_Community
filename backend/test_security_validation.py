#!/usr/bin/env python3
"""보안 및 검증 요구사항 테스트 스크립트."""

import asyncio
import aiohttp
import hashlib
import json
from nadle_backend.models.core import User
from nadle_backend.database.connection import database

# 테스트 설정
BACKEND_URL = "http://localhost:8000"

class SecurityValidationTester:
    """보안 및 검증 요구사항 테스트 클래스"""
    
    def __init__(self):
        self.session = None
        self.results = {
            "password_hashing": False,
            "email_validation": False,
            "password_strength": False,
            "duplicate_prevention": False,
            "data_sanitization": False,
            "cors_security": False
        }
    
    async def setup(self):
        """테스트 초기 설정"""
        self.session = aiohttp.ClientSession()
        await database.connect()
        
    async def cleanup(self):
        """테스트 정리"""
        if self.session:
            await self.session.close()
        await database.disconnect()
    
    async def test_password_hashing(self):
        """비밀번호 해싱 검증"""
        print("\n1. 비밀번호 해싱 검증...")
        
        # 고유한 테스트 사용자 생성
        test_email = "hash.test@example.com"
        test_password = "TestHash123"
        
        try:
            # 기존 사용자 삭제
            await self.cleanup_user(test_email)
            
            # 회원가입
            async with self.session.post(
                f"{BACKEND_URL}/auth/register",
                json={
                    "email": test_email,
                    "password": test_password,
                    "user_handle": "hashtest"
                }
            ) as response:
                if response.status != 201:
                    print(f"❌ 회원가입 실패: {response.status}")
                    return
            
            # 데이터베이스에서 사용자 확인
            user = await User.find_one({"email": test_email})
            if not user:
                print("❌ 사용자를 데이터베이스에서 찾을 수 없음")
                return
            
            # 비밀번호가 해싱되었는지 확인
            if hasattr(user, 'password_hash'):
                # 원본 비밀번호와 해시가 다른지 확인
                if user.password_hash != test_password:
                    print("✅ 비밀번호가 해싱되어 저장됨")
                    print(f"   원본: {test_password}")
                    print(f"   해시: {user.password_hash[:20]}...")
                    
                    # bcrypt 해시 형식인지 확인
                    if user.password_hash.startswith('$2b$'):
                        print("✅ bcrypt 해싱 알고리즘 사용 확인")
                        self.results["password_hashing"] = True
                    else:
                        print("❌ bcrypt가 아닌 다른 해싱 방식 사용")
                else:
                    print("❌ 비밀번호가 평문으로 저장됨")
            else:
                print("❌ 비밀번호 해시 필드를 찾을 수 없음")
            
            await self.cleanup_user(test_email)
            
        except Exception as e:
            print(f"❌ 비밀번호 해싱 테스트 실패: {e}")
    
    async def test_email_validation(self):
        """이메일 형식 검증"""
        print("\n2. 이메일 형식 검증...")
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            ""
        ]
        
        valid_count = 0
        total_count = len(invalid_emails)
        
        for email in invalid_emails:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/auth/register",
                    json={
                        "email": email,
                        "password": "TestPass123",
                        "user_handle": "emailtest"
                    }
                ) as response:
                    if response.status == 422:  # Validation error
                        valid_count += 1
                        print(f"   ✅ '{email}' 올바르게 거부됨")
                    else:
                        print(f"   ❌ '{email}' 부적절하게 허용됨 ({response.status})")
            except Exception as e:
                print(f"   ⚠️  '{email}' 테스트 중 오류: {e}")
        
        if valid_count == total_count:
            print("✅ 이메일 형식 검증 통과")
            self.results["email_validation"] = True
        else:
            print(f"❌ 이메일 검증 실패: {valid_count}/{total_count}")
    
    async def test_password_strength(self):
        """비밀번호 강도 검증"""
        print("\n3. 비밀번호 강도 검증...")
        
        weak_passwords = [
            "123",           # 너무 짧음
            "12345678",      # 숫자만
            "password",      # 문자만
            "PASSWORD",      # 대문자만
            "Pass123",       # 대소문자 + 숫자 (8자 미만)
        ]
        
        valid_count = 0
        total_count = len(weak_passwords)
        
        for i, password in enumerate(weak_passwords):
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/auth/register",
                    json={
                        "email": f"pwtest{i}@example.com",
                        "password": password,
                        "user_handle": f"pwtest{i}"
                    }
                ) as response:
                    if response.status == 422:  # Validation error
                        valid_count += 1
                        print(f"   ✅ '{password}' 올바르게 거부됨")
                    else:
                        print(f"   ❌ '{password}' 부적절하게 허용됨 ({response.status})")
            except Exception as e:
                print(f"   ⚠️  '{password}' 테스트 중 오류: {e}")
        
        if valid_count >= total_count * 0.8:  # 80% 이상 통과
            print("✅ 비밀번호 강도 검증 통과")
            self.results["password_strength"] = True
        else:
            print(f"❌ 비밀번호 강도 검증 실패: {valid_count}/{total_count}")
    
    async def test_duplicate_prevention(self):
        """중복 방지 검증"""
        print("\n4. 중복 방지 검증...")
        
        test_email = "duplicate.test@example.com"
        test_handle = "duplicatetest"
        
        try:
            # 기존 사용자 정리
            await self.cleanup_user(test_email)
            
            # 첫 번째 사용자 생성
            async with self.session.post(
                f"{BACKEND_URL}/auth/register",
                json={
                    "email": test_email,
                    "password": "TestPass123",
                    "user_handle": test_handle
                }
            ) as response:
                if response.status != 201:
                    print(f"❌ 첫 번째 사용자 생성 실패: {response.status}")
                    return
            
            print("   첫 번째 사용자 생성 성공")
            
            # 동일한 이메일로 두 번째 시도
            async with self.session.post(
                f"{BACKEND_URL}/auth/register",
                json={
                    "email": test_email,
                    "password": "TestPass123",
                    "user_handle": "duplicatetest2"
                }
            ) as response:
                if response.status == 400:
                    print("   ✅ 중복 이메일 올바르게 거부됨")
                    duplicate_email_blocked = True
                else:
                    print(f"   ❌ 중복 이메일 부적절하게 허용됨 ({response.status})")
                    duplicate_email_blocked = False
            
            # 동일한 핸들로 세 번째 시도
            async with self.session.post(
                f"{BACKEND_URL}/auth/register",
                json={
                    "email": "another.test@example.com",
                    "password": "TestPass123",
                    "user_handle": test_handle
                }
            ) as response:
                if response.status == 400:
                    print("   ✅ 중복 핸들 올바르게 거부됨")
                    duplicate_handle_blocked = True
                else:
                    print(f"   ❌ 중복 핸들 부적절하게 허용됨 ({response.status})")
                    duplicate_handle_blocked = False
            
            if duplicate_email_blocked and duplicate_handle_blocked:
                print("✅ 중복 방지 검증 통과")
                self.results["duplicate_prevention"] = True
            else:
                print("❌ 중복 방지 검증 실패")
            
            await self.cleanup_user(test_email)
            await self.cleanup_user("another.test@example.com")
            
        except Exception as e:
            print(f"❌ 중복 방지 테스트 실패: {e}")
    
    async def test_data_sanitization(self):
        """데이터 무결성 및 XSS 방지 검증"""
        print("\n5. 데이터 무결성 및 XSS 방지 검증...")
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')"
        ]
        
        safe_count = 0
        total_count = len(malicious_inputs)
        
        for i, malicious_input in enumerate(malicious_inputs):
            try:
                # 사용자 핸들에 악성 스크립트 삽입 시도
                async with self.session.post(
                    f"{BACKEND_URL}/auth/register",
                    json={
                        "email": f"xss.test{i}@example.com",
                        "password": "TestPass123",
                        "user_handle": malicious_input
                    }
                ) as response:
                    if response.status == 422:  # Validation error
                        safe_count += 1
                        print(f"   ✅ 악성 입력 '{malicious_input[:20]}...' 올바르게 거부됨")
                    else:
                        # 성공한 경우 데이터베이스에서 실제 저장된 값 확인
                        user = await User.find_one({"email": f"xss.test{i}@example.com"})
                        if user:
                            if user.user_handle != malicious_input:
                                safe_count += 1
                                print(f"   ✅ 입력이 안전하게 처리됨: '{user.user_handle[:20]}...'")
                            else:
                                print(f"   ❌ 악성 입력이 그대로 저장됨: '{user.user_handle[:20]}...'")
                            await user.delete()
                        else:
                            safe_count += 1
                            print(f"   ✅ 악성 입력으로 인한 사용자 생성 실패")
            except Exception as e:
                print(f"   ⚠️  악성 입력 테스트 중 오류: {e}")
        
        if safe_count >= total_count * 0.8:  # 80% 이상 안전
            print("✅ 데이터 무결성 검증 통과")
            self.results["data_sanitization"] = True
        else:
            print(f"❌ 데이터 무결성 검증 실패: {safe_count}/{total_count}")
    
    async def test_cors_security(self):
        """CORS 보안 설정 검증"""
        print("\n6. CORS 보안 설정 검증...")
        
        # 허용된 오리진에서 요청
        async with self.session.options(
            f"{BACKEND_URL}/auth/register",
            headers={"Origin": "http://localhost:5173"}
        ) as response:
            cors_origin = response.headers.get("access-control-allow-origin")
            if cors_origin:
                print(f"   ✅ 허용된 오리진에 대한 CORS 응답: {cors_origin}")
                allowed_origin_ok = True
            else:
                print("   ❌ 허용된 오리진에 대한 CORS 응답 없음")
                allowed_origin_ok = False
        
        # 허용되지 않은 오리진에서 요청
        async with self.session.options(
            f"{BACKEND_URL}/auth/register",
            headers={"Origin": "http://malicious-site.com"}
        ) as response:
            cors_origin = response.headers.get("access-control-allow-origin")
            if cors_origin and "malicious-site.com" not in cors_origin:
                print("   ✅ 허용되지 않은 오리진 적절하게 차단됨")
                blocked_origin_ok = True
            elif not cors_origin:
                print("   ✅ 허용되지 않은 오리진에 대한 CORS 응답 없음")
                blocked_origin_ok = True
            else:
                print(f"   ❌ 허용되지 않은 오리진이 부적절하게 허용됨: {cors_origin}")
                blocked_origin_ok = False
        
        if allowed_origin_ok and blocked_origin_ok:
            print("✅ CORS 보안 설정 검증 통과")
            self.results["cors_security"] = True
        else:
            print("❌ CORS 보안 설정 검증 실패")
    
    async def cleanup_user(self, email: str):
        """테스트 사용자 정리"""
        try:
            user = await User.find_one({"email": email})
            if user:
                await user.delete()
        except:
            pass  # 정리 실패는 무시
    
    async def run_all_tests(self):
        """모든 보안 테스트 실행"""
        print("=" * 60)
        print("보안 및 검증 요구사항 테스트 시작")
        print("=" * 60)
        
        await self.setup()
        
        try:
            await self.test_password_hashing()
            await self.test_email_validation()
            await self.test_password_strength()
            await self.test_duplicate_prevention()
            await self.test_data_sanitization()
            await self.test_cors_security()
            
        finally:
            await self.cleanup()
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("보안 테스트 결과 요약")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(self.results.values())
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} : {status}")
        
        print("-" * 60)
        print(f"총 테스트: {total_tests}")
        print(f"통과: {passed_tests}")
        print(f"실패: {total_tests - passed_tests}")
        print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 모든 보안 테스트가 성공했습니다!")
            security_level = "매우 안전"
        elif passed_tests >= total_tests * 0.8:
            print(f"\n✅ 대부분의 보안 테스트가 성공했습니다.")
            security_level = "안전"
        else:
            print(f"\n⚠️  {total_tests - passed_tests}개의 보안 테스트가 실패했습니다.")
            security_level = "위험"
        
        print(f"보안 수준: {security_level}")
        print("=" * 60)
        
        return passed_tests >= total_tests * 0.8  # 80% 이상 통과 시 성공

async def main():
    """메인 테스트 함수"""
    tester = SecurityValidationTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)