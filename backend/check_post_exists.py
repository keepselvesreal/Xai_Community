#!/usr/bin/env python3
"""
실제 DB에서 게시글 존재 여부 및 정보 확인
"""

import asyncio
from nadle_backend.models.core import Post, User, Comment, PostStats, UserReaction, Stats, FileRecord
from nadle_backend.database.connection import database


async def check_post_info():
    """게시글 정보 확인"""
    
    # DB 연결 초기화
    await database.connect()
    document_models = [User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
    await database.init_beanie_models(document_models)
    print("✅ DB 연결 및 Beanie 초기화 완료")
    
    # 1. 전체 게시글 수 확인
    total_posts = await Post.count()
    print(f"📊 전체 게시글 수: {total_posts}")
    
    # 2. 최근 게시글 5개 조회 (slug 확인용)
    recent_posts = await Post.find().sort("-created_at").limit(5).to_list()
    print(f"\n📝 최근 게시글 5개:")
    for i, post in enumerate(recent_posts, 1):
        print(f"  {i}. ID: {post.id}")
        print(f"     Slug: {post.slug}")
        print(f"     Title: {post.title}")
        print(f"     Status: {post.status}")
        print(f"     Created: {post.created_at}")
        print()
    
    # 3. 특정 게시글 확인
    target_slug = "6867b9d96ec8a1b04c9c116b-정수1"
    print(f"🔍 특정 게시글 조회: {target_slug}")
    
    # slug로 조회
    post_by_slug = await Post.find_one({"slug": target_slug})
    if post_by_slug:
        print(f"✅ Slug로 찾음:")
        print(f"   ID: {post_by_slug.id}")
        print(f"   Title: {post_by_slug.title}")
        print(f"   Content: {post_by_slug.content[:100]}...")
        print(f"   Status: {post_by_slug.status}")
        print(f"   Author ID: {post_by_slug.author_id}")
    else:
        print(f"❌ Slug로 찾을 수 없음")
    
    # 4. ID 부분으로 조회해보기
    post_id = "6867b9d96ec8a1b04c9c116b"
    try:
        from bson import ObjectId
        post_by_id = await Post.get(ObjectId(post_id))
        if post_by_id:
            print(f"✅ ID로 찾음:")
            print(f"   ID: {post_by_id.id}")
            print(f"   Real Slug: {post_by_id.slug}")
            print(f"   Title: {post_by_id.title}")
            print(f"   Status: {post_by_id.status}")
    except Exception as e:
        print(f"❌ ID로 조회 실패: {e}")
    
    # 5. 부분 slug 검색
    print(f"\n🔍 부분 slug 검색:")
    partial_posts = await Post.find({"slug": {"$regex": "정수"}}).to_list()
    for post in partial_posts:
        print(f"   Found: {post.slug} - {post.title}")
    
    # 6. 'board' 타입 게시글 확인
    board_posts = await Post.find({"$or": [
        {"metadata.type": "board"}, 
        {"metadata.type": {"$exists": False}},
        {"metadata.type": None}
    ]}).sort("-created_at").limit(3).to_list()
    
    print(f"\n📋 보드 타입 게시글 3개:")
    for i, post in enumerate(board_posts, 1):
        print(f"  {i}. Slug: {post.slug}")
        print(f"     Title: {post.title}")
        if post.metadata:
            print(f"     Type: {post.metadata.type}")
        print()


if __name__ == "__main__":
    asyncio.run(check_post_info())