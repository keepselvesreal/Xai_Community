"""
Sentry 연동 단위 테스트

TDD Red 단계: Sentry 초기화 및 에러 캡처 기능 테스트
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestSentryIntegration:
    """Sentry 연동 기능 테스트"""

    @patch('sentry_sdk.init')
    def test_sentry_initialization_with_valid_config(self, mock_sentry_init):
        """유효한 설정으로 Sentry 초기화 테스트"""
        from nadle_backend.monitoring.sentry_config import init_sentry
        
        # Given: 유효한 Sentry 설정
        dsn = "https://test@sentry.io/12345"
        environment = "production"
        
        # When: Sentry 초기화
        init_sentry(dsn=dsn, environment=environment)
        
        # Then: sentry_sdk.init이 올바른 인자로 호출됨
        mock_sentry_init.assert_called_once()
        args, kwargs = mock_sentry_init.call_args
        
        assert kwargs['dsn'] == dsn
        assert kwargs['environment'] == environment
        assert kwargs['traces_sample_rate'] == 1.0
        assert kwargs['send_default_pii'] == True
        assert callable(kwargs['before_send'])
        assert len(kwargs['integrations']) == 2  # FastAPI + Asyncio
        assert kwargs['debug'] == False

    @patch('sentry_sdk.init')
    def test_sentry_initialization_with_invalid_dsn(self, mock_sentry_init):
        """잘못된 DSN으로 초기화 시 예외 처리 테스트"""
        from nadle_backend.monitoring.sentry_config import init_sentry
        
        # Given: 잘못된 DSN
        invalid_dsn = "invalid-dsn-format"
        
        # When & Then: ValueError 발생
        with pytest.raises(ValueError, match="Invalid Sentry DSN format"):
            init_sentry(dsn=invalid_dsn, environment="test")

    @patch('sentry_sdk.init')
    def test_sentry_initialization_without_dsn(self, mock_sentry_init):
        """DSN 없이 초기화 시 건너뛰기 테스트"""
        from nadle_backend.monitoring.sentry_config import init_sentry
        
        # Given: DSN이 None
        # When: Sentry 초기화
        init_sentry(dsn=None, environment="development")
        
        # Then: sentry_sdk.init이 호출되지 않음
        mock_sentry_init.assert_not_called()

    @patch('sentry_sdk.capture_exception')
    def test_sentry_error_capture(self, mock_capture_exception):
        """Sentry 에러 캡처 기능 테스트"""
        from nadle_backend.monitoring.sentry_config import capture_error
        
        # Given: 테스트 예외
        test_exception = ValueError("Test error message")
        
        # When: 에러 캡처
        capture_error(test_exception, user_id="test_user_123")
        
        # Then: Sentry에 에러가 캡처됨
        mock_capture_exception.assert_called_once_with(test_exception)

    @patch('sentry_sdk.set_user')
    @patch('sentry_sdk.set_tag')
    def test_sentry_user_context_setting(self, mock_set_tag, mock_set_user):
        """Sentry 사용자 컨텍스트 설정 테스트"""
        from nadle_backend.monitoring.sentry_config import set_user_context
        
        # Given: 사용자 정보
        user_id = "user_123"
        user_email = "test@example.com"
        
        # When: 사용자 컨텍스트 설정
        set_user_context(user_id=user_id, email=user_email)
        
        # Then: Sentry에 사용자 정보 설정됨
        mock_set_user.assert_called_once_with({
            "id": user_id,
            "email": user_email
        })
        mock_set_tag.assert_called_with("user.id", user_id)

    def test_sentry_config_from_environment_variables(self):
        """환경변수로부터 Sentry 설정 로드 테스트"""
        from nadle_backend.monitoring.sentry_config import get_sentry_config
        
        # Given: 환경변수 설정
        with patch.dict(os.environ, {
            'SENTRY_DSN': 'https://test@sentry.io/12345',
            'SENTRY_ENVIRONMENT': 'staging',
            'SENTRY_TRACES_SAMPLE_RATE': '0.5'
        }):
            # When: 설정 로드
            config = get_sentry_config()
            
            # Then: 올바른 설정 반환
            assert config['dsn'] == 'https://test@sentry.io/12345'
            assert config['environment'] == 'staging'
            assert config['traces_sample_rate'] == 0.5

    def test_sentry_config_defaults(self):
        """기본 Sentry 설정 테스트"""
        from nadle_backend.monitoring.sentry_config import get_sentry_config
        
        # Given: 환경변수 없음
        with patch.dict(os.environ, {}, clear=True):
            # When: 설정 로드
            config = get_sentry_config()
            
            # Then: 기본값 반환
            assert config['dsn'] is None
            assert config['environment'] == 'development'
            assert config['traces_sample_rate'] == 1.0

    @patch('sentry_sdk.init')
    def test_sentry_fastapi_integration(self, mock_sentry_init):
        """FastAPI Sentry 통합 테스트"""
        from nadle_backend.monitoring.sentry_config import init_sentry_for_fastapi
        
        # Given: FastAPI 앱
        mock_app = Mock()
        
        # When: FastAPI용 Sentry 초기화
        init_sentry_for_fastapi(
            app=mock_app,
            dsn="https://test@sentry.io/12345",
            environment="production"
        )
        
        # Then: FastAPI integration 포함하여 초기화됨
        mock_sentry_init.assert_called_once()
        args, kwargs = mock_sentry_init.call_args
        assert 'integrations' in kwargs
        # FastAPI integration이 포함되어 있는지 확인
        integrations = kwargs['integrations']
        assert len(integrations) > 0