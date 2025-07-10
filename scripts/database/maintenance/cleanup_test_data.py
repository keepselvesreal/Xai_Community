#!/usr/bin/env python3
"""
테스트 데이터 정리 스크립트 - 특정 사용자의 모든 데이터 삭제
"""
import asyncio
import aiohttp
from typing import Optional

class TestDataCleaner:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login_user(self, email: str, password: str) -> bool:
        """로그인"""
        print(f"🔐 로그인 시도: {email}")
        
        login_data = {
            "username": email,
            "password": password
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result["access_token"]
                    print(f"✅ 로그인 성공")
                    return True
                else:
                    print(f"❌ 로그인 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return False
    
    def get_auth_headers(self) -> dict:
        """인증 헤더 생성"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def get_user_activity(self) -> dict:
        """사용자 활동 데이터 조회"""
        print("📊 사용자 활동 데이터 조회 중...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/users/me/activity?limit=100",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 활동 데이터 조회 성공")
                    return result
                else:
                    print(f"❌ 활동 데이터 조회 실패: {response.status}")
                    return {}
        except Exception as e:
            print(f"❌ 활동 데이터 조회 오류: {str(e)}")
            return {}
    
    async def delete_comment(self, post_slug: str, comment_id: str) -> bool:
        """댓글 삭제"""
        print(f"🗑️  댓글 삭제 중: {comment_id}")
        
        try:
            async with self.session.delete(
                f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    print(f"✅ 댓글 삭제 성공: {comment_id}")
                    return True
                else:
                    print(f"❌ 댓글 삭제 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 댓글 삭제 오류: {str(e)}")
            return False
    
    async def delete_post(self, post_slug: str) -> bool:
        """게시글 삭제"""
        print(f"🗑️  게시글 삭제 중: {post_slug}")
        
        try:
            async with self.session.delete(
                f"{self.base_url}/api/posts/{post_slug}",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    print(f"✅ 게시글 삭제 성공: {post_slug}")
                    return True
                else:
                    print(f"❌ 게시글 삭제 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 게시글 삭제 오류: {str(e)}")
            return False
    
    async def cleanup_user_data(self, email: str, password: str):
        """사용자 데이터 정리"""
        print("🧹 테스트 데이터 정리 시작")
        print("=" * 50)
        
        # 1. 로그인
        if not await self.login_user(email, password):
            print("❌ 로그인 실패로 인해 정리 작업 중단")
            return
        
        # 2. 사용자 활동 데이터 조회
        activity_data = await self.get_user_activity()
        if not activity_data:
            print("❌ 활동 데이터 조회 실패")
            return
        
        # 3. 댓글 삭제
        comments = activity_data.get("comments", [])
        print(f"\n📝 댓글 {len(comments)}개 삭제 시작")
        
        for comment in comments:
            comment_id = comment["id"]
            # route_path에서 post_slug 추출
            route_path = comment["route_path"]
            if "/board/" in route_path:
                post_slug = route_path.split("/board/")[1]
            elif "/property-information/" in route_path:
                post_slug = route_path.split("/property-information/")[1]
            elif "/moving-services/" in route_path:
                post_slug = route_path.split("/moving-services/")[1]
            elif "/expert-tips/" in route_path:
                post_slug = route_path.split("/expert-tips/")[1]
            else:
                continue
            
            await self.delete_comment(post_slug, comment_id)
        
        # 4. 게시글 삭제
        posts = activity_data.get("posts", {})
        total_posts = 0
        
        for post_type, post_list in posts.items():
            total_posts += len(post_list)
        
        print(f"\n📄 게시글 {total_posts}개 삭제 시작")
        
        for post_type, post_list in posts.items():
            for post in post_list:
                post_slug = post["slug"]
                await self.delete_post(post_slug)
        
        print("\n" + "=" * 50)
        print("✅ 테스트 데이터 정리 완료!")
        print("=" * 50)

async def main():
    """메인 실행 함수"""
    # 기존 테스트 유저들 정리
    test_users = [
        ("testuser_w5kc97@test.com", "TestPass123!"),
        ("testuser_d3tpqv@test.com", "TestPass123!"),
        ("testuser_eql116@test.com", "TestPass123!"),
    ]
    
    for email, password in test_users:
        print(f"\n🔍 {email} 계정 데이터 정리 시도")
        async with TestDataCleaner() as cleaner:
            await cleaner.cleanup_user_data(email, password)

if __name__ == "__main__":
    asyncio.run(main())