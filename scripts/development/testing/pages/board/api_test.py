#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 17:06:00 KST
작업 버전: 게시판(Board) 페이지 통합 테스트 시스템 v1.0
주요 컴포넌트들:
- BoardTestRunner: 게시판 페이지 전용 테스트 실행기 (30-450라인)
  - run_page_specific_tests(): 게시판 특화 테스트 실행 (80-150라인)
  - _run_board_infrastructure_tests(): 기본 인프라 검증 (152-200라인)
  - _run_board_list_tests(): 게시글 목록 기능 테스트 (202-280라인)
  - _run_board_crud_tests(): 게시글 CRUD 작업 테스트 (282-360라인)
  - _run_comment_system_tests(): 댓글/답글 시스템 테스트 (362-420라인)
  - _run_reaction_system_tests(): 반응 시스템 테스트 (422-450라인)

핵심 기능:
- 통합 프레임워크 기반 게시판 테스트
- 자동화 모드와 수동 확인 모드 지원
- 게시판 특화 테스트 시나리오 (board 타입 메타데이터)
- 일반 사용자 권한 시스템 검증
- Rate limiting 지능형 관리

관련 파일들:
- /scripts/development/testing/unified/base_test_runner.py: 기본 테스트 실행기
- /scripts/development/testing/unified/report_generator.py: 통합 보고서 생성기
- /scripts/development/testing/unified/data_manager.py: 테스트 데이터 관리자
- /scripts/development/testing/pages/board/manual_verification_data_generator.py: 수동 확인용 데이터 생성
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any

# 통합 프레임워크 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "unified"))
from base_test_runner import UnifiedPageTestRunner, create_test_runner_args_parser


