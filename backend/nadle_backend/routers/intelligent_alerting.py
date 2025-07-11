"""
지능형 알림 시스템 API 라우터

알림 규칙 관리, 알림 전송, 알림 이력 조회 등의 API 엔드포인트를 제공합니다.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from nadle_backend.services.intelligent_alerting import (
    IntelligentAlertingService,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    AlertCondition,
    AlertThreshold,
    get_intelligent_alerting_service
)
from nadle_backend.services.notification_service import get_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["intelligent-alerting"])


# === Pydantic 모델 정의 ===

class AlertThresholdRequest(BaseModel):
    """알림 임계값 요청 모델"""
    metric: str = Field(..., description="메트릭 이름")
    value: float = Field(..., description="임계값")
    duration_minutes: int = Field(default=0, ge=0, description="지속 시간 (분)")


class AlertRuleRequest(BaseModel):
    """알림 규칙 생성/수정 요청 모델"""
    name: str = Field(..., min_length=1, max_length=100, description="규칙 이름")
    description: str = Field(default="", max_length=500, description="규칙 설명")
    condition: str = Field(..., description="알림 조건 (greater_than, less_than, equals 등)")
    threshold: AlertThresholdRequest = Field(..., description="알림 임계값")
    severity: str = Field(..., description="심각도 (low, medium, high, critical)")
    channels: List[str] = Field(..., min_items=1, description="알림 채널 목록")
    cooldown_minutes: int = Field(default=30, ge=0, description="쿨다운 시간 (분)")
    escalation_minutes: Optional[int] = Field(default=None, ge=0, description="에스컬레이션 시간 (분)")
    enabled: bool = Field(default=True, description="규칙 활성화 여부")


class AlertRuleResponse(BaseModel):
    """알림 규칙 응답 모델"""
    id: str = Field(..., description="규칙 ID")
    name: str = Field(..., description="규칙 이름")
    description: str = Field(..., description="규칙 설명")
    condition: str = Field(..., description="알림 조건")
    threshold: Dict[str, Any] = Field(..., description="알림 임계값")
    severity: str = Field(..., description="심각도")
    channels: List[str] = Field(..., description="알림 채널 목록")
    cooldown_minutes: int = Field(..., description="쿨다운 시간 (분)")
    escalation_minutes: Optional[int] = Field(default=None, description="에스컬레이션 시간 (분)")
    enabled: bool = Field(..., description="규칙 활성화 여부")
    created_at: datetime = Field(..., description="생성 시간")
    last_triggered: Optional[datetime] = Field(default=None, description="마지막 트리거 시간")


class AlertRuleListResponse(BaseModel):
    """알림 규칙 목록 응답 모델"""
    rules: List[AlertRuleResponse] = Field(..., description="알림 규칙 목록")
    total: int = Field(..., description="전체 규칙 수")


class ManualAlertRequest(BaseModel):
    """수동 알림 전송 요청 모델"""
    rule_name: str = Field(..., description="알림 규칙 이름")
    metric_data: Dict[str, Any] = Field(..., description="메트릭 데이터")


class AlertHistoryResponse(BaseModel):
    """알림 이력 응답 모델"""
    rule_name: str = Field(..., description="규칙 이름")
    history: List[Dict[str, Any]] = Field(..., description="알림 이력 목록")
    total: int = Field(..., description="전체 이력 수")


class AlertStatisticsResponse(BaseModel):
    """알림 통계 응답 모델"""
    total_rules: int = Field(..., description="전체 규칙 수")
    active_rules: int = Field(..., description="활성 규칙 수")
    alerts_sent_today: int = Field(..., description="오늘 전송된 알림 수")
    alerts_by_severity: Dict[str, int] = Field(..., description="심각도별 알림 수")
    alerts_by_channel: Dict[str, int] = Field(..., description="채널별 알림 수")


class SuppressionRuleRequest(BaseModel):
    """알림 억제 규칙 요청 모델"""
    type: str = Field(..., description="억제 타입 (maintenance_window 등)")
    name: str = Field(..., min_length=1, description="억제 규칙 이름")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: datetime = Field(..., description="종료 시간")
    affected_services: List[str] = Field(..., description="영향받는 서비스 목록")
    description: str = Field(default="", description="설명")


class HealthCheckResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str = Field(..., description="전체 상태")
    services: Dict[str, str] = Field(..., description="서비스별 상태")
    last_check: datetime = Field(..., description="마지막 체크 시간")


# === 의존성 함수들 ===

def get_alerting_service() -> IntelligentAlertingService:
    """지능형 알림 서비스 인스턴스 반환"""
    notification_service = get_notification_service()
    # Mock 모니터링 서비스 (실제 구현 시 교체)
    class MockMonitoringService:
        async def get_current_metric(self, metric_name: str) -> float:
            # Mock 데이터 반환
            mock_values = {
                "cpu_usage": 45.5,
                "memory_usage": 67.2,
                "disk_usage": 23.8,
                "network_latency": 120.0,
                "error_rate": 2.1
            }
            return mock_values.get(metric_name, 50.0)
    
    monitoring_service = MockMonitoringService()
    return get_intelligent_alerting_service(notification_service, monitoring_service)


# === API 엔드포인트들 ===

@router.post("/rules", status_code=status.HTTP_201_CREATED, response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_data: AlertRuleRequest,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleResponse:
    """
    새로운 알림 규칙을 생성합니다.
    
    Args:
        rule_data: 알림 규칙 생성 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        생성된 알림 규칙 정보
        
    Raises:
        HTTPException: 유효성 검사 실패 또는 중복된 규칙 이름
    """
    try:
        # 규칙 이름 중복 확인
        existing_rule = await alerting_service.rule_engine.get_rule(rule_data.name)
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"알림 규칙 '{rule_data.name}'이 이미 존재합니다"
            )
        
        # 열거형 값 검증
        try:
            condition = AlertCondition(rule_data.condition)
            severity = AlertSeverity(rule_data.severity)
            channels = [AlertChannel(ch) for ch in rule_data.channels]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"잘못된 열거형 값: {e}"
            )
        
        # AlertRule 객체 생성
        threshold = AlertThreshold(
            metric=rule_data.threshold.metric,
            value=rule_data.threshold.value,
            duration_minutes=rule_data.threshold.duration_minutes
        )
        
        alert_rule = AlertRule(
            name=rule_data.name,
            description=rule_data.description,
            condition=condition,
            threshold=threshold,
            severity=severity,
            channels=channels,
            cooldown_minutes=rule_data.cooldown_minutes,
            escalation_minutes=rule_data.escalation_minutes,
            enabled=rule_data.enabled
        )
        
        # 규칙 추가
        success = await alerting_service.rule_engine.add_rule(alert_rule)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 규칙 생성에 실패했습니다"
            )
        
        # 응답 데이터 생성
        return AlertRuleResponse(
            id=alert_rule.name,  # 임시로 name을 id로 사용
            name=alert_rule.name,
            description=alert_rule.description,
            condition=alert_rule.condition.value,
            threshold={
                "metric": alert_rule.threshold.metric,
                "value": alert_rule.threshold.value,
                "duration_minutes": alert_rule.threshold.duration_minutes
            },
            severity=alert_rule.severity.value,
            channels=[ch.value for ch in alert_rule.channels],
            cooldown_minutes=alert_rule.cooldown_minutes,
            escalation_minutes=alert_rule.escalation_minutes,
            enabled=alert_rule.enabled,
            created_at=alert_rule.created_at,
            last_triggered=alert_rule.last_triggered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 생성 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 생성 중 내부 오류가 발생했습니다"
        )


@router.get("/rules", response_model=AlertRuleListResponse)
async def get_alert_rules(
    active_only: bool = Query(False, description="활성 규칙만 조회"),
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleListResponse:
    """
    알림 규칙 목록을 조회합니다.
    
    Args:
        active_only: True인 경우 활성 규칙만 조회
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 규칙 목록
    """
    try:
        if active_only:
            rules = await alerting_service.rule_engine.get_active_rules()
        else:
            rules = list(alerting_service.rule_engine.rules.values())
        
        rule_responses = []
        for rule in rules:
            rule_responses.append(AlertRuleResponse(
                id=rule.name,
                name=rule.name,
                description=rule.description,
                condition=rule.condition.value,
                threshold={
                    "metric": rule.threshold.metric if rule.threshold else "",
                    "value": rule.threshold.value if rule.threshold else 0,
                    "duration_minutes": rule.threshold.duration_minutes if rule.threshold else 0
                },
                severity=rule.severity.value,
                channels=[ch.value for ch in rule.channels],
                cooldown_minutes=rule.cooldown_minutes,
                escalation_minutes=rule.escalation_minutes,
                enabled=rule.enabled,
                created_at=rule.created_at,
                last_triggered=rule.last_triggered
            ))
        
        return AlertRuleListResponse(
            rules=rule_responses,
            total=len(rule_responses)
        )
        
    except Exception as e:
        logger.error(f"알림 규칙 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/rules/{rule_name}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_name: str,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleResponse:
    """
    특정 알림 규칙을 조회합니다.
    
    Args:
        rule_name: 알림 규칙 이름
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 규칙 정보
        
    Raises:
        HTTPException: 규칙을 찾을 수 없는 경우
    """
    try:
        rule = await alerting_service.rule_engine.get_rule(rule_name)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙 '{rule_name}'을 찾을 수 없습니다"
            )
        
        return AlertRuleResponse(
            id=rule.name,
            name=rule.name,
            description=rule.description,
            condition=rule.condition.value,
            threshold={
                "metric": rule.threshold.metric if rule.threshold else "",
                "value": rule.threshold.value if rule.threshold else 0,
                "duration_minutes": rule.threshold.duration_minutes if rule.threshold else 0
            },
            severity=rule.severity.value,
            channels=[ch.value for ch in rule.channels],
            cooldown_minutes=rule.cooldown_minutes,
            escalation_minutes=rule.escalation_minutes,
            enabled=rule.enabled,
            created_at=rule.created_at,
            last_triggered=rule.last_triggered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 조회 중 오류가 발생했습니다"
        )


@router.put("/rules/{rule_name}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_name: str,
    rule_data: AlertRuleRequest,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleResponse:
    """
    알림 규칙을 수정합니다.
    
    Args:
        rule_name: 수정할 알림 규칙 이름
        rule_data: 수정할 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        수정된 알림 규칙 정보
        
    Raises:
        HTTPException: 규칙을 찾을 수 없는 경우
    """
    try:
        # 기존 규칙 확인
        existing_rule = await alerting_service.rule_engine.get_rule(rule_name)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙 '{rule_name}'을 찾을 수 없습니다"
            )
        
        # 열거형 값 검증
        try:
            condition = AlertCondition(rule_data.condition)
            severity = AlertSeverity(rule_data.severity)
            channels = [AlertChannel(ch) for ch in rule_data.channels]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"잘못된 열거형 값: {e}"
            )
        
        # 기존 규칙 삭제 후 새 규칙 추가
        await alerting_service.rule_engine.remove_rule(rule_name)
        
        # 새 규칙 생성 (이름은 유지하고 요청 데이터는 무시)
        threshold = AlertThreshold(
            metric=rule_data.threshold.metric,
            value=rule_data.threshold.value,
            duration_minutes=rule_data.threshold.duration_minutes
        )
        
        updated_rule = AlertRule(
            name=rule_name,  # 기존 이름 유지
            description=rule_data.description,
            condition=condition,
            threshold=threshold,
            severity=severity,
            channels=channels,
            cooldown_minutes=rule_data.cooldown_minutes,
            escalation_minutes=rule_data.escalation_minutes,
            enabled=rule_data.enabled,
            created_at=existing_rule.created_at,  # 기존 생성 시간 유지
            last_triggered=existing_rule.last_triggered  # 기존 트리거 시간 유지
        )
        
        # 수정된 규칙 추가
        success = await alerting_service.rule_engine.add_rule(updated_rule)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 규칙 수정에 실패했습니다"
            )
        
        return AlertRuleResponse(
            id=updated_rule.name,
            name=updated_rule.name,
            description=updated_rule.description,
            condition=updated_rule.condition.value,
            threshold={
                "metric": updated_rule.threshold.metric,
                "value": updated_rule.threshold.value,
                "duration_minutes": updated_rule.threshold.duration_minutes
            },
            severity=updated_rule.severity.value,
            channels=[ch.value for ch in updated_rule.channels],
            cooldown_minutes=updated_rule.cooldown_minutes,
            escalation_minutes=updated_rule.escalation_minutes,
            enabled=updated_rule.enabled,
            created_at=updated_rule.created_at,
            last_triggered=updated_rule.last_triggered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 수정 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 수정 중 오류가 발생했습니다"
        )


@router.delete("/rules/{rule_name}")
async def delete_alert_rule(
    rule_name: str,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, str]:
    """
    알림 규칙을 삭제합니다.
    
    Args:
        rule_name: 삭제할 알림 규칙 이름
        alerting_service: 지능형 알림 서비스
        
    Returns:
        삭제 성공 메시지
        
    Raises:
        HTTPException: 규칙을 찾을 수 없는 경우
    """
    try:
        # 규칙 존재 확인
        existing_rule = await alerting_service.rule_engine.get_rule(rule_name)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙 '{rule_name}'을 찾을 수 없습니다"
            )
        
        # 규칙 삭제
        success = await alerting_service.rule_engine.remove_rule(rule_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 규칙 삭제에 실패했습니다"
            )
        
        return {"message": f"알림 규칙 '{rule_name}'이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 삭제 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 삭제 중 오류가 발생했습니다"
        )


@router.post("/evaluate")
async def evaluate_alert_rules(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    모든 활성 알림 규칙을 평가합니다.
    
    Args:
        alerting_service: 지능형 알림 서비스
        
    Returns:
        평가 결과 목록
    """
    try:
        active_rules = await alerting_service.rule_engine.get_active_rules()
        
        if not active_rules:
            return {
                "evaluation_results": [],
                "message": "평가할 활성 규칙이 없습니다"
            }
        
        # 배치로 규칙 평가
        results = await alerting_service.evaluate_rules_batch(active_rules)
        
        return {
            "evaluation_results": results,
            "total_evaluated": len(results),
            "evaluated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"알림 규칙 평가 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 평가 중 오류가 발생했습니다"
        )


