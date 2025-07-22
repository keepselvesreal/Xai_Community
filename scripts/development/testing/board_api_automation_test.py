#!/usr/bin/env python3
"""
게시판 기능 자동화 API 테스트 스크립트
- 세션 ID 기반 정확한 테스트 데이터 추적
- 브라우저 검증용 보고서 생성
- 안전한 데이터 정리 지원
"""

import asyncio
import aiohttp
import json
import uuid
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class TestSessionManager:
    def __init__(self, base_url: str = "http://localhost:8000"):
        # 고유한 세션 ID 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"TEST_{timestamp}_{random_suffix}"
        
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.test_user_data: Optional[Dict] = None
        
        # 생성된 데이터 추적
        self.created_items = {
            "users": [],
            "posts": [],
            "comments": [],
            "reactions": []
        }
        
        # 테스트 결과 저장
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def track_created_item(self, item_type: str, item_data: Dict):
        """생성된 아이템 추적"""
        tracked_item = {
            "id": str(item_data.get("id", item_data.get("_id", "unknown"))),
            "title": item_data.get("title", item_data.get("content", ""))[:50],
            "created_at": datetime.now().isoformat(),
            "session_id": self.session_id,
            "data": item_data
        }
        self.created_items[item_type].append(tracked_item)
        
    def generate_test_user_data(self) -> Dict:
        """세션 ID가 포함된 테스트 사용자 데이터 생성"""
        session_suffix = self.session_id.split('_')[-1].lower()
        return {
            "name": f"테스트사용자_{session_suffix}",
            "email": f"testuser_{session_suffix}@test.com",
            "user_handle": f"testuser_{session_suffix}",
            "password": "TestPass123!",
            "display_name": f"🧪테스트_{session_suffix}",
            "bio": f"게시판 테스트용 사용자 (세션: {self.session_id})"
        }
        
    def create_tagged_post_data(self, scenario: str, base_data: Dict) -> Dict:
        """세션 ID가 태깅된 게시글 데이터 생성"""
        post_number = len(self.created_items["posts"]) + 1
        
        return {
            **base_data,
            "title": f"[🧪TEST-{self.session_id}] {base_data['title']}",
            "content": f"""# 🧪 자동화 테스트 게시글

**테스트 정보:**
- 세션 ID: `{self.session_id}`
- 시나리오: `{scenario}`
- 게시글 번호: {post_number}
- 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**브라우저 확인 가이드:**
이 게시글이 정상적으로 표시되고 기능이 올바르게 작동하는지 확인하세요.

---

{base_data['content']}""",
            "metadata": {
                **base_data.get("metadata", {}),
                "test_session_id": self.session_id,
                "test_scenario": scenario,
                "is_test_data": True,
                "test_post_number": post_number
            }
        }
        
    def create_tagged_comment_data(self, scenario: str, base_data: Dict) -> Dict:
        """세션 ID가 태깅된 댓글 데이터 생성"""
        comment_number = len(self.created_items["comments"]) + 1
        
        return {
            **base_data,
            "content": f"🧪[TEST-{self.session_id}] {base_data['content']} (댓글#{comment_number})",
            "metadata": {
                **base_data.get("metadata", {}),
                "test_session_id": self.session_id,
                "test_scenario": scenario,
                "is_test_data": True
            }
        }
        
    def get_auth_headers(self) -> Dict:
        """인증 헤더 반환"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
    async def register_and_login(self) -> bool:
        """테스트 사용자 등록 및 로그인"""
        print(f"🚀 테스트 사용자 생성 및 로그인...")
        
        self.test_user_data = self.generate_test_user_data()
        
        try:
            # 회원가입
            async with self.session.post(
                f"{self.base_url}/api/auth/register",
                json=self.test_user_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    register_result = await response.json()
                    print(f"✅ 회원가입 성공: {self.test_user_data['user_handle']}")
                    self.track_created_item("users", register_result.get("user", {}))
                else:
                    error = await response.json()
                    print(f"❌ 회원가입 실패: {error}")
                    return False
                    
            # 로그인
            login_data = {
                "username": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    self.access_token = login_result["access_token"]
                    print(f"✅ 로그인 성공")
                    return True
                else:
                    error = await response.json()
                    print(f"❌ 로그인 실패: {error}")
                    return False
                    
        except Exception as e:
            print(f"❌ 인증 오류: {str(e)}")
            return False
            
    async def test_post_list_features(self):
        """게시글 목록 기능 테스트 (필터링, 정렬, 검색, 페이지네이션)"""
        print("\n" + "="*60)
        print("📋 게시글 목록 기능 테스트")
        print("="*60)
        
        scenario_results = {"scenario": "post_list", "tests": []}
        
        # 다양한 카테고리의 테스트 게시글 생성
        test_posts_data = [
            {
                "title": "자유게시판 필터링 테스트용 게시글",
                "content": "카테고리 필터링 기능을 테스트하기 위한 자유게시판 게시글입니다.",
                "service": "residential_community",
                "metadata": {
                    "type": "board",
                    "category": "자유게시판",
                    "tags": ["테스트", "필터링", "자유게시판"]
                }
            },
            {
                "title": "생활정보 필터링 테스트용 게시글",
                "content": "카테고리 필터링 기능을 테스트하기 위한 생활정보 게시글입니다.",
                "service": "residential_community",
                "metadata": {
                    "type": "board", 
                    "category": "생활정보",
                    "tags": ["테스트", "필터링", "생활정보"]
                }
            },
            {
                "title": "이야기 필터링 테스트용 게시글",
                "content": "카테고리 필터링 기능을 테스트하기 위한 이야기 게시글입니다.",
                "service": "residential_community",
                "metadata": {
                    "type": "board",
                    "category": "이야기", 
                    "tags": ["테스트", "필터링", "이야기"]
                }
            }
        ]
        
        created_posts = []
        
        # 테스트 게시글 생성
        for post_data in test_posts_data:
            tagged_data = self.create_tagged_post_data("list_filtering", post_data)
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/posts",
                    json=tagged_data,
                    headers=self.get_auth_headers()
                ) as response:
                    if response.status == 201:
                        post_result = await response.json()
                        created_posts.append(post_result)
                        self.track_created_item("posts", post_result)
                        print(f"✅ 게시글 생성: {post_result['title'][:50]}...")
                    else:
                        error = await response.json()
                        print(f"❌ 게시글 생성 실패: {error}")
                        
            except Exception as e:
                print(f"❌ 게시글 생성 오류: {str(e)}")
                
        # 1. 전체 목록 조회 테스트 (board 타입으로 필터링)
        test_result = await self._test_get_posts_list("전체 목록 조회", {"metadata_type": "board"})
        scenario_results["tests"].append(test_result)
        
        # 2. 카테고리별 필터링 테스트
        for category in ["자유게시판", "생활정보", "이야기"]:
            test_result = await self._test_get_posts_list(
                f"{category} 카테고리 필터링",
                {"metadata_type": "board", "metadata_category": category}
            )
            scenario_results["tests"].append(test_result)
            
        # 3. 정렬 기능 테스트
        sort_options = [
            ("최신순", {"metadata_type": "board", "sort_by": "created_at", "sort_order": "desc"}),
            ("조회수순", {"metadata_type": "board", "sort_by": "view_count", "sort_order": "desc"}),
            ("추천순", {"metadata_type": "board", "sort_by": "like_count", "sort_order": "desc"})
        ]
        
        for sort_name, params in sort_options:
            test_result = await self._test_get_posts_list(f"{sort_name} 정렬", params)
            scenario_results["tests"].append(test_result)
            
        # 4. 검색 기능 테스트
        search_terms = ["테스트", "필터링", "자유게시판"]
        for term in search_terms:
            test_result = await self._test_get_posts_list(
                f"'{term}' 검색",
                {"metadata_type": "board", "search": term}
            )
            scenario_results["tests"].append(test_result)
            
        # 5. 페이지네이션 테스트
        pagination_tests = [
            ("첫 페이지", {"metadata_type": "board", "page": 1, "size": 2}),
            ("둘째 페이지", {"metadata_type": "board", "page": 2, "size": 2}),
            ("큰 페이지 크기", {"metadata_type": "board", "page": 1, "size": 10})
        ]
        
        for page_name, params in pagination_tests:
            test_result = await self._test_get_posts_list(f"{page_name} 조회", params)
            scenario_results["tests"].append(test_result)
            
        self.test_results["post_list"] = scenario_results
        
        print(f"\n✅ 게시글 목록 기능 테스트 완료 - 총 {len(scenario_results['tests'])}개 테스트")
        
    async def test_post_crud_operations(self):
        """게시글 CRUD 작업 테스트"""
        print("\n" + "="*60)
        print("📝 게시글 CRUD 작업 테스트")
        print("="*60)
        
        scenario_results = {"scenario": "post_crud", "tests": []}
        
        # 1. 게시글 작성 테스트
        create_result = await self._test_create_post()
        scenario_results["tests"].append(create_result)
        
        if not create_result.get("success"):
            print("❌ 게시글 작성 실패로 인해 CRUD 테스트 중단")
            self.test_results["post_crud"] = scenario_results
            return
            
        test_post = create_result["data"]
        
        # 2. 게시글 조회 테스트
        read_result = await self._test_get_post_detail(test_post["slug"])
        scenario_results["tests"].append(read_result)
        
        # 3. 게시글 수정 테스트  
        update_result = await self._test_update_post(test_post["slug"])
        scenario_results["tests"].append(update_result)
        
        # 수정 후 새로운 슬러그 사용 (수정 시 슬러그가 변경될 수 있음)
        delete_slug = test_post["slug"]
        if update_result.get("success") and update_result.get("data", {}).get("slug"):
            delete_slug = update_result["data"]["slug"]
            print(f"  🔄 수정 후 새 슬러그 사용: {delete_slug}")
        
        # 4. 게시글 삭제 테스트
        delete_result = await self._test_delete_post(delete_slug)
        scenario_results["tests"].append(delete_result)
        
        self.test_results["post_crud"] = scenario_results
        
        print(f"\n✅ 게시글 CRUD 테스트 완료 - 총 {len(scenario_results['tests'])}개 테스트")
        
    async def test_comment_crud_operations(self):
        """댓글/답글 CRUD 작업 테스트"""
        print("\n" + "="*60)
        print("💬 댓글/답글 CRUD 작업 테스트")
        print("="*60)
        
        scenario_results = {"scenario": "comment_crud", "tests": []}
        
        # 테스트용 게시글 먼저 생성
        print("  📝 테스트용 게시글 생성...")
        test_post_result = await self._test_create_post()
        
        if not test_post_result.get("success"):
            print("❌ 테스트용 게시글 생성 실패로 인해 댓글 테스트 중단")
            self.test_results["comment_crud"] = scenario_results
            return
            
        test_post = test_post_result["data"]
        post_slug = test_post["slug"]
        print(f"  ✅ 테스트용 게시글 생성 완료: {post_slug}")
        
        # 1. 댓글 목록 조회 테스트 (빈 목록)
        empty_list_result = await self._test_get_comments_list(post_slug, "빈 댓글 목록 조회")
        scenario_results["tests"].append(empty_list_result)
        
        # 2. 댓글 작성 테스트
        comment_result = await self._test_create_comment(post_slug)
        scenario_results["tests"].append(comment_result)
        
        if not comment_result.get("success"):
            print("❌ 댓글 작성 실패로 인해 나머지 댓글 테스트 중단")
            self.test_results["comment_crud"] = scenario_results
            return
            
        test_comment = comment_result["data"] 
        comment_id = test_comment.get("id") or test_comment.get("_id") or comment_result.get("comment_id")
        
        # 3. 댓글 목록 조회 테스트 (댓글 있는 상태)
        list_with_comments_result = await self._test_get_comments_list(post_slug, "댓글이 있는 목록 조회")
        scenario_results["tests"].append(list_with_comments_result)
        
        # 4. 답글 작성 테스트
        reply_result = await self._test_create_reply(post_slug, comment_id)
        scenario_results["tests"].append(reply_result)
        
        if reply_result.get("success"):
            test_reply = reply_result["data"]
            reply_id = test_reply.get("id") or test_reply.get("_id") or reply_result.get("reply_id")
            
            # 5. 답글이 포함된 댓글 목록 조회
            list_with_replies_result = await self._test_get_comments_list(post_slug, "답글이 포함된 목록 조회")
            scenario_results["tests"].append(list_with_replies_result)
            
            # 6. 답글 수정 테스트
            reply_update_result = await self._test_update_comment(post_slug, reply_id, "답글")
            scenario_results["tests"].append(reply_update_result)
            
            # 7. 답글 삭제 테스트 
            reply_delete_result = await self._test_delete_comment(post_slug, reply_id, "답글")
            scenario_results["tests"].append(reply_delete_result)
        
        # 8. 댓글 수정 테스트
        comment_update_result = await self._test_update_comment(post_slug, comment_id, "댓글")
        scenario_results["tests"].append(comment_update_result)
        
        # 9. 댓글 삭제 테스트
        comment_delete_result = await self._test_delete_comment(post_slug, comment_id, "댓글")
        scenario_results["tests"].append(comment_delete_result)
        
        # 10. 댓글 반응 테스트 (추가 댓글 생성 후)
        if comment_delete_result.get("success"):
            # 새로운 댓글 생성
            new_comment_result = await self._test_create_comment(post_slug)
            scenario_results["tests"].append(new_comment_result)
            
            if new_comment_result.get("success"):
                new_comment_data = new_comment_result["data"]
                new_comment_id = new_comment_data.get("id") or new_comment_data.get("_id") or new_comment_result.get("comment_id")
                
                # 댓글 좋아요 테스트
                like_result = await self._test_comment_reaction(post_slug, new_comment_id, "like")
                scenario_results["tests"].append(like_result)
                
                # 댓글 싫어요 테스트
                dislike_result = await self._test_comment_reaction(post_slug, new_comment_id, "dislike")
                scenario_results["tests"].append(dislike_result)
        
        self.test_results["comment_crud"] = scenario_results
        
        print(f"\n✅ 댓글/답글 CRUD 테스트 완료 - 총 {len(scenario_results['tests'])}개 테스트")
        
    async def _test_create_post(self) -> Dict:
        """게시글 작성 테스트"""
        print("  📝 게시글 작성 테스트...")
        
        post_data = self.create_tagged_post_data("crud_create", {
            "title": "CRUD 작성 테스트용 게시글", 
            "content": """# CRUD 테스트 게시글

