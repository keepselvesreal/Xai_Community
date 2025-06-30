"""ID + 한글 Slug 생성 테스트."""

import pytest
import re
from datetime import datetime
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.models.core import PostCreate, PostMetadata


class TestKoreanSlugGeneration:
    """ID + 한글 Slug 생성 TDD 테스트 클래스."""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정."""
        self.post_repository = PostRepository()
    
    def test_generate_korean_slug_format(self):
        """한글 제목으로부터 올바른 slug 형식이 생성되는지 테스트."""
        # Given: 한글 제목
        title = "테스트 게시글"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: ID-한글제목 형식의 slug가 생성됨
        # 형식: {post_id}-{korean_title}
        # 예: 507f1f77bcf86cd799439011-테스트-게시글
        assert slug is not None
        assert len(slug) > 0
        # 하이픈이 포함되어야 함 (ID와 제목 구분)
        assert "-" in slug
        
    def test_generate_slug_with_mixed_content(self):
        """영문과 한글이 섞인 제목의 slug 생성 테스트."""
        # Given: 영문과 한글이 섞인 제목
        title = "FastAPI 개발 가이드"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 영문과 한글이 모두 보존됨
        assert "fastapi" in slug.lower()
        assert "개발" in slug
        assert "가이드" in slug
        
    def test_generate_slug_special_characters_removed(self):
        """특수문자가 포함된 제목의 slug 생성 테스트."""
        # Given: 특수문자가 포함된 제목
        title = "React + TypeScript 완벽 가이드!"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 특수문자는 제거되고 안전한 문자만 남음
        assert "+" not in slug
        assert "!" not in slug
        assert "react" in slug.lower()
        assert "typescript" in slug.lower()
        assert "완벽" in slug
        assert "가이드" in slug
        
    def test_generate_slug_spaces_to_hyphens(self):
        """공백이 하이픈으로 변환되는지 테스트."""
        # Given: 공백이 포함된 제목
        title = "프론트엔드 백엔드 연동"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 공백이 하이픈으로 변환됨
        assert " " not in slug
        assert "프론트엔드" in slug
        assert "백엔드" in slug
        assert "연동" in slug
        # 단어 사이에 하이픈이 있어야 함
        hyphens_count = slug.count("-")
        assert hyphens_count >= 2  # 최소 2개의 하이픈 (공백 변환)
        
    def test_generate_slug_empty_title(self):
        """빈 제목에 대한 slug 생성 테스트."""
        # Given: 빈 제목
        title = ""
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 기본 slug가 생성됨
        assert slug is not None
        assert len(slug) > 0
        assert slug != ""
        
    def test_generate_slug_only_special_characters(self):
        """특수문자만 있는 제목의 slug 생성 테스트."""
        # Given: 특수문자만 있는 제목
        title = "!@#$%^&*()"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 유효한 slug가 생성됨
        assert slug is not None
        assert len(slug) > 0
        # 특수문자는 제거되고 안전한 slug가 생성되어야 함
        
    def test_generate_slug_very_long_title(self):
        """매우 긴 제목의 slug 생성 테스트."""
        # Given: 매우 긴 제목
        title = "이것은 매우 긴 제목입니다 " * 10  # 반복으로 긴 제목 생성
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: slug가 생성되고 합리적인 길이를 가짐
        assert slug is not None
        assert len(slug) > 0
        # URL에서 사용하기에 적절한 길이여야 함
        # 너무 길면 문제가 될 수 있으므로 제한이 있을 수 있음
        
    def test_generate_slug_with_numbers(self):
        """숫자가 포함된 제목의 slug 생성 테스트."""
        # Given: 숫자가 포함된 제목
        title = "Vue 3.0 마이그레이션 가이드"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 숫자가 보존됨
        assert "vue" in slug.lower()
        assert "3" in slug
        assert "0" in slug
        assert "마이그레이션" in slug
        assert "가이드" in slug
        
    def test_generate_slug_uniqueness_simulation(self):
        """slug 고유성 보장을 위한 시뮬레이션 테스트."""
        # Given: 동일한 제목
        title = "동일한 제목"
        
        # When: 여러 번 slug 생성
        slug1 = self.post_repository._generate_slug(title)
        slug2 = self.post_repository._generate_slug(title)
        
        # Then: 기본 slug는 동일하지만, 실제 사용시에는 고유성이 보장되어야 함
        # (이는 _ensure_unique_slug 메서드에서 처리됨)
        assert slug1 == slug2  # 기본 생성은 동일
        assert "동일한" in slug1
        assert "제목" in slug1
        
    def test_slug_url_safety(self):
        """생성된 slug가 URL에서 안전한지 테스트."""
        # Given: 다양한 문자가 포함된 제목
        title = "React/Vue 비교분석 (2024년)"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: URL에서 안전한 문자만 포함됨
        # 허용되는 문자: 영문, 숫자, 하이픈, 한글
        safe_pattern = re.compile(r'^[a-zA-Z0-9\-가-힣]+$')
        assert safe_pattern.match(slug), f"Unsafe characters in slug: {slug}"
        
    def test_slug_no_leading_trailing_hyphens(self):
        """slug가 하이픈으로 시작하거나 끝나지 않는지 테스트."""
        # Given: 특수문자로 시작/끝나는 제목
        title = "-시작과 끝-"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(title)
        
        # Then: 하이픈으로 시작하거나 끝나지 않음
        assert not slug.startswith("-")
        assert not slug.endswith("-")
        assert "시작과" in slug
        assert "끝" in slug


class TestKoreanSlugWithPostID:
    """Post ID와 함께 한글 Slug 생성 테스트."""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정."""
        self.post_repository = PostRepository()
    
    def test_slug_with_post_id_format(self):
        """Post ID가 포함된 slug 형식 테스트."""
        # Given: Post ID와 한글 제목
        post_id = "507f1f77bcf86cd799439011"
        title = "테스트 게시글"
        
        # When: ID + slug 조합 생성
        base_slug = self.post_repository._generate_slug(title)
        id_slug = f"{post_id}-{base_slug}"
        
        # Then: ID-제목 형식이 됨
        assert id_slug.startswith(post_id)
        assert base_slug in id_slug
        assert "테스트" in id_slug
        assert "게시글" in id_slug
        
    def test_slug_id_extraction(self):
        """slug에서 Post ID 추출 테스트."""
        # Given: ID가 포함된 slug
        post_id = "507f1f77bcf86cd799439011"
        base_slug = "테스트-게시글"
        full_slug = f"{post_id}-{base_slug}"
        
        # When: ID 추출
        extracted_id = full_slug.split("-")[0]
        
        # Then: 올바른 ID가 추출됨
        assert extracted_id == post_id
        assert len(extracted_id) == 24  # MongoDB ObjectId 길이
        
    def test_slug_title_extraction(self):
        """slug에서 제목 부분 추출 테스트."""
        # Given: ID가 포함된 slug
        post_id = "507f1f77bcf86cd799439011"
        base_slug = "테스트-게시글"
        full_slug = f"{post_id}-{base_slug}"
        
        # When: 제목 부분 추출
        title_part = "-".join(full_slug.split("-")[1:])
        
        # Then: 올바른 제목이 추출됨
        assert title_part == base_slug
        assert "테스트" in title_part
        assert "게시글" in title_part


