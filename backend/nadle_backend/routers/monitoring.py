"""
통합 모니터링 API 라우터

HetrixTools 업타임 모니터링과 인프라 모니터링(Cloud Run, Vercel, Atlas, Upstash)을 
통합하여 제공하는 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# 기존 HetrixTools 모니터링
from ..services.hetrix_monitoring import (
    HetrixMonitoringService, 
    HealthCheckService,
    Monitor,
    UptimeStatus
)

# 새로운 인프라 모니터링
from ..services.monitoring import UnifiedMonitoringService
from ..models.monitoring import (
    InfrastructureType,
    ServiceStatus,
    UnifiedMonitoringResponse,
    HealthCheckResponse
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


def get_unified_monitoring_service() -> UnifiedMonitoringService:
    """UnifiedMonitoringService 의존성 주입"""
    return UnifiedMonitoringService()


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


# === 새로운 인프라 모니터링 엔드포인트들 ===

@router.get("/infrastructure/status", response_model=UnifiedMonitoringResponse)
async def get_infrastructure_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> UnifiedMonitoringResponse:
    """모든 인프라의 통합 상태 조회"""
    try:
        logger.info("인프라 통합 상태 조회 요청")
        result = await unified_service.get_all_infrastructure_status()
        logger.info(f"인프라 통합 상태 조회 완료: {result.infrastructure_count}개 서비스")
        return result
        
    except Exception as e:
        logger.error(f"인프라 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인프라 상태 조회 실패: {str(e)}")


@router.get("/infrastructure/health", response_model=HealthCheckResponse)
async def infrastructure_health_check(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> HealthCheckResponse:
    """인프라 통합 헬스체크 (빠른 상태 확인)"""
    try:
        logger.info("인프라 헬스체크 요청")
        result = await unified_service.health_check()
        logger.info(f"인프라 헬스체크 완료: {result.status.value}")
        return result
        
    except Exception as e:
        logger.error(f"인프라 헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인프라 헬스체크 실패: {str(e)}")


@router.get("/infrastructure/services")
async def get_configured_services(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> Dict[str, Any]:
    """설정된 인프라 서비스 목록 조회"""
    try:
        configured_services = unified_service.get_configured_services()
        
        return {
            "total_services": len(configured_services),
            "configured_services": [service.value for service in configured_services],
            "service_details": {
                service.value: {
                    "name": service.value.replace('_', ' ').title(),
                    "type": service.value
                }
                for service in configured_services
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"설정된 서비스 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서비스 목록 조회 실패: {str(e)}")


@router.get("/infrastructure/{infrastructure_type}/metrics")
async def get_service_metrics(
    infrastructure_type: InfrastructureType,
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> Dict[str, Any]:
    """특정 인프라 서비스의 상세 메트릭 조회"""
    try:
        logger.info(f"{infrastructure_type.value} 메트릭 조회 요청")
        
        metrics = await unified_service.get_service_metrics(infrastructure_type)
        
        if metrics is None:
            raise HTTPException(
                status_code=404, 
                detail=f"{infrastructure_type.value} 서비스가 설정되지 않았거나 메트릭을 가져올 수 없습니다"
            )
        
        # 메트릭을 딕셔너리로 변환
        metrics_dict = metrics.dict() if hasattr(metrics, 'dict') else metrics.__dict__
        
        result = {
            "infrastructure_type": infrastructure_type.value,
            "metrics": metrics_dict,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"{infrastructure_type.value} 메트릭 조회 완료")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{infrastructure_type.value} 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메트릭 조회 실패: {str(e)}")


@router.get("/infrastructure/cloud-run/status")
async def get_cloud_run_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> Dict[str, Any]:
    """Google Cloud Run 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(InfrastructureType.CLOUD_RUN)
        
        if metrics is None:
            raise HTTPException(status_code=404, detail="Cloud Run 서비스가 설정되지 않았습니다")
        
        return {
            "service": "cloud_run",
            "status": metrics.status.value,
            "service_name": metrics.service_name,
            "region": metrics.region,
            "metrics": {
                "cpu_utilization": metrics.cpu_utilization,
                "memory_utilization": metrics.memory_utilization,
                "instance_count": metrics.instance_count,
                "request_count": metrics.request_count,
                "response_time_ms": metrics.response_time_ms
            },
            "timestamp": metrics.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cloud Run 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Cloud Run 상태 조회 실패: {str(e)}")


@router.get("/infrastructure/vercel/status")
async def get_vercel_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> Dict[str, Any]:
    """Vercel 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(InfrastructureType.VERCEL)
        
        if metrics is None:
            raise HTTPException(status_code=404, detail="Vercel 서비스가 설정되지 않았습니다")
        
        return {
            "service": "vercel",
            "status": metrics.status.value,
            "project_id": metrics.project_id,
            "deployment_status": metrics.deployment_status,
            "metrics": {
                "deployment_url": metrics.deployment_url,
                "function_invocations": metrics.function_invocations,
                "core_web_vitals_score": metrics.core_web_vitals_score,
                "response_time_ms": metrics.response_time_ms
            },
            "timestamp": metrics.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vercel 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Vercel 상태 조회 실패: {str(e)}")


@router.get("/infrastructure/atlas/status")
async def get_atlas_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> Dict[str, Any]:
    """MongoDB Atlas 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(InfrastructureType.MONGODB_ATLAS)
        
        if metrics is None:
            raise HTTPException(status_code=404, detail="MongoDB Atlas 서비스가 설정되지 않았습니다")
        
        return {
            "service": "mongodb_atlas",
            "status": metrics.status.value,
            "cluster_name": metrics.cluster_name,
            "cluster_type": metrics.cluster_type,
            "metrics": {
                "connections_current": metrics.connections_current,
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "memory_usage_percent": metrics.memory_usage_percent,
                "operations_per_second": metrics.operations_per_second,
                "response_time_ms": metrics.response_time_ms
            },
            "timestamp": metrics.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MongoDB Atlas 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"MongoDB Atlas 상태 조회 실패: {str(e)}")


@router.get("/infrastructure/upstash/status")
async def get_upstash_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service)
) -> Dict[str, Any]:
    """Upstash Redis 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(InfrastructureType.UPSTASH_REDIS)
        
        if metrics is None:
            raise HTTPException(status_code=404, detail="Upstash Redis 서비스가 설정되지 않았습니다")
        
        return {
            "service": "upstash_redis",
            "status": metrics.status.value,
            "database_id": metrics.database_id,
            "database_name": metrics.database_name,
            "metrics": {
                "hit_rate": metrics.hit_rate,
                "memory_usage_percent": metrics.memory_usage_percent,
                "connection_count": metrics.connection_count,
                "operations_per_second": metrics.operations_per_second,
                "response_time_ms": metrics.response_time_ms
            },
            "timestamp": metrics.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upstash Redis 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Upstash Redis 상태 조회 실패: {str(e)}")