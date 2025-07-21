# 로깅 시스템 구축 설계 문서

**작성일**: 2025-07-19  
**작성자**: Claude Code (태수 요청)  
**프로젝트**: Xai Community v5 Backend Logging System

---

## 📋 개요

본 문서는 TDD 기반 점진적 구현으로 설계된 Xai Community 프로젝트의 통합 로깅 시스템 구축 방안을 제시합니다. 실제 외부 인프라 API 응답을 기반으로 한 Mock 데이터와 검증된 테스트 케이스를 포함합니다.

### 🎯 주요 목표
- 내부 애플리케이션 로그 + 외부 인프라 로그 통합
- 다른 프로젝트에서도 재사용 가능한 추상화된 설계
- TDD 기반 안전한 점진적 구현
- 실제 API 응답 기반의 정확한 Mock 데이터 활용

---

## 🏗️ 시스템 아키텍처

### 1. 전체 구조 (3계층 + 어댑터 패턴)

```
nadle_backend/
├── core/
│   └── logging/                    # 추상화 계층 (프로젝트 독립적)
│       ├── models.py              # 로깅 데이터 모델
│       ├── interfaces.py          # 추상 인터페이스
│       └── exceptions.py          # 로깅 전용 예외
├── logging/                       # 구현 계층 (현재 프로젝트용)
│   ├── adapters/                  # 외부 시스템 어댑터
│   │   ├── vercel_adapter.py      # Vercel 로그 수집
│   │   ├── upstash_adapter.py     # Upstash Redis 메트릭
│   │   ├── cloudrun_adapter.py    # Google Cloud Run 로그
│   │   └── atlas_adapter.py       # MongoDB Atlas 로그
│   ├── repositories/              # 데이터 저장소 (Motor 기반)
│   │   └── log_repository.py
│   ├── services/                  # 비즈니스 로직
│   │   ├── log_service.py
│   │   └── log_collector.py
│   └── routers/                   # API 엔드포인트
│       └── logging_router.py
└── tests/
    ├── fixtures/
    │   └── external_api_mocks.py   # 실제 API 응답 기반 Mock
    ├── unit/
    │   └── test_external_log_collectors.py
    └── integration/
        └── discover_api_responses.py
```

### 2. 핵심 설계 원칙

#### 🔄 Beanie ODM 우회 전략
```python
# 문제: Beanie의 Indexed() 함수가 Enum 타입 확장 시도 → 실패
# 해결: Motor 네이티브 + Pydantic 조합

# 기존 시스템 (유지)
class User(Document):  # Beanie 계속 사용
    email: Indexed(str, unique=True)

# 로깅 시스템만 (새로운 방식)  
class LogEntry(BaseModel):  # Beanie 없이 순수 Pydantic
    level: Literal["ERROR", "WARN", "INFO", "DEBUG"]
    service: Literal["api", "web", "cloud-run", "database"]

class LogRepository:
    def __init__(self, database: AsyncIOMotorDatabase):  # Motor 직접
        self.logs_collection = database.logs
    
    async def setup_indexes(self):
        # 수동 인덱스 생성
        await self.logs_collection.create_index([
            ("level", 1), ("service", 1), ("timestamp", -1)
        ])
```

#### 🌐 크로스 프로젝트 호환성
```python
# 설정 주입 패턴으로 다른 프로젝트에서 사용
from nadle_backend.core.logging import LoggingSystem

# 다른 프로젝트에서 사용 시
logging_system = LoggingSystem(
    database_adapter=MongoDBAdapter(database),
    cache_adapter=RedisAdapter(redis),
    config={
        "log_retention_days": 30,
        "batch_size": 100,
        "alert_channels": ["discord", "email"]
    }
)

# PostgreSQL 프로젝트에서 사용 시
class PostgreSQLAdapter(DatabaseAdapter):
    async def save_log(self, log_entry: LogEntry) -> None:
        # PostgreSQL 구현

logging_system = LoggingSystem(
    database_adapter=PostgreSQLAdapter(pg_connection)
)
```

---

## 🔌 외부 시스템 통합

### 1. 실제 API 응답 기반 구현

#### ✅ Vercel API (구현 완료)
**수집된 실제 응답 구조**:
```json
{
  "deployments": [
    {
      "uid": "dpl_GdJ1VgmkMpdyygKDADR3yNdqDHZm",
      "name": "xai-community", 
      "state": "READY|ERROR",
      "created": 1752821987235,
      "meta": {
        "githubCommitMessage": "실제 커밋 메시지",
        "githubCommitSha": "실제 SHA"
      }
    }
  ]
}
```

