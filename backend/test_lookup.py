#!/usr/bin/env python3
"""
MongoDB $lookup 테스트
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings
from nadle_backend.models.core import Post
from beanie import init_beanie
from pprint import pprint

async def test_lookup():
    """$lookup 테스트"""
    try:
        # MongoDB 연결 설정
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Beanie 초기화
        await init_beanie(database=db, document_models=[Post])
        
        print("=== MongoDB $lookup 테스트 ===")
        
        # Aggregation 파이프라인 테스트
        pipeline = [
            # 1. 매치 조건 (게시판 타입만)
            {"$match": {
                "status": {"$ne": "deleted"},
                "$or": [
                    {"metadata.type": {"$exists": False}},
                    {"metadata.type": None},
                    {"metadata.type": "board"}
                ]
            }},
            
            # 2. 작성자 정보 조회
            {"$lookup": {
                "from": "users",
                "localField": "author_id",
                "foreignField": "_id",
                "as": "author_info"
            }},
            
            # 3. 작성자 정보 처리
            {"$addFields": {
                "author": {"$arrayElemAt": ["$author_info", 0]}
            }},
            
            # 4. 불필요한 필드 제거
            {"$project": {
                "title": 1,
                "author_id": 1,
                "author_info": 1,
                "author": 1
            }},
            
            # 5. 제한
            {"$limit": 2}
        ]
        
        # 직접 MongoDB aggregation 실행
        result = await Post.aggregate(pipeline).to_list()
        
        print(f"📊 결과 개수: {len(result)}")
        for i, post in enumerate(result, 1):
            print(f"\n{i}. 게시글: {post.get('title')}")
            print(f"   author_id: {post.get('author_id')}")
            print(f"   author_info 길이: {len(post.get('author_info', []))}")
            
            if post.get('author_info'):
                author_info = post['author_info'][0]
                print(f"   author_info: {author_info}")
            
            if post.get('author'):
                author = post['author']
                print(f"   author: {author}")
                print(f"   author.display_name: {author.get('display_name')}")
                print(f"   author.user_handle: {author.get('user_handle')}")
                print(f"   author.name: {author.get('name')}")
            else:
                print(f"   author: None")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lookup())