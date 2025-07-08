# XAI Community Backend Cloud Run 배포 성공 기록

**작업일**: 2025년 7월 8일  
**목적**: XAI Community 백엔드 FastAPI 애플리케이션의 Google Cloud Run 배포  
**결과**: 성공적 배포 및 모든 엔드포인트 정상 동작 확인  
**참고**: Cloud Run 자동배포 완전해결 가이드 기반으로 진행

## 📋 작업 개요

XAI Community의 FastAPI 백엔드 애플리케이션을 Google Cloud Run에 배포하는 과정에서 발생한 문제들을 해결하고 성공적으로 배포를 완료했습니다.

## 🎯 해결한 주요 문제들

### 1. Windows 줄바꿈 문제
**문제**: `/bin/bash^M: bad interpreter` 오류  
**원인**: 배포 스크립트에 Windows 스타일 줄바꿈 문자 포함  
**해결책**: 
```bash
sed -i 's/\r$//' deploy-xai-community.sh
```
**참고**: 이전 가이드에서 동일한 문제와 해결책이 문서화되어 있었음

### 2. Dockerfile 환경변수 처리 문제
**문제**: Docker 빌드 중 `.env.prod` 파일 복사 실패  
```
COPY failed: file not found in build context or excluded by .dockerignore: stat .env: file does not exist
```
**원인**: Docker 컨텍스트에서 조건부 파일 복사 시도  
**해결책**: 
- Dockerfile에서 `.env.prod` 복사 제거
- Cloud Run 환경변수로 대체
```dockerfile
# 변경 전
COPY .env.prod .env 2>/dev/null || true

# 변경 후  
# Environment file will be set via Cloud Run environment variables
# No need to copy .env.prod - using Cloud Run env vars instead
```

### 3. 환경변수 누락 문제
**문제**: 서비스 시작 실패 - 필수 환경변수 누락
```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
mongodb_url
  Field required [type=missing, input_value={'environment': 'production', 'port': '8080'}, input_type=dict]
secret_key
  Field required [type=missing, input_value={'environment': 'production', 'port': '8080'}, input_type=dict]
```
**원인**: `.env.prod` 파일이 숨겨진 파일이라 초기 확인에서 누락  
**해결책**: 
- `.env.prod` 파일 발견 및 내용 확인
- `gcloud run services update`로 환경변수 직접 설정

### 4. 환경변수 파일 형식 문제
**문제**: `env-vars-file` 옵션 사용 시 YAML 파싱 오류
```
ERROR: (gcloud) Failed to parse YAML from [.env.prod]: expected '<document start>', but found '<scalar>'
```
**원인**: `.env` 형식과 gcloud의 YAML 형식 불일치  
**해결책**: `--set-env-vars` 옵션으로 개별 변수 설정

### 5. 포트 설정 불일치
**문제**: `.env.prod`에서 PORT=8000 설정, Cloud Run은 8080 필요  
**해결책**: `.env.prod` 파일의 PORT를 8080으로 수정

## 🏗️ 최종 배포 아키텍처

```
로컬 개발환경 (backend/)
    ↓
Docker 이미지 빌드 (Google Cloud Build)
    ↓ 
Container Registry 저장 (gcr.io/xai-community/xai-community-backend)
    ↓
Cloud Run 서비스 배포 (asia-northeast3)
    ↓
환경변수 설정 및 서비스 시작
    ↓
헬스체크 통과 및 서비스 정상 운영
```

## 📁 프로젝트 구조 (수정된 파일들)

```
backend/
├── Dockerfile                           # Cloud Run 최적화
├── .env.prod                           # 포트 8080으로 수정
├── deploy-xai-community.sh             # 새로 생성된 배포 스크립트
├── main.py                             # health 라우터 추가
└── nadle_backend/
    └── routers/
        └── health.py                   # 헬스체크 라우터 (기존)
```

## 🔧 핵심 구성 요소

### 1. 최적화된 Dockerfile
```dockerfile
# Python base image - optimized for Cloud Run
FROM python:3.11-slim

# Install system dependencies (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Working directory and dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY README.md ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser -m
RUN mkdir -p uploads && chown -R appuser:appuser /app
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /home/appuser/.cache
USER appuser

# Cloud Run optimized environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start application
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info"]
```

### 2. 개선된 배포 스크립트 핵심 기능

#### 배포 전 검증
```bash
# 필수 파일 확인
# gcloud CLI 설치 및 인증 확인  
# API 활성화 (cloudbuild, run, containerregistry)
```

#### Docker 이미지 빌드
```bash
gcloud builds submit --tag gcr.io/xai-community/xai-community-backend --project=xai-community --quiet
```

#### Cloud Run 배포
```bash
gcloud run deploy xai-community-backend \
    --image gcr.io/xai-community/xai-community-backend \
    --region asia-northeast3 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --concurrency 100 \
    --max-instances 10 \
    --timeout 300 \
    --project=xai-community \
    --quiet
```

#### 환경변수 설정
```bash
gcloud run services update xai-community-backend \
    --region=asia-northeast3 \
    --set-env-vars="ENVIRONMENT=production,MONGODB_URL=mongodb+srv://...,SECRET_KEY=...,ALLOWED_ORIGINS=https://xai-community.vercel.app" \
    --project=xai-community \
    --quiet
```

## 🚀 배포 결과

### 성공적 배포 정보
- **프로젝트**: xai-community
- **리전**: asia-northeast3 (서울)
- **서비스명**: xai-community-backend
- **이미지**: gcr.io/xai-community/xai-community-backend
- **서비스 URL**: https://xai-community-backend-798170408536.asia-northeast3.run.app

