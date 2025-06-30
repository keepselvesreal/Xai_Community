#!/usr/bin/env python3
"""MongoDB Atlas connection test script."""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """MongoDB Atlas 연결 테스트"""
    print("=" * 60)
    print("MongoDB Atlas 연결 테스트 시작")
    print("=" * 60)
    
    # 설정 정보 출력
    print(f"MongoDB URL: {settings.mongodb_url}")
    print(f"Database Name: {settings.database_name}")
    print(f"Users Collection: {settings.users_collection}")
    print("-" * 60)
    
    client = None
    try:
        # 1. 클라이언트 생성
        print("1. MongoDB 클라이언트 생성 중...")
        client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=10000,  # 10초 타임아웃
            connectTimeoutMS=10000,          # 10초 연결 타임아웃
            socketTimeoutMS=10000,           # 10초 소켓 타임아웃
            retryWrites=True,
            w='majority'
        )
        print("✅ 클라이언트 생성 완료")
        
        # 2. 서버 정보 확인
        print("\n2. 서버 연결 테스트 중...")
        server_info = await client.server_info()
        print(f"✅ 서버 연결 성공")
        print(f"   MongoDB 버전: {server_info.get('version', 'Unknown')}")
        print(f"   서버 정보: {server_info.get('buildInfo', {}).get('gitVersion', 'Unknown')}")
        
        # 3. 데이터베이스 접근 테스트
        print(f"\n3. 데이터베이스 '{settings.database_name}' 접근 테스트 중...")
        db = client[settings.database_name]
        
        # 데이터베이스 목록 확인
        db_list = await client.list_database_names()
        print(f"   사용 가능한 데이터베이스: {db_list}")
        
        if settings.database_name in db_list:
            print(f"✅ 데이터베이스 '{settings.database_name}' 존재함")
        else:
            print(f"⚠️  데이터베이스 '{settings.database_name}' 존재하지 않음 (첫 문서 삽입 시 생성됨)")
        
        # 4. 컬렉션 접근 테스트
        print(f"\n4. 컬렉션 '{settings.users_collection}' 접근 테스트 중...")
        users_collection = db[settings.users_collection]
        
        # 컬렉션 목록 확인
        collections = await db.list_collection_names()
        print(f"   사용 가능한 컬렉션: {collections}")
        
        if settings.users_collection in collections:
            print(f"✅ 컬렉션 '{settings.users_collection}' 존재함")
            # 문서 개수 확인
            count = await users_collection.count_documents({})
            print(f"   현재 사용자 수: {count}")
        else:
            print(f"⚠️  컬렉션 '{settings.users_collection}' 존재하지 않음 (첫 문서 삽입 시 생성됨)")
        
        # 5. 읽기/쓰기 권한 테스트
        print(f"\n5. 읽기/쓰기 권한 테스트 중...")
        test_doc = {
            "test": True,
            "message": "Connection test document",
            "timestamp": "2025-06-30T15:50:00Z"
        }
        
        # 테스트 문서 삽입
        result = await users_collection.insert_one(test_doc)
        print(f"✅ 테스트 문서 삽입 성공: {result.inserted_id}")
        
        # 테스트 문서 조회
        found_doc = await users_collection.find_one({"_id": result.inserted_id})
        if found_doc:
            print("✅ 테스트 문서 조회 성공")
        
        # 테스트 문서 삭제
        delete_result = await users_collection.delete_one({"_id": result.inserted_id})
        if delete_result.deleted_count > 0:
            print("✅ 테스트 문서 삭제 성공")
        
        # 6. 인덱스 확인
        print(f"\n6. 인덱스 정보 확인 중...")
        indexes = await users_collection.list_indexes().to_list(length=None)
        print("   현재 인덱스:")
        for idx in indexes:
            print(f"   - {idx.get('name', 'Unknown')}: {idx.get('key', {})}")
        
        print("\n" + "=" * 60)
        print("✅ MongoDB Atlas 연결 테스트 완료 - 모든 테스트 통과!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB 연결 실패:")
        print(f"   오류 타입: {type(e).__name__}")
        print(f"   오류 메시지: {str(e)}")
        
        # 상세 오류 분석
        error_str = str(e).lower()
        if "authentication failed" in error_str:
            print("\n🔍 인증 실패 분석:")
            print("   - 사용자명/비밀번호가 올바른지 확인하세요")
            print("   - MongoDB Atlas에서 사용자 권한을 확인하세요")
        elif "connection refused" in error_str or "timeout" in error_str:
            print("\n🔍 연결 실패 분석:")
            print("   - 네트워크 연결을 확인하세요")
            print("   - MongoDB Atlas IP 화이트리스트를 확인하세요")
            print("   - 방화벽 설정을 확인하세요")
        elif "ssl" in error_str or "tls" in error_str:
            print("\n🔍 SSL/TLS 오류 분석:")
            print("   - MongoDB Atlas는 TLS 연결이 필요합니다")
            print("   - 연결 문자열에 ssl=true가 포함되어야 합니다")
        
        logger.exception("Detailed error information:")
        return False
        
    finally:
        if client:
            print("\n7. 연결 종료 중...")
            client.close()
            print("✅ 연결 종료 완료")

async def test_beanie_integration():
    """Beanie ODM 통합 테스트"""
    print("\n" + "=" * 60)
    print("Beanie ODM 통합 테스트 시작")
    print("=" * 60)
    
    try:
        from nadle_backend.database.connection import database
        from nadle_backend.models.core import User
        
        print("1. Beanie 데이터베이스 연결 테스트...")
        await database.connect()
        print("✅ Beanie 데이터베이스 연결 성공")
        
        print("2. Beanie 모델 초기화...")
        await database.init_beanie_models([User])
        print("✅ Beanie 모델 초기화 성공")
        
        print("3. User 모델 테스트...")
        # 기존 사용자 수 확인
        user_count = await User.count()
        print(f"   현재 사용자 수: {user_count}")
        
        print("\n✅ Beanie ODM 통합 테스트 완료!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Beanie ODM 테스트 실패:")
        print(f"   오류: {str(e)}")
        logger.exception("Beanie integration test failed:")
        return False
        
    finally:
        try:
            await database.disconnect()
            print("✅ Beanie 데이터베이스 연결 종료")
        except:
            pass

async def main():
    """메인 테스트 함수"""
    print("MongoDB Atlas 연결 진단 도구")
    print("현재 시간:", "2025-06-30 15:50:00")
    print()
    
    # 기본 연결 테스트
    basic_test = await test_mongodb_connection()
    
    if basic_test:
        # Beanie 통합 테스트
        await test_beanie_integration()
    else:
        print("\n⚠️  기본 연결 테스트 실패로 Beanie 테스트를 건너뜁니다.")
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())