@router.post("/send")
async def send_manual_alert(
    alert_data: ManualAlertRequest,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    수동으로 알림을 전송합니다.
    
    Args:
        alert_data: 알림 전송 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 전송 결과
        
    Raises:
        HTTPException: 규칙을 찾을 수 없는 경우
    """
    try:
        # 규칙 확인
        rule = await alerting_service.rule_engine.get_rule(alert_data.rule_name)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙 '{alert_data.rule_name}'을 찾을 수 없습니다"
            )
        
        # 알림 전송
        results = await alerting_service.send_alert(rule, alert_data.metric_data)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수동 알림 전송 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수동 알림 전송 중 오류가 발생했습니다"
        )


@router.get("/history/{rule_name}", response_model=AlertHistoryResponse)
async def get_alert_history(
    rule_name: str,
    hours: int = Query(24, ge=1, le=720, description="조회할 시간 범위 (시간 단위)"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertHistoryResponse:
    """
    특정 알림 규칙의 이력을 조회합니다.
    
    Args:
        rule_name: 알림 규칙 이름
        hours: 조회할 시간 범위 (기본 24시간)
        limit: 최대 결과 수 (기본 100개)
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 이력 목록
    """
    try:
        # 규칙 존재 확인
        rule = await alerting_service.rule_engine.get_rule(rule_name)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙 '{rule_name}'을 찾을 수 없습니다"
            )
        
        # 이력 조회
        history = await alerting_service.get_alert_history(rule_name, hours)
        
        # 결과 제한
        limited_history = history[:limit] if len(history) > limit else history
        
        return AlertHistoryResponse(
            rule_name=rule_name,
            history=limited_history,
            total=len(limited_history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 이력 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 이력 조회 중 오류가 발생했습니다"
        )


@router.get("/statistics", response_model=AlertStatisticsResponse)
async def get_alert_statistics(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertStatisticsResponse:
    """
    알림 시스템의 통계 정보를 조회합니다.
    
    Args:
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 통계 정보
    """
    try:
        all_rules = list(alerting_service.rule_engine.rules.values())
        active_rules = await alerting_service.rule_engine.get_active_rules()
        
        # 오늘 전송된 알림 수 계산 (이력에서)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        alerts_today = 0
        severity_counts = {severity.value: 0 for severity in AlertSeverity}
        channel_counts = {channel.value: 0 for channel in AlertChannel}
        
        for history_entry in alerting_service.rule_engine.alert_history:
            if history_entry.timestamp >= today:
                alerts_today += 1
                
                # 해당 규칙의 심각도와 채널 정보 찾기
                rule = await alerting_service.rule_engine.get_rule(history_entry.rule_name)
                if rule:
                    severity_counts[rule.severity.value] += 1
                    for channel in history_entry.channels_sent:
                        if channel.value in channel_counts:
                            channel_counts[channel.value] += 1
        
        return AlertStatisticsResponse(
            total_rules=len(all_rules),
            active_rules=len(active_rules),
            alerts_sent_today=alerts_today,
            alerts_by_severity=severity_counts,
            alerts_by_channel=channel_counts
        )
        
    except Exception as e:
        logger.error(f"알림 통계 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 통계 조회 중 오류가 발생했습니다"
        )


@router.post("/suppression", status_code=status.HTTP_201_CREATED)
async def create_suppression_rule(
    suppression_data: SuppressionRuleRequest,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 억제 규칙을 생성합니다.
    
    Args:
        suppression_data: 억제 규칙 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        생성된 억제 규칙 정보
    """
    try:
        # 억제 규칙을 서비스에 추가
        suppression_rule = {
            "type": suppression_data.type,
            "name": suppression_data.name,
            "start_time": suppression_data.start_time,
            "end_time": suppression_data.end_time,
            "affected_services": suppression_data.affected_services,
            "description": suppression_data.description
        }
        
        alerting_service.suppression_rules.append(suppression_rule)
        
        return suppression_rule
        
    except Exception as e:
        logger.error(f"억제 규칙 생성 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="억제 규칙 생성 중 오류가 발생했습니다"
        )


@router.get("/suppression")
async def get_suppression_rules(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 억제 규칙 목록을 조회합니다.
    
    Args:
        alerting_service: 지능형 알림 서비스
        
    Returns:
        억제 규칙 목록
    """
    try:
        return {
            "suppression_rules": alerting_service.suppression_rules,
            "total": len(alerting_service.suppression_rules)
        }
        
    except Exception as e:
        logger.error(f"억제 규칙 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="억제 규칙 조회 중 오류가 발생했습니다"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> HealthCheckResponse:
    """
    알림 시스템의 헬스체크를 수행합니다.
    
    Args:
        alerting_service: 지능형 알림 서비스
        
    Returns:
        헬스체크 결과
    """
    try:
        services = {}
        
        # 알림 서비스 상태 확인
        try:
            if alerting_service.notification_service:
                services["notification_service"] = "healthy"
            else:
                services["notification_service"] = "unavailable"
        except Exception:
            services["notification_service"] = "error"
        
        # 모니터링 서비스 상태 확인
        try:
            if alerting_service.monitoring_service:
                services["monitoring_service"] = "healthy"
            else:
                services["monitoring_service"] = "unavailable"
        except Exception:
            services["monitoring_service"] = "error"
        
        # 규칙 엔진 상태 확인
        try:
            if alerting_service.rule_engine:
                services["rule_engine"] = "healthy"
            else:
                services["rule_engine"] = "unavailable"
        except Exception:
            services["rule_engine"] = "error"
        
        # 전체 상태 판단
        if all(status == "healthy" for status in services.values()):
            overall_status = "healthy"
        elif any(status == "healthy" for status in services.values()):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            services=services,
            last_check=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"헬스체크 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="헬스체크 중 오류가 발생했습니다"
        )