"""Unit tests for user activity service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from typing import List, Dict, Any
from nadle_backend.models.core import User, Post, Comment, UserReaction
from nadle_backend.services.user_activity_service import UserActivityService
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository


class TestUserActivityService:
    """Test suite for UserActivityService."""
    
    @pytest.fixture
    def mock_post_repository(self):
        """Mock post repository."""
        return AsyncMock(spec=PostRepository)
    
    @pytest.fixture
    def mock_comment_repository(self):
        """Mock comment repository."""
        return AsyncMock(spec=CommentRepository)
        
    @pytest.fixture
    def mock_user_reaction_repository(self):
        """Mock user reaction repository."""
        return AsyncMock(spec=UserReactionRepository)
    
    @pytest.fixture
    def user_activity_service(self, mock_post_repository, mock_comment_repository, mock_user_reaction_repository):
        """UserActivityService instance with mocked dependencies."""
        return UserActivityService(
            post_repository=mock_post_repository,
            comment_repository=mock_comment_repository,
            user_reaction_repository=mock_user_reaction_repository
        )
    
    @pytest.fixture
    def sample_user(self):
        """Sample user fixture."""
        user = Mock()
        user.id = "507f1f77bcf86cd799439011"
        user.email = "john@example.com"
        user.user_handle = "johndoe"
        user.display_name = "John Doe"
        user.created_at = datetime.utcnow()
        return user
    
    @pytest.fixture
    def sample_posts(self):
        """Sample posts for different page types."""
        posts = []
        
        # Board post
        board_post = Mock()
        board_post.id = "507f1f77bcf86cd799439012"
        board_post.title = "게시판 게시글"
        board_post.slug = "board-post-slug"
        board_post.service = "residential_community"
        board_post.metadata = Mock()
        board_post.metadata.type = "board"
        board_post.metadata.category = "자유게시판"
        board_post.author_id = "507f1f77bcf86cd799439011"
        board_post.created_at = datetime.utcnow()
        board_post.like_count = 5
        board_post.comment_count = 3
        posts.append(board_post)
        
        # Info post
        info_post = Mock()
        info_post.id = "507f1f77bcf86cd799439013"
        info_post.title = "입주 정보 게시글"
        info_post.slug = "info-post-slug"
        info_post.service = "residential_community"
        info_post.metadata = Mock()
        info_post.metadata.type = "property_information"
        info_post.metadata.category = "입주 정보"
        info_post.author_id = "507f1f77bcf86cd799439011"
        info_post.created_at = datetime.utcnow()
        info_post.like_count = 2
        info_post.comment_count = 1
        posts.append(info_post)
        
        # Services post
        services_post = Mock()
        services_post.id = "507f1f77bcf86cd799439014"
        services_post.title = "이사 서비스 게시글"
        services_post.slug = "services-post-slug"
        services_post.service = "residential_community"
        services_post.metadata = Mock()
        services_post.metadata.type = "services"
        services_post.metadata.category = "이사 업체"
        services_post.author_id = "507f1f77bcf86cd799439011"
        services_post.created_at = datetime.utcnow()
        services_post.like_count = 1
        services_post.comment_count = 2
        posts.append(services_post)
        
        # Tips post
        tips_post = Mock()
        tips_post.id = "507f1f77bcf86cd799439015"
        tips_post.title = "전문가 꿀팁"
        tips_post.slug = "tips-post-slug"
        tips_post.service = "residential_community"
        tips_post.metadata = Mock()
        tips_post.metadata.type = "expert_tips"
        tips_post.metadata.category = "생활 팁"
        tips_post.author_id = "507f1f77bcf86cd799439011"
        tips_post.created_at = datetime.utcnow()
        tips_post.like_count = 8
        tips_post.comment_count = 5
        posts.append(tips_post)
        
        return posts
    
    @pytest.fixture
    def sample_comments(self):
        """Sample comments with subtypes."""
        comments = []
        
        # Regular comment
        regular_comment = Mock()
        regular_comment.id = "507f1f77bcf86cd799439020"
        regular_comment.content = "일반 댓글입니다"
        regular_comment.parent_id = "507f1f77bcf86cd799439012"
        regular_comment.author_id = "507f1f77bcf86cd799439011"
        regular_comment.created_at = datetime.utcnow()
        regular_comment.metadata = {"route_path": "/board-post/board-post-slug"}
        comments.append(regular_comment)
        
        # Service inquiry comment
        inquiry_comment = Mock()
        inquiry_comment.id = "507f1f77bcf86cd799439021"
        inquiry_comment.content = "서비스 문의 댓글입니다"
        inquiry_comment.parent_id = "507f1f77bcf86cd799439014"
        inquiry_comment.author_id = "507f1f77bcf86cd799439011"
        inquiry_comment.created_at = datetime.utcnow()
        inquiry_comment.metadata = {"subtype": "inquiry", "route_path": "/moving-services-post/services-post-slug"}
        comments.append(inquiry_comment)
        
        # Service review comment
        review_comment = Mock()
        review_comment.id = "507f1f77bcf86cd799439022"
        review_comment.content = "서비스 후기 댓글입니다"
        review_comment.parent_id = "507f1f77bcf86cd799439014"
        review_comment.author_id = "507f1f77bcf86cd799439011"
        review_comment.created_at = datetime.utcnow()
        review_comment.metadata = {"subtype": "review", "route_path": "/moving-services-post/services-post-slug"}
        comments.append(review_comment)
        
        return comments
    
    @pytest.fixture
    def sample_reactions(self):
        """Sample user reactions."""
        reactions = []
        
        # Post likes
        post_like = Mock()
        post_like.id = "507f1f77bcf86cd799439030"
        post_like.user_id = "507f1f77bcf86cd799439011"
        post_like.target_type = "post"
        post_like.target_id = "507f1f77bcf86cd799439012"
        post_like.liked = True
        post_like.disliked = False
        post_like.bookmarked = False
        post_like.created_at = datetime.utcnow()
        post_like.metadata = {"route_path": "/board-post/board-post-slug", "target_title": "게시판 게시글"}
        reactions.append(post_like)
        
        # Comment like
        comment_like = Mock()
        comment_like.id = "507f1f77bcf86cd799439031"
        comment_like.user_id = "507f1f77bcf86cd799439011"
        comment_like.target_type = "comment"
        comment_like.target_id = "507f1f77bcf86cd799439020"
        comment_like.liked = True
        comment_like.disliked = False
        comment_like.bookmarked = False
        comment_like.created_at = datetime.utcnow()
        comment_like.metadata = {"route_path": "/board-post/board-post-slug", "target_title": "일반 댓글입니다"}
        reactions.append(comment_like)
        
        # Bookmark (info page)
        bookmark = Mock()
        bookmark.id = "507f1f77bcf86cd799439032"
        bookmark.user_id = "507f1f77bcf86cd799439011"
        bookmark.target_type = "post"
        bookmark.target_id = "507f1f77bcf86cd799439013"
        bookmark.liked = False
        bookmark.disliked = False
        bookmark.bookmarked = True
        bookmark.created_at = datetime.utcnow()
        bookmark.metadata = {"route_path": "/property-info/info-post-slug", "target_title": "입주 정보 게시글"}
        reactions.append(bookmark)
        
        # Services dislike
        services_dislike = Mock()
        services_dislike.id = "507f1f77bcf86cd799439033"
        services_dislike.user_id = "507f1f77bcf86cd799439011"
        services_dislike.target_type = "post"
        services_dislike.target_id = "507f1f77bcf86cd799439014"
        services_dislike.liked = False
        services_dislike.disliked = True
        services_dislike.bookmarked = False
        services_dislike.created_at = datetime.utcnow()
        services_dislike.metadata = {"route_path": "/moving-services-post/services-post-slug", "target_title": "이사 서비스 게시글"}
        reactions.append(services_dislike)
        
        # Tips like
        tips_like = Mock()
        tips_like.id = "507f1f77bcf86cd799439034"
        tips_like.user_id = "507f1f77bcf86cd799439011"
        tips_like.target_type = "post"
        tips_like.target_id = "507f1f77bcf86cd799439015"
        tips_like.liked = True
        tips_like.disliked = False
        tips_like.bookmarked = False
        tips_like.created_at = datetime.utcnow()
        tips_like.metadata = {"route_path": "/expert-tips/tips-post-slug", "target_title": "전문가 꿀팁"}
        reactions.append(tips_like)
        
        return reactions

    async def test_get_user_activity_summary_success(
        self, user_activity_service, mock_post_repository, mock_comment_repository, 
        mock_user_reaction_repository, sample_user, sample_posts, sample_comments, sample_reactions
    ):
        """Test successful retrieval of user activity summary."""
        # Arrange
        mock_post_repository.find_by_author.return_value = sample_posts
        mock_comment_repository.find_by_author.return_value = sample_comments
        mock_user_reaction_repository.find_by_user.return_value = sample_reactions
        
        # Act
        result = await user_activity_service.get_user_activity_summary(sample_user.id)
        
        # Assert
        assert result is not None
        assert "posts" in result
        assert "comments" in result  
        assert "reactions" in result
        assert "summary" in result
        
        # Verify posts are grouped by page type
        assert "board" in result["posts"]
        assert "info" in result["posts"]
        assert "services" in result["posts"]
        assert "tips" in result["posts"]
        
        # Verify comments include subtype information
        assert len(result["comments"]) == 3
        inquiry_comments = [c for c in result["comments"] if c.get("subtype") == "inquiry"]
        review_comments = [c for c in result["comments"] if c.get("subtype") == "review"]
        assert len(inquiry_comments) == 1
        assert len(review_comments) == 1
        
        # Verify reactions are grouped by type and page
        assert "likes" in result["reactions"]
        assert "bookmarks" in result["reactions"]
        assert "dislikes" in result["reactions"]
        
        # Verify reaction structure has page type groups
        for reaction_type in ["likes", "bookmarks", "dislikes"]:
            assert reaction_type in result["reactions"]
            for page_type in ["board", "info", "services", "tips"]:
                assert page_type in result["reactions"][reaction_type]
                assert isinstance(result["reactions"][reaction_type][page_type], list)
        
        # Verify routing information is included
        for post_group in result["posts"].values():
            for post in post_group:
                assert "route_path" in post
                
        for comment in result["comments"]:
            assert "route_path" in comment
            
        for reaction_type_group in result["reactions"].values():
            for page_group in reaction_type_group.values():
                for reaction in page_group:
                    assert "route_path" in reaction

    async def test_get_user_posts_by_page_type(
        self, user_activity_service, mock_post_repository, sample_user, sample_posts
    ):
        """Test retrieval of user posts grouped by page type."""
        # Arrange
        mock_post_repository.find_by_author.return_value = sample_posts
        
        # Act
        result = await user_activity_service._get_user_posts_by_page_type(sample_user.id)
        
        # Assert
        assert isinstance(result, dict)
        assert "board" in result
        assert "info" in result
        assert "services" in result
        assert "tips" in result
        
        # Verify each group contains correct posts
        assert len(result["board"]) == 1
        assert result["board"][0]["title"] == "게시판 게시글"
        assert result["board"][0]["route_path"] == "/board-post/board-post-slug"
        
        assert len(result["info"]) == 1
        assert result["info"][0]["title"] == "입주 정보 게시글"
        assert result["info"][0]["route_path"] == "/property-info/info-post-slug"
        
        assert len(result["services"]) == 1
        assert result["services"][0]["title"] == "이사 서비스 게시글"
        assert result["services"][0]["route_path"] == "/moving-services-post/services-post-slug"
        
        assert len(result["tips"]) == 1
        assert result["tips"][0]["title"] == "전문가 꿀팁"
        assert result["tips"][0]["route_path"] == "/expert-tips/tips-post-slug"

    async def test_get_user_comments_with_subtype(
        self, user_activity_service, mock_comment_repository, sample_user, sample_comments
    ):
        """Test retrieval of user comments with subtype information."""
        # Arrange
        mock_comment_repository.find_by_author.return_value = sample_comments
        
        # Act
        result = await user_activity_service._get_user_comments_with_subtype(sample_user.id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        
        # Find inquiry and review comments
        inquiry_comment = next((c for c in result if c.get("subtype") == "inquiry"), None)
        review_comment = next((c for c in result if c.get("subtype") == "review"), None)
        regular_comment = next((c for c in result if c.get("subtype") is None), None)
        
        assert inquiry_comment is not None
        assert inquiry_comment["content"] == "서비스 문의 댓글입니다"
        assert inquiry_comment["route_path"] == "/moving-services-post/services-post-slug"
        
        assert review_comment is not None
        assert review_comment["content"] == "서비스 후기 댓글입니다"
        assert review_comment["route_path"] == "/moving-services-post/services-post-slug"
        
        assert regular_comment is not None
        assert regular_comment["content"] == "일반 댓글입니다"
        assert regular_comment["route_path"] == "/board-post/board-post-slug"

    async def test_get_user_reactions_grouped_legacy(
        self, user_activity_service, mock_user_reaction_repository, sample_user, sample_reactions
    ):
        """Test retrieval of user reactions grouped by type (legacy method)."""
        # Arrange
        mock_user_reaction_repository.find_by_user.return_value = sample_reactions
        
        # Act
        result = await user_activity_service._get_user_reactions_grouped(sample_user.id)
        
        # Assert
        assert isinstance(result, dict)
        assert "likes" in result
        assert "bookmarks" in result
        assert "dislikes" in result
        
        # Verify likes include post, comment, and tips likes
        assert len(result["likes"]) == 3  # board post + board comment + tips post
        post_likes = [r for r in result["likes"] if r["target_type"] == "post"]
        comment_likes = [r for r in result["likes"] if r["target_type"] == "comment"]
        
        assert len(post_likes) == 2  # board post + tips post
        assert len(comment_likes) == 1  # board comment
        
        # Verify bookmarks
        assert len(result["bookmarks"]) == 1
        assert result["bookmarks"][0]["route_path"] == "/property-info/info-post-slug"
        assert result["bookmarks"][0]["target_title"] == "입주 정보 게시글"
        
        # Verify dislikes
        assert len(result["dislikes"]) == 1
        assert result["dislikes"][0]["route_path"] == "/moving-services-post/services-post-slug"
        assert result["dislikes"][0]["target_title"] == "이사 서비스 게시글"

    def test_generate_route_path(self, user_activity_service):
        """Test route path generation for different page types."""
        # Test board posts
        board_path = user_activity_service._generate_route_path("board", "test-slug")
        assert board_path == "/board-post/test-slug"
        
        # Test info posts
        info_path = user_activity_service._generate_route_path("info", "info-slug")
        assert info_path == "/property-info/info-slug"
        
        # Test services posts
        services_path = user_activity_service._generate_route_path("services", "service-slug")
        assert services_path == "/moving-services-post/service-slug"
        
        # Test tips posts
        tips_path = user_activity_service._generate_route_path("tips", "tips-slug")
        assert tips_path == "/expert-tips/tips-slug"
        
        # Test unknown type (should return default)
        unknown_path = user_activity_service._generate_route_path("unknown", "test-slug")
        assert unknown_path == "/post/test-slug"

    async def test_get_user_activity_summary_empty_data(
        self, user_activity_service, mock_post_repository, mock_comment_repository, 
        mock_user_reaction_repository, sample_user
    ):
        """Test user activity summary with no data."""
        # Arrange
        mock_post_repository.find_by_author.return_value = []
        mock_comment_repository.find_by_author.return_value = []
        mock_user_reaction_repository.find_by_user.return_value = []
        
        # Act
        result = await user_activity_service.get_user_activity_summary(sample_user.id)
        
        # Assert
        assert result is not None
        assert result["posts"] == {"board": [], "info": [], "services": [], "tips": []}
        assert result["comments"] == []
        
        # Verify empty reactions structure
        expected_reactions = {
            "likes": {"board": [], "info": [], "services": [], "tips": []},
            "bookmarks": {"board": [], "info": [], "services": [], "tips": []},
            "dislikes": {"board": [], "info": [], "services": [], "tips": []}
        }
        assert result["reactions"] == expected_reactions
        
        assert result["summary"]["total_posts"] == 0
        assert result["summary"]["total_comments"] == 0
        assert result["summary"]["total_reactions"] == 0

    async def test_repository_error_handling(
        self, user_activity_service, mock_post_repository, sample_user
    ):
        """Test error handling when repository operations fail."""
        # Arrange
        mock_post_repository.find_by_author.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await user_activity_service._get_user_posts_by_page_type(sample_user.id)

    async def test_get_user_activity_summary_with_pagination(
        self, user_activity_service, mock_post_repository, mock_comment_repository, 
        mock_user_reaction_repository, sample_user, sample_posts, sample_comments, sample_reactions
    ):
        """Test user activity summary with pagination parameters."""
        # Arrange
        mock_post_repository.find_by_author_paginated.return_value = sample_posts[:2]  # 2개만 반환
        mock_post_repository.count_by_author.return_value = 4  # 총 4개
        mock_comment_repository.find_by_author_paginated.return_value = sample_comments[:1]  # 1개만 반환
        mock_comment_repository.count_by_author.return_value = 3  # 총 3개
        mock_user_reaction_repository.find_by_user_paginated.return_value = sample_reactions[:2]  # 2개만 반환
        mock_user_reaction_repository.count_by_user.return_value = 3  # 총 3개
        
        # Act
        result = await user_activity_service.get_user_activity_summary_paginated(
            user_id=sample_user.id,
            page=1,
            limit=10
        )
        
        # Assert
        assert result is not None
        assert "posts" in result
        assert "comments" in result  
        assert "reactions" in result
        assert "pagination" in result
        
        # 페이지네이션 정보 확인
        assert result["pagination"]["posts"]["total_count"] == 4
        assert result["pagination"]["posts"]["page"] == 1
        assert result["pagination"]["posts"]["limit"] == 10
        assert result["pagination"]["posts"]["has_more"] == False  # 4개 중 10개 요청이므로 더이상 없음
        
        assert result["pagination"]["comments"]["total_count"] == 3
        assert result["pagination"]["comments"]["page"] == 1
        assert result["pagination"]["comments"]["limit"] == 10
        assert result["pagination"]["comments"]["has_more"] == False
        
        assert result["pagination"]["reactions"]["total_count"] == 3
        assert result["pagination"]["reactions"]["page"] == 1
        assert result["pagination"]["reactions"]["limit"] == 10
        assert result["pagination"]["reactions"]["has_more"] == False
        
        # Repository 메서드가 올바른 파라미터로 호출되었는지 확인
        mock_post_repository.find_by_author_paginated.assert_called_once_with(sample_user.id, 10, 0)
        mock_post_repository.count_by_author.assert_called_once_with(sample_user.id)
        mock_comment_repository.find_by_author_paginated.assert_called_once_with(sample_user.id, 10, 0)
        mock_comment_repository.count_by_author.assert_called_once_with(sample_user.id)
        mock_user_reaction_repository.find_by_user_paginated.assert_called_once_with(sample_user.id, 10, 0)
        mock_user_reaction_repository.count_by_user.assert_called_once_with(sample_user.id)

    async def test_pagination_has_more_calculation(
        self, user_activity_service, mock_post_repository, mock_comment_repository, 
        mock_user_reaction_repository, sample_user
    ):
        """Test has_more calculation for pagination."""
        # Arrange - 많은 데이터가 있는 상황
        mock_post_repository.find_by_author_paginated.return_value = []
        mock_post_repository.count_by_author.return_value = 25  # 총 25개
        mock_comment_repository.find_by_author_paginated.return_value = []
        mock_comment_repository.count_by_author.return_value = 15  # 총 15개
        mock_user_reaction_repository.find_by_user_paginated.return_value = []
        mock_user_reaction_repository.count_by_user.return_value = 8   # 총 8개
        
        # Act - page=2, limit=10으로 요청
        result = await user_activity_service.get_user_activity_summary_paginated(
            user_id=sample_user.id,
            page=2,
            limit=10
        )
        
        # Assert
        # Posts: 25개 총, 2페이지(11-20), 더 있음
        assert result["pagination"]["posts"]["has_more"] == True  # 25 > 20이므로 더 있음
        
        # Comments: 15개 총, 2페이지(11-15), 더 없음  
        assert result["pagination"]["comments"]["has_more"] == False  # 15 <= 20이므로 더 없음
        
        # Reactions: 8개 총, 2페이지 요청했지만 이미 1페이지에서 모두 끝남
        assert result["pagination"]["reactions"]["has_more"] == False  # 8 <= 20이므로 더 없음
        
        # Repository가 올바른 skip 값으로 호출되었는지 확인
        mock_post_repository.find_by_author_paginated.assert_called_once_with(sample_user.id, 10, 10)
        mock_comment_repository.find_by_author_paginated.assert_called_once_with(sample_user.id, 10, 10)
        mock_user_reaction_repository.find_by_user_paginated.assert_called_once_with(sample_user.id, 10, 10)

    # 새로운 페이지별 분류 테스트 추가
    def test_extract_page_type_from_reaction(self, user_activity_service):
        """Test page type extraction from reaction route_path."""
        # Test board reactions
        board_path = user_activity_service._extract_page_type_from_reaction("/board-post/test-slug")
        assert board_path == "board"
        
        # Test info reactions  
        info_path = user_activity_service._extract_page_type_from_reaction("/property-info/test-slug")
        assert info_path == "info"
        
        # Test services reactions
        services_path = user_activity_service._extract_page_type_from_reaction("/moving-services-post/test-slug")
        assert services_path == "services"
        
        # Test tips reactions
        tips_path = user_activity_service._extract_page_type_from_reaction("/expert-tips/test-slug")
        assert tips_path == "tips"
        
        # Test unknown route (should return None)
        unknown_path = user_activity_service._extract_page_type_from_reaction("/unknown/test-slug")
        assert unknown_path is None

    async def test_get_user_reactions_grouped_by_page_type_paginated(
        self, user_activity_service, mock_user_reaction_repository, mock_post_repository, sample_user, sample_reactions
    ):
        """Test retrieval of user reactions grouped by page type and reaction type."""
        # Arrange
        mock_user_reaction_repository.find_by_user_paginated.return_value = sample_reactions
        
        # Mock post repository responses for post reactions
        async def mock_get_by_id(post_id):
            mock_post = Mock()
            mock_post.status = "active"
            if post_id == "507f1f77bcf86cd799439012":
                mock_post.title = "게시판 게시글"
            elif post_id == "507f1f77bcf86cd799439013":
                mock_post.title = "입주 정보 게시글"
            elif post_id == "507f1f77bcf86cd799439014":
                mock_post.title = "이사 서비스 게시글"
            elif post_id == "507f1f77bcf86cd799439015":
                mock_post.title = "전문가 꿀팁"
            return mock_post
        
        mock_post_repository.get_by_id.side_effect = mock_get_by_id
        
        # Act
        result = await user_activity_service._get_user_reactions_grouped_paginated(sample_user.id, 10, 0)
        
        # Assert
        assert isinstance(result, dict)
        
        # Verify structure has both reaction type and page type grouping
        for reaction_type in ["likes", "bookmarks", "dislikes"]:
            assert reaction_type in result
            for page_type in ["board", "info", "services", "tips"]:
                assert page_type in result[reaction_type]
                assert isinstance(result[reaction_type][page_type], list)
        
        # Verify specific counts by page type
        assert len(result["likes"]["board"]) == 2  # post like + comment like
        assert len(result["likes"]["info"]) == 0
        assert len(result["likes"]["services"]) == 0
        assert len(result["likes"]["tips"]) == 1  # tips like
        
        assert len(result["bookmarks"]["board"]) == 0
        assert len(result["bookmarks"]["info"]) == 1  # info bookmark
        assert len(result["bookmarks"]["services"]) == 0
        assert len(result["bookmarks"]["tips"]) == 0
        
        assert len(result["dislikes"]["board"]) == 0
        assert len(result["dislikes"]["info"]) == 0
        assert len(result["dislikes"]["services"]) == 1  # services dislike
        assert len(result["dislikes"]["tips"]) == 0
        
        # Verify reaction data structure
        board_post_like = result["likes"]["board"][0]
        assert board_post_like["target_type"] == "post"
        assert board_post_like["route_path"] == "/board-post/board-post-slug"
        assert board_post_like["target_title"] == "게시판 게시글"
        assert board_post_like["title"] == "게시판 게시글"
        
        info_bookmark = result["bookmarks"]["info"][0]
        assert info_bookmark["target_type"] == "post"
        assert info_bookmark["route_path"] == "/property-info/info-post-slug"
        assert info_bookmark["target_title"] == "입주 정보 게시글"
        assert info_bookmark["title"] == "입주 정보 게시글"
        
        services_dislike = result["dislikes"]["services"][0]
        assert services_dislike["target_type"] == "post"
        assert services_dislike["route_path"] == "/moving-services-post/services-post-slug"
        assert services_dislike["target_title"] == "이사 서비스 게시글"
        assert services_dislike["title"] == "이사 서비스 게시글"
        
        tips_like = result["likes"]["tips"][0]
        assert tips_like["target_type"] == "post"
        assert tips_like["route_path"] == "/expert-tips/tips-post-slug"
        assert tips_like["target_title"] == "전문가 꿀팁"
        assert tips_like["title"] == "전문가 꿀팁"