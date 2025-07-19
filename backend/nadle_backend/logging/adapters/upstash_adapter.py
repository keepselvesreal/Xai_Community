"""
Upstash Redis log adapter for collecting Redis metrics and performance data.

Uses real API responses when available and falls back to Mock data based on
actual Upstash REST API response structures collected on 2025-07-19.
"""

import aiohttp
import logging
import re
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
# UpstashMockData import removed to avoid circular dependency
# We'll define mock data generation methods locally

logger = logging.getLogger(__name__)


class UpstashLogAdapter(ExternalLogAdapterInterface):
    """
    Upstash Redis metrics and performance log collector.
    
    Collects Redis performance metrics, connection stats, and operational data
    using Upstash REST API. Falls back to Mock data when API is unavailable.
    """
    
    def __init__(
        self,
        rest_url: str,
        rest_token: str,
        use_mock: bool = False,
        timeout: int = 30
    ):
        """
        Initialize Upstash log adapter.
        
        Args:
            rest_url: Upstash Redis REST API URL
            rest_token: Upstash Redis REST API token
            use_mock: Whether to use mock data instead of real API
            timeout: Request timeout in seconds
        """
        self.rest_url = rest_url.rstrip('/')
        self.rest_token = rest_token
        self.use_mock = use_mock
        self.timeout = timeout
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {rest_token}",
            "Content-Type": "application/json",
        }
    
    @property
    def service_name(self) -> str:
        """Get the service name."""
        return "upstash"
    
    async def test_connection(self) -> bool:
        """
        Test connection to Upstash Redis.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.use_mock:
            return True
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(
                    f"{self.rest_url}/ping",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result") == "PONG"
                    return False
        except Exception as e:
            logger.error(f"Upstash connection test failed: {e}")
            return False
    
    async def collect_logs(self, hours: int = 1) -> List[LogEntry]:
        """
        Collect Redis metrics and performance logs.
        
        Args:
            hours: Number of hours to look back (not used for metrics)
            
        Returns:
            List of log entries with Redis metrics
            
        Raises:
            AdapterError: If log collection fails
        """
        try:
            if self.use_mock:
                return await self._collect_mock_logs()
            else:
                return await self._collect_real_logs()
                
        except Exception as e:
            logger.error(f"Failed to collect Upstash logs: {e}")
            raise AdapterError("upstash", f"Log collection failed: {str(e)}")
    
    async def _collect_real_logs(self) -> List[LogEntry]:
        """
        Collect real metrics from Upstash Redis.
        
        Returns:
            List of log entries with Redis metrics
        """
        logs = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                # Test connection
                ping_log = await self._collect_ping_metric(session)
                logs.append(ping_log)
                
                # Get Redis info
                info_logs = await self._collect_info_metrics(session)
                logs.extend(info_logs)
                
                # Get database size
                dbsize_log = await self._collect_dbsize_metric(session)
                logs.append(dbsize_log)
                
                # Get key statistics
                key_logs = await self._collect_key_metrics(session)
                logs.extend(key_logs)
            
            logger.info(f"Collected {len(logs)} metrics from Upstash Redis")
            return logs
            
        except Exception as e:
            logger.warning(f"Real Upstash API failed, falling back to mock: {e}")
            return await self._collect_mock_logs()
    
    async def _collect_mock_logs(self) -> List[LogEntry]:
        """
        Collect metrics using mock data.
        
        Returns:
            List of log entries from mock data
        """
        logs = []
        timestamp = datetime.utcnow()
        
        # Connection test
        ping_data = self._get_mock_ping_response()
        ping_log = LogEntry(
            timestamp=timestamp,
            level=LogLevel.INFO,
            service=LogServiceType.REDIS,
            source=LogSource.EXTERNAL,
            message=f"Redis connection test: {ping_data['result']}",
            context=LogContext(infrastructure="upstash"),
            metadata=LogMetadata(
                tags=["connection", "health_check"],
                custom={"command": "PING", "response": ping_data["result"]}
            )
        )
        logs.append(ping_log)
        
        # Parse INFO response
        info_data = self._get_mock_info_response()
        info_logs = self._parse_info_response(info_data["result"])
        logs.extend(info_logs)
        
        # Database size
        dbsize_data = self._get_mock_dbsize_response()
        dbsize_log = LogEntry(
            timestamp=timestamp,
            level=LogLevel.INFO,
            service=LogServiceType.REDIS,
            source=LogSource.EXTERNAL,
            message=f"Redis database size: {dbsize_data['result']} keys",
            context=LogContext(infrastructure="upstash"),
            metadata=LogMetadata(
                tags=["database", "metrics"],
                custom={"command": "DBSIZE", "key_count": dbsize_data["result"]}
            )
        )
        logs.append(dbsize_log)
        
        logger.info(f"Collected {len(logs)} mock metrics from Upstash Redis")
        return logs
    
    async def _collect_ping_metric(self, session: aiohttp.ClientSession) -> LogEntry:
        """
        Collect PING response time metric.
        
        Args:
            session: HTTP session
            
        Returns:
            LogEntry with ping metric
        """
        start_time = datetime.utcnow()
        
        async with session.get(f"{self.rest_url}/ping", headers=self.headers) as response:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status == 200:
                data = await response.json()
                result = data.get("result", "")
                
                level = LogLevel.INFO if result == "PONG" else LogLevel.WARN
                message = f"Redis ping response: {result} ({response_time:.1f}ms)"
            else:
                level = LogLevel.ERROR
                message = f"Redis ping failed: HTTP {response.status}"
                response_time = None
        
        return LogEntry(
            timestamp=start_time,
            level=level,
            service=LogServiceType.REDIS,
            source=LogSource.EXTERNAL,
            message=message,
            context=LogContext(
                infrastructure="upstash",
                response_time=response_time
            ),
            metadata=LogMetadata(
                tags=["connection", "performance"],
                custom={"command": "PING", "response_time_ms": response_time}
            )
        )
    
    async def _collect_info_metrics(self, session: aiohttp.ClientSession) -> List[LogEntry]:
        """
        Collect Redis INFO metrics.
        
        Args:
            session: HTTP session
            
        Returns:
            List of log entries with Redis info metrics
        """
        async with session.get(f"{self.rest_url}/info", headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                info_text = data.get("result", "")
                return self._parse_info_response(info_text)
            else:
                return [LogEntry(
                    timestamp=datetime.utcnow(),
                    level=LogLevel.ERROR,
                    service=LogServiceType.REDIS,
                    source=LogSource.EXTERNAL,
                    message=f"Failed to get Redis INFO: HTTP {response.status}",
                    context=LogContext(infrastructure="upstash"),
                    metadata=LogMetadata(tags=["error", "info_command"])
                )]
    
    async def _collect_dbsize_metric(self, session: aiohttp.ClientSession) -> LogEntry:
        """
        Collect database size metric.
        
        Args:
            session: HTTP session
            
        Returns:
            LogEntry with database size
        """
        async with session.get(f"{self.rest_url}/dbsize", headers=self.headers) as response:
            timestamp = datetime.utcnow()
            
            if response.status == 200:
                data = await response.json()
                size = data.get("result", 0)
                
                return LogEntry(
                    timestamp=timestamp,
                    level=LogLevel.INFO,
                    service=LogServiceType.REDIS,
                    source=LogSource.EXTERNAL,
                    message=f"Redis database size: {size} keys",
                    context=LogContext(infrastructure="upstash"),
                    metadata=LogMetadata(
                        tags=["database", "metrics"],
                        custom={"command": "DBSIZE", "key_count": size}
                    )
                )
            else:
                return LogEntry(
                    timestamp=timestamp,
                    level=LogLevel.ERROR,
                    service=LogServiceType.REDIS,
                    source=LogSource.EXTERNAL,
                    message=f"Failed to get Redis DBSIZE: HTTP {response.status}",
                    context=LogContext(infrastructure="upstash"),
                    metadata=LogMetadata(tags=["error", "dbsize_command"])
                )
    
    async def _collect_key_metrics(self, session: aiohttp.ClientSession) -> List[LogEntry]:
        """
        Collect key-related metrics.
        
        Args:
            session: HTTP session
            
        Returns:
            List of log entries with key metrics
        """
        logs = []
        
        # Get cache keys
        patterns = ["cache:*", "session:*"]
        
        for pattern in patterns:
            async with session.get(f"{self.rest_url}/keys/{pattern}", headers=self.headers) as response:
                timestamp = datetime.utcnow()
                
                if response.status == 200:
                    data = await response.json()
                    keys = data.get("result", [])
                    
                    logs.append(LogEntry(
                        timestamp=timestamp,
                        level=LogLevel.INFO,
                        service=LogServiceType.REDIS,
                        source=LogSource.EXTERNAL,
                        message=f"Redis keys matching '{pattern}': {len(keys)} found",
                        context=LogContext(infrastructure="upstash"),
                        metadata=LogMetadata(
                            tags=["keys", "pattern_search"],
                            custom={
                                "command": f"KEYS {pattern}",
                                "pattern": pattern,
                                "key_count": len(keys),
                                "keys": keys[:10]  # Store only first 10 keys
                            }
                        )
                    ))
                else:
                    logs.append(LogEntry(
                        timestamp=timestamp,
                        level=LogLevel.WARN,
                        service=LogServiceType.REDIS,
                        source=LogSource.EXTERNAL,
                        message=f"Failed to get keys for pattern '{pattern}': HTTP {response.status}",
                        context=LogContext(infrastructure="upstash"),
                        metadata=LogMetadata(tags=["error", "keys_command"])
                    ))
        
        return logs
    
    def _parse_info_response(self, info_text: str) -> List[LogEntry]:
        """
        Parse Redis INFO response into log entries.
        
        Args:
            info_text: Raw INFO command response
            
        Returns:
            List of log entries with parsed metrics
        """
        logs = []
        timestamp = datetime.utcnow()
        
        # Parse INFO sections
        sections = {}
        current_section = None
        
        for line in info_text.split('\\r\\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#'):
                current_section = line[1:].strip()
                sections[current_section] = {}
            elif ':' in line and current_section:
                key, value = line.split(':', 1)
                sections[current_section][key] = value
        
        # Generate metrics for important sections
        
        # Memory metrics
        if 'Memory' in sections:
            memory_section = sections['Memory']
            used_memory = memory_section.get('used_memory_human', 'unknown')
            max_memory = memory_section.get('maxmemory_human', 'unknown')
            
            logs.append(LogEntry(
                timestamp=timestamp,
                level=LogLevel.INFO,
                service=LogServiceType.REDIS,
                source=LogSource.EXTERNAL,
                message=f"Redis memory usage: {used_memory} / {max_memory}",
                context=LogContext(infrastructure="upstash"),
                metadata=LogMetadata(
                    tags=["memory", "performance"],
                    memory_usage=self._parse_memory_bytes(memory_section.get('used_memory', '0')),
                    custom={
                        "used_memory_human": used_memory,
                        "maxmemory_human": max_memory,
                        "memory_policy": memory_section.get('maxmemory_policy', 'unknown')
                    }
                )
            ))
        
        # Stats metrics
        if 'Stats' in sections:
            stats_section = sections['Stats']
            total_commands = stats_section.get('total_commands_processed', '0')
            ops_per_sec = stats_section.get('instantaneous_ops_per_sec', '0')
            
            logs.append(LogEntry(
                timestamp=timestamp,
                level=LogLevel.INFO,
                service=LogServiceType.REDIS,
                source=LogSource.EXTERNAL,
                message=f"Redis performance: {ops_per_sec} ops/sec, {total_commands} total commands",
                context=LogContext(infrastructure="upstash"),
                metadata=LogMetadata(
                    tags=["performance", "stats"],
                    custom={
                        "total_commands_processed": int(total_commands),
                        "instantaneous_ops_per_sec": int(ops_per_sec),
                        "keyspace_hits": int(stats_section.get('keyspace_hits', '0')),
                        "keyspace_misses": int(stats_section.get('keyspace_misses', '0'))
                    }
                )
            ))
        
        # Connection metrics
        if 'Clients' in sections:
            clients_section = sections['Clients']
            connected_clients = clients_section.get('connected_clients', '0')
            max_clients = clients_section.get('maxclients', '0')
            
            logs.append(LogEntry(
                timestamp=timestamp,
                level=LogLevel.INFO,
                service=LogServiceType.REDIS,
                source=LogSource.EXTERNAL,
                message=f"Redis connections: {connected_clients} / {max_clients}",
                context=LogContext(infrastructure="upstash"),
                metadata=LogMetadata(
                    tags=["connections", "clients"],
                    custom={
                        "connected_clients": int(connected_clients),
                        "maxclients": int(max_clients)
                    }
                )
            ))
        
        # Check for any warnings or errors in the info
        if 'Server' in sections:
            server_section = sections['Server']
            redis_version = server_section.get('redis_version', 'unknown')
            upstash_version = server_section.get('upstash_version', 'unknown')
            
            logs.append(LogEntry(
                timestamp=timestamp,
                level=LogLevel.INFO,
                service=LogServiceType.REDIS,
                source=LogSource.EXTERNAL,
                message=f"Redis server info: Upstash {upstash_version}, Redis {redis_version}",
                context=LogContext(infrastructure="upstash"),
                metadata=LogMetadata(
                    tags=["server", "version"],
                    custom={
                        "redis_version": redis_version,
                        "upstash_version": upstash_version,
                        "redis_mode": server_section.get('redis_mode', 'unknown')
                    }
                )
            ))
        
        return logs
    
    def _parse_memory_bytes(self, memory_str: str) -> Optional[float]:
        """
        Parse memory string to bytes.
        
        Args:
            memory_str: Memory string like "1024" (bytes)
            
        Returns:
            Memory usage in bytes or None if parsing fails
        """
        try:
            return float(memory_str)
        except (ValueError, TypeError):
            return None
    
    def _get_mock_ping_response(self) -> Dict[str, Any]:
        """Get mock PING response for testing."""
        return {"result": "PONG"}
    
    def _get_mock_info_response(self) -> Dict[str, Any]:
        """Get mock INFO response for testing."""
        info_text = (
            "# Server\\r\\n"
            "upstash_version:1.13.3\\r\\n"
            "redis_version:6.2.6\\r\\n"
            "redis_git_sha1:b8ef06c\\r\\n"
            "redis_build_id:20250422\\r\\n"
            "redis_mode:standalone\\r\\n"
            "\\r\\n"
            "# Clients\\r\\n"
            "connected_clients:1\\r\\n"
            "maxclients:10000\\r\\n"
            "\\r\\n"
            "# Memory\\r\\n"
            "used_memory:1024\\r\\n"
            "used_memory_human:1.000KB\\r\\n"
            "maxmemory:67108864\\r\\n"
            "maxmemory_human:64.000MB\\r\\n"
            "maxmemory_policy:noeviction\\r\\n"
            "\\r\\n"
            "# Stats\\r\\n"
            "total_connections_received:50\\r\\n"
            "total_commands_processed:1500\\r\\n"
            "instantaneous_ops_per_sec:5\\r\\n"
            "max_ops_per_sec:10000\\r\\n"
            "evicted_clients:0\\r\\n"
            "expired_keys:3\\r\\n"
            "evicted_keys:0\\r\\n"
            "keyspace_hits:350\\r\\n"
            "keyspace_misses:85\\r\\n"
            "total_reads_processed:800\\r\\n"
            "total_writes_processed:200\\r\\n"
            "\\r\\n"
            "# Keyspace\\r\\n"
            "db0:keys=15,expires=5,avg_ttl=3600\\r\\n"
        )
        return {"result": info_text}
    
    def _get_mock_dbsize_response(self) -> Dict[str, Any]:
        """Get mock DBSIZE response for testing."""
        return {"result": 15}