# Task 4: 게시글 API 확장

**Feature Group**: editor-integration  
**Task 제목**: 게시글 API 확장  
**작성 시각**: 2025-06-26  
**대상 파일**: `backend/src/routers/posts.py` (기존 파일 수정)

## 개요

기존 게시글 API에 에디터 통합을 위한 기능을 추가합니다. 콘텐츠 미리보기, 새로운 필드 지원, 응답 형식 확장 등을 통해 다양한 에디터 형식을 지원하는 API로 확장합니다.

## 리스크 정보

**리스크 레벨**: 낮음

**리스크 설명**:
- 기존 API 호환성 유지하며 확장 (하위 호환성)
- 점진적 기능 추가로 기존 기능에 영향 최소
- 응답 형식 확장 시 클라이언트 대응 필요
- 성능 영향 최소화 필요

## Subtask 구성

### Subtask 4.1: 콘텐츠 미리보기 엔드포인트

**테스트 함수**: `test_content_preview_endpoint()`

**설명**: 
- 게시글 저장 전 실시간 콘텐츠 미리보기
- 마크다운 → HTML 변환 미리보기
- 메타데이터 정보 (단어 수, 읽기 시간) 제공

**구현 요구사항**:
```python
from pydantic import BaseModel
from src.services.content_service import ContentService

class PreviewRequest(BaseModel):
    """미리보기 요청 모델"""
    content: str
    content_type: str = "markdown"

class PreviewResponse(BaseModel):
    """미리보기 응답 모델"""
    content_rendered: str
    word_count: int
    reading_time: int
    inline_images: List[str]
    processing_time: float

@router.post("/preview", response_model=PreviewResponse)
async def preview_content(
    request: PreviewRequest,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    content_service: ContentService = Depends(get_content_service)
):
    """콘텐츠 실시간 미리보기"""
    import time
    start_time = time.time()
    
    try:
        # 콘텐츠 처리 (캐싱 없이 즉시 처리)
        result = await content_service.preview_content(
            request.content,
            request.content_type
        )
        
        processing_time = time.time() - start_time
        
        return PreviewResponse(
            content_rendered=result["content_rendered"],
            word_count=result["word_count"],
            reading_time=result["reading_time"],
            inline_images=result["inline_images"],
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Preview generation failed: {str(e)}"
        )
```

**검증 조건**:
- 인증 선택적 (로그인 없이도 미리보기 가능)
- 마크다운, HTML, 텍스트 형식 지원
- 응답 시간 1초 이내
- XSS 방지된 안전한 HTML 반환

### Subtask 4.2: 게시글 응답 확장 (Social Unit)

**테스트 함수**: `test_post_response_content_fields()`

**설명**: 
- 기존 게시글 조회 API 응답에 새로운 콘텐츠 필드 추가
- 하위 호환성 유지하며 점진적 확장
- 클라이언트 요청에 따라 상세 정보 제공

**Social Unit 정보**: Task 2의 ContentService와 통합

**구현 요구사항**:
```python
# 기존 get_post 엔드포인트 확장
@router.get("/{slug}", response_model=Dict[str, Any])
async def get_post(
    slug: str,
    include_content_meta: bool = Query(False, description="Include content metadata"),
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """게시글 상세 조회 (확장된 응답)"""
    try:
        post = await posts_service.get_post(slug, current_user)
        
        # 기본 응답 구성 (기존과 동일)
        response = {
            "id": str(post.id),
            "_id": str(post.id),
            "title": post.title,
            "content": post.content,  # 원본 콘텐츠
            "slug": post.slug,
            "service": post.service,
            "metadata": post.metadata,
            "file_ids": post.metadata.file_ids if post.metadata else [],
            "author_id": str(post.author_id),
            "status": post.status,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at,
            "stats": await posts_service._calculate_post_stats(str(post.id))
        }
        
        # 확장 정보 추가 (요청 시)
        if include_content_meta and hasattr(post, 'content_type'):
            response.update({
                "content_type": getattr(post, 'content_type', 'text'),
                "content_rendered": getattr(post, 'content_rendered', None),
                "word_count": getattr(post, 'word_count', None),
                "reading_time": getattr(post, 'reading_time', None),
                "content_text": getattr(post, 'content_text', None)
            })
            
            # 인라인 이미지 정보
            if hasattr(post.metadata, 'inline_images'):
                response["inline_images"] = post.metadata.inline_images
        
        # 사용자 반응 정보 (기존 로직 유지)
        if current_user:
            # ... 기존 user_reaction 로직
            pass
            
        return response
        
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get post: {str(e)}")
```

**검증 조건**:
- 기존 클라이언트 호환성 유지
- 새로운 필드는 선택적 제공
- 성능 영향 최소화
- 점진적 마이그레이션 지원

### Subtask 4.3: 게시글 생성/수정 확장

**테스트 함수**: `test_post_create_with_content_type()`

**설명**: 
- 게시글 생성/수정 시 새로운 콘텐츠 필드 처리
- 콘텐츠 타입별 자동 처리
- 인라인 이미지 연결 관리

