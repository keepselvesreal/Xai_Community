"""
Google Cloud Run log adapter for collecting service logs and metrics.

Uses Mock data based on Google Cloud Logging API documentation since the
real API encountered authentication issues during initial testing.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ...core.logging import (
    ExternalLogAdapterInterface,
    LogEntry,
    LogLevel,
    LogServiceType,
    LogSource,
    LogContext,
    LogMetadata,
    AdapterError,
)
# CloudRunMockData import removed to avoid circular dependency
# We'll define mock data generation methods locally

logger = logging.getLogger(__name__)


class CloudRunLogAdapter(ExternalLogAdapterInterface):
    """
    Google Cloud Run log collector.
    
    Collects logs from Cloud Run services including application logs, 
    request logs, and system metrics. Currently uses Mock data due to 
    authentication complexity in the API setup.
    """
    
    def __init__(
        self,
        project_id: str,
        service_name: Optional[str] = None,
        region: Optional[str] = None,
        credentials_path: Optional[str] = None,
        use_mock: bool = True,  # Default to True since API setup is complex
        timeout: int = 30
    ):
        """
        Initialize Cloud Run log adapter.
        
        Args:
            project_id: Google Cloud project ID
            service_name: Optional Cloud Run service name filter
            region: Optional region filter
            credentials_path: Path to service account credentials
            use_mock: Whether to use mock data (default True)
            timeout: Request timeout in seconds
        """
        self.project_id = project_id
        self._service_name_filter = service_name
        self.region = region
        self.credentials_path = credentials_path
        self.use_mock = use_mock
        self.timeout = timeout
    
    @property
    def service_name(self) -> str:
        """Get the service name."""
        return "cloud_run"
    
    async def test_connection(self) -> bool:
        """
        Test connection to Google Cloud Logging API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.use_mock:
            return True
        
        # For real implementation, would test Google Cloud Logging API
        # Currently returns False since API setup is complex
        logger.warning("Real Cloud Run API not implemented, using mock data")
        return False
    
    async def collect_logs(self, hours: int = 1) -> List[LogEntry]:
        """
        Collect logs from Cloud Run services.
        
        Args:
            hours: Number of hours to look back for logs
            
        Returns:
            List of log entries from Cloud Run services
            
        Raises:
            AdapterError: If log collection fails
        """
        try:
            if self.use_mock:
                return await self._collect_mock_logs(hours)
            else:
                return await self._collect_real_logs(hours)
                
        except Exception as e:
            logger.error(f"Failed to collect Cloud Run logs: {e}")
            raise AdapterError("cloud_run", f"Log collection failed: {str(e)}")
    
    async def _collect_real_logs(self, hours: int) -> List[LogEntry]:
        """
        Collect real logs from Google Cloud Logging API.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of log entries (currently falls back to mock)
        """
        # TODO: Implement real Google Cloud Logging API integration
        # This would require:
        # 1. Authentication with service account
        # 2. Cloud Logging API client setup
        # 3. Query construction with filters
        # 4. Log parsing and transformation
        
        logger.warning("Real Cloud Run API not implemented, falling back to mock")
        return await self._collect_mock_logs(hours)
    
    async def _collect_mock_logs(self, hours: int) -> List[LogEntry]:
        """
        Collect logs using mock data.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of log entries from mock data
        """
        logs = []
        
        # Get mock log entries
        mock_entries = self._get_mock_log_entries()
        
        for entry in mock_entries:
            log_entry = self._cloud_log_to_log_entry(entry)
            logs.append(log_entry)
        
        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        # Add some synthetic metrics logs
        metrics_logs = self._generate_metrics_logs()
        logs.extend(metrics_logs)
        
        logger.info(f"Collected {len(logs)} mock logs from Cloud Run")
        return logs
    
    def _cloud_log_to_log_entry(self, cloud_log: Dict[str, Any]) -> LogEntry:
        """
        Convert Cloud Logging entry to LogEntry.
        
        Args:
            cloud_log: Log entry from Cloud Logging API
            
        Returns:
            LogEntry representing the cloud log
        """
        # Parse timestamp
        timestamp_str = cloud_log.get("timestamp", "")
        try:
            # Remove timezone info for parsing
            timestamp_clean = timestamp_str.replace("+00:00", "").replace("Z", "")
            timestamp = datetime.fromisoformat(timestamp_clean)
        except:
            timestamp = datetime.utcnow()
        
        # Map severity to log level
        severity = cloud_log.get("severity", "INFO")
        level_mapping = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "NOTICE": LogLevel.INFO,
            "WARNING": LogLevel.WARN,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.ERROR,
            "ALERT": LogLevel.ERROR,
            "EMERGENCY": LogLevel.ERROR,
        }
        level = level_mapping.get(severity, LogLevel.INFO)
        
        # Extract message
        message = cloud_log.get("payload", "")
        if not message:
            message = f"Cloud Run {severity.lower()} log"
        
        # Build context from resource and HTTP request
        resource = cloud_log.get("resource", {})
        labels = resource.get("labels", {})
        http_request = cloud_log.get("http_request", {})
        
        context = LogContext(
            infrastructure="gcp",
            region=labels.get("location", "unknown"),
            instance_id=cloud_log.get("labels", {}).get("instanceId", "")[:16],  # Truncate for readability
            endpoint=http_request.get("request_url", "").split("?")[0] if http_request.get("request_url") else None,
            method=http_request.get("request_method"),
            status_code=http_request.get("status"),
            response_time=self._parse_latency(http_request.get("latency")),
            ip_address=http_request.get("remote_ip"),
            user_agent=http_request.get("user_agent"),
        )
        
        # Build metadata
        metadata = LogMetadata(
            cloud_trace_id=cloud_log.get("trace", "").split("/")[-1] if cloud_log.get("trace") else None,
            tags=[
                "cloud_run",
                severity.lower(),
                labels.get("service_name", "unknown_service"),
            ],
            custom={
                "insert_id": cloud_log.get("insert_id"),
                "resource": resource,
                "labels": cloud_log.get("labels", {}),
                "operation": cloud_log.get("operation"),
                "source_location": cloud_log.get("source_location"),
            }
        )
        
        # Add stack trace if available from source location
        stack_trace = None
        source_location = cloud_log.get("source_location")
        if source_location and level == LogLevel.ERROR:
            stack_trace = f"File: {source_location.get('file', 'unknown')}\n" \
                         f"Line: {source_location.get('line', 'unknown')}\n" \
                         f"Function: {source_location.get('function', 'unknown')}"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=LogServiceType.CLOUD_RUN,
            source=LogSource.EXTERNAL,
            message=message,
            context=context,
            metadata=metadata,
            stack_trace=stack_trace,
        )
    
    def _generate_metrics_logs(self) -> List[LogEntry]:
        """
        Generate synthetic metrics logs for Cloud Run.
        
        Returns:
            List of synthetic metric log entries
        """
        logs = []
        timestamp = datetime.utcnow()
        
        # CPU usage metric
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=1),
            level=LogLevel.INFO,
            service=LogServiceType.CLOUD_RUN,
            source=LogSource.EXTERNAL,
            message="Cloud Run CPU usage: 45%",
            context=LogContext(
                infrastructure="gcp",
                region="asia-northeast3",
            ),
            metadata=LogMetadata(
                tags=["metrics", "cpu", "performance"],
                cpu_usage=45.0,
                custom={
                    "metric_type": "cpu_utilization",
                    "service_name": self._service_name_filter or "xai-community-backend",
                }
            )
        ))
        
        # Memory usage metric
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=1),
            level=LogLevel.INFO,
            service=LogServiceType.CLOUD_RUN,
            source=LogSource.EXTERNAL,
            message="Cloud Run memory usage: 67% (512MB / 768MB)",
            context=LogContext(
                infrastructure="gcp",
                region="asia-northeast3",
            ),
            metadata=LogMetadata(
                tags=["metrics", "memory", "performance"],
                memory_usage=536870912,  # 512MB in bytes
                custom={
                    "metric_type": "memory_utilization",
                    "memory_limit_mb": 768,
                    "memory_used_mb": 512,
                    "memory_percentage": 67.0,
                    "service_name": self._service_name_filter or "xai-community-backend",
                }
            )
        ))
        
        # Request count metric
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=1),
            level=LogLevel.INFO,
            service=LogServiceType.CLOUD_RUN,
            source=LogSource.EXTERNAL,
            message="Cloud Run request rate: 15 requests/minute",
            context=LogContext(
                infrastructure="gcp",
                region="asia-northeast3",
            ),
            metadata=LogMetadata(
                tags=["metrics", "requests", "traffic"],
                custom={
                    "metric_type": "request_count",
                    "requests_per_minute": 15,
                    "active_instances": 2,
                    "service_name": self._service_name_filter or "xai-community-backend",
                }
            )
        ))
        
        # Container startup log
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=10),
            level=LogLevel.INFO,
            service=LogServiceType.CLOUD_RUN,
            source=LogSource.EXTERNAL,
            message="Container instance started successfully",
            context=LogContext(
                infrastructure="gcp",
                region="asia-northeast3",
                instance_id="00bf4bf02dccfc02",
            ),
            metadata=LogMetadata(
                tags=["container", "startup", "lifecycle"],
                custom={
                    "event_type": "container_start",
                    "revision_name": f"{self._service_name_filter or 'xai-community-backend'}-00010-kb7",
                    "startup_time_ms": 2500,
                }
            )
        ))
        
        return logs
    
    def _parse_latency(self, latency_str: Optional[str]) -> Optional[float]:
        """
        Parse latency string to milliseconds.
        
        Args:
            latency_str: Latency string like "25ms" or "30.125s"
            
        Returns:
            Latency in milliseconds or None if parsing fails
        """
        if not latency_str:
            return None
        
        try:
            if latency_str.endswith("ms"):
                return float(latency_str[:-2])
            elif latency_str.endswith("s"):
                return float(latency_str[:-1]) * 1000
            else:
                return float(latency_str)
        except (ValueError, TypeError):
            return None
    
    def _get_mock_log_entries(self) -> List[Dict[str, Any]]:
        """
        Generate mock log entries for testing.
        
        Returns:
            List of mock Cloud Logging entries
        """
        base_time = datetime.utcnow()
        
        return [
            {
                "timestamp": (base_time - timedelta(minutes=5)).isoformat() + "+00:00",
                "severity": "INFO",
                "insert_id": "6879b1ba000b2fa7f34c88e7",
                "resource": {
                    "type": "cloud_run_revision",
                    "labels": {
                        "revision_name": "xai-community-backend-00010-kb7",
                        "configuration_name": "xai-community-backend",
                        "service_name": "xai-community-backend",
                        "project_id": "xai-community",
                        "location": "asia-northeast3"
                    }
                },
                "payload_type": "str",
                "payload": "Application started successfully on port 8080",
                "http_request": {
                    "request_method": "GET",
                    "request_url": "https://xai-community-backend-123456789-xx.a.run.app/health",
                    "request_size": 0,
                    "status": 200,
                    "response_size": 45,
                    "user_agent": "GoogleHC/1.0",
                    "remote_ip": "169.254.1.1",
                    "server_ip": "10.4.0.1",
                    "referer": None,
                    "latency": "25ms",
                    "cache_lookup": False,
                    "cache_hit": False
                },
                "trace": "projects/xai-community/traces/c4a91ba24e09ea503af1625359e2e8db",
                "span_id": "02e9a71872c63c08",
                "source_location": None,
                "operation": None,
                "labels": {
                    "instanceId": "0069c7a98871a594bc6b2d445f662d1f3a561e217d7a17ca6930d70b90c95c1cae77525436fb0712589f9160720caeefe1a473f86f02344681da1c9510ba81051c66d0eb1966ddb7432729f087c362a871ce"
                },
                "receive_timestamp": None
            },
            {
                "timestamp": (base_time - timedelta(minutes=3)).isoformat() + "+00:00",
                "severity": "ERROR",
                "insert_id": "6879b1ba000b2cd465a9da98",
                "resource": {
                    "type": "cloud_run_revision",
                    "labels": {
                        "revision_name": "xai-community-backend-00010-kb7",
                        "configuration_name": "xai-community-backend",
                        "service_name": "xai-community-backend",
                        "project_id": "xai-community",
                        "location": "asia-northeast3"
                    }
                },
                "payload_type": "str",
                "payload": "Database connection timeout after 30 seconds",
                "http_request": {
                    "request_method": "POST",
                    "request_url": "https://xai-community-backend-123456789-xx.a.run.app/api/posts",
                    "request_size": 1024,
                    "status": 500,
                    "response_size": 128,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "remote_ip": "203.0.113.1",
                    "server_ip": "10.4.0.1",
                    "referer": "https://xai-community.vercel.app",
                    "latency": "30125ms",
                    "cache_lookup": False,
                    "cache_hit": False
                },
                "trace": "projects/xai-community/traces/d5b82ca35f1afb614bf2636468f3f9ec",
                "span_id": "15fa8e2983d74d09",
                "source_location": {
                    "file": "/app/nadle_backend/services/posts_service.py",
                    "line": 45,
                    "function": "create_post"
                },
                "operation": {
                    "id": "operation_001",
                    "producer": "cloud-run-service",
                    "first": True,
                    "last": True
                },
                "labels": {
                    "instanceId": "0069c7a98871a594bc6b2d445f662d1f3a561e217d7a17ca6930d70b90c95c1cae77525436fb0712589f9160720caeefe1a473f86f02344681da1c9510ba81051c66d0eb1966ddb7432729f087c362a871ce",
                    "error_type": "database_timeout"
                },
                "receive_timestamp": None
            }
        ]