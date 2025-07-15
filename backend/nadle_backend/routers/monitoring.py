"""
HetrixTools 모니터링 API 라우터

업타임 모니터링, 헬스체크, 모니터 관리를 위한 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.hetrix_monitoring import (
    HetrixMonitoringService, 
    HealthCheckService,
    Monitor,
    UptimeStatus
)
from ..config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


def get_hetrix_service() -> HetrixMonitoringService:
    """HetrixMonitoringService 의존성 주입"""
    settings = get_settings()
    if not settings.hetrixtools_api_token:
        raise HTTPException(
            status_code=503, 
            detail="HetrixTools API 토큰이 설정되지 않았습니다"
        )
    return HetrixMonitoringService(api_token=settings.hetrixtools_api_token)


def get_health_service() -> HealthCheckService:
    """HealthCheckService 의존성 주입"""
    return HealthCheckService()


@router.get("/status")
async def monitoring_status() -> Dict[str, Any]:
    """모니터링 시스템 전체 상태 조회"""
    try:
        health_service = get_health_service()
        
        # 간단한 헬스체크와 HetrixTools 상태 확인
        simple_health = await health_service.simple_health_check()
        hetrix_health = await health_service._check_hetrix_monitoring()
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_service": "hetrixtools",
            "api_health": simple_health,
            "hetrix_monitoring": hetrix_health
        }
        
    except Exception as e:
        logger.error(f"모니터링 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


@router.get("/hetrix/monitors")
async def get_monitors(
    environment: Optional[str] = Query(None, description="환경 필터 (production, staging)"),
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service)
) -> Dict[str, Any]:
    """HetrixTools 모니터 목록 조회"""
    try:
        async with hetrix_service as service:
            if environment:
                # 특정 환경의 모니터만 조회
                monitors = await service.client.get_monitors_by_environment(environment)
                logger.info(f"환경 '{environment}'의 모니터 {len(monitors)}개 조회")
            else:
                # 모든 모니터 조회
                monitors = await service.get_monitors_async()
                logger.info(f"전체 모니터 {len(monitors)}개 조회")
            
            # Monitor 객체를 dict로 변환
            monitors_data = []
            for monitor in monitors:
                monitors_data.append({
                    "id": monitor.id,
                    "name": monitor.name,
                    "url": monitor.url,
                    "status": monitor.status.value,
                    "uptime": monitor.uptime,
                    "monitor_type": monitor.monitor_type,
                    "created_at": monitor.created_at,
                    "last_check": monitor.last_check,
                    "last_status_change": monitor.last_status_change,
                    "response_time": monitor.response_time,
                    "locations": monitor.locations
                })
            
            return {
                "total": len(monitors_data),
                "environment": environment or "all",
                "monitors": monitors_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"모니터 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모니터 목록 조회 실패: {str(e)}")


@router.get("/hetrix/monitors/{monitor_id}")
async def get_monitor_by_id(
    monitor_id: str,
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service)
) -> Dict[str, Any]:
    """특정 모니터 상세 정보 조회"""
    try:
        async with hetrix_service as service:
            monitor = await service.client.get_monitor_by_id(monitor_id)
            
            if not monitor:
                raise HTTPException(status_code=404, detail=f"모니터 ID '{monitor_id}'를 찾을 수 없습니다")
            
            return {
                "monitor": {
                    "id": monitor.id,
                    "name": monitor.name,
                    "url": monitor.url,
                    "status": monitor.status.value,
                    "uptime": monitor.uptime,
                    "monitor_type": monitor.monitor_type,
                    "created_at": monitor.created_at,
                    "last_check": monitor.last_check,
                    "last_status_change": monitor.last_status_change,
                    "response_time": monitor.response_time,
                    "locations": monitor.locations
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모니터 조회 실패 (ID: {monitor_id}): {e}")
        raise HTTPException(status_code=500, detail=f"모니터 조회 실패: {str(e)}")


@router.get("/hetrix/monitors/name/{monitor_name}")
async def get_monitor_by_name(
    monitor_name: str,
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service)
) -> Dict[str, Any]:
    """모니터 이름으로 특정 모니터 조회"""
    try:
        async with hetrix_service as service:
            monitor = await service.client.get_monitor_by_name(monitor_name)
            
            if not monitor:
                raise HTTPException(status_code=404, detail=f"모니터 '{monitor_name}'를 찾을 수 없습니다")
            
            return {
                "monitor": {
                    "id": monitor.id,
                    "name": monitor.name,
                    "url": monitor.url,
                    "status": monitor.status.value,
                    "uptime": monitor.uptime,
                    "monitor_type": monitor.monitor_type,
                    "created_at": monitor.created_at,
                    "last_check": monitor.last_check,
                    "last_status_change": monitor.last_status_change,
                    "response_time": monitor.response_time,
                    "locations": monitor.locations
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모니터 조회 실패 (이름: {monitor_name}): {e}")
        raise HTTPException(status_code=500, detail=f"모니터 조회 실패: {str(e)}")


@router.get("/hetrix/current-environment")
async def get_current_environment_monitors(
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service)
) -> Dict[str, Any]:
    """현재 환경의 모니터 목록 조회"""
    try:
        async with hetrix_service as service:
            monitors = await service.get_current_environment_monitors()
            
            # Monitor 객체를 dict로 변환
            monitors_data = []
            for monitor in monitors:
                monitors_data.append({
                    "id": monitor.id,
                    "name": monitor.name,
                    "url": monitor.url,
                    "status": monitor.status.value,
                    "uptime": monitor.uptime,
                    "monitor_type": monitor.monitor_type,
                    "created_at": monitor.created_at,
                    "last_check": monitor.last_check,
                    "last_status_change": monitor.last_status_change,
                    "response_time": monitor.response_time,
                    "locations": monitor.locations
                })
            
            settings = get_settings()
            current_env = getattr(settings, 'environment', 'development')
            
            return {
                "environment": current_env,
                "total": len(monitors_data),
                "monitors": monitors_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"현재 환경 모니터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"현재 환경 모니터 조회 실패: {str(e)}")


@router.get("/hetrix/logs/{monitor_id}")
async def get_monitor_logs(
    monitor_id: str,
    days: int = Query(1, ge=1, le=30, description="조회할 일수 (1-30일)"),
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service)
) -> Dict[str, Any]:
    """모니터 로그 조회 (현재 HetrixTools v3 API에서 미지원)"""
    try:
        async with hetrix_service as service:
            logs = await service.client.get_monitor_logs(monitor_id, days)
            
            return {
                "monitor_id": monitor_id,
                "days": days,
                "logs": logs,
                "total": len(logs),
                "note": "HetrixTools v3 API에서 로그 조회 기능이 현재 미지원됩니다",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"모니터 로그 조회 실패 (ID: {monitor_id}): {e}")
        raise HTTPException(status_code=500, detail=f"모니터 로그 조회 실패: {str(e)}")


@router.get("/health/comprehensive")
async def comprehensive_health_check(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """종합 헬스체크 (데이터베이스, Redis, 외부 API, HetrixTools 포함)"""
    try:
        result = await health_service.comprehensive_health_check()
        return result
        
    except Exception as e:
        logger.error(f"종합 헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"종합 헬스체크 실패: {str(e)}")


@router.get("/health/simple")
async def simple_health_check(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """간단한 헬스체크 (외부 모니터링 서비스용)"""
    try:
        result = await health_service.simple_health_check()
        return result
        
    except Exception as e:
        logger.error(f"간단한 헬스체크 실패: {e}")
        # 간단한 헬스체크는 실패하더라도 기본 응답 반환
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "nadle-backend-api",
            "error": str(e),
            "monitoring_service": "hetrixtools"
        }


@router.get("/summary")
async def monitoring_summary(
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """모니터링 시스템 요약 정보"""
    try:
        # 모든 모니터 조회
        async with hetrix_service as service:
            all_monitors = await service.get_monitors_async()
            
        # 상태별 집계
        status_counts = {}
        total_uptime = 0
        for monitor in all_monitors:
            status = monitor.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            total_uptime += monitor.uptime
        
        avg_uptime = total_uptime / len(all_monitors) if all_monitors else 0
        
        # HetrixTools 모니터링 상태
        hetrix_health = await health_service._check_hetrix_monitoring()
        
        return {
            "total_monitors": len(all_monitors),
            "status_breakdown": status_counts,
            "average_uptime": round(avg_uptime, 2),
            "hetrix_api_status": hetrix_health.get("status", "unknown"),
            "monitoring_service": "hetrixtools_v3",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"모니터링 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모니터링 요약 조회 실패: {str(e)}")


# 기존 UptimeRobot 호환성을 위한 별칭 엔드포인트들
@router.get("/uptime/monitors", deprecated=True)
async def get_uptime_monitors_legacy(
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service)
) -> Dict[str, Any]:
    """기존 UptimeRobot API 호환성을 위한 엔드포인트 (deprecated)"""
    logger.warning("레거시 /uptime/monitors 엔드포인트 사용됨. /hetrix/monitors 사용 권장")
    
    try:
        async with hetrix_service as service:
            monitors = await service.get_monitors_async()
            
            # UptimeRobot 형식으로 변환
            uptime_monitors = []
            for monitor in monitors:
                uptime_monitors.append({
                    "id": monitor.id,
                    "friendly_name": monitor.name,
                    "url": monitor.url,
                    "status": 2 if monitor.status == UptimeStatus.UP else 1,  # UptimeRobot 형식
                    "type": 1,  # HTTP(s)
                    "create_datetime": str(monitor.created_at)
                })
            
            return {
                "stat": "ok",
                "monitors": uptime_monitors
            }
            
    except Exception as e:
        logger.error(f"레거시 모니터 목록 조회 실패: {e}")
        return {
            "stat": "fail",
            "error": {
                "type": "api_error",
                "message": str(e)
            }
        }