**구현 요구사항**:
```python
# PostCreate 모델 확장 (models/core.py에서 이미 정의됨)
# 기존 create_post 엔드포인트 수정

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """게시글 생성 (확장된 기능)"""
    try:
        # 콘텐츠 타입 감지 (클라이언트에서 지정하지 않은 경우)
        if not hasattr(post_data.metadata, 'editor_type'):
            # 마크다운 문법 감지
            if detect_markdown_syntax(post_data.content):
                post_data.metadata.editor_type = "markdown"
            else:
                post_data.metadata.editor_type = "plain"
        
        # 게시글 생성 (PostsService에서 콘텐츠 처리)
        post = await posts_service.create_post(post_data, current_user)
        
        # 응답 생성 (기존과 동일)
        return PostResponse(
            id=str(post.id),
            title=post.title,
            content=post.content,
            slug=post.slug,
            service=post.service,
            metadata=post.metadata,
            author_id=str(post.author_id),
            status=post.status,
            created_at=post.created_at,
            updated_at=post.updated_at,
            published_at=post.published_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create post: {str(e)}"
        )

def detect_markdown_syntax(content: str) -> bool:
    """마크다운 문법 감지"""
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
- 자동 콘텐츠 타입 감지
- 인라인 이미지 file_id 추출 및 연결
- 메타데이터 자동 생성
- 기존 게시글 생성 API 호환성

### Subtask 4.4: 검색 API 개선

**테스트 함수**: `test_search_with_enhanced_content()`

**설명**: 
- HTML 태그 제거 후 검색
- 콘텐츠 타입별 검색 옵션
- 검색 결과 하이라이팅 개선

**구현 요구사항**:
```python
@router.get("/search", response_model=Dict[str, Any])
async def search_posts(
    q: str = Query(..., description="Search query"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    sort_by: str = Query("created_at", description="Sort field"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """게시글 검색 (개선된 기능)"""
    try:
        result = await posts_service.search_posts(
            query=q,
            content_type=content_type,  # 새로운 필터
            service_type=service_type,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            current_user=current_user
        )
        
        # 검색 결과 후처리
        if "items" in result:
            for item in result["items"]:
                # 기존 ID 변환 로직 유지
                if "_id" in item:
                    item["_id"] = str(item["_id"])
                if "id" in item:
                    item["id"] = str(item["id"])
                if "author_id" in item:
                    item["author_id"] = str(item["author_id"])
                
                # 새로운 필드 추가
                if "metadata" in item and item["metadata"]:
                    item["file_ids"] = item["metadata"].get("file_ids", [])
                    item["inline_images"] = item["metadata"].get("inline_images", [])
                
                # 검색어 하이라이팅 (HTML 안전)
                if "content_text" in item:
                    item["highlighted_content"] = highlight_search_term(
                        item["content_text"], q
                    )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

def highlight_search_term(text: str, term: str) -> str:
    """검색어 하이라이팅 (HTML 안전)"""
    if not term or not text:
        return text
    
    # HTML 이스케이프
    escaped_text = html.escape(text)
    escaped_term = html.escape(term)
    
    # 대소문자 무시하고 하이라이팅
    pattern = re.compile(re.escape(escaped_term), re.IGNORECASE)
    highlighted = pattern.sub(
        f'<mark>{escaped_term}</mark>',
        escaped_text
    )
    
    return highlighted
```

**검증 조건**:
- 순수 텍스트 기반 검색
- 콘텐츠 타입별 필터링
- HTML 안전한 하이라이팅
- 성능 최적화된 검색

## 의존성 정보

**선행 조건**: 
- Task 1 (콘텐츠 모델 확장) - 새로운 필드 사용
- Task 2 (콘텐츠 처리 서비스) - 미리보기 기능에서 사용

**Social Unit 통합**:
- ContentService와 긴밀한 통합
- PostsService 확장 필요

**후속 작업**: 
- Task 5 (PostsService 확장)와 동시 작업
- Task 7 (UI 통합)에서 새로운 API 사용

## 테스트 요구사항

### 단위 테스트
```python
def test_content_preview_endpoint():
    """콘텐츠 미리보기 테스트"""
    # 마크다운 미리보기
    # HTML 미리보기
    # 텍스트 미리보기
    # 에러 처리 테스트
    pass

def test_post_response_content_fields():
    """게시글 응답 확장 테스트"""
    # 기본 응답 호환성
    # 확장 필드 포함 응답
    # 선택적 메타데이터 포함
    pass

def test_post_create_with_content_type():
    """콘텐츠 타입 포함 게시글 생성 테스트"""
    # 마크다운 게시글 생성
    # 자동 타입 감지
    # 인라인 이미지 연결
    pass

def test_search_with_enhanced_content():
    """개선된 검색 기능 테스트"""
    # 콘텐츠 타입별 검색
    # 하이라이팅 기능
    # HTML 태그 제거 후 검색
    pass
```

### 통합 테스트
```python
def test_posts_api_integration():
    """게시글 API 통합 테스트"""
    # 전체 CRUD 플로우
    # 새로운 필드 포함 동작
    # 기존 클라이언트 호환성
    pass

def test_api_performance():
    """API 성능 테스트"""
    # 미리보기 응답 시간
    # 검색 성능
    # 메타데이터 처리 성능
    pass
```

### API 테스트
```python
def test_api_endpoints():
    """API 엔드포인트 테스트"""
    # POST /api/posts/preview
    # GET /api/posts/{slug}?include_content_meta=true
    # GET /api/posts/search?content_type=markdown
    # HTTP 상태 코드 검증
    pass
```

## 구현 참고사항

### 1. 하위 호환성 유지
- 기존 클라이언트가 영향받지 않도록 설계
- 새로운 필드는 선택적 제공
- 응답 구조 변경 최소화

### 2. 성능 고려사항
- 미리보기는 캐싱 없이 즉시 처리
- 확장 필드는 요청 시에만 포함
- 검색 성능 최적화

### 3. 보안 강화
- 미리보기에도 XSS 방지 적용
- 검색어 하이라이팅 시 HTML 이스케이프
- 입력 검증 강화

### 4. 사용성 개선
- 자동 콘텐츠 타입 감지
- 직관적인 API 파라미터
- 명확한 에러 메시지

이 Task는 기존 안정성을 유지하면서 새로운 기능을 점진적으로 추가하는 것이 핵심입니다.