from fastapi import APIRouter, Depends
from typing import Dict, Any
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