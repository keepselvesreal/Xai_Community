# 환경변수 설정 및 배포 문제 해결 가이드

**작성일**: 2025-07-06  
**대상**: 주니어 개발자  
**목적**: Render/Vercel 배포 시 환경변수 관련 오류 해결  

## 📋 목차
1. [문제 상황 이해하기](#1-문제-상황-이해하기)
2. [환경변수 기본 개념](#2-환경변수-기본-개념)
3. [현재 프로젝트 구조 분석](#3-현재-프로젝트-구조-분석)
4. [문제점 진단](#4-문제점-진단)
5. [단계별 해결 방법](#5-단계별-해결-방법)
6. [배포 환경별 설정 방법](#6-배포-환경별-설정-방법)
7. [검증 및 테스트](#7-검증-및-테스트)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 문제 상황 이해하기

### 🚨 현재 발생하는 문제들
- **Render 배포 시**: 환경변수 읽기 오류로 서버 시작 실패
- **Vercel 배포 시**: 프론트엔드에서 API 연결 실패
- **개발 환경**: 로컬에서는 정상 작동하지만 배포하면 오류 발생

### 💡 왜 이런 문제가 발생하나?
1. **환경변수 파일 누락**: `.env` 파일이 실제로 존재하지 않음
2. **하드코딩된 URL**: 코드에 직접 박혀있는 서버 주소들
3. **복잡한 설정 로직**: 환경변수 처리 코드가 너무 복잡함
4. **플랫폼별 차이**: Render와 Vercel의 환경변수 설정 방식 차이

---

## 2. 환경변수 기본 개념

### 🔧 환경변수란?
환경변수는 프로그램이 실행되는 환경에 따라 달라지는 설정값들입니다.

```bash
# 예시: 개발 환경
DATABASE_URL=mongodb://localhost:27017/dev_db
API_URL=http://localhost:8000

# 예시: 프로덕션 환경  
DATABASE_URL=mongodb://production-server/prod_db
API_URL=https://api.myapp.com
```

### 🎯 왜 환경변수를 사용하나?
- **보안**: 비밀번호, API 키 등을 코드에 직접 쓰지 않음
- **유연성**: 환경별로 다른 설정 사용 가능
- **배포 편의성**: 코드 변경 없이 설정 변경 가능

---

## 3. 현재 프로젝트 구조 분석

### 📁 백엔드 구조 (v5/backend/)
```
v5/backend/
├── .env.example          # 환경변수 템플릿 (✅ 존재)
├── .env                  # 실제 환경변수 파일 (❌ 없음)
├── config.py             # 환경변수 설정 로직 (⚠️ 복잡함)
├── main.py              # FastAPI 앱 실행
└── deploy_config.py     # 배포 설정 (⚠️ 하드코딩)
```

### 📁 프론트엔드 구조 (@frontend/)
```
@frontend/
├── .env.example         # 환경변수 템플릿 (✅ 존재)
├── .env                 # 실제 환경변수 파일 (❌ 없음)
├── app/lib/api.ts       # API 설정 (⚠️ 하드코딩)
└── vite.config.ts       # Vite 설정
```

### 📋 필요한 환경변수들

#### 백엔드 환경변수
```bash
# 데이터베이스 설정
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=xai_community

# 보안 설정
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 설정
CORS_ORIGINS=https://your-frontend-domain.com,https://another-domain.com
FRONTEND_URL=https://your-frontend-domain.com

# 환경 설정
ENVIRONMENT=production
```

#### 프론트엔드 환경변수
```bash
# API 설정
VITE_API_URL=https://your-backend-domain.com

# 환경 설정
NODE_ENV=production
```

---

## 4. 문제점 진단

### 🔍 주요 문제점들

#### 1. 하드코딩된 URL들
**위치**: `@frontend/app/lib/api.ts:28`
```typescript
// ❌ 문제가 되는 코드
const API_BASE_URL = 'https://xai-community.onrender.com';

// ✅ 올바른 코드
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

#### 2. 복잡한 환경변수 파싱
**위치**: `v5/backend/config.py`
- 546줄의 복잡한 설정 로직
- GitHub Actions 특수 처리
- 정규식 기반 URL 매칭

#### 3. 환경변수 파일 누락
```bash
# 현재 상태
ls v5/backend/.env      # 파일 없음
ls @frontend/.env       # 파일 없음

# 필요한 상태
ls v5/backend/.env      # 파일 있어야 함
ls @frontend/.env       # 파일 있어야 함
```

---

## 5. 단계별 해결 방법

### 🚀 Phase 1: 환경변수 파일 생성

#### Step 1.1: 백엔드 환경변수 파일 생성
```bash
# 1. 백엔드 폴더로 이동
cd v5/backend/

# 2. .env.example을 복사해서 .env 파일 생성
cp .env.example .env

# 3. .env 파일 편집 (실제 값으로 변경)
nano .env
```

#### Step 1.2: 프론트엔드 환경변수 파일 생성
```bash
# 1. 프론트엔드 폴더로 이동
cd @frontend/

# 2. .env.example을 복사해서 .env 파일 생성
cp .env.example .env

# 3. .env 파일 편집
nano .env
```

### 🔧 Phase 2: 하드코딩된 URL 제거

#### Step 2.1: 프론트엔드 API URL 수정
**파일**: `@frontend/app/lib/api.ts`

```typescript
// 현재 코드 (28번 줄 근처)
const API_BASE_URL = 'https://xai-community.onrender.com';

// 수정할 코드
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

#### Step 2.2: 백엔드 CORS 설정 단순화
**파일**: `v5/backend/config.py`

복잡한 파싱 로직을 단순화:
```python
# 현재: 복잡한 파싱 로직
# 수정: 단순한 환경변수 읽기
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
```

### 🎯 Phase 3: 배포 설정 최적화

#### Step 3.1: Render 환경변수 설정 확인
**파일**: `render.yaml`

```yaml
services:
  - type: web
    name: xai-community-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
    envVars:
      - key: MONGODB_URL
        sync: false  # Render 대시보드에서 설정
      - key: SECRET_KEY
        sync: false
      - key: CORS_ORIGINS
        sync: false
      - key: ENVIRONMENT
        value: production
```

#### Step 3.2: Vercel 환경변수 설정 확인
**파일**: `vercel.json`

```json
{
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/node"
    }
  ],
  "env": {
    "VITE_API_URL": "https://xai-community.onrender.com"
  }
}
```

---

## 6. 배포 환경별 설정 방법

### 🌐 Render 배포 설정

#### 1. Render 대시보드 접속
1. [render.com](https://render.com) 로그인
2. 백엔드 서비스 선택
3. "Environment" 탭 클릭

#### 2. 환경변수 추가
```
MONGODB_URL: mongodb+srv://실제몽고DB연결문자열
SECRET_KEY: 실제비밀키
CORS_ORIGINS: https://your-frontend-domain.vercel.app
ENVIRONMENT: production
DATABASE_NAME: xai_community
```

#### 3. 배포 확인
```bash
# 로그 확인
curl https://xai-community.onrender.com/health
```

### ⚡ Vercel 배포 설정

#### 1. Vercel 대시보드 접속
1. [vercel.com](https://vercel.com) 로그인
2. 프론트엔드 프로젝트 선택
3. "Settings" → "Environment Variables"

#### 2. 환경변수 추가
```
VITE_API_URL: https://xai-community.onrender.com
NODE_ENV: production
```

#### 3. 재배포
```bash
# Vercel CLI 사용 시
vercel --prod
```

---

## 7. 검증 및 테스트

### ✅ 로컬 환경 테스트

#### 백엔드 테스트
```bash
# 1. 백엔드 실행
cd v5/backend/
python main.py

# 2. 환경변수 확인
curl http://localhost:8000/health

# 3. CORS 확인
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

#### 프론트엔드 테스트
```bash
# 1. 프론트엔드 실행
cd @frontend/
npm run dev

# 2. 환경변수 확인
echo $VITE_API_URL

# 3. API 연결 확인
# 브라우저에서 Network 탭 확인
```

### 🌍 프로덕션 환경 테스트

#### 백엔드 프로덕션 테스트
```bash
# 1. 서버 상태 확인
curl https://xai-community.onrender.com/health

# 2. CORS 확인
curl -H "Origin: https://your-frontend.vercel.app" \
     https://xai-community.onrender.com/health

# 3. 환경변수 확인 (보안상 민감하지 않은 것만)
curl https://xai-community.onrender.com/info
```

#### 프론트엔드 프로덕션 테스트
```bash
# 1. 사이트 접속
curl https://your-frontend.vercel.app

# 2. API 연결 확인
# 브라우저 개발자 도구 → Network 탭에서 API 호출 확인
```

---

## 8. 트러블슈팅

### 🔧 자주 발생하는 문제들

#### 문제 1: "Environment variable not found"
**증상**: 환경변수를 찾을 수 없다는 오류

**해결책**:
```bash
# 1. .env 파일 존재 확인
ls -la .env

# 2. 환경변수 형식 확인
cat .env
# 올바른 형식: KEY=value (띄어쓰기 없음)
# 잘못된 형식: KEY = value (띄어쓰기 있음)

# 3. 환경변수 로딩 확인
python -c "import os; print(os.getenv('MONGODB_URL'))"
```

#### 문제 2: CORS 오류
**증상**: 브라우저에서 "blocked by CORS policy" 오류

**해결책**:
```python
# config.py에서 CORS_ORIGINS 확인
CORS_ORIGINS = [
    "https://your-exact-frontend-domain.vercel.app",  # 정확한 도메인
    "https://localhost:3000",  # 개발용
]
```

#### 문제 3: API 연결 실패
**증상**: 프론트엔드에서 API 호출 실패

**해결책**:
```typescript
// api.ts에서 URL 확인
console.log('API_BASE_URL:', import.meta.env.VITE_API_URL);

// 네트워크 탭에서 실제 호출 URL 확인
// 예상: https://xai-community.onrender.com/api/...
// 실제: https://wrong-url.com/api/... (이런 경우 환경변수 오류)
```

#### 문제 4: 배포 후 환경변수 적용 안됨
**증상**: 로컬에서는 되는데 배포하면 안됨

**해결책**:
```bash
# 1. 배포 플랫폼 환경변수 확인
# Render: 대시보드 → Environment 탭
# Vercel: 대시보드 → Settings → Environment Variables

# 2. 재배포 필요 여부 확인
# 환경변수 변경 후 반드시 재배포 필요

# 3. 로그 확인
# Render: 대시보드에서 로그 확인
# Vercel: 대시보드에서 Function 로그 확인
```

### 🆘 긴급 해결 방법

#### 임시 수정 (빠른 배포용)
```typescript
// 1. api.ts에서 임시 하드코딩 (비추천, 긴급시만)
const API_BASE_URL = 'https://xai-community.onrender.com';

// 2. 환경변수 fallback 추가
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://xai-community.onrender.com';
```

#### 환경변수 디버깅
```python
# config.py 맨 위에 추가 (디버깅용)
import os
print("=== 환경변수 디버깅 ===")
print(f"MONGODB_URL: {os.getenv('MONGODB_URL', 'NOT SET')}")
print(f"SECRET_KEY: {'SET' if os.getenv('SECRET_KEY') else 'NOT SET'}")
print(f"CORS_ORIGINS: {os.getenv('CORS_ORIGINS', 'NOT SET')}")
print("========================")
```

---

## 📚 참고 자료

### 공식 문서
- [Render 환경변수 가이드](https://render.com/docs/environment-variables)
- [Vercel 환경변수 가이드](https://vercel.com/docs/concepts/projects/environment-variables)
- [Vite 환경변수 가이드](https://vitejs.dev/guide/env-and-mode.html)

### 도구들
- [dotenv checker](https://www.npmjs.com/package/dotenv) - 환경변수 파일 검증
- [env-cmd](https://www.npmjs.com/package/env-cmd) - 환경변수 관리

### 보안 주의사항
- 🚨 **절대 금지**: `.env` 파일을 Git에 커밋하지 마세요
- 🔒 **비밀번호**: 모든 비밀 정보는 배포 플랫폼에서 설정
- 🔑 **API 키**: 환경변수로만 관리, 코드에 직접 쓰지 마세요

---

## 🎯 체크리스트

### 개발 환경 설정 완료 체크리스트
- [ ] `v5/backend/.env` 파일 생성 및 설정
- [ ] `@frontend/.env` 파일 생성 및 설정
- [ ] 로컬에서 백엔드 실행 확인
- [ ] 로컬에서 프론트엔드 실행 확인
- [ ] API 연결 테스트 완료

### 배포 환경 설정 완료 체크리스트
- [ ] Render 환경변수 설정 완료
- [ ] Vercel 환경변수 설정 완료
- [ ] 하드코딩된 URL 제거 완료
- [ ] 프로덕션 배포 테스트 완료
- [ ] CORS 설정 확인 완료

### 코드 수정 완료 체크리스트
- [ ] `@frontend/app/lib/api.ts` 환경변수 적용
- [ ] `v5/backend/config.py` 설정 단순화
- [ ] `v5/backend/deploy_config.py` 하드코딩 제거
- [ ] 환경변수 fallback 로직 추가
- [ ] 오류 처리 개선

---

**💡 마지막 팁**: 환경변수 설정은 한 번에 모든 것을 바꾸려 하지 말고, 단계별로 하나씩 확인하면서 진행하세요. 각 단계마다 테스트를 해보면 어디서 문제가 발생하는지 쉽게 찾을 수 있습니다!