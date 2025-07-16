"""
지능형 알림 시스템 서비스

알림 규칙 평가, 쿨다운, 에스컬레이션, 집계 등의 고급 알림 기능을 제공
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from collections import defaultdict

from nadle_backend.models.alerts import (
    AlertRule,
    AlertSeverity,
    AlertChannel,
    AlertThreshold,
    AlertCondition,
    AlertStatus,
    AlertEvent,
    AlertAggregation
)
from nadle_backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class AlertRuleEngine:
    """알림 규칙 엔진"""
    
    def __init__(self):
        """규칙 엔진 초기화"""
        self.rules: Dict[str, AlertRule] = {}  # rule_id -> AlertRule
        self.name_to_id: Dict[str, str] = {}   # rule_name -> rule_id
        logger.info("AlertRuleEngine 초기화 완료")
    
    async def add_rule(self, rule: AlertRule) -> None:
        """
        알림 규칙 추가
        
        Args:
            rule: 추가할 알림 규칙
        """
        self.rules[rule.id] = rule
        self.name_to_id[rule.name] = rule.id
        logger.info(f"알림 규칙 추가됨: {rule.name} (ID: {rule.id})")
    
    async def remove_rule(self, rule_id: str) -> bool:
        """
        알림 규칙 제거
        
        Args:
            rule_id: 제거할 규칙 ID
            
        Returns:
            제거 성공 여부
        """
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            del self.rules[rule_id]
            del self.name_to_id[rule.name]
            logger.info(f"알림 규칙 제거됨: {rule.name} (ID: {rule_id})")
            return True
        return False
    
    async def get_active_rules(self) -> List[AlertRule]:
        """
        활성화된 알림 규칙 목록 조회
        
        Returns:
            활성화된 규칙 목록
        """
        return [rule for rule in self.rules.values() if rule.enabled]
    
    async def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        특정 알림 규칙 조회 (ID 기반)
        
        Args:
            rule_id: 규칙 ID
            
        Returns:
            알림 규칙 (없으면 None)
        """
        return self.rules.get(rule_id)
    
    async def get_rule_by_name(self, rule_name: str) -> Optional[AlertRule]:
        """
        특정 알림 규칙 조회 (이름 기반)
        
        Args:
            rule_name: 규칙 이름
            
        Returns:
            알림 규칙 (없으면 None)
        """
        rule_id = self.name_to_id.get(rule_name)
        if rule_id:
            return self.rules.get(rule_id)
        return None


