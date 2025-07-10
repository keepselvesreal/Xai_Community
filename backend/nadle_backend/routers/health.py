from fastapi import APIRouter, Depends
from typing import Dict, Any
import os
from ..services.cache_service import get_cache_service, CacheService

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "message": "API 서버가 정상적으로 동작 중입니다."
    }

@router.get("/cache")
async def cache_health_check(
    cache_service: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """Redis 캐시 상태 확인"""
    cache_stats = await cache_service.get_cache_stats()
    return {
        "cache": cache_stats
    }

@router.get("/full")
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

@router.get("/version")
async def version_info() -> Dict[str, Any]:
    """버전 정보 및 빌드 정보 반환"""
    return {
        "version": os.getenv("BUILD_VERSION", "unknown"),
        "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
        "build_time": os.getenv("BUILD_TIME", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "service": "xai-community-backend"
    }