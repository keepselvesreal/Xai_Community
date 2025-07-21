"""UTC로 저장된 시간 데이터를 KST로 변환하는 마이그레이션 스크립트"""
import asyncio
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# 프로젝트 루트 경로를 Python 경로에 추가
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from nadle_backend.models.core import User, Post, Comment, UserReaction, FileMetadata, UserStatistics
from nadle_backend.config import settings
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def convert_utc_to_kst(utc_dt: datetime) -> datetime:
    """UTC datetime을 KST로 변환"""
    if utc_dt is None:
        return None
    
    # timezone 정보가 없으면 UTC로 가정
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    
    # KST로 변환
    kst_dt = utc_dt.astimezone(ZoneInfo("Asia/Seoul"))
    
    # timezone 정보를 제거하여 저장 (MongoDB는 timezone-naive datetime을 선호)
    return kst_dt.replace(tzinfo=None)


async def migrate_collection(collection_class, collection_name: str):
    """특정 컬렉션의 모든 문서를 UTC에서 KST로 변환"""
    logger.info(f"마이그레이션 시작: {collection_name}")
    
    # 전체 문서 수 확인
    total_count = await collection_class.count()
    logger.info(f"총 {total_count}개의 문서 발견")
    
    # 배치 단위로 처리
    batch_size = 100
    processed = 0
    
    async for doc in collection_class.find_all():
        try:
            updated = False
            
            # created_at 변환
            if hasattr(doc, 'created_at') and doc.created_at:
                new_created_at = await convert_utc_to_kst(doc.created_at)
                if new_created_at != doc.created_at:
                    doc.created_at = new_created_at
                    updated = True
            
            # updated_at 변환
            if hasattr(doc, 'updated_at') and doc.updated_at:
                new_updated_at = await convert_utc_to_kst(doc.updated_at)
                if new_updated_at != doc.updated_at:
                    doc.updated_at = new_updated_at
                    updated = True
            
            # 기타 시간 필드들 변환
            # Post의 published_at, resolved_at
            if hasattr(doc, 'published_at') and doc.published_at:
                doc.published_at = await convert_utc_to_kst(doc.published_at)
                updated = True
            
            if hasattr(doc, 'resolved_at') and doc.resolved_at:
                doc.resolved_at = await convert_utc_to_kst(doc.resolved_at)
                updated = True
            
            # User의 last_login
            if hasattr(doc, 'last_login') and doc.last_login:
                doc.last_login = await convert_utc_to_kst(doc.last_login)
                updated = True
            
            # UserStatistics의 last_viewed_at
            if hasattr(doc, 'last_viewed_at') and doc.last_viewed_at:
                doc.last_viewed_at = await convert_utc_to_kst(doc.last_viewed_at)
                updated = True
            
            # FileMetadata의 upload_timestamp
            if hasattr(doc, 'upload_timestamp') and doc.upload_timestamp:
                doc.upload_timestamp = await convert_utc_to_kst(doc.upload_timestamp)
                updated = True
            
            # UserStatistics의 last_calculated, last_updated
            if hasattr(doc, 'last_calculated') and doc.last_calculated:
                doc.last_calculated = await convert_utc_to_kst(doc.last_calculated)
                updated = True
            
            if hasattr(doc, 'last_updated') and doc.last_updated:
                doc.last_updated = await convert_utc_to_kst(doc.last_updated)
                updated = True
            
            # 변경사항이 있으면 저장
            if updated:
                await doc.save()
                processed += 1
                
                if processed % batch_size == 0:
                    logger.info(f"{collection_name}: {processed}/{total_count} 문서 처리 완료")
                    
        except Exception as e:
            logger.error(f"{collection_name} 문서 처리 중 오류 발생 (ID: {doc.id}): {str(e)}")
            continue
    
    logger.info(f"{collection_name} 마이그레이션 완료: 총 {processed}개 문서 업데이트")


async def main():
    """메인 마이그레이션 함수"""
    logger.info("UTC to KST 마이그레이션 시작...")
    
    # MongoDB 연결
    client = AsyncIOMotorClient(settings.database_url)
    database = client[settings.database_name]
    
    # Beanie 초기화
    await init_beanie(
        database=database,
        document_models=[User, Post, Comment, UserReaction, FileMetadata, UserStatistics]
    )
    
    # 각 컬렉션 마이그레이션
    collections = [
        (User, "users"),
        (Post, "posts"),
        (Comment, "comments"),
        (UserReaction, "user_reactions"),
        (FileMetadata, "file_metadata"),
        (UserStatistics, "user_statistics")
    ]
    
    for collection_class, collection_name in collections:
        await migrate_collection(collection_class, collection_name)
    
    logger.info("모든 마이그레이션 완료!")
    
    # 연결 종료
    client.close()


if __name__ == "__main__":
    # 환경 확인
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        response = input("프로덕션 환경에서 마이그레이션을 실행하시겠습니까? (yes/no): ")
        if response.lower() != "yes":
            logger.info("마이그레이션 취소됨")
            sys.exit(0)
    
    # 마이그레이션 실행
    asyncio.run(main())