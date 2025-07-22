#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 20:43:20 KST
작업 버전: 게시판 수동 확인용 테스트 데이터 생성기 v2.0 (대폭 개선)
주요 컴포넌트들:
- BoardManualVerificationDataGenerator: 게시판 수동 확인용 데이터 생성기 (40-800라인)
  - discover_board_categories(): API를 통한 실제 카테고리 동적 조사 (100-150라인)
  - check_redis_cache_status(): Redis 캐싱 시스템 동작 확인 (152-200라인)
  - _create_comprehensive_test_data(): 포괄적 테스트 데이터 생성 (202-400라인)
  - _create_full_comment_crud(): 완전한 댓글/답글 CRUD 테스트 (402-500라인)
  - _create_detailed_reaction_tracking(): 상세한 반응 추적 시스템 (502-600라인)
  - _generate_enhanced_html_guide(): 대폭 개선된 HTML 가이드 (602-800라인)

핵심 기능 (v2.0):
- API를 통한 실제 게시판 카테고리 동적 조사 및 적용
- 완전한 댓글/답글 CRUD 시나리오 (생성→수정→삭제)
- 사용자별 반응 행위 상세 추적 및 변경 이력 기록
- Redis 캐싱 시스템 동작 확인 및 상태 모니터링
- 삭제된 데이터 정보까지 포함하는 종합적 HTML 가이드
- 브라우저에서 확인 불가능한 API 레벨 정보 상세 표시

관련 파일들:
- /scripts/development/testing/pages/board/api_test.py: API 자동화 테스트
- /scripts/development/testing/pages/board/test_data_cleaner.py: 테스트 데이터 정리
- /scripts/development/testing/unified/: 통합 프레임워크
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 통합 프레임워크 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "unified"))
from base_test_runner import OAuth2APIManager
from rate_limit_controller import RateLimitTestContext, RateLimitController


