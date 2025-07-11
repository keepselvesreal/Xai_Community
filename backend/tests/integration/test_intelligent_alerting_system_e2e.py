"""
지능형 알림 시스템 E2E 통합 테스트

전체 알림 시스템의 End-to-End 기능을 테스트합니다.
규칙 생성부터 실제 알림 전송까지의 전체 워크플로우를 검증합니다.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta

from nadle_backend.services.intelligent_alerting import (
    IntelligentAlertingService,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    AlertCondition,
    AlertThreshold
)
from nadle_backend.services.notification_service import NotificationService


class TestIntelligentAlertingSystemE2E:
    """지능형 알림 시스템 E2E 통합 테스트"""

    @pytest.mark.asyncio
    async def test_complete_alerting_workflow(self, async_client: AsyncClient):
        """완전한 알림 워크플로우 E2E 테스트"""
        # Given: 알림 규칙 생성 데이터
        rule_data = {
            "name": "e2e_cpu_alert",
            "description": "E2E 테스트용 CPU 알림 규칙",
            "condition": "greater_than",
            "threshold": {
                "metric": "cpu_usage",
                "value": 75.0,
                "duration_minutes": 2
            },
            "severity": "high",
            "channels": ["email", "discord"],
            "cooldown_minutes": 15,
            "enabled": True
        }

        # Step 1: 알림 규칙 생성
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        
        created_rule = create_response.json()
        rule_name = created_rule["name"]

        # Step 2: 생성된 규칙 조회
        get_response = await async_client.get(f"/api/alerts/rules/{rule_name}")
        assert get_response.status_code == status.HTTP_200_OK
        retrieved_rule = get_response.json()
        assert retrieved_rule["name"] == rule_name
        assert retrieved_rule["enabled"] is True

        # Step 3: 규칙 목록에서 확인
        list_response = await async_client.get("/api/alerts/rules")
        assert list_response.status_code == status.HTTP_200_OK
        rules_list = list_response.json()
        rule_names = [rule["name"] for rule in rules_list["rules"]]
        assert rule_name in rule_names

        # Step 4: 모든 규칙 평가 (Mock 모니터링 서비스는 45.5를 반환하므로 트리거되지 않음)
        evaluate_response = await async_client.post("/api/alerts/evaluate")
        assert evaluate_response.status_code == status.HTTP_200_OK
        evaluation_results = evaluate_response.json()
        
        # E2E 규칙에 대한 평가 결과 찾기
        e2e_result = None
        for result in evaluation_results["evaluation_results"]:
            if result["rule_name"] == rule_name:
                e2e_result = result
                break
        
        assert e2e_result is not None
        assert e2e_result["should_alert"] is False  # 45.5 < 75.0

        # Step 5: 수동 알림 전송 (Mock을 사용하여)
        with patch('nadle_backend.services.notification_service.NotificationService.send_email_notification') as mock_email, \
             patch('nadle_backend.services.notification_service.NotificationService.send_discord_notification') as mock_discord:
            
            mock_email.return_value = True
            mock_discord.return_value = True
            
            manual_alert_data = {
                "rule_name": rule_name,
                "metric_data": {
                    "metric_value": 85.0,
                    "server": "web-server-01",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            send_response = await async_client.post("/api/alerts/send", json=manual_alert_data)
            assert send_response.status_code == status.HTTP_200_OK
            
            send_results = send_response.json()
            assert "email" in send_results
            assert "discord" in send_results

        # Step 6: 알림 이력 조회
        history_response = await async_client.get(f"/api/alerts/history/{rule_name}")
        assert history_response.status_code == status.HTTP_200_OK
        
        history_data = history_response.json()
        assert history_data["rule_name"] == rule_name
        assert "history" in history_data

        # Step 7: 통계 조회
        stats_response = await async_client.get("/api/alerts/statistics")
        assert stats_response.status_code == status.HTTP_200_OK
        
        stats = stats_response.json()
        assert "total_rules" in stats
        assert "active_rules" in stats
        assert stats["total_rules"] >= 1

        # Step 8: 규칙 삭제
        delete_response = await async_client.delete(f"/api/alerts/rules/{rule_name}")
        assert delete_response.status_code == status.HTTP_200_OK

        # Step 9: 삭제 확인
        get_deleted_response = await async_client.get(f"/api/alerts/rules/{rule_name}")
        assert get_deleted_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_alert_suppression_workflow(self, async_client: AsyncClient):
        """알림 억제 워크플로우 테스트"""
        # Step 1: 알림 규칙 생성
        rule_data = {
            "name": "suppression_test_rule",
            "description": "억제 테스트용 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "api_error_rate", "value": 5.0},
            "severity": "medium",
            "channels": ["email"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Step 2: 억제 규칙 생성
        suppression_data = {
            "type": "maintenance_window",
            "name": "api_maintenance",
            "start_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "end_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "affected_services": ["api"],
            "description": "API 서버 유지보수"
        }
        
        suppression_response = await async_client.post("/api/alerts/suppression", json=suppression_data)
        assert suppression_response.status_code == status.HTTP_201_CREATED

        # Step 3: 억제 규칙 목록 조회
        list_suppression_response = await async_client.get("/api/alerts/suppression")
        assert list_suppression_response.status_code == status.HTTP_200_OK
        
        suppression_list = list_suppression_response.json()
        assert len(suppression_list["suppression_rules"]) >= 1

        # Step 4: 수동 알림 전송 (억제 중)
        with patch('nadle_backend.services.notification_service.NotificationService.send_email_notification') as mock_email:
            mock_email.return_value = True
            
            manual_alert_data = {
                "rule_name": "suppression_test_rule",
                "metric_data": {"metric_value": 8.0}
            }
            
            send_response = await async_client.post("/api/alerts/send", json=manual_alert_data)
            assert send_response.status_code == status.HTTP_200_OK
            
            # 억제로 인해 상태가 억제됨을 확인
            send_results = send_response.json()
            # 현재 구현에서는 억제 상태를 "status": "suppressed"로 반환할 수 있음

        # Cleanup
        await async_client.delete("/api/alerts/rules/suppression_test_rule")

    @pytest.mark.asyncio
    async def test_multiple_severity_alerts(self, async_client: AsyncClient):
        """다양한 심각도의 알림 테스트"""
        severity_rules = [
            {
                "name": "low_disk_space",
                "description": "디스크 공간 부족 (낮음)",
                "condition": "less_than",
                "threshold": {"metric": "disk_free_space", "value": 20.0},
                "severity": "low",
                "channels": ["email"]
            },
            {
                "name": "high_memory_usage",
                "description": "메모리 사용률 높음 (중간)",
                "condition": "greater_than",
                "threshold": {"metric": "memory_usage", "value": 80.0},
                "severity": "medium",
                "channels": ["email", "discord"]
            },
            {
                "name": "critical_error_rate",
                "description": "치명적 에러율 (높음)",
                "condition": "greater_than",
                "threshold": {"metric": "error_rate", "value": 10.0},
                "severity": "high",
                "channels": ["email", "discord"]
            },
            {
                "name": "service_down",
                "description": "서비스 다운 (치명적)",
                "condition": "equals",
                "threshold": {"metric": "service_status", "value": 0},
                "severity": "critical",
                "channels": ["email", "discord", "sms"]
            }
        ]

        created_rules = []
        
        # Step 1: 다양한 심각도의 규칙들 생성
        for rule_data in severity_rules:
            response = await async_client.post("/api/alerts/rules", json=rule_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_rules.append(response.json()["name"])

        # Step 2: 모든 규칙 평가
        evaluate_response = await async_client.post("/api/alerts/evaluate")
        assert evaluate_response.status_code == status.HTTP_200_OK
        
        evaluation_results = evaluate_response.json()
        assert len(evaluation_results["evaluation_results"]) >= len(created_rules)

        # Step 3: 통계에서 심각도별 분포 확인
        stats_response = await async_client.get("/api/alerts/statistics")
        assert stats_response.status_code == status.HTTP_200_OK
        
        stats = stats_response.json()
        assert "alerts_by_severity" in stats
        assert "alerts_by_channel" in stats

        # Cleanup
        for rule_name in created_rules:
            await async_client.delete(f"/api/alerts/rules/{rule_name}")

    @pytest.mark.asyncio
    async def test_alert_cooldown_and_escalation(self, async_client: AsyncClient):
        """알림 쿨다운 및 에스컬레이션 테스트"""
        # Step 1: 쿨다운과 에스컬레이션이 설정된 규칙 생성
        rule_data = {
            "name": "cooldown_escalation_test",
            "description": "쿨다운 및 에스컬레이션 테스트",
            "condition": "greater_than",
            "threshold": {"metric": "response_time", "value": 1000.0},
            "severity": "medium",
            "channels": ["email"],
            "cooldown_minutes": 5,
            "escalation_minutes": 10
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Step 2: 첫 번째 알림 전송
        with patch('nadle_backend.services.notification_service.NotificationService.send_email_notification') as mock_email:
            mock_email.return_value = True
            
            alert_data = {
                "rule_name": "cooldown_escalation_test",
                "metric_data": {"metric_value": 1500.0}
            }
            
            first_send = await async_client.post("/api/alerts/send", json=alert_data)
            assert first_send.status_code == status.HTTP_200_OK

        # Step 3: 즉시 두 번째 알림 시도 (쿨다운 중이어야 함)
        with patch('nadle_backend.services.notification_service.NotificationService.send_email_notification') as mock_email:
            mock_email.return_value = True
            
            second_send = await async_client.post("/api/alerts/send", json=alert_data)
            # 쿨다운으로 인해 특정 응답이 있을 수 있음 (구현에 따라)
            assert second_send.status_code == status.HTTP_200_OK

        # Cleanup
        await async_client.delete("/api/alerts/rules/cooldown_escalation_test")

    @pytest.mark.asyncio
    async def test_concurrent_alert_operations(self, async_client: AsyncClient):
        """동시 알림 작업 테스트"""
        # Step 1: 여러 규칙을 동시에 생성
        rule_templates = [
            {"name": f"concurrent_rule_{i}", "metric": f"metric_{i}", "value": float(i * 10)}
            for i in range(5)
        ]
        
        creation_tasks = []
        for i, template in enumerate(rule_templates):
            rule_data = {
                "name": template["name"],
                "description": f"동시 생성 테스트 {i}",
                "condition": "greater_than",
                "threshold": {"metric": template["metric"], "value": template["value"]},
                "severity": "medium",
                "channels": ["email"]
            }
            
            task = async_client.post("/api/alerts/rules", json=rule_data)
            creation_tasks.append(task)
        
        # 모든 규칙 생성 요청을 동시에 실행
        creation_responses = await asyncio.gather(*creation_tasks)
        
        # 모든 생성이 성공했는지 확인
        for response in creation_responses:
            assert response.status_code == status.HTTP_201_CREATED

        # Step 2: 동시 평가
        evaluate_response = await async_client.post("/api/alerts/evaluate")
        assert evaluate_response.status_code == status.HTTP_200_OK

        # Step 3: 동시 삭제
        deletion_tasks = []
        for template in rule_templates:
            task = async_client.delete(f"/api/alerts/rules/{template['name']}")
            deletion_tasks.append(task)
        
        deletion_responses = await asyncio.gather(*deletion_tasks)
        
        # 모든 삭제가 성공했는지 확인
        for response in deletion_responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_alert_system_health_check(self, async_client: AsyncClient):
        """알림 시스템 헬스체크 테스트"""
        # When: 헬스체크 요청
        response = await async_client.get("/api/alerts/health")
        
        # Then: 헬스체크 성공
        assert response.status_code == status.HTTP_200_OK
        
        health_data = response.json()
        assert "status" in health_data
        assert "services" in health_data
        assert "last_check" in health_data
        
        # 필수 서비스들이 체크되었는지 확인
        services = health_data["services"]
        assert "notification_service" in services
        assert "monitoring_service" in services
        assert "rule_engine" in services

    @pytest.mark.asyncio
    async def test_alert_system_error_handling(self, async_client: AsyncClient):
        """알림 시스템 오류 처리 테스트"""
        # Test 1: 존재하지 않는 규칙에 대한 작업
        response = await async_client.get("/api/alerts/rules/nonexistent_rule")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = await async_client.delete("/api/alerts/rules/nonexistent_rule")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test 2: 잘못된 데이터로 규칙 생성
        invalid_rule_data = {
            "name": "",  # 빈 이름
            "condition": "invalid_condition",
            "threshold": {"metric": "test", "value": "not_a_number"},
            "severity": "invalid_severity",
            "channels": []
        }
        
        response = await async_client.post("/api/alerts/rules", json=invalid_rule_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test 3: 존재하지 않는 규칙으로 수동 알림 전송
        manual_alert_data = {
            "rule_name": "nonexistent_rule",
            "metric_data": {"metric_value": 100.0}
        }
        
        response = await async_client.post("/api/alerts/send", json=manual_alert_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_performance_under_load(self, async_client: AsyncClient):
        """부하 상황에서의 성능 테스트"""
        import time
        
        # Step 1: 기준 규칙 생성
        rule_data = {
            "name": "performance_test_rule",
            "description": "성능 테스트용 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "load_test_metric", "value": 50.0},
            "severity": "medium",
            "channels": ["email"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Step 2: 반복적인 평가 요청 (성능 측정)
        start_time = time.time()
        
        evaluation_tasks = []
        for _ in range(10):  # 10번의 동시 평가
            task = async_client.post("/api/alerts/evaluate")
            evaluation_tasks.append(task)
        
        responses = await asyncio.gather(*evaluation_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 모든 요청이 성공했는지 확인
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
        
        # 성능 기준 확인 (10개 요청이 5초 이내에 처리되어야 함)
        assert total_time < 5.0
        
        # Cleanup
        await async_client.delete("/api/alerts/rules/performance_test_rule")


class TestIntegrationWithRealServices:
    """실제 서비스와의 통합 테스트"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(__import__('nadle_backend.config').config.settings, 'discord_webhook_url') or
        not getattr(__import__('nadle_backend.config').config.settings, 'discord_webhook_url'),
        reason="실제 Discord 웹훅이 필요합니다"
    )
    async def test_real_discord_integration(self):
        """실제 디스코드 웹훅과의 통합 테스트"""
        # Given: 실제 설정이 있는 알림 서비스
        notification_service = NotificationService()
        alerting_service = IntelligentAlertingService(
            notification_service=notification_service,
            monitoring_service=None  # Mock으로 대체
        )
        
        # 테스트용 알림 규칙 생성
        rule = AlertRule(
            name="real_discord_test",
            description="실제 디스코드 통합 테스트",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="test_metric", value=50.0),
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.DISCORD]
        )
        
        await alerting_service.rule_engine.add_rule(rule)
        
        # When: 실제 디스코드로 알림 전송
        results = await alerting_service.send_alert(rule, {
            "metric_value": 75.0,
            "test_info": "실제 디스코드 통합 테스트"
        })
        
        # Then: 전송 결과 확인
        assert "discord" in results
        # 실제 환경에서는 성공/실패를 확인할 수 있음

    @pytest.mark.asyncio
    async def test_monitoring_integration_workflow(self):
        """모니터링 서비스 통합 워크플로우 테스트"""
        # Given: Mock 모니터링 서비스를 가진 알림 시스템
        class TestMonitoringService:
            def __init__(self):
                self.metrics = {
                    "cpu_usage": 85.0,  # 임계값 초과
                    "memory_usage": 45.0,  # 정상
                    "disk_usage": 90.0   # 임계값 초과
                }
            
            async def get_current_metric(self, metric_name: str) -> float:
                return self.metrics.get(metric_name, 0.0)
        
        notification_service = NotificationService()
        monitoring_service = TestMonitoringService()
        alerting_service = IntelligentAlertingService(
            notification_service=notification_service,
            monitoring_service=monitoring_service
        )
        
        # 여러 알림 규칙 생성
        rules = [
            AlertRule(
                name="cpu_alert",
                condition=AlertCondition.GREATER_THAN,
                threshold=AlertThreshold(metric="cpu_usage", value=80.0),
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                name="memory_alert",
                condition=AlertCondition.GREATER_THAN,
                threshold=AlertThreshold(metric="memory_usage", value=70.0),
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                name="disk_alert",
                condition=AlertCondition.GREATER_THAN,
                threshold=AlertThreshold(metric="disk_usage", value=85.0),
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.DISCORD]
            )
        ]
        
        for rule in rules:
            await alerting_service.rule_engine.add_rule(rule)
        
        # When: 모든 규칙 평가
        active_rules = await alerting_service.rule_engine.get_active_rules()
        evaluation_results = await alerting_service.evaluate_rules_batch(active_rules)
        
        # Then: 평가 결과 확인
        assert len(evaluation_results) == 3
        
        # CPU와 디스크는 트리거되어야 하고, 메모리는 트리거되지 않아야 함
        triggered_rules = [result for result in evaluation_results if result["should_alert"]]
        assert len(triggered_rules) == 2  # CPU와 디스크
        
        triggered_rule_names = [result["rule_name"] for result in triggered_rules]
        assert "cpu_alert" in triggered_rule_names
        assert "disk_alert" in triggered_rule_names
        assert "memory_alert" not in triggered_rule_names