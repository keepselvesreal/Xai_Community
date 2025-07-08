#!/bin/bash

# FastAPI 테스트 Cloud Run 배포 스크립트
# 사용법: ./deploy-fastapi-test.sh

set -e  # 에러 시 스크립트 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정 값들 (고정값 사용)
PROJECT_ID="xai-community"
REGION="asia-northeast3"  # 서울 리전
SERVICE_NAME="fastapi-test-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info "========================================="
log_info "   FastAPI 테스트 서버 배포 시작"
log_info "========================================="

log_info "프로젝트 ID: $PROJECT_ID"
log_info "리전: $REGION"
log_info "서비스 이름: $SERVICE_NAME"
log_info "이미지 이름: $IMAGE_NAME"

# 현재 디렉토리 확인
log_info "현재 디렉토리: $SCRIPT_DIR"

# 필수 파일 확인
log_info "필수 파일 확인 중..."
if [ ! -f "$SCRIPT_DIR/Dockerfile" ]; then
    log_error "Dockerfile을 찾을 수 없습니다."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    log_error "main.py를 찾을 수 없습니다."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/requirements.txt" ]; then
    log_error "requirements.txt를 찾을 수 없습니다."
    exit 1
fi

log_success "필수 파일 확인 완료"

# gcloud CLI 설치 확인
log_info "gcloud CLI 설치 확인 중..."
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI가 설치되지 않았습니다."
    log_info "설치 방법: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

log_success "gcloud CLI 확인 완료"

# gcloud 인증 확인
log_info "gcloud 인증 상태 확인 중..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    log_error "gcloud 인증이 필요합니다."
    log_info "인증 명령: gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
log_success "인증된 계정: $ACTIVE_ACCOUNT"

# 프로젝트 설정
log_info "프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
log_info "필요한 API 활성화 중..."
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet

log_success "API 활성화 완료"

# Docker 이미지 빌드
log_info "Docker 이미지 빌드 시작..."
cd "$SCRIPT_DIR"

log_info "빌드 진행 상황을 모니터링합니다..."
if ! gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID .; then
    log_error "Docker 이미지 빌드 실패"
    exit 1
fi

log_success "Docker 이미지 빌드 완료: $IMAGE_NAME"

# Cloud Run 배포
log_info "Cloud Run 서비스 배포 시작..."

if ! gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --concurrency 100 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "ENVIRONMENT=production" \
    --project=$PROJECT_ID \
    --quiet; then
    log_error "Cloud Run 배포 실패"
    exit 1
fi

log_success "Cloud Run 배포 완료!"

# 서비스 URL 가져오기
log_info "서비스 URL 가져오는 중..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    log_error "서비스 URL을 가져올 수 없습니다."
    exit 1
fi

log_success "배포 완료! 서비스 URL: $SERVICE_URL"

# 배포 확인
log_info "배포 상태 확인 중..."
echo ""
echo "========================================="
echo "           배포 결과"
echo "========================================="
echo "서비스 이름: $SERVICE_NAME"
echo "리전: $REGION"
echo "이미지: $IMAGE_NAME"
echo "서비스 URL: $SERVICE_URL"
echo ""
echo "테스트 URL들:"
echo "  - 기본: $SERVICE_URL"
echo "  - 헬스체크: $SERVICE_URL/health"
echo "  - 환경 정보: $SERVICE_URL/env"
echo "  - API 문서: $SERVICE_URL/docs"
echo "  - 디버그 환경변수: $SERVICE_URL/debug/all-env"
echo ""

# 자동 헬스체크
log_info "자동 헬스체크 수행 중..."
if command -v curl &> /dev/null; then
    log_info "서비스 준비 대기 중... (최대 60초)"
    for i in {1..12}; do
        if curl -s -f "$SERVICE_URL/health" >/dev/null 2>&1; then
            log_success "서비스가 준비되었습니다!"
            break
        fi
        if [ $i -eq 12 ]; then
            log_error "서비스 준비 시간 초과"
            exit 1
        fi
        echo "대기 중... ($i/12)"
        sleep 5
    done
    
    echo "헬스체크 결과:"
    if curl -s -f "$SERVICE_URL/health" | python3 -m json.tool 2>/dev/null; then
        log_success "헬스체크 성공!"
    else
        log_warning "헬스체크 응답을 받았지만 JSON 파싱에 실패했습니다."
        echo "Raw 응답:"
        curl -s "$SERVICE_URL/health" || log_error "헬스체크 실패"
    fi
else
    log_warning "curl이 설치되지 않아 자동 헬스체크를 수행할 수 없습니다."
fi

echo ""
log_success "FastAPI 테스트 서버 배포 완료!"
echo "문제가 발생한 경우 다음 명령으로 로그를 확인하세요:"
echo "gcloud run services logs read $SERVICE_NAME --region $REGION"