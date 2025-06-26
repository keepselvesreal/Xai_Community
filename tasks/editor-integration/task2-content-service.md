# Task 2: 콘텐츠 처리 서비스

**Feature Group**: editor-integration  
**Task 제목**: 콘텐츠 처리 서비스  
**작성 시각**: 2025-06-26  
**대상 파일**: `backend/src/services/content_service.py` (신규 생성)

## 개요

마크다운 렌더링, HTML 새니타이징, 콘텐츠 메타데이터 추출 등 다양한 콘텐츠 처리 기능을 제공하는 서비스를 구현합니다. 이 서비스는 에디터로부터 입력된 콘텐츠를 안전하고 일관된 형태로 변환하는 핵심 역할을 수행합니다.

## 리스크 정보

**리스크 레벨**: 높음

**리스크 설명**:
- 마크다운 렌더링 성능 이슈 가능 (대용량 콘텐츠)
- XSS 공격 벡터 존재 (HTML 새니타이징 취약점)
- 외부 라이브러리 의존성 (markdown, bleach)
- 콘텐츠 처리 로직의 복잡성

## Subtask 구성

### Subtask 2.1: 마크다운 렌더러 (Social Unit)

**테스트 함수**: `test_markdown_to_html_conversion()`

**설명**: 
- Python-Markdown 라이브러리 기반 마크다운 → HTML 변환
- 이미지 URL 패턴 처리 (/api/files/{file_id})
- 코드 블록, 테이블, 링크 등 확장 기능 지원

**Social Unit 정보**: markdown, bleach 라이브러리와 통합

**구현 요구사항**:
```python
import markdown
from markdown.extensions import codehilite, tables, toc

class MarkdownRenderer:
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'tables', 
                'toc',
                'fenced_code',
                'nl2br'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': False
                }
            }
        )
    
    def render(self, content: str) -> str:
        """마크다운을 HTML로 변환"""
        # 이미지 URL 패턴 검증
        # 마크다운 렌더링
        # 기본 HTML 구조 생성
        pass
```

**검증 조건**:
- 기본 마크다운 구문 지원 (헤딩, 볼드, 이탤릭, 링크)
- 코드 블록 및 인라인 코드 지원
- 테이블 렌더링
- 이미지 URL 검증 (/api/files/ 패턴만 허용)

### Subtask 2.2: HTML 새니타이저 (Social Unit)

**테스트 함수**: `test_html_sanitization_security()`

**설명**: 
- bleach 라이브러리 기반 XSS 방지
- 허용된 태그 및 속성만 유지
- 악성 스크립트 및 이벤트 핸들러 제거

**Social Unit 정보**: Subtask 2.1과 통합하여 렌더링 후 새니타이징

**구현 요구사항**:
```python
import bleach
import re

class HTMLSanitizer:
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr',
        'img', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'img': ['src', 'alt', 'title'],
        'a': ['href', 'title', 'target'],
        'code': ['class'],
        'pre': ['class'],
        'table': ['class'],
        'th': ['class'],
        'td': ['class']
    }
    
    ALLOWED_PROTOCOLS = ['http', 'https']
    ALLOWED_IMAGE_PATTERN = r'^/api/files/[a-f0-9-]+$'
    
    def sanitize(self, html: str) -> str:
        """HTML 새니타이징"""
        # 이미지 URL 검증
        # 스크립트 태그 제거
        # 이벤트 핸들러 제거
        # 허용된 태그/속성만 유지
        pass
```

**검증 조건**:
- XSS 공격 패턴 차단 (<script>, onclick 등)
- 허용되지 않은 태그/속성 제거
- 이미지 URL 패턴 검증
- 외부 링크 검증

### Subtask 2.3: 콘텐츠 메타데이터 추출기

**테스트 함수**: `test_content_metadata_extraction()`

**설명**: 
- 콘텐츠로부터 메타데이터 추출 (단어 수, 읽기 시간, 인라인 이미지)
- HTML 태그 제거 후 순수 텍스트 생성
- 검색 최적화를 위한 텍스트 정제

**구현 요구사항**:
```python
import re
from bs4 import BeautifulSoup

class ContentMetadataExtractor:
    def extract_metadata(self, content: str, content_type: str) -> dict:
        """콘텐츠 메타데이터 추출"""
        # HTML 태그 제거하여 순수 텍스트 생성
        # 단어 수 계산
        # 읽기 시간 추정 (분당 200단어 기준)
        # 인라인 이미지 file_id 추출
        pass
    
    def extract_plain_text(self, html: str) -> str:
        """HTML에서 순수 텍스트 추출"""
        # BeautifulSoup으로 HTML 파싱
        # 태그 제거, 텍스트만 추출
        # 불필요한 공백 정리
        pass
    
    def count_words(self, text: str) -> int:
        """단어 수 계산"""
        # 한글/영문 혼합 텍스트 처리
        # 공백 기준 단어 분리
        # 특수문자 제외
        pass
    
    def estimate_reading_time(self, word_count: int) -> int:
        """읽기 시간 추정 (분 단위)"""
        # 분당 200단어 기준
        # 최소 1분 보장
        pass
    
    def extract_inline_images(self, html: str) -> List[str]:
        """인라인 이미지 file_id 추출"""
        # img 태그의 src 속성에서 file_id 추출
        # /api/files/{file_id} 패턴 매칭
        pass
```

**검증 조건**:
- 정확한 단어 수 계산 (한글/영문 혼합)
- 읽기 시간 추정 알고리즘
- 인라인 이미지 file_id 정확한 추출
- HTML 태그 완전 제거

