# Cloud Run 실험용 프로젝트

## 개요
이 프로젝트는 Cloud Run 배포를 간단하게 테스트하고 디버깅하기 위한 실험용 FastAPI 애플리케이션입니다.

## 프로젝트 구조
```
cloud-run-experiment/
├── main.py                    # 간단한 FastAPI 앱
├── pyproject.toml            # uv 의존성 파일
├── uv.lock                   # uv 락 파일
├── Dockerfile                # 단순한 Dockerfile
├── deploy.sh                 # Cloud Run 배포 스크립트
├── .github/workflows/deploy.yml  # GitHub Actions 워크플로우
└── README.md                 # 이 파일
```

## 주요 특징

### 1. 간단한 FastAPI 앱 (main.py)
- `/` : 기본 엔드포인트
- `/health` : 헬스체크 엔드포인트
- `/test` : 테스트 엔드포인트
- 환경변수 정보 출력

### 2. 단순한 Dockerfile
- 단일 단계 빌드 (multi-stage 없음)
- uv 사용한 의존성 관리
- 상세한 로그 출력

### 3. 디버깅 친화적인 배포 스크립트
- `set -x` 로 모든 명령어 출력
- 단계별 로그 메시지
- 헬스체크 및 API 테스트 포함

### 4. GitHub Actions 워크플로우
- 기본 검증 단계
- 실험용 배포 단계
- 서비스 검증 단계
- 결과 알림 단계

## 사용 방법

### 로컬 개발
```bash
# 의존성 설치
uv sync

# 로컬 실행
uv run uvicorn main:app --reload --port 8080

# 테스트
curl http://localhost:8080/health
```

### 수동 배포
```bash
# 배포 스크립트 실행
./deploy.sh

# 또는 환경변수 설정 후 실행
export PROJECT_ID=your-project-id
export SERVICE_NAME=your-service-name
export REGION=asia-northeast3
./deploy.sh
```

### GitHub Actions 배포
1. GitHub 저장소에 코드 푸시
2. GitHub Secrets에 `GCP_SA_KEY` 설정
3. `main` 브랜치에 푸시하면 자동 배포

## 필요한 Google Cloud 설정

### 1. 프로젝트 설정
```bash
export PROJECT_ID=xai-community
gcloud config set project $PROJECT_ID
```

### 2. API 활성화
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### 3. 서비스 계정 생성 (GitHub Actions용)
```bash
gcloud iam service-accounts create cloud-run-deployer \
    --display-name="Cloud Run Deployer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-run-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-run-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"

gcloud iam service-accounts keys create key.json \
    --iam-account=cloud-run-deployer@$PROJECT_ID.iam.gserviceaccount.com
```

## 디버깅 팁

### 1. 로컬 Docker 빌드 테스트
```bash
docker build -t cloud-run-experiment .
docker run -p 8080:8080 cloud-run-experiment
```

### 2. Cloud Build 로그 확인
```bash
# 최근 빌드 로그 확인
gcloud builds log --limit=1

# 특정 빌드 ID 로그 확인
gcloud builds log [BUILD_ID]
```

### 3. Cloud Run 서비스 로그 확인
```bash
# 서비스 로그 확인
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=cloud-run-experiment" --limit 50

# 실시간 로그 스트리밍
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=cloud-run-experiment"
```

### 4. 서비스 상태 확인
```bash
# 서비스 상세 정보
gcloud run services describe cloud-run-experiment --region=asia-northeast3

# 서비스 목록
gcloud run services list --region=asia-northeast3
```

## 주요 환경변수

- `PROJECT_ID`: Google Cloud 프로젝트 ID (기본값: xai-community)
- `SERVICE_NAME`: Cloud Run 서비스명 (기본값: cloud-run-experiment)
- `REGION`: 배포 리전 (기본값: asia-northeast3)
- `ENVIRONMENT`: 환경 구분 (기본값: production)
- `LOG_LEVEL`: 로그 레벨 (기본값: info)

## 테스트 URL

배포 후 다음 URL들로 테스트할 수 있습니다:

- 메인: `https://cloud-run-experiment-[hash]-du.a.run.app/`
- 헬스체크: `https://cloud-run-experiment-[hash]-du.a.run.app/health`
- 테스트: `https://cloud-run-experiment-[hash]-du.a.run.app/test`

## 문제 해결

### 1. 배포 실패 시
1. GitHub Actions 로그 확인
2. Google Cloud Build 로그 확인
3. Cloud Run 서비스 로그 확인

### 2. 헬스체크 실패 시
1. 서비스 상태 확인
2. 환경변수 설정 확인
3. 컨테이너 로그 확인

### 3. 권한 오류 시
1. 서비스 계정 권한 확인
2. API 활성화 상태 확인
3. 프로젝트 ID 확인

## 현재 프로젝트 적용 방안

이 실험이 성공하면 다음과 같이 현재 프로젝트에 적용할 수 있습니다:

1. **로깅 개선**: `set -x` 및 상세한 로그 메시지 추가
2. **단계별 검증**: 각 단계별 성공/실패 확인
3. **에러 처리**: 명확한 에러 메시지 및 디버깅 정보
4. **헬스체크 강화**: 더 안정적인 헬스체크 로직
5. **배포 단순화**: 복잡한 환경변수 설정 최적화