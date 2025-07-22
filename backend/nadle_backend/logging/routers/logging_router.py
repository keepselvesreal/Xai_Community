"""
FastAPI router for logging system endpoints.

Provides REST API endpoints for log management, search, statistics,
and external log collection operations.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ...core.logging import (
    LogFilter,
    LogListResponse,
    LogStats,
    LogDashboardResponse,
    LogEntry,
    LogLevel,
    LogServiceType,
    LogSource,
    RepositoryError,
    AdapterError,
)
from ..services import LogService, ExternalLogCollectorService
from ..dependencies import (
    get_log_service,
    get_external_log_collector,
    get_current_user_optional,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/logs", tags=["logging"])


@router.get("/search", response_model=LogListResponse)
async def search_logs(
    # Query parameters for filtering
    levels: Optional[List[str]] = Query(None, description="Log levels to filter by"),
    services: Optional[List[str]] = Query(None, description="Services to filter by"),
    sources: Optional[List[str]] = Query(None, description="Sources to filter by"),
    search_query: Optional[str] = Query(None, description="Text search query"),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    endpoint: Optional[str] = Query(None, description="Endpoint filter"),
    status_codes: Optional[List[int]] = Query(
        None, description="HTTP status codes to filter by"
    ),
    regions: Optional[List[str]] = Query(None, description="Regions to filter by"),
    instance_ids: Optional[List[str]] = Query(
        None, description="Instance IDs to filter by"
    ),
    deployment_ids: Optional[List[str]] = Query(
        None, description="Deployment IDs to filter by"
    ),
    # Time range
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    # Dependencies
    log_service: LogService = Depends(get_log_service),
    current_user=Depends(get_current_user_optional),
):
    """
    Search logs with filtering and pagination.

    Supports filtering by:
    - Log levels (ERROR, WARN, INFO, DEBUG)
    - Services (api, web, cloud-run, database, redis, vercel)
    - Sources (internal, external)
    - Text search in messages
    - User context, endpoints, status codes
    - Infrastructure details (regions, instances, deployments)
    - Time range

    Returns paginated results with metadata.
    """
    try:
        # Build filter object
        filter_obj = LogFilter(
            levels=[LogLevel(level) for level in levels] if levels else None,
            services=(
                [LogServiceType(service) for service in services] if services else None
            ),
            sources=[LogSource(source) for source in sources] if sources else None,
            search_query=search_query,
            user_id=user_id,
            endpoint=endpoint,
            status_codes=status_codes,
            regions=regions,
            instance_ids=instance_ids,
            deployment_ids=deployment_ids,
            page=page,
            page_size=page_size,
        )

        # Set time range
        from datetime import datetime, timedelta

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        filter_obj.start_time = start_time
        filter_obj.end_time = end_time

        # Perform search
        result = await log_service.search_logs(filter_obj)

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter parameter: {str(e)}",
        )
    except RepositoryError as e:
        logger.error(f"Search logs failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search logs",
        )


@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    log_service: LogService = Depends(get_log_service),
    current_user=Depends(get_current_user_optional),
):
    """
    Get log statistics for a time range.

    Returns aggregated statistics including:
    - Count by log level
    - Count by service
    - Count by source
    - Performance metrics
    - Error rates
    """
    try:
        stats = await log_service.get_stats(hours)
        return stats

    except RepositoryError as e:
        logger.error(f"Get stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get log statistics",
        )


@router.get("/dashboard", response_model=LogDashboardResponse)
async def get_dashboard_data(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    log_service: LogService = Depends(get_log_service),
    current_user=Depends(get_current_user_optional),
):
    """
    Get comprehensive dashboard data.

    Returns all data needed for the logging dashboard:
    - Statistics
    - Recent error groupings
    - Time series data for charts
    - Top endpoints by traffic and errors
    - Performance summary
    """
    try:
        dashboard_data = await log_service.get_dashboard_data(hours)
        return dashboard_data

    except RepositoryError as e:
        logger.error(f"Get dashboard data failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data",
        )


@router.get("/{log_id}", response_model=LogEntry)
async def get_log_by_id(
    log_id: str,
    log_service: LogService = Depends(get_log_service),
    current_user=Depends(get_current_user_optional),
):
    """
    Get a single log entry by ID.

    Returns the complete log entry with all context and metadata.
    """
    try:
        log_entry = await log_service.get_log_by_id(log_id)

        if not log_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log entry with ID {log_id} not found",
            )

        return log_entry

    except RepositoryError as e:
        logger.error(f"Get log by ID failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get log entry",
        )


@router.post("/collect")
async def collect_external_logs(
    hours: int = Query(1, ge=1, le=24, description="Hours to look back (1-24)"),
    services: Optional[List[str]] = Query(
        None, description="Specific services to collect from"
    ),
    external_collector: ExternalLogCollectorService = Depends(
        get_external_log_collector
    ),
    current_user=Depends(get_current_user_optional),
):
    """
    Trigger collection of external logs.

    Collects logs from configured external services:
    - Vercel deployments and build logs
    - Upstash Redis metrics
    - Google Cloud Run logs
    - MongoDB Atlas logs

    Returns collection results and statistics.
    """
    try:
        if services:
            # Collect from specific services
            results = {}
            for service_name in services:
                try:
                    service_result = await external_collector.collect_from_service(
                        service_name, hours
                    )
                    results[service_name] = service_result
                except (ValueError, AdapterError) as e:
                    results[service_name] = {
                        "success": False,
                        "error": str(e),
                        "logs_collected": 0,
                    }

            # Calculate summary
            total_logs = sum(
                result.get("logs_collected", 0)
                for result in results.values()
                if result.get("success", False)
            )
            successful_services = sum(
                1 for result in results.values() if result.get("success", False)
            )

            return {
                "message": f"External log collection completed for {len(services)} services",
                "services": results,
                "summary": {
                    "total_logs_collected": total_logs,
                    "successful_services": successful_services,
                    "failed_services": len(services) - successful_services,
                },
            }
        else:
            # Collect from all services
            results = await external_collector.collect_all_logs(hours)

            return {
                "message": "External log collection completed for all services",
                **results,
            }

    except AdapterError as e:
        logger.error(f"External log collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External service error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"External log collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect external logs",
        )


@router.get("/health/external")
async def get_external_health(
    external_collector: ExternalLogCollectorService = Depends(
        get_external_log_collector
    ),
    current_user=Depends(get_current_user_optional),
):
    """
    Get health status of external log collection.

    Tests connections to all external services and returns:
    - Overall health status
    - Individual adapter status
    - Connection test results
    - Recent collection statistics
    """
    try:
        health_data = await external_collector.get_collection_health()
        return health_data

    except Exception as e:
        logger.error(f"Get external health failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get external health status",
        )


@router.post("/cleanup")
async def cleanup_old_logs(
    retention_days: int = Query(30, ge=1, le=365, description="Days to retain logs"),
    log_service: LogService = Depends(get_log_service),
    current_user=Depends(get_current_user_optional),
):
    """
    Clean up old logs based on retention policy.

    Deletes logs older than the specified retention period.
    Different log levels may have different retention policies.

    Note: This operation is irreversible.
    """
    try:
        # Note: In production, this might need admin privileges
        # if current_user and not current_user.is_admin:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Admin privileges required for log cleanup"
        #     )

        cleanup_results = await log_service.cleanup_old_logs(retention_days)

        total_deleted = sum(cleanup_results.values())

        return {
            "message": f"Log cleanup completed: {total_deleted} logs deleted",
            "retention_days": retention_days,
            "deleted_by_level": cleanup_results,
            "total_deleted": total_deleted,
        }

    except RepositoryError as e:
        logger.error(f"Log cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old logs",
        )


@router.get("/count")
async def count_logs(
    # Same filter parameters as search
    levels: Optional[List[str]] = Query(None),
    services: Optional[List[str]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    search_query: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    endpoint: Optional[str] = Query(None),
    status_codes: Optional[List[int]] = Query(None),
    regions: Optional[List[str]] = Query(None),
    instance_ids: Optional[List[str]] = Query(None),
    deployment_ids: Optional[List[str]] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    log_service: LogService = Depends(get_log_service),
    current_user=Depends(get_current_user_optional),
):
    """
    Count logs matching filter criteria.

    Returns the total count of logs matching the specified filters
    without returning the actual log entries.
    """
    try:
        # Build filter object (same as search)
        filter_obj = LogFilter(
            levels=[LogLevel(level) for level in levels] if levels else None,
            services=(
                [LogServiceType(service) for service in services] if services else None
            ),
            sources=[LogSource(source) for source in sources] if sources else None,
            search_query=search_query,
            user_id=user_id,
            endpoint=endpoint,
            status_codes=status_codes,
            regions=regions,
            instance_ids=instance_ids,
            deployment_ids=deployment_ids,
        )

        # Set time range
        from datetime import datetime, timedelta

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        filter_obj.start_time = start_time
        filter_obj.end_time = end_time

        # Count logs
        count = await log_service.count_logs(filter_obj)

        return {"count": count}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter parameter: {str(e)}",
        )
    except RepositoryError as e:
        logger.error(f"Count logs failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count logs",
        )


# === Rate Limiting 로깅 엔드포인트들 ===

@router.get("/rate-limiting/summary", response_model=Dict[str, Any])
async def get_rate_limiting_log_summary(
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 범위 (시간)"),
    log_service: LogService = Depends(get_log_service),
) -> Dict[str, Any]:
    """
    Rate Limiting 관련 로그 요약 정보 조회
    
    Args:
        hours: 조회할 시간 범위
        log_service: 로그 서비스 인스턴스
        
    Returns:
        Rate limiting 로그 통계 및 요약 정보
    """
    try:
        # Rate limiting 관련 로그 필터 생성
        filter_params = LogFilter(
            search_query="rate limit",
            status_codes=[429],  # Too Many Requests
            hours_back=hours,
            page=1,
            limit=1000  # 충분한 데이터 수집을 위해
        )
        
        # Rate limiting 로그 검색
        logs_response = await log_service.search_logs(filter_params)
        
        # 통계 생성
        summary = {
            "total_rate_limit_events": logs_response.total_count,
            "time_range_hours": hours,
            "blocked_requests": 0,
            "top_blocked_endpoints": {},
            "blocked_ips": {},
            "hourly_distribution": {},
            "summary_stats": {}
        }
        
        # 로그 분석
        for log_entry in logs_response.logs:
            # 차단된 요청 수 계산
            if log_entry.status_code == 429:
                summary["blocked_requests"] += 1
                
                # 엔드포인트별 차단 통계
                endpoint = log_entry.endpoint or "unknown"
                summary["top_blocked_endpoints"][endpoint] = summary["top_blocked_endpoints"].get(endpoint, 0) + 1
                
                # IP별 차단 통계 (클라이언트 IP 정보가 있다면)
                client_ip = getattr(log_entry, 'client_ip', None) or getattr(log_entry.metadata, 'client_ip', None) if hasattr(log_entry, 'metadata') else None
                if client_ip:
                    summary["blocked_ips"][client_ip] = summary["blocked_ips"].get(client_ip, 0) + 1
                
                # 시간별 분포 (시간대별)
                hour_key = log_entry.timestamp.strftime("%H:00") if log_entry.timestamp else "unknown"
                summary["hourly_distribution"][hour_key] = summary["hourly_distribution"].get(hour_key, 0) + 1
        
        # 상위 5개 엔드포인트와 IP 추출
        summary["top_blocked_endpoints"] = dict(sorted(summary["top_blocked_endpoints"].items(), key=lambda x: x[1], reverse=True)[:5])
        summary["blocked_ips"] = dict(sorted(summary["blocked_ips"].items(), key=lambda x: x[1], reverse=True)[:5])
        
        # 요약 통계
        summary["summary_stats"] = {
            "avg_blocks_per_hour": summary["blocked_requests"] / hours if hours > 0 else 0,
            "unique_blocked_endpoints": len(summary["top_blocked_endpoints"]),
            "unique_blocked_ips": len(summary["blocked_ips"]),
            "most_blocked_endpoint": max(summary["top_blocked_endpoints"].items(), key=lambda x: x[1])[0] if summary["top_blocked_endpoints"] else None
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Rate limiting 로그 요약 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rate limiting 로그 요약 조회 실패: {str(e)}"
        )


@router.get("/rate-limiting/blocked-requests", response_model=LogListResponse)
async def get_blocked_requests_logs(
    endpoint: Optional[str] = Query(None, description="특정 엔드포인트 필터"),
    client_ip: Optional[str] = Query(None, description="특정 IP 주소 필터"),
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 범위"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=500, description="페이지당 로그 수"),
    log_service: LogService = Depends(get_log_service),
) -> LogListResponse:
    """
    Rate Limiting으로 차단된 요청 로그 조회
    
    Args:
        endpoint: 특정 엔드포인트 필터
        client_ip: 특정 클라이언트 IP 필터
        hours: 조회할 시간 범위
        page: 페이지 번호
        limit: 페이지당 로그 수
        log_service: 로그 서비스 인스턴스
        
    Returns:
        차단된 요청 로그 목록
    """
    try:
        # 검색 쿼리 구성
        search_parts = ["rate limit", "blocked", "429"]
        if endpoint:
            search_parts.append(f"endpoint:{endpoint}")
        if client_ip:
            search_parts.append(f"ip:{client_ip}")
        
        search_query = " ".join(search_parts)
        
        # 필터 생성
        filter_params = LogFilter(
            search_query=search_query,
            status_codes=[429],
            endpoint=endpoint,
            hours_back=hours,
            page=page,
            limit=limit
        )
        
        # 로그 검색
        logs_response = await log_service.search_logs(filter_params)
        
        return logs_response
        
    except Exception as e:
        logger.error(f"차단된 요청 로그 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"차단된 요청 로그 조회 실패: {str(e)}"
        )


@router.get("/rate-limiting/analytics", response_model=Dict[str, Any])
async def get_rate_limiting_analytics(
    days: int = Query(7, ge=1, le=30, description="분석할 일수"),
    log_service: LogService = Depends(get_log_service),
) -> Dict[str, Any]:
    """
    Rate Limiting 로그 분석 및 트렌드 정보
    
    Args:
        days: 분석할 일수
        log_service: 로그 서비스 인스턴스
        
    Returns:
        Rate limiting 트렌드 분석 결과
    """
    try:
        # 일별 Rate limiting 로그 통계 수집
        daily_stats = {}
        endpoint_trends = {}
        
        for day_offset in range(days):
            # 각 날짜별로 24시간 범위로 로그 조회
            filter_params = LogFilter(
                search_query="rate limit",
                status_codes=[429],
                hours_back=24,
                page=1,
                limit=1000
            )
            
            # 해당 날짜의 로그 조회
            logs_response = await log_service.search_logs(filter_params)
            
            # 날짜 키 생성 (오늘로부터 몇일 전)
            day_key = f"day_{day_offset}"
            daily_stats[day_key] = {
                "total_blocks": logs_response.total_count,
                "endpoints": {},
                "peak_hour": None,
                "peak_hour_blocks": 0
            }
            
            # 시간별 분포 및 엔드포인트별 통계
            hourly_blocks = {}
            for log_entry in logs_response.logs:
                endpoint = log_entry.endpoint or "unknown"
                hour = log_entry.timestamp.hour if log_entry.timestamp else 0
                
                # 엔드포인트별 통계
                daily_stats[day_key]["endpoints"][endpoint] = daily_stats[day_key]["endpoints"].get(endpoint, 0) + 1
                
                # 전체 엔드포인트 트렌드
                if endpoint not in endpoint_trends:
                    endpoint_trends[endpoint] = []
                
                # 시간별 통계
                hourly_blocks[hour] = hourly_blocks.get(hour, 0) + 1
            
            # 각 엔드포인트의 일별 데이터 추가
            for endpoint in endpoint_trends:
                endpoint_trends[endpoint].append(daily_stats[day_key]["endpoints"].get(endpoint, 0))
            
            # 피크 시간 찾기
            if hourly_blocks:
                peak_hour = max(hourly_blocks.items(), key=lambda x: x[1])
                daily_stats[day_key]["peak_hour"] = peak_hour[0]
                daily_stats[day_key]["peak_hour_blocks"] = peak_hour[1]
        
        # 트렌드 분석
        total_blocks_trend = [daily_stats[f"day_{i}"]["total_blocks"] for i in range(days)]
        
        # 증가/감소 트렌드 계산
        trend_direction = "stable"
        if len(total_blocks_trend) >= 2:
            recent_avg = sum(total_blocks_trend[:3]) / min(3, len(total_blocks_trend))  # 최근 3일 평균
            older_avg = sum(total_blocks_trend[3:]) / max(1, len(total_blocks_trend) - 3)  # 이전 평균
            
            if recent_avg > older_avg * 1.2:
                trend_direction = "increasing"
            elif recent_avg < older_avg * 0.8:
                trend_direction = "decreasing"
        
        analytics = {
            "period_days": days,
            "daily_statistics": daily_stats,
            "endpoint_trends": endpoint_trends,
            "overall_trend": {
                "direction": trend_direction,
                "total_blocks_series": total_blocks_trend,
                "avg_daily_blocks": sum(total_blocks_trend) / len(total_blocks_trend) if total_blocks_trend else 0,
                "peak_day_blocks": max(total_blocks_trend) if total_blocks_trend else 0,
                "min_day_blocks": min(total_blocks_trend) if total_blocks_trend else 0
            },
            "recommendations": []
        }
        
        # 추천사항 생성
        if trend_direction == "increasing":
            analytics["recommendations"].append("Rate limiting 차단이 증가하고 있습니다. 정책 검토를 권장합니다.")
        
        peak_blocks = max(total_blocks_trend) if total_blocks_trend else 0
        if peak_blocks > 100:
            analytics["recommendations"].append("높은 차단율이 감지되었습니다. DDoS 공격 가능성을 확인하세요.")
            
        # 가장 문제가 되는 엔드포인트 식별
        total_endpoint_blocks = {ep: sum(blocks) for ep, blocks in endpoint_trends.items()}
        if total_endpoint_blocks:
            top_problematic = max(total_endpoint_blocks.items(), key=lambda x: x[1])
            if top_problematic[1] > peak_blocks * 0.5:  # 전체의 50% 이상을 차지하는 엔드포인트
                analytics["recommendations"].append(f"엔드포인트 '{top_problematic[0]}'에서 과도한 차단이 발생하고 있습니다.")
        
        return analytics
        
    except Exception as e:
        logger.error(f"Rate limiting 분석 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rate limiting 분석 실패: {str(e)}"
        )


# Note: Exception handlers are defined at the app level, not router level
# These functions can be used by the main app if needed


async def repository_error_handler(request, exc: RepositoryError):
    """Handle repository errors."""
    logger.error(f"Repository error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operation failed"},
    )


async def adapter_error_handler(request, exc: AdapterError):
    """Handle external adapter errors."""
    logger.error(f"Adapter error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"External service error: {exc.service_name}"},
    )
