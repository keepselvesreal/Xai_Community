# 초보자를 위한 클라우드 무료 티어 배포 가이드 (2025년 7월 버전)

## 목차
1. [개요](#개요)
2. [MongoDB Atlas 무료 티어 설정](#mongodb-atlas-무료-티어-설정)
3. [AWS 무료 티어 배포 옵션](#aws-무료-티어-배포-옵션)
4. [GCP 무료 티어 배포 옵션](#gcp-무료-티어-배포-옵션)
5. [Vercel을 이용한 프론트엔드 배포](#vercel을-이용한-프론트엔드-배포)
6. [환경 변수 설정 방법](#환경-변수-설정-방법)
7. [단계별 체크리스트](#단계별-체크리스트)
8. [비용 최적화 팁](#비용-최적화-팁)
9. [주의사항 및 트러블슈팅](#주의사항-및-트러블슈팅)

---

## 개요

이 가이드는 **현재 프로젝트(FastAPI + MongoDB + Remix React)**를 클라우드 무료 티어로 배포하는 방법을 초보자도 쉽게 따라할 수 있도록 단계별로 설명합니다.

### 현재 프로젝트 구조
- **백엔드**: FastAPI (Python 3.11) + MongoDB
- **프론트엔드**: Remix React 앱
- **패키지 관리**: UV (백엔드), NPM (프론트엔드)

### 목표 아키텍처
```
[사용자] → [Vercel: Remix Frontend] → [AWS/GCP: FastAPI Backend] → [MongoDB Atlas: Database]
```

---

## MongoDB Atlas 무료 티어 설정

### 1. MongoDB Atlas 개요
- **무료 저장소**: 512MB
- **지역 제한**: 없음 (가까운 지역 선택 권장)
- **동시 연결**: 500개
- **백업**: 제한적 백업 기능

### 2. 단계별 설정 가이드

#### 2.1 회원가입 및 클러스터 생성
```bash
# 1. MongoDB Atlas 회원가입
# https://www.mongodb.com/cloud/atlas/register 접속
# 2. 구글 계정으로 로그인 또는 이메일 회원가입
# 3. 이메일 인증 완료
```

#### 2.2 무료 클러스터 생성
1. **Shared Clusters** 선택
2. **"Create a cluster"** 클릭
3. **지역 선택**: 
   - 추천: `ap-southeast-1` (Singapore) - 한국과 가장 가까움
   - 대안: `ap-northeast-1` (Tokyo)
4. **클러스터 설정**:
   - **Cluster Tier**: M0 Sandbox (FREE) 선택
   - **Cluster Name**: 원하는 이름 입력 (예: `xai-community-db`)
5. **"Create Cluster"** 클릭

#### 2.3 보안 설정
1. **Database Access** 설정:
   ```
   Username: admin
   Password: 안전한 비밀번호 생성 (기록해두기!)
   Database User Privileges: Atlas admin
   ```

2. **Network Access** 설정:
   ```
   IP Address: 0.0.0.0/0 (모든 IP 허용)
   Description: Allow all IPs
   ```
   > ⚠️ 보안상 위험하므로 추후 특정 IP로 제한 권장

#### 2.4 연결 문자열 획득
1. **Connect** 버튼 클릭
2. **Connect your application** 선택
3. **Driver**: Python 3.6 or later
4. **연결 문자열 복사**:
   ```
   mongodb+srv://admin:<password>@xai-community-db.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 3. 로컬 데이터 마이그레이션
```bash
# 현재 로컬 MongoDB 데이터 백업
mongodump --uri="mongodb://localhost:27017/xai_community" --out=./backup

# Atlas로 데이터 복원
mongorestore --uri="mongodb+srv://admin:<password>@cluster.xxxxx.mongodb.net/xai_community" ./backup/xai_community
```

---

## AWS 무료 티어 배포 옵션

### 1. AWS 무료 티어 개요 (2025년 기준)
- **12개월 무료**: EC2, RDS, S3 등
- **항상 무료**: Lambda, API Gateway, CloudWatch 등
- **평가판**: 특정 기간 동안 무료

### 2. 배포 옵션 비교

| 서비스 | 무료 한도 | 장점 | 단점 | 추천도 |
|--------|-----------|------|------|--------|
| **EC2** | t2.micro 750시간/월 | 완전한 제어, 지속적 실행 | 관리 복잡, 보안 설정 필요 | ⭐⭐⭐ |
| **Lambda** | 월 100만 요청 | 서버리스, 확장 자동 | 콜드 스타트, 실행 시간 제한 | ⭐⭐⭐⭐ |
| **App Runner** | 월 $5 크레딧 | 자동 스케일링, 간편 배포 | 제한적 무료 크레딧 | ⭐⭐⭐⭐⭐ |

### 3. 추천 옵션: AWS App Runner

#### 3.1 App Runner 설정
1. **AWS 콘솔** → **App Runner** 서비스 접속
2. **Create service** 클릭
3. **Source and deployment** 설정:
   ```
   Repository type: Container registry
   Provider: Amazon ECR Public
   Container image URI: public.ecr.aws/aws-containers/hello-app-runner:latest
   ```

#### 3.2 Dockerfile 준비
```dockerfile
# 현재 프로젝트의 Dockerfile 사용
FROM python:3.11-slim

WORKDIR /app

# UV 설치
RUN pip install uv

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 소스 코드 복사
COPY . .

# 포트 설정
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# 애플리케이션 시작
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.3 환경 변수 설정
```bash
# App Runner 환경 변수 설정
MONGODB_URL=mongodb+srv://admin:<password>@cluster.xxxxx.mongodb.net/xai_community
DATABASE_NAME=xai_community
SECRET_KEY=your-production-secret-key-32-characters-long
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

---

## GCP 무료 티어 배포 옵션

### 1. GCP 무료 티어 개요 (2025년 기준)
- **90일 $300 크레딧**: 신규 사용자 대상
- **항상 무료**: Cloud Run, App Engine, Compute Engine f1-micro 등

### 2. 추천 옵션: Google Cloud Run

#### 2.1 Cloud Run 장점
- **요청 기반 요금**: 사용한 만큼만 과금
- **자동 스케일링**: 0에서 무한대까지 자동 확장
- **무료 한도**: 월 2백만 요청, 360,000 GB-초 CPU 시간

#### 2.2 Cloud Run 배포 단계

**1단계: GCP 프로젝트 생성**
```bash
# Google Cloud Console에서 프로젝트 생성
# 프로젝트 ID: xai-community-backend
```

**2단계: Cloud SDK 설치 및 인증**
```bash
# Cloud SDK 설치 (Windows/Mac/Linux)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 인증
gcloud auth login
gcloud config set project xai-community-backend
```

**3단계: 컨테이너 빌드 및 배포**
```bash
# 현재 프로젝트 디렉토리에서 실행
cd backend

# Cloud Build를 사용한 컨테이너 빌드
gcloud builds submit --tag gcr.io/xai-community-backend/fastapi-app

# Cloud Run에 배포
gcloud run deploy xai-community-api \
    --image gcr.io/xai-community-backend/fastapi-app \
    --platform managed \
    --region asia-northeast1 \
    --allow-unauthenticated \
    --set-env-vars MONGODB_URL="mongodb+srv://admin:<password>@cluster.xxxxx.mongodb.net/xai_community" \
    --set-env-vars DATABASE_NAME="xai_community" \
    --set-env-vars SECRET_KEY="your-production-secret-key-32-characters-long" \
    --set-env-vars ENVIRONMENT="production"
```

**4단계: 배포 확인**
```bash
# 배포된 서비스 URL 확인
gcloud run services describe xai-community-api --region asia-northeast1

# 헬스 체크
curl https://xai-community-api-xxx-an.a.run.app/health
```

---

## Vercel을 이용한 프론트엔드 배포

### 1. Vercel 무료 티어 특징 (2025년 기준)
- **월 대역폭**: 100GB
- **빌드 시간**: 6,000분/월
- **Serverless Functions**: 12개 제한
- **도메인**: 무료 `.vercel.app` 서브도메인 제공

### 2. Remix React 앱 배포 단계

#### 2.1 Vercel 설정 파일 생성
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build/client",
  "functions": {
    "app/routes/**/*.ts": {
      "maxDuration": 30
    }
  },
  "routes": [
    {
      "src": "/build/(.*)",
      "dest": "/build/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/build/server/index.js"
    }
  ]
}
```

#### 2.2 환경 변수 설정
```bash
# Vercel 환경 변수 (.env.production)
VITE_API_BASE_URL=https://xai-community-api-xxx-an.a.run.app
VITE_ENVIRONMENT=production
```

#### 2.3 배포 단계
1. **Vercel 회원가입**: https://vercel.com/signup
2. **GitHub 연동**: "Continue with GitHub" 선택
3. **프로젝트 Import**:
   - Repository: `Xai_Community` 선택
   - Framework Preset: `Remix` 선택
   - Root Directory: `frontend` 설정
4. **환경 변수 설정**: 
   - Dashboard → Settings → Environment Variables
   - 위에서 정의한 환경 변수들 추가
5. **Deploy** 클릭

#### 2.4 배포 후 확인
```bash
# 배포 URL 확인 (예시)
https://xai-community-frontend.vercel.app

# API 연결 테스트
curl https://xai-community-frontend.vercel.app/api/health
```

---

## 환경 변수 설정 방법

### 1. 백엔드 환경 변수 (FastAPI)

#### AWS App Runner
```bash
# AWS Console → App Runner → Configuration → Environment variables
MONGODB_URL=mongodb+srv://admin:<password>@cluster.xxxxx.mongodb.net/xai_community
DATABASE_NAME=xai_community
SECRET_KEY=your-production-secret-key-32-characters-long
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-domain.vercel.app
API_TITLE=XAI Community API
API_VERSION=1.0.0
```

#### Google Cloud Run
```bash
# gcloud CLI 사용
gcloud run services update xai-community-api \
    --region asia-northeast1 \
    --update-env-vars MONGODB_URL="mongodb+srv://admin:<password>@cluster.xxxxx.mongodb.net/xai_community" \
    --update-env-vars DATABASE_NAME="xai_community" \
    --update-env-vars SECRET_KEY="your-production-secret-key-32-characters-long" \
    --update-env-vars ENVIRONMENT="production" \
    --update-env-vars CORS_ORIGINS="https://your-frontend-domain.vercel.app"
```

### 2. 프론트엔드 환경 변수 (Remix)

#### Vercel Dashboard
```bash
# Environment Variables 탭에서 설정
VITE_API_BASE_URL=https://your-backend-url
VITE_ENVIRONMENT=production
VITE_APP_NAME=XAI Community
```

### 3. 보안 키 생성
```bash
# 안전한 SECRET_KEY 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 또는
openssl rand -base64 32
```

---

## 단계별 체크리스트

### 📋 배포 전 준비사항
- [ ] GitHub 저장소 최신 상태 확인
- [ ] 로컬 환경에서 모든 테스트 통과 확인
- [ ] 프로덕션 환경 변수 준비
- [ ] 보안 키 생성 및 안전한 저장

### 📋 데이터베이스 설정
- [ ] MongoDB Atlas 계정 생성
- [ ] 무료 클러스터 생성 (M0 Sandbox)
- [ ] 데이터베이스 사용자 생성
- [ ] 네트워크 액세스 설정
- [ ] 연결 문자열 확인
- [ ] 로컬 데이터 백업 및 마이그레이션

### 📋 백엔드 배포
- [ ] AWS 또는 GCP 계정 생성
- [ ] 무료 티어 자격 확인
- [ ] 컨테이너 이미지 빌드 테스트
- [ ] 배포 서비스 선택 및 설정
- [ ] 환경 변수 설정
- [ ] 배포 및 헬스 체크

### 📋 프론트엔드 배포
- [ ] Vercel 계정 생성 및 GitHub 연동
- [ ] 프로젝트 Import 및 설정
- [ ] 환경 변수 설정
- [ ] 빌드 및 배포
- [ ] 도메인 연결 확인

### 📋 통합 테스트
- [ ] 프론트엔드 → 백엔드 API 연결 확인
- [ ] 백엔드 → 데이터베이스 연결 확인
- [ ] CORS 설정 확인
- [ ] 주요 기능 동작 확인

---

## 비용 최적화 팁

### 1. 무료 티어 한계 모니터링

#### AWS
```bash
# CloudWatch 알림 설정
aws cloudwatch put-metric-alarm \
    --alarm-name "EC2-Free-Tier-Usage" \
    --alarm-description "EC2 free tier usage alarm" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold
```

#### GCP
```bash
# 예산 알림 설정
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Free Tier Budget" \
    --budget-amount=50USD \
    --threshold-rule=percent=80
```

### 2. 리소스 사용 최적화

#### 백엔드 최적화
```python
# FastAPI 설정 최적화
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 리소스 초기화
    yield
    # 종료 시 리소스 정리

app = FastAPI(lifespan=lifespan)

# 불필요한 로깅 제거
import logging
logging.getLogger("uvicorn").setLevel(logging.WARNING)
```

#### 프론트엔드 최적화
```javascript
// 번들 크기 최적화
// vite.config.ts
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['@remix-run/react']
        }
      }
    }
  }
}
```

### 3. 캐싱 전략
```python
# Redis 대신 메모리 캐시 사용
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_cached_data(key: str):
    # 데이터베이스 쿼리 결과 캐시
    pass
```

---

## 주의사항 및 트러블슈팅

### 1. 일반적인 오류 및 해결방법

#### CORS 오류
```python
# backend/nadle_backend/config.py 확인
cors_origins = [
    "https://your-frontend-domain.vercel.app",
    "http://localhost:3000"  # 개발 환경
]
```

#### 환경 변수 오류
```bash
# 환경 변수 확인
echo $MONGODB_URL
echo $SECRET_KEY

# 컨테이너 내부에서 확인
docker exec -it container_name env | grep MONGODB_URL
```

#### 메모리 부족 오류
```yaml
# Docker 메모리 제한 설정
version: '3.8'
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### 2. 보안 고려사항

#### 네트워크 보안
```bash
# MongoDB Atlas IP 제한
# 0.0.0.0/0 대신 특정 IP 사용
# AWS: NAT Gateway IP
# GCP: Cloud Run 송신 IP
```

#### 환경 변수 보안
```bash
# 환경 변수 암호화
# AWS: Parameter Store 사용
# GCP: Secret Manager 사용
# Vercel: Environment Variables (자동 암호화)
```

### 3. 성능 모니터링

#### 로그 확인
```bash
# AWS CloudWatch 로그
aws logs tail /aws/apprunner/xai-community-api --follow

# GCP Cloud Logging
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Vercel 로그
vercel logs https://your-app.vercel.app
```

#### 성능 메트릭
```python
# FastAPI 성능 모니터링
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## 마무리

이 가이드를 통해 무료 티어로 전체 스택을 배포할 수 있습니다. 각 단계를 차근차근 따라하고, 문제가 발생하면 해당 섹션의 트러블슈팅을 참고하세요.

### 추가 참고 자료
- [MongoDB Atlas 공식 문서](https://docs.atlas.mongodb.com/)
- [AWS App Runner 가이드](https://docs.aws.amazon.com/apprunner/)
- [Google Cloud Run 문서](https://cloud.google.com/run/docs)
- [Vercel 배포 가이드](https://vercel.com/docs/deployments/overview)

### 업데이트 이력
- 2025.07.06: 최초 작성 (최신 무료 티어 정보 반영)

---

💡 **도움이 필요하면?** 
- 각 플랫폼의 공식 문서 확인
- 커뮤니티 포럼 활용
- 오류 로그 분석 후 검색