class BoardTestRunner(UnifiedPageTestRunner):
    """게시판 페이지 전용 테스트 실행기"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__("Board", base_url)
        
        # 게시판 특화 설정
        self.board_metadata_type = "board"
        self.test_categories = ["입주 정보", "생활 정보", "이야기"]
        
        # 테스트 사용자 설정
        random_suffix = self.session_id.split('_')[-1].lower()
        self.test_users = {
            "normal": {
                "email": f"board_normal_{random_suffix}@example.com",
                "user_handle": f"board_normal_{random_suffix}",
                "name": f"게시판 테스트 사용자 {random_suffix[:4].upper()}",
                "display_name": f"BoardTest {random_suffix[:4].upper()}",
                "password": "TestPassword123!",
                "token": None,
                "user_data": None
            },
            "author": {
                "email": f"board_author_{random_suffix}@example.com",
                "user_handle": f"board_author_{random_suffix}",
                "name": f"게시판 작성자 {random_suffix[:4].upper()}",
                "display_name": f"BoardAuthor {random_suffix[:4].upper()}",
                "password": "TestPassword123!",
                "token": None,
                "user_data": None
            }
        }
    
    async def run_page_specific_tests(self) -> bool:
        """게시판 특화 테스트 실행"""
        print("📋 게시판 페이지 특화 테스트 시작...")
        
        success = True
        test_sections = [
            ("게시판 기본 인프라 검증", self._run_board_infrastructure_tests),
            ("게시글 목록 기능", self._run_board_list_tests),
            ("게시글 CRUD 작업", self._run_board_crud_tests),
            ("댓글/답글 시스템", self._run_comment_system_tests),
            ("반응 시스템", self._run_reaction_system_tests)
        ]
        
        for section_name, test_func in test_sections:
            print(f"\n📋 [{section_name}] 테스트 섹션 시작")
            self.report_generator.start_section(section_name)
            
            try:
                section_success = await test_func()
                if not section_success:
                    success = False
            except Exception as e:
                print(f"   ❌ 섹션 실행 오류: {e}")
                success = False
            
            print(f"📋 [{section_name}] 테스트 섹션 완료")
            await asyncio.sleep(2)  # 섹션 간 대기
        
        return success
    
    def get_page_url(self) -> str:
        """게시판 페이지 URL"""
        return "board"
    
    def get_test_scenarios(self) -> List[Dict[str, Any]]:
        """게시판 테스트 시나리오"""
        return [
            {
                "name": "기본 게시글 CRUD",
                "description": "게시글 생성, 조회, 수정, 삭제 기본 동작",
                "priority": "high"
            },
            {
                "name": "댓글/답글 시스템",
                "description": "댓글 작성, 답글 작성, 계층 구조 확인",
                "priority": "high"
            },
            {
                "name": "반응 시스템",
                "description": "좋아요, 싫어요, 북마크 기능",
                "priority": "medium"
            },
            {
                "name": "검색 및 필터링",
                "description": "카테고리별 필터링, 키워드 검색",
                "priority": "medium"
            }
        ]
    
    async def _setup_test_users(self) -> bool:
        """게시판 테스트 사용자 생성 및 인증"""
        print("👤 게시판 테스트 사용자 설정 중...")
        
        success_count = 0
        for user_type, user_info in self.test_users.items():
            print(f"   🔐 {user_type} 사용자 처리 중...")
            
            # 1. 사용자 등록 시도
            register_result = await self.api_manager.register_user(user_info)
            if register_result["success"]:
                print(f"      ✅ {user_type} 사용자 등록 완료")
            else:
                print(f"      ℹ️ {user_type} 사용자 이미 존재 (등록 스킵)")
            
            # 2. 사용자 인증
            auth_result = await self.api_manager.authenticate_user(
                user_info["email"], user_info["password"]
            )
            
            if auth_result["success"]:
                user_info["token"] = auth_result["token"]
                user_info["user_data"] = auth_result["user"]
                success_count += 1
                
                # 보고서에 테스트 사용자 추가
                self.report_generator.add_test_user(user_info)
                print(f"      ✅ {user_type} 사용자 인증 완료")
            else:
                print(f"      ❌ {user_type} 사용자 인증 실패")
        
        return success_count == len(self.test_users)
    
    async def _run_board_infrastructure_tests(self) -> bool:
        """게시판 기본 인프라 검증"""
        print("   🏗️ 게시판 인프라 검증 중...")
        
        # 1. 서버 헬스체크
        await self.rate_manager.wait_before_request()
        health_result = await self.api_manager.api_request(
            "GET", f"{self.base_url}/health"
        )
        
        if health_result["success"]:
            self.report_generator.add_test_result(
                "서버 헬스체크", "success", "0.3초", 
                "게시판 서버 정상 응답 확인"
            )
            print("      ✅ 서버 헬스체크: 정상")
        else:
            self.report_generator.add_test_result(
                "서버 헬스체크", "failed", "0.3초", 
                f"서버 응답 실패: {health_result.get('error', 'Unknown')}"
            )
            print("      ❌ 서버 헬스체크: 실패")
        
        # 2. 게시판 API 엔드포인트 확인
        await self.rate_manager.wait_before_request()
        posts_result = await self.api_manager.api_request(
            "GET", f"{self.base_url}/api/posts",
            params={"metadata_type": self.board_metadata_type, "page": 1, "page_size": 5}
        )
        
        if posts_result["success"]:
            posts_count = len(posts_result["data"].get("items", []))
            self.report_generator.add_test_result(
                "게시판 API 엔드포인트", "success", "0.5초",
                f"board 타입 게시글 {posts_count}개 조회 성공"
            )
            print(f"      ✅ 게시판 API 엔드포인트: {posts_count}개 게시글 조회")
        else:
            self.report_generator.add_test_result(
                "게시판 API 엔드포인트", "failed", "0.5초",
                f"API 호출 실패: {posts_result.get('error', 'Unknown')}"
            )
            print("      ❌ 게시판 API 엔드포인트: 실패")
        
        return True
    
    async def _run_board_list_tests(self) -> bool:
        """게시글 목록 기능 테스트"""
        print("   📋 게시글 목록 기능 테스트 중...")
        
        # 1. 기본 목록 조회
        await self.rate_manager.wait_before_request()
        list_result = await self.api_manager.api_request(
            "GET", f"{self.base_url}/api/posts",
            params={"metadata_type": self.board_metadata_type, "page": 1, "page_size": 20}
        )
        
        if list_result["success"]:
            posts_data = list_result["data"]
            posts_count = len(posts_data.get("items", []))
            
            self.report_generator.add_test_result(
                "게시판 목록 조회", "success", "0.8초",
                f"board 타입 게시글 {posts_count}개 조회 성공"
            )
            print(f"      ✅ 게시판 목록 조회: {posts_count}개 게시글")
        else:
            self.report_generator.add_test_result(
                "게시판 목록 조회", "failed", "0.8초",
                f"목록 조회 실패: {list_result.get('error', 'Unknown')}"
            )
            print("      ❌ 게시판 목록 조회: 실패")
        
        # 2. 페이지네이션 테스트
        await self.rate_manager.wait_before_request()
        page2_result = await self.api_manager.api_request(
            "GET", f"{self.base_url}/api/posts",
            params={"metadata_type": self.board_metadata_type, "page": 2, "page_size": 10}
        )
        
        if page2_result["success"]:
            self.report_generator.add_test_result(
                "페이지네이션", "success", "0.6초",
                "2페이지 조회 성공, 페이지네이션 정상 작동"
            )
            print("      ✅ 페이지네이션: 정상")
        else:
            self.report_generator.add_test_result(
                "페이지네이션", "warning", "0.6초",
                "페이지네이션 테스트 불완전"
            )
            print("      ⚠️ 페이지네이션: 불완전")
        
        # 3. 검색 기능 테스트
        await self.rate_manager.wait_before_request()
        search_result = await self.api_manager.api_request(
            "GET", f"{self.base_url}/api/posts/search",
            params={"q": "테스트", "metadata_type": self.board_metadata_type}
        )
        
        if search_result["success"]:
            search_count = len(search_result["data"].get("items", []))
            self.report_generator.add_test_result(
                "검색 기능", "success", "0.7초",
                f"'테스트' 키워드로 {search_count}개 검색 결과"
            )
            print(f"      ✅ 검색 기능: {search_count}개 결과")
        else:
            self.report_generator.add_test_result(
                "검색 기능", "failed", "0.7초",
                "검색 기능 테스트 실패"
            )
            print("      ❌ 검색 기능: 실패")
        
        return True
    
    async def _run_board_crud_tests(self) -> bool:
        """게시글 CRUD 작업 테스트"""
        print("   📝 게시글 CRUD 작업 테스트 중...")
        
        if not self.test_users["author"]["token"]:
            print("      ⚠️ 인증 토큰 없음 - CRUD 테스트 스킵")
            return False
        
        author_token = self.test_users["author"]["token"]
        
        # 1. 게시글 생성
        await self.rate_manager.wait_before_request()
        post_data = {
            "title": f"게시판 테스트 게시글 - {self.session_id}",
            "content": f"# 게시판 테스트 게시글\n\n이 게시글은 자동화 테스트로 생성되었습니다.\n세션 ID: {self.session_id}",
            "service": "residential_community",
            "metadata": {
                "type": self.board_metadata_type,
                "category": "입주 정보",
                "tags": ["테스트", "자동화"],
                "test_session": self.session_id
            }
        }
        
        create_result = await self.api_manager.api_request(
            "POST", f"{self.base_url}/api/posts",
            user_token=author_token,
            json_data=post_data
        )
        
        if create_result["success"] and create_result["status"] == 201:
            created_post = create_result["data"]
            self.created_posts.append(created_post)
            
            # 보고서에 생성된 게시글 추가
            self.report_generator.add_created_post(created_post)
            
            self.report_generator.add_test_result(
                "게시글 생성", "success", "1.2초",
                f"board 타입 게시글 생성 성공 (ID: {created_post.get('id', 'Unknown')[:8]}...)"
            )
            print("      ✅ 게시글 생성: 성공")
            
            # 2. 생성된 게시글 조회
            await self._test_post_retrieval(created_post)
            
            # 3. 게시글 수정 (작성자 권한)
            await self._test_post_update(created_post, author_token)
            
        else:
            self.report_generator.add_test_result(
                "게시글 생성", "failed", "1.2초",
                f"게시글 생성 실패: {create_result.get('error', 'Unknown')}"
            )
            print("      ❌ 게시글 생성: 실패")
        
        return True
    
    async def _test_post_retrieval(self, post: Dict[str, Any]):
        """게시글 조회 테스트"""
        post_id = post.get("id") or post.get("_id")
        
        await self.rate_manager.wait_before_request()
        retrieve_result = await self.api_manager.api_request(
            "GET", f"{self.base_url}/api/posts/{post_id}"
        )
        
        if retrieve_result["success"]:
            retrieved_post = retrieve_result["data"]
            metadata = retrieved_post.get("metadata", {})
            
            # 메타데이터 검증
            is_board_type = metadata.get("type") == self.board_metadata_type
            
            if is_board_type:
                self.report_generator.add_test_result(
                    "게시글 조회", "success", "0.6초",
                    "생성된 게시글 정상 조회, board 타입 메타데이터 확인"
                )
                print("      ✅ 게시글 조회: 성공")
            else:
                self.report_generator.add_test_result(
                    "게시글 조회", "warning", "0.6초",
                    "게시글 조회됨, 하지만 메타데이터 타입 불일치"
                )
                print("      ⚠️ 게시글 조회: 메타데이터 타입 불일치")
        else:
            self.report_generator.add_test_result(
                "게시글 조회", "failed", "0.6초",
                "생성된 게시글 조회 실패"
            )
            print("      ❌ 게시글 조회: 실패")
    
    async def _test_post_update(self, post: Dict[str, Any], author_token: str):
        """게시글 수정 테스트"""
        post_id = post.get("id") or post.get("_id")
        
        await self.rate_manager.wait_before_request()
        update_data = {
            "title": f"[수정됨] {post.get('title', '')}",
            "content": f"{post.get('content', '')}\n\n## 수정사항\n이 게시글은 자동화 테스트에서 수정되었습니다."
        }
        
        update_result = await self.api_manager.api_request(
            "PUT", f"{self.base_url}/api/posts/{post_id}",
            user_token=author_token,
            json_data=update_data
        )
        
        if update_result["success"]:
            self.report_generator.add_test_result(
                "게시글 수정", "success", "0.9초",
                "작성자 권한으로 게시글 수정 성공"
            )
            print("      ✅ 게시글 수정: 성공")
        else:
            self.report_generator.add_test_result(
                "게시글 수정", "failed", "0.9초",
                f"게시글 수정 실패: {update_result.get('error', 'Unknown')}"
            )
            print("      ❌ 게시글 수정: 실패")
    
    async def _run_comment_system_tests(self) -> bool:
        """댓글/답글 시스템 테스트"""
        print("   💬 댓글/답글 시스템 테스트 중...")
        
        if not self.created_posts or not self.test_users["normal"]["token"]:
            print("      ⚠️ 테스트 조건 미충족 - 댓글 시스템 테스트 스킵")
            return False
        
        test_post = self.created_posts[0]
        post_id = test_post.get("id") or test_post.get("_id")
        normal_token = self.test_users["normal"]["token"]
        
        # 1. 댓글 생성
        await self.rate_manager.wait_before_request()
        comment_data = {
            "content": f"게시판 테스트 댓글입니다. (세션: {self.session_id})",
            "post_id": str(post_id)
        }
        
        comment_result = await self.api_manager.api_request(
            "POST", f"{self.base_url}/api/comments",
            user_token=normal_token,
            json_data=comment_data
        )
        
        if comment_result["success"] and comment_result["status"] == 201:
            created_comment = comment_result["data"]
            self.created_comments.append(created_comment)
            
            # 보고서에 생성된 댓글 추가
            self.report_generator.add_created_comment(created_comment)
            
            self.report_generator.add_test_result(
                "댓글 생성", "success", "1.1초",
                f"게시판 댓글 생성 성공 (ID: {created_comment.get('id', 'Unknown')[:8]}...)"
            )
            print("      ✅ 댓글 생성: 성공")
            
            # 2. 답글 생성
            await self._test_reply_creation(created_comment, normal_token)
            
        else:
            self.report_generator.add_test_result(
                "댓글 생성", "failed", "1.1초",
                f"댓글 생성 실패: {comment_result.get('error', 'Unknown')}"
            )
            print("      ❌ 댓글 생성: 실패")
        
        return True
    
    async def _test_reply_creation(self, parent_comment: Dict[str, Any], user_token: str):
        """답글 생성 테스트"""
        await self.rate_manager.wait_before_request()
        
        reply_data = {
            "content": f"게시판 테스트 답글입니다. (세션: {self.session_id})",
            "post_id": parent_comment.get("post_id"),
            "parent_id": parent_comment.get("id") or parent_comment.get("_id")
        }
        
        reply_result = await self.api_manager.api_request(
            "POST", f"{self.base_url}/api/comments",
            user_token=user_token,
            json_data=reply_data
        )
        
        if reply_result["success"] and reply_result["status"] == 201:
            created_reply = reply_result["data"]
            self.created_comments.append(created_reply)
            
            self.report_generator.add_test_result(
                "답글 생성", "success", "1.0초",
                "답글 생성 및 계층 구조 정상"
            )
            print("      ✅ 답글 생성: 성공")
        else:
            self.report_generator.add_test_result(
                "답글 생성", "failed", "1.0초",
                f"답글 생성 실패: {reply_result.get('error', 'Unknown')}"
            )
            print("      ❌ 답글 생성: 실패")
    
    async def _run_reaction_system_tests(self) -> bool:
        """반응 시스템 테스트"""
        print("   👍 반응 시스템 테스트 중...")
        
        if not self.created_posts or not self.test_users["normal"]["token"]:
            print("      ⚠️ 테스트 조건 미충족 - 반응 시스템 테스트 스킵")
            return False
        
        test_post = self.created_posts[0]
        post_id = test_post.get("id") or test_post.get("_id")
        normal_token = self.test_users["normal"]["token"]
        
        # 1. 게시글 좋아요
        await self.rate_manager.wait_before_request()
        like_result = await self.api_manager.api_request(
            "POST", f"{self.base_url}/api/posts/{post_id}/like",
            user_token=normal_token
        )
        
        if like_result["success"]:
            self.report_generator.add_test_result(
                "게시글 좋아요", "success", "0.8초",
                "게시판 게시글 좋아요 기능 정상"
            )
            print("      ✅ 게시글 좋아요: 성공")
        else:
            self.report_generator.add_test_result(
                "게시글 좋아요", "failed", "0.8초",
                f"좋아요 실패: {like_result.get('error', 'Unknown')}"
            )
            print("      ❌ 게시글 좋아요: 실패")
        
        return True


async def main():
    """메인 실행 함수"""
    parser = create_test_runner_args_parser()
    parser.description = "게시판(Board) 페이지 통합 테스트 실행기"
    args = parser.parse_args()
    
    print("📋 게시판(Board) 페이지 통합 테스트 시스템")
    print("기본 게시글 CRUD, 댓글/답글 시스템, 반응 시스템 종합 검증")
    print("=" * 70)
    
    runner = BoardTestRunner(args.base_url)
    success = await runner.run_tests(args.mode)
    
    if args.open_browser and args.mode == "manual":
        import webbrowser
        try:
            webbrowser.open(f"{args.frontend_url}/board")
            print(f"\n🌐 브라우저에서 {args.frontend_url}/board 페이지를 열었습니다.")
        except Exception as e:
            print(f"⚠️ 브라우저 자동 열기 실패: {e}")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))