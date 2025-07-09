#!/usr/bin/env python3
"""
기존 서비스 글 참고하여 올바른 형태로 작성
"""
import asyncio
import aiohttp
import json
from datetime import datetime

class ProperServicePostCreator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.access_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self, email: str, password: str):
        """로그인"""
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
                result = await response.json()
                
                if response.status == 200:
                    self.access_token = result["access_token"]
                    print(f"✅ 로그인 성공")
                    return True
                else:
                    print(f"❌ 로그인 실패: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return False
    
    def get_auth_headers(self):
        """인증 헤더 생성"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def delete_post(self, post_id: str):
        """게시글 삭제"""
        try:
            async with self.session.delete(
                f"{self.base_url}/api/posts/{post_id}",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    print(f"✅ 게시글 삭제 성공: {post_id}")
                    return True
                else:
                    print(f"❌ 게시글 삭제 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 게시글 삭제 오류: {str(e)}")
            return False
    
    async def create_proper_service_post(self):
        """기존 서비스 글 형태를 참고하여 올바른 서비스 게시글 작성"""
        # 기존 서비스 글과 동일한 형태로 작성
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
                    "price": 200000,  # 숫자 형태로 (기존 글 참고)
                    "specialPrice": 150000
                },
                {
                    "name": "인테리어 서비스", 
                    "price": 500000
                },
                {
                    "name": "청소 서비스",
                    "price": 80000,
                    "specialPrice": 60000
                }
            ]
        }
        
        post_data = {
            "title": f"테스트 입주 서비스 업체 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": json.dumps(service_data, ensure_ascii=False, indent=2),
            "service": "residential_community",
            "metadata": {
                "type": "moving services",  # 공백 포함 (기존 글과 동일)
                "category": "입주 서비스",
                "tags": ["입주", "서비스", "업체"],
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
                    print(f"✅ 서비스 게시글 작성 성공: {result['title']}")
                    print(f"   슬러그: {result['slug']}")
                    return result
                else:
                    print(f"❌ 서비스 게시글 작성 실패: {result}")
                    return None
                    
        except Exception as e:
            print(f"❌ 서비스 게시글 작성 오류: {str(e)}")
            return None

async def main():
    async with ProperServicePostCreator() as creator:
        # 기존 사용자로 로그인
        await creator.login("testuser_nyxt69@test.com", "TestPass123!")
        
        # 기존 잘못된 글들 삭제
        print("🗑️ 기존 잘못된 글들 삭제 중...")
        await creator.delete_post("686e66e2ce3b9447b1ca25ba-올바른-json-형태-입주-서비스-업체-2025-07-09-215602")
        await creator.delete_post("686e6324ce3b9447b1ca25b3-입주-서비스-업체-추천-2025-07-09-214004")
        
        # 올바른 형태의 서비스 게시글 작성
        print("\n📝 올바른 서비스 게시글 작성 중...")
        result = await creator.create_proper_service_post()
        
        if result:
            print(f"\n🎉 성공! 새로운 서비스 게시글이 생성되었습니다.")
            print(f"URL: /moving-services/{result['slug']}")
            print(f"이제 프론트엔드에서 접근해보세요!")

if __name__ == "__main__":
    asyncio.run(main())