#!/usr/bin/env python3
"""
세션 ID 기반 테스트 데이터 정리 스크립트
- 특정 세션 ID의 모든 관련 데이터 정확하게 삭제
- Dry-run 모드로 안전성 보장
- 삭제 전 상세 미리보기 제공
"""

import asyncio
import argparse
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))

from nadle_backend.config import settings
from nadle_backend.models.core import User, Post, Comment, UserReaction
from motor.motor_asyncio import AsyncIOMotorClient
import beanie


class SessionBasedCleaner:
    def __init__(self):
        self.db = None
        self.client = None
        
    async def connect_db(self):
        """데이터베이스 연결 설정"""
        # 테스트 데이터베이스 사용
        test_db_name = f"{settings.database_name}_test"
        
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[test_db_name]
        
        # Beanie 초기화
        await beanie.init_beanie(
            database=self.db,
            document_models=[User, Post, Comment, UserReaction]
        )
        
    async def disconnect_db(self):
        """데이터베이스 연결 종료"""
        if self.client:
            self.client.close()
            
    def parse_session_timestamp(self, session_id: str) -> datetime:
        """세션 ID에서 타임스탬프 파싱"""
        try:
            # TEST_20250121_143022_AB7F -> 20250121_143022
            parts = session_id.split('_')
            if len(parts) >= 3:
                date_str = parts[1]
                time_str = parts[2]
                timestamp_str = f"{date_str}_{time_str}"
                return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except:
            pass
        return datetime.now()
        
    async def find_test_data_by_session(self, session_id: str) -> Dict[str, List[Any]]:
        """세션 ID로 모든 관련 테스트 데이터 찾기"""
        print(f"🔍 세션 {session_id} 데이터 검색 중...")
        
        found_data = {
            "posts": [],
            "comments": [],
            "reactions": [],
            "users": []
        }
        
        # 1. 게시글 찾기 (metadata.test_session_id로)
        posts = await Post.find({
            "metadata.test_session_id": session_id
        }).to_list()
        found_data["posts"] = posts
        
        # 2. 댓글 찾기 (metadata.test_session_id로)
        comments = await Comment.find({
            "metadata.test_session_id": session_id
        }).to_list()
        found_data["comments"] = comments
        
        # 3. 세션 ID가 포함된 콘텐츠로 댓글 추가 검색 (백업)
        content_comments = await Comment.find({
            "content": {"$regex": f"TEST-{session_id}"}
        }).to_list()
        
        # 중복 제거
        existing_comment_ids = {str(c.id) for c in found_data["comments"]}
        for comment in content_comments:
            if str(comment.id) not in existing_comment_ids:
                found_data["comments"].append(comment)
        
        # 4. 반응 찾기 (게시글/댓글과 연관된)
        post_ids = [str(p.id) for p in found_data["posts"]]
        comment_ids = [str(c.id) for c in found_data["comments"]]
        
        if post_ids or comment_ids:
            reactions = await UserReaction.find({
                "$or": [
                    {"parent_id": {"$in": post_ids}},
                    {"parent_id": {"$in": comment_ids}}
                ]
            }).to_list()
            found_data["reactions"] = reactions
        
        # 5. 테스트 사용자 찾기
        session_suffix = session_id.split('_')[-1].lower()
        test_users = await User.find({
            "email": {"$regex": f"testuser_{session_suffix}@test.com"}
        }).to_list()
        found_data["users"] = test_users
        
        return found_data
        
    def print_data_summary(self, session_id: str, found_data: Dict[str, List[Any]]):
        """발견된 데이터 요약 출력"""
        total_items = sum(len(items) for items in found_data.values())
        
        print(f"\n📊 세션 {session_id} 데이터 요약:")
        print(f"   게시글: {len(found_data['posts'])}개")
        print(f"   댓글: {len(found_data['comments'])}개")
        print(f"   반응: {len(found_data['reactions'])}개")
        print(f"   사용자: {len(found_data['users'])}개")
        print(f"   총계: {total_items}개")
        
        if total_items == 0:
            print("❌ 해당 세션 ID의 데이터가 없습니다.")
            return False
            
        return True
        
    def print_detailed_preview(self, found_data: Dict[str, List[Any]]):
        """상세 미리보기 출력"""
        print(f"\n🔍 상세 데이터 미리보기:")
        
        # 게시글 미리보기
        if found_data["posts"]:
            print(f"\n📝 게시글 ({len(found_data['posts'])}개):")
            for i, post in enumerate(found_data["posts"][:3], 1):
                print(f"   {i}. {post.title[:60]}...")
                print(f"      생성: {post.created_at}")
                print(f"      슬러그: {post.slug}")
            if len(found_data["posts"]) > 3:
                print(f"   ... 외 {len(found_data['posts']) - 3}개 더")
                
        # 댓글 미리보기
        if found_data["comments"]:
            print(f"\n💬 댓글 ({len(found_data['comments'])}개):")
            for i, comment in enumerate(found_data["comments"][:3], 1):
                print(f"   {i}. {comment.content[:50]}...")
                print(f"      생성: {comment.created_at}")
            if len(found_data["comments"]) > 3:
                print(f"   ... 외 {len(found_data['comments']) - 3}개 더")
                
        # 사용자 미리보기
        if found_data["users"]:
            print(f"\n👤 테스트 사용자 ({len(found_data['users'])}개):")
            for user in found_data["users"]:
                print(f"   - {user.user_handle} ({user.email})")
                print(f"     생성: {user.created_at}")
                
    async def perform_deletion(self, found_data: Dict[str, List[Any]]) -> Dict[str, int]:
        """실제 데이터 삭제 수행"""
        print(f"\n🧹 삭제 시작...")
        
        deleted_counts = {"posts": 0, "comments": 0, "reactions": 0, "users": 0}
        
        try:
            # 1. 반응 삭제 (참조 관계 고려)
            for reaction in found_data["reactions"]:
                await reaction.delete()
                deleted_counts["reactions"] += 1
                
            # 2. 댓글 삭제
            for comment in found_data["comments"]:
                await comment.delete()
                deleted_counts["comments"] += 1
                
            # 3. 게시글 삭제
            for post in found_data["posts"]:
                await post.delete()
                deleted_counts["posts"] += 1
                
            # 4. 테스트 사용자 삭제
            for user in found_data["users"]:
                await user.delete()
                deleted_counts["users"] += 1
                
        except Exception as e:
            print(f"❌ 삭제 중 오류 발생: {e}")
            raise
            
        return deleted_counts
        
    async def cleanup_by_session_id(self, session_id: str, dry_run: bool = True):
        """세션 ID로 데이터 정리"""
        await self.connect_db()
        
        try:
            # 세션 ID 형식 검증
            if not session_id.startswith("TEST_") or len(session_id.split('_')) < 4:
                print(f"❌ 올바른 테스트 세션 ID 형식이 아닙니다.")
                print(f"   올바른 형식: TEST_YYYYMMDD_HHMMSS_XXXX")
                print(f"   입력된 값: {session_id}")
                return
                
            # 데이터 찾기
            found_data = await self.find_test_data_by_session(session_id)
            
            # 요약 출력
            if not self.print_data_summary(session_id, found_data):
                return
                
            # 상세 미리보기
            self.print_detailed_preview(found_data)
            
            if dry_run:
                print(f"\n🔍 DRY RUN 모드 - 실제 삭제되지 않습니다.")
                print(f"실제 삭제하려면: python cleanup_test_data.py {session_id} --confirm")
                return
                
            # 실제 삭제 수행
            deleted_counts = await self.perform_deletion(found_data)
            
            print(f"\n✅ 삭제 완료:")
            for data_type, count in deleted_counts.items():
                if count > 0:
                    print(f"   - {data_type}: {count}개")
                    
            # 세션 파일도 삭제
            session_file = f"test_session_{session_id}.json"
            if os.path.exists(session_file):
                os.remove(session_file)
                print(f"   - 세션 파일: {session_file}")
                
            print(f"\n🎉 세션 {session_id} 정리 완료!")
            
        finally:
            await self.disconnect_db()
            
    async def list_active_sessions(self):
        """활성 테스트 세션 목록 표시"""
        await self.connect_db()
        
        try:
            print("🔍 활성 테스트 세션 검색 중...")
            
            # metadata에 test_session_id가 있는 게시글들로부터 세션 ID 추출
            posts = await Post.find({
                "metadata.test_session_id": {"$exists": True}
            }).to_list()
            
            sessions = {}
            for post in posts:
                session_id = post.metadata.get("test_session_id")
                if session_id and session_id.startswith("TEST_"):
                    if session_id not in sessions:
                        sessions[session_id] = {
                            "posts": 0,
                            "latest_created": post.created_at
                        }
                    sessions[session_id]["posts"] += 1
                    if post.created_at > sessions[session_id]["latest_created"]:
                        sessions[session_id]["latest_created"] = post.created_at
            
            if not sessions:
                print("📭 활성 테스트 세션이 없습니다.")
                return
                
            print(f"\n📋 활성 테스트 세션 ({len(sessions)}개):")
            for session_id, info in sorted(sessions.items(), key=lambda x: x[1]["latest_created"], reverse=True):
                age = datetime.now() - info["latest_created"].replace(tzinfo=None)
                age_str = f"{age.seconds // 3600}시간 {(age.seconds % 3600) // 60}분 전"
                if age.days > 0:
                    age_str = f"{age.days}일 {age_str}"
                    
                print(f"   🧪 {session_id}")
                print(f"      게시글: {info['posts']}개")
                print(f"      최근 활동: {age_str}")
                print(f"      정리 명령: cleanup_test_data.py {session_id} --confirm")
                print()
                
        finally:
            await self.disconnect_db()


async def main():
    parser = argparse.ArgumentParser(
        description="세션 ID 기반 테스트 데이터 정리",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s TEST_20250121_143022_AB7F              # 미리보기 (dry-run)
  %(prog)s TEST_20250121_143022_AB7F --confirm    # 실제 삭제
  %(prog)s --list                                 # 활성 세션 목록
        """
    )
    
    parser.add_argument("session_id", nargs="?", help="삭제할 테스트 세션 ID")
    parser.add_argument("--confirm", action="store_true", help="실제 삭제 실행 (기본은 dry-run)")
    parser.add_argument("--list", action="store_true", help="활성 테스트 세션 목록 표시")
    
    args = parser.parse_args()
    
    cleaner = SessionBasedCleaner()
    
    try:
        if args.list:
            await cleaner.list_active_sessions()
        elif args.session_id:
            await cleaner.cleanup_by_session_id(args.session_id, dry_run=not args.confirm)
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))