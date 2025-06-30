"""게시글 상세 페이지 통합 테스트."""

import pytest
from httpx import AsyncClient
from fastapi import status
from nadle_backend.models.core import User, Post, PostStats


class TestPostDetailIntegration:
    """게시글 상세 조회 통합 테스트 클래스."""
    
    @pytest.mark.asyncio
    async def test_get_post_by_slug_success(self, async_client: AsyncClient, test_user: User, test_post: Post):
        """유효한 slug로 게시글 조회 성공 테스트."""
        # Given: 테스트 게시글이 존재함
        assert test_post.slug is not None
        
        # When: slug로 게시글 조회
        response = await async_client.get(f"/api/posts/{test_post.slug}")
        
        # Then: 성공적으로 조회됨
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(test_post.id)
        assert data["title"] == test_post.title
        assert data["content"] == test_post.content
        assert data["slug"] == test_post.slug
        assert data["author_id"] == str(test_post.author_id)
        
        # 통계 정보 확인
        assert "stats" in data
        stats = data["stats"]
        assert "view_count" in stats
        assert "like_count" in stats
        assert "dislike_count" in stats
        assert "comment_count" in stats
        assert "bookmark_count" in stats
        
        # 조회수 증가 확인 (1 이상)
        assert stats["view_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_post_by_slug_not_found(self, async_client: AsyncClient):
        """존재하지 않는 slug로 게시글 조회 실패 테스트."""
        # Given: 존재하지 않는 slug
        non_existent_slug = "non-existent-slug-12345"
        
        # When: 존재하지 않는 slug로 조회
        response = await async_client.get(f"/api/posts/{non_existent_slug}")
        
        # Then: 404 오류 반환
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_post_with_authentication(self, async_client: AsyncClient, test_user: User, test_post: Post, auth_headers):
        """인증된 사용자의 게시글 조회 테스트."""
        # Given: 인증된 사용자와 테스트 게시글
        assert test_post.slug is not None
        
        # When: 인증된 상태에서 게시글 조회
        response = await async_client.get(
            f"/api/posts/{test_post.slug}", 
            headers=auth_headers
        )
        
        # Then: 성공적으로 조회됨
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(test_post.id)
        
        # 사용자 반응 정보가 포함될 수 있음 (구현에 따라)
        # 현재는 기본 응답 구조 확인

    @pytest.mark.asyncio
    async def test_get_post_without_authentication(self, async_client: AsyncClient, test_post: Post):
        """비인증 사용자의 게시글 조회 테스트."""
        # Given: 비인증 상태와 테스트 게시글
        assert test_post.slug is not None
        
        # When: 비인증 상태에서 게시글 조회
        response = await async_client.get(f"/api/posts/{test_post.slug}")
        
        # Then: 성공적으로 조회됨 (공개 게시글이므로)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(test_post.id)
        assert data["title"] == test_post.title

    @pytest.mark.asyncio
    async def test_post_view_count_increments(self, async_client: AsyncClient, test_post: Post):
        """게시글 조회시 조회수 증가 테스트."""
        # Given: 테스트 게시글
        assert test_post.slug is not None
        
        # When: 게시글을 여러 번 조회
        response1 = await async_client.get(f"/api/posts/{test_post.slug}")
        assert response1.status_code == status.HTTP_200_OK
        initial_views = response1.json()["stats"]["view_count"]
        
        response2 = await async_client.get(f"/api/posts/{test_post.slug}")
        assert response2.status_code == status.HTTP_200_OK
        second_views = response2.json()["stats"]["view_count"]
        
        # Then: 조회수가 증가함
        assert second_views > initial_views

    @pytest.mark.asyncio
    async def test_post_response_structure(self, async_client: AsyncClient, test_post: Post):
        """게시글 응답 구조 검증 테스트."""
        # Given: 테스트 게시글
        assert test_post.slug is not None
        
        # When: 게시글 조회
        response = await async_client.get(f"/api/posts/{test_post.slug}")
        
        # Then: 응답 구조가 올바름
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # 필수 필드 확인
        required_fields = [
            "id", "_id", "title", "content", "slug", "service", 
            "metadata", "author_id", "status", "created_at", 
            "updated_at", "published_at", "stats"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # 메타데이터 구조 확인
        metadata = data["metadata"]
        assert "type" in metadata
        assert "category" in metadata
        assert "tags" in metadata
        
        # 통계 구조 확인
        stats = data["stats"]
        stat_fields = ["view_count", "like_count", "dislike_count", "comment_count", "bookmark_count"]
        for field in stat_fields:
            assert field in stats, f"Missing stats field: {field}"
            assert isinstance(stats[field], int), f"Stats field {field} should be integer"

    @pytest.mark.asyncio
    async def test_multiple_posts_different_slugs(self, async_client: AsyncClient, test_user: User):
        """여러 게시글이 서로 다른 slug를 갖는지 테스트."""
        # Given: 여러 테스트 게시글 생성
        posts_data = [
            {
                "title": "첫 번째 테스트 게시글",
                "content": "첫 번째 내용",
                "service": "residential_community",
                "metadata": {
                    "type": "자유게시판",
                    "category": "생활정보",
                    "tags": ["테스트1"]
                }
            },
            {
                "title": "두 번째 테스트 게시글",
                "content": "두 번째 내용",
                "service": "residential_community",
                "metadata": {
                    "type": "질문답변",
                    "category": "입주정보",
                    "tags": ["테스트2"]
                }
            }
        ]
        
        created_posts = []
        
        # When: 여러 게시글 생성
        from nadle_backend.services.posts_service import PostsService
        posts_service = PostsService()
        
        for post_data in posts_data:
            from nadle_backend.models.core import PostCreate
            post_create = PostCreate(**post_data)
            post = await posts_service.create_post(post_create, test_user)
            created_posts.append(post)
        
        # Then: 각 게시글이 고유한 slug를 가짐
        slugs = [post.slug for post in created_posts]
        assert len(slugs) == len(set(slugs)), "모든 게시글은 고유한 slug를 가져야 함"
        
        # 각 slug로 조회 가능한지 확인
        for post in created_posts:
            response = await async_client.get(f"/api/posts/{post.slug}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(post.id)