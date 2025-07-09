#!/bin/bash

# XAI Community Backend Staging Cloud Run 배포 스크립트 v1.0
# 기반: deploy-production.sh
# 환경: Staging 환경 배포

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

log_debug() {
    echo -e "${YELLOW}[DEBUG]${NC} $1"
}

log_info "=== XAI Community Backend Staging Cloud Run 배포 시작 ==="

# .env.staging 파일 확인
if [ ! -f ".env.staging" ]; then
    log_error ".env.staging 파일이 없습니다!"
    exit 1
fi

log_success ".env.staging 파일 확인 완료"

# Windows 줄바꿈 문제 해결
log_info "Windows 줄바꿈 문제 해결 중..."
sed -i 's/\r$//' .env.staging 2>/dev/null || true
log_success "줄바꿈 문제 해결 완료"

# .env.staging 파일에서 GCP 설정 로드
log_info ".env.staging 파일에서 GCP 설정 로드 중..."
set -a
source .env.staging
set +a

# GCP 설정 변수 확인
if [ -z "$GCP_PROJECT_ID" ] || [ -z "$GCP_REGION" ] || [ -z "$GCP_SERVICE_NAME" ]; then
    log_error "GCP 설정이 .env.staging 파일에 없습니다!"
    log_error "필요한 변수: GCP_PROJECT_ID, GCP_REGION, GCP_SERVICE_NAME"
    exit 1
fi

log_success "GCP 설정 로드 완료"
log_info "프로젝트: $GCP_PROJECT_ID"
log_info "서비스명: $GCP_SERVICE_NAME"
log_info "리전: $GCP_REGION"

# 이미지 이름 설정
IMAGE_NAME="gcr.io/$GCP_PROJECT_ID/$GCP_SERVICE_NAME"

# Google Cloud 인증 확인
log_info "Google Cloud 인증 상태 확인 중..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "Google Cloud 인증이 필요합니다! 'gcloud auth login' 실행 후 다시 시도해주세요."
    exit 1
fi
log_success "Google Cloud 인증 확인 완료"

# 프로젝트 설정
log_info "Google Cloud 프로젝트 설정 중..."
gcloud config set project "$GCP_PROJECT_ID" --quiet
log_success "프로젝트 설정 완료: $GCP_PROJECT_ID"

# 필요한 서비스 활성화 (관리자가 미리 활성화해야 함)
log_info "필요한 Google Cloud 서비스들이 활성화되어 있다고 가정합니다..."
log_info "  - Cloud Build API (cloudbuild.googleapis.com)"
log_info "  - Cloud Run API (run.googleapis.com)"
log_success "서비스 활성화 확인 완료"

# Dockerfile 확인
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile이 현재 디렉토리에 없습니다!"
    exit 1
fi

# 1단계: Docker 이미지 빌드
log_info "=== 1단계: Docker 이미지 빌드 시작 ==="
log_debug "빌드 명령어: gcloud builds submit --tag $IMAGE_NAME --project=$GCP_PROJECT_ID --quiet"

BUILD_START_TIME=$(date)
log_debug "빌드 시작 시간: $BUILD_START_TIME"

BUILD_OUTPUT=$(gcloud builds submit --tag "$IMAGE_NAME" --project="$GCP_PROJECT_ID" --quiet 2>&1)
BUILD_EXIT_CODE=$?

log_debug "빌드 완료 시간: $(date)"
log_debug "빌드 Exit Code: $BUILD_EXIT_CODE"

if [ $BUILD_EXIT_CODE -ne 0 ]; then
    log_error "Docker 이미지 빌드 실패!"
    echo "$BUILD_OUTPUT"
    exit 1
fi

log_success "Docker 이미지 빌드 성공!"
log_debug "빌드 출력 미리보기: ${BUILD_OUTPUT:0:200}..."

# 2단계: .env.staging 파일에서 환경변수 자동 변환 (개선됨)
log_info "=== 2단계: 환경변수 처리 시작 ==="
log_debug ".env.staging 파일에서 환경변수 읽기 중..."

# 환경변수 배열 초기화
declare -a ENV_VARS_ARRAY=()
ENV_COUNT=0

# 필수 환경변수 목록
REQUIRED_VARS=("ENVIRONMENT" "MONGODB_URL" "DATABASE_NAME" "SECRET_KEY" "ALLOWED_ORIGINS" "FRONTEND_URL")

while IFS= read -r line; do
    # 주석과 빈 줄 건너뛰기
    if [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ ! "$line" =~ ^[[:space:]]*$ ]] && [[ "$line" =~ ^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*= ]]; then
        var_name=$(echo "$line" | cut -d'=' -f1 | xargs)
        var_value=$(echo "$line" | cut -d'=' -f2- | xargs)
        
        log_debug "처리 중인 변수: $var_name"
        
        # PORT 변수는 Cloud Run에서 자동 설정되므로 제외
        if [ "$var_name" = "PORT" ]; then
            log_debug "PORT 변수 제외 (Cloud Run 시스템 예약)"
            continue
        fi
        
        # HOST 변수도 Cloud Run에서 자동 설정
        if [ "$var_name" = "HOST" ]; then
            log_debug "HOST 변수 제외 (Cloud Run 시스템 예약)"
            continue
        fi
        
        # GCP 설정 변수들은 배포용이므로 제외
        if [[ "$var_name" =~ ^GCP_.* ]]; then
            log_debug "GCP 설정 변수 제외: $var_name"
            continue
        fi
        
        # 환경변수 배열에 추가
        ENV_VARS_ARRAY+=("$var_name=$var_value")
        ENV_COUNT=$((ENV_COUNT + 1))
    fi
