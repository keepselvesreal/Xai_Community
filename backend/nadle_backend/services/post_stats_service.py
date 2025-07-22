"""
작성 시간: 2025-07-22 16:30 KST
작업 버전: v1.0
주요 컴포넌트들:
- PostStatsService: 게시글 통계 관련 공통 로직을 처리하는 서비스
주요 함수들:
- get_bulk_moving_services_stats: 여러 게시글의 moving services 통계를 배치로 조회 (lines 45-80)
- normalize_post_type: 게시글 타입 정규화 (lines 15-42)

관련 파일들:
- UserActivityService: 이 서비스를 사용하여 중복 로직 제거
- PostsService: 향후 이 서비스로 마이그레이션 예정
"""

from typing import Dict, List, Optional
import logging
from nadle_backend.repositories.comment_repository import CommentRepository

logger = logging.getLogger(__name__)


def normalize_post_type(post_type: Optional[str]) -> Optional[str]:
    """Normalize post type - handles DB inconsistency between space and underscore variants.
    
    Enhanced to handle both "moving services" and "moving_services" variants
    consistently throughout the application to prevent bugs.
    
    Args:
        post_type: The post type from database
        
    Returns:
        Normalized type (board, property_information, expert_tips, moving_services)
    """
    if not post_type:
        return None

    # 정규화 매핑 테이블 (DB 불일치 문제 해결)
    type_mapping = {
        # Moving services variants (공백/언더스코어 둘 다 처리)
        "moving services": "moving_services",
        "moving_services": "moving_services", 
        "services": "moving_services",
        
        # 다른 타입들도 일관성 확보
        "property information": "property_information",
        "property_information": "property_information",
        "expert tips": "expert_tips", 
        "expert_tips": "expert_tips",
        "board": "board",
        
        # 관리자 타입들
        "suggestions": "suggestions",
        "report": "report", 
        "moving-services-register-inquiry": "moving-services-register-inquiry",
        "expert-tips-register-inquiry": "expert-tips-register-inquiry",
    }
    
    # 매핑 테이블에서 찾아서 반환, 없으면 원본 그대로
    return type_mapping.get(post_type.lower().strip(), post_type)


class PostStatsService:
    """Service for handling post statistics and related operations."""

    def __init__(self, comment_repository: CommentRepository):
        """Initialize post stats service with comment repository.
        
        Args:
            comment_repository: Comment repository instance
        """
        self.comment_repository = comment_repository

    async def get_bulk_moving_services_stats(self, post_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """Get moving services statistics for multiple posts in a single batch query.
        
        This method optimizes N+1 query problems by fetching all comment statistics
        for multiple posts in one aggregation query.
        
        Args:
            post_ids: List of post IDs to get statistics for
            
        Returns:
            Dictionary mapping post_id to statistics:
            {
                "post_id_1": {"inquiry_count": 3, "review_count": 2},
                "post_id_2": {"inquiry_count": 0, "review_count": 1},
                ...
            }
        """
        if not post_ids:
            return {}
            
        try:
            # 배치로 모든 moving services 게시글의 댓글 통계 조회
            bulk_comment_stats = await self.comment_repository.get_bulk_comment_stats_by_posts(post_ids)
            
            # Convert to the format expected by callers
            result = {}
            for post_id in post_ids:
                stats = bulk_comment_stats.get(post_id, {"service_inquiry": 0, "service_review": 0})
                result[post_id] = {
                    "inquiry_count": stats["service_inquiry"],
                    "review_count": stats["service_review"],
                }
                
            logger.info(f"✅ PostStatsService: 배치 처리로 {len(post_ids)}개 moving services 게시글 통계 조회 완료")  # 성능 관련은 info로 유지
            return result
            
        except Exception as e:
            logger.warning(f"Failed to get bulk moving services stats: {e}")
            # Fallback to empty stats
            return {post_id: {"inquiry_count": 0, "review_count": 0} for post_id in post_ids}

    def identify_moving_services_posts(self, posts_data: List[Dict]) -> List[str]:
        """Identify moving services posts from a list of post data.
        
        Args:
            posts_data: List of post dictionaries from database
            
        Returns:
            List of post IDs that are moving services type
        """
        moving_services_post_ids = []
        for post_dict in posts_data:
            if post_dict.get("status") == "deleted":
                continue
                
            metadata = post_dict.get("metadata", {})
            post_type = metadata.get("type") if metadata else None
            
            # Use normalized type comparison for consistency
            if normalize_post_type(post_type) == "moving_services":
                moving_services_post_ids.append(str(post_dict["_id"]))
                
        return moving_services_post_ids

    def identify_moving_services_from_dict(self, posts_dict: Dict[str, Dict]) -> List[str]:
        """Identify moving services posts from a posts dictionary.
        
        Args:
            posts_dict: Dictionary mapping post_id to post data
            
        Returns:
            List of post IDs that are moving services type
        """
        return [
            post_id for post_id, post_data in posts_dict.items()
            if normalize_post_type(post_data.get("metadata", {}).get("type")) == "moving_services"
        ]