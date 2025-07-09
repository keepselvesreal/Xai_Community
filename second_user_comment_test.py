#!/usr/bin/env python3
"""
두 번째 사용자로 댓글 작성 테스트
"""
import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime
from typing import Dict, Optional

class SecondUserCommentTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.user_data: Optional[Dict] = None
        
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
        username = f"commenter_{self.generate_random_string(6)}"
        email = f"{username}@test.com"
        password = "TestPass123!"
        
        return {
            "name": f"댓글 작성자 {username}",
            "email": email,
            "user_handle": username,
            "password": password,
            "display_name": f"댓글 작성자 {username}",
            "bio": "댓글 작성 테스트를 위한 계정입니다."
        }
    
    async def register_user(self) -> Dict:
        """회원가입"""
        print("🚀 두 번째 사용자 회원가입 시작...")
        
        self.user_data = self.generate_test_user_data()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/register",
                json=self.user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    print(f"✅ 회원가입 성공: {self.user_data['user_handle']} ({self.user_data['email']})")
                    return {"success": True, "data": result}
                else:
                    print(f"❌ 회원가입 실패: {result}")
                    return {"success": False, "error": result}
                    
        except Exception as e:
            print(f"❌ 회원가입 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def login_user(self) -> Dict:
        """로그인"""
        print("🔐 두 번째 사용자 로그인 시작...")
        
        login_data = {
            "username": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    self.access_token = result["access_token"]
                    print(f"✅ 로그인 성공: {self.user_data['email']}")
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
    
    async def get_recent_posts(self) -> list:
        """최근 게시글 조회"""
        print("🔍 최근 게시글 조회 중...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/posts/?page=1&page_size=10",
                headers=self.get_auth_headers()
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    # API 응답 구조에 맞게 수정
                    posts = result.get("items", [])
                    print(f"✅ 최근 게시글 {len(posts)}개 조회 완료")
                    return posts
                else:
                    print(f"❌ 게시글 조회 실패: {result}")
                    return []
                    
        except Exception as e:
            print(f"❌ 게시글 조회 오류: {str(e)}")
            return []
    
    async def create_comment(self, post_slug: str, post_title: str, content: str) -> Dict:
        """댓글 작성"""
        print(f"💬 댓글 작성 시작: {post_title}")
        
        comment_data = {
            "content": content,
            "parent_comment_id": None
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
    
    async def run_comment_test(self):
        """댓글 작성 테스트 실행"""
        print("🎯 두 번째 사용자 댓글 작성 테스트 시작!")
        print("=" * 60)
        
        # 1. 회원가입 및 로그인
        register_result = await self.register_user()
        if not register_result["success"]:
            print("❌ 회원가입 실패로 인해 테스트 중단")
            return
        
        login_result = await self.login_user()
        if not login_result["success"]:
            print("❌ 로그인 실패로 인해 테스트 중단")
            return
        
        # 2. 최근 게시글 조회
        posts = await self.get_recent_posts()
        if not posts:
            print("❌ 댓글을 작성할 게시글이 없습니다.")
            return
        
        # 3. 다양한 게시글에 댓글 작성
        print("\\n" + "=" * 60)
        print("💬 다양한 게시글에 댓글 작성")
        print("=" * 60)
        
        comment_contents = [
            f"""정말 유용한 정보네요! 👍

{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}에 댓글을 작성했습니다.

이런 정보를 공유해주셔서 감사합니다.
앞으로도 좋은 글 부탁드려요!

**도움이 많이 되었습니다!** 🙏""",
            
            f"""좋은 글 감사합니다! 🌟

제가 찾고 있던 정보가 바로 이거였어요.
시간: {datetime.now().strftime('%H:%M:%S')}

질문이 하나 있는데, 추가적인 정보도 있을까요?

**정말 도움이 되는 글이네요!** 💡""",
            
            f"""와! 전문가 분이 직접 알려주시네요! 🎯

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이런 꿀팁을 무료로 볼 수 있어서 너무 감사해요.
실제로 적용해보겠습니다!

**진짜 유용한 정보 감사합니다!** ✨"""
        ]
        
        success_count = 0
        
        for i, post in enumerate(posts[:3]):  # 최대 3개 게시글에 댓글 작성
            if i < len(comment_contents):
                comment_result = await self.create_comment(
                    post_slug=post["slug"],
                    post_title=post["title"],
                    content=comment_contents[i]
                )
                
                if comment_result["success"]:
                    success_count += 1
                    
                # 잠깐 대기 (API 호출 간격 조정)
                await asyncio.sleep(0.5)
        
        # 4. 결과 요약
        print("\\n" + "=" * 60)
        print("🎊 댓글 작성 테스트 완료!")
        print("=" * 60)
        
        print(f"✅ 생성된 댓글 작성자: {self.user_data['user_handle']} ({self.user_data['email']})")
        print(f"✅ 작성된 댓글: {success_count}개")
        print(f"✅ 댓글 작성 대상 게시글: {len(posts)}개 중 {min(3, len(posts))}개")
        
        print(f"\\n📧 댓글 작성자 계정 정보:")
        print(f"   이메일: {self.user_data['email']}")
        print(f"   패스워드: {self.user_data['password']}")

async def main():
    """메인 실행 함수"""
    async with SecondUserCommentTest() as test:
        await test.run_comment_test()

if __name__ == "__main__":
    asyncio.run(main())