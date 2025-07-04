#!/usr/bin/env python3
"""
사용자 정보 확인 스크립트
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings
from nadle_backend.models.core import User, Post
from beanie import init_beanie
from pprint import pprint

async def check_user_data():
    """사용자 정보 확인"""
    try:
        # MongoDB 연결 설정
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Beanie 초기화
        await init_beanie(database=db, document_models=[User, Post])
        
        print("=== 사용자 정보 확인 ===")
        
        # 1. 전체 사용자 개수 확인
        total_users = await User.count()
        print(f"📊 전체 사용자 개수: {total_users}")
        
        # 2. 사용자 정보 확인
        users = await User.find_all().to_list()
        print(f"\n👤 사용자 목록:")
        for user in users:
            print(f"  - ID: {user.id}")
            print(f"    display_name: '{user.display_name}'")
            print(f"    user_handle: '{user.user_handle}'")
            print(f"    name: '{user.name}'")
            print(f"    email: '{user.email}'")
            print()
        
        # 3. 게시글 작성자 ID 확인
        print("📋 게시글 작성자 ID 확인:")
        posts = await Post.find().limit(5).to_list()
        for post in posts:
            print(f"  - 게시글: {post.title}")
            print(f"    author_id: {post.author_id}")
            
            # 작성자 정보 조회
            try:
                author = await User.get(post.author_id)
                if author:
                    print(f"    작성자: {author.display_name or author.name or author.user_handle}")
                else:
                    print(f"    작성자: 찾을 수 없음")
            except Exception as e:
                print(f"    작성자 조회 오류: {e}")
            print()
        
        await client.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_data())