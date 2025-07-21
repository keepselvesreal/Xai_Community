#!/usr/bin/env python3
"""
테스트용 등록 문의 데이터 생성
"""
import asyncio
import aiohttp
import json
from datetime import datetime

class TestInquiryCreator:
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
        """인증 헤더 반환"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def create_inquiry(self, title: str, content: str, inquiry_type: str):
        """문의 생성"""
        inquiry_data = {
            "title": title,
            "content": content,
            "service": "residential_community",
            "metadata": {
                "type": inquiry_type
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts/",
                data=json.dumps(inquiry_data),
                headers=self.get_auth_headers()
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    print(f"✅ 문의 생성 성공: {title}")
                    return True
                else:
                    print(f"❌ 문의 생성 실패: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ 문의 생성 오류: {str(e)}")
            return False

async def main():
    """메인 함수"""
    print("=== 테스트 문의 데이터 생성 시작 ===")
    
    async with TestInquiryCreator() as creator:
        # 로그인
        if not await creator.login("ktsfrank@naver.com", "Kts137900!"):
            return
        
        # 입주 업체 서비스 등록 문의 생성
        inquiries = [
            {
                "title": "입주 업체 서비스 등록 문의 - 청소업체",
                "content": json.dumps({
                    "content": "안녕하세요. 저희는 전문 청소업체입니다. 입주 업체 서비스에 등록하고 싶습니다.",
                    "contact": "010-1234-5678",
                    "website_url": "https://clean-service.com"
                }),
                "type": "moving-services-register-inquiry"
            },
            {
                "title": "입주 업체 서비스 등록 문의 - 수리업체",
                "content": json.dumps({
                    "content": "아파트 수리 전문 업체입니다. 서비스 등록을 원합니다.",
                    "contact": "010-9876-5432",
                    "website_url": "https://repair-service.com"
                }),
                "type": "moving-services-register-inquiry"
            },
            {
                "title": "전문가 꿀정보 등록 문의 - 요리 전문가",
                "content": json.dumps({
                    "content": "요리 전문가입니다. 꿀정보를 공유하고 싶습니다.",
                    "contact": "010-1111-2222",
                    "website_url": "https://cooking-tips.com"
                }),
                "type": "expert-tips-register-inquiry"
            },
            {
                "title": "전문가 꿀정보 등록 문의 - 인테리어 전문가",
                "content": json.dumps({
                    "content": "인테리어 관련 유용한 정보를 공유하고 싶습니다.",
                    "contact": "010-3333-4444",
                    "website_url": "https://interior-tips.com"
                }),
                "type": "expert-tips-register-inquiry"
            }
        ]
        
        for inquiry in inquiries:
            await creator.create_inquiry(
                inquiry["title"],
                inquiry["content"],
                inquiry["type"]
            )
            await asyncio.sleep(0.5)  # API 부하 방지
    
    print("=== 테스트 문의 데이터 생성 완료 ===")

if __name__ == "__main__":
    asyncio.run(main())