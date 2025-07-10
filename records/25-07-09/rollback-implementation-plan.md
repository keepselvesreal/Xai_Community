# 버전 확인 기능을 포함한 Rollback 스크립트 구현 계획

## 1. 버전 추적 시스템 구축

### 백엔드 버전 추적
- `/version` API 엔드포인트 추가 (commit hash, build time, version)
- 배포 스크립트에서 Git 정보를 환경변수로 주입
- Cloud Run 리비전 메타데이터에 버전 정보 저장

### 프론트엔드 버전 추적
- `/version` 페이지 생성 (Vercel 환경변수 활용)
- HTML 메타태그에 빌드 정보 포함
- package.json 버전과 Git 커밋 해시 연동

## 2. 백엔드 Cloud Run Rollback 스크립트
- `rollback-backend.sh` 생성
- 현재 활성 리비전 확인 및 이전 리비전 식별
- 트래픽 전환 후 `/version` API로 롤백 검증
- 환경변수 백업/복구 기능

## 3. 프론트엔드 Vercel Rollback 스크립트
- `rollback-frontend.sh` 생성
- Vercel CLI로 이전 배포 복원
- `/version` 페이지로 롤백 검증
- 환경변수 동기화

## 4. 통합 Rollback 스크립트
- `rollback-full.sh` 생성
- 백엔드와 프론트엔드 순차 롤백
- 각 단계별 버전 확인 및 검증
- 롤백 전후 버전 비교 로그

## 5. 자동화된 검증 스크립트
- `verify-rollback.sh` 생성
- API 응답으로 백엔드 버전 확인
- 프론트엔드 페이지로 빌드 정보 확인
- 예상 이전 버전과 비교 검증

## 6. CI/CD 통합
- 배포 시 버전 정보 자동 주입
- GitHub Actions에 rollback job 추가
- 자동 헬스체크 실패 시 rollback 트리거
- 수동 rollback 워크플로우

## 7. 모니터링 및 알림
- 롤백 성공/실패 알림
- 버전 불일치 감지 및 경고
- 로그 수집 및 분석 개선

각 스크립트는 명확한 버전 확인 메커니즘을 포함하여 롤백이 정상적으로 수행되었는지 확실하게 검증할 수 있도록 구현합니다.