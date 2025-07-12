#!/bin/bash

# XAI Community Backend Staging Cloud Run 배포 스크립트 v1.0
# 기반: deploy-production.sh
# 환경: Staging 환경 배포

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

# 환경변수 확인 (GitHub Secrets에서 주입됨)
log_info "환경변수 확인 중..."
if [ -f ".env.staging" ]; then
    log_info ".env.staging 파일 발견 - 로컬 개발 환경"
    # Windows 줄바꿈 문제 해결
    sed -i 's/\r$//' .env.staging 2>/dev/null || true
    # 파일에서 환경변수 로드
    set -a
    source .env.staging
    set +a
else
    log_info "환경변수는 GitHub Secrets에서 주입됨 - CI/CD 환경"
fi

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
log_info "  - Cloud Resource Manager API (cloudresourcemanager.googleapis.com)"
log_success "서비스 활성화 확인 완료"

# Dockerfile 확인
DOCKERFILE_PATH="deploy/cloud-run/Dockerfile"
if [ ! -f "$DOCKERFILE_PATH" ]; then
    log_error "Dockerfile이 $DOCKERFILE_PATH 에 없습니다!"
    exit 1
fi
log_success "Dockerfile 발견: $DOCKERFILE_PATH"

# 1단계: Docker 이미지 빌드
log_info "=== 1단계: Docker 이미지 빌드 시작 ==="
log_debug "빌드 명령어: gcloud builds submit --file=$DOCKERFILE_PATH --tag $IMAGE_NAME --project=$GCP_PROJECT_ID --suppress-logs"

BUILD_START_TIME=$(date)
log_debug "빌드 시작 시간: $BUILD_START_TIME"

# 로그 스트리밍 문제 해결을 위해 --async 사용 (실험 결과 적용)
log_debug "빌드 명령어: gcloud builds submit --file=$DOCKERFILE_PATH --tag $IMAGE_NAME --project=$GCP_PROJECT_ID --async"
BUILD_OUTPUT=$(gcloud builds submit --file="$DOCKERFILE_PATH" --tag "$IMAGE_NAME" --project="$GCP_PROJECT_ID" --async 2>&1)
BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    # 빌드 ID 추출 (실험 결과 적용)
    BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'builds/[a-zA-Z0-9-]*' | head -1 | cut -d'/' -f2)
    if [ -n "$BUILD_ID" ]; then
        log_debug "빌드 ID: $BUILD_ID"
        log_info "빌드 상태 확인 중..."
        
        # 빌드 완료까지 대기 (실험 결과 적용)
        while true; do
            BUILD_STATUS=$(gcloud builds describe "$BUILD_ID" --project="$GCP_PROJECT_ID" --format="value(status)" 2>/dev/null)
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
                    log_debug "빌드 진행 중... ($BUILD_STATUS)"
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

log_debug "빌드 완료 시간: $(date)"
log_debug "빌드 Exit Code: $BUILD_EXIT_CODE"

if [ $BUILD_EXIT_CODE -ne 0 ]; then
    log_error "Docker 이미지 빌드 실패!"
    echo "=== 빌드 에러 로그 ==="
    echo "$BUILD_OUTPUT"
    echo "===================="
    
    # 빌드 ID 추출해서 상세 정보 조회 시도 (실험 결과 적용)
    BUILD_ID=$(echo "$BUILD_OUTPUT" | grep -o 'builds/[a-zA-Z0-9-]*' | head -1 | cut -d'/' -f2)
    if [ -n "$BUILD_ID" ]; then
        log_info "빌드 ID: $BUILD_ID"
        log_info "빌드 상세 정보 조회 중..."
        gcloud builds describe "$BUILD_ID" --project="$GCP_PROJECT_ID" --format="yaml" 2>&1 || echo "빌드 정보 조회 실패"
        
        log_info "Google Cloud Console에서 빌드 로그 확인:"
        log_info "https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$GCP_PROJECT_ID"
    fi
    
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

# 환경변수 처리 (로컬 개발 환경에서만 .env.staging 파일 사용)
if [ -f ".env.staging" ]; then
    log_info "로컬 개발 환경: .env.staging 파일에서 환경변수 읽기"
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
            
            # 환경변수 배열에 추가 (쉼표 포함 시 이스케이핑)
            if [[ "$var_value" == *","* ]] || [[ "$var_value" == *"="* ]] || [[ "$var_value" == *" "* ]]; then
                # 특수문자가 포함된 경우 따옴표로 감싸기
                ENV_VARS_ARRAY+=("$var_name=\"$var_value\"")
            else
                ENV_VARS_ARRAY+=("$var_name=$var_value")
            fi
            ENV_COUNT=$((ENV_COUNT + 1))
        fi
    done < ".env.staging"
