# Task 5: 게시글 서비스 확장

**Feature Group**: editor-integration  
**Task 제목**: 게시글 서비스 확장  
**작성 시각**: 2025-06-26  
**대상 파일**: `backend/src/services/posts_service.py` (기존 파일 수정)

## 개요

기존 게시글 서비스에 콘텐츠 처리 기능을 통합하고, 새로운 필드 지원, 검색 기능 개선, 인라인 이미지 관리 등의 기능을 추가합니다. 이는 에디터 통합을 위한 핵심 비즈니스 로직을 담당합니다.

## 리스크 정보

**리스크 레벨**: 중간

**리스크 설명**:
- 기존 비즈니스 로직과의 통합 복잡성
- 성능 영향 최소화 필요 (콘텐츠 처리 오버헤드)
- 데이터 일관성 유지 (원본/렌더링 콘텐츠)
- 트랜잭션 처리 복잡성 증가

## Subtask 구성

### Subtask 5.1: 콘텐츠 처리 통합 (Social Unit)

**테스트 함수**: `test_post_service_content_processing()`

**설명**: 
- 게시글 저장 시 ContentService를 사용한 자동 콘텐츠 처리
- 원본 콘텐츠와 렌더링된 HTML 동시 관리
- 메타데이터 자동 추출 및 저장

**Social Unit 정보**: Task 2의 ContentService와 긴밀한 통합

**구현 요구사항**:
```python
from src.services.content_service import ContentService
from src.models.core import Post, PostCreate, PostUpdate
import logging

class PostsService:
    def __init__(self):
        # 기존 초기화 코드 유지
        self.content_service = ContentService()
        self.logger = logging.getLogger(__name__)
    
    async def create_post(self, post_data: PostCreate, current_user: User) -> Post:
        """게시글 생성 (확장된 콘텐츠 처리)"""
        try:
            # 콘텐츠 타입 결정
            content_type = self._determine_content_type(post_data)
            
            # 콘텐츠 처리
            processed_content = await self.content_service.process_content(
                post_data.content,
                content_type
            )
            
            # Post 객체 생성
            post_dict = post_data.dict()
            
            # 처리된 콘텐츠 정보 추가
            post_dict.update({
                "content_type": content_type,
                "content_rendered": processed_content["content_rendered"],
                "word_count": processed_content["word_count"],
                "reading_time": processed_content["reading_time"],
                "content_text": processed_content["content_text"]
            })
            
            # 메타데이터 확장
            if not post_dict.get("metadata"):
                post_dict["metadata"] = {}
            
            post_dict["metadata"].update({
                "inline_images": processed_content["inline_images"],
                "editor_type": content_type
            })
            
            # 기존 생성 로직 (slug 생성, author_id 설정 등)
            post_dict["author_id"] = str(current_user.id)
            post_dict["slug"] = await self._generate_unique_slug(post_dict["title"])
            
            # 데이터베이스 저장
            post = Post(**post_dict)
            await post.save()
            
            # 인라인 이미지 연결 처리
            await self._associate_inline_images(post, processed_content["inline_images"])
            
            self.logger.info(f"Post created with content processing: {post.slug}")
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to create post with content processing: {str(e)}")
            raise
    
    def _determine_content_type(self, post_data: PostCreate) -> str:
        """콘텐츠 타입 결정"""
        # 메타데이터에서 명시적 타입 확인
        if hasattr(post_data.metadata, 'editor_type'):
            type_mapping = {
                "markdown": "markdown",
                "wysiwyg": "html",
                "plain": "text"
            }
            return type_mapping.get(post_data.metadata.editor_type, "text")
        
        # 자동 감지 (마크다운 문법 패턴)
        if self._detect_markdown_syntax(post_data.content):
            return "markdown"
        
        return "text"
    
    def _detect_markdown_syntax(self, content: str) -> bool:
        """마크다운 문법 감지"""
        import re
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
                return True
        return False
```

**검증 조건**:
- 콘텐츠 타입 자동 감지 정확성
- 처리된 모든 필드 정상 저장
- 에러 발생 시 롤백 처리
- 기존 게시글 생성 호환성

### Subtask 5.2: 검색 기능 개선

**테스트 함수**: `test_search_with_html_content()`

**설명**: 
- HTML 태그 제거 후 순수 텍스트 검색
- 콘텐츠 타입별 검색 필터링
- 검색 결과 최적화

