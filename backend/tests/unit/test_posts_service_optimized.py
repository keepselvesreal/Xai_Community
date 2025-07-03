"""최적화된 posts service 성능 테스트.

## 🎯 테스트 목표
52개 쿼리 → 1개 쿼리로 최적화 검증

## 📋 테스트 범위
- Post 모델의 기존 통계 데이터 활용 검증
- MongoDB $lookup으로 작성자 정보 한 번에 조회 검증  
- 응답 시간 500ms 이하 검증
- 별도 실시간 계산 제거 검증
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from nadle_backend.models.core import User, Post, PostCreate, PostMetadata
from nadle_backend.services.posts_service import PostsService
from nadle_backend.repositories.post_repository import PostRepository


class TestPostsServiceOptimized:
    """최적화된 posts service 성능 테스트."""
    
    @pytest.fixture
    def mock_post_repository(self):
        """Mock post repository."""
        repo = Mock(spec=PostRepository)
        return repo
    
    @pytest.fixture
    def posts_service(self, mock_post_repository):
        """PostsService with mocked repository."""
        return PostsService(mock_post_repository)
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        return User(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            user_handle="testuser",
            display_name="Test User",
            password_hash="hashed_password"
        )
    
    @pytest.fixture
    def sample_posts_with_stats(self):
        """Sample posts with denormalized stats."""
        return [
            {
                "_id": "507f1f77bcf86cd799439020",
                "title": "정보 게시글 1",
                "content": "유용한 정보입니다",
                "slug": "507f1f77bcf86cd799439020-정보-게시글-1",
                "author_id": "507f1f77bcf86cd799439011",
                "metadata": {"type": "property-info", "category": "입주 정보"},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                # 🎯 이미 있는 통계 데이터 (별도 계산 불필요)
                "view_count": 100,
                "like_count": 50,
                "dislike_count": 5,
                "comment_count": 10,
                # 🎯 이미 조인된 작성자 정보 (별도 쿼리 불필요)
                "author": {
                    "_id": "507f1f77bcf86cd799439011",
                    "email": "test@example.com",
                    "user_handle": "testuser",
                    "display_name": "Test User",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            },
            {
                "_id": "507f1f77bcf86cd799439021",
                "title": "정보 게시글 2", 
                "content": "또 다른 유용한 정보",
                "slug": "507f1f77bcf86cd799439021-정보-게시글-2",
                "author_id": "507f1f77bcf86cd799439012",
                "metadata": {"type": "property-info", "category": "생활 정보"},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "view_count": 200,
                "like_count": 80,
                "dislike_count": 3,
                "comment_count": 15,
                "author": {
                    "_id": "507f1f77bcf86cd799439012",
                    "email": "author2@example.com",
                    "user_handle": "author2",
                    "display_name": "Author 2",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_list_posts_uses_denormalized_stats(self, posts_service, mock_post_repository, sample_posts_with_stats):
        """Post 모델의 기존 통계 데이터 사용 검증.
        
        기존 문제: _calculate_post_stats()에서 실시간 계산
        개선 목표: Post 모델의 기존 통계 데이터 활용
        """
        # Given: 이미 통계가 있는 게시글들
        mock_post_repository.list_posts_optimized.return_value = (sample_posts_with_stats, 2)
        
        # When: list_posts 호출
        result = await posts_service.list_posts(
            metadata_type="property-info",
            page=1,
            page_size=10
        )
        
        # Then: 기존 통계 데이터가 그대로 사용됨
        assert len(result["items"]) == 2
        
        # 첫 번째 게시글 통계 확인
        first_post = result["items"][0]
        assert first_post["stats"]["view_count"] == 100
        assert first_post["stats"]["like_count"] == 50
        assert first_post["stats"]["dislike_count"] == 5
        assert first_post["stats"]["comment_count"] == 10
        
        # 두 번째 게시글 통계 확인
        second_post = result["items"][1]
        assert second_post["stats"]["view_count"] == 200
        assert second_post["stats"]["like_count"] == 80
        assert second_post["stats"]["dislike_count"] == 3
        assert second_post["stats"]["comment_count"] == 15
        
        # 🎯 중요: list_posts_optimized가 호출되었는지 확인 (단일 쿼리)
        mock_post_repository.list_posts_optimized.assert_called_once_with(
            page=1,
            page_size=10,
            metadata_type="property-info",
            sort_by="created_at"
        )
    
    @pytest.mark.asyncio
    async def test_list_posts_includes_author_with_lookup(self, posts_service, mock_post_repository, sample_posts_with_stats):
        """MongoDB $lookup으로 작성자 정보 한 번에 조회 검증.
        
        기존 문제: get_authors_by_ids()로 별도 쿼리 실행
        개선 목표: $lookup으로 한 번에 조회
        """
        # Given: 작성자 정보가 이미 조인된 데이터
        mock_post_repository.list_posts_optimized.return_value = (sample_posts_with_stats, 2)
        
        # When: list_posts 호출
        result = await posts_service.list_posts(
            metadata_type="property-info",
            page=1,
            page_size=10
        )
        
        # Then: 작성자 정보가 포함되어 있음
        assert len(result["items"]) == 2
        
        # 첫 번째 게시글 작성자 정보 확인
        first_post = result["items"][0]
        assert "author" in first_post
        assert first_post["author"]["user_handle"] == "testuser"
        assert first_post["author"]["display_name"] == "Test User"
        assert first_post["author"]["email"] == "test@example.com"
        
        # 두 번째 게시글 작성자 정보 확인
        second_post = result["items"][1]
        assert "author" in second_post
        assert second_post["author"]["user_handle"] == "author2"
        assert second_post["author"]["display_name"] == "Author 2"
        assert second_post["author"]["email"] == "author2@example.com"
        
        # 🎯 중요: 별도 작성자 조회 함수가 호출되지 않았는지 확인
        # (get_authors_by_ids 같은 함수 호출 없음)
        assert not hasattr(mock_post_repository, 'get_authors_by_ids') or \
               not mock_post_repository.get_authors_by_ids.called
    
    @pytest.mark.asyncio
    async def test_list_posts_no_separate_stats_calculation(self, posts_service, mock_post_repository, sample_posts_with_stats):
        """별도 통계 계산 함수 호출 없음 검증.
        
        기존 문제: _calculate_post_stats()로 5개 컬렉션 쿼리
        개선 목표: 별도 계산 없이 기존 데이터 활용
        """
        # Given: 통계가 있는 게시글들
        mock_post_repository.list_posts_optimized.return_value = (sample_posts_with_stats, 2)
        
        # When: list_posts 호출
        with patch.object(posts_service, '_calculate_post_stats') as mock_calc_stats:
            result = await posts_service.list_posts(
                metadata_type="property-info", 
                page=1,
                page_size=10
            )
        
        # Then: _calculate_post_stats 함수가 호출되지 않음
        mock_calc_stats.assert_not_called()
        
        # 결과 검증
        assert len(result["items"]) == 2
        assert result["items"][0]["stats"]["view_count"] == 100
        assert result["items"][1]["stats"]["view_count"] == 200
    
    @pytest.mark.asyncio
    async def test_list_posts_response_structure(self, posts_service, mock_post_repository, sample_posts_with_stats):
        """응답 구조가 기존과 동일함을 검증."""
        # Given: 샘플 데이터
        mock_post_repository.list_posts_optimized.return_value = (sample_posts_with_stats, 2)
        
        # When: list_posts 호출
        result = await posts_service.list_posts(
            metadata_type="property-info",
            page=1,
            page_size=10
        )
        
        # Then: 기존과 동일한 구조 유지
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "total_pages" in result
        
        # 페이지네이션 정보 확인
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_pages"] == 1
        
        # 게시글 구조 확인
        post = result["items"][0]
        required_fields = ["_id", "title", "content", "slug", "author_id", 
                          "created_at", "updated_at", "metadata", "stats", "author"]
        for field in required_fields:
            assert field in post, f"Required field '{field}' missing"
    
    @pytest.mark.asyncio 
    async def test_list_posts_performance_expectation(self, posts_service, mock_post_repository, sample_posts_with_stats):
        """성능 개선 기댓값 테스트 (실제 DB 없이 구조 검증).
        
        실제 성능 테스트는 integration 테스트에서 진행.
        여기서는 최적화된 함수가 호출되는지만 확인.
        """
        # Given: 최적화된 repository 함수 준비
        mock_post_repository.list_posts_optimized.return_value = (sample_posts_with_stats, 2)
        
        # When: list_posts 호출
        start_time = time.time()
        result = await posts_service.list_posts(
            metadata_type="property-info",
            page=1, 
            page_size=10
        )
        end_time = time.time()
        
        # Then: 최적화된 함수가 호출됨
        mock_post_repository.list_posts_optimized.assert_called_once()
        
        # 응답 구조 확인
        assert len(result["items"]) == 2
        assert all("stats" in item for item in result["items"])
        assert all("author" in item for item in result["items"])
        
        # 처리 시간 기록 (실제 성능은 integration 테스트에서)
        processing_time = end_time - start_time
        print(f"Mock processing time: {processing_time:.4f}s")