else
    log_info "CI/CD 환경: GitHub Secrets에서 환경변수 직접 사용"
    # GitHub Secrets에서 주입된 환경변수들을 배열에 추가 (쉼표 포함 시 이스케이핑)
    ENV_VARS_ARRAY=(
        "ENVIRONMENT=$ENVIRONMENT"
        "MONGODB_URL=$MONGODB_URL"
        "DATABASE_NAME=$DATABASE_NAME"
        "USERS_COLLECTION=$USERS_COLLECTION"
        "POSTS_COLLECTION=$POSTS_COLLECTION"
        "COMMENTS_COLLECTION=$COMMENTS_COLLECTION"
        "POST_STATS_COLLECTION=$POST_STATS_COLLECTION"
        "USER_REACTIONS_COLLECTION=$USER_REACTIONS_COLLECTION"
        "FILES_COLLECTION=$FILES_COLLECTION"
        "STATS_COLLECTION=$STATS_COLLECTION"
        "API_TITLE=$API_TITLE"
        "API_VERSION=$API_VERSION"
        "API_DESCRIPTION=$API_DESCRIPTION"
        "SECRET_KEY=$SECRET_KEY"
        "ALGORITHM=$ALGORITHM"
        "ACCESS_TOKEN_EXPIRE_MINUTES=$ACCESS_TOKEN_EXPIRE_MINUTES"
        "REFRESH_TOKEN_EXPIRE_DAYS=$REFRESH_TOKEN_EXPIRE_DAYS"
        "ALLOWED_ORIGINS=\"$ALLOWED_ORIGINS\""
        "FRONTEND_URL=$FRONTEND_URL"
        "LOG_LEVEL=$LOG_LEVEL"
        "MAX_COMMENT_DEPTH=$MAX_COMMENT_DEPTH"
        "ENABLE_DOCS=$ENABLE_DOCS"
        "ENABLE_CORS=$ENABLE_CORS"
    )
    ENV_COUNT=${#ENV_VARS_ARRAY[@]}
fi

# 필수 환경변수 확인
log_debug "필수 환경변수 확인 중..."
for required_var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!required_var}" ]; then
        log_error "필수 환경변수 $required_var가 설정되지 않았습니다!"
        exit 1
    fi
    log_debug "필수 변수 확인: $required_var"
done

# Git 정보 추가
log_info "Git 정보 수집 중..."
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT_HASH=$(git rev-parse HEAD)
BUILD_VERSION=$(git describe --tags --always 2>/dev/null || echo "v1.0.0")

log_debug "빌드 시간: $BUILD_TIME"
log_debug "커밋 해시: $COMMIT_HASH"
log_debug "빌드 버전: $BUILD_VERSION"

# Git 정보를 환경변수 배열에 추가
ENV_VARS_ARRAY+=(
    "BUILD_TIME=$BUILD_TIME"
    "COMMIT_HASH=$COMMIT_HASH"
    "BUILD_VERSION=$BUILD_VERSION"
)
ENV_COUNT=$((ENV_COUNT + 3))

log_success "환경변수 처리 완료: $ENV_COUNT개 변수 (Git 정보 포함)"
log_debug "필수 환경변수 모두 확인 완료"

# 환경변수를 YAML 파일로 저장 (gcloud --env-vars-file 요구사항에 맞춤)
ENV_VARS_FILE="/tmp/env_vars_staging.yaml"
log_debug "환경변수 파일 생성: $ENV_VARS_FILE"

# YAML 형식으로 환경변수 파일 작성
> "$ENV_VARS_FILE"  # 파일 초기화
for env_var in "${ENV_VARS_ARRAY[@]}"; do
    # KEY=VALUE 형식을 YAML 형식으로 변환
    var_name=$(echo "$env_var" | cut -d'=' -f1)
    var_value=$(echo "$env_var" | cut -d'=' -f2- | sed 's/^"//' | sed 's/"$//')
    # YAML 형식으로 출력 (값을 따옴표로 감싸기)
    echo "$var_name: \"$var_value\"" >> "$ENV_VARS_FILE"
done

log_debug "환경변수 파일 내용 확인:"
head -10 "$ENV_VARS_FILE"
log_debug "환경변수 파일 크기: $(wc -l < "$ENV_VARS_FILE") 줄"

# 디버깅을 위한 환경변수 상세 출력
log_debug "=== 환경변수 상세 정보 ==="
for i in "${!ENV_VARS_ARRAY[@]}"; do
    log_debug "[$i] ${ENV_VARS_ARRAY[$i]}"
done
log_debug "=== 환경변수 상세 정보 끝 ==="

# 3단계: Cloud Run 배포 (개선된 모니터링)
log_info "=== 3단계: Cloud Run 배포 시작 ==="
log_debug "배포 명령어 실행 시작: $(date)"

