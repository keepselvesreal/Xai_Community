#!/usr/bin/env python3
"""
Expert Tips Test Data Generator (API Version)

This script generates expert tips test data using the FastAPI REST endpoints.
It creates posts with metadata.type = "expert_tips" through HTTP API calls.
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# API Configuration
API_BASE = "http://localhost:8000"
API_ENDPOINTS = {
    "register": f"{API_BASE}/api/auth/register",
    "login": f"{API_BASE}/api/auth/login",
    "posts": f"{API_BASE}/api/posts",
    "search": f"{API_BASE}/api/posts/search"
}

# Expert tip categories and their related keywords
EXPERT_CATEGORIES = {
    "인테리어": ["방 꾸미기", "가구 배치", "색상 선택", "조명", "수납", "소품"],
    "생활팁": ["청소", "정리정돈", "절약", "효율성", "생활습관", "건강"],
    "요리": ["레시피", "요리법", "식재료", "주방용품", "건강식", "간편식"],
    "육아": ["아이 돌보기", "교육", "놀이", "건강관리", "소통", "성장"],
    "반려동물": ["반려견", "반려묘", "건강관리", "훈련", "용품", "놀이"],
    "가드닝": ["식물 키우기", "베란다", "화분", "물주기", "흙", "햇빛"],
    "DIY": ["만들기", "수리", "조립", "도구", "재료", "창작"],
    "건강": ["운동", "스트레칭", "영양", "수면", "스트레스", "관리"],
    "재정관리": ["절약", "투자", "가계부", "적금", "보험", "계획"],
    "취미": ["독서", "음악", "영화", "게임", "수집", "체험"]
}

# Expert profiles for generating realistic data
EXPERT_PROFILES = [
    {"name": "김민수", "title": "인테리어 디자이너", "specialties": ["인테리어", "DIY"]},
    {"name": "박영희", "title": "생활컨설턴트", "specialties": ["생활팁", "정리정돈"]},
    {"name": "이준호", "title": "요리연구가", "specialties": ["요리", "건강"]},
    {"name": "최수진", "title": "육아전문가", "specialties": ["육아", "교육"]},
    {"name": "정민아", "title": "반려동물 훈련사", "specialties": ["반려동물", "건강"]},
    {"name": "홍길동", "title": "가드닝 전문가", "specialties": ["가드닝", "생활팁"]},
    {"name": "서지혜", "title": "DIY 크리에이터", "specialties": ["DIY", "인테리어"]},
    {"name": "강태우", "title": "헬스 트레이너", "specialties": ["건강", "운동"]},
    {"name": "윤소영", "title": "재정관리 전문가", "specialties": ["재정관리", "절약"]},
    {"name": "한승우", "title": "취미생활 큐레이터", "specialties": ["취미", "생활팁"]}
]

# Expert tip content templates
EXPERT_TIP_TEMPLATES = {
    "인테리어": [
        {
            "title": "작은 방을 넓어 보이게 하는 {tip_detail} 방법",
            "content": """작은 방을 넓어 보이게 하려면 다음과 같은 방법을 사용해보세요:

## 1. 밝은 색상 활용
벽지와 가구를 밝은 색으로 선택하여 공간감을 확대시킵니다. 흰색, 베이지, 연한 회색 등이 효과적입니다.

## 2. 거울 배치
창문 맞은편에 큰 거울을 설치하여 자연광을 반사시키고 공간을 두 배로 넓어 보이게 합니다.

## 3. 수직 공간 활용
높은 선반과 벽걸이 수납을 이용해 바닥 공간을 확보하고, 시선을 위로 끌어올립니다.

## 4. 투명 가구 사용
유리나 아크릴 소재의 가구를 사용하여 시각적 부담을 줄이고 개방감을 조성합니다.

## 5. 멀티 가구 활용
하나의 가구가 여러 기능을 할 수 있도록 선택하여 공간을 효율적으로 사용합니다.

이러한 방법들을 조합하여 사용하면 좁은 공간도 훨씬 넓고 쾌적하게 느낄 수 있습니다.""",
            "keywords": ["공간 확장", "밝은 색상", "거울", "수납"]
        },
        {
            "title": "아파트 현관 {tip_detail} 인테리어 꿀팁",
            "content": """아파트 현관을 더욱 실용적이고 예쁘게 만들어보세요:

