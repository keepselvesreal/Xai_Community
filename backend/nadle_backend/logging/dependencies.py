"""
Dependency injection for the logging system.

Provides FastAPI dependency functions for injecting services, repositories,
and external adapters into API endpoints.
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.logging import (
    LogRepositoryInterface,
    ExternalLogAdapterInterface,
    CacheServiceInterface,
)
from ..database.connection import get_database
from ..services.cache_service import CacheService
from .repositories.mongo_log_repository import MongoLogRepository
from .services.log_service import LogService
from .services.external_log_collector import ExternalLogCollectorService
from .adapters import (
    VercelLogAdapter,
    UpstashLogAdapter,
    CloudRunLogAdapter,
    AtlasLogAdapter,
)

logger = logging.getLogger(__name__)

# Global instances (initialized on first use)
_log_repository: Optional[LogRepositoryInterface] = None
_log_service: Optional[LogService] = None
_external_log_collector: Optional[ExternalLogCollectorService] = None


async def get_log_repository(
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> LogRepositoryInterface:
    """
    Get log repository instance.

    Creates and configures MongoDB log repository with proper indexing.
    """
    global _log_repository

    if _log_repository is None:
        _log_repository = MongoLogRepository(database)
        await _log_repository.setup_indexes()
        logger.info("Log repository initialized")

    return _log_repository


async def get_cache_service() -> Optional[CacheServiceInterface]:
    """
    Get cache service instance.

    Returns the logging cache adapter if available, None otherwise.
    """
    try:
        # Import here to avoid circular dependencies
        from .adapters.cache_adapter import get_logging_cache_adapter

        return await get_logging_cache_adapter()
    except Exception as e:
        logger.warning(f"Cache service not available: {e}")
        return None


async def get_log_service(
    log_repository: LogRepositoryInterface = Depends(get_log_repository),
    cache_service: Optional[CacheServiceInterface] = Depends(get_cache_service),
) -> LogService:
    """
    Get log service instance.

    Creates log service with repository and optional caching.
    """
    global _log_service

    if _log_service is None:
        _log_service = LogService(
            log_repository=log_repository,
            cache_service=cache_service,
            cache_ttl=300,  # 5 minutes
        )
        await _log_service.setup()
        logger.info("Log service initialized")

    return _log_service


def _create_external_adapters() -> Dict[str, ExternalLogAdapterInterface]:
    """
    Create external log adapters based on environment configuration.

    Returns:
        Dictionary of adapter name to adapter instance
    """
    adapters = {}

    # Vercel adapter
    vercel_token = os.getenv("VERCEL_API_TOKEN")
    vercel_project_id = os.getenv("VERCEL_PROJECT_ID")

    if vercel_token:
        adapters["vercel"] = VercelLogAdapter(
            api_token=vercel_token,
            project_id=vercel_project_id,
            use_mock=False,  # Try real API first
        )
        logger.info("Vercel log adapter configured")
    else:
        # Use mock adapter for development
        adapters["vercel"] = VercelLogAdapter(
            api_token="mock-token",
            project_id="mock-project",
            use_mock=True,
        )
        logger.info("Vercel log adapter configured with mock data")

    # Upstash adapter
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    if upstash_url and upstash_token:
        adapters["upstash"] = UpstashLogAdapter(
            rest_url=upstash_url,
            rest_token=upstash_token,
            use_mock=False,  # Try real API first
        )
        logger.info("Upstash log adapter configured")
    else:
        # Use mock adapter for development
        adapters["upstash"] = UpstashLogAdapter(
            rest_url="https://mock-upstash.upstash.io",
            rest_token="mock-token",
            use_mock=True,
        )
        logger.info("Upstash log adapter configured with mock data")

    # Cloud Run adapter
    gcp_project_id = os.getenv("GCP_PROJECT_ID", "xai-community")
    gcp_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    adapters["cloud_run"] = CloudRunLogAdapter(
        project_id=gcp_project_id,
        service_name="xai-community-backend",
        region="asia-northeast3",
        credentials_path=gcp_credentials_path,
        use_mock=True,  # Use mock due to API complexity
    )
    logger.info("Cloud Run log adapter configured with mock data")

    # Atlas adapter
    atlas_api_key = os.getenv("ATLAS_API_KEY")
    atlas_group_id = os.getenv("ATLAS_GROUP_ID")
    atlas_cluster_name = os.getenv("ATLAS_CLUSTER_NAME", "Cluster0")

    adapters["atlas"] = AtlasLogAdapter(
        api_key=atlas_api_key or "mock-key",
        group_id=atlas_group_id or "mock-group",
        cluster_name=atlas_cluster_name,
        use_mock=True,  # Use mock due to API complexity
    )
    logger.info("Atlas log adapter configured with mock data")

    return adapters


async def get_external_log_collector(
    log_repository: LogRepositoryInterface = Depends(get_log_repository),
) -> ExternalLogCollectorService:
    """
    Get external log collector service.

    Creates external log collector with all configured adapters.
    """
    global _external_log_collector

    if _external_log_collector is None:
        adapters = _create_external_adapters()

        _external_log_collector = ExternalLogCollectorService(
            log_repository=log_repository,
            adapters=adapters,
            max_concurrent_collections=3,
            collection_timeout=300,  # 5 minutes
        )

        logger.info(f"External log collector initialized with {len(adapters)} adapters")

    return _external_log_collector


async def get_current_user_optional():
    """
    Get current user (optional for logging endpoints).

    Most logging endpoints don't require authentication for internal use,
    but may want to log who is accessing the logs for audit purposes.
    """
    try:
        # Import here to avoid circular dependencies
        from ..dependencies.auth import get_current_user_optional as get_auth_user

        return await get_auth_user()
    except Exception:
        # If auth is not available or fails, allow anonymous access
        return None


# Utility functions for testing and development


async def reset_log_repository():
    """Reset log repository instance (for testing)."""
    global _log_repository
    _log_repository = None


async def reset_log_service():
    """Reset log service instance (for testing)."""
    global _log_service
    _log_service = None


async def reset_external_log_collector():
    """Reset external log collector instance (for testing)."""
    global _external_log_collector
    _external_log_collector = None


async def get_log_service_with_mock_adapters(
    log_repository: LogRepositoryInterface = Depends(get_log_repository),
    cache_service: Optional[CacheServiceInterface] = Depends(get_cache_service),
) -> LogService:
    """
    Get log service with forced mock adapters (for testing).
    """
    service = LogService(
        log_repository=log_repository,
        cache_service=cache_service,
        cache_ttl=60,  # Shorter TTL for testing
    )
    await service.setup()
    return service


async def get_external_log_collector_with_mock_adapters(
    log_repository: LogRepositoryInterface = Depends(get_log_repository),
) -> ExternalLogCollectorService:
    """
    Get external log collector with forced mock adapters (for testing).
    """
    adapters = {
        "vercel": VercelLogAdapter(
            api_token="test-token",
            project_id="test-project",
            use_mock=True,
        ),
        "upstash": UpstashLogAdapter(
            rest_url="https://test.upstash.io",
            rest_token="test-token",
            use_mock=True,
        ),
        "cloud_run": CloudRunLogAdapter(
            project_id="test-project",
            use_mock=True,
        ),
        "atlas": AtlasLogAdapter(
            api_key="test-key",
            group_id="test-group",
            cluster_name="test-cluster",
            use_mock=True,
        ),
    }

    return ExternalLogCollectorService(
        log_repository=log_repository,
        adapters=adapters,
        max_concurrent_collections=2,
        collection_timeout=30,  # Shorter timeout for testing
    )
