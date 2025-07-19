"""
External log collector service for gathering logs from multiple external services.

Coordinates log collection from various external adapters and handles
aggregation, error handling, and health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ...core.logging import (
    LogRepositoryInterface,
    ExternalLogAdapterInterface,
    LogEntry,
    LogLevel,
    LogServiceType,
    LogSource,
    LogContext,
    AdapterError,
    RepositoryError,
)

logger = logging.getLogger(__name__)


class ExternalLogCollectorService:
    """
    Service for collecting logs from external systems.
    
    Coordinates multiple log adapters and handles collection scheduling,
    error handling, and health monitoring for external log sources.
    """
    
    def __init__(
        self,
        log_repository: LogRepositoryInterface,
        adapters: Dict[str, ExternalLogAdapterInterface],
        max_concurrent_collections: int = 3,
        collection_timeout: int = 300  # 5 minutes
    ):
        """
        Initialize external log collector service.
        
        Args:
            log_repository: Repository for storing collected logs
            adapters: Dictionary of adapter name to adapter instance
            max_concurrent_collections: Maximum concurrent adapter collections
            collection_timeout: Timeout for each collection in seconds
        """
        self.log_repository = log_repository
        self.adapters = adapters
        self.max_concurrent_collections = max_concurrent_collections
        self.collection_timeout = collection_timeout
        self._collection_semaphore = asyncio.Semaphore(max_concurrent_collections)
    
    async def collect_all_logs(self, hours: int = 1) -> Dict[str, Any]:
        """
        Collect logs from all configured external adapters.
        
        Args:
            hours: Number of hours to look back for logs
            
        Returns:
            Dictionary with collection results and statistics
        """
        collection_start = datetime.utcnow()
        results = {
            "start_time": collection_start.isoformat(),
            "hours": hours,
            "adapters": {},
            "summary": {
                "total_logs_collected": 0,
                "successful_adapters": 0,
                "failed_adapters": 0,
                "errors": [],
            }
        }
        
        logger.info(f"Starting external log collection for {hours} hours from {len(self.adapters)} adapters")
        
        # Create collection tasks for all adapters
        collection_tasks = []
        for adapter_name, adapter in self.adapters.items():
            task = asyncio.create_task(
                self._collect_from_adapter(adapter_name, adapter, hours)
            )
            collection_tasks.append(task)
        
        # Wait for all collections to complete
        adapter_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Process results
        for i, (adapter_name, result) in enumerate(zip(self.adapters.keys(), adapter_results)):
            if isinstance(result, Exception):
                # Collection failed
                error_msg = f"Collection from {adapter_name} failed: {str(result)}"
                logger.error(error_msg)
                
                results["adapters"][adapter_name] = {
                    "success": False,
                    "error": str(result),
                    "logs_collected": 0,
                }
                results["summary"]["failed_adapters"] += 1
                results["summary"]["errors"].append(error_msg)
                
                # Log the collection failure
                await self._log_collection_error(adapter_name, str(result))
                
            else:
                # Collection succeeded
                logs_collected = result.get("logs_collected", 0)
                
                results["adapters"][adapter_name] = result
                results["summary"]["total_logs_collected"] += logs_collected
                results["summary"]["successful_adapters"] += 1
        
        # Calculate collection duration
        collection_end = datetime.utcnow()
        collection_duration = (collection_end - collection_start).total_seconds()
        results["end_time"] = collection_end.isoformat()
        results["duration_seconds"] = collection_duration
        
        # Log collection summary
        summary = results["summary"]
        logger.info(
            f"External log collection completed in {collection_duration:.1f}s: "
            f"{summary['total_logs_collected']} logs from "
            f"{summary['successful_adapters']}/{len(self.adapters)} adapters"
        )
        
        # Log collection completion
        await self._log_collection_completion(results)
        
        return results
    
    async def collect_from_service(self, service_name: str, hours: int = 1) -> Dict[str, Any]:
        """
        Collect logs from a specific external service.
        
        Args:
            service_name: Name of the service/adapter
            hours: Number of hours to look back
            
        Returns:
            Collection result for the specified service
            
        Raises:
            ValueError: If service is not configured
            AdapterError: If collection fails
        """
        if service_name not in self.adapters:
            raise ValueError(f"Adapter '{service_name}' not configured")
        
        adapter = self.adapters[service_name]
        
        logger.info(f"Starting log collection from {service_name}")
        
        try:
            result = await self._collect_from_adapter(service_name, adapter, hours)
            logger.info(f"Successfully collected {result['logs_collected']} logs from {service_name}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to collect logs from {service_name}: {str(e)}"
            logger.error(error_msg)
            await self._log_collection_error(service_name, str(e))
            raise AdapterError(service_name, str(e))
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections to all configured external adapters.
        
        Returns:
            Dictionary mapping adapter names to connection status
        """
        logger.info("Testing connections to all external adapters")
        
        connection_tests = []
        for adapter_name, adapter in self.adapters.items():
            test_task = asyncio.create_task(
                self._test_adapter_connection(adapter_name, adapter)
            )
            connection_tests.append(test_task)
        
        # Wait for all connection tests
        test_results = await asyncio.gather(*connection_tests, return_exceptions=True)
        
        # Process results
        connection_status = {}
        for adapter_name, result in zip(self.adapters.keys(), test_results):
            if isinstance(result, Exception):
                connection_status[adapter_name] = False
                logger.error(f"Connection test failed for {adapter_name}: {result}")
            else:
                connection_status[adapter_name] = result
                status_str = "successful" if result else "failed"
                logger.info(f"Connection test {status_str} for {adapter_name}")
        
        return connection_status
    
    async def get_collection_health(self) -> Dict[str, Any]:
        """
        Get health status of external log collection.
        
        Returns:
            Dictionary with health information for all adapters
        """
        health_status = {
            "overall_status": "healthy",
            "adapters": {},
            "last_collection_check": datetime.utcnow().isoformat(),
        }
        
        # Test connections
        connection_status = await self.test_all_connections()
        
        # Check recent collection success
        recent_logs_filter = {
            "source": LogSource.EXTERNAL,
            "start_time": datetime.utcnow() - timedelta(hours=2),
        }
        
        healthy_adapters = 0
        for adapter_name, adapter in self.adapters.items():
            is_connected = connection_status.get(adapter_name, False)
            
            adapter_health = {
                "connection_status": "healthy" if is_connected else "unhealthy",
                "service_name": adapter.service_name,
                "last_connection_test": datetime.utcnow().isoformat(),
            }
            
            if is_connected:
                healthy_adapters += 1
                adapter_health["status"] = "healthy"
            else:
                adapter_health["status"] = "unhealthy"
                health_status["overall_status"] = "degraded"
            
            health_status["adapters"][adapter_name] = adapter_health
        
        # Determine overall health
        if healthy_adapters == 0:
            health_status["overall_status"] = "unhealthy"
        elif healthy_adapters < len(self.adapters):
            health_status["overall_status"] = "degraded"
        
        health_status["healthy_adapters"] = healthy_adapters
        health_status["total_adapters"] = len(self.adapters)
        
        return health_status
    
    async def _collect_from_adapter(
        self,
        adapter_name: str,
        adapter: ExternalLogAdapterInterface,
        hours: int
    ) -> Dict[str, Any]:
        """
        Collect logs from a single adapter with error handling.
        
        Args:
            adapter_name: Name of the adapter
            adapter: Adapter instance
            hours: Hours to look back
            
        Returns:
            Collection result dictionary
            
        Raises:
            Exception: If collection fails
        """
        async with self._collection_semaphore:
            collection_start = datetime.utcnow()
            
            try:
                # Collect logs with timeout
                logs = await asyncio.wait_for(
                    adapter.collect_logs(hours),
                    timeout=self.collection_timeout
                )
                
                # Save logs to repository
                if logs:
                    saved_logs = await self.log_repository.save_logs_batch(logs)
                    logs_saved = len(saved_logs)
                else:
                    logs_saved = 0
                
                collection_end = datetime.utcnow()
                duration = (collection_end - collection_start).total_seconds()
                
                result = {
                    "success": True,
                    "logs_collected": logs_saved,
                    "logs_attempted": len(logs) if logs else 0,
                    "duration_seconds": duration,
                    "start_time": collection_start.isoformat(),
                    "end_time": collection_end.isoformat(),
                    "service_name": adapter.service_name,
                }
                
                logger.info(
                    f"Collected {logs_saved} logs from {adapter_name} in {duration:.1f}s"
                )
                
                return result
                
            except asyncio.TimeoutError:
                raise AdapterError(adapter_name, f"Collection timeout after {self.collection_timeout}s")
            except Exception as e:
                raise AdapterError(adapter_name, f"Collection failed: {str(e)}")
    
    async def _test_adapter_connection(
        self,
        adapter_name: str,
        adapter: ExternalLogAdapterInterface
    ) -> bool:
        """
        Test connection for a single adapter.
        
        Args:
            adapter_name: Name of the adapter
            adapter: Adapter instance
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            return await asyncio.wait_for(
                adapter.test_connection(),
                timeout=30  # 30 second timeout for connection test
            )
        except Exception as e:
            logger.warning(f"Connection test failed for {adapter_name}: {e}")
            return False
    
    async def _log_collection_error(self, adapter_name: str, error_message: str) -> None:
        """
        Log collection error as an internal log entry.
        
        Args:
            adapter_name: Name of the adapter that failed
            error_message: Error message
        """
        try:
            log_entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.ERROR,
                service=LogServiceType.API,
                source=LogSource.INTERNAL,
                message=f"External log collection failed for {adapter_name}: {error_message}",
                context=LogContext(
                    infrastructure="external_collector",
                ),
                metadata={
                    "adapter_name": adapter_name,
                    "error_type": "collection_failure",
                    "tags": ["external_collection", "error", adapter_name],
                }
            )
            
            await self.log_repository.save_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log collection error: {e}")
    
    async def _log_collection_completion(self, results: Dict[str, Any]) -> None:
        """
        Log collection completion as an internal log entry.
        
        Args:
            results: Collection results dictionary
        """
        try:
            summary = results["summary"]
            
            # Determine log level based on results
            if summary["failed_adapters"] == 0:
                level = LogLevel.INFO
                message = f"External log collection completed successfully: {summary['total_logs_collected']} logs collected"
            elif summary["successful_adapters"] > 0:
                level = LogLevel.WARN
                message = f"External log collection partially successful: {summary['total_logs_collected']} logs collected, {summary['failed_adapters']} adapters failed"
            else:
                level = LogLevel.ERROR
                message = f"External log collection failed: all {summary['failed_adapters']} adapters failed"
            
            log_entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=level,
                service=LogServiceType.API,
                source=LogSource.INTERNAL,
                message=message,
                context=LogContext(
                    infrastructure="external_collector",
                    response_time=results.get("duration_seconds", 0) * 1000,  # Convert to ms
                ),
                metadata={
                    "collection_results": summary,
                    "adapters_count": len(self.adapters),
                    "hours_collected": results["hours"],
                    "tags": ["external_collection", "completion"],
                }
            )
            
            await self.log_repository.save_log(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log collection completion: {e}")