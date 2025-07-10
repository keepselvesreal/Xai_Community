"""
TDD 테스트: 사용자 활동 타입 매핑 문제 해결

이 테스트는 UserActivityService에서 발생하는 타입 매핑 문제를 해결합니다:
- DB에 저장된 타입: "expert_tips", "property_information" 
- 서비스가 기대하는 타입: "tips", "info"
- 알 수 없는 타입이 "board"로 잘못 분류되는 문제
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from bson import ObjectId
from nadle_backend.services.user_activity_service import UserActivityService
from nadle_backend.models.core import User, Post, Comment, PostMetadata


class TestPostTypeNormalization:
    """포스트 타입 정규화 함수 테스트"""
    
    @pytest.fixture
    def service(self):
        """Mock 의존성으로 UserActivityService 생성"""
        post_repo = AsyncMock()
        comment_repo = AsyncMock()
        user_reaction_repo = AsyncMock()
        return UserActivityService(post_repo, comment_repo, user_reaction_repo)
    
    def test_normalize_post_type_expert_tips_to_tips(self, service):
        """expert_tips가 tips로 정규화되는지 테스트"""
        result = service.normalize_post_type("expert_tips")
        assert result == "tips"
    
    def test_normalize_post_type_property_information_to_info(self, service):
        """property_information이 info로 정규화되는지 테스트"""
        result = service.normalize_post_type("property_information")
        assert result == "info"
    
    def test_normalize_post_type_board_unchanged(self, service):
        """board 타입은 그대로 유지되는지 테스트"""
        result = service.normalize_post_type("board")
        assert result == "board"
    
    def test_normalize_post_type_unknown_type_returns_none(self, service):
        """알 수 없는 타입은 None을 반환하는지 테스트"""
        result = service.normalize_post_type("unknown_type")
        assert result is None


class TestUserActivityServiceTypeMapping:
    """UserActivityService의 타입 매핑 로직 테스트"""
    
    @pytest.fixture
    def service(self):
        """Mock 의존성으로 UserActivityService 생성"""
        post_repo = AsyncMock()
        comment_repo = AsyncMock()
        user_reaction_repo = AsyncMock()
        return UserActivityService(post_repo, comment_repo, user_reaction_repo)
    
    @pytest.fixture
    def sample_posts(self):
        """테스트용 포스트 데이터"""
        # ObjectId 생성을 위한 mock 데이터
        posts = []
        post_data = [
            {
                "title": "Expert Tips Post",
                "content": "Tips content",
                "slug": "expert-tips-1", 
                "type": "expert_tips",
                "category": "투자 정보"
            },
            {
                "title": "Property Info Post",
                "content": "Info content",
                "slug": "property-info-1",
                "type": "property_information", 
                "category": "시세 분석"
            },
            {
                "title": "Board Post",
                "content": "Board content",
                "slug": "board-post-1",
                "type": "board",
                "category": "자유게시판"
            },
            {
                "title": "Unknown Type Post",
                "content": "Unknown content",
                "slug": "unknown-post-1",
                "type": "unknown_type",
                "category": "기타"
            }
        ]
        
        for i, data in enumerate(post_data):
            # Mock Post 객체 생성
            post = MagicMock()
            post.id = ObjectId()
            post.title = data["title"]
            post.content = data["content"]
            post.slug = data["slug"]
            post.author_id = "user1"
            post.service = "residential_community"
            post.created_at = datetime.utcnow()
            
            # PostMetadata mock
            metadata = MagicMock()
            metadata.type = data["type"]
            metadata.category = data["category"]
            post.metadata = metadata
            
            posts.append(post)
        
        return posts
    
    @pytest.mark.asyncio
    async def test_group_posts_by_page_type_expert_tips_in_tips_section(self, service, sample_posts):
        """expert_tips 포스트가 tips 섹션에 분류되는지 테스트"""
        # RED: 현재 구현에서는 expert_tips가 board로 잘못 분류됨
        service.post_repository.find_by_author.return_value = [sample_posts[0]]  # expert_tips 포스트만
        service.comment_repository.find_by_author.return_value = []
        
        result = await service.get_user_activity_summary("user1")
        
        # 현재는 실패할 예정 - expert_tips가 board에 들어감
        assert "tips" in result["posts"]
        assert len(result["posts"]["tips"]) == 1
        assert result["posts"]["tips"][0]["title"] == "Expert Tips Post"
        # board 섹션에는 들어가지 않아야 함
        assert len(result["posts"].get("board", [])) == 0
    
    @pytest.mark.asyncio
    async def test_group_posts_by_page_type_property_info_in_info_section(self, service, sample_posts):
        """property_information 포스트가 info 섹션에 분류되는지 테스트"""
        # RED: 현재 구현에서는 property_information이 board로 잘못 분류됨
        service.post_repository.find_by_author.return_value = [sample_posts[1]]  # property_information 포스트만
        service.comment_repository.find_by_author.return_value = []
        
        result = await service.get_user_activity_summary("user1")
        
        # 현재는 실패할 예정 - property_information이 board에 들어감
        assert "info" in result["posts"]
        assert len(result["posts"]["info"]) == 1
        assert result["posts"]["info"][0]["title"] == "Property Info Post"
        # board 섹션에는 들어가지 않아야 함
        assert len(result["posts"].get("board", [])) == 0
    
    @pytest.mark.asyncio
    async def test_unknown_type_not_added_to_board_silently(self, service, sample_posts):
        """알 수 없는 타입이 board에 자동으로 추가되지 않는지 테스트"""
        service.post_repository.find_by_author.return_value = [sample_posts[3]]  # unknown_type 포스트만
        service.comment_repository.find_by_author.return_value = []
        
        result = await service.get_user_activity_summary("user1")
        
        # 알 수 없는 타입은 어떤 섹션에도 추가되지 않아야 함
        assert len(result["posts"].get("board", [])) == 0
        assert len(result["posts"].get("tips", [])) == 0
        assert len(result["posts"].get("info", [])) == 0
        assert len(result["posts"].get("services", [])) == 0
    
    @pytest.mark.asyncio
    async def test_unknown_type_logged_as_warning(self, service, sample_posts):
        """알 수 없는 타입이 로그에 기록되는지 테스트"""
        service.post_repository.find_by_author.return_value = [sample_posts[3]]  # unknown_type 포스트만
        service.comment_repository.find_by_author.return_value = []
        
        with patch('nadle_backend.services.user_activity_service.logger') as mock_logger:
            await service.get_user_activity_summary("user1")
            
            # 경고 로그가 기록되어야 함
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "unknown_type" in call_args
            assert "unrecognized post type" in call_args.lower()


class TestPostTypeNormalizationFunction:
    """독립적인 타입 정규화 함수 테스트"""
    
    def test_normalize_post_type_function_mapping(self):
        """타입 정규화 함수의 매핑이 정확한지 테스트"""
        from nadle_backend.services.user_activity_service import normalize_post_type
        
        assert normalize_post_type("expert_tips") == "tips"
        assert normalize_post_type("property_information") == "info"
        assert normalize_post_type("board") == "board"
        assert normalize_post_type("services") == "services"
        assert normalize_post_type("unknown") is None
        assert normalize_post_type(None) is None
        assert normalize_post_type("") is None


class TestUserActivityServiceIntegration:
    """통합 테스트"""
    
    @pytest.fixture
    def service(self):
        """Mock 의존성으로 UserActivityService 생성"""
        post_repo = AsyncMock()
        comment_repo = AsyncMock()
        user_reaction_repo = AsyncMock()
        return UserActivityService(post_repo, comment_repo, user_reaction_repo)
    
    @pytest.mark.asyncio
    async def test_full_type_mapping_scenario(self, service):
        """전체 타입 매핑 시나리오 테스트"""
        # 다양한 타입의 포스트 생성 (Mock 객체)
        posts = []
        post_data = [
            {"title": "Expert Tips", "type": "expert_tips", "category": "투자"},
            {"title": "Property Info", "type": "property_information", "category": "시세"},
            {"title": "Board Post", "type": "board", "category": "자유게시판"}
        ]
        
        for i, data in enumerate(post_data):
            post = MagicMock()
            post.id = ObjectId()
            post.title = data["title"]
            post.content = "Content"
            post.slug = f"slug-{i}"
            post.author_id = "user1"
            post.service = "residential_community"
            post.created_at = datetime.utcnow()
            
            metadata = MagicMock()
            metadata.type = data["type"]
            metadata.category = data["category"]
            post.metadata = metadata
            
            posts.append(post)
        
        service.post_repository.find_by_author.return_value = posts
        service.comment_repository.find_by_author.return_value = []
        
        result = await service.get_user_activity_summary("user1")
        
        # 각 섹션에 올바른 포스트가 분류되어야 함
        assert len(result["posts"]["tips"]) == 1
        assert result["posts"]["tips"][0]["title"] == "Expert Tips"
        
        assert len(result["posts"]["info"]) == 1
        assert result["posts"]["info"][0]["title"] == "Property Info"
        
        assert len(result["posts"]["board"]) == 1
        assert result["posts"]["board"][0]["title"] == "Board Post"