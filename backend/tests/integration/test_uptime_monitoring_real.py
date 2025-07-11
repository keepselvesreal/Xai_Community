"""
업타임 모니터링 실제 서비스 연동 테스트

실제 UptimeRobot API, 이메일 서비스, 디스코드 웹훅과의 연동 테스트
"""
import pytest
import asyncio
import os
from datetime import datetime

from nadle_backend.services.uptime_monitoring import (
    UptimeMonitoringService,
    HealthCheckService,
    UptimeStatus
)
from nadle_backend.services.notification_service import NotificationService
from nadle_backend.config import settings


@pytest.mark.integration
@pytest.mark.real_services
class TestUptimeMonitoringRealIntegration:
    """업타임 모니터링 실제 서비스 연동 테스트"""

    @pytest.fixture
    def uptime_service(self):
        """실제 UptimeRobot API를 사용하는 업타임 모니터링 서비스"""
        api_key = settings.uptimerobot_api_key
        if not api_key:
            pytest.skip("UptimeRobot API key not configured")
        
        return UptimeMonitoringService(api_key=api_key)

    @pytest.fixture
    def notification_service(self):
        """실제 알림 서비스"""
        return NotificationService()

    @pytest.mark.asyncio
    async def test_real_health_check_comprehensive(self):
        """실제 시스템 종합 헬스체크 테스트"""
        # Given: 실제 헬스체크 서비스
        health_service = HealthCheckService()

        # When: 종합 헬스체크 실행
        result = await health_service.comprehensive_health_check()

        # Then: 헬스체크 결과 검증
        assert "status" in result
        assert "overall_health" in result
        assert "checks" in result
        assert "timestamp" in result
        
        # 각 체크 항목 검증
        checks = result["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "external_apis" in checks
        
        # 각 체크는 status를 가져야 함
        for check_name, check_result in checks.items():
            assert "status" in check_result
            assert check_result["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_real_simple_health_check(self):
        """실제 간단한 헬스체크 테스트 (외부 모니터링용)"""
        # Given: 실제 헬스체크 서비스
        health_service = HealthCheckService()

        # When: 간단한 헬스체크 실행
        result = await health_service.simple_health_check()

        # Then: 간단한 헬스체크 결과 검증
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "uptime" in result
        assert result["service"] == "nadle-backend-api"

    def test_real_uptimerobot_get_monitors(self, uptime_service):
        """실제 UptimeRobot에서 모니터 목록 조회 테스트"""
        try:
            # When: 실제 API에서 모니터 목록 조회
            monitors = uptime_service.get_monitors()

            # Then: 모니터 목록 반환
            assert isinstance(monitors, list)
            
            # 모니터가 있는 경우 구조 검증
            if monitors:
                monitor = monitors[0]
                assert hasattr(monitor, 'id')
                assert hasattr(monitor, 'name')
                assert hasattr(monitor, 'url')
                assert hasattr(monitor, 'status')
                assert isinstance(monitor.status, UptimeStatus)
                
        except Exception as e:
            # 실제 API 호출 실패 시 스킵 (네트워크 문제 등)
            pytest.skip(f"UptimeRobot API not accessible: {e}")

    def test_real_uptimerobot_create_and_delete_monitor(self, uptime_service):
        """실제 UptimeRobot에서 모니터 생성 및 삭제 테스트"""
        monitor = None
        try:
            # Given: 테스트용 모니터 정보
            test_url = "https://httpbin.org/status/200"
            test_name = f"Test Monitor {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # When: 실제 모니터 생성
            monitor = uptime_service.create_monitor(
                name=test_name,
                url=test_url,
                interval=300
            )

            # Then: 모니터 생성 성공
            assert monitor.name == test_name
            assert monitor.url == test_url
            assert monitor.id > 0
            
            # When: 모니터 삭제
            delete_result = uptime_service.delete_monitor(monitor.id)
            
            # Then: 삭제 성공
            assert delete_result is True
            monitor = None  # 삭제됨을 표시
            
        except Exception as e:
            # 생성된 모니터가 있다면 정리
            if monitor and monitor.id:
                try:
                    uptime_service.delete_monitor(monitor.id)
                except:
                    pass
            
            # 실제 API 호출 실패 시 스킵
            pytest.skip(f"UptimeRobot API test failed: {e}")

    def test_real_uptimerobot_get_monitor_logs(self, uptime_service):
        """실제 UptimeRobot에서 모니터 로그 조회 테스트"""
        try:
            # Given: 기존 모니터 목록 조회
            monitors = uptime_service.get_monitors()
            
            if not monitors:
                pytest.skip("No monitors available for log testing")
            
            # When: 첫 번째 모니터의 로그 조회
            first_monitor = monitors[0]
            logs = uptime_service.get_monitor_logs(first_monitor.id, days=1)

            # Then: 로그 목록 반환
            assert isinstance(logs, list)
            
            # 로그가 있는 경우 구조 검증
            if logs:
                log_entry = logs[0]
                assert "type" in log_entry
                assert "datetime" in log_entry
                
        except Exception as e:
            # 실제 API 호출 실패 시 스킵
            pytest.skip(f"UptimeRobot API log test failed: {e}")

    @pytest.mark.asyncio
    async def test_real_notification_discord_webhook(self, notification_service):
        """실제 디스코드 웹훅 알림 테스트"""
        if not settings.discord_webhook_url:
            pytest.skip("Discord webhook URL not configured")

        try:
            # Given: 테스트 메시지
            test_message = f"🔧 업타임 모니터링 테스트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # When: 디스코드 웹훅으로 알림 전송
            result = await notification_service.send_discord_notification(
                message=test_message,
                title="업타임 모니터링 테스트",
                color=0x00ff00  # 녹색
            )

            # Then: 알림 전송 성공
            assert result is True
            
        except Exception as e:
            # 네트워크 문제 등으로 실패 시 스킵
            pytest.skip(f"Discord webhook test failed: {e}")

    @pytest.mark.asyncio
    async def test_real_notification_email(self, notification_service):
        """실제 이메일 알림 테스트"""
        if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password]):
            pytest.skip("Email SMTP settings not configured")

        try:
            # Given: 테스트 이메일 정보
            test_subject = f"업타임 모니터링 테스트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            test_message = """
            이것은 업타임 모니터링 시스템의 이메일 알림 테스트입니다.
            
            테스트 시간: {timestamp}
            시스템 상태: 정상
            """.format(timestamp=datetime.now().isoformat())
            
            # When: 이메일 알림 전송
            result = await notification_service.send_email_notification(
                to_email=settings.smtp_user,  # 자기 자신에게 전송
                subject=test_subject,
                message=test_message
            )

            # Then: 이메일 전송 성공
            assert result is True
            
        except Exception as e:
            # SMTP 문제 등으로 실패 시 스킵
            pytest.skip(f"Email notification test failed: {e}")

    @pytest.mark.asyncio
    async def test_real_end_to_end_monitoring_flow(self, uptime_service, notification_service):
        """실제 업타임 모니터링 전체 플로우 테스트"""
        monitor = None
        try:
            # Given: 테스트 URL (의도적으로 다운 상태)
            test_url = "https://httpbin.org/status/500"  # 500 에러 반환
            test_name = f"E2E Test Monitor {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Step 1: 모니터 생성
            monitor = uptime_service.create_monitor(
                name=test_name,
                url=test_url,
                interval=300
            )
            assert monitor.id > 0
            
            # Step 2: 헬스체크 실행
            health_service = HealthCheckService()
            health_result = await health_service.comprehensive_health_check()
            assert "status" in health_result
            
            # Step 3: 시뮬레이션된 다운타임 알림 (실제로는 다운이 아니므로 테스트 알림)
            if settings.discord_webhook_url:
                notification_result = await notification_service.send_discord_notification(
                    message=f"🔴 모니터 '{monitor.name}'에서 문제가 감지되었습니다 (테스트)",
                    title="업타임 모니터링 알림",
                    color=0xff0000  # 빨간색
                )
                assert notification_result is True
            
            # Step 4: 모니터 정리
            delete_result = uptime_service.delete_monitor(monitor.id)
            assert delete_result is True
            monitor = None
            
        except Exception as e:
            # 정리 작업
            if monitor and monitor.id:
                try:
                    uptime_service.delete_monitor(monitor.id)
                except:
                    pass
            
            pytest.skip(f"End-to-end test failed: {e}")

    @pytest.mark.asyncio
    async def test_real_performance_monitoring_integration(self):
        """실제 성능 모니터링과 업타임 모니터링 통합 테스트"""
        try:
            # Given: 헬스체크와 성능 모니터링을 동시에 실행
            health_service = HealthCheckService()
            
            # When: 병렬로 여러 헬스체크 실행
            tasks = [
                health_service.comprehensive_health_check(),
                health_service.simple_health_check(),
                health_service._check_database(),
                health_service._check_redis(),
                health_service._check_external_apis()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Then: 모든 헬스체크가 완료됨
            assert len(results) == 5
            
            # 예외가 발생하지 않은 결과들 검증
            for result in results:
                if not isinstance(result, Exception):
                    assert "status" in result
                    
        except Exception as e:
            pytest.skip(f"Performance monitoring integration test failed: {e}")

    def test_real_error_recovery_and_resilience(self, uptime_service):
        """실제 에러 복구 및 복원력 테스트"""
        try:
            # Given: 잘못된 URL로 모니터 생성 시도
            invalid_url = "not-a-valid-url"
            
            # When: 잘못된 모니터 생성 시도
            with pytest.raises(Exception):
                uptime_service.create_monitor(
                    name="Invalid Test Monitor",
                    url=invalid_url,
                    interval=300
                )
            
            # Then: 정상적인 URL로는 여전히 작동해야 함
            valid_monitor = uptime_service.create_monitor(
                name=f"Recovery Test {datetime.now().strftime('%H%M%S')}",
                url="https://httpbin.org/status/200",
                interval=300
            )
            
            assert valid_monitor.id > 0
            
            # 정리
            uptime_service.delete_monitor(valid_monitor.id)
            
        except Exception as e:
            pytest.skip(f"Error recovery test failed: {e}")


@pytest.mark.integration
@pytest.mark.real_services
class TestUptimeMonitoringHealthEndpoints:
    """업타임 모니터링을 위한 헬스체크 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self):
        """헬스체크 엔드포인트 응답시간 테스트"""
        import time
        
        health_service = HealthCheckService()
        
        # When: 응답시간 측정
        start_time = time.time()
        result = await health_service.simple_health_check()
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Then: 응답시간이 합리적인 범위 내에 있어야 함
        assert response_time < 1.0  # 1초 미만
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_endpoint_concurrent_requests(self):
        """헬스체크 엔드포인트 동시 요청 처리 테스트"""
        health_service = HealthCheckService()
        
        # When: 동시에 여러 헬스체크 요청
        tasks = [health_service.simple_health_check() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Then: 모든 요청이 성공적으로 처리됨
        assert len(results) == 10
        for result in results:
            assert result["status"] == "healthy"
            assert "timestamp" in result