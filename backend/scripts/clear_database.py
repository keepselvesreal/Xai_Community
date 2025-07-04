#!/usr/bin/env python3
"""
MongoDB Atlas 데이터베이스 정리 스크립트

이 스크립트는 현재 프로젝트의 MongoDB Atlas 데이터베이스에서 
모든 컬렉션의 데이터를 안전하게 삭제합니다.

주의: 이 작업은 되돌릴 수 없습니다. 실행 전 반드시 백업을 확인하세요.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nadle_backend.config import settings
from nadle_backend.database.connection import database

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'database_clear_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """MongoDB Atlas 데이터베이스 정리 클래스"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # 설정에서 컬렉션 이름들 가져오기
        self.collections = [
            settings.users_collection,
            settings.posts_collection,
            settings.comments_collection,
            settings.post_stats_collection,
            settings.user_reactions_collection,
            settings.files_collection,
            settings.stats_collection
        ]
    
    async def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            await database.connect()
            self.client = database.get_client()
            self.db = database.get_database()
            logger.info(f"✅ MongoDB Atlas 연결 성공: {settings.database_name}")
            return True
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {str(e)}")
            return False
    
    async def disconnect(self):
        """데이터베이스 연결 종료"""
        if database.is_connected:
            await database.disconnect()
            logger.info("✅ 데이터베이스 연결 종료")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """각 컬렉션의 현재 데이터 개수 조회"""
        stats = {}
        total_documents = 0
        
        logger.info("📊 컬렉션별 데이터 현황 조회 중...")
        
        for collection_name in self.collections:
            try:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = count
                total_documents += count
                logger.info(f"  📁 {collection_name}: {count:,}개 문서")
            except Exception as e:
                logger.warning(f"  ⚠️  {collection_name}: 조회 실패 ({str(e)})")
                stats[collection_name] = 0
        
        stats['total'] = total_documents
        logger.info(f"📊 총 {total_documents:,}개 문서 발견")
        return stats
    
    async def clear_collection(self, collection_name: str) -> Dict[str, Any]:
        """특정 컬렉션의 모든 데이터 삭제"""
        try:
            collection = self.db[collection_name]
            
            # 삭제 전 개수 확인
            before_count = await collection.count_documents({})
            
            if before_count == 0:
                logger.info(f"  📁 {collection_name}: 삭제할 데이터 없음")
                return {
                    'collection': collection_name,
                    'before_count': 0,
                    'deleted_count': 0,
                    'success': True
                }
            
            # 모든 문서 삭제
            result = await collection.delete_many({})
            
            # 삭제 후 개수 확인
            after_count = await collection.count_documents({})
            
            success = (after_count == 0 and result.deleted_count == before_count)
            
            if success:
                logger.info(f"  ✅ {collection_name}: {result.deleted_count:,}개 문서 삭제 완료")
            else:
                logger.warning(f"  ⚠️  {collection_name}: 삭제 불완전 (삭제: {result.deleted_count}, 남은 문서: {after_count})")
            
            return {
                'collection': collection_name,
                'before_count': before_count,
                'deleted_count': result.deleted_count,
                'after_count': after_count,
                'success': success
            }
            
        except Exception as e:
            logger.error(f"  ❌ {collection_name}: 삭제 실패 ({str(e)})")
            return {
                'collection': collection_name,
                'before_count': 0,
                'deleted_count': 0,
                'error': str(e),
                'success': False
            }
    
    async def clear_all_collections(self) -> Dict[str, Any]:
        """모든 컬렉션의 데이터 삭제"""
        logger.info("🗑️  모든 컬렉션 데이터 삭제 시작...")
        
        results = []
        total_deleted = 0
        
        for collection_name in self.collections:
            result = await self.clear_collection(collection_name)
            results.append(result)
            
            if result['success']:
                total_deleted += result['deleted_count']
        
        # 결과 요약
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"🎯 삭제 작업 완료:")
        logger.info(f"  ✅ 성공: {successful}개 컬렉션")
        logger.info(f"  ❌ 실패: {failed}개 컬렉션")
        logger.info(f"  🗑️  총 삭제된 문서: {total_deleted:,}개")
        
        return {
            'results': results,
            'total_deleted': total_deleted,
            'successful_collections': successful,
            'failed_collections': failed,
            'success': failed == 0
        }
    
    async def clear_specific_collections(self, collection_names: List[str]) -> Dict[str, Any]:
        """특정 컬렉션들만 삭제"""
        logger.info(f"🗑️  선택된 컬렉션 데이터 삭제 시작: {', '.join(collection_names)}")
        
        results = []
        total_deleted = 0
        
        for collection_name in collection_names:
            if collection_name not in self.collections:
                logger.warning(f"  ⚠️  알 수 없는 컬렉션: {collection_name}")
                continue
            
            result = await self.clear_collection(collection_name)
            results.append(result)
            
            if result['success']:
                total_deleted += result['deleted_count']
        
        # 결과 요약
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"🎯 삭제 작업 완료:")
        logger.info(f"  ✅ 성공: {successful}개 컬렉션")
        logger.info(f"  ❌ 실패: {failed}개 컬렉션")
        logger.info(f"  🗑️  총 삭제된 문서: {total_deleted:,}개")
        
        return {
            'results': results,
            'total_deleted': total_deleted,
            'successful_collections': successful,
            'failed_collections': failed,
            'success': failed == 0
        }