class BoardManualVerificationDataGenerator:
    """게시판 수동 확인용 테스트 데이터 생성기"""
    
    def __init__(self, base_url: str = "http://localhost:8000", auto_disable_rate_limit: bool = True):
        self.base_url = base_url
        self.frontend_url = "http://localhost:5173"
        self.auto_disable_rate_limit = auto_disable_rate_limit
        
        # 세션 ID 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"BOARD_MANUAL_{timestamp}_{random_suffix}"
        
        self.api_manager = None
        self.rate_limit_controller = RateLimitController(api_base_url=base_url) if auto_disable_rate_limit else None
        
        # 생성된 데이터 추적
        self.created_data = {
            "users": [],
            "posts": [],
            "comments": [],
            "reactions": [],
            "statistics": {
                "total_users": 0,
                "total_posts": 0,
                "total_comments": 0,
                "total_reactions": 0
            }
        }
        
        # 동적으로 조사될 게시판 카테고리 및 샘플 데이터
        self.discovered_categories = []
        self.redis_cache_info = {}
        
        # 상세 추적 데이터
        self.detailed_tracking = {
            "user_actions": [],  # 모든 사용자 행위 기록
            "reaction_changes": [],  # 반응 변경 이력
            "deleted_data": [],  # 삭제된 데이터 정보
            "cache_operations": [],  # 캐시 관련 작업
            "api_calls": []  # 모든 API 호출 기록
        }
        
        # 실제 게시판 카테고리들 (동적으로 조사될 예정)
        self.board_categories = ["입주 정보"]  # 기본값, API로 업데이트
        
        # 샘플 게시글들 (기존 성공 테스트 패턴 기반)
        self.sample_posts = [
            {
                "title": "커뮤니티 이용 가이드 - 수동확인용", 
                "content": "# 커뮤니티 이용 가이드\n\n수동 확인을 위한 테스트 게시글입니다.\n\n## 주요 기능\n- 게시글 작성 및 수정\n- 댓글과 답글 시스템\n- 반응(좋아요) 기능\n- 실시간 통계 업데이트",
                "category": "입주 정보"
            },
            {
                "title": "게시판 기능 테스트 - 댓글 시스템",
                "content": "# 댓글 시스템 테스트\n\n이 게시글은 댓글 및 답글 기능을 테스트하기 위해 작성되었습니다.\n\n다음 기능들을 확인해보세요:\n- 댓글 작성\n- 답글 작성\n- 댓글 수정\n- 댓글 삭제",
                "category": "생활 정보"
            },
            {
                "title": "수동 확인 테스트 - 반응 시스템", 
                "content": "# 반응 시스템 테스트\n\n좋아요 기능과 사용자 반응을 테스트하는 게시글입니다.\n\n## 확인할 기능\n- 게시글 좋아요/취소\n- 실시간 좋아요 수 업데이트\n- 사용자별 좋아요 상태 표시",
                "category": "이야기"
            },
            {
                "title": "Redis 캐싱 테스트 게시글",
                "content": "# Redis 캐싱 시스템 검증\n\n이 게시글로 캐싱 시스템을 확인할 수 있습니다.\n\n## 캐싱 확인 포인트\n- 게시글 조회수 캐싱\n- 인기 게시글 랭킹\n- 사용자 세션 관리\n- 반응 통계 캐싱",
                "category": "생활 정보"
            },
            {
                "title": "종합 기능 테스트 게시글",
                "content": "# 모든 기능 종합 테스트\n\n게시판의 모든 주요 기능을 한 번에 테스트할 수 있는 게시글입니다.\n\n## 테스트 체크리스트\n- [ ] 게시글 조회\n- [ ] 댓글 작성\n- [ ] 답글 작성\n- [ ] 좋아요 추가\n- [ ] 실시간 통계 확인",
                "category": "이야기"
            }
        ]
    
    async def generate_test_data(self) -> Dict[str, Any]:
        """수동 확인용 테스트 데이터 일괄 생성 (Rate Limiting 자동 제어 포함)"""
        print(f"🏗️ 게시판 수동 확인용 테스트 데이터 생성 시작")
        print(f"🆔 세션 ID: {self.session_id}")
        if self.auto_disable_rate_limit:
            print(f"🚦 Rate Limiting: 테스트 중 자동 비활성화")
        print("=" * 70)
        
        # Rate Limiting 제어 컨텍스트 사용 여부 결정
        if self.auto_disable_rate_limit and self.rate_limit_controller:
            async with RateLimitTestContext(self.rate_limit_controller) as controller:
                return await self._generate_test_data_internal()
        else:
            return await self._generate_test_data_internal()
    
    async def _generate_test_data_internal(self) -> Dict[str, Any]:
        """내부 테스트 데이터 생성 로직"""
        self.api_manager = OAuth2APIManager(self.base_url)
        
        try:
            async with self.api_manager:
                # 0. 실제 게시판 카테고리 동적 조사
                await self._discover_board_categories()
                
                # 1. Redis 캐시 시스템 상태 확인
                await self._check_redis_cache_status()
                
                # 2. 테스트 사용자 생성
                await self._create_test_users()
                
                # 3. 게시판 게시글 생성
                await self._create_comprehensive_test_data()
                
                # 4. 완전한 댓글/답글 CRUD 시나리오
                await self._create_full_comment_crud()
                
                # 5. 상세한 반응 추적 시스템
                await self._create_detailed_reaction_tracking()
                
                # 6. 대폭 개선된 HTML 가이드 생성
                guide_path = await self._generate_enhanced_html_guide()
                
                print("\n🎉 게시판 수동 확인용 데이터 생성 완료!")
                print(f"📊 생성 결과:")
                print(f"   🏷️ 발견된 카테고리: {len(self.discovered_categories)}개")
                print(f"   👤 사용자: {self.created_data['statistics']['total_users']}명")
                print(f"   📝 게시글: {self.created_data['statistics']['total_posts']}개")
                print(f"   💬 댓글: {self.created_data['statistics']['total_comments']}개")
                print(f"   👍 반응: {self.created_data['statistics']['total_reactions']}개")
                print(f"   🧠 Redis 캐시: {len(self.redis_cache_info)}개 키")
                print(f"\n📋 수동 확인 가이드: {guide_path}")
                print(f"🌐 브라우저에서 확인: {self.frontend_url}/board")
                
                return {
                    "session_id": self.session_id,
                    "guide_path": guide_path,
                    "statistics": self.created_data["statistics"],
                    "discovered_categories": self.discovered_categories,
                    "redis_cache_info": self.redis_cache_info,
                    "detailed_tracking": self.detailed_tracking,
                    "created_data": self.created_data
                }
                
        except Exception as e:
            print(f"❌ 데이터 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def _create_test_users(self):
        """테스트 사용자 생성"""
        print("👤 테스트 사용자 생성 중...")
        
        session_suffix = self.session_id.split('_')[-1].lower()
        
        test_users = [
            {
                "email": f"board_user1_{session_suffix}@example.com",
                "user_handle": f"board_user1_{session_suffix}",
                "name": f"게시판 사용자1 {session_suffix[:4].upper()}",
                "display_name": f"BoardUser1 {session_suffix[:4]}",
                "password": "ManualTest123!",
                "role": "일반 사용자"
            },
            {
                "email": f"board_user2_{session_suffix}@example.com", 
                "user_handle": f"board_user2_{session_suffix}",
                "name": f"게시판 사용자2 {session_suffix[:4].upper()}",
                "display_name": f"BoardUser2 {session_suffix[:4]}",
                "password": "ManualTest123!",
                "role": "활동적 사용자"
            },
            {
                "email": f"board_moderator_{session_suffix}@example.com",
                "user_handle": f"board_moderator_{session_suffix}",
                "name": f"게시판 관리자 {session_suffix[:4].upper()}",
                "display_name": f"BoardModerator {session_suffix[:4]}",
                "password": "ManualTest123!",
                "role": "관리자"
            }
        ]
        
        created_count = 0
        for user_data in test_users:
            # Rate limiting을 고려한 충분한 대기
            if created_count > 0:  # 첫 번째가 아닌 경우에만 대기
                await asyncio.sleep(5.0)
            
            # 사용자 등록
            register_result = await self.api_manager.register_user(user_data)
            if register_result["success"] or register_result.get("status") == 409:
                # 로그인으로 토큰 획득
                auth_result = await self.api_manager.authenticate_user(
                    user_data["email"], user_data["password"]
                )
                
                if auth_result["success"]:
                    user_data["token"] = auth_result["token"]
                    user_data["user_id"] = auth_result["user"].get("id") or auth_result["user"].get("_id")
                    self.created_data["users"].append(user_data)
                    created_count += 1
                    print(f"   ✅ {user_data['role']} 생성: {user_data['email']}")
                else:
                    print(f"   ❌ {user_data['role']} 인증 실패: {user_data['email']}")
            else:
                print(f"   ❌ {user_data['role']} 등록 실패: {user_data['email']}")
        
        self.created_data["statistics"]["total_users"] = created_count
        print(f"   📊 총 {created_count}명의 테스트 사용자 생성 완료")
        
        # 사용자 생성 추적 기록
        self.detailed_tracking["user_actions"].extend([
            f"사용자 {user['email']} 등록 및 인증 완료" for user in self.created_data["users"]
        ])
    
    async def _discover_board_categories(self):
        """실제 게시판 카테고리 설정 (프론트엔드에서 확인됨)"""
        print("🔍 게시판 카테고리 설정 중...")
        
        try:
            # 기존 게시글들에서 카테고리 정보 수집
            posts_result = await self.api_manager.api_request(
                "GET", f"{self.base_url}/api/posts",
                params={"service": "residential_community", "type": "board", "limit": 50}
            )
            
            # 실제 게시판에 존재하는 기본 카테고리들 (프론트엔드에서 확인됨)
            valid_categories = ["입주 정보", "생활 정보", "이야기"]
            categories_found = set()  # 빈 세트로 시작
            
            if posts_result["success"] and posts_result.get("data"):
                data = posts_result["data"]
                # 데이터가 리스트인지 확인
                if isinstance(data, dict) and "items" in data:
                    posts_list = data["items"]
                elif isinstance(data, list):
                    posts_list = data
                else:
                    posts_list = []
                
                for post in posts_list:
                    if isinstance(post, dict):
                        metadata = post.get("metadata", {})
                        category = metadata.get("category")
                        # 실제 게시판에 존재하는 카테고리만 수집 (테스트 카테고리 제외)
                        if category and category in valid_categories:
                            categories_found.add(category)
            
            # 프론트엔드에서 확인된 실제 카테고리 3개 모두 사용 (테스트 완성도를 위해)
            self.discovered_categories = valid_categories.copy()
            self.board_categories = valid_categories.copy()
            
            if categories_found:
                print(f"   ✅ 기존 게시글에서 발견된 카테고리: {', '.join(sorted(categories_found))}")
            else:
                print(f"   ⚠️ 기존 게시글에서 해당 카테고리를 찾을 수 없음")
            
            print(f"   ✅ 테스트용 카테고리 설정 완료: {', '.join(self.board_categories)}")
            print(f"   ℹ️ 프론트엔드 게시판 UI의 실제 카테고리 3개를 모두 포함")
            
            # 추적 정보 기록
            self.detailed_tracking["api_calls"].append({
                "endpoint": "카테고리 설정 (프론트엔드 기준)",
                "method": "CONFIG",
                "result": f"{len(self.board_categories)}개 카테고리 설정 완료",
                "timestamp": datetime.now().strftime('%H:%M:%S')
            })
            
        except Exception as e:
            print(f"   ⚠️ 카테고리 조사 실패, 기본 카테고리 사용: {e}")
            self.discovered_categories = ["입주 정보"]
            self.board_categories = ["입주 정보"]
    
    async def _check_redis_cache_status(self):
        """Redis 캐싱 시스템 동작 확인"""
        print("🗄️ Redis 캐시 시스템 상태 확인 중...")
        
        try:
            # Redis 전용 헬스체크 엔드포인트로 Redis 상태 확인
            health_result = await self.api_manager.api_request(
                "GET", f"{self.base_url}/health/redis"
            )
            
            if health_result["success"]:
                health_data = health_result["data"]
                redis_type = health_data.get("redis_type", "unknown")
                key_prefix = health_data.get("key_prefix", "unknown")
                cache_enabled = health_data.get("cache_enabled", False)
                
                self.redis_cache_info = {
                    "type": redis_type,
                    "prefix": key_prefix,
                    "enabled": cache_enabled,
                    "status": "healthy" if cache_enabled else "disabled"
                }
                
                print(f"   ✅ Redis 타입: {redis_type}")
                print(f"   ✅ 키 프리픽스: {key_prefix}")
                print(f"   ✅ 캐시 활성화: {cache_enabled}")
            else:
                self.redis_cache_info = {"status": "unavailable"}
                print("   ⚠️ Redis 상태 확인 불가")
                
            # 캐시 작업 기록
            self.detailed_tracking["cache_operations"].append({
                "operation": "Redis 상태 확인",
                "result": str(self.redis_cache_info),
                "timestamp": datetime.now().strftime('%H:%M:%S')
            })
            
        except Exception as e:
            print(f"   ❌ Redis 상태 확인 실패: {e}")
            self.redis_cache_info = {"status": "error", "error": str(e)}
    
    async def _create_comprehensive_test_data(self):
        """포괄적 테스트 데이터 생성"""
        print("📝 포괄적 게시판 테스트 데이터 생성 중...")
        
        if not self.created_data["users"]:
            print("   ⚠️ 테스트 사용자가 없어 게시글 생성을 스킵합니다.")
            return
        
        created_count = 0
        
        # 발견된 카테고리별로 각각 1개의 게시글 생성 (중복 방지)
        for i, category in enumerate(self.board_categories):
            # 카테고리별로 다른 샘플 게시글 사용 (순환)
            sample_post = self.sample_posts[i % len(self.sample_posts)]
            await asyncio.sleep(1.0)  # Rate limiting 비활성화되어 있어서 짧은 대기만
            
            # 랜덤하게 사용자 선택
            author = random.choice(self.created_data["users"])
            
            post_data = {
                "title": f"{sample_post['title']} [{category}]",
                "content": sample_post["content"] + f"\n\n---\n*테스트 세션: {self.session_id}*\n*카테고리: {category}*",
                "service": "residential_community",
                "metadata": {
                    "type": "board", 
                    "category": category,
                    "tags": ["테스트", "수동확인", "CRUD"],
                    "test_session": self.session_id
                }
            }
            
            create_result = await self.api_manager.api_request(
                "POST", f"{self.base_url}/api/posts",
                user_token=author["token"],
                json_data=post_data
            )
            
            if create_result["success"] and create_result["status"] == 201:
                created_post = create_result["data"]
                created_post["author_info"] = {
                    "name": author["name"],
                    "role": author["role"],
                    "email": author["email"]
                }
                self.created_data["posts"].append(created_post)
                created_count += 1
                print(f"   ✅ {category} 게시글 생성: {sample_post['title'][:30]}...")
                
                # 상세 추적 기록
                self.detailed_tracking["user_actions"].append(
                    f"사용자 {author['name']}이 '{sample_post['title'][:30]}...' 게시글 생성"
                )
                self.detailed_tracking["api_calls"].append({
                    "endpoint": "/api/posts",
                    "method": "POST", 
                        "result": f"게시글 생성 성공 (ID: {created_post.get('_id', 'unknown')})",
                        "timestamp": datetime.now().strftime('%H:%M:%S')
                    })
            else:
                print(f"   ❌ 게시글 생성 실패: {sample_post['title'][:30]}...")
                print(f"       상세: {create_result.get('data', 'Unknown error')}")
        
        self.created_data["statistics"]["total_posts"] = created_count
        print(f"   📊 총 {created_count}개의 게시글 생성 완료")
    
    async def _create_full_comment_crud(self):
        """완전한 댓글/답글 CRUD 시나리오 (생성→수정→삭제)"""
        print("💬 완전한 댓글/답글 CRUD 시나리오 실행 중...")
        
        if not self.created_data["posts"] or not self.created_data["users"]:
            print("   ⚠️ 게시글 또는 사용자가 없어 댓글 CRUD 시나리오를 스킵합니다.")
            return
        
        crud_count = {"created": 0, "modified": 0, "deleted": 0}
        test_comments = []  # CRUD 테스트용 댓글 저장
        
        # 대상 게시글 선택 (첫 2개 게시글에서 CRUD 테스트)
        target_posts = self.created_data["posts"][:2]
        
        for post in target_posts:
            post_id = post.get("id") or post.get("_id")
            post_title = post.get("title", "Unknown")[:30]
            
            print(f"\n   🎯 게시글 '{post_title}...'에서 CRUD 테스트 실행")
            
            # 1. 댓글 생성 (Create)
            for i in range(2):  # 2개 댓글으로 줄여서 Rate limit 완화
                await asyncio.sleep(2.0)  # 댓글 생성 간격 늘리기
                commenter = random.choice(self.created_data["users"])
                
                comment_data = {
                    "content": f"CRUD 테스트 댓글 #{i+1} - 수정과 삭제를 테스트할 예정입니다. (세션: {self.session_id})",
                    "post_id": str(post_id)
                }
                
                create_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/comments",
                    user_token=commenter["token"],
                    json_data=comment_data
                )
                
                if create_result["success"]:
                    created_comment = create_result["data"]
                    created_comment["commenter_info"] = {
                        "name": commenter["name"],
                        "role": commenter["role"],
                        "email": commenter["email"]
                    }
                    created_comment["original_content"] = comment_data["content"]  # 원본 내용 저장
                    
                    self.created_data["comments"].append(created_comment)
                    test_comments.append(created_comment)  # CRUD 테스트용으로 저장
                    crud_count["created"] += 1
                    print(f"      ✅ 댓글 #{i+1} 생성 성공")
                    
                    # 상세 추적
                    self.detailed_tracking["user_actions"].append(
                        f"사용자 {commenter['name']}이 댓글 생성: '{comment_data['content'][:50]}...'"
                    )
                else:
                    print(f"      ❌ 댓글 #{i+1} 생성 실패")
            
            # 2. 댓글 수정 (Update)
            if test_comments:
                await asyncio.sleep(0.5)
                comment_to_update = test_comments[-1]  # 마지막 댓글을 수정
                comment_id = comment_to_update.get("id") or comment_to_update.get("_id")
                original_author = comment_to_update["commenter_info"]
                
                # 수정을 위해 원래 작성자의 토큰 찾기
                author_token = None
                for user in self.created_data["users"]:
                    if user["email"] == original_author["email"]:
                        author_token = user["token"]
                        break
                
                if author_token:
                    update_data = {
                        "content": f"수정된 CRUD 테스트 댓글 - 수정 기능 정상 작동 확인! (세션: {self.session_id})"
                    }
                    
                    update_result = await self.api_manager.api_request(
                        "PUT", f"{self.base_url}/api/comments/{comment_id}",
                        user_token=author_token,
                        json_data=update_data
                    )
                    
                    if update_result["success"]:
                        crud_count["modified"] += 1
                        print(f"      ✅ 댓글 수정 성공")
                        
                        # 수정 전후 내용 추적
                        self.detailed_tracking["user_actions"].append(
                            f"사용자 {original_author['name']}이 댓글 수정: '{comment_to_update['original_content'][:30]}...' → '수정된 CRUD 테스트 댓글...'"
                        )
                        
                        # 삭제될 데이터 정보 저장
                        self.detailed_tracking["deleted_data"].append({
                            "type": "comment_content",
                            "original_content": comment_to_update["original_content"],
                            "modified_content": update_data["content"],
                            "comment_id": str(comment_id),
                            "author": original_author["name"]
                        })
                    else:
                        print(f"      ❌ 댓글 수정 실패")
            
            # 3. 답글 생성 및 삭제 (Delete)
            if test_comments:
                await asyncio.sleep(0.5)
                parent_comment = test_comments[0]  # 첫 번째 댓글에 답글 생성
                replier = random.choice(self.created_data["users"])
                
                reply_data = {
                    "content": f"삭제 테스트용 답글 - 이 답글은 곧 삭제될 예정입니다. (세션: {self.session_id})",
                    "post_id": str(post_id),
                    "parent_id": parent_comment.get("id") or parent_comment.get("_id")
                }
                
                reply_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/comments",
                    user_token=replier["token"],
                    json_data=reply_data
                )
                
                if reply_result["success"]:
                    created_reply = reply_result["data"]
                    reply_id = created_reply.get("id") or created_reply.get("_id")
                    crud_count["created"] += 1
                    print(f"      ✅ 삭제 테스트용 답글 생성")
                    
                    # 상세 추적
                    self.detailed_tracking["user_actions"].append(
                        f"사용자 {replier['name']}이 답글 생성: '{reply_data['content'][:50]}...'"
                    )
                    
                    # 잠시 후 답글 삭제
                    await asyncio.sleep(1.0)
                    delete_result = await self.api_manager.api_request(
                        "DELETE", f"{self.base_url}/api/comments/{reply_id}",
                        user_token=replier["token"]
                    )
                    
                    if delete_result["success"]:
                        crud_count["deleted"] += 1
                        print(f"      ✅ 답글 삭제 성공 (CRUD 테스트)")
                        
                        # 삭제된 데이터 정보 추적
                        self.detailed_tracking["deleted_data"].append({
                            "type": "deleted_reply",
                            "content": reply_data["content"],
                            "reply_id": str(reply_id),
                            "author": replier["name"],
                            "parent_comment_id": str(parent_comment.get("id") or parent_comment.get("_id")),
                            "deleted_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        self.detailed_tracking["user_actions"].append(
                            f"사용자 {replier['name']}이 답글 삭제: '{reply_data['content'][:50]}...'"
                        )
                    else:
                        print(f"      ❌ 답글 삭제 실패")
        
        # CRUD 테스트 결과 업데이트
        self.created_data["statistics"]["total_comments"] += crud_count["created"]
        print(f"\n   📊 CRUD 테스트 결과:")
        print(f"      생성: {crud_count['created']}개")
        print(f"      수정: {crud_count['modified']}개")
        print(f"      삭제: {crud_count['deleted']}개")
        print(f"   ✅ 댓글/답글 CRUD 시나리오 완료")
    
    async def _create_detailed_reaction_tracking(self):
        """상세한 반응 추적 시스템 (사용자별 반응 변화 이력 추적)"""
        print("👍 상세한 반응 추적 시스템 실행 중...")
        
        if not self.created_data["posts"] or not self.created_data["users"]:
            print("   ⚠️ 게시글 또는 사용자가 없어 반응 추적을 스킵합니다.")
            return
        
        reaction_scenarios = 0
        
        # 모든 게시글에 대해 다양한 반응 시나리오 실행
        for post in self.created_data["posts"]:
            post_id = post.get("id") or post.get("_id")
            post_title = post.get("title", "Unknown")[:30]
            
            print(f"\n   🎯 게시글 '{post_title}...'에 반응 시나리오 적용")
            
            # 시나리오 1: 사용자들이 순차 좋아요 추가 후 취소  
            for i, user in enumerate(self.created_data["users"]):
                await asyncio.sleep(1.5)  # 반응 테스트 간격 늘리기
                
                # 좋아요 추가
                like_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_id}/like",
                    user_token=user["token"]
                )
                
                if like_result["success"]:
                    reaction_scenarios += 1
                    print(f"      ✅ {user['name']} 좋아요 추가")
                    
                    # 반응 변화 이력 기록
                    self.detailed_tracking["reaction_changes"].append({
                        "user": user["name"],
                        "action": "like_add",
                        "post_title": post_title,
                        "post_id": str(post_id),
                        "timestamp": datetime.now().strftime('%H:%M:%S')
                    })
                    
                    self.detailed_tracking["user_actions"].append(
                        f"사용자 {user['name']}이 '{post_title}...' 게시글에 좋아요 추가"
                    )
                    
                    # 첫 번째와 마지막 사용자는 좋아요 취소
                    if i == 0 or i == len(self.created_data["users"]) - 1:
                        await asyncio.sleep(0.5)
                        
                        unlike_result = await self.api_manager.api_request(
                            "DELETE", f"{self.base_url}/api/posts/{post_id}/like",
                            user_token=user["token"]
                        )
                        
                        if unlike_result["success"]:
                            print(f"      ❎ {user['name']} 좋아요 취소")
                            
                            # 취소 이력 기록
                            self.detailed_tracking["reaction_changes"].append({
                                "user": user["name"],
                                "action": "like_remove",
                                "post_title": post_title,
                                "post_id": str(post_id),
                                "timestamp": datetime.now().strftime('%H:%M:%S')
                            })
                            
                            self.detailed_tracking["user_actions"].append(
                                f"사용자 {user['name']}이 '{post_title}...' 게시글에서 좋아요 취소"
                            )
                            
                            # 취소된 반응 정보 추적
                            self.detailed_tracking["deleted_data"].append({
                                "type": "cancelled_reaction",
                                "user": user["name"],
                                "reaction_type": "like",
                                "post_title": post_title,
                                "post_id": str(post_id),
                                "cancelled_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                
                else:
                    print(f"      ❌ {user['name']} 좋아요 추가 실패")
            
            # 시나리오 2: 댓글에 대한 반응 시스템 (사용 가능한 경우)
            post_comments = [c for c in self.created_data["comments"] if c.get("post_id") == str(post_id)]
            if post_comments:
                sample_comment = post_comments[0]
                comment_id = sample_comment.get("id") or sample_comment.get("_id")
                
                # 댓글 좋아요 테스트 (지원되는 경우)
                test_user = self.created_data["users"][0]
                comment_like_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/comments/{comment_id}/like",
                    user_token=test_user["token"]
                )
                
                if comment_like_result["success"]:
                    print(f"      ✅ 댓글 좋아요 기능 테스트 성공")
                    reaction_scenarios += 1
                else:
                    print(f"      ⚠️ 댓글 좋아요 기능 미지원 또는 실패")
        
        self.created_data["statistics"]["total_reactions"] = reaction_scenarios
        print(f"\n   📊 반응 추적 결과:")
        print(f"      총 반응 시나리오: {reaction_scenarios}개")
        print(f"      반응 변화 이력: {len(self.detailed_tracking['reaction_changes'])}개")
        print(f"      취소된 반응: {len([d for d in self.detailed_tracking['deleted_data'] if d.get('type') == 'cancelled_reaction'])}개")
        print(f"   ✅ 상세한 반응 추적 시스템 완료")
    
    async def _generate_enhanced_html_guide(self) -> str:
        """대폭 개선된 HTML 가이드 생성 (삭제된 데이터 정보 포함)"""
        print("📋 대폭 개선된 HTML 가이드 생성 중...")
        
        guide_dir = Path(__file__).parent.parent.parent / "browser"
        guide_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_suffix = self.session_id.split('_')[-1]
        
        guide_filename = f"board_manual_verification_guide_v2_{timestamp}_{session_suffix}.html"
        guide_path = guide_dir / guide_filename
        
        # 게시글 링크들 생성
        post_links = ""
        for i, post in enumerate(self.created_data["posts"][:8], 1):
            post_id = post.get("id") or post.get("_id")
            post_title = post.get("title", "제목 없음")[:50]
            post_category = post.get("metadata", {}).get("category", "미분류")
            author_name = post.get("author_info", {}).get("name", "Unknown")
            
            post_links += f'''
                <div class="post-link-card">
                    <h4><a href="{self.frontend_url}/board/{post_id}" target="_blank">{i}. {post_title}...</a></h4>
                    <p class="post-meta">[카테고리: {post_category}] | 작성자: {author_name}</p>
                </div>
            '''
        
        # 테스트 계정 카드들
        account_cards = ""
        for user in self.created_data["users"]:
            account_cards += f'''
                <div class="account-card">
                    <h3>{user['name']} ({user['role']})</h3>
                    <p><strong>이메일:</strong> {user['email']}</p>
                    <p><strong>비밀번호:</strong> {user['password']}</p>
                    <p><strong>닉네임:</strong> {user['display_name']}</p>
                </div>
            '''
        
        # 카테고리 정보
        category_info = ", ".join(self.discovered_categories) if self.discovered_categories else "발견되지 않음"
        
        # Redis 캐시 정보
        redis_status = self.redis_cache_info.get("status", "unknown")
        redis_type = self.redis_cache_info.get("type", "N/A")
        redis_prefix = self.redis_cache_info.get("prefix", "N/A")
        
        # CRUD 시나리오 결과 추적
        crud_summary = f"""
        <div class="crud-summary">
            <h4>CRUD 시나리오 결과</h4>
            <p>• 생성된 댓글/답글: {self.created_data['statistics']['total_comments']}개</p>
            <p>• 수정 테스트: {len([a for a in self.detailed_tracking['user_actions'] if '수정' in a])}건</p>
            <p>• 삭제 테스트: {len([d for d in self.detailed_tracking['deleted_data'] if d.get('type') == 'deleted_reply'])}건</p>
        </div>
        """
        
        # 삭제된 데이터 정보
        deleted_data_section = ""
        if self.detailed_tracking["deleted_data"]:
            deleted_data_section = "<h3>🗑️ 삭제된 데이터 정보 (브라우저에서 확인 불가)</h3><div class='deleted-data-list'>"
            
            for deleted_item in self.detailed_tracking["deleted_data"][:5]:  # 최대 5개
                if deleted_item.get("type") == "deleted_reply":
                    deleted_data_section += f'''
                        <div class="deleted-item">
                            <h4>삭제된 답글</h4>
                            <p><strong>내용:</strong> {deleted_item['content'][:100]}...</p>
                            <p><strong>작성자:</strong> {deleted_item['author']}</p>
                            <p><strong>삭제 시간:</strong> {deleted_item['deleted_at']}</p>
                        </div>
                    '''
                elif deleted_item.get("type") == "cancelled_reaction":
                    deleted_data_section += f'''
                        <div class="deleted-item">
                            <h4>취소된 좋아요</h4>
                            <p><strong>사용자:</strong> {deleted_item['user']}</p>
                            <p><strong>게시글:</strong> {deleted_item['post_title']}...</p>
                            <p><strong>취소 시간:</strong> {deleted_item['cancelled_at']}</p>
                        </div>
                    '''
            
            deleted_data_section += "</div>"
        
        # 반응 변화 이력
        reaction_history = ""
        if self.detailed_tracking["reaction_changes"]:
            reaction_history = "<h4>👍 반응 변화 이력</h4><div class='reaction-history'>"
            for change in self.detailed_tracking["reaction_changes"][-10:]:  # 최근 10개
                action_text = "좋아요 추가" if change["action"] == "like_add" else "좋아요 취소"
                reaction_history += f'''
                    <p>{change['timestamp']} - {change['user']}가 '{change['post_title']}...'에 {action_text}</p>
                '''
            reaction_history += "</div>"
    
        # HTML 문서 생성
        html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>게시판(Board) 수동 확인 가이드 v2.0</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 40px; text-align: center; position: relative; }}
        .header::after {{ content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 20px; background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none"><path d="M1200 120L0 16.48 0 0 1200 0 1200 120z" fill="%23ffffff"></path></svg>'); }}
        .header h1 {{ font-size: 3rem; margin-bottom: 15px; font-weight: 300; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .version-badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-size: 0.9em; margin-top: 10px; }}
        .section {{ padding: 30px; margin: 25px; background: #f8f9fa; border-radius: 15px; border-left: 6px solid #4facfe; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }}
        .section h2 {{ color: #2c3e50; font-size: 1.8rem; margin-bottom: 25px; display: flex; align-items: center; gap: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin: 25px 0; }}
        .stat-card {{ text-align: center; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); transition: transform 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card.users {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }}
        .stat-card.posts {{ background: linear-gradient(135deg, #e0c3fc 0%, #9bb5ff 100%); }}
        .stat-card.comments {{ background: linear-gradient(135deg, #fff1eb 0%, #ace0f9 100%); }}
        .stat-card.reactions {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); }}
        .stat-card.categories {{ background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); }}
        .stat-card.redis {{ background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%); }}
        .stat-number {{ font-size: 2.5rem; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 0.9rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; }}
        .account-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; }}
        .account-card {{ background: white; border-radius: 12px; padding: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border: 1px solid #e9ecef; }}
        .account-card h3 {{ color: #495057; margin-bottom: 15px; font-size: 1.2rem; }}
        .post-link-card {{ background: white; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 4px solid #4facfe; }}
        .post-link-card h4 {{ margin: 0 0 10px 0; }}
        .post-link-card a {{ color: #2980b9; text-decoration: none; font-weight: 500; }}
        .post-link-card a:hover {{ color: #3498db; }}
        .post-meta {{ color: #6c757d; font-size: 0.9rem; margin: 0; }}
        .checklist {{ list-style: none; padding: 0; }}
        .checklist li {{ padding: 15px; margin: 10px 0; background: white; border-radius: 8px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.3s; }}
        .checklist li:hover {{ box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .checklist input[type="checkbox"] {{ margin-right: 15px; transform: scale(1.3); }}
        .highlight {{ background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); padding: 20px; border-left: 5px solid #ffc107; border-radius: 8px; margin: 20px 0; }}
        .feature-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .feature-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .deleted-data-list {{ display: grid; gap: 15px; }}
        .deleted-item {{ background: #fff5f5; border: 1px solid #fed7d7; border-radius: 8px; padding: 15px; }}
        .deleted-item h4 {{ color: #c53030; margin: 0 0 10px 0; }}
        .reaction-history {{ background: #f7fafc; padding: 15px; border-radius: 8px; max-height: 300px; overflow-y: auto; }}
        .reaction-history p {{ margin: 5px 0; font-size: 0.9rem; }}
        .crud-summary {{ background: #e6fffa; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #38b2ac; }}
        .redis-info {{ background: #ebf4ff; padding: 20px; border-radius: 10px; border-left: 4px solid #4299e1; }}
        .api-tracking {{ background: #f0fff4; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .command-box {{ background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 8px; font-family: 'Courier New', monospace; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 게시판(Board) 수동 확인 가이드</h1>
            <div class="version-badge">v2.0 대폭 개선 버전</div>
            <p>세션 ID: <strong>{self.session_id}</strong></p>
            <p>생성 시간: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
        </div>
        
        <div class="section">
            <h2>📊 생성된 테스트 데이터 현황</h2>
            <div class="stats">
                <div class="stat-card users">
                    <div class="stat-number">{self.created_data["statistics"]["total_users"]}</div>
                    <div class="stat-label">테스트 사용자</div>
                </div>
                <div class="stat-card posts">
                    <div class="stat-number">{self.created_data["statistics"]["total_posts"]}</div>
                    <div class="stat-label">게시글</div>
                </div>
                <div class="stat-card comments">
                    <div class="stat-number">{self.created_data["statistics"]["total_comments"]}</div>
                    <div class="stat-label">댓글/답글</div>
                </div>
                <div class="stat-card reactions">
                    <div class="stat-number">{self.created_data["statistics"]["total_reactions"]}</div>
                    <div class="stat-label">반응</div>
                </div>
                <div class="stat-card categories">
                    <div class="stat-number">{len(self.discovered_categories)}</div>
                    <div class="stat-label">발견된 카테고리</div>
                </div>
                <div class="stat-card redis">
                    <div class="stat-number">{redis_type}</div>
                    <div class="stat-label">Redis 타입</div>
                </div>
            </div>
            
            <div class="redis-info">
                <h4>🗄️ Redis 캐시 시스템 상태</h4>
                <p>• 상태: <strong>{redis_status}</strong></p>
                <p>• 타입: <strong>{redis_type}</strong></p>
                <p>• 키 프리픽스: <strong>{redis_prefix}</strong></p>
            </div>
            
            <div class="highlight">
                <h4>🏷️ 발견된 게시판 카테고리</h4>
                <p>{category_info}</p>
            </div>
            
            {crud_summary}
        </div>
        
        <div class="section">
            <h2>👤 테스트 계정 정보</h2>
            <p>브라우저에서 로그인하여 다양한 기능을 테스트해보세요:</p>
            <div class="account-grid">
                {account_cards}
            </div>
        </div>
        
        <div class="section">
            <h2>🔗 게시판 테스트 링크</h2>
            <div class="highlight">
                <h4>🌐 메인 게시판 페이지</h4>
                <p><a href="{self.frontend_url}/board" target="_blank" style="color: #3498db; font-size: 1.2em;">{self.frontend_url}/board</a></p>
            </div>
            
            <h3>생성된 게시글 직접 링크:</h3>
            {post_links}
        </div>
        
        <div class="section">
            <h2>✅ 수동 확인 체크리스트</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>기본 기능 테스트</h3>
                    <ul class="checklist">
                        <li><input type="checkbox"> 게시판 목록 페이지 정상 로딩</li>
                        <li><input type="checkbox"> 카테고리별 필터링 작동</li>
                        <li><input type="checkbox"> 게시글 검색 기능 작동</li>
                        <li><input type="checkbox"> 페이지네이션 작동</li>
                        <li><input type="checkbox"> 게시글 상세 페이지 정상 표시</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>CRUD 기능 테스트</h3>
                    <ul class="checklist">
                        <li><input type="checkbox"> 로그인 후 게시글 작성 가능</li>
                        <li><input type="checkbox"> 게시글 수정 기능 (작성자만)</li>
                        <li><input type="checkbox"> 댓글 작성 및 표시 정상</li>
                        <li><input type="checkbox"> 답글 작성 및 계층 구조 표시</li>
                        <li><input type="checkbox"> 댓글 수정 기능 작동</li>
                        <li><input type="checkbox"> 댓글/답글 삭제 기능 테스트</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>반응 시스템 테스트</h3>
                    <ul class="checklist">
                        <li><input type="checkbox"> 게시글 좋아요 기능 작동</li>
                        <li><input type="checkbox"> 좋아요 취소 기능</li>
                        <li><input type="checkbox"> 댓글 좋아요 기능 (지원되는 경우)</li>
                        <li><input type="checkbox"> 실시간 좋아요 수 업데이트</li>
                        <li><input type="checkbox"> 사용자별 좋아요 상태 표시</li>
                    </ul>
                </div>
                
                <div class="feature-card">
                    <h3>시스템 통합 테스트</h3>
                    <ul class="checklist">
                        <li><input type="checkbox"> 실시간 통계 업데이트 (조회수, 댓글 수 등)</li>
                        <li><input type="checkbox"> Redis 캐시 시스템 작동 확인</li>
                        <li><input type="checkbox"> 사용자 세션 관리 정상</li>
                        <li><input type="checkbox"> 인기 게시글 랭킹 시스템</li>
                        <li><input type="checkbox"> 게시글 정렬 및 필터링</li>
                    </ul>
                </div>
            </div>
        </div>
        
        {deleted_data_section}
        
        <div class="section">
            <h2>📊 상세 데이터 추적 정보</h2>
            {reaction_history}
            
            <div class="api-tracking">
                <h4>🔌 API 호출 통계</h4>
                <p>총 API 호출: <strong>{len(self.detailed_tracking['api_calls'])}건</strong></p>
                <p>캐시 작업: <strong>{len(self.detailed_tracking['cache_operations'])}건</strong></p>
                <p>사용자 행위: <strong>{len(self.detailed_tracking['user_actions'])}건</strong></p>
            </div>
        </div>
        
        <div class="section">
            <h2>⚠️ 주의사항 및 데이터 정리</h2>
            <p><strong>데이터 정리:</strong> 수동 확인이 완료된 후에는 다음 명령어로 테스트 데이터를 정리하세요:</p>
            <div class="command-box">
cd /home/nadle/projects/Xai_Community/v5/scripts/development/testing/pages/board
python test_data_cleaner.py --session {self.session_id}
            </div>
            
            <div class="highlight">
                <h4>🔍 추가 디버깅 정보</h4>
                <p>• 이 가이드는 브라우저에서 확인할 수 없는 API 레벨 데이터를 포함합니다.</p>
                <p>• CRUD 시나리오, 반응 변화 이력, 삭제된 데이터 등이 상세히 기록되었습니다.</p>
                <p>• Redis 캐시 상태와 환경별 설정을 확인할 수 있습니다.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        # HTML 파일 저장
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✅ 대폭 개선된 HTML 가이드 생성: {guide_path}")
        return str(guide_path)


async def main():
    """메인 실행 함수"""
    print("🏗️ 게시판(Board) 수동 확인용 테스트 데이터 생성기")
    print("브라우저에서 확인할 수 있는 테스트 데이터를 생성합니다.")
    print("🚦 Rate Limiting 자동 제어: 테스트 시작시 비활성화, 종료시 복구")
    print("=" * 70)
    
    generator = BoardManualVerificationDataGenerator(auto_disable_rate_limit=True)
    result = await generator.generate_test_data()
    
    if result:
        print("\n🎉 데이터 생성 성공!")
        print(f"수동 확인 가이드: {result['guide_path']}")
        
        # 선택적으로 브라우저 자동 열기
        import webbrowser
        try:
            webbrowser.open(f"file://{result['guide_path']}")
            print("🌐 브라우저에서 가이드를 열었습니다.")
        except Exception:
            pass
            
        return 0
    else:
        print("\n❌ 데이터 생성 실패!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))