class IntelligentAlertingService:
    """
    지능형 알림 서비스
    
    알림 규칙 평가, 쿨다운, 에스컬레이션, 집계 등을 관리합니다.
    """
    
    def __init__(self, notification_service: NotificationService, monitoring_service: Any = None):
        """
        지능형 알림 서비스 초기화
        
        Args:
            notification_service: 알림 서비스
            monitoring_service: 모니터링 서비스 (선택사항)
        """
        self.notification_service = notification_service
        self.monitoring_service = monitoring_service
        self.rule_engine = AlertRuleEngine()
        
        # 쿨다운 및 에스컬레이션 추적
        self.last_alert_times: Dict[str, datetime] = {}
        self.alert_history: List[AlertEvent] = []
        
        logger.info("IntelligentAlertingService 초기화 완료")
    
    async def evaluate_rule(self, rule: AlertRule) -> bool:
        """
        알림 규칙 평가
        
        Args:
            rule: 평가할 알림 규칙
            
        Returns:
            알림 트리거 여부
        """
        try:
            if not rule.enabled:
                return False
            
            # 모니터링 서비스에서 현재 메트릭 값 조회
            if self.monitoring_service:
                current_value = await self.monitoring_service.get_current_metric(rule.threshold.metric)
            else:
                # 테스트용 기본값
                current_value = 0.0
            
            # 조건 평가
            return await self.evaluate_condition(rule.condition, rule.threshold, current_value)
            
        except Exception as e:
            logger.error(f"알림 규칙 평가 실패 ({rule.name}): {e}")
            return False
    
    async def evaluate_condition(self, condition: AlertCondition, threshold: AlertThreshold, current_value: float) -> bool:
        """
        알림 조건 평가
        
        Args:
            condition: 알림 조건
            threshold: 임계값
            current_value: 현재 값
            
        Returns:
            조건 만족 여부
        """
        if condition == AlertCondition.GREATER_THAN:
            return current_value > threshold.value
        elif condition == AlertCondition.LESS_THAN:
            return current_value < threshold.value
        elif condition == AlertCondition.EQUALS:
            return abs(current_value - threshold.value) < 0.001  # 부동소수점 비교
        else:
            return False
    
    async def evaluate_rules_batch(self, rules: List[AlertRule]) -> List[Dict[str, Any]]:
        """
        여러 알림 규칙 배치 평가
        
        Args:
            rules: 평가할 규칙 목록
            
        Returns:
            평가 결과 목록
        """
        results = []
        
        for rule in rules:
            try:
                should_alert = await self.evaluate_rule(rule)
                results.append({
                    "rule_name": rule.name,
                    "triggered": should_alert,
                    "severity": rule.severity,
                    "timestamp": datetime.utcnow()
                })
            except Exception as e:
                logger.error(f"규칙 배치 평가 실패 ({rule.name}): {e}")
                results.append({
                    "rule_name": rule.name,
                    "triggered": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow()
                })
        
        return results
    
    async def can_send_alert(self, rule: AlertRule) -> bool:
        """
        알림 전송 가능 여부 확인 (쿨다운 체크)
        
        Args:
            rule: 알림 규칙
            
        Returns:
            전송 가능 여부
        """
        if not rule.cooldown_minutes:
            return True
        
        last_alert = self.last_alert_times.get(rule.name)
        if not last_alert:
            return True
        
        time_diff = datetime.utcnow() - last_alert
        cooldown_seconds = rule.cooldown_minutes * 60
        
        return time_diff.total_seconds() >= cooldown_seconds
    
    async def should_escalate(self, rule: AlertRule, alert_time: datetime) -> bool:
        """
        알림 에스컬레이션 필요 여부 확인
        
        Args:
            rule: 알림 규칙
            alert_time: 알림 발생 시간
            
        Returns:
            에스컬레이션 필요 여부
        """
        if not rule.escalation_minutes:
            return False
        
        time_diff = datetime.utcnow() - alert_time
        escalation_seconds = rule.escalation_minutes * 60
        
        return time_diff.total_seconds() >= escalation_seconds
    
    async def send_alert(self, rule: AlertRule, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        알림 전송
        
        Args:
            rule: 알림 규칙
            metric_data: 메트릭 데이터
            
        Returns:
            전송 결과
        """
        try:
            # 쿨다운 체크
            if not await self.can_send_alert(rule):
                logger.info(f"알림 쿨다운 중: {rule.name}")
                return {"sent": False, "reason": "cooldown"}
            
            # 알림 전송
            result = await self.route_notification(rule, metric_data)
            
            # 전송 시간 기록
            self.last_alert_times[rule.name] = datetime.utcnow()
            
            # 알림 이력 저장
            alert_event = AlertEvent(
                rule_name=rule.name,
                metric_name=rule.threshold.metric,
                current_value=metric_data.get(rule.threshold.metric, 0.0),
                threshold_value=rule.threshold.value,
                severity=rule.severity,
                status=AlertStatus.SENT if result.get("sent") else AlertStatus.FAILED,
                message=metric_data.get("message", "알림"),
                triggered_at=datetime.utcnow(),
                metadata=metric_data
            )
            self.alert_history.append(alert_event)
            
            return result
            
        except Exception as e:
            logger.error(f"알림 전송 실패 ({rule.name}): {e}")
            return {"sent": False, "error": str(e)}
    
    async def route_notification(self, rule: AlertRule, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        알림 라우팅 (채널별 전송)
        
        Args:
            rule: 알림 규칙
            alert_data: 알림 데이터
            
        Returns:
            채널별 전송 결과
        """
        results = {}
        message = alert_data.get("message", f"알림: {rule.name}")
        
        try:
            for channel in rule.channels:
                if channel == AlertChannel.EMAIL:
                    results["email"] = await self.notification_service.send_email_notification(
                        to_email=alert_data.get("email", "admin@example.com"),
                        subject=f"[{rule.severity.value.upper()}] {rule.name}",
                        message=message
                    )
                elif channel == AlertChannel.DISCORD:
                    color = self._get_severity_color(rule.severity)
                    results["discord"] = await self.notification_service.send_discord_notification(
                        message=message,
                        title=f"알림: {rule.name}",
                        color=color,
                        username="Alert Bot"
                    )
            
            results["sent"] = any(results.values())
            return results
            
        except Exception as e:
            logger.error(f"알림 라우팅 실패: {e}")
            return {"sent": False, "error": str(e)}
    
    def _get_severity_color(self, severity: AlertSeverity) -> int:
        """심각도에 따른 색상 반환"""
        color_map = {
            AlertSeverity.LOW: 0x00FF00,      # 녹색
            AlertSeverity.MEDIUM: 0xFFFF00,   # 노란색
            AlertSeverity.HIGH: 0xFF9900,     # 주황색
            AlertSeverity.CRITICAL: 0xFF0000  # 빨간색
        }
        return color_map.get(severity, 0x808080)  # 기본: 회색
    
    async def aggregate_alerts(self, alerts: List[Dict[str, Any]], time_window_minutes: int = 5) -> Dict[str, Any]:
        """
        알림 집계
        
        Args:
            alerts: 알림 목록
            time_window_minutes: 시간 윈도우 (분)
            
        Returns:
            집계된 알림 정보
        """
        try:
            severity_distribution = defaultdict(int)
            affected_services = set()
            
            for alert in alerts:
                severity = alert.get("severity", AlertSeverity.LOW)
                if isinstance(severity, AlertSeverity):
                    severity_distribution[severity.value] += 1
                else:
                    severity_distribution[str(severity)] += 1
                
                if "rule" in alert:
                    affected_services.add(alert["rule"])
            
            return {
                "total_alerts": len(alerts),
                "severity_distribution": dict(severity_distribution),
                "affected_services": list(affected_services),
                "time_window_minutes": time_window_minutes,
                "aggregated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"알림 집계 실패: {e}")
            return {"total_alerts": 0, "error": str(e)}
    
    async def sort_by_priority(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        알림 우선순위별 정렬
        
        Args:
            alerts: 정렬할 알림 목록
            
        Returns:
            우선순위별 정렬된 알림 목록
        """
        severity_order = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.HIGH: 3,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 1
        }
        
        def get_priority(alert):
            severity = alert.get("severity", AlertSeverity.LOW)
            return severity_order.get(severity, 0)
        
        return sorted(alerts, key=get_priority, reverse=True)
    
    async def get_alert_history(self, rule_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        알림 이력 조회
        
        Args:
            rule_name: 규칙 이름
            hours: 조회할 시간 범위 (시간)
            
        Returns:
            알림 이력 목록
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_history = [
            {
                "rule_name": event.rule_name,
                "metric_name": event.metric_name,
                "current_value": event.current_value,
                "threshold_value": event.threshold_value,
                "severity": event.severity.value,
                "status": event.status.value,
                "triggered_at": event.triggered_at.isoformat(),
                "message": event.message
            }
            for event in self.alert_history
            if event.rule_name == rule_name and event.triggered_at >= cutoff_time
        ]
        
        return filtered_history
    
    async def render_alert_message(self, template: str, data: Dict[str, Any]) -> str:
        """
        알림 메시지 템플릿 렌더링
        
        Args:
            template: 메시지 템플릿
            data: 템플릿 데이터
            
        Returns:
            렌더링된 메시지
        """
        try:
            return template.format(**data)
        except Exception as e:
            logger.error(f"메시지 템플릿 렌더링 실패: {e}")
            return template
    
    async def is_alert_suppressed(self, rule: AlertRule, suppression_rule: Dict[str, Any]) -> bool:
        """
        알림 억제 여부 확인
        
        Args:
            rule: 알림 규칙
            suppression_rule: 억제 규칙
            
        Returns:
            억제 여부
        """
        try:
            # 유지보수 창 체크
            if suppression_rule.get("type") == "maintenance_window":
                current_time = datetime.utcnow()
                start_time = suppression_rule.get("start_time")
                end_time = suppression_rule.get("end_time")
                affected_services = suppression_rule.get("affected_services", [])
                
                # 시간 체크
                in_time_window = False
                if start_time and end_time:
                    in_time_window = start_time <= current_time <= end_time
                
                # 서비스 매칭 체크 (규칙 이름에 서비스 이름이 포함되어 있는지)
                service_affected = False
                for service in affected_services:
                    if service in rule.name:
                        service_affected = True
                        break
                
                return in_time_window and (not affected_services or service_affected)
            
            # 간단한 패턴 매칭
            patterns = suppression_rule.get("rule_patterns", [])
            return rule.name in patterns
            
        except Exception as e:
            logger.error(f"알림 억제 확인 실패: {e}")
            return False


# 모델들을 다시 export (테스트 호환성)
__all__ = [
    "IntelligentAlertingService",
    "AlertRuleEngine", 
    "AlertRule",
    "AlertSeverity",
    "AlertChannel",
    "AlertThreshold",
    "AlertCondition",
    "AlertStatus"
]