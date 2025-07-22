#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 11:37:00 KST
주요 컴포넌트들:
- PropertyInfoTestDataManager: 부동산 정보 테스트 데이터 관리자 (lines 25-420)

주요 함수들:
- identify_test_data(): 세션 ID 기반 테스트 데이터 식별 (lines 78-130)
- cleanup_test_data(): 안전한 테스트 데이터 정리 (lines 132-220)
- generate_cleanup_report(): 정리 결과 보고서 생성 (lines 222-270)
- list_test_sessions(): 활성 테스트 세션 목록 조회 (lines 272-320)
- backup_test_data(): 정리 전 테스트 데이터 백업 (lines 322-370)

관련 파일:
- property_info_browser_test_setup.py: 테스트 데이터 생성 스크립트
- property_info_browser_test_guide.html: 브라우저 확인 가이드
- ../api/property_info_api_automation_test.py: API 자동화 테스트
"""

import asyncio
import aiohttp
import json
import argparse
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


class PropertyInfoTestDataManager:
    """부동산 정보 페이지 테스트 데이터 관리자"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.management_session_id = f"CLEANUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"
        
        # 관리자 계정 정보
        self.admin_credentials = {
            "username": "admin@nadle.io",
            "password": "Admin123"  # 대문자 포함 비밀번호 정책 준수
        }
        
        self.auth_token = None
        self.cleanup_stats = {
            "comments_deleted": 0,
            "reactions_removed": 0,
            "users_deleted": 0,
            "sessions_processed": 0,
            "errors": []
        }
    
    async def manage_test_data(self, action: str, session_id: Optional[str] = None, 
                              days_old: Optional[int] = None, dry_run: bool = False):
        """테스트 데이터 관리 메인 함수"""
        
        print("🧹 부동산 정보 페이지 테스트 데이터 관리자")
        print(f"🆔 관리 세션 ID: {self.management_session_id}")
        print(f"🎯 작업: {action}")
        if dry_run:
            print("🔍 드라이 런 모드 (실제 삭제 없음)")
        print("=" * 70)
        
        session = aiohttp.ClientSession()
        
        try:
            # 관리자 로그인
            await self._admin_login(session)
            
            if action == "cleanup":
                if session_id:
                    await self._cleanup_specific_session(session, session_id, dry_run)
                elif days_old is not None:
                    await self._cleanup_old_sessions(session, days_old, dry_run)
                else:
                    print("❌ cleanup 작업을 위해서는 --session-id 또는 --days-old 옵션이 필요합니다.")
                    return False
                    
            elif action == "list":
                await self._list_test_sessions(session)
                
            elif action == "backup":
                if session_id:
                    await self._backup_session_data(session, session_id)
                else:
                    await self._backup_all_test_data(session)
                    
            elif action == "restore":
                if session_id:
                    await self._restore_session_data(session, session_id)
                else:
                    print("❌ restore 작업을 위해서는 --session-id 옵션이 필요합니다.")
                    return False
                    
            else:
                print(f"❌ 알 수 없는 작업: {action}")
                return False
            
            # 최종 보고서 생성
            if action == "cleanup":
                await self._generate_cleanup_report()
            
        except Exception as e:
            print(f"\n❌ 작업 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await session.close()
        
        print(f"\n🎉 테스트 데이터 관리 작업 완료!")
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
                else:
                    error_text = await response.text()
                    raise Exception(f"관리자 로그인 실패: {response.status} - {error_text}")
        except Exception as e:
            raise Exception(f"관리자 로그인 오류: {str(e)}")
    
    async def _cleanup_specific_session(self, session: aiohttp.ClientSession, 
                                       session_id: str, dry_run: bool):
        """특정 세션의 테스트 데이터 정리"""
        print(f"🎯 세션 '{session_id}' 데이터 정리 시작")
        
        # 1. 세션 데이터 식별
        test_data = await self._identify_session_data(session, session_id)
        
        if not any(test_data.values()):
            print(f"   ℹ️ 세션 '{session_id}'에 해당하는 테스트 데이터를 찾을 수 없습니다.")
            return
        
        # 2. 정리 전 백업 (드라이런이 아닌 경우)
        if not dry_run:
            await self._backup_session_data(session, session_id)
        
        # 3. 데이터 정리
        await self._cleanup_session_data(session, test_data, dry_run)
        
        # 4. 통계 업데이트
        self.cleanup_stats["sessions_processed"] += 1
    
    async def _cleanup_old_sessions(self, session: aiohttp.ClientSession, 
                                   days_old: int, dry_run: bool):
        """오래된 테스트 세션들 정리"""
        print(f"📅 {days_old}일 이상 된 테스트 데이터 정리 시작")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        print(f"   📅 기준일: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 모든 테스트 세션 조회
        all_sessions = await self._find_all_test_sessions(session)
        old_sessions = []
        
        for session_info in all_sessions:
            session_date = datetime.fromisoformat(session_info["created_at"].replace('Z', '+00:00'))
            if session_date < cutoff_date:
                old_sessions.append(session_info)
        
        print(f"   📊 정리 대상 세션: {len(old_sessions)}개")
        
        for session_info in old_sessions:
            await self._cleanup_specific_session(session, session_info["session_id"], dry_run)
    
    async def _identify_session_data(self, session: aiohttp.ClientSession, 
                                   session_id: str) -> Dict[str, List]:
        """세션 ID로 테스트 데이터 식별"""
        print(f"   🔍 세션 '{session_id}' 데이터 식별 중...")
        
        test_data = {
            "comments": [],
            "users": [],
            "reactions": []
        }
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # 1. 댓글 데이터 식별
        try:
            # 댓글 내용에 세션 ID가 포함된 댓글들 검색
            params = {"page": 1, "page_size": 100}
            async with session.get(f"{self.base_url}/api/comments/", params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    comments = data.get("items", [])
                    
                    session_comments = [
                        comment for comment in comments 
                        if session_id in comment.get("content", "")
                    ]
                    
                    test_data["comments"] = session_comments
                    print(f"      💬 댓글: {len(session_comments)}개 발견")
        except Exception as e:
            self.cleanup_stats["errors"].append(f"댓글 식별 오류: {str(e)}")
            print(f"      ❌ 댓글 식별 오류: {e}")
        
        # 2. 사용자 데이터 식별 (세션 ID 기반)
        try:
            # 사용자 이름이나 이메일에 세션 ID 관련 패턴이 있는 사용자들
            session_suffix = session_id.split('_')[-1].lower()
            params = {"page": 1, "page_size": 100}
            async with session.get(f"{self.base_url}/api/users/", params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    users = data.get("items", [])
                    
                    session_users = [
                        user for user in users 
                        if (session_suffix in user.get("email", "").lower() or 
                            "browser" in user.get("email", "").lower() or
                            "proptest" in user.get("email", "").lower())
                    ]
                    
                    test_data["users"] = session_users
                    print(f"      👤 사용자: {len(session_users)}개 발견")
        except Exception as e:
            self.cleanup_stats["errors"].append(f"사용자 식별 오류: {str(e)}")
            print(f"      ❌ 사용자 식별 오류: {e}")
        
        # 3. 반응 데이터는 별도 API가 없으므로 댓글/사용자 기반으로 추정
        print(f"      ❤️ 반응 데이터: 사용자 기반으로 정리 예정")
        
        return test_data
    
    async def _cleanup_session_data(self, session: aiohttp.ClientSession, 
                                  test_data: Dict[str, List], dry_run: bool):
        """식별된 테스트 데이터 정리"""
        print("   🧹 테스트 데이터 정리 시작")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # 1. 댓글 삭제
        for comment in test_data["comments"]:
            comment_id = comment.get("id") or comment.get("_id")
            if dry_run:
                print(f"      [드라이런] 댓글 삭제 예정: {comment_id}")
                self.cleanup_stats["comments_deleted"] += 1
            else:
                try:
                    await asyncio.sleep(0.3)  # API 호출 간격
                    async with session.delete(
                        f"{self.base_url}/api/comments/{comment_id}", 
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            self.cleanup_stats["comments_deleted"] += 1
                            print(f"      ✅ 댓글 삭제: {comment_id}")
                        else:
                            error = f"댓글 삭제 실패 ({comment_id}): {response.status}"
                            self.cleanup_stats["errors"].append(error)
                            print(f"      ❌ {error}")
                except Exception as e:
                    error = f"댓글 삭제 오류 ({comment_id}): {str(e)}"
                    self.cleanup_stats["errors"].append(error)
                    print(f"      ❌ {error}")
        
        # 2. 사용자 삭제 (관리자는 제외)
        for user in test_data["users"]:
            user_id = user.get("id") or user.get("_id")
            user_email = user.get("email", "")
            
            # 관리자 계정은 삭제하지 않음
            if user_email == self.admin_credentials["email"]:
                print(f"      ⚠️ 관리자 계정 삭제 건너뜀: {user_email}")
                continue
                
            if dry_run:
                print(f"      [드라이런] 사용자 삭제 예정: {user_email}")
                self.cleanup_stats["users_deleted"] += 1
            else:
                try:
                    await asyncio.sleep(0.3)
                    async with session.delete(
                        f"{self.base_url}/api/users/{user_id}", 
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            self.cleanup_stats["users_deleted"] += 1
                            print(f"      ✅ 사용자 삭제: {user_email}")
                        else:
                            error = f"사용자 삭제 실패 ({user_email}): {response.status}"
                            self.cleanup_stats["errors"].append(error)
                            print(f"      ❌ {error}")
                except Exception as e:
                    error = f"사용자 삭제 오류 ({user_email}): {str(e)}"
                    self.cleanup_stats["errors"].append(error)
                    print(f"      ❌ {error}")
        
        print(f"   📊 정리 완료: 댓글 {len(test_data['comments'])}개, 사용자 {len(test_data['users'])}개")
    
    async def _list_test_sessions(self, session: aiohttp.ClientSession):
        """활성 테스트 세션 목록 조회"""
        print("📋 활성 테스트 세션 목록")
        print("-" * 70)
        
        all_sessions = await self._find_all_test_sessions(session)
        
        if not all_sessions:
            print("   ℹ️ 활성 테스트 세션이 없습니다.")
            return
        
        for i, session_info in enumerate(all_sessions, 1):
            print(f"{i}. 세션 ID: {session_info['session_id']}")
            print(f"   생성일: {session_info['created_at']}")
            print(f"   댓글: {session_info['comment_count']}개")
            print(f"   사용자: {session_info['user_count']}개")
            print()
    
    async def _find_all_test_sessions(self, session: aiohttp.ClientSession) -> List[Dict]:
        """모든 테스트 세션 찾기"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        sessions = []
        
        try:
            # 1. 댓글에서 세션 ID 패턴 찾기
            params = {"page": 1, "page_size": 200}
            async with session.get(f"{self.base_url}/api/comments/", params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    comments = data.get("items", [])
                    
                    session_patterns = set()
                    for comment in comments:
                        content = comment.get("content", "")
                        # 세션 ID 패턴 추출 (BROWSER_PROPINFO_, TEST_, 등)
                        if "세션:" in content:
                            parts = content.split("세션:")
                            if len(parts) > 1:
                                session_id = parts[1].split(")")[0].strip()
                                session_patterns.add(session_id)
                    
                    # 각 세션에 대한 정보 수집
                    for session_id in session_patterns:
                        session_comments = [c for c in comments if session_id in c.get("content", "")]
                        
                        # 세션 생성일 추정 (가장 오래된 댓글 기준)
                        created_at = min([c.get("created_at", "") for c in session_comments]) if session_comments else ""
                        
                        sessions.append({
                            "session_id": session_id,
                            "created_at": created_at,
                            "comment_count": len(session_comments),
                            "user_count": len(set([c.get("author_id") for c in session_comments]))
                        })
        except Exception as e:
            print(f"   ❌ 세션 조회 오류: {e}")
        
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)
    
    async def _backup_session_data(self, session: aiohttp.ClientSession, session_id: str):
        """세션 데이터 백업"""
        print(f"   💾 세션 '{session_id}' 데이터 백업 중...")
        
        test_data = await self._identify_session_data(session, session_id)
        
        backup_data = {
            "session_id": session_id,
            "backup_timestamp": datetime.now().isoformat(),
            "management_session": self.management_session_id,
            "data": test_data
        }
        
        # 백업 파일 저장
        backup_path = Path(__file__).parent / f"backup_session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            print(f"      ✅ 백업 저장: {backup_path}")
        except Exception as e:
            error = f"백업 저장 실패: {str(e)}"
            self.cleanup_stats["errors"].append(error)
            print(f"      ❌ {error}")
    
    async def _backup_all_test_data(self, session: aiohttp.ClientSession):
        """모든 테스트 데이터 백업"""
        print("💾 모든 테스트 데이터 백업 시작")
        
        all_sessions = await self._find_all_test_sessions(session)
        
        for session_info in all_sessions:
            await self._backup_session_data(session, session_info["session_id"])
    
    async def _restore_session_data(self, session: aiohttp.ClientSession, session_id: str):
        """세션 데이터 복원 (백업에서)"""
        print(f"🔄 세션 '{session_id}' 데이터 복원")
        
        # 백업 파일 찾기
        backup_files = list(Path(__file__).parent.glob(f"backup_session_{session_id}_*.json"))
        
        if not backup_files:
            print(f"   ❌ 세션 '{session_id}'의 백업 파일을 찾을 수 없습니다.")
            return
        
        # 가장 최신 백업 파일 사용
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        print(f"   📁 백업 파일: {latest_backup}")
        
        # 복원 로직 구현 (실제로는 복잡한 데이터 재생성 필요)
        print("   ⚠️ 데이터 복원 기능은 향후 구현 예정입니다.")
        print("   💡 현재는 백업 파일을 수동으로 확인하여 필요한 데이터를 복원하세요.")
    
    async def _generate_cleanup_report(self):
        """정리 작업 보고서 생성"""
        print("\n📊 테스트 데이터 정리 보고서 생성 중...")
        
        report = {
            "management_session_id": self.management_session_id,
            "timestamp": datetime.now().isoformat(),
            "cleanup_stats": self.cleanup_stats,
            "summary": {
                "total_items_deleted": (
                    self.cleanup_stats["comments_deleted"] + 
                    self.cleanup_stats["users_deleted"]
                ),
                "sessions_processed": self.cleanup_stats["sessions_processed"],
                "errors_count": len(self.cleanup_stats["errors"]),
                "success_rate": self._calculate_success_rate()
            }
        }
        
        # JSON 보고서 저장
        report_path = Path(__file__).parent / f"cleanup_report_{self.management_session_id}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"   📄 JSON 보고서: {report_path}")
        except Exception as e:
            print(f"   ❌ 보고서 저장 실패: {e}")
        
        # 콘솔 요약 출력
        print("\n" + "=" * 70)
        print("🎉 테스트 데이터 정리 완료!")
        print("=" * 70)
        print(f"📊 정리 통계:")
        print(f"   💬 댓글 삭제: {self.cleanup_stats['comments_deleted']}개")
        print(f"   👤 사용자 삭제: {self.cleanup_stats['users_deleted']}개")
        print(f"   📁 처리된 세션: {self.cleanup_stats['sessions_processed']}개")
        print(f"   ❌ 오류 발생: {len(self.cleanup_stats['errors'])}건")
        print(f"   ✅ 성공률: {report['summary']['success_rate']:.1f}%")
        
        if self.cleanup_stats["errors"]:
            print(f"\n⚠️ 발생한 오류들:")
            for i, error in enumerate(self.cleanup_stats["errors"][:5], 1):
                print(f"   {i}. {error}")
            if len(self.cleanup_stats["errors"]) > 5:
                print(f"   ... 외 {len(self.cleanup_stats['errors']) - 5}건")
    
    def _calculate_success_rate(self) -> float:
        """성공률 계산"""
        total_operations = (
            self.cleanup_stats["comments_deleted"] + 
            self.cleanup_stats["users_deleted"]
        )
        total_errors = len(self.cleanup_stats["errors"])
        
        if total_operations + total_errors == 0:
            return 100.0
        
        return (total_operations / (total_operations + total_errors)) * 100


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="부동산 정보 페이지 테스트 데이터 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  특정 세션 정리:
    python property_info_test_data_manager.py cleanup --session-id BROWSER_PROPINFO_20250122_120000_ABCD

  오래된 데이터 정리:
    python property_info_test_data_manager.py cleanup --days-old 7

  테스트 세션 목록:
    python property_info_test_data_manager.py list

  드라이런 (실제 삭제 없이 확인):
    python property_info_test_data_manager.py cleanup --session-id XXXXX --dry-run

  백업:
    python property_info_test_data_manager.py backup --session-id XXXXX
        """
    )
    
    parser.add_argument(
        "action", 
        choices=["cleanup", "list", "backup", "restore"],
        help="수행할 작업"
    )
    
    parser.add_argument(
        "--session-id", 
        help="대상 세션 ID"
    )
    
    parser.add_argument(
        "--days-old", 
        type=int,
        help="지정된 일수보다 오래된 데이터 정리"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="드라이 런 모드 (실제 삭제 없이 확인만)"
    )
    
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8000",
        help="백엔드 서버 URL (기본값: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    manager = PropertyInfoTestDataManager(args.base_url)
    success = await manager.manage_test_data(
        action=args.action,
        session_id=args.session_id,
        days_old=args.days_old,
        dry_run=args.dry_run
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))