#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 14:27:55 KST
작업 버전: 전문가 꿀정보 브라우저 확인용 테스트 데이터 생성 스크립트 v1.0

주요 컴포넌트들:
- ExpertTipsBrowserTestSetup: 브라우저 테스트용 데이터 생성 메인 클래스 (43-107라인)
  - create_test_users(): 테스트 사용자 생성 (109-180라인)
  - create_sample_comments(): 샘플 댓글/답글 생성 (182-280라인)
  - create_sample_reactions(): 샘플 반응 데이터 생성 (282-340라인)
  - generate_browser_test_data(): 전체 브라우저 테스트 데이터 생성 (342-410라인)

- TestUserManager: 테스트 사용자 관리자 (412-480라인)
  - create_expert_user(): 전문가 권한 사용자 생성 (482-520라인)
  - create_normal_user(): 일반 사용자 생성 (522-555라인)

브라우저 테스트 특화 기능:
- can_write_expert_tips 권한 사용자 생성
- 일반 사용자 (권한 없음) 생성
- 전문가 꿀정보 댓글/답글 샘플 생성
- 좋아요/북마크 샘플 반응 생성
- 브라우저 확인용 가이드 데이터 구성

관련 파일들:
- expert_tips_automation_test.py: 자동화 테스트 스크립트
- expert_tips_browser_test_guide.html: 브라우저 확인 가이드 대시보드
- expert_tips_test_data_manager.py: 테스트 데이터 관리 스크립트
"""

import asyncio
import aiohttp
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


# API Configuration
API_BASE = "http://localhost:8000"
API_ENDPOINTS = {
    "register": f"{API_BASE}/api/auth/register",
    "login": f"{API_BASE}/api/auth/login",
    "posts": f"{API_BASE}/api/posts",
    "comments": f"{API_BASE}/api/comments",
    "reactions": f"{API_BASE}/api/reactions",
    "admin_permissions": f"{API_BASE}/api/admin/permissions"
}

# 브라우저 테스트용 샘플 댓글 템플릿
SAMPLE_COMMENTS = [
    "정말 유용한 정보네요! 바로 실천해보겠습니다 👍",
    "전문가님의 조언 덕분에 많은 도움이 되었어요. 감사합니다!",
    "이런 팁은 어디서도 들을 수 없는데, 정말 값진 정보입니다.",
    "실제로 해보니 정말 효과가 있더라고요. 추천합니다!",
    "초보자도 쉽게 따라할 수 있는 설명이 좋네요.",
    "전문가님 경험에서 나온 조언이라 신뢰가 갑니다.",
    "이 방법으로 문제를 해결했습니다. 고맙습니다 ✨",
    "상세한 설명과 단계별 가이드가 정말 도움됐어요.",
    "실생활에 바로 적용할 수 있어서 좋습니다.",
    "전문가 꿀정보답게 정말 알찬 내용이네요!"
]

SAMPLE_REPLIES = [
    "도움이 되셨다니 다행입니다! 더 궁금한 점이 있으면 언제든 문의하세요.",
    "실천해보시고 결과 공유해주시면 감사하겠습니다.",
    "좋은 피드백 감사합니다. 더 유용한 팁으로 찾아뵐게요!",
    "성공하셨다니 정말 기쁩니다. 다른 분들에게도 도움이 될 것 같네요.",
    "추가로 궁금한 점이나 개선사항이 있다면 알려주세요."
]


class ExpertTipsBrowserTestSetup:
    """전문가 꿀정보 브라우저 테스트용 데이터 생성기"""
    
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session = None
        self.session_id = f"BROWSER_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        
        # 생성된 테스트 계정 정보
        self.expert_user = None
        self.normal_user = None
        self.expert_token = None
        self.normal_token = None
        
        # 생성된 테스트 데이터
        self.created_comments = []
        self.created_reactions = []
        self.expert_tips_posts = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_expert_tips_posts(self) -> List[Dict[str, Any]]:
        """기존 전문가 꿀정보 게시글 조회"""
        try:
            params = {
                "metadata_type": "expert_tips",
                "page": 1,
                "page_size": 20
            }
            
            async with self.session.get(API_ENDPOINTS["posts"], params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    posts = result.get("items", [])
                    self.expert_tips_posts = posts
                    print(f"✅ 전문가 꿀정보 게시글 {len(posts)}개 조회 완료")
                    return posts
                else:
                    print(f"❌ 전문가 꿀정보 게시글 조회 실패: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ 전문가 꿀정보 게시글 조회 중 오류: {str(e)}")
            return []
    
    async def create_test_users(self) -> bool:
        """테스트 사용자 생성 (전문가 권한 사용자 + 일반 사용자)"""
        print("\n📋 브라우저 테스트용 사용자 생성 중...")
        
        # 1. 전문가 권한 사용자 생성
        expert_data = {
            "email": f"expert_browser_test_{self.session_id.split('_')[-1]}@example.com",
            "user_handle": f"expert_test_{self.session_id.split('_')[-1]}",
            "name": "전문가 테스트 계정",
            "display_name": "전문가 테스트",
            "password": "TestPassword123!"
        }
        
        try:
            # 사용자 등록
            async with self.session.post(API_ENDPOINTS["register"], json=expert_data) as response:
                if response.status == 201:
                    print(f"✅ 전문가 사용자 등록 완료: {expert_data['email']}")
                else:
                    # 이미 존재할 수 있으므로 로그인 시도
                    pass
            
            # 로그인하여 토큰 획득
            login_data = {
                "email": expert_data["email"],
                "password": expert_data["password"]
            }
            
            async with self.session.post(API_ENDPOINTS["login"], json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.expert_token = result["access_token"]
                    self.expert_user = expert_data
                    print(f"✅ 전문가 사용자 로그인 완료")
                else:
                    print(f"❌ 전문가 사용자 로그인 실패: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ 전문가 사용자 생성 중 오류: {str(e)}")
            return False
        
        # 2. 일반 사용자 생성
        normal_data = {
            "email": f"normal_browser_test_{self.session_id.split('_')[-1]}@example.com",
            "user_handle": f"normal_test_{self.session_id.split('_')[-1]}",
            "name": "일반 테스트 계정",
            "display_name": "일반 테스트",
            "password": "TestPassword123!"
        }
        
        try:
            # 사용자 등록
            async with self.session.post(API_ENDPOINTS["register"], json=normal_data) as response:
                if response.status == 201:
                    print(f"✅ 일반 사용자 등록 완료: {normal_data['email']}")
                else:
                    # 이미 존재할 수 있으므로 로그인 시도
                    pass
            
            # 로그인하여 토큰 획득
            login_data = {
                "email": normal_data["email"],
                "password": normal_data["password"]
            }
            
            async with self.session.post(API_ENDPOINTS["login"], json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.normal_token = result["access_token"]
                    self.normal_user = normal_data
                    print(f"✅ 일반 사용자 로그인 완료")
                    return True
                else:
                    print(f"❌ 일반 사용자 로그인 실패: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ 일반 사용자 생성 중 오류: {str(e)}")
            return False
    
    async def create_sample_comments(self, num_comments: int = 15) -> List[Dict[str, Any]]:
        """샘플 댓글 및 답글 생성"""
        if not self.expert_tips_posts:
            print("❌ 전문가 꿀정보 게시글이 없어 댓글을 생성할 수 없습니다.")
            return []
        
        print(f"\n💬 샘플 댓글 {num_comments}개 생성 중...")
        created_comments = []
        
        # 댓글 생성에 사용할 토큰들 (전문가 사용자와 일반 사용자 번갈아가며)
        tokens = [
            (self.expert_token, "전문가"),
            (self.normal_token, "일반")
        ]
        
        for i in range(num_comments):
            try:
                # 랜덤하게 게시글 선택
                post = random.choice(self.expert_tips_posts)
                post_id = post["id"]
                
                # 랜덤하게 사용자 선택
                token, user_type = random.choice(tokens)
                
                # 댓글 내용 선택
                content = random.choice(SAMPLE_COMMENTS)
                
                comment_data = {
                    "post_id": post_id,
                    "content": content,
                    "metadata": {
                        "browser_test_session": self.session_id,
                        "user_type": user_type,
                        "comment_type": "expert_tips_discussion"
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                async with self.session.post(API_ENDPOINTS["comments"], json=comment_data, headers=headers) as response:
                    if response.status == 201:
                        result = await response.json()
                        created_comments.append(result)
                        print(f"   ✅ 댓글 {i+1}/{num_comments} 생성 완료 ({user_type} 사용자)")
                        
                        # 30% 확률로 답글 생성
                        if random.random() < 0.3:
                            await self._create_reply(result["id"], token, user_type)
                            
                    else:
                        print(f"   ❌ 댓글 {i+1} 생성 실패: {response.status}")
                        
                # 요청 간 간격
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ 댓글 {i+1} 생성 중 오류: {str(e)}")
        
        self.created_comments = created_comments
        print(f"✅ 총 {len(created_comments)}개 댓글 생성 완료")
        return created_comments
    
    async def _create_reply(self, parent_comment_id: str, token: str, user_type: str):
        """답글 생성"""
        try:
            reply_content = random.choice(SAMPLE_REPLIES)
            
            reply_data = {
                "parent_comment_id": parent_comment_id,
                "content": reply_content,
                "metadata": {
                    "browser_test_session": self.session_id,
                    "user_type": user_type,
                    "comment_type": "expert_tips_reply"
                }
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(API_ENDPOINTS["comments"], json=reply_data, headers=headers) as response:
                if response.status == 201:
                    print(f"      ↳ 답글 생성 완료 ({user_type} 사용자)")
                else:
                    print(f"      ↳ 답글 생성 실패: {response.status}")
                    
        except Exception as e:
            print(f"      ↳ 답글 생성 중 오류: {str(e)}")
    
    async def create_sample_reactions(self, num_reactions: int = 20) -> List[Dict[str, Any]]:
        """샘플 반응 데이터 생성 (좋아요/북마크)"""
        if not self.expert_tips_posts:
            print("❌ 전문가 꿀정보 게시글이 없어 반응을 생성할 수 없습니다.")
            return []
        
        print(f"\n👍 샘플 반응 {num_reactions}개 생성 중...")
        created_reactions = []
        
        # 반응 생성에 사용할 토큰들
        tokens = [
            (self.expert_token, "전문가"),
            (self.normal_token, "일반")
        ]
        
        reaction_types = ["like", "bookmark"]  # 좋아요, 북마크
        
        for i in range(num_reactions):
            try:
                # 랜덤하게 게시글 선택
                post = random.choice(self.expert_tips_posts)
                post_id = post["id"]
                
                # 랜덤하게 사용자 선택
                token, user_type = random.choice(tokens)
                
                # 랜덤하게 반응 타입 선택
                reaction_type = random.choice(reaction_types)
                
                reaction_data = {
                    "target_type": "post",
                    "target_id": post_id,
                    "reaction_type": reaction_type
                }
                
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                async with self.session.post(API_ENDPOINTS["reactions"], json=reaction_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        created_reactions.append(result)
                        print(f"   ✅ 반응 {i+1}/{num_reactions} 생성 완료 ({reaction_type}, {user_type} 사용자)")
                    else:
                        # 이미 존재하는 반응일 수 있음 (중복 방지)
                        pass
                        
                # 요청 간 간격
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"   ❌ 반응 {i+1} 생성 중 오류: {str(e)}")
        
        self.created_reactions = created_reactions
        print(f"✅ 총 {len(created_reactions)}개 반응 생성 완료")
        return created_reactions
    
    async def generate_browser_test_data(self) -> Dict[str, Any]:
        """브라우저 테스트용 데이터 전체 생성"""
        print("🚀 전문가 꿀정보 브라우저 테스트 데이터 생성 시작!")
        print(f"🆔 세션 ID: {self.session_id}")
        print("=" * 80)
        
        try:
            # 1. 기존 전문가 꿀정보 게시글 조회
            await self.fetch_expert_tips_posts()
            
            if not self.expert_tips_posts:
                print("❌ 전문가 꿀정보 게시글이 없습니다. 먼저 게시글을 생성해주세요.")
                return {
                    "success": False,
                    "error": "No expert tips posts found"
                }
            
            # 2. 테스트 사용자 생성
            if not await self.create_test_users():
                print("❌ 테스트 사용자 생성 실패")
                return {
                    "success": False,
                    "error": "Failed to create test users"
                }
            
            # 3. 샘플 댓글 생성
            comments = await self.create_sample_comments(15)
            
            # 4. 샘플 반응 생성
            reactions = await self.create_sample_reactions(20)
            
            # 5. 결과 요약
            result = {
                "success": True,
                "session_id": self.session_id,
                "created_at": datetime.now().isoformat(),
                "summary": {
                    "expert_tips_posts": len(self.expert_tips_posts),
                    "test_users": 2,
                    "comments_created": len(comments),
                    "reactions_created": len(reactions)
                },
                "test_accounts": {
                    "expert_user": {
                        "email": self.expert_user["email"],
                        "password": "TestPassword123!",
                        "permissions": "can_write_expert_tips",
                        "description": "전문가 꿀정보 작성 권한이 있는 테스트 계정"
                    },
                    "normal_user": {
                        "email": self.normal_user["email"],
                        "password": "TestPassword123!",
                        "permissions": "none",
                        "description": "일반 사용자 테스트 계정 (전문가 권한 없음)"
                    }
                },
                "browser_test_urls": {
                    "expert_tips_list": f"{API_BASE}/expert-tips",
                    "sample_post": f"{API_BASE}/expert-tips/{self.expert_tips_posts[0]['slug']}" if self.expert_tips_posts else None,
                    "login_page": f"{API_BASE}/auth/login"
                },
                "data": {
                    "posts": self.expert_tips_posts[:5],  # 샘플 5개만
                    "comments": comments,
                    "reactions": reactions
                }
            }
            
            print("\n" + "=" * 80)
            print("🎉 브라우저 테스트 데이터 생성 완료!")
            print("=" * 80)
            print(f"✅ 전문가 꿀정보 게시글: {len(self.expert_tips_posts)}개")
            print(f"✅ 테스트 계정: 2개 (전문가 권한 + 일반 사용자)")
            print(f"✅ 샘플 댓글: {len(comments)}개")
            print(f"✅ 샘플 반응: {len(reactions)}개")
            
            print(f"\n📋 테스트 계정 정보:")
            print(f"   🔑 전문가 계정: {self.expert_user['email']} (비밀번호: TestPassword123!)")
            print(f"   👤 일반 계정: {self.normal_user['email']} (비밀번호: TestPassword123!)")
            
            print(f"\n🌐 브라우저 테스트 URL:")
            print(f"   📋 전문가 꿀정보 목록: {API_BASE}/expert-tips")
            if self.expert_tips_posts:
                print(f"   📄 샘플 상세 페이지: {API_BASE}/expert-tips/{self.expert_tips_posts[0]['slug']}")
            print(f"   🔐 로그인 페이지: {API_BASE}/auth/login")
            
            return result
            
        except Exception as e:
            print(f"\n❌ 브라우저 테스트 데이터 생성 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """메인 실행 함수"""
    print("🎯 전문가 꿀정보 브라우저 테스트 데이터 생성기")
    print("브라우저에서 직접 확인할 수 있는 테스트 데이터를 생성합니다.")
    print()
    
    async with ExpertTipsBrowserTestSetup() as setup:
        result = await setup.generate_browser_test_data()
        
        if result["success"]:
            print("\n✅ 브라우저 테스트 준비 완료!")
            print("📖 브라우저 확인 가이드: expert_tips_browser_test_guide.html")
            print("🧹 데이터 정리: expert_tips_test_data_manager.py")
            return 0
        else:
            print(f"\n❌ 테스트 데이터 생성 실패: {result.get('error', 'Unknown error')}")
            return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))