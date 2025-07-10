#!/usr/bin/env python3
"""
MongoDB 인덱스 생성 스크립트.

최적화된 쿼리 성능을 위해 필요한 인덱스들을 생성합니다.
"""

import asyncio
import sys
from pymongo import IndexModel
from nadle_backend.database import Database
from nadle_backend.database.manager import IndexManager
from nadle_backend.config import settings


async def create_indexes():
    """MongoDB 인덱스를 생성합니다."""
    print("🚀 MongoDB 인덱스 생성을 시작합니다...")
    
    # 데이터베이스 연결
    db = Database()
    try:
        await db.connect()
        print("✅ 데이터베이스 연결 성공")
        
        # 현재 사용 중인 데이터베이스 가져오기
        mongo_db = db.client[settings.database_name]
        print(f"📊 대상 데이터베이스: {settings.database_name}")
        
        # 기존 인덱스 확인
        print("\n📋 기존 인덱스 확인 중...")
        posts_indexes = await IndexManager.get_index_info(mongo_db, "posts")
        print(f"   Posts 컬렉션 기존 인덱스: {len(posts_indexes)}개")
        for idx in posts_indexes:
            print(f"   - {idx['name']}")
        
        # Posts 컬렉션만 SSR 최적화 인덱스 생성 (다른 컬렉션은 스킵)
        print("\n🔨 Posts 컬렉션 SSR 최적화 인덱스 생성 중...")
        posts_collection = mongo_db[settings.posts_collection]
        
        # SSR 최적화 인덱스들만 생성
        ssr_indexes = [
            IndexModel(
                [("metadata.type", 1), ("status", 1), ("created_at", -1)],
                name="metadata_type_status_created_idx"
            ),
            IndexModel(
                [("metadata.type", 1), ("created_at", -1)],
                name="metadata_type_created_idx"
            ),
            IndexModel(
                [("metadata.type", 1), ("status", 1), ("view_count", -1)],
                name="metadata_type_status_views_idx"
            ),
            IndexModel(
                [("metadata.type", 1), ("status", 1), ("like_count", -1)],
                name="metadata_type_status_likes_idx"
            )
        ]
        
        # 기존 인덱스 이름 목록
        existing_index_names = {idx['name'] for idx in posts_indexes}
        
        # 새로운 인덱스만 생성
        indexes_to_create = []
        for idx in ssr_indexes:
            if idx.document["name"] not in existing_index_names:
                indexes_to_create.append(idx)
                print(f"   ➕ 생성 예정: {idx.document['name']}")
            else:
                print(f"   ⚠️  이미 존재: {idx.document['name']}")
        
        if indexes_to_create:
            created_names = await posts_collection.create_indexes(indexes_to_create)
            print(f"\n✅ Posts 컬렉션에 {len(created_names)}개 인덱스 생성 완료!")
            for name in created_names:
                print(f"   ✅ {name}")
        else:
            print(f"\n⚠️  모든 SSR 최적화 인덱스가 이미 존재합니다.")
        
        # 생성된 인덱스 확인
        print("\n📋 최종 인덱스 확인...")
        posts_indexes_after = await IndexManager.get_index_info(mongo_db, "posts")
        print(f"   Posts 컬렉션 총 인덱스: {len(posts_indexes_after)}개")
        
        # 새로 추가된 SSR 최적화 인덱스들 확인
        ssr_index_names = [
            "metadata_type_status_created_idx",
            "metadata_type_created_idx", 
            "metadata_type_status_views_idx",
            "metadata_type_status_likes_idx"
        ]
        
        print("\n🎯 SSR 최적화 인덱스 확인:")
        for idx_name in ssr_index_names:
            found = any(idx['name'] == idx_name for idx in posts_indexes_after)
            status = "✅" if found else "❌"
            print(f"   {status} {idx_name}")
        
        print("\n🎉 인덱스 생성이 완료되었습니다!")
        print("   이제 SSR 페이지 성능이 크게 향상됩니다.")
        
    except Exception as e:
        print(f"❌ 인덱스 생성 실패: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        await db.disconnect()
        print("📌 데이터베이스 연결 종료")


async def check_metadata_types():
    """실제 데이터베이스의 메타데이터 타입들을 확인합니다."""
    print("\n🔍 실제 데이터베이스의 메타데이터 타입 확인...")
    
    db = Database()
    try:
        await db.connect()
        mongo_db = db.client[settings.database_name]
        posts_collection = mongo_db["posts"]
        
        # 실제 메타데이터 타입들 조회
        pipeline = [
            {"$group": {"_id": "$metadata.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        result = await posts_collection.aggregate(pipeline).to_list(length=None)
        
        print("📊 실제 데이터베이스의 메타데이터 타입들:")
        for item in result:
            metadata_type = item["_id"]
            count = item["count"]
            print(f"   - '{metadata_type}': {count}개 게시글")
        
        return result
        
    except Exception as e:
        print(f"❌ 메타데이터 확인 실패: {e}")
        return []
    finally:
        await db.disconnect()


async def main():
    """메인 함수."""
    print("=" * 60)
    print("🚀 백엔드 API 성능 최적화: 인덱스 생성")
    print("=" * 60)
    
    # 1. 메타데이터 타입 확인
    await check_metadata_types()
    
    # 2. 인덱스 생성
    await create_indexes()
    
    print("\n" + "=" * 60)
    print("🎯 다음 단계:")
    print("   1. 백엔드 서버 재시작")
    print("   2. 프론트엔드에서 SSR 페이지 테스트")
    print("   3. 응답 시간 1초 이내 확인")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())