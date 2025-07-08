#!/usr/bin/env python3
"""
Aggregation에서 author 정보가 제대로 조회되지 않는 문제 디버깅
"""

import asyncio
from nadle_backend.models.core import Post, User, Comment, PostStats, UserReaction, Stats, FileRecord
from nadle_backend.database.connection import database
from nadle_backend.config import get_settings
from bson import ObjectId


async def debug_aggregation_author():
    """Aggregation에서 author 정보 조회 디버깅"""
    
    # DB 연결 초기화
    await database.connect()
    document_models = [User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
    await database.init_beanie_models(document_models)
    print("✅ DB 연결 및 Beanie 초기화 완료")
    
    # 테스트할 게시글 정보
    test_slug = "6867b9d96ec8a1b04c9c116b-정수1"
    post_id = "6867b9d96ec8a1b04c9c116b"
    author_id = "6867b9cb6ec8a1b04c9c116a"
    
    print(f"🔍 테스트 대상:")
    print(f"   Slug: {test_slug}")
    print(f"   Post ID: {post_id}")
    print(f"   Author ID: {author_id}")
    
    try:
        settings = get_settings()
        
        # 1. 직접 사용자 조회
        print(f"\n🔍 1. 직접 사용자 조회:")
        user = await User.get(ObjectId(author_id))
        if user:
            print(f"   ✅ 사용자 존재: {user.user_handle}")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
        else:
            print(f"   ❌ 사용자 없음")
        
        # 2. 기본 lookup 테스트
        print(f"\n🔍 2. 기본 Lookup 테스트:")
        basic_pipeline = [
            {"$match": {"slug": test_slug}},
            {"$lookup": {
                "from": settings.users_collection,
                "localField": "author_id", 
                "foreignField": "_id",
                "as": "author_info"
            }},
            {"$project": {
                "title": 1,
                "author_id": 1,
                "author_info": 1
            }}
        ]
        
        results = await Post.aggregate(basic_pipeline).to_list()
        if results:
            result = results[0]
            print(f"   게시글: {result.get('title')}")
            print(f"   Author ID: {result.get('author_id')}")
            print(f"   Author Info 배열 길이: {len(result.get('author_info', []))}")
            
            if result.get('author_info'):
                author_info = result['author_info'][0]
                print(f"   Author Info: {author_info}")
            else:
                print(f"   ❌ Author Info 없음")
        
        # 3. ObjectId 변환 테스트
        print(f"\n🔍 3. ObjectId 변환 테스트:")
        print(f"   Author ID 타입: {type(ObjectId(author_id))}")
        print(f"   Post의 author_id 필드 확인...")
        
        post = await Post.find_one({"slug": test_slug})
        if post:
            print(f"   Post author_id: {post.author_id} (타입: {type(post.author_id)})")
            print(f"   ObjectId 비교: {post.author_id == ObjectId(author_id)}")
        
        # 4. Collection 이름 확인
        print(f"\n🔍 4. Collection 설정 확인:")
        print(f"   Users collection: {settings.users_collection}")
        print(f"   Posts collection: {settings.posts_collection}")
        
        # 5. 실제 컬렉션에서 직접 조회
        print(f"\n🔍 5. 컬렉션 직접 조회:")
        db = database.get_database()
        
        # Users 컬렉션에서 직접 조회
        user_doc = await db[settings.users_collection].find_one({"_id": ObjectId(author_id)})
        if user_doc:
            print(f"   ✅ Users 컬렉션에서 직접 조회 성공:")
            print(f"      ID: {user_doc['_id']}")
            print(f"      Handle: {user_doc.get('user_handle')}")
        else:
            print(f"   ❌ Users 컬렉션에서 직접 조회 실패")
        
        # Posts 컬렉션에서 직접 조회
        post_doc = await db[settings.posts_collection].find_one({"slug": test_slug})
        if post_doc:
            print(f"   ✅ Posts 컬렉션에서 직접 조회 성공:")
            print(f"      ID: {post_doc['_id']}")
            print(f"      Author ID: {post_doc.get('author_id')} (타입: {type(post_doc.get('author_id'))})")
        else:
            print(f"   ❌ Posts 컬렉션에서 직접 조회 실패")
            
    except Exception as e:
        print(f"❌ 디버깅 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_aggregation_author())