# Task 6: 데이터 마이그레이션

**Feature Group**: editor-integration  
**Task 제목**: 데이터 마이그레이션  
**작성 시각**: 2025-06-26  
**대상 파일**: `backend/src/migrations/add_content_fields.py` (신규 생성)

## 개요

기존 게시글 데이터를 새로운 콘텐츠 모델로 마이그레이션합니다. 기존의 단순 텍스트 콘텐츠를 확장된 필드 구조로 변환하고, 데이터 무결성을 보장하며, 롤백 기능을 제공합니다.

## 리스크 정보

**리스크 레벨**: 높음

**리스크 설명**:
- 기존 데이터 손실 위험 (대용량 데이터베이스)
- 마이그레이션 시간 오래 소요 가능
- 서비스 중단 시간 발생 가능성
- 롤백 실패 시 데이터 복구 어려움
- 메모리 사용량 급증 가능성

## Subtask 구성

### Subtask 6.1: 마이그레이션 스크립트

**테스트 함수**: `test_migration_script_execution()`

**설명**: 
- 기존 게시글 데이터를 새로운 스키마로 변환
- 배치 처리를 통한 안전한 마이그레이션
- 진행 상황 추적 및 로깅

**구현 요구사항**:
```python
"""
데이터 마이그레이션 스크립트: 콘텐츠 필드 추가
실행 방법: python -m migrations.add_content_fields
"""

import asyncio
import logging
import html
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from src.config import get_settings
from src.models.core import Post, PostMetadata
from src.services.content_service import ContentService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentFieldsMigration:
    """콘텐츠 필드 추가 마이그레이션"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.content_service = ContentService()
        self.batch_size = 100  # 배치 크기
        self.total_processed = 0
        self.total_failed = 0
        
    async def connect(self):
        """데이터베이스 연결"""
        try:
            self.client = AsyncIOMotorClient(self.settings.mongodb_url)
            self.db = self.client[self.settings.database_name]
            
            # 연결 테스트
            await self.client.admin.command('ping')
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def run_migration(self):
        """마이그레이션 실행"""
        try:
            await self.connect()
            
            # 마이그레이션 시작 로그
            logger.info("Starting content fields migration")
            start_time = datetime.now()
            
            # 총 게시글 수 확인
            total_posts = await self.db.posts.count_documents({})
            logger.info(f"Total posts to migrate: {total_posts}")
            
            if total_posts == 0:
                logger.info("No posts to migrate")
                return
            
            # 배치 단위로 마이그레이션 수행
            cursor = self.db.posts.find({})
            batch = []
            
            async for post_doc in cursor:
                batch.append(post_doc)
                
                if len(batch) >= self.batch_size:
                    await self._process_batch(batch)
                    batch = []
                    
                    # 진행률 출력
                    progress = (self.total_processed / total_posts) * 100
                    logger.info(f"Progress: {self.total_processed}/{total_posts} ({progress:.1f}%)")
            
            # 마지막 배치 처리
            if batch:
                await self._process_batch(batch)
            
            # 마이그레이션 완료 로그
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("Migration completed")
            logger.info(f"Total processed: {self.total_processed}")
            logger.info(f"Total failed: {self.total_failed}")
            logger.info(f"Duration: {duration}")
            
            # 검증 수행
            await self._verify_migration()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await self.disconnect()
    
    async def _process_batch(self, batch: list):
        """배치 처리"""
        operations = []
        
        for post_doc in batch:
            try:
                # 새로운 필드가 이미 있는지 확인
                if 'content_type' in post_doc:
                    logger.debug(f"Post {post_doc['_id']} already migrated, skipping")
                    self.total_processed += 1
                    continue
                
                # 마이그레이션 수행
                update_doc = await self._migrate_post(post_doc)
                
                if update_doc:
                    operations.append(
                        UpdateOne(
                            {"_id": post_doc["_id"]},
                            {"$set": update_doc}
                        )
                    )
                
                self.total_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate post {post_doc.get('_id', 'unknown')}: {e}")
                self.total_failed += 1
        
        # 배치 업데이트 실행
        if operations:
            try:
                result = await self.db.posts.bulk_write(operations, ordered=False)
                logger.debug(f"Batch update completed: {result.modified_count} documents updated")
            except Exception as e:
                logger.error(f"Batch update failed: {e}")
                raise
    
    async def _migrate_post(self, post_doc: dict) -> Optional[Dict[str, Any]]:
        """개별 게시글 마이그레이션"""
        try:
            content = post_doc.get('content', '')
            
            # 콘텐츠 타입 결정
            content_type = self._determine_content_type(content)
            
            # 콘텐츠 처리
            if content_type == "markdown":
                # 마크다운 콘텐츠 처리
                processed = await self.content_service.process_content(content, "markdown")
                content_rendered = processed["content_rendered"]
                word_count = processed["word_count"]
                reading_time = processed["reading_time"]
                content_text = processed["content_text"]
                inline_images = processed["inline_images"]
            else:
                # 플레인 텍스트 처리
                content_rendered = html.escape(content).replace('\n', '<br>')
                word_count = len(content.split())
                reading_time = max(1, word_count // 200)
                content_text = content
                inline_images = []
            
            # 메타데이터 업데이트
            metadata = post_doc.get('metadata', {})
            if isinstance(metadata, dict):
                metadata['inline_images'] = inline_images
                metadata['editor_type'] = 'markdown' if content_type == 'markdown' else 'plain'
            
            # 업데이트할 필드 구성
            update_doc = {
                'content_type': content_type,
                'content_rendered': content_rendered,
                'word_count': word_count,
                'reading_time': reading_time,
                'content_text': content_text,
                'metadata': metadata,
                'updated_at': datetime.now(timezone.utc)
            }
            
            return update_doc
            
        except Exception as e:
            logger.error(f"Error processing post content: {e}")
            return None
    
    def _determine_content_type(self, content: str) -> str:
        """콘텐츠 타입 결정"""
        import re
        
        # 마크다운 패턴 감지
        markdown_patterns = [
            r'^#{1,6}\s+',     # 헤딩
            r'\*\*.*?\*\*',    # 볼드
            r'\*.*?\*',        # 이탤릭
            r'!\[.*?\]\(.*?\)', # 이미지
            r'\[.*?\]\(.*?\)', # 링크
            r'^[-*+]\s+',      # 리스트
            r'```',            # 코드 블록
        ]
        
        for pattern in markdown_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return "markdown"
        
        return "text"
    
    async def _verify_migration(self):
        """마이그레이션 검증"""
        try:
            # 새로운 필드가 추가된 게시글 수 확인
            migrated_count = await self.db.posts.count_documents({
                "content_type": {"$exists": True}
            })
            
            total_count = await self.db.posts.count_documents({})
            
            logger.info(f"Verification: {migrated_count}/{total_count} posts have new fields")
            
            if migrated_count != total_count:
                logger.warning("Some posts may not have been migrated properly")
            else:
                logger.info("All posts successfully migrated")
            
            # 샘플 데이터 검증
            sample_posts = await self.db.posts.find({
                "content_type": {"$exists": True}
            }).limit(5).to_list(5)
            
            for post in sample_posts:
                required_fields = ['content_type', 'content_rendered', 'word_count', 'reading_time', 'content_text']
                missing_fields = [field for field in required_fields if field not in post]
                
                if missing_fields:
                    logger.warning(f"Post {post['_id']} missing fields: {missing_fields}")
                else:
                    logger.debug(f"Post {post['_id']} has all required fields")
                    
        except Exception as e:
            logger.error(f"Verification failed: {e}")
