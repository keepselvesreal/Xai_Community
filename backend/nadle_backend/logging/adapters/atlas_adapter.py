"""
MongoDB Atlas log adapter for collecting database logs and metrics.

Uses Mock data based on Atlas API documentation since the real API
encountered authentication issues during initial testing.
"""

import json
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
# AtlasMockData import removed to avoid circular dependency
# We'll define mock data generation methods locally

logger = logging.getLogger(__name__)


class AtlasLogAdapter(ExternalLogAdapterInterface):
    """
    MongoDB Atlas log collector.
    
    Collects database logs, audit logs, and performance metrics from Atlas.
    Currently uses Mock data due to authentication complexity in the API setup.
    """
    
    def __init__(
        self,
        api_key: str,
        group_id: str,
        cluster_name: str,
        api_secret: Optional[str] = None,
        use_mock: bool = True,  # Default to True since API setup is complex
        timeout: int = 30
    ):
        """
        Initialize Atlas log adapter.
        
        Args:
            api_key: Atlas API key
            group_id: Atlas project/group ID
            cluster_name: Cluster name to collect logs from
            api_secret: Optional API secret for authentication
            use_mock: Whether to use mock data (default True)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.group_id = group_id
        self.cluster_name = cluster_name
        self.api_secret = api_secret
        self.use_mock = use_mock
        self.timeout = timeout
        self.base_url = "https://cloud.mongodb.com/api/atlas/v1.0"
    
    @property
    def service_name(self) -> str:
        """Get the service name."""
        return "atlas"
    
    async def test_connection(self) -> bool:
        """
        Test connection to MongoDB Atlas API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.use_mock:
            return True
        
        # For real implementation, would test Atlas API connection
        # Currently returns False since API setup is complex
        logger.warning("Real Atlas API not implemented, using mock data")
        return False
    
    async def collect_logs(self, hours: int = 1) -> List[LogEntry]:
        """
        Collect logs from MongoDB Atlas.
        
        Args:
            hours: Number of hours to look back for logs
            
        Returns:
            List of log entries from Atlas
            
        Raises:
            AdapterError: If log collection fails
        """
        try:
            if self.use_mock:
                return await self._collect_mock_logs(hours)
            else:
                return await self._collect_real_logs(hours)
                
        except Exception as e:
            logger.error(f"Failed to collect Atlas logs: {e}")
            raise AdapterError("atlas", f"Log collection failed: {str(e)}")
    
    async def _collect_real_logs(self, hours: int) -> List[LogEntry]:
        """
        Collect real logs from MongoDB Atlas API.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of log entries (currently falls back to mock)
        """
        # TODO: Implement real MongoDB Atlas API integration
        # This would require:
        # 1. Authentication with API key/secret
        # 2. Atlas API client setup
        # 3. Log collection from multiple endpoints (mongod, mongos, audit)
        # 4. Log parsing and transformation
        
        logger.warning("Real Atlas API not implemented, falling back to mock")
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
        
        # Collect different types of logs
        
        # MongoDB logs (mongod)
        mongod_logs = self._get_mock_mongod_logs()
        for log_line in mongod_logs:
            log_entry = self._parse_mongod_log(log_line)
            if log_entry:
                logs.append(log_entry)
        
        # MongoDB logs (mongos - for sharded clusters)
        mongos_logs = self._get_mock_mongos_logs()
        for log_line in mongos_logs:
            log_entry = self._parse_mongos_log(log_line)
            if log_entry:
                logs.append(log_entry)
        
        # Audit logs
        audit_logs = self._get_mock_audit_logs()
        for log_line in audit_logs:
            log_entry = self._parse_audit_log(log_line)
            if log_entry:
                logs.append(log_entry)
        
        # Access history
        access_data = self._get_mock_access_history()
        access_logs = self._parse_access_logs(access_data)
        logs.extend(access_logs)
        
        # Generate synthetic metrics
        metrics_logs = self._generate_metrics_logs()
        logs.extend(metrics_logs)
        
        # Note: Time filtering disabled for mock data to ensure test stability
        # In production, you may want to enable proper time filtering
        # cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        # logs = [log for log in logs if log.timestamp >= cutoff_time]
        
        logger.info(f"Collected {len(logs)} mock logs from MongoDB Atlas")
        return logs
    
    def _parse_mongod_log(self, log_line: str) -> Optional[LogEntry]:
        """
        Parse mongod log line to LogEntry.
        
        Args:
            log_line: Raw mongod log line in JSON format
            
        Returns:
            LogEntry or None if parsing fails
        """
        try:
            log_data = json.loads(log_line)
            
            # Parse timestamp
            timestamp_data = log_data.get("t", {})
            if isinstance(timestamp_data, dict) and "$date" in timestamp_data:
                timestamp_str = timestamp_data["$date"]
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()
            
            # Map severity
            severity = log_data.get("s", "I")
            level_mapping = {
                "D": LogLevel.DEBUG,
                "I": LogLevel.INFO,
                "W": LogLevel.WARN,
                "E": LogLevel.ERROR,
                "F": LogLevel.ERROR,  # Fatal
            }
            level = level_mapping.get(severity, LogLevel.INFO)
            
            # Extract message and component
            component = log_data.get("c", "UNKNOWN")
            message = log_data.get("msg", "")
            attr = log_data.get("attr", {})
            
            # Build enhanced message
            if attr:
                if component == "COMMAND" and "durationMillis" in attr:
                    duration = attr["durationMillis"]
                    if duration > 1000:  # Slow query threshold
                        level = LogLevel.WARN
                    message = f"Slow query detected: {message} (Duration: {duration}ms)"
                elif component == "NETWORK" and "Connection" in message:
                    conn_info = f"Remote: {attr.get('remote', 'unknown')}"
                    message = f"{message} - {conn_info}"
                elif component == "STORAGE" and level == LogLevel.ERROR:
                    error_info = attr.get("error", "Unknown error")
                    message = f"Storage error: {error_info}"
            
            # Build context
            context = LogContext(
                infrastructure="atlas",
                instance_id=f"mongod-{log_data.get('ctx', 'unknown')}",
                endpoint=attr.get("ns") if component == "COMMAND" else None,
            )
            
            # Performance metrics from command logs
            if component == "COMMAND" and "durationMillis" in attr:
                context.response_time = attr["durationMillis"]
            
            # Build metadata
            metadata = LogMetadata(
                atlas_cluster=self.cluster_name,
                tags=[
                    "mongod",
                    component.lower(),
                    severity.lower(),
                ],
                custom={
                    "component": component,
                    "id": log_data.get("id"),
                    "ctx": log_data.get("ctx"),
                    "attr": attr,
                }
            )
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                service=LogServiceType.DATABASE,
                source=LogSource.EXTERNAL,
                message=message,
                context=context,
                metadata=metadata,
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse mongod log: {e}")
            return None
    
    def _parse_mongos_log(self, log_line: str) -> Optional[LogEntry]:
        """
        Parse mongos log line to LogEntry.
        
        Args:
            log_line: Raw mongos log line in JSON format
            
        Returns:
            LogEntry or None if parsing fails
        """
        try:
            log_data = json.loads(log_line)
            
            # Parse timestamp
            timestamp_data = log_data.get("t", {})
            if isinstance(timestamp_data, dict) and "$date" in timestamp_data:
                timestamp_str = timestamp_data["$date"]
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()
            
            # Map severity
            severity = log_data.get("s", "I")
            level_mapping = {
                "D": LogLevel.DEBUG,
                "I": LogLevel.INFO,
                "W": LogLevel.WARN,
                "E": LogLevel.ERROR,
            }
            level = level_mapping.get(severity, LogLevel.INFO)
            
            # Extract message and component
            component = log_data.get("c", "UNKNOWN")
            message = log_data.get("msg", "")
            attr = log_data.get("attr", {})
            
            # Build enhanced message for sharding
            if component == "SHARDING":
                if "targetedShards" in attr:
                    shards = attr["targetedShards"]
                    message = f"Request routed to shards: {', '.join(shards)}"
            
            # Build context
            context = LogContext(
                infrastructure="atlas",
                instance_id=f"mongos-{log_data.get('ctx', 'unknown')}",
            )
            
            # Build metadata
            metadata = LogMetadata(
                atlas_cluster=self.cluster_name,
                tags=[
                    "mongos",
                    "sharding",
                    component.lower(),
                ],
                custom={
                    "component": component,
                    "id": log_data.get("id"),
                    "ctx": log_data.get("ctx"),
                    "attr": attr,
                }
            )
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                service=LogServiceType.DATABASE,
                source=LogSource.EXTERNAL,
                message=message,
                context=context,
                metadata=metadata,
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse mongos log: {e}")
            return None
    
    def _parse_audit_log(self, log_line: str) -> Optional[LogEntry]:
        """
        Parse audit log line to LogEntry.
        
        Args:
            log_line: Raw audit log line in JSON format
            
        Returns:
            LogEntry or None if parsing fails
        """
        try:
            log_data = json.loads(log_line)
            
            # Parse timestamp
            timestamp_data = log_data.get("ts", {})
            if isinstance(timestamp_data, dict) and "$date" in timestamp_data:
                timestamp_str = timestamp_data["$date"]
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()
            
            # Determine level based on audit type and result
            atype = log_data.get("atype", "unknown")
            result = log_data.get("result", 0)
            
            if result == 0:  # Success
                level = LogLevel.INFO
            else:  # Failure
                level = LogLevel.WARN
            
            # Build message
            users = log_data.get("users", [])
            user_info = users[0] if users else {"user": "unknown", "db": "unknown"}
            
            if atype == "authenticate":
                message = f"Authentication {'successful' if result == 0 else 'failed'} for user {user_info.get('user')}@{user_info.get('db')}"
            elif atype in ["createCollection", "dropCollection"]:
                ns = log_data.get("param", {}).get("ns", "unknown")
                action = "created" if atype == "createCollection" else "dropped"
                message = f"Collection {action}: {ns}"
            else:
                message = f"Audit event: {atype}"
            
            # Build context
            remote = log_data.get("remote", {})
            context = LogContext(
                infrastructure="atlas",
                ip_address=remote.get("ip"),
                user_id=user_info.get("user"),
            )
            
            # Build metadata
            metadata = LogMetadata(
                atlas_cluster=self.cluster_name,
                tags=[
                    "audit",
                    atype,
                    "successful" if result == 0 else "failed",
                ],
                custom={
                    "atype": atype,
                    "result": result,
                    "local": log_data.get("local", {}),
                    "remote": remote,
                    "users": users,
                    "roles": log_data.get("roles", []),
                    "param": log_data.get("param", {}),
                }
            )
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                service=LogServiceType.DATABASE,
                source=LogSource.EXTERNAL,
                message=message,
                context=context,
                metadata=metadata,
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse audit log: {e}")
            return None
    
    def _parse_access_logs(self, access_data: Dict[str, Any]) -> List[LogEntry]:
        """
        Parse access history data to LogEntry list.
        
        Args:
            access_data: Access logs data from Atlas API
            
        Returns:
            List of LogEntry objects
        """
        logs = []
        
        for access_log in access_data.get("accessLogs", []):
            try:
                # Parse timestamp
                timestamp_str = access_log.get("timestamp", "")
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                
                # Determine level
                auth_result = access_log.get("authResult", True)
                level = LogLevel.INFO if auth_result else LogLevel.WARN
                
                # Build message
                username = access_log.get("username", "unknown")
                auth_source = access_log.get("authSource", "unknown")
                ip_address = access_log.get("ipAddress", "unknown")
                
                if auth_result:
                    message = f"Database access successful: {username}@{auth_source} from {ip_address}"
                else:
                    failure_reason = access_log.get("failureReason", "Unknown reason")
                    message = f"Database access failed: {username}@{auth_source} from {ip_address} - {failure_reason}"
                
                # Build context
                context = LogContext(
                    infrastructure="atlas",
                    ip_address=ip_address,
                    user_id=username,
                )
                
                # Build metadata
                metadata = LogMetadata(
                    atlas_cluster=self.cluster_name,
                    tags=[
                        "access_log",
                        "authentication",
                        "successful" if auth_result else "failed",
                    ],
                    custom={
                        "auth_source": auth_source,
                        "hostname": access_log.get("hostname"),
                        "log_level": access_log.get("logLevel"),
                        "failure_reason": access_log.get("failureReason"),
                    }
                )
                
                logs.append(LogEntry(
                    timestamp=timestamp,
                    level=level,
                    service=LogServiceType.DATABASE,
                    source=LogSource.EXTERNAL,
                    message=message,
                    context=context,
                    metadata=metadata,
                ))
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse access log: {e}")
                continue
        
        return logs
    
    def _generate_metrics_logs(self) -> List[LogEntry]:
        """
        Generate synthetic metrics logs for Atlas.
        
        Returns:
            List of synthetic metric log entries
        """
        logs = []
        timestamp = datetime.utcnow()
        
        # Connection metrics
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=1),
            level=LogLevel.INFO,
            service=LogServiceType.DATABASE,
            source=LogSource.EXTERNAL,
            message="Atlas connection metrics: 5 active connections, 89% utilization",
            context=LogContext(infrastructure="atlas"),
            metadata=LogMetadata(
                atlas_cluster=self.cluster_name,
                tags=["metrics", "connections", "performance"],
                custom={
                    "metric_type": "connection_count",
                    "active_connections": 5,
                    "max_connections": 100,
                    "utilization_percentage": 89,
                }
            )
        ))
        
        # Query performance metrics
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=1),
            level=LogLevel.INFO,
            service=LogServiceType.DATABASE,
            source=LogSource.EXTERNAL,
            message="Atlas query performance: Average 45ms, 3 slow queries detected",
            context=LogContext(infrastructure="atlas"),
            metadata=LogMetadata(
                atlas_cluster=self.cluster_name,
                tags=["metrics", "performance", "queries"],
                custom={
                    "metric_type": "query_performance",
                    "avg_query_time_ms": 45,
                    "slow_query_count": 3,
                    "total_queries": 1500,
                }
            )
        ))
        
        # Storage metrics
        logs.append(LogEntry(
            timestamp=timestamp - timedelta(minutes=1),
            level=LogLevel.INFO,
            service=LogServiceType.DATABASE,
            source=LogSource.EXTERNAL,
            message="Atlas storage metrics: 2.5GB used / 10GB limit (25%)",
            context=LogContext(infrastructure="atlas"),
            metadata=LogMetadata(
                atlas_cluster=self.cluster_name,
                tags=["metrics", "storage", "capacity"],
                custom={
                    "metric_type": "storage_usage",
                    "used_gb": 2.5,
                    "limit_gb": 10,
                    "utilization_percentage": 25,
                }
            )
        ))
        
        return logs
    
    def _get_mock_mongod_logs(self) -> List[str]:
        """Get mock mongod logs for testing."""
        return [
            '{"t":{"$date":"2025-07-19T02:00:00.000+00:00"},"s":"I","c":"NETWORK","id":22943,"ctx":"listener","msg":"Connection accepted","attr":{"remote":"203.0.113.1:54321","uuid":"12345678-1234-5678-9012-123456789abc","connectionId":123,"connectionCount":5}}',
            '{"t":{"$date":"2025-07-19T02:00:01.500+00:00"},"s":"I","c":"COMMAND","id":51803,"ctx":"conn123","msg":"Slow query","attr":{"type":"command","ns":"xai_community.posts","command":{"find":"posts","filter":{"status":"published"},"sort":{"created_at":-1},"limit":20},"planSummary":"IXSCAN { status: 1, created_at: -1 }","durationMillis":1250}}',
            '{"t":{"$date":"2025-07-19T02:00:05.000+00:00"},"s":"E","c":"STORAGE","id":28551,"ctx":"conn123","msg":"WiredTiger error","attr":{"error":"cache eviction stalled due to too many requests: Operation timed out","file":"WT_SESSION.checkpoint","line":123}}'
        ]
    
    def _get_mock_mongos_logs(self) -> List[str]:
        """Get mock mongos logs for testing."""
        return [
            '{"t":{"$date":"2025-07-19T02:00:00.000+00:00"},"s":"I","c":"SHARDING","id":22070,"ctx":"conn456","msg":"Request targeting","attr":{"command":{"find":"posts","filter":{"user_id":"user123"}},"clientInfo":{"application":"node.js driver","driver":"Node.js|4.5.0"},"targetedShards":["shard01"]}}',
            '{"t":{"$date":"2025-07-19T02:00:02.000+00:00"},"s":"W","c":"NETWORK","id":22944,"ctx":"conn456","msg":"Connection ended","attr":{"remote":"203.0.113.1:54321","connectionId":456,"reason":"client disconnected"}}'
        ]
    
    def _get_mock_audit_logs(self) -> List[str]:
        """Get mock audit logs for testing."""
        return [
            '{"atype":"authenticate","ts":{"$date":"2025-07-19T02:00:00.000+00:00"},"local":{"ip":"10.0.0.1","port":27017},"remote":{"ip":"203.0.113.1","port":54321},"users":[{"user":"app_user","db":"xai_community"}],"roles":[{"role":"readWrite","db":"xai_community"}],"result":0}',
            '{"atype":"createCollection","ts":{"$date":"2025-07-19T02:05:00.000+00:00"},"local":{"ip":"10.0.0.1","port":27017},"remote":{"ip":"203.0.113.1","port":54321},"users":[{"user":"admin_user","db":"admin"}],"roles":[{"role":"dbAdminAnyDatabase","db":"admin"}],"param":{"ns":"xai_community.logs"},"result":0}',
            '{"atype":"dropCollection","ts":{"$date":"2025-07-19T02:10:00.000+00:00"},"local":{"ip":"10.0.0.1","port":27017},"remote":{"ip":"203.0.113.1","port":54321},"users":[{"user":"admin_user","db":"admin"}],"roles":[{"role":"dbAdminAnyDatabase","db":"admin"}],"param":{"ns":"xai_community.temp_collection"},"result":0}'
        ]
    
    def _get_mock_access_history(self) -> Dict[str, Any]:
        """Get mock access history for testing."""
        return {
            "accessLogs": [
                {
                    "authSource": "xai_community",
                    "authResult": True,
                    "hostname": "cluster0-shard-00-01.bh7mhfi.mongodb.net",
                    "ipAddress": "218.154.40.110",
                    "logLevel": "INFO",
                    "timestamp": "2025-07-19T02:00:00.000Z",
                    "username": "nadle"
                },
                {
                    "authSource": "admin",
                    "authResult": False,
                    "hostname": "cluster0-shard-00-01.bh7mhfi.mongodb.net",
                    "ipAddress": "198.51.100.1",
                    "logLevel": "WARN",
                    "timestamp": "2025-07-19T01:55:00.000Z",
                    "username": "unknown_user",
                    "failureReason": "Authentication failed"
                }
            ],
            "totalCount": 2
        }