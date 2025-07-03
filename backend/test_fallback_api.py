#!/usr/bin/env python3
"""
기존 list_posts 함수 테스트
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings
from nadle_backend.models.core import Post
from nadle_backend.repositories.post_repository import PostRepository
from beanie import init_beanie

async def test_fallback_api():
    """기존 list_posts 함수 테스트"""
    try:
        # MongoDB 연결 설정
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Beanie 초기화
        await init_beanie(database=db, document_models=[Post])
        
        print("=== 기존 list_posts 함수 테스트 ===")
        
        # 리포지토리 초기화
        post_repo = PostRepository()
        
        # 1. property_information 타입 게시글 조회
        print("\n1. property_information 타입 게시글 조회:")
        property_posts, total = await post_repo.list_posts(
            page=1, 
            page_size=10, 
            metadata_type="property_information"
        )
        print(f"Property information posts: {total}")
        print(f"Items returned: {len(property_posts)}")
        
        # 샘플 데이터 출력
        for i, post in enumerate(property_posts[:3]):
            print(f"  {i+1}. {post.title}")
            print(f"     metadata.type: {post.metadata.type if post.metadata else 'None'}")
            print(f"     metadata.category: {post.metadata.category if post.metadata else 'None'}")
            print(f"     id: {post.id}")
            print(f"     author_id: {post.author_id}")
            print()
        
        # 2. 다른 metadata_type들 테스트
        print("\n2. 다른 metadata_type들 테스트:")
        test_types = ["board", "expert_tips", "moving services"]
        for test_type in test_types:
            posts, total = await post_repo.list_posts(
                page=1, 
                page_size=3, 
                metadata_type=test_type
            )
            print(f"  {test_type}: {total}개")
        
        # 3. 모든 게시글 조회
        print("\n3. 모든 게시글 조회:")
        all_posts, total = await post_repo.list_posts(page=1, page_size=5)
        print(f"Total posts: {total}")
        print(f"Items returned: {len(all_posts)}")
        
        print("\n=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fallback_api())