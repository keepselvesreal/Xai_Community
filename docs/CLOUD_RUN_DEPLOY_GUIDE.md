# Google Cloud Run 배포 가이드

## 🚀 배포 준비 사항

### 1. Google Cloud CLI 설치
```bash
# Google Cloud CLI 설치 (Ubuntu/Debian)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 또는 macOS (Homebrew)
brew install google-cloud-sdk
```

### 2. Google Cloud 로그인 및 프로젝트 생성
```bash
# Google Cloud 로그인
gcloud auth login

# 프로젝트 생성 (선택사항)
gcloud projects create xai-community --name="XAI Community"

# 프로젝트 설정
gcloud config set project xai-community

# 결제 계정 연결 (필수)
gcloud billing projects link xai-community --billing-account=YOUR_BILLING_ACCOUNT_ID
```

## 📋 배포 전 체크리스트

### 환경변수 확인
- [x] `.env.prod` 파일 완성
- [x] MongoDB Atlas 연결 URL 확인
- [x] SECRET_KEY 안전한 키로 설정
- [x] ALLOWED_ORIGINS 프론트엔드 도메인 설정
- [x] Google Cloud 프로젝트 설정

### 필수 환경변수 리스트
```bash
# 데이터베이스 설정
MONGODB_URL=mongodb+srv://...
DATABASE_NAME=xai_community

# 보안 설정
SECRET_KEY=your-secure-secret-key

# CORS 설정
ALLOWED_ORIGINS=https://xai-community.vercel.app
FRONTEND_URL=https://xai-community.vercel.app

# Google Cloud 설정
PROJECT_ID=xai-community
SERVICE_NAME=Xai_Community
REGION=asia-northeast3
```

## 🔧 배포 실행

### 방법 1: 자동 배포 스크립트 사용 (권장)
```bash
# backend 디렉토리로 이동
cd /home/nadle/projects/Xai_Community/v5/backend

# 배포 스크립트 실행
./deploy-cloud-run.sh
```

### 방법 2: 수동 배포
```bash
# 1. 프로젝트 설정
gcloud config set project xai-community

# 2. 서비스 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# 3. 배포
gcloud run deploy Xai_Community \
  --source . \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production

# 4. 환경변수 업데이트
gcloud run services update Xai_Community \
  --region asia-northeast3 \
  --set-env-vars \
  MONGODB_URL="mongodb+srv://...",\
  DATABASE_NAME="xai_community",\
  SECRET_KEY="your-secret-key",\
  ALLOWED_ORIGINS="https://xai-community.vercel.app"
```

## 🎯 배포 후 확인사항

### 1. 서비스 상태 확인
```bash
# 서비스 상태 확인
gcloud run services describe Xai_Community --region asia-northeast3

# 서비스 URL 확인
gcloud run services describe Xai_Community --region asia-northeast3 --format="value(status.url)"
```

### 2. API 엔드포인트 테스트
```bash
# 헬스 체크
curl https://your-service-url.run.app/

# API 문서 확인 (ENABLE_DOCS=false로 설정했으므로 404 예상)
curl https://your-service-url.run.app/docs
```

### 3. 로그 확인
```bash
# 최근 로그 확인
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=Xai_Community" --limit 50

# 실시간 로그 스트림
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=Xai_Community"
```

## 🔧 사후 관리

### 환경변수 업데이트
```bash
gcloud run services update Xai_Community \
  --region asia-northeast3 \
  --set-env-vars NEW_VAR=new_value
```

### 서비스 스케일링 조정
```bash
gcloud run services update Xai_Community \
  --region asia-northeast3 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 20
```

### 커스텀 도메인 연결
```bash
# 도메인 매핑 생성
gcloud run domain-mappings create \
  --service Xai_Community \
  --domain api.your-domain.com \
  --region asia-northeast3
```

## 🚨 트러블슈팅

### 일반적인 문제들

1. **빌드 실패**
   - Dockerfile 경로 확인
   - 의존성 설치 오류 확인

2. **환경변수 문제**
   - MongoDB 연결 문자열 확인
   - SECRET_KEY 길이 확인 (32자 이상)

3. **CORS 오류**
   - ALLOWED_ORIGINS 설정 확인
   - 프론트엔드 도메인 정확성 확인

4. **메모리 부족**
   - 메모리 할당량 증가
   - 불필요한 의존성 제거

### 유용한 명령어
```bash
# 서비스 삭제
gcloud run services delete Xai_Community --region asia-northeast3

# 모든 Cloud Run 서비스 확인
gcloud run services list

# 특정 서비스 트래픽 확인
gcloud run services describe Xai_Community --region asia-northeast3 --format="value(spec.traffic)"
```

## 💰 비용 최적화

### 권장 설정
```bash
# 비용 효율적인 설정으로 업데이트
gcloud run services update Xai_Community \
  --region asia-northeast3 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --concurrency 100
```

### 모니터링
- Google Cloud Console에서 사용량 확인
- 알림 설정으로 비용 모니터링
- 불필요한 트래픽 패턴 분석

---

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. [Google Cloud Run 문서](https://cloud.google.com/run/docs)
2. [Cloud Run 가격 정보](https://cloud.google.com/run/pricing)
3. 로그를 통한 오류 분석