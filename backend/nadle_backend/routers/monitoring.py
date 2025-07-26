"""
통합 모니터링 API 라우터

HetrixTools 업타임 모니터링과 인프라 모니터링(Cloud Run, Vercel, Upstash)을
통합하여 제공하는 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime

# 기존 HetrixTools 모니터링
from ..services.hetrix_monitoring import (
    HetrixMonitoringService,
    HealthCheckService,
    Monitor,
    UptimeStatus,
)

# 새로운 인프라 모니터링
from ..services.monitoring import UnifiedMonitoringService
from ..models.monitoring import (
    InfrastructureType,
    ServiceStatus,
    UnifiedMonitoringResponse,
    HealthCheckResponse,
)

# 새로운 Sentry 및 엔드포인트 모니터링
from ..services.sentry_monitoring_service import SentryMonitoringService
from ..services.endpoint_monitoring_service import EndpointMonitoringService

from ..config import get_settings
from ..logging.dependencies import get_log_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])



def get_hetrix_service() -> HetrixMonitoringService:
    """HetrixMonitoringService 의존성 주입"""
    settings = get_settings()
    if not settings.hetrixtools_api_token:
        raise HTTPException(
            status_code=503, detail="HetrixTools API 토큰이 설정되지 않았습니다"
        )
    return HetrixMonitoringService(api_token=settings.hetrixtools_api_token)


def get_health_service() -> HealthCheckService:
    """HealthCheckService 의존성 주입"""
    return HealthCheckService()


def get_unified_monitoring_service() -> UnifiedMonitoringService:
    """UnifiedMonitoringService 의존성 주입"""
    return UnifiedMonitoringService()


async def get_sentry_monitoring_service() -> SentryMonitoringService:
    """SentryMonitoringService 의존성 주입 - LogService 연계"""
    try:
        # 직접 LogService를 생성해서 주입
        from ..database.connection import get_database
        from ..logging.repositories.mongo_log_repository import MongoLogRepository
        from ..logging.services.log_service import LogService
        
        db = await get_database()
        repository = MongoLogRepository(db)
        
        # 인덱스가 이미 있는지 확인하고 없으면 생성
        try:
            await repository.setup_indexes()
        except Exception:
            # 인덱스가 이미 존재하면 무시
            pass
        
        log_service = LogService(repository, cache_service=None)
        
        return SentryMonitoringService(log_service=log_service)
    except Exception as e:
        logger.error(f"SentryMonitoringService 초기화 실패: {e}")
        # LogService 없이라도 기본 기능은 제공
        return SentryMonitoringService(log_service=None)


def get_endpoint_monitoring_service() -> EndpointMonitoringService:
    """EndpointMonitoringService 의존성 주입"""
    return EndpointMonitoringService()


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
            "hetrix_monitoring": hetrix_health,
        }

    except Exception as e:
        logger.error(f"모니터링 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


@router.get("/hetrix/monitors")
async def get_monitors(
    environment: Optional[str] = Query(
        None, description="환경 필터 (development, staging, production)"
    ),
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
) -> Dict[str, Any]:
    """HetrixTools 모니터 목록 조회"""
    # 환경 검증
    if environment:
        valid_environments = ["development", "staging", "production"]
        if environment not in valid_environments:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 환경입니다. 사용 가능한 환경: {', '.join(valid_environments)}",
            )

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
                monitors_data.append(
                    {
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
                        "locations": monitor.locations,
                    }
                )

            return {
                "total": len(monitors_data),
                "environment": environment or "all",
                "monitors": monitors_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"모니터 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모니터 목록 조회 실패: {str(e)}")


@router.get("/hetrix/monitors/{monitor_id}")
async def get_monitor_by_id(
    monitor_id: str,
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
) -> Dict[str, Any]:
    """특정 모니터 상세 정보 조회"""
    try:
        async with hetrix_service as service:
            monitor = await service.client.get_monitor_by_id(monitor_id)

            if not monitor:
                raise HTTPException(
                    status_code=404,
                    detail=f"모니터 ID '{monitor_id}'를 찾을 수 없습니다",
                )

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
                    "locations": monitor.locations,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모니터 조회 실패 (ID: {monitor_id}): {e}")
        raise HTTPException(status_code=500, detail=f"모니터 조회 실패: {str(e)}")


@router.get("/hetrix/monitors/name/{monitor_name}")
async def get_monitor_by_name(
    monitor_name: str,
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
) -> Dict[str, Any]:
    """모니터 이름으로 특정 모니터 조회"""
    try:
        async with hetrix_service as service:
            monitor = await service.client.get_monitor_by_name(monitor_name)

            if not monitor:
                raise HTTPException(
                    status_code=404,
                    detail=f"모니터 '{monitor_name}'를 찾을 수 없습니다",
                )

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
                    "locations": monitor.locations,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모니터 조회 실패 (이름: {monitor_name}): {e}")
        raise HTTPException(status_code=500, detail=f"모니터 조회 실패: {str(e)}")


@router.get("/hetrix/current-environment")
async def get_current_environment_monitors(
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
) -> Dict[str, Any]:
    """현재 환경의 모니터 목록 조회"""
    try:
        async with hetrix_service as service:
            monitors = await service.get_current_environment_monitors()

            # Monitor 객체를 dict로 변환
            monitors_data = []
            for monitor in monitors:
                monitors_data.append(
                    {
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
                        "locations": monitor.locations,
                    }
                )

            settings = get_settings()
            current_env = getattr(settings, "environment", "development")

            return {
                "environment": current_env,
                "total": len(monitors_data),
                "monitors": monitors_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"현재 환경 모니터 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"현재 환경 모니터 조회 실패: {str(e)}"
        )


@router.get("/hetrix/logs/{monitor_id}")
async def get_monitor_logs(
    monitor_id: str,
    days: int = Query(1, ge=1, le=30, description="조회할 일수 (1-30일)"),
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
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
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"모니터 로그 조회 실패 (ID: {monitor_id}): {e}")
        raise HTTPException(status_code=500, detail=f"모니터 로그 조회 실패: {str(e)}")


@router.get("/health/comprehensive")
async def comprehensive_health_check(
    health_service: HealthCheckService = Depends(get_health_service),
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
    health_service: HealthCheckService = Depends(get_health_service),
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
            "monitoring_service": "hetrixtools",
        }


@router.get("/summary")
async def monitoring_summary(
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
    health_service: HealthCheckService = Depends(get_health_service),
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
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"모니터링 요약 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"모니터링 요약 조회 실패: {str(e)}"
        )


# 기존 UptimeRobot 호환성을 위한 별칭 엔드포인트들
@router.get("/uptime/monitors", deprecated=True)
async def get_uptime_monitors_legacy(
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
) -> Dict[str, Any]:
    """기존 UptimeRobot API 호환성을 위한 엔드포인트 (deprecated)"""
    logger.warning(
        "레거시 /uptime/monitors 엔드포인트 사용됨. /hetrix/monitors 사용 권장"
    )

    try:
        async with hetrix_service as service:
            monitors = await service.get_monitors_async()

            # UptimeRobot 형식으로 변환
            uptime_monitors = []
            for monitor in monitors:
                uptime_monitors.append(
                    {
                        "id": monitor.id,
                        "friendly_name": monitor.name,
                        "url": monitor.url,
                        "status": (
                            2 if monitor.status == UptimeStatus.UP else 1
                        ),  # UptimeRobot 형식
                        "type": 1,  # HTTP(s)
                        "create_datetime": str(monitor.created_at),
                    }
                )

            return {"stat": "ok", "monitors": uptime_monitors}

    except Exception as e:
        logger.error(f"레거시 모니터 목록 조회 실패: {e}")
        return {"stat": "fail", "error": {"type": "api_error", "message": str(e)}}


# === 새로운 인프라 모니터링 엔드포인트들 ===


@router.get("/infrastructure/status", response_model=UnifiedMonitoringResponse)
async def get_infrastructure_status(
    environment: Optional[str] = Query(
        None, description="환경 필터 (development, staging, production)"
    ),
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
) -> UnifiedMonitoringResponse:
    """모든 인프라의 통합 상태 조회"""
    # 환경 검증
    if environment:
        valid_environments = ["development", "staging", "production"]
        if environment not in valid_environments:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 환경입니다. 사용 가능한 환경: {', '.join(valid_environments)}",
            )

    try:
        logger.info(f"인프라 통합 상태 조회 요청 (환경: {environment or 'all'})")
        result = await unified_service.get_all_infrastructure_status()

        # 환경 정보를 응답에 추가
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        elif hasattr(result, "dict"):
            result_dict = result.dict()
        else:
            result_dict = result.__dict__

        result_dict["environment"] = environment or "all"

        logger.info(
            f"인프라 통합 상태 조회 완료: {result.infrastructure_count}개 서비스"
        )
        return result_dict

    except Exception as e:
        logger.error(f"인프라 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"인프라 상태 조회 실패: {str(e)}")


@router.get("/infrastructure/health", response_model=HealthCheckResponse)
async def infrastructure_health_check(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
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
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
) -> Dict[str, Any]:
    """설정된 인프라 서비스 목록 조회"""
    try:
        configured_services = unified_service.get_configured_services()

        return {
            "total_services": len(configured_services),
            "configured_services": [service.value for service in configured_services],
            "service_details": {
                service.value: {
                    "name": service.value.replace("_", " ").title(),
                    "type": service.value,
                }
                for service in configured_services
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"설정된 서비스 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서비스 목록 조회 실패: {str(e)}")


@router.get("/infrastructure/{infrastructure_type}/metrics")
async def get_service_metrics(
    infrastructure_type: InfrastructureType,
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
) -> Dict[str, Any]:
    """특정 인프라 서비스의 상세 메트릭 조회"""
    try:
        logger.info(f"{infrastructure_type.value} 메트릭 조회 요청")

        metrics = await unified_service.get_service_metrics(infrastructure_type)

        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"{infrastructure_type.value} 서비스가 설정되지 않았거나 메트릭을 가져올 수 없습니다",
            )

        # 메트릭을 딕셔너리로 변환
        metrics_dict = metrics.dict() if hasattr(metrics, "dict") else metrics.__dict__

        result = {
            "infrastructure_type": infrastructure_type.value,
            "metrics": metrics_dict,
            "timestamp": datetime.utcnow().isoformat(),
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
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
) -> Dict[str, Any]:
    """Google Cloud Run 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(
            InfrastructureType.CLOUD_RUN
        )

        if metrics is None:
            raise HTTPException(
                status_code=404, detail="Cloud Run 서비스가 설정되지 않았습니다"
            )

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
                "response_time_ms": metrics.response_time_ms,
            },
            "timestamp": metrics.timestamp.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cloud Run 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cloud Run 상태 조회 실패: {str(e)}"
        )


