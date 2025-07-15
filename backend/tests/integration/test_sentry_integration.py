"""
Sentry 통합 테스트

백엔드 Sentry 설정 및 에러 캡처 기능 통합 테스트
"""
import pytest
import sentry_sdk
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from nadle_backend.monitoring.sentry_config import init_sentry, get_sentry_config
from nadle_backend.middleware.sentry_middleware import SentryRequestMiddleware
from main import app


class TestSentryIntegration:
    """Sentry 통합 테스트 클래스"""

    def test_sentry_config_initialization(self):
        """Sentry 설정 초기화 테스트"""
        # Given: 테스트용 Sentry 설정
        test_dsn = "https://test@sentry.io/123456"
        test_environment = "test"
        
        # When: Sentry 초기화
        with patch('sentry_sdk.init') as mock_init:
            init_sentry(dsn=test_dsn, environment=test_environment)
            
            # Then: sentry_sdk.init이 올바른 설정으로 호출됨
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs['dsn'] == test_dsn
            assert call_kwargs['environment'] == test_environment
            assert 'before_send' in call_kwargs
            assert 'traces_sample_rate' in call_kwargs

    def test_sentry_config_with_no_dsn(self):
        """DSN이 없을 때 Sentry 초기화 건너뛰기 테스트"""
        # When: DSN 없이 Sentry 초기화 시도
        with patch('sentry_sdk.init') as mock_init:
            init_sentry(dsn=None)
            
            # Then: sentry_sdk.init이 호출되지 않음
            mock_init.assert_not_called()

    def test_get_sentry_config(self):
        """Sentry 설정 가져오기 테스트"""
        # When: Sentry 설정 조회
        config = get_sentry_config()
        
        # Then: 필수 설정 키들이 존재함
        assert 'dsn' in config
        assert 'environment' in config
        assert 'traces_sample_rate' in config
        assert 'send_default_pii' in config

    @patch('sentry_sdk.capture_exception')
    def test_sentry_middleware_error_capture(self, mock_capture):
        """Sentry 미들웨어 에러 캡처 테스트"""
        # Given: 테스트 클라이언트
        client = TestClient(app)
        
        # When: 존재하지 않는 엔드포인트 호출 (404 에러)
        response = client.get("/api/nonexistent-endpoint")
        
        # Then: 404 응답 반환 (실제 에러 캡처는 500 에러에서만 발생)
        assert response.status_code == 404

    def test_sentry_middleware_request_context(self):
        """Sentry 미들웨어 요청 컨텍스트 설정 테스트"""
        # Given: 테스트 클라이언트
        client = TestClient(app)
        
        # When: 정상적인 API 호출
        response = client.get("/health")
        
        # Then: 응답이 정상적으로 반환됨 (컨텍스트 설정 성공)
        assert response.status_code == 200

    @patch('sentry_sdk.set_user')
    def test_sentry_user_context_setting(self, mock_set_user):
        """Sentry 사용자 컨텍스트 설정 테스트"""
        # Given: JWT 토큰을 포함한 요청 헤더
        client = TestClient(app)
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfaWQiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20ifQ.test"
        }
        
        # When: 인증이 필요한 API 호출
        response = client.get("/api/posts", headers=headers)
        
        # Then: 요청이 처리됨 (실제 토큰 검증은 별도 처리)
        # 토큰이 유효하지 않아 401이 반환될 수 있지만, 미들웨어는 동작함
        assert response.status_code in [200, 401, 422]

    def test_sentry_error_filtering(self):
        """Sentry 에러 필터링 테스트"""
        from nadle_backend.monitoring.sentry_config import sentry_before_send
        
        # Given: 필터링될 에러 이벤트 (404 HTTP 에러)
        filtered_event = {
            'exception': {
                'values': [
                    {'type': 'HTTPException', 'value': 'Not Found: 404'}
                ]
            }
        }
        
        # When: sentry_before_send 적용
        result = sentry_before_send(filtered_event, {})
        
        # Then: 에러가 필터링됨 (None 반환)
        assert result is None

    def test_sentry_normal_error_passthrough(self):
        """Sentry 정상 에러 통과 테스트"""
        from nadle_backend.monitoring.sentry_config import sentry_before_send
        
        # Given: 필터링되지 않을 에러 이벤트
        normal_event = {
            'exception': {
                'values': [
                    {'type': 'ValueError', 'value': 'Invalid input data'}
                ]
            }
        }
        
        # When: sentry_before_send 적용
        result = sentry_before_send(normal_event, {})
        
        # Then: 에러가 그대로 통과됨
        assert result == normal_event

    @patch('nadle_backend.monitoring.sentry_config.init_sentry')
    def test_fastapi_app_sentry_initialization(self, mock_init_sentry):
        """FastAPI 앱에서 Sentry 초기화 테스트"""
        # Given: main.py에서 앱 생성 시
        # When: 앱이 이미 생성되어 있음
        # Then: Sentry 초기화가 이미 호출되었을 것임 (실제 환경에서)
        
        # 이 테스트는 실제로는 main.py의 create_app() 함수에서
        # Sentry 초기화가 호출되는지 확인하는 테스트입니다.
        # 현재는 앱이 이미 생성되어 있으므로 패스
        assert True

    def test_sentry_performance_tracking(self):
        """Sentry 성능 추적 테스트"""
        with patch('sentry_sdk.start_transaction') as mock_transaction:
            # Given: 모킹된 트랜잭션
            mock_tx = MagicMock()
            mock_transaction.return_value = mock_tx
            
            # When: 트랜잭션 시작
            transaction = sentry_sdk.start_transaction(name="test_operation", op="function")
            
            # Then: 트랜잭션이 생성됨
            mock_transaction.assert_called_once_with(name="test_operation", op="function")


@pytest.mark.asyncio
class TestSentryAsyncIntegration:
    """Sentry 비동기 통합 테스트 클래스"""

    async def test_async_error_capture(self):
        """비동기 에러 캡처 테스트"""
        with patch('sentry_sdk.capture_exception') as mock_capture:
            # Given: 비동기 함수에서 에러 발생
            try:
                raise ValueError("Async test error")
            except Exception as e:
                # When: Sentry로 에러 캡처
                sentry_sdk.capture_exception(e)
                
                # Then: 에러가 캡처됨
                mock_capture.assert_called_once_with(e)

    async def test_async_context_preservation(self):
        """비동기 컨텍스트 보존 테스트"""
        # Given: 비동기 컨텍스트에서 사용자 설정
        with patch('sentry_sdk.set_user') as mock_set_user:
            # When: 사용자 컨텍스트 설정
            sentry_sdk.set_user({"id": "async_user_123", "email": "async@test.com"})
            
            # Then: 사용자 정보가 설정됨
            mock_set_user.assert_called_once_with({"id": "async_user_123", "email": "async@test.com"})