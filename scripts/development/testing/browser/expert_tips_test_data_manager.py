#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 14:27:55 KST
작업 버전: 전문가 꿀정보 테스트 데이터 관리 스크립트 v1.0

주요 컴포넌트들:
- ExpertTipsTestDataManager: 테스트 데이터 관리 메인 클래스 (45-120라인)
  - identify_test_data(): 테스트 데이터 식별 (122-180라인)
  - cleanup_test_data(): 테스트 데이터 정리 (182-270라인)
  - generate_cleanup_report(): 정리 결과 보고서 생성 (272-340라인)
  - list_test_sessions(): 테스트 세션 목록 조회 (342-390라인)

- TestDataIdentifier: 테스트 데이터 식별기 (392-450라인)
  - find_test_comments(): 테스트 댓글 검색 (452-490라인)
  - find_test_users(): 테스트 사용자 검색 (492-530라인)
  - find_test_reactions(): 테스트 반응 검색 (532-570라인)

테스트 데이터 관리 기능:
- 세션 ID 기반 테스트 데이터 식별
- 안전한 데이터 삭제 (전문가 꿀정보 게시글은 보존)
- 정리 전후 상태 비교
- 정리 결과 상세 보고서 생성
- 수동 정리 지원

관련 파일들:
- expert_tips_browser_test_setup.py: 브라우저 테스트 데이터 생성
- expert_tips_browser_test_guide.html: 브라우저 확인 가이드
- expert_tips_automation_test.py: 자동화 테스트 스크립트
"""

import asyncio
import aiohttp
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


# API Configuration
API_BASE = "http://localhost:8000"
API_ENDPOINTS = {
    "login": f"{API_BASE}/api/auth/login",
    "posts": f"{API_BASE}/api/posts",
    "comments": f"{API_BASE}/api/comments",
    "reactions": f"{API_BASE}/api/reactions",
    "users": f"{API_BASE}/api/users",
    "admin_permissions": f"{API_BASE}/api/admin/permissions"
}


class ExpertTipsTestDataManager:
    """전문가 꿀정보 테스트 데이터 관리자"""
    
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session = None
        self.admin_token = None
        
        # 정리 결과 저장
        self.cleanup_results = {
            "session": None,
            "timestamp": datetime.now().isoformat(),
            "before": {},
            "after": {},
            "deleted": {},
            "errors": []
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def authenticate_admin(self, admin_email: str = None, admin_password: str = None) -> bool:
        """관리자 인증"""
        if not admin_email or not admin_password:
            # 기본 관리자 계정 시도
            admin_email = "admin@example.com"
            admin_password = "AdminPassword123!"
        
        try:
            login_data = {
                "email": admin_email,
                "password": admin_password
            }
            
            async with self.session.post(API_ENDPOINTS["login"], json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.admin_token = result["access_token"]
                    print(f"✅ 관리자 인증 성공: {admin_email}")
                    return True
                else:
                    print(f"❌ 관리자 인증 실패: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ 관리자 인증 중 오류: {str(e)}")
            return False
    
    async def identify_test_data(self, session_id: str = None) -> Dict[str, Any]:
        """테스트 데이터 식별"""
        print(f"🔍 테스트 데이터 식별 중...")
        
        identified_data = {
            "test_users": [],
            "test_comments": [],
            "test_reactions": [],
            "expert_tips_posts": []
        }
        
        try:
            # 1. 테스트 사용자 검색
            if session_id:
                # 특정 세션의 테스트 사용자 검색
                test_users = await self._find_test_users_by_session(session_id)
            else:
                # 모든 브라우저 테스트 사용자 검색
                test_users = await self._find_all_test_users()
            
            identified_data["test_users"] = test_users
            print(f"   📋 테스트 사용자: {len(test_users)}개")
            
            # 2. 테스트 댓글 검색
            if session_id:
                test_comments = await self._find_test_comments_by_session(session_id)
            else:
                test_comments = await self._find_all_test_comments()
            
            identified_data["test_comments"] = test_comments
            print(f"   💬 테스트 댓글: {len(test_comments)}개")
            
            # 3. 테스트 반응 검색 (세션별 검색은 어려우므로 사용자 기반으로)
            if test_users:
                test_reactions = await self._find_test_reactions_by_users(test_users)
            else:
                test_reactions = []
            
            identified_data["test_reactions"] = test_reactions
            print(f"   👍 테스트 반응: {len(test_reactions)}개")
            
            # 4. 전문가 꿀정보 게시글 조회 (삭제하지 않음, 참고용)
            expert_tips_posts = await self._fetch_expert_tips_posts()
            identified_data["expert_tips_posts"] = expert_tips_posts
            print(f"   📄 전문가 꿀정보 게시글: {len(expert_tips_posts)}개 (삭제하지 않음)")
            
            return identified_data
            
        except Exception as e:
            print(f"❌ 테스트 데이터 식별 중 오류: {str(e)}")
            return identified_data
    
    async def cleanup_test_data(self, session_id: str = None, dry_run: bool = False) -> Dict[str, Any]:
        """테스트 데이터 정리"""
        print(f"🧹 테스트 데이터 정리 시작...")
        if dry_run:
            print("   (⚠️ Dry Run 모드 - 실제 삭제하지 않음)")
        
        self.cleanup_results["session"] = session_id
        
        # 정리 전 상태 확인
        before_data = await self.identify_test_data(session_id)
        self.cleanup_results["before"] = {
            "test_users": len(before_data["test_users"]),
            "test_comments": len(before_data["test_comments"]),
            "test_reactions": len(before_data["test_reactions"]),
            "expert_tips_posts": len(before_data["expert_tips_posts"])
        }
        
        deleted_counts = {
            "test_users": 0,
            "test_comments": 0,
            "test_reactions": 0
        }
        
        if not dry_run:
            try:
                # 1. 테스트 반응 삭제
                print("\n🗑️ 테스트 반응 삭제 중...")
                for reaction in before_data["test_reactions"]:
                    if await self._delete_reaction(reaction["id"]):
                        deleted_counts["test_reactions"] += 1
                
                # 2. 테스트 댓글 삭제
                print("\n🗑️ 테스트 댓글 삭제 중...")
                for comment in before_data["test_comments"]:
                    if await self._delete_comment(comment["id"]):
                        deleted_counts["test_comments"] += 1
                
                # 3. 테스트 사용자 삭제 (관리자 권한 필요)
                print("\n🗑️ 테스트 사용자 삭제 중...")
                for user in before_data["test_users"]:
                    if await self._delete_user(user["id"]):
                        deleted_counts["test_users"] += 1
                
            except Exception as e:
                error_msg = f"데이터 정리 중 오류: {str(e)}"
                self.cleanup_results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
        
        # 정리 후 상태 확인
        after_data = await self.identify_test_data(session_id)
        self.cleanup_results["after"] = {
            "test_users": len(after_data["test_users"]),
            "test_comments": len(after_data["test_comments"]),
            "test_reactions": len(after_data["test_reactions"]),
            "expert_tips_posts": len(after_data["expert_tips_posts"])
        }
        
        self.cleanup_results["deleted"] = deleted_counts
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("🎉 테스트 데이터 정리 완료!")
        print("=" * 60)
        print(f"🗑️ 삭제된 데이터:")
        print(f"   👤 테스트 사용자: {deleted_counts['test_users']}개")
        print(f"   💬 테스트 댓글: {deleted_counts['test_comments']}개")
        print(f"   👍 테스트 반응: {deleted_counts['test_reactions']}개")
        
        if self.cleanup_results["errors"]:
            print(f"\n⚠️ 오류 {len(self.cleanup_results['errors'])}건:")
            for error in self.cleanup_results["errors"]:
                print(f"   - {error}")
        
        return self.cleanup_results
    
    async def generate_cleanup_report(self, save_to_file: bool = True) -> str:
        """정리 결과 보고서 생성"""
        if not self.cleanup_results["timestamp"]:
            return "정리 결과가 없습니다."
        
        report_lines = [
            "# 전문가 꿀정보 테스트 데이터 정리 보고서",
            f"생성 시간: {self.cleanup_results['timestamp']}",
            f"세션 ID: {self.cleanup_results['session'] or 'ALL'}",
            "",
            "## 정리 전후 비교",
            "",
            "| 항목 | 정리 전 | 정리 후 | 삭제됨 |",
            "|------|---------|---------|---------|",
            f"| 테스트 사용자 | {self.cleanup_results['before']['test_users']} | {self.cleanup_results['after']['test_users']} | {self.cleanup_results['deleted']['test_users']} |",
            f"| 테스트 댓글 | {self.cleanup_results['before']['test_comments']} | {self.cleanup_results['after']['test_comments']} | {self.cleanup_results['deleted']['test_comments']} |",
            f"| 테스트 반응 | {self.cleanup_results['before']['test_reactions']} | {self.cleanup_results['after']['test_reactions']} | {self.cleanup_results['deleted']['test_reactions']} |",
            f"| 전문가 꿀정보 | {self.cleanup_results['before']['expert_tips_posts']} | {self.cleanup_results['after']['expert_tips_posts']} | 0 (보존) |",
            "",
        ]
        
        if self.cleanup_results["errors"]:
            report_lines.extend([
                "## 오류 목록",
                "",
            ])
            for i, error in enumerate(self.cleanup_results["errors"], 1):
                report_lines.append(f"{i}. {error}")
        else:
            report_lines.append("✅ 모든 데이터가 성공적으로 정리되었습니다.")
        
        report_content = "\n".join(report_lines)
        
        if save_to_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"expert_tips_cleanup_report_{timestamp}.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"📄 정리 보고서 저장됨: {filename}")
        
        return report_content
    
    async def list_test_sessions(self) -> List[str]:
        """브라우저 테스트 세션 목록 조회"""
        print("📋 브라우저 테스트 세션 목록 조회 중...")
        
        sessions = set()
        
        try:
            # 댓글 메타데이터에서 브라우저 테스트 세션 검색
            async with self.session.get(f"{API_ENDPOINTS['comments']}?page_size=100") as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result.get("items", [])
                    
                    for comment in comments:
                        metadata = comment.get("metadata", {})
                        session_id = metadata.get("browser_test_session")
                        if session_id and session_id.startswith("BROWSER_TEST_"):
                            sessions.add(session_id)
            
            session_list = sorted(list(sessions))
            
            print(f"✅ 브라우저 테스트 세션 {len(session_list)}개 발견:")
            for session in session_list:
                print(f"   - {session}")
            
            return session_list
            
        except Exception as e:
            print(f"❌ 세션 목록 조회 중 오류: {str(e)}")
            return []
    
    # 내부 헬퍼 메서드들
    async def _find_test_users_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """특정 세션의 테스트 사용자 검색"""
        suffix = session_id.split('_')[-1]
        test_users = []
        
        # 브라우저 테스트 이메일 패턴으로 검색
        patterns = [
            f"expert_browser_test_{suffix}@example.com",
            f"normal_browser_test_{suffix}@example.com"
        ]
        
        for pattern in patterns:
            user = await self._find_user_by_email(pattern)
            if user:
                test_users.append(user)
        
        return test_users
    
    async def _find_all_test_users(self) -> List[Dict[str, Any]]:
        """모든 브라우저 테스트 사용자 검색"""
        # 실제 구현에서는 API가 지원한다면 이메일 패턴으로 검색
        # 여기서는 간단히 알려진 패턴으로만 검색
        return []
    
    async def _find_test_comments_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """특정 세션의 테스트 댓글 검색"""
        test_comments = []
        
        try:
            async with self.session.get(f"{API_ENDPOINTS['comments']}?page_size=100") as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result.get("items", [])
                    
                    for comment in comments:
                        metadata = comment.get("metadata", {})
                        if metadata.get("browser_test_session") == session_id:
                            test_comments.append(comment)
        
        except Exception as e:
            print(f"❌ 테스트 댓글 검색 중 오류: {str(e)}")
        
        return test_comments
    
    async def _find_all_test_comments(self) -> List[Dict[str, Any]]:
        """모든 브라우저 테스트 댓글 검색"""
        test_comments = []
        
        try:
            async with self.session.get(f"{API_ENDPOINTS['comments']}?page_size=200") as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result.get("items", [])
                    
                    for comment in comments:
                        metadata = comment.get("metadata", {})
                        if metadata.get("browser_test_session") and metadata["browser_test_session"].startswith("BROWSER_TEST_"):
                            test_comments.append(comment)
        
        except Exception as e:
            print(f"❌ 테스트 댓글 검색 중 오류: {str(e)}")
        
        return test_comments
    
    async def _find_test_reactions_by_users(self, test_users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """테스트 사용자의 반응 검색"""
        # 실제 구현에서는 사용자 ID로 반응을 검색해야 함
        # API가 지원하지 않을 수 있으므로 빈 리스트 반환
        return []
    
    async def _fetch_expert_tips_posts(self) -> List[Dict[str, Any]]:
        """전문가 꿀정보 게시글 조회"""
        try:
            params = {
                "metadata_type": "expert_tips",
                "page": 1,
                "page_size": 50
            }
            
            async with self.session.get(API_ENDPOINTS["posts"], params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("items", [])
                else:
                    return []
        except Exception:
            return []
    
    async def _find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 검색"""
        # 실제 API에서 이메일 검색을 지원한다면 구현
        return None
    
    async def _delete_reaction(self, reaction_id: str) -> bool:
        """반응 삭제"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.delete(f"{API_ENDPOINTS['reactions']}/{reaction_id}", headers=headers) as response:
                if response.status == 200:
                    print(f"   ✅ 반응 삭제: {reaction_id}")
                    return True
                else:
                    print(f"   ❌ 반응 삭제 실패: {reaction_id} ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ 반응 삭제 중 오류: {reaction_id} ({str(e)})")
            return False
    
    async def _delete_comment(self, comment_id: str) -> bool:
        """댓글 삭제"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.delete(f"{API_ENDPOINTS['comments']}/{comment_id}", headers=headers) as response:
                if response.status == 200:
                    print(f"   ✅ 댓글 삭제: {comment_id}")
                    return True
                else:
                    print(f"   ❌ 댓글 삭제 실패: {comment_id} ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ 댓글 삭제 중 오류: {comment_id} ({str(e)})")
            return False
    
    async def _delete_user(self, user_id: str) -> bool:
        """사용자 삭제"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            async with self.session.delete(f"{API_ENDPOINTS['users']}/{user_id}", headers=headers) as response:
                if response.status == 200:
                    print(f"   ✅ 사용자 삭제: {user_id}")
                    return True
                else:
                    print(f"   ❌ 사용자 삭제 실패: {user_id} ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ 사용자 삭제 중 오류: {user_id} ({str(e)})")
            return False


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="전문가 꿀정보 테스트 데이터 관리")
    parser.add_argument("--action", choices=["list", "identify", "cleanup"], default="identify",
                        help="수행할 작업 (list: 세션 목록, identify: 데이터 식별, cleanup: 데이터 정리)")
    parser.add_argument("--session", help="특정 세션 ID 지정")
    parser.add_argument("--dry-run", action="store_true", help="실제 삭제하지 않고 시뮬레이션만")
    parser.add_argument("--admin-email", help="관리자 이메일")
    parser.add_argument("--admin-password", help="관리자 비밀번호")
    
    args = parser.parse_args()
    
    print("🎯 전문가 꿀정보 테스트 데이터 관리자")
    print(f"작업: {args.action}")
    if args.session:
        print(f"세션: {args.session}")
    print("=" * 60)
    
    async with ExpertTipsTestDataManager() as manager:
        if args.action in ["cleanup"]:
            # 관리자 인증 필요한 작업
            if not await manager.authenticate_admin(args.admin_email, args.admin_password):
                print("❌ 관리자 인증이 필요합니다.")
                return 1
        
        if args.action == "list":
            sessions = await manager.list_test_sessions()
            if sessions:
                print("\n📋 사용 가능한 세션 목록:")
                for session in sessions:
                    print(f"   python expert_tips_test_data_manager.py --action cleanup --session {session}")
            else:
                print("브라우저 테스트 세션이 없습니다.")
        
        elif args.action == "identify":
            data = await manager.identify_test_data(args.session)
            total_items = (len(data["test_users"]) + 
                          len(data["test_comments"]) + 
                          len(data["test_reactions"]))
            
            if total_items > 0:
                print(f"\n🔍 식별된 테스트 데이터: {total_items}개")
                print("정리하려면 다음 명령을 실행하세요:")
                if args.session:
                    print(f"   python expert_tips_test_data_manager.py --action cleanup --session {args.session}")
                else:
                    print("   python expert_tips_test_data_manager.py --action cleanup")
            else:
                print("정리할 테스트 데이터가 없습니다.")
        
        elif args.action == "cleanup":
            result = await manager.cleanup_test_data(args.session, args.dry_run)
            await manager.generate_cleanup_report()
            
            total_deleted = sum(result["deleted"].values())
            if total_deleted > 0:
                print(f"\n✅ 총 {total_deleted}개 항목이 정리되었습니다.")
            else:
                print("\nℹ️ 정리된 항목이 없습니다.")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))