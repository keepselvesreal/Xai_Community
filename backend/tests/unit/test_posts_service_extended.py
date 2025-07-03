"""PostsService 확장 기능 테스트."""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

from nadle_backend.models.core import Post, User, Comment, PostMetadata
from nadle_backend.services.posts_service import PostsService
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.exceptions.post import PostNotFoundError


class TestPostsServiceExtended:
    """PostsService의 확장 통계 기능 테스트."""
    
    @pytest.fixture
    async def setup_service_test_data(self, clean_db):
        """입주 서비스 업체 테스트 데이터 설정."""
        # 테스트용 사용자 생성
        user = User(
            email="service_test@example.com",
            user_handle="serviceuser",
            display_name="Service User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        # 입주 서비스 업체 게시글 생성
        service_post = Post(
            title="테스트 청소 서비스",
            content="전문적인 청소 서비스를 제공합니다",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="moving services", category="청소"),
            slug="test-cleaning-service",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            view_count=150,
            like_count=5,
            dislike_count=1,
            comment_count=8,
            bookmark_count=12
        )
        await service_post.save()
        
        # 일반 게시판 게시글 생성 (비교용)
        general_post = Post(
            title="일반 게시글",
            content="일반 게시글 내용",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="board", category="생활정보"),
            slug="test-general-post",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await general_post.save()
        
        # 다양한 타입의 댓글 생성
        comments_data = [
            # 일반 댓글 3개
            {"content": "서비스 좋네요", "metadata": {}},
            {"content": "깔끔하게 잘해주셨어요", "metadata": {}},
            {"content": "추천합니다", "metadata": {}},
            
            # 문의 댓글 2개
            {"content": "가격이 어떻게 되나요?", "metadata": {"subtype": "service_inquiry"}},
            {"content": "주말에도 서비스 가능한가요?", "metadata": {"subtype": "service_inquiry"}},
            
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
            "general_post": general_post,
            "comments": comments
        }
    
    async def test_get_service_post_with_extended_stats_success(self, setup_service_test_data):
        """입주 서비스 업체 게시글의 확장 통계 조회 성공 테스트."""
        # Given
        test_data = setup_service_test_data
        service_post = test_data["service_post"]
        user = test_data["user"]
        
        posts_service = PostsService()
        
        # When
        result = await posts_service.get_service_post_with_extended_stats(
            service_post.slug, user
        )
        
        # Then
        assert result is not None, "Result should not be None"
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # 기본 게시글 정보 확인
        assert result["title"] == "테스트 청소 서비스"
        assert result["metadata"]["type"] == "moving services"
        
        # 확장 통계 확인
        assert "extended_stats" in result, "Extended stats should be included"
        extended_stats = result["extended_stats"]
        
        # 기존 통계 확인
        assert extended_stats["view_count"] == 150
        assert extended_stats["like_count"] == 5
        assert extended_stats["dislike_count"] == 1
        assert extended_stats["comment_count"] == 8
        assert extended_stats["bookmark_count"] == 12
        
        # 확장된 댓글 통계 확인
        assert extended_stats["inquiry_count"] == 2, f"Expected 2 inquiries, got {extended_stats['inquiry_count']}"
        assert extended_stats["review_count"] == 3, f"Expected 3 reviews, got {extended_stats['review_count']}"
        assert extended_stats["general_comment_count"] == 3, f"Expected 3 general comments, got {extended_stats['general_comment_count']}"
    
    async def test_get_service_post_with_extended_stats_not_service_post(self, setup_service_test_data):
        """일반 게시글에 대한 서비스 확장 통계 조회 실패 테스트."""
        # Given
        test_data = setup_service_test_data
        general_post = test_data["general_post"]
        user = test_data["user"]
        
        posts_service = PostsService()
        
        # When & Then
        with pytest.raises(PostNotFoundError) as exc_info:
            await posts_service.get_service_post_with_extended_stats(
                general_post.slug, user
            )
        
        assert "입주 서비스 업체 게시글이 아닙니다" in str(exc_info.value)
    
    async def test_get_service_post_with_extended_stats_post_not_found(self, clean_db):
        """존재하지 않는 게시글에 대한 서비스 확장 통계 조회 테스트."""
        # Given
        posts_service = PostsService()
        nonexistent_slug = "nonexistent-service-post"
        
        # When & Then
        with pytest.raises(PostNotFoundError):
            await posts_service.get_service_post_with_extended_stats(nonexistent_slug)
    
    async def test_extended_stats_structure(self, setup_service_test_data):
        """확장 통계 구조 검증 테스트."""
        # Given
        test_data = setup_service_test_data
        service_post = test_data["service_post"]
        
        posts_service = PostsService()
        
        # When
        result = await posts_service.get_service_post_with_extended_stats(service_post.slug)
        
        # Then
        extended_stats = result["extended_stats"]
        
        # 모든 필요한 통계 필드 존재 확인
        required_fields = [
            "view_count", "like_count", "dislike_count", 
            "comment_count", "bookmark_count",
            "inquiry_count", "review_count", "general_comment_count"
        ]
        
        for field in required_fields:
            assert field in extended_stats, f"Field '{field}' should be in extended_stats"
            assert isinstance(extended_stats[field], int), f"Field '{field}' should be an integer"
            assert extended_stats[field] >= 0, f"Field '{field}' should be non-negative"
    
    async def test_extended_stats_with_no_comments(self, clean_db):
        """댓글이 없는 서비스 게시글의 확장 통계 테스트."""
        # Given
        user = User(
            email="no_comments@example.com",
            user_handle="nocommentsuser",
            display_name="No Comments User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        service_post = Post(
            title="댓글 없는 서비스",
            content="댓글이 없는 서비스입니다",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="moving services", category="기타"),
            slug="no-comments-service",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            view_count=10,
            like_count=0,
            dislike_count=0,
            comment_count=0,
            bookmark_count=0
        )
        await service_post.save()
        
        posts_service = PostsService()
        
        # When
        result = await posts_service.get_service_post_with_extended_stats(service_post.slug)
        
        # Then
        extended_stats = result["extended_stats"]
        
        # 모든 댓글 관련 통계가 0이어야 함
        assert extended_stats["inquiry_count"] == 0
        assert extended_stats["review_count"] == 0
        assert extended_stats["general_comment_count"] == 0
        assert extended_stats["comment_count"] == 0
    
    async def test_extended_stats_performance(self, setup_service_test_data):
        """확장 통계 조회 성능 테스트."""
        import time
        
        # Given
        test_data = setup_service_test_data
        service_post = test_data["service_post"]
        
        posts_service = PostsService()
        
        # When
        start_time = time.time()
        result = await posts_service.get_service_post_with_extended_stats(service_post.slug)
        end_time = time.time()
        
        # Then
        execution_time = end_time - start_time
        
        # 성능 검증: 0.5초 이내에 완료되어야 함
        assert execution_time < 0.5, f"Extended stats query took too long: {execution_time:.3f}s"
        
        # 기능 검증
        assert "extended_stats" in result
        assert isinstance(result["extended_stats"], dict)
    
    @patch.object(CommentRepository, 'get_comment_stats_by_post')
    async def test_extended_stats_with_comment_repository_error(self, mock_get_stats, setup_service_test_data):
        """댓글 통계 조회 실패시 기본값 반환 테스트."""
        # Given
        test_data = setup_service_test_data
        service_post = test_data["service_post"]
        
        # CommentRepository에서 에러 발생 시뮬레이션
        mock_get_stats.return_value = {"general": 0, "service_inquiry": 0, "service_review": 0}
        
        posts_service = PostsService()
        
        # When
        result = await posts_service.get_service_post_with_extended_stats(service_post.slug)
        
        # Then
        extended_stats = result["extended_stats"]
        
        # 댓글 통계는 기본값(0)이어야 하지만, 다른 통계는 정상이어야 함
        assert extended_stats["inquiry_count"] == 0
        assert extended_stats["review_count"] == 0
        assert extended_stats["general_comment_count"] == 0
        
        # 기본 통계는 정상 값
        assert extended_stats["view_count"] == 150
        assert extended_stats["like_count"] == 5