# Cloud Run 테스트 서버

Google Cloud Run 배포를 테스트하기 위한 간단한 FastAPI 서버입니다.

## 📋 구성요소

- **main.py**: 메인 FastAPI 애플리케이션
- **Dockerfile**: Cloud Run 최적화된 컨테이너 이미지
- **requirements.txt**: Python 의존성 목록
- **deploy.sh**: 자동 배포 스크립트

## 🚀 빠른 시작

### 1. 로컬 테스트

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

서버가 시작되면 http://localhost:8080 에서 확인할 수 있습니다.

### 2. Cloud Run 배포

```bash
# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh YOUR_PROJECT_ID
```

## 🎯 주요 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `/` | 기본 상태 확인 |
| `/health` | 헬스체크 |
| `/docs` | API 문서 (Swagger UI) |
| `/env` | 환경변수 정보 (안전한 정보만) |
| `/debug/all-env` | 모든 환경변수 (민감 정보 마스킹) |
| `/debug/request-info` | 요청 정보 디버깅 |
| `/debug/echo` | 요청 데이터 에코 |
| `/metrics` | 서버 메트릭 |
| `/test/error` | 에러 테스트 |
| `/test/log` | 로그 테스트 |

## 🔧 설정 옵션

### 환경변수

- `PORT`: 서버 포트 (기본값: 8080)
- `ENVIRONMENT`: 실행 환경 (development/production)
- `GOOGLE_CLOUD_PROJECT`: Google Cloud 프로젝트 ID

### 배포 스크립트 파라미터

```bash
./deploy.sh [PROJECT_ID] [REGION] [SERVICE_NAME]
```

- `PROJECT_ID`: Google Cloud 프로젝트 ID (필수)
- `REGION`: 배포 리전 (기본값: asia-northeast3)
- `SERVICE_NAME`: Cloud Run 서비스 이름 (기본값: cloud-run-test)

## 🐛 디버깅 기능

### 로그 확인

```bash
# Cloud Run 로그 확인
gcloud run services logs read cloud-run-test --region asia-northeast3

# 실시간 로그 스트림
gcloud run services logs tail cloud-run-test --region asia-northeast3
```

### 로컬 디버깅

```bash
# 로컬에서 Docker 이미지 빌드 및 실행
docker build -t cloud-run-test .
docker run -p 8080:8080 -e PORT=8080 cloud-run-test
```

## 📊 모니터링

서버는 다음 정보를 제공합니다:

- 요청/응답 로깅
- 업타임 추적
- 환경변수 상태
- 시스템 정보
- 에러 추적

## 🔍 문제해결

### 일반적인 문제들

1. **배포 실패**
   - gcloud CLI 인증 확인: `gcloud auth list`
   - 프로젝트 설정 확인: `gcloud config get-value project`
   - API 활성화 상태 확인

2. **서비스 접근 불가**
   - Cloud Run 서비스 상태 확인
   - 방화벽 설정 확인
   - 헬스체크 엔드포인트 테스트

3. **로그 관련 문제**
   - `/test/log` 엔드포인트로 로그 출력 테스트
   - Cloud Console에서 로그 확인

### 유용한 명령어

```bash
# 서비스 상태 확인
gcloud run services describe cloud-run-test --region asia-northeast3

# 서비스 삭제
gcloud run services delete cloud-run-test --region asia-northeast3

# 트래픽 설정
gcloud run services update-traffic cloud-run-test --to-latest --region asia-northeast3
```

## 📝 다음 단계

이 테스트 서버로 Cloud Run 배포가 성공하면:

1. 기존 백엔드 애플리케이션의 Dockerfile 최적화
2. 환경변수 설정 단순화
3. 의존성 최적화
4. 프로덕션 환경 설정 검토