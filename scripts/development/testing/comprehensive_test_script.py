#!/usr/bin/env python3
"""
포괄적인 테스트 스크립트 - 다양한 페이지에 게시글과 댓글 작성
"""
import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime
from typing import Dict, Optional, List

class ComprehensiveTestAutomation:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.user_data: Optional[Dict] = None
        self.created_posts: List[Dict] = []
        
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
        password = "TestPass123!"
        
        return {
            "name": f"테스트 사용자 {username}",
            "email": email,
            "user_handle": username,
            "password": password,
            "display_name": f"테스트 사용자 {username}",
            "bio": "다양한 페이지 테스트를 위한 계정입니다."
        }
    
    async def register_user(self) -> Dict:
        """회원가입"""
        print("🚀 회원가입 시작...")
        
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
        print("🔐 로그인 시작...")
        
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
    
    async def create_post(self, post_type: str, category: str, title: str, content: str) -> Dict:
        """게시글 작성"""
        print(f"📝 게시글 작성 시작: {title[:30]}...")
        
        post_data = {
            "title": title,
            "content": content,
            "service": "residential_community",
            "metadata": {
                "type": post_type,
                "category": category,
                "tags": ["테스트", "자동화", post_type],
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
                    print(f"✅ 게시글 작성 성공: {result['title']}")
                    print(f"   슬러그: {result['slug']}")
                    self.created_posts.append(result)
                    return {"success": True, "data": result}
                else:
                    print(f"❌ 게시글 작성 실패: {result}")
                    return {"success": False, "error": result}
                    
        except Exception as e:
            print(f"❌ 게시글 작성 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_existing_posts(self) -> List[Dict]:
        """기존 게시글 목록 조회"""
        print("🔍 기존 게시글 조회 중...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/posts/?page=1&page_size=20",
                headers=self.get_auth_headers()
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    posts = result.get("posts", [])
                    print(f"✅ 기존 게시글 {len(posts)}개 조회 완료")
                    return posts
                else:
                    print(f"❌ 게시글 조회 실패: {result}")
                    return []
                    
        except Exception as e:
            print(f"❌ 게시글 조회 오류: {str(e)}")
            return []
    
    async def create_comment(self, post_slug: str, content: str) -> Dict:
        """댓글 작성"""
        print(f"💬 댓글 작성 시작: {content[:30]}...")
        
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
    
    async def run_comprehensive_test(self):
        """포괄적인 테스트 실행"""
        print("🎯 포괄적인 테스트 시작!")
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
        
        # 2. 다양한 페이지에 게시글 작성
        print("\\n" + "=" * 60)
        print("📝 다양한 페이지에 게시글 작성")
        print("=" * 60)
        
        # 2-1. 자유게시판 게시글
        await self.create_post(
            post_type="board",
            category="자유게시판",
            title=f"자유게시판 테스트 게시글 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            content=f"""# 자유게시판 테스트 게시글입니다! 🎉

안녕하세요! 자유게시판에 테스트 게시글을 작성해보았습니다.

## 테스트 내용
- 작성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
- 게시판 유형: 자유게시판
- 작성자: {self.user_data['user_handle']}

## 목적
이 게시글은 자유게시판 기능 테스트를 위해 작성되었습니다.

**잘 작동하고 있나요?** 👍"""
        )
        
        # 2-2. 입주 서비스 업체 페이지 게시글 (JSON 형태)
        service_data = {
            "company": {
                "name": f"테스트 입주 서비스 업체 - {datetime.now().strftime('%H:%M')}",
                "contact": "010-1234-5678",
                "availableHours": "09:00-18:00",
                "description": "입주 관련 모든 서비스를 제공하는 전문 업체입니다. 이사, 인테리어, 청소 등 원스톱 서비스로 편리하게 이용하세요."
            },
            "services": [
                {
                    "name": "이사 서비스",
                    "price": "200000",
                    "specialPrice": "150000",
                    "description": "전문 이사팀이 안전하고 신속하게 이사 서비스를 제공합니다"
                },
                {
                    "name": "인테리어 서비스",
                    "price": "500000",
                    "description": "입주 후 인테리어 설치 및 배치 서비스"
                },
                {
                    "name": "청소 서비스",
                    "price": "80000",
                    "specialPrice": "60000",
                    "description": "입주 전후 전문 청소 서비스"
                }
            ]
        }
        
        await self.create_post(
            post_type="moving_services",
            category="입주 서비스",
            title=f"입주 서비스 업체 추천 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            content=json.dumps(service_data, ensure_ascii=False, indent=2)
        )
        
        # 2-3. 전문가의 꿀정보 페이지 게시글
        await self.create_post(
            post_type="expert_tips",
            category="전문가 꿀정보",
            title=f"전문가 꿀정보 - 효율적인 이사 팁 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            content=f"""# 전문가가 알려주는 이사 꿀정보! 🍯

이사 전문가로서 유용한 팁을 공유드립니다.

## 이사 전 체크리스트
- 작성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
- 전문가: {self.user_data['user_handle']}

## 핵심 팁
1. **포장 재료 미리 준비하기** 📦
   - 박스, 테이프, 뽁뽁이 등
   
2. **라벨링 시스템 구축** 🏷️
   - 방별로 색깔 구분
   - 우선순위 표시

3. **필수품 따로 보관** 💼
   - 하루치 생필품
   - 중요 서류

**전문가 팁이 도움이 되길 바랍니다!** 💡"""
        )
        
        # 3. 기존 게시글에 댓글 작성
        print("\\n" + "=" * 60)
        print("💬 기존 게시글에 댓글 작성")
        print("=" * 60)
        
        existing_posts = await self.get_existing_posts()
        
        # 내가 작성한 글이 아닌 다른 글을 찾아서 댓글 작성
        other_posts = [post for post in existing_posts if post.get("author_id") != str(login_result["data"]["user"]["_id"])]
        
        if other_posts:
            target_post = other_posts[0]
            await self.create_comment(
                post_slug=target_post["slug"],
                content=f"""좋은 글이네요! 👍

{datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}에 댓글을 달았습니다.

이런 정보는 정말 유용해요. 감사합니다!

**앞으로도 좋은 글 부탁드립니다!** 🙏"""
            )
        else:
            print("❌ 댓글을 달 수 있는 다른 사용자의 게시글이 없습니다.")
        
        # 4. 결과 요약
        print("\\n" + "=" * 60)
        print("🎊 포괄적인 테스트 완료!")
        print("=" * 60)
        
        print(f"✅ 생성된 사용자: {self.user_data['user_handle']} ({self.user_data['email']})")
        print(f"✅ 생성된 게시글: {len(self.created_posts)}개")
        
        for i, post in enumerate(self.created_posts, 1):
            post_type = post.get("metadata", {}).get("type", "unknown")
            print(f"   {i}. {post_type}: {post['title']}")
        
        if other_posts:
            print(f"✅ 댓글 작성: 1개 (다른 사용자의 게시글에)")
        else:
            print(f"⚠️  댓글 작성: 0개 (다른 사용자의 게시글 없음)")
        
        print(f"\\n📧 테스트 계정 정보:")
        print(f"   이메일: {self.user_data['email']}")
        print(f"   패스워드: {self.user_data['password']}")

async def main():
    """메인 실행 함수"""
    async with ComprehensiveTestAutomation() as automation:
        await automation.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())