class TestSlugIntegrationScenarios:
    """실제 사용 시나리오 통합 테스트."""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정."""
        self.post_repository = PostRepository()
    
    def test_real_world_korean_titles(self):
        """실제 사용될 법한 한글 제목들 테스트."""
        real_titles = [
            "입주민 커뮤니티 이용 안내",
            "아파트 관리사무소 연락처",
            "주차장 이용 규칙 변경사항",
            "엘리베이터 점검 일정 공지",
            "택배 보관함 사용법",
            "헬스장 운영시간 안내",
            "독서실 예약 방법",
            "분리수거 배출 요령",
            "소음 관련 생활수칙",
            "화재대피 경로 안내"
        ]
        
        # When: 각 제목으로 slug 생성
        generated_slugs = []
        for title in real_titles:
            slug = self.post_repository._generate_slug(title)
            generated_slugs.append(slug)
            
            # Then: 각 slug가 유효함
            assert slug is not None
            assert len(slug) > 0
            assert not slug.startswith("-")
            assert not slug.endswith("-")
            
        # Then: 모든 slug가 생성되고 고유함
        assert len(generated_slugs) == len(real_titles)
        # 기본 slug는 제목이 다르면 다를 수 있음
        
    def test_slug_backward_compatibility(self):
        """기존 slug 방식과의 호환성 테스트."""
        # Given: 영문 제목 (기존 방식과 호환되어야 함)
        english_title = "Getting Started with FastAPI"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(english_title)
        
        # Then: 영문 slug가 올바르게 생성됨
        assert "getting" in slug.lower()
        assert "started" in slug.lower()
        assert "fastapi" in slug.lower()
        assert " " not in slug  # 공백 제거
        
    def test_mixed_language_slug(self):
        """다국어가 섞인 제목의 slug 생성 테스트."""
        # Given: 한영 혼합 제목
        mixed_title = "React 컴포넌트 개발 Guide"
        
        # When: slug 생성
        slug = self.post_repository._generate_slug(mixed_title)
        
        # Then: 모든 언어가 보존됨
        assert "react" in slug.lower()
        assert "컴포넌트" in slug
        assert "개발" in slug
        assert "guide" in slug.lower()