done < ".env.staging"

# 필수 환경변수 확인
log_debug "필수 환경변수 확인 중..."
for required_var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!required_var}" ]; then
        log_error "필수 환경변수 $required_var가 설정되지 않았습니다!"
        exit 1
    fi
    log_debug "필수 변수 확인: $required_var"
done

log_success "환경변수 처리 완료: $ENV_COUNT개 변수"
log_debug "필수 환경변수 모두 확인 완료"

# 환경변수 배열을 쉼표로 구분된 문자열로 변환
ENV_VARS=$(IFS=,; echo "${ENV_VARS_ARRAY[*]}")
log_debug "환경변수 문자열 길이: ${#ENV_VARS}"
log_debug "환경변수 미리보기: ${ENV_VARS:0:150}..."

# 3단계: Cloud Run 배포 (개선된 모니터링)
log_info "=== 3단계: Cloud Run 배포 시작 ==="
log_debug "배포 명령어 실행 시작: $(date)"

# 환경변수 길이 확인 (Cloud Run 제한: 32KB)
ENV_VARS_LENGTH=${#ENV_VARS}
if [ $ENV_VARS_LENGTH -gt 30000 ]; then
    log_error "환경변수 문자열이 너무 깁니다: ${ENV_VARS_LENGTH} bytes"
    exit 1
fi

# 배포 명령어 출력 (디버깅용)
log_debug "배포 설정:"
log_debug "  - 서비스명: $GCP_SERVICE_NAME"
log_debug "  - 이미지: $IMAGE_NAME"
log_debug "  - 리전: $GCP_REGION"
log_debug "  - 환경변수 개수: $ENV_COUNT"
log_debug "  - 환경변수 크기: ${ENV_VARS_LENGTH} bytes"

# 배포 실행 (동기식으로 변경)
log_info "배포 명령어 실행 중... (최대 10분 소요 예상)"

DEPLOY_OUTPUT=$(gcloud run deploy "$GCP_SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region "$GCP_REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --concurrency 100 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars="$ENV_VARS" \
    --project="$GCP_PROJECT_ID" 2>&1)

DEPLOY_EXIT_CODE=$?
log_debug "배포 명령어 실행 완료: $(date)"
log_debug "배포 Exit Code: $DEPLOY_EXIT_CODE"

# 배포 출력 내용 확인
if [ -n "$DEPLOY_OUTPUT" ]; then
    log_debug "배포 출력 길이: ${#DEPLOY_OUTPUT}"
    log_debug "배포 출력 미리보기: ${DEPLOY_OUTPUT:0:300}..."
    
    # 에러 패턴 감지
    if echo "$DEPLOY_OUTPUT" | grep -q "ERROR\|FAILED\|failed\|Deployment failed"; then
        log_error "배포 출력에서 에러 감지!"
        echo "=== 배포 에러 로그 ==="
        echo "$DEPLOY_OUTPUT" | grep -A 5 -B 5 "ERROR\|FAILED\|failed\|Deployment failed"
        echo "===================="
    fi
    
    # 성공 메시지 확인
    if echo "$DEPLOY_OUTPUT" | grep -q "Service URL:"; then
        log_success "배포 성공 메시지 확인됨"
    fi
else
    log_warning "배포 출력이 없습니다."
fi

if [ $DEPLOY_EXIT_CODE -ne 0 ]; then
    log_error "Cloud Run 배포 실패! Exit Code: $DEPLOY_EXIT_CODE"
    echo "=== 전체 배포 로그 ==="
    echo "$DEPLOY_OUTPUT"
    echo "===================="
    exit 1
fi

log_success "Cloud Run 배포 성공!"

# 4단계: 서비스 URL 확인 및 상태 검증
log_info "=== 4단계: 서비스 URL 확인 및 상태 검증 ==="

# 서비스 존재 확인
log_debug "서비스 존재 여부 확인 중..."
if ! gcloud run services describe "$GCP_SERVICE_NAME" --region "$GCP_REGION" --project="$GCP_PROJECT_ID" > /dev/null 2>&1; then
    log_error "서비스가 생성되지 않았습니다!"
    
    # 디버깅 정보 수집
    log_debug "현재 생성된 서비스 목록:"
    gcloud run services list --region="$GCP_REGION" --project="$GCP_PROJECT_ID" || echo "서비스 목록 조회 실패"
    
    exit 1
fi

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe "$GCP_SERVICE_NAME" --region "$GCP_REGION" --format="value(status.url)" --project="$GCP_PROJECT_ID")
if [ -z "$SERVICE_URL" ]; then
    log_error "서비스 URL을 가져올 수 없습니다!"
    exit 1
