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
