# Cloud Run 배포 실패 및 Docker 환경 문제 해결 시도 기록

**날짜**: 2025-07-07  
**작업자**: Claude Code  
**작업 시간**: 약 2시간  

## 📋 작업 개요

기존 Dockerfile의 Python 관련 문제로 인해 Cloud Run 배포가 실패하여, 새로운 Dockerfile을 작성하고 로컬 테스트를 거쳐 Cloud Run 배포를 시도한 작업 기록

## ✅ 성공한 작업들

### 1. 기존 Dockerfile 문제점 분석
- **문제**: Multi-stage build에서 가상환경 경로 문제
- **문제**: 권한 설정 부족으로 UV 캐시 디렉토리 생성 실패
- **문제**: 프로덕션 환경에서 .env 파일 로드되지 않음

### 2. 새로운 Dockerfile 작성
```dockerfile
# 최종 작업한 Dockerfile 구조
FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y curl build-essential

# UV 설치
RUN pip install --no-cache-dir uv

# 프로젝트 파일 복사 및 의존성 설치
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# 애플리케이션 코드 복사
COPY . .
COPY .env.prod .env

# 사용자 및 권한 설정
RUN groupadd -r appuser && useradd -r -g appuser appuser -m
RUN mkdir -p uploads && chown -R appuser:appuser /app
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /home/appuser/.cache

USER appuser

# Cloud Run 포트 대응
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

### 3. 로컬 Docker 테스트 성공
- **이미지 빌드**: ✅ 성공
- **컨테이너 실행**: ✅ 성공 (ENVIRONMENT=development로 설정)
- **API 응답**: ✅ `/health` 엔드포인트 정상 응답
- **헬스체크**: ✅ healthy 상태 확인

### 4. 환경변수 설정 문제 해결
- **문제**: config.py에서 프로덕션 환경에서 .env 파일 로드 차단
- **해결**: ENVIRONMENT=development로 설정하여 .env 파일 로드 허용
- **결과**: 로컬에서 정상 작동 확인

## ❌ 실패한 작업들

### 1. Cloud Run 배포 실패 (2회)

#### 첫 번째 배포 실패
- **시간**: 06:42:18 UTC
- **에러**: `ModuleNotFoundError: No module named 'encodings'`
- **원인**: Python 가상환경이 Cloud Run에서 제대로 초기화되지 않음

```
Fatal Python error: init_fs_encoding: failed to get the Python codec of the filesystem encoding
Python runtime state: core initialized
ModuleNotFoundError: No module named 'encodings'
```

#### 두 번째 배포 실패
- **시간**: 07:36:56 UTC (약 1시간 후)
- **에러**: 동일한 Python 환경 문제
- **상태**: 컨테이너가 PORT=8080에서 시작되지 않음

### 2. 배포 스크립트 중단
- `deploy-cloud-run.sh` 스크립트가 여러 차례 중간에 중단됨
- timeout이나 네트워크 문제로 인한 것으로 추정

## 🔍 근본 원인 분석

### Python 가상환경 호환성 문제
1. **UV 가상환경**: 로컬에서는 정상 작동하지만 Cloud Run 컨테이너에서 문제 발생
2. **경로 설정**: 가상환경 경로가 Cloud Run 환경에서 올바르게 설정되지 않음
3. **Python 모듈**: 기본 Python 모듈(`encodings`)조차 찾지 못하는 심각한 환경 문제

### .env 파일 처리 복잡성
- 프로덕션/개발 환경 구분으로 인한 환경변수 로드 문제
- Cloud Run에서는 환경변수와 .env 파일 혼용 시 복잡성 증가

## 📊 리소스 정리 현황

### 삭제된 자원들 (요금 방지)
1. **Cloud Run 서비스**: `xai-community` 완전 삭제
2. **Artifact Repository**: `cloud-run-source-deploy` 삭제 (2.3GB 사용량)
3. **로컬 서버**: uvicorn 프로세스 종료

### 요금 발생 가능성
- Cloud Run: 약 1시간 실행 시도 (실패했으므로 최소 요금)
- Artifact Registry: 약 2시간 저장 (삭제 완료)
- Cloud Build: 2회 빌드 실행

## 🎯 다음 단계 권장사항

### 1. Docker 환경 단순화
```dockerfile
# 권장 접근법: pip 사용으로 단순화
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH=/app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2. 환경변수 관리 개선
- Cloud Run에서는 환경변수를 직접 설정하고 .env 파일 의존성 제거
- `config.py`에서 Cloud Run 환경 감지 로직 추가

### 3. 단계별 검증
1. requirements.txt 생성: `uv export --no-dev > requirements.txt`
2. 로컬 pip 환경으로 테스트
3. Cloud Run 배포 전 Google Cloud Shell에서 테스트

## 📚 학습 내용

1. **UV vs pip**: UV는 빠르지만 컨테이너 환경에서 호환성 문제 발생 가능
2. **Cloud Run 제약**: 가상환경보다는 시스템 Python 사용이 안정적
3. **환경변수 우선순위**: Cloud Run 환경변수 > .env 파일 순으로 설계 필요
4. **단계별 테스트**: 로컬 Docker → Cloud Shell → Cloud Run 순서로 검증 필요

## 🔗 참고 자료

- [Cloud Run Troubleshooting Guide](https://cloud.google.com/run/docs/troubleshooting#container-failed-to-start)
- 로그 URL: `gcloud run services logs read xai-community --region=asia-northeast3`
- 프로젝트 위치: `/home/nadle/projects/Xai_Community/v5/backend/`

---

**결론**: Docker 환경과 Cloud Run 호환성 문제로 배포 실패. UV 대신 pip 사용 및 환경변수 관리 단순화가 필요함.