#!/bin/bash

# Cloud Run 배포 스크립트
# 사용법: ./deploy-cloud-run.sh

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

# .env.prod 파일에서 환경변수 로드
if [ -f ".env.prod" ]; then
    log_info ".env.prod 파일에서 환경변수 로드 중..."
    log_info "파일 내용 확인: $(head -n 5 .env.prod)"
    set -a
    source .env.prod
    set +a
    log_success "환경변수 로드 완료"
else
    log_error ".env.prod 파일이 없습니다!"
    exit 1
fi

# 필수 환경변수 확인
log_info "필수 환경변수 확인 중..."
required_vars=("PROJECT_ID" "SERVICE_NAME" "REGION" "MONGODB_URL" "SECRET_KEY" "DATABASE_NAME")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "환경변수 $var가 설정되지 않았습니다!"
        exit 1
    else
        log_info "$var = ${!var}"
    fi
done
log_success "필수 환경변수 확인 완료"

# Google Cloud 인증 상태 확인
log_info "Google Cloud 인증 상태 확인 중..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "Google Cloud 인증이 필요합니다! 'gcloud auth login' 실행 후 다시 시도해주세요."
    exit 1
fi
log_success "Google Cloud 인증 확인 완료"

# Google Cloud 프로젝트 설정
log_info "Google Cloud 프로젝트 설정 중..."
if ! gcloud config set project "$PROJECT_ID" 2>&1; then
    log_error "프로젝트 설정 실패: $PROJECT_ID"
    exit 1
fi
log_success "프로젝트 설정 완료: $PROJECT_ID"

# 필요한 서비스 활성화
log_info "Google Cloud 서비스 활성화 중..."
if ! gcloud services enable cloudbuild.googleapis.com 2>&1; then
    log_error "Cloud Build API 활성화 실패"
    exit 1
fi
if ! gcloud services enable run.googleapis.com 2>&1; then
    log_error "Cloud Run API 활성화 실패"
    exit 1
fi
log_success "서비스 활성화 완료"

# 현재 디렉토리 확인
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile이 현재 디렉토리에 없습니다!"
    exit 1
fi

# Cloud Run 배포
log_info "Cloud Run 서비스 배포 중..."
log_info "배포 설정:"
log_info "  - 서비스명: $SERVICE_NAME"
log_info "  - 리전: $REGION"
log_info "  - 소스: $(pwd)"
log_info "  - Dockerfile 존재: $([ -f Dockerfile ] && echo '예' || echo '아니오')"

DEPLOY_OUTPUT=$(gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --port "$PORT" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 300 \
    --set-env-vars \
    ENVIRONMENT="$ENVIRONMENT",\
    MONGODB_URL="$MONGODB_URL",\
    DATABASE_NAME="$DATABASE_NAME",\
    SECRET_KEY="$SECRET_KEY",\
    ALLOWED_ORIGINS="$ALLOWED_ORIGINS",\
    FRONTEND_URL="$FRONTEND_URL",\
    PORT="$PORT",\
    LOG_LEVEL="$LOG_LEVEL",\
    MAX_COMMENT_DEPTH="$MAX_COMMENT_DEPTH",\
    ENABLE_DOCS="$ENABLE_DOCS",\
    ENABLE_CORS="$ENABLE_CORS",\
    REFRESH_TOKEN_EXPIRE_DAYS="$REFRESH_TOKEN_EXPIRE_DAYS" 2>&1)

DEPLOY_EXIT_CODE=$?
if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    log_success "Cloud Run 배포 완료!"
    echo "$DEPLOY_OUTPUT"
else
    log_error "Cloud Run 배포 실패! (Exit code: $DEPLOY_EXIT_CODE)"
    echo "$DEPLOY_OUTPUT"
    exit 1
fi

# 환경변수는 배포 시 함께 설정되므로 별도 업데이트 불필요
log_info "환경변수가 배포와 함께 설정되었습니다."

# 서비스 URL 확인
log_info "서비스 URL 확인 중..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
log_success "서비스 배포 완료!"
echo -e "${GREEN}서비스 URL: $SERVICE_URL${NC}"

# 배포 확인
log_info "배포 상태 확인 중..."
curl -f "$SERVICE_URL" -o /dev/null -s
if [ $? -eq 0 ]; then
    log_success "서비스가 정상적으로 응답합니다!"
else
    log_warning "서비스 응답 확인 실패. 수동으로 확인해주세요."
fi

# 로그 확인 가이드
echo -e "\n${BLUE}=== 배포 완료 ===\n"
echo -e "${GREEN}서비스 URL:${NC} $SERVICE_URL"
echo -e "${GREEN}Google Cloud Console:${NC} https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo -e "\n${YELLOW}로그 확인 명령어:${NC}"
echo -e "gcloud logs read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo -e "\n${YELLOW}서비스 관리 명령어:${NC}"
echo -e "gcloud run services describe $SERVICE_NAME --region $REGION"
echo -e "gcloud run services update $SERVICE_NAME --region $REGION"
echo -e "\n${GREEN}배포 완료!${NC}"