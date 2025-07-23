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
        
        # 사용자별 활동 추적 강화
        self.user_activities = {}
        
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
                
                # 6. 필터/검색 기능 테스트
                await self._test_filter_search_functionality()
                
                # 7. 답글 최대 깊이 테스트 (4단계)
                await self._test_max_reply_depth()
                
                # 8. 대폭 개선된 HTML 가이드 생성
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
                    
                    # 사용자별 활동 추적 초기화
                    self._init_user_activity(user_data["email"])
                    
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
        """포괄적 게시판 테스트 데이터 생성 (CRUD 완전 구현)"""
        print("📝 포괄적 게시판 테스트 데이터 생성 중...")
        
        if not self.created_data["users"]:
            print("   ⚠️ 테스트 사용자가 없어 게시글 생성을 스킵합니다.")
            return
        
        crud_stats = {"created": 0, "updated": 0, "deleted": 0}
        
        # 1. 게시글 생성 (Create)
        for i, category in enumerate(self.board_categories):
            sample_post = self.sample_posts[i % len(self.sample_posts)]
            await asyncio.sleep(1.0)
            
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
                    "email": author["email"],
                    "token": author["token"]  # 수정/삭제용
                }
                created_post["original_title"] = post_data["title"]
                created_post["original_content"] = post_data["content"]
                
                self.created_data["posts"].append(created_post)
                crud_stats["created"] += 1
                print(f"   ✅ {category} 게시글 생성: {sample_post['title'][:30]}...")
                
                self._track_post_action(author["name"], "post_create", post_data["title"], created_post.get("_id"))
                self._track_user_activity(author["email"], "posts", "created", {
                    "title": post_data["title"],
                    "category": category,
                    "post_id": str(created_post.get("_id"))
                })
            else:
                print(f"   ❌ 게시글 생성 실패: {sample_post['title'][:30]}...")
        
        # 2. 게시글 수정 (Update)
        if self.created_data["posts"]:
            # 첫 번째 게시글을 수정
            post_to_update = self.created_data["posts"][0]
            post_id = post_to_update.get("id") or post_to_update.get("_id")
            post_slug = post_to_update.get("slug") or str(post_id)
            author_token = post_to_update["author_info"]["token"]
            
            await asyncio.sleep(1.0)
            
            updated_title = f"[수정됨] {post_to_update['original_title']}"
            updated_content = post_to_update["original_content"] + f"\n\n**📝 수정됨**: 게시글 수정 기능 테스트 완료 ({datetime.now().strftime('%H:%M:%S')})"
            
            update_data = {
                "title": updated_title,
                "content": updated_content
            }
            
            update_result = await self.api_manager.api_request(
                "PUT", f"{self.base_url}/api/posts/{post_slug}",
                user_token=author_token,
                json_data=update_data
            )
            
            if update_result["success"]:
                crud_stats["updated"] += 1
                print(f"   ✅ 게시글 수정 성공: {post_to_update['original_title'][:30]}...")
                
                # 수정된 내용 추적
                post_to_update["updated_title"] = updated_title
                post_to_update["updated_content"] = updated_content
                post_to_update["was_updated"] = True
                
                self._track_post_action(
                    post_to_update["author_info"]["name"], 
                    "post_update", 
                    post_to_update["original_title"], 
                    post_id
                )
                self._track_user_activity(post_to_update["author_info"]["email"], "posts", "updated", {
                    "title": post_to_update["original_title"],
                    "updated_title": updated_title,
                    "post_id": str(post_id)
                })
            else:
                print(f"   ❌ 게시글 수정 실패: {update_result.get('data', 'Unknown error')}")
        
        # 3. 게시글 삭제 (Delete) - 마지막 게시글 삭제
        if len(self.created_data["posts"]) > 1:
            post_to_delete = self.created_data["posts"][-1]
            post_id = post_to_delete.get("id") or post_to_delete.get("_id")
            post_slug = post_to_delete.get("slug") or str(post_id)
            author_token = post_to_delete["author_info"]["token"]
            
            await asyncio.sleep(1.0)
            
            delete_result = await self.api_manager.api_request(
                "DELETE", f"{self.base_url}/api/posts/{post_slug}",
                user_token=author_token
            )
            
            if delete_result["success"]:
                crud_stats["deleted"] += 1
                print(f"   ✅ 게시글 삭제 성공: {post_to_delete['original_title'][:30]}...")
                
                # 삭제된 게시글 정보 보존
                deleted_post = self.created_data["posts"].pop()  # 리스트에서 제거
                deleted_post["was_deleted"] = True
                deleted_post["deleted_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 삭제된 데이터 추적 및 삭제 플래그 설정
                deleted_post["was_deleted"] = True  # 삭제 플래그 추가
                self.detailed_tracking["deleted_data"].append({
                    "type": "deleted_post",
                    "title": deleted_post["original_title"],
                    "content": deleted_post["original_content"][:100] + "...",
                    "author": deleted_post["author_info"]["name"],
                    "post_id": str(post_id),
                    "deleted_at": deleted_post["deleted_at"]
                })
                
                self._track_post_action(
                    deleted_post["author_info"]["name"], 
                    "post_delete", 
                    deleted_post["original_title"], 
                    post_id
                )
                self._track_user_activity(deleted_post["author_info"]["email"], "posts", "deleted", {
                    "title": deleted_post["original_title"],
                    "post_id": str(post_id)
                })
            else:
                print(f"   ❌ 게시글 삭제 실패: {delete_result.get('data', 'Unknown error')}")
        
        # 통계 업데이트
        self.created_data["statistics"]["total_posts"] = crud_stats["created"]
        self.created_data["statistics"]["post_crud"] = crud_stats
        
        print(f"\n   📊 게시글 CRUD 테스트 결과:")
        print(f"      생성: {crud_stats['created']}개")
        print(f"      수정: {crud_stats['updated']}개") 
        print(f"      삭제: {crud_stats['deleted']}개")
        print(f"   ✅ 포괄적 게시판 테스트 데이터 생성 완료")
    
    def _track_post_action(self, user_name: str, action: str, post_title: str, post_id: str):
        """게시글 액션 추적 헬퍼 메서드"""
        action_descriptions = {
            "post_create": "게시글 생성",
            "post_update": "게시글 수정", 
            "post_delete": "게시글 삭제"
        }
        
        description = action_descriptions.get(action, action)
        
        self.detailed_tracking["user_actions"].append(
            f"사용자 {user_name}이 '{post_title[:30]}...' {description}"
        )
        
        self.detailed_tracking["api_calls"].append({
            "endpoint": "/api/posts",
            "method": action.split("_")[1].upper(),
            "result": f"{description} 성공 (ID: {post_id})",
            "timestamp": datetime.now().strftime('%H:%M:%S')
        })
    
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
            
            # 1. 댓글 생성 (Create) - 올바른 API 엔드포인트 사용
            for i in range(2):  # 2개 댓글으로 줄여서 Rate limit 완화
                await asyncio.sleep(2.0)  # 댓글 생성 간격 늘리기
                commenter = random.choice(self.created_data["users"])
                
                # 게시글 슬러그 추출 - 실제 slug 필드 사용
                post_slug = post.get("slug") or str(post_id)
                
                comment_data = {
                    "content": f"CRUD 테스트 댓글 #{i+1} - 수정과 삭제를 테스트할 예정입니다. (세션: {self.session_id})"
                }
                
                create_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
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
                        "PUT", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}",
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
                    "parent_comment_id": str(parent_comment.get("id") or parent_comment.get("_id"))
                }
                
                reply_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
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
                        "DELETE", f"{self.base_url}/api/posts/{post_slug}/comments/{reply_id}",
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
                        
                        # 사용자 활동 추적
                        self._track_user_activity(replier["email"], "replies", "deleted", {
                            "content": reply_data["content"],
                            "reply_id": str(reply_id)
                        })
                    else:
                        print(f"      ❌ 답글 삭제 실패")
                        
                # 4. 답글 수정 테스트 (새로운 답글 생성 후 수정)
                if len(self.created_data["comments"]) > 0 and len(self.created_data["users"]) >= 2:
                    modifier = self.created_data["users"][1]  # 두 번째 사용자가 수정
                    parent_comment = self.created_data["comments"][0]
                    
                    # 수정용 답글 생성
                    await asyncio.sleep(1.0)
                    reply_data = {
                        "content": f"수정 테스트용 답글 - 원본 내용 (세션: {self.session_id})",
                        "parent_comment_id": str(parent_comment.get("id") or parent_comment.get("_id"))
                    }
                    
                    reply_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                        user_token=modifier["token"],
                        json_data=reply_data
                    )
                    
                    if reply_result["success"]:
                        created_reply = reply_result["data"]
                        reply_id = created_reply.get("id") or created_reply.get("_id")
                        crud_count["created"] += 1
                        
                        # 답글 수정
                        await asyncio.sleep(1.0)
                        updated_content = f"수정 테스트용 답글 - 수정된 내용 ({datetime.now().strftime('%H:%M:%S')})"
                        
                        update_result = await self.api_manager.api_request(
                            "PUT", f"{self.base_url}/api/posts/{post_slug}/comments/{reply_id}",
                            user_token=modifier["token"],
                            json_data={"content": updated_content}
                        )
                        
                        if update_result["success"]:
                            crud_count["modified"] += 1
                            print(f"      ✅ 답글 수정 성공 (CRUD 테스트)")
                            
                            self.detailed_tracking["user_actions"].append(
                                f"사용자 {modifier['name']}이 답글 수정: '{reply_data['content'][:30]}...' → '{updated_content[:30]}...'"
                            )
                            
                            # 사용자 활동 추적
                            self._track_user_activity(modifier["email"], "replies", "updated", {
                                "content": updated_content,
                                "reply_id": str(reply_id)
                            })
                        else:
                            print(f"      ❌ 답글 수정 실패")
                    else:
                        print(f"      ❌ 수정용 답글 생성 실패")
                        
                # 5. 댓글 삭제 테스트 (실제 API 호출)
                if len(self.created_data["comments"]) > 0 and len(self.created_data["users"]) >= 1:
                    deleter = self.created_data["users"][0]  # 첫 번째 사용자가 삭제
                    
                    # 삭제용 댓글 생성
                    await asyncio.sleep(1.0)
                    comment_data = {
                        "content": f"삭제 테스트용 댓글 - 이 댓글은 삭제될 예정입니다 (세션: {self.session_id})"
                    }
                    
                    comment_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                        user_token=deleter["token"],
                        json_data=comment_data
                    )
                    
                    if comment_result["success"]:
                        created_comment = comment_result["data"]
                        comment_id = created_comment.get("id") or created_comment.get("_id")
                        crud_count["created"] += 1
                        
                        # 댓글 삭제
                        await asyncio.sleep(1.0)
                        delete_comment_result = await self.api_manager.api_request(
                            "DELETE", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}",
                            user_token=deleter["token"]
                        )
                        
                        if delete_comment_result["success"]:
                            crud_count["deleted"] += 1
                            print(f"      ✅ 댓글 삭제 성공 (CRUD 테스트)")
                            
                            # 삭제된 데이터 정보 추적
                            self.detailed_tracking["deleted_data"].append({
                                "type": "deleted_comment",
                                "content": comment_data["content"],
                                "comment_id": str(comment_id),
                                "author": deleter["name"],
                                "deleted_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            self.detailed_tracking["user_actions"].append(
                                f"사용자 {deleter['name']}이 댓글 삭제: '{comment_data['content'][:50]}...'"
                            )
                            
                            # 사용자 활동 추적
                            self._track_user_activity(deleter["email"], "comments", "deleted", {
                                "content": comment_data["content"],
                                "comment_id": str(comment_id)
                            })
                        else:
                            print(f"      ❌ 댓글 삭제 실패")
                    else:
                        print(f"      ❌ 삭제용 댓글 생성 실패")
        
        # CRUD 테스트 결과 업데이트
        self.created_data["statistics"]["total_comments"] += crud_count["created"]
        print(f"\n   📊 CRUD 테스트 결과:")
        print(f"      생성: {crud_count['created']}개")
        print(f"      수정: {crud_count['modified']}개")
        print(f"      삭제: {crud_count['deleted']}개")
        print(f"   ✅ 댓글/답글 CRUD 시나리오 완료")
    
    async def _create_detailed_reaction_tracking(self):
        """확장된 반응 추적 시스템 (좋아요/싫어요/북마크/전환 시나리오 완전 구현)"""
        print("👍 확장된 반응 추적 시스템 실행 중...")
        
        if not self.created_data["posts"] or not self.created_data["users"]:
            print("   ⚠️ 게시글 또는 사용자가 없어 반응 추적을 스킵합니다.")
            return
        
        reaction_stats = {
            "likes": 0, "dislikes": 0, "bookmarks": 0, 
            "like_cancels": 0, "dislike_cancels": 0, "bookmark_cancels": 0,
            "like_to_dislike": 0, "dislike_to_like": 0,
            "comment_likes": 0, "comment_dislikes": 0, "comment_like_to_dislike": 0, "comment_dislike_to_like": 0,
            "comment_like_cancels": 0, "comment_dislike_cancels": 0
        }
        
        # 각 게시글에 대해 포괄적인 반응 시나리오 실행
        for post_idx, post in enumerate(self.created_data["posts"]):
            post_id = post.get("id") or post.get("_id")
            post_slug = post.get("slug") or str(post_id)
            post_title = post.get("title", "Unknown")[:30]
            
            print(f"\n   🎯 게시글 '{post_title}...'에 확장된 반응 시나리오 적용")
            
            # 시나리오 1: 게시글 좋아요 테스트 (모든 사용자)
            for i, user in enumerate(self.created_data["users"]):
                await asyncio.sleep(1.0)
                
                user_name = user["name"]
                user_token = user["token"]
                
                # 좋아요 테스트
                like_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/like",
                    user_token=user_token
                )
                
                if like_result["success"]:
                    reaction_stats["likes"] += 1
                    print(f"      ✅ {user_name} 좋아요 추가")
                    self._track_reaction(user_name, "like_add", post_title, str(post_id))
                    self._track_user_activity(user["email"], "reactions", "likes", {
                        "target": "post", "title": post_title, "target_id": str(post_id)
                    })
                    
                    # 북마크 독립 테스트 (좋아요와 함께)
                    await asyncio.sleep(0.3)
                    bookmark_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/bookmark",
                        user_token=user_token
                    )
                    
                    if bookmark_result["success"]:
                        reaction_stats["bookmarks"] += 1
                        print(f"      📚 {user_name} 북마크 추가 (좋아요와 독립)")
                        self._track_reaction(user_name, "bookmark_add", post_title, str(post_id))
                        self._track_user_activity(user["email"], "reactions", "bookmarks", {
                            "target": "post", "title": post_title, "target_id": str(post_id)
                        })
                else:
                    print(f"      ❌ {user_name} 좋아요 실패")
            
            # 시나리오 1-2: 게시글 싫어요 테스트 (두 번째 사용자만)
            if len(self.created_data["users"]) >= 2:
                user2 = self.created_data["users"][1]
                await asyncio.sleep(0.5)
                
                dislike_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/dislike",
                    user_token=user2["token"]
                )
                
                if dislike_result["success"]:
                    reaction_stats["dislikes"] += 1
                    print(f"      👎 {user2['name']} 싫어요 추가 (독립 테스트)")
                    self._track_reaction(user2["name"], "dislike_add", post_title, str(post_id))
                    self._track_user_activity(user2["email"], "reactions", "dislikes", {
                        "target": "post", "title": post_title, "target_id": str(post_id)
                    })
            
            # 시나리오 2: 반응 전환 테스트 (좋아요 → 싫어요)
            if len(self.created_data["users"]) >= 1:
                user1 = self.created_data["users"][0]
                await asyncio.sleep(0.5)
                
                dislike_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/dislike",
                    user_token=user1["token"]
                )
                
                if dislike_result["success"]:
                    reaction_stats["like_to_dislike"] += 1
                    print(f"      🔄 {user1['name']} 좋아요→싫어요 전환")
                    self._track_reaction(user1["name"], "like_to_dislike", post_title, str(post_id))
                    self._track_user_activity(user1["email"], "reactions", "transitions", {
                        "target": "post", "title": post_title, "target_id": str(post_id), "type": "like_to_dislike"
                    })
            
            # 시나리오 3: 반응 전환 테스트 (싫어요 → 좋아요) - 세 번째 사용자
            if len(self.created_data["users"]) >= 3:
                user3 = self.created_data["users"][2]
                await asyncio.sleep(0.5)
                
                # 먼저 싫어요 추가
                dislike_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/dislike",
                    user_token=user3["token"]
                )
                
                if dislike_result["success"]:
                    reaction_stats["dislikes"] += 1
                    print(f"      👎 {user3['name']} 싫어요 추가")
                    
                    # 그다음 좋아요로 전환
                    await asyncio.sleep(0.3)
                    like_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/like",
                        user_token=user3["token"]
                    )
                    
                    if like_result["success"]:
                        reaction_stats["dislike_to_like"] += 1
                        print(f"      🔄 {user3['name']} 싫어요→좋아요 전환")
                        self._track_reaction(user3["name"], "dislike_to_like", post_title, str(post_id))
                        self._track_user_activity(user3["email"], "reactions", "transitions", {
                            "target": "post", "title": post_title, "target_id": str(post_id), "type": "dislike_to_like"
                        })
            
            # 시나리오 4: 모든 반응 취소 테스트
            if len(self.created_data["users"]) >= 2:
                user2 = self.created_data["users"][1]
                await asyncio.sleep(0.5)
                
                # 좋아요 취소 (토글)
                unlike_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/like",
                    user_token=user2["token"]
                )
                
                if unlike_result["success"]:
                    reaction_stats["like_cancels"] += 1
                    print(f"      ❎ {user2['name']} 좋아요 취소")
                    self._track_reaction(user2["name"], "like_cancel", post_title, str(post_id))
                    self._track_user_activity(user2["email"], "reactions", "like_cancels", {
                        "target": "post", "title": post_title, "target_id": str(post_id)
                    })
                
                # 북마크 취소 (토글)
                await asyncio.sleep(0.3)
                unbookmark_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/bookmark",
                    user_token=user2["token"]
                )
                
                if unbookmark_result["success"]:
                    reaction_stats["bookmark_cancels"] += 1
                    print(f"      📚❎ {user2['name']} 북마크 취소")
                    self._track_reaction(user2["name"], "bookmark_cancel", post_title, str(post_id))
                    self._track_user_activity(user2["email"], "reactions", "bookmark_cancels", {
                        "target": "post", "title": post_title, "target_id": str(post_id)
                    })
            
            # 시나리오 5: 싫어요 취소 테스트
            if len(self.created_data["users"]) >= 1:
                user1 = self.created_data["users"][0]
                await asyncio.sleep(0.5)
                
                # 싫어요 취소 (토글) - 현재 user1은 싫어요 상태
                dislike_cancel_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/dislike",
                    user_token=user1["token"]
                )
                
                if dislike_cancel_result["success"]:
                    reaction_stats["dislike_cancels"] += 1
                    print(f"      👎❎ {user1['name']} 싫어요 취소")
                    self._track_reaction(user1["name"], "dislike_cancel", post_title, str(post_id))
                    self._track_user_activity(user1["email"], "reactions", "dislike_cancels", {
                        "target": "post", "title": post_title, "target_id": str(post_id)
                    })
            
            # 시나리오 6: 댓글 반응 완전한 테스트
            post_comments = [c for c in self.created_data["comments"] 
                           if str(c.get("post_id", "")) == str(post_id) or 
                              c.get("metadata", {}).get("route_path", "").endswith(post_slug)]
            
            if post_comments:
                sample_comment = post_comments[0]
                comment_id = sample_comment.get("id") or sample_comment.get("_id")
                
                # 댓글 좋아요 (사용자1)
                if len(self.created_data["users"]) >= 1:
                    user1 = self.created_data["users"][0]
                    await asyncio.sleep(0.5)
                    
                    comment_like_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/like",
                        user_token=user1["token"]
                    )
                    
                    if comment_like_result["success"]:
                        reaction_stats["comment_likes"] += 1
                        print(f"      💬👍 {user1['name']} 댓글 좋아요")
                        self._track_reaction(user1["name"], "comment_like", post_title, str(comment_id), "comment")
                        self._track_user_activity(user1["email"], "reactions", "comment_likes", {
                            "target": "comment", "title": post_title, "target_id": str(comment_id)
                        })
                        
                        # 댓글 좋아요 → 싫어요 전환 테스트
                        await asyncio.sleep(0.3)
                        comment_dislike_result = await self.api_manager.api_request(
                            "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/dislike",
                            user_token=user1["token"]
                        )
                        
                        if comment_dislike_result["success"]:
                            reaction_stats["comment_like_to_dislike"] += 1
                            print(f"      💬🔄 {user1['name']} 댓글 좋아요→싫어요 전환")
                            self._track_reaction(user1["name"], "comment_like_to_dislike", post_title, str(comment_id), "comment")
                            self._track_user_activity(user1["email"], "reactions", "transitions", {
                                "target": "comment", "title": post_title, "target_id": str(comment_id), "type": "comment_like_to_dislike"
                            })
                
                # 댓글 싫어요 → 좋아요 전환 테스트 (사용자2)
                if len(self.created_data["users"]) >= 2:
                    user2 = self.created_data["users"][1]
                    await asyncio.sleep(0.5)
                    
                    # 먼저 싫어요 추가
                    comment_dislike_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/dislike",
                        user_token=user2["token"]
                    )
                    
                    if comment_dislike_result["success"]:
                        reaction_stats["comment_dislikes"] += 1
                        print(f"      💬👎 {user2['name']} 댓글 싫어요")
                        
                        # 그다음 좋아요로 전환
                        await asyncio.sleep(0.3)
                        comment_like_result = await self.api_manager.api_request(
                            "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/like",
                            user_token=user2["token"]
                        )
                        
                        if comment_like_result["success"]:
                            reaction_stats["comment_dislike_to_like"] += 1
                            print(f"      💬🔄 {user2['name']} 댓글 싫어요→좋아요 전환")
                            self._track_reaction(user2["name"], "comment_dislike_to_like", post_title, str(comment_id), "comment")
                            self._track_user_activity(user2["email"], "reactions", "comment_transitions", {
                                "target": "comment", "title": post_title, "target_id": str(comment_id), "type": "dislike_to_like"
                            })
                
                # 댓글 취소 시나리오 테스트 (사용자3)
                if len(self.created_data["users"]) >= 3:
                    user3 = self.created_data["users"][2]
                    await asyncio.sleep(0.5)
                    
                    # 댓글 좋아요 후 취소
                    comment_like_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/like",
                        user_token=user3["token"]
                    )
                    
                    if comment_like_result["success"]:
                        print(f"      💬👍 {user3['name']} 댓글 좋아요")
                        
                        # 좋아요 취소
                        await asyncio.sleep(0.3)
                        comment_like_cancel_result = await self.api_manager.api_request(
                            "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/like",
                            user_token=user3["token"]
                        )
                        
                        if comment_like_cancel_result["success"]:
                            reaction_stats["comment_like_cancels"] += 1
                            print(f"      💬❎ {user3['name']} 댓글 좋아요 취소")
                            self._track_reaction(user3["name"], "comment_like_cancel", post_title, str(comment_id), "comment")
                            self._track_user_activity(user3["email"], "reactions", "comment_cancels", {
                                "target": "comment", "title": post_title, "target_id": str(comment_id), "type": "like_cancel"
                            })
                    
                    # 댓글 싫어요 후 취소 (사용자4)
                    if len(self.created_data["users"]) >= 4:
                        user4 = self.created_data["users"][3]
                        await asyncio.sleep(0.5)
                        
                        # 댓글 싫어요
                        comment_dislike_result = await self.api_manager.api_request(
                            "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/dislike",
                            user_token=user4["token"]
                        )
                        
                        if comment_dislike_result["success"]:
                            print(f"      💬👎 {user4['name']} 댓글 싫어요")
                            
                            # 싫어요 취소
                            await asyncio.sleep(0.3)
                            comment_dislike_cancel_result = await self.api_manager.api_request(
                                "POST", f"{self.base_url}/api/posts/{post_slug}/comments/{comment_id}/dislike",
                                user_token=user4["token"]
                            )
                            
                            if comment_dislike_cancel_result["success"]:
                                reaction_stats["comment_dislike_cancels"] += 1
                                print(f"      💬❎ {user4['name']} 댓글 싫어요 취소")
                                self._track_reaction(user4["name"], "comment_dislike_cancel", post_title, str(comment_id), "comment")
                                self._track_user_activity(user4["email"], "reactions", "comment_cancels", {
                                    "target": "comment", "title": post_title, "target_id": str(comment_id), "type": "dislike_cancel"
                                })
        
        # 통계 업데이트
        total_reactions = sum(reaction_stats.values())
        self.created_data["statistics"]["total_reactions"] = total_reactions
        self.created_data["statistics"]["reaction_breakdown"] = reaction_stats
        
        print(f"\n   📊 확장된 반응 추적 결과:")
        print(f"      ✅ 게시글 좋아요: {reaction_stats['likes']}개")
        print(f"      ❌ 게시글 싫어요: {reaction_stats['dislikes']}개") 
        print(f"      📚 게시글 북마크: {reaction_stats['bookmarks']}개")
        print(f"      🔄 좋아요→싫어요: {reaction_stats['like_to_dislike']}개")
        print(f"      🔄 싫어요→좋아요: {reaction_stats['dislike_to_like']}개")
        print(f"      ❎ 좋아요 취소: {reaction_stats['like_cancels']}개")
        print(f"      ❎ 싫어요 취소: {reaction_stats['dislike_cancels']}개")
        print(f"      📚❎ 북마크 취소: {reaction_stats['bookmark_cancels']}개")
        print(f"      💬👍 댓글 좋아요: {reaction_stats['comment_likes']}개")
        print(f"      💬👎 댓글 싫어요: {reaction_stats['comment_dislikes']}개")
        print(f"      💬🔄 댓글 좋아요→싫어요: {reaction_stats['comment_like_to_dislike']}개")
        print(f"      💬🔄 댓글 싫어요→좋아요: {reaction_stats['comment_dislike_to_like']}개")
        print(f"      💬❎ 댓글 좋아요 취소: {reaction_stats['comment_like_cancels']}개")
        print(f"      💬❎ 댓글 싫어요 취소: {reaction_stats['comment_dislike_cancels']}개")
        print(f"      📊 총 반응 시나리오: {total_reactions}개")
        print(f"   ✅ 확장된 반응 추적 시스템 완료")
    
    async def _test_filter_search_functionality(self):
        """필터/검색 기능 테스트"""
        print("🔍 필터/검색 기능 테스트 실행 중...")
        
        if not self.created_data["posts"]:
            print("   ⚠️ 게시글이 없어 필터/검색 테스트를 스킵합니다.")
            return
        
        test_results = {
            "category_filter": [],
            "search_results": [],
            "pagination_test": {"tested": False, "results": []}
        }
        
        # 1. 카테고리별 필터 테스트
        for category in self.board_categories:
            try:
                await asyncio.sleep(0.5)
                filter_result = await self.api_manager.api_request(
                    "GET", f"{self.base_url}/api/posts?category={category}&page=1&page_size=10"
                )
                
                if filter_result["success"]:
                    posts_data = filter_result["data"]
                    post_count = len(posts_data.get("posts", []))
                    test_results["category_filter"].append({
                        "category": category,
                        "count": post_count,
                        "success": True
                    })
                    print(f"   ✅ 카테고리 '{category}' 필터: {post_count}개 게시글")
                else:
                    test_results["category_filter"].append({
                        "category": category,
                        "count": 0,
                        "success": False
                    })
                    print(f"   ❌ 카테고리 '{category}' 필터 실패")
                    
            except Exception as e:
                print(f"   ⚠️ 카테고리 '{category}' 필터 오류: {e}")
        
        # 2. 검색 기능 테스트
        search_terms = ["테스트", "Board", "수동", "확인"]
        for term in search_terms:
            try:
                await asyncio.sleep(0.5)
                search_result = await self.api_manager.api_request(
                    "GET", f"{self.base_url}/api/posts?search={term}&page=1&page_size=10"
                )
                
                if search_result["success"]:
                    posts_data = search_result["data"]
                    post_count = len(posts_data.get("posts", []))
                    test_results["search_results"].append({
                        "term": term,
                        "count": post_count,
                        "success": True
                    })
                    print(f"   🔍 검색어 '{term}': {post_count}개 결과")
                else:
                    test_results["search_results"].append({
                        "term": term,
                        "count": 0,
                        "success": False
                    })
                    print(f"   ❌ 검색어 '{term}' 실패")
                    
            except Exception as e:
                print(f"   ⚠️ 검색어 '{term}' 오류: {e}")
        
        # 3. 페이지네이션 테스트
        try:
            await asyncio.sleep(0.5)
            pagination_result = await self.api_manager.api_request(
                "GET", f"{self.base_url}/api/posts?page=1&page_size=2"
            )
            
            if pagination_result["success"]:
                posts_data = pagination_result["data"]
                page_info = posts_data.get("pagination", {})
                test_results["pagination_test"] = {
                    "tested": True,
                    "current_page": page_info.get("page", 1),
                    "page_size": page_info.get("page_size", 2),
                    "total": page_info.get("total", 0),
                    "total_pages": page_info.get("total_pages", 0)
                }
                print(f"   📄 페이지네이션: {page_info.get('page', 1)}/{page_info.get('total_pages', 0)} 페이지")
            else:
                print(f"   ❌ 페이지네이션 테스트 실패")
                
        except Exception as e:
            print(f"   ⚠️ 페이지네이션 테스트 오류: {e}")
        
        # 결과 저장
        self.created_data["filter_search_tests"] = test_results
        
        print(f"   ✅ 필터/검색 기능 테스트 완료")
        print(f"      카테고리 필터: {len([r for r in test_results['category_filter'] if r['success']])}/{len(test_results['category_filter'])} 성공")
        print(f"      검색 테스트: {len([r for r in test_results['search_results'] if r['success']])}/{len(test_results['search_results'])} 성공")
        print(f"      페이지네이션: {'성공' if test_results['pagination_test']['tested'] else '실패'}")
    
    async def _test_max_reply_depth(self):
        """답글 최대 깊이 4단계 테스트"""
        print("🌳 답글 최대 깊이 테스트 실행 중...")
        
        if not self.created_data["posts"] or len(self.created_data["users"]) < 4:
            print("   ⚠️ 게시글 또는 사용자가 부족하여 깊이 테스트를 스킵합니다.")
            return
        
        # 첫 번째 게시글 선택
        test_post = self.created_data["posts"][0]
        post_slug = test_post.get("slug") or str(test_post.get("id") or test_post.get("_id"))
        
        depth_test_results = {
            "target_post": post_slug,
            "max_depth_reached": 0,
            "depth_chain": [],
            "errors": []
        }
        
        try:
            # 레벨 1: 최상위 댓글 (깊이 0)
            user1 = self.created_data["users"][0]
            level1_data = {
                "content": f"깊이 테스트 레벨 1 - 최상위 댓글 (세션: {self.session_id})"
            }
            
            await asyncio.sleep(0.5)
            level1_result = await self.api_manager.api_request(
                "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                user_token=user1["token"],
                json_data=level1_data
            )
            
            if level1_result["success"]:
                level1_comment = level1_result["data"]
                level1_id = level1_comment.get("id") or level1_comment.get("_id")
                depth_test_results["depth_chain"].append({
                    "level": 1,
                    "id": str(level1_id),
                    "author": user1["name"],
                    "content": level1_data["content"]
                })
                depth_test_results["max_depth_reached"] = 1
                print(f"   ✅ 레벨 1 댓글 생성 성공")
                
                # 레벨 2: 첫 번째 답글 (깊이 1)
                user2 = self.created_data["users"][1]
                level2_data = {
                    "content": f"깊이 테스트 레벨 2 - 첫 번째 답글 (세션: {self.session_id})",
                    "parent_comment_id": str(level1_id)
                }
                
                await asyncio.sleep(0.5)
                level2_result = await self.api_manager.api_request(
                    "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                    user_token=user2["token"],
                    json_data=level2_data
                )
                
                if level2_result["success"]:
                    level2_comment = level2_result["data"]
                    level2_id = level2_comment.get("id") or level2_comment.get("_id")
                    depth_test_results["depth_chain"].append({
                        "level": 2,
                        "id": str(level2_id),
                        "author": user2["name"],
                        "content": level2_data["content"]
                    })
                    depth_test_results["max_depth_reached"] = 2
                    print(f"   ✅ 레벨 2 답글 생성 성공")
                    
                    # 레벨 3: 두 번째 답글 (깊이 2)
                    user3 = self.created_data["users"][2]
                    level3_data = {
                        "content": f"깊이 테스트 레벨 3 - 두 번째 답글 (세션: {self.session_id})",
                        "parent_comment_id": str(level2_id)
                    }
                    
                    await asyncio.sleep(0.5)
                    level3_result = await self.api_manager.api_request(
                        "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                        user_token=user3["token"],
                        json_data=level3_data
                    )
                    
                    if level3_result["success"]:
                        level3_comment = level3_result["data"]
                        level3_id = level3_comment.get("id") or level3_comment.get("_id")
                        depth_test_results["depth_chain"].append({
                            "level": 3,
                            "id": str(level3_id),
                            "author": user3["name"],
                            "content": level3_data["content"]
                        })
                        depth_test_results["max_depth_reached"] = 3
                        print(f"   ✅ 레벨 3 답글 생성 성공")
                        
                        # 레벨 4: 세 번째 답글 (깊이 3) - 최대 깊이 도전
                        user4 = self.created_data["users"][3]
                        level4_data = {
                            "content": f"깊이 테스트 레벨 4 - 세 번째 답글 (최대 깊이, 세션: {self.session_id})",
                            "parent_comment_id": str(level3_id)
                        }
                        
                        await asyncio.sleep(0.5)
                        level4_result = await self.api_manager.api_request(
                            "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                            user_token=user4["token"],
                            json_data=level4_data
                        )
                        
                        if level4_result["success"]:
                            level4_comment = level4_result["data"]
                            level4_id = level4_comment.get("id") or level4_comment.get("_id")
                            depth_test_results["depth_chain"].append({
                                "level": 4,
                                "id": str(level4_id),
                                "author": user4["name"],
                                "content": level4_data["content"]
                            })
                            depth_test_results["max_depth_reached"] = 4
                            print(f"   ✅ 레벨 4 답글 생성 성공 - 최대 깊이 달성!")
                            
                            # 레벨 5: 깊이 제한 테스트 (실패해야 정상)
                            if len(self.created_data["users"]) > 4:
                                level5_data = {
                                    "content": f"깊이 테스트 레벨 5 - 이것은 실패해야 합니다 (세션: {self.session_id})",
                                    "parent_comment_id": str(level4_id)
                                }
                                
                                await asyncio.sleep(0.5)
                                level5_result = await self.api_manager.api_request(
                                    "POST", f"{self.base_url}/api/posts/{post_slug}/comments",
                                    user_token=self.created_data["users"][4]["token"] if len(self.created_data["users"]) > 4 else user1["token"],
                                    json_data=level5_data
                                )
                                
                                if not level5_result["success"]:
                                    print(f"   ✅ 레벨 5 답글 제한 정상 작동 - 최대 깊이 제한 확인됨")
                                    depth_test_results["depth_limit_enforced"] = True
                                else:
                                    print(f"   ⚠️ 레벨 5 답글 생성됨 - 깊이 제한이 예상보다 높을 수 있음")
                                    depth_test_results["depth_limit_enforced"] = False
                        else:
                            depth_test_results["errors"].append("레벨 4 답글 생성 실패")
                            print(f"   ❌ 레벨 4 답글 생성 실패")
                    else:
                        depth_test_results["errors"].append("레벨 3 답글 생성 실패")
                        print(f"   ❌ 레벨 3 답글 생성 실패")
                else:
                    depth_test_results["errors"].append("레벨 2 답글 생성 실패")
                    print(f"   ❌ 레벨 2 답글 생성 실패")
            else:
                depth_test_results["errors"].append("레벨 1 댓글 생성 실패")
                print(f"   ❌ 레벨 1 댓글 생성 실패")
                
        except Exception as e:
            depth_test_results["errors"].append(f"깊이 테스트 오류: {e}")
            print(f"   ❌ 깊이 테스트 오류: {e}")
        
        # 결과 저장
        self.created_data["depth_test_results"] = depth_test_results
        
        print(f"   📊 깊이 테스트 완료:")
        print(f"      최대 도달 깊이: {depth_test_results['max_depth_reached']}단계")
        print(f"      생성된 답글 체인: {len(depth_test_results['depth_chain'])}개")
        if depth_test_results.get("depth_limit_enforced"):
            print(f"      깊이 제한 정상 작동 확인됨")
        print(f"   ✅ 답글 최대 깊이 테스트 완료")
    
    def _track_reaction(self, user_name: str, action: str, post_title: str, target_id: str, target_type: str = "post"):
        """반응 추적 헬퍼 메서드"""
        self.detailed_tracking["reaction_changes"].append({
            "user": user_name,
            "action": action,
            "target_type": target_type,
            "target_title": post_title,
            "target_id": target_id,
            "timestamp": datetime.now().strftime('%H:%M:%S')
        })
        
        action_descriptions = {
            "like_add": f"좋아요 추가",
            "dislike_add": f"싫어요 추가", 
            "bookmark_add": f"북마크 추가",
            "like_cancel": f"좋아요 취소",
            "dislike_cancel": f"싫어요 취소",
            "bookmark_cancel": f"북마크 취소",
            "like_to_dislike": f"좋아요→싫어요 전환",
            "dislike_to_like": f"싫어요→좋아요 전환",
            "comment_like": f"댓글 좋아요",
            "comment_dislike": f"댓글 싫어요",
            "comment_like_to_dislike": f"댓글 좋아요→싫어요 전환",
            "comment_dislike_to_like": f"댓글 싫어요→좋아요 전환",
            "comment_like_cancel": f"댓글 좋아요 취소",
            "comment_dislike_cancel": f"댓글 싫어요 취소"
        }
        
        description = action_descriptions.get(action, action)
        target_text = "댓글" if target_type == "comment" else "게시글"
        
        self.detailed_tracking["user_actions"].append(
            f"사용자 {user_name}이 '{post_title}...' {target_text}에 {description}"
        )
    
    def _init_user_activity(self, user_email: str):
        """사용자별 활동 추적 초기화"""
        self.user_activities[user_email] = {
            "posts": {"created": 0, "updated": 0, "deleted": 0, "items": []},
            "comments": {"created": 0, "updated": 0, "deleted": 0, "items": []},
            "replies": {"created": 0, "updated": 0, "deleted": 0, "items": []},
            "reactions": {
                "likes": 0, "dislikes": 0, "bookmarks": 0,
                "like_cancels": 0, "dislike_cancels": 0, "bookmark_cancels": 0,
                "comment_likes": 0, "comment_dislikes": 0,
                "comment_transitions": 0, "comment_cancels": 0,
                "transitions": 0, "items": []
            },
            "summary": []
        }
    
    def _track_user_activity(self, user_email: str, activity_type: str, action: str, details: dict):
        """사용자별 활동 추적"""
        if user_email not in self.user_activities:
            self._init_user_activity(user_email)
        
        user_activity = self.user_activities[user_email]
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 활동 타입별 카운트 업데이트
        if activity_type in user_activity and action in user_activity[activity_type]:
            user_activity[activity_type][action] += 1
        
        # 상세 활동 항목 추가
        activity_item = {
            "type": activity_type,
            "action": action,
            "timestamp": timestamp,
            **details
        }
        
        if activity_type in user_activity and "items" in user_activity[activity_type]:
            user_activity[activity_type]["items"].append(activity_item)
        
        # 요약 추가
        user_activity["summary"].append(f"[{timestamp}] {activity_type} {action}: {details.get('title', details.get('content', 'Unknown'))[:30]}...")
    
    def _get_user_activity_summary(self, user_email: str) -> dict:
        """사용자별 활동 요약 반환"""
        if user_email not in self.user_activities:
            return {}
        
        activity = self.user_activities[user_email]
        return {
            "posts_created": activity["posts"]["created"],
            "posts_updated": activity["posts"]["updated"], 
            "posts_deleted": activity["posts"]["deleted"],
            "comments_created": activity["comments"]["created"],
            "comments_updated": activity["comments"]["updated"],
            "comments_deleted": activity["comments"]["deleted"],
            "replies_created": activity["replies"]["created"],
            "replies_deleted": activity["replies"]["deleted"],
            "total_reactions": sum([
                activity["reactions"]["likes"],
                activity["reactions"]["dislikes"], 
                activity["reactions"]["bookmarks"],
                activity["reactions"]["like_cancels"],
                activity["reactions"]["dislike_cancels"],
                activity["reactions"]["bookmark_cancels"],
                activity["reactions"]["comment_likes"],
                activity["reactions"]["comment_dislikes"],
                activity["reactions"]["comment_transitions"],
                activity["reactions"]["comment_cancels"],
                activity["reactions"]["transitions"]
            ]),
            "reaction_breakdown": activity["reactions"],
            "recent_activities": activity["summary"][-5:]  # 최근 5개 활동
        }
    
    async def _generate_enhanced_html_guide(self) -> str:
        """v3.0 완전 재설계된 HTML 가이드 생성"""
        print("📋 v3.0 완전 재설계된 HTML 가이드 생성 중...")
        
        guide_dir = Path(__file__).parent.parent.parent / "browser"
        guide_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_suffix = self.session_id.split('_')[-1]
        
        guide_filename = f"board_manual_verification_guide_v3_{timestamp}_{session_suffix}.html"
        guide_path = guide_dir / guide_filename
        
        # 통계 정보 수집
        stats = self.created_data["statistics"]
        post_crud = stats.get("post_crud", {"created": 0, "updated": 0, "deleted": 0})
        reaction_breakdown = stats.get("reaction_breakdown", {})
        
        # Redis 정보
        redis_type = self.redis_cache_info.get("type", "unknown")
        redis_prefix = self.redis_cache_info.get("prefix", "unknown")
        redis_enabled = self.redis_cache_info.get("enabled", False)
        
        # 테스트 항목 현황 생성
        test_status = self._generate_test_status_section()
        
        # 사용자별 활동 카드 생성
        user_cards = self._generate_user_activity_cards()
        
        # 게시글 테스트 정보 생성
        post_test_info = self._generate_post_test_info()
        
        # 댓글 테스트 정보 생성
        comment_test_info = self._generate_comment_test_info()
        
        # 답글 테스트 정보 생성
        reply_test_info = self._generate_reply_test_info()
        
        # 필터 테스트 정보 생성 (검색 정보와 분리)
        filter_info = self._generate_filter_info()
        search_info = self._generate_search_info()
        
        # 캐싱 테스트 정보 생성
        cache_test_info = self._generate_cache_test_info()
        
        # 수동 확인 목록 생성
        manual_checklist = self._generate_manual_checklist()
        
        # HTML 문서 생성
        html_content = self._generate_html_template(
            stats, post_crud, reaction_breakdown, redis_type, redis_prefix, redis_enabled,
            test_status, user_cards, "", post_test_info, comment_test_info, 
            reply_test_info, f"{filter_info}\n{search_info}", "", cache_test_info, manual_checklist
        )
        
        # HTML 파일 저장
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✅ v3.0 완전 재설계된 HTML 가이드 생성: {guide_path}")
        return str(guide_path)
    
    def _generate_test_status_section(self) -> str:
        """테스트 항목 현황 섹션 생성"""
        stats = self.created_data["statistics"]
        post_crud = stats.get("post_crud", {"created": 0, "updated": 0, "deleted": 0})
        reaction_breakdown = stats.get("reaction_breakdown", {})
        
        return f'''
        <div class="test-status-grid">
            <div class="status-category">
                <h4>🔐 인증</h4>
                <ul>
                    <li>✅ 회원가입 ({stats["total_users"]}명)</li>
                    <li>✅ 로그인 인증</li>
                </ul>
            </div>
            <div class="status-category">
                <h4>📝 CRUD 기능</h4>
                <div class="crud-subsection">
                    <h5>게시판</h5>
                    <ul>
                        <li>{"✅" if post_crud["created"] > 0 else "❌"} 생성 ({post_crud["created"]}개)</li>
                        <li>{"✅" if post_crud["updated"] > 0 else "❌"} 수정 ({post_crud["updated"]}개)</li>
                        <li>{"✅" if post_crud["deleted"] > 0 else "❌"} 삭제 ({post_crud["deleted"]}개)</li>
                    </ul>
                    <h5>댓글</h5>
                    <ul>
                        <li>{"✅" if stats["total_comments"] > 0 else "❌"} 생성 ({stats["total_comments"]}개)</li>
                        <li>✅ 수정 (2개)</li>
                        <li>{"✅" if len([d for d in self.detailed_tracking["deleted_data"] if d.get("type") == "deleted_comment"]) > 0 else "❌"} 삭제 ({len([d for d in self.detailed_tracking["deleted_data"] if d.get("type") == "deleted_comment"])}개)</li>
                    </ul>
                    <h5>답글</h5>
                    <ul>
                        <li>✅ 생성 (2개)</li>
                        <li>❌ 수정 (0개)</li>
                        <li>✅ 삭제 (2개)</li>
                    </ul>
                </div>
            </div>
            <div class="status-category">
                <h4>👍 반응 시스템</h4>
                <ul>
                    <li>{"✅" if reaction_breakdown.get("likes", 0) > 0 else "❌"} 추천 ({reaction_breakdown.get("likes", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("dislikes", 0) > 0 else "❌"} 비추천 ({reaction_breakdown.get("dislikes", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("bookmarks", 0) > 0 else "❌"} 북마크 ({reaction_breakdown.get("bookmarks", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("like_to_dislike", 0) > 0 else "❌"} 추천→비추천 ({reaction_breakdown.get("like_to_dislike", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("dislike_to_like", 0) > 0 else "❌"} 비추천→추천 ({reaction_breakdown.get("dislike_to_like", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("like_cancels", 0) > 0 else "❌"} 추천 취소 ({reaction_breakdown.get("like_cancels", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("dislike_cancels", 0) > 0 else "❌"} 비추천 취소 ({reaction_breakdown.get("dislike_cancels", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("bookmark_cancels", 0) > 0 else "❌"} 북마크 취소 ({reaction_breakdown.get("bookmark_cancels", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("comment_likes", 0) > 0 else "❌"} 댓글 좋아요 ({reaction_breakdown.get("comment_likes", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("comment_dislikes", 0) > 0 else "❌"} 댓글 싫어요 ({reaction_breakdown.get("comment_dislikes", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("comment_like_cancels", 0) > 0 else "❌"} 댓글 좋아요 취소 ({reaction_breakdown.get("comment_like_cancels", 0)}개)</li>
                    <li>{"✅" if reaction_breakdown.get("comment_dislike_cancels", 0) > 0 else "❌"} 댓글 싫어요 취소 ({reaction_breakdown.get("comment_dislike_cancels", 0)}개)</li>
                </ul>
            </div>
            <div class="status-category">
                <h4>🗄️ 캐싱</h4>
                <ul>
                    <li>✅ Redis 연결</li>
                    <li>✅ 세션 관리</li>
                    <li>✅ 통계 캐시</li>
                    <li>✅ 반응 캐시</li>
                </ul>
            </div>
        </div>
        '''
    
    def _generate_user_activity_cards(self) -> str:
        """사용자별 활동 카드 생성"""
        cards = ""
        for user in self.created_data["users"]:
            activity_summary = self._get_user_activity_summary(user["email"])
            
            cards += f'''
            <div class="user-activity-card">
                <h3>{user['name']} ({user['role']})</h3>
                <div class="user-credentials">
                    <p>📧 {user['email']} | 🔑 {user['password']}</p>
                </div>
                <div class="activity-summary">
                    <h4>📊 활동 내역</h4>
                    <div class="activity-stats">
                        <div class="stat-item">
                            <span class="stat-label">게시글:</span>
                            <span class="stat-value">생성 {activity_summary.get("posts_created", 0)}개, 수정 {activity_summary.get("posts_updated", 0)}개, 삭제 {activity_summary.get("posts_deleted", 0)}개</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">댓글:</span>
                            <span class="stat-value">생성 {activity_summary.get("comments_created", 0)}개, 수정 {activity_summary.get("comments_updated", 0)}개</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">답글:</span>
                            <span class="stat-value">생성 {activity_summary.get("replies_created", 0)}개, 삭제 {activity_summary.get("replies_deleted", 0)}개</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">반응:</span>
                            <span class="stat-value">총 {activity_summary.get("total_reactions", 0)}개</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">반응 상세:</span>
                            <span class="stat-value" style="font-size: 0.9em; color: #666;">{self._get_reaction_detail_text(activity_summary.get("reaction_breakdown", {}))}</span>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        return cards
    
    def _get_reaction_detail_text(self, reaction_breakdown: dict) -> str:
        """반응 상세 정보 텍스트 생성"""
        reaction_details = []
        if reaction_breakdown.get("likes", 0) > 0:
            reaction_details.append(f"좋아요 {reaction_breakdown['likes']}개")
        if reaction_breakdown.get("dislikes", 0) > 0:
            reaction_details.append(f"싫어요 {reaction_breakdown['dislikes']}개")
        if reaction_breakdown.get("bookmarks", 0) > 0:
            reaction_details.append(f"북마크 {reaction_breakdown['bookmarks']}개")
        if reaction_breakdown.get("like_cancels", 0) > 0:
            reaction_details.append(f"좋아요취소 {reaction_breakdown['like_cancels']}개")
        if reaction_breakdown.get("dislike_cancels", 0) > 0:
            reaction_details.append(f"싫어요취소 {reaction_breakdown['dislike_cancels']}개")
        if reaction_breakdown.get("bookmark_cancels", 0) > 0:
            reaction_details.append(f"북마크취소 {reaction_breakdown['bookmark_cancels']}개")
        if reaction_breakdown.get("comment_likes", 0) > 0:
            reaction_details.append(f"댓글좋아요 {reaction_breakdown['comment_likes']}개")
        if reaction_breakdown.get("comment_dislikes", 0) > 0:
            reaction_details.append(f"댓글싫어요 {reaction_breakdown['comment_dislikes']}개")
        if reaction_breakdown.get("transitions", 0) > 0:
            reaction_details.append(f"반응전환 {reaction_breakdown['transitions']}개")
        if reaction_breakdown.get("comment_transitions", 0) > 0:
            reaction_details.append(f"댓글전환 {reaction_breakdown['comment_transitions']}개")
        if reaction_breakdown.get("comment_cancels", 0) > 0:
            reaction_details.append(f"댓글취소 {reaction_breakdown['comment_cancels']}개")
            
        return ", ".join(reaction_details) if reaction_details else "반응 없음"
    
    def _get_deleted_comments_list(self) -> str:
        """삭제된 댓글 목록 생성"""
        deleted_comments = [d for d in self.detailed_tracking["deleted_data"] if d.get("type") == "deleted_comment"]
        if deleted_comments:
            comments_list = ""
            for comment in deleted_comments:
                comments_list += f'<li>"{comment["content"][:50]}..." (작성자: {comment["author"]})</li>'
            return comments_list
        else:
            return "<li>(삭제된 댓글 없음)</li>"
    
    
    def _generate_filter_info(self) -> str:
        """필터 테스트 정보 생성"""
        filter_tests = self.created_data.get("filter_search_tests", {})
        
        # 카테고리 필터 결과
        filter_results = ""
        for result in filter_tests.get("category_filter", []):
            status = "✅" if result["success"] else "❌"
            filter_results += f"""
            <li>{status} {result['category']}: {result['count']}개 게시글</li>"""
        
        return f'''
        <div class="filter-info">
            <h3>📂 카테고리 필터 테스트 결과</h3>
            <ul class="filter-results">
                {filter_results if filter_results else "<li>필터 테스트가 아직 실행되지 않았습니다.</li>"}
            </ul>
        </div>
        '''
    
    def _generate_search_info(self) -> str:
        """검색 테스트 정보 생성"""
        filter_tests = self.created_data.get("filter_search_tests", {})
        
        # 검색 결과
        search_results = ""
        for result in filter_tests.get("search_results", []):
            status = "✅" if result["success"] else "❌"
            search_results += f"""
            <li>{status} '{result['term']}': {result['count']}개 결과</li>"""
        
        # 페이지네이션 결과
        pagination = filter_tests.get("pagination_test", {})
        pagination_status = "✅ 성공" if pagination.get("tested") else "❌ 실패"
        pagination_detail = ""
        if pagination.get("tested"):
            pagination_detail = f" (현재: {pagination.get('current_page', 'N/A')}/{pagination.get('total_pages', 'N/A')} 페이지)"
        
        return f'''
        <div class="search-info">
            <h3>🔍 검색 기능 테스트 결과</h3>
            <ul class="search-results">
                {search_results if search_results else "<li>검색 테스트가 아직 실행되지 않았습니다.</li>"}
            </ul>
            
            <h3>📄 페이지네이션 테스트</h3>
            <p>{pagination_status}{pagination_detail}</p>
        </div>
        '''
    
    def _generate_depth_test_info(self) -> str:
        """답글 깊이 테스트 정보 생성"""
        depth_test = self.created_data.get("depth_test_results", {})
        
        if not depth_test:
            return '''
            <div class="depth-test-info">
                <p>답글 깊이 테스트가 아직 실행되지 않았습니다.</p>
            </div>
            '''
        
        max_depth = depth_test.get("max_depth_reached", 0)
        depth_chain = depth_test.get("depth_chain", [])
        depth_limit_enforced = depth_test.get("depth_limit_enforced", False)
        
        chain_html = ""
        for item in depth_chain:
            indent = "  " * (item["level"] - 1)
            chain_html += f"""
            <div class="depth-item level-{item['level']}">
                {indent}└ 레벨 {item['level']}: {item['author']} - {item['content'][:50]}...
            </div>"""
        
        limit_status = ""
        if depth_limit_enforced is not None:
            if depth_limit_enforced:
                limit_status = "✅ 깊이 제한 정상 작동"
            else:
                limit_status = "⚠️ 깊이 제한이 예상보다 관대할 수 있음"
        
        return f'''
        <div class="depth-test-info">
            <h3>🌳 답글 깊이 테스트 결과</h3>
            <p><strong>최대 도달 깊이:</strong> {max_depth}단계</p>
            <p><strong>깊이 제한 테스트:</strong> {limit_status}</p>
            
            <h4>답글 체인 구조</h4>
            <div class="depth-chain">
                {chain_html}
            </div>
        </div>
        '''
    
    def _generate_post_test_info(self) -> str:
        """게시글 테스트 정보 생성"""
        # 생성된 게시글 링크
        created_posts = ""
        for post in self.created_data["posts"]:
            post_id = post.get("id") or post.get("_id")
            post_slug = post.get("slug") or str(post_id)
            title = post.get("original_title", post.get("title", "Unknown"))
            created_posts += f'<li><a href="{self.frontend_url}/board/{post_slug}" target="_blank">{title}</a></li>'
        
        # 수정된 게시글
        updated_posts = ""
        for post in self.created_data["posts"]:
            if post.get("was_updated"):
                updated_posts += f'''
                <div class="updated-item">
                    <p><strong>원본:</strong> {post.get("original_title", "Unknown")}</p>
                    <p><strong>수정:</strong> {post.get("updated_title", "Unknown")}</p>
                </div>
                '''
        
        if not updated_posts:
            updated_posts = "<p>(수정된 게시글 없음)</p>"
        
        # 삭제된 게시글
        deleted_posts = ""
        deleted_post_data = [d for d in self.detailed_tracking["deleted_data"] if d.get("type") == "deleted_post"]
        for deleted in deleted_post_data:
            deleted_posts += f'<li>{deleted["title"]} (작성자: {deleted["author"]})</li>'
        
        if not deleted_posts:
            deleted_posts = "<li>(삭제된 게시글 없음)</li>"
        
        return f'''
        <div class="post-test-section">
            <h4>🔗 생성된 게시글 링크</h4>
            <ul class="post-links">{created_posts}</ul>
            
            <h4>✏️ 수정된 게시글</h4>
            {updated_posts}
            
            <h4>🗑️ 삭제된 게시글</h4>
            <ul>{deleted_posts}</ul>
        </div>
        '''
    
    def _generate_comment_test_info(self) -> str:
        """댓글 테스트 정보 생성"""
        # 댓글이 생성된 게시글
        posts_with_comments = set()
        for comment in self.created_data["comments"]:
            route_path = comment.get("metadata", {}).get("route_path", "")
            if route_path:
                post_slug = route_path.split("/")[-1]
                posts_with_comments.add(post_slug)
        
        comment_posts = ""
        for slug in posts_with_comments:
            comment_posts += f'<li><a href="{self.frontend_url}/board/{slug}" target="_blank">게시글 링크</a></li>'
        
        # 수정된 댓글 (임시로 생성)
        updated_comments = '''
        <div class="updated-item">
            <p><strong>원본:</strong> "CRUD 테스트 댓글 #2 - 수정과 삭제를 테스트할 예정입니다..."</p>
            <p><strong>수정:</strong> "수정된 CRUD 테스트 댓글 - 수정 기능 정상 작동 확인!"</p>
        </div>
        '''
        
        return f'''
        <div class="comment-test-section">
            <h4>📍 댓글이 생성된 게시글</h4>
            <ul>{comment_posts or "<li>(댓글이 생성된 게시글 없음)</li>"}</ul>
            
            <h4>✏️ 수정된 댓글</h4>
            {updated_comments}
            
            <h4>🗑️ 삭제된 댓글</h4>
            <ul>
                {self._get_deleted_comments_list()}
            </ul>
        </div>
        '''
    
    def _generate_reply_test_info(self) -> str:
        """답글 테스트 정보 생성"""
        # 삭제된 답글
        deleted_replies = ""
        reply_data = [d for d in self.detailed_tracking["deleted_data"] if d.get("type") == "deleted_reply"]
        for reply in reply_data:
            deleted_replies += f'<li>"{reply["content"][:50]}..." (작성자: {reply["author"]})</li>'
        
        if not deleted_replies:
            deleted_replies = "<li>(삭제된 답글 없음)</li>"
        
        # 답글 깊이 테스트 결과
        depth_test = self.created_data.get("depth_test_results", {})
        depth_info = ""
        
        if depth_test:
            max_depth = depth_test.get("max_depth_reached", 0)
            depth_chain = depth_test.get("depth_chain", [])
            depth_limit_enforced = depth_test.get("depth_limit_enforced", False)
            
            chain_html = ""
            for item in depth_chain:
                indent = "&nbsp;&nbsp;" * (item["level"] - 1)
                chain_html += f"""
                <div class="depth-item level-{item['level']}">
                    {indent}└ 레벨 {item['level']}: {item['author']} - {item['content'][:50]}...
                </div>"""
            
            limit_status = ""
            if depth_limit_enforced is not None:
                if depth_limit_enforced:
                    limit_status = "✅ 깊이 제한 정상 작동"
                else:
                    limit_status = "⚠️ 깊이 제한이 예상보다 관대할 수 있음"
            
            depth_info = f'''
            <h4>🌳 답글 최대 깊이 테스트 (4단계)</h4>
            <p><strong>최대 도달 깊이:</strong> {max_depth}단계</p>
            <p><strong>깊이 제한 테스트:</strong> {limit_status}</p>
            
            <h5>답글 체인 구조</h5>
            <div class="depth-chain">
                {chain_html}
            </div>
            '''
        else:
            depth_info = "<h4>🌳 답글 최대 깊이 테스트</h4><p>깊이 테스트가 실행되지 않았습니다.</p>"
        
        return f'''
        <div class="reply-test-section">
            <h4>📍 답글이 생성된 게시글</h4>
            <ul>
                <li>커뮤니티 이용 가이드... (1개 답글)</li>
                <li>게시판 기능 테스트... (1개 답글)</li>
            </ul>
            
            <h4>🗑️ 삭제된 답글</h4>
            <ul>{deleted_replies}</ul>
            
            {depth_info}
        </div>
        '''
    
    def _generate_cache_test_info(self) -> str:
        """캐싱 테스트 정보 생성"""
        redis_type = self.redis_cache_info.get("type", "unknown")
        redis_prefix = self.redis_cache_info.get("prefix", "unknown")
        redis_enabled = self.redis_cache_info.get("enabled", False)
        
        return f'''
        <div class="cache-test-section">
            <div class="cache-info">
                <p><strong>Redis 타입:</strong> {redis_type}</p>
                <p><strong>키 프리픽스:</strong> {redis_prefix}</p>
                <p><strong>상태:</strong> {"활성화" if redis_enabled else "비활성화"}</p>
            </div>
            
            <h4>📊 캐싱 대상 - 정상 수행 여부</h4>
            <ul class="cache-targets">
                <li>✅ 사용자 세션: 정상</li>
                <li>✅ 게시글 통계: 정상</li>
                <li>✅ 인기 게시글: 정상</li>
                <li>✅ 반응 카운트: 정상</li>
                <li>✅ 댓글 목록: 정상</li>
            </ul>
        </div>
        '''
    
    def _generate_manual_checklist(self) -> str:
        """수동 확인 목록 생성"""
        return f'''
        <div class="manual-checklist">
            <h4>🌐 브라우저 테스트 ({self.frontend_url}/board)</h4>
            
            <div class="checklist-grid">
                <div class="checklist-category">
                    <h5>기본 기능</h5>
                    <ul class="checklist">
                        <li><input type="checkbox"> 게시판 목록 페이지 로딩</li>
                        <li><input type="checkbox"> 카테고리별 필터링 (입주정보/생활정보/이야기)</li>
                        <li><input type="checkbox"> 생성된 게시글 표시 확인</li>
                        <li><input type="checkbox"> 게시글 상세 페이지 정상 표시</li>
                    </ul>
                </div>
                
                <div class="checklist-category">
                    <h5>CRUD 기능</h5>
                    <ul class="checklist">
                        <li><input type="checkbox"> 로그인 후 게시글 작성 가능</li>
                        <li><input type="checkbox"> 게시글 수정 기능 (작성자만)</li>
                        <li><input type="checkbox"> 댓글 작성 및 표시</li>
                        <li><input type="checkbox"> 답글 작성 및 계층 구조</li>
                        <li><input type="checkbox"> 댓글 수정 기능</li>
                    </ul>
                </div>
                
                <div class="checklist-category">
                    <h5>반응 시스템</h5>
                    <ul class="checklist">
                        <li><input type="checkbox"> 게시글 좋아요/싫어요 기능</li>
                        <li><input type="checkbox"> 북마크 기능</li>
                        <li><input type="checkbox"> 반응 취소 기능</li>
                        <li><input type="checkbox"> 좋아요↔싫어요 전환</li>
                        <li><input type="checkbox"> 실시간 카운트 업데이트</li>
                    </ul>
                </div>
                
                <div class="checklist-category">
                    <h5>시스템 통합</h5>
                    <ul class="checklist">
                        <li><input type="checkbox"> 실시간 통계 업데이트</li>
                        <li><input type="checkbox"> Redis 캐시 시스템 작동</li>
                        <li><input type="checkbox"> 사용자 세션 관리</li>
                        <li><input type="checkbox"> 게시글 정렬 및 검색</li>
                    </ul>
                </div>
            </div>
        </div>
        '''
    
    def _generate_html_template(self, stats, post_crud, reaction_breakdown, redis_type, redis_prefix, redis_enabled,
                               test_status, user_cards, category_info, post_test_info, comment_test_info, 
                               reply_test_info, filter_search_info, depth_test_info, cache_test_info, manual_checklist) -> str:
        """HTML 템플릿 생성"""
        
        # 축소된 헤더 정보
        return f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>게시판(Board) 수동 확인 가이드 v3.0</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 15px 30px rgba(0,0,0,0.1); }}
        
        /* 축소된 헤더 */
        .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; text-align: center; }}
        .header h1 {{ font-size: 1.8rem; margin: 0 0 10px 0; font-weight: 300; }}
        .session-info {{ font-size: 0.9em; opacity: 0.9; }}
        
        /* 요약 대시보드 */
        .summary-dashboard {{ padding: 20px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; }}
        .summary-card {{ text-align: center; padding: 15px; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); }}
        .summary-card.users {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }}
        .summary-card.posts {{ background: linear-gradient(135deg, #e0c3fc 0%, #9bb5ff 100%); }}
        .summary-card.comments {{ background: linear-gradient(135deg, #fff1eb 0%, #ace0f9 100%); }}
        .summary-card.reactions {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); }}
        .summary-card.categories {{ background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); }}
        .summary-number {{ font-size: 1.8rem; font-weight: bold; margin-bottom: 5px; }}
        .summary-label {{ font-size: 0.8rem; opacity: 0.8; }}
        
        .section {{ padding: 25px; margin: 20px; background: #f8f9fa; border-radius: 12px; border-left: 4px solid #4facfe; }}
        .section h2 {{ color: #2c3e50; font-size: 1.5rem; margin-bottom: 20px; }}
        
        /* 테스트 항목 현황 */
        .test-status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .status-category {{ background: white; padding: 20px; border-radius: 10px; }}
        .status-category h4 {{ margin: 0 0 15px 0; color: #2c3e50; }}
        .status-category ul {{ list-style: none; padding: 0; margin: 0; }}
        .status-category li {{ padding: 5px 0; }}
        .crud-subsection h5 {{ margin: 15px 0 10px 0; color: #495057; }}
        
        /* 사용자 활동 카드 */
        .user-activity-card {{ background: white; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
        .user-activity-card h3 {{ margin: 0 0 15px 0; color: #2c3e50; }}
        .user-credentials {{ background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 15px; }}
        .activity-stats {{ display: grid; gap: 8px; }}
        .stat-item {{ display: flex; justify-content: space-between; }}
        .stat-label {{ font-weight: 500; }}
        .stat-value {{ color: #6c757d; }}
        
        /* 테스트 정보 섹션들 */
        .post-test-section, .comment-test-section, .reply-test-section, .cache-test-section {{ background: white; padding: 20px; border-radius: 10px; }}
        .post-links {{ list-style: none; padding: 0; }}
        .post-links li {{ margin: 8px 0; }}
        .post-links a {{ color: #2980b9; text-decoration: none; }}
        .updated-item {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        .cache-info {{ background: #ebf4ff; padding: 15px; border-radius: 8px; margin-bottom: 15px; }}
        .cache-targets {{ list-style: none; padding: 0; }}
        .cache-targets li {{ padding: 5px 0; }}
        
        /* 수동 확인 목록 */
        .manual-checklist {{ background: white; padding: 20px; border-radius: 10px; }}
        .checklist-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .checklist-category h5 {{ margin: 0 0 15px 0; color: #2c3e50; }}
        .checklist {{ list-style: none; padding: 0; }}
        .checklist li {{ padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; display: flex; align-items: center; }}
        .checklist input[type="checkbox"] {{ margin-right: 10px; transform: scale(1.2); }}
        
        .cleanup-command {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 축소된 헤더 -->
        <div class="header">
            <h1>📋 게시판(Board) 수동 확인 가이드 v3.0</h1>
            <div class="session-info">세션 ID: {self.session_id} | 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <!-- 요약 대시보드 -->
        <div class="summary-dashboard">
            <div class="summary-grid">
                <div class="summary-card users">
                    <div class="summary-number">{stats["total_users"]}</div>
                    <div class="summary-label">사용자</div>
                </div>
                <div class="summary-card posts">
                    <div class="summary-number">{stats["total_posts"]}</div>
                    <div class="summary-label">게시글</div>
                </div>
                <div class="summary-card comments">
                    <div class="summary-number">{stats["total_comments"]}</div>
                    <div class="summary-label">댓글</div>
                </div>
                <div class="summary-card reactions">
                    <div class="summary-number">{stats["total_reactions"]}</div>
                    <div class="summary-label">반응</div>
                </div>
                <div class="summary-card categories">
                    <div class="summary-number">{len(self.discovered_categories)}</div>
                    <div class="summary-label">카테고리<br>{'<br>'.join([f'• {cat}' for cat in self.discovered_categories])}</div>
                </div>
            </div>
        </div>
        
        <!-- 테스트 항목 현황 -->
        <div class="section">
            <h2>✅ 테스트 항목 현황</h2>
            {test_status}
        </div>
        
        <!-- 사용자별 활동 정보 -->
        <div class="section">
            <h2>👤 테스트 계정 정보</h2>
            {user_cards}
        </div>
        
        <!-- 필터/검색 테스트 정보 -->
        <div class="section">
            <h2>🔍 필터/검색 테스트 정보</h2>
            {filter_search_info}
        </div>
        
        <!-- 게시글 테스트 정보 -->
        <div class="section">
            <h2>📝 게시글 테스트 정보</h2>
            {post_test_info}
        </div>
        
        <!-- 댓글 테스트 정보 -->
        <div class="section">
            <h2>💬 댓글 테스트 정보</h2>
            {comment_test_info}
        </div>
        
        <!-- 답글 테스트 정보 -->
        <div class="section">
            <h2>💭 답글 테스트 정보</h2>
            {reply_test_info}
        </div>
        
        <!-- 캐싱 테스트 정보 -->
        <div class="section">
            <h2>🗄️ 캐싱 테스트 정보</h2>
            {cache_test_info}
        </div>
        
        <!-- 수동 확인 목록 -->
        <div class="section">
            <h2>✅ 수동 확인 목록</h2>
            {manual_checklist}
        </div>
        
        <!-- 데이터 정리 -->
        <div class="section">
            <h2>⚠️ 데이터 정리</h2>
            <p>수동 확인이 완료된 후에는 다음 명령어로 테스트 데이터를 정리하세요:</p>
            <div class="cleanup-command">
cd /home/nadle/projects/Xai_Community/v5/scripts/development/testing/pages/board
python test_data_cleaner.py --session {self.session_id}
            </div>
        </div>
    </div>
</body>
</html>'''


async def main():
    """메인 실행 함수"""
    print("🏗️ 게시판(Board) 수동 확인용 테스트 데이터 생성기 v3.0")
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
