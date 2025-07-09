# GitHub Actions 환경변수 특수문자 및 CORS 문제 해결 기록

**날짜**: 2025년 7월 9일  
**환경**: Staging Deployment (GitHub Actions CI/CD)  
**상태**: ✅ 해결 완료

## 📋 문제 요약

GitHub Actions의 staging deployment에서 두 가지 주요 문제가 발생:
1. **환경변수 특수문자 이스케이핑 문제**: gcloud 배포 시 환경변수 파싱 오류
2. **CORS 정책 오류**: 프론트엔드에서 백엔드 API 호출 차단

## 🚨 발생한 문제들

### 1. 환경변수 특수문자 이스케이핑 문제

**에러 메시지:**
```
ERROR: (gcloud.run.deploy) argument --set-env-vars: Bad syntax for dict arg: [***]. 
Please see `gcloud topic flags-file` or `gcloud topic escaping` for information on providing list or dictionary flag values with special characters.
```

**원인:**
- `ALLOWED_ORIGINS` 환경변수에 쉼표(`,`)와 와일드카드(`*`) 문자 포함
- gcloud `--set-env-vars` 옵션에서 특수문자 파싱 실패
- GitHub Secrets에서 주입된 환경변수가 올바르게 이스케이핑되지 않음

### 2. CORS 정책 오류

**에러 메시지:**
```
Access to fetch at 'https://xai-community-backend-staging-798170408536.asia-northeast3.run.app/api/auth/register' 
from origin 'https://xai-community-git-staging-ktsfrank-navercoms-projects.vercel.app' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**원인:**
- `main.py`에서 GitHub Secrets의 `ALLOWED_ORIGINS` 환경변수를 사용하지 않음
- 하드코딩된 정규식 패턴만 사용: `r"^https://xai-community.*\.vercel\.app$"`
- staging 환경의 URL 형식이 기존 패턴과 일치하지 않음

## 🔧 해결 과정

### 단계 1: 환경변수 특수문자 문제 해결

#### 1.1 GitHub CLI로 ALLOWED_ORIGINS 수정
```bash
gh secret set ALLOWED_ORIGINS --body "https://xai-community-git-staging-ktsfrank-navercoms-projects.vercel.app,https://xai-community.vercel.app"
```

#### 1.2 배포 스크립트 수정 (`deploy-staging.sh`)

**AS-IS: 문자열 방식**
```bash
--set-env-vars="$ENV_VARS"
```

**TO-BE: 파일 방식**
```bash
--env-vars-file="$ENV_VARS_FILE"
```

**핵심 변경사항:**
1. **환경변수를 YAML 파일로 저장**
```bash
# YAML 형식으로 환경변수 파일 작성
for env_var in "${ENV_VARS_ARRAY[@]}"; do
    var_name=$(echo "$env_var" | cut -d'=' -f1)
    var_value=$(echo "$env_var" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
    echo "$var_name: \"$var_value\"" >> "$ENV_VARS_FILE"
done
```

2. **gcloud 명령어 수정**
```bash
gcloud run deploy "$GCP_SERVICE_NAME" \
    --env-vars-file="$ENV_VARS_FILE" \
    --project="$GCP_PROJECT_ID"
```

### 단계 2: CORS 설정 문제 해결

#### 2.1 main.py 수정 - GitHub Secrets 사용

**AS-IS: 하드코딩된 패턴**
```python
if settings.environment == "production":
    vercel_pattern = r"^https://xai-community.*\.vercel\.app$"
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=vercel_pattern,  # 패턴만 사용
        # ...
    )
```

**TO-BE: 환경변수 기반**
```python
if settings.environment in ["production", "staging"]:
    if cors_origins:  # GitHub Secrets의 ALLOWED_ORIGINS 사용
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,  # 명시적 origins 사용
            # ...
        )
```

#### 2.2 동적 CORS Origins 함수 개선
```python
def get_dynamic_cors_origins():
    origins = []
    
    if settings.environment in ["production", "staging"]:
        # GitHub Secrets의 ALLOWED_ORIGINS 사용
        if settings.allowed_origins:
            origins.extend(settings.allowed_origins)
            logger.info(f"{settings.environment.capitalize()} CORS origins from settings: {origins}")
        else:
            logger.warning(f"{settings.environment.capitalize()} 환경에서 ALLOWED_ORIGINS가 설정되지 않았습니다!")
    
    return origins
```

## ✅ 해결 결과

### 1. 환경변수 문제 해결
- gcloud 배포 시 YAML 파일 방식으로 특수문자 이스케이핑 문제 해결
- 쉼표와 특수문자가 포함된 환경변수 정상 처리

### 2. CORS 문제 해결
- GitHub Secrets의 `ALLOWED_ORIGINS` 값 정상 사용
- staging 환경에서 프론트엔드-백엔드 통신 정상화
- 명시적 origins 사용으로 더 안전하고 예측 가능한 CORS 설정

## 📊 커밋 이력

1. **b94ba93**: 환경변수 특수문자 이스케이핑 문제 해결
   - `--env-vars-file` 옵션 도입
   - 환경변수를 임시 파일로 저장하여 특수문자 처리

2. **173f641**: 환경변수 파일을 YAML 형식으로 수정
   - gcloud 요구사항에 맞는 YAML 형식 적용
   - `KEY: "VALUE"` 형식으로 변환

3. **cc05e48**: GitHub Secrets의 ALLOWED_ORIGINS 사용하도록 CORS 설정 수정
   - 하드코딩된 regex 패턴 제거
   - 환경변수 기반 명시적 origins 사용

## 🎯 핵심 학습 포인트

### 1. gcloud 환경변수 처리
- `--set-env-vars` 옵션은 특수문자에 취약
- `--env-vars-file` 옵션이 더 안전하고 권장됨
- YAML 형식으로 환경변수 파일 작성 필요

### 2. GitHub Secrets 활용
- 환경변수가 설정되어도 코드에서 사용하지 않으면 의미 없음
- 설정과 코드 로직이 일치해야 함
- 환경별 분기 처리 중요

### 3. CORS 설정 모범 사례
- 명시적 origins가 regex 패턴보다 안전
- 환경변수 기반 설정으로 유연성 확보
- 적절한 로깅으로 디버깅 용이성 향상

## 🔮 향후 개선 방안

1. **환경변수 검증 강화**
   - 배포 전 환경변수 형식 검증 스크립트 추가
   - 필수 환경변수 누락 체크

2. **CORS 설정 문서화**
   - 각 환경별 CORS 설정 가이드 작성
   - 새로운 도메인 추가 시 절차 정의

3. **모니터링 개선**
   - CORS 오류 실시간 모니터링 추가
   - 환경변수 설정 상태 대시보드 구축

---

**작성자**: Claude Code Assistant  
**검토자**: 태수  
**문서 버전**: 1.0