"""
지능형 알림 시스템

알림 우선순위, 중복 방지, 알림 스케줄링, 에스컬레이션 등 고급 알림 기능
"""
import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """알림 심각도"""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def priority_order(self) -> int:
        """우선순위 순서 (낮을수록 높은 우선순위)"""
        return {
            self.CRITICAL: 0,
            self.HIGH: 1,
            self.MEDIUM: 2,
            self.LOW: 3
        }[self]


class AlertChannel(Enum):
    """알림 채널"""
    EMAIL = "email"
    DISCORD = "discord"
    SLACK = "slack"
    SMS = "sms"


class AlertCondition(Enum):
    """알림 조건"""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    BETWEEN = "between"
    OUTSIDE = "outside"


class AlertStatus(Enum):
    """알림 상태"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SUPPRESSED = "suppressed"
    ESCALATED = "escalated"


@dataclass
class AlertThreshold:
    """알림 임계값"""
    metric: str
    value: Union[float, int]
    duration_minutes: int = 0
    comparison_operator: Optional[str] = None


@dataclass
class AlertRule:
    """알림 규칙"""
    name: str
    description: str = ""
    condition: AlertCondition = AlertCondition.GREATER_THAN
    threshold: Optional[AlertThreshold] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    channels: List[AlertChannel] = field(default_factory=list)
    cooldown_minutes: int = 30
    escalation_minutes: Optional[int] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    
    def __post_init__(self):
        """객체 생성 후 검증"""
        if not self.channels:
            self.channels = [AlertChannel.EMAIL]


@dataclass
class AlertHistory:
    """알림 이력"""
    rule_name: str
    status: AlertStatus
    message: str
    channels_sent: List[AlertChannel]
    timestamp: datetime = field(default_factory=datetime.now)
    metric_value: Optional[float] = None
    error_message: Optional[str] = None


class AlertRuleEngine:
    """알림 규칙 엔진"""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[AlertHistory] = []
        self.last_alerts: Dict[str, datetime] = {}  # 쿨다운 추적
    
    async def add_rule(self, rule: AlertRule) -> bool:
        """규칙 추가"""
        try:
            self.rules[rule.name] = rule
            logger.info(f"알림 규칙 추가됨: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"알림 규칙 추가 실패: {e}")
            return False
    
    async def remove_rule(self, rule_name: str) -> bool:
        """규칙 제거"""
        try:
            if rule_name in self.rules:
                del self.rules[rule_name]
                logger.info(f"알림 규칙 제거됨: {rule_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"알림 규칙 제거 실패: {e}")
            return False
    
    async def get_active_rules(self) -> List[AlertRule]:
        """활성 규칙 조회"""
        return [rule for rule in self.rules.values() if rule.enabled]
    
    async def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """특정 규칙 조회"""
        return self.rules.get(rule_name)


class IntelligentAlertingService:
    """지능형 알림 서비스"""
    
    def __init__(self, notification_service=None, monitoring_service=None):
        self.notification_service = notification_service
        self.monitoring_service = monitoring_service
        self.rule_engine = AlertRuleEngine()
        self.suppression_rules: List[Dict[str, Any]] = []
        
    async def evaluate_rule(self, rule: AlertRule) -> bool:
        """알림 규칙 평가"""
        try:
            if not rule.threshold:
                return False
                
            # 모니터링 서비스에서 현재 메트릭 값 가져오기
            current_value = await self.monitoring_service.get_current_metric(rule.threshold.metric)
            
            # 조건 평가
            return await self.evaluate_condition(
                rule.condition, 
                rule.threshold.value, 
                current_value
            )
        except Exception as e:
            logger.error(f"알림 규칙 평가 실패: {e}")
            return False
    
    async def evaluate_condition(self, condition: AlertCondition, threshold: float, current_value: float) -> bool:
        """조건 평가"""
        if condition == AlertCondition.GREATER_THAN:
            return current_value > threshold
        elif condition == AlertCondition.LESS_THAN:
            return current_value < threshold
        elif condition == AlertCondition.EQUALS:
            return current_value == threshold
        elif condition == AlertCondition.NOT_EQUALS:
            return current_value != threshold
        else:
            return False
    
    async def can_send_alert(self, rule: AlertRule) -> bool:
        """알림 전송 가능 여부 확인 (쿨다운 체크)"""
        if rule.name not in self.rule_engine.last_alerts:
            return True
            
        last_alert_time = self.rule_engine.last_alerts[rule.name]
        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now() - last_alert_time > cooldown_period
    
    async def send_alert(self, rule: AlertRule, metric_data: Dict[str, Any]) -> Dict[str, bool]:
        """알림 전송"""
        results = {}
        
        # 쿨다운 체크
        if not await self.can_send_alert(rule):
            logger.info(f"알림 쿨다운 중: {rule.name}")
            return {"status": "cooldown"}
        
        # 억제 규칙 체크
        for suppression_rule in self.suppression_rules:
            if await self.is_alert_suppressed(rule, suppression_rule):
                logger.info(f"알림 억제됨: {rule.name}")
                return {"status": "suppressed"}
        
        # 알림 메시지 생성
        message = await self.generate_alert_message(rule, metric_data)
        
        # 채널별 알림 전송
        for channel in rule.channels:
            try:
                success = await self.send_to_channel(channel, message, rule)
                results[channel.value] = success
            except Exception as e:
                logger.error(f"채널 {channel.value} 알림 전송 실패: {e}")
                results[channel.value] = False
        
        # 마지막 알림 시간 기록
        self.rule_engine.last_alerts[rule.name] = datetime.now()
        
        # 이력 기록
        await self.record_alert_history(rule, message, list(rule.channels), AlertStatus.SENT)
        
        return results
    
    async def send_to_channel(self, channel: AlertChannel, message: str, rule: AlertRule) -> bool:
        """특정 채널로 알림 전송"""
        try:
            if channel == AlertChannel.EMAIL:
                return await self.notification_service.send_email_notification(
                    to_email="admin@example.com",  # 실제로는 설정에서 가져옴
                    subject=f"[{rule.severity.value.upper()}] {rule.name}",
                    message=message
                )
            elif channel == AlertChannel.DISCORD:
                color = self._get_severity_color(rule.severity)
                return await self.notification_service.send_discord_notification(
                    message=message,
                    title=f"{rule.severity.value.upper()} Alert",
                    color=color,
                    username="Alert System"
                )
            elif channel == AlertChannel.SMS:
                return await self.notification_service.send_sms_notification(
                    phone="+821012345678",  # 실제로는 설정에서 가져옴
                    message=message
                )
            else:
                logger.warning(f"지원되지 않는 채널: {channel}")
                return False
        except Exception as e:
            logger.error(f"채널 {channel.value} 전송 실패: {e}")
            return False
    
    def _get_severity_color(self, severity: AlertSeverity) -> int:
        """심각도별 색상"""
        colors = {
            AlertSeverity.LOW: 0x00FF00,       # 녹색
            AlertSeverity.MEDIUM: 0xFFA500,    # 주황색
            AlertSeverity.HIGH: 0xFF0000,      # 빨간색
            AlertSeverity.CRITICAL: 0x8B0000   # 진한 빨간색
        }
        return colors.get(severity, 0x808080)  # 기본 회색
    
    async def generate_alert_message(self, rule: AlertRule, metric_data: Dict[str, Any]) -> str:
        """알림 메시지 생성"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"🚨 [{rule.severity.value.upper()}] {rule.name}\n\n"
        message += f"상세: {rule.description}\n"
        
        if rule.threshold:
            message += f"메트릭: {rule.threshold.metric}\n"
            if "metric_value" in metric_data:
                message += f"현재 값: {metric_data['metric_value']}\n"
                message += f"임계값: {rule.threshold.value}\n"
        
        message += f"감지 시간: {timestamp}"
        
        return message
    
    async def route_notification(self, rule: AlertRule, alert_data: Dict[str, Any]) -> Dict[str, bool]:
        """스마트 알림 라우팅"""
        results = {}
        
        for channel in rule.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    success = await self.notification_service.send_email_notification(
                        to_email="admin@example.com",
                        subject=f"[ALERT] {rule.name}",
                        message=alert_data.get("message", "")
                    )
                elif channel == AlertChannel.DISCORD:
                    success = await self.notification_service.send_discord_notification(
                        message=alert_data.get("message", ""),
                        title="Alert Notification"
                    )
                elif channel == AlertChannel.SMS:
                    success = await self.notification_service.send_sms_notification(
                        phone="+821012345678",
                        message=alert_data.get("message", "")
                    )
                else:
                    success = False
                
                results[channel.value] = success
            except Exception as e:
                logger.error(f"라우팅 실패 {channel.value}: {e}")
                results[channel.value] = False
        
        return results
    
    async def aggregate_alerts(self, alerts: List[Dict[str, Any]], time_window_minutes: int = 5) -> Dict[str, Any]:
        """알림 집계"""
        aggregated = {
            "total_alerts": len(alerts),
            "severity_distribution": defaultdict(int),
            "affected_services": set(),
            "time_window_minutes": time_window_minutes
        }
        
        for alert in alerts:
            # 심각도 분포
            if "severity" in alert:
                severity = alert["severity"]
                if isinstance(severity, AlertSeverity):
                    aggregated["severity_distribution"][severity.value] += 1
            
            # 영향받는 서비스
            if "service" in alert:
                aggregated["affected_services"].add(alert["service"])
            
            # 규칙 이름에서 서비스 추출
            if "rule" in alert:
                service = alert["rule"].split("_")[0]  # 예: "api_error_rate" -> "api"
                aggregated["affected_services"].add(service)
        
        # set을 list로 변환
        aggregated["affected_services"] = list(aggregated["affected_services"])
        aggregated["severity_distribution"] = dict(aggregated["severity_distribution"])
        
        return aggregated
    
    async def sort_by_priority(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """우선순위별 알림 정렬"""
        def get_priority(alert):
            severity = alert.get("severity")
            if isinstance(severity, AlertSeverity):
                return severity.priority_order
            return 999  # 알 수 없는 심각도는 가장 낮은 우선순위
        
        return sorted(alerts, key=get_priority)
    
    async def should_escalate(self, rule: AlertRule, alert_time: datetime) -> bool:
        """에스컬레이션 필요 여부 확인"""
        if not rule.escalation_minutes:
            return False
        
        escalation_threshold = timedelta(minutes=rule.escalation_minutes)
        return datetime.now() - alert_time > escalation_threshold
    
    async def is_alert_suppressed(self, rule: AlertRule, suppression_rule: Dict[str, Any]) -> bool:
        """알림 억제 여부 확인"""
        try:
            # 유지보수 시간 체크
            if suppression_rule.get("type") == "maintenance_window":
                start_time = suppression_rule.get("start_time")
                end_time = suppression_rule.get("end_time")
                now = datetime.now()
                
                if start_time and end_time and start_time <= now <= end_time:
                    # 영향받는 서비스 체크
                    affected_services = suppression_rule.get("affected_services", [])
                    if not affected_services:  # 모든 서비스 영향
                        return True
                    
                    # 규칙 이름에서 서비스 추출하여 체크
                    for service in affected_services:
                        if service in rule.name.lower():
                            return True
            
            return False
        except Exception as e:
            logger.error(f"알림 억제 체크 실패: {e}")
            return False
    
    async def get_alert_history(self, rule_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """알림 이력 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = []
        for record in self.rule_engine.alert_history:
            if (record.rule_name == rule_name and 
                record.timestamp >= cutoff_time):
                history.append({
                    "rule_name": record.rule_name,
                    "status": record.status,
                    "message": record.message,
                    "timestamp": record.timestamp,
                    "channels_sent": [ch.value for ch in record.channels_sent],
                    "metric_value": record.metric_value
                })
        
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)
    
    async def record_alert_history(self, rule: AlertRule, message: str, channels: List[AlertChannel], 
                                 status: AlertStatus, metric_value: Optional[float] = None):
        """알림 이력 기록"""
        history_entry = AlertHistory(
            rule_name=rule.name,
            status=status,
            message=message,
            channels_sent=channels,
            metric_value=metric_value
        )
        self.rule_engine.alert_history.append(history_entry)
    
    async def render_alert_message(self, template: str, data: Dict[str, Any]) -> str:
        """알림 템플릿 렌더링"""
        try:
            return template.format(**data)
        except KeyError as e:
            logger.error(f"템플릿 렌더링 실패 - 누락된 키: {e}")
            return template
        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {e}")
            return template
    
    async def evaluate_rules_batch(self, rules: List[AlertRule]) -> List[Dict[str, Any]]:
        """배치로 알림 규칙 평가"""
        results = []
        
        # 병렬 처리를 위한 코루틴들
        tasks = []
        for rule in rules:
            task = asyncio.create_task(self._evaluate_single_rule(rule))
            tasks.append(task)
        
        # 모든 태스크 완료 대기
        evaluation_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리
        for rule, result in zip(rules, evaluation_results):
            if isinstance(result, Exception):
                results.append({
                    "rule_name": rule.name,
                    "should_alert": False,
                    "error": str(result)
                })
            else:
                results.append({
                    "rule_name": rule.name,
                    "should_alert": result,
                    "evaluated_at": datetime.now()
                })
        
        return results
    
    async def _evaluate_single_rule(self, rule: AlertRule) -> bool:
        """단일 규칙 평가 (내부 메서드)"""
        try:
            return await self.evaluate_rule(rule)
        except Exception as e:
            logger.error(f"규칙 {rule.name} 평가 실패: {e}")
            raise


# 의존성 주입을 위한 팩토리 함수들
def get_alert_rule_engine() -> AlertRuleEngine:
    """알림 규칙 엔진 인스턴스 반환"""
    return AlertRuleEngine()


def get_intelligent_alerting_service(notification_service=None, monitoring_service=None) -> IntelligentAlertingService:
    """지능형 알림 서비스 인스턴스 반환"""
    return IntelligentAlertingService(
        notification_service=notification_service,
        monitoring_service=monitoring_service
    )