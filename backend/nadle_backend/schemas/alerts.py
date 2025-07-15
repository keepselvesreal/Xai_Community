"""
알림 시스템 Pydantic 스키마

API 요청/응답을 위한 데이터 검증 및 직렬화 스키마
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AlertThresholdSchema(BaseModel):
    """알림 임계값 스키마"""
    metric: str = Field(..., description="메트릭 이름")
    value: float = Field(..., description="임계값")
    duration_minutes: Optional[int] = Field(None, description="지속 시간 (분)")
    
    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('임계값은 0 이상이어야 합니다')
        return v


class AlertRuleCreate(BaseModel):
    """알림 규칙 생성 스키마"""
    name: str = Field(..., description="알림 규칙 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="알림 규칙 설명", max_length=500)
    condition: str = Field(..., description="알림 조건 (greater_than, less_than, equals)")
    threshold: AlertThresholdSchema = Field(..., description="임계값 설정")
    severity: str = Field(..., description="알림 심각도 (low, medium, high, critical)")
    channels: List[str] = Field(..., description="알림 채널 목록 (email, discord)", min_items=1)
    cooldown_minutes: Optional[int] = Field(None, description="쿨다운 시간 (분)")
    escalation_minutes: Optional[int] = Field(None, description="에스컬레이션 시간 (분)")
    enabled: bool = Field(True, description="규칙 활성화 여부")
    tags: Optional[Dict[str, str]] = Field(None, description="태그")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('이름은 공백일 수 없습니다')
        return v.strip()
    
    @validator('condition')
    def validate_condition(cls, v):
        valid_conditions = ['greater_than', 'less_than', 'equals']
        if v not in valid_conditions:
            raise ValueError(f'유효하지 않은 조건: {v}. 사용 가능한 조건: {valid_conditions}')
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v not in valid_severities:
            raise ValueError(f'유효하지 않은 심각도: {v}. 사용 가능한 심각도: {valid_severities}')
        return v
    
    @validator('channels')
    def validate_channels(cls, v):
        valid_channels = ['email', 'discord']
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f'유효하지 않은 채널: {channel}. 사용 가능한 채널: {valid_channels}')
        return v
    
    @validator('cooldown_minutes')
    def validate_cooldown_minutes(cls, v):
        if v is not None and v < 0:
            raise ValueError('쿨다운 시간은 0 이상이어야 합니다')
        return v
    
    @validator('escalation_minutes')
    def validate_escalation_minutes(cls, v):
        if v is not None and v < 0:
            raise ValueError('에스컬레이션 시간은 0 이상이어야 합니다')
        return v


class AlertRuleUpdate(BaseModel):
    """알림 규칙 수정 스키마"""
    description: Optional[str] = Field(None, description="알림 규칙 설명", max_length=500)
    condition: Optional[str] = Field(None, description="알림 조건")
    threshold: Optional[AlertThresholdSchema] = Field(None, description="임계값 설정")
    severity: Optional[str] = Field(None, description="알림 심각도")
    channels: Optional[List[str]] = Field(None, description="알림 채널 목록")
    cooldown_minutes: Optional[int] = Field(None, description="쿨다운 시간 (분)")
    escalation_minutes: Optional[int] = Field(None, description="에스컬레이션 시간 (분)")
    enabled: Optional[bool] = Field(None, description="규칙 활성화 여부")
    tags: Optional[Dict[str, str]] = Field(None, description="태그")
    
    @validator('condition')
    def validate_condition(cls, v):
        if v is not None:
            valid_conditions = ['greater_than', 'less_than', 'equals']
            if v not in valid_conditions:
                raise ValueError(f'유효하지 않은 조건: {v}. 사용 가능한 조건: {valid_conditions}')
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            valid_severities = ['low', 'medium', 'high', 'critical']
            if v not in valid_severities:
                raise ValueError(f'유효하지 않은 심각도: {v}. 사용 가능한 심각도: {valid_severities}')
        return v
    
    @validator('channels')
    def validate_channels(cls, v):
        if v is not None:
            valid_channels = ['email', 'discord']
            for channel in v:
                if channel not in valid_channels:
                    raise ValueError(f'유효하지 않은 채널: {channel}. 사용 가능한 채널: {valid_channels}')
        return v


class AlertRuleResponse(BaseModel):
    """알림 규칙 응답 스키마"""
    id: str = Field(..., description="알림 규칙 ID")
    name: str = Field(..., description="알림 규칙 이름")
    description: Optional[str] = Field(None, description="알림 규칙 설명")
    condition: str = Field(..., description="알림 조건")
    threshold: Dict[str, Any] = Field(..., description="임계값 설정")
    severity: str = Field(..., description="알림 심각도")
    channels: List[str] = Field(..., description="알림 채널 목록")
    cooldown_minutes: Optional[int] = Field(None, description="쿨다운 시간 (분)")
    escalation_minutes: Optional[int] = Field(None, description="에스컬레이션 시간 (분)")
    enabled: bool = Field(..., description="규칙 활성화 여부")
    tags: Optional[Dict[str, str]] = Field(None, description="태그")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertEventResponse(BaseModel):
    """알림 이벤트 응답 스키마"""
    rule_name: str = Field(..., description="규칙 이름")
    metric_name: str = Field(..., description="메트릭 이름")
    current_value: float = Field(..., description="현재 값")
    threshold_value: float = Field(..., description="임계값")
    severity: str = Field(..., description="심각도")
    status: str = Field(..., description="상태")
    message: str = Field(..., description="알림 메시지")
    triggered_at: str = Field(..., description="트리거 시간")


class AlertStatisticsResponse(BaseModel):
    """알림 통계 응답 스키마"""
    total_rules: int = Field(..., description="총 규칙 수")
    active_rules: int = Field(..., description="활성 규칙 수")
    total_alerts: int = Field(..., description="총 알림 수")
    alerts_sent_today: int = Field(..., description="오늘 전송된 알림 수")
    alerts_by_severity: Dict[str, int] = Field(..., description="심각도별 알림 수")
    alerts_by_channel: Dict[str, int] = Field(..., description="채널별 알림 수")
    alert_rate_per_hour: float = Field(..., description="시간당 알림 발생률")


class AlertSuppressionCreate(BaseModel):
    """알림 억제 생성 스키마"""
    name: str = Field(..., description="억제 규칙 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="설명", max_length=500)
    rule_patterns: List[str] = Field(..., description="억제할 규칙 패턴", min_length=1)
    time_windows: Optional[List[Dict[str, str]]] = Field(None, description="억제 시간대")
    enabled: bool = Field(True, description="활성화 여부")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('이름은 공백일 수 없습니다')
        return v.strip()


class AlertSuppressionResponse(BaseModel):
    """알림 억제 응답 스키마"""
    id: str = Field(..., description="억제 규칙 ID")
    name: str = Field(..., description="억제 규칙 이름")
    description: Optional[str] = Field(None, description="설명")
    rule_patterns: List[str] = Field(..., description="억제할 규칙 패턴")
    time_windows: Optional[List[Dict[str, str]]] = Field(None, description="억제 시간대")
    enabled: bool = Field(..., description="활성화 여부")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }