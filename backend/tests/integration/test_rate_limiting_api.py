# Rate Limiting API 테스트
# 최종 수정시간: 2025-07-21 오후 2:45 (KST)
# 주요 컴포넌트: Rate Limiting API 엔드포인트 테스트
# 함수:
#   - TestRateLimitingAPIEndpoints: API 엔드포인트별 Rate Limiting 테스트 (라인 30-350)
#   - TestRateLimitingHTTPHeaders: HTTP 헤더 검증 테스트 (라인 352-420)
#   - TestRateLimitingErrorHandling: 에러 처리 및 429 응답 테스트 (라인 422-480)
# 관련 파일:
#   - nadle_backend.services.rate_limiting_service: Rate Limiting 서비스
#   - nadle_backend.models.rate_limit_config: Rate Limiting 설정 모델
#   - nadle_backend.routers.*: 각종 API 라우터들

import pytest
import pytest_asyncio
import asyncio
import time
from typing import Dict, Any
import httpx
from httpx import AsyncClient
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from unittest.mock import Mock, patch

from nadle_backend.services.rate_limiting_service import (
    RateLimitingService, 
    get_rate_limiting_service
)
from nadle_backend.models.rate_limit_config import (
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitConfigRegistry,
    RateLimitResult
)
from nadle_backend.config import get_settings


