"""
모니터링 API 라우터

API 성능 모니터링 데이터를 제공하는 REST API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
import logging

from nadle_backend.services.monitoring_service import MonitoringService, get_monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics", summary="시스템 전체 메트릭 조회")
async def get_system_metrics(
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, Any]:
    """
    시스템 전체 메트릭 조회
    
    Returns:
        - endpoints: 엔드포인트별 요청 수
        - status_codes: 상태코드별 요청 수  
        - timestamp: 조회 시간
    """
    try:
        return await service.get_system_metrics()
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.get("/health", summary="시스템 헬스 상태 조회")
async def get_health_status(
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, Any]:
    """
    시스템 헬스 상태 조회
    
    Returns:
        - status: healthy/warning/critical
        - total_requests: 총 요청 수
        - error_rate: 에러율
        - availability: 가용성
        - timestamp: 조회 시간
    """
    try:
        return await service.get_health_status()
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")


@router.get("/endpoints/{endpoint:path}", summary="특정 엔드포인트 통계 조회")
async def get_endpoint_stats(
    endpoint: str,
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, Any]:
    """
    특정 엔드포인트 통계 조회
    
    Args:
        endpoint: 엔드포인트 (예: "GET:/api/posts")
    
    Returns:
        - avg_response_time: 평균 응답시간
        - min_response_time: 최소 응답시간
        - max_response_time: 최대 응답시간
        - request_count: 요청 수
    """
    try:
        return await service.get_endpoint_stats(endpoint)
    except Exception as e:
        logger.error(f"Failed to get endpoint stats for {endpoint}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats for endpoint {endpoint}")


@router.get("/slow-requests", summary="느린 요청 목록 조회")
async def get_slow_requests(
    limit: int = Query(50, ge=1, le=200, description="조회할 최대 개수"),
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    느린 요청 목록 조회
    
    Args:
        limit: 조회할 최대 개수 (기본값: 50, 최대: 200)
    
    Returns:
        - slow_requests: 느린 요청 목록
            - endpoint: 엔드포인트
            - response_time: 응답시간
            - timestamp: 발생 시간
            - status_code: 상태코드
    """
    try:
        slow_requests = await service.get_slow_requests(limit)
        return {"slow_requests": slow_requests}
    except Exception as e:
        logger.error(f"Failed to get slow requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve slow requests")


@router.get("/timeseries/{endpoint:path}", summary="시간별 시계열 데이터 조회")
async def get_time_series_data(
    endpoint: str,
    minutes: int = Query(60, ge=1, le=1440, description="조회할 시간 범위 (분)"),
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, List]:
    """
    시간별 시계열 데이터 조회
    
    Args:
        endpoint: 엔드포인트 (예: "GET:/api/posts")
        minutes: 조회할 시간 범위 (분, 기본값: 60, 최대: 1440=24시간)
    
    Returns:
        - timestamps: 타임스탬프 목록
        - response_times: 응답시간 목록
    """
    try:
        return await service.get_time_series_data(endpoint, minutes)
    except Exception as e:
        logger.error(f"Failed to get time series data for {endpoint}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve time series data for {endpoint}")


@router.get("/popular-endpoints", summary="인기 엔드포인트 조회")
async def get_popular_endpoints(
    limit: int = Query(10, ge=1, le=50, description="조회할 최대 개수"),
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    인기 엔드포인트 조회
    
    Args:
        limit: 조회할 최대 개수 (기본값: 10, 최대: 50)
    
    Returns:
        - popular_endpoints: 인기 엔드포인트 목록
            - endpoint: 엔드포인트
            - requests: 요청 수
    """
    try:
        popular_endpoints = await service.get_popular_endpoints(limit)
        return {"popular_endpoints": popular_endpoints}
    except Exception as e:
        logger.error(f"Failed to get popular endpoints: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve popular endpoints")


@router.get("/summary", summary="요약 대시보드 데이터 조회")
async def get_monitoring_summary(
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, Any]:
    """
    모니터링 요약 대시보드 데이터 조회
    
    대시보드에 필요한 주요 메트릭들을 한 번에 조회합니다.
    
    Returns:
        - health: 헬스 상태
        - aggregated_metrics: 집계 메트릭
        - popular_endpoints: 상위 5개 인기 엔드포인트
        - recent_slow_requests: 최근 10개 느린 요청
    """
    try:
        # 병렬로 여러 데이터 조회
        import asyncio
        
        health_task = service.get_health_status()
        aggregated_task = service.get_aggregated_metrics()
        popular_task = service.get_popular_endpoints(5)
        slow_requests_task = service.get_slow_requests(10)
        
        health, aggregated, popular, slow_requests = await asyncio.gather(
            health_task,
            aggregated_task,
            popular_task,
            slow_requests_task,
            return_exceptions=True
        )
        
        # 에러가 발생한 경우 기본값 사용
        if isinstance(health, Exception):
            logger.error(f"Failed to get health status: {health}")
            health = {"status": "unknown", "error": str(health)}
        
        if isinstance(aggregated, Exception):
            logger.error(f"Failed to get aggregated metrics: {aggregated}")
            aggregated = {"total_requests": 0, "success_rate": 0}
        
        if isinstance(popular, Exception):
            logger.error(f"Failed to get popular endpoints: {popular}")
            popular = []
        
        if isinstance(slow_requests, Exception):
            logger.error(f"Failed to get slow requests: {slow_requests}")
            slow_requests = []
        
        return {
            "health": health,
            "aggregated_metrics": aggregated,
            "popular_endpoints": popular,
            "recent_slow_requests": slow_requests
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring summary")


@router.get("/dashboard", summary="실시간 대시보드 데이터")
async def get_dashboard_data(
    service: MonitoringService = Depends(get_monitoring_service)
) -> Dict[str, Any]:
    """
    실시간 대시보드용 데이터 조회
    
    프론트엔드 대시보드에서 사용할 실시간 데이터를 제공합니다.
    
    Returns:
        모든 주요 모니터링 데이터를 포함한 종합 정보
    """
    try:
        # 모든 주요 데이터를 병렬로 조회
        import asyncio
        
        tasks = {
            "metrics": service.get_system_metrics(),
            "health": service.get_health_status(),
            "popular_endpoints": service.get_popular_endpoints(10),
            "slow_requests": service.get_slow_requests(20)
        }
        
        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logger.error(f"Failed to get {key}: {e}")
                results[key] = None
        
        return {
            "timestamp": __import__("time").time(),
            "status": "success",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")