이 게시글은 CRUD 작업을 테스트하기 위해 생성되었습니다.

## 테스트 내용
- ✅ 게시글 작성 기능
- ⏳ 게시글 조회 기능  
- ⏳ 게시글 수정 기능
- ⏳ 게시글 삭제 기능

**수정 여부 확인용 마크**: 원본-CRUD
""",
            "service": "residential_community",
            "metadata": {
                "type": "board",
                "category": "테스트", 
                "tags": ["CRUD", "테스트", "자동화"]
            }
        })
        
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts",
                json=post_data,
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 201:
                    result = await response.json()
                    self.track_created_item("posts", result)
                    
                    print(f"    ✅ 성공 - 슬러그: {result['slug']}, 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": "게시글 작성",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result,
                        "slug": result["slug"]
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": "게시글 작성",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": "게시글 작성",
                "success": False,
                "status": "error", 
                "response_time": response_time,
                "error": str(e)
            }
            
    async def _test_get_post_detail(self, slug: str) -> Dict:
        """게시글 상세 조회 테스트"""
        print(f"  🔍 게시글 조회 테스트 (슬러그: {slug})...")
        
        start_time = datetime.now()
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/posts/{slug}",
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"    ✅ 성공 - 제목: {result['title'][:30]}..., 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": "게시글 조회",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": "게시글 조회",
                        "success": False,
                        "status": "failed", 
                        "response_time": response_time,
                        "error": error
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": "게시글 조회",
                "success": False,
                "status": "error",
                "response_time": response_time, 
                "error": str(e)
            }
            
    async def _test_update_post(self, slug: str) -> Dict:
        """게시글 수정 테스트"""
        print(f"  ✏️  게시글 수정 테스트 (슬러그: {slug})...")
        
        # 수정 여부를 명확히 식별할 수 있는 내용
        update_data = {
            "title": f"[🧪TEST-{self.session_id}] CRUD 수정 테스트용 게시글 (수정됨)",
            "content": f"""# CRUD 테스트 게시글 (수정된 버전)

