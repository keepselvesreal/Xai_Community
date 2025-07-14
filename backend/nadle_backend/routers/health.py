from fastapi import APIRouter, Depends
from typing import Dict, Any
import os
from ..services.cache_service import get_cache_service, CacheService
from ..database.redis_factory import get_redis_health
from ..config import get_settings

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "message": "API 서버가 정상적으로 동작 중입니다."
    }

@router.get("/health/cache")
async def cache_health_check(
    cache_service: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """Redis 캐시 상태 확인"""
    cache_stats = await cache_service.get_cache_stats()
    return {
        "cache": cache_stats
    }

@router.get("/health/full")
async def full_health_check(
    cache_service: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """전체 시스템 상태 확인"""
    cache_stats = await cache_service.get_cache_stats()
    
    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "cache": cache_stats
        }
    }

@router.get("/health/version")
async def health_version_info() -> Dict[str, Any]:
    """헬스 체크 버전 정보"""
    return {
        "version": os.getenv("BUILD_VERSION", "unknown"),
        "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "service": "xai-community-backend"
    }

@router.get("/health/redis")
async def redis_health_check() -> Dict[str, Any]:
    """Redis 세부 상태 확인"""
    redis_health = await get_redis_health()
    settings = get_settings()
    
    return {
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

@router.get("/version")
async def version_info() -> Dict[str, Any]:
    """버전 정보 및 빌드 정보 반환 (루트 레벨)"""
    return {
        "version": os.getenv("BUILD_VERSION", "unknown"),
        "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "service": "xai-community-backend"
    }