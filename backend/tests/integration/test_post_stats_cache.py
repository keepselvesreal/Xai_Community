import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.services.post_stats_cache_service import PostStatsCacheService, PostStatsData
from nadle_backend.database.redis import redis_manager

@pytest.fixture
async def stats_cache_service():
    """게시글 통계 캐시 서비스 픽스처"""
    service = PostStatsCacheService()
    await redis_manager.connect()
    
    # 테스트 전 데이터 정리
    if await redis_manager.is_connected():
        await service.clear_all_stats_cache()
    
    yield service
    
    # 테스트 후 정리
    if await redis_manager.is_connected():
        await service.clear_all_stats_cache()
    
    await redis_manager.disconnect()

@pytest.fixture
def mock_post_stats():
    """테스트용 게시글 통계 데이터"""
    return PostStatsData(
        post_id="test_post_123",
        view_count=100,
        like_count=25,
        dislike_count=3,
        comment_count=12,
        bookmark_count=8,
        share_count=5,
        last_updated=datetime.now()
    )

class TestPostStatsCache:
    """게시글 통계 캐싱 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_cache_post_stats(self, stats_cache_service, mock_post_stats):
        """게시글 통계 캐싱 테스트"""
        # Given
        post_stats = mock_post_stats
        
        # When
        success = await stats_cache_service.cache_post_stats(post_stats)
        
        # Then
        assert success is True
        
        # 캐시에서 조회 확인
        cached_stats = await stats_cache_service.get_post_stats(post_stats.post_id)
        assert cached_stats is not None
        assert cached_stats.post_id == post_stats.post_id
        assert cached_stats.view_count == post_stats.view_count
        assert cached_stats.like_count == post_stats.like_count
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_post_stats(self, stats_cache_service):
        """존재하지 않는 게시글 통계 조회 테스트"""
        # When
        cached_stats = await stats_cache_service.get_post_stats("nonexistent_post")
        
        # Then
        assert cached_stats is None
    
    @pytest.mark.asyncio
    async def test_increment_view_count(self, stats_cache_service, mock_post_stats):
        """조회수 증가 테스트"""
        # Given
        post_id = mock_post_stats.post_id
        await stats_cache_service.cache_post_stats(mock_post_stats)
        initial_views = mock_post_stats.view_count
        
        # When
        new_count = await stats_cache_service.increment_view_count(post_id)
        
        # Then
        assert new_count == initial_views + 1
        
        # 캐시에서 확인
        cached_stats = await stats_cache_service.get_post_stats(post_id)
        assert cached_stats.view_count == initial_views + 1
    
    @pytest.mark.asyncio
    async def test_increment_like_count(self, stats_cache_service, mock_post_stats):
        """좋아요 수 증가 테스트"""
        # Given
        post_id = mock_post_stats.post_id
        await stats_cache_service.cache_post_stats(mock_post_stats)
        initial_likes = mock_post_stats.like_count
        
        # When
        new_count = await stats_cache_service.increment_like_count(post_id)
        
        # Then
        assert new_count == initial_likes + 1
        
        # 캐시에서 확인
        cached_stats = await stats_cache_service.get_post_stats(post_id)
        assert cached_stats.like_count == initial_likes + 1
    
    @pytest.mark.asyncio
    async def test_decrement_like_count(self, stats_cache_service, mock_post_stats):
        """좋아요 수 감소 테스트"""
        # Given
        post_id = mock_post_stats.post_id
        await stats_cache_service.cache_post_stats(mock_post_stats)
        initial_likes = mock_post_stats.like_count
        
        # When
        new_count = await stats_cache_service.decrement_like_count(post_id)
        
        # Then
        assert new_count == initial_likes - 1
        
        # 캐시에서 확인
        cached_stats = await stats_cache_service.get_post_stats(post_id)
        assert cached_stats.like_count == initial_likes - 1
    
    @pytest.mark.asyncio
    async def test_increment_comment_count(self, stats_cache_service, mock_post_stats):
        """댓글 수 증가 테스트"""
        # Given
        post_id = mock_post_stats.post_id
        await stats_cache_service.cache_post_stats(mock_post_stats)
        initial_comments = mock_post_stats.comment_count
        
        # When
        new_count = await stats_cache_service.increment_comment_count(post_id)
        
        # Then
        assert new_count == initial_comments + 1
        
        # 캐시에서 확인
        cached_stats = await stats_cache_service.get_post_stats(post_id)
        assert cached_stats.comment_count == initial_comments + 1
    
    @pytest.mark.asyncio
    async def test_increment_bookmark_count(self, stats_cache_service, mock_post_stats):
        """북마크 수 증가 테스트"""
        # Given
        post_id = mock_post_stats.post_id
        await stats_cache_service.cache_post_stats(mock_post_stats)
        initial_bookmarks = mock_post_stats.bookmark_count
        
        # When
        new_count = await stats_cache_service.increment_bookmark_count(post_id)
        
        # Then
        assert new_count == initial_bookmarks + 1
        
        # 캐시에서 확인
        cached_stats = await stats_cache_service.get_post_stats(post_id)
        assert cached_stats.bookmark_count == initial_bookmarks + 1
    
    @pytest.mark.asyncio
    async def test_batch_update_stats(self, stats_cache_service):
        """여러 게시글 통계 일괄 업데이트 테스트"""
        # Given
        stats_list = [
            PostStatsData(
                post_id=f"post_{i}",
                view_count=i * 10,
                like_count=i * 2,
                dislike_count=i,
                comment_count=i * 3,
                bookmark_count=i,
                share_count=i,
                last_updated=datetime.now()
            )
            for i in range(1, 4)
        ]
        
        # When
        success_count = await stats_cache_service.batch_cache_post_stats(stats_list)
        
        # Then
        assert success_count == 3
        
        # 각 게시글 통계 확인
        for stats in stats_list:
            cached_stats = await stats_cache_service.get_post_stats(stats.post_id)
            assert cached_stats is not None
            assert cached_stats.view_count == stats.view_count
            assert cached_stats.like_count == stats.like_count
    
    @pytest.mark.asyncio
    async def test_update_stats_with_ttl(self, stats_cache_service, mock_post_stats):
        """TTL을 가진 통계 업데이트 테스트"""
        # Given
        post_stats = mock_post_stats
        short_ttl = 2  # 2초
        
        # When
        success = await stats_cache_service.cache_post_stats(post_stats, ttl=short_ttl)
        
        # Then
        assert success is True
        
        # 즉시 조회 - 존재해야 함
        cached_stats = await stats_cache_service.get_post_stats(post_stats.post_id)
        assert cached_stats is not None
        
        # TTL 대기 후 조회 - 만료되어야 함
        await asyncio.sleep(2.1)
        expired_stats = await stats_cache_service.get_post_stats(post_stats.post_id)
        assert expired_stats is None
    
    @pytest.mark.asyncio
    async def test_sync_to_database(self, stats_cache_service, mock_post_stats):
        """데이터베이스 동기화 테스트"""
        # Given
        post_id = mock_post_stats.post_id
        await stats_cache_service.cache_post_stats(mock_post_stats)
        
        # 통계 수정
        await stats_cache_service.increment_view_count(post_id)
        await stats_cache_service.increment_like_count(post_id)
        
        # When
        with patch.object(stats_cache_service, '_sync_stats_to_db') as mock_sync:
            mock_sync.return_value = True
            success = await stats_cache_service.sync_stats_to_database(post_id)
        
        # Then
        assert success is True
        mock_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_popular_posts_by_views(self, stats_cache_service):
        """조회수 기준 인기 게시글 조회 테스트"""
        # Given
        stats_list = [
            PostStatsData(
                post_id=f"post_{i}",
                view_count=i * 100,  # 100, 200, 300, 400, 500
                like_count=i * 10,
                dislike_count=0,
                comment_count=i * 5,
                bookmark_count=i * 2,
                share_count=i,
                last_updated=datetime.now()
            )
            for i in range(1, 6)
        ]
        
        await stats_cache_service.batch_cache_post_stats(stats_list)
        
        # When
        popular_posts = await stats_cache_service.get_popular_posts_by_views(limit=3)
        
        # Then
        assert len(popular_posts) == 3
        # 조회수 순으로 정렬되어야 함 (높은 순)
        assert popular_posts[0]["post_id"] == "post_5"  # 500 views
        assert popular_posts[1]["post_id"] == "post_4"  # 400 views
        assert popular_posts[2]["post_id"] == "post_3"  # 300 views
    
    @pytest.mark.asyncio
    async def test_get_popular_posts_by_likes(self, stats_cache_service):
        """좋아요 기준 인기 게시글 조회 테스트"""
        # Given
        stats_list = [
            PostStatsData(
                post_id=f"post_{i}",
                view_count=100,
                like_count=i * 20,  # 20, 40, 60, 80, 100
                dislike_count=0,
                comment_count=i * 5,
                bookmark_count=i * 2,
                share_count=i,
                last_updated=datetime.now()
            )
            for i in range(1, 6)
        ]
        
        await stats_cache_service.batch_cache_post_stats(stats_list)
        
        # When
        popular_posts = await stats_cache_service.get_popular_posts_by_likes(limit=3)
        
        # Then
        assert len(popular_posts) == 3
        # 좋아요 순으로 정렬되어야 함 (높은 순)
        assert popular_posts[0]["post_id"] == "post_5"  # 100 likes
        assert popular_posts[1]["post_id"] == "post_4"  # 80 likes
        assert popular_posts[2]["post_id"] == "post_3"  # 60 likes
    
    @pytest.mark.asyncio
    async def test_increment_on_nonexistent_post(self, stats_cache_service):
        """존재하지 않는 게시글에 대한 증가 연산 테스트"""
        # Given
        import uuid
        nonexistent_post_id = f"nonexistent_post_{uuid.uuid4().hex[:8]}"
        
        # When
        view_count = await stats_cache_service.increment_view_count(nonexistent_post_id)
        
        # Then
        assert view_count == 1  # 0에서 1로 증가
        
        # 캐시에 새로 생성되었는지 확인
        cached_stats = await stats_cache_service.get_post_stats(nonexistent_post_id)
        assert cached_stats is not None
        assert cached_stats.view_count == 1
        assert cached_stats.like_count == 0  # 기본값
    
    @pytest.mark.asyncio
    async def test_stats_cache_performance(self, stats_cache_service):
        """통계 캐시 성능 테스트"""
        # Given
        post_id = "performance_test_post"
        initial_stats = PostStatsData(
            post_id=post_id,
            view_count=0,
            like_count=0,
            dislike_count=0,
            comment_count=0,
            bookmark_count=0,
            share_count=0,
            last_updated=datetime.now()
        )
        await stats_cache_service.cache_post_stats(initial_stats)
        
        # When - 100번 연속 조회수 증가
        start_time = datetime.now()
        for _ in range(100):
            await stats_cache_service.increment_view_count(post_id)
        end_time = datetime.now()
        
        # Then
        duration = (end_time - start_time).total_seconds()
        assert duration < 1.0  # 1초 이내에 완료되어야 함
        
        # 최종 결과 확인
        final_stats = await stats_cache_service.get_post_stats(post_id)
        assert final_stats.view_count == 100