## 공간 활용 팁
- **벽면 활용**: 현관 벽면에 후크를 설치하여 가방이나 우산을 걸 수 있게 합니다
- **상단 공간**: 신발장 위 공간에 작은 화분이나 소품을 배치합니다
- **거울 설치**: 전신거울을 설치하여 외출 전 마지막 점검을 할 수 있게 합니다

## 분위기 연출
- **조명**: 따뜻한 색온도의 조명을 사용하여 집에 들어오는 순간부터 편안함을 느끼게 합니다
- **계절 소품**: 계절에 맞는 소품으로 포인트를 주어 항상 새로운 느낌을 연출합니다
- **향**: 향초나 디퓨저로 좋은 향을 연출하여 후각적 만족도를 높입니다

## 수납 최적화
- **신발 정리**: 자주 신는 신발과 계절 신발을 분리하여 보관합니다
- **우산꽂이**: 젖은 우산을 위한 별도의 보관공간을 마련합니다
- **열쇠 보관**: 열쇠와 같은 소품을 위한 전용 공간을 만듭니다

현관은 집의 첫인상을 결정하는 중요한 공간이니 신경 써서 꾸며보세요!""",
            "keywords": ["현관 인테리어", "수납", "조명", "소품"]
        }
    ],
    "생활팁": [
        {
            "title": "전기요금 {tip_detail}% 절약하는 실용적인 방법",
            "content": """전기요금을 크게 절약할 수 있는 실용적인 방법들을 소개합니다:

## 가전제품 효율적 사용법

### 에어컨 관리
- **적정온도 설정**: 여름 26-28°C, 겨울 18-20°C 유지
- **필터 청소**: 월 1회 필터 청소로 효율성 향상
- **문 닫기**: 사용 시 문과 창문을 닫아 냉난방 효율 극대화

### 냉장고 관리
- **문 여는 횟수 줄이기**: 필요한 것을 미리 정리하여 한 번에 꺼내기
- **적정 온도 유지**: 냉장실 3-4°C, 냉동실 -18°C 설정
- **60-70% 채우기**: 너무 비우거나 가득 채우지 않기

### 세탁기 효율 사용
- **찬물 사용**: 대부분의 세탁은 찬물로도 충분
- **적정량 세탁**: 용량의 80% 정도로 한 번에 세탁
- **자연 건조**: 가능한 자연 건조 활용

## 전력 절약 생활 습관

### 대기전력 차단
- **멀티탭 스위치 활용**: 사용하지 않는 전자제품의 플러그 뽑기
- **완전 전원 차단**: TV, 컴퓨터 등은 대기모드가 아닌 완전 차단

### 조명 관리
- **LED 전구 교체**: 백열전구 대비 80% 전력 절약
- **자연채광 활용**: 낮시간에는 가능한 자연광 이용
- **필요한 곳만 켜기**: 사용하지 않는 방의 조명 끄기

## 계절별 절약 팁

### 여름철
- **선풍기와 에어컨 함께 사용**: 체감온도 2-3도 낮춤 효과
- **냉장고 문 자주 열지 않기**: 찬 공기 손실 최소화

### 겨울철
- **보온용품 활용**: 전기장판보다 두꺼운 이불이나 담요 사용
- **창문 단열**: 뽁뽁이나 단열재로 창문 단열 강화

이 방법들을 실천하면 월 전기요금을 20-30% 절약할 수 있습니다!""",
            "keywords": ["전기요금", "절약", "가전제품", "생활습관"]
        }
    ],
    "요리": [
        {
            "title": "초보자도 실패없는 {tip_detail} 요리법",
            "content": """요리 초보자도 쉽게 따라할 수 있는 간단한 요리법을 소개합니다:

## 기본 준비사항

### 필수 도구
- **기본 도구**: 도마, 칼, 프라이팬, 냄비
- **계량 도구**: 계량컵, 계량스푼
- **보조 도구**: 뒤집개, 국자, 집게

### 기본 재료 (항상 준비)
- **조미료**: 소금, 후추, 간장, 식용유
- **양념**: 마늘, 양파, 생강
- **기본 채소**: 당근, 양배추, 감자

## 실패하지 않는 요리 순서

