#!/usr/bin/env python3
"""Frontend-Backend API 통합 테스트 스크립트."""

import asyncio
import json
import time
from playwright.async_api import async_playwright
import aiohttp
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 테스트 설정
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
TEST_USER = {
    "email": "integration.test@example.com",
    "password": "TestPass123",
    "user_handle": "integrationtest"
}

class APIIntegrationTester:
    """API 통합 테스트 클래스"""
    
    def __init__(self):
        self.session = None
        self.results = {
            "backend_health": False,
            "frontend_accessible": False,
            "cors_enabled": False,
            "registration_api": False,
            "frontend_registration": False,
            "data_persistence": False
        }
    
    async def setup(self):
        """테스트 초기 설정"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """테스트 정리"""
        if self.session:
            await self.session.close()
    
    async def test_backend_health(self):
        """백엔드 서버 상태 확인"""
        print("\n1. 백엔드 서버 상태 확인...")
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 백엔드 서버 정상: {data}")
                    self.results["backend_health"] = True
                else:
                    print(f"❌ 백엔드 서버 응답 오류: {response.status}")
        except Exception as e:
            print(f"❌ 백엔드 연결 실패: {e}")
    
    async def test_cors_configuration(self):
        """CORS 설정 확인"""
        print("\n2. CORS 설정 확인...")
        try:
            headers = {
                "Origin": FRONTEND_URL,
                "Content-Type": "application/json"
            }
            async with self.session.options(f"{BACKEND_URL}/auth/register", headers=headers) as response:
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                    "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                    "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
                }
                print(f"   CORS 헤더: {cors_headers}")
                
                if cors_headers["access-control-allow-origin"]:
                    print("✅ CORS 설정 확인됨")
                    self.results["cors_enabled"] = True
                else:
                    print("❌ CORS 설정 누락")
        except Exception as e:
            print(f"❌ CORS 테스트 실패: {e}")
    
    async def test_registration_api_direct(self):
        """백엔드 회원가입 API 직접 테스트"""
        print("\n3. 백엔드 회원가입 API 직접 테스트...")
        
        # 기존 사용자 삭제 (있다면)
        await self.cleanup_test_user()
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Origin": FRONTEND_URL
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/register",
                headers=headers,
                json=TEST_USER
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ 회원가입 API 성공: {data.get('user', {}).get('email')}")
                    self.results["registration_api"] = True
                else:
                    error_data = await response.text()
                    print(f"❌ 회원가입 API 실패 ({response.status}): {error_data}")
                    
        except Exception as e:
            print(f"❌ 회원가입 API 테스트 실패: {e}")
    
    async def test_data_persistence(self):
        """데이터 영속성 확인"""
        print("\n4. 데이터 영속성 확인...")
        try:
            # MongoDB에서 사용자 확인
            from nadle_backend.models.core import User
            from nadle_backend.database.connection import database
            
            await database.connect()
            user = await User.find_one({"email": TEST_USER["email"]})
            
            if user:
                print(f"✅ 데이터베이스에 사용자 저장 확인: {user.email}")
                print(f"   사용자 ID: {user.id}")
                print(f"   생성 시간: {user.created_at}")
                self.results["data_persistence"] = True
            else:
                print("❌ 데이터베이스에서 사용자를 찾을 수 없음")
                
            await database.disconnect()
            
        except Exception as e:
            print(f"❌ 데이터 영속성 테스트 실패: {e}")
    
    async def test_frontend_registration_ui(self):
        """프론트엔드 회원가입 UI 테스트"""
        print("\n5. 프론트엔드 회원가입 UI 테스트...")
        
        try:
            async with async_playwright() as p:
                # 헤드리스 브라우저 실행
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # 네트워크 요청 모니터링
                requests = []
                responses = []
                
                def handle_request(request):
                    if BACKEND_URL in request.url:
                        requests.append({
                            "url": request.url,
                            "method": request.method,
                            "headers": dict(request.headers)
                        })
                
                def handle_response(response):
                    if BACKEND_URL in response.url:
                        responses.append({
                            "url": response.url,
                            "status": response.status,
                            "headers": dict(response.headers)
                        })
                
                page.on("request", handle_request)
                page.on("response", handle_response)
                
                # 프론트엔드 페이지 로드
                await page.goto(f"{FRONTEND_URL}/auth/register")
                await page.wait_for_load_state("networkidle")
                
                # 회원가입 폼 확인
                email_input = await page.query_selector('input[name="email"]')
                password_input = await page.query_selector('input[name="password"]')
                handle_input = await page.query_selector('input[name="user_handle"]')
                submit_button = await page.query_selector('button[type="submit"]')
                
                if not all([email_input, password_input, handle_input, submit_button]):
                    print("❌ 회원가입 폼 요소를 찾을 수 없음")
                    await browser.close()
                    return
                
                print("✅ 회원가입 폼 요소 확인됨")
                
                # 고유한 테스트 사용자 생성
                test_timestamp = int(time.time())
                unique_user = {
                    "email": f"ui.test.{test_timestamp}@example.com",
                    "password": "TestPass123",
                    "user_handle": f"uitest{test_timestamp}",
                    "confirm_password": "TestPass123"
                }
                
                # 폼 입력
                await email_input.fill(unique_user["email"])
                await handle_input.fill(unique_user["user_handle"])
                await password_input.fill(unique_user["password"])
                
                # 비밀번호 확인 필드
                confirm_input = await page.query_selector('input[name="confirm_password"]')
                if confirm_input:
                    await confirm_input.fill(unique_user["confirm_password"])
                
                # 폼 제출
                await submit_button.click()
                
                # 응답 대기 (최대 10초)
                await page.wait_for_timeout(5000)
                
                print(f"   보낸 요청 수: {len(requests)}")
                print(f"   받은 응답 수: {len(responses)}")
                
                # API 호출 확인
                registration_request = None
                registration_response = None
                
                for req in requests:
                    if "/auth/register" in req["url"] and req["method"] == "POST":
                        registration_request = req
                        break
                
                for res in responses:
                    if "/auth/register" in res["url"]:
                        registration_response = res
                        break
                
                if registration_request:
                    print("✅ 프론트엔드에서 회원가입 API 호출 확인")
                    print(f"   요청 URL: {registration_request['url']}")
                    print(f"   Content-Type: {registration_request['headers'].get('content-type', 'N/A')}")
                    
                    if registration_response:
                        print(f"✅ API 응답 수신: {registration_response['status']}")
                        if registration_response['status'] in [200, 201]:
                            self.results["frontend_registration"] = True
                        else:
                            print(f"❌ API 응답 오류: {registration_response['status']}")
                    else:
                        print("❌ API 응답을 받지 못함")
                else:
                    print("❌ 프론트엔드에서 API 호출이 확인되지 않음")
                
                await browser.close()
                
        except Exception as e:
            print(f"❌ 프론트엔드 UI 테스트 실패: {e}")
    
    async def cleanup_test_user(self):
        """테스트 사용자 정리"""
        try:
            from nadle_backend.models.core import User
            from nadle_backend.database.connection import database
            
            await database.connect()
            user = await User.find_one({"email": TEST_USER["email"]})
            if user:
                await user.delete()
                print(f"   기존 테스트 사용자 삭제: {TEST_USER['email']}")
            await database.disconnect()
            
        except Exception as e:
            logger.debug(f"테스트 사용자 정리 중 오류 (무시됨): {e}")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 60)
        print("Frontend-Backend API 통합 테스트 시작")
        print("=" * 60)
        
        await self.setup()
        
        try:
            await self.test_backend_health()
            await self.test_cors_configuration()
            await self.test_registration_api_direct()
            await self.test_data_persistence()
            await self.test_frontend_registration_ui()
            
        finally:
            await self.cleanup()
            await self.cleanup_test_user()
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("테스트 결과 요약")
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
            print("\n🎉 모든 통합 테스트가 성공했습니다!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests}개의 테스트가 실패했습니다.")
        
        print("=" * 60)
        
        return passed_tests == total_tests

async def main():
    """메인 테스트 함수"""
    tester = APIIntegrationTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    # Playwright 설치 확인
    try:
        import playwright
    except ImportError:
        print("❌ Playwright가 설치되지 않았습니다.")
        print("설치 명령어: pip install playwright && playwright install chromium")
        exit(1)
    
    # 테스트 실행
    success = asyncio.run(main())
    exit(0 if success else 1)