```

**검증 조건**:
- 모든 기존 게시글 처리
- 새로운 필드 정확한 설정
- 데이터 무결성 유지
- 성능 최적화 (배치 처리)

### Subtask 6.2: 롤백 스크립트

**테스트 함수**: `test_migration_rollback()`

**설명**: 
- 마이그레이션 실패 시 원상 복구
- 새로 추가된 필드 제거
- 원본 데이터 보존 확인

**구현 요구사항**:
```python
class ContentFieldsRollback:
    """콘텐츠 필드 마이그레이션 롤백"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.batch_size = 100
        self.total_processed = 0
    
    async def run_rollback(self):
        """롤백 실행"""
        try:
            await self.connect()
            
            logger.info("Starting content fields rollback")
            start_time = datetime.now()
            
            # 마이그레이션된 게시글 수 확인
            migrated_count = await self.db.posts.count_documents({
                "content_type": {"$exists": True}
            })
            
            logger.info(f"Posts to rollback: {migrated_count}")
            
            if migrated_count == 0:
                logger.info("No migrated posts found")
                return
            
            # 새로 추가된 필드들 제거
            fields_to_remove = {
                "content_type": 1,
                "content_rendered": 1,
                "word_count": 1,
                "reading_time": 1,
                "content_text": 1
            }
            
            # 메타데이터에서 새로 추가된 필드 제거
            await self.db.posts.update_many(
                {"content_type": {"$exists": True}},
                {
                    "$unset": fields_to_remove,
                    "$unset": {
                        "metadata.inline_images": 1,
                        "metadata.editor_type": 1
                    },
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            
            # 롤백 완료 로그
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("Rollback completed")
            logger.info(f"Duration: {duration}")
            
            # 롤백 검증
            await self._verify_rollback()
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
        finally:
            await self.disconnect()
    
    async def _verify_rollback(self):
        """롤백 검증"""
        try:
            # 새로운 필드가 남아있는 게시글 수 확인
            remaining_count = await self.db.posts.count_documents({
                "content_type": {"$exists": True}
            })
            
            if remaining_count == 0:
                logger.info("All new fields successfully removed")
            else:
                logger.warning(f"Some posts still have new fields: {remaining_count}")
            
            # 원본 필드 확인
            total_with_content = await self.db.posts.count_documents({
                "content": {"$exists": True}
            })
            
            total_posts = await self.db.posts.count_documents({})
            
            logger.info(f"Posts with original content field: {total_with_content}/{total_posts}")
            
        except Exception as e:
            logger.error(f"Rollback verification failed: {e}")
```

**검증 조건**:
- 새로 추가된 필드 완전 제거
- 원본 content 필드 보존
- 메타데이터 정리
- 데이터 무결성 유지

### Subtask 6.3: 데이터 검증

**테스트 함수**: `test_migrated_data_validation()`

**설명**: 
- 마이그레이션 후 데이터 품질 검증
- 필드 일관성 확인
- 성능 테스트

**구현 요구사항**:
```python
class MigrationValidator:
    """마이그레이션 데이터 검증"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.validation_results = {
            "total_posts": 0,
            "migrated_posts": 0,
            "validation_errors": [],
            "performance_issues": []
        }
    
    async def validate_migration(self):
        """마이그레이션 검증 실행"""
        try:
            await self.connect()
            
            logger.info("Starting migration validation")
            
            # 기본 통계
            await self._validate_basic_stats()
            
            # 필드 일관성 검증
            await self._validate_field_consistency()
            
            # 데이터 품질 검증
            await self._validate_data_quality()
            
            # 성능 검증
            await self._validate_performance()
            
            # 검증 결과 출력
            self._print_validation_results()
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
        finally:
            await self.disconnect()
    
    async def _validate_basic_stats(self):
        """기본 통계 검증"""
        self.validation_results["total_posts"] = await self.db.posts.count_documents({})
        self.validation_results["migrated_posts"] = await self.db.posts.count_documents({
            "content_type": {"$exists": True}
        })
        
        logger.info(f"Total posts: {self.validation_results['total_posts']}")
        logger.info(f"Migrated posts: {self.validation_results['migrated_posts']}")
    
    async def _validate_field_consistency(self):
        """필드 일관성 검증"""
        # 필수 필드 존재 확인
        required_fields = ['content_type', 'content_rendered', 'word_count', 'reading_time', 'content_text']
        
        for field in required_fields:
            count = await self.db.posts.count_documents({
                "content_type": {"$exists": True},
                field: {"$exists": False}
            })
            
            if count > 0:
                error = f"Missing {field} in {count} migrated posts"
                self.validation_results["validation_errors"].append(error)
                logger.error(error)
    
    async def _validate_data_quality(self):
        """데이터 품질 검증"""
        # 샘플 데이터 상세 검증
        sample_posts = await self.db.posts.find({
            "content_type": {"$exists": True}
        }).limit(100).to_list(100)
        
        for post in sample_posts:
            try:
                # 필드 타입 검증
                if not isinstance(post.get('word_count'), int):
                    self.validation_results["validation_errors"].append(
                        f"Post {post['_id']}: word_count is not integer"
                    )
                
                if not isinstance(post.get('reading_time'), int):
                    self.validation_results["validation_errors"].append(
                        f"Post {post['_id']}: reading_time is not integer"
                    )
                
                # 콘텐츠 일관성 검증
                content = post.get('content', '')
                content_text = post.get('content_text', '')
                
                if len(content_text) == 0 and len(content) > 0:
                    self.validation_results["validation_errors"].append(
                        f"Post {post['_id']}: content_text is empty but content exists"
                    )
                
                # 단어 수 검증 (대략적)
                actual_words = len(content.split())
                stored_words = post.get('word_count', 0)
                
                if abs(actual_words - stored_words) > actual_words * 0.2:  # 20% 오차 허용
                    self.validation_results["validation_errors"].append(
                        f"Post {post['_id']}: word count mismatch (actual: {actual_words}, stored: {stored_words})"
                    )
                    
            except Exception as e:
                self.validation_results["validation_errors"].append(
                    f"Post {post['_id']}: validation error - {str(e)}"
                )
    
    async def _validate_performance(self):
        """성능 검증"""
        import time
        
        # 검색 성능 테스트
        start_time = time.time()
        
        # 콘텐츠 타입별 검색
        await self.db.posts.find({"content_type": "markdown"}).count()
        
        # 단어 수 기준 정렬
        await self.db.posts.find({}).sort("word_count", -1).limit(10).to_list(10)
        
        # 텍스트 검색
        await self.db.posts.find({"content_text": {"$regex": "test", "$options": "i"}}).limit(10).to_list(10)
        
        elapsed = time.time() - start_time
        
        if elapsed > 5.0:  # 5초 이상 소요 시 성능 이슈
            self.validation_results["performance_issues"].append(
                f"Search queries took {elapsed:.2f} seconds (too slow)"
            )
        
        logger.info(f"Performance test completed in {elapsed:.2f} seconds")
    
    def _print_validation_results(self):
        """검증 결과 출력"""
        results = self.validation_results
        
        print("\n" + "="*50)
        print("MIGRATION VALIDATION RESULTS")
        print("="*50)
        print(f"Total Posts: {results['total_posts']}")
        print(f"Migrated Posts: {results['migrated_posts']}")
        print(f"Migration Coverage: {(results['migrated_posts']/results['total_posts']*100):.1f}%")
        
        if results['validation_errors']:
            print(f"\nValidation Errors ({len(results['validation_errors'])}):")
            for error in results['validation_errors'][:10]:  # 최대 10개만 표시
                print(f"  - {error}")
            if len(results['validation_errors']) > 10:
                print(f"  ... and {len(results['validation_errors']) - 10} more errors")
        else:
            print("\n✓ No validation errors found")
        
        if results['performance_issues']:
            print(f"\nPerformance Issues ({len(results['performance_issues'])}):")
            for issue in results['performance_issues']:
                print(f"  - {issue}")
        else:
            print("\n✓ No performance issues found")
        
        print("="*50)