### 1단계: 계획 세우기
- **메뉴 선정**: 간단한 요리부터 시작
- **재료 준비**: 모든 재료를 미리 손질하고 계량
- **순서 확인**: 조리 순서를 미리 숙지

### 2단계: 기본 조리법 익히기
- **중간 불 사용**: 처음에는 강불보다 중간 불로 천천히
- **간 보기**: 조리 중간중간 맛을 보며 간 조절
- **타이밍**: 재료 투입 타이밍이 가장 중요

### 3단계: 마무리
- **간 맞추기**: 마지막에 전체적인 간 조절
- **플레이팅**: 깔끔하게 담아내기
- **정리**: 조리 후 즉시 설거지

## 초보자 추천 레시피

### 계란볶음밥
1. 밥과 계란, 기본 야채 준비
2. 계란을 먼저 볶아 덜어내기
3. 야채 볶은 후 밥 넣고 볶기
4. 계란 다시 넣고 간 맞추기

### 김치찌개
1. 김치를 먼저 볶아 신맛 제거
2. 물과 육수 넣고 끓이기
3. 두부, 파 등 재료 순서대로 투입
4. 간 맞추고 마무리

## 성공을 위한 꿀팁

### 실패 방지법
- **레시피 정확히 따르기**: 처음에는 창의적 변화 자제
- **재료 아끼지 말기**: 정량을 지키는 것이 중요
- **서두르지 않기**: 천천히 차근차근 진행

### 발전 방법
- **기록하기**: 성공한 레시피와 실패 원인 기록
- **단계적 발전**: 기본기를 익힌 후 응용 도전
- **경험 쌓기**: 같은 요리를 여러 번 반복 연습

한 번 성공하면 다음부터는 자신만의 변화를 줄 수 있어요!""",
            "keywords": ["초보 요리", "레시피", "조리법", "간단"]
        }
    ],
    "건강": [
        {
            "title": "하루 10분 {tip_detail} 운동으로 건강 챙기기",
            "content": """바쁜 일상 속에서도 할 수 있는 간단한 운동법을 소개합니다:

## 시간대별 운동 계획

### 아침 운동 (5분)
**목표**: 하루를 시작하는 활력 충전

1. **목과 어깨 스트레칭** (2분)
   - 목을 좌우, 앞뒤로 천천히 돌리기
   - 어깨를 위아래, 앞뒤로 돌리기

2. **허리 스트레칭** (1분)
   - 허리를 좌우로 비틀기
   - 앞으로 굽혀 스트레칭

3. **제자리 걷기** (2분)
   - 무릎을 높이 올리며 제자리에서 걷기
   - 팔도 함께 움직여 전신 활성화

### 점심 운동 (3분)
**목표**: 오전 업무 피로 해소

1. **의자 운동** (2분)
   - 의자에 앉아 다리 들어 올리기
   - 발목 돌리기, 종아리 스트레칭

2. **상체 운동** (1분)
   - 어깨 돌리기
   - 목 좌우 스트레칭

### 저녁 운동 (2분)
**목표**: 하루 종료 전 몸 정리

1. **요가 자세** (1분)
   - 고양이 자세로 등 스트레칭
   - 아이 자세로 몸 이완

2. **복부 운동** (1분)
   - 플랭크 30초 x 2세트
   - 복식호흡으로 마무리

## 운동 효과

### 신체적 효과
- **혈액순환 개선**: 장시간 앉아있는 직장인에게 특히 효과적
- **근력 유지**: 기본적인 근력과 유연성 유지
- **체력 향상**: 꾸준한 운동으로 전반적인 체력 향상

### 정신적 효과
- **스트레스 해소**: 운동을 통한 스트레스 호르몬 감소
- **집중력 향상**: 혈액순환 개선으로 뇌 기능 활성화
- **수면의 질 개선**: 적절한 운동으로 숙면 유도

## 지속하는 방법

### 습관 만들기
- **알람 설정**: 운동 시간을 정해두고 알람 설정
- **운동 달력**: 달력에 체크하며 성취감 느끼기
- **점진적 증가**: 익숙해지면 조금씩 강도나 시간 늘리기

### 동기 유지
- **목표 설정**: 작은 목표부터 차근차근 달성
- **기록 관리**: 운동 일지 작성으로 변화 관찰
- **함께하기**: 가족이나 동료와 함께 동기 부여

## 주의사항