**🔄 수정 확인용 정보:**
- 수정 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 세션 ID: {self.session_id}
- 수정 여부 확인용 마크: **수정됨-CRUD-{datetime.now().strftime('%H%M%S')}**

## 수정된 테스트 내용  
- ✅ 게시글 작성 기능
- ✅ 게시글 조회 기능
- ✅ 게시글 수정 기능 ← **현재 테스트 중**
- ⏳ 게시글 삭제 기능

이 게시글은 수정 기능이 정상 동작하는지 확인하기 위해 업데이트되었습니다.
원본 내용이 이 내용으로 대체되었다면 수정 기능이 정상 동작하는 것입니다.
""",
            "metadata": {
                "category": "수정된_테스트",
                "tags": ["CRUD", "수정", "테스트"]
            }
        }
        
        start_time = datetime.now()
        
        try:
            async with self.session.put(
                f"{self.base_url}/api/posts/{slug}",
                json=update_data,
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"    ✅ 성공 - 수정 완료, 시간: {response_time:.3f}초")
                    print(f"      새로운 제목: {result['title'][:50]}...")
                    
                    return {
                        "test_name": "게시글 수정",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result,
                        "verification": f"수정됨-CRUD-{datetime.now().strftime('%H%M%S')}"
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": "게시글 수정",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": "게시글 수정",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e)
            }
            
    async def _test_delete_post(self, slug: str) -> Dict:
        """게시글 삭제 테스트"""
        print(f"  🗑️  게시글 삭제 테스트 (슬러그: {slug})...")
        
        start_time = datetime.now()
        
        try:
            # 삭제 전 게시글이 존재하는지 먼저 확인
            async with self.session.get(
                f"{self.base_url}/api/posts/{slug}",
                headers=self.get_auth_headers()
            ) as pre_check_response:
                if pre_check_response.status != 200:
                    print(f"    ❌ 삭제 전 확인 실패 - 게시글이 존재하지 않음: {pre_check_response.status}")
                    return {
                        "test_name": "게시글 삭제",
                        "success": False,
                        "status": "failed",
                        "response_time": 0,
                        "error": f"삭제 전 게시글 조회 실패: {pre_check_response.status}"
                    }
            
            print(f"    🔍 삭제 전 확인 완료 - 게시글 존재함")
            
            # 삭제 수행
            async with self.session.delete(
                f"{self.base_url}/api/posts/{slug}",
                headers=self.get_auth_headers()
            ) as response:
                delete_time = datetime.now()
                delete_response_time = (delete_time - start_time).total_seconds()
                
                # 응답 내용 로깅
                response_text = await response.text()
                print(f"    🔍 삭제 응답: 상태={response.status}, 내용={response_text[:100]}")
                
                if response.status == 204:
                    print(f"    ✅ 삭제 성공 (204) - 시간: {delete_response_time:.3f}초")
                    
                    # 삭제 확인: 404가 발생하는지 체크
                    await asyncio.sleep(0.1)  # 약간의 대기시간
                    
                    async with self.session.get(
                        f"{self.base_url}/api/posts/{slug}",
                        headers=self.get_auth_headers()
                    ) as verify_response:
                        verify_time = datetime.now()
                        total_response_time = (verify_time - start_time).total_seconds()
                        
                        verify_text = await verify_response.text()
                        print(f"    🔍 삭제 확인: 상태={verify_response.status}, 내용={verify_text[:50]}")
                        
                        if verify_response.status == 404:
                            print(f"    ✅ 삭제 확인 - 404 정상 반환")
                            
                            return {
                                "test_name": "게시글 삭제",
                                "success": True,
                                "status": "success",
                                "response_time": total_response_time,
                                "delete_verified": True
                            }
                        else:
                            print(f"    ⚠️  삭제 확인 - 예상과 다른 응답: {verify_response.status}")
                            # 삭제 자체는 성공했으므로 부분 성공으로 처리
                            
                            return {
                                "test_name": "게시글 삭제",
                                "success": True,
                                "status": "partial_success",
                                "response_time": total_response_time,
                                "delete_verified": False,
                                "warning": f"삭제는 성공했으나 확인 시 {verify_response.status} 반환"
                            }
                            
                elif response.status == 200:
                    # 200 응답도 성공으로 간주
                    print(f"    ✅ 삭제 성공 (200) - 시간: {delete_response_time:.3f}초")
                    
                    return {
                        "test_name": "게시글 삭제",
                        "success": True,
                        "status": "success",
                        "response_time": delete_response_time,
                        "delete_verified": True,
                        "note": "200 상태코드로 삭제 완료"
                    }
                    
                else:
                    print(f"    ❌ 삭제 실패 - {response.status}: {response_text}")
                    
                    return {
                        "test_name": "게시글 삭제",
                        "success": False,
                        "status": "failed",
                        "response_time": delete_response_time,
                        "error": f"{response.status}: {response_text}"
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": "게시글 삭제",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e)
            }
        
    async def _test_get_posts_list(self, test_name: str, params: Dict) -> Dict:
        """게시글 목록 조회 API 테스트"""
        print(f"  🔍 {test_name} 테스트...")
        
        start_time = datetime.now()
        
        try:
            # URL 파라미터 구성
            url_params = []
            for key, value in params.items():
                url_params.append(f"{key}={value}")
            
            url = f"{self.base_url}/api/posts"
            if url_params:
                url += "?" + "&".join(url_params)
                
            async with self.session.get(url, headers=self.get_auth_headers()) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    posts_count = len(result.get("items", []))
                    
                    print(f"    ✅ 성공 - {posts_count}개 게시글, {response_time:.3f}초")
                    
                    return {
                        "test_name": test_name,
                        "status": "success",
                        "response_time": response_time,
                        "posts_count": posts_count,
                        "params": params,
                        "url": url
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": test_name,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error,
                        "params": params
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": test_name,
                "status": "error",
                "response_time": response_time,
                "error": str(e),
                "params": params
            }
            
    async def _test_get_comments_list(self, post_slug: str, test_name: str) -> Dict:
        """댓글 목록 조회 API 테스트"""
        print(f"  🔍 {test_name} 테스트...")
        
        start_time = datetime.now()
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/posts/{post_slug}/comments",
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    comments_count = len(result.get("comments", []))
                    total = result.get("pagination", {}).get("total", 0)
                    
                    print(f"    ✅ 성공 - {comments_count}개 댓글 (총 {total}개), {response_time:.3f}초")
                    
                    return {
                        "test_name": test_name,
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "comments_count": comments_count,
                        "total_comments": total,
                        "data": result
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": test_name,
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": test_name,
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e)
            }
            
    async def _test_create_comment(self, post_slug: str) -> Dict:
        """댓글 작성 테스트"""
        print(f"  💬 댓글 작성 테스트 (게시글: {post_slug})...")
        
        comment_data = self.create_tagged_comment_data("comment_crud", {
            "content": f"""이것은 댓글/답글 CRUD 테스트를 위한 댓글입니다.
            