@router.get("/infrastructure/vercel/status")
async def get_vercel_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
) -> Dict[str, Any]:
    """Vercel 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(InfrastructureType.VERCEL)

        if metrics is None:
            raise HTTPException(
                status_code=404, detail="Vercel 서비스가 설정되지 않았습니다"
            )

        return {
            "service": "vercel",
            "status": metrics.status.value,
            "project_id": metrics.project_id,
            "deployment_status": metrics.deployment_status,
            "metrics": {
                "deployment_url": metrics.deployment_url,
                "function_invocations": metrics.function_invocations,
                "core_web_vitals_score": metrics.core_web_vitals_score,
                "response_time_ms": metrics.response_time_ms,
            },
            "timestamp": metrics.timestamp.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vercel 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Vercel 상태 조회 실패: {str(e)}")




@router.get("/infrastructure/upstash/status")
async def get_upstash_status(
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
) -> Dict[str, Any]:
    """Upstash Redis 상태 조회"""
    try:
        metrics = await unified_service.get_service_metrics(
            InfrastructureType.UPSTASH_REDIS
        )

        if metrics is None:
            raise HTTPException(
                status_code=404, detail="Upstash Redis 서비스가 설정되지 않았습니다"
            )

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
                "response_time_ms": metrics.response_time_ms,
            },
            "timestamp": metrics.timestamp.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upstash Redis 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"Upstash Redis 상태 조회 실패: {str(e)}"
        )


# === 새로운 통합 API들 ===


@router.get("/environments")
async def get_environments() -> Dict[str, Any]:
    """사용 가능한 환경 목록 조회"""
    return {
        "environments": ["development", "staging", "production"],
        "default": "production",
        "description": "모니터링 가능한 환경 목록",
    }


@router.get("/dashboard/{environment}")
async def get_unified_dashboard(
    environment: str,
    hetrix_service: HetrixMonitoringService = Depends(get_hetrix_service),
    unified_service: UnifiedMonitoringService = Depends(get_unified_monitoring_service),
    health_service: HealthCheckService = Depends(get_health_service),
) -> Dict[str, Any]:
    """환경별 통합 대시보드 API - 모든 모니터링 데이터를 하나의 엔드포인트에서 제공"""

    # 환경 검증
    valid_environments = ["development", "staging", "production"]
    if environment not in valid_environments:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 환경입니다. 사용 가능한 환경: {', '.join(valid_environments)}",
        )

    try:
        logger.info(f"환경 '{environment}' 통합 대시보드 조회 시작")

        # 1. 외부 모니터링 (HetrixTools)
        external_monitoring = {}
        try:
            async with hetrix_service as service:
                monitors = await service.client.get_monitors_by_environment(environment)

                monitors_data = []
                for monitor in monitors:
                    monitors_data.append(
                        {
                            "id": monitor.id,
                            "name": monitor.name,
                            "url": monitor.url,
                            "status": monitor.status.value,
                            "uptime": monitor.uptime,
                            "response_time": monitor.response_time,
                            "last_check": monitor.last_check,
                        }
                    )

                external_monitoring = {
                    "service": "hetrixtools",
                    "total_monitors": len(monitors_data),
                    "monitors": monitors_data,
                }

        except Exception as e:
            logger.warning(f"외부 모니터링 조회 실패: {e}")
            external_monitoring = {
                "service": "hetrixtools",
                "error": str(e),
                "total_monitors": 0,
                "monitors": [],
            }

        # 2. 애플리케이션 모니터링 (헬스체크)
        application_monitoring = {}
        try:
            health_result = await health_service.simple_health_check()
            application_monitoring = {
                "health_status": health_result.get("status", "unknown"),
                "service": health_result.get("service", "nadle-backend-api"),
                "timestamp": health_result.get(
                    "timestamp", datetime.utcnow().isoformat()
                ),
            }
        except Exception as e:
            logger.warning(f"애플리케이션 모니터링 조회 실패: {e}")
            application_monitoring = {
                "health_status": "unhealthy",
                "error": str(e),
                "service": "nadle-backend-api",
            }

        # 3. 인프라 모니터링 (4개 서비스)
        infrastructure_monitoring = {}
        try:
            infra_result = await unified_service.get_all_infrastructure_status()
            # Pydantic 모델을 딕셔너리로 변환
            if hasattr(infra_result, "model_dump"):
                infrastructure_monitoring = infra_result.model_dump()
            elif hasattr(infra_result, "dict"):
                infrastructure_monitoring = infra_result.dict()
            else:
                infrastructure_monitoring = infra_result.__dict__
        except Exception as e:
            logger.warning(f"인프라 모니터링 조회 실패: {e}")
            infrastructure_monitoring = {"error": str(e), "services": {}}

        # 4. Rate Limiting 모니터링 추가
        rate_limiting_monitoring = {}
        try:
            from ..middleware.monitoring import PerformanceTracker
            from ..database.redis_factory import get_redis_manager
            
            # Redis 클라이언트 가져오기
            redis_manager = await get_redis_manager()
            
            # 다양한 Redis 클라이언트 속성 시도
            redis_client = (
                getattr(redis_manager, 'redis_client', None) or 
                getattr(redis_manager, 'client', None) or
                redis_manager
            )
            
            if redis_client:
                # PerformanceTracker 인스턴스 생성
                tracker = PerformanceTracker(redis_client)
                
                # Rate limiting 요약 정보 조회
                rate_limiting_summary = await tracker.get_rate_limit_summary()
                rate_limiting_monitoring = {
                    "service": "rate_limiting",
                    "status": rate_limiting_summary.get("status", "unknown"),
                    "total_blocks_24h": rate_limiting_summary.get("total_blocks_24h", 0),
                    "recent_hour_blocks": rate_limiting_summary.get("recent_hour_blocks", 0),
                    "overall_block_rate": rate_limiting_summary.get("overall_block_rate", 0.0),
                    "top_blocked_endpoints": rate_limiting_summary.get("top_blocked_endpoints", [])[:3]  # 상위 3개만
                }
            else:
                rate_limiting_monitoring = {
                    "service": "rate_limiting",
                    "status": "unavailable",
                    "error": "Redis 연결 불가"
                }
                
        except Exception as e:
            logger.warning(f"Rate Limiting 모니터링 조회 실패: {e}")
            rate_limiting_monitoring = {
                "service": "rate_limiting",
                "status": "error",
                "error": str(e)
            }

        # 통합 응답 구성
        response = {
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat(),
            "external_monitoring": external_monitoring,
            "application_monitoring": application_monitoring,
            "infrastructure_monitoring": infrastructure_monitoring,
            "rate_limiting_monitoring": rate_limiting_monitoring,
        }

        logger.info(f"환경 '{environment}' 통합 대시보드 조회 완료")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"통합 대시보드 조회 실패 (환경: {environment}): {e}")
        raise HTTPException(
            status_code=500, detail=f"통합 대시보드 조회 실패: {str(e)}"
        )


@router.get("/health/cache")
async def cache_health_check(
    health_service: HealthCheckService = Depends(get_health_service),
) -> Dict[str, Any]:
    """Redis 캐시 상태 확인 (통합 API)"""
    try:
        result = await health_service._check_redis_cache()
        return result
    except Exception as e:
        logger.error(f"캐시 헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"캐시 헬스체크 실패: {str(e)}")


@router.get("/version")
async def version_info(
    health_service: HealthCheckService = Depends(get_health_service),
) -> Dict[str, Any]:
    """버전 정보 조회 (통합 API)"""
    try:
        result = await health_service.get_version_info()
        return result
    except Exception as e:
        logger.error(f"버전 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"버전 정보 조회 실패: {str(e)}")


@router.get("/debug/config")
async def debug_config() -> Dict[str, Any]:
    """외부 인프라 API 키 설정 상태 디버깅"""
    settings = get_settings()

    return {
        "vercel": {
            "api_token_configured": bool(settings.vercel_api_token),
            "team_id_configured": bool(settings.vercel_team_id),
            "project_id_configured": bool(settings.vercel_project_id),
            "api_token_preview": (
                settings.vercel_api_token[:8] + "..."
                if settings.vercel_api_token
                else None
            ),
        },
        "upstash": {
            "api_key_configured": bool(settings.upstash_api_key),
            "email_configured": bool(settings.upstash_email),
            "database_id_configured": bool(settings.upstash_database_id),
            "email_preview": (
                settings.upstash_email[:5] + "..." if settings.upstash_email else None
            ),
        },
        "hetrix": {
            "api_token_configured": bool(settings.hetrixtools_api_token),
            "api_token_preview": (
                settings.hetrixtools_api_token[:8] + "..."
                if settings.hetrixtools_api_token
                else None
            ),
        },
        "environment": settings.environment,
        "env_file_loaded": getattr(settings, "_env_file", "unknown"),
    }


# === 새로운 Sentry 및 엔드포인트 모니터링 API들 ===


@router.get("/sentry/errors")
async def get_sentry_errors(
    sentry_service: SentryMonitoringService = Depends(get_sentry_monitoring_service),
) -> Dict[str, Any]:
    """Sentry 에러 통계 조회 (1시간/24시간/3일)"""
    try:
        logger.info("Sentry 에러 통계 조회 요청")

        error_stats = await sentry_service.get_error_statistics()

        response = {
            "last_hour_errors": error_stats.last_hour_errors,
            "last_24h_errors": error_stats.last_24h_errors,
            "last_3d_errors": error_stats.last_3d_errors,
            "error_rate_per_hour": error_stats.error_rate_per_hour,
            "status": error_stats.status,
            "last_error_time": error_stats.last_error_time,
            "environment": error_stats.environment,
            "total_events": error_stats.total_events,
            "recent_errors": [
                {
                    "message": error.message,
                    "timestamp": error.timestamp,
                    "error_type": error.error_type,
                    "file_path": error.file_path,
                    "line_number": error.line_number,
                }
                for error in error_stats.recent_errors
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Sentry 에러 통계 조회 완료: {error_stats.status} 상태")
        return response

    except Exception as e:
        logger.error(f"Sentry 에러 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sentry 에러 통계 조회 실패: {str(e)}"
        )


@router.get("/sentry/health")
async def get_sentry_health(
    sentry_service: SentryMonitoringService = Depends(get_sentry_monitoring_service),
) -> Dict[str, Any]:
    """Sentry 연결 상태 확인"""
    try:
        health_info = await sentry_service.check_sentry_health()

        return {
            "sentry_health": health_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Sentry 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Sentry 상태 확인 실패: {str(e)}")


@router.get("/sentry/trends")
async def get_sentry_trends(
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 (1-168시간)"),
    sentry_service: SentryMonitoringService = Depends(get_sentry_monitoring_service),
) -> Dict[str, Any]:
    """Sentry 에러 트렌드 조회"""
    try:
        logger.info(f"Sentry 에러 트렌드 조회 요청 ({hours}시간)")

        trends = await sentry_service.get_error_trends(hours)

        return {
            "hours": hours,
            "trends": trends,
            "total_data_points": len(trends),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Sentry 에러 트렌드 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sentry 에러 트렌드 조회 실패: {str(e)}"
        )


@router.post("/sentry/test-error")
async def send_test_error(
    sentry_service: SentryMonitoringService = Depends(get_sentry_monitoring_service),
) -> Dict[str, Any]:
    """테스트 에러를 Sentry에 전송"""
    try:
        result = await sentry_service.capture_test_error()

        if result["success"]:
            logger.info("테스트 에러 전송 성공")
            return result
        else:
            logger.warning(f"테스트 에러 전송 실패: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"테스트 에러 전송 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"테스트 에러 전송 실패: {str(e)}")


@router.get("/endpoints/status")
async def get_endpoints_status(
    endpoint_service: EndpointMonitoringService = Depends(
        get_endpoint_monitoring_service
    ),
) -> Dict[str, Any]:
    """API 엔드포인트 상태 체크"""
    try:
        logger.info("API 엔드포인트 상태 체크 요청")

        monitoring_result = await endpoint_service.check_all_endpoints()

        response = {
            "overall_status": monitoring_result.overall_status,
            "total_endpoints": monitoring_result.total_endpoints,
            "healthy_count": monitoring_result.healthy_count,
            "degraded_count": monitoring_result.degraded_count,
            "down_count": monitoring_result.down_count,
            "average_response_time": monitoring_result.average_response_time,
            "endpoints": [
                {
                    "endpoint": ep.endpoint,
                    "name": ep.name,
                    "status": ep.status,
                    "response_time": ep.response_time,
                    "status_code": ep.status_code,
                    "last_check": ep.last_check,
                    "error_message": ep.error_message,
                }
                for ep in monitoring_result.endpoints
            ],
            "last_check": monitoring_result.last_check,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"API 엔드포인트 상태 체크 완료: {monitoring_result.overall_status}"
        )
        return response

    except Exception as e:
        logger.error(f"API 엔드포인트 상태 체크 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"API 엔드포인트 상태 체크 실패: {str(e)}"
        )


@router.get("/endpoints/{endpoint_name}/status")
async def get_endpoint_status(
    endpoint_name: str,
    endpoint_service: EndpointMonitoringService = Depends(
        get_endpoint_monitoring_service
    ),
) -> Dict[str, Any]:
    """특정 엔드포인트 상태 체크"""
    try:
        logger.info(f"특정 엔드포인트 상태 체크 요청: {endpoint_name}")

        endpoint_status = await endpoint_service.check_specific_endpoint(endpoint_name)

        if not endpoint_status:
            raise HTTPException(
                status_code=404,
                detail=f"엔드포인트 '{endpoint_name}'를 찾을 수 없습니다",
            )

        response = {
            "endpoint": endpoint_status.endpoint,
            "name": endpoint_status.name,
            "status": endpoint_status.status,
            "response_time": endpoint_status.response_time,
            "status_code": endpoint_status.status_code,
            "last_check": endpoint_status.last_check,
            "error_message": endpoint_status.error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"특정 엔드포인트 상태 체크 완료: {endpoint_name} - {endpoint_status.status}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"특정 엔드포인트 상태 체크 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"특정 엔드포인트 상태 체크 실패: {str(e)}"
        )


@router.get("/endpoints/{endpoint_name}/history")
async def get_endpoint_history(
    endpoint_name: str,
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 (1-168시간)"),
    endpoint_service: EndpointMonitoringService = Depends(
        get_endpoint_monitoring_service
    ),
) -> Dict[str, Any]:
    """특정 엔드포인트의 히스토리 조회"""
    try:
        logger.info(f"엔드포인트 히스토리 조회 요청: {endpoint_name} ({hours}시간)")

        history = await endpoint_service.get_endpoint_history(endpoint_name, hours)

        return {
            "endpoint_name": endpoint_name,
            "hours": hours,
            "history": history,
            "total_data_points": len(history),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"엔드포인트 히스토리 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"엔드포인트 히스토리 조회 실패: {str(e)}"
        )


@router.get("/endpoints/list")
async def get_monitored_endpoints(
    endpoint_service: EndpointMonitoringService = Depends(
        get_endpoint_monitoring_service
    ),
) -> Dict[str, Any]:
    """모니터링 대상 엔드포인트 목록 조회"""
    try:
        endpoints = endpoint_service.get_monitored_endpoints()

        return {
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"모니터링 엔드포인트 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"모니터링 엔드포인트 목록 조회 실패: {str(e)}"
        )


@router.get("/advanced/status")
async def get_advanced_monitoring_status(
    sentry_service: SentryMonitoringService = Depends(get_sentry_monitoring_service),
    endpoint_service: EndpointMonitoringService = Depends(
        get_endpoint_monitoring_service
    ),
) -> Dict[str, Any]:
    """고급 모니터링 상태 (Sentry + 엔드포인트) 통합 조회"""
    try:
        logger.info("고급 모니터링 상태 통합 조회 요청")

        # 병렬로 데이터 수집
        sentry_stats_task = asyncio.create_task(sentry_service.get_error_statistics())
        endpoint_status_task = asyncio.create_task(
            endpoint_service.check_all_endpoints()
        )

        sentry_stats, endpoint_status = await asyncio.gather(
            sentry_stats_task, endpoint_status_task, return_exceptions=True
        )

        # 결과 처리
        response = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "unknown",
        }

        # Sentry 데이터 처리
        if isinstance(sentry_stats, Exception):
            logger.error(f"Sentry 데이터 수집 실패: {sentry_stats}")
            response["sentry"] = {"status": "error", "error": str(sentry_stats)}
        else:
            response["sentry"] = {
                "status": sentry_stats.status,
                "last_hour_errors": sentry_stats.last_hour_errors,
                "last_24h_errors": sentry_stats.last_24h_errors,
                "last_3d_errors": sentry_stats.last_3d_errors,
                "error_rate_per_hour": sentry_stats.error_rate_per_hour,
            }

        # 엔드포인트 데이터 처리
        if isinstance(endpoint_status, Exception):
            logger.error(f"엔드포인트 데이터 수집 실패: {endpoint_status}")
            response["endpoints"] = {"status": "error", "error": str(endpoint_status)}
        else:
            response["endpoints"] = {
                "overall_status": endpoint_status.overall_status,
                "healthy_count": endpoint_status.healthy_count,
                "degraded_count": endpoint_status.degraded_count,
                "down_count": endpoint_status.down_count,
                "average_response_time": endpoint_status.average_response_time,
            }

        # 전체 상태 결정
        sentry_healthy = response["sentry"].get("status") in ["healthy", "warning"]
        endpoints_healthy = response["endpoints"].get("overall_status") in [
            "healthy",
            "degraded",
        ]

        if sentry_healthy and endpoints_healthy:
            response["overall_health"] = "healthy"
        elif sentry_healthy or endpoints_healthy:
            response["overall_health"] = "degraded"
        else:
            response["overall_health"] = "unhealthy"

        logger.info(f"고급 모니터링 상태 통합 조회 완료: {response['overall_health']}")
        return response

    except Exception as e:
        logger.error(f"고급 모니터링 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"고급 모니터링 상태 조회 실패: {str(e)}"
        )


# === Rate Limiting 모니터링 엔드포인트들 ===

@router.get("/rate-limiting/metrics")
async def get_rate_limiting_metrics() -> Dict[str, Any]:
    """Rate Limiting 상세 메트릭 조회"""
    try:
        from ..middleware.monitoring import MonitoringMiddleware
        from ..database.redis_factory import RedisFactory
        
        # Redis 클라이언트 가져오기
        from ..database.redis_factory import get_redis_manager
        redis_manager = await get_redis_manager()
        
        # Redis 연결 확인
        if not await redis_manager.is_connected():
            await redis_manager.connect()
            
        redis_client = getattr(redis_manager, 'redis_client', None)
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis 연결을 사용할 수 없습니다")
        
        # 환경별 키 프리픽스 가져오기
        from ..config import get_settings
        settings = get_settings()
        key_prefix = ""
        if settings.environment == "development":
            key_prefix = "dev:"
        elif settings.environment == "test":
            key_prefix = "test:"
        elif settings.environment == "staging":
            key_prefix = "stage:"
        elif settings.environment == "production":
            key_prefix = "prod:"
        
        # PerformanceTracker 인스턴스 생성 (key_prefix 포함)
        from ..middleware.monitoring import PerformanceTracker
        tracker = PerformanceTracker(redis_client, key_prefix=key_prefix)
        
        # Rate limiting 메트릭 조회
        metrics = await tracker.get_rate_limit_metrics()
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rate limiting 메트릭 조회 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Rate limiting 메트릭 조회 실패: {str(e)}"
        )


@router.get("/rate-limiting/summary")
async def get_rate_limiting_summary() -> Dict[str, Any]:
    """Rate Limiting 요약 정보 조회"""
    try:
        from ..middleware.monitoring import PerformanceTracker
        from ..database.redis_factory import RedisFactory
        
        # Redis 클라이언트 가져오기
        from ..database.redis_factory import get_redis_manager
        redis_manager = await get_redis_manager()
        
        # Redis 연결 확인
        if not await redis_manager.is_connected():
            await redis_manager.connect()
            
        redis_client = getattr(redis_manager, 'redis_client', None)
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis 연결을 사용할 수 없습니다")
        
        # 환경별 키 프리픽스 가져오기
        from ..config import get_settings
        settings = get_settings()
        
        key_prefix = ""
        if settings.environment == "development":
            key_prefix = "dev:"
        elif settings.environment == "test":
            key_prefix = "test:"
        elif settings.environment == "staging":
            key_prefix = "stage:"
        elif settings.environment == "production":
            key_prefix = "prod:"
        
        # PerformanceTracker 인스턴스 생성
        tracker = PerformanceTracker(redis_client, key_prefix=key_prefix)
        
        # Rate limiting 요약 정보 조회
        summary = await tracker.get_rate_limit_summary()
        
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rate limiting 요약 조회 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Rate limiting 요약 조회 실패: {str(e)}"
        )


@router.get("/rate-limiting/debug")
async def debug_rate_limiting_redis() -> Dict[str, Any]:
    """Rate Limiting Redis 데이터 디버깅"""
    try:
        from ..database.redis_factory import get_redis_manager
        from ..config import get_settings
        
        settings = get_settings()
        key_prefix = ""
        if settings.environment == "development":
            key_prefix = "dev:"
        elif settings.environment == "test":
            key_prefix = "test:"
        elif settings.environment == "staging":
            key_prefix = "stage:"
        elif settings.environment == "production":
            key_prefix = "prod:"
        
        redis_manager = await get_redis_manager()
        
        # Redis 연결 확인 및 클라이언트 추출
        if not await redis_manager.is_connected():
            await redis_manager.connect()
            
        redis_client = getattr(redis_manager, 'redis_client', None)
        
        if not redis_client:
            return {"error": "Redis client not available"}
        
        # 직접 Redis 데이터 조회
        test_key = f"{key_prefix}api:metrics:rate_limit_blocks"
        raw_data = await redis_client.hgetall(test_key)
        
        # 상태코드 데이터도 조회
        status_key = f"{key_prefix}api:metrics:status_codes"
        status_data = await redis_client.hgetall(status_key)
        
        return {
            "environment": settings.environment,
            "key_prefix": key_prefix,
            "redis_client_type": str(type(redis_client)),
            "rate_limit_blocks_key": test_key,
            "rate_limit_blocks_data": dict(raw_data) if raw_data else {},
            "status_codes_key": status_key,
            "status_codes_data": dict(status_data) if status_data else {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/rate-limiting/config")
async def get_rate_limiting_config() -> Dict[str, Any]:
    """Rate Limiting 설정 정보 조회"""
    try:
        from ..models.rate_limit_config import RateLimitConfigRegistry
        
        # 모든 설정 조회
        configs = {}
        for endpoint_key in ["auth_login", "auth_register", "posts_create", "posts_list", "comments_create", "files_upload", "email_verification"]:
            config = RateLimitConfigRegistry.get_config(endpoint_key)
            if config:
                configs[config.endpoint] = {
                    "limit": config.limit,
                    "window": config.window,
                    "strategy": config.key_strategy.value,
                    "enabled": config.enabled
                }
        
        return {
            "status": "success",
            "data": {
                "configs": configs,
                "total_endpoints": len(configs)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rate limiting 설정 조회 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Rate limiting 설정 조회 실패: {str(e)}"
        )


@router.get("/performance/overview")
async def get_performance_overview() -> Dict[str, Any]:
    """성능 모니터링 종합 정보 (Rate Limiting 포함)"""
    try:
        from ..middleware.monitoring import PerformanceTracker
        from ..database.redis_factory import get_redis_manager
        
        # Redis 클라이언트 가져오기
        redis_manager = await get_redis_manager()
        
        # 다양한 Redis 클라이언트 속성 시도
        redis_client = (
            getattr(redis_manager, 'redis_client', None) or 
            getattr(redis_manager, 'client', None) or
            redis_manager
        )
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis 연결을 사용할 수 없습니다")
        
        # 환경별 키 프리픽스 가져오기
        from ..config import get_settings
        settings = get_settings()
        
        key_prefix = ""
        if settings.environment == "development":
            key_prefix = "dev:"
        elif settings.environment == "test":
            key_prefix = "test:"
        elif settings.environment == "staging":
            key_prefix = "stage:"
        elif settings.environment == "production":
            key_prefix = "prod:"
        
        # PerformanceTracker 인스턴스 생성
        tracker = PerformanceTracker(redis_client, key_prefix=key_prefix)
        
        # 모든 성능 데이터 수집
        performance_data = {}
        
        # 1. 엔드포인트 통계
        endpoint_stats = await tracker.get_metrics()
        performance_data["endpoint_statistics"] = endpoint_stats
        
        # 2. 에러율 계산
        error_rate = await tracker.calculate_error_rate()
        performance_data["error_rate"] = error_rate
        
        # 3. 인기 엔드포인트
        popular_endpoints = await tracker.get_popular_endpoints(limit=10)
        performance_data["popular_endpoints"] = popular_endpoints
        
        # 4. Rate limiting 요약
        rate_limit_summary = await tracker.get_rate_limit_summary()
        performance_data["rate_limiting"] = rate_limit_summary
        
        # 5. 전체 요청 수 계산
        total_requests = sum(endpoint_stats.get("endpoints", {}).values())
        performance_data["total_requests"] = total_requests
        
        # 6. 시스템 상태 평가
        system_status = "healthy"
        if error_rate > 0.05:  # 5% 이상 에러율
            system_status = "critical"
        elif error_rate > 0.01 or rate_limit_summary.get("overall_block_rate", 0) > 5:
            system_status = "warning"
        
        performance_data["system_status"] = system_status
        
        return {
            "status": "success",
            "data": performance_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"성능 오버뷰 조회 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"성능 오버뷰 조회 실패: {str(e)}"
        )


@router.get("/performance/endpoints")
async def get_endpoint_performance() -> Dict[str, Any]:
    """엔드포인트별 성능 분석 (Rate Limiting 포함)"""
    try:
        from ..middleware.monitoring import PerformanceTracker
        from ..database.redis_factory import get_redis_manager
        
        # Redis 클라이언트 가져오기
        redis_manager = await get_redis_manager()
        
        # 다양한 Redis 클라이언트 속성 시도
        redis_client = (
            getattr(redis_manager, 'redis_client', None) or 
            getattr(redis_manager, 'client', None) or
            redis_manager
        )
        
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis 연결을 사용할 수 없습니다")
        
        # 환경별 키 프리픽스 가져오기
        from ..config import get_settings
        settings = get_settings()
        
        key_prefix = ""
        if settings.environment == "development":
            key_prefix = "dev:"
        elif settings.environment == "test":
            key_prefix = "test:"
        elif settings.environment == "staging":
            key_prefix = "stage:"
        elif settings.environment == "production":
            key_prefix = "prod:"
        
        # PerformanceTracker 인스턴스 생성
        tracker = PerformanceTracker(redis_client, key_prefix=key_prefix)
        
        # 엔드포인트 통계와 Rate limiting 데이터 결합
        endpoint_stats = await tracker.get_metrics()
        rate_limit_metrics = await tracker.get_rate_limit_metrics()
        
        # 엔드포인트별 종합 분석
        endpoint_analysis = {}
        
        for endpoint, request_count in endpoint_stats.get("endpoints", {}).items():
            # Rate limiting 정보 찾기
            rate_limit_info = None
            for rl_endpoint in rate_limit_metrics.get("endpoints", []):
                if rl_endpoint.get("endpoint") == endpoint:
                    rate_limit_info = rl_endpoint
                    break
            
            # 간단한 성능 통계 구성
            performance_stats = {
                "request_count": request_count,
                "avg_response_time": 0,  # 실제 구현 시 계산 필요
                "error_rate": 0  # 실제 구현 시 계산 필요
            }
            
            endpoint_analysis[endpoint] = {
                "performance": performance_stats,
                "rate_limiting": {
                    "blocks": rate_limit_info.get("blocks", 0) if rate_limit_info else 0,
                    "block_rate": rate_limit_info.get("block_rate", 0) if rate_limit_info else 0,
                    "total_requests": rate_limit_info.get("total_requests", 0) if rate_limit_info else 0
                },
                "health_score": _calculate_endpoint_health_score(performance_stats, rate_limit_info)
            }
        
        return {
            "status": "success",
            "data": {
                "endpoints": endpoint_analysis,
                "total_endpoints": len(endpoint_analysis),
                "summary": {
                    "total_requests": sum(ep.get("performance", {}).get("request_count", 0) for ep in endpoint_analysis.values()),
                    "total_blocks": sum(ep.get("rate_limiting", {}).get("blocks", 0) for ep in endpoint_analysis.values()),
                    "avg_block_rate": sum(ep.get("rate_limiting", {}).get("block_rate", 0) for ep in endpoint_analysis.values()) / len(endpoint_analysis) if endpoint_analysis else 0
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"엔드포인트 성능 분석 조회 실패: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"엔드포인트 성능 분석 조회 실패: {str(e)}"
        )


# === 테스트 모드 관련 엔드포인트 ===


def _calculate_endpoint_health_score(performance_stats: Dict, rate_limit_info: Dict) -> Dict[str, Any]:
    """엔드포인트 건강도 점수 계산"""
    score = 100
    issues = []
    
    # 성능 기반 점수 감점
    error_rate = performance_stats.get("error_rate", 0)
    if error_rate > 0.05:  # 5% 이상
        score -= 30
        issues.append("high_error_rate")
    elif error_rate > 0.01:  # 1% 이상
        score -= 15
        issues.append("moderate_error_rate")
    
    avg_response_time = performance_stats.get("avg_response_time", 0)
    if avg_response_time > 2000:  # 2초 이상
        score -= 25
        issues.append("slow_response")
    elif avg_response_time > 1000:  # 1초 이상
        score -= 10
        issues.append("moderate_response_time")
    
    # Rate limiting 기반 점수 감점
    if rate_limit_info:
        block_rate = rate_limit_info.get("block_rate", 0)
        if block_rate > 10:  # 10% 이상 차단
            score -= 20
            issues.append("high_block_rate")
        elif block_rate > 5:  # 5% 이상 차단
            score -= 10
            issues.append("moderate_block_rate")
    
    # 건강도 등급 결정
    if score >= 90:
        grade = "excellent"
    elif score >= 75:
        grade = "good"
    elif score >= 60:
        grade = "fair"
    elif score >= 40:
        grade = "poor"
    else:
        grade = "critical"
    
    return {
        "score": max(0, score),
        "grade": grade,
        "issues": issues
    }

# === Sentry 테스트 엔드포인트 ===

@router.post("/test/sentry/error")
async def test_sentry_single_error() -> Dict[str, Any]:
    """단일 테스트 에러를 Sentry에 전송"""
    try:
        # LogService와 연동된 SentryMonitoringService 사용
        sentry_service = await get_sentry_monitoring_service()
        result = await sentry_service.capture_test_error()
        
        logger.info(f"Sentry 단일 테스트 에러 전송 결과: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Sentry 테스트 에러 전송 실패: {e}")
        return {"success": False, "message": f"테스트 에러 전송 실패: {str(e)}"}

@router.post("/test/sentry/multiple-errors")
async def test_sentry_multiple_errors(count: int = 3) -> Dict[str, Any]:
    """다중 테스트 에러를 Sentry에 전송 (통계 테스트용)"""
    try:
        # LogService와 연동된 SentryMonitoringService 사용
        sentry_service = await get_sentry_monitoring_service()
        result = await sentry_service.capture_multiple_test_errors(count)
        
        logger.info(f"Sentry 다중 테스트 에러 전송 결과: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Sentry 다중 테스트 에러 전송 실패: {e}")
        return {"success": False, "message": f"다중 테스트 에러 전송 실패: {str(e)}"}

@router.get("/sentry/statistics")
async def get_sentry_error_statistics() -> Dict[str, Any]:
    """Sentry 에러 통계 조회 (DB 기반)"""
    try:
        # LogService와 연동된 SentryMonitoringService 사용
        sentry_service = await get_sentry_monitoring_service()
        stats = await sentry_service.get_error_statistics()
        
        # 직렬화 가능한 형태로 변환
        result = {
            "last_hour_errors": stats.last_hour_errors,
            "last_24h_errors": stats.last_24h_errors,
            "last_3d_errors": stats.last_3d_errors,
            "error_rate_per_hour": stats.error_rate_per_hour,
            "status": stats.status,
            "last_error_time": stats.last_error_time,
            "environment": stats.environment,
            "total_events": stats.total_events,
            "recent_errors": [
                {
                    "message": error.message,
                    "timestamp": error.timestamp,
                    "error_type": error.error_type,
                    "file_path": error.file_path,
                    "line_number": error.line_number
                }
                for error in stats.recent_errors
            ]
        }
        
        logger.info(f"Sentry 에러 통계 조회 완료: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Sentry 에러 통계 조회 실패: {e}")
        return {
            "status": "error",
            "message": f"에러 통계 조회 실패: {str(e)}",
            "last_hour_errors": 0,
            "last_24h_errors": 0,
            "last_3d_errors": 0,
            "error_rate_per_hour": 0.0
        }

@router.get("/sentry/health")
async def get_sentry_health() -> Dict[str, Any]:
    """Sentry 연결 상태 확인"""
    try:
        from nadle_backend.services.sentry_monitoring_service import SentryMonitoringService
        
        sentry_service = SentryMonitoringService()
        health_status = await sentry_service.check_sentry_health()
        
        logger.info(f"Sentry 헬스체크 완료: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Sentry 헬스체크 실패: {e}")
        return {
            "status": "error",
            "message": f"Sentry 헬스체크 실패: {str(e)}",
            "configured": False
        }

@router.get("/sentry/debug")
async def get_sentry_debug_info() -> Dict[str, Any]:
    """Sentry 디버깅 정보 조회 (개발용)"""
    try:
        from nadle_backend.services.sentry_monitoring_service import SentryMonitoringService
        
        sentry_service = SentryMonitoringService()
        
        # 디버깅 정보 수집
        debug_info = {
            "sentry_configured": sentry_service.sentry_configured,
            "error_memory_count": len(sentry_service._error_memory["recent_errors"]),
            "total_count": sentry_service._error_memory["total_count"],
            "recent_errors_raw": sentry_service._error_memory["recent_errors"][-3:],  # 최근 3개만
            "instance_id": id(sentry_service),
            "initialized": getattr(sentry_service, '_initialized', False)
        }
        
        logger.info(f"Sentry 디버깅 정보: {debug_info}")
        return debug_info
        
    except Exception as e:
        logger.error(f"Sentry 디버깅 정보 조회 실패: {e}")
        return {
            "status": "error", 
            "message": f"디버깅 정보 조회 실패: {str(e)}"
        }


@router.post("/sentry/frontend-error")
async def record_frontend_error(request: Request) -> Dict[str, Any]:
    """프론트엔드에서 발생한 에러를 백엔드에서도 기록"""
    try:
        from nadle_backend.services.sentry_monitoring_service import SentryMonitoringService
        
        # 요청 본문 파싱
        body = await request.json()
        message = body.get('message', '프론트엔드 에러')
        source = body.get('source', 'frontend')
        timestamp = body.get('timestamp', datetime.utcnow().isoformat())
        url = body.get('url', 'unknown')
        
        sentry_service = SentryMonitoringService()
        
        # 프론트엔드 에러를 메모리에 기록
        sentry_service.record_error(
            error_message=f"[Frontend] {message}",
            error_type="FrontendError",
            file_path=url,
            line_number=None
        )
        
        logger.info(f"프론트엔드 에러 백엔드 기록 완료: {message}")
        
        return {
            "success": True,
            "message": "프론트엔드 에러가 백엔드에 기록되었습니다",
            "timestamp": timestamp
        }
    
    except Exception as e:
        logger.error(f"프론트엔드 에러 백엔드 기록 실패: {e}")
        return {
            "success": False,
            "message": f"프론트엔드 에러 기록 실패: {str(e)}"
        }


@router.post("/test/api/server-error")
async def test_api_server_error() -> Dict[str, Any]:
    """
    실제 API에서 서버 에러를 발생시켜 Sentry 포착 테스트
    """
    try:
        logger.info("🔥 의도적인 서버 에러 발생 테스트 시작")
        
        # 다양한 타입의 서버 에러 발생
        import random
        error_types = [
            lambda: 1 / 0,  # ZeroDivisionError
            lambda: [][1],  # IndexError  
            lambda: {}["nonexistent"],  # KeyError
            lambda: None.some_method(),  # AttributeError
            lambda: int("not_a_number"),  # ValueError
        ]
        
        # 랜덤하게 에러 타입 선택
        error_func = random.choice(error_types)
        error_func()  # 에러 발생!
        
        # 여기까지 오면 안됨
        return {"success": False, "message": "에러가 발생하지 않았습니다"}
        
    except Exception as e:
        # 에러 정보 로깅
        logger.error(f"🔥 의도적인 API 에러 발생: {type(e).__name__} - {str(e)}")
        
        # 에러를 다시 raise해서 Sentry가 포착하도록 함
        raise e


@router.get("/test/api/database-error")
async def test_api_database_error() -> Dict[str, Any]:
    """
    데이터베이스 관련 에러를 발생시켜 Sentry 포착 테스트
    """
    try:
        logger.info("🗄️ 의도적인 데이터베이스 에러 발생 테스트 시작")
        
        # 잘못된 데이터베이스 쿼리 시도
        from nadle_backend.models.core import User
        
        # 존재하지 않는 필드로 쿼리 (MongoDB 에러 발생)
        result = await User.find({"nonexistent_field_12345": "value"}).to_list()
        
        return {"success": False, "message": "데이터베이스 에러가 발생하지 않았습니다"}
        
    except Exception as e:
        # 에러 정보 로깅
        logger.error(f"🗄️ 의도적인 데이터베이스 에러 발생: {type(e).__name__} - {str(e)}")
        
        # 에러를 다시 raise해서 Sentry가 포착하도록 함
        raise e
