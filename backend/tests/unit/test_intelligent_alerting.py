"""
지능형 알림 시스템 단위 테스트

알림 우선순위, 중복 방지, 알림 스케줄링 등 고급 알림 기능 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from nadle_backend.services.intelligent_alerting import (
    IntelligentAlertingService,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    AlertThreshold,
    AlertCondition,
    AlertStatus
)


class TestIntelligentAlertingService:
    """지능형 알림 시스템 서비스 단위 테스트"""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock 알림 서비스"""
        return Mock()

    @pytest.fixture
    def mock_monitoring_service(self):
        """Mock 모니터링 서비스"""
        return Mock()

    @pytest.fixture
    def alerting_service(self, mock_notification_service, mock_monitoring_service):
        """지능형 알림 서비스 인스턴스"""
        return IntelligentAlertingService(
            notification_service=mock_notification_service,
            monitoring_service=mock_monitoring_service
        )

    def test_alert_rule_creation(self):
        """알림 규칙 생성 테스트"""
        # Given: 알림 규칙 파라미터
        rule = AlertRule(
            name="high_error_rate",
            description="높은 에러율 감지",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(
                metric="error_rate",
                value=5.0,
                duration_minutes=5
            ),
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.DISCORD],
            cooldown_minutes=30
        )

        # Then: 알림 규칙 속성 확인
        assert rule.name == "high_error_rate"
        assert rule.condition == AlertCondition.GREATER_THAN
        assert rule.threshold.value == 5.0
        assert rule.severity == AlertSeverity.HIGH
        assert AlertChannel.EMAIL in rule.channels
        assert rule.cooldown_minutes == 30

    def test_alert_severity_enum(self):
        """알림 심각도 열거형 테스트"""
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_alert_channel_enum(self):
        """알림 채널 열거형 테스트"""
        assert AlertChannel.EMAIL.value == "email"
        assert AlertChannel.DISCORD.value == "discord"
        # SLACK과 SMS는 구현하지 않음

    @pytest.mark.asyncio
    async def test_evaluate_alert_rule_triggered(self, alerting_service, mock_monitoring_service):
        """알림 규칙 평가 - 트리거됨 테스트"""
        # Given: 높은 에러율 임계값을 초과하는 메트릭
        rule = AlertRule(
            name="error_rate_alert",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="error_rate", value=5.0),
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.DISCORD]
        )
        
        mock_monitoring_service.get_current_metric = AsyncMock(return_value=7.5)

        # When: 알림 규칙 평가
        should_alert = await alerting_service.evaluate_rule(rule)

        # Then: 알림이 트리거되어야 함
        assert should_alert is True
        mock_monitoring_service.get_current_metric.assert_called_with("error_rate")

    @pytest.mark.asyncio
    async def test_evaluate_alert_rule_not_triggered(self, alerting_service, mock_monitoring_service):
        """알림 규칙 평가 - 트리거되지 않음 테스트"""
        # Given: 임계값 미만의 메트릭
        rule = AlertRule(
            name="error_rate_alert",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="error_rate", value=5.0),
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.DISCORD]
        )
        
        mock_monitoring_service.get_current_metric = AsyncMock(return_value=2.3)

        # When: 알림 규칙 평가
        should_alert = await alerting_service.evaluate_rule(rule)

        # Then: 알림이 트리거되지 않아야 함
        assert should_alert is False

    @pytest.mark.asyncio
    async def test_alert_cooldown_prevention(self, alerting_service):
        """알림 쿨다운 중복 방지 테스트"""
        # Given: 쿨다운이 설정된 알림 규칙
        rule = AlertRule(
            name="cpu_alert",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="cpu_usage", value=80.0),
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.EMAIL],
            cooldown_minutes=30
        )

        # When: 첫 번째 알림 전송
        await alerting_service.send_alert(rule, {"cpu_usage": 85.0})
        
        # When: 쿨다운 기간 내 두 번째 알림 시도
        can_send = await alerting_service.can_send_alert(rule)

        # Then: 쿨다운으로 인해 알림 전송 불가
        assert can_send is False

    @pytest.mark.asyncio
    async def test_alert_aggregation(self, alerting_service):
        """알림 집계 테스트"""
        # Given: 여러 관련 알림들
        alerts = [
            {"rule": "high_response_time", "value": 1200, "timestamp": datetime.now()},
            {"rule": "high_error_rate", "value": 6.5, "timestamp": datetime.now()},
            {"rule": "low_availability", "value": 95.2, "timestamp": datetime.now()}
        ]

        # When: 알림 집계
        aggregated = await alerting_service.aggregate_alerts(alerts, time_window_minutes=5)

        # Then: 집계된 알림 정보
        assert "total_alerts" in aggregated
        assert "severity_distribution" in aggregated
        assert "affected_services" in aggregated
        assert aggregated["total_alerts"] == 3

    @pytest.mark.asyncio
    async def test_alert_priority_ordering(self, alerting_service):
        """알림 우선순위 정렬 테스트"""
        # Given: 다양한 심각도의 알림들
        alerts = [
            {"severity": AlertSeverity.LOW, "timestamp": datetime.now()},
            {"severity": AlertSeverity.CRITICAL, "timestamp": datetime.now()},
            {"severity": AlertSeverity.MEDIUM, "timestamp": datetime.now()},
            {"severity": AlertSeverity.HIGH, "timestamp": datetime.now()}
        ]

        # When: 우선순위별 정렬
        sorted_alerts = await alerting_service.sort_by_priority(alerts)

        # Then: 심각도 순으로 정렬됨 (CRITICAL -> HIGH -> MEDIUM -> LOW)
        assert sorted_alerts[0]["severity"] == AlertSeverity.CRITICAL
        assert sorted_alerts[1]["severity"] == AlertSeverity.HIGH
        assert sorted_alerts[2]["severity"] == AlertSeverity.MEDIUM
        assert sorted_alerts[3]["severity"] == AlertSeverity.LOW

    @pytest.mark.asyncio
    async def test_smart_notification_routing(self, alerting_service, mock_notification_service):
        """스마트 알림 라우팅 테스트"""
        # Given: 심각도별 채널 설정
        critical_rule = AlertRule(
            name="critical_alert",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="error_rate", value=5.0),
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannel.EMAIL, AlertChannel.DISCORD]
        )
        
        low_rule = AlertRule(
            name="low_alert",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="response_time", value=1000.0),
            severity=AlertSeverity.LOW,
            channels=[AlertChannel.EMAIL]
        )

        mock_notification_service.send_email_notification = AsyncMock(return_value=True)
        mock_notification_service.send_discord_notification = AsyncMock(return_value=True)

        # When: 중요 알림 전송
        await alerting_service.route_notification(critical_rule, {"message": "Critical issue"})

        # Then: 모든 채널로 전송됨
        mock_notification_service.send_email_notification.assert_called_once()
        mock_notification_service.send_discord_notification.assert_called_once()
        
        # When: 낮은 심각도 알림 전송
        mock_notification_service.reset_mock()
        await alerting_service.route_notification(low_rule, {"message": "Minor issue"})

        # Then: 이메일만 전송됨
        mock_notification_service.send_email_notification.assert_called_once()
        mock_notification_service.send_discord_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_alert_escalation(self, alerting_service):
        """알림 에스컬레이션 테스트"""
        # Given: 에스컬레이션 규칙
        rule = AlertRule(
            name="escalation_test",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="cpu_usage", value=80.0),
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.EMAIL],
            escalation_minutes=15
        )

        # When: 15분 후 에스컬레이션 체크
        alert_time = datetime.utcnow() - timedelta(minutes=20)
        should_escalate = await alerting_service.should_escalate(rule, alert_time)

        # Then: 에스컬레이션 필요
        assert should_escalate is True

    @pytest.mark.asyncio
    async def test_alert_condition_evaluation(self, alerting_service):
        """알림 조건 평가 테스트"""
        # Given: 다양한 조건들
        conditions = [
            (AlertCondition.GREATER_THAN, 10.0, 15.0, True),
            (AlertCondition.GREATER_THAN, 10.0, 5.0, False),
            (AlertCondition.LESS_THAN, 50.0, 30.0, True),
            (AlertCondition.LESS_THAN, 50.0, 70.0, False),
            (AlertCondition.EQUALS, 100.0, 100.0, True),
            (AlertCondition.EQUALS, 100.0, 99.0, False),
        ]

        for condition, threshold_value, current_value, expected in conditions:
            # Given: AlertThreshold 객체 생성
            threshold = AlertThreshold(metric="test_metric", value=threshold_value)
            
            # When: 조건 평가
            result = await alerting_service.evaluate_condition(condition, threshold, current_value)
            
            # Then: 예상된 결과
            assert result == expected, f"Failed for {condition} {threshold} vs {current_value}"

    @pytest.mark.asyncio
    async def test_alert_history_tracking(self, alerting_service, mock_notification_service):
        """알림 이력 추적 테스트"""
        # Given: 알림 규칙과 Mock 알림 서비스
        rule = AlertRule(
            name="test_rule", 
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="test_metric", value=70.0),
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.EMAIL]
        )

        # Mock 알림 서비스 설정
        mock_notification_service.send_email_notification = AsyncMock(return_value=True)

        # When: 알림 전송
        await alerting_service.send_alert(rule, {"test_metric": 75.0})

        # Then: 이력에 기록됨
        history = await alerting_service.get_alert_history(rule.name, hours=1)
        assert len(history) == 1
        assert history[0]["rule_name"] == "test_rule"
        assert history[0]["status"] == AlertStatus.SENT.value

    @pytest.mark.asyncio
    async def test_alert_template_rendering(self, alerting_service):
        """알림 템플릿 렌더링 테스트"""
        # Given: 알림 템플릿과 데이터
        template = "🚨 {severity} Alert: {metric} is {value} (threshold: {threshold})"
        data = {
            "severity": "HIGH",
            "metric": "CPU Usage",
            "value": "85%",
            "threshold": "80%"
        }

        # When: 템플릿 렌더링
        rendered = await alerting_service.render_alert_message(template, data)

        # Then: 올바르게 렌더링됨
        expected = "🚨 HIGH Alert: CPU Usage is 85% (threshold: 80%)"
        assert rendered == expected

    @pytest.mark.asyncio
    async def test_alert_batch_processing(self, alerting_service):
        """알림 배치 처리 테스트"""
        # Given: 여러 알림 규칙들
        rules = [
            AlertRule(
                name=f"rule_{i}", 
                condition=AlertCondition.GREATER_THAN,
                threshold=AlertThreshold(metric=f"metric_{i}", value=50.0),
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL]
            )
            for i in range(5)
        ]

        # When: 배치로 알림 규칙 평가
        results = await alerting_service.evaluate_rules_batch(rules)

        # Then: 모든 규칙이 평가됨
        assert len(results) == 5
        assert all("rule_name" in result for result in results)
        assert all("triggered" in result for result in results)

    @pytest.mark.asyncio
    async def test_alert_suppression(self, alerting_service):
        """알림 억제 테스트"""
        # Given: 억제 규칙
        suppression_rule = {
            "type": "maintenance_window",
            "start_time": datetime.utcnow() - timedelta(hours=1),
            "end_time": datetime.utcnow() + timedelta(hours=1),
            "affected_services": ["api", "database"]
        }

        rule = AlertRule(
            name="api_alert", 
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="response_time", value=1000.0),
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL]
        )

        # When: 유지보수 시간 중 알림 억제 확인
        is_suppressed = await alerting_service.is_alert_suppressed(rule, suppression_rule)

        # Then: 알림이 억제됨
        assert is_suppressed is True


