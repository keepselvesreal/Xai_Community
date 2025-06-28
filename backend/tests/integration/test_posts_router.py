"""Integration tests for posts router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from nadle_backend.models.core import User, Post, PostCreate


@pytest.fixture
def mock_posts_service():
    """Create mock posts service."""
    service = MagicMock()
    service.create_post = AsyncMock()
    service.get_post = AsyncMock()
    service.list_posts = AsyncMock()
    service.update_post = AsyncMock()
    service.delete_post = AsyncMock()
    service.search_posts = AsyncMock()
    return service


@pytest.fixture
def app_with_posts(mock_posts_service):
    """Create test app with mocked posts service."""
    from nadle_backend.routers.posts import router, get_posts_service
    from nadle_backend.dependencies.auth import get_current_active_user, get_optional_current_active_user
    
    app = FastAPI()
    
    # Create mock user for auth
    mock_user = MagicMock()
    mock_user.id = "507f1f77bcf86cd799439011"
    mock_user.email = "john@example.com"
    mock_user.user_handle = "johndoe"
    mock_user.status = "active"
    mock_user.is_admin = False
    
    # Override dependencies
    def get_mock_posts_service():
        return mock_posts_service
    
    def get_mock_current_user():
        return mock_user
    
    def get_mock_optional_current_user():
        return mock_user
    
    app.dependency_overrides[get_posts_service] = get_mock_posts_service
    app.dependency_overrides[get_current_active_user] = get_mock_current_user
    app.dependency_overrides[get_optional_current_active_user] = get_mock_optional_current_user
    app.include_router(router)
    
    return app


@pytest.fixture
def client(app_with_posts):
    """Create test client with mocked dependencies."""
    return TestClient(app_with_posts)


class TestPostsRouter:
    """Test suite for posts router endpoints."""
    
    @pytest.fixture
    def sample_user(self):
        """Sample user fixture."""
        user = MagicMock()
        user.id = "507f1f77bcf86cd799439011"
        user.email = "john@example.com"
        user.user_handle = "johndoe"
        user.password_hash = "hashed_password"
        user.status = "active"
        user.is_admin = False
        return user
    
    @pytest.fixture
    def sample_post(self):
        """Sample post fixture."""
        post = MagicMock()
        post.id = "507f1f77bcf86cd799439012"
        post.title = "Test Post"
        post.content = "This is a test post content"
        post.service = "X"
        post.tags = ["test", "python"]
        post.slug = "test-post"
        post.author_id = "507f1f77bcf86cd799439011"
        post.status = "published"
        post.view_count = 0
        post.like_count = 0
        post.comment_count = 0
        post.share_count = 0
        
        # Mock the model_dump method
        post.model_dump.return_value = {
            "_id": "507f1f77bcf86cd799439012",
            "title": "Test Post",
            "content": "This is a test post content",
            "service": "X",
            "tags": ["test", "python"],
            "slug": "test-post",
            "author_id": "507f1f77bcf86cd799439011",
            "status": "published",
            "metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "published_at": "2024-01-01T00:00:00",
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0
        }
        return post
    
    def test_posts_router_with_auth(self, client, mock_posts_service, sample_post):
        """Test posts router endpoints with authentication."""
        # Test POST /posts (create post)
        mock_posts_service.create_post.return_value = sample_post.model_dump()
        response = client.post(
            "/api/posts",
            json={
                "title": "Test Post",
                "content": "This is a test post content",
                "service": "X",
                "tags": ["test", "python"]
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Post"
        
        # Test GET /posts (list posts)
        mock_posts_service.list_posts.return_value = {
            "items": [sample_post.model_dump()],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        response = client.get("/api/posts")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        
        # Test GET /posts/{slug} (get post)
        mock_posts_service.get_post.return_value = sample_post.model_dump()
        response = client.get("/api/posts/test-post")
        assert response.status_code == 200
        assert response.json()["slug"] == "test-post"
        
        # Test PUT /posts/{slug} (update post)
        mock_posts_service.update_post.return_value = sample_post.model_dump()
        response = client.put(
            "/api/posts/test-post",
            json={"title": "Updated Test Post"},
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 200
        
        # Test DELETE /posts/{slug} (delete post)
        mock_posts_service.delete_post.return_value = True
        response = client.delete(
            "/api/posts/test-post",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 204
        
        # Test GET /posts/search (search posts)
        mock_posts_service.search_posts.return_value = {
            "items": [sample_post.model_dump()],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        response = client.get("/api/posts/search?q=test")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1