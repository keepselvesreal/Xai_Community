# Cloud Run CI/CD 실험 및 문제해결 기록

**날짜**: 2025-07-09  
**작업자**: Claude Code  
**목적**: Cloud Run 배포 문제 해결을 위한 실험용 프로젝트 구성 및 CI/CD 파이프라인 구축

## 1. 프로젝트 개요

### 실험 목적
- 현재 프로젝트의 복잡한 staging 배포에서 자세한 로그가 출력되지 않아 디버깅 어려움
- 간단한 실험용 프로젝트로 Cloud Run 배포의 기본 원리 확인
- 성공적인 패턴을 현재 프로젝트에 적용

### 실험용 프로젝트 구조
```
cloud-run-experiment/
├── main.py                    # 간단한 FastAPI 앱
├── pyproject.toml            # uv 의존성 파일 (최종적으로 불사용)
├── uv.lock                   # uv 락 파일 (최종적으로 불사용)
├── Dockerfile                # 단순한 Dockerfile
├── deploy.sh                 # Cloud Run 배포 스크립트
└── README.md                 # 실험 가이드
```

## 2. 발생한 문제들과 해결 과정

### 2.1 GitHub Actions 워크플로우 인식 문제

**문제**: 
- 실험용 프로젝트 내의 `.github/workflows/deploy.yml`이 GitHub Actions에서 인식되지 않음

**원인**: 
- GitHub Actions는 루트 경로의 `.github/workflows/`에서만 워크플로우 파일을 인식

**해결방법**:
```bash
# 워크플로우 파일을 루트로 이동
cp cloud-run-experiment/.github/workflows/deploy.yml .github/workflows/cloud-run-experiment.yml
rm -rf cloud-run-experiment/.github/
```

### 2.2 서비스 계정 권한 부족 문제

**문제 1**: API 활성화 권한 부족
```
ERROR: Permission denied to enable service [cloudbuild.googleapis.com]
Permission denied to enable service [run.googleapis.com]
```

**해결방법**:
```bash
gcloud projects add-iam-policy-binding xai-community \
    --member="serviceAccount:xai-community-backend@xai-community.iam.gserviceaccount.com" \
    --role="roles/serviceusage.serviceUsageAdmin"
```

**문제 2**: Cloud Run 관리 권한 부족
**해결방법**:
```bash
gcloud projects add-iam-policy-binding xai-community \
    --member="serviceAccount:xai-community-backend@xai-community.iam.gserviceaccount.com" \
    --role="roles/run.admin"
```

**문제 3**: Cloud Build 빌더 권한 부족
**해결방법**:
```bash
gcloud projects add-iam-policy-binding xai-community \
    --member="serviceAccount:xai-community-backend@xai-community.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"
```

**문제 4**: 서비스 계정 사용 권한 부족
```
ERROR: caller does not have permission to act as service account
```

**해결방법**:
```bash
gcloud projects add-iam-policy-binding xai-community \
    --member="serviceAccount:xai-community-backend@xai-community.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding xai-community \
    --member="serviceAccount:xai-community-backend@xai-community.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountTokenCreator"
```

### 2.3 Cloud Build 로그 스트리밍 문제

**문제**:
```
ERROR: The build is running, and logs are being written to the default logs bucket.
This tool can only stream logs if you are Viewer/Owner of the project
```

**시도한 해결방법들**:

1. **첫 번째 시도**: `--suppress-logs` 옵션 사용
   - 결과: 여전히 같은 오류 발생

2. **최종 해결방법**: `--async` 옵션 사용 + 상태 폴링
```bash
# 비동기 빌드 시작
BUILD_OUTPUT=$(gcloud builds submit --tag "$IMAGE_NAME" --project="$PROJECT_ID" --async 2>&1)

# 빌드 상태를 주기적으로 체크
while true; do
    BUILD_STATUS=$(gcloud builds describe "$BUILD_ID" --project="$PROJECT_ID" --format="value(status)")
    case "$BUILD_STATUS" in
        "SUCCESS") break ;;
        "FAILURE"|"CANCELLED"|"TIMEOUT") exit 1 ;;
        *) sleep 10 ;;
    esac
done
```

### 2.4 Docker 빌드 실패 문제

**문제**: 복잡한 Dockerfile로 인한 빌드 실패

**시도한 해결방법들**:

1. **첫 번째 시도**: uv를 사용한 복잡한 Dockerfile
```dockerfile
FROM python:3.11-slim
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
```

2. **최종 해결방법**: pip를 사용한 단순한 Dockerfile
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn[standard] python-multipart
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 3. 최종 구성

### 3.1 필요한 서비스 계정 권한 목록
```bash
# 최종적으로 부여된 권한들
roles/serviceusage.serviceUsageAdmin  # API 활성화
roles/run.admin                       # Cloud Run 관리
roles/cloudbuild.builds.builder       # Cloud Build 빌더
roles/iam.serviceAccountUser          # 서비스 계정 사용자
roles/iam.serviceAccountTokenCreator  # 서비스 계정 토큰 생성자
roles/storage.objectAdmin            # 기존 권한 (이미지 저장)
roles/cloudsql.client                # 기존 권한 (DB 접근)
```

