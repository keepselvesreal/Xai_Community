"""
정보 콘텐츠 생성 기본 클래스

이 모듈은 모든 콘텐츠 생성기의 기본 클래스를 제공합니다.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import uuid

from scripts.info_content.content_types import InfoContent, ContentMetadata, ContentType, InfoCategory
from nadle_backend.models.core import Post
from nadle_backend.database.connection import Database


class BaseContentCreator(ABC):
    """콘텐츠 생성 기본 클래스"""
    
    def __init__(self, admin_user_id: str):
        self.admin_user_id = admin_user_id
        self.db = None
    
    async def initialize_db(self):
        """데이터베이스 연결 초기화"""
        if not self.db:
            self.db = Database()
            await self.db.connect()
    
    @abstractmethod
    async def create_content(self, **kwargs) -> InfoContent:
        """콘텐츠 생성 (각 서브클래스에서 구현)"""
        pass
    
    def generate_slug(self, title: str) -> str:
        """제목에서 URL slug 생성"""
        # 한글과 영문 처리
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        
        # 고유성을 위해 UUID 일부 추가
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{slug}-{unique_suffix}"
    
    def create_metadata(
        self,
        category: InfoCategory,
        content_type: ContentType,
        tags: List[str] = None,
        summary: str = None,
        data_source: str = None,
        chart_config: Dict[str, Any] = None,
        ai_prompt: str = None
    ) -> ContentMetadata:
        """메타데이터 생성"""
        return ContentMetadata(
            type="property_information",
            category=category.value,
            tags=tags or [],
            content_type=content_type.value,
            summary=summary,
            data_source=data_source,
            chart_config=chart_config,
            ai_prompt=ai_prompt
        )
    
    async def save_to_database(self, content: InfoContent) -> str:
        """콘텐츠를 데이터베이스에 저장"""
        await self.initialize_db()
        
        # InfoContent를 Post 딕셔너리로 변환
        post_data = content.to_post_dict()
        
        # Post 객체 생성
        post = Post(**post_data)
        
        # 데이터베이스에 저장
        await post.insert()
        
        print(f"✅ 콘텐츠 저장 완료: {content.title} (ID: {post.id})")
        return str(post.id)
    
    async def create_and_save(self, **kwargs) -> str:
        """콘텐츠 생성 및 저장"""
        content = await self.create_content(**kwargs)
        content_id = await self.save_to_database(content)
        return content_id
    
    def get_default_tags(self, category: InfoCategory) -> List[str]:
        """카테고리별 기본 태그 반환"""
        tag_mapping = {
            InfoCategory.MARKET_ANALYSIS: ["시세", "분석"],
            InfoCategory.LEGAL_INFO: ["법률", "계약"],
            InfoCategory.MOVE_IN_GUIDE: ["입주", "가이드"],
            InfoCategory.INVESTMENT_TREND: ["투자", "동향"]
        }
        return tag_mapping.get(category, [])
    
    def validate_content(self, content: InfoContent) -> bool:
        """콘텐츠 유효성 검사"""
        if not content.title or len(content.title.strip()) == 0:
            raise ValueError("제목은 필수입니다")
        
        if not content.content or len(content.content.strip()) == 0:
            raise ValueError("내용은 필수입니다")
        
        if not content.slug or len(content.slug.strip()) == 0:
            raise ValueError("슬러그는 필수입니다")
        
        if len(content.metadata.tags) > 3:
            raise ValueError("태그는 최대 3개까지 가능합니다")
        
        return True
    
    async def cleanup(self):
        """리소스 정리"""
        if self.db:
            await self.db.disconnect()


class ContentGenerator:
    """콘텐츠 생성 관리 클래스"""
    
    def __init__(self, admin_user_id: str):
        self.admin_user_id = admin_user_id
        self.creators: Dict[ContentType, BaseContentCreator] = {}
    
    def register_creator(self, content_type: ContentType, creator: BaseContentCreator):
        """콘텐츠 생성기 등록"""
        self.creators[content_type] = creator
    
    async def create_content(self, content_type: ContentType, **kwargs) -> str:
        """지정된 타입의 콘텐츠 생성"""
        if content_type not in self.creators:
            raise ValueError(f"지원하지 않는 콘텐츠 타입: {content_type}")
        
        creator = self.creators[content_type]
        return await creator.create_and_save(**kwargs)
    
    async def create_all_sample_contents(self) -> List[str]:
        """모든 타입의 샘플 콘텐츠 생성"""
        content_ids = []
        
        for content_type, creator in self.creators.items():
            try:
                content_id = await creator.create_and_save()
                content_ids.append(content_id)
                print(f"✅ {content_type.value} 샘플 콘텐츠 생성 완료")
            except Exception as e:
                print(f"❌ {content_type.value} 샘플 콘텐츠 생성 실패: {e}")
        
        return content_ids
    
    async def cleanup(self):
        """모든 생성기 정리"""
        for creator in self.creators.values():
            await creator.cleanup()