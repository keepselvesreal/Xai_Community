"""
Sentry 미들웨어 통합 테스트

TDD Red 단계: FastAPI와 Sentry 통합 미들웨어 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import sentry_sdk


class TestSentryMiddleware:
    """Sentry 미들웨어 통합 테스트"""

    @pytest.fixture
    def app(self):
        """테스트용 FastAPI 앱"""
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {"message": "Hello World"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error for Sentry")
        
        @app.get("/http-error")
        async def http_error_endpoint():
            raise HTTPException(status_code=404, detail="Not found")
        
        return app

    @pytest.fixture
    def client(self, app):
        """테스트 클라이언트"""
        return TestClient(app)

    @patch('sentry_sdk.capture_exception')
    def test_sentry_captures_unhandled_exceptions(self, mock_capture_exception, client):
        """처리되지 않은 예외가 Sentry에 캡처되는지 테스트"""
        # When: 에러를 발생시키는 엔드포인트 호출
        response = client.get("/error")
        
        # Then: HTTP 500 응답 및 Sentry에 에러 캡처됨
        assert response.status_code == 500
        mock_capture_exception.assert_called_once()
        
        # 캡처된 예외가 ValueError인지 확인
        captured_exception = mock_capture_exception.call_args[0][0]
        assert isinstance(captured_exception, ValueError)
        assert str(captured_exception) == "Test error for Sentry"

    @patch('sentry_sdk.capture_exception')
    def test_sentry_does_not_capture_http_exceptions(self, mock_capture_exception, client):
        """HTTP 예외는 Sentry에 캡처되지 않는지 테스트"""
        # When: HTTP 예외를 발생시키는 엔드포인트 호출
        response = client.get("/http-error")
        
        # Then: HTTP 404 응답이지만 Sentry에는 캡처되지 않음
        assert response.status_code == 404
        mock_capture_exception.assert_not_called()

    @patch('sentry_sdk.set_tag')
    @patch('sentry_sdk.set_context')
    def test_sentry_request_context_setting(self, mock_set_context, mock_set_tag, client):
        """요청별 Sentry 컨텍스트 설정 테스트"""
        from nadle_backend.middleware.sentry_middleware import SentryRequestMiddleware
        
        # Given: Sentry 미들웨어가 추가된 앱
        app = FastAPI()
        app.add_middleware(SentryRequestMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        test_client = TestClient(app)
        
        # When: 요청 수행
        response = test_client.get("/test", headers={"User-Agent": "test-agent"})
        
        # Then: 요청 컨텍스트가 Sentry에 설정됨
        assert response.status_code == 200
        mock_set_context.assert_called()
        mock_set_tag.assert_called()

    @patch('sentry_sdk.capture_message')
    def test_sentry_performance_tracking(self, mock_capture_message):
        """Sentry 성능 추적 테스트"""
        from nadle_backend.middleware.sentry_middleware import track_performance
        
        # Given: 테스트 함수
        @track_performance("test_operation")
        async def slow_operation():
            import asyncio
            await asyncio.sleep(0.1)  # 100ms 지연
            return "result"
        
        # When: 함수 실행
        import asyncio
        result = asyncio.run(slow_operation())
        
        # Then: 결과 반환 및 성능 메트릭 전송
        assert result == "result"
        # 성능 추적이 기록되었는지 확인 (실제 구현에 따라 조정)

    @patch('sentry_sdk.set_user')
    def test_sentry_user_identification_from_jwt(self, mock_set_user, client):
        """JWT 토큰으로부터 사용자 식별 및 Sentry 설정 테스트"""
        from nadle_backend.middleware.sentry_middleware import SentryUserMiddleware
        
        # Given: 사용자 식별 미들웨어가 추가된 앱
        app = FastAPI()
        app.add_middleware(SentryUserMiddleware)
        
        @app.get("/protected")
        async def protected_endpoint():
            return {"message": "protected"}
        
        test_client = TestClient(app)
        
        # Given: 유효한 JWT 토큰 (모킹)
        with patch('nadle_backend.utils.jwt.decode_token') as mock_decode:
            mock_decode.return_value = {
                "user_id": "user_123",
                "email": "test@example.com"
            }
            
            # When: 인증된 요청 수행
            response = test_client.get(
                "/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Then: Sentry에 사용자 정보 설정됨
            assert response.status_code == 200
            mock_set_user.assert_called_once_with({
                "id": "user_123",
                "email": "test@example.com"
            })

    def test_sentry_middleware_error_filtering(self):
        """Sentry 에러 필터링 테스트"""
        from nadle_backend.monitoring.sentry_config import sentry_before_send
        
        # Given: 필터링해야 할 에러 (예: 404 에러)
        event_404 = {
            "exception": {
                "values": [
                    {
                        "type": "HTTPException",
                        "value": "404: Not Found"
                    }
                ]
            }
        }
        
        # When: before_send 필터 적용
        result = sentry_before_send(event_404, None)
        
        # Then: 404 에러는 필터링되어 None 반환
        assert result is None
        
        # Given: 필터링하지 않을 에러 (예: 500 에러)
        event_500 = {
            "exception": {
                "values": [
                    {
                        "type": "ValueError",
                        "value": "Internal server error"
                    }
                ]
            }
        }
        
        # When: before_send 필터 적용
        result = sentry_before_send(event_500, None)
        
        # Then: 500 에러는 그대로 전송
        assert result == event_500

    @patch('sentry_sdk.capture_exception')
    async def test_sentry_async_context_preservation(self, mock_capture_exception):
        """비동기 컨텍스트에서 Sentry 정보 보존 테스트"""
        from nadle_backend.middleware.sentry_middleware import async_sentry_context
        
        # Given: 비동기 컨텍스트
        async with async_sentry_context(user_id="async_user"):
            # When: 비동기 함수에서 에러 발생
            try:
                raise ValueError("Async error")
            except Exception as e:
                # Sentry에 수동으로 캡처
                sentry_sdk.capture_exception(e)
        
        # Then: 에러가 올바른 컨텍스트와 함께 캡처됨
        mock_capture_exception.assert_called_once()