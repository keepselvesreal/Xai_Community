"""CommentRepository 통계 기능 테스트."""

import pytest
from datetime import datetime
from typing import Dict, Any
from beanie import init_beanie, PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from nadle_backend.models.core import Comment, Post, User
from nadle_backend.repositories.comment_repository import CommentRepository


class TestCommentRepositoryStats:
    """CommentRepository의 통계 집계 기능 테스트."""
    
    @pytest.fixture
    async def setup_test_data(self, clean_db):
        """테스트용 데이터 설정."""
        # 테스트용 사용자 생성
        user = User(
            email="test@example.com",
            user_handle="testuser",
            display_name="Test User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        # 테스트용 게시글 생성 (입주 서비스 업체)
        from nadle_backend.models.core import PostMetadata
        
        post = Post(
            title="테스트 서비스 업체",
            content="테스트 서비스 내용",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="moving services", category="청소"),
            slug="test-service-slug",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await post.save()
        
        # 다양한 타입의 댓글 생성
        comments_data = [
            # 일반 댓글 5개 (metadata.subtype 없음)
            {"content": "일반 댓글 1", "metadata": {}},
            {"content": "일반 댓글 2", "metadata": {}},
            {"content": "일반 댓글 3", "metadata": {}},
            {"content": "일반 댓글 4", "metadata": {}},
            {"content": "일반 댓글 5", "metadata": {}},
            
            # 문의 댓글 3개
            {"content": "문의 댓글 1", "metadata": {"subtype": "service_inquiry"}},
            {"content": "문의 댓글 2", "metadata": {"subtype": "service_inquiry"}},
            {"content": "문의 댓글 3", "metadata": {"subtype": "service_inquiry"}},
            
            # 후기 댓글 2개
            {"content": "후기 댓글 1", "metadata": {"subtype": "service_review"}},
            {"content": "후기 댓글 2", "metadata": {"subtype": "service_review"}},
        ]
        
        comments = []
        for comment_data in comments_data:
            comment = Comment(
                content=comment_data["content"],
                parent_id=str(post.id),
                author_id=str(user.id),
                metadata=comment_data["metadata"],
                status="active",
                created_at=datetime.utcnow()
            )
            await comment.save()
            comments.append(comment)
        
        # 삭제된 댓글도 하나 추가 (집계에서 제외되어야 함)
        deleted_comment = Comment(
            content="삭제된 댓글",
            parent_id=str(post.id),
            author_id=str(user.id),
            metadata={"subtype": "service_inquiry"},
            status="deleted",
            created_at=datetime.utcnow()
        )
        await deleted_comment.save()
        
        return {
            "user": user,
            "post": post,
            "comments": comments,
            "deleted_comment": deleted_comment
        }
    
    async def test_count_comments_by_subtype_service_inquiry(self, setup_test_data):
        """service_inquiry 타입 댓글 수 집계 테스트."""
        # Given
        test_data = setup_test_data
        post_id = str(test_data["post"].id)
        comment_repo = CommentRepository()
        
        # When
        count = await comment_repo.count_comments_by_subtype(post_id, "service_inquiry")
        
        # Then
        assert count == 3, f"Expected 3 service_inquiry comments, got {count}"
    
    async def test_count_comments_by_subtype_service_review(self, setup_test_data):
        """service_review 타입 댓글 수 집계 테스트."""
        # Given
        test_data = setup_test_data
        post_id = str(test_data["post"].id)
        comment_repo = CommentRepository()
        
        # When
        count = await comment_repo.count_comments_by_subtype(post_id, "service_review")
        
        # Then
        assert count == 2, f"Expected 2 service_review comments, got {count}"
    
    async def test_count_comments_by_subtype_nonexistent(self, setup_test_data):
        """존재하지 않는 subtype에 대한 집계 테스트."""
        # Given
        test_data = setup_test_data
        post_id = str(test_data["post"].id)
        comment_repo = CommentRepository()
        
        # When
        count = await comment_repo.count_comments_by_subtype(post_id, "nonexistent_type")
        
        # Then
        assert count == 0, f"Expected 0 nonexistent_type comments, got {count}"
    
    async def test_get_comment_stats_by_post_comprehensive(self, setup_test_data):
        """게시글별 전체 댓글 통계 집계 테스트."""
        # Given
        test_data = setup_test_data
        post_id = str(test_data["post"].id)
        comment_repo = CommentRepository()
        
        # When
        stats = await comment_repo.get_comment_stats_by_post(post_id)
        
        # Then
        expected_stats = {
            "general": 5,          # 일반 댓글 (subtype 없음)
            "service_inquiry": 3,  # 문의 댓글
            "service_review": 2    # 후기 댓글
        }
        
        assert stats == expected_stats, f"Expected {expected_stats}, got {stats}"
    
    async def test_get_comment_stats_empty_post(self, clean_db):
        """댓글이 없는 게시글의 통계 테스트."""
        # Given
        user = User(
            email="empty@example.com",
            user_handle="emptyuser",
            display_name="Empty User",
            password_hash="test_hash",
            is_active=True
        )
        await user.save()
        
        from nadle_backend.models.core import PostMetadata
        
        post = Post(
            title="댓글 없는 게시글",
            content="내용",
            service="residential_community",
            author_id=str(user.id),
            metadata=PostMetadata(type="moving services"),
            slug="empty-post-slug",
            status="published",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await post.save()
        
        comment_repo = CommentRepository()
        
        # When
        stats = await comment_repo.get_comment_stats_by_post(str(post.id))
        
        # Then
        expected_stats = {
            "general": 0,
            "service_inquiry": 0,
            "service_review": 0
        }
        
        assert stats == expected_stats, f"Expected {expected_stats}, got {stats}"
    
    async def test_get_comment_stats_invalid_post_id(self):
        """잘못된 게시글 ID에 대한 통계 테스트."""
        # Given
        invalid_post_id = str(PydanticObjectId())
        comment_repo = CommentRepository()
        
        # When
        stats = await comment_repo.get_comment_stats_by_post(invalid_post_id)
        
        # Then
        expected_stats = {
            "general": 0,
            "service_inquiry": 0,
            "service_review": 0
        }
        
        assert stats == expected_stats, f"Expected {expected_stats}, got {stats}"
    
    async def test_count_comments_excludes_deleted_status(self, setup_test_data):
        """삭제된 댓글이 집계에서 제외되는지 테스트."""
        # Given
        test_data = setup_test_data
        post_id = str(test_data["post"].id)
        comment_repo = CommentRepository()
        
        # When
        inquiry_count = await comment_repo.count_comments_by_subtype(post_id, "service_inquiry")
        
        # Then
        # 삭제된 댓글 1개가 제외되어 3개여야 함 (생성된 4개 중 1개는 deleted 상태)
        assert inquiry_count == 3, f"Expected 3 active service_inquiry comments (excluding deleted), got {inquiry_count}"
    
    async def test_get_comment_stats_performance(self, setup_test_data):
        """통계 집계 성능 테스트 (기본적인 응답 시간 확인)."""
        import time
        
        # Given
        test_data = setup_test_data
        post_id = str(test_data["post"].id)
        comment_repo = CommentRepository()
        
        # When
        start_time = time.time()
        stats = await comment_repo.get_comment_stats_by_post(post_id)
        end_time = time.time()
        
        # Then
        execution_time = end_time - start_time
        
        # 성능 검증: 0.1초 이내에 완료되어야 함
        assert execution_time < 0.1, f"Comment stats query took too long: {execution_time:.3f}s"
        
        # 기능 검증
        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert all(key in stats for key in ["general", "service_inquiry", "service_review"]), \
            "Stats should contain all required keys"