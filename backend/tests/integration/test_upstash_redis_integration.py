#!/usr/bin/env python3
"""Upstash Redis REST API 통합 테스트"""

import asyncio
import aiohttp
import json
import base64
import os
import sys
import pytest
from typing import Optional, Any, Dict

# 현재 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nadle_backend.config import get_settings


class UpstashRedisClient:
    """Upstash Redis REST API 클라이언트 (테스트용)"""
    
    def __init__(self, rest_url: str, rest_token: str):
        self.rest_url = rest_url.rstrip('/')
        self.rest_token = rest_token
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.rest_token}',
                'Content-Type': 'application/json'
            },
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, command: list) -> Dict[str, Any]:
        """Upstash REST API 요청 수행"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"{self.rest_url}"
        data = command
        
        async with self.session.post(url, json=data) as response:
            result = await response.json()
            
            if response.status != 200:
                raise Exception(f"Upstash API Error: {response.status} - {result}")
                
            return result
    
    async def ping(self) -> str:
        """연결 테스트"""
        result = await self._request(["PING"])
        return result.get("result", "")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """값 저장"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        command = ["SET", key, value]
        if ttl:
            command.extend(["EX", str(ttl)])
            
        result = await self._request(command)
        return result.get("result") == "OK"
    
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        result = await self._request(["GET", key])
        value = result.get("result")
        
        if value is None:
            return None
            
        # JSON 파싱 시도
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        result = await self._request(["DEL", key])
        return result.get("result", 0) > 0
    
    async def exists(self, key: str) -> bool:
        """키 존재 확인"""
        result = await self._request(["EXISTS", key])
        return result.get("result", 0) > 0
    
    async def info(self) -> str:
        """Redis 정보 조회"""
        result = await self._request(["INFO"])
        return result.get("result", "")


@pytest.mark.asyncio
async def test_upstash_connection():
    """Upstash Redis 연결 테스트"""
    settings = get_settings()
    
    # Upstash 설정 확인
    upstash_url = getattr(settings, 'upstash_redis_rest_url', None) or os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = getattr(settings, 'upstash_redis_rest_token', None) or os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다. UPSTASH_REDIS_REST_URL과 UPSTASH_REDIS_REST_TOKEN 환경변수를 설정하세요.")
    
    print(f"Upstash URL: {upstash_url}")
    print(f"Upstash Token: {upstash_token[:20]}...")
    
    async with UpstashRedisClient(upstash_url, upstash_token) as client:
        # 연결 테스트
        pong = await client.ping()
        assert pong == "PONG", f"PING 실패: {pong}"
        print("✅ Upstash Redis 연결 성공")


@pytest.mark.asyncio
async def test_upstash_basic_operations():
    """Upstash Redis 기본 CRUD 작업 테스트"""
    settings = get_settings()
    
    upstash_url = getattr(settings, 'upstash_redis_rest_url', None) or os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = getattr(settings, 'upstash_redis_rest_token', None) or os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    async with UpstashRedisClient(upstash_url, upstash_token) as client:
        test_key = "test:upstash:basic"
        test_value = {"message": "Hello Upstash!", "number": 42, "array": [1, 2, 3]}
        
        # SET 테스트
        print(f"데이터 저장: {test_key} = {test_value}")
        success = await client.set(test_key, test_value, ttl=300)  # 5분 TTL
        assert success, "데이터 저장 실패"
        print("✅ SET 작업 성공")
        
        # EXISTS 테스트
        exists = await client.exists(test_key)
        assert exists, "저장한 키가 존재하지 않음"
        print("✅ EXISTS 작업 성공")
        
        # GET 테스트
        retrieved = await client.get(test_key)
        assert retrieved == test_value, f"조회된 데이터가 다름: {retrieved} != {test_value}"
        print("✅ GET 작업 성공")
        
        # DELETE 테스트
        deleted = await client.delete(test_key)
        assert deleted, "데이터 삭제 실패"
        print("✅ DELETE 작업 성공")
        
        # 삭제 후 조회 테스트
        retrieved_after_delete = await client.get(test_key)
        assert retrieved_after_delete is None, f"삭제 후에도 데이터가 존재함: {retrieved_after_delete}"
        print("✅ 삭제 후 조회 검증 성공")