**이벤트 로그 구조**:
```json
{
  "type": "stdout|stderr",
  "created": 1752821987952,
  "payload": {
    "deploymentId": "dpl_xxx",
    "text": "실제 빌드 로그 메시지",
    "info": {
      "type": "build",
      "name": "bld_xxx"
    }
  }
}
```

#### ✅ Upstash Redis (구현 완료)
**수집된 실제 응답 구조**:
```json
{
  "result": "PONG"  // PING 명령
}

{
  "result": "# Server\\r\\nupstash_version:1.13.3\\r\\n..."  // INFO 명령
}

{
  "result": 15  // DBSIZE 명령
}
```

#### ⚠️ Google Cloud Run (API 오류 - Mock 구현 필요)
**예상 응답 구조** (Google Cloud Logging API 문서 기반):
```json
{
  "entries": [
    {
      "timestamp": "2025-07-19T02:00:00.000Z",
      "severity": "ERROR|INFO|WARNING",
      "resource": {
        "type": "cloud_run_revision",
        "labels": {
          "service_name": "xai-community-backend",
          "location": "asia-northeast3"
        }
      },
      "httpRequest": {
        "requestMethod": "POST",
        "requestUrl": "https://...",
        "status": 500,
        "latency": "30.125s"
      }
    }
  ]
}
```

#### ❌ MongoDB Atlas (인증 오류 - Mock 구현 필요)
**예상 응답 구조** (Atlas API 문서 기반):
```json
{
  "logs": [
    "{\"t\":{\"$date\":\"2025-07-19T02:00:00.000Z\"},\"s\":\"I\",\"c\":\"NETWORK\",\"msg\":\"Connection accepted\"}"
  ]
}

{
  "accessLogs": [
    {
      "authSource": "xai_community",
      "authResult": true,
      "hostname": "cluster0-shard-00-01.bh7mhfi.mongodb.net",
      "ipAddress": "203.0.113.1",
      "timestamp": "2025-07-19T02:00:00.000Z",
      "username": "app_user"
    }
  ]
}
```

### 2. 통합 로그 수집 플로우

```python
async def collect_all_external_logs(hours: int = 1) -> List[LogEntry]:
    """모든 외부 시스템 로그 수집"""
    
    log_entries = []
    
    # 1. Vercel 배포 로그 수집
    vercel_collector = VercelLogCollector(api_token, project_id)
    vercel_logs = await vercel_collector.collect_logs(hours)
    log_entries.extend(vercel_logs)
    
    # 2. Upstash Redis 메트릭 수집
    upstash_collector = UpstashRedisCollector(rest_url, rest_token)
    upstash_metrics = await upstash_collector.collect_metrics()
    log_entries.extend(upstash_metrics)
    
    # 3. Google Cloud Run 로그 수집
    cloudrun_collector = CloudRunLogCollector(project_id, credentials_path)
    cloudrun_logs = await cloudrun_collector.collect_logs(hours)
    log_entries.extend(cloudrun_logs)
    
    # 4. MongoDB Atlas 로그 수집
    atlas_collector = AtlasLogCollector(api_key, group_id, cluster_name)
    atlas_logs = await atlas_collector.collect_logs(hours)
    log_entries.extend(atlas_logs)
    
    return log_entries
```

---

## 🧪 TDD 구현 전략

### 1. 완성된 테스트 (7개 테스트 모두 통과)

#### Vercel 수집기 테스트
```python
✅ test_get_deployments_success        # 배포 목록 조회
✅ test_get_deployment_events_success  # 배포 이벤트 수집
✅ test_collect_logs_integration       # 통합 로그 수집
✅ test_api_error_handling            # 에러 처리 (401 등)
```

#### Upstash Redis 수집기 테스트  
```python
✅ test_ping_command                  # PING 명령 실행
✅ test_info_command                  # INFO 명령 및 파싱
✅ test_collect_metrics_integration   # 통합 메트릭 수집
```

### 2. 개발 순서 (Red-Green-Refactor)

```bash
# 1. Red: 실패하는 테스트 작성
pytest tests/unit/test_external_log_collectors.py::TestVercelLogCollector::test_get_deployments_success

# 2. Green: 최소한의 구현으로 테스트 통과
async def get_deployments(self, limit: int = 5) -> Dict[str, Any]:
    # 최소 구현

# 3. Refactor: 코드 개선 및 최적화
# 에러 처리, 타입 안전성, 성능 최적화 등
```

### 3. 빠른 피드백 루프

