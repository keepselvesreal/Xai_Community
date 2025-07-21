"""마이그레이션 미리보기 - 실제 변경 없이 변환될 데이터 확인"""
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
from nadle_backend.models.core import User, Post, Comment
from nadle_backend.config import settings
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def preview_time_conversion(utc_dt: datetime) -> tuple[datetime, datetime]:
    """UTC datetime을 KST로 변환하고 원본과 변환된 값을 반환"""
    if utc_dt is None:
        return None, None
    
    # timezone 정보가 없으면 UTC로 가정
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    
    # KST로 변환
    kst_dt = utc_dt.astimezone(ZoneInfo("Asia/Seoul"))
    
    return utc_dt, kst_dt.replace(tzinfo=None)


async def preview_collection(collection_class, collection_name: str, limit: int = 5):
    """특정 컬렉션의 샘플 데이터 변환 미리보기"""
    logger.info(f"\n{'='*60}")
    logger.info(f"{collection_name} 컬렉션 미리보기")
    logger.info(f"{'='*60}")
    
    # 전체 문서 수 확인
    total_count = await collection_class.count()
    logger.info(f"총 {total_count}개의 문서 존재\n")
    
    # 샘플 문서 가져오기
    sample_docs = await collection_class.find_all().limit(limit).to_list()
    
    for i, doc in enumerate(sample_docs, 1):
        logger.info(f"문서 #{i} (ID: {doc.id})")
        
        # created_at 미리보기
        if hasattr(doc, 'created_at') and doc.created_at:
            utc_time, kst_time = await preview_time_conversion(doc.created_at)
            logger.info(f"  created_at:")
            logger.info(f"    현재 (UTC): {doc.created_at}")
            logger.info(f"    변환 (KST): {kst_time}")
            logger.info(f"    차이: 9시간")
        
        # updated_at 미리보기
        if hasattr(doc, 'updated_at') and doc.updated_at:
            utc_time, kst_time = await preview_time_conversion(doc.updated_at)
            logger.info(f"  updated_at:")
            logger.info(f"    현재 (UTC): {doc.updated_at}")
            logger.info(f"    변환 (KST): {kst_time}")
        
        # Post의 추가 필드들
        if collection_name == "posts":
            if hasattr(doc, 'title'):
                logger.info(f"  제목: {doc.title[:50]}...")
            
            if hasattr(doc, 'published_at') and doc.published_at:
                utc_time, kst_time = await preview_time_conversion(doc.published_at)
                logger.info(f"  published_at:")
                logger.info(f"    현재 (UTC): {doc.published_at}")
                logger.info(f"    변환 (KST): {kst_time}")
        
        # User의 추가 필드들
        if collection_name == "users":
            if hasattr(doc, 'username'):
                logger.info(f"  사용자명: {doc.username}")
            
            if hasattr(doc, 'last_login') and doc.last_login:
                utc_time, kst_time = await preview_time_conversion(doc.last_login)
                logger.info(f"  last_login:")
                logger.info(f"    현재 (UTC): {doc.last_login}")
                logger.info(f"    변환 (KST): {kst_time}")
        
        logger.info("")


async def main():
    """메인 미리보기 함수"""
    logger.info("UTC to KST 마이그레이션 미리보기")
    logger.info("실제 데이터는 변경되지 않습니다.\n")
    
    # MongoDB 연결
    client = AsyncIOMotorClient(settings.database_url)
    database = client[settings.database_name]
    
    # Beanie 초기화
    await init_beanie(
        database=database,
        document_models=[User, Post, Comment]
    )
    
    # 각 컬렉션 미리보기
    await preview_collection(User, "users", limit=3)
    await preview_collection(Post, "posts", limit=3)
    await preview_collection(Comment, "comments", limit=3)
    
    logger.info("\n미리보기 완료!")
    logger.info("실제 마이그레이션을 실행하려면 migrate_utc_to_kst.py를 실행하세요.")
    
    # 연결 종료
    client.close()


if __name__ == "__main__":
    asyncio.run(main())