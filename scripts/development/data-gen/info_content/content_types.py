"""
정보 페이지 콘텐츠 타입 정의

이 모듈은 정보 페이지에서 사용되는 다양한 콘텐츠 타입을 정의합니다.
관리자가 직접 콘텐츠를 생성할 때 사용되는 기본 구조입니다.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class ContentType(Enum):
    """콘텐츠 타입 열거형"""
    INTERACTIVE_CHART = "interactive_chart"
    AI_ARTICLE = "ai_article" 
    DATA_VISUALIZATION = "data_visualization"
    MIXED_CONTENT = "mixed_content"


class InfoCategory(Enum):
    """정보 카테고리 열거형"""
    MARKET_ANALYSIS = "market_analysis"
    LEGAL_INFO = "legal_info"
    MOVE_IN_GUIDE = "move_in_guide"
    INVESTMENT_TREND = "investment_trend"


@dataclass
class ContentMetadata:
    """콘텐츠 메타데이터"""
    type: str = "property_information"
    category: str = ""
    tags: list = None
    content_type: str = ContentType.AI_ARTICLE.value
    summary: Optional[str] = None
    data_source: Optional[str] = None
    chart_config: Optional[Dict[str, Any]] = None
    ai_prompt: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class InfoContent:
    """정보 콘텐츠 기본 구조"""
    title: str
    content: str
    slug: str
    author_id: str
    content_type: ContentType
    metadata: ContentMetadata
    service: str = "residential_community"
    status: str = "published"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_post_dict(self) -> Dict[str, Any]:
        """Post 모델에 맞는 딕셔너리로 변환"""
        return {
            "title": self.title,
            "content": self.content,
            "slug": self.slug,
            "author_id": self.author_id,
            "service": self.service,
            "status": self.status,
            "created_at": self.created_at,
            "metadata": {
                "type": self.metadata.type,
                "category": self.metadata.category,
                "tags": self.metadata.tags,
                "content_type": self.content_type.value,
                "summary": self.metadata.summary,
                "data_source": self.metadata.data_source,
                "chart_config": self.metadata.chart_config,
                "ai_prompt": self.metadata.ai_prompt
            }
        }


def get_content_type_info() -> Dict[ContentType, Dict[str, str]]:
    """각 콘텐츠 타입에 대한 정보 반환"""
    return {
        ContentType.INTERACTIVE_CHART: {
            "name": "인터렉티브 차트",
            "description": "사용자가 직접 조작 가능한 차트",
            "example": "아파트 시세 차트, 관리비 비교 차트",
            "technology": "Chart.js, D3.js"
        },
        ContentType.AI_ARTICLE: {
            "name": "AI 생성 글",
            "description": "AI가 스크래핑 데이터를 바탕으로 작성한 글",
            "example": "시장 동향 분석, 법률 가이드",
            "technology": "마크다운, 구조화된 텍스트"
        },
        ContentType.DATA_VISUALIZATION: {
            "name": "데이터 시각화",
            "description": "정적인 데이터 시각화",
            "example": "월별 전세가 변동 그래프, 층별 분양가 차트",
            "technology": "이미지, 정적 SVG"
        },
        ContentType.MIXED_CONTENT: {
            "name": "혼합 콘텐츠",
            "description": "여러 타입을 조합한 콘텐츠",
            "example": "차트 + AI 해석 + 데이터 테이블",
            "technology": "모든 기술 조합"
        }
    }


def get_category_info() -> Dict[InfoCategory, Dict[str, str]]:
    """각 카테고리에 대한 정보 반환"""
    return {
        InfoCategory.MARKET_ANALYSIS: {
            "name": "시세분석",
            "description": "부동산 시세 및 시장 동향 분석",
            "keywords": ["시세", "가격", "동향", "전망"]
        },
        InfoCategory.LEGAL_INFO: {
            "name": "법률정보",
            "description": "부동산 관련 법률 및 계약 정보",
            "keywords": ["계약", "법률", "권리", "의무"]
        },
        InfoCategory.MOVE_IN_GUIDE: {
            "name": "입주가이드",
            "description": "입주 관련 절차 및 안내사항",
            "keywords": ["입주", "절차", "준비", "체크리스트"]
        },
        InfoCategory.INVESTMENT_TREND: {
            "name": "투자동향",
            "description": "부동산 투자 관련 정보 및 동향",
            "keywords": ["투자", "수익", "전략", "리스크"]
        }
    }