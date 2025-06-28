"""
콘텐츠 처리 관련 모델 정의
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from nadle_backend.models.core import ContentType


class ContentMetadata(BaseModel):
    """콘텐츠 메타데이터 모델"""
    word_count: int = 0
    reading_time: int = 1  # 최소 1분
    inline_images: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    headings: List[str] = Field(default_factory=list)


class ProcessedContent(BaseModel):
    """처리된 콘텐츠 모델"""
    original_content: str
    content_type: ContentType
    rendered_html: str
    content_text: str  # 검색용 순수 텍스트
    metadata: ContentMetadata


class PreviewRequest(BaseModel):
    """미리보기 요청 모델"""
    content: str = Field(..., min_length=1)
    content_type: ContentType = "markdown"


class PreviewResponse(BaseModel):
    """미리보기 응답 모델"""
    content_rendered: str
    word_count: int
    reading_time: int
    inline_images: List[str] = Field(default_factory=list)


class InlineImageResponse(BaseModel):
    """인라인 이미지 업로드 응답 모델"""
    file_id: str
    url: str
    markdown: str
    html: str