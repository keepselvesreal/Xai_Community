# Sentry 모니터링 상세 분석

작성일: 2025-07-19  
분석 범위: 백엔드 + 프론트엔드 Sentry 통합  

## 1. 백엔드 Sentry 구현

### 1.1 설정 관리 (`nadle_backend/monitoring/sentry_config.py`)

#### 주요 기능
```python
# 실제 추적하는 설정들
- dsn: Sentry DSN (환경변수에서 로드)
- environment: 환경 설정 (development/staging/production)
- traces_sample_rate: 성능 추적 샘플링 비율 (기본 1.0)
- send_default_pii: 개인정보 전송 여부 (기본 true)
- debug: 디버그 모드 (개발 환경에서만)
```

#### 통합 서비스
```python
# 실제 로드된 통합들
- FastApiIntegration(): FastAPI 요청/응답 자동 추적
- AsyncioIntegration(): 비동기 작업 추적
```

#### 필터링 로직
```python
# 실제 필터링되는 에러들
- HTTPException (404, 403)
- ChunkLoadError
- ResizeObserver errors
```

### 1.2 서비스 계층 (`nadle_backend/services/sentry_monitoring_service.py`)

#### 실제 수집하는 에러 통계
```python
class SentryErrorStats:
    last_hour_errors: int        # 최근 1시간 에러 수
    last_24h_errors: int         # 최근 24시간 에러 수  
    last_3d_errors: int          # 최근 3일 에러 수
    error_rate_per_hour: float   # 시간당 에러 비율
    status: str                  # healthy/warning/critical/unconfigured/error/no_data
    last_error_time: str         # 마지막 에러 발생 시간
    environment: str             # 현재 환경
    total_events: int            # 총 이벤트 수
    recent_errors: List[SentryErrorInfo]  # 최근 에러 목록
```

#### 에러 정보 상세
```python
class SentryErrorInfo:
    message: str                 # 에러 메시지
    timestamp: str              # 발생 시간
    error_type: str             # 에러 타입
    file_path: str              # 파일 경로
    line_number: int            # 라인 번호
```

#### 현재 한계점
- ❌ **Sentry Web API 미연동**: 실제 에러 데이터를 가져올 수 없음
- ❌ **Mock 데이터**: 현재는 상태만 확인 가능
- ❌ **실시간 통계**: 실제 에러 트렌드 분석 불가

### 1.3 미들웨어 (`nadle_backend/middleware/sentry_middleware.py`)

#### 요청 컨텍스트 추적
```python
# 실제 수집하는 요청 정보
- method: HTTP 메서드
- url: 요청 URL
- headers: 요청 헤더
- client_ip: 클라이언트 IP
- request_id: 요청 ID (X-Request-ID 헤더)
- duration: 요청 처리 시간
- status_code: 응답 상태 코드
```

#### 사용자 식별 자동화
```python
# JWT 토큰에서 자동 추출하는 정보
- user_id: 사용자 ID (sub 또는 user_id 클레임)
- email: 사용자 이메일
```

#### 성능 추적 데코레이터
```python
@track_performance("operation_name")
async def some_function():
    # 자동으로 시간 측정 및 Sentry에 전송
    pass
```

## 2. 프론트엔드 Sentry 구현

### 2.1 서비스 (`frontend/app/lib/sentry-service.ts`)

#### 환경별 설정
```typescript
// 실제 환경 감지 및 설정
- measurementId: 환경별 자동 선택
- environment: development/staging/production
- tracesSampleRate: 성능 추적 샘플링
- sendDefaultPii: PII 전송 설정
- debug: 디버그 모드 (개발환경)
```

#### 자동 사용자 추적
```typescript
// 로그인 시 자동 설정되는 정보
interface UserContext {
    id: string;
    email?: string;
    username?: string;
    [key: string]: any;
}
```

#### 에러 컨텍스트 수집
```typescript
interface ErrorContext {
    component?: string;      // React 컴포넌트 이름
    action?: string;         // 사용자 액션
    url?: string;           // 현재 URL
    userId?: string;        // 사용자 ID
    sessionId?: string;     // 세션 ID
    additionalData?: Record<string, any>;
}
```

### 2.2 에러 바운더리 (`frontend/app/components/common/ErrorBoundary.tsx`)

#### 자동 수집하는 React 에러
```typescript
// 실제 캡처되는 에러 정보
- error.message: 에러 메시지
- error.stack: 스택 트레이스
- errorInfo.componentStack: React 컴포넌트 스택
- 에러 발생 시간
- 현재 URL
- 사용자 정보 (로그인된 경우)
```

#### 특별 처리 로직
```typescript
// AuthContext 에러 자동 복구
if (error.message.includes('useAuth must be used within an AuthProvider')) {
    // 100ms 후 자동 복구 시도
    setTimeout(() => this.resetError(), 100);
}
```

### 2.3 전역 노출 (`window` 객체)

#### 디버깅용 전역 접근
```typescript
// 브라우저 콘솔에서 접근 가능
window.Sentry          // Sentry SDK
window.SentryClient     // Sentry 클라이언트
window.SentryCurrentScope // 현재 스코프
```

## 3. 실제 수집되는 데이터 유형

### 3.1 에러 이벤트
```json
{
  "event_id": "unique-id",
  "timestamp": "2025-07-19T10:00:00Z",
  "level": "error",
  "environment": "production",
  "user": {
    "id": "user123",
    "email": "user@example.com"
  },
  "exception": {
    "type": "TypeError",
    "value": "Cannot read property 'x' of undefined",
    "stacktrace": {
      "frames": [...]
    }
  },
  "request": {
    "method": "POST",
    "url": "/api/posts",
    "headers": {...}
  },
  "tags": {
    "component": "PostCreation",
    "environment": "production"
  }
}
```

### 3.2 성능 이벤트 (트랜잭션)
```json
{
  "type": "transaction",
  "transaction": "POST /api/posts",
  "start_timestamp": 1234567890.123,
  "timestamp": 1234567890.456,
  "contexts": {
    "trace": {
      "trace_id": "trace-id",
      "span_id": "span-id"
    }
  },
  "spans": [
    {
      "op": "db.query",
      "description": "INSERT INTO posts",
      "start_timestamp": 1234567890.200,
      "timestamp": 1234567890.300
    }
  ]
}
```

### 3.3 브레드크럼 (사용자 행동)
```json
{
  "breadcrumbs": [
    {
      "timestamp": "2025-07-19T10:00:00Z",
      "category": "navigation",
      "message": "User navigated to /posts/create",
      "level": "info"
    },
    {
      "timestamp": "2025-07-19T10:00:05Z", 
      "category": "ui.click",
      "message": "User clicked submit button",
      "level": "info"
    }
  ]
}
```

## 4. 현재 누락된 기능 및 데이터

### 4.1 백엔드 누락 기능
- ❌ **Sentry Web API**: 실제 통계 조회 불가
- ❌ **Release 추적**: 배포별 에러 분석 부족
- ❌ **커스텀 메트릭**: 비즈니스 메트릭 수집 부족
- ❌ **Alert 연동**: Sentry 알림과 자체 알림 시스템 연동 부족

### 4.2 프론트엔드 누락 기능
- ❌ **Release Health**: 크래시 무료 세션 추적 부족
- ❌ **Web Vitals**: Core Web Vitals 성능 지표 미수집
- ❌ **User Feedback**: 사용자 피드백 위젯 부족
- ❌ **Source Maps**: 프로덕션 소스맵 업로드 자동화 부족

### 4.3 통합 누락 기능
- ❌ **팀 알림**: Slack/Teams 통합 부족
- ❌ **대시보드**: 커스텀 Sentry 대시보드 부족
- ❌ **데이터 보존**: 장기 데이터 보존 정책 부족

## 5. 개선 제안

### 5.1 Sentry Web API 통합 (우선순위: 높음)
```python
# 구현 예시
async def get_real_error_stats(project_id: str, auth_token: str):
    """실제 Sentry API를 통한 에러 통계 조회"""
    url = f"https://sentry.io/api/0/projects/{org_slug}/{project_slug}/stats/"
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 실제 API 호출로 변경
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()
```

### 5.2 Release Health 구현 (우선순위: 중간)
```typescript
// 프론트엔드 Release Health 추적
Sentry.init({
  release: `frontend@${process.env.VERCEL_GIT_COMMIT_SHA}`,
  autoSessionTracking: true, // 이미 구현됨
  beforeSendTransaction(event) {
    // Web Vitals 수집 추가
    return event;
  }
});
```

### 5.3 Web Vitals 수집 (우선순위: 중간)
```typescript
// Web Vitals 자동 수집
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToSentry(metric) {
  Sentry.addBreadcrumb({
    category: 'web-vitals',
    message: `${metric.name}: ${metric.value}`,
    level: 'info',
    data: metric
  });
}

getCLS(sendToSentry);
getFID(sendToSentry);
getFCP(sendToSentry);
getLCP(sendToSentry);
getTTFB(sendToSentry);
```

### 5.4 커스텀 대시보드 (우선순위: 낮음)
```typescript
// React 컴포넌트로 Sentry 데이터 시각화
function SentryDashboard() {
  const [errorStats, setErrorStats] = useState();
  
  useEffect(() => {
    // Sentry API를 통한 실제 데이터 조회
    fetchSentryStats().then(setErrorStats);
  }, []);
  
  return (
    <div>
      <ErrorChart data={errorStats} />
      <PerformanceChart data={errorStats} />
    </div>
  );
}
```

## 6. 결론

현재 Sentry 구현은 **기본적인 에러 추적과 성능 모니터링**은 잘 되어 있으나, **실제 데이터 조회와 고급 분석 기능**이 부족합니다.

**즉시 개선이 필요한 부분:**
1. Sentry Web API 통합으로 실제 에러 통계 조회
2. Release Health 및 Web Vitals 수집
3. 커스텀 대시보드 개발

**현재 시스템의 장점:**
- 포괄적인 에러 캡처
- 환경별 독립적인 모니터링
- 자동화된 사용자/요청 컨텍스트 수집
- 지능적인 에러 필터링

이러한 개선사항들을 구현하면 **production-grade 에러 모니터링 시스템**이 완성될 것입니다.