# 실행 함수들
async def run_migration():
    """마이그레이션 실행"""
    migration = ContentFieldsMigration()
    await migration.run_migration()

async def run_rollback():
    """롤백 실행"""
    rollback = ContentFieldsRollback()
    await rollback.run_rollback()

async def run_validation():
    """검증 실행"""
    validator = MigrationValidator()
    await validator.validate_migration()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m migrations.add_content_fields [migrate|rollback|validate]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "migrate":
        asyncio.run(run_migration())
    elif command == "rollback":
        asyncio.run(run_rollback())
    elif command == "validate":
        asyncio.run(run_validation())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

**검증 조건**:
- 모든 필드 타입 정확성
- 데이터 일관성 확인
- 성능 벤치마크 통과
- 에러 케이스 처리

### Subtask 6.4: 안전 장치 및 백업

**테스트 함수**: `test_migration_safety_measures()`

**설명**: 
- 마이그레이션 전 데이터 백업
- 단계별 체크포인트
- 실패 시 자동 복구

**구현 요구사항**:
```python
class MigrationSafetyManager:
    """마이그레이션 안전 장치"""
    
    def __init__(self):
        self.settings = get_settings()
        self.backup_collection = f"posts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def create_backup(self):
        """백업 생성"""
        try:
            logger.info(f"Creating backup collection: {self.backup_collection}")
            
            # 기존 posts 컬렉션 복사
            pipeline = [{"$out": self.backup_collection}]
            await self.db.posts.aggregate(pipeline).to_list(None)
            
            # 백업 검증
            original_count = await self.db.posts.count_documents({})
            backup_count = await self.db[self.backup_collection].count_documents({})
            
            if original_count != backup_count:
                raise Exception(f"Backup verification failed: {original_count} != {backup_count}")
                
            logger.info(f"Backup created successfully: {backup_count} documents")
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise
    
    async def restore_from_backup(self):
        """백업에서 복원"""
        try:
            logger.info(f"Restoring from backup: {self.backup_collection}")
            
            # 백업 존재 확인
            collections = await self.db.list_collection_names()
            if self.backup_collection not in collections:
                raise Exception(f"Backup collection not found: {self.backup_collection}")
            
            # 기존 posts 컬렉션 삭제
            await self.db.posts.drop()
            
            # 백업에서 복원
            pipeline = [{"$out": "posts"}]
            await self.db[self.backup_collection].aggregate(pipeline).to_list(None)
            
            logger.info("Data restored from backup successfully")
            
        except Exception as e:
            logger.error(f"Restore from backup failed: {e}")
            raise
    
    async def cleanup_backup(self):
        """백업 정리"""
        try:
            await self.db[self.backup_collection].drop()
            logger.info(f"Backup collection {self.backup_collection} cleaned up")
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")
```

