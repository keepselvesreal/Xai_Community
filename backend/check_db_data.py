#!/usr/bin/env python3
"""
데이터베이스 정보 페이지 관련 데이터 확인 스크립트
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings
from nadle_backend.models.core import Post
from beanie import init_beanie
from pprint import pprint

async def check_db_info():
    """데이터베이스 정보 확인"""
    try:
        # MongoDB 연결 설정
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Beanie 초기화
        await init_beanie(database=db, document_models=[Post])
        
        print("=== 데이터베이스 정보 페이지 관련 데이터 확인 ===")
        
        # 1. 전체 게시글 개수 확인
        total_posts = await Post.count()
        print(f"📊 전체 게시글 개수: {total_posts}")
        
        # 2. metadata.type이 property_information인 게시글 확인
        property_info_posts = await Post.find({"metadata.type": "property_information"}).count()
        print(f"🏢 property_information 타입 게시글 개수: {property_info_posts}")
        
        # 3. 모든 metadata.type 값 확인
        print("\n📋 모든 metadata.type 값 확인:")
        pipeline = [
            {"$group": {"_id": "$metadata.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        types = await Post.aggregate(pipeline).to_list()
        for type_info in types:
            print(f"  - {type_info['_id']}: {type_info['count']}개")
        
        # 4. 샘플 게시글 메타데이터 확인 (최근 10개)
        print("\n📝 최근 게시글 10개의 메타데이터 확인:")
        recent_posts = await Post.find().sort("-created_at").limit(10).to_list()
        for i, post in enumerate(recent_posts, 1):
            print(f"  {i}. {post.title[:30]}...")
            print(f"     metadata.type: {post.metadata.type if post.metadata else 'None'}")
            print(f"     metadata.category: {post.metadata.category if post.metadata else 'None'}")
            print(f"     created_at: {post.created_at}")
            print()
        
        # 5. 특정 키워드를 포함한 게시글 확인
        info_keywords = ["정보", "안내", "부동산", "입주", "이사"]
        print("🔍 정보성 키워드를 포함한 게시글 확인:")
        for keyword in info_keywords:
            count = await Post.find({"title": {"$regex": keyword, "$options": "i"}}).count()
            print(f"  - '{keyword}' 포함 게시글: {count}개")
            
        # 6. 실제 property_information 게시글 샘플 확인
        if property_info_posts > 0:
            print("\n🏠 property_information 게시글 샘플:")
            sample_posts = await Post.find({"metadata.type": "property_information"}).limit(5).to_list()
            for post in sample_posts:
                print(f"  - {post.title}")
                print(f"    ID: {post.id}")
                print(f"    Slug: {post.slug}")
                print(f"    Metadata: {post.metadata.model_dump() if post.metadata else 'None'}")
                print()
        
        await client.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_db_info())