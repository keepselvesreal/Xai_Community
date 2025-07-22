#!/usr/bin/env python3
"""
입주 서비스 업체 페이지 테스트 데이터 관리 스크립트
- 작업 시간: 2025-07-22 12:04 (KST) (date 명령어로 직접 확인한 현재 한국 시간 기준)
- 작업 버전: v1.0
- 주요 컴포넌트들:
  - ServiceProviderTestDataManager: 테스트 데이터 관리 메인 클래스 (lines 25-450)
  - 세션 기반 데이터 식별 (lines 80-120)
  - 안전한 데이터 삭제 (lines 200-280)
  - 정리 전후 상태 비교 (lines 350-400)
  - 정리 결과 보고서 생성 (lines 410-450)
- 관련 파일: service_provider_browser_test_setup.py (테스트 데이터 생성기)
"""

import asyncio
import argparse
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
import os
import json

# 백엔드 패키지 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../backend'))

from nadle_backend.models.core import User, Post, Comment
from nadle_backend.config import settings
from nadle_backend.database import init_db


class ServiceProviderTestDataManager:
    """입주 서비스 업체 페이지 테스트 데이터 관리자"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.cleanup_stats = {
            "deleted_users": 0,
            "deleted_posts": 0,
            "deleted_comments": 0,
            "deleted_inquiry_comments": 0,
            "deleted_review_comments": 0,
            "deleted_private_inquiries": 0,
            "preserved_posts": 0,
            "cleanup_time": None
        }
        
        # 상태 비교용
        self.before_state = {}
        self.after_state = {}
    
    async def identify_test_data(self, session_id: str = None) -> Dict[str, Any]:
        """테스트 데이터 식별"""
        print("🔍 테스트 데이터 식별 중...")
        
        # 세션 ID 기반 검색
        session_filter = session_id if session_id else self.session_id
        
        if session_filter:
            print(f"   세션 ID: {session_filter}")
            
            # 세션 기반 사용자 검색
            test_users = await User.find(
                {"metadata.session_id": session_filter}
            ).to_list()
            
            # 세션 기반 게시글 검색
            test_posts = await Post.find(
                {"metadata.session_id": session_filter}
            ).to_list()
            
            # 세션 기반 댓글 검색
            test_comments = await Comment.find(
                {"metadata.session_id": session_filter}
            ).to_list()
        else:
            # 전체 브라우저 테스트 데이터 검색
            print("   전체 브라우저 테스트 데이터 검색")
            
            test_users = await User.find(
                {"metadata.test_type": "browser_test"}
            ).to_list()
            
            test_posts = await Post.find(
                {"metadata.test_type": "browser_test"}
            ).to_list()
            
            test_comments = await Comment.find(
                {"metadata.test_type": {"$in": ["browser_test", "browser_test_privacy"]}}
            ).to_list()
        
        # 댓글 타입별 분류
        inquiry_comments = [c for c in test_comments if c.metadata.get("subtype") == "service_inquiry"]
        review_comments = [c for c in test_comments if c.metadata.get("subtype") == "service_review"]
        private_inquiries = [c for c in inquiry_comments if c.metadata.get("is_private")]
        
        results = {
            "users": test_users,
            "posts": test_posts,
            "comments": test_comments,
            "inquiry_comments": inquiry_comments,
            "review_comments": review_comments,
            "private_inquiries": private_inquiries,
            "total_count": len(test_users) + len(test_posts) + len(test_comments)
        }
        
        print(f"   ✅ 식별 완료:")
        print(f"      - 사용자: {len(test_users)}명")
        print(f"      - 게시글: {len(test_posts)}개")
        print(f"      - 댓글: {len(test_comments)}개")
        print(f"        • 문의 댓글: {len(inquiry_comments)}개")
        print(f"        • 후기 댓글: {len(review_comments)}개")
        print(f"        • 비공개 문의: {len(private_inquiries)}개")
        
        return results
    
    async def get_system_state(self) -> Dict[str, int]:
        """시스템 전체 상태 조회"""
        total_users = await User.find().count()
        total_posts = await Post.find().count()
        total_comments = await Comment.find().count()
        
        service_posts = await Post.find(
            Post.metadata.type == "moving services"
        ).count()
        
        service_comments = await Comment.find(
            {"metadata.subtype": {"$in": ["service_inquiry", "service_review"]}}
        ).count()
        
        return {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "service_posts": service_posts,
            "service_comments": service_comments
        }
    
    async def safe_cleanup(self, session_id: str = None, dry_run: bool = False) -> bool:
        """안전한 테스트 데이터 정리"""
        try:
            print("🧹 테스트 데이터 정리 시작!")
            if dry_run:
                print("   [DRY RUN 모드] - 실제 삭제 없이 시뮬레이션")
            
            # 정리 전 상태 기록
            self.before_state = await self.get_system_state()
            print(f"\n📊 정리 전 시스템 상태:")
            print(f"   - 전체 사용자: {self.before_state['total_users']}명")
            print(f"   - 전체 게시글: {self.before_state['total_posts']}개")
            print(f"   - 전체 댓글: {self.before_state['total_comments']}개")
            
            # 테스트 데이터 식별
            test_data = await self.identify_test_data(session_id)
            
            if test_data['total_count'] == 0:
                print("   ⚠️ 정리할 테스트 데이터가 없습니다.")
                return True
            
            # 사용자 확인 (dry_run이 아닌 경우)
            if not dry_run:
                confirmation = input(f"\n⚠️ {test_data['total_count']}개의 테스트 데이터를 삭제하시겠습니까? (y/N): ")
                if confirmation.lower() != 'y':
                    print("   정리 작업이 취소되었습니다.")
                    return False
            
            print(f"\n🗑️ 테스트 데이터 정리 진행...")
            
            # 1. 댓글 삭제 (가장 먼저)
            await self._cleanup_comments(test_data['comments'], dry_run)
            
            # 2. 게시글 정리 (테스트용만 삭제, 기존 서비스 게시글 보존)
            await self._cleanup_posts(test_data['posts'], dry_run)
            
            # 3. 사용자 삭제 (가장 마지막)
            await self._cleanup_users(test_data['users'], dry_run)
            
            # 정리 후 상태 기록
            if not dry_run:
                self.after_state = await self.get_system_state()
                await self._generate_cleanup_report()
            
            print(f"\n🎉 테스트 데이터 정리 완료!")
            if dry_run:
                print("   [DRY RUN] 실제 삭제는 수행되지 않았습니다.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 정리 중 오류 발생: {str(e)}")
            return False
    
    async def _cleanup_comments(self, comments: List[Comment], dry_run: bool):
        """댓글 정리"""
        if not comments:
            return
            
        print(f"   💬 댓글 정리: {len(comments)}개")
        
        for comment in comments:
            try:
                # 통계 업데이트
                if comment.metadata.get("subtype") == "service_inquiry":
                    if comment.metadata.get("is_private"):
                        self.cleanup_stats['deleted_private_inquiries'] += 1
                    self.cleanup_stats['deleted_inquiry_comments'] += 1
                elif comment.metadata.get("subtype") == "service_review":
                    self.cleanup_stats['deleted_review_comments'] += 1
                
                self.cleanup_stats['deleted_comments'] += 1
                
                if not dry_run:
                    await comment.delete()
                    
                print(f"      ✅ 댓글 삭제: {comment.content[:30]}...")
                
            except Exception as e:
                print(f"      ❌ 댓글 삭제 실패: {str(e)}")
    
    async def _cleanup_posts(self, posts: List[Post], dry_run: bool):
        """게시글 정리"""
        if not posts:
            return
            
        print(f"   🏢 게시글 정리: {len(posts)}개")
        
        for post in posts:
            try:
                # 테스트용 게시글만 삭제, 기존 서비스 게시글은 보존
                if post.metadata and post.metadata.session_id:
                    self.cleanup_stats['deleted_posts'] += 1
                    
                    if not dry_run:
                        await post.delete()
                        
                    print(f"      ✅ 테스트 게시글 삭제: {post.title}")
                else:
                    self.cleanup_stats['preserved_posts'] += 1
                    print(f"      🔒 기존 게시글 보존: {post.title}")
                    
            except Exception as e:
                print(f"      ❌ 게시글 처리 실패: {str(e)}")
    
    async def _cleanup_users(self, users: List[User], dry_run: bool):
        """사용자 정리"""
        if not users:
            return
            
        print(f"   👥 사용자 정리: {len(users)}명")
        
        for user in users:
            try:
                self.cleanup_stats['deleted_users'] += 1
                
                if not dry_run:
                    await user.delete()
                    
                print(f"      ✅ 테스트 사용자 삭제: {user.email}")
                
            except Exception as e:
                print(f"      ❌ 사용자 삭제 실패: {str(e)}")
    
    async def _generate_cleanup_report(self):
        """정리 결과 보고서 생성"""
        self.cleanup_stats['cleanup_time'] = datetime.now().isoformat()
        
        print(f"\n📋 정리 결과 요약:")
        print(f"   🗑️ 삭제된 항목:")
        print(f"      - 사용자: {self.cleanup_stats['deleted_users']}명")
        print(f"      - 게시글: {self.cleanup_stats['deleted_posts']}개")
        print(f"      - 댓글: {self.cleanup_stats['deleted_comments']}개")
        print(f"        • 문의 댓글: {self.cleanup_stats['deleted_inquiry_comments']}개")
        print(f"        • 후기 댓글: {self.cleanup_stats['deleted_review_comments']}개")
        print(f"        • 비공개 문의: {self.cleanup_stats['deleted_private_inquiries']}개")
        print(f"   🔒 보존된 항목:")
        print(f"      - 기존 게시글: {self.cleanup_stats['preserved_posts']}개")
        
        print(f"\n📊 정리 후 시스템 상태:")
        print(f"   - 전체 사용자: {self.after_state['total_users']}명 (변화: {self.after_state['total_users'] - self.before_state['total_users']})")
        print(f"   - 전체 게시글: {self.after_state['total_posts']}개 (변화: {self.after_state['total_posts'] - self.before_state['total_posts']})")
        print(f"   - 전체 댓글: {self.after_state['total_comments']}개 (변화: {self.after_state['total_comments'] - self.before_state['total_comments']})")
        
        # JSON 보고서 파일 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"service_provider_cleanup_report_{timestamp}.json"
        
        report_data = {
            "cleanup_summary": self.cleanup_stats,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "changes": {
                "users": self.after_state['total_users'] - self.before_state['total_users'],
                "posts": self.after_state['total_posts'] - self.before_state['total_posts'],
                "comments": self.after_state['total_comments'] - self.before_state['total_comments']
            }
        }
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 정리 보고서 저장: {report_filename}")
        except Exception as e:
            print(f"\n⚠️ 보고서 저장 실패: {str(e)}")
    
    async def list_test_sessions(self) -> List[str]:
        """테스트 세션 목록 조회"""
        print("📋 브라우저 테스트 세션 목록:")
        
        # 사용자 메타데이터에서 세션 ID 추출
        users = await User.find(
            {"metadata.test_type": "browser_test"}
        ).to_list()
        
        # 게시글 메타데이터에서 세션 ID 추출
        posts = await Post.find(
            {"metadata.test_type": "browser_test"}
        ).to_list()
        
        # 댓글 메타데이터에서 세션 ID 추출
        comments = await Comment.find(
            {"metadata.test_type": {"$in": ["browser_test", "browser_test_privacy"]}}
        ).to_list()
        
        session_ids = set()
        session_info = {}
        
        # 세션 ID 수집 및 정보 집계
        for user in users:
            sid = user.metadata.get('session_id')
            if sid:
                session_ids.add(sid)
                if sid not in session_info:
                    session_info[sid] = {'users': 0, 'posts': 0, 'comments': 0, 'created_at': user.created_at}
                session_info[sid]['users'] += 1
        
        for post in posts:
            sid = post.metadata.get('session_id')
            if sid:
                session_ids.add(sid)
                if sid not in session_info:
                    session_info[sid] = {'users': 0, 'posts': 0, 'comments': 0, 'created_at': post.created_at}
                session_info[sid]['posts'] += 1
        
        for comment in comments:
            sid = comment.metadata.get('session_id')
            if sid:
                session_ids.add(sid)
                if sid not in session_info:
                    session_info[sid] = {'users': 0, 'posts': 0, 'comments': 0, 'created_at': comment.created_at}
                session_info[sid]['comments'] += 1
        
        if not session_ids:
            print("   📭 활성 테스트 세션이 없습니다.")
            return []
        
        # 세션 정보 출력 (최신순 정렬)
        sorted_sessions = sorted(
            session_info.items(),
            key=lambda x: x[1]['created_at'],
            reverse=True
        )
        
        for session_id, info in sorted_sessions:
            created_str = info['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"   🆔 {session_id}")
            print(f"      생성일: {created_str}")
            print(f"      데이터: 사용자 {info['users']}명, 게시글 {info['posts']}개, 댓글 {info['comments']}개")
            print()
        
        return list(session_ids)


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='입주 서비스 업체 페이지 테스트 데이터 관리')
    parser.add_argument('--cleanup', action='store_true', help='테스트 데이터 정리')
    parser.add_argument('--list', action='store_true', help='테스트 세션 목록 조회')
    parser.add_argument('--session', type=str, help='특정 세션 ID 지정')
    parser.add_argument('--dry-run', action='store_true', help='실제 삭제 없이 시뮬레이션')
    
    args = parser.parse_args()
    
    print("🎯 입주 서비스 업체 페이지 테스트 데이터 관리자")
    print("세션 기반 안전한 데이터 정리 시스템")
    print()
    
    try:
        # 데이터베이스 연결
        await init_db()
        print("✅ 데이터베이스 연결 완료")
        
        manager = ServiceProviderTestDataManager(args.session)
        
        if args.list:
            # 테스트 세션 목록 조회
            await manager.list_test_sessions()
            
        elif args.cleanup:
            # 테스트 데이터 정리
            success = await manager.safe_cleanup(
                session_id=args.session,
                dry_run=args.dry_run
            )
            return 0 if success else 1
            
        else:
            # 기본: 테스트 데이터 식별만 수행
            await manager.identify_test_data(args.session)
            print("\n💡 사용법:")
            print("   --cleanup         : 테스트 데이터 정리")
            print("   --list           : 테스트 세션 목록 조회")
            print("   --session SESSION_ID : 특정 세션만 처리")
            print("   --dry-run        : 실제 삭제 없이 시뮬레이션")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))