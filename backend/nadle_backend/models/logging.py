"""
로깅 시스템 모델

통합 로깅 시스템을 위한 MongoDB 모델 정의
내부 애플리케이션 로그와 외부 인프라 로그를 통합 관리
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from beanie import Document, Indexed
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """로그 레벨 열거형"""
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogSource(str, Enum):
    """로그 소스 열거형"""
    INTERNAL = "internal"  # 내부 애플리케이션
    EXTERNAL = "external"  # 외부 인프라


class ServiceType(str, Enum):
    """서비스 타입 열거형"""
    API = "api"           # FastAPI 백엔드
    WEB = "web"           # Remix 프론트엔드
    CLOUD_RUN = "cloud-run"  # Google Cloud Run
    DATABASE = "database"  # MongoDB Atlas
    REDIS = "redis"       # Redis 캐시
    VERCEL = "vercel"     # Vercel 배포


class LogContext(BaseModel):
    """로그 컨텍스트 정보"""
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[int] = None  # 밀리초
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # 외부 인프라 관련
    infrastructure: Optional[str] = None
    instance_id: Optional[str] = None
    region: Optional[str] = None
    version: Optional[str] = None


class LogMetadata(BaseModel):
    """로그 메타데이터"""
    tags: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # 성능 메트릭
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    
    # 외부 인프라 관련
    cloud_trace_id: Optional[str] = None
    atlas_cluster: Optional[str] = None
    vercel_deployment_id: Optional[str] = None


class LogEntry(Document):
    """
    통합 로그 엔트리 모델
    
    내부/외부 모든 로그를 저장하는 메인 모델
    """
    
    # 기본 필드
    timestamp: Indexed(datetime) = Field(default_factory=datetime.utcnow)
    level: Indexed(LogLevel)
    service: Indexed(ServiceType)
    source: Indexed(LogSource)
    message: str
    
    # 상세 정보
    context: Optional[LogContext] = None
    metadata: Optional[LogMetadata] = None
    stack_trace: Optional[str] = None
    
    # 검색 및 분석용
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "log_entries"
        indexes = [
            [
                ("timestamp", -1),
                ("level", 1),
                ("service", 1)
            ],
            [
                ("service", 1),
                ("source", 1),
                ("timestamp", -1)
            ],
            [
                ("level", 1),
                ("timestamp", -1)
            ],
            [
                ("context.user_id", 1),
                ("timestamp", -1)
            ],
            [
                ("context.endpoint", 1),
                ("timestamp", -1)
            ]
        ]
        # TTL 인덱스: 30일 후 자동 삭제
        ttl_index = {
            "field": "timestamp",
            "expireAfterSeconds": 30 * 24 * 60 * 60  # 30일
        }


class LogStats(BaseModel):
    """로그 통계 정보"""
    total_count: int = 0
    error_count: int = 0
    warn_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    
    # 서비스별 통계
    service_stats: Dict[str, int] = Field(default_factory=dict)
    
    # 시간 범위
    start_time: datetime
    end_time: datetime


class LogFilter(BaseModel):
    """로그 필터링 조건"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    levels: Optional[List[LogLevel]] = None
    services: Optional[List[ServiceType]] = None
    sources: Optional[List[LogSource]] = None
    search_query: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    
    # 페이징
    page: int = 1
    page_size: int = 50


class ErrorGrouping(Document):
    """에러 그룹핑 정보"""
    
    # 에러 식별
    error_hash: Indexed(str)  # 에러 메시지 해시
    service: Indexed(ServiceType)
    endpoint: Optional[str] = None
    error_type: Optional[str] = None
    
    # 통계
    count: int = 1
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # 상세 정보
    sample_message: str
    sample_stack_trace: Optional[str] = None
    
    # 분석
    severity: Optional[str] = None
    is_resolved: bool = False
    resolution_notes: Optional[str] = None
    
    class Settings:
        name = "error_groupings"
        indexes = [
            [
                ("error_hash", 1),
                ("service", 1)
            ],
            [
                ("service", 1),
                ("count", -1),
                ("last_seen", -1)
            ],
            [
                ("last_seen", -1),
                ("is_resolved", 1)
            ]
        ]


class LogSearchIndex(BaseModel):
    """로그 검색 인덱스"""
    message_tokens: List[str] = Field(default_factory=list)
    context_tokens: List[str] = Field(default_factory=list)
    full_text: str = ""


class PerformanceMetric(Document):
    """성능 메트릭 로그"""
    
    timestamp: Indexed(datetime) = Field(default_factory=datetime.utcnow)
    service: Indexed(ServiceType)
    metric_name: str
    metric_value: float
    unit: str
    
    # 컨텍스트
    endpoint: Optional[str] = None
    instance_id: Optional[str] = None
    region: Optional[str] = None
    
    # 메타데이터
    tags: Dict[str, str] = Field(default_factory=dict)
    
    class Settings:
        name = "performance_metrics"
        indexes = [
            [
                ("timestamp", -1),
                ("service", 1),
                ("metric_name", 1)
            ],
            [
                ("service", 1),
                ("endpoint", 1),
                ("timestamp", -1)
            ]
        ]
        # TTL 인덱스: 7일 후 자동 삭제
        ttl_index = {
            "field": "timestamp",
            "expireAfterSeconds": 7 * 24 * 60 * 60  # 7일
        }


# 로그 관련 응답 모델들
class LogEntryResponse(BaseModel):
    """로그 엔트리 응답 모델"""
    id: str
    timestamp: datetime
    level: LogLevel
    service: ServiceType
    source: LogSource
    message: str
    context: Optional[LogContext] = None
    metadata: Optional[LogMetadata] = None
    stack_trace: Optional[str] = None


class LogListResponse(BaseModel):
    """로그 목록 응답 모델"""
    logs: List[LogEntryResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class LogDashboardResponse(BaseModel):
    """로그 대시보드 응답 모델"""
    stats: LogStats
    recent_errors: List[ErrorGrouping]
    time_series: List[Dict[str, Any]] = Field(default_factory=list)
    top_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    performance_summary: Dict[str, Any] = Field(default_factory=dict)