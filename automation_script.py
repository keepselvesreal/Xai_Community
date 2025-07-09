#!/usr/bin/env python3
"""
자동화 스크립트 - 회원가입, 로그인, 게시글 작성, 댓글 작성
"""
import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime
from typing import Dict, Optional

class XaiCommunityAutomate:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_email: Optional[str] = None
        self.created_post_slug: Optional[str] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def generate_random_string(self, length: int = 8) -> str:
        """랜덤 문자열 생성"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_test_user_data(self) -> Dict:
        """테스트 사용자 데이터 생성"""
        username = f"testuser_{self.generate_random_string(6)}"
        email = f"{username}@test.com"
        password = "TestPass123!"  # 대문자, 소문자, 숫자, 특수문자 포함
        
        return {
            "name": f"테스트 사용자 {username}",
            "email": email,
            "user_handle": username,
            "password": password,
            "display_name": f"테스트 사용자 {username}",
            "bio": "자동화 테스트를 위한 계정입니다."
        }
    
    async def register_user(self) -> Dict:
        """회원가입"""
        print("🚀 회원가입 시작...")
        
        user_data = self.generate_test_user_data()
        self.user_email = user_data["email"]
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    print(f"✅ 회원가입 성공: {user_data['user_handle']} ({user_data['email']})")
                    return {"success": True, "data": result, "user_data": user_data}
                else:
                    print(f"❌ 회원가입 실패: {result}")
                    return {"success": False, "error": result}
                    
        except Exception as e:
            print(f"❌ 회원가입 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def login_user(self, email: str, password: str) -> Dict:
        """로그인"""
        print("🔐 로그인 시작...")
        
        login_data = {
            "username": email,  # FastAPI OAuth2PasswordRequestForm은 username 필드 사용
            "password": password
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,  # form data로 전송
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    self.access_token = result["access_token"]
                    self.refresh_token = result.get("refresh_token")
                    print(f"✅ 로그인 성공: {email}")
                    return {"success": True, "data": result}
                else:
                    print(f"❌ 로그인 실패: {result}")
                    return {"success": False, "error": result}
                    
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_auth_headers(self) -> Dict:
        """인증 헤더 생성"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def create_post(self) -> Dict:
        """게시글 작성"""
        print("📝 게시글 작성 시작...")
        
        post_data = {
            "title": f"자동화 테스트 게시글 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": f"""# 안녕하세요! 자동화 테스트 게시글입니다.

이 게시글은 자동화 스크립트를 통해 작성되었습니다.

## 주요 내용
- 테스트 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
- 작성자: 자동화 봇
- 목적: 시스템 기능 테스트

## 기능 테스트 항목
1. 회원가입 ✅
2. 로그인 ✅
3. 게시글 작성 ✅
4. 댓글 작성 (진행 예정)

**잘 동작하고 있네요!** 🎉""",
            "service": "residential_community",
            "metadata": {
                "type": "board",
                "category": "자유게시판",
                "tags": ["자동화", "테스트", "시스템체크"],
                "editor_type": "markdown",
                "visibility": "public"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts/",
                json=post_data,
                headers=self.get_auth_headers()
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    self.created_post_slug = result["slug"]
                    print(f"✅ 게시글 작성 성공: {result['title']}")
                    print(f"   슬러그: {result['slug']}")
                    return {"success": True, "data": result}
                else:
                    print(f"❌ 게시글 작성 실패: {result}")
                    return {"success": False, "error": result}
                    
        except Exception as e:
            print(f"❌ 게시글 작성 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_comment(self, post_slug: str, content: str) -> Dict:
        """댓글 작성"""
        print(f"💬 댓글 작성 시작: {content[:30]}...")
        
        comment_data = {
            "content": content,
            "parent_comment_id": None  # 일반 댓글 (대댓글 아님)
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts/{post_slug}/comments",
                json=comment_data,
                headers=self.get_auth_headers()
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    comment_id = result.get('id', result.get('_id', 'unknown'))
                    print(f"✅ 댓글 작성 성공: {comment_id}")
                    return {"success": True, "data": result}
                else:
                    print(f"❌ 댓글 작성 실패: {result}")
                    return {"success": False, "error": result}
                    
        except Exception as e:
            print(f"❌ 댓글 작성 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_automation(self):
        """전체 자동화 프로세스 실행"""
        print("🎯 Xai Community 자동화 스크립트 시작!")
        print("=" * 50)
        
        results = {
            "register": None,
            "login": None,
            "post": None,
            "comments": []
        }
        
        # 1. 회원가입
        register_result = await self.register_user()
        results["register"] = register_result
        
        if not register_result["success"]:
            print("❌ 회원가입 실패로 인해 자동화 중단")
            return results
        
        user_data = register_result["user_data"]
        
        # 2. 로그인
        login_result = await self.login_user(user_data["email"], user_data["password"])
        results["login"] = login_result
        
        if not login_result["success"]:
            print("❌ 로그인 실패로 인해 자동화 중단")
            return results
        
        # 3. 게시글 작성
        post_result = await self.create_post()
        results["post"] = post_result
        
        if not post_result["success"]:
            print("❌ 게시글 작성 실패로 인해 자동화 중단")
            return results
        
        # 4. 댓글 2개 작성
        comments_content = [
            f"""
정말 좋은 테스트 게시글이네요! 👍

자동화 스크립트가 잘 동작하는 것 같습니다.
시간: {datetime.now().strftime('%H:%M:%S')}
            """.strip(),
            f"""
두 번째 댓글입니다! 🎉

시스템이 정상적으로 동작하고 있어서 기쁩니다.
- 회원가입: OK
- 로그인: OK  
- 게시글 작성: OK
- 댓글 작성: OK (현재 진행 중)

훌륭한 시스템이네요! 🚀
            """.strip()
        ]
        
        for i, comment_content in enumerate(comments_content, 1):
            print(f"\n--- 댓글 {i} 작성 ---")
            comment_result = await self.create_comment(self.created_post_slug, comment_content)
            results["comments"].append(comment_result)
            
            if comment_result["success"]:
                print(f"✅ {i}번째 댓글 작성 완료")
            else:
                print(f"❌ {i}번째 댓글 작성 실패")
        
        # 최종 결과
        print("\n" + "=" * 50)
        print("🎊 자동화 스크립트 완료!")
        print("=" * 50)
        
        success_count = sum([
            1 if results["register"]["success"] else 0,
            1 if results["login"]["success"] else 0,
            1 if results["post"]["success"] else 0,
            sum(1 for c in results["comments"] if c["success"])
        ])
        
        total_count = 4  # 회원가입, 로그인, 게시글, 댓글2개
        
        print(f"✅ 성공: {success_count}/{total_count}")
        print(f"📧 생성된 사용자: {user_data['user_handle']} ({user_data['email']})")
        
        if self.created_post_slug:
            print(f"📝 생성된 게시글: {self.created_post_slug}")
        
        return results

async def main():
    """메인 실행 함수"""
    async with XaiCommunityAutomate() as automation:
        await automation.run_automation()

if __name__ == "__main__":
    asyncio.run(main())