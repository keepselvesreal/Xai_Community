#!/bin/bash

# Cloud Run 실험용 배포 스크립트
# 간단하고 디버깅이 쉬운 버전

set -e  # 오류 시 스크립트 중단
set -x  # 모든 명령어 출력 (디버깅용)

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "=== Cloud Run 실험용 배포 시작 ==="

# 기본 설정
PROJECT_ID=${PROJECT_ID:-"xai-community"}
SERVICE_NAME=${SERVICE_NAME:-"cloud-run-experiment"}
REGION=${REGION:-"asia-northeast3"}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

log_info "배포 설정:"
log_info "  - 프로젝트 ID: $PROJECT_ID"
log_info "  - 서비스명: $SERVICE_NAME"
log_info "  - 리전: $REGION"
log_info "  - 이미지: $IMAGE_NAME"

# Google Cloud 인증 확인
log_info "Google Cloud 인증 상태 확인..."
gcloud auth list --filter=status:ACTIVE --format="value(account)"

# 프로젝트 설정
log_info "Google Cloud 프로젝트 설정..."
gcloud config set project "$PROJECT_ID"

# 필수 API 활성화
log_info "필수 API 활성화..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Dockerfile 확인
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile이 현재 디렉토리에 없습니다!"
    exit 1
fi

# 1단계: Docker 이미지 빌드
log_info "=== 1단계: Docker 이미지 빌드 ==="
log_info "빌드 시작: $(date)"

# 로그 스트리밍 문제 해결을 위해 --async 사용
BUILD_OUTPUT=$(gcloud builds submit --tag "$IMAGE_NAME" --project="$PROJECT_ID" --async 2>&1)
BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    # 빌드 ID 추출
    BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'builds/[a-zA-Z0-9-]*' | head -1 | cut -d'/' -f2)
    if [ -n "$BUILD_ID" ]; then
        log_info "빌드 ID: $BUILD_ID"
        log_info "빌드 상태 확인 중..."
        
        # 빌드 완료까지 대기
        while true; do
            BUILD_STATUS=$(gcloud builds describe "$BUILD_ID" --project="$PROJECT_ID" --format="value(status)" 2>/dev/null)
            case "$BUILD_STATUS" in
                "SUCCESS")
                    log_success "빌드 완료!"
                    break
                    ;;
                "FAILURE"|"CANCELLED"|"TIMEOUT")
                    log_error "빌드 실패: $BUILD_STATUS"
                    BUILD_EXIT_CODE=1
                    break
                    ;;
                "QUEUED"|"WORKING")
                    log_info "빌드 진행 중... ($BUILD_STATUS)"
                    sleep 10
                    ;;
                *)
                    log_warning "알 수 없는 빌드 상태: $BUILD_STATUS"
                    sleep 10
                    ;;
            esac
        done
    fi
fi

log_info "빌드 완료: $(date)"
log_info "빌드 Exit Code: $BUILD_EXIT_CODE"

if [ $BUILD_EXIT_CODE -ne 0 ]; then
    log_error "Docker 이미지 빌드 실패!"
    echo "=== 빌드 출력 ==="
    echo "$BUILD_OUTPUT"
    echo "==================="
    
    # 빌드 ID 추출해서 상세 정보 조회 시도
    BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'builds/[a-zA-Z0-9-]*' | head -1 | cut -d'/' -f2)
    if [ -n "$BUILD_ID" ]; then
        log_info "빌드 ID: $BUILD_ID"
        log_info "빌드 상세 정보 조회 중..."
        gcloud builds describe "$BUILD_ID" --project="$PROJECT_ID" --format="yaml" 2>&1 || echo "빌드 정보 조회 실패"
        
        log_info "Google Cloud Console에서 빌드 로그 확인:"
        log_info "https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"
    fi
    
    exit 1
fi

log_success "Docker 이미지 빌드 성공!"
echo "=== 빌드 출력 ==="
echo "$BUILD_OUTPUT"
echo "==================="

# 2단계: Cloud Run 배포
log_info "=== 2단계: Cloud Run 배포 ==="
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 5 \
    --timeout 300 \
    --set-env-vars \
    "ENVIRONMENT=production,LOG_LEVEL=info" \
    --project="$PROJECT_ID"

# 3단계: 서비스 URL 확인
log_info "=== 3단계: 서비스 URL 확인 ==="
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)" --project="$PROJECT_ID")
log_success "서비스 URL: $SERVICE_URL"

# 4단계: 헬스체크
log_info "=== 4단계: 헬스체크 ==="
sleep 10  # 서비스 시작 대기

for i in {1..6}; do
    log_info "헬스체크 시도 $i/6..."
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        log_success "헬스체크 성공!"
        break
    fi
    
    if [ $i -eq 6 ]; then
        log_error "헬스체크 실패"
        exit 1
    else
        log_info "5초 후 재시도..."
        sleep 5
    fi
done

# 5단계: 기본 API 테스트
log_info "=== 5단계: 기본 API 테스트 ==="
if curl -f -s "$SERVICE_URL/" > /dev/null; then
    log_success "기본 API 테스트 성공!"
else
    log_error "기본 API 테스트 실패"
    exit 1
fi

# 배포 완료
echo ""
log_success "=== 배포 완료! ==="
echo -e "${GREEN}서비스 URL: $SERVICE_URL${NC}"
echo -e "${GREEN}헬스체크: $SERVICE_URL/health${NC}"
echo -e "${GREEN}테스트: $SERVICE_URL/test${NC}"
echo ""
echo -e "${YELLOW}Google Cloud Console:${NC}"
echo -e "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"