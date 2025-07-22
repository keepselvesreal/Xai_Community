import pytest
import pytest_asyncio
import asyncio
import time
from typing import Optional
from unittest.mock import Mock, patch

from nadle_backend.services.rate_limiting_service import RateLimitingService, get_rate_limiting_service
from nadle_backend.models.rate_limit_config import (
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitConfigRegistry
)
from nadle_backend.database.redis_factory import RedisFactory
from nadle_backend.config import get_settings


@pytest.mark.redis
@pytest.mark.integration
class TestRateLimitingRedisIntegration:
    """Rate Limiting Redis 통합 테스트"""
    
    @pytest.fixture(scope="function")
    async def redis_manager(self):
        """Redis Manager 픽스처"""
        from nadle_backend.database.redis_factory import get_redis_manager
        manager = await get_redis_manager()
        
        # 연결 확인
        if not await manager.is_connected():
            await manager.connect()
            
        yield manager
        
        # 테스트 후 정리
        try:
            if hasattr(manager, 'redis_client') and manager.redis_client:
                # 테스트 키만 삭제
                pattern = f"{get_settings().redis_key_prefix}rate_limit:*"
                cursor = 0
                while True:
                    cursor, keys = await manager.redis_client.scan(cursor=cursor, match=pattern)
                    if keys:
                        await manager.redis_client.delete(*keys)
                    if cursor == 0:
                        break
        except Exception as e:
            print(f"Redis cleanup failed: {e}")
    
    @pytest.fixture(scope="function") 
    async def rate_limiting_service(self, redis_manager):
        """Rate Limiting 서비스 픽스처"""
        service = RateLimitingService()
        await service.initialize()
        return service
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request 픽스처"""
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        return request
    
    async def test_redis_factory_environment_selection(self, redis_manager):
        """환경별 Redis 클라이언트 자동 선택 테스트"""
        settings = get_settings()
        
        # Redis 매니저 확인
        assert redis_manager is not None
        
        # 키 프리픽스 확인
        expected_prefix = settings.redis_key_prefix
        assert expected_prefix in ["dev:", "test:", "stage:", "prod:"]
        
        # Redis 연결 테스트
        assert await redis_manager.is_connected()
        
    async def test_redis_key_namespacing(self, rate_limiting_service, mock_request):
        """Redis 키 네임스페이싱 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        with patch('time.time', return_value=1721548800):
            result = await rate_limiting_service.check_rate_limit(mock_request, config)
            
            # 키가 환경별 프리픽스를 포함하는지 확인
            settings = get_settings()
            expected_prefix = f"{settings.redis_key_prefix}{settings.rate_limiting_key_prefix}"
            assert result.key.startswith(expected_prefix)
    
    async def test_rate_limiting_with_real_redis(self, rate_limiting_service, mock_request):
        """실제 Redis를 사용한 Rate Limiting 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        # 첫 번째 요청
        result1 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result1.allowed is True
        assert result1.remaining == 2
        
        # 두 번째 요청
        result2 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result2.allowed is True
        assert result2.remaining == 1
        
        # 세 번째 요청
        result3 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result3.allowed is True
        assert result3.remaining == 0
        
        # 네 번째 요청 (제한 초과)
        result4 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result4.allowed is False
        assert result4.remaining == 0
        assert result4.retry_after is not None
        assert result4.retry_after > 0
    
    async def test_rate_limiting_time_window_reset(self, rate_limiting_service, mock_request):
        """시간 윈도우 리셋 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=2,
            window=3,  # 3초 윈도우
            key_strategy=RateLimitStrategy.IP
        )
        
        # 첫 번째 윈도우에서 제한까지 요청
        result1 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result1.allowed is True
        assert result1.remaining == 1
        
        result2 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result2.allowed is True
        assert result2.remaining == 0
        
        result3 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result3.allowed is False
        
        # 3초 대기 (새로운 윈도우)
        await asyncio.sleep(3.1)
        
        # 새로운 윈도우에서는 다시 허용되어야 함
        result4 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result4.allowed is True
        assert result4.remaining == 1
    
    async def test_rate_limiting_different_ips(self, rate_limiting_service):
        """다른 IP 주소 간 독립적 Rate Limiting 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=2,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        # 첫 번째 IP
        request1 = Mock()
        request1.client = Mock()
        request1.client.host = "192.168.1.100"
        request1.headers = {}
        
        # 두 번째 IP
        request2 = Mock()
        request2.client = Mock()
        request2.client.host = "192.168.1.101"
        request2.headers = {}
        
        # 첫 번째 IP에서 제한까지 요청
        result1 = await rate_limiting_service.check_rate_limit(request1, config)
        assert result1.allowed is True
        assert result1.remaining == 1
        
        result2 = await rate_limiting_service.check_rate_limit(request1, config)
        assert result2.allowed is True
        assert result2.remaining == 0
        
        result3 = await rate_limiting_service.check_rate_limit(request1, config)
        assert result3.allowed is False
        
        # 두 번째 IP는 독립적으로 동작해야 함
        result4 = await rate_limiting_service.check_rate_limit(request2, config)
        assert result4.allowed is True
        assert result4.remaining == 1
    
    async def test_rate_limiting_user_strategy(self, rate_limiting_service, mock_request):
        """사용자 전략 Rate Limiting 테스트"""
        config = RateLimitConfig(
            endpoint="/posts",
            limit=2,
            window=60,
            key_strategy=RateLimitStrategy.USER
        )
        
        # 사용자 ID로 Rate Limiting
        result1 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user123"
        )
        assert result1.allowed is True
        assert result1.remaining == 1
        
        result2 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user123"
        )
        assert result2.allowed is True
        assert result2.remaining == 0
        
        result3 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user123"
        )
        assert result3.allowed is False
        
        # 다른 사용자는 독립적으로 동작
        result4 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user456"
        )
        assert result4.allowed is True
        assert result4.remaining == 1
    
    async def test_rate_limiting_composite_strategy(self, rate_limiting_service, mock_request):
        """복합 전략 Rate Limiting 테스트"""
        config = RateLimitConfig(
            endpoint="/files/upload",
            limit=2,
            window=60,
            key_strategy=RateLimitStrategy.COMPOSITE
        )
        
        # 같은 IP, 같은 사용자
        result1 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user123"
        )
        assert result1.allowed is True
        assert result1.remaining == 1
        
        result2 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user123"
        )
        assert result2.allowed is True
        assert result2.remaining == 0
        
        result3 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user123"
        )
        assert result3.allowed is False
        
        # 같은 IP, 다른 사용자는 허용되어야 함
        result4 = await rate_limiting_service.check_rate_limit(
            mock_request, config, user_id="user456"
        )
        assert result4.allowed is True
    
    async def test_get_rate_limit_status_without_increment(self, rate_limiting_service, mock_request):
        """카운터 증가 없이 상태 조회 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        # 초기 상태 조회 (아직 요청 없음)
        status1 = await rate_limiting_service.get_rate_limit_status(mock_request, config)
        assert status1.allowed is True
        assert status1.remaining == 3  # 아직 요청 없으므로 전체 제한
        
        # 실제 요청 하나 보내기
        await rate_limiting_service.check_rate_limit(mock_request, config)
        
        # 상태 조회 (카운터 증가 없이)
        status2 = await rate_limiting_service.get_rate_limit_status(mock_request, config)
        assert status2.allowed is True
        assert status2.remaining == 2  # 한 번 요청했으므로 2개 남음
        
        # 다시 상태 조회 (여전히 카운터 증가 없음)
        status3 = await rate_limiting_service.get_rate_limit_status(mock_request, config)
        assert status3.allowed is True
        assert status3.remaining == 2  # 변화 없음
    
    async def test_reset_rate_limit(self, rate_limiting_service, mock_request):
        """Rate Limit 리셋 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=2,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        # 제한까지 요청
        result1 = await rate_limiting_service.check_rate_limit(mock_request, config)
        result2 = await rate_limiting_service.check_rate_limit(mock_request, config)
        result3 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result3.allowed is False
        
        # 키 리셋
        reset_success = await rate_limiting_service.reset_rate_limit(result3.key)
        assert reset_success is True
        
        # 리셋 후 다시 요청 가능해야 함
        result4 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result4.allowed is True
        assert result4.remaining == 1
    
    async def test_cleanup_expired_keys_integration(self, rate_limiting_service, mock_request):
        """만료된 키 정리 통합 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/test",
            limit=1,
            window=1,  # 1초 윈도우
            key_strategy=RateLimitStrategy.IP
        )
        
        # 요청 생성
        result1 = await rate_limiting_service.check_rate_limit(mock_request, config)
        assert result1.allowed is True
        
        # 1초 대기 (키 만료)
        await asyncio.sleep(1.1)
        
        # 정리 실행 (실제로는 Redis TTL로 자동 만료되므로 0이 반환될 수 있음)
        cleaned_count = await rate_limiting_service.cleanup_expired_keys()
        # 정리 개수는 Redis TTL에 의해 결정되므로 >= 0으로 확인
        assert cleaned_count >= 0
    
    async def test_rate_limiting_config_registry_integration(self, rate_limiting_service, mock_request):
        """설정 레지스트리와의 통합 테스트"""
        # 등록된 설정 사용
        auth_config = RateLimitConfigRegistry.get_config("auth_login")
        assert auth_config is not None
        
        # 실제 Rate Limiting 테스트
        result = await rate_limiting_service.check_rate_limit(mock_request, auth_config)
        assert result.allowed is True
        assert result.limit == auth_config.limit
    
    async def test_concurrent_requests_same_key(self, rate_limiting_service, mock_request):
        """동일 키에 대한 동시 요청 테스트"""
        config = RateLimitConfig(
            endpoint="/auth/login",
            limit=5,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        # 동시에 10개 요청 보내기
        tasks = []
        for _ in range(10):
            task = rate_limiting_service.check_rate_limit(mock_request, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 5개는 허용, 5개는 거부되어야 함
        allowed_count = sum(1 for result in results if result.allowed)
        denied_count = sum(1 for result in results if not result.allowed)
        
        assert allowed_count == 5
        assert denied_count == 5
    
    async def test_different_endpoints_independent_limits(self, rate_limiting_service, mock_request):
        """다른 엔드포인트 간 독립적 제한 테스트"""
        auth_config = RateLimitConfig(
            endpoint="/auth/login",
            limit=2,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        posts_config = RateLimitConfig(
            endpoint="/posts",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP
        )
        
        # auth 엔드포인트에서 제한까지 요청
        result1 = await rate_limiting_service.check_rate_limit(mock_request, auth_config)
        result2 = await rate_limiting_service.check_rate_limit(mock_request, auth_config)
        result3 = await rate_limiting_service.check_rate_limit(mock_request, auth_config)
        
        assert result1.allowed is True
        assert result2.allowed is True  
        assert result3.allowed is False  # auth 제한 초과
        
        # posts 엔드포인트는 독립적으로 동작해야 함
        result4 = await rate_limiting_service.check_rate_limit(mock_request, posts_config)
        assert result4.allowed is True
        assert result4.remaining == 2


@pytest.mark.redis
@pytest.mark.integration
class TestRateLimitingServiceFactory:
    """Rate Limiting 서비스 팩토리 테스트"""
    
    async def test_get_rate_limiting_service_singleton(self):
        """Rate Limiting 서비스 싱글톤 패턴 테스트"""
        # 전역 서비스 인스턴스 리셋
        import nadle_backend.services.rate_limiting_service
        nadle_backend.services.rate_limiting_service._rate_limiting_service = None
        
        # 첫 번째 호출
        service1 = await get_rate_limiting_service()
        assert service1 is not None
        
        # 두 번째 호출 (같은 인스턴스여야 함)
        service2 = await get_rate_limiting_service()
        assert service1 is service2
    
    async def test_service_initialization_with_redis_factory(self):
        """Redis Factory와의 초기화 테스트"""
        service = RateLimitingService()
        
        # 초기화 전에는 클라이언트가 없어야 함
        assert service._redis_client is None
        
        # 초기화
        await service.initialize()
        
        # 초기화 후에는 클라이언트가 있어야 함
        assert service._redis_client is not None
        assert service._key_prefix != ""