@pytest.mark.redis
@pytest.mark.integration
class TestRateLimitingAPIEndpoints:
    """API 엔드포인트별 Rate Limiting 테스트"""
    
    @pytest.fixture
    async def rate_limiting_service(self):
        """Rate Limiting 서비스 픽스처"""
        # 전역 서비스 리셋
        import nadle_backend.services.rate_limiting_service
        nadle_backend.services.rate_limiting_service._rate_limiting_service = None
        
        service = await get_rate_limiting_service()
        yield service
        
        # 테스트 후 정리
        try:
            if service._redis_client:
                pattern = f"{get_settings().redis_key_prefix}rate_limit:*"
                cursor = 0
                while True:
                    cursor, keys = await service._redis_client.scan(
                        cursor=cursor, match=pattern
                    )
                    if keys:
                        await service._redis_client.delete(*keys)
                    if cursor == 0:
                        break
        except Exception as e:
            print(f"Redis cleanup failed: {e}")
    
    @pytest.fixture
    def test_app(self):
        """테스트용 FastAPI 앱"""
        app = FastAPI()
        
        @app.post("/auth/login")
        async def mock_login(request: Request):
            # Rate limiting 체크 (실제 구현에서는 미들웨어에서 처리)
            service = await get_rate_limiting_service()
            config = RateLimitConfigRegistry.get_config("auth_login")
            
            result = await service.check_rate_limit(request, config)
            
            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "Too many requests",
                        "retry_after": result.retry_after
                    },
                    headers={
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "Retry-After": str(result.retry_after) if result.retry_after else "60"
                    }
                )
            
            # 성공 응답에도 헤더 추가
            return JSONResponse(
                content={"message": "Login successful"},
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_time)
                }
            )
        
        @app.post("/posts")
        async def mock_create_post(request: Request):
            service = await get_rate_limiting_service()
            config = RateLimitConfigRegistry.get_config("posts_create")
            
            # 사용자 ID 모킹 (실제로는 인증에서 추출)
            user_id = request.headers.get("X-User-ID", "test_user")
            
            result = await service.check_rate_limit(request, config, user_id=user_id)
            
            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "Too many posts created",
                        "retry_after": result.retry_after
                    },
                    headers={
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "Retry-After": str(result.retry_after) if result.retry_after else "60"
                    }
                )
            
            return JSONResponse(
                content={"message": "Post created", "id": "123"},
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_time)
                }
            )
        
        @app.post("/files/upload")
        async def mock_upload_file(request: Request):
            service = await get_rate_limiting_service()
            config = RateLimitConfigRegistry.get_config("files_upload")
            
            result = await service.check_rate_limit(request, config)
            
            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "Too many file uploads",
                        "retry_after": result.retry_after
                    },
                    headers={
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "Retry-After": str(result.retry_after) if result.retry_after else "60"
                    }
                )
            
            return JSONResponse(
                content={"message": "File uploaded", "file_id": "file123"},
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_time)
                }
            )
        
        return app
    
    @pytest.fixture
    async def client(self, test_app):
        """테스트 클라이언트"""
        transport = httpx.ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    
    async def test_auth_login_rate_limiting(self, client, rate_limiting_service):
        """인증 로그인 Rate Limiting 테스트"""
        # 설정 확인
        config = RateLimitConfigRegistry.get_config("auth_login")
        assert config.limit == 3
        
        # 첫 번째 요청 (허용)
        response1 = await client.post("/auth/login", json={"username": "test"})
        assert response1.status_code == 200
        assert response1.headers["X-RateLimit-Limit"] == "3"
        assert response1.headers["X-RateLimit-Remaining"] == "2"
        
        # 두 번째 요청 (허용)
        response2 = await client.post("/auth/login", json={"username": "test"})
        assert response2.status_code == 200
        assert response2.headers["X-RateLimit-Remaining"] == "1"
        
        # 세 번째 요청 (허용)
        response3 = await client.post("/auth/login", json={"username": "test"})
        assert response3.status_code == 200
        assert response3.headers["X-RateLimit-Remaining"] == "0"
        
        # 네 번째 요청 (거부)
        response4 = await client.post("/auth/login", json={"username": "test"})
        assert response4.status_code == 429
        assert response4.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in response4.headers
        
        response_data = response4.json()
        assert "Too many requests" in response_data["detail"]["message"]
        assert "retry_after" in response_data["detail"]
    
    async def test_posts_create_user_based_rate_limiting(self, client, rate_limiting_service):
        """게시글 생성 사용자 기반 Rate Limiting 테스트"""
        config = RateLimitConfigRegistry.get_config("posts_create")
        assert config.limit == 5
        assert config.key_strategy == RateLimitStrategy.USER
        
        headers_user1 = {"X-User-ID": "user123"}
        headers_user2 = {"X-User-ID": "user456"}
        
        # 사용자1이 제한까지 요청
        for i in range(5):
            response = await client.post(
                "/posts", 
                json={"title": f"Post {i}"}, 
                headers=headers_user1
            )
            assert response.status_code == 200
            assert response.headers["X-RateLimit-Remaining"] == str(4 - i)
        
        # 사용자1의 추가 요청 거부
        response = await client.post(
            "/posts", 
            json={"title": "Post 6"}, 
            headers=headers_user1
        )
        assert response.status_code == 429
        
        # 사용자2는 독립적으로 허용되어야 함
        response = await client.post(
            "/posts", 
            json={"title": "User2 Post"}, 
            headers=headers_user2
        )
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Remaining"] == "4"
    
    async def test_files_upload_ip_based_rate_limiting(self, client, rate_limiting_service):
        """파일 업로드 IP 기반 Rate Limiting 테스트"""
        config = RateLimitConfigRegistry.get_config("files_upload")
        assert config.limit == 3
        assert config.key_strategy == RateLimitStrategy.IP
        
        # 제한까지 요청
        for i in range(3):
            response = await client.post("/files/upload", json={"filename": f"file{i}.txt"})
            assert response.status_code == 200
            assert response.headers["X-RateLimit-Remaining"] == str(2 - i)
        
        # 추가 요청 거부
        response = await client.post("/files/upload", json={"filename": "file4.txt"})
        assert response.status_code == 429
        assert response.headers["X-RateLimit-Remaining"] == "0"
        
        response_data = response.json()
        assert "Too many file uploads" in response_data["detail"]["message"]
    
    async def test_different_endpoints_independent_limits(self, client, rate_limiting_service):
        """다른 엔드포인트 간 독립적 제한 테스트"""
        # auth 엔드포인트에서 제한까지 요청
        for i in range(3):
            response = await client.post("/auth/login", json={"username": "test"})
            assert response.status_code == 200
        
        # auth 제한 초과
        response = await client.post("/auth/login", json={"username": "test"})
        assert response.status_code == 429
        
        # files 엔드포인트는 독립적으로 허용되어야 함
        response = await client.post("/files/upload", json={"filename": "test.txt"})
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Remaining"] == "2"  # files는 별도 카운터
    
    async def test_concurrent_requests_rate_limiting(self, client, rate_limiting_service):
        """동시 요청 Rate Limiting 테스트"""
        # 10개의 동시 요청 생성 (auth는 3개 제한)
        tasks = []
        for i in range(10):
            task = client.post("/auth/login", json={"username": f"test{i}"})
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성공한 요청과 실패한 요청 분류
        success_count = 0
        failed_count = 0
        
        for response in responses:
            if hasattr(response, 'status_code'):
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    failed_count += 1
        
        # 정확히 3개만 성공, 7개는 실패해야 함
        assert success_count == 3
        assert failed_count == 7


