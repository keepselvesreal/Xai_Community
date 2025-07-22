# Rate Limiting 미들웨어 테스트
# 최종 수정시간: 2025-07-21 오후 3:20 (KST)
# 주요 컴포넌트: Rate Limiting 미들웨어 Unit 테스트
# 함수:
#   - TestRateLimitingMiddleware: 미들웨어 주요 기능 테스트 (라인 25-200)
#   - TestPathConfigMapping: 경로별 설정 매핑 테스트 (라인 202-250)
#   - TestUserIdExtraction: 사용자 ID 추출 테스트 (라인 252-300)

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

from nadle_backend.middleware.rate_limiting_middleware import (
    RateLimitingMiddleware,
    get_rate_limit_config_for_path,
    extract_user_id_from_request,
    create_rate_limiting_middleware
)
from nadle_backend.models.rate_limit_config import (
    RateLimitConfig,
    RateLimitResult,
    RateLimitStrategy
)


class TestRateLimitingMiddleware:
    """Rate Limiting 미들웨어 테스트"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI 앱"""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        return app
    
    @pytest.fixture
    def middleware(self, mock_app):
        """미들웨어 인스턴스"""
        return RateLimitingMiddleware(mock_app)
    
    @pytest.fixture
    def mock_request(self):
        """Mock Request"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    def test_middleware_initialization(self, mock_app):
        """미들웨어 초기화 테스트"""
        middleware = RateLimitingMiddleware(
            app=mock_app,
            enabled=True,
            exempt_paths=["/custom-exempt"],
            custom_error_handler=None
        )
        
        assert middleware.enabled is True
        assert "/custom-exempt" in middleware.exempt_paths
        assert "/health" in middleware.exempt_paths  # 기본 제외 경로
    
    def test_is_exempt_path(self, middleware):
        """제외 경로 확인 테스트"""
        assert middleware._is_exempt_path("/health") is True
        assert middleware._is_exempt_path("/docs") is True
        assert middleware._is_exempt_path("/api/docs") is True  # 부분 매칭
        assert middleware._is_exempt_path("/api/test") is False
    
    @pytest.mark.asyncio
    async def test_middleware_disabled(self, mock_app, mock_request):
        """미들웨어 비활성화 테스트"""
        middleware = RateLimitingMiddleware(mock_app, enabled=False)
        
        # call_next Mock
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_exempt_path_bypass(self, mock_app, mock_request):
        """제외 경로 우회 테스트"""
        middleware = RateLimitingMiddleware(mock_app, enabled=True)
        mock_request.url.path = "/health"
        
        async def mock_call_next(request):
            return JSONResponse(content={"status": "healthy"})
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_success(self, mock_app, mock_request):
        """성공 응답 헤더 테스트"""
        middleware = RateLimitingMiddleware(mock_app, enabled=True)
        
        # Rate limiting 서비스 모킹
        mock_result = RateLimitResult(
            allowed=True,
            limit=5,
            remaining=4,
            reset_time=1721548860,
            key="test_key"
        )
        
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limiting_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.check_rate_limit.return_value = mock_result
            mock_service.return_value = mock_service_instance
            
            with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limit_config_for_path') as mock_config:
                mock_config.return_value = RateLimitConfig(
                    endpoint="/test",
                    limit=5,
                    window=60
                )
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                assert response.status_code == 200
                assert "X-RateLimit-Limit" in response.headers
                assert response.headers["X-RateLimit-Limit"] == "5"
                assert response.headers["X-RateLimit-Remaining"] == "4"
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, mock_app, mock_request):
        """Rate limit 초과 테스트"""
        middleware = RateLimitingMiddleware(mock_app, enabled=True)
        
        # Rate limit 초과 결과 모킹
        mock_result = RateLimitResult(
            allowed=False,
            limit=3,
            remaining=0,
            reset_time=1721548860,
            retry_after=45,
            key="test_key"
        )
        
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limiting_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.check_rate_limit.return_value = mock_result
            mock_service.return_value = mock_service_instance
            
            with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limit_config_for_path') as mock_config:
                mock_config.return_value = RateLimitConfig(
                    endpoint="/test",
                    limit=3,
                    window=60
                )
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                assert response.status_code == 429
                assert "X-RateLimit-Limit" in response.headers
                assert response.headers["X-RateLimit-Limit"] == "3"
                assert response.headers["X-RateLimit-Remaining"] == "0"
                assert "Retry-After" in response.headers
                
                # 응답 내용 확인
                import json
                content = json.loads(response.body.decode())
                assert "Rate limit exceeded" in content["error"]
                assert content["retry_after"] == 45
    
    @pytest.mark.asyncio
    async def test_custom_error_handler(self, mock_app, mock_request):
        """커스텀 에러 핸들러 테스트"""
        async def custom_handler(rate_result):
            return JSONResponse(
                status_code=429,
                content={"custom": "error", "limit": rate_result.limit}
            )
        
        middleware = RateLimitingMiddleware(
            mock_app, 
            enabled=True,
            custom_error_handler=custom_handler
        )
        
        mock_result = RateLimitResult(
            allowed=False,
            limit=3,
            remaining=0,
            reset_time=1721548860,
            retry_after=45,
            key="test_key"
        )
        
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limiting_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.check_rate_limit.return_value = mock_result
            mock_service.return_value = mock_service_instance
            
            with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limit_config_for_path') as mock_config:
                mock_config.return_value = RateLimitConfig(
                    endpoint="/test",
                    limit=3,
                    window=60
                )
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                assert response.status_code == 429
                import json
                content = json.loads(response.body.decode())
                assert content["custom"] == "error"
                assert content["limit"] == 3
    
    @pytest.mark.asyncio
    async def test_middleware_error_fail_open(self, mock_app, mock_request):
        """미들웨어 에러 시 fail-open 테스트"""
        middleware = RateLimitingMiddleware(mock_app, enabled=True)
        
        async def mock_call_next(request):
            return JSONResponse(content={"message": "success"})
        
        # Rate limiting 서비스에서 예외 발생
        with patch('nadle_backend.middleware.rate_limiting_middleware.get_rate_limiting_service') as mock_service:
            mock_service.side_effect = Exception("Service error")
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # 에러 발생해도 요청은 통과해야 함 (fail-open)
            assert response.status_code == 200


class TestPathConfigMapping:
    """경로별 설정 매핑 테스트"""
    
    def test_auth_endpoints_mapping(self):
        """인증 엔드포인트 매핑 테스트"""
        config = get_rate_limit_config_for_path("/auth/login", "POST")
        assert config is not None
        assert config.endpoint == "/auth/login"
        assert config.limit == 3
        
        config = get_rate_limit_config_for_path("/auth/register", "POST")
        assert config is not None
        assert config.endpoint == "/auth/register"
        assert config.limit == 2
    
    def test_posts_endpoints_mapping(self):
        """게시글 엔드포인트 매핑 테스트"""
        config = get_rate_limit_config_for_path("/posts", "POST")
        assert config is not None
        assert config.endpoint == "/posts"
        assert config.limit == 5
        assert config.key_strategy == RateLimitStrategy.USER
        
        config = get_rate_limit_config_for_path("/posts/list", "GET")
        assert config is not None
        assert config.limit == 20
    
    def test_files_endpoints_mapping(self):
        """파일 엔드포인트 매핑 테스트"""
        config = get_rate_limit_config_for_path("/files/upload", "POST")
        assert config is not None
        assert config.endpoint == "/files/upload"
        assert config.limit == 3
        assert config.key_strategy == RateLimitStrategy.IP
    
    def test_unmapped_endpoint(self):
        """매핑되지 않은 엔드포인트 테스트"""
        config = get_rate_limit_config_for_path("/unknown", "GET")
        assert config is None
        
        config = get_rate_limit_config_for_path("/auth/login", "GET")  # 잘못된 메소드
        assert config is None


class TestUserIdExtraction:
    """사용자 ID 추출 테스트"""
    
    @pytest.mark.asyncio
    async def test_extract_user_id_with_valid_token(self):
        """유효한 JWT 토큰에서 사용자 ID 추출 테스트"""
        request = Mock(spec=Request)
        request.headers = {
            "authorization": "Bearer valid_token_here"
        }
        
        # JWT 검증 모킹
        with patch('nadle_backend.utils.jwt.decode_token') as mock_verify:
            mock_verify.return_value = {"user_id": "user123", "exp": 1721548860}
            
            user_id = await extract_user_id_from_request(request)
            assert user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_extract_user_id_no_auth_header(self):
        """인증 헤더 없는 경우 테스트"""
        request = Mock(spec=Request)
        request.headers = {}
        
        user_id = await extract_user_id_from_request(request)
        assert user_id is None
    
    @pytest.mark.asyncio
    async def test_extract_user_id_invalid_token_format(self):
        """잘못된 토큰 형식 테스트"""
        request = Mock(spec=Request)
        request.headers = {
            "authorization": "InvalidFormat token_here"
        }
        
        user_id = await extract_user_id_from_request(request)
        assert user_id is None
    
    @pytest.mark.asyncio
    async def test_extract_user_id_invalid_token(self):
        """유효하지 않은 JWT 토큰 테스트"""
        request = Mock(spec=Request)
        request.headers = {
            "authorization": "Bearer invalid_token"
        }
        
        # JWT 검증 실패 모킹
        with patch('nadle_backend.utils.jwt.decode_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            user_id = await extract_user_id_from_request(request)
            assert user_id is None


class TestMiddlewareFactory:
    """미들웨어 팩토리 테스트"""
    
    def test_create_rate_limiting_middleware_default(self):
        """기본 설정으로 미들웨어 생성 테스트"""
        with patch('nadle_backend.middleware.rate_limiting_middleware.get_settings') as mock_settings:
            mock_settings.return_value.rate_limiting_enabled = True
            
            factory = create_rate_limiting_middleware()
            assert callable(factory)
    
    def test_create_rate_limiting_middleware_custom(self):
        """커스텀 설정으로 미들웨어 생성 테스트"""
        async def custom_handler(rate_result):
            return JSONResponse(status_code=429, content={"custom": "handler"})
        
        factory = create_rate_limiting_middleware(
            enabled=False,
            exempt_paths=["/custom"],
            custom_error_handler=custom_handler
        )
        
        assert callable(factory)
        
        # 팩토리로 미들웨어 생성
        mock_app = FastAPI()
        middleware = factory(mock_app)
        
        assert isinstance(middleware, RateLimitingMiddleware)
        assert middleware.enabled is False
        assert "/custom" in middleware.exempt_paths
        assert middleware.custom_error_handler == custom_handler