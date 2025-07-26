실제 API 중지 구현 계획                                                         │ │
│ │                                                                                 │ │
│ │ 🎯 목표                                                                         │ │
│ │                                                                                 │ │
│ │ 기존 시뮬레이션 방식을 실제 API 중지 방식으로 변경하여 Sentry가 실제 에러를     │ │
│ │ 포착할 수 있도록 구현                                                           │ │
│ │                                                                                 │ │
│ │ 📋 구현 계획                                                                    │ │
│ │                                                                                 │ │
│ │ 1단계: 엔드포인트 제어 서비스 생성                                              │ │
│ │                                                                                 │ │
│ │ - 파일: backend/nadle_backend/services/endpoint_control_service.py (신규 생성)  │ │
│ │ - 기능:                                                                         │ │
│ │   - 중지된 엔드포인트를 메모리에서 관리하는 싱글톤 서비스                       │ │
│ │   - 개발/테스트 환경에서만 작동                                                 │ │
│ │   - 엔드포인트별 중지/활성화 기능                                               │ │
│ │                                                                                 │ │
│ │ 2단계: 데코레이터 구현                                                          │ │
│ │                                                                                 │ │
│ │ - 기능: 각 엔드포인트에 쉽게 적용할 수 있는 데코레이터                          │ │
│ │ - 동작: 중지된 엔드포인트 호출 시 HTTPException(503) 발생 → Sentry 포착         │ │
│ │                                                                                 │ │
│ │ 3단계: 기존 엔드포인트에 데코레이터 적용                                        │ │
│ │                                                                                 │ │
│ │ - 대상 파일들:                                                                  │ │
│ │   - backend/nadle_backend/routers/health.py - /api/health, /api/auth/health,    │ │
│ │ /api/posts/health, /api/comments/health                                         │ │
│ │   - backend/nadle_backend/routers/posts.py - /api/posts (목록 조회)             │ │
│ │ - 변경: 각 엔드포인트 함수에 @endpoint_control_check 데코레이터 추가            │ │
│ │                                                                                 │ │
│ │ 4단계: 제어 API 엔드포인트 추가                                                 │ │
│ │                                                                                 │ │
│ │ - 파일: backend/nadle_backend/routers/monitoring.py                             │ │
│ │ - 새 엔드포인트들:                                                              │ │
│ │   - POST /api/monitoring/test/endpoint/disable - 특정 엔드포인트 중지           │ │
│ │   - POST /api/monitoring/test/endpoint/enable - 특정 엔드포인트 활성화          │ │
│ │   - GET /api/monitoring/test/endpoint/status - 중지된 엔드포인트 목록 조회      │ │
│ │ - 보안: 프로덕션 환경에서는 403 에러 반환                                       │ │
│ │                                                                                 │ │
│ │ 5단계: 프론트엔드 연동 수정                                                     │ │
│ │                                                                                 │ │
│ │ - 파일: frontend/app/components/monitoring/LayeredMonitoring.tsx                │ │
│ │ - 변경사항:                                                                     │ │
│ │   - toggleEndpointStatus 함수를 실제 API 호출로 변경                            │ │
│ │   - toggleServerStatus 함수를 새로운 방식으로 통합                              │ │
│ │   - 에러 처리 및 로딩 상태 관리 추가                                            │ │
│ │                                                                                 │ │
│ │ 6단계: 기존 테스트 모드 코드 정리                                               │ │
│ │                                                                                 │ │
│ │ - 파일: backend/nadle_backend/routers/monitoring.py                             │ │
│ │ - 제거 대상:                                                                    │ │
│ │   - TEST_MODE_ENABLED, TEST_SERVER_STATUS 전역 변수                             │ │
│ │   - /test/server/toggle, /test/server/reset 엔드포인트                          │ │
│ │   - 관련 테스트 모드 로직                                                       │ │
│ │                                                                                 │ │
│ │ 🔍 기대 효과                                                                    │ │
│ │                                                                                 │ │
│ │ Sentry 포착 시나리오:                                                           │ │
│ │                                                                                 │ │
│ │ 1. 프론트엔드에서 중지 버튼 클릭                                                │ │
│ │ 2. 백엔드에서 해당 엔드포인트 비활성화                                          │ │
│ │ 3. 모니터링 시스템이 해당 엔드포인트 호출                                       │ │
│ │ 4. HTTPException(503) 발생                                                      │ │
│ │ 5. Sentry가 실제 서버 에러 포착 ✅                                               │ │
│ │                                                                                 │ │
│ │ 개선사항:                                                                       │ │
│ │                                                                                 │ │
│ │ - 시뮬레이션이 아닌 실제 API 에러 발생                                          │ │
│ │ - 개발 환경에서만 작동하는 안전한 구조                                          │ │
│ │ - 즉시 복구 가능한 제어 시스템                                                  │ │
│ │ - 일관된 방식의 전체 서버/개별 엔드포인트 제어                                  │ │
│ │                                                                                 │ │
│ │ 🚀 구현 순서                                                                    │ │
│ │                                                                                 │ │
│ │ 1. 백엔드 서비스 및 데코레이터 구현                                             │ │
│ │ 2. 기존 엔드포인트에 데코레이터 적용                                            │ │
│ │ 3. 제어 API 엔드포인트 추가                                                     │ │
│ │ 4. 프론트엔드 연동 수정                                                         │ │
│ │ 5. 기존 테스트 모드 코드 정리                                                   │ │
│ │ 6. 테스트 및 검증