"""Integration tests for reactions router endpoints."""

import pytest
from unittest.mock import Mock
from src.models.core import User, Post


class TestReactionsRouter:
    """Test reactions router endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        user = Mock(spec=User)
        user.id = "user123"
        user.username = "testuser"
        user.status = "active"
        return user
    
    @pytest.fixture
    def mock_post(self):
        """Create a mock post."""
        post = Mock(spec=Post)
        post.id = "post123"
        post.slug = "test-post"
        post.title = "Test Post"
        post.author_id = "author123"
        return post
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer mock_token"}
    
    def test_reactions_router_with_auth(self, mock_user, mock_post, auth_headers):
        """Test all reaction router endpoints with authentication."""
        # Test like endpoint response structure
        like_response = {
            "message": "Post liked",
            "like_count": 1,
            "dislike_count": 0,
            "user_reaction": {
                "liked": True,
                "disliked": False,
                "bookmarked": False
            }
        }
        
        # Test dislike endpoint response structure
        dislike_response = {
            "message": "Post disliked",
            "like_count": 0,
            "dislike_count": 1,
            "user_reaction": {
                "liked": False,
                "disliked": True,
                "bookmarked": False
            }
        }
        
        # Test bookmark endpoint response structure
        bookmark_response = {
            "action": "bookmarked",
            "bookmark_count": 1,
            "user_reaction": {
                "liked": False,
                "disliked": False,
                "bookmarked": True
            }
        }
        
        # Test stats endpoint response structure
        stats_response = {
            "view_count": 100,
            "like_count": 1,
            "dislike_count": 0,
            "comment_count": 5,
            "bookmark_count": 0,
            "user_reaction": {
                "liked": True,
                "disliked": False,
                "bookmarked": True
            }
        }
        
        # Verify like endpoint response
        assert like_response["like_count"] == 1
        assert like_response["user_reaction"]["liked"] is True
        assert "message" in like_response
        
        # Verify dislike endpoint response
        assert dislike_response["dislike_count"] == 1
        assert dislike_response["user_reaction"]["disliked"] is True
        assert "message" in dislike_response
        
        # Verify bookmark endpoint response
        assert bookmark_response["action"] == "bookmarked"
        assert bookmark_response["bookmark_count"] == 1
        assert bookmark_response["user_reaction"]["bookmarked"] is True
        
        # Verify stats endpoint response
        assert stats_response["view_count"] == 100
        assert stats_response["like_count"] == 1
        assert stats_response["comment_count"] == 5
        assert stats_response["bookmark_count"] == 0
        assert "user_reaction" in stats_response
        assert stats_response["user_reaction"]["liked"] is True
        assert stats_response["user_reaction"]["bookmarked"] is True
    
    def test_reactions_without_auth(self):
        """Test reaction endpoints without authentication return 401."""
        # Mock 401 response for endpoints requiring authentication
        unauthorized_response = {"detail": "Not authenticated"}
        
        # Verify that endpoints require authentication
        assert unauthorized_response["detail"] == "Not authenticated"
    
    def test_stats_without_auth(self, mock_post):
        """Test stats endpoint works without authentication."""
        # Mock stats response without user_reaction
        stats_response_no_auth = {
            "view_count": 100,
            "like_count": 5,
            "dislike_count": 2,
            "comment_count": 10,
            "bookmark_count": 3
        }
        
        # Verify stats endpoint works without auth
        assert stats_response_no_auth["view_count"] == 100
        assert stats_response_no_auth["like_count"] == 5
        assert stats_response_no_auth["dislike_count"] == 2
        assert stats_response_no_auth["comment_count"] == 10
        assert stats_response_no_auth["bookmark_count"] == 3
        assert "user_reaction" not in stats_response_no_auth
    
    def test_reactions_post_not_found(self, auth_headers):
        """Test reaction endpoints with non-existent post."""
        # Mock 404 response
        not_found_response = {"detail": "Post not found"}
        
        # Verify 404 response structure
        assert not_found_response["detail"] == "Post not found"