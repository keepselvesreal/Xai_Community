"""
알림 시스템 데이터 모델

지능형 알림 시스템에서 사용하는 데이터 모델들
"""
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """알림 심각도 열거형"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """알림 채널 열거형"""
    EMAIL = "email"
    DISCORD = "discord"


class AlertCondition(str, Enum):
    """알림 조건 열거형"""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"


class AlertStatus(str, Enum):
    """알림 상태 열거형"""
    SENT = "sent"
    PENDING = "pending"
    FAILED = "failed"
    SUPPRESSED = "suppressed"


class AlertThreshold(BaseModel):
    """알림 임계값 모델"""
    metric: str = Field(..., description="메트릭 이름")
    value: float = Field(..., description="임계값")
    duration_minutes: Optional[int] = Field(None, description="지속 시간 (분)")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertRule(BaseModel):
    """알림 규칙 모델"""
    name: str = Field(..., description="알림 규칙 이름")
    description: Optional[str] = Field(None, description="알림 규칙 설명")
    condition: AlertCondition = Field(..., description="알림 조건")
    threshold: AlertThreshold = Field(..., description="임계값 설정")
    severity: AlertSeverity = Field(..., description="알림 심각도")
    channels: List[AlertChannel] = Field(..., description="알림 채널 목록")
    cooldown_minutes: Optional[int] = Field(None, description="쿨다운 시간 (분)")
    escalation_minutes: Optional[int] = Field(None, description="에스컬레이션 시간 (분)")
    enabled: bool = Field(True, description="규칙 활성화 여부")
    tags: Optional[Dict[str, str]] = Field(None, description="태그")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertEvent(BaseModel):
    """알림 이벤트 모델"""
    id: Optional[str] = Field(None, description="이벤트 ID")
    rule_name: str = Field(..., description="규칙 이름")
    metric_name: str = Field(..., description="메트릭 이름")
    current_value: float = Field(..., description="현재 값")
    threshold_value: float = Field(..., description="임계값")
    severity: AlertSeverity = Field(..., description="심각도")
    status: AlertStatus = Field(..., description="상태")
    message: str = Field(..., description="알림 메시지")
    triggered_at: datetime = Field(..., description="트리거 시간")
    resolved_at: Optional[datetime] = Field(None, description="해결 시간")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertSuppression(BaseModel):
    """알림 억제 규칙 모델"""
    name: str = Field(..., description="억제 규칙 이름")
    description: Optional[str] = Field(None, description="설명")
    rule_patterns: List[str] = Field(..., description="억제할 규칙 패턴")
    time_windows: Optional[List[Dict[str, str]]] = Field(None, description="억제 시간대")
    enabled: bool = Field(True, description="활성화 여부")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertStatistics(BaseModel):
    """알림 통계 모델"""
    total_rules: int = Field(..., description="총 규칙 수")
    active_rules: int = Field(..., description="활성 규칙 수")
    total_alerts: int = Field(..., description="총 알림 수")
    alerts_by_severity: Dict[str, int] = Field(..., description="심각도별 알림 수")
    alerts_by_channel: Dict[str, int] = Field(..., description="채널별 알림 수")
    alert_rate_per_hour: float = Field(..., description="시간당 알림 발생률")
    false_positive_rate: Optional[float] = Field(None, description="오탐률")
    response_time_avg: Optional[float] = Field(None, description="평균 응답 시간")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertAggregation(BaseModel):
    """알림 집계 모델"""
    rule_name: str = Field(..., description="규칙 이름")
    count: int = Field(..., description="집계된 알림 수")
    first_occurrence: datetime = Field(..., description="첫 발생 시간")
    last_occurrence: datetime = Field(..., description="마지막 발생 시간")
    severity: AlertSeverity = Field(..., description="심각도")
    summary_message: str = Field(..., description="요약 메시지")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }