#!/bin/bash

# XAI Community Backend - Cloud Run 자동 배포 스크립트
# 작성일: 2025-07-08
# 참고: Cloud Run 자동배포 완전해결 가이드 기반

set -e  # 오류 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
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

# 설정 값들
PROJECT_ID="xai-community"
SERVICE_NAME="xai-community-backend"
REGION="asia-northeast3"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

log_info "=== XAI Community Backend Cloud Run 배포 시작 ==="
log_info "프로젝트 ID: $PROJECT_ID"
log_info "서비스명: $SERVICE_NAME"
log_info "리전: $REGION"
log_info "이미지명: $IMAGE_NAME"

# 배포 전 검증
log_info "배포 전 검증 시작..."

# 필수 파일 확인
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile이 현재 디렉토리에 없습니다!"
    exit 1
fi

if [ ! -f "main.py" ]; then
    log_error "main.py가 현재 디렉토리에 없습니다!"
    exit 1
fi

if [ ! -f "pyproject.toml" ]; then
    log_error "pyproject.toml이 현재 디렉토리에 없습니다!"
    exit 1
fi

log_success "필수 파일 확인 완료"

# gcloud CLI 설치 및 인증 확인
log_info "gcloud CLI 확인 중..."
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI가 설치되지 않았습니다!"
    exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "Google Cloud 인증이 필요합니다!"
    log_info "다음 명령을 실행하여 인증하세요:"
    log_info "gcloud auth login"
    exit 1
fi

log_success "gcloud CLI 및 인증 확인 완료"

# 프로젝트 설정
log_info "Google Cloud 프로젝트 설정 중..."
gcloud config set project $PROJECT_ID --quiet
log_success "프로젝트 설정 완료: $PROJECT_ID"

# API 활성화
log_info "필요한 Google Cloud API 활성화 중..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID --quiet
gcloud services enable run.googleapis.com --project=$PROJECT_ID --quiet
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID --quiet
log_success "API 활성화 완료"

# Docker 이미지 빌드
log_info "Docker 이미지 빌드 시작..."
log_info "빌드 명령: gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID"

if gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID --quiet; then
    log_success "Docker 이미지 빌드 완료!"
else
    log_error "Docker 이미지 빌드 실패!"
    exit 1
fi

# Cloud Run 배포
log_info "Cloud Run 서비스 배포 중..."
log_info "배포 설정:"
log_info "  - 서비스명: $SERVICE_NAME"
log_info "  - 리전: $REGION"
log_info "  - 이미지: $IMAGE_NAME"

# 환경변수 파일 처리
ENV_FILE_FLAG=""
if [ -f ".env.prod" ]; then
    log_info ".env.prod 파일 발견 - env-vars-file 옵션 사용"
    ENV_FILE_FLAG="--env-vars-file .env.prod"
else
    log_warning ".env.prod 파일이 없습니다. 기본 환경변수만 사용합니다."
fi

DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
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
    --set-env-vars ENVIRONMENT=production \
    --project=$PROJECT_ID \
    --quiet"

if [ -n "$ENV_FILE_FLAG" ]; then
    DEPLOY_CMD="$DEPLOY_CMD $ENV_FILE_FLAG"
fi

log_info "배포 명령 실행 중..."
if eval $DEPLOY_CMD; then
    log_success "Cloud Run 배포 완료!"
else
    log_error "Cloud Run 배포 실패!"
    exit 1
fi

# 서비스 URL 확인
log_info "서비스 URL 확인 중..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" --project=$PROJECT_ID --quiet)

if [ -n "$SERVICE_URL" ]; then
    log_success "서비스 배포 완료!"
    echo -e "${GREEN}서비스 URL: $SERVICE_URL${NC}"
else
    log_error "서비스 URL 확인 실패!"
    exit 1
fi

# 자동 헬스체크 (참고 문서의 성공 패턴)
log_info "서비스 헬스체크 시작..."
log_info "서비스 준비 상태 확인 중 (최대 60초 대기)..."

for i in {1..12}; do
    if curl -s -f "$SERVICE_URL/health" >/dev/null 2>&1; then
        log_success "서비스가 준비되었습니다!"
        break
    fi
    
    if [ $i -eq 12 ]; then
        log_warning "헬스체크 타임아웃 - 서비스가 아직 준비되지 않았을 수 있습니다."
        log_info "수동으로 확인해주세요: $SERVICE_URL/health"
    else
        log_info "서비스 준비 중... ($i/12) - 5초 후 재시도"
        sleep 5
    fi
done

# 기본 엔드포인트 테스트
log_info "기본 엔드포인트 테스트 중..."
if curl -s -f "$SERVICE_URL/" >/dev/null 2>&1; then
    log_success "기본 엔드포인트 정상!"
else
    log_warning "기본 엔드포인트 확인 실패 - 서비스가 아직 시작 중일 수 있습니다."
fi

# 배포 완료 정보 출력
echo -e "\n${BLUE}=== 배포 완료 ===\n"
echo -e "${GREEN}서비스 URL:${NC} $SERVICE_URL"
echo -e "${GREEN}API 문서:${NC} $SERVICE_URL/docs"
echo -e "${GREEN}헬스체크:${NC} $SERVICE_URL/health"
echo -e "${GREEN}Google Cloud Console:${NC} https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"

echo -e "\n${YELLOW}테스트 가능한 엔드포인트:${NC}"
echo -e "- 기본: $SERVICE_URL/"
echo -e "- 헬스체크: $SERVICE_URL/health"
echo -e "- 전체 헬스체크: $SERVICE_URL/health/full"
echo -e "- API 문서: $SERVICE_URL/docs"

echo -e "\n${YELLOW}로그 확인 명령어:${NC}"
echo -e "gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"

echo -e "\n${YELLOW}서비스 관리 명령어:${NC}"
echo -e "gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo -e "gcloud run services delete $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --quiet"

echo -e "\n${GREEN}✅ XAI Community Backend 배포 완료! 🎉${NC}"