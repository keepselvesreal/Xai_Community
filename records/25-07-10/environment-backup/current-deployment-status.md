# 현재 배포 상태 백업 (2025-07-10)

## 백엔드 프로덕션 상태
- **서비스명**: xai-community-backend
- **현재 리비전**: xai-community-backend-00001-vmq
- **배포 시간**: 2025-07-09T02:59:47.287098Z
- **이미지**: gcr.io/xai-community/xai-community-backend@sha256:b7d50f37334a1e40a1329841c0a687c66be3e004dbfe40238ac2f10b97de3065
- **URL**: https://xai-community-backend-798170408536.asia-northeast3.run.app
- **상태**: 정상 (healthy)

## 백엔드 스테이징 상태
- **서비스명**: xai-community-backend-staging
- **현재 리비전**: xai-community-backend-staging-00002-xw5
- **배포 시간**: 2025-07-09T12:35:26.052883Z
- **이미지**: gcr.io/xai-community/xai-community-backend-staging@sha256:3fde9c77f1b595afbc702eb72af8737e52c72319b9cebe429c6232c6eba94c0c
- **URL**: https://xai-community-backend-staging-798170408536.asia-northeast3.run.app
- **상태**: 정상 (healthy)

## 프론트엔드 상태
- **URL**: https://xai-community.vercel.app
- **상태**: 정상 (로딩됨)
- **현재 Git 커밋**: b021765e48a9c7e1c2aa30511af30187ff1cad6d
- **커밋 메시지**: "add: 자동화 테스트 스크립트들 추가"

## 최근 배포 히스토리
### 백엔드 프로덕션 리비전
- xai-community-backend-00001-vmq (2025-07-09T02:59:47.287098Z) - 활성

### 백엔드 스테이징 리비전
- xai-community-backend-staging-00002-xw5 (2025-07-09T12:35:26.052883Z) - 활성
- xai-community-backend-staging-00001-92f (2025-07-09T12:11:53.258561Z) - 이전 버전

### 최근 Git 커밋
- b021765: add: 자동화 테스트 스크립트들 추가
- 12133c0: fix: 프론트엔드 댓글 API 응답 처리 및 서비스 타입 변환 로직 개선
- 9e5b7c4: fix: 프론트엔드 댓글 API 응답 처리 및 서비스 타입 변환 로직 개선
- cc05e48: fix: GitHub Secrets의 ALLOWED_ORIGINS 환경변수 사용하도록 CORS 설정 수정
- 173f641: fix: 환경변수 파일을 YAML 형식으로 수정

## 환경 설정 정보
- **GCP 프로젝트**: xai-community
- **리전**: asia-northeast3
- **GitHub 레포지토리**: keepselvesreal/Xai_Community
- **현재 브랜치**: staging
- **Vercel 계정**: ktsfrank-3285

## 백업 파일 목록
- backend-production-config.yaml: 백엔드 프로덕션 Cloud Run 설정
- backend-staging-config.yaml: 백엔드 스테이징 Cloud Run 설정
- github-secrets-list.json: GitHub Actions Secrets 목록
- current-deployment-status.md: 현재 배포 상태 요약