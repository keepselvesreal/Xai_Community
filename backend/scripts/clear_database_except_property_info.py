#!/usr/bin/env python3
"""
MongoDB Atlas 데이터베이스 정리 스크립트 (부동산 정보 게시글 제외)

이 스크립트는 현재 프로젝트의 MongoDB Atlas 데이터베이스에서 
부동산 정보 게시글(property_information)을 제외한 모든 데이터를 안전하게 삭제합니다.

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
        logging.FileHandler(f'database_clear_except_property_info_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class SelectiveDatabaseCleaner:
    """부동산 정보 게시글을 제외한 MongoDB Atlas 데이터베이스 정리 클래스"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # 완전 삭제할 컬렉션들
        self.collections_to_clear = [
            settings.users_collection,
            settings.comments_collection,
            settings.post_stats_collection,
            settings.user_reactions_collection,
            settings.files_collection,
            settings.stats_collection
        ]
        
        # 부분 삭제할 컬렉션 (posts - property_information 제외)
        self.posts_collection = settings.posts_collection
    
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
        
        # 완전 삭제 대상 컬렉션들
        for collection_name in self.collections_to_clear:
            try:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = count
                total_documents += count
                logger.info(f"  📁 {collection_name}: {count:,}개 문서 (전체 삭제 예정)")
            except Exception as e:
                logger.warning(f"  ⚠️  {collection_name}: 조회 실패 ({str(e)})")
                stats[collection_name] = 0
        
        # posts 컬렉션 세부 분석
        try:
            posts_collection = self.db[self.posts_collection]
            total_posts = await posts_collection.count_documents({})
            property_info_posts = await posts_collection.count_documents({
                "metadata.type": "property_information"
            })
            other_posts = total_posts - property_info_posts
            
            stats[f'{self.posts_collection}_total'] = total_posts
            stats[f'{self.posts_collection}_property_info'] = property_info_posts
            stats[f'{self.posts_collection}_others'] = other_posts
            
            total_documents += other_posts  # 삭제될 게시글만 카운트
            
            logger.info(f"  📁 {self.posts_collection}: {total_posts:,}개 문서")
            logger.info(f"    🏡 부동산 정보 (보존): {property_info_posts:,}개")
            logger.info(f"    🗑️  기타 게시글 (삭제): {other_posts:,}개")
            
        except Exception as e:
            logger.warning(f"  ⚠️  {self.posts_collection}: 조회 실패 ({str(e)})")
            stats[f'{self.posts_collection}_total'] = 0
            stats[f'{self.posts_collection}_property_info'] = 0
            stats[f'{self.posts_collection}_others'] = 0
        
        stats['total_to_delete'] = total_documents
        logger.info(f"🗑️  총 {total_documents:,}개 문서 삭제 예정")
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
    
    async def clear_posts_except_property_info(self) -> Dict[str, Any]:
        """부동산 정보 게시글을 제외한 모든 게시글 삭제"""
        try:
            collection = self.db[self.posts_collection]
            
            # 삭제 전 개수 확인
            total_before = await collection.count_documents({})
            property_info_count = await collection.count_documents({
                "metadata.type": "property_information"
            })
            others_before = total_before - property_info_count
            
            if others_before == 0:
                logger.info(f"  📁 {self.posts_collection}: 삭제할 게시글 없음 (부동산 정보만 {property_info_count}개 존재)")
                return {
                    'collection': self.posts_collection,
                    'before_count': others_before,
                    'deleted_count': 0,
                    'preserved_count': property_info_count,
                    'success': True
                }
            
            # 부동산 정보가 아닌 게시글들 삭제
            result = await collection.delete_many({
                "metadata.type": {"$ne": "property_information"}
            })
            
            # 삭제 후 개수 확인
            total_after = await collection.count_documents({})
            property_info_after = await collection.count_documents({
                "metadata.type": "property_information"
            })
            
            success = (total_after == property_info_after and result.deleted_count == others_before)
            
            if success:
                logger.info(f"  ✅ {self.posts_collection}: {result.deleted_count:,}개 게시글 삭제 완료")
                logger.info(f"    🏡 부동산 정보 보존: {property_info_after:,}개")
            else:
                logger.warning(f"  ⚠️  {self.posts_collection}: 삭제 불완전")
                logger.warning(f"    🗑️  삭제된 게시글: {result.deleted_count:,}개")
                logger.warning(f"    🏡 남은 부동산 정보: {property_info_after:,}개")
                logger.warning(f"    📊 총 남은 게시글: {total_after:,}개")
            
            return {
                'collection': self.posts_collection,
                'before_count': others_before,
                'deleted_count': result.deleted_count,
                'preserved_count': property_info_after,
                'total_after': total_after,
                'success': success
            }
            
        except Exception as e:
            logger.error(f"  ❌ {self.posts_collection}: 삭제 실패 ({str(e)})")
            return {
                'collection': self.posts_collection,
                'before_count': 0,
                'deleted_count': 0,
                'preserved_count': 0,
                'error': str(e),
                'success': False
            }
    
    async def clear_selected_data(self) -> Dict[str, Any]:
        """선택적 데이터 삭제 실행"""
        logger.info("🗑️  선택적 데이터 삭제 시작...")
        
        results = []
        total_deleted = 0
        
        # 1. 완전 삭제 대상 컬렉션들 처리
        for collection_name in self.collections_to_clear:
            result = await self.clear_collection(collection_name)
            results.append(result)
            
            if result['success']:
                total_deleted += result['deleted_count']
        
        # 2. posts 컬렉션 부분 삭제
        posts_result = await self.clear_posts_except_property_info()
        results.append(posts_result)
        
        if posts_result['success']:
            total_deleted += posts_result['deleted_count']
        
        # 결과 요약
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"🎯 삭제 작업 완료:")
        logger.info(f"  ✅ 성공: {successful}개 컬렉션")
        logger.info(f"  ❌ 실패: {failed}개 컬렉션")
        logger.info(f"  🗑️  총 삭제된 문서: {total_deleted:,}개")
        if 'preserved_count' in posts_result:
            logger.info(f"  🏡 보존된 부동산 정보: {posts_result['preserved_count']:,}개")
        
        return {
            'results': results,
            'total_deleted': total_deleted,
            'successful_collections': successful,
            'failed_collections': failed,
            'success': failed == 0
        }


