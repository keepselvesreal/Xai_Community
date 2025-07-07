from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import logging
from ..database.redis import get_redis_manager
from ..config import get_settings

logger = logging.getLogger(__name__)

class PostStatsData(BaseModel):
    """게시글 통계 데이터 모델"""
    post_id: str
    view_count: int = 0
    like_count: int = 0
    dislike_count: int = 0
    comment_count: int = 0
    bookmark_count: int = 0
    share_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)

class PostStatsCacheService:
    """Redis 기반 게시글 통계 캐싱 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.stats_prefix = "post_stats:"
        self.popular_views_key = "popular:views"
        self.popular_likes_key = "popular:likes"
        self.default_ttl = 1800  # 30분
    
    def _get_stats_key(self, post_id: str) -> str:
        """게시글 통계 Redis 키 생성"""
        return f"{self.stats_prefix}{post_id}"
    
    async def cache_post_stats(self, stats: PostStatsData, ttl: Optional[int] = None) -> bool:
        """게시글 통계를 캐시에 저장"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            logger.warning("Redis 연결 없음 - 통계 캐싱 불가")
            return False
        
        try:
            stats_key = self._get_stats_key(stats.post_id)
            
            # 통계 데이터 직렬화
            stats_dict = stats.model_dump(mode='json')
            
            # TTL 설정
            cache_ttl = ttl or self.default_ttl
            
            # Redis에 저장
            success = await redis_manager.set(stats_key, stats_dict, ttl=cache_ttl)
            
            if success:
                logger.debug(f"게시글 통계 캐싱 성공: {stats.post_id}")
                
                # 인기 게시글 목록 업데이트
                await self._update_popular_lists(stats)
            else:
                logger.error(f"게시글 통계 캐싱 실패: {stats.post_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"게시글 통계 캐싱 오류: {e}")
            return False
    
    async def get_post_stats(self, post_id: str) -> Optional[PostStatsData]:
        """게시글 통계를 캐시에서 조회"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return None
        
        try:
            stats_key = self._get_stats_key(post_id)
            stats_dict = await redis_manager.get(stats_key)
            
            if not stats_dict:
                return None
            
            # PostStatsData 객체로 변환
            return PostStatsData(**stats_dict)
            
        except Exception as e:
            logger.error(f"게시글 통계 조회 오류: {e}")
            return None
    
    async def increment_view_count(self, post_id: str) -> int:
        """조회수 증가"""
        return await self._increment_stat(post_id, "view_count")
    
    async def increment_like_count(self, post_id: str) -> int:
        """좋아요 수 증가"""
        return await self._increment_stat(post_id, "like_count")
    
    async def decrement_like_count(self, post_id: str) -> int:
        """좋아요 수 감소"""
        return await self._decrement_stat(post_id, "like_count")
    
    async def increment_dislike_count(self, post_id: str) -> int:
        """싫어요 수 증가"""
        return await self._increment_stat(post_id, "dislike_count")
    
    async def decrement_dislike_count(self, post_id: str) -> int:
        """싫어요 수 감소"""
        return await self._decrement_stat(post_id, "dislike_count")
    
    async def increment_comment_count(self, post_id: str) -> int:
        """댓글 수 증가"""
        return await self._increment_stat(post_id, "comment_count")
    
    async def decrement_comment_count(self, post_id: str) -> int:
        """댓글 수 감소"""
        return await self._decrement_stat(post_id, "comment_count")
    
    async def increment_bookmark_count(self, post_id: str) -> int:
        """북마크 수 증가"""
        return await self._increment_stat(post_id, "bookmark_count")
    
    async def decrement_bookmark_count(self, post_id: str) -> int:
        """북마크 수 감소"""
        return await self._decrement_stat(post_id, "bookmark_count")
    
    async def increment_share_count(self, post_id: str) -> int:
        """공유 수 증가"""
        return await self._increment_stat(post_id, "share_count")
    
    async def _increment_stat(self, post_id: str, stat_field: str) -> int:
        """특정 통계 필드 증가"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 현재 통계 조회
            current_stats = await self.get_post_stats(post_id)
            
            if current_stats is None:
                # 통계가 없으면 새로 생성
                current_stats = PostStatsData(post_id=post_id)
            
            # 해당 필드 증가
            current_value = getattr(current_stats, stat_field)
            new_value = current_value + 1
            setattr(current_stats, stat_field, new_value)
            current_stats.last_updated = datetime.now()
            
            # 캐시 업데이트
            await self.cache_post_stats(current_stats)
            
            logger.debug(f"게시글 {post_id} {stat_field} 증가: {current_value} -> {new_value}")
            return new_value
            
        except Exception as e:
            logger.error(f"통계 증가 오류 - {post_id}.{stat_field}: {e}")
            return 0
    
    async def _decrement_stat(self, post_id: str, stat_field: str) -> int:
        """특정 통계 필드 감소"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 현재 통계 조회
            current_stats = await self.get_post_stats(post_id)
            
            if current_stats is None:
                return 0
            
            # 해당 필드 감소 (0 이하로는 내려가지 않음)
            current_value = getattr(current_stats, stat_field)
            new_value = max(0, current_value - 1)
            setattr(current_stats, stat_field, new_value)
            current_stats.last_updated = datetime.now()
            
            # 캐시 업데이트
            await self.cache_post_stats(current_stats)
            
            logger.debug(f"게시글 {post_id} {stat_field} 감소: {current_value} -> {new_value}")
            return new_value
            
        except Exception as e:
            logger.error(f"통계 감소 오류 - {post_id}.{stat_field}: {e}")
            return 0
    
    async def batch_cache_post_stats(self, stats_list: List[PostStatsData]) -> int:
        """여러 게시글 통계 일괄 캐싱"""
        if not stats_list:
            return 0
        
        success_count = 0
        for stats in stats_list:
            if await self.cache_post_stats(stats):
                success_count += 1
        
        logger.info(f"게시글 통계 일괄 캐싱 완료: {success_count}/{len(stats_list)}")
        return success_count
    
    async def _update_popular_lists(self, stats: PostStatsData):
        """인기 게시글 목록 업데이트"""
        redis_manager = await get_redis_manager()
        
        try:
            # 조회수 기준 인기 목록 업데이트
            await redis_manager.redis_client.zadd(
                self.popular_views_key,
                {stats.post_id: stats.view_count}
            )
            
            # 좋아요 기준 인기 목록 업데이트
            await redis_manager.redis_client.zadd(
                self.popular_likes_key,
                {stats.post_id: stats.like_count}
            )
            
            # TTL 설정
            await redis_manager.redis_client.expire(self.popular_views_key, self.default_ttl)
            await redis_manager.redis_client.expire(self.popular_likes_key, self.default_ttl)
            
        except Exception as e:
            logger.error(f"인기 목록 업데이트 오류: {e}")
    
    async def get_popular_posts_by_views(self, limit: int = 10) -> List[Dict[str, Any]]:
        """조회수 기준 인기 게시글 목록 조회"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return []
        
        try:
            # Redis ZREVRANGE로 높은 점수 순으로 조회
            popular_posts = await redis_manager.redis_client.zrevrange(
                self.popular_views_key, 0, limit - 1, withscores=True
            )
            
            result = []
            for post_id, view_count in popular_posts:
                # 상세 통계 정보 가져오기
                stats = await self.get_post_stats(post_id)
                if stats:
                    result.append({
                        "post_id": post_id,
                        "view_count": int(view_count),
                        "like_count": stats.like_count,
                        "comment_count": stats.comment_count,
                        "bookmark_count": stats.bookmark_count
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"인기 게시글 조회 오류 (조회수): {e}")
            return []
    
    async def get_popular_posts_by_likes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """좋아요 기준 인기 게시글 목록 조회"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return []
        
        try:
            # Redis ZREVRANGE로 높은 점수 순으로 조회
            popular_posts = await redis_manager.redis_client.zrevrange(
                self.popular_likes_key, 0, limit - 1, withscores=True
            )
            
            result = []
            for post_id, like_count in popular_posts:
                # 상세 통계 정보 가져오기
                stats = await self.get_post_stats(post_id)
                if stats:
                    result.append({
                        "post_id": post_id,
                        "like_count": int(like_count),
                        "view_count": stats.view_count,
                        "comment_count": stats.comment_count,
                        "bookmark_count": stats.bookmark_count
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"인기 게시글 조회 오류 (좋아요): {e}")
            return []
    
    async def sync_stats_to_database(self, post_id: str) -> bool:
        """캐시된 통계를 데이터베이스에 동기화"""
        try:
            # 캐시에서 통계 조회
            cached_stats = await self.get_post_stats(post_id)
            if not cached_stats:
                return False
            
            # 데이터베이스 동기화 수행
            success = await self._sync_stats_to_db(cached_stats)
            
            if success:
                logger.info(f"게시글 통계 DB 동기화 성공: {post_id}")
            else:
                logger.error(f"게시글 통계 DB 동기화 실패: {post_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"게시글 통계 동기화 오류: {e}")
            return False
    
    async def _sync_stats_to_db(self, stats: PostStatsData) -> bool:
        """실제 데이터베이스 동기화 구현 (추후 구현)"""
        # TODO: 실제 데이터베이스 업데이트 로직 구현
        # 현재는 테스트를 위한 Mock 함수
        logger.debug(f"DB 동기화 시뮬레이션: {stats.post_id}")
        return True
    
    async def clear_all_stats_cache(self) -> int:
        """모든 통계 캐시 삭제 (테스트용)"""
        redis_manager = await get_redis_manager()
        
        if not await redis_manager.is_connected():
            return 0
        
        try:
            # 개발/테스트 환경에서만 사용
            if self.settings.environment not in ["development", "test"]:
                logger.warning("프로덕션 환경에서는 전체 통계 캐시 삭제 불가")
                return 0
            
            # 통계 관련 모든 키 삭제
            deleted_count = 0
            
            # 개별 게시글 통계 삭제
            pattern = f"{self.stats_prefix}*"
            # 실제 구현에서는 SCAN 명령어 사용 권장
            
            # 인기 목록 삭제
            await redis_manager.delete(self.popular_views_key)
            await redis_manager.delete(self.popular_likes_key)
            
            logger.info(f"테스트 환경: 통계 캐시 데이터 정리 완료")
            return deleted_count
            
        except Exception as e:
            logger.error(f"통계 캐시 전체 삭제 오류: {e}")
            return 0

# 글로벌 게시글 통계 캐시 서비스 인스턴스
post_stats_cache_service = PostStatsCacheService()

async def get_post_stats_cache_service() -> PostStatsCacheService:
    """게시글 통계 캐시 서비스 인스턴스 반환"""
    return post_stats_cache_service