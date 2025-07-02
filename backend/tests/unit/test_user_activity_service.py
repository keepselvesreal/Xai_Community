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
        
        # Bookmark
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
        
        # Verify reactions are grouped by type
        assert "likes" in result["reactions"]
        assert "bookmarks" in result["reactions"]
        
        # Verify routing information is included
        for post_group in result["posts"].values():
            for post in post_group:
                assert "route_path" in post
                
        for comment in result["comments"]:
            assert "route_path" in comment
            
        for reaction_group in result["reactions"].values():
            for reaction in reaction_group:
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

    async def test_get_user_reactions_grouped(
        self, user_activity_service, mock_user_reaction_repository, sample_user, sample_reactions
    ):
        """Test retrieval of user reactions grouped by type."""
        # Arrange
        mock_user_reaction_repository.find_by_user.return_value = sample_reactions
        
        # Act
        result = await user_activity_service._get_user_reactions_grouped(sample_user.id)
        
        # Assert
        assert isinstance(result, dict)
        assert "likes" in result
        assert "bookmarks" in result
        
        # Verify likes include both post and comment likes
        assert len(result["likes"]) == 2
        post_like = next((r for r in result["likes"] if r["target_type"] == "post"), None)
        comment_like = next((r for r in result["likes"] if r["target_type"] == "comment"), None)
        
        assert post_like is not None
        assert post_like["route_path"] == "/board-post/board-post-slug"
        assert post_like["target_title"] == "게시판 게시글"
        
        assert comment_like is not None
        assert comment_like["route_path"] == "/board-post/board-post-slug"
        assert comment_like["target_title"] == "일반 댓글입니다"
        
        # Verify bookmarks
        assert len(result["bookmarks"]) == 1
        assert result["bookmarks"][0]["route_path"] == "/property-info/info-post-slug"
        assert result["bookmarks"][0]["target_title"] == "입주 정보 게시글"

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
        assert result["reactions"] == {"likes": [], "bookmarks": [], "dislikes": []}
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