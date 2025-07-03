"""최적화된 post repository 테스트.

## 🎯 테스트 목표
MongoDB aggregation을 사용한 단일 쿼리 검증

## 📋 테스트 범위
- list_posts_optimized 함수 구현 검증
- $lookup을 통한 작성자 정보 조인 검증
- 메타데이터 타입별 필터링 검증
- 페이지네이션 및 정렬 검증
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
from nadle_backend.models.core import Post, User
from nadle_backend.repositories.post_repository import PostRepository


class TestPostRepositoryOptimized:
    """최적화된 post repository 테스트."""
    
    @pytest.fixture
    def sample_aggregation_result(self):
        """MongoDB aggregation 결과 샘플."""
        return [
            {
                "posts": [
                    {
                        "_id": "507f1f77bcf86cd799439020",
                        "title": "정보 게시글 1",
                        "content": "유용한 정보입니다",
                        "slug": "507f1f77bcf86cd799439020-정보-게시글-1",
                        "author_id": "507f1f77bcf86cd799439011",
                        "metadata": {"type": "property-info", "category": "입주 정보"},
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "view_count": 100,
                        "like_count": 50,
                        "dislike_count": 5,
                        "comment_count": 10,
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
                ],
                "total": [{"count": 2}]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_list_posts_optimized_aggregation_pipeline(self, sample_aggregation_result):
        """list_posts_optimized가 올바른 aggregation 파이프라인을 생성하는지 검증."""
        # Given: PostRepository 인스턴스
        repo = PostRepository()
        
        # Mock Post.aggregate to verify pipeline structure
        with patch.object(Post, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value.to_list = AsyncMock(return_value=sample_aggregation_result)
            
            # When: list_posts_optimized 호출
            result_posts, total = await repo.list_posts_optimized(
                page=1,
                page_size=10,
                metadata_type="property-info",
                sort_by="created_at"
            )
            
            # Then: aggregate가 호출되었는지 확인
            mock_aggregate.assert_called_once()
            
            # 파이프라인 구조 검증
            called_pipeline = mock_aggregate.call_args[0][0]
            
            # $match 단계 확인
            match_stage = called_pipeline[0]
            assert "$match" in match_stage
            assert match_stage["$match"]["status"]["$ne"] == "deleted"
            assert match_stage["$match"]["metadata.type"] == "property-info"
            
            # $lookup 단계 확인 (작성자 정보 조인)
            lookup_stage = called_pipeline[1]
            assert "$lookup" in lookup_stage
            lookup_config = lookup_stage["$lookup"]
            assert lookup_config["from"] == "users"
            assert lookup_config["localField"] == "author_id"
            assert lookup_config["foreignField"] == "_id"
            assert lookup_config["as"] == "author"
            
            # $unwind 단계 확인
            unwind_stage = called_pipeline[2]
            assert "$unwind" in unwind_stage
            assert unwind_stage["$unwind"]["path"] == "$author"
            assert unwind_stage["$unwind"]["preserveNullAndEmptyArrays"] == True
            
            # $sort 단계 확인
            sort_stage = called_pipeline[3]
            assert "$sort" in sort_stage
            assert sort_stage["$sort"]["created_at"] == -1
            
            # $facet 단계 확인 (페이지네이션)
            facet_stage = called_pipeline[4]
            assert "$facet" in facet_stage
            assert "posts" in facet_stage["$facet"]
            assert "total" in facet_stage["$facet"]
    
    @pytest.mark.asyncio
    async def test_list_posts_optimized_returns_correct_data(self, sample_aggregation_result):
        """list_posts_optimized가 올바른 데이터를 반환하는지 검증."""
        # Given: PostRepository와 mock 데이터
        repo = PostRepository()
        
        with patch.object(Post, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value.to_list = AsyncMock(return_value=sample_aggregation_result)
            
            # When: list_posts_optimized 호출
            result_posts, total = await repo.list_posts_optimized(
                page=1,
                page_size=10,
                metadata_type="property-info",
                sort_by="created_at"
            )
            
            # Then: 올바른 데이터 반환 확인
            assert len(result_posts) == 2
            assert total == 2
            
            # 첫 번째 게시글 확인
            first_post = result_posts[0]
            assert first_post["title"] == "정보 게시글 1"
            assert first_post["view_count"] == 100
            assert first_post["like_count"] == 50
            assert "author" in first_post
            assert first_post["author"]["user_handle"] == "testuser"
            
            # 두 번째 게시글 확인
            second_post = result_posts[1]
            assert second_post["title"] == "정보 게시글 2"
            assert second_post["view_count"] == 200
            assert second_post["like_count"] == 80
            assert "author" in second_post
            assert second_post["author"]["user_handle"] == "author2"
    
    @pytest.mark.asyncio
    async def test_list_posts_optimized_pagination(self, sample_aggregation_result):
        """페이지네이션이 올바르게 적용되는지 검증."""
        # Given: PostRepository
        repo = PostRepository()
        
        with patch.object(Post, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value.to_list = AsyncMock(return_value=sample_aggregation_result)
            
            # When: 2페이지, 5개씩 요청
            result_posts, total = await repo.list_posts_optimized(
                page=2,
                page_size=5,
                metadata_type="property-info",
                sort_by="created_at"
            )
            
            # Then: 올바른 파이프라인이 생성되었는지 확인
            called_pipeline = mock_aggregate.call_args[0][0]
            facet_stage = called_pipeline[4]
            
            # 페이지네이션 확인: (2-1) * 5 = 5 skip
            posts_pipeline = facet_stage["$facet"]["posts"]
            skip_stage = posts_pipeline[0]
            limit_stage = posts_pipeline[1]
            
            assert skip_stage["$skip"] == 5  # (page-1) * page_size
            assert limit_stage["$limit"] == 5  # page_size
    
    @pytest.mark.asyncio
    async def test_list_posts_optimized_without_metadata_type(self, sample_aggregation_result):
        """metadata_type 없이 호출시 필터 없음 확인."""
        # Given: PostRepository
        repo = PostRepository()
        
        with patch.object(Post, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value.to_list = AsyncMock(return_value=sample_aggregation_result)
            
            # When: metadata_type 없이 호출
            result_posts, total = await repo.list_posts_optimized(
                page=1,
                page_size=10,
                metadata_type=None,
                sort_by="created_at"
            )
            
            # Then: metadata.type 필터가 없어야 함
            called_pipeline = mock_aggregate.call_args[0][0]
            match_stage = called_pipeline[0]
            
            # status 필터는 있지만 metadata.type은 없음
            assert "status" in match_stage["$match"]
            assert "metadata.type" not in match_stage["$match"]
    
    @pytest.mark.asyncio
    async def test_list_posts_optimized_empty_result(self):
        """빈 결과 처리 확인."""
        # Given: PostRepository와 빈 결과
        repo = PostRepository()
        empty_result = []
        
        with patch.object(Post, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value.to_list = AsyncMock(return_value=empty_result)
            
            # When: 빈 결과로 호출
            result_posts, total = await repo.list_posts_optimized(
                page=1,
                page_size=10,
                metadata_type="property-info",
                sort_by="created_at"
            )
            
            # Then: 빈 배열과 0 반환
            assert result_posts == []
            assert total == 0
    
    @pytest.mark.asyncio
    async def test_list_posts_optimized_different_sort_fields(self, sample_aggregation_result):
        """다양한 정렬 필드 테스트."""
        # Given: PostRepository
        repo = PostRepository()
        
        with patch.object(Post, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value.to_list = AsyncMock(return_value=sample_aggregation_result)
            
            # When: view_count로 정렬
            await repo.list_posts_optimized(
                page=1,
                page_size=10,
                metadata_type="property-info",
                sort_by="view_count"
            )
            
            # Then: view_count 내림차순 정렬 확인
            called_pipeline = mock_aggregate.call_args[0][0]
            sort_stage = called_pipeline[3]
            assert sort_stage["$sort"]["view_count"] == -1
    
    def test_list_posts_optimized_method_exists(self):
        """list_posts_optimized 메서드가 존재하는지 확인."""
        # Given: PostRepository
        repo = PostRepository()
        
        # Then: list_posts_optimized 메서드 존재 확인
        assert hasattr(repo, 'list_posts_optimized'), \
            "PostRepository should have list_posts_optimized method"
        
        # 메서드가 async인지 확인
        import inspect
        assert inspect.iscoroutinefunction(repo.list_posts_optimized), \
            "list_posts_optimized should be an async method"