**검증 조건**:
- 완전한 백업 생성
- 빠른 복원 기능
- 백업 무결성 검증
- 자동 정리 기능

## 의존성 정보

**선행 조건**: 
- Task 1 (콘텐츠 모델 확장) - 새로운 스키마 정의
- Task 2 (콘텐츠 처리 서비스) - 마이그레이션 시 콘텐츠 처리

**외부 라이브러리**:
- `motor` - 비동기 MongoDB 드라이버
- `pymongo` - MongoDB 작업

**후속 작업**: 
- 마이그레이션 후 Task 4, 5의 기능 완전 활용 가능

## 테스트 요구사항

### 단위 테스트
```python
def test_migration_script_execution():
    """마이그레이션 스크립트 실행 테스트"""
    # 샘플 데이터로 마이그레이션 테스트
    # 필드 생성 확인
    # 데이터 일관성 확인
    pass

def test_migration_rollback():
    """마이그레이션 롤백 테스트"""
    # 롤백 후 필드 제거 확인
    # 원본 데이터 보존 확인
    pass

def test_migrated_data_validation():
    """마이그레이션된 데이터 검증 테스트"""
    # 필드 타입 검증
    # 데이터 품질 확인
    # 성능 테스트
    pass

def test_migration_safety_measures():
    """마이그레이션 안전 장치 테스트"""
    # 백업 생성/복원
    # 실패 시 자동 복구
    pass
```

### 통합 테스트
```python
def test_full_migration_workflow():
    """전체 마이그레이션 워크플로우 테스트"""
    # 백업 → 마이그레이션 → 검증 → 정리
    # 실패 시나리오 테스트
    # 대용량 데이터 테스트
    pass

def test_migration_performance():
    """마이그레이션 성능 테스트"""
    # 대용량 데이터 처리 시간
    # 메모리 사용량 확인
    # 배치 크기 최적화
    pass
```

## 구현 참고사항

### 1. 안전성 우선
- 마이그레이션 전 반드시 백업
- 배치 처리로 메모리 사용량 제한
- 실패 시 자동 롤백 메커니즘

### 2. 성능 고려
- 배치 크기 조정 (100-1000개)
- 인덱스 활용한 효율적 쿼리
- 진행 상황 모니터링

### 3. 운영 고려사항
- 서비스 중단 시간 최소화
- 점진적 마이그레이션 옵션
- 상세한 로깅 및 모니터링

### 4. 복구 계획
- 명확한 롤백 절차
- 백업 검증 프로세스
- 비상 연락체계

이 Task는 기존 데이터의 안전을 최우선으로 하면서 새로운 기능을 지원하는 데이터 구조로 전환하는 중요한 작업입니다.