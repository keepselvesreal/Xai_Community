"""
HetrixTools API 실제 서비스 연동 테스트

실제 HetrixTools API, 이메일 서비스, 디스코드 웹훅과의 연동 테스트
UptimeRobot에서 HetrixTools로 마이그레이션하는 TDD 기반 테스트
"""
import pytest
import asyncio
import os
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from nadle_backend.config import settings
from nadle_backend.services.hetrix_monitoring import (
    HetrixToolsClient,
    HetrixMonitoringService,
    HealthCheckService,
    UptimeStatus,
    Monitor
)


# HetrixToolsTestClient 제거 - 실제 구현체인 HetrixToolsClient 사용


@pytest.mark.integration
@pytest.mark.real_services
class TestHetrixToolsRealIntegration:
    """HetrixTools API 실제 서비스 연동 테스트"""

    @pytest.fixture
    def hetrix_client(self):
        """실제 HetrixTools API를 사용하는 클라이언트"""
        api_token = settings.hetrixtools_api_token
        if not api_token:
            pytest.skip("HetrixTools API token not configured")
        
        return HetrixToolsClient(api_token=api_token)

    @pytest.mark.asyncio
    async def test_hetrixtools_api_authentication(self, hetrix_client):
        """HetrixTools API 인증 테스트"""
        try:
            async with hetrix_client as client:
                # When: API 토큰으로 모니터 목록 조회
                monitors = await client.get_monitors()
                
                # Then: 성공적으로 응답을 받아야 함
                assert isinstance(monitors, list)
                print(f"✅ HetrixTools API 인증 성공. 등록된 모니터 수: {len(monitors)}")
            
        except Exception as e:
            pytest.fail(f"HetrixTools API 인증 실패: {e}")
        finally:
            # Rate limit 방지를 위한 지연
            await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_hetrixtools_get_existing_monitors(self, hetrix_client):
        """등록된 모니터 조회 테스트"""
        try:
            async with hetrix_client as client:
                # When: 모니터 목록 조회
                monitors = await client.get_monitors()
                
                # Then: 모니터 목록 반환
                assert isinstance(monitors, list)
                
                # 각 모니터의 기본 구조 검증
                if monitors:
                    monitor = monitors[0]
                    assert hasattr(monitor, 'id'), "모니터에 'id' 속성이 없습니다"
                    assert hasattr(monitor, 'name'), "모니터에 'name' 속성이 없습니다"
                    assert hasattr(monitor, 'url'), "모니터에 'url' 속성이 없습니다"
                    assert hasattr(monitor, 'status'), "모니터에 'status' 속성이 없습니다"
                    
                    print(f"✅ 모니터 목록 조회 성공. 모니터 수: {len(monitors)}")
                    for monitor in monitors:
                        print(f"  - {monitor.name}: {monitor.url} (상태: {monitor.status.value})")
                else:
                    print("⚠️ 등록된 모니터가 없습니다")
                
        except Exception as e:
            pytest.fail(f"모니터 목록 조회 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrixtools_environment_specific_monitors(self, hetrix_client):
        """환경별 모니터 구분 테스트"""
        try:
            async with hetrix_client as client:
                # Given: 환경별 모니터 이름 패턴
                production_pattern = "production-xai-community"
                staging_pattern = "staging-xai-community"
                
                # When: 모니터 목록 조회
                monitors = await client.get_monitors()
                
                # Then: 환경별 모니터 확인
                production_monitor = None
                staging_monitor = None
                
                for monitor in monitors:
                    if production_pattern in monitor.name:
                        production_monitor = monitor
                    elif staging_pattern in monitor.name:
                        staging_monitor = monitor
                
                # 환경별 모니터 존재 여부 확인
                if production_monitor:
                    print(f"✅ 프로덕션 모니터 발견: {production_monitor.name}")
                    assert production_pattern in production_monitor.name
                else:
                    print(f"⚠️ 프로덕션 모니터 '{production_pattern}'를 찾을 수 없습니다")
                
                if staging_monitor:
                    print(f"✅ 스테이징 모니터 발견: {staging_monitor.name}")
                    assert staging_pattern in staging_monitor.name
                else:
                    print(f"⚠️ 스테이징 모니터 '{staging_pattern}'를 찾을 수 없습니다")
                
                # 최소 하나의 환경 모니터는 있어야 함
                assert production_monitor or staging_monitor, "환경별 모니터가 설정되지 않았습니다"
            
        except Exception as e:
            pytest.fail(f"환경별 모니터 구분 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrixtools_get_specific_monitor_by_name(self, hetrix_client):
        """특정 이름으로 모니터 조회 테스트"""
        try:
            async with hetrix_client as client:
                # Given: 조회할 모니터 이름들
                target_names = ["production-xai-community", "staging-xai-community"]
                
                for name in target_names:
                    # When: 이름으로 모니터 조회
                    monitor = await client.get_monitor_by_name(name)
                    
                    # Then: 모니터 존재 확인
                    if monitor:
                        assert monitor.name == name
                        assert monitor.id
                        assert monitor.url
                        assert monitor.status
                        print(f"✅ 모니터 '{name}' 조회 성공")
                        print(f"  - ID: {monitor.id}")
                        print(f"  - URL: {monitor.url}")
                        print(f"  - 상태: {monitor.status.value}")
                    else:
                        print(f"⚠️ 모니터 '{name}'를 찾을 수 없습니다")
                    
        except Exception as e:
            pytest.fail(f"특정 모니터 조회 실패: {e}")


@pytest.mark.integration
@pytest.mark.real_services
class TestHetrixMonitoringService:
    """새로 구현한 HetrixMonitoringService 테스트"""

    @pytest.fixture
    def hetrix_service(self):
        """HetrixMonitoringService 픽스처"""
        api_token = settings.hetrixtools_api_token
        if not api_token:
            pytest.skip("HetrixTools API 토큰이 설정되지 않았습니다")
        
        return HetrixMonitoringService(api_token=api_token)

    @pytest.mark.asyncio
    async def test_hetrix_service_get_monitors(self, hetrix_service):
        """HetrixMonitoringService로 모니터 목록 조회 테스트"""
        try:
            async with hetrix_service as service:
                # When: 모니터 목록 조회
                monitors = await service.get_monitors_async()
                
                # Then: 모니터 목록 반환
                assert isinstance(monitors, list)
                assert len(monitors) > 0
                
                print(f"✅ 서비스를 통한 모니터 조회 성공: {len(monitors)}개")
                
                # 각 모니터 객체 검증
                for monitor in monitors:
                    assert isinstance(monitor, Monitor)
                    assert monitor.id
                    assert monitor.name
                    assert monitor.url
                    assert isinstance(monitor.status, UptimeStatus)
                    
                    print(f"  - {monitor.name}: {monitor.status.value} (업타임: {monitor.uptime}%)")
                    
        except Exception as e:
            pytest.fail(f"HetrixMonitoringService 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrix_service_environment_filtering(self, hetrix_service):
        """환경별 모니터 필터링 테스트"""
        try:
            async with hetrix_service as service:
                # When: 프로덕션 환경 모니터 조회
                prod_monitors = await service.client.get_monitors_by_environment("production")
                
                # Then: 프로덕션 모니터만 반환
                assert isinstance(prod_monitors, list)
                
                for monitor in prod_monitors:
                    assert "production-xai-community" in monitor.name
                    print(f"✅ 프로덕션 모니터: {monitor.name}")
                
                # When: 스테이징 환경 모니터 조회
                staging_monitors = await service.client.get_monitors_by_environment("staging")
                
                # Then: 스테이징 모니터만 반환
                assert isinstance(staging_monitors, list)
                
                for monitor in staging_monitors:
                    assert "staging-xai-community" in monitor.name
                    print(f"✅ 스테이징 모니터: {monitor.name}")
                
                # 최소 하나씩은 있어야 함
                assert len(prod_monitors) > 0 or len(staging_monitors) > 0
                
        except Exception as e:
            pytest.fail(f"환경별 필터링 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrix_service_current_environment(self, hetrix_service):
        """현재 환경 모니터 조회 테스트"""
        try:
            async with hetrix_service as service:
                # When: 현재 환경 모니터 조회
                current_monitors = await service.get_current_environment_monitors()
                
                # Then: 현재 환경에 맞는 모니터 반환
                assert isinstance(current_monitors, list)
                
                print(f"✅ 현재 환경 모니터 수: {len(current_monitors)}개")
                
                for monitor in current_monitors:
                    print(f"  - {monitor.name}: {monitor.status.value}")
                    
        except Exception as e:
            pytest.fail(f"현재 환경 모니터 조회 실패: {e}")

    @pytest.mark.asyncio
    async def test_health_check_service_integration(self):
        """HealthCheckService와 HetrixTools 통합 테스트"""
        try:
            # Given: HealthCheckService
            health_service = HealthCheckService()
            
            # When: 종합 헬스체크 실행
            health_result = await health_service.comprehensive_health_check()
            
            # Then: 헬스체크 결과 검증
            assert "status" in health_result
            assert "checks" in health_result
            assert "hetrix_monitoring" in health_result["checks"]
            
            hetrix_check = health_result["checks"]["hetrix_monitoring"]
            assert "status" in hetrix_check
            
            print(f"✅ HetrixTools 헬스체크 상태: {hetrix_check['status']}")
            print(f"   총 모니터 수: {hetrix_check.get('total_monitors', 'N/A')}")
            print(f"   활성 모니터 수: {hetrix_check.get('active_monitors', 'N/A')}")
            
        except Exception as e:
            pytest.fail(f"헬스체크 통합 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrix_client_context_manager(self):
        """HetrixToolsClient 컨텍스트 매니저 테스트"""
        try:
            api_token = settings.hetrixtools_api_token
            if not api_token:
                pytest.skip("API 토큰이 없습니다")
            
            # When: 컨텍스트 매니저로 클라이언트 사용
            async with HetrixToolsClient(api_token) as client:
                monitors = await client.get_monitors()
                
                # Then: 정상 작동
                assert isinstance(monitors, list)
                print(f"✅ 컨텍스트 매니저 테스트 성공: {len(monitors)}개 모니터")
                
        except Exception as e:
            pytest.fail(f"컨텍스트 매니저 테스트 실패: {e}")
            
    @pytest.mark.asyncio
    async def test_monitor_data_structure(self, hetrix_service):
        """Monitor 데이터 구조 검증 테스트"""
        try:
            async with hetrix_service as service:
                monitors = await service.get_monitors_async()
                
                if not monitors:
                    pytest.skip("테스트할 모니터가 없습니다")
                
                monitor = monitors[0]
                
                # Monitor 객체 필드 검증
                assert hasattr(monitor, 'id')
                assert hasattr(monitor, 'name')
                assert hasattr(monitor, 'url')
                assert hasattr(monitor, 'status')
                assert hasattr(monitor, 'uptime')
                assert hasattr(monitor, 'created_at')
                assert hasattr(monitor, 'last_check')
                assert hasattr(monitor, 'last_status_change')
                assert hasattr(monitor, 'response_time')
                assert hasattr(monitor, 'locations')
                
                # 타입 검증
                assert isinstance(monitor.status, UptimeStatus)
                assert isinstance(monitor.uptime, float)
                assert isinstance(monitor.response_time, dict)
                assert isinstance(monitor.locations, dict)
                
                print(f"✅ Monitor 데이터 구조 검증 완료")
                print(f"   ID: {monitor.id}")
                print(f"   이름: {monitor.name}")
                print(f"   상태: {monitor.status.value}")
                print(f"   업타임: {monitor.uptime}%")
                print(f"   응답 시간: {monitor.response_time}")
                
        except Exception as e:
            pytest.fail(f"Monitor 데이터 구조 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrixtools_get_monitor_logs(self, hetrix_service):
        """모니터 로그 조회 테스트"""
        try:
            async with hetrix_service as service:
                # Given: 기존 모니터 조회
                monitors = await service.get_monitors_async()
                
                if not monitors:
                    pytest.skip("로그 조회 테스트를 위한 모니터가 없습니다")
                
                # When: 첫 번째 모니터의 로그 조회
                first_monitor = monitors[0]
                monitor_id = first_monitor.id
                
                try:
                    logs = await service.client.get_monitor_logs(monitor_id, days=1)
                
                    # Then: 로그 목록 반환
                    assert isinstance(logs, list)
                    print(f"✅ 모니터 '{first_monitor.name}' 로그 조회 성공. 로그 수: {len(logs)}")
                    
                    # 로그가 있는 경우 구조 검증
                    if logs:
                        log_entry = logs[0]
                        print(f"  - 최근 로그: {log_entry}")
                    else:
                        print("  - 최근 로그가 없습니다")
                        
                except aiohttp.ClientResponseError as e:
                    if e.status == 404:
                        print(f"⚠️ 모니터 로그 API 엔드포인트를 찾을 수 없습니다 (404)")
                        pytest.skip("로그 API 엔드포인트가 지원되지 않습니다")
                    else:
                        raise
                    
        except Exception as e:
            pytest.fail(f"모니터 로그 조회 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrixtools_api_error_handling(self, hetrix_service):
        """HetrixTools API 에러 처리 테스트"""
        try:
            async with hetrix_service as service:
                # Given: 잘못된 API 클라이언트
                invalid_client = HetrixToolsClient(api_token="invalid_token_123")
                
                # When: 잘못된 토큰으로 API 호출
                with pytest.raises(aiohttp.ClientResponseError):
                    async with invalid_client as client:
                        await client.get_monitors()
                
                print("✅ 잘못된 API 토큰에 대한 에러 처리 확인")
                
                # When: 존재하지 않는 모니터 조회
                non_existent_monitor = await service.client.get_monitor_by_name("non-existent-monitor-123")
                
                # Then: None 반환
                assert non_existent_monitor is None
                print("✅ 존재하지 않는 모니터 조회 시 None 반환 확인")
            
        except Exception as e:
            pytest.fail(f"API 에러 처리 테스트 실패: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="실제 모니터 생성/삭제는 신중하게 진행")
    async def test_hetrixtools_create_and_delete_monitor(self, hetrix_client):
        """HetrixTools 모니터 생성 및 삭제 테스트 (선택적)"""
        monitor_id = None
        try:
            # Given: 테스트용 모니터 정보
            test_name = f"Test Monitor {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_url = "https://httpbin.org/status/200"
            
            # When: 테스트 모니터 생성
            create_result = await hetrix_client.create_monitor(
                name=test_name,
                url=test_url
            )
            
            # Then: 모니터 생성 성공
            assert "id" in create_result
            monitor_id = create_result["id"]
            print(f"✅ 테스트 모니터 생성 성공: {test_name} (ID: {monitor_id})")
            
            # When: 모니터 삭제
            delete_result = await hetrix_client.delete_monitor(monitor_id)
            
            # Then: 삭제 성공
            assert delete_result is True
            print(f"✅ 테스트 모니터 삭제 성공: {monitor_id}")
            monitor_id = None
            
        except Exception as e:
            # 생성된 모니터가 있다면 정리
            if monitor_id:
                try:
                    await hetrix_client.delete_monitor(monitor_id)
                    print(f"🧹 정리: 테스트 모니터 {monitor_id} 삭제")
                except:
                    pass
            
            pytest.fail(f"모니터 생성/삭제 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrixtools_api_response_time(self, hetrix_service):
        """HetrixTools API 응답시간 테스트"""
        import time
        
        try:
            async with hetrix_service as service:
                # When: API 응답시간 측정
                start_time = time.time()
                monitors = await service.get_monitors_async()
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Then: 응답시간이 합리적인 범위 내에 있어야 함
                assert response_time < 5.0  # 5초 미만
                print(f"✅ HetrixTools API 응답시간: {response_time:.2f}초")
            
        except Exception as e:
            pytest.fail(f"API 응답시간 테스트 실패: {e}")

    @pytest.mark.asyncio
    async def test_hetrixtools_concurrent_requests(self, hetrix_service):
        """HetrixTools API 동시 요청 처리 테스트 (Rate Limit 고려)"""
        try:
            async with hetrix_service as service:
                # When: 순차적으로 여러 API 요청 (Rate Limit 방지)
                results = []
                for i in range(2):  # 무료 플랜 고려하여 2개만
                    try:
                        monitors = await service.get_monitors_async()
                        results.append(monitors)
                        print(f"✅ 요청 {i+1} 성공: {len(monitors)}개 모니터")
                    except Exception as e:
                        print(f"❌ 요청 {i+1} 실패: {e}")
                        results.append(e)
                    
                    # Rate limit 방지를 위한 지연
                    if i < 1:  # 마지막 요청 후에는 대기하지 않음
                        await asyncio.sleep(2)
                
                # Then: 최소 1개는 성공해야 함
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) >= 1, f"모든 요청이 실패했습니다: {results}"
                
                print(f"✅ 순차 요청 처리 테스트: {len(successful_results)}/{len(results)} 성공")
            
        except Exception as e:
            pytest.fail(f"동시 요청 처리 테스트 실패: {e}")


@pytest.mark.integration
@pytest.mark.real_services
class TestHetrixToolsEnvironmentConfiguration:
    """HetrixTools 환경 설정 테스트"""

    def test_hetrixtools_api_token_configuration(self):
        """HetrixTools API 토큰 설정 확인"""
        # When: 설정에서 API 토큰 확인
        api_token = settings.hetrixtools_api_token
        
        # Then: API 토큰이 설정되어 있어야 함
        if api_token:
            assert isinstance(api_token, str)
            assert len(api_token) > 10  # 최소 길이 확인
            print(f"✅ HetrixTools API 토큰 설정 확인: {api_token[:8]}...")
        else:
            pytest.skip("HetrixTools API 토큰이 설정되지 않았습니다")

    def test_environment_detection(self):
        """현재 환경 감지 테스트"""
        # When: 환경 변수에서 현재 환경 확인
        current_env = os.getenv("ENVIRONMENT", "development")
        
        # Then: 환경이 올바르게 설정되어 있어야 함
        valid_environments = ["development", "staging", "production"]
        assert current_env in valid_environments
        
        print(f"✅ 현재 환경: {current_env}")
        
        # 환경별 모니터 이름 패턴 확인
        if current_env == "production":
            expected_monitor = "production-xai-community"
        else:
            expected_monitor = "staging-xai-community"
        
        print(f"✅ 예상 모니터 이름: {expected_monitor}")


if __name__ == "__main__":
    # 직접 실행 시 간단한 API 테스트
    import asyncio
    
    async def quick_test():
        api_token = os.getenv("HETRIXTOOLS_API_TOKEN")
        if not api_token:
            print("❌ HETRIXTOOLS_API_TOKEN 환경변수가 설정되지 않았습니다")
            return
        
        client = HetrixToolsTestClient(api_token)
        
        try:
            print("🔍 HetrixTools API 빠른 테스트 시작...")
            monitors = await client.get_monitors()
            print(f"✅ API 연결 성공! 등록된 모니터 수: {len(monitors)}")
            
            for monitor in monitors:
                print(f"  - {monitor['name']}: {monitor['url']}")
                
        except Exception as e:
            print(f"❌ API 연결 실패: {e}")
    
    asyncio.run(quick_test())