### 테스트 가능한 엔드포인트
- **기본**: https://xai-community-backend-798170408536.asia-northeast3.run.app/
  - 응답: `{"message":"Content Management API","status":"running"}`
- **헬스체크**: https://xai-community-backend-798170408536.asia-northeast3.run.app/health
  - 응답: `{"status":"healthy","service":"xai-community-backend"}`
- **전체 헬스체크**: https://xai-community-backend-798170408536.asia-northeast3.run.app/health/full
  - 응답: Redis 연결 상태 포함한 전체 시스템 상태
- **API 엔드포인트**: https://xai-community-backend-798170408536.asia-northeast3.run.app/api/

## 📊 성능 및 설정

### Cloud Run 서비스 설정
- **메모리**: 512Mi
- **CPU**: 1 core
- **동시 요청**: 100개
- **최대 인스턴스**: 10개
- **타임아웃**: 300초
- **트래픽**: 인증 없이 접근 가능

### 현재 서비스 상태
- **API 서버**: 정상 동작 ✅
- **데이터베이스**: MongoDB Atlas 연결됨 ✅
- **헬스체크**: 모든 엔드포인트 통과 ✅
- **Redis 캐시**: 연결 안됨 (별도 설정 필요) ⚠️

## 🔍 문제 해결 과정 상세

### 단계별 해결 과정
1. **참고 문서 분석**: 이전 성공 사례의 패턴 파악
2. **Dockerfile 최적화**: 참고 문서의 모범 사례 적용
3. **배포 스크립트 생성**: 자동화된 배포 파이프라인 구축
4. **문제 발생 시 즉시 진단**: 로그 분석을 통한 빠른 원인 파악
5. **단계별 해결**: 각 문제를 개별적으로 해결하여 복합 문제 방지

### 핵심 개선사항
- **자동화**: 사용자 개입 없는 완전 자동 배포
- **에러 처리**: 상세한 로그 및 에러 메시지 제공
- **검증 로직**: 배포 후 자동 헬스체크
- **모니터링**: 실시간 빌드 및 배포 상태 확인

## 📋 다음 작업 시 확인사항

### 배포 전 체크리스트
- [ ] `.env.prod` 파일 존재 및 포트 8080 설정 확인
- [ ] gcloud CLI 설치 및 인증 상태 확인
- [ ] 프로젝트 ID 및 리전 설정 확인
- [ ] 필요한 Google Cloud API 활성화 확인

### 문제 발생 시 확인사항
- [ ] Windows 줄바꿈 문제: `sed -i 's/\r$//'` 실행
- [ ] 환경변수 누락: `.env.prod` 파일 확인 및 Cloud Run 환경변수 설정
- [ ] 포트 설정: Cloud Run용 8080 포트 사용 확인
- [ ] 빌드 로그: `gcloud builds list` 및 `gcloud builds log` 확인

### 모니터링 명령어
```bash
# 서비스 상태 확인
gcloud run services describe xai-community-backend --region=asia-northeast3 --project=xai-community

# 로그 확인
gcloud run services logs read xai-community-backend --region=asia-northeast3 --project=xai-community

# 빌드 상태 확인
gcloud builds list --project=xai-community

# 헬스체크
curl -s "https://xai-community-backend-798170408536.asia-northeast3.run.app/health"
```

## 💡 향후 개선 방향

1. **Redis 연결 설정**: Cloud Memorystore 또는 외부 Redis 서비스 연결
2. **환경별 배포**: 개발/스테이징/프로덕션 환경 분리
3. **CI/CD 파이프라인**: GitHub Actions 연동
4. **보안 강화**: Secret Manager 사용으로 민감 정보 관리
5. **모니터링 강화**: Cloud Logging 및 Cloud Monitoring 설정

## 🎯 성공 요인

1. **체계적 접근**: 참고 문서를 기반으로 한 단계별 진행
2. **문제 분석**: 로그 분석을 통한 정확한 문제 파악
3. **빠른 대응**: 각 문제를 즉시 해결하여 복합 문제 방지
4. **테스트 검증**: 배포 후 모든 엔드포인트 테스트로 완전성 확인

## 📝 관련 명령어 모음

### 빠른 재배포
```bash
cd /home/nadle/projects/Xai_Community/v5/backend
./deploy-xai-community.sh
```

### 서비스 관리
```bash
# 서비스 업데이트
gcloud run services update xai-community-backend --region=asia-northeast3 --project=xai-community

# 서비스 삭제 (필요시)
gcloud run services delete xai-community-backend --region=asia-northeast3 --project=xai-community --quiet

# 트래픽 분할 (새 버전 배포 시)
gcloud run services update-traffic xai-community-backend --to-revisions=REVISION=PERCENT --region=asia-northeast3 --project=xai-community
```

### 이미지 관리
```bash
# 이미지 목록 확인
gcloud container images list --repository=gcr.io/xai-community

# 이미지 삭제 (필요시)
gcloud container images delete gcr.io/xai-community/xai-community-backend --force-delete-tags --quiet
```

## 🎉 결론

XAI Community Backend의 Google Cloud Run 배포를 성공적으로 완료했습니다. 이전 실패 경험과 참고 문서를 바탕으로 모든 주요 문제점을 해결하였으며, 안정적인 서비스 운영 환경을 구축했습니다.

특히 환경변수 처리, Dockerfile 최적화, 배포 자동화 등의 핵심 문제들을 체계적으로 해결하여 향후 유사한 배포 작업에 대한 완전한 가이드를 제공할 수 있게 되었습니다.

이 기록은 다음 배포 작업이나 문제 해결 시 중요한 참고 자료가 될 것입니다.