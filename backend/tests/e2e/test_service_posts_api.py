"""입주 서비스 업체 API 통합 테스트."""

import pytest
from datetime import datetime
from httpx import AsyncClient

from nadle_backend.models.core import Post, User, Comment, PostMetadata


class TestServicePostsAPI:
    """입주 서비스 업체 API 엔드포인트 통합 테스트."""
    
    @pytest.fixture
    async def setup_api_test_data(self, clean_db):
        """API 테스트용 데이터 설정."""
        # 테스트용 사용자 생성
        user = User(
            email="api_test@example.com",
            user_handle="apiuser",
            display_name="API Test User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        # 입주 서비스 업체 게시글 생성
        service_post = Post(
            title="API 테스트 청소 서비스",
            content="API 테스트를 위한 청소 서비스 설명",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="moving services", category="청소"),
            slug="api-test-cleaning-service",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            view_count=100,
            like_count=10,
            dislike_count=2,
            comment_count=8,
            bookmark_count=15
        )
        await service_post.save()
        
        # 댓글 생성 (통계 확인용)
        comments_data = [
            # 일반 댓글 2개
            {"content": "좋은 서비스네요", "metadata": {}},
            {"content": "추천합니다", "metadata": {}},
            
            # 문의 댓글 3개
            {"content": "가격이 어떻게 되나요?", "metadata": {"subtype": "service_inquiry"}},
            {"content": "예약은 어떻게 하나요?", "metadata": {"subtype": "service_inquiry"}},
            {"content": "주말 서비스 가능한가요?", "metadata": {"subtype": "service_inquiry"}},
            
            # 후기 댓글 3개
            {"content": "정말 만족스러웠어요", "metadata": {"subtype": "service_review"}},
            {"content": "다음에도 이용하겠습니다", "metadata": {"subtype": "service_review"}},
            {"content": "꼼꼼하게 잘해주셨습니다", "metadata": {"subtype": "service_review"}},
        ]
        
        comments = []
        for comment_data in comments_data:
            comment = Comment(
                content=comment_data["content"],
                parent_id=str(service_post.id),
                author_id=str(user.id),
                metadata=comment_data["metadata"],
                status="active",
                created_at=datetime.utcnow()
            )
            await comment.save()
            comments.append(comment)
        
        return {
            "user": user,
            "service_post": service_post,
            "comments": comments
        }
    
    async def test_get_service_post_detail_endpoint(self, async_client: AsyncClient, setup_api_test_data):
        """서비스 게시글 상세 API 엔드포인트 테스트."""
        # Given
        test_data = setup_api_test_data
        service_post = test_data["service_post"]
        
        # When
        response = await async_client.get(f"/api/posts/services/{service_post.slug}")
        
        # Then
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        post_data = data["data"]
        
        # 기본 게시글 정보 확인
        assert post_data["title"] == "API 테스트 청소 서비스"
        assert post_data["metadata"]["type"] == "moving services"
        assert post_data["slug"] == service_post.slug
        
        # 확장 통계 확인
        assert "extended_stats" in post_data
        extended_stats = post_data["extended_stats"]
        
        # 기존 통계 확인
        assert extended_stats["view_count"] == 100
        assert extended_stats["like_count"] == 10
        assert extended_stats["dislike_count"] == 2
        assert extended_stats["comment_count"] == 8
        assert extended_stats["bookmark_count"] == 15
        
        # 확장된 댓글 통계 확인
        assert extended_stats["inquiry_count"] == 3
        assert extended_stats["review_count"] == 3
        assert extended_stats["general_comment_count"] == 2
    
    async def test_get_service_post_detail_not_found(self, async_client: AsyncClient, clean_db):
        """존재하지 않는 서비스 게시글 조회 테스트."""
        # Given
        nonexistent_slug = "nonexistent-service-post"
        
        # When
        response = await async_client.get(f"/api/posts/services/{nonexistent_slug}")
        
        # Then
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    async def test_get_service_post_detail_wrong_type(self, async_client: AsyncClient, clean_db):
        """일반 게시글을 서비스 API로 조회했을 때 오류 테스트."""
        # Given
        user = User(
            email="wrong_type@example.com",
            user_handle="wrongtypeuser",
            display_name="Wrong Type User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        # 일반 게시판 게시글 생성
        general_post = Post(
            title="일반 게시글",
            content="일반 게시글 내용",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="board", category="생활정보"),
            slug="general-post-wrong-type",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await general_post.save()
        
        # When
        response = await async_client.get(f"/api/posts/services/{general_post.slug}")
        
        # Then
        assert response.status_code == 404
        
        data = response.json()
        assert "입주 서비스 업체 게시글이 아닙니다" in data["detail"]
    
    async def test_extended_stats_data_accuracy(self, async_client: AsyncClient, setup_api_test_data):
        """API를 통한 확장 통계 데이터 정확성 검증."""
        # Given
        test_data = setup_api_test_data
        service_post = test_data["service_post"]
        
        # When
        response = await async_client.get(f"/api/posts/services/{service_post.slug}")
        
        # Then
        assert response.status_code == 200
        
        data = response.json()
        post_data = data["data"]
        extended_stats = post_data["extended_stats"]
        
        # 실제 댓글 수와 API 응답 통계 일치 확인
        expected_stats = {
            "inquiry_count": 3,      # service_inquiry 댓글 3개
            "review_count": 3,       # service_review 댓글 3개
            "general_comment_count": 2  # 일반 댓글 2개
        }
        
        for stat_name, expected_value in expected_stats.items():
            actual_value = extended_stats[stat_name]
            assert actual_value == expected_value, \
                f"Expected {stat_name}={expected_value}, got {actual_value}"
    
    async def test_service_post_api_response_structure(self, async_client: AsyncClient, setup_api_test_data):
        """서비스 게시글 API 응답 구조 검증."""
        # Given
        test_data = setup_api_test_data
        service_post = test_data["service_post"]
        
        # When
        response = await async_client.get(f"/api/posts/services/{service_post.slug}")
        
        # Then
        assert response.status_code == 200
        
        data = response.json()
        
        # 응답 최상위 구조 확인
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        
        post_data = data["data"]
        
        # 기본 게시글 필드 확인
        required_fields = [
            "title", "content", "slug", "author_id", "metadata",
            "created_at", "updated_at", "extended_stats"
        ]
        
        for field in required_fields:
            assert field in post_data, f"Field '{field}' should be in response"
        
        # 확장 통계 구조 확인
        extended_stats = post_data["extended_stats"]
        extended_stats_fields = [
            "view_count", "like_count", "dislike_count", 
            "comment_count", "bookmark_count",
            "inquiry_count", "review_count", "general_comment_count"
        ]
        
        for field in extended_stats_fields:
            assert field in extended_stats, f"Extended stats field '{field}' should be in response"
            assert isinstance(extended_stats[field], int), f"Field '{field}' should be an integer"
    
    async def test_service_post_api_performance(self, async_client: AsyncClient, setup_api_test_data):
        """서비스 게시글 API 성능 테스트."""
        import time
        
        # Given
        test_data = setup_api_test_data
        service_post = test_data["service_post"]
        
        # When
        start_time = time.time()
        response = await async_client.get(f"/api/posts/services/{service_post.slug}")
        end_time = time.time()
        
        # Then
        execution_time = end_time - start_time
        
        # 성능 검증: 1초 이내에 완료되어야 함
        assert execution_time < 1.0, f"API call took too long: {execution_time:.3f}s"
        assert response.status_code == 200
        
        # 기능 검증
        data = response.json()
        assert data["success"] is True
        assert "extended_stats" in data["data"]
    
    async def test_service_post_api_with_no_comments(self, async_client: AsyncClient, clean_db):
        """댓글이 없는 서비스 게시글 API 테스트."""
        # Given
        user = User(
            email="no_comments_api@example.com",
            user_handle="nocommentsapi",
            display_name="No Comments API User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        service_post = Post(
            title="댓글 없는 API 서비스",
            content="댓글이 없는 서비스입니다",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="moving services", category="기타"),
            slug="no-comments-api-service",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            view_count=5,
            like_count=0,
            dislike_count=0,
            comment_count=0,
            bookmark_count=0
        )
        await service_post.save()
        
        # When
        response = await async_client.get(f"/api/posts/services/{service_post.slug}")
        
        # Then
        assert response.status_code == 200
        
        data = response.json()
        extended_stats = data["data"]["extended_stats"]
        
        # 모든 댓글 관련 통계가 0이어야 함
        assert extended_stats["inquiry_count"] == 0
        assert extended_stats["review_count"] == 0
        assert extended_stats["general_comment_count"] == 0
        assert extended_stats["comment_count"] == 0