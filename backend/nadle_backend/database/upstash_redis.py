"""Upstash Redis REST API 클라이언트"""

import aiohttp
import json
import logging
from typing import Optional, Any, Dict
from ..config import get_settings

logger = logging.getLogger(__name__)


class UpstashRedisManager:
    """Upstash Redis REST API 기반 Redis 매니저
    
    기존 RedisManager와 동일한 인터페이스를 제공하면서
    Upstash REST API를 사용하여 작업을 수행합니다.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
        # 시작 시 한 번만 설정 로드 (운영 환경에서는 변경되지 않음)
        self.rest_url = getattr(self.settings, 'upstash_redis_rest_url', None)
        self.rest_token = getattr(self.settings, 'upstash_redis_rest_token', None)
        
    async def connect(self) -> bool:
        """Upstash Redis REST API에 연결"""
        if not self.settings.cache_enabled:
            logger.info("Redis 캐시가 비활성화되어 있습니다.")
            return False
            
        if not self.rest_url or not self.rest_token:
            logger.warning("Upstash Redis 설정이 없습니다. (UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN)")
            return False
        
        try:
            # HTTP 세션 생성
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.rest_token}',
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            # 연결 테스트 (PING)
            result = await self._request(["PING"])
            if result.get("result") == "PONG":
                self._connected = True
                logger.info(f"Upstash Redis 연결 성공: {self.rest_url}")
                return True
            else:
                logger.warning(f"Upstash Redis PING 실패: {result}")
                return False
                
        except Exception as e:
            logger.warning(f"Upstash Redis 연결 실패: {e}")
            self._connected = False
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def disconnect(self):
        """Upstash Redis 연결 종료"""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False
        logger.info("Upstash Redis 연결 종료")
    
    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 - 세션 정리"""
        await self.disconnect()
    
    async def is_connected(self) -> bool:
        """Upstash Redis 연결 상태 확인"""
        if not self._connected or not self.session:
            return False
        
        try:
            result = await self._request(["PING"])
            is_ok = result.get("result") == "PONG"
            if not is_ok:
                self._connected = False
            return is_ok
        except:
            self._connected = False
            return False
    
    async def _request(self, command: list) -> Dict[str, Any]:
        """Upstash REST API 요청 수행"""
        if not self.session:
            raise RuntimeError("Upstash Redis 세션이 초기화되지 않았습니다. connect()를 먼저 호출하세요.")
        
        url = self.rest_url.rstrip('/')
        
        try:
            async with self.session.post(url, json=command) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"Upstash API Error: {response.status} - {result}")
                    raise Exception(f"Upstash API Error: {response.status} - {result}")
                    
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Upstash 요청 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"Upstash 요청 처리 오류: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if not await self.is_connected():
            return None
        
        try:
            result = await self._request(["GET", key])
            value = result.get("result")
            
            if value is None:
                return None
            
            # JSON 파싱 시도
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Upstash GET 오류 - key: {key}, error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 값 저장"""
        if not await self.is_connected():
            return False
        
        try:
            # 값을 JSON으로 직렬화
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            # TTL과 함께 SET 명령 실행
            command = ["SET", key, value]
            if ttl and ttl > 0:
                command.extend(["EX", str(ttl)])
            
            result = await self._request(command)
            return result.get("result") == "OK"
            
        except Exception as e:
            logger.error(f"Upstash SET 오류 - key: {key}, error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        if not await self.is_connected():
            return False
        
        try:
            result = await self._request(["DEL", key])
            return result.get("result", 0) > 0
            
        except Exception as e:
            logger.error(f"Upstash DELETE 오류 - key: {key}, error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """캐시에 키가 존재하는지 확인"""
        if not await self.is_connected():
            return False
        
        try:
            result = await self._request(["EXISTS", key])
            return result.get("result", 0) > 0
            
        except Exception as e:
            logger.error(f"Upstash EXISTS 오류 - key: {key}, error: {e}")
            return False
    
    async def health_check(self) -> dict:
        """Upstash Redis 상태 확인"""
        if not self.settings.cache_enabled:
            return {
                "status": "disabled",
                "message": "Redis 캐시가 비활성화되어 있습니다."
            }
        
        if not self.rest_url or not self.rest_token:
            return {
                "status": "misconfigured",
                "message": "Upstash Redis 설정이 없습니다."
            }
        
        try:
            if await self.is_connected():
                # Upstash Redis 정보 조회
                info_result = await self._request(["INFO"])
                info_str = info_result.get("result", "")
                
                # INFO 결과 파싱
                info_dict = {}
                for line in info_str.split('\n'):
                    if ':' in line and not line.startswith('#'):
                        key, value = line.split(':', 1)
                        info_dict[key.strip()] = value.strip()
                
                return {
                    "status": "connected",
                    "provider": "upstash",
                    "redis_version": info_dict.get("redis_version", "unknown"),
                    "used_memory": info_dict.get("used_memory_human", "unknown"),
                    "connected_clients": info_dict.get("connected_clients", "0"),
                    "total_commands_processed": info_dict.get("total_commands_processed", "0"),
                    "uptime_in_seconds": info_dict.get("uptime_in_seconds", "0")
                }
            else:
                return {
                    "status": "disconnected",
                    "provider": "upstash",
                    "message": "Upstash Redis 서버에 연결할 수 없습니다."
                }
        except Exception as e:
            return {
                "status": "error",
                "provider": "upstash",
                "message": f"Upstash Redis 상태 확인 중 오류: {str(e)}"
            }


# 글로벌 Upstash Redis 매니저 인스턴스
upstash_redis_manager = UpstashRedisManager()


async def get_upstash_redis_manager() -> UpstashRedisManager:
    """Upstash Redis 매니저 인스턴스 반환"""
    return upstash_redis_manager