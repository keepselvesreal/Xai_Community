#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 11:37:00 KST
주요 컴포넌트들:
- PropertyInfoBrowserTestSetup: 브라우저 확인용 테스트 데이터 생성기 (lines 25-380)

주요 함수들:
- create_test_user(): 테스트 사용자 계정 생성 (lines 78-108)
- ensure_property_info_exists(): 부동산 정보 게시글 존재 확인 (lines 110-145)
- create_sample_comments(): 샘플 댓글/답글 생성 (lines 147-220)
- create_sample_reactions(): 샘플 반응 데이터 생성 (lines 222-270)
- generate_comprehensive_report(): 생성 결과 보고서 생성 (lines 330-378)

관련 파일:
- ../api/property_info_api_automation_test.py: API 자동화 테스트 스크립트
- property_info_browser_test_guide.html: 브라우저 확인 가이드 (생성 예정)
- property_info_test_data_manager.py: 데이터 관리 스크립트 (생성 예정)
"""

import asyncio
import aiohttp
import json
import uuid
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class PropertyInfoBrowserTestSetup:
    """부동산 정보 페이지 브라우저 확인용 테스트 데이터 생성기"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"BROWSER_PROPINFO_{timestamp}_{random_suffix}"
        
        self.base_url = base_url
        self.frontend_url = "http://localhost:5173"
        
        # 브라우저 테스트용 사용자 정보
        self.test_users = [
            {
                "email": f"propbrowser_{random_suffix.lower()}@example.com",
                "user_handle": f"propbrowser_{random_suffix.lower()}",
                "name": f"Property Browser Test User {random_suffix}",
                "display_name": f"PropBrowser {random_suffix}",
                "password": "BrowserTest123"  # 대문자 포함 비밀번호 정책 준수
            },
            {
                "email": f"propuser2_{random_suffix.lower()}@example.com",
                "user_handle": f"propuser2_{random_suffix.lower()}",
                "name": f"Property User 2 {random_suffix}",
                "display_name": f"PropUser2 {random_suffix}",
                "password": "BrowserTest123"  # 대문자 포함 비밀번호 정책 준수
            }
        ]
        
        self.created_data = {
            "users": [],
            "comments": [],
            "reactions": [],
            "property_posts": []
        }
        
        self.auth_tokens = {}
    
    async def setup_browser_test_environment(self):
        """브라우저 테스트 환경 전체 설정"""
        print("🌐 부동산 정보 페이지 브라우저 테스트 환경 설정 시작!")
        print(f"🆔 세션 ID: {self.session_id}")
        print("=" * 70)
        
        session = aiohttp.ClientSession()
        
        try:
            # 1. 테스트 사용자 생성
            print("\n📝 1단계: 테스트 사용자 계정 생성")
            await self._create_test_users(session)
            
            # 2. 부동산 정보 게시글 확인
            print("\n🏠 2단계: 부동산 정보 게시글 확인")
            await self._ensure_property_info_exists(session)
            
            # 3. 샘플 댓글/답글 생성
            print("\n💬 3단계: 샘플 댓글/답글 생성")
            await self._create_sample_comments(session)
            
            # 4. 샘플 반응 데이터 생성
            print("\n❤️ 4단계: 샘플 반응 데이터 생성")
            await self._create_sample_reactions(session)
            
            # 5. 브라우저 확인 가이드 생성
            print("\n📋 5단계: 브라우저 확인 가이드 생성")
            await self._generate_browser_guide()
            
            # 6. 종합 보고서 생성
            print("\n📊 6단계: 설정 완료 보고서 생성")
            await self._generate_comprehensive_report()
            
        except Exception as e:
            print(f"\n❌ 설정 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await session.close()
        
        print("\n🎉 브라우저 테스트 환경 설정 완료!")
        return True
    
    async def _create_test_users(self, session: aiohttp.ClientSession):
        """테스트 사용자 계정 생성"""
        
        for i, user_info in enumerate(self.test_users, 1):
            print(f"   👤 사용자 {i} 생성: {user_info['display_name']}")
            
            # 사용자 등록
            try:
                async with session.post(f"{self.base_url}/api/auth/register", json=user_info) as response:
                    if response.status == 201:
                        print(f"      ✅ 계정 생성 성공")
                    elif response.status == 409:
                        print(f"      ✅ 계정 이미 존재 (재사용)")
                    else:
                        print(f"      ⚠️ 계정 생성 상태: {response.status}")
            except Exception as e:
                print(f"      ❌ 계정 생성 오류: {e}")
                continue
            
            # 로그인하여 토큰 획득 - OAuth2PasswordRequestForm 사용
            form_data = aiohttp.FormData()
            form_data.add_field('username', user_info["email"])
            form_data.add_field('password', user_info["password"])
            
            try:
                async with session.post(f"{self.base_url}/api/auth/login", data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        token = data.get("access_token")
                        self.auth_tokens[user_info["email"]] = token
                        self.created_data["users"].append(user_info)
                        print(f"      ✅ 로그인 성공, 토큰 획득")
                    else:
                        print(f"      ❌ 로그인 실패: {response.status}")
            except Exception as e:
                print(f"      ❌ 로그인 오류: {e}")
    
    async def _ensure_property_info_exists(self, session: aiohttp.ClientSession):
        """부동산 정보 게시글 존재 확인 및 목록 수집"""
        
        try:
            params = {
                "metadata_type": "property_information",
                "page": 1,
                "page_size": 50
            }
            async with session.get(f"{self.base_url}/api/posts/", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get("items", [])
                    self.created_data["property_posts"] = posts
                    
                    print(f"   📊 부동산 정보 게시글 {len(posts)}개 발견")
                    
                    # 카테고리별 분석
                    categories = {}
                    for post in posts:
                        metadata = post.get("metadata", {})
                        category = metadata.get("category", "Unknown")
                        categories[category] = categories.get(category, 0) + 1
                    
                    print(f"   📂 카테고리별 분포: {dict(categories)}")
                    
                    if len(posts) < 5:
                        print(f"   ⚠️ 부동산 정보가 부족합니다. 추가 생성을 권장합니다.")
                        print(f"      권장: scripts/development/data-gen/create_property_info_posts.py 실행")
                else:
                    print(f"   ❌ 부동산 정보 조회 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 부동산 정보 확인 오류: {e}")
    
    async def _create_sample_comments(self, session: aiohttp.ClientSession):
        """샘플 댓글/답글 생성"""
        
        if not self.created_data["property_posts"] or not self.auth_tokens:
            print("   ⚠️ 부동산 정보 게시글 또는 사용자 토큰이 없어 댓글 생성을 건너뜁니다.")
            return
        
        # 최대 3개 게시글에 댓글 생성
        target_posts = self.created_data["property_posts"][:3]
        user_emails = list(self.auth_tokens.keys())
        
        comment_templates = [
            "이 부동산 정보가 정말 도움이 되네요! 감사합니다.",
            "최근 시세 정보에 대한 상세한 분석이 인상적입니다.",
            "투자 관점에서 고려해볼 만한 좋은 금융 정보입니다.",
            "부동산 지식이 풍부해서 많이 배웠습니다.",
            "입주 정보가 매우 실용적이네요. 참고하겠습니다.",
            "이런 정보를 어디서 더 얻을 수 있을까요?",
            "전문가 의견이 궁금합니다.",
            "지역별 차이점도 알고 싶습니다."
        ]
        
        reply_templates = [
            "좋은 지적이네요. 저도 같은 생각입니다.",
            "추가 정보를 공유해드리겠습니다.",
            "관련 경험이 있어서 의견 드립니다.",
            "이 부분에 대해서는 전문가 상담을 받아보시는 것을 추천합니다.",
            "최근 변경된 내용도 있으니 확인해보세요.",
            "좋은 질문입니다. 저도 궁금하네요."
        ]
        
        total_comments = 0
        
        for post in target_posts:
            post_id = post.get("id") or post.get("_id")
            post_title = post.get("title", "")[:30]
            
            print(f"   💬 게시글 '{post_title}...' 에 댓글 생성")
            
            # 각 게시글에 2-4개 댓글 생성
            num_comments = random.randint(2, 4)
            created_parent_comments = []
            
            for i in range(num_comments):
                user_email = random.choice(user_emails)
                token = self.auth_tokens[user_email]
                headers = {"Authorization": f"Bearer {token}"}
                
                comment_content = f"{random.choice(comment_templates)} (브라우저 테스트용 댓글 #{i+1}, 세션: {self.session_id})"
                
                comment_data = {
                    "content": comment_content,
                    "post_id": str(post_id)
                }
                
                try:
                    await asyncio.sleep(0.5)  # API 호출 간격
                    async with session.post(
                        f"{self.base_url}/api/comments/", 
                        json=comment_data, 
                        headers=headers
                    ) as response:
                        if response.status == 201:
                            comment = await response.json()
                            self.created_data["comments"].append(comment)
                            created_parent_comments.append(comment)
                            total_comments += 1
                            print(f"      ✅ 댓글 생성 성공 ({total_comments})")
                        else:
                            print(f"      ❌ 댓글 생성 실패: {response.status}")
                except Exception as e:
                    print(f"      ❌ 댓글 생성 오류: {e}")
            
            # 일부 댓글에 답글 생성
            if created_parent_comments:
                num_replies = min(2, len(created_parent_comments))
                for j in range(num_replies):
                    parent_comment = random.choice(created_parent_comments)
                    user_email = random.choice(user_emails)
                    token = self.auth_tokens[user_email]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    reply_content = f"{random.choice(reply_templates)} (브라우저 테스트용 답글, 세션: {self.session_id})"
                    
                    reply_data = {
                        "content": reply_content,
                        "post_id": str(post_id),
                        "parent_id": parent_comment.get("id") or parent_comment.get("_id")
                    }
                    
                    try:
                        await asyncio.sleep(0.5)
                        async with session.post(
                            f"{self.base_url}/api/comments/", 
                            json=reply_data, 
                            headers=headers
                        ) as response:
                            if response.status == 201:
                                reply = await response.json()
                                self.created_data["comments"].append(reply)
                                total_comments += 1
                                print(f"      ✅ 답글 생성 성공 ({total_comments})")
                            else:
                                print(f"      ❌ 답글 생성 실패: {response.status}")
                    except Exception as e:
                        print(f"      ❌ 답글 생성 오류: {e}")
        
        print(f"   📊 총 {total_comments}개 댓글/답글 생성 완료")
    
    async def _create_sample_reactions(self, session: aiohttp.ClientSession):
        """샘플 반응 데이터 생성"""
        
        if not self.created_data["property_posts"] or not self.auth_tokens:
            print("   ⚠️ 부동산 정보 게시글 또는 사용자 토큰이 없어 반응 생성을 건너뜁니다.")
            return
        
        user_emails = list(self.auth_tokens.keys())
        target_posts = self.created_data["property_posts"][:5]  # 최대 5개 게시글
        
        reaction_types = ["like", "bookmark"]  # 좋아요, 북마크
        total_reactions = 0
        
        for post in target_posts:
            post_id = post.get("id") or post.get("_id")
            post_title = post.get("title", "")[:30]
            
            print(f"   ❤️ 게시글 '{post_title}...' 에 반응 생성")
            
            # 각 사용자가 무작위로 반응
            for user_email in user_emails:
                token = self.auth_tokens[user_email]
                headers = {"Authorization": f"Bearer {token}"}
                
                # 70% 확률로 좋아요, 40% 확률로 북마크
                for reaction_type in reaction_types:
                    if random.random() < (0.7 if reaction_type == "like" else 0.4):
                        try:
                            await asyncio.sleep(0.3)
                            async with session.post(
                                f"{self.base_url}/api/posts/{post_id}/{reaction_type}", 
                                headers=headers
                            ) as response:
                                if response.status == 200:
                                    total_reactions += 1
                                    self.created_data["reactions"].append({
                                        "post_id": str(post_id),
                                        "user_email": user_email,
                                        "type": reaction_type,
                                        "session_id": self.session_id
                                    })
                                    print(f"      ✅ {reaction_type} 반응 성공 ({total_reactions})")
                        except Exception as e:
                            print(f"      ❌ {reaction_type} 반응 오류: {e}")
        
        # 댓글에도 반응 생성
        target_comments = self.created_data["comments"][:10]  # 최대 10개 댓글
        
        for comment in target_comments:
            comment_id = comment.get("id") or comment.get("_id")
            
            # 50% 확률로 댓글에 좋아요
            for user_email in user_emails:
                if random.random() < 0.5:
                    token = self.auth_tokens[user_email]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    try:
                        await asyncio.sleep(0.3)
                        async with session.post(
                            f"{self.base_url}/api/comments/{comment_id}/like", 
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                total_reactions += 1
                                self.created_data["reactions"].append({
                                    "comment_id": str(comment_id),
                                    "user_email": user_email,
                                    "type": "comment_like",
                                    "session_id": self.session_id
                                })
                    except Exception:
                        pass  # 댓글 반응 실패는 무시
        
        print(f"   📊 총 {total_reactions}개 반응 생성 완료")
    
    async def _generate_browser_guide(self):
        """브라우저 확인 가이드 생성"""
        print("   📋 브라우저 확인 가이드 HTML 생성 중...")
        
        # 가이드 HTML 파일 경로
        guide_path = Path(__file__).parent / "property_info_browser_test_guide.html"
        
        # 가이드 템플릿 생성 (간단한 버전)
        guide_content = self._generate_guide_template()
        
        try:
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(guide_content)
            print(f"   ✅ 가이드 파일 생성: {guide_path}")
        except Exception as e:
            print(f"   ❌ 가이드 파일 생성 실패: {e}")
    
    def _generate_guide_template(self) -> str:
        """브라우저 확인 가이드 HTML 템플릿 생성"""
        
        # 생성된 사용자 정보
        user_info_html = ""
        for user in self.created_data["users"]:
            user_info_html += f"""
                <div class="user-info">
                    <strong>{user['display_name']}</strong><br>
                    이메일: {user['email']}<br>
                    비밀번호: {user['password']}
                </div>
            """
        
        # 부동산 정보 게시글 링크
        post_links_html = ""
        for i, post in enumerate(self.created_data["property_posts"][:5], 1):
            post_id = post.get("id") or post.get("_id")
            post_title = post.get("title", "")
            slug = post.get("slug", post_id)
            post_links_html += f"""
                <a href="{self.frontend_url}/property-information/{slug}" target="_blank" class="post-link">
                    {i}. {post_title[:50]}...
                </a>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>부동산 정보 페이지 브라우저 테스트 가이드</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .user-info {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #27ae60; }}
                .post-link {{ display: block; padding: 10px; margin: 5px 0; background: #e8f8f5; text-decoration: none; color: #27ae60; border-radius: 5px; }}
                .post-link:hover {{ background: #d1f2eb; }}
                .checklist {{ list-style: none; padding: 0; }}
                .checklist li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .checklist input[type="checkbox"] {{ margin-right: 10px; }}
                .stats {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .btn {{ background: #27ae60; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
                .btn:hover {{ background: #2ecc71; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏠 부동산 정보 페이지 브라우저 테스트 가이드</h1>
                <p>세션 ID: {self.session_id}</p>
                <p>생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📊 생성된 테스트 데이터 현황</h2>
                <div class="stats">
                    <strong>테스트 사용자:</strong> {len(self.created_data['users'])}명<br>
                    <strong>부동산 정보 게시글:</strong> {len(self.created_data['property_posts'])}개<br>
                    <strong>댓글/답글:</strong> {len(self.created_data['comments'])}개<br>
                    <strong>반응 데이터:</strong> {len(self.created_data['reactions'])}개
                </div>
            </div>
            
            <div class="section">
                <h2>👤 테스트 사용자 계정</h2>
                <p>브라우저에서 로그인하여 테스트할 수 있는 계정들입니다:</p>
                {user_info_html}
            </div>
            
            <div class="section">
                <h2>🏠 부동산 정보 페이지 링크</h2>
                <p>아래 링크들을 클릭하여 브라우저에서 직접 확인하세요:</p>
                <div style="margin: 15px 0;">
                    <a href="{self.frontend_url}/info" target="_blank" class="post-link">
                        📋 부동산 정보 목록 페이지
                    </a>
                </div>
                {post_links_html}
            </div>
            
            <div class="section">
                <h2>✅ 브라우저 확인 체크리스트</h2>
                <ul class="checklist">
                    <li><input type="checkbox"> 정보 목록 페이지 정상 로딩</li>
                    <li><input type="checkbox"> 카테고리별 필터링 작동</li>
                    <li><input type="checkbox"> 검색 기능 작동</li>
                    <li><input type="checkbox"> 페이지네이션 작동</li>
                    <li><input type="checkbox"> 상세 페이지 정상 표시</li>
                    <li><input type="checkbox"> 조회수 증가 확인</li>
                    <li><input type="checkbox"> 로그인 후 댓글 작성 가능</li>
                    <li><input type="checkbox"> 답글 작성 가능</li>
                    <li><input type="checkbox"> 좋아요/북마크 기능 작동</li>
                    <li><input type="checkbox"> 댓글 좋아요 기능 작동</li>
                    <li><input type="checkbox"> 실시간 카운트 업데이트</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>🧹 테스트 완료 후 정리</h2>
                <p>테스트 완료 후 생성된 데이터를 정리하려면:</p>
                <div style="margin: 15px 0;">
                    <button class="btn" onclick="alert('property_info_test_data_manager.py --cleanup --session-id {self.session_id} 명령을 터미널에서 실행하세요.')">
                        데이터 정리 명령 확인
                    </button>
                </div>
                <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">
cd scripts/development/testing/browser
python property_info_test_data_manager.py --cleanup --session-id {self.session_id}
                </pre>
            </div>
        </body>
        </html>
        """
    
    async def _generate_comprehensive_report(self):
        """종합 보고서 생성"""
        
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "test_users": len(self.created_data["users"]),
                "property_posts": len(self.created_data["property_posts"]),
                "comments": len(self.created_data["comments"]),
                "reactions": len(self.created_data["reactions"])
            },
            "created_data": self.created_data,
            "frontend_url": self.frontend_url,
            "base_url": self.base_url
        }
        
        # JSON 보고서 저장
        report_path = Path(__file__).parent / f"browser_test_setup_report_{self.session_id}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"   📄 JSON 보고서 저장: {report_path}")
        except Exception as e:
            print(f"   ❌ 보고서 저장 실패: {e}")
        
        # 콘솔 요약 출력
        print("\n" + "=" * 70)
        print("🎉 브라우저 테스트 환경 설정 완료!")
        print("=" * 70)
        print(f"📊 생성된 데이터:")
        print(f"   👤 테스트 사용자: {len(self.created_data['users'])}명")
        print(f"   🏠 부동산 정보: {len(self.created_data['property_posts'])}개 (기존 활용)")
        print(f"   💬 댓글/답글: {len(self.created_data['comments'])}개")
        print(f"   ❤️ 반응 데이터: {len(self.created_data['reactions'])}개")
        print(f"\n🌐 브라우저 확인 가이드:")
        guide_path = Path(__file__).parent / "property_info_browser_test_guide.html"
        print(f"   📋 {guide_path}")
        print(f"   🔗 브라우저에서 열기: file://{guide_path.absolute()}")
        print(f"\n📋 주요 테스트 페이지:")
        print(f"   🏠 정보 목록: {self.frontend_url}/info")
        if self.created_data["property_posts"]:
            first_post = self.created_data["property_posts"][0]
            slug = first_post.get("slug", first_post.get("id"))
            print(f"   📄 상세 페이지: {self.frontend_url}/property-information/{slug}")


async def main():
    """메인 실행 함수"""
    print("🌐 부동산 정보 페이지 브라우저 테스트 환경 설정")
    print("사용자가 직접 브라우저에서 확인할 수 있는 테스트 데이터를 생성합니다.")
    print("=" * 80)
    
    setup = PropertyInfoBrowserTestSetup()
    success = await setup.setup_browser_test_environment()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))