### 3.2 성공적인 배포 스크립트 패턴
```bash
# 1. 비동기 빌드 시작
BUILD_OUTPUT=$(gcloud builds submit --tag "$IMAGE_NAME" --project="$PROJECT_ID" --async 2>&1)

# 2. 빌드 ID 추출
BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'builds/[a-zA-Z0-9-]*' | head -1 | cut -d'/' -f2)

# 3. 빌드 상태 폴링
while true; do
    BUILD_STATUS=$(gcloud builds describe "$BUILD_ID" --project="$PROJECT_ID" --format="value(status)")
    case "$BUILD_STATUS" in
        "SUCCESS") break ;;
        "FAILURE"|"CANCELLED"|"TIMEOUT") exit 1 ;;
        "QUEUED"|"WORKING") sleep 10 ;;
    esac
done

# 4. Cloud Run 배포
gcloud run deploy "$SERVICE_NAME" --image "$IMAGE_NAME" --project="$PROJECT_ID"
```

## 4. 현재 상태 및 남은 과제

### 4.1 현재 상태
- ✅ 서비스 계정 권한 모두 설정 완료
- ✅ GitHub Actions 워크플로우 정상 인식
- ✅ Cloud Build 로그 스트리밍 문제 해결 (비동기 방식)
- ✅ 배포 스크립트 상세 로깅 구현
- ❌ Docker 빌드 여전히 실패 (단순화했음에도 불구하고)

### 4.2 빌드 실패 디버깅 정보
- 빌드 ID: `9d5e15e5-fc55-4a54-ba43-a9819e06651f`
- 상태: `FAILURE`
- 로그 조회 권한 부족으로 정확한 실패 원인 파악 어려움

### 4.3 다음 단계
1. **빌드 로그 접근 권한 추가**:
   ```bash
   gcloud projects add-iam-policy-binding xai-community \
       --member="serviceAccount:xai-community-backend@xai-community.iam.gserviceaccount.com" \
       --role="roles/logging.viewer"
   ```

2. **Google Cloud Console에서 수동 빌드 로그 확인**:
   - URL: `https://console.cloud.google.com/cloud-build/builds/9d5e15e5-fc55-4a54-ba43-a9819e06651f?project=xai-community`

3. **더 단순한 Dockerfile 시도**:
   - Python 기본 이미지에서 최소한의 의존성만 설치
   - COPY 명령어 최소화

## 5. 현재 프로젝트 적용 방안

### 5.1 즉시 적용 가능한 개선사항
1. **상세한 로깅**: `set -x` 및 단계별 로그 메시지
2. **비동기 빌드**: `--async` 옵션 사용 + 상태 폴링
3. **에러 처리 강화**: 빌드 실패 시 상세 정보 수집
4. **권한 검증**: 배포 전 필요한 권한 확인

### 5.2 배포 스크립트 개선 패턴
```bash
# 실험에서 성공한 패턴을 현재 프로젝트에 적용
# 1. set -x로 모든 명령어 출력
# 2. 각 단계별 시작/완료 시간 로그
# 3. 비동기 빌드 + 상태 폴링
# 4. 실패 시 빌드 ID와 Console 링크 제공
```

## 6. 교훈 및 베스트 프랙티스

### 6.1 GitHub Actions CI/CD 구축 시 주의사항
1. 워크플로우 파일은 반드시 루트의 `.github/workflows/`에 위치
2. 서비스 계정 권한을 단계적으로 추가하며 테스트
3. 로그 스트리밍 문제 시 비동기 방식 사용 고려

### 6.2 Cloud Build 디버깅 전략
1. 빌드 실패 시 Google Cloud Console 링크 제공
2. 빌드 상태를 주기적으로 체크하는 로직 구현
3. Dockerfile은 최대한 단순하게 시작해서 점진적으로 복잡도 증가

### 6.3 권한 관리 베스트 프랙티스
1. 최소 권한 원칙으로 시작하여 필요에 따라 추가
2. 권한 추가 시 즉시 테스트하여 효과 확인
3. 모든 권한 변경 사항을 문서화

## 7. 결론

실험용 프로젝트를 통해 Cloud Run CI/CD 파이프라인 구축 과정에서 발생할 수 있는 주요 문제들과 해결 방법을 체계적으로 파악했습니다. 비록 Docker 빌드 문제가 완전히 해결되지는 않았지만, 서비스 계정 권한 설정, 로그 스트리밸 문제 해결, GitHub Actions 워크플로우 구성 등 핵심적인 문제들에 대한 해결책을 확보했습니다.

이제 이 경험을 바탕으로 현재 프로젝트의 staging 배포 문제를 해결할 수 있을 것입니다.