@pytest.mark.redis
@pytest.mark.integration  
class TestRateLimitingHTTPHeaders:
    """Rate Limiting HTTP 헤더 검증 테스트"""
    
    @pytest.fixture
    async def rate_limiting_service(self):
        """Rate Limiting 서비스 픽스처"""
        # 전역 서비스 리셋
        import nadle_backend.services.rate_limiting_service
        nadle_backend.services.rate_limiting_service._rate_limiting_service = None
        
        service = await get_rate_limiting_service()
        yield service
        
        # 테스트 후 정리
        try:
            if service._redis_client:
                pattern = f"{get_settings().redis_key_prefix}rate_limit:*"
                cursor = 0
                while True:
                    cursor, keys = await service._redis_client.scan(
                        cursor=cursor, match=pattern
                    )
                    if keys:
                        await service._redis_client.delete(*keys)
                    if cursor == 0:
                        break
        except Exception as e:
            print(f"Redis cleanup failed: {e}")
    
    @pytest.fixture
    async def simple_app(self, rate_limiting_service):
        """간단한 테스트 앱"""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            config = RateLimitConfig(
                endpoint="/test",
                limit=5,
                window=60,
                key_strategy=RateLimitStrategy.IP
            )
            
            result = await rate_limiting_service.check_rate_limit(request, config)
            
            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "X-RateLimit-Reset": str(result.reset_time),
                        "Retry-After": str(result.retry_after) if result.retry_after else "60"
                    }
                )
            
            return JSONResponse(
                content={"status": "ok"},
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_time)
                }
            )
        
        return app
    
    @pytest.fixture
    async def client(self, simple_app):
        """테스트 클라이언트"""
        transport = httpx.ASGITransport(app=simple_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    
    async def test_rate_limit_headers_success(self, client):
        """성공 응답의 Rate Limit 헤더 테스트"""
        response = await client.get("/test")
        assert response.status_code == 200
        
        # 필수 헤더 존재 확인
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # 헤더 값 검증
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "4"
        assert int(response.headers["X-RateLimit-Reset"]) > int(time.time())
    
    async def test_rate_limit_headers_429_response(self, client):
        """429 응답의 Rate Limit 헤더 테스트"""
        # 제한까지 요청
        for i in range(5):
            response = await client.get("/test")
            assert response.status_code == 200
        
        # 제한 초과 요청
        response = await client.get("/test")
        assert response.status_code == 429
        
        # 429 응답 헤더 검증
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert "Retry-After" in response.headers
        
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert int(response.headers["Retry-After"]) > 0
    
    async def test_rate_limit_remaining_decrements(self, client):
        """Rate Limit Remaining 카운터 감소 테스트"""
        # 연속 요청으로 카운터 감소 확인
        for i in range(5):
            response = await client.get("/test")
            assert response.status_code == 200
            assert response.headers["X-RateLimit-Remaining"] == str(4 - i)


@pytest.mark.redis
@pytest.mark.integration
class TestRateLimitingErrorHandling:
    """Rate Limiting 에러 처리 테스트"""
    
    @pytest.fixture
    async def error_app(self):
        """에러 상황 테스트용 앱"""
        app = FastAPI()
        
        @app.get("/redis-error")
        async def redis_error_endpoint(request: Request):
            # Redis 오류 시뮬레이션
            with patch.object(
                RateLimitingService, 
                'check_rate_limit',
                side_effect=Exception("Redis connection failed")
            ):
                service = await get_rate_limiting_service()
                config = RateLimitConfig(
                    endpoint="/redis-error",
                    limit=3,
                    window=60
                )
                
                try:
                    result = await service.check_rate_limit(request, config)
                    # Redis 오류 시 fail-open (요청 허용)
                    return {"status": "ok", "fail_open": True}
                except Exception as e:
                    # 예상치 못한 오류 처리
                    raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/disabled")
        async def disabled_endpoint(request: Request):
            service = await get_rate_limiting_service()
            # 비활성화된 설정
            config = RateLimitConfig(
                endpoint="/disabled",
                limit=1,
                window=60,
                enabled=False
            )
            
            result = await service.check_rate_limit(request, config)
            return {
                "status": "ok", 
                "allowed": result.allowed,
                "key": result.key
            }
        
        return app
    
    @pytest.fixture
    async def client(self, error_app):
        """테스트 클라이언트"""
        transport = httpx.ASGITransport(app=error_app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    
    async def test_rate_limiting_disabled(self, client):
        """Rate Limiting 비활성화 테스트"""
        # 비활성화된 엔드포인트는 제한 없이 허용
        for i in range(5):
            response = await client.get("/disabled")
            assert response.status_code == 200
            
            data = response.json()
            assert data["allowed"] is True
            assert data["key"] == "disabled"
    
    async def test_custom_error_messages(self):
        """커스텀 에러 메시지 테스트"""
        config = RateLimitConfigRegistry.get_config("auth_login")
        assert config.custom_error_message is not None
        assert "로그인 시도가 너무 많습니다" in config.custom_error_message
        
        config = RateLimitConfigRegistry.get_config("posts_create")
        assert config.custom_error_message is not None
        assert "게시글 작성이 너무 빈번합니다" in config.custom_error_message
    
    async def test_rate_limiting_with_different_ip_headers(self):
        """다양한 IP 헤더 처리 테스트"""
        from nadle_backend.services.rate_limiting_service import RateLimitingService
        
        service = RateLimitingService()
        
        # X-Forwarded-For 헤더 테스트
        request1 = Mock()
        request1.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        request1.client = Mock()
        request1.client.host = "127.0.0.1"
        
        ip1 = service._get_client_ip(request1)
        assert ip1 == "203.0.113.1"
        
        # X-Real-IP 헤더 테스트
        request2 = Mock()
        request2.headers = {"X-Real-IP": "203.0.113.2"}
        request2.client = Mock()
        request2.client.host = "127.0.0.1"
        
        ip2 = service._get_client_ip(request2)
        assert ip2 == "203.0.113.2"
        
        # 직접 연결 테스트
        request3 = Mock()
        request3.headers = {}
        request3.client = Mock()
        request3.client.host = "192.168.1.100"
        
        ip3 = service._get_client_ip(request3)
        assert ip3 == "192.168.1.100"