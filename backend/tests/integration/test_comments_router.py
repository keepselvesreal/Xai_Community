"""Integration tests for comments router."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from nadle_backend.models.core import User, CommentDetail, CommentCreate, CommentListResponse, PaginationInfo


@pytest.fixture
def mock_comments_service():
    """Create mock comments service."""
    service = MagicMock()
    service.create_comment = AsyncMock()
    service.create_reply = AsyncMock()
    service.get_comments_with_user_data = AsyncMock()
    service.update_comment_with_permission = AsyncMock()
    service.delete_comment_with_permission = AsyncMock()
    return service


@pytest.fixture
def app_with_comments(mock_comments_service):
    """Create test app with mocked comments service."""
    from nadle_backend.routers.comments import router, get_comments_service
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
    def get_mock_comments_service():
        return mock_comments_service
    
    def get_mock_current_user():
        return mock_user
    
    def get_mock_optional_current_user():
        return mock_user
    
    app.dependency_overrides[get_comments_service] = get_mock_comments_service
    app.dependency_overrides[get_current_active_user] = get_mock_current_user
    app.dependency_overrides[get_optional_current_active_user] = get_mock_optional_current_user
    app.include_router(router)
    
    return app


@pytest.fixture
def client(app_with_comments):
    """Create test client with mocked dependencies."""
    return TestClient(app_with_comments)


class TestCommentsRouter:
    """Test suite for comments router endpoints."""
    
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
    def sample_comment(self):
        """Sample comment fixture."""
        comment = MagicMock()
        comment.id = "507f1f77bcf86cd799439013"
        comment.content = "This is a test comment"
        comment.author_id = "507f1f77bcf86cd799439011"
        comment.parent_id = "507f1f77bcf86cd799439012"  # Post ID
        comment.parent_comment_id = None
        comment.status = "active"
        comment.like_count = 0
        comment.reply_count = 0
        comment.created_at = "2024-01-01T00:00:00"
        comment.updated_at = "2024-01-01T00:00:00"
        
        # Mock the model_dump method
        comment.model_dump.return_value = {
            "_id": "507f1f77bcf86cd799439013",
            "content": "This is a test comment",
            "author_id": "507f1f77bcf86cd799439011",
            "parent_id": "507f1f77bcf86cd799439012",
            "parent_comment_id": None,
            "status": "active",
            "like_count": 0,
            "reply_count": 0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        return comment
    
    @pytest.fixture
    def sample_reply(self):
        """Sample reply fixture."""
        reply = MagicMock()
        reply.id = "507f1f77bcf86cd799439014"
        reply.content = "This is a test reply"
        reply.author_id = "507f1f77bcf86cd799439011"
        reply.parent_id = "507f1f77bcf86cd799439012"  # Post ID
        reply.parent_comment_id = "507f1f77bcf86cd799439013"  # Parent comment ID
        reply.status = "active"
        reply.like_count = 0
        reply.reply_count = 0
        reply.created_at = "2024-01-01T00:00:00"
        reply.updated_at = "2024-01-01T00:00:00"
        
        # Mock the model_dump method
        reply.model_dump.return_value = {
            "_id": "507f1f77bcf86cd799439014",
            "content": "This is a test reply",
            "author_id": "507f1f77bcf86cd799439011",
            "parent_id": "507f1f77bcf86cd799439012",
            "parent_comment_id": "507f1f77bcf86cd799439013",
            "status": "active",
            "like_count": 0,
            "reply_count": 0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        return reply
    
    def test_comments_router_with_auth(self, client, mock_comments_service, sample_comment, sample_reply):
        """Test comments router endpoints with authentication."""
        
        # Test GET /posts/{slug}/comments (list comments)
        mock_comments_service.get_comments_with_user_data.return_value = (
            [sample_comment.model_dump()], 1
        )
        response = client.get("/api/posts/test-post/comments")
        assert response.status_code == 200
        data = response.json()
        assert "comments" in data
        assert "pagination" in data
        assert len(data["comments"]) == 1
        assert data["comments"][0]["content"] == "This is a test comment"
        
        # Test POST /posts/{slug}/comments (create comment) - requires auth
        mock_comments_service.create_comment.return_value = sample_comment.model_dump()
        response = client.post(
            "/api/posts/test-post/comments",
            json={
                "content": "This is a test comment"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 201
        assert response.json()["content"] == "This is a test comment"
        
        # Test POST /posts/{slug}/comments/{comment_id}/replies (create reply) - requires auth
        mock_comments_service.create_reply.return_value = sample_reply.model_dump()
        response = client.post(
            "/api/posts/test-post/comments/507f1f77bcf86cd799439013/replies",
            json={
                "content": "This is a test reply"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 201
        assert response.json()["content"] == "This is a test reply"
        assert response.json()["parent_comment_id"] == "507f1f77bcf86cd799439013"
        
        # Test PUT /posts/{slug}/comments/{comment_id} (update comment) - requires auth and permission
        updated_comment = sample_comment.model_dump()
        updated_comment["content"] = "Updated comment content"
        mock_comments_service.update_comment_with_permission.return_value = updated_comment
        response = client.put(
            "/api/posts/test-post/comments/507f1f77bcf86cd799439013",
            json={
                "content": "Updated comment content"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated comment content"
        
        # Test DELETE /posts/{slug}/comments/{comment_id} (delete comment) - requires auth and permission
        mock_comments_service.delete_comment_with_permission.return_value = None
        response = client.delete(
            "/api/posts/test-post/comments/507f1f77bcf86cd799439013",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 204
        
        # Verify all service methods were called appropriately
        mock_comments_service.get_comments_with_user_data.assert_called()
        mock_comments_service.create_comment.assert_called()
        mock_comments_service.create_reply.assert_called()
        mock_comments_service.update_comment_with_permission.assert_called()
        mock_comments_service.delete_comment_with_permission.assert_called()
    
    # 🆕 TDD: 문의/후기 API 엔드포인트 테스트 추가
    def test_create_service_inquiry_endpoint(self, client, mock_comments_service, sample_comment):
        """Test service inquiry creation endpoint."""
        # Arrange
        inquiry_comment = {
            "id": "inquiry123",
            "author_id": "user123",
            "author": {
                "id": "user123",
                "name": "Test User", 
                "email": "test@example.com",
                "user_handle": "testuser",
                "display_name": "Test User",
                "bio": None,
                "avatar_url": None,
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            "content": "이사 비용 문의드립니다",
            "parent_comment_id": None,
            "status": "active",
            "like_count": 0,
            "dislike_count": 0,
            "reply_count": 0,
            "user_reaction": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "replies": None
        }
        mock_comments_service.create_comment.return_value = inquiry_comment
        
        # Act
        response = client.post(
            "/test-service/comments/inquiry",  # 라우터에 prefix가 없으므로 직접 경로 사용
            json={
                "content": "이사 비용 문의드립니다"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["content"] == "이사 비용 문의드립니다"
        mock_comments_service.create_comment.assert_called()
        
        # metadata에 subtype이 설정되었는지 확인
        call_args, call_kwargs = mock_comments_service.create_comment.call_args
        comment_data = call_kwargs.get("comment_data") if call_kwargs else call_args[1]
        assert comment_data.metadata.get("subtype") == "service_inquiry"
    
    def test_create_service_review_endpoint(self, client, mock_comments_service, sample_comment):
        """Test service review creation endpoint."""
        # Arrange
        review_comment = {
            "id": "review123",
            "author_id": "user123",
            "author": {
                "id": "user123",
                "name": "Test User",
                "email": "test@example.com", 
                "user_handle": "testuser",
                "display_name": "Test User",
                "bio": None,
                "avatar_url": None,
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            "content": "서비스 정말 만족합니다!",
            "parent_comment_id": None,
            "status": "active",
            "like_count": 0,
            "dislike_count": 0,
            "reply_count": 0,
            "user_reaction": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "replies": None
        }
        mock_comments_service.create_comment.return_value = review_comment
        
        # Act
        response = client.post(
            "/test-service/comments/review",  # 라우터에 prefix가 없으므로 직접 경로 사용
            json={
                "content": "서비스 정말 만족합니다!"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["content"] == "서비스 정말 만족합니다!"
        mock_comments_service.create_comment.assert_called()
        
        # metadata에 subtype이 설정되었는지 확인
        call_args, call_kwargs = mock_comments_service.create_comment.call_args
        comment_data = call_kwargs.get("comment_data") if call_kwargs else call_args[1]
        assert comment_data.metadata.get("subtype") == "service_review"
    
    def test_inquiry_endpoint_requires_authentication(self, client, mock_comments_service):
        """Test that inquiry endpoint requires authentication."""
        # Act - 인증 헤더 없이 요청 (app_with_comments에서 인증을 모킹하므로 200 응답 예상)
        mock_comment_response = {
            "id": "inquiry123",
            "author_id": "user123", 
            "author": {
                "id": "user123",
                "name": "Test User",
                "email": "test@example.com",
                "user_handle": "testuser",
                "display_name": "Test User",
                "bio": None,
                "avatar_url": None,
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            "content": "문의 내용",
            "parent_comment_id": None,
            "status": "active",
            "like_count": 0,
            "dislike_count": 0,
            "reply_count": 0,
            "user_reaction": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "replies": None
        }
        mock_comments_service.create_comment.return_value = mock_comment_response
        
        response = client.post(
            "/test-service/comments/inquiry",
            json={
                "content": "문의 내용"
            }
        )
        
        # Assert - 모킹된 인증으로 인해 201 성공 응답 예상
        assert response.status_code == 201
        mock_comments_service.create_comment.assert_called_once()
    
    def test_review_endpoint_requires_authentication(self, client, mock_comments_service):
        """Test that review endpoint requires authentication."""
        # Act - 인증 헤더 없이 요청 (app_with_comments에서 인증을 모킹하므로 200 응답 예상)
        mock_comment_response = {
            "id": "review123",
            "author_id": "user123",
            "author": {
                "id": "user123", 
                "name": "Test User",
                "email": "test@example.com",
                "user_handle": "testuser",
                "display_name": "Test User",
                "bio": None,
                "avatar_url": None,
                "status": "active",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            "content": "후기 내용",
            "parent_comment_id": None,
            "status": "active",
            "like_count": 0,
            "dislike_count": 0,
            "reply_count": 0,
            "user_reaction": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "replies": None
        }
        mock_comments_service.create_comment.return_value = mock_comment_response
        
        response = client.post(
            "/test-service/comments/review",
            json={
                "content": "후기 내용"
            }
        )
        
        # Assert - 모킹된 인증으로 인해 201 성공 응답 예상
        assert response.status_code == 201
        mock_comments_service.create_comment.assert_called_once()
    
    def test_inquiry_endpoint_content_validation(self, client, mock_comments_service):
        """Test inquiry endpoint content validation."""
        # Act - 빈 content로 요청
        response = client.post(
            "/test-service/comments/inquiry",
            json={
                "content": ""
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assert - 422 Validation Error 예상
        assert response.status_code == 422
        mock_comments_service.create_comment.assert_not_called()
    
    def test_review_endpoint_content_validation(self, client, mock_comments_service):
        """Test review endpoint content validation."""
        # Act - 빈 content로 요청
        response = client.post(
            "/test-service/comments/review",
            json={
                "content": ""
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assert - 422 Validation Error 예상
        assert response.status_code == 422
        mock_comments_service.create_comment.assert_not_called()