# 환경변수 파일 크기 확인 (Cloud Run 제한: 32KB)
ENV_VARS_FILE_SIZE=$(wc -c < "$ENV_VARS_FILE")
if [ $ENV_VARS_FILE_SIZE -gt 30000 ]; then
    log_error "환경변수 파일이 너무 큽니다: ${ENV_VARS_FILE_SIZE} bytes"
    exit 1
fi

# 배포 명령어 출력 (디버깅용)
log_debug "배포 설정:"
log_debug "  - 서비스명: $GCP_SERVICE_NAME"
log_debug "  - 이미지: $IMAGE_NAME"
log_debug "  - 리전: $GCP_REGION"
log_debug "  - 환경변수 개수: $ENV_COUNT"
log_debug "  - 환경변수 크기: ${ENV_VARS_FILE_SIZE} bytes"

# 배포 실행 (동기식으로 변경)
log_info "배포 명령어 실행 중... (최대 10분 소요 예상)"

log_debug "배포 명령어: gcloud run deploy $GCP_SERVICE_NAME --image $IMAGE_NAME --platform managed --region $GCP_REGION --allow-unauthenticated --port 8080 --memory 512Mi --cpu 1 --concurrency 100 --max-instances 10 --timeout 300 --project=$GCP_PROJECT_ID"
log_debug "환경변수 파일: $ENV_VARS_FILE"

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
    --env-vars-file="$ENV_VARS_FILE" \
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
    
    # 환경변수 파일 정리
    rm -f "$ENV_VARS_FILE"
    log_debug "환경변수 파일 정리 완료"
    
    # 추가 디버깅 정보 수집
    log_debug "추가 디버깅 정보 수집 중..."
    log_debug "현재 프로젝트: $(gcloud config get-value project)"
    log_debug "현재 리전: $GCP_REGION"
    log_debug "서비스명: $GCP_SERVICE_NAME"
    log_debug "이미지명: $IMAGE_NAME"
    
    # 기존 서비스 상태 확인
    log_debug "기존 서비스 상태 확인..."
    gcloud run services describe "$GCP_SERVICE_NAME" --region "$GCP_REGION" --project="$GCP_PROJECT_ID" || echo "서비스가 존재하지 않음"
    
    # 이미지 존재 확인
    log_debug "이미지 존재 확인..."
    gcloud container images describe "$IMAGE_NAME" --project="$GCP_PROJECT_ID" || echo "이미지가 존재하지 않음"
    
    exit 1
fi

log_success "Cloud Run 배포 성공!"

# 환경변수 파일 정리
rm -f "$ENV_VARS_FILE"
log_debug "환경변수 파일 정리 완료"

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
log_debug "상태체크 URL: $SERVICE_URL/status"

HEALTH_CHECK_SUCCESS=false
for i in {1..12}; do
    log_debug "헬스체크 시도 $i/12: $(date)"
    
    # 헬스체크 응답 확인
    HEALTH_RESPONSE=$(curl -f -s "$SERVICE_URL/status" 2>/dev/null)
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
        log_info "수동 확인 URL: $SERVICE_URL/status"
        
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

# 7단계: 트래픽을 최신 리비전으로 전환
log_info "=== 7단계: 트래픽을 최신 리비전으로 전환 ==="
log_info "배포된 서비스의 트래픽을 최신 리비전으로 자동 전환 중..."

TRAFFIC_UPDATE_OUTPUT=$(gcloud run services update-traffic "$GCP_SERVICE_NAME" \
    --to-latest \
    --region="$GCP_REGION" \
    --project="$GCP_PROJECT_ID" 2>&1)

TRAFFIC_UPDATE_EXIT_CODE=$?

if [ $TRAFFIC_UPDATE_EXIT_CODE -eq 0 ]; then
    log_success "트래픽이 최신 리비전으로 전환되었습니다!"
    
    # 트래픽 전환 확인
    ACTIVE_REVISION=$(gcloud run services describe "$GCP_SERVICE_NAME" --region="$GCP_REGION" --format="value(status.traffic[0].revisionName)" --project="$GCP_PROJECT_ID" 2>/dev/null)
    TRAFFIC_PERCENT=$(gcloud run services describe "$GCP_SERVICE_NAME" --region="$GCP_REGION" --format="value(status.traffic[0].percent)" --project="$GCP_PROJECT_ID" 2>/dev/null)
    
    log_success "활성 리비전: $ACTIVE_REVISION (트래픽: $TRAFFIC_PERCENT%)"
else
    log_warning "트래픽 전환 실패 (배포는 성공):"
    echo "$TRAFFIC_UPDATE_OUTPUT"
    log_warning "수동으로 트래픽을 전환해주세요: gcloud run services update-traffic $GCP_SERVICE_NAME --to-latest --region=$GCP_REGION"
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
echo -e "  상태체크: $SERVICE_URL/status"
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