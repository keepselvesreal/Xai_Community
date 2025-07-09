#!/usr/bin/env python3
"""
올바른 JSON 형태의 서비스 게시글 작성
"""
import asyncio
import aiohttp
import json
from datetime import datetime

class ServicePostCreator:
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
    
    async def create_service_post(self):
        """올바른 JSON 형태의 서비스 게시글 작성"""
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
        
        post_data = {
            "title": f"올바른 JSON 형태 입주 서비스 업체 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": json.dumps(service_data, ensure_ascii=False, indent=2),
            "service": "residential_community",
            "metadata": {
                "type": "moving_services",
                "category": "입주 서비스",
                "tags": ["입주", "서비스", "업체"],
                "editor_type": "plain",
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
    async with ServicePostCreator() as creator:
        # 기존 사용자로 로그인
        await creator.login("testuser_nyxt69@test.com", "TestPass123!")
        
        # 올바른 JSON 형태의 서비스 게시글 작성
        result = await creator.create_service_post()
        
        if result:
            print(f"\n🎉 성공! 새로운 서비스 게시글이 생성되었습니다.")
            print(f"URL: /moving-services/{result['slug']}")

if __name__ == "__main__":
    asyncio.run(main())