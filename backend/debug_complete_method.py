#!/usr/bin/env python3
"""
완전 통합 메서드 디버그
"""

import asyncio
from nadle_backend.models.core import Post, User, Comment, PostStats, UserReaction, Stats, FileRecord
from nadle_backend.database.connection import database
from nadle_backend.services.posts_service import PostsService


async def debug_complete_method():
    """완전 통합 메서드 디버그"""
    
    # DB 연결 초기화
    await database.connect()
    document_models = [User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
    await database.init_beanie_models(document_models)
    print("✅ DB 연결 및 Beanie 초기화 완료")
    
    # 테스트할 게시글 slug
    test_slug = "6867b9d96ec8a1b04c9c116b-정수1"
    print(f"🔍 테스트 대상: {test_slug}")
    
    # PostsService 인스턴스 생성
    posts_service = PostsService()
    
    try:
        print(f"\n🔍 1. 직접 게시글 존재 확인:")
        post_direct = await Post.find_one({"slug": test_slug})
        if post_direct:
            print(f"   ✅ 게시글 존재: {post_direct.title}")
            print(f"   ID: {post_direct.id}")
            print(f"   Author ID: {post_direct.author_id}")
        else:
            print(f"   ❌ 게시글 없음")
            return
        
        print(f"\n🚀 2. 완전 통합 메서드 호출:")
        try:
            complete_data = await posts_service.get_post_with_everything_aggregated(test_slug)
            
            if complete_data:
                print(f"   ✅ 성공!")
                print(f"   Title: {complete_data.get('title', 'N/A')}")
                print(f"   ID: {complete_data.get('id', 'N/A')}")
                print(f"   Author: {complete_data.get('author', {}).get('user_handle', 'N/A')}")
                print(f"   Comments: {len(complete_data.get('comments', []))}")
                print(f"   Has User Reaction: {'user_reaction' in complete_data}")
            else:
                print(f"   ❌ 반환값이 None")
                
        except Exception as e:
            print(f"   ❌ 메서드 호출 실패: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🔍 3. 기존 get_post 메서드와 비교:")
        try:
            normal_post = await posts_service.get_post(test_slug)
            print(f"   ✅ 기존 get_post 성공: {normal_post.title}")
        except Exception as e:
            print(f"   ❌ 기존 get_post 실패: {e}")
    
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_complete_method())