def confirm_deletion(stats: Dict[str, Any], auto_confirm: bool = False) -> bool:
    """삭제 확인 대화"""
    print("\n" + "="*60)
    print("⚠️  MongoDB Atlas 선택적 데이터 삭제 확인")
    print("="*60)
    print(f"🎯 대상 데이터베이스: {settings.database_name}")
    print(f"🌐 MongoDB URL: {settings.mongodb_url[:50]}...")
    print()
    
    if stats['total_to_delete'] == 0:
        print("📁 삭제할 데이터가 없습니다.")
        return False
    
    print("📊 삭제될 데이터:")
    for key, count in stats.items():
        if key.endswith('_total') or key.endswith('_property_info') or key.endswith('_others'):
            continue
        if key not in ['total_to_delete'] and count > 0:
            print(f"  📁 {key}: {count:,}개 문서 (전체 삭제)")
    
    # posts 상세 정보
    if f'{settings.posts_collection}_others' in stats:
        others = stats[f'{settings.posts_collection}_others']
        preserved = stats[f'{settings.posts_collection}_property_info']
        if others > 0:
            print(f"  📁 {settings.posts_collection}: {others:,}개 문서 삭제 (부동산 정보 {preserved:,}개 보존)")
    
    print()
    print(f"🗑️  총 {stats['total_to_delete']:,}개 문서가 삭제됩니다.")
    if f'{settings.posts_collection}_property_info' in stats:
        preserved = stats[f'{settings.posts_collection}_property_info']
        print(f"🏡 부동산 정보 게시글 {preserved:,}개는 보존됩니다.")
    print()
    print("⚠️  주의사항:")
    print("  • 이 작업은 되돌릴 수 없습니다")
    print("  • 삭제 전 데이터 백업을 권장합니다")
    print("  • 부동산 정보 게시글만 보존됩니다")
    print()
    
    if auto_confirm:
        print("🤖 자동 확인 모드: 삭제를 진행합니다.")
        return True
    
    while True:
        response = input("정말로 선택된 데이터를 삭제하시겠습니까? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("'yes' 또는 'no'를 입력해주세요.")


async def main(auto_confirm: bool = False):
    """메인 실행 함수"""
    print("🗑️  MongoDB Atlas 선택적 데이터베이스 정리 도구")
    print("🏡 부동산 정보 게시글 보존 모드")
    print("="*60)
    
    cleaner = SelectiveDatabaseCleaner()
    
    try:
        # 데이터베이스 연결
        if not await cleaner.connect():
            logger.error("❌ 데이터베이스 연결 실패. 프로그램을 종료합니다.")
            return
        
        # 현재 데이터 현황 조회
        stats = await cleaner.get_collection_stats()
        
        # 삭제 확인
        if not confirm_deletion(stats, auto_confirm):
            logger.info("🚫 사용자가 삭제를 취소했습니다.")
            return
        
        # 데이터 삭제 실행
        print("\n🗑️  선택적 데이터 삭제를 시작합니다...")
        result = await cleaner.clear_selected_data()
        
        # 최종 결과 출력
        print("\n" + "="*60)
        print("🎯 최종 결과")
        print("="*60)
        
        if result['success']:
            print(f"✅ 선택적 데이터 삭제 완료!")
            print(f"🗑️  총 {result['total_deleted']:,}개 문서 삭제됨")
        else:
            print(f"⚠️  일부 컬렉션에서 오류 발생")
            print(f"✅ 성공: {result['successful_collections']}개 컬렉션")
            print(f"❌ 실패: {result['failed_collections']}개 컬렉션")
            print(f"🗑️  삭제된 문서: {result['total_deleted']:,}개")
        
        # 삭제 후 상태 확인
        print("\n📊 삭제 후 데이터 현황:")
        final_stats = await cleaner.get_collection_stats()
        
        property_info_preserved = final_stats.get(f'{settings.posts_collection}_property_info', 0)
        if property_info_preserved > 0:
            print(f"✅ 부동산 정보 게시글 {property_info_preserved:,}개가 성공적으로 보존되었습니다!")
        
        total_remaining = final_stats.get('total_to_delete', 0)
        if total_remaining == 0:
            print("✅ 모든 대상 데이터가 성공적으로 삭제되었습니다!")
        else:
            print(f"⚠️  {total_remaining:,}개 문서가 예상치 못하게 남아있습니다.")
        
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류 발생: {str(e)}")
        sys.exit(1)
    
    finally:
        await cleaner.disconnect()


if __name__ == "__main__":
    try:
        # 명령줄 인자로 자동 확인 모드 설정
        auto_confirm = len(sys.argv) > 1 and sys.argv[1] == "--auto-confirm"
        asyncio.run(main(auto_confirm))
    except KeyboardInterrupt:
        print("\n\n🚫 사용자가 프로그램을 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 프로그램 실행 중 오류: {str(e)}")
        sys.exit(1)