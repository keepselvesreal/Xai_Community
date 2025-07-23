"""Analytics router for user analytics and statistics endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel

from nadle_backend.services.analytics_service import AnalyticsService
from nadle_backend.dependencies.auth import get_current_user
from nadle_backend.models.core import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Response models
class UserStatsResponse(BaseModel):
    """사용자 통계 응답 모델"""

    total_users: int
    new_users_today: int
    new_users_weekly: int
    daily_active_users: int


class ConversionRateResponse(BaseModel):
    """전환율 응답 모델"""

    visitors_today: int
    signups_today: int
    conversion_rate_today: float
    visitors_yesterday: int
    signups_yesterday: int
    conversion_rate_yesterday: float
    conversion_rate_change: float  # 어제 대비 변화율


class EventStatsResponse(BaseModel):
    """이벤트 통계 응답 모델"""

    post_creation: Dict[str, int]  # today, yesterday_change
    post_likes: Dict[str, int]
    post_bookmarks: Dict[str, int]
    comment_creation: Dict[str, int]


class BounceRateResponse(BaseModel):
    """이탈률 응답 모델"""

    site_bounce_rate: float


class RealtimeActivityResponse(BaseModel):
    """실시간 활동 응답 모델"""

    timestamp: str
    activity_type: str  # 'signup', 'post_create', 'comment_create', 'like', 'bookmark'
    user_name: str
    description: str
    target_title: Optional[str] = None


# Dependency injection
def get_analytics_service() -> AnalyticsService:
    """Analytics 서비스 의존성 주입"""
    return AnalyticsService()


@router.get("/users/stats", response_model=UserStatsResponse)
async def get_user_stats(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    사용자 통계 조회
    - 총 사용자 수
    - 신규 사용자 (오늘, 최근 7일)
    - 일일 활성 사용자
    """
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

        stats = await analytics_service.get_user_statistics()
        return UserStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"사용자 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/funnel/signup", response_model=ConversionRateResponse)
async def get_signup_conversion(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    가입 전환율 조회 (방문 → 가입)
    - 어제 방문자 수
    - 어제 가입자 수
    - 어제 전환율
    - 어제 대비 전환율 변화
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

        conversion_data = await analytics_service.get_signup_conversion_rate()
        return ConversionRateResponse(**conversion_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"가입 전환율 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/events/stats", response_model=EventStatsResponse)
async def get_event_stats(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    이벤트 통계 조회
    - 게시글 작성, 추천, 저장
    - 댓글 작성
    - 각각 오늘 건수와 어제 대비 변화
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

        event_stats = await analytics_service.get_event_statistics()
        return EventStatsResponse(**event_stats)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"이벤트 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/bounce-rate", response_model=BounceRateResponse)
async def get_bounce_rate(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    전체 사이트 이탈률 조회
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

        bounce_rate = await analytics_service.get_site_bounce_rate()
        return BounceRateResponse(site_bounce_rate=bounce_rate)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"이탈률 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/realtime/activity", response_model=list[RealtimeActivityResponse])
async def get_realtime_activity(
    limit: int = Query(default=10, le=50, description="조회할 활동 수"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    실시간 활동 피드 조회
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

        activities = await analytics_service.get_realtime_activities(limit)
        return [RealtimeActivityResponse(**activity) for activity in activities]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"실시간 활동 조회 중 오류가 발생했습니다: {str(e)}"
        )


