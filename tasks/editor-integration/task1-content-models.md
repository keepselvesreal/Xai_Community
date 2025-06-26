# Task 1: 콘텐츠 모델 확장

**Feature Group**: editor-integration  
**Task 제목**: 콘텐츠 모델 확장  
**작성 시각**: 2025-06-26  
**대상 파일**: `backend/src/models/content.py` (신규 생성)

## 개요

에디터 통합을 위한 확장된 콘텐츠 모델을 정의합니다. 기존 Post 모델에 콘텐츠 타입, 렌더링된 HTML, 메타데이터 등의 필드를 추가하여 다양한 에디터 형식을 지원합니다.

## 리스크 정보

**리스크 레벨**: 중간

**리스크 설명**:
- 기존 Post 모델과의 호환성 유지 필요
- 데이터베이스 마이그레이션 시 기존 데이터 영향
- 새로운 필드 검증 로직의 복잡성

## Subtask 구성

### Subtask 1.1: 콘텐츠 타입 정의

**테스트 함수**: `test_content_type_enum_validation()`

**설명**: 
- ContentType enum 정의 및 유효성 검증
- 지원 타입: "text", "markdown", "html"
- 기본값 및 제약 조건 설정

**구현 요구사항**:
```python
ContentType = Literal["text", "markdown", "html"]

# 검증 로직
- 허용된 타입만 입력 가능
- 기본값: "text"
- 대소문자 구분 없이 처리
```

### Subtask 1.2: 확장된 Post 모델

**테스트 함수**: `test_post_content_fields_validation()`

**설명**: 
- Post 모델에 새로운 콘텐츠 관련 필드 추가
- 기존 content 필드는 원본 에디터 데이터 저장
- content_rendered 필드는 렌더링된 HTML 저장

**구현 요구사항**:
```python
class Post(Document, PostBase):
    # 기존 필드 유지
    content: str = Field(..., min_length=1)
    
    # 새로 추가되는 필드
    content_type: ContentType = "text"
    content_rendered: Optional[str] = None
    word_count: Optional[int] = None
    reading_time: Optional[int] = None  # 분 단위
    content_text: Optional[str] = None  # 검색용 순수 텍스트
```

**검증 조건**:
- content_type이 "markdown"인 경우 content_rendered 필수
- word_count는 0 이상의 정수
- reading_time은 1 이상의 정수

### Subtask 1.3: PostMetadata 확장

**테스트 함수**: `test_post_metadata_inline_images()`

**설명**: 
- PostMetadata 모델에 에디터 관련 메타데이터 추가
- 인라인 이미지 file_id 목록 관리
- 에디터 타입 정보 저장

**구현 요구사항**:
```python
class PostMetadata(BaseModel):
    # 기존 필드 유지
    type: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list, max_items=3)
    attachments: Optional[List[str]] = Field(default_factory=list)
    file_ids: Optional[List[str]] = Field(default_factory=list)
    thumbnail: Optional[str] = None
    visibility: Literal["public", "private"] = "public"
    
    # 새로 추가되는 필드
    inline_images: Optional[List[str]] = Field(default_factory=list)  # 인라인 이미지 file_ids
    editor_type: Literal["plain", "markdown", "wysiwyg"] = "plain"
```

**검증 조건**:
- inline_images는 유효한 file_id 형식 (UUID)
- editor_type은 정의된 값만 허용
- inline_images 최대 10개 제한

### Subtask 1.4: 데이터베이스 인덱스 설정

**테스트 함수**: `test_content_model_indexes()`

**설명**: 
- 새로운 필드에 대한 적절한 데이터베이스 인덱스 설정
- 검색 성능 및 필터링 최적화

**구현 요구사항**:
```python
class Post(Document, PostBase):
    class Settings:
        name = "posts"
        indexes = [
            # 기존 인덱스 유지
            [("slug", ASCENDING)],
            [("author_id", ASCENDING), ("created_at", DESCENDING)],
            [("service", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
            
            # 새로 추가되는 인덱스
            [("content_type", ASCENDING)],
            [("word_count", DESCENDING)],
            [("content_text", "text")]  # 전문 검색용
        ]
```

## 의존성 정보

**선행 조건**: 없음 (독립적으로 구현 가능)

**후속 작업**: 
- Task 2 (콘텐츠 처리 서비스)가 이 모델을 사용
- Task 6 (데이터 마이그레이션)에서 기존 데이터 변환

## 테스트 요구사항

### 단위 테스트
```python
def test_content_type_enum_validation():
    """ContentType enum 검증 테스트"""
    # 유효한 타입 테스트
    # 무효한 타입 거부 테스트
    # 기본값 테스트
    pass

def test_post_content_fields_validation():
    """Post 모델 새 필드 검증 테스트"""
    # 필수 필드 검증
    # 선택 필드 기본값 테스트
    # 데이터 타입 검증
    pass

def test_post_metadata_inline_images():
    """PostMetadata 인라인 이미지 필드 테스트"""
    # inline_images 리스트 검증
    # UUID 형식 검증
    # 최대 개수 제한 테스트
    pass

def test_content_model_indexes():
    """인덱스 생성 및 성능 테스트"""
    # 인덱스 존재 확인
    # 쿼리 성능 테스트
    pass
```

### 통합 테스트
```python
def test_post_model_integration():
    """Post 모델 전체 기능 통합 테스트"""
    # 새로운 필드를 포함한 Post 생성
    # 기존 Post와의 호환성 확인
    # 데이터베이스 저장/조회 테스트
    pass
```

## 구현 참고사항

### 1. 기존 호환성 유지
- 기존 Post 모델의 필드는 변경하지 않음
- 새 필드는 모두 Optional 또는 기본값 설정
- 기존 API 응답에 영향 없도록 구현

### 2. 성능 고려사항
- content_text 필드는 검색 최적화용
- 인덱스 설정으로 쿼리 성능 확보
- 대용량 텍스트 처리 시 메모리 사용량 고려

### 3. 확장성 고려
- 향후 새로운 콘텐츠 타입 추가 가능한 구조
- 메타데이터 필드의 확장 가능성
- 다국어 지원 준비

이 Task는 에디터 통합의 기반이 되는 데이터 모델을 정의하므로 신중하게 설계해야 합니다.