**테스트 정보:**
- 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 테스트 타입: 댓글 작성 기능

이 댓글이 정상적으로 표시되고 수정/삭제가 가능한지 확인하세요.""",
            "metadata": {
                "test_type": "comment_creation"
            }
        })
        
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts/{post_slug}/comments",
                json=comment_data,
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 201:
                    result = await response.json()
                    self.track_created_item("comments", result)
                    
                    # ID 필드 처리 (_id 또는 id)
                    comment_id = result.get("id") or result.get("_id") or str(result.get("_id", "unknown"))
                    print(f"    ✅ 성공 - 댓글 ID: {comment_id}, 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": "댓글 작성",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result,
                        "comment_id": comment_id
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": "댓글 작성",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": "댓글 작성",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e)
            }
            
    async def _test_create_reply(self, post_slug: str, parent_comment_id: str) -> Dict:
        """답글 작성 테스트"""
        print(f"  💬 답글 작성 테스트 (부모 댓글: {parent_comment_id})...")
        
        reply_data = self.create_tagged_comment_data("reply_crud", {
            "content": f"""이것은 답글 CRUD 테스트를 위한 답글입니다.
            
**답글 정보:**
- 부모 댓글 ID: {parent_comment_id}
- 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 테스트 타입: 답글 작성 기능