@pytest.mark.asyncio
async def test_upstash_multiple_keys():
    """Upstash Redis 다중 키 작업 테스트"""
    settings = get_settings()
    
    upstash_url = getattr(settings, 'upstash_redis_rest_url', None) or os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = getattr(settings, 'upstash_redis_rest_token', None) or os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    async with UpstashRedisClient(upstash_url, upstash_token) as client:
        # 여러 키에 데이터 저장
        test_data = {
            "test:upstash:user:1": {"id": 1, "name": "Alice", "email": "alice@example.com"},
            "test:upstash:user:2": {"id": 2, "name": "Bob", "email": "bob@example.com"},
            "test:upstash:user:3": {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            "test:upstash:session:abc123": {"user_id": 1, "expires_at": "2024-07-12T12:00:00Z"},
            "test:upstash:cache:popular_posts": [{"id": 101, "title": "Post 1"}, {"id": 102, "title": "Post 2"}]
        }
        
        print(f"다중 키 저장 테스트: {len(test_data)}개 키")
        
        # 저장
        for key, value in test_data.items():
            success = await client.set(key, value, ttl=300)
            assert success, f"키 {key} 저장 실패"
        
        print("✅ 다중 키 저장 성공")
        
        # 조회 및 검증
        for key, expected_value in test_data.items():
            retrieved = await client.get(key)
            assert retrieved == expected_value, f"키 {key} 데이터 불일치: {retrieved} != {expected_value}"
        
        print("✅ 다중 키 조회 성공")
        
        # 정리
        for key in test_data.keys():
            deleted = await client.delete(key)
            assert deleted, f"키 {key} 삭제 실패"
        
        print("✅ 다중 키 삭제 성공")


@pytest.mark.asyncio 
async def test_upstash_info():
    """Upstash Redis 정보 조회 테스트"""
    settings = get_settings()
    
    upstash_url = getattr(settings, 'upstash_redis_rest_url', None) or os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = getattr(settings, 'upstash_redis_rest_token', None) or os.getenv('UPSTASH_REDIS_REST_TOKEN')
    
    if not upstash_url or not upstash_token:
        pytest.skip("Upstash Redis 설정이 없습니다.")
    
    async with UpstashRedisClient(upstash_url, upstash_token) as client:
        info = await client.info()
        assert isinstance(info, str), f"INFO 명령 결과가 문자열이 아님: {type(info)}"
        assert len(info) > 0, "INFO 명령 결과가 비어있음"
        
        # Redis 정보에서 주요 필드 확인
        info_lines = info.split('\n')
        redis_version_found = False
        
        for line in info_lines:
            if line.startswith('redis_version:'):
                redis_version_found = True
                version = line.split(':')[1].strip()
                print(f"Redis Version: {version}")
                break
        
        assert redis_version_found, "Redis 버전 정보를 찾을 수 없음"
        print("✅ Redis 정보 조회 성공")


async def main():
    """메인 테스트 함수 (스크립트 실행용)"""
    print("=== Upstash Redis 통합 테스트 시작 ===\n")
    
    try:
        # 연결 테스트
        print("1. 연결 테스트")
        await test_upstash_connection()
        print()
        
        # 기본 작업 테스트
        print("2. 기본 CRUD 작업 테스트")
        await test_upstash_basic_operations()
        print()
        
        # 다중 키 테스트
        print("3. 다중 키 작업 테스트")
        await test_upstash_multiple_keys()
        print()
        
        # 정보 조회 테스트
        print("4. Redis 정보 조회 테스트")
        await test_upstash_info()
        print()
        
        print("✅ 모든 Upstash Redis 통합 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)