class TestAlertRuleEngine:
    """알림 규칙 엔진 테스트"""

    @pytest.fixture
    def rule_engine(self):
        """알림 규칙 엔진 인스턴스"""
        from nadle_backend.services.intelligent_alerting import AlertRuleEngine
        return AlertRuleEngine()

    def test_rule_engine_initialization(self, rule_engine):
        """규칙 엔진 초기화 테스트"""
        assert rule_engine is not None
        assert hasattr(rule_engine, 'rules')
        assert isinstance(rule_engine.rules, dict)

    @pytest.mark.asyncio
    async def test_add_rule(self, rule_engine):
        """규칙 추가 테스트"""
        # Given: 새로운 알림 규칙
        rule = AlertRule(
            name="test_rule",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="cpu_usage", value=80.0),
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.EMAIL]
        )

        # When: 규칙 추가
        await rule_engine.add_rule(rule)

        # Then: 규칙이 추가됨
        assert "test_rule" in rule_engine.rules
        assert rule_engine.rules["test_rule"] == rule

    @pytest.mark.asyncio
    async def test_remove_rule(self, rule_engine):
        """규칙 제거 테스트"""
        # Given: 기존 규칙
        rule = AlertRule(
            name="temp_rule", 
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="memory_usage", value=85.0),
            severity=AlertSeverity.LOW,
            channels=[AlertChannel.EMAIL]
        )
        await rule_engine.add_rule(rule)

        # When: 규칙 제거
        removed = await rule_engine.remove_rule("temp_rule")

        # Then: 규칙이 제거됨
        assert removed is True
        assert "temp_rule" not in rule_engine.rules

    @pytest.mark.asyncio
    async def test_get_active_rules(self, rule_engine):
        """활성 규칙 조회 테스트"""
        # Given: 활성/비활성 규칙들
        active_rule = AlertRule(
            name="active", 
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="cpu_usage", value=80.0),
            severity=AlertSeverity.HIGH, 
            channels=[AlertChannel.EMAIL],
            enabled=True
        )
        inactive_rule = AlertRule(
            name="inactive", 
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(metric="memory_usage", value=90.0),
            severity=AlertSeverity.LOW, 
            channels=[AlertChannel.EMAIL],
            enabled=False
        )
        
        await rule_engine.add_rule(active_rule)
        await rule_engine.add_rule(inactive_rule)

        # When: 활성 규칙 조회
        active_rules = await rule_engine.get_active_rules()

        # Then: 활성 규칙만 반환됨
        assert len(active_rules) == 1
        assert active_rules[0].name == "active"