```bash
# 개발 중 빠른 단위 테스트 (< 5초)
uv run pytest tests/unit/test_external_log_collectors.py -v

# 특정 테스트만 실행
uv run pytest tests/unit/test_external_log_collectors.py::TestVercelLogCollector::test_ping_command -v

# 커버리지 포함 전체 테스트
uv run pytest tests/ --cov=nadle_backend.logging --cov-report=html
```

---

## 📊 데이터 모델 및 API

### 1. 핵심 로그 엔트리 모델

```python
class LogEntry(BaseModel):
    """통합 로그 엔트리 (모든 외부 시스템 공통)"""
    id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: Literal["ERROR", "WARN", "INFO", "DEBUG"]
    service: Literal["api", "web", "cloud-run", "database", "redis", "vercel"]
    source: Literal["internal", "external"]
    message: str
    context: Optional[LogContext] = None
    metadata: Optional[LogMetadata] = None
    stack_trace: Optional[str] = None

class LogContext(BaseModel):
    """로그 컨텍스트 정보"""
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    deployment_id: Optional[str] = None  # Vercel
    instance_id: Optional[str] = None    # Cloud Run
    cluster_name: Optional[str] = None   # Atlas

class LogMetadata(BaseModel):
    """인프라별 메타데이터"""
    infrastructure: Optional[str] = None  # "vercel", "gcp", "atlas"
    deployment_url: Optional[str] = None
    cloud_trace_id: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
```

### 2. REST API 엔드포인트

```python
# 로그 검색
GET /api/v1/logs/search
Query Parameters:
- levels: List[str] = ["ERROR", "WARN"]
- services: List[str] = ["vercel", "cloud-run"]
- sources: List[str] = ["external"]
- start_time: datetime
- end_time: datetime
- search_query: str
- page: int = 1
- page_size: int = 50

# 로그 통계
GET /api/v1/logs/stats?hours=24
Response:
{
  "stats": {
    "total_count": 1500,
    "error_count": 45,
    "warn_count": 120,
    "info_count": 1200,
    "debug_count": 135
  },
  "service_stats": {
    "vercel": 300,
    "cloud-run": 800,
    "database": 400
  }
}

# 대시보드 데이터
GET /api/v1/logs/dashboard?hours=24
Response:
{
  "stats": {...},
  "recent_errors": [...],
  "time_series": [...],
  "top_endpoints": [...]
}

# 외부 로그 수집 실행
POST /api/v1/logs/collect
Body: { "hours": 1 }
Response:
{
  "message": "Collected 1,234 external logs",
  "errors": [],
  "status": "success"
}
```

---

## 🚀 구현 로드맵

### Phase 1: 핵심 기반 구조 (1일)
```bash
✅ 실제 API 응답 탐색 스크립트 구현
✅ Vercel, Upstash 실제 응답 수집 완료
✅ 정확한 Mock 데이터 생성 완료
✅ TDD 테스트 케이스 7개 작성 및 통과
```

### Phase 2: Cloud Run, Atlas Mock 구현 (0.5일)
```bash
🔄 Cloud Run API 오류 기반 Mock 데이터 생성
🔄 Atlas 인증 오류 기반 Mock 데이터 생성  
🔄 해당 수집기들의 TDD 테스트 작성
```

### Phase 3: 로깅 시스템 구현 (1.5일)
```bash
📋 LogEntry 모델 및 LogRepository 구현
📋 LogService 비즈니스 로직 구현
📋 외부 수집기들 통합
📋 REST API 엔드포인트 구현
```

### Phase 4: 프론트엔드 통합 (0.5일)
```bash
📋 기존 React 컴포넌트와 API 연동
📋 로깅 페이지에 외부 인프라 필터 추가
📋 실시간 로그 스트리밍 테스트
```

### Phase 5: 배포 및 모니터링 (0.5일)
```bash
📋 프로덕션 환경 배포
📋 실제 외부 시스템 연동 테스트
📋 성능 모니터링 및 최적화
```

---

## 🔧 기술적 세부사항

### 1. MongoDB 네이티브 인덱싱
```python
# Beanie 우회를 위한 수동 인덱스 생성
await logs_collection.create_index([
    ("timestamp", DESCENDING),     # 시간 순 정렬
    ("level", ASCENDING),          # 레벨별 필터링
    ("service", ASCENDING),        # 서비스별 필터링  
    ("source", ASCENDING)          # 소스별 필터링
])

# 복합 인덱스로 복잡한 쿼리 최적화
await logs_collection.create_index([
    ("level", ASCENDING),
    ("service", ASCENDING), 
    ("timestamp", DESCENDING)
])

# 텍스트 검색을 위한 인덱스
await logs_collection.create_index([("message", "text")])
```

