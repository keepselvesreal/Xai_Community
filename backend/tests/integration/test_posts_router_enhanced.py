"""Enhanced integration tests for posts router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from src.models.core import PostMetadata
from src.exceptions.post import PostNotFoundError, PostPermissionError


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
    from src.routers.posts import router, get_posts_service
    from src.dependencies.auth import get_current_active_user, get_optional_current_active_user
    
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
    """Create test client."""
    return TestClient(app_with_posts)


class TestPostCreation:
    """Test post creation endpoints."""
    
    def test_create_post_success(self, client, mock_posts_service):
        """Test successful post creation."""
        # Arrange
        post_data = {
            "title": "Test Post",
            "content": "This is a test post content.",
            "service": "community",
            "metadata": {
                "type": "자유게시판",
                "tags": ["test", "sample"],
                "editor_type": "plain"
            }
        }
        
        mock_post = {
            "id": "post123",
            "title": "Test Post",
            "content": "This is a test post content.",
            "slug": "test-post",
            "author_id": "507f1f77bcf86cd799439011",
            "service": "community",
            "status": "published",
            "metadata": post_data["metadata"]
        }
        
        mock_posts_service.create_post.return_value = mock_post
        
        # Act
        response = client.post("/api/posts", json=post_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Post"
        assert data["slug"] == "test-post"
        mock_posts_service.create_post.assert_called_once()
    
    def test_create_post_unauthorized(self, client, mock_posts_service):
        """Test post creation without authentication."""
        # Arrange
        post_data = {
            "title": "Test Post",
            "content": "This is a test post content.",
            "service": "community"
        }
        
        with client as c:
            # Remove auth dependency override
            from src.dependencies.auth import get_current_active_user
            if get_current_active_user in c.app.dependency_overrides:
                del c.app.dependency_overrides[get_current_active_user]
            
            # Act
            response = c.post("/api/posts", json=post_data)
            
            # Assert
            assert response.status_code == 401
    
    def test_create_post_invalid_data(self, client, mock_posts_service):
        """Test post creation with invalid data."""
        # Arrange
        invalid_data = {
            "title": "",  # Empty title
            "content": "",  # Empty content
            "service": "invalid_service"  # Invalid service type
        }
        
        # Act
        response = client.post("/api/posts", json=invalid_data)
        
        # Assert
        assert response.status_code == 422  # Validation error


class TestPostRetrieval:
    """Test post retrieval endpoints."""
    
    def test_get_post_success(self, client, mock_posts_service):
        """Test successful post retrieval."""
        # Arrange
        slug = "test-post"
        mock_post = {
            "id": "post123",
            "title": "Test Post",
            "content": "This is a test post content.",
            "slug": slug,
            "author_id": "507f1f77bcf86cd799439011",
            "service": "community",
            "status": "published"
        }
        
        mock_posts_service.get_post.return_value = mock_post
        
        # Act
        response = client.get(f"/api/posts/{slug}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Post"
        assert data["slug"] == slug
        mock_posts_service.get_post.assert_called_once_with(slug, None)
    
    def test_get_post_not_found(self, client, mock_posts_service):
        """Test post retrieval when post not found."""
        # Arrange
        slug = "non-existent-post"
        mock_posts_service.get_post.side_effect = PostNotFoundError(slug=slug)
        
        # Act
        response = client.get(f"/api/posts/{slug}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_posts_success(self, client, mock_posts_service):
        """Test successful posts listing."""
        # Arrange
        mock_response = {
            "items": [
                {
                    "id": "post1",
                    "title": "Post 1",
                    "slug": "post-1",
                    "service": "community"
                },
                {
                    "id": "post2",
                    "title": "Post 2",
                    "slug": "post-2",
                    "service": "community"
                }
            ],
            "total": 2,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        
        mock_posts_service.list_posts.return_value = mock_response
        
        # Act
        response = client.get("/api/posts")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        mock_posts_service.list_posts.assert_called_once()
    
    def test_list_posts_with_filters(self, client, mock_posts_service):
        """Test posts listing with filters."""
        # Arrange
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "total_pages": 0
        }
        
        mock_posts_service.list_posts.return_value = mock_response
        
        # Act
        response = client.get(
            "/api/posts?service_type=community&page=1&page_size=10&sort_by=created_at"
        )
        
        # Assert
        assert response.status_code == 200
        mock_posts_service.list_posts.assert_called_once()


class TestPostUpdate:
    """Test post update endpoints."""
    
    def test_update_post_success(self, client, mock_posts_service):
        """Test successful post update."""
        # Arrange
        slug = "test-post"
        update_data = {
            "title": "Updated Test Post",
            "content": "Updated content"
        }
        
        mock_updated_post = {
            "id": "post123",
            "title": "Updated Test Post",
            "content": "Updated content",
            "slug": "updated-test-post",
            "author_id": "507f1f77bcf86cd799439011",
            "service": "community"
        }
        
        mock_posts_service.update_post.return_value = mock_updated_post
        
        # Act
        response = client.put(f"/api/posts/{slug}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Test Post"
        mock_posts_service.update_post.assert_called_once()
    
    def test_update_post_unauthorized(self, client, mock_posts_service):
        """Test post update without authentication."""
        # Arrange
        slug = "test-post"
        update_data = {"title": "Updated Title"}
        
        with client as c:
            from src.dependencies.auth import get_current_active_user
            if get_current_active_user in c.app.dependency_overrides:
                del c.app.dependency_overrides[get_current_active_user]
            
            # Act
            response = c.put(f"/api/posts/{slug}", json=update_data)
            
            # Assert
            assert response.status_code == 401
    
    def test_update_post_permission_denied(self, client, mock_posts_service):
        """Test post update with permission denied."""
        # Arrange
        slug = "test-post"
        update_data = {"title": "Updated Title"}
        
        mock_posts_service.update_post.side_effect = PostPermissionError("Permission denied")
        
        # Act
        response = client.put(f"/api/posts/{slug}", json=update_data)
        
        # Assert
        assert response.status_code == 403
        assert "permission denied" in response.json()["detail"].lower()


class TestPostDeletion:
    """Test post deletion endpoints."""
    
    def test_delete_post_success(self, client, mock_posts_service):
        """Test successful post deletion."""
        # Arrange
        slug = "test-post"
        mock_posts_service.delete_post.return_value = True
        
        # Act
        response = client.delete(f"/api/posts/{slug}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Post deleted successfully"
        mock_posts_service.delete_post.assert_called_once()
    
    def test_delete_post_not_found(self, client, mock_posts_service):
        """Test post deletion when post not found."""
        # Arrange
        slug = "non-existent-post"
        mock_posts_service.delete_post.side_effect = PostNotFoundError(slug=slug)
        
        # Act
        response = client.delete(f"/api/posts/{slug}")
        
        # Assert
        assert response.status_code == 404
    
    def test_delete_post_permission_denied(self, client, mock_posts_service):
        """Test post deletion with permission denied."""
        # Arrange
        slug = "test-post"
        mock_posts_service.delete_post.side_effect = PostPermissionError("Permission denied")
        
        # Act
        response = client.delete(f"/api/posts/{slug}")
        
        # Assert
        assert response.status_code == 403


class TestPostSearch:
    """Test post search endpoints."""
    
    def test_search_posts_success(self, client, mock_posts_service):
        """Test successful post search."""
        # Arrange
        search_query = "test"
        mock_response = {
            "items": [
                {
                    "id": "post1",
                    "title": "Test Post 1",
                    "slug": "test-post-1",
                    "content": "Content with test keyword"
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        
        mock_posts_service.search_posts.return_value = mock_response
        
        # Act
        response = client.get(f"/api/posts/search?q={search_query}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        mock_posts_service.search_posts.assert_called_once()
    
    def test_search_posts_empty_query(self, client, mock_posts_service):
        """Test post search with empty query."""
        # Act
        response = client.get("/api/posts/search?q=")
        
        # Assert
        assert response.status_code == 400
        assert "query cannot be empty" in response.json()["detail"].lower()
    
    def test_search_posts_with_filters(self, client, mock_posts_service):
        """Test post search with additional filters."""
        # Arrange
        mock_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0
        }
        
        mock_posts_service.search_posts.return_value = mock_response
        
        # Act
        response = client.get(
            "/api/posts/search?q=test&service_type=community&sort_by=relevance"
        )
        
        # Assert
        assert response.status_code == 200
        mock_posts_service.search_posts.assert_called_once_with(
            query="test",
            service_type="community",
            sort_by="relevance",
            page=1,
            page_size=20,
            current_user=mock_posts_service.list_posts.call_args[1].get("current_user") if mock_posts_service.list_posts.call_args else None
        )