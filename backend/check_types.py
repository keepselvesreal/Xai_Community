#!/usr/bin/env python3
"""
데이터 타입 확인 스크립트
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings
from nadle_backend.models.core import Post
from beanie import init_beanie

async def check_types():
    """데이터 타입 확인"""
    try:
        # MongoDB 연결 설정
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Beanie 초기화
        await init_beanie(database=db, document_models=[Post])
        
        print("=== 데이터 타입 확인 ===")
        
        # 1. Posts collection에서 author_id 타입 확인
        posts_collection = db.posts
        posts = await posts_collection.find().limit(2).to_list(length=2)
        print("📋 Posts collection:")
        for post in posts:
            print(f"  - title: {post.get('title')}")
            print(f"    author_id: {post.get('author_id')} (type: {type(post.get('author_id'))})")
            print(f"    _id: {post.get('_id')} (type: {type(post.get('_id'))})")
            print()
        
        # 2. Users collection에서 _id 타입 확인
        users_collection = db.users
        users = await users_collection.find().limit(2).to_list(length=2)
        print("👤 Users collection:")
        for user in users:
            print(f"  - user_handle: {user.get('user_handle')}")
            print(f"    _id: {user.get('_id')} (type: {type(user.get('_id'))})")
            print()
        
        # 3. 직접 매치 테스트
        print("🔍 직접 매치 테스트:")
        if posts and users:
            post = posts[0]
            author_id = post.get('author_id')
            print(f"  - 찾을 author_id: {author_id} (type: {type(author_id)})")
            
            # 직접 users collection에서 찾기
            user = await users_collection.find_one({"_id": author_id})
            print(f"  - 찾은 사용자: {user}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_types())