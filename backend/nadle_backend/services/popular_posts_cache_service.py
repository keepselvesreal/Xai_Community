from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import logging
from ..database.redis import get_redis_manager
from ..config import get_settings

logger = logging.getLogger(__name__)

class PopularPostData(BaseModel):
    """인기 게시글 데이터 모델"""
    post_id: str
    title: str
    author_id: str
    service_type: str  # community, tips, info 등
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    bookmark_count: int = 0
    created_at: datetime
    score: float = 0.0  # 인기도 점수
    
    def calculate_score(self) -> float:
        """인기도 점수 계산"""
        # 시간 가중치 (최근 글일수록 높은 점수)
        days_old = (datetime.now() - self.created_at).days
        time_weight = max(0.1, 1.0 - (days_old * 0.1))
        
        # 상호작용 점수 계산
        interaction_score = (
            self.view_count * 1.0 +
            self.like_count * 5.0 +
            self.comment_count * 3.0 +
            self.bookmark_count * 4.0
        )
        
        return interaction_score * time_weight

class PopularPostsCacheService:
    """Redis 기반 인기 게시글 캐싱 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.popular_views_key = "popular:views"
        self.popular_likes_key = "popular:likes"
        self.popular_service_prefix = "popular:service:"
        self.hot_posts_key = "hot:realtime"
        self.trending_weekly_key = "trending:weekly"
        self.popular_authors_key = "popular:authors"
        self.default_ttl = 1800  # 30분
    
    def _get_service_key(self, service_type: str) -> str:
        """서비스별 인기 게시글 키 생성"""
        return f"{self.popular_service_prefix}{service_type}"
    
    async def cache_popular_posts_by_views(self, posts: List[PopularPostData], ttl: Optional[int] = None) -> bool:
        """조회수 기준 인기 게시글 캐싱"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            logger.warning("Redis 연결 없음 - 인기 게시글 캐싱 불가")
            return False
        
        try:
            # Redis Sorted Set에 저장 (조회수를 점수로 사용)
            post_scores = {}
            post_details = {}
            
            for post in posts:
                post_scores[post.post_id] = post.view_count
                post_details[f"post_detail:{post.post_id}"] = post.model_dump(mode='json')
            
            # Sorted Set에 점수와 함께 저장
            if post_scores:
                await redis_manager.redis_client.zadd(self.popular_views_key, post_scores)
                
                # 각 게시글의 상세 정보 저장
                for detail_key, detail_data in post_details.items():
                    await redis_manager.set(detail_key, detail_data, ttl=ttl or self.default_ttl)
                
                # TTL 설정
                await redis_manager.redis_client.expire(
                    self.popular_views_key, ttl or self.default_ttl
                )
            
            logger.info(f"조회수 기준 인기 게시글 캐싱 완료: {len(posts)}개")
            return True
            
        except Exception as e:
            logger.error(f"조회수 기준 인기 게시글 캐싱 오류: {e}")
            return False
    
    async def cache_popular_posts_by_likes(self, posts: List[PopularPostData], ttl: Optional[int] = None) -> bool:
        """좋아요 기준 인기 게시글 캐싱"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # Redis Sorted Set에 저장 (좋아요를 점수로 사용)
            post_scores = {}
            post_details = {}
            
            for post in posts:
                post_scores[post.post_id] = post.like_count
                post_details[f"post_detail:{post.post_id}"] = post.model_dump(mode='json')
            
            # Sorted Set에 점수와 함께 저장
            if post_scores:
                await redis_manager.redis_client.zadd(self.popular_likes_key, post_scores)
                
                # 각 게시글의 상세 정보 저장
                for detail_key, detail_data in post_details.items():
                    await redis_manager.set(detail_key, detail_data, ttl=ttl or self.default_ttl)
                
                # TTL 설정
                await redis_manager.redis_client.expire(
                    self.popular_likes_key, ttl or self.default_ttl
                )
            
            logger.info(f"좋아요 기준 인기 게시글 캐싱 완료: {len(posts)}개")
            return True
            
        except Exception as e:
            logger.error(f"좋아요 기준 인기 게시글 캐싱 오류: {e}")
            return False
    
    async def cache_popular_posts_by_service(self, service_type: str, posts: List[PopularPostData], ttl: Optional[int] = None) -> bool:
        """서비스별 인기 게시글 캐싱"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            service_key = self._get_service_key(service_type)
            
            # 점수 계산 후 저장
            post_scores = {}
            post_details = {}
            
            for post in posts:
                score = post.calculate_score()
                post_scores[post.post_id] = score
                post_details[f"post_detail:{post.post_id}"] = post.model_dump(mode='json')
            
            if post_scores:
                await redis_manager.redis_client.zadd(service_key, post_scores)
                
                # 상세 정보 저장
                for detail_key, detail_data in post_details.items():
                    await redis_manager.set(detail_key, detail_data, ttl=ttl or self.default_ttl)
                
                # TTL 설정
                await redis_manager.redis_client.expire(service_key, ttl or self.default_ttl)
            
            logger.info(f"서비스 '{service_type}' 인기 게시글 캐싱 완료: {len(posts)}개")
            return True
            
        except Exception as e:
            logger.error(f"서비스별 인기 게시글 캐싱 오류: {e}")
            return False
    
    async def cache_hot_posts_realtime(self, posts: List[PopularPostData], ttl: int = 900) -> bool:
        """실시간 HOT 게시글 캐싱 (15분 TTL)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # 실시간 점수 계산 (최근성과 상호작용 중심)
            post_scores = {}
            post_details = {}
            
            for post in posts:
                # 실시간 점수: 최근 24시간 내 게시글에 가중치 부여
                hours_old = (datetime.now() - post.created_at).total_seconds() / 3600
                recency_weight = max(0.1, 1.0 - (hours_old / 24))
                
                hot_score = (
                    post.view_count * 1.0 +
                    post.like_count * 10.0 +  # 좋아요에 높은 가중치
                    post.comment_count * 5.0
                ) * recency_weight
                
                post_scores[post.post_id] = hot_score
                post_details[f"post_detail:{post.post_id}"] = post.model_dump(mode='json')
            
            if post_scores:
                await redis_manager.redis_client.zadd(self.hot_posts_key, post_scores)
                
                # 상세 정보 저장
                for detail_key, detail_data in post_details.items():
                    await redis_manager.set(detail_key, detail_data, ttl=ttl)
                
                # 짧은 TTL 설정 (실시간)
                await redis_manager.redis_client.expire(self.hot_posts_key, ttl)
            
            logger.info(f"실시간 HOT 게시글 캐싱 완료: {len(posts)}개")
            return True
            
        except Exception as e:
            logger.error(f"실시간 HOT 게시글 캐싱 오류: {e}")
            return False
    
    async def cache_trending_posts_weekly(self, posts: List[PopularPostData], ttl: int = 3600) -> bool:
        """주간 트렌딩 게시글 캐싱 (1시간 TTL)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # 주간 트렌딩 점수 계산
            post_scores = {}
            post_details = {}
            
            for post in posts:
                # 지난 7일 내 게시글만 고려
                days_old = (datetime.now() - post.created_at).days
                if days_old <= 7:
                    trending_score = post.calculate_score()
                    post_scores[post.post_id] = trending_score
                    post_details[f"post_detail:{post.post_id}"] = post.model_dump(mode='json')
            
            if post_scores:
                await redis_manager.redis_client.zadd(self.trending_weekly_key, post_scores)
                
                # 상세 정보 저장
                for detail_key, detail_data in post_details.items():
                    await redis_manager.set(detail_key, detail_data, ttl=ttl)
                
                # TTL 설정
                await redis_manager.redis_client.expire(self.trending_weekly_key, ttl)
            
            logger.info(f"주간 트렌딩 게시글 캐싱 완료: {len(post_scores)}개")
            return True
            
        except Exception as e:
            logger.error(f"주간 트렌딩 게시글 캐싱 오류: {e}")
            return False
    
    async def get_popular_posts_by_views(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """조회수 기준 인기 게시글 조회"""
        return await self._get_popular_posts_from_sorted_set(
            self.popular_views_key, limit, offset
        )
    
    async def get_popular_posts_by_likes(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """좋아요 기준 인기 게시글 조회"""
        return await self._get_popular_posts_from_sorted_set(
            self.popular_likes_key, limit, offset
        )
    
    async def get_popular_posts_by_service(self, service_type: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """서비스별 인기 게시글 조회"""
        service_key = self._get_service_key(service_type)
        return await self._get_popular_posts_from_sorted_set(service_key, limit, offset)
    
    async def get_hot_posts_realtime(self, limit: int = 10) -> List[Dict[str, Any]]:
        """실시간 HOT 게시글 조회"""
        return await self._get_popular_posts_from_sorted_set(self.hot_posts_key, limit)
    
    async def get_trending_posts_weekly(self, limit: int = 10) -> List[Dict[str, Any]]:
        """주간 트렌딩 게시글 조회"""
        return await self._get_popular_posts_from_sorted_set(self.trending_weekly_key, limit)
    
    async def _get_popular_posts_from_sorted_set(self, key: str, limit: int, offset: int = 0) -> List[Dict[str, Any]]:
        """Sorted Set에서 인기 게시글 조회 (공통 메서드)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return []
        
        try:
            # Redis ZREVRANGE로 높은 점수 순으로 조회 (페이지네이션 지원)
            end_index = offset + limit - 1
            popular_posts = await redis_manager.redis_client.zrevrange(
                key, offset, end_index, withscores=True
            )
            
            result = []
            for post_id, score in popular_posts:
                # 상세 정보 조회
                detail_key = f"post_detail:{post_id}"
                post_detail = await redis_manager.get(detail_key)
                
                if post_detail:
                    post_data = dict(post_detail)
                    post_data["score"] = float(score)
                    result.append(post_data)
            
            return result
            
        except Exception as e:
            logger.error(f"인기 게시글 조회 오류 ({key}): {e}")
            return []
    
    async def update_post_in_popular_lists(self, post: PopularPostData) -> bool:
        """인기 목록에서 특정 게시글 업데이트"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # 모든 관련 Sorted Set에서 업데이트
            tasks = [
                redis_manager.redis_client.zadd(self.popular_views_key, {post.post_id: post.view_count}),
                redis_manager.redis_client.zadd(self.popular_likes_key, {post.post_id: post.like_count}),
                redis_manager.redis_client.zadd(
                    self._get_service_key(post.service_type), 
                    {post.post_id: post.calculate_score()}
                )
            ]
            
            # 상세 정보 업데이트
            detail_key = f"post_detail:{post.post_id}"
            await redis_manager.set(detail_key, post.model_dump(mode='json'), ttl=self.default_ttl)
            
            # 병렬 실행
            await asyncio.gather(*tasks)
            
            logger.debug(f"게시글 인기 목록 업데이트 완료: {post.post_id}")
            return True
            
        except Exception as e:
            logger.error(f"게시글 인기 목록 업데이트 오류: {e}")
            return False
    
    async def remove_post_from_popular_lists(self, post_id: str) -> bool:
        """인기 목록에서 게시글 제거"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # 모든 Sorted Set에서 제거
            keys_to_clean = [
                self.popular_views_key,
                self.popular_likes_key,
                self.hot_posts_key,
                self.trending_weekly_key
            ]
            
            tasks = []
            for key in keys_to_clean:
                tasks.append(redis_manager.redis_client.zrem(key, post_id))
            
            # 상세 정보 삭제
            detail_key = f"post_detail:{post_id}"
            tasks.append(redis_manager.delete(detail_key))
            
            # 병렬 실행
            await asyncio.gather(*tasks)
            
            logger.info(f"게시글 인기 목록에서 제거 완료: {post_id}")
            return True
            
        except Exception as e:
            logger.error(f"게시글 인기 목록 제거 오류: {e}")
            return False
    
    async def get_popular_authors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """인기 작성자 조회"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return []
        
        try:
            # 작성자별 점수 집계
            author_scores = {}
            author_post_counts = {}
            
            # 조회수 기준 인기 게시글에서 작성자 정보 수집
            popular_posts = await redis_manager.redis_client.zrevrange(
                self.popular_views_key, 0, 99, withscores=True
            )
            
            for post_id, score in popular_posts:
                detail_key = f"post_detail:{post_id}"
                post_detail = await redis_manager.get(detail_key)
                
                if post_detail:
                    author_id = post_detail.get("author_id")
                    if author_id:
                        author_scores[author_id] = author_scores.get(author_id, 0) + score
                        author_post_counts[author_id] = author_post_counts.get(author_id, 0) + 1
            
            # 점수 순으로 정렬
            sorted_authors = sorted(
                author_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit]
            
            result = []
            for author_id, total_score in sorted_authors:
                result.append({
                    "author_id": author_id,
                    "total_score": float(total_score),
                    "post_count": author_post_counts.get(author_id, 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"인기 작성자 조회 오류: {e}")
            return []
    
    async def search_popular_posts(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """키워드 기반 인기 게시글 검색"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return []
        
        try:
            # 조회수 기준 인기 게시글에서 검색
            popular_posts = await self.get_popular_posts_by_views(limit=100)
            
            # 키워드 매칭
            search_results = []
            for post in popular_posts:
                if keyword.lower() in post.get("title", "").lower():
                    search_results.append(post)
                    if len(search_results) >= limit:
                        break
            
            return search_results
            
        except Exception as e:
            logger.error(f"인기 게시글 검색 오류: {e}")
            return []
    
    async def refresh_popular_lists_by_views(self, posts: List[PopularPostData]) -> bool:
        """조회수 기준 인기 목록 전체 갱신"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return False
        
        try:
            # 기존 목록 삭제
            await redis_manager.delete(self.popular_views_key)
            
            # 새 목록으로 교체
            return await self.cache_popular_posts_by_views(posts)
            
        except Exception as e:
            logger.error(f"인기 목록 갱신 오류: {e}")
            return False
    
    async def clear_all_popular_cache(self) -> int:
        """모든 인기 게시글 캐시 삭제 (테스트용)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 개발/테스트 환경에서만 사용
            if self.settings.environment not in ["development", "test"]:
                logger.warning("프로덕션 환경에서는 전체 인기 캐시 삭제 불가")
                return 0
            
            # 인기 게시글 관련 모든 키 삭제
            keys_to_delete = [
                self.popular_views_key,
                self.popular_likes_key,
                self.hot_posts_key,
                self.trending_weekly_key,
                self.popular_authors_key
            ]
            
            # 서비스별 키들도 삭제
            service_keys = [
                f"{self.popular_service_prefix}community",
                f"{self.popular_service_prefix}tips",
                f"{self.popular_service_prefix}info"
            ]
            keys_to_delete.extend(service_keys)
            
            deleted_count = 0
            for key in keys_to_delete:
                if await redis_manager.delete(key):
                    deleted_count += 1
            
            # 게시글 상세 정보 캐시도 삭제
            try:
                keys = await redis_manager.redis_client.keys("post_detail:*")
                for key in keys:
                    await redis_manager.delete(key)
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"게시글 상세 정보 캐시 삭제 중 오류: {e}")
            
            logger.info("테스트 환경: 인기 게시글 캐시 데이터 정리 완료")
            return deleted_count
            
        except Exception as e:
            logger.error(f"인기 캐시 전체 삭제 오류: {e}")
            return 0

# asyncio import 추가
import asyncio

# 글로벌 인기 게시글 캐시 서비스 인스턴스
popular_posts_cache_service = PopularPostsCacheService()

async def get_popular_posts_cache_service() -> PopularPostsCacheService:
    """인기 게시글 캐시 서비스 인스턴스 반환"""
    return popular_posts_cache_service