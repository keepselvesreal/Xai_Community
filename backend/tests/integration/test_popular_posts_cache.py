import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.services.popular_posts_cache_service import PopularPostsCacheService, PopularPostData
from nadle_backend.database.redis import redis_manager

@pytest.fixture
async def popular_cache_service():
    """인기 게시글 캐시 서비스 픽스처"""
    service = PopularPostsCacheService()
    await redis_manager.connect()
    
    # 테스트 전 데이터 정리
    if await redis_manager.is_connected():
        await service.clear_all_popular_cache()
    
    yield service
    
    # 테스트 후 정리
    if await redis_manager.is_connected():
        await service.clear_all_popular_cache()
    
    await redis_manager.disconnect()

@pytest.fixture
def mock_popular_posts():
    """테스트용 인기 게시글 데이터"""
    return [
        PopularPostData(
            post_id=f"post_{i}",
            title=f"테스트 게시글 {i}",
            author_id=f"author_{i % 3}",
            service_type="community",
            view_count=i * 100,
            like_count=i * 20,
            comment_count=i * 5,
            created_at=datetime.now() - timedelta(days=i),
            score=i * 100 + i * 20  # view_count + like_count
        )
        for i in range(1, 6)
    ]

class TestPopularPostsCache:
    """인기 게시글 캐싱 테스트 클래스"""
    
    @pytest.mark.asyncio
    async def test_cache_popular_posts_by_views(self, popular_cache_service, mock_popular_posts):
        """조회수 기준 인기 게시글 캐싱 테스트"""
        # Given
        posts = mock_popular_posts
        
        # When
        success = await popular_cache_service.cache_popular_posts_by_views(posts)
        
        # Then
        assert success is True
        
        # 캐시에서 조회 확인
        cached_posts = await popular_cache_service.get_popular_posts_by_views(limit=5)
        assert len(cached_posts) == 5
        
        # 조회수 순으로 정렬되어 있는지 확인 (높은 순)
        for i in range(len(cached_posts) - 1):
            assert cached_posts[i]["view_count"] >= cached_posts[i + 1]["view_count"]
    
    @pytest.mark.asyncio
    async def test_cache_popular_posts_by_likes(self, popular_cache_service, mock_popular_posts):
        """좋아요 기준 인기 게시글 캐싱 테스트"""
        # Given
        posts = mock_popular_posts
        
        # When
        success = await popular_cache_service.cache_popular_posts_by_likes(posts)
        
        # Then
        assert success is True
        
        # 캐시에서 조회 확인
        cached_posts = await popular_cache_service.get_popular_posts_by_likes(limit=5)
        assert len(cached_posts) == 5
        
        # 좋아요 순으로 정렬되어 있는지 확인 (높은 순)
        for i in range(len(cached_posts) - 1):
            assert cached_posts[i]["like_count"] >= cached_posts[i + 1]["like_count"]
    
    @pytest.mark.asyncio
    async def test_cache_popular_posts_by_service(self, popular_cache_service):
        """서비스별 인기 게시글 캐싱 테스트"""
        # Given
        community_posts = [
            PopularPostData(
                post_id=f"community_post_{i}",
                title=f"커뮤니티 게시글 {i}",
                author_id=f"author_{i}",
                service_type="community",
                view_count=i * 100,
                like_count=i * 20,
                comment_count=i * 5,
                created_at=datetime.now(),
                score=i * 100
            )
            for i in range(1, 4)
        ]
        
        tips_posts = [
            PopularPostData(
                post_id=f"tips_post_{i}",
                title=f"팁 게시글 {i}",
                author_id=f"author_{i}",
                service_type="tips",
                view_count=i * 150,
                like_count=i * 25,
                comment_count=i * 3,
                created_at=datetime.now(),
                score=i * 150
            )
            for i in range(1, 4)
        ]
        
        # When
        success1 = await popular_cache_service.cache_popular_posts_by_service("community", community_posts)
        success2 = await popular_cache_service.cache_popular_posts_by_service("tips", tips_posts)
        
        # Then
        assert success1 is True
        assert success2 is True
        
        # 서비스별 조회 확인
        cached_community = await popular_cache_service.get_popular_posts_by_service("community", limit=5)
        cached_tips = await popular_cache_service.get_popular_posts_by_service("tips", limit=5)
        
        assert len(cached_community) == 3
        assert len(cached_tips) == 3
        
        # 서비스 타입 확인
        for post in cached_community:
            assert post["service_type"] == "community"
        for post in cached_tips:
            assert post["service_type"] == "tips"
    
    @pytest.mark.asyncio
    async def test_get_hot_posts_realtime(self, popular_cache_service, mock_popular_posts):
        """실시간 HOT 게시글 조회 테스트"""
        # Given
        recent_posts = [
            PopularPostData(
                post_id=f"hot_post_{i}",
                title=f"HOT 게시글 {i}",
                author_id=f"author_{i}",
                service_type="community",
                view_count=i * 200,
                like_count=i * 50,
                comment_count=i * 10,
                created_at=datetime.now() - timedelta(hours=i),  # 최근 게시글
                score=i * 200 + i * 50 * 2  # view_count + like_count * 2
            )
            for i in range(1, 6)
        ]
        
        # When
        success = await popular_cache_service.cache_hot_posts_realtime(recent_posts)
        
        # Then
        assert success is True
        
        # HOT 게시글 조회
        hot_posts = await popular_cache_service.get_hot_posts_realtime(limit=3)
        assert len(hot_posts) <= 3
        
        # 스코어 순으로 정렬되어 있는지 확인
        for i in range(len(hot_posts) - 1):
            assert hot_posts[i]["score"] >= hot_posts[i + 1]["score"]
    
    @pytest.mark.asyncio
    async def test_get_trending_posts_weekly(self, popular_cache_service):
        """주간 트렌딩 게시글 조회 테스트"""
        # Given
        trending_posts = [
            PopularPostData(
                post_id=f"trending_post_{i}",
                title=f"트렌딩 게시글 {i}",
                author_id=f"author_{i}",
                service_type="info",
                view_count=i * 300,
                like_count=i * 30,
                comment_count=i * 8,
                created_at=datetime.now() - timedelta(days=i),
                score=i * 300 + i * 30  # 주간 점수 계산
            )
            for i in range(1, 8)
        ]
        
        # When
        success = await popular_cache_service.cache_trending_posts_weekly(trending_posts)
        
        # Then
        assert success is True
        
        # 트렌딩 게시글 조회
        trending = await popular_cache_service.get_trending_posts_weekly(limit=5)
        assert len(trending) <= 5
    
    @pytest.mark.asyncio
    async def test_update_post_in_popular_lists(self, popular_cache_service, mock_popular_posts):
        """인기 목록에서 특정 게시글 업데이트 테스트"""
        # Given
        posts = mock_popular_posts
        await popular_cache_service.cache_popular_posts_by_views(posts)
        
        # 특정 게시글의 조회수 대폭 증가
        updated_post = PopularPostData(
            post_id="post_1",
            title="업데이트된 게시글 1",
            author_id="author_1",
            service_type="community",
            view_count=1000,  # 크게 증가
            like_count=200,
            comment_count=50,
            created_at=datetime.now(),
            score=1200
        )
        
        # When
        success = await popular_cache_service.update_post_in_popular_lists(updated_post)
        
        # Then
        assert success is True
        
        # 업데이트된 게시글이 상위에 올라왔는지 확인
        popular_posts = await popular_cache_service.get_popular_posts_by_views(limit=5)
        assert popular_posts[0]["post_id"] == "post_1"
        assert popular_posts[0]["view_count"] == 1000
    
    @pytest.mark.asyncio
    async def test_remove_post_from_popular_lists(self, popular_cache_service, mock_popular_posts):
        """인기 목록에서 게시글 제거 테스트"""
        # Given
        posts = mock_popular_posts
        await popular_cache_service.cache_popular_posts_by_views(posts)
        
        # When
        success = await popular_cache_service.remove_post_from_popular_lists("post_3")
        
        # Then
        assert success is True
        
        # 제거된 게시글이 목록에 없는지 확인
        popular_posts = await popular_cache_service.get_popular_posts_by_views(limit=10)
        post_ids = [post["post_id"] for post in popular_posts]
        assert "post_3" not in post_ids
    
    @pytest.mark.asyncio
    async def test_get_popular_posts_with_pagination(self, popular_cache_service, mock_popular_posts):
        """페이지네이션을 통한 인기 게시글 조회 테스트"""
        # Given
        posts = mock_popular_posts
        await popular_cache_service.cache_popular_posts_by_views(posts)
        
        # When
        page1 = await popular_cache_service.get_popular_posts_by_views(limit=2, offset=0)
        page2 = await popular_cache_service.get_popular_posts_by_views(limit=2, offset=2)
        
        # Then
        assert len(page1) == 2
        assert len(page2) == 2
        
        # 페이지간 게시글이 겹치지 않는지 확인
        page1_ids = set(post["post_id"] for post in page1)
        page2_ids = set(post["post_id"] for post in page2)
        assert page1_ids.isdisjoint(page2_ids)
    
    @pytest.mark.asyncio
    async def test_popular_posts_ttl_expiration(self, popular_cache_service, mock_popular_posts):
        """인기 게시글 목록 TTL 만료 테스트"""
        # Given
        posts = mock_popular_posts
        short_ttl = 2  # 2초
        
        # When
        success = await popular_cache_service.cache_popular_posts_by_views(posts, ttl=short_ttl)
        
        # Then
        assert success is True
        
        # 즉시 조회 - 존재해야 함
        cached_posts = await popular_cache_service.get_popular_posts_by_views(limit=5)
        assert len(cached_posts) == 5
        
        # TTL 대기 후 조회 - 만료되어야 함
        await asyncio.sleep(2.1)
        expired_posts = await popular_cache_service.get_popular_posts_by_views(limit=5)
        assert len(expired_posts) == 0
    
    @pytest.mark.asyncio
    async def test_get_popular_authors(self, popular_cache_service, mock_popular_posts):
        """인기 작성자 조회 테스트"""
        # Given
        posts = mock_popular_posts
        await popular_cache_service.cache_popular_posts_by_views(posts)
        
        # When
        popular_authors = await popular_cache_service.get_popular_authors(limit=3)
        
        # Then
        assert len(popular_authors) <= 3
        
        # 작성자별 점수가 계산되어 있는지 확인
        for author in popular_authors:
            assert "author_id" in author
            assert "total_score" in author
            assert "post_count" in author
    
    @pytest.mark.asyncio
    async def test_refresh_popular_lists(self, popular_cache_service, mock_popular_posts):
        """인기 목록 전체 갱신 테스트"""
        # Given
        old_posts = mock_popular_posts[:3]
        await popular_cache_service.cache_popular_posts_by_views(old_posts)
        
        # 새로운 데이터
        new_posts = [
            PopularPostData(
                post_id=f"new_post_{i}",
                title=f"새 게시글 {i}",
                author_id=f"new_author_{i}",
                service_type="community",
                view_count=i * 500,
                like_count=i * 100,
                comment_count=i * 15,
                created_at=datetime.now(),
                score=i * 600
            )
            for i in range(1, 4)
        ]
        
        # When
        success = await popular_cache_service.refresh_popular_lists_by_views(new_posts)
        
        # Then
        assert success is True
        
        # 새로운 데이터만 있는지 확인
        cached_posts = await popular_cache_service.get_popular_posts_by_views(limit=10)
        cached_ids = [post["post_id"] for post in cached_posts]
        
        for new_post in new_posts:
            assert new_post.post_id in cached_ids
        
        for old_post in old_posts:
            assert old_post.post_id not in cached_ids
    
    @pytest.mark.asyncio
    async def test_popular_posts_cache_performance(self, popular_cache_service):
        """인기 게시글 캐시 성능 테스트"""
        # Given
        large_posts = [
            PopularPostData(
                post_id=f"perf_post_{i}",
                title=f"성능 테스트 게시글 {i}",
                author_id=f"author_{i % 10}",
                service_type="community",
                view_count=i * 10,
                like_count=i * 2,
                comment_count=i,
                created_at=datetime.now(),
                score=i * 12
            )
            for i in range(1, 101)  # 100개 게시글
        ]
        
        # When - 대량 데이터 캐싱
        start_time = datetime.now()
        success = await popular_cache_service.cache_popular_posts_by_views(large_posts)
        cache_time = (datetime.now() - start_time).total_seconds()
        
        # When - 조회 성능 측정
        start_time = datetime.now()
        for _ in range(10):  # 10번 연속 조회
            await popular_cache_service.get_popular_posts_by_views(limit=20)
        query_time = (datetime.now() - start_time).total_seconds()
        
        # Then
        assert success is True
        assert cache_time < 2.0  # 캐싱은 2초 이내
        assert query_time < 0.5  # 10번 조회는 0.5초 이내
        
        print(f"캐싱 시간: {cache_time:.3f}초, 조회 시간: {query_time:.3f}초")
    
    @pytest.mark.asyncio
    async def test_popular_posts_search_by_keyword(self, popular_cache_service, mock_popular_posts):
        """키워드 기반 인기 게시글 검색 테스트"""
        # Given
        posts = mock_popular_posts
        await popular_cache_service.cache_popular_posts_by_views(posts)
        
        # When
        search_results = await popular_cache_service.search_popular_posts("테스트")
        
        # Then
        assert len(search_results) > 0
        
        # 검색 결과에 키워드가 포함되어 있는지 확인
        for post in search_results:
            assert "테스트" in post["title"]