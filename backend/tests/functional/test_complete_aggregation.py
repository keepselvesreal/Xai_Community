#!/usr/bin/env python3
"""
완전 통합 Aggregation 메서드 직접 테스트
"""

import asyncio
from nadle_backend.models.core import Post, User, Comment, PostStats, UserReaction, Stats, FileRecord
from nadle_backend.database.connection import database
from nadle_backend.services.posts_service import PostsService


async def test_complete_aggregation():
    """완전 통합 Aggregation 메서드 테스트"""
    
    # DB 연결 초기화
    await database.connect()
    document_models = [User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
    await database.init_beanie_models(document_models)
    print("✅ DB 연결 및 Beanie 초기화 완료")
    
    # 테스트할 게시글 slug
    test_slug = "6867b9d96ec8a1b04c9c116b-정수1"
    print(f"\n🔍 테스트 대상: {test_slug}")
    
    # PostsService 인스턴스 생성
    posts_service = PostsService()
    
    try:
        # 1. 기존 개별 조회 방식 테스트
        print("\n📋 1. 기존 개별 조회 방식:")
        start_time = asyncio.get_event_loop().time()
        
        # 게시글 조회
        post = await posts_service.get_post(test_slug)
        print(f"   게시글 조회 완료: {post.title}")
        
        # 댓글 조회
        comments = await posts_service.get_comments_with_batch_authors(test_slug)
        print(f"   댓글 조회 완료: {len(comments)}개")
        
        end_time = asyncio.get_event_loop().time()
        separate_time = (end_time - start_time) * 1000
        print(f"   소요 시간: {separate_time:.2f}ms")
        
    except Exception as e:
        print(f"❌ 기존 방식 실패: {e}")
        separate_time = 0
    
    try:
        # 2. 완전 통합 Aggregation 방식 테스트
        print("\n🚀 2. 완전 통합 Aggregation 방식:")
        start_time = asyncio.get_event_loop().time()
        
        complete_data = await posts_service.get_post_with_everything_aggregated(test_slug)
        
        end_time = asyncio.get_event_loop().time()
        complete_time = (end_time - start_time) * 1000
        
        if complete_data:
            print(f"   ✅ 완전 통합 조회 성공!")
            print(f"   게시글: {complete_data.get('title', 'N/A')}")
            print(f"   작성자: {complete_data.get('author', {}).get('user_handle', 'N/A')}")
            print(f"   댓글 수: {len(complete_data.get('comments', []))}")
            print(f"   사용자 반응: {'user_reaction' in complete_data}")
            print(f"   소요 시간: {complete_time:.2f}ms")
            
            # 성능 비교
            if separate_time > 0:
                improvement = ((separate_time - complete_time) / separate_time) * 100
                print(f"\n📊 성능 비교:")
                print(f"   기존 방식: {separate_time:.2f}ms")
                print(f"   완전 통합: {complete_time:.2f}ms")
                print(f"   성능 개선: {improvement:+.1f}%")
            
        else:
            print(f"   ❌ 완전 통합 조회 실패: 데이터 없음")
    
    except Exception as e:
        print(f"❌ 완전 통합 방식 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 서비스 내부 확인
    try:
        print(f"\n🔍 3. 서비스 내부 확인:")
        # 직접 Post 모델로 조회
        post_direct = await Post.find_one({"slug": test_slug})
        if post_direct:
            print(f"   Post 모델 직접 조회 성공: {post_direct.title}")
        else:
            print(f"   Post 모델 직접 조회 실패")
            
        # MongoDB 연결 상태 확인
        from nadle_backend.config import get_settings
        settings = get_settings()
        print(f"   Collections:")
        print(f"   - Users: {settings.users_collection}")
        print(f"   - Posts: {settings.posts_collection}")
        print(f"   - Comments: {settings.comments_collection}")
        
    except Exception as e:
        print(f"❌ 서비스 내부 확인 실패: {e}")


if __name__ == "__main__":
    asyncio.run(test_complete_aggregation())