### 2. 비동기 배치 처리
```python
async def save_logs_batch(self, log_entries: List[LogEntry]) -> List[LogEntry]:
    """성능 최적화를 위한 배치 저장"""
    docs = [entry.model_dump(exclude={"id"}) for entry in log_entries]
    result = await self.logs_collection.insert_many(docs)
    
    for i, inserted_id in enumerate(result.inserted_ids):
        log_entries[i].id = str(inserted_id)
    
    return log_entries
```

### 3. Redis 캐싱 전략
```python
# 하이브리드 Redis 시스템 활용
class LogService:
    async def search_logs(self, filter_obj: LogFilter) -> Dict[str, Any]:
        # 캐시 키 생성
        cache_key = f"logs:search:{hash(str(filter_obj.model_dump()))}"
        
        if self.cache_service:
            cached = await self.cache_service.get(cache_key)
            if cached:
                return cached
        
        # DB 조회 및 캐싱
        result = await self._db_search(filter_obj)
        await self.cache_service.set(cache_key, result, expire=300)
        return result
```

---

## 📈 성능 및 확장성

### 1. 예상 성능 지표
- **로그 수집 속도**: 1,000개/분 (외부 API 제한에 따라)
- **검색 응답 시간**: < 100ms (인덱스 및 캐싱 활용)
- **동시 접속**: 100명 (FastAPI async 처리)
- **저장 용량**: 1GB/월 (텍스트 로그 기준)

### 2. 확장성 고려사항
```python
# 로그 보존 정책
class LogRetentionPolicy:
    def __init__(self):
        self.policies = {
            "ERROR": timedelta(days=90),    # 에러 로그 90일
            "WARN": timedelta(days=30),     # 경고 로그 30일  
            "INFO": timedelta(days=7),      # 정보 로그 7일
            "DEBUG": timedelta(days=1)      # 디버그 로그 1일
        }
    
    async def cleanup_old_logs(self):
        """자동 로그 정리"""
        for level, retention in self.policies.items():
            cutoff_date = datetime.utcnow() - retention
            await self.log_repository.delete_logs_before(level, cutoff_date)
```

### 3. 모니터링 및 알림
```python
# Discord 알림 통합
class LogAlertService:
    async def check_error_threshold(self):
        """에러 임계치 초과 시 알림"""
        error_count = await self.get_recent_error_count(minutes=5)
        if error_count > 10:  # 5분간 10개 이상 에러
            await self.send_discord_alert(
                f"🚨 높은 에러율 감지: {error_count}개 에러 발생"
            )
```

---

## 🎯 기대 효과

### 1. 개발 효율성
- **통합 로깅**: 모든 인프라 로그를 한 곳에서 조회
- **빠른 디버깅**: 에러 발생 시 관련 외부 시스템 로그 즉시 확인
- **자동 알림**: 임계치 초과 시 Discord 자동 알림

### 2. 운영 안정성  
- **TDD 기반**: 견고한 테스트로 안정성 보장
- **점진적 배포**: 단계별 구현으로 리스크 최소화
- **실시간 모니터링**: 시스템 상태 실시간 파악

### 3. 확장성
- **다중 프로젝트**: 설정 주입으로 다른 프로젝트에서도 사용
- **새로운 인프라**: 어댑터 패턴으로 쉬운 확장
- **표준화**: OpenTelemetry 호환 구조

---

## 📝 결론

본 로깅 시스템은 **실제 API 응답 기반의 정확한 Mock 데이터**와 **검증된 TDD 테스트**를 토대로 설계되었습니다. Vercel과 Upstash의 실제 연동을 성공적으로 완료했으며, Cloud Run과 Atlas는 API 문제로 인해 Mock 기반으로 구현할 예정입니다.

**현업에서 사용하는 DDD + TDD 패턴**을 적용하여 안전하고 확장 가능한 시스템을 구축할 수 있는 견고한 기반을 마련했습니다. 다음 단계에서는 실패한 API들의 Mock 구현과 실제 로깅 시스템 구축을 진행할 예정입니다.

---

**문서 버전**: v1.0  
**마지막 업데이트**: 2025-07-19  
**관련 파일**: 
- `/backend/tests/fixtures/external_api_mocks.py`
- `/backend/tests/unit/test_external_log_collectors.py`
- `/backend/tests/integration/discover_api_responses.py`