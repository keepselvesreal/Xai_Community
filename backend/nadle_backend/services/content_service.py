"""
콘텐츠 처리 서비스
"""
import re
import html
from typing import List, Optional
from markdown import markdown
import bleach
from bs4 import BeautifulSoup

from nadle_backend.models.content import ContentMetadata, ProcessedContent
from nadle_backend.models.core import ContentType


class ContentService:
    """콘텐츠 처리 서비스"""
    
    # 허용된 HTML 태그 및 속성
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr',
        'img', 'a', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'img': ['src', 'alt', 'title'],
        'a': ['href', 'title', 'target'],
        'code': ['class'],
        'pre': ['class'],
    }
    
    # 이미지 URL 패턴 검증
    ALLOWED_IMAGE_PATTERN = r'^/api/files/[a-f0-9-]+$'
    
    def render_markdown(self, content: str) -> str:
        """
        마크다운을 HTML로 렌더링
        
        Args:
            content: 마크다운 콘텐츠
            
        Returns:
            str: 렌더링된 HTML
        """
        if not content:
            return ""
        
        # Python-Markdown으로 변환
        html_content = markdown(
            content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.codehilite'
            ]
        )
        
        return html_content
    
    def sanitize_html(self, html_content: str) -> str:
        """
        HTML 새니타이징 (XSS 방지)
        
        Args:
            html_content: 원본 HTML
            
        Returns:
            str: 새니타이징된 안전한 HTML
        """
        if not html_content:
            return ""
        
        # bleach를 사용한 HTML 새니타이징
        cleaned_html = bleach.clean(
            html_content,
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        # 이미지 URL 패턴 추가 검증
        cleaned_html = self._validate_image_urls(cleaned_html)
        
        return cleaned_html
    
    def _validate_image_urls(self, html_content: str) -> str:
        """이미지 URL 패턴 검증"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not re.match(self.ALLOWED_IMAGE_PATTERN, src):
                # 외부 URL이나 위험한 패턴 제거
                img.decompose()
        
        return str(soup)
    
    def extract_metadata(self, content: str) -> ContentMetadata:
        """
        콘텐츠에서 메타데이터 추출
        
        Args:
            content: 텍스트 콘텐츠
            
        Returns:
            ContentMetadata: 추출된 메타데이터
        """
        # HTML 태그 제거하여 순수 텍스트 추출
        clean_text = self._extract_text_from_html(content)
        
        # 단어 수 계산 (한국어와 영어 혼합 고려)
        word_count = self._count_words(clean_text)
        
        # 읽기 시간 계산 (분당 200단어 기준)
        reading_time = max(1, word_count // 200)
        
        # 인라인 이미지 추출
        inline_images = self._extract_inline_images(content)
        
        return ContentMetadata(
            word_count=word_count,
            reading_time=reading_time,
            inline_images=inline_images
        )
    
    def _extract_text_from_html(self, content: str) -> str:
        """HTML에서 순수 텍스트 추출"""
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(strip=True)
    
    def _count_words(self, text: str) -> int:
        """단어 수 계산 (한국어와 영어 혼합)"""
        if not text:
            return 0
        
        # 영어 단어 계산
        english_words = re.findall(r'\b[a-zA-Z]+\b', text)
        
        # 한국어 문자 계산 (대략 2-3글자당 1단어로 계산)
        korean_chars = re.findall(r'[가-힣]', text)
        korean_words = len(korean_chars) // 2
        
        return len(english_words) + korean_words
    
    def _extract_inline_images(self, content: str) -> List[str]:
        """인라인 이미지 file_id 추출"""
        # 마크다운과 HTML 모두에서 이미지 URL 추출
        file_ids = []
        
        # 마크다운 패턴: ![alt](/api/files/file_id)
        markdown_pattern = r'!\[[^\]]*\]\(/api/files/([a-f0-9-]+)\)'
        markdown_matches = re.findall(markdown_pattern, content)
        file_ids.extend(markdown_matches)
        
        # HTML 패턴: <img src="/api/files/file_id">
        html_pattern = r'<img[^>]*src="/api/files/([a-f0-9-]+)"'
        html_matches = re.findall(html_pattern, content)
        file_ids.extend(html_matches)
        
        # 중복 제거
        return list(set(file_ids))
    
    def process_content(self, content: str, content_type: ContentType) -> ProcessedContent:
        """
        전체 콘텐츠 처리 플로우
        
        Args:
            content: 원본 콘텐츠
            content_type: 콘텐츠 타입
            
        Returns:
            ProcessedContent: 처리된 콘텐츠
        """
        # 1. 콘텐츠 타입에 따른 렌더링
        if content_type == "markdown":
            rendered_html = self.render_markdown(content)
        elif content_type == "html":
            rendered_html = content
        else:  # text
            rendered_html = html.escape(content).replace('\n', '<br>')
        
        # 2. HTML 새니타이징
        safe_html = self.sanitize_html(rendered_html)
        
        # 3. 검색용 순수 텍스트 추출
        content_text = self._extract_text_from_html(safe_html)
        
        # 4. 메타데이터 추출
        metadata = self.extract_metadata(content)
        
        return ProcessedContent(
            original_content=content,
            content_type=content_type,
            rendered_html=safe_html,
            content_text=content_text,
            metadata=metadata
        )