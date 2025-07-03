#!/usr/bin/env python3
"""
API 직접 테스트 스크립트
"""
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings
from nadle_backend.models.core import Post
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.services.posts_service import PostsService
from beanie import init_beanie

async def test_api_endpoints():
    """API 엔드포인트 직접 테스트"""
    try:
        # MongoDB 연결 설정
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Beanie 초기화
        await init_beanie(database=db, document_models=[Post])
        
        print("=== API 엔드포인트 직접 테스트 ===")
        
        # 서비스 초기화
        posts_service = PostsService()
        
        # 1. 모든 게시글 조회
        print("\n1. 모든 게시글 조회:")
        all_posts = await posts_service.list_posts(page=1, page_size=5)
        print(f"Total posts: {all_posts.get('total', 0)}")
        print(f"Items returned: {len(all_posts.get('items', []))}")
        
        # 2. property_information 타입 게시글 조회
        print("\n2. property_information 타입 게시글 조회:")
        property_posts = await posts_service.list_posts(
            page=1, 
            page_size=10, 
            metadata_type="property_information"
        )
        print(f"Property information posts: {property_posts.get('total', 0)}")
        print(f"Items returned: {len(property_posts.get('items', []))}")
        
        # 샘플 데이터 출력
        for i, post in enumerate(property_posts.get('items', [])[:3]):
            print(f"  {i+1}. {post.get('title', 'No title')}")
            print(f"     metadata.type: {post.get('metadata', {}).get('type', 'None')}")
            print(f"     metadata.category: {post.get('metadata', {}).get('category', 'None')}")
            print(f"     id: {post.get('id', 'None')}")
            print()
        
        # 3. 다른 metadata_type들 테스트
        print("\n3. 다른 metadata_type들 테스트:")
        test_types = ["board", "expert_tips", "moving services"]
        for test_type in test_types:
            result = await posts_service.list_posts(
                page=1, 
                page_size=3, 
                metadata_type=test_type
            )
            print(f"  {test_type}: {result.get('total', 0)}개")
        
        # 4. 게시글 검색 테스트
        print("\n4. 게시글 검색 테스트:")
        search_result = await posts_service.search_posts(
            query="계약",
            page=1,
            page_size=5
        )
        print(f"'계약' 검색 결과: {search_result.get('total', 0)}개")
        
        # 5. 특정 게시글 조회
        if property_posts.get('items'):
            first_post = property_posts['items'][0]
            post_id = first_post.get('id')
            if post_id:
                print(f"\n5. 특정 게시글 조회 (ID: {post_id}):")
                try:
                    single_post = await posts_service.get_post(post_id)
                    print(f"  제목: {single_post.title}")
                    print(f"  메타데이터: {single_post.metadata.model_dump() if single_post.metadata else 'None'}")
                except Exception as e:
                    print(f"  오류: {e}")
        
        print("\n=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())