def confirm_deletion(stats: Dict[str, Any]) -> bool:
    """삭제 확인 대화"""
    print("\n" + "="*60)
    print("⚠️  MongoDB Atlas 데이터 삭제 확인")
    print("="*60)
    print(f"🎯 대상 데이터베이스: {settings.database_name}")
    print(f"🌐 MongoDB URL: {settings.mongodb_url[:50]}...")
    print()
    
    if stats['total'] == 0:
        print("📁 삭제할 데이터가 없습니다.")
        return False
    
    print("📊 삭제될 데이터:")
    for collection_name, count in stats.items():
        if collection_name != 'total' and count > 0:
            print(f"  📁 {collection_name}: {count:,}개 문서")
    
    print()
    print(f"🗑️  총 {stats['total']:,}개 문서가 삭제됩니다.")
    print()
    print("⚠️  주의사항:")
    print("  • 이 작업은 되돌릴 수 없습니다")
    print("  • 삭제 전 데이터 백업을 권장합니다")
    print("  • 프로덕션 환경에서는 특히 주의하세요")
    print()
    
    while True:
        response = input("정말로 모든 데이터를 삭제하시겠습니까? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("'yes' 또는 'no'를 입력해주세요.")


async def main():
    """메인 실행 함수"""
    print("🗑️  MongoDB Atlas 데이터베이스 정리 도구")
    print("="*60)
    
    cleaner = DatabaseCleaner()
    
    try:
        # 데이터베이스 연결
        if not await cleaner.connect():
            logger.error("❌ 데이터베이스 연결 실패. 프로그램을 종료합니다.")
            return
        
        # 현재 데이터 현황 조회
        stats = await cleaner.get_collection_stats()
        
        # 삭제 확인
        if not confirm_deletion(stats):
            logger.info("🚫 사용자가 삭제를 취소했습니다.")
            return
        
        # 데이터 삭제 실행
        print("\n🗑️  데이터 삭제를 시작합니다...")
        result = await cleaner.clear_all_collections()
        
        # 최종 결과 출력
        print("\n" + "="*60)
        print("🎯 최종 결과")
        print("="*60)
        
        if result['success']:
            print(f"✅ 모든 컬렉션 데이터 삭제 완료!")
            print(f"🗑️  총 {result['total_deleted']:,}개 문서 삭제됨")
        else:
            print(f"⚠️  일부 컬렉션에서 오류 발생")
            print(f"✅ 성공: {result['successful_collections']}개 컬렉션")
            print(f"❌ 실패: {result['failed_collections']}개 컬렉션")
            print(f"🗑️  삭제된 문서: {result['total_deleted']:,}개")
        
        # 삭제 후 상태 확인
        print("\n📊 삭제 후 데이터 현황:")
        final_stats = await cleaner.get_collection_stats()
        
        if final_stats['total'] == 0:
            print("✅ 모든 데이터가 성공적으로 삭제되었습니다!")
        else:
            print(f"⚠️  {final_stats['total']:,}개 문서가 남아있습니다.")
            for collection_name, count in final_stats.items():
                if collection_name != 'total' and count > 0:
                    print(f"  📁 {collection_name}: {count:,}개 문서")
        
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류 발생: {str(e)}")
        sys.exit(1)
    
    finally:
        await cleaner.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🚫 사용자가 프로그램을 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 프로그램 실행 중 오류: {str(e)}")
        sys.exit(1)