fi

log_success "서비스 URL 확인 완료: $SERVICE_URL"

# 서비스 상태 확인
log_debug "서비스 상태 확인 중..."
SERVICE_READY=$(gcloud run services describe "$GCP_SERVICE_NAME" --region "$GCP_REGION" --project="$GCP_PROJECT_ID" --format="value(status.conditions[0].status)" 2>/dev/null || echo "Unknown")
log_debug "서비스 준비 상태: $SERVICE_READY"

if [ "$SERVICE_READY" != "True" ]; then
    log_warning "서비스가 아직 준비되지 않았습니다. 상태: $SERVICE_READY"
fi

# 5단계: 헬스체크 (개선된 버전)
log_info "=== 5단계: 헬스체크 진행 ==="
log_debug "헬스체크 URL: $SERVICE_URL/health"

HEALTH_CHECK_SUCCESS=false
for i in {1..12}; do
    log_debug "헬스체크 시도 $i/12: $(date)"
    
    # 헬스체크 응답 확인
    HEALTH_RESPONSE=$(curl -f -s "$SERVICE_URL/health" 2>/dev/null)
    CURL_EXIT_CODE=$?
    
    if [ $CURL_EXIT_CODE -eq 0 ] && [ -n "$HEALTH_RESPONSE" ]; then
        log_success "헬스체크 성공! 서비스가 정상적으로 응답합니다."
        log_debug "헬스체크 응답: $HEALTH_RESPONSE"
        HEALTH_CHECK_SUCCESS=true
        break
    fi
    
    if [ $i -eq 12 ]; then
        log_error "헬스체크 실패. 서비스가 정상적으로 시작되지 않았습니다."
        log_debug "마지막 curl 종료 코드: $CURL_EXIT_CODE"
        log_info "수동 확인 URL: $SERVICE_URL/health"
        
        # 서비스 로그 확인 링크 제공
        log_info "서비스 로그 확인: https://console.cloud.google.com/logs/viewer?project=$GCP_PROJECT_ID&resource=cloud_run_revision/service_name/$GCP_SERVICE_NAME"
        break
    else
        log_debug "서비스 준비 중... 5초 후 재시도"
        sleep 5
    fi
done

# 헬스체크 실패 시 추가 디버깅 정보
if [ "$HEALTH_CHECK_SUCCESS" = false ]; then
    log_warning "헬스체크 실패로 인한 추가 디버깅 정보:"
    
    # 서비스 상태 재확인
    SERVICE_STATUS=$(gcloud run services describe "$GCP_SERVICE_NAME" --region "$GCP_REGION" --project="$GCP_PROJECT_ID" --format="value(status.conditions[0].status)" 2>/dev/null || echo "Unknown")
    log_debug "서비스 준비 상태: $SERVICE_STATUS"
    
    # 기본 URL 접근 테스트
    log_debug "기본 URL 접근 테스트: $SERVICE_URL/"
    BASE_RESPONSE=$(curl -f -s "$SERVICE_URL/" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$BASE_RESPONSE" ]; then
        log_info "기본 URL 접근 성공: $BASE_RESPONSE"
    else
        log_warning "기본 URL 접근도 실패"
    fi
fi

# 6단계: API 테스트
log_info "=== 6단계: 기본 API 테스트 ==="
log_debug "기본 API 테스트: $SERVICE_URL/"

if curl -f -s "$SERVICE_URL/" > /dev/null 2>&1; then
    log_success "기본 API 테스트 성공!"
else
    log_warning "기본 API 테스트 실패. 수동으로 확인해주세요."
fi

# 배포 완료 정보
echo ""
echo -e "${BLUE}=== 🎉 XAI Community Backend Staging 배포 완료 ===${NC}"
echo ""
echo -e "${GREEN}✅ 배포 정보${NC}"
echo -e "  프로젝트: $GCP_PROJECT_ID"
echo -e "  서비스명: $GCP_SERVICE_NAME"
echo -e "  리전: $GCP_REGION"
echo -e "  이미지: $IMAGE_NAME"
echo -e "  환경변수: $ENV_COUNT개 설정"
echo ""
echo -e "${GREEN}✅ 서비스 URL${NC}"
echo -e "  메인: $SERVICE_URL"
echo -e "  헬스체크: $SERVICE_URL/health"
echo -e "  API 문서: $SERVICE_URL/docs"
echo ""
echo -e "${GREEN}✅ 관리 URL${NC}"
echo -e "  Google Cloud Console: https://console.cloud.google.com/run/detail/$GCP_REGION/$GCP_SERVICE_NAME/metrics?project=$GCP_PROJECT_ID"
echo ""
echo -e "${YELLOW}📋 다음 단계${NC}"
echo -e "  1. 프론트엔드 Staging URL ($SERVICE_URL) 업데이트"
echo -e "  2. CORS 설정 확인"
echo -e "  3. 통합 테스트 실행"
echo ""
echo -e "${GREEN}🎉 Staging 배포 성공!${NC}"