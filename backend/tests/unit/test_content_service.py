"""
🔵 기반 계층 - 독립적 핵심 콘텐츠 처리 로직

📝 모듈 목차: test_content_service.py

주요 컴포넌트들:
- ContentService: 마크다운 렌더링과 HTML 처리
- MarkdownRenderer: 마크다운 → HTML 변환
- HTMLSanitizer: XSS 방지를 위한 HTML 새니타이징
- MetadataExtractor: 콘텐츠 메타데이터 추출

구성 함수와 핵심 내용:
- test_render_markdown(): 마크다운 → HTML 변환 (구문 파싱, 이미지 처리)
- test_sanitize_html(): XSS 방지 새니타이징 (태그 필터링, 속성 검증)
- test_extract_metadata(): 메타데이터 추출 (단어수, 읽기시간, 인라인 이미지)
- test_process_content(): 전체 콘텐츠 처리 플로우 통합
"""
import pytest
import asyncio
from unittest.mock import Mock, patch


class TestContentService:
    """🔵 기반 계층 - 독립적 핵심 콘텐츠 처리 로직"""
    
    def test_render_markdown_basic(self):
        """
        기본 마크다운 렌더링 검증
        
        테스트 전: 다양한 마크다운 구문 (헤딩, 강조, 리스트)
        실행 작업: 마크다운 → HTML 변환
        테스트 후: 올바른 HTML 태그로 변환, 구조 유지
        
        🔗 통합 시나리오: 에디터 입력 → 실시간 미리보기 첫 단계
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (마크다운 라이브러리 활용, 구문 처리)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (markdown_content)
        출력: str (rendered_html)
        """
        from nadle_backend.services.content_service import ContentService
        
        service = ContentService()
        markdown_content = TestData.BASIC_MARKDOWN
        
        # 실행
        result = service.render_markdown(markdown_content)
        
        # 검증
        assert isinstance(result, str)
        assert "<h1>" in result  # 제목 변환 확인
        assert "<h2>" in result  # 부제목 변환 확인
        assert "<strong>" in result  # 굵은 글씨 변환 확인
        assert "<em>" in result  # 기울임 변환 확인
        assert "<ul>" in result and "<li>" in result  # 리스트 변환 확인
        assert "script" not in result.lower()  # 스크립트 태그 없음
    
    def test_render_markdown_with_images(self):
        """
        이미지 포함 마크다운 렌더링
        
        테스트 전: 이미지 마크다운 구문 (![alt](/api/files/id) 형식)
        실행 작업: 이미지 URL 처리 및 HTML 변환
        테스트 후: 올바른 img 태그, src 속성 검증
        
        🔗 통합 시나리오: 인라인 이미지 업로드 → 에디터 표시 플로우
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (URL 패턴 매칭, 이미지 처리)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (markdown_with_images)
        출력: str (html_with_img_tags)
        """
        from nadle_backend.services.content_service import ContentService
        
        service = ContentService()
        markdown_content = TestData.MARKDOWN_WITH_IMAGES
        
        # 실행
        result = service.render_markdown(markdown_content)
        
        # 검증
        assert isinstance(result, str)
        assert '<img' in result  # img 태그 존재
        assert 'src="/api/files/' in result  # 올바른 src 패턴
        assert 'alt=' in result  # alt 속성 존재
        
        # 이미지가 2개 포함되어야 함
        import re
        img_tags = re.findall(r'<img[^>]*>', result)
        assert len(img_tags) == 2
    
    def test_render_markdown_complex_structure(self):
        """
        복잡한 마크다운 구조 렌더링
        
        테스트 전: 중첩 리스트, 테이블, 코드 블록이 포함된 마크다운
        실행 작업: 복합 구문 처리 및 HTML 변환
        테스트 후: 정확한 중첩 구조, 테이블 태그, 코드 하이라이팅
        
        🔗 통합 시나리오: 고급 에디터 기능 → 복잡한 문서 작성
        우선순위: 🟡 권장 (안정화)
        난이도: 🔴 고급 (복합 구문, 중첩 처리)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (complex_markdown)
        출력: str (structured_html)
        """
        pass
    
    def test_sanitize_html_xss_prevention(self):
        """
        XSS 공격 방지를 위한 HTML 새니타이징
        
        테스트 전: 악성 스크립트, 이벤트 핸들러 포함 HTML
        실행 작업: 허용되지 않은 태그/속성 제거
        테스트 후: 안전한 HTML, 스크립트 태그 완전 제거
        
        🔗 통합 시나리오: 사용자 입력 → 보안 검증 → 저장
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (보안 규칙, 태그 필터링)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (malicious_html)
        출력: str (sanitized_safe_html)
        """
        from nadle_backend.services.content_service import ContentService
        
        service = ContentService()
        malicious_html = TestData.MALICIOUS_HTML
        
        # 실행
        result = service.sanitize_html(malicious_html)
        
        # 검증
        assert isinstance(result, str)
        assert "<script>" not in result.lower()  # 스크립트 태그 제거
        assert "javascript:" not in result.lower()  # 자바스크립트 URL 제거
        assert "onerror" not in result.lower()  # 이벤트 핸들러 제거
        assert "onclick" not in result.lower()  # 클릭 핸들러 제거
        
        # 기본적인 내용은 보존되어야 함
        assert len(result.strip()) > 0  # 완전히 빈 것은 아님
    
    def test_sanitize_html_allowed_tags(self):
        """
        허용된 HTML 태그 유지 검증
        
        테스트 전: 안전한 HTML 태그 (p, strong, em, img, a)
        실행 작업: 허용 목록 기반 태그 필터링
        테스트 후: 허용된 태그는 유지, 속성 검증
        
        🔗 통합 시나리오: 렌더링된 콘텐츠 → 안전한 표시
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (허용 목록 검증)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (safe_html)
        출력: str (validated_html)
        """
        pass
    
    def test_extract_metadata_basic(self):
        """
        기본 메타데이터 추출
        
        테스트 전: 일반적인 텍스트 콘텐츠
        실행 작업: 단어 수, 읽기 시간 계산
        테스트 후: 정확한 단어 수, 읽기 시간 (분당 200단어 기준)
        
        🔗 통합 시나리오: 게시글 저장 → 메타데이터 표시
        우선순위: 🟡 권장 (안정화)
        난이도: 🟢 초급 (텍스트 처리, 수학 계산)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (content_text)
        출력: ContentMetadata (word_count, reading_time)
        """
        from nadle_backend.services.content_service import ContentService
        from nadle_backend.models.content import ContentMetadata
        
        service = ContentService()
        content = "이것은 테스트 콘텐츠입니다. " * 50  # 약 200단어
        
        # 실행
        metadata = service.extract_metadata(content)
        
        # 검증
        assert isinstance(metadata, ContentMetadata)
        assert metadata.word_count > 0
        assert metadata.reading_time >= 1  # 최소 1분
        
        # 대략적인 계산 검증 (200단어 = 1분)
        expected_reading_time = max(1, metadata.word_count // 200)
        assert metadata.reading_time == expected_reading_time
    
    def test_extract_metadata_with_html(self):
        """
        HTML 태그 제외 메타데이터 추출
        
        테스트 전: HTML 태그가 포함된 콘텐츠
        실행 작업: HTML 태그 제거 후 순수 텍스트 분석
        테스트 후: 태그 제외한 정확한 단어 수
        
        🔗 통합 시나리오: 렌더링된 콘텐츠 → 정확한 메타데이터
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (HTML 파싱, 텍스트 추출)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (html_content)
        출력: ContentMetadata (accurate_word_count)
        """
        pass
    
    def test_extract_inline_images(self):
        """
        인라인 이미지 file_id 추출
        
        테스트 전: 마크다운/HTML에 포함된 이미지 링크
        실행 작업: /api/files/{file_id} 패턴에서 file_id 추출
        테스트 후: 모든 file_id 리스트, 중복 제거
        
        🔗 통합 시나리오: 게시글 저장 → 파일 연결 관리
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (정규식, URL 파싱)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (content_with_images)
        출력: List[str] (file_ids)
        """
        pass
    
    def test_process_content_full_flow(self):
        """
        전체 콘텐츠 처리 플로우 통합
        
        테스트 전: 원본 마크다운 콘텐츠 (이미지 포함)
        실행 작업: 렌더링 → 새니타이징 → 메타데이터 추출
        테스트 후: 완전한 ProcessedContent 객체
        
        🔗 통합 시나리오: 에디터 입력 → 최종 저장 전체 플로우
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (여러 단계 통합, 상태 관리)
        실행 그룹: 🔄 순차 (상태 변경)
        
        입력: str (raw_markdown), str (content_type)
        출력: ProcessedContent (rendered_html, metadata, file_ids)
        """
        from nadle_backend.services.content_service import ContentService
        from nadle_backend.models.content import ProcessedContent
        
        service = ContentService()
        raw_content = TestData.MARKDOWN_WITH_IMAGES
        content_type = "markdown"
        
        # 실행
        result = service.process_content(raw_content, content_type)
        
        # 검증
        assert isinstance(result, ProcessedContent)
        assert result.original_content == raw_content
        assert result.content_type == content_type
        assert result.rendered_html is not None
        assert result.content_text is not None
        assert result.metadata is not None
        
        # 이미지 파일 ID 추출 확인
        assert len(result.metadata.inline_images) > 0
        
        # HTML 안전성 확인
        assert "<script>" not in result.rendered_html.lower()
        assert "<img" in result.rendered_html  # 이미지 변환 확인
    
    def test_process_content_error_handling(self):
        """
        콘텐츠 처리 오류 상황 검증
        
        테스트 전: 잘못된 마크다운, 손상된 이미지 링크
        실행 작업: 오류 복구 및 부분 처리
        테스트 후: 오류 로그, 처리 가능한 부분만 결과 반환
        
        🔗 통합 시나리오: 오류 발생 → 사용자 친화적 에러 메시지
        우선순위: 🟡 권장 (안정화)
        난이도: 🔴 고급 (예외 처리, 오류 복구)
        실행 그룹: ⚡ 병렬 (예외 테스트)
        
        입력: str (invalid_content)
        출력: ProcessedContent (partial_result, error_info)
        """
        pass


class TestMarkdownRenderer:
    """마크다운 렌더링 세부 기능 테스트"""
    
    def test_code_block_rendering(self):
        """
        코드 블록 렌더링 검증
        
        테스트 전: 언어별 코드 블록 (```python, ```javascript)
        실행 작업: 코드 하이라이팅 및 pre/code 태그 생성
        테스트 후: 올바른 클래스 속성, 이스케이프 처리
        
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (구문 하이라이팅)
        실행 그룹: ⚡ 병렬 (순수 함수)
        """
        pass
    
    def test_table_rendering(self):
        """
        테이블 렌더링 검증
        
        테스트 전: 마크다운 테이블 구문
        실행 작업: table, thead, tbody, tr, td 태그 생성
        테스트 후: 올바른 테이블 구조, 정렬 속성
        
        우선순위: 🟢 선택 (최적화)
        난이도: 🟡 중급 (테이블 구조)
        실행 그룹: ⚡ 병렬 (순수 함수)
        """
        pass


class TestHTMLSanitizer:
    """HTML 새니타이징 세부 기능 테스트"""
    
    def test_malicious_script_removal(self):
        """
        악성 스크립트 완전 제거
        
        테스트 전: 다양한 형태의 스크립트 태그
        실행 작업: 스크립트 태그 및 이벤트 핸들러 제거
        테스트 후: 스크립트 관련 요소 완전 제거
        
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (보안 필터링)
        실행 그룹: ⚡ 병렬 (보안 테스트)
        """
        pass
    
    def test_image_url_validation(self):
        """
        이미지 URL 패턴 검증
        
        테스트 전: 다양한 이미지 URL (/api/files/*, 외부 URL)
        실행 작업: 허용된 패턴만 유지
        테스트 후: 내부 파일 URL만 유지, 외부 URL 제거
        
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (URL 패턴 매칭)
        실행 그룹: ⚡ 병렬 (보안 테스트)
        """
        pass


class TestMetadataExtractor:
    """메타데이터 추출 세부 기능 테스트"""
    
    def test_reading_time_calculation(self):
        """
        읽기 시간 정확한 계산
        
        테스트 전: 다양한 길이의 텍스트 (짧은 글, 긴 글)
        실행 작업: 분당 200단어 기준 읽기 시간 계산
        테스트 후: 정확한 분 단위 시간, 최소 1분
        
        우선순위: 🟡 권장 (안정화)
        난이도: 🟢 초급 (수학 계산)
        실행 그룹: ⚡ 병렬 (순수 함수)
        """
        pass
    
    def test_multilingual_word_count(self):
        """
        다국어 단어 수 계산
        
        테스트 전: 한국어, 영어, 일본어 혼합 텍스트
        실행 작업: 언어별 특성 고려한 단어 수 계산
        테스트 후: 정확한 단어/문자 수 반환
        
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (다국어 처리)
        실행 그룹: ⚡ 병렬 (언어 처리)
        """
        pass


# 테스트 데이터 정의
class TestData:
    """테스트용 샘플 데이터"""
    
    BASIC_MARKDOWN = """# 제목

## 부제목

**굵은 글씨** *기울임*

- 리스트 항목 1
- 리스트 항목 2
"""
    
    MARKDOWN_WITH_IMAGES = """
# 이미지 포함 게시글
![첫 번째 이미지](/api/files/123e4567-e89b-12d3-a456-426614174000)
본문 내용
![두 번째 이미지](/api/files/987fcdeb-51a2-43d7-8c5a-426614174001)
"""
    
    MALICIOUS_HTML = """
<script>alert('XSS')</script>
<img src="x" onerror="alert('XSS')">
<a href="javascript:alert('XSS')">악성 링크</a>
<p onclick="alert('XSS')">클릭하지 마세요</p>
"""
    
    SAFE_HTML = """
<h1>안전한 제목</h1>
<p>일반 텍스트</p>
<strong>굵은 글씨</strong>
<em>기울임</em>
<img src="/api/files/safe-image" alt="안전한 이미지">
<a href="https://example.com">안전한 링크</a>
"""
    
    LONG_TEXT = " ".join(["단어"] * 1000)  # 1000단어 텍스트