**구현 요구사항**:
```python
async def search_posts(
    self,
    query: str,
    content_type: Optional[str] = None,
    service_type: Optional[str] = None,
    sort_by: str = "created_at",
    page: int = 1,
    page_size: int = 20,
    current_user: Optional[User] = None
) -> Dict[str, Any]:
    """게시글 검색 (개선된 기능)"""
    try:
        # 검색 필터 구성
        filters = {}
        
        # 기본 필터 (기존 로직 유지)
        if service_type:
            filters["service"] = service_type
        
        # 새로운 필터: 콘텐츠 타입
        if content_type:
            filters["content_type"] = content_type
        
        # 텍스트 검색 쿼리 구성
        search_filters = []
        if query:
            # 순수 텍스트 필드에서 검색 (HTML 태그 제거된 텍스트)
            search_filters.append({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"content_text": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}}  # 후방 호환성
                ]
            })
        
        # 최종 쿼리 구성
        final_filter = {"$and": [filters] + search_filters} if search_filters else filters
        
        # 정렬 기준
        sort_criteria = self._build_sort_criteria(sort_by)
        
        # 페이지네이션 계산
        skip = (page - 1) * page_size
        
        # 검색 실행
        posts_cursor = Post.find(final_filter).sort(sort_criteria).skip(skip).limit(page_size)
        posts = await posts_cursor.to_list()
        
        # 총 개수 계산
        total = await Post.find(final_filter).count()
        
        # 응답 구성
        items = []
        for post in posts:
            item = {
                "_id": str(post.id),
                "id": str(post.id),
                "title": post.title,
                "slug": post.slug,
                "author_id": str(post.author_id),
                "service": post.service,
                "metadata": post.metadata,
                "created_at": post.created_at,
                "updated_at": post.updated_at
            }
            
            # 새로운 필드 추가 (있는 경우)
            if hasattr(post, 'content_type'):
                item["content_type"] = post.content_type
                item["word_count"] = post.word_count
                item["reading_time"] = post.reading_time
            
            # 검색어가 있는 경우 하이라이팅용 텍스트 제공
            if query and hasattr(post, 'content_text'):
                item["content_text"] = post.content_text[:200] + "..." if len(post.content_text) > 200 else post.content_text
            
            items.append(item)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        self.logger.error(f"Search failed: {str(e)}")
        raise

def _build_sort_criteria(self, sort_by: str):
    """정렬 기준 구성"""
    sort_mapping = {
        "created_at": [("created_at", -1)],
        "updated_at": [("updated_at", -1)],
        "title": [("title", 1)],
        "word_count": [("word_count", -1)],  # 새로운 정렬 기준
        "reading_time": [("reading_time", -1)]  # 새로운 정렬 기준
    }
    
    return sort_mapping.get(sort_by, [("created_at", -1)])
```

**검증 조건**:
- HTML 태그 제거된 텍스트 검색
- 콘텐츠 타입별 필터링
- 새로운 정렬 기준 동작
- 기존 검색 API 호환성

### Subtask 5.3: 인라인 이미지 연결 관리

**테스트 함수**: `test_inline_image_association()`

**설명**: 
- 게시글과 인라인 이미지 파일 연결 관리
- 삭제된 게시글의 인라인 이미지 정리
- 참조되지 않는 이미지 파일 관리