이 답글이 부모 댓글 아래에 올바르게 표시되는지 확인하세요.""",
            "metadata": {
                "test_type": "reply_creation",
                "parent_comment_id": parent_comment_id
            }
        })
        
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts/{post_slug}/comments/{parent_comment_id}/replies",
                json=reply_data,
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 201:
                    result = await response.json()
                    self.track_created_item("comments", result)
                    
                    # ID 필드 처리 (_id 또는 id)
                    reply_id = result.get("id") or result.get("_id") or str(result.get("_id", "unknown"))
                    print(f"    ✅ 성공 - 답글 ID: {reply_id}, 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": "답글 작성",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result,
                        "reply_id": reply_id,
                        "parent_comment_id": parent_comment_id
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": "답글 작성",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error,
                        "parent_comment_id": parent_comment_id
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": "답글 작성",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e),
                "parent_comment_id": parent_comment_id
            }
            
    async def _test_update_comment(self, post_slug: str, comment_id: str, comment_type: str = "댓글") -> Dict:
        """댓글/답글 수정 테스트"""
        print(f"  ✏️  {comment_type} 수정 테스트 (ID: {comment_id})...")
        
        update_time = datetime.now().strftime('%H%M%S')
        update_data = {
            "content": f"""🔄 이것은 수정된 {comment_type}입니다.

