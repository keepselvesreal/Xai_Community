환경별 모니터링 시스템 구현 최종 계획 (수정됨)                                                                │ │
│ │                                                                                                               │ │
│ │ 📊 현재 상황 분석 (업데이트됨)                                                                                │ │
│ │                                                                                                               │ │
│ │ - 데이터베이스: 모든 환경에서 Atlas MongoDB 사용 (개발/스테이징/프로덕션)                                     │ │
│ │ - Sentry: 모든 환경에서 사용, 환경별 구분 (development/staging/production)                                    │ │
│ │ - UptimeRobot: 모든 환경에서 동일한 API 키 사용 (환경 구분 없음)                                              │ │
│ │ - Discord 웹훅: 모든 환경에서 동일한 웹훅 URL 사용 (환경 구분 없음)                                           │ │
│ │ - 프론트엔드: 완전한 모니터링 대시보드 구현 완료                                                              │ │
│ │ - 백엔드: 모니터링 인프라 구현, API 라우터 누락                                                               │ │
│ │ - 스테이징: GitHub Secrets 사용 (별도 .env 파일 불필요)                                                       │ │
│ │                                                                                                               │ │
│ │ 🎯 구현 목표                                                                                                  │ │
│ │                                                                                                               │ │
│ │ 환경별 모니터링 버튼을 통해 각 환경의 도구와 지표를 분리하여 표시하고, UptimeRobot과 Discord 웹훅의 환경별    │ │
│ │ 구분 구현                                                                                                     │ │
│ │                                                                                                               │ │
│ │ 📋 상세 구현 계획                                                                                             │ │
│ │                                                                                                               │ │
│ │ 1단계: 백엔드 모니터링 API 라우터 구현                                                                        │ │
│ │                                                                                                               │ │
│ │ - backend/nadle_backend/routers/monitoring.py 생성                                                            │ │
│ │ - 프론트엔드가 호출하는 /api/internal/* 엔드포인트 구현                                                       │ │
│ │ - 환경별 데이터 분리 로직 구현                                                                                │ │
│ │                                                                                                               │ │
│ │ 2단계: 환경별 외부 서비스 구분 구현                                                                           │ │
│ │                                                                                                               │ │
│ │ UptimeRobot 환경 구분                                                                                         │ │
│ │                                                                                                               │ │
│ │ - config.py에 환경별 UptimeRobot 설정 추가:                                                                   │ │
│ │   - UPTIMEROBOT_API_KEY_DEV                                                                                   │ │
│ │   - UPTIMEROBOT_API_KEY_STAGING                                                                               │ │
│ │   - UPTIMEROBOT_API_KEY_PROD                                                                                  │ │
│ │ - 환경별 UptimeRobot API 키 선택 로직 구현                                                                    │ │
│ │                                                                                                               │ │
│ │ Discord 웹훅 환경 구분                                                                                        │ │
│ │                                                                                                               │ │
│ │ - config.py에 환경별 Discord 웹훅 설정 추가:                                                                  │ │
│ │   - DISCORD_WEBHOOK_URL_DEV                                                                                   │ │
│ │   - DISCORD_WEBHOOK_URL_STAGING                                                                               │ │
│ │   - DISCORD_WEBHOOK_URL_PROD                                                                                  │ │
│ │ - 환경별 Discord 웹훅 URL 선택 로직 구현                                                                      │ │
│ │                                                                                                               │ │
│ │ 3단계: 프론트엔드 환경 선택 기능 추가                                                                         │ │
│ │                                                                                                               │ │
│ │ - 모니터링 대시보드에 환경 선택 버튼 추가                                                                     │ │
│ │ - 환경별 API 엔드포인트 동적 설정                                                                             │ │
│ │ - 환경별 표시 정보 구분:                                                                                      │ │
│ │   - Development: 로컬 Redis (dev: 프리픽스)                                                                   │ │
│ │   - Staging: Upstash Redis (stage: 프리픽스)                                                                  │ │
│ │   - Production: Upstash Redis (prod: 프리픽스)                                                                │ │
│ │                                                                                                               │ │
│ │ 4단계: 환경별 모니터링 데이터 표시 개선                                                                       │ │
│ │                                                                                                               │ │
│ │ - 환경별 Redis 타입 및 키 프리픽스 표시                                                                       │ │
│ │ - 환경별 Sentry 구분 표시                                                                                     │ │
│ │ - 환경별 UptimeRobot 모니터링 상태 표시                                                                       │ │
│ │ - 환경별 Discord 알림 채널 표시                                                                               │ │
│ │                                                                                                               │ │
│ │ 5단계: 환경별 설정 파일 업데이트                                                                              │ │
│ │                                                                                                               │ │
│ │ - .env.dev에 개발용 외부 서비스 설정 추가                                                                     │ │
│ │ - .env.prod에 프로덕션용 외부 서비스 설정 추가                                                                │ │
│ │ - GitHub Secrets에 스테이징용 외부 서비스 설정 추가                                                           │ │
│ │                                                                                                               │ │
│ │ 🔧 핵심 작업 요약                                                                                             │ │
│ │                                                                                                               │ │
│ │ 1. 백엔드 모니터링 API 라우터 구현 (최우선)                                                                   │ │
│ │ 2. UptimeRobot 환경별 구분 구현                                                                               │ │
│ │ 3. Discord 웹훅 환경별 구분 구현                                                                              │ │
│ │ 4. 프론트엔드 환경 선택 UI 추가                                                                               │ │
│ │ 5. 환경별 모니터링 데이터 표시 개선                                                                           │ │
│ │                                                                                                               │ │
│ │ 이 계획은 기존 아키텍처를 유지하면서 환경별 모니터링을 구현하고, 외부 서비스(UptimeRobot, Discord)의 환경별   │ │
│ │ 구분을 추가하여 각 환경의 독립적인 모니터링을 가능하게 합니다.