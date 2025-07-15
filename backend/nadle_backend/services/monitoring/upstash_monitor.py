"""
Upstash Redis 모니터링 서비스

Upstash REST API와 Database Stats API를 사용하여
Redis 캐시 성능, 사용량, 연결 상태를 모니터링
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
import aiohttp
import base64

from ...config import get_settings
from ...models.monitoring.monitoring_models import UpstashMetrics, ServiceStatus, MonitoringError


logger = logging.getLogger(__name__)


class UpstashMonitoringService:
    """Upstash Redis 모니터링 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self._rest_url = self.settings.upstash_redis_rest_url
        self._rest_token = self.settings.upstash_redis_rest_token
        self._email = self.settings.upstash_email
        self._api_key = self.settings.upstash_api_key
        self._database_id = self.settings.upstash_database_id
        self._console_base_url = "https://api.upstash.com"
        self._session = None
        self._console_session = None
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        if self._session is None:
            # REST API 세션
            headers = {
                "Authorization": f"Bearer {self._rest_token}",
                "Content-Type": "application/json"
            }
            self._session = aiohttp.ClientSession(headers=headers)
        
        if self._console_session is None and self._email and self._api_key:
            # Console API 세션 (Dashboard API)
            auth_string = f"{self._email}:{self._api_key}"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')
            
            console_headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json"
            }
            self._console_session = aiohttp.ClientSession(headers=console_headers)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self._session:
            await self._session.close()
            self._session = None
        
        if self._console_session:
            await self._console_session.close()
            self._console_session = None
    
    async def get_redis_status(self) -> ServiceStatus:
        """Upstash Redis 상태 확인"""
        try:
            if not self._rest_url or not self._rest_token:
                logger.warning("Upstash Redis 설정이 불완전합니다")
                return ServiceStatus.UNKNOWN
            
            async with self as service:
                # PING 명령으로 기본 연결 확인
                ping_result = await service._execute_redis_command("PING")
                
                if ping_result == "PONG":
                    return ServiceStatus.HEALTHY
                else:
                    return ServiceStatus.UNHEALTHY
                    
        except Exception as e:
            logger.error(f"Upstash Redis 상태 확인 실패: {e}")
            return ServiceStatus.UNKNOWN
    
    async def _execute_redis_command(self, command: str, *args) -> Any:
        """Redis 명령 실행"""
        try:
            # Upstash REST API 명령 형식
            command_list = [command] + list(args)
            
            async with self._session.post(self._rest_url, json=command_list) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('result')
                else:
                    logger.debug(f"Redis 명령 실행 실패: {response.status}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Redis 명령 '{command}' 실행 실패: {e}")
            return None
    
    async def _get_database_stats(self) -> Optional[Dict[str, Any]]:
        """데이터베이스 통계 조회 (Console API)"""
        try:
            if not self._console_session or not self._database_id:
                logger.debug("Console API 설정이 없어 통계 조회 건너뜀")
                return None
            
            url = f"{self._console_base_url}/v2/redis/database/{self._database_id}/stats"
            
            async with self._console_session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.debug(f"데이터베이스 통계 조회 실패: {response.status}")
                    error_text = await response.text()
                    logger.debug(f"오류 내용: {error_text}")
                    return None
                    
        except Exception as e:
            logger.debug(f"데이터베이스 통계 조회 실패: {e}")
            return None
    
    async def _get_database_info(self) -> Optional[Dict[str, Any]]:
        """데이터베이스 정보 조회 (Console API)"""
        try:
            if not self._console_session or not self._database_id:
                return None
            
            url = f"{self._console_base_url}/v2/redis/database/{self._database_id}"
            
            async with self._console_session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.debug(f"데이터베이스 정보 조회 실패: {response.status}")
                    return None
                    
        except Exception as e:
            logger.debug(f"데이터베이스 정보 조회 실패: {e}")
            return None
    
    async def get_metrics(self) -> UpstashMetrics:
        """Upstash Redis 메트릭 수집"""
        try:
            async with self as service:
                status = await service.get_redis_status()
                
                # 기본 메트릭 데이터
                metrics_data = {
                    "database_id": self._database_id or "unknown",
                    "status": status
                }
                
                # 데이터베이스 정보
                db_info = await service._get_database_info()
                if db_info:
                    metrics_data.update({
                        "database_name": db_info.get('database_name'),
                        "region": db_info.get('region'),
                        "max_connections": db_info.get('max_connections')
                    })
                
                # Console API 통계 (사용 가능한 경우)
                db_stats = await service._get_database_stats()
                if db_stats:
                    await service._extract_console_metrics(db_stats, metrics_data)
                
                # REST API를 통한 실시간 메트릭
                await service._collect_runtime_metrics(metrics_data)
                
                # 성능 측정
                response_time = await service._measure_response_time()
                if response_time:
                    metrics_data["response_time_ms"] = response_time
                
                metrics = UpstashMetrics(**metrics_data)
                logger.info(f"Upstash Redis 메트릭 수집 완료: {self._database_id}")
                return metrics
                
        except Exception as e:
            logger.error(f"Upstash Redis 메트릭 수집 실패: {e}")
            return UpstashMetrics(
                database_id=self._database_id or "unknown",
                status=ServiceStatus.UNKNOWN,
                error_message=str(e)
            )
    
    async def _extract_console_metrics(self, stats: Dict[str, Any], metrics_data: Dict[str, Any]):
        """Console API 통계에서 메트릭 추출"""
        try:
            # 연결 수
            if 'connections' in stats:
                metrics_data["connection_count"] = stats['connections']
            
            # 키스페이스
            if 'keyspace' in stats:
                metrics_data["keyspace"] = stats['keyspace']
            
            # 메모리 사용량
            if 'memory_usage' in stats:
                metrics_data["memory_usage_bytes"] = stats['memory_usage']
            
            # 처리량
            if 'throughput' in stats:
                throughput = stats['throughput']
                if isinstance(throughput, dict):
                    metrics_data["throughput_reads"] = throughput.get('reads', 0)
                    metrics_data["throughput_writes"] = throughput.get('writes', 0)
                    
                    # 전체 OPS 계산
                    total_ops = throughput.get('reads', 0) + throughput.get('writes', 0)
                    metrics_data["operations_per_second"] = total_ops
            
            # 지연시간
            if 'latency' in stats:
                latency = stats['latency']
                if isinstance(latency, dict):
                    metrics_data["read_latency_ms"] = latency.get('read', 0)
                    metrics_data["write_latency_ms"] = latency.get('write', 0)
                    metrics_data["read_latency_p99_ms"] = latency.get('read_p99', 0)
                    metrics_data["write_latency_p99_ms"] = latency.get('write_p99', 0)
            
            # Hit/Miss Rate
            if 'hit_rate' in stats:
                metrics_data["hit_rate"] = stats['hit_rate']
                metrics_data["miss_rate"] = 100 - stats['hit_rate']  # Hit rate에서 계산
            
            # 대역폭
            if 'bandwidth' in stats:
                bandwidth = stats['bandwidth']
                if isinstance(bandwidth, dict):
                    metrics_data["bandwidth_in_bytes"] = bandwidth.get('in', 0)
                    metrics_data["bandwidth_out_bytes"] = bandwidth.get('out', 0)
            
            # 메모리 한계 및 사용률
            if 'memory_limit' in stats:
                memory_limit = stats['memory_limit']
                memory_usage = metrics_data.get('memory_usage_bytes', 0)
                
                metrics_data["memory_limit_bytes"] = memory_limit
                
                if memory_limit > 0:
                    usage_percent = (memory_usage / memory_limit) * 100
                    metrics_data["memory_usage_percent"] = min(100, usage_percent)
                    
        except Exception as e:
            logger.debug(f"Console 메트릭 추출 실패: {e}")
    
    async def _collect_runtime_metrics(self, metrics_data: Dict[str, Any]):
        """런타임 메트릭 수집 (REST API 사용)"""
        try:
            # INFO 명령으로 서버 정보 조회
            info_result = await self._execute_redis_command("INFO")
            if info_result:
                await self._parse_info_command(info_result, metrics_data)
            
            # DBSIZE로 키 개수 확인
            dbsize = await self._execute_redis_command("DBSIZE")
            if dbsize is not None:
                metrics_data["keyspace"] = int(dbsize)
            
            # 간단한 성능 테스트
            await self._run_simple_performance_test(metrics_data)
            
        except Exception as e:
            logger.debug(f"런타임 메트릭 수집 실패: {e}")
    
    async def _parse_info_command(self, info_text: str, metrics_data: Dict[str, Any]):
        """INFO 명령 결과 파싱"""
        try:
            if not isinstance(info_text, str):
                return
            
            lines = info_text.split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 유용한 메트릭 추출
                    if key == 'connected_clients':
                        metrics_data["connection_count"] = int(value)
                    elif key == 'used_memory':
                        metrics_data["memory_usage_bytes"] = int(value)
                    elif key == 'maxmemory':
                        if int(value) > 0:
                            metrics_data["memory_limit_bytes"] = int(value)
                    elif key == 'keyspace_hits':
                        hits = int(value)
                        # Miss 정보와 함께 Hit Rate 계산
                        misses = 0
                        for line2 in lines:
                            if 'keyspace_misses:' in line2:
                                misses = int(line2.split(':')[1].strip())
                                break
                        
                        total = hits + misses
                        if total > 0:
                            metrics_data["hit_rate"] = (hits / total) * 100
                            metrics_data["miss_rate"] = (misses / total) * 100
                            
        except Exception as e:
            logger.debug(f"INFO 명령 파싱 실패: {e}")
    
    async def _run_simple_performance_test(self, metrics_data: Dict[str, Any]):
        """간단한 성능 테스트"""
        try:
            test_key = f"__perf_test_{int(datetime.utcnow().timestamp())}"
            test_value = "performance_test_value"
            
            # 쓰기 성능 측정
            start_time = asyncio.get_event_loop().time()
            await self._execute_redis_command("SET", test_key, test_value, "EX", "5")  # 5초 TTL
            write_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # 읽기 성능 측정
            start_time = asyncio.get_event_loop().time()
            result = await self._execute_redis_command("GET", test_key)
            read_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if result == test_value:
                # 성능이 이미 Console API에서 설정되지 않은 경우에만 설정
                if "read_latency_ms" not in metrics_data:
                    metrics_data["read_latency_ms"] = read_time
                if "write_latency_ms" not in metrics_data:
                    metrics_data["write_latency_ms"] = write_time
            
            # 테스트 키 정리
            await self._execute_redis_command("DEL", test_key)
            
        except Exception as e:
            logger.debug(f"성능 테스트 실패: {e}")
    
    async def _measure_response_time(self) -> Optional[float]:
        """응답 시간 측정"""
        try:
            start_time = asyncio.get_event_loop().time()
            result = await self._execute_redis_command("PING")
            end_time = asyncio.get_event_loop().time()
            
            if result == "PONG":
                return (end_time - start_time) * 1000  # milliseconds
            else:
                return None
                
        except Exception as e:
            logger.debug(f"응답 시간 측정 실패: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Upstash Redis 헬스체크"""
        try:
            async with self as service:
                status = await service.get_redis_status()
                
                return {
                    "service": "upstash_redis",
                    "status": status.value,
                    "database_id": self._database_id,
                    "rest_url": self._rest_url.split('@')[-1] if self._rest_url else None,  # 민감 정보 제거
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Upstash Redis 헬스체크 실패: {e}")
            return {
                "service": "upstash_redis",
                "status": ServiceStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def is_configured(self) -> bool:
        """Upstash Redis 모니터링 설정 여부 확인"""
        # REST API는 필수, Console API는 선택사항
        return all([
            self._rest_url,
            self._rest_token
        ])