### Subtask 2.4: 콘텐츠 처리 파사드

**테스트 함수**: `test_content_service_integration()`

**설명**: 
- 전체 콘텐츠 처리 플로우 통합
- 콘텐츠 타입별 처리 로직 분기
- 에러 핸들링 및 로깅

**Social Unit 정보**: Subtask 2.1, 2.2, 2.3의 통합 서비스

**구현 요구사항**:
```python
from typing import Dict, Any
import logging

class ContentService:
    def __init__(self):
        self.markdown_renderer = MarkdownRenderer()
        self.html_sanitizer = HTMLSanitizer()
        self.metadata_extractor = ContentMetadataExtractor()
        self.logger = logging.getLogger(__name__)
    
    async def process_content(
        self, 
        content: str, 
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """콘텐츠 전체 처리 플로우"""
        try:
            result = {
                "content_original": content,
                "content_type": content_type
            }
            
            if content_type == "markdown":
                # 마크다운 → HTML 변환
                html = self.markdown_renderer.render(content)
                # HTML 새니타이징
                result["content_rendered"] = self.html_sanitizer.sanitize(html)
            elif content_type == "html":
                # HTML 직접 새니타이징
                result["content_rendered"] = self.html_sanitizer.sanitize(content)
            else:  # text
                # 플레인 텍스트를 HTML로 변환 (줄바꿈 → <br>)
                result["content_rendered"] = content.replace('\n', '<br>')
            
            # 메타데이터 추출
            metadata = self.metadata_extractor.extract_metadata(
                result["content_rendered"], 
                content_type
            )
            result.update(metadata)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Content processing failed: {str(e)}")
            raise ContentProcessingError(f"Failed to process content: {str(e)}")
    
    async def preview_content(
        self, 
        content: str, 
        content_type: str = "markdown"
    ) -> str:
        """실시간 미리보기용 빠른 렌더링"""
        # 캐싱 없이 즉시 렌더링
        # 메타데이터 추출 생략
        pass
```

**검증 조건**:
- 모든 콘텐츠 타입 처리 지원
- 에러 발생 시 적절한 예외 처리
- 로깅 및 모니터링 지원
- 성능 최적화 (캐싱 등)

## 의존성 정보

**선행 조건**: 
- Task 1 (콘텐츠 모델 확장) 완료 필요

**외부 라이브러리**:
- `markdown` - 마크다운 렌더링
- `bleach` - HTML 새니타이징
- `beautifulsoup4` - HTML 파싱
- `pygments` - 코드 하이라이팅 (선택적)

**후속 작업**: 
- Task 4, 5에서 이 서비스 사용
- Task 3에서 인라인 이미지 처리 연동

## 테스트 요구사항

### 단위 테스트
```python
def test_markdown_to_html_conversion():
    """마크다운 렌더링 테스트"""
    # 기본 마크다운 구문 테스트
    # 코드 블록 렌더링 테스트
    # 이미지 URL 검증 테스트
    # 테이블 렌더링 테스트
    pass

def test_html_sanitization_security():
    """HTML 새니타이징 보안 테스트"""
    # XSS 공격 패턴 차단 테스트
    # 스크립트 태그 제거 테스트
    # 이벤트 핸들러 제거 테스트
    # 허용된 태그만 유지 테스트
    pass

def test_content_metadata_extraction():
    """메타데이터 추출 테스트"""
    # 단어 수 계산 정확성 테스트
    # 읽기 시간 추정 테스트
    # 인라인 이미지 추출 테스트
    # 순수 텍스트 변환 테스트
    pass

def test_content_service_integration():
    """콘텐츠 서비스 통합 테스트"""
    # 전체 플로우 테스트
    # 에러 핸들링 테스트
    # 성능 테스트
    # 캐싱 테스트
    pass
```

### 보안 테스트
```python
def test_xss_prevention():
    """XSS 공격 방지 테스트"""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src='x' onerror='alert(1)'>",
        "<a href='javascript:alert(1)'>click</a>",
        "<iframe src='javascript:alert(1)'></iframe>"
    ]
    # 각 페이로드가 안전하게 처리되는지 확인
    pass

def test_image_url_validation():
    """이미지 URL 검증 테스트"""
    valid_urls = ["/api/files/123e4567-e89b-12d3-a456-426614174000"]
    invalid_urls = [
        "http://evil.com/image.jpg",
        "javascript:alert(1)",
        "/api/files/../../../etc/passwd"
    ]
    # URL 검증 로직 테스트
    pass
```

### 성능 테스트
```python
def test_large_content_processing():
    """대용량 콘텐츠 처리 성능 테스트"""
    # 10MB 마크다운 문서 처리 시간 측정
    # 메모리 사용량 확인
    # 타임아웃 처리 테스트
    pass
```

## 구현 참고사항

### 1. 보안 우선사항
- 모든 사용자 입력을 신뢰하지 않음
- 화이트리스트 기반 태그/속성 허용
- 정규표현식을 통한 URL 패턴 검증
- 에러 메시지에서 민감 정보 노출 방지

### 2. 성능 최적화
- 자주 사용되는 렌더링 결과 캐싱
- 대용량 콘텐츠 처리 시 청크 단위 처리
- 비동기 처리로 블로킹 방지

### 3. 확장성 고려
- 플러그인 형태로 새로운 렌더러 추가 가능
- 설정 파일을 통한 허용 태그/속성 관리
- 다국어 지원을 위한 로케일 처리

이 Task는 에디터 통합의 핵심 기능을 담당하므로 보안과 성능에 특별히 주의해야 합니다.