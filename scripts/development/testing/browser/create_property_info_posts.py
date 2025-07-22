#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 11:37:00 KST
주요 컴포넌트들:
- PropertyInfoPostCreator: 새로운 카테고리별 부동산 정보 게시글 생성기 (lines 25-350)

주요 함수들:
- create_category_posts(): 카테고리별 게시글 생성 (lines 78-150)
- generate_post_content(): 카테고리별 콘텐츠 생성 (lines 152-250)
- ensure_admin_user(): 관리자 계정 확인 및 생성 (lines 252-300)

관련 파일:
- property_info_browser_test_setup.py: 브라우저 테스트 데이터 생성
- /frontend/app/config/pageConfigs.tsx: 프론트엔드 카테고리 설정
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class PropertyInfoPostCreator:
    """부동산 정보 카테고리별 게시글 생성기"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"PROPINFO_POSTS_{timestamp}_{random_suffix}"
        
        self.base_url = base_url
        
        # 새로운 부동산 정보 카테고리
        self.categories = [
            {
                "key": "market_info",
                "name": "시세 정보",
                "description": "부동산 시장 가격 동향 및 시세 분석"
            },
            {
                "key": "real_estate_knowledge",
                "name": "부동산 지식",
                "description": "부동산 법률, 제도, 전문 지식"
            },
            {
                "key": "financial_info",
                "name": "금융 정보",
                "description": "부동산 투자, 대출, 세금 관련 정보"
            },
            {
                "key": "move_in_info",
                "name": "입주 정보",
                "description": "입주 절차, 체크리스트, 생활 가이드"
            }
        ]
        
        # 관리자 계정 정보
        self.admin_credentials = {
            "username": "admin@nadle.io",
            "password": "Admin123"  # 대문자 포함 비밀번호 정책 준수
        }
        
        self.auth_token = None
        self.created_posts = []
    
    async def create_all_category_posts(self):
        """모든 카테고리별 부동산 정보 게시글 생성"""
        print("🏠 부동산 정보 카테고리별 게시글 생성 시작!")
        print(f"🆔 세션 ID: {self.session_id}")
        print("=" * 70)
        
        session = aiohttp.ClientSession()
        
        try:
            # 1. 관리자 로그인
            await self._admin_login(session)
            
            # 2. 기존 게시글 확인
            existing_posts = await self._check_existing_posts(session)
            
            # 3. 카테고리별 게시글 생성
            for category in self.categories:
                await self._create_category_posts(session, category, existing_posts)
            
            # 4. 생성 결과 보고
            await self._generate_creation_report()
            
        except Exception as e:
            print(f"\n❌ 게시글 생성 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await session.close()
        
        print("\n🎉 부동산 정보 게시글 생성 완료!")
        return True
    
    async def _admin_login(self, session: aiohttp.ClientSession):
        """관리자 로그인"""
        print("🔐 관리자 계정으로 로그인 중...")
        
        try:
            # OAuth2PasswordRequestForm은 form 데이터를 요구함
            form_data = aiohttp.FormData()
            form_data.add_field('username', self.admin_credentials["username"])
            form_data.add_field('password', self.admin_credentials["password"])
            
            async with session.post(f"{self.base_url}/api/auth/login", data=form_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    print("   ✅ 관리자 로그인 성공")
                elif response.status == 401:
                    # 관리자 계정이 없으면 생성 시도
                    print("   ⚠️ 관리자 계정이 없습니다. 생성을 시도합니다...")
                    await self._create_admin_user(session)
                    # 다시 로그인 시도
                    retry_form_data = aiohttp.FormData()
                    retry_form_data.add_field('username', self.admin_credentials["username"])
                    retry_form_data.add_field('password', self.admin_credentials["password"])
                    
                    async with session.post(f"{self.base_url}/api/auth/login", data=retry_form_data) as retry_response:
                        if retry_response.status == 200:
                            data = await retry_response.json()
                            self.auth_token = data.get("access_token")
                            print("   ✅ 관리자 로그인 성공")
                        else:
                            raise Exception(f"재로그인 실패: {retry_response.status}")
                else:
                    error_text = await response.text()
                    raise Exception(f"관리자 로그인 실패: {response.status} - {error_text}")
        except Exception as e:
            raise Exception(f"관리자 로그인 오류: {str(e)}")
    
    async def _create_admin_user(self, session: aiohttp.ClientSession):
        """관리자 계정 생성"""
        admin_user_data = {
            "email": "admin@nadle.io",
            "password": self.admin_credentials["password"],
            "user_handle": "admin",
            "display_name": "관리자",
            "name": "시스템 관리자"
        }
        
        try:
            async with session.post(f"{self.base_url}/api/auth/register", json=admin_user_data) as response:
                if response.status == 201:
                    print("   ✅ 관리자 계정 생성 성공")
                else:
                    error_text = await response.text()
                    print(f"   ⚠️ 관리자 계정 생성 실패: {response.status} - {error_text}")
        except Exception as e:
            print(f"   ⚠️ 관리자 계정 생성 오류: {e}")
    
    async def _check_existing_posts(self, session: aiohttp.ClientSession) -> Dict[str, List]:
        """기존 부동산 정보 게시글 확인"""
        print("🔍 기존 부동산 정보 게시글 확인 중...")
        
        existing_posts = {}
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            params = {
                "metadata_type": "property_information",
                "page": 1,
                "page_size": 100
            }
            async with session.get(f"{self.base_url}/api/posts/", params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get("items", [])
                    
                    # 카테고리별로 분류
                    for post in posts:
                        category = post.get("metadata", {}).get("category", "")
                        if category not in existing_posts:
                            existing_posts[category] = []
                        existing_posts[category].append(post)
                    
                    print(f"   📊 기존 게시글 {len(posts)}개 발견")
                    for category, posts_list in existing_posts.items():
                        print(f"      - {category}: {len(posts_list)}개")
                else:
                    print(f"   ⚠️ 기존 게시글 조회 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 기존 게시글 확인 오류: {e}")
        
        return existing_posts
    
    async def _create_category_posts(self, session: aiohttp.ClientSession, 
                                   category: Dict, existing_posts: Dict[str, List]):
        """카테고리별 게시글 생성"""
        category_key = category["key"]
        category_name = category["name"]
        
        print(f"\n📝 '{category_name}' 카테고리 게시글 생성")
        
        # 기존 게시글 확인 (새로운 키와 기존 키 모두 확인)
        existing_count = 0
        for key in [category_name, category_key]:
            if key in existing_posts:
                existing_count += len(existing_posts[key])
        
        # 기존 호환성을 위한 매핑
        legacy_mappings = {
            "market_info": ["시세분석", "market_analysis"],
            "real_estate_knowledge": ["법률정보", "legal_info"],
            "financial_info": ["투자동향", "investment_trend"],
            "move_in_info": ["입주가이드", "move_in_guide"]
        }
        
        if category_key in legacy_mappings:
            for legacy_key in legacy_mappings[category_key]:
                if legacy_key in existing_posts:
                    existing_count += len(existing_posts[legacy_key])
        
        # 새로운 카테고리 키로 된 게시글 확인
        new_category_posts = existing_posts.get(category_key, [])
        
        if len(new_category_posts) >= 2:
            print(f"   ✅ '{category_name}' 카테고리에 충분한 게시글이 있습니다 ({len(new_category_posts)}개)")
            return
        
        # 새로운 카테고리 키로 부족한 만큼 생성
        posts_to_create = 3 - len(new_category_posts)
        print(f"   📝 '{category_name}' 카테고리에 {posts_to_create}개 게시글 생성 필요")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        for i in range(posts_to_create):
            post_data = self._generate_post_content(category, i + 1)
            
            try:
                await asyncio.sleep(0.5)  # API 호출 간격
                async with session.post(
                    f"{self.base_url}/api/posts/", 
                    json=post_data, 
                    headers=headers
                ) as response:
                    if response.status == 201:
                        post = await response.json()
                        self.created_posts.append(post)
                        print(f"   ✅ 게시글 생성 성공: {post_data['title']}")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ 게시글 생성 실패: {response.status} - {error_text}")
            except Exception as e:
                print(f"   ❌ 게시글 생성 오류: {e}")
    
    def _generate_post_content(self, category: Dict, index: int) -> Dict:
        """카테고리별 게시글 콘텐츠 생성"""
        category_key = category["key"]
        category_name = category["name"]
        
        # 카테고리별 제목과 내용 템플릿
        content_templates = {
            "market_info": {
                "titles": [
                    "2025년 상반기 아파트 시세 동향 분석",
                    "지역별 부동산 가격 변동률 현황",
                    "최신 매매/전세 시장 트렌드 분석"
                ],
                "contents": [
                    "최근 6개월간 아파트 시세 변동을 종합 분석한 결과, 수도권을 중심으로 안정화 추세를 보이고 있습니다. 특히 강남권의 경우 전월 대비 0.2% 상승하며 소폭 상승세를 유지하고 있습니다.",
                    "지역별로 살펴보면 서울 25개구 중 15개구에서 상승, 8개구에서 보합, 2개구에서 하락하는 모습을 보였습니다. 경기도와 인천 지역도 전반적으로 안정적인 움직임을 나타내고 있습니다.",
                    "전세시장의 경우 전월 대비 0.1% 상승하며 매매시장과 비슷한 흐름을 보이고 있습니다. 전세가율은 평균 60-70% 수준을 유지하고 있어 상대적으로 안정적인 상황입니다."
                ]
            },
            "real_estate_knowledge": {
                "titles": [
                    "부동산 등기부등본 읽는 법과 확인사항",
                    "분양권 전매 시 주의사항 및 절차",
                    "부동산 계약 시 특약사항 작성 가이드"
                ],
                "contents": [
                    "등기부등본은 부동산의 법적 현황을 확인할 수 있는 중요한 서류입니다. 표제부, 갑구, 을구로 구성되어 있으며, 각각 건물의 기본정보, 소유권 현황, 권리관계를 나타냅니다.",
                    "분양권 전매는 원칙적으로 허용되나 분양계약서에 따라 제한될 수 있습니다. 전매 시에는 양도소득세, 부가세 등의 세금 부담과 함께 사업주체의 승인 절차를 거쳐야 합니다.",
                    "부동산 계약서의 특약사항은 당사자 간의 특별한 약정을 명시하는 중요한 부분입니다. 특히 잔금 지급 시기, 등기 이전 시기, 하자담보책임 등에 대해 명확히 기재해야 합니다."
                ]
            },
            "financial_info": {
                "titles": [
                    "2025년 주택담보대출 금리 동향 및 전망",
                    "부동산 투자 시 세금 절약 방법",
                    "주택청약종합저축 활용법과 청약 전략"
                ],
                "contents": [
                    "주요 시중은행의 주택담보대출 금리가 연 3.5~4.2% 수준에서 형성되고 있습니다. 고정금리와 변동금리 중 선택 시 향후 금리 전망과 개인의 상환 능력을 종합적으로 고려해야 합니다.",
                    "부동산 투자 시 양도소득세, 종합부동산세 등의 세금 부담을 줄이기 위해서는 보유기간, 거주기간, 취득 시기 등을 전략적으로 계획해야 합니다. 특히 1세대 1주택 특례를 활용하면 양도소득세를 절약할 수 있습니다.",
                    "주택청약종합저축은 청약 당첨 확률을 높이는 중요한 수단입니다. 가점제와 추첨제의 특성을 이해하고, 무주택기간과 청약통장 가입기간을 적절히 관리하는 것이 핵심입니다."
                ]
            },
            "move_in_info": {
                "titles": [
                    "신축 아파트 입주 전 점검 체크리스트",
                    "입주 시 필수 신청 사항 및 절차 안내",
                    "새 아파트 하자 발견 시 대응 방법"
                ],
                "contents": [
                    "신축 아파트 입주 전 점검에서는 벽체 균열, 바닥 기울기, 창호 개폐, 전기·배관 상태 등을 꼼꼼히 확인해야 합니다. 하자가 발견되면 즉시 사진 촬영 후 시공사에 보수를 요청하세요.",
                    "입주 시에는 관리사무소에서 세대 키 수령, 관리비 계좌 개설, 인터넷·케이블TV 신청 등의 절차를 진행해야 합니다. 또한 전입신고와 함께 각종 공과금 계좌 이전도 함께 처리하는 것이 좋습니다.",
                    "입주 후 하자를 발견했다면 관리사무소 또는 시공사에 즉시 신고해야 합니다. 하자보수기간(1-10년)이 정해져 있으므로 조기에 발견하여 무상 보수를 받는 것이 중요합니다."
                ]
            }
        }
        
        templates = content_templates.get(category_key, {
            "titles": [f"{category_name} 관련 정보"],
            "contents": [f"{category_name}에 대한 상세한 정보를 제공합니다."]
        })
        
        title = templates["titles"][index - 1] if index <= len(templates["titles"]) else f"{category_name} 정보 #{index}"
        content = templates["contents"][index - 1] if index <= len(templates["contents"]) else f"{category_name}에 대한 유용한 정보를 제공합니다."
        
        post_data = {
            "title": title,
            "content": content,
            "service": "residential_community",
            "metadata": {
                "type": "property_information",
                "category": category_name,  # 새로운 카테고리 이름 사용
                "tags": [category_name, "부동산", "정보"],
                "session_id": self.session_id,
                "auto_generated": True
            },
            "slug": f"{category_key}-{index}-{self.session_id.lower()}",
            "status": "published"
        }
        
        return post_data
    
    async def _generate_creation_report(self):
        """생성 결과 보고서"""
        print(f"\n📊 부동산 정보 게시글 생성 결과")
        print("=" * 60)
        print(f"🆔 세션 ID: {self.session_id}")
        print(f"📝 생성된 게시글: {len(self.created_posts)}개")
        
        # 카테고리별 생성 개수
        category_counts = {}
        for post in self.created_posts:
            category = post.get("metadata", {}).get("category", "기타")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            print(f"   - {category}: {count}개")
        
        print(f"\n🎯 목표 달성: 모든 카테고리별 부동산 정보 게시글 확보")
        print(f"   - 시세 정보, 부동산 지식, 금융 정보, 입주 정보")
        
        # JSON 보고서 저장
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "created_posts": self.created_posts,
            "categories": self.categories,
            "summary": {
                "total_created": len(self.created_posts),
                "category_counts": category_counts
            }
        }
        
        report_path = Path(__file__).parent / f"property_info_posts_creation_report_{self.session_id}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📄 JSON 보고서 저장: {report_path}")
        except Exception as e:
            print(f"\n⚠️ 보고서 저장 실패: {e}")


async def main():
    """메인 실행 함수"""
    print("🏠 부동산 정보 카테고리별 게시글 생성기")
    print("새로운 4개 카테고리: 시세 정보, 부동산 지식, 금융 정보, 입주 정보")
    print("=" * 80)
    
    creator = PropertyInfoPostCreator()
    success = await creator.create_all_category_posts()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))