### 안전 수칙
- **무리하지 않기**: 몸의 신호를 들으며 적당히 조절
- **통증 시 중단**: 운동 중 통증이 있으면 즉시 중단
- **충분한 수분**: 운동 전후 충분한 수분 섭취

### 효과 극대화
- **일정한 시간**: 매일 같은 시간에 운동하여 생체리듬 형성
- **정확한 자세**: 횟수보다 정확한 자세가 중요
- **꾸준함**: 하루 걸러 하루보다 매일 조금씩이 더 효과적

건강한 습관을 만들어 더 활기찬 하루를 보내세요!""",
            "keywords": ["간단 운동", "건강 관리", "스트레칭", "일상"]
        }
    ]
}

class ExpertTipsGenerator:
    """Expert tips generator using HTTP API calls."""
    
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def create_test_user(self) -> bool:
        """Create and authenticate test user."""
        user_data = {
            "email": "expert_tips_admin@example.com",
            "user_handle": "expert_admin",
            "name": "Expert Tips Admin",
            "display_name": "Expert Tips Admin",
            "password": "TestPassword123!"
        }
        
        try:
            # Try to login first (user might already exist)
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }
            
            async with self.session.post(API_ENDPOINTS["login"], json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result["access_token"]
                    print(f"✅ Logged in as existing user: {user_data['email']}")
                    return True
        except:
            pass
        
        # If login failed, try to register
        try:
            async with self.session.post(API_ENDPOINTS["register"], json=user_data) as response:
                if response.status == 201:
                    print(f"✅ Registered new user: {user_data['email']}")
                    
                    # Login after registration
                    login_data = {
                        "email": user_data["email"],
                        "password": user_data["password"]
                    }
                    
                    async with self.session.post(API_ENDPOINTS["login"], json=login_data) as login_response:
                        if login_response.status == 200:
                            result = await login_response.json()
                            self.auth_token = result["access_token"]
                            print(f"✅ Logged in after registration")
                            return True
                        else:
                            print(f"❌ Login failed after registration: {login_response.status}")
                            return False
                else:
                    error_text = await response.text()
                    print(f"❌ Registration failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error during user creation: {str(e)}")
            return False
    
    def generate_expert_tip_data(self, expert: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Generate a single expert tip data structure."""
        templates = EXPERT_TIP_TEMPLATES.get(category, [])
        if not templates:
            # Fallback template
            templates = [{
                "title": f"{category} 전문가 팁",
                "content": f"""# {category} 전문가의 조언

{category} 분야의 전문가로서 실생활에 도움이 되는 실용적인 팁을 제공합니다.

## 핵심 포인트
- 전문가의 경험을 바탕으로 한 검증된 방법
- 누구나 쉽게 따라할 수 있는 실용적인 내용
- 실제 효과를 경험할 수 있는 구체적인 방법

## 실천 방법
1. 기본적인 이해
2. 단계적 접근
3. 꾸준한 실천
4. 개인화 적용

전문가의 조언을 통해 더 나은 결과를 얻어보세요!""",
                "keywords": [category, "팁", "전문가"]
            }]
        
        template = random.choice(templates)
        keywords = EXPERT_CATEGORIES.get(category, [category])
        
        # Generate specific tip details
        tip_details = [
            "3가지 핵심", "5단계", "완벽한", "실용적인", "간단한", 
            "효과적인", "전문가의", "검증된", "실전", "꿀"
        ]
        
        tip_detail = random.choice(tip_details)
        title = template["title"].format(tip_detail=tip_detail)
        
        # Generate tags
        tags = random.sample(keywords, min(3, len(keywords)))
        
        # Generate view counts and engagement metrics
        views_count = random.randint(150, 2500)
        likes_count = random.randint(10, int(views_count * 0.15))
        saves_count = random.randint(5, int(views_count * 0.08))
        
        # Generate creation date (within last 6 months)
        days_ago = random.randint(1, 180)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        # Determine if it's "new" (within last 7 days)
        is_new = days_ago <= 7
        
        return {
            "title": title,
            "content": template["content"],
            "service": "residential_community",
            "metadata": {
                "type": "expert_tips",
                "category": category,
                "tags": tags,
                "expert_name": expert["name"],
                "expert_title": expert["title"],
                "views_count": views_count,
                "likes_count": likes_count,
                "saves_count": saves_count,
                "is_new": is_new,
                "visibility": "public",
                "editor_type": "markdown"
            }
        }
    
    async def create_expert_tip(self, tip_data: Dict[str, Any]) -> bool:
        """Create a single expert tip via API."""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(API_ENDPOINTS["posts"], json=tip_data, headers=headers) as response:
                if response.status == 201:
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create tip '{tip_data['title'][:50]}...': {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error creating tip '{tip_data['title'][:50]}...': {str(e)}")
            return False
    
    async def generate_expert_tips(self, num_tips: int = 30) -> List[Dict[str, Any]]:
        """Generate multiple expert tips."""
        created_tips = []
        
        for i in range(num_tips):
            # Select random expert and category
            expert = random.choice(EXPERT_PROFILES)
            # Choose category from expert's specialties
            category = random.choice(expert["specialties"])
            
            # Generate tip data
            tip_data = self.generate_expert_tip_data(expert, category)
            
            # Create tip via API
            success = await self.create_expert_tip(tip_data)
            
            if success:
                created_tips.append(tip_data)
                print(f"✅ Created expert tip {i+1}/{num_tips}: {tip_data['title'][:50]}...")
            else:
                print(f"❌ Failed to create expert tip {i+1}/{num_tips}")
        
        return created_tips
    
    async def verify_created_tips(self) -> Dict[str, Any]:
        """Verify that expert tips were created successfully."""
        try:
            params = {
                "metadata_type": "expert_tips",
                "page": 1,
                "page_size": 50
            }
            
            async with self.session.get(API_ENDPOINTS["posts"], params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    tips = result.get("items", [])
                    
                    print(f"\n📊 Verification Results:")
                    print(f"   Total expert tips found: {len(tips)}")
                    
                    # Analyze by category
                    categories = {}
                    experts = {}
                    
                    for tip in tips:
                        metadata = tip.get("metadata", {})
                        category = metadata.get("category", "Unknown")
                        expert_name = metadata.get("expert_name", "Unknown")
                        
                        categories[category] = categories.get(category, 0) + 1
                        experts[expert_name] = experts.get(expert_name, 0) + 1
                    
                    print(f"   Categories: {dict(categories)}")
                    print(f"   Experts: {dict(experts)}")
                    
                    return {
                        "total_tips": len(tips),
                        "categories": categories,
                        "experts": experts,
                        "tips": tips
                    }
                else:
                    print(f"❌ Verification failed: {response.status}")
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
            return {"error": str(e)}

async def main():
    """Main function to generate expert tips test data via API."""
    print("🚀 Expert Tips Test Data Generator (API Version)")
    print("=" * 60)
    
    async with ExpertTipsGenerator() as generator:
        try:
            # Create and authenticate test user
            print("1. Creating and authenticating test user...")
            if not await generator.create_test_user():
                print("❌ Failed to create/authenticate user")
                return
            
            # Generate expert tips
            print("2. Generating expert tips...")
            num_tips = 30  # Generate 30 expert tips
            created_tips = await generator.generate_expert_tips(num_tips)
            
            print(f"\n✅ Successfully created {len(created_tips)} expert tips!")
            
            # Verify creation
            print("3. Verifying created tips...")
            verification = await generator.verify_created_tips()
            
            # Generate summary report
            print("\n" + "=" * 60)
            print("📋 EXPERT TIPS GENERATION SUMMARY")
            print("=" * 60)
            print(f"✅ Total tips created: {len(created_tips)}")
            print(f"✅ API connection: Success")
            print(f"✅ Authentication: Success")
            print(f"✅ Verification: {verification.get('total_tips', 0)} tips found")
            
            # Show sample tips
            if created_tips:
                print("\n🎯 Sample Expert Tips:")
                for i, tip in enumerate(created_tips[:3]):
                    metadata = tip["metadata"]
                    print(f"\n{i+1}. {tip['title']}")
                    print(f"   Expert: {metadata['expert_name']} ({metadata['expert_title']})")
                    print(f"   Category: {metadata['category']}")
                    print(f"   Tags: {', '.join(metadata['tags'])}")
                    print(f"   Views: {metadata['views_count']}")
            
            print("\n" + "=" * 60)
            print("🎉 Expert Tips Test Data Generation Complete!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error during expert tips generation: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())