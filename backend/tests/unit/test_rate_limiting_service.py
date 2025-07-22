import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from redis.asyncio import Redis

from nadle_backend.services.rate_limiting_service import RateLimitingService
from nadle_backend.models.rate_limit_config import (
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitConfigRegistry,
    RateLimitResult
)
from nadle_backend.database.redis_factory import RedisFactory
from nadle_backend.config import Settings


class TestRateLimitConfig:
    """Rate Limit 설정 모델 테스트"""
    
    def test_rate_limit_config_creation(self):
        """Rate Limit 설정 생성 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        assert config.endpoint == "/auth/login"
        assert config.limit == 3
        assert config.window == 60
        assert config.key_strategy == RateLimitStrategy.IP
        assert config.enabled is True
        assert config.custom_error_message is None
    
    def test_rate_limit_config_validation(self):
        """Rate Limit 설정 검증 테스트"""
        # 음수 limit 테스트
        with pytest.raises(ValueError):
            RateLimitConfig(
                endpoint="/test",
                limit=-1,
                window=60
            )
        
        # 음수 window 테스트
        with pytest.raises(ValueError):
            RateLimitConfig(
                endpoint="/test",
                limit=5,
                window=-1
            )
    
    def test_rate_limit_config_with_custom_message(self):
        """커스텀 에러 메시지 포함 설정 테스트"""
        custom_message = "너무 많은 요청입니다."
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            custom_error_message=custom_message
        )
        
        assert config.custom_error_message == custom_message


class TestRateLimitConfigRegistry:
    """Rate Limit 설정 레지스트리 테스트"""
    
    def test_get_auth_login_config(self):
        """인증 로그인 설정 조회 테스트"""
        config = RateLimitConfigRegistry.get_config("auth_login")
        
        assert config is not None
        assert config.endpoint == "/auth/login"
        assert config.limit == 3
        assert config.window == 60
        assert config.key_strategy == RateLimitStrategy.IP
    
    def test_get_posts_create_config(self):
        """게시글 생성 설정 조회 테스트"""
        config = RateLimitConfigRegistry.get_config("posts_create")
        
        assert config is not None
        assert config.endpoint == "/posts"
        assert config.limit == 5
        assert config.window == 60
        assert config.key_strategy == RateLimitStrategy.USER
    
    def test_get_nonexistent_config(self):
        """존재하지 않는 설정 조회 테스트"""
        config = RateLimitConfigRegistry.get_config("nonexistent")
        assert config is None
    
    def test_is_enabled(self):
        """설정 활성화 여부 확인 테스트"""
        assert RateLimitConfigRegistry.is_enabled("auth_login") is True
        assert RateLimitConfigRegistry.is_enabled("nonexistent") is False
    
    def test_get_all_configs(self):
        """모든 설정 조회 테스트"""
        configs = RateLimitConfigRegistry.get_all_configs()
        
        assert isinstance(configs, dict)
        assert "auth_login" in configs
        assert "posts_create" in configs
        assert "comments_create" in configs
        assert len(configs) >= 5  # 최소 5개 설정 있어야 함


class TestRateLimitResult:
    """Rate Limit 결과 모델 테스트"""
    
    def test_rate_limit_result_creation(self):
        """Rate Limit 결과 생성 테스트"""
        result = RateLimitResult(
            allowed=True,
            limit=5,
            remaining=3,
            reset_time=1721548860,
            key="test_key"
        )
        
        assert result.allowed is True
        assert result.limit == 5
        assert result.remaining == 3
        assert result.reset_time == 1721548860
        assert result.retry_after is None
        assert result.key == "test_key"
    
    def test_rate_limit_result_with_retry_after(self):
        """Retry-After 포함 Rate Limit 결과 테스트"""
        result = RateLimitResult(
            allowed=False,
            limit=3,
            remaining=0,
            reset_time=1721548860,
            retry_after=45,
            key="test_key"
        )
        
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 45


class TestRateLimitingService:
    """Rate Limiting 서비스 테스트"""
    
    @pytest.fixture
    def mock_redis_factory(self):
        """Mock Redis Factory 픽스처"""
        factory = Mock(spec=RedisFactory)
        mock_redis = AsyncMock(spec=Redis)
        # Redis 메소드들을 AsyncMock으로 설정
        mock_redis.incr = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.scan = AsyncMock()
        mock_redis.pipeline = Mock()
        mock_redis.ttl = AsyncMock()
        
        factory.get_client = AsyncMock(return_value=mock_redis)
        return factory, mock_redis
    
    @pytest.fixture
    def mock_settings(self):
        """Mock Settings 픽스처"""
        with patch('nadle_backend.services.rate_limiting_service.get_settings') as mock:
            settings = Mock()
            settings.rate_limiting_enabled = True
            settings.redis_key_prefix = "test:"
            settings.rate_limiting_key_prefix = "rate_limit:"
            mock.return_value = settings
            yield settings
    
    @pytest.fixture
    def rate_limiting_service(self, mock_redis_factory, mock_settings):
        """Rate Limiting 서비스 픽스처"""
        factory, mock_redis = mock_redis_factory
        service = RateLimitingService(factory)
        service._redis_client = mock_redis
        service._key_prefix = "test:rate_limit:"
        return service, mock_redis
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request 픽스처"""
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}
        return request
    
    def test_get_client_ip_direct(self, rate_limiting_service, mock_request):
        """직접 연결 IP 추출 테스트"""
        service, _ = rate_limiting_service
        
        ip = service._get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_forwarded_for(self, rate_limiting_service, mock_request):
        """X-Forwarded-For 헤더 IP 추출 테스트"""
        service, _ = rate_limiting_service
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        
        ip = service._get_client_ip(mock_request)
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_real_ip(self, rate_limiting_service, mock_request):
        """X-Real-IP 헤더 IP 추출 테스트"""
        service, _ = rate_limiting_service
        mock_request.headers = {"X-Real-IP": "203.0.113.2"}
        
        ip = service._get_client_ip(mock_request)
        assert ip == "203.0.113.2"
    
    def test_generate_rate_limit_key_ip_strategy(self, rate_limiting_service, mock_request):
        """IP 전략 키 생성 테스트"""
        service, _ = rate_limiting_service
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        with patch('time.time', return_value=1721548800):
            key = service._generate_rate_limit_key(mock_request, config)
            
            # 키 형식: prefix + endpoint_hash + : + ip + : + window
            assert key.startswith("test:rate_limit:")
            assert "192.168.1.1" in key
            assert "28692480" in key  # 1721548800 // 60 = 28692480
    
    def test_generate_rate_limit_key_user_strategy(self, rate_limiting_service, mock_request):
        """사용자 전략 키 생성 테스트"""
        service, _ = rate_limiting_service
        config = RateLimitConfig(
            endpoint="/posts",
            limit=5,
            window=60,
            key_strategy=RateLimitStrategy.USER
        )
        
        with patch('time.time', return_value=1721548800):
            key = service._generate_rate_limit_key(mock_request, config, user_id="user123")
            
            assert key.startswith("test:rate_limit:")
            assert "user:user123" in key
    
    def test_generate_rate_limit_key_user_strategy_no_user(self, rate_limiting_service, mock_request):
        """사용자 전략에서 사용자 ID 없을 때 IP 폴백 테스트"""
        service, _ = rate_limiting_service
        config = RateLimitConfig(
            endpoint="/posts",
            limit=5,
            window=60,
            key_strategy=RateLimitStrategy.USER
        )
        
        with patch('time.time', return_value=1721548800):
            key = service._generate_rate_limit_key(mock_request, config)
            
            assert key.startswith("test:rate_limit:")
            assert "192.168.1.1" in key
    
    def test_generate_rate_limit_key_composite_strategy(self, rate_limiting_service, mock_request):
        """복합 전략 키 생성 테스트"""
        service, _ = rate_limiting_service
        config = RateLimitConfig(
            endpoint="/files/upload",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.COMPOSITE
        )
        
        with patch('time.time', return_value=1721548800):
            key = service._generate_rate_limit_key(mock_request, config, user_id="user123")
            
            assert key.startswith("test:rate_limit:")
            assert "192.168.1.1:user:user123" in key
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled_globally(self, rate_limiting_service, mock_request):
        """전역 Rate Limiting 비활성화 테스트"""
        service, _ = rate_limiting_service
        service.settings.rate_limiting_enabled = False
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        result = await service.check_rate_limit(mock_request, config)
        
        assert result.allowed is True
        assert result.key == "disabled"
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled_config(self, rate_limiting_service, mock_request):
        """설정별 Rate Limiting 비활성화 테스트"""
        service, _ = rate_limiting_service
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            enabled=False
        )
        
        result = await service.check_rate_limit(mock_request, config)
        
        assert result.allowed is True
        assert result.key == "disabled"
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self, rate_limiting_service, mock_request):
        """첫 번째 요청 Rate Limiting 테스트"""
        service, mock_redis = rate_limiting_service
        
        # Redis INCR 첫 번째 호출 시 1 반환
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        with patch('time.time', return_value=1721548800):
            result = await service.check_rate_limit(mock_request, config)
        
        assert result.allowed is True
        assert result.limit == 3
        assert result.remaining == 2
        assert result.retry_after is None
        
        # Redis 호출 확인
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self, rate_limiting_service, mock_request):
        """제한 내 요청 Rate Limiting 테스트"""
        service, mock_redis = rate_limiting_service
        
        # Redis INCR 두 번째 호출 시 2 반환
        mock_redis.incr.return_value = 2
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        with patch('time.time', return_value=1721548800):
            result = await service.check_rate_limit(mock_request, config)
        
        assert result.allowed is True
        assert result.limit == 3
        assert result.remaining == 1
        assert result.retry_after is None
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(self, rate_limiting_service, mock_request):
        """제한 정확히 도달 Rate Limiting 테스트"""
        service, mock_redis = rate_limiting_service
        
        # Redis INCR 세 번째 호출 시 3 반환
        mock_redis.incr.return_value = 3
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        with patch('time.time', return_value=1721548800):
            result = await service.check_rate_limit(mock_request, config)
        
        assert result.allowed is True
        assert result.limit == 3
        assert result.remaining == 0
        assert result.retry_after is None
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceed_limit(self, rate_limiting_service, mock_request):
        """제한 초과 Rate Limiting 테스트"""
        service, mock_redis = rate_limiting_service
        
        # Redis INCR 네 번째 호출 시 4 반환
        mock_redis.incr.return_value = 4
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        current_time = 1721548800
        with patch('time.time', return_value=current_time):
            result = await service.check_rate_limit(mock_request, config)
        
        assert result.allowed is False
        assert result.limit == 3
        assert result.remaining == 0
        assert result.retry_after is not None
        assert result.retry_after > 0
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error(self, rate_limiting_service, mock_request):
        """Redis 오류 시 fail-open 테스트"""
        service, mock_redis = rate_limiting_service
        
        # Redis INCR 오류 발생
        mock_redis.incr.side_effect = Exception("Redis connection error")
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        result = await service.check_rate_limit(mock_request, config)
        
        # 오류 시 요청 허용 (fail-open)
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, rate_limiting_service, mock_request):
        """Rate Limit 상태 조회 테스트"""
        service, mock_redis = rate_limiting_service
        
        # Redis GET 호출 시 현재 카운트 반환
        mock_redis.get.return_value = b"2"
        
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60
        )
        
        with patch('time.time', return_value=1721548800):
            result = await service.get_rate_limit_status(mock_request, config)
        
        assert result.allowed is True
        assert result.limit == 3
        assert result.remaining == 1
        
        # INCR이 아닌 GET 호출 확인
        mock_redis.get.assert_called_once()
        mock_redis.incr.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, rate_limiting_service):
        """Rate Limit 리셋 테스트"""
        service, mock_redis = rate_limiting_service
        
        mock_redis.delete.return_value = 1
        
        result = await service.reset_rate_limit("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit_not_found(self, rate_limiting_service):
        """존재하지 않는 키 리셋 테스트"""
        service, mock_redis = rate_limiting_service
        
        mock_redis.delete.return_value = 0
        
        result = await service.reset_rate_limit("nonexistent_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_keys(self, rate_limiting_service):
        """만료된 키 정리 테스트"""
        service, mock_redis = rate_limiting_service
        
        # SCAN 결과 모킹
        test_keys = [b"test:rate_limit:key1", b"test:rate_limit:key2", b"test:rate_limit:key3"]
        mock_redis.scan.return_value = (0, test_keys)
        
        # Pipeline 모킹
        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [-1, 30, -1]  # key1과 key3은 TTL 없음
        mock_pipe.ttl = Mock()  # Pipeline의 ttl은 async가 아님
        mock_redis.pipeline.return_value = mock_pipe
        
        # DELETE 모킹
        mock_redis.delete.return_value = 2
        
        cleaned_count = await service.cleanup_expired_keys()
        
        assert cleaned_count == 2
        mock_redis.delete.assert_called_once()
        
        # TTL이 -1인 키들만 삭제되었는지 확인
        deleted_keys = mock_redis.delete.call_args[0]
        assert len(deleted_keys) == 2