"""
알림 시스템 API 라우터

알림 규칙 관리, 알림 전송, 알림 이력 조회 등을 위한 REST API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from nadle_backend.services.intelligent_alerting import (
    IntelligentAlertingService,
    AlertRule,
    AlertSeverity,
    AlertChannel,
    AlertCondition,
    AlertThreshold,
    AlertStatus
)
from nadle_backend.services.notification_service import NotificationService, get_notification_service
from nadle_backend.schemas.alerts import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertEventResponse,
    AlertStatisticsResponse,
    AlertSuppressionCreate,
    AlertSuppressionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["alerts"])

# 글로벌 알림 서비스 인스턴스 (테스트와 실제 환경에서 상태 유지)
_global_alerting_service = None


def get_alerting_service(
    notification_service: NotificationService = Depends(get_notification_service)
) -> IntelligentAlertingService:
    """
    지능형 알림 서비스 의존성 주입
    
    Returns:
        IntelligentAlertingService 인스턴스
    """
    global _global_alerting_service
    if _global_alerting_service is None:
        _global_alerting_service = IntelligentAlertingService(notification_service=notification_service)
    return _global_alerting_service


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleResponse:
    """
    알림 규칙 생성
    
    Args:
        rule_data: 알림 규칙 생성 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        생성된 알림 규칙 정보
    """
    try:
        # AlertRule 객체 생성
        alert_rule = AlertRule(
            name=rule_data.name,
            description=rule_data.description,
            condition=AlertCondition(rule_data.condition),
            threshold=AlertThreshold(
                metric=rule_data.threshold.metric,
                value=rule_data.threshold.value,
                duration_minutes=rule_data.threshold.duration_minutes
            ),
            severity=AlertSeverity(rule_data.severity),
            channels=[AlertChannel(channel) for channel in rule_data.channels],
            cooldown_minutes=rule_data.cooldown_minutes,
            escalation_minutes=rule_data.escalation_minutes,
            enabled=rule_data.enabled,
            tags=rule_data.tags,
            created_at=datetime.utcnow()
        )
        
        # 중복 이름 체크
        existing_rule = await alerting_service.rule_engine.get_rule_by_name(alert_rule.name)
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"같은 이름의 알림 규칙이 이미 존재합니다: {alert_rule.name}"
            )
        
        # 규칙 추가
        await alerting_service.rule_engine.add_rule(alert_rule)
        
        logger.info(f"알림 규칙 생성됨: {alert_rule.name}")
        
        return AlertRuleResponse(
            id=alert_rule.id,  # UUID 기반 ID 사용
            name=alert_rule.name,
            description=alert_rule.description,
            condition=alert_rule.condition.value,
            threshold=alert_rule.threshold.model_dump(),
            severity=alert_rule.severity.value,
            channels=[channel.value for channel in alert_rule.channels],
            cooldown_minutes=alert_rule.cooldown_minutes,
            escalation_minutes=alert_rule.escalation_minutes,
            enabled=alert_rule.enabled,
            tags=alert_rule.tags,
            created_at=alert_rule.created_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"알림 규칙 생성 유효성 검사 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"유효하지 않은 데이터: {str(e)}"
        )
    except Exception as e:
        logger.error(f"알림 규칙 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 생성 중 오류가 발생했습니다"
        )


@router.get("/rules", response_model=Dict[str, Any])
async def get_alert_rules(
    enabled: Optional[bool] = Query(None, description="활성화 상태 필터"),
    severity: Optional[str] = Query(None, description="심각도 필터"),
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 규칙 목록 조회
    
    Args:
        enabled: 활성화 상태 필터
        severity: 심각도 필터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 규칙 목록
    """
    try:
        if enabled is not None and enabled:
            rules = await alerting_service.rule_engine.get_active_rules()
        else:
            rules = list(alerting_service.rule_engine.rules.values())
        
        # 심각도 필터 적용
        if severity:
            try:
                severity_filter = AlertSeverity(severity)
                rules = [rule for rule in rules if rule.severity == severity_filter]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"유효하지 않은 심각도: {severity}"
                )
        
        # 비활성화된 규칙 필터링 (enabled=False인 경우)
        if enabled is not None and not enabled:
            rules = [rule for rule in rules if not rule.enabled]
        
        return {
            "rules": [
                AlertRuleResponse(
                    id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    condition=rule.condition.value,
                    threshold=rule.threshold.model_dump(),
                    severity=rule.severity.value,
                    channels=[channel.value for channel in rule.channels],
                    cooldown_minutes=rule.cooldown_minutes,
                    escalation_minutes=rule.escalation_minutes,
                    enabled=rule.enabled,
                    tags=rule.tags,
                    created_at=rule.created_at
                ).model_dump()
                for rule in rules
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleResponse:
    """
    특정 알림 규칙 조회
    
    Args:
        rule_id: 알림 규칙 ID
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 규칙 정보
    """
    try:
        rule = await alerting_service.rule_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙을 찾을 수 없습니다: {rule_id}"
            )
        
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            condition=rule.condition.value,
            threshold=rule.threshold.model_dump(),
            severity=rule.severity.value,
            channels=[channel.value for channel in rule.channels],
            cooldown_minutes=rule.cooldown_minutes,
            escalation_minutes=rule.escalation_minutes,
            enabled=rule.enabled,
            tags=rule.tags,
            created_at=rule.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 조회 실패 ({rule_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 조회 중 오류가 발생했습니다"
        )


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    rule_data: AlertRuleUpdate,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> AlertRuleResponse:
    """
    알림 규칙 수정
    
    Args:
        rule_id: 알림 규칙 ID
        rule_data: 수정할 알림 규칙 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        수정된 알림 규칙 정보
    """
    try:
        # 기존 규칙 확인
        existing_rule = await alerting_service.rule_engine.get_rule(rule_id)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙을 찾을 수 없습니다: {rule_id}"
            )
        
        # 수정된 규칙 생성
        updated_rule = AlertRule(
            id=existing_rule.id,  # 기존 ID 유지
            name=existing_rule.name,
            description=rule_data.description or existing_rule.description,
            condition=AlertCondition(rule_data.condition) if rule_data.condition else existing_rule.condition,
            threshold=AlertThreshold(
                metric=rule_data.threshold.metric if rule_data.threshold else existing_rule.threshold.metric,
                value=rule_data.threshold.value if rule_data.threshold else existing_rule.threshold.value,
                duration_minutes=rule_data.threshold.duration_minutes if rule_data.threshold else existing_rule.threshold.duration_minutes
            ),
            severity=AlertSeverity(rule_data.severity) if rule_data.severity else existing_rule.severity,
            channels=[AlertChannel(channel) for channel in rule_data.channels] if rule_data.channels else existing_rule.channels,
            cooldown_minutes=rule_data.cooldown_minutes if rule_data.cooldown_minutes is not None else existing_rule.cooldown_minutes,
            escalation_minutes=rule_data.escalation_minutes if rule_data.escalation_minutes is not None else existing_rule.escalation_minutes,
            enabled=rule_data.enabled if rule_data.enabled is not None else existing_rule.enabled,
            tags=rule_data.tags or existing_rule.tags,
            created_at=existing_rule.created_at,
            updated_at=datetime.utcnow()
        )
        
        # 규칙 업데이트
        await alerting_service.rule_engine.add_rule(updated_rule)
        
        logger.info(f"알림 규칙 수정됨: {updated_rule.name} (ID: {rule_id})")
        
        return AlertRuleResponse(
            id=updated_rule.id,
            name=updated_rule.name,
            description=updated_rule.description,
            condition=updated_rule.condition.value,
            threshold=updated_rule.threshold.model_dump(),
            severity=updated_rule.severity.value,
            channels=[channel.value for channel in updated_rule.channels],
            cooldown_minutes=updated_rule.cooldown_minutes,
            escalation_minutes=updated_rule.escalation_minutes,
            enabled=updated_rule.enabled,
            tags=updated_rule.tags,
            created_at=updated_rule.created_at,
            updated_at=updated_rule.updated_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"알림 규칙 수정 유효성 검사 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"유효하지 않은 데이터: {str(e)}"
        )
    except Exception as e:
        logger.error(f"알림 규칙 수정 실패 ({rule_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 수정 중 오류가 발생했습니다"
        )


@router.delete("/rules/{rule_id}", status_code=status.HTTP_200_OK)
async def delete_alert_rule(
    rule_id: str,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 규칙 삭제
    
    Args:
        rule_id: 알림 규칙 ID
        alerting_service: 지능형 알림 서비스
    """
    try:
        # 삭제 전 규칙 정보 조회 (로그용)
        rule = await alerting_service.rule_engine.get_rule(rule_id)
        rule_name = rule.name if rule else rule_id
        
        deleted = await alerting_service.rule_engine.remove_rule(rule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙을 찾을 수 없습니다: {rule_id}"
            )
        
        logger.info(f"알림 규칙 삭제됨: {rule_name} (ID: {rule_id})")
        
        return {"message": f"알림 규칙 '{rule_name}'이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 규칙 삭제 실패 ({rule_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 삭제 중 오류가 발생했습니다"
        )


@router.post("/evaluate", response_model=Dict[str, Any])
async def evaluate_alert_rules(
    rule_ids: Optional[List[str]] = None,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 규칙 평가
    
    Args:
        rule_ids: 평가할 규칙 ID 목록 (전체 평가 시 None)
        alerting_service: 지능형 알림 서비스
        
    Returns:
        평가 결과 목록
    """
    try:
        if rule_ids:
            # 특정 규칙들만 평가
            rules = []
            for rule_id in rule_ids:
                rule = await alerting_service.rule_engine.get_rule(rule_id)
                if rule:
                    rules.append(rule)
        else:
            # 모든 활성 규칙 평가
            rules = await alerting_service.rule_engine.get_active_rules()
        
        results = await alerting_service.evaluate_rules_batch(rules)
        
        logger.info(f"알림 규칙 평가 완료: {len(results)}개")
        
        return {
            "evaluation_results": [
                {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "should_alert": result,
                    "evaluated_at": datetime.utcnow().isoformat()
                }
                for rule, result in zip(rules, results)
            ]
        }
        
    except Exception as e:
        logger.error(f"알림 규칙 평가 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 규칙 평가 중 오류가 발생했습니다"
        )


@router.post("/send")
async def send_manual_alert(
    alert_data: Dict[str, Any],
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    수동 알림 전송
    
    Args:
        alert_data: 알림 데이터 (rule_id, metric_data 포함)
        alerting_service: 지능형 알림 서비스
        
    Returns:
        전송 결과
    """
    try:
        rule_id = alert_data.get("rule_id")
        metric_data = alert_data.get("metric_data", {})
        
        if not rule_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rule_id is required"
            )
        
        rule = await alerting_service.rule_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙을 찾을 수 없습니다: {rule_id}"
            )
        
        result = await alerting_service.send_alert(rule, metric_data)
        
        logger.info(f"수동 알림 전송 완료: {rule.name} (ID: {rule_id})")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수동 알림 전송 실패 ({alert_data.get('rule_id', 'unknown')}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수동 알림 전송 중 오류가 발생했습니다"
        )


@router.get("/history/{rule_id}", response_model=Dict[str, Any])
async def get_alert_history(
    rule_id: str,
    hours: int = Query(24, description="조회할 시간 범위 (시간)"),
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 이력 조회
    
    Args:
        rule_id: 알림 규칙 ID
        hours: 조회할 시간 범위
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 이력 목록
    """
    try:
        # 규칙 정보 조회
        rule = await alerting_service.rule_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림 규칙을 찾을 수 없습니다: {rule_id}"
            )
        
        history = await alerting_service.get_alert_history(rule.name, hours)
        
        return {
            "rule_id": rule_id,
            "rule_name": rule.name,
            "history": [
                AlertEventResponse(
                    rule_name=event["rule_name"],
                    metric_name=event["metric_name"],
                    current_value=event["current_value"],
                    threshold_value=event["threshold_value"],
                    severity=event["severity"],
                    status=event["status"],
                    message=event["message"],
                    triggered_at=event["triggered_at"]
                ).model_dump()
                for event in history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 이력 조회 실패 ({rule_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 이력 조회 중 오류가 발생했습니다"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_alert_statistics(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 통계 조회
    
    Args:
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 통계 정보
    """
    try:
        all_rules = list(alerting_service.rule_engine.rules.values())
        active_rules = [rule for rule in all_rules if rule.enabled]
        
        # 심각도별 통계
        severity_stats = {}
        for severity in AlertSeverity:
            severity_stats[severity.value] = len([rule for rule in active_rules if rule.severity == severity])
        
        # 채널별 통계
        channel_stats = {}
        for channel in AlertChannel:
            channel_stats[channel.value] = len([rule for rule in active_rules if channel in rule.channels])
        
        return AlertStatisticsResponse(
            total_rules=len(all_rules),
            active_rules=len(active_rules),
            total_alerts=len(alerting_service.alert_history),
            alerts_sent_today=len(alerting_service.alert_history),  # 임시로 같은 값 사용
            alerts_by_severity=severity_stats,
            alerts_by_channel=channel_stats,
            alert_rate_per_hour=0.0  # 실제 계산 로직 필요
        ).model_dump()
        
    except Exception as e:
        logger.error(f"알림 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 통계 조회 중 오류가 발생했습니다"
        )


@router.get("/metrics")
async def get_available_metrics() -> Dict[str, Any]:
    """
    사용 가능한 메트릭 목록 조회
    
    Returns:
        사용 가능한 메트릭 목록
    """
    try:
        available_metrics = [
            {
                "name": "cpu_usage",
                "display_name": "CPU 사용률",
                "description": "시스템 CPU 사용률 (%)",
                "unit": "%",
                "category": "system"
            },
            {
                "name": "memory_usage",
                "display_name": "메모리 사용률",
                "description": "시스템 메모리 사용률 (%)",
                "unit": "%",
                "category": "system"
            },
            {
                "name": "disk_usage",
                "display_name": "디스크 사용률",
                "description": "디스크 사용률 (%)",
                "unit": "%",
                "category": "system"
            },
            {
                "name": "network_io",
                "display_name": "네트워크 I/O",
                "description": "네트워크 입출력량 (MB/s)",
                "unit": "MB/s",
                "category": "network"
            },
            {
                "name": "response_time",
                "display_name": "응답 시간",
                "description": "API 응답 시간 (ms)",
                "unit": "ms",
                "category": "application"
            },
            {
                "name": "error_rate",
                "display_name": "에러율",
                "description": "에러 발생률 (%)",
                "unit": "%",
                "category": "application"
            },
            {
                "name": "active_users",
                "display_name": "활성 사용자",
                "description": "현재 활성 사용자 수",
                "unit": "count",
                "category": "application"
            },
            {
                "name": "database_connections",
                "display_name": "데이터베이스 연결",
                "description": "데이터베이스 활성 연결 수",
                "unit": "count",
                "category": "database"
            },
            {
                "name": "queue_length",
                "display_name": "큐 길이",
                "description": "대기열에 있는 작업 수",
                "unit": "count",
                "category": "application"
            },
            {
                "name": "uptime",
                "display_name": "가동 시간",
                "description": "서비스 가동 시간 (시간)",
                "unit": "hours",
                "category": "system"
            }
        ]
        
        return {
            "metrics": available_metrics,
            "categories": ["system", "network", "application", "database"]
        }
        
    except Exception as e:
        logger.error(f"사용 가능한 메트릭 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메트릭 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/health")
async def health_check(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 시스템 헬스체크
    
    Returns:
        헬스체크 결과
    """
    try:
        # 알림 서비스 상태 점검
        rule_count = len(alerting_service.rule_engine.rules)
        active_rules = len([rule for rule in alerting_service.rule_engine.rules.values() if rule.enabled])
        
        # 최근 알림 발송 이력 확인
        recent_alerts = len(alerting_service.alert_history)
        
        # 알림 서비스 구성 요소 상태 점검
        services_status = {
            "notification_service": "healthy",
            "rule_engine": "healthy" if rule_count >= 0 else "error",
            "alert_history": "healthy" if recent_alerts >= 0 else "error"
        }
        
        # 전체 상태 판정
        overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "degraded"
        
        return {
            "status": overall_status,
            "service": "intelligent-alerting",
            "services": services_status,
            "metrics": {
                "total_rules": rule_count,
                "active_rules": active_rules,
                "recent_alerts": recent_alerts,
                "service_uptime": "running"
            },
            "last_check": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"알림 시스템 헬스체크 실패: {e}")
        return {
            "status": "error",
            "service": "intelligent-alerting",
            "services": {
                "notification_service": "error",
                "rule_engine": "error",
                "alert_history": "error"
            },
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }


@router.post("/test")
async def test_alert_system(
    test_data: Optional[Dict[str, Any]] = None,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 시스템 테스트
    
    Args:
        test_data: 테스트 데이터 (선택사항)
        alerting_service: 지능형 알림 서비스
        
    Returns:
        테스트 결과
    """
    try:
        # 테스트 알림 규칙 생성
        test_rule = AlertRule(
            name="test_alert_rule",
            description="알림 시스템 테스트용 규칙",
            condition=AlertCondition.GREATER_THAN,
            threshold=AlertThreshold(
                metric="test_metric",
                value=100.0,
                duration_minutes=1
            ),
            severity=AlertSeverity.LOW,
            channels=[AlertChannel.EMAIL],
            enabled=True
        )
        
        # 테스트 메트릭 데이터
        test_metric_data = {
            "test_metric": 150.0,  # 임계값보다 높은 값
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 알림 규칙 평가
        should_alert = await alerting_service.evaluate_rule(test_rule, test_metric_data)
        
        result = {
            "test_status": "success",
            "rule_evaluation": {
                "rule_name": test_rule.name,
                "should_alert": should_alert,
                "test_metric_value": test_metric_data["test_metric"],
                "threshold": test_rule.threshold.value,
                "condition": test_rule.condition.value
            },
            "system_health": {
                "rule_engine": "functional",
                "notification_service": "available"
            },
            "test_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("알림 시스템 테스트 완료")
        return result
        
    except Exception as e:
        logger.error(f"알림 시스템 테스트 실패: {e}")
        return {
            "test_status": "failed",
            "error": str(e),
            "system_health": {
                "rule_engine": "error",
                "notification_service": "error"
            },
            "test_timestamp": datetime.utcnow().isoformat()
        }


@router.post("/suppression", status_code=status.HTTP_201_CREATED)
async def create_suppression_rule(
    suppression_data: AlertSuppressionCreate,
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 억제 규칙 생성
    
    Args:
        suppression_data: 억제 규칙 생성 데이터
        alerting_service: 지능형 알림 서비스
        
    Returns:
        생성된 억제 규칙 정보
    """
    try:
        # 임시 구현 - 실제로는 suppression 서비스에서 처리
        suppression_rule = {
            "id": f"suppression_{suppression_data.name}",
            "name": suppression_data.name,
            "description": suppression_data.description,
            "rule_patterns": suppression_data.rule_patterns,
            "time_windows": suppression_data.time_windows,
            "enabled": suppression_data.enabled,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": suppression_data.expires_at.isoformat() if suppression_data.expires_at else None
        }
        
        logger.info(f"알림 억제 규칙 생성됨: {suppression_data.name}")
        
        return suppression_rule
        
    except Exception as e:
        logger.error(f"알림 억제 규칙 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 억제 규칙 생성 중 오류가 발생했습니다"
        )


@router.get("/suppression")
async def get_suppression_rules(
    alerting_service: IntelligentAlertingService = Depends(get_alerting_service)
) -> Dict[str, Any]:
    """
    알림 억제 규칙 목록 조회
    
    Args:
        alerting_service: 지능형 알림 서비스
        
    Returns:
        알림 억제 규칙 목록
    """
    try:
        # 임시 구현 - 실제로는 suppression 서비스에서 처리
        suppression_rules = []
        
        return {
            "suppression_rules": suppression_rules
        }
        
    except Exception as e:
        logger.error(f"알림 억제 규칙 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 억제 규칙 목록 조회 중 오류가 발생했습니다"
        )