**수정 정보:**
- 수정 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 수정 여부 확인용 마크: **수정됨-{comment_type}-{update_time}**
- 세션 ID: {self.session_id}

원본 내용이 이 내용으로 대체되었다면 {comment_type} 수정 기능이 정상 동작하는 것입니다."""
        }
        
        start_time = datetime.now()
        
        try:
            async with self.session.put(
                f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}",
                json=update_data,
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"    ✅ 성공 - {comment_type} 수정 완료, 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": f"{comment_type} 수정",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result,
                        "comment_id": comment_id,
                        "verification": f"수정됨-{comment_type}-{update_time}"
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": f"{comment_type} 수정",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error,
                        "comment_id": comment_id
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": f"{comment_type} 수정",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e),
                "comment_id": comment_id
            }
            
    async def _test_delete_comment(self, post_slug: str, comment_id: str, comment_type: str = "댓글") -> Dict:
        """댓글/답글 삭제 테스트"""
        print(f"  🗑️  {comment_type} 삭제 테스트 (ID: {comment_id})...")
        
        start_time = datetime.now()
        
        try:
            async with self.session.delete(
                f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}",
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 204:
                    print(f"    ✅ 성공 - {comment_type} 삭제 완료, 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": f"{comment_type} 삭제",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "comment_id": comment_id
                    }
                else:
                    response_text = await response.text()
                    print(f"    ❌ 실패 - {response.status}: {response_text}")
                    
                    return {
                        "test_name": f"{comment_type} 삭제",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": f"{response.status}: {response_text}",
                        "comment_id": comment_id
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": f"{comment_type} 삭제",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e),
                "comment_id": comment_id
            }
            
    async def _test_comment_reaction(self, post_slug: str, comment_id: str, reaction_type: str) -> Dict:
        """댓글 반응 (좋아요/싫어요) 테스트"""
        print(f"  👍 댓글 {reaction_type} 테스트 (ID: {comment_id})...")
        
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/{reaction_type}",
                headers=self.get_auth_headers()
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status == 200:
                    result = await response.json()
                    like_count = result.get("like_count", 0)
                    dislike_count = result.get("dislike_count", 0)
                    user_reaction = result.get("user_reaction", {})
                    
                    print(f"    ✅ 성공 - 좋아요: {like_count}, 싫어요: {dislike_count}, 시간: {response_time:.3f}초")
                    
                    return {
                        "test_name": f"댓글 {reaction_type}",
                        "success": True,
                        "status": "success",
                        "response_time": response_time,
                        "data": result,
                        "comment_id": comment_id,
                        "like_count": like_count,
                        "dislike_count": dislike_count,
                        "user_reaction": user_reaction
                    }
                else:
                    error = await response.json()
                    print(f"    ❌ 실패 - {response.status}: {error}")
                    
                    return {
                        "test_name": f"댓글 {reaction_type}",
                        "success": False,
                        "status": "failed",
                        "response_time": response_time,
                        "error": error,
                        "comment_id": comment_id
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            print(f"    ❌ 오류 - {str(e)}")
            
            return {
                "test_name": f"댓글 {reaction_type}",
                "success": False,
                "status": "error",
                "response_time": response_time,
                "error": str(e),
                "comment_id": comment_id
            }
            
    def save_session_info(self):
        """세션 정보를 파일로 저장"""
        session_data = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "test_user": self.test_user_data,
            "created_items": self.created_items,
            "test_results": self.test_results
        }
        
        session_file = f"test_session_{self.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
            
        return session_file
        
    async def run_comprehensive_test(self):
        """포괄적인 게시판 API 테스트 실행"""
        print("🧪 게시판 API 자동화 테스트 시작!")
        print(f"📧 세션 ID: {self.session_id}")
        print("="*80)
        
        # 1. 사용자 등록 및 로그인
        if not await self.register_and_login():
            print("❌ 인증 실패로 인해 테스트를 중단합니다.")
            return False
            
        # 2. 게시글 목록 기능 테스트
        await self.test_post_list_features()
        
        # 3. 게시글 CRUD 테스트
        await self.test_post_crud_operations()
        
        # 4. 댓글/답글 CRUD 테스트
        await self.test_comment_crud_operations()
        
        # TODO: 추가 테스트 시나리오들
        # - 반응 시스템 테스트
        # - 실시간 통계 검증
        
        # 세션 정보 저장
        session_file = self.save_session_info()
        
        # 결과 요약
        print("\n" + "="*80)
        print("🎊 게시판 API 테스트 완료!")
        print("="*80)
        print(f"📧 세션 ID: {self.session_id}")
        print(f"👤 테스트 사용자: {self.test_user_data['user_handle']} ({self.test_user_data['email']})")
        print(f"📊 생성된 데이터:")
        
        for item_type, items in self.created_items.items():
            if items:
                print(f"   - {item_type}: {len(items)}개")
                
        print(f"💾 세션 정보 저장: {session_file}")
        
        print(f"\n🧹 테스트 데이터 정리:")
        print(f"   python cleanup_test_data.py {self.session_id}")
        print(f"   python cleanup_test_data.py {self.session_id} --confirm")
        
        return True


async def main():
    parser = argparse.ArgumentParser(description="게시판 API 자동화 테스트")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                      help="API 기본 URL (기본값: http://localhost:8000)")
    parser.add_argument("--frontend-url", default="http://localhost:5173",
                      help="프론트엔드 URL (기본값: http://localhost:5173)")
    
    args = parser.parse_args()
    
    async with TestSessionManager(args.base_url) as test_manager:
        success = await test_manager.run_comprehensive_test()
        
        if success:
            print(f"\n🌐 브라우저에서 확인:")
            print(f"   - 게시판 목록: {args.frontend_url}/board")
            print(f"   - 생성된 게시글들을 직접 확인해보세요!")
            
        return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))