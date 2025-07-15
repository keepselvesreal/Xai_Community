from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import os
from ..services.cache_service import get_cache_service, CacheService
from ..database.redis_factory import get_redis_health
from ..config import get_settings
from ..services.hetrix_monitoring import HealthCheckService

router = APIRouter(tags=["health"])

# 의존성 주입
def get_health_service() -> HealthCheckService:
    """HealthCheckService 의존성 주입"""
    return HealthCheckService()

@router.get("/health")
async def health_check(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """기본 헬스체크 (새로운 통합 API로 위임)"""
    try:
        result = await health_service.simple_health_check()
        return result
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "nadle-backend-api",
            "error": str(e)
        }

@router.get("/health/cache")
async def cache_health_check(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Redis 캐시 상태 확인 (새로운 통합 API로 위임)"""
    try:
        result = await health_service._check_redis_cache()
        return result
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/health/full")
async def full_health_check(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """전체 시스템 상태 확인 (새로운 통합 API로 위임)"""
    try:
        result = await health_service.comprehensive_health_check()
        return result
    except Exception as e:
        return {
            "status": "unhealthy",
            "overall_health": "unhealthy",
            "error": str(e)
        }

@router.get("/health/version")
async def health_version_info(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """헬스 체크 버전 정보 (새로운 통합 API로 위임)"""
    try:
        result = await health_service.get_version_info()
        return result
    except Exception as e:
        return {
            "version": "unknown",
            "error": str(e)
        }

@router.get("/health/redis")
async def redis_health_check(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """Redis 세부 상태 확인 (새로운 통합 API로 위임)"""
    try:
        result = await health_service._check_redis_cache()
        # 세부 정보 추가
        redis_health = await get_redis_health()
        settings = get_settings()
        
        return {
            **result,
            "redis": redis_health,
            "config": {
                "environment": settings.environment,
                "use_upstash_redis": settings.use_upstash_redis,
                "redis_key_prefix": settings.redis_key_prefix,
                "cache_enabled": settings.cache_enabled,
                "upstash_url_configured": bool(settings.upstash_redis_rest_url),
                "upstash_token_configured": bool(settings.upstash_redis_rest_token)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/version")
async def version_info(
    health_service: HealthCheckService = Depends(get_health_service)
) -> Dict[str, Any]:
    """버전 정보 및 빌드 정보 반환 (루트 레벨) (새로운 통합 API로 위임)"""
    try:
        result = await health_service.get_version_info()
        return result
    except Exception as e:
        return {
            "version": "unknown",
            "service": "xai-community-backend",
            "error": str(e)
        }