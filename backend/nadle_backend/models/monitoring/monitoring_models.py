"""
인프라 모니터링을 위한 Pydantic 데이터 모델들

4개 외부 인프라(Cloud Run, Vercel, MongoDB Atlas, Upstash Redis)의
모니터링 데이터를 정의하는 모델들
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """서비스 상태 열거형"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class InfrastructureType(str, Enum):
    """인프라 타입 열거형"""
    CLOUD_RUN = "cloud_run"
    VERCEL = "vercel"
    MONGODB_ATLAS = "mongodb_atlas"
    UPSTASH_REDIS = "upstash_redis"


class BaseMetrics(BaseModel):
    """기본 메트릭 모델"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ServiceStatus
    response_time_ms: Optional[float] = Field(None, ge=0)
    error_message: Optional[str] = None


class CloudRunMetrics(BaseMetrics):
    """Google Cloud Run 메트릭"""
    service_name: str
    region: str
    revision_name: Optional[str] = None
    
    # 성능 메트릭
    request_count: Optional[int] = Field(None, ge=0)
    request_latency_ms: Optional[float] = Field(None, ge=0)
    error_rate: Optional[float] = Field(None, ge=0, le=100)
    
    # 자원 사용량
    cpu_utilization: Optional[float] = Field(None, ge=0, le=100)
    memory_utilization: Optional[float] = Field(None, ge=0, le=100)
    memory_limit_mb: Optional[int] = Field(None, gt=0)
    
    # 인스턴스 정보
    instance_count: Optional[int] = Field(None, ge=0)
    max_instances: Optional[int] = Field(None, ge=0)
    
    # 빌링 정보
    billable_instance_time: Optional[float] = Field(None, ge=0)


class VercelMetrics(BaseMetrics):
    """Vercel 메트릭"""
    project_id: str
    deployment_id: Optional[str] = None
    
    # 배포 정보
    deployment_status: Optional[str] = None
    deployment_url: Optional[str] = None
    deployment_created_at: Optional[datetime] = None
    
    # 함수 성능
    function_invocations: Optional[int] = Field(None, ge=0)
    function_duration_ms: Optional[float] = Field(None, ge=0)
    function_errors: Optional[int] = Field(None, ge=0)
    
    # Web Vitals
    core_web_vitals_score: Optional[float] = Field(None, ge=0, le=100)
    first_contentful_paint: Optional[float] = Field(None, ge=0)
    largest_contentful_paint: Optional[float] = Field(None, ge=0)
    cumulative_layout_shift: Optional[float] = Field(None, ge=0)
    
    # 대역폭
    bandwidth_bytes: Optional[int] = Field(None, ge=0)


class AtlasMetrics(BaseMetrics):
    """MongoDB Atlas 메트릭"""
    cluster_name: str
    cluster_type: Optional[str] = None
    
    # 연결 정보
    connections_current: Optional[int] = Field(None, ge=0)
    connections_available: Optional[int] = Field(None, ge=0)
    connections_created: Optional[int] = Field(None, ge=0)
    
    # 성능 메트릭
    operations_per_second: Optional[float] = Field(None, ge=0)
    read_operations_per_second: Optional[float] = Field(None, ge=0)
    write_operations_per_second: Optional[float] = Field(None, ge=0)
    
    # 지연시간
    read_latency_ms: Optional[float] = Field(None, ge=0)
    write_latency_ms: Optional[float] = Field(None, ge=0)
    
    # 자원 사용량
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    disk_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    
    # 저장 공간
    data_size_bytes: Optional[int] = Field(None, ge=0)
    storage_size_bytes: Optional[int] = Field(None, ge=0)
    index_size_bytes: Optional[int] = Field(None, ge=0)
    
    # 네트워크
    network_bytes_in: Optional[int] = Field(None, ge=0)
    network_bytes_out: Optional[int] = Field(None, ge=0)


class UpstashMetrics(BaseMetrics):
    """Upstash Redis 메트릭"""
    database_id: str
    database_name: Optional[str] = None
    region: Optional[str] = None
    
    # 연결 정보
    connection_count: Optional[int] = Field(None, ge=0)
    max_connections: Optional[int] = Field(None, ge=0)
    
    # 성능 메트릭
    hit_rate: Optional[float] = Field(None, ge=0, le=100)
    miss_rate: Optional[float] = Field(None, ge=0, le=100)
    operations_per_second: Optional[float] = Field(None, ge=0)
    
    # 지연시간
    read_latency_ms: Optional[float] = Field(None, ge=0)
    write_latency_ms: Optional[float] = Field(None, ge=0)
    read_latency_p99_ms: Optional[float] = Field(None, ge=0)
    write_latency_p99_ms: Optional[float] = Field(None, ge=0)
    
    # 메모리 사용량
    keyspace: Optional[int] = Field(None, ge=0)
    memory_usage_bytes: Optional[int] = Field(None, ge=0)
    memory_limit_bytes: Optional[int] = Field(None, ge=0)
    memory_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    
    # 처리량
    throughput_reads: Optional[float] = Field(None, ge=0)
    throughput_writes: Optional[float] = Field(None, ge=0)
    
    # 대역폭
    bandwidth_in_bytes: Optional[int] = Field(None, ge=0)
    bandwidth_out_bytes: Optional[int] = Field(None, ge=0)


class InfrastructureStatus(BaseModel):
    """개별 인프라 상태"""
    infrastructure_type: InfrastructureType
    service_name: str
    status: ServiceStatus
    last_check: datetime = Field(default_factory=datetime.utcnow)
    metrics: Optional[Union[CloudRunMetrics, VercelMetrics, AtlasMetrics, UpstashMetrics]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class UnifiedMonitoringResponse(BaseModel):
    """통합 모니터링 응답"""
    overall_status: ServiceStatus
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    infrastructure_count: int
    healthy_count: int
    unhealthy_count: int
    
    infrastructures: List[InfrastructureStatus]
    
    # 요약 메트릭
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    @property
    def uptime_percentage(self) -> float:
        """전체 가동 시간 비율"""
        if self.infrastructure_count == 0:
            return 0.0
        return (self.healthy_count / self.infrastructure_count) * 100


class MonitoringError(BaseModel):
    """모니터링 에러 정보"""
    infrastructure_type: InfrastructureType
    error_code: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    service: str
    status: ServiceStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: Optional[str] = None
    checks: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }