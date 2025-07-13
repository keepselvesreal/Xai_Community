slowapi 활용 Redis 기반 분산 Rate Limiting TDD 구현 계획                                      │ │
│ │                                                                                               │ │
│ │ 🔍 현재 상태 분석                                                                             │ │
│ │                                                                                               │ │
│ │ - ✅ Redis 인프라: 기존 RedisManager 활용 가능                                                 │ │
│ │ - ✅ 테스트 인프라: 포괄적인 테스트 구조 (unit/integration/e2e/performance)                    │ │
│ │ - ❌ Rate Limiting: 현재 미구현                                                                │ │
│ │ - ❌ slowapi: 패키지 미설치                                                                    │ │
│ │                                                                                               │ │
│ │ 📋 TDD 기반 구현 단계                                                                         │ │
│ │                                                                                               │ │
│ │ 1단계: 의존성 및 기본 구조 설정                                                               │ │
│ │                                                                                               │ │
│ │ - slowapi 패키지 추가 (pyproject.toml)                                                        │ │
│ │ - Rate limiting 설정 모델 생성                                                                │ │
│ │ - 기본 rate limiter 클래스 구조 설계                                                          │ │
│ │                                                                                               │ │
│ │ 2단계: 핵심 테스트 작성 (TDD)                                                                 │ │
│ │                                                                                               │ │
│ │ - Unit Tests: Rate limiter 로직 테스트                                                        │ │
│ │ - Integration Tests: Redis 연동 테스트                                                        │ │
│ │ - API Tests: 엔드포인트별 rate limiting 테스트                                                │ │
│ │ - Performance Tests: 부하 상황 테스트                                                         │ │
│ │                                                                                               │ │
│ │ 3단계: Rate Limiting 구현                                                                     │ │
│ │                                                                                               │ │
│ │ - RedisManager 확장 (rate limiting 전용 메서드)                                               │ │
│ │ - slowapi 기반 rate limiter 구현                                                              │ │
│ │ - 설정된 RATE_LIMITS 적용                                                                     │ │
│ │                                                                                               │ │
│ │ 4단계: API 라우터 통합                                                                        │ │
│ │                                                                                               │ │
│ │ - 인증 라우터 (auth): 3/minute                                                                │ │
│ │ - 게시글 라우터 (posts): 5/minute                                                             │ │
│ │ - 댓글 라우터 (comments): 10/minute                                                           │ │
│ │ - 파일 업로드 (files): 3/minute                                                               │ │
│ │ - 기타 제한사항 적용                                                                          │ │
│ │                                                                                               │ │
│ │ 5단계: 실제 시스템 통합 테스트                                                                │ │
│ │                                                                                               │ │
│ │ - Redis 실제 연결 테스트                                                                      │ │
│ │ - 분산 환경 동작 확인                                                                         │ │
│ │ - 성능 벤치마크 측정                                                                          │ │
│ │ - 오류 상황 처리 검증                                                                         │ │
│ │                                                                                               │ │
│ │ 6단계: 모니터링 및 로깅                                                                       │ │
│ │                                                                                               │ │
│ │ - Rate limiting 메트릭 수집                                                                   │ │
│ │ - 제한 초과 로그 기록                                                                         │ │
│ │ - 관리자 알림 시스템 연동                                                                     │ │
│ │                                                                                               │ │
│ │ 🧪 테스트 전략                                                                                │ │
│ │                                                                                               │ │
│ │ Unit Tests (tests/unit/test_rate_limiter.py)                                                  │ │
│ │                                                                                               │ │
│ │ - Rate limiter 클래스 로직                                                                    │ │
│ │ - 설정 파싱 및 검증                                                                           │ │
│ │ - 시간 윈도우 계산                                                                            │ │
│ │                                                                                               │ │
│ │ Integration Tests (tests/integration/test_rate_limiting_redis.py)                             │ │
│ │                                                                                               │ │
│ │ - Redis 연동 테스트                                                                           │ │
│ │ - 분산 카운터 동작                                                                            │ │
│ │ - 캐시 만료 처리                                                                              │ │
│ │                                                                                               │ │
│ │ API Tests (tests/integration/test_rate_limiting_api.py)                                       │ │
│ │                                                                                               │ │
│ │ - 각 엔드포인트별 제한 테스트                                                                 │ │
│ │ - 헤더 응답 검증                                                                              │ │
│ │ - 초과 시 429 응답 확인                                                                       │ │
│ │                                                                                               │ │
│ │ Performance Tests (tests/performance/test_rate_limiting_performance.py)                       │ │
│ │                                                                                               │ │
│ │ - 동시 요청 처리 성능                                                                         │ │
│ │ - Redis 부하 측정                                                                             │ │
│ │ - 응답 시간 영향 분석                                                                         │ │
│ │                                                                                               │ │
│ │ 🔧 기술 세부사항                                                                              │ │
│ │                                                                                               │ │
│ │ slowapi 설정                                                                                  │ │
│ │                                                                                               │ │
│ │ from slowapi import Limiter, _rate_limit_exceeded_handler                                     │ │
│ │ from slowapi.util import get_remote_address                                                   │ │
│ │ from slowapi.errors import RateLimitExceeded                                                  │ │
│ │                                                                                               │ │
│ │ limiter = Limiter(                                                                            │ │
│ │     key_func=get_remote_address,                                                              │ │
│ │     storage_uri="redis://localhost:6379"                                                      │ │
│ │ )                                                                                             │ │
│ │                                                                                               │ │
│ │ Rate Limiting 적용 패턴                                                                       │ │
│ │                                                                                               │ │
│ │ @limiter.limit("3/minute")                                                                    │ │
│ │ async def login_endpoint():                                                                   │ │
│ │     # 로그인 로직                                                                             │ │
│ │                                                                                               │ │
│ │ Redis 키 패턴                                                                                 │ │
│ │                                                                                               │ │
│ │ - rate_limit:auth:{ip}:{minute}                                                               │ │
│ │ - rate_limit:posts:{user_id}:{minute}                                                         │ │
│ │ - rate_limit:files:{ip}:{minute}                                                              │ │
│ │                                                                                               │ │
│ │ ✅ 검증 기준                                                                                   │ │
│ │                                                                                               │ │
│ │ 1. 모든 테스트 통과 (coverage > 90%)                                                          │ │
│ │ 2. Redis 실제 연결 동작 확인                                                                  │ │
│ │ 3. 동시 요청 1000개 처리 성능 테스트                                                          │ │
│ │ 4. 분산 환경에서 정확한 제한 적용                                                             │ │
│ │ 5. 오류 상황 복구 메커니즘 동작                                                               │ │
│ │                                                                                               │ │
│ │ 이 계획으로 진행하면 안전하고 확장 가능한 rate limiting 시스템을 구축할 수 있을 것 같아! 