"""Integration tests for user activity API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from nadle_backend.models.core import User


@pytest.fixture
def mock_user_activity_service():
    """Create mock user activity service."""
    service = MagicMock()
    service.get_user_activity_summary = AsyncMock()
    return service


@pytest.fixture
def mock_auth_dependency():
    """Create mock auth dependency."""
    def get_current_user():
        user = MagicMock()
        user.id = "507f1f77bcf86cd799439011"
        user.email = "john@example.com"
        user.user_handle = "johndoe"
        user.display_name = "John Doe"
        user.created_at = datetime.utcnow()
        return user
    
    return get_current_user


@pytest.fixture
def app_with_user_activity(mock_user_activity_service, mock_auth_dependency):
    """Create test app with mocked user activity service."""
    from nadle_backend.routers.users import router, get_user_activity_service
    from nadle_backend.dependencies.auth import get_current_user
    
    app = FastAPI()
    
    # Override dependencies
    def get_mock_user_activity_service():
        return mock_user_activity_service
    
    app.dependency_overrides[get_user_activity_service] = get_mock_user_activity_service
    app.dependency_overrides[get_current_user] = mock_auth_dependency
    app.include_router(router, prefix="/users")
    
    return app


@pytest.fixture
def client(app_with_user_activity):
    """Create test client with mocked dependencies."""
    return TestClient(app_with_user_activity)


@pytest.fixture
def sample_activity_data():
    """Sample user activity data."""
    return {
        "posts": {
            "board": [
                {
                    "id": "507f1f77bcf86cd799439012",
                    "title": "게시판 게시글",
                    "slug": "board-post-slug",
                    "created_at": "2024-01-01T10:00:00Z",
                    "like_count": 5,
                    "comment_count": 3,
                    "route_path": "/board-post/board-post-slug"
                }
            ],
            "info": [
                {
                    "id": "507f1f77bcf86cd799439013",
                    "title": "입주 정보 게시글",
                    "slug": "info-post-slug",
                    "created_at": "2024-01-01T11:00:00Z",
                    "like_count": 2,
                    "comment_count": 1,
                    "route_path": "/property-info/info-post-slug"
                }
            ],
            "services": [
                {
                    "id": "507f1f77bcf86cd799439014",
                    "title": "이사 서비스 게시글",
                    "slug": "services-post-slug",
                    "created_at": "2024-01-01T12:00:00Z",
                    "like_count": 1,
                    "comment_count": 2,
                    "route_path": "/moving-services-post/services-post-slug"
                }
            ],
            "tips": [
                {
                    "id": "507f1f77bcf86cd799439015",
                    "title": "전문가 꿀팁",
                    "slug": "tips-post-slug",
                    "created_at": "2024-01-01T13:00:00Z",
                    "like_count": 8,
                    "comment_count": 5,
                    "route_path": "/expert-tips/tips-post-slug"
                }
            ]
        },
        "comments": [
            {
                "id": "507f1f77bcf86cd799439020",
                "content": "일반 댓글입니다",
                "parent_id": "507f1f77bcf86cd799439012",
                "created_at": "2024-01-01T14:00:00Z",
                "route_path": "/board-post/board-post-slug",
                "subtype": None
            },
            {
                "id": "507f1f77bcf86cd799439021",
                "content": "서비스 문의 댓글입니다",
                "parent_id": "507f1f77bcf86cd799439014",
                "created_at": "2024-01-01T15:00:00Z",
                "route_path": "/moving-services-post/services-post-slug",
                "subtype": "inquiry"
            },
            {
                "id": "507f1f77bcf86cd799439022",
                "content": "서비스 후기 댓글입니다",
                "parent_id": "507f1f77bcf86cd799439014",
                "created_at": "2024-01-01T16:00:00Z",
                "route_path": "/moving-services-post/services-post-slug",
                "subtype": "review"
            }
        ],
        "reactions": {
            "likes": [
                {
                    "id": "507f1f77bcf86cd799439030",
                    "target_type": "post",
                    "target_id": "507f1f77bcf86cd799439012",
                    "created_at": "2024-01-01T17:00:00Z",
                    "route_path": "/board-post/board-post-slug",
                    "target_title": "게시판 게시글"
                },
                {
                    "id": "507f1f77bcf86cd799439031",
                    "target_type": "comment",
                    "target_id": "507f1f77bcf86cd799439020",
                    "created_at": "2024-01-01T18:00:00Z",
                    "route_path": "/board-post/board-post-slug",
                    "target_title": "일반 댓글입니다"
                }
            ],
            "bookmarks": [
                {
                    "id": "507f1f77bcf86cd799439032",
                    "target_type": "post",
                    "target_id": "507f1f77bcf86cd799439013",
                    "created_at": "2024-01-01T19:00:00Z",
                    "route_path": "/property-info/info-post-slug",
                    "target_title": "입주 정보 게시글"
                }
            ],
            "dislikes": []
        },
        "summary": {
            "total_posts": 4,
            "total_comments": 3,
            "total_reactions": 3,
            "most_active_page_type": "board"
        }
    }


class TestUserActivityAPI:
    """Test suite for User Activity API endpoints."""

    def test_get_user_activity_success(
        self, client, mock_user_activity_service, sample_activity_data
    ):
        """Test successful retrieval of user activity."""
        # Arrange
        mock_user_activity_service.get_user_activity_summary.return_value = sample_activity_data
        
        # Act
        response = client.get("/users/me/activity")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "posts" in data
        assert "comments" in data
        assert "reactions" in data
        assert "summary" in data
        
        # Verify post data grouped by page type
        assert "board" in data["posts"]
        assert "info" in data["posts"]
        assert "services" in data["posts"]
        assert "tips" in data["posts"]
        
        # Verify post routing information
        board_post = data["posts"]["board"][0]
        assert board_post["title"] == "게시판 게시글"
        assert board_post["route_path"] == "/board-post/board-post-slug"
        assert board_post["like_count"] == 5
        assert board_post["comment_count"] == 3
        
        info_post = data["posts"]["info"][0]
        assert info_post["route_path"] == "/property-info/info-post-slug"
        
        services_post = data["posts"]["services"][0]
        assert services_post["route_path"] == "/moving-services-post/services-post-slug"
        
        tips_post = data["posts"]["tips"][0]
        assert tips_post["route_path"] == "/expert-tips/tips-post-slug"
        
        # Verify comment data with subtype information
        assert len(data["comments"]) == 3
        
        regular_comment = next((c for c in data["comments"] if c["subtype"] is None), None)
        assert regular_comment is not None
        assert regular_comment["content"] == "일반 댓글입니다"
        assert regular_comment["route_path"] == "/board-post/board-post-slug"
        
        inquiry_comment = next((c for c in data["comments"] if c["subtype"] == "inquiry"), None)
        assert inquiry_comment is not None
        assert inquiry_comment["content"] == "서비스 문의 댓글입니다"
        assert inquiry_comment["route_path"] == "/moving-services-post/services-post-slug"
        
        review_comment = next((c for c in data["comments"] if c["subtype"] == "review"), None)
        assert review_comment is not None
        assert review_comment["content"] == "서비스 후기 댓글입니다"
        assert review_comment["route_path"] == "/moving-services-post/services-post-slug"
        
        # Verify reaction data grouped by type
        assert "likes" in data["reactions"]
        assert "bookmarks" in data["reactions"]
        assert "dislikes" in data["reactions"]
        
        assert len(data["reactions"]["likes"]) == 2
        assert len(data["reactions"]["bookmarks"]) == 1
        assert len(data["reactions"]["dislikes"]) == 0
        
        # Verify reaction routing information
        post_like = next((r for r in data["reactions"]["likes"] if r["target_type"] == "post"), None)
        assert post_like is not None
        assert post_like["route_path"] == "/board-post/board-post-slug"
        assert post_like["target_title"] == "게시판 게시글"
        
        bookmark = data["reactions"]["bookmarks"][0]
        assert bookmark["route_path"] == "/property-info/info-post-slug"
        assert bookmark["target_title"] == "입주 정보 게시글"
        
        # Verify summary data
        assert data["summary"]["total_posts"] == 4
        assert data["summary"]["total_comments"] == 3
        assert data["summary"]["total_reactions"] == 3
        assert data["summary"]["most_active_page_type"] == "board"
        
        # Verify service was called with correct user ID
        mock_user_activity_service.get_user_activity_summary.assert_called_once_with("507f1f77bcf86cd799439011")

    def test_get_user_activity_empty_data(
        self, client, mock_user_activity_service
    ):
        """Test user activity endpoint with no data."""
        # Arrange
        empty_data = {
            "posts": {"board": [], "info": [], "services": [], "tips": []},
            "comments": [],
            "reactions": {"likes": [], "bookmarks": [], "dislikes": []},
            "summary": {
                "total_posts": 0,
                "total_comments": 0,
                "total_reactions": 0,
                "most_active_page_type": None
            }
        }
        mock_user_activity_service.get_user_activity_summary.return_value = empty_data
        
        # Act
        response = client.get("/users/me/activity")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["posts"]["board"] == []
        assert data["posts"]["info"] == []
        assert data["posts"]["services"] == []
        assert data["posts"]["tips"] == []
        assert data["comments"] == []
        assert data["reactions"]["likes"] == []
        assert data["reactions"]["bookmarks"] == []
        assert data["reactions"]["dislikes"] == []
        assert data["summary"]["total_posts"] == 0
        assert data["summary"]["total_comments"] == 0
        assert data["summary"]["total_reactions"] == 0

    def test_get_user_activity_unauthorized(self, mock_user_activity_service):
        """Test user activity endpoint without authentication."""
        # Create app without auth override
        from nadle_backend.routers.users import router
        
        app = FastAPI()
        app.include_router(router, prefix="/users")
        client = TestClient(app)
        
        # Act
        response = client.get("/users/me/activity")
        
        # Assert
        assert response.status_code == 401 or response.status_code == 403

    def test_get_user_activity_service_error(
        self, client, mock_user_activity_service
    ):
        """Test user activity endpoint when service raises an error."""
        # Arrange
        mock_user_activity_service.get_user_activity_summary.side_effect = Exception("Service error")
        
        # Act
        response = client.get("/users/me/activity")
        
        # Assert
        assert response.status_code == 500

    def test_get_user_activity_response_format(
        self, client, mock_user_activity_service, sample_activity_data
    ):
        """Test that response matches expected format for frontend consumption."""
        # Arrange
        mock_user_activity_service.get_user_activity_summary.return_value = sample_activity_data
        
        # Act
        response = client.get("/users/me/activity")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify each post has required navigation fields
        for page_type in ["board", "info", "services", "tips"]:
            for post in data["posts"][page_type]:
                assert "id" in post
                assert "title" in post
                assert "slug" in post
                assert "route_path" in post
                assert "created_at" in post
                assert "like_count" in post
                assert "comment_count" in post
        
        # Verify each comment has required navigation fields
        for comment in data["comments"]:
            assert "id" in comment
            assert "content" in comment
            assert "route_path" in comment
            assert "created_at" in comment
            assert "subtype" in comment  # May be None
        
        # Verify each reaction has required navigation fields
        for reaction_type in ["likes", "bookmarks", "dislikes"]:
            for reaction in data["reactions"][reaction_type]:
                assert "id" in reaction
                assert "target_type" in reaction
                assert "route_path" in reaction
                assert "created_at" in reaction
                assert "target_title" in reaction

    def test_get_user_activity_pagination_support(
        self, client, mock_user_activity_service, sample_activity_data
    ):
        """Test user activity endpoint with pagination parameters."""
        # Arrange
        mock_user_activity_service.get_user_activity_summary.return_value = sample_activity_data
        
        # Act
        response = client.get("/users/me/activity?page=1&page_size=10")
        
        # Assert
        assert response.status_code == 200
        
        # Verify service was called with pagination parameters if supported
        # Note: The current implementation might not support pagination yet
        # This test ensures the endpoint accepts pagination parameters without error