**구현 요구사항**:
```python
async def _associate_inline_images(self, post: Post, inline_image_ids: List[str]):
    """인라인 이미지와 게시글 연결"""
    if not inline_image_ids:
        return
    
    try:
        from src.models.core import FileRecord
        
        # 인라인 이미지 파일들의 attachment 정보 업데이트
        for file_id in inline_image_ids:
            file_record = await FileRecord.find_one({"file_id": file_id})
            if file_record:
                file_record.attachment_type = "inline"
                file_record.attachment_id = str(post.id)
                await file_record.save()
                
        self.logger.info(f"Associated {len(inline_image_ids)} inline images with post {post.slug}")
        
    except Exception as e:
        self.logger.warning(f"Failed to associate inline images: {str(e)}")
        # 이미지 연결 실패는 게시글 생성을 막지 않음

async def delete_post(self, slug: str, current_user: User) -> None:
    """게시글 삭제 (확장된 정리 기능)"""
    try:
        # 기존 삭제 로직
        post = await self.get_post_by_slug(slug)
        
        if post.author_id != str(current_user.id) and not current_user.is_admin:
            raise PostPermissionError("Insufficient permissions to delete this post")
        
        # 인라인 이미지 정리
        await self._cleanup_inline_images(post)
        
        # 게시글 삭제
        await post.delete()
        
        self.logger.info(f"Post deleted with cleanup: {slug}")
        
    except Exception as e:
        self.logger.error(f"Failed to delete post: {str(e)}")
        raise

async def _cleanup_inline_images(self, post: Post):
    """게시글 삭제 시 인라인 이미지 정리"""
    try:
        from src.models.core import FileRecord
        
        # 게시글에 연결된 인라인 이미지 찾기
        inline_files = await FileRecord.find({
            "attachment_type": "inline",
            "attachment_id": str(post.id)
        }).to_list()
        
        # 각 파일의 참조 확인 후 정리
        for file_record in inline_files:
            # 다른 게시글에서도 사용되는지 확인
            other_posts = await Post.find({
                "_id": {"$ne": post.id},
                "metadata.inline_images": file_record.file_id
            }).count()
            
            if other_posts == 0:
                # 다른 곳에서 사용되지 않으면 파일 삭제
                await self._delete_file_record(file_record)
            else:
                # 다른 곳에서 사용되면 연결만 해제
                file_record.attachment_type = None
                file_record.attachment_id = None
                await file_record.save()
        
        self.logger.info(f"Cleaned up inline images for post: {post.slug}")
        
    except Exception as e:
        self.logger.warning(f"Failed to cleanup inline images: {str(e)}")

async def _delete_file_record(self, file_record):
    """파일 레코드 및 실제 파일 삭제"""
    try:
        import os
        
        # 실제 파일 삭제
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        
        # 데이터베이스 레코드 삭제
        await file_record.delete()
        
        self.logger.info(f"Deleted file: {file_record.file_id}")
        
    except Exception as e:
        self.logger.error(f"Failed to delete file {file_record.file_id}: {str(e)}")
```

**검증 조건**:
- 인라인 이미지 연결 정확성
- 게시글 삭제 시 정리 동작
- 참조 계수 기반 파일 관리
- 실제 파일 시스템 정리

### Subtask 5.4: 게시글 업데이트 확장

**테스트 함수**: `test_post_update_with_content_processing()`

**설명**: 
- 게시글 수정 시 콘텐츠 재처리
- 인라인 이미지 변경 사항 반영
- 메타데이터 업데이트

**구현 요구사항**:
```python
async def update_post(self, slug: str, update_data: PostUpdate, current_user: User) -> Post:
    """게시글 수정 (확장된 콘텐츠 처리)"""
    try:
        # 기존 게시글 조회
        post = await self.get_post_by_slug(slug)
        
        if post.author_id != str(current_user.id) and not current_user.is_admin:
            raise PostPermissionError("Insufficient permissions to update this post")
        
        # 업데이트할 필드 구성
        update_fields = {}
        
        # 기본 필드 업데이트
        if update_data.title is not None:
            update_fields["title"] = update_data.title
        
        if update_data.status is not None:
            update_fields["status"] = update_data.status
        
        # 콘텐츠 업데이트 처리
        if update_data.content is not None:
            # 콘텐츠 타입 결정 (기존 유지 또는 새로 감지)
            current_type = getattr(post, 'content_type', 'text')
            content_type = current_type
            
            # 새로운 콘텐츠 처리
            processed_content = await self.content_service.process_content(
                update_data.content,
                content_type
            )
            
            # 콘텐츠 관련 필드 업데이트
            update_fields.update({
                "content": update_data.content,
                "content_rendered": processed_content["content_rendered"],
                "word_count": processed_content["word_count"],
                "reading_time": processed_content["reading_time"],
                "content_text": processed_content["content_text"],
                "updated_at": datetime.utcnow()
            })
            
            # 인라인 이미지 변경 처리
            old_inline_images = getattr(post.metadata, 'inline_images', []) if post.metadata else []
            new_inline_images = processed_content["inline_images"]
            
            if old_inline_images != new_inline_images:
                # 이전 연결 해제
                await self._disassociate_inline_images(post, old_inline_images)
                # 새로운 연결 설정
                await self._associate_inline_images(post, new_inline_images)
                
                # 메타데이터 업데이트
                if not post.metadata:
                    post.metadata = {}
                post.metadata.inline_images = new_inline_images
                update_fields["metadata"] = post.metadata
        
        # 메타데이터 업데이트
        if update_data.metadata is not None:
            merged_metadata = post.metadata.dict() if post.metadata else {}
            merged_metadata.update(update_data.metadata.dict(exclude_unset=True))
            update_fields["metadata"] = merged_metadata
        
        # 데이터베이스 업데이트
        await post.update({"$set": update_fields})
        
        # 업데이트된 게시글 반환
        updated_post = await self.get_post_by_slug(slug)
        
        self.logger.info(f"Post updated with content processing: {slug}")
        return updated_post
        
    except Exception as e:
        self.logger.error(f"Failed to update post: {str(e)}")
        raise

async def _disassociate_inline_images(self, post: Post, image_ids: List[str]):
    """인라인 이미지 연결 해제"""
    try:
        from src.models.core import FileRecord
        
        for file_id in image_ids:
            file_record = await FileRecord.find_one({
                "file_id": file_id,
                "attachment_type": "inline",
                "attachment_id": str(post.id)
            })
            
            if file_record:
                file_record.attachment_type = None
                file_record.attachment_id = None
                await file_record.save()
        
        self.logger.info(f"Disassociated {len(image_ids)} inline images from post {post.slug}")
        
    except Exception as e:
        self.logger.warning(f"Failed to disassociate inline images: {str(e)}")
```

**검증 조건**:
- 콘텐츠 변경 시 재처리
- 인라인 이미지 변경사항 반영
- 기존 연결 정리
- 메타데이터 정확한 업데이트

## 의존성 정보

**선행 조건**: 
- Task 1 (콘텐츠 모델 확장) - 새로운 필드 사용
- Task 2 (콘텐츠 처리 서비스) - ContentService 통합

**Social Unit 통합**:
- ContentService와 긴밀한 통합
- FileRecord 모델과의 연동

**후속 작업**: 
- Task 4 (Posts API)에서 이 서비스 사용
- Task 6 (마이그레이션) 시 기존 데이터 변환

## 테스트 요구사항

### 단위 테스트
```python
def test_post_service_content_processing():
    """게시글 서비스 콘텐츠 처리 테스트"""
    # 마크다운 게시글 생성
    # 자동 콘텐츠 타입 감지
    # 메타데이터 자동 추출
    # 인라인 이미지 연결
    pass

def test_search_with_html_content():
    """HTML 콘텐츠 검색 테스트"""
    # 순수 텍스트 검색
    # 콘텐츠 타입별 필터링
    # 새로운 정렬 기준
    pass

def test_inline_image_association():
    """인라인 이미지 연결 테스트"""
    # 이미지 연결 생성
    # 게시글 삭제 시 정리
    # 참조 계수 관리
    pass

def test_post_update_with_content_processing():
    """콘텐츠 처리 포함 게시글 수정 테스트"""
    # 콘텐츠 재처리
    # 인라인 이미지 변경
    # 메타데이터 업데이트
    pass
```

### 통합 테스트
```python
def test_posts_service_integration():
    """게시글 서비스 통합 테스트"""
    # 전체 CRUD 플로우
    # ContentService 통합
    # 파일 시스템 연동
    pass

def test_service_performance():
    """서비스 성능 테스트"""
    # 콘텐츠 처리 성능
    # 검색 성능
    # 대용량 데이터 처리
    pass
```

## 구현 참고사항

### 1. 트랜잭션 처리
- 콘텐츠 처리 실패 시 롤백
- 파일 연결 실패는 게시글 생성 차단하지 않음
- 일관된 데이터 상태 유지

### 2. 성능 최적화
- 콘텐츠 처리 캐싱 고려
- 검색 인덱스 최적화
- 비동기 처리 활용

### 3. 에러 처리
- 부분 실패 허용 (이미지 연결 등)
- 명확한 에러 로깅
- 복구 가능한 상태 유지

### 4. 호환성 유지
- 기존 게시글과의 호환성
- 점진적 마이그레이션 지원
- 새로운 필드는 Optional 처리

이 Task는 에디터 통합의 핵심 비즈니스 로직을 담당하므로 안정성과 확장성을 모두 고려해야 합니다.