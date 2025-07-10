#!/bin/bash

# XAI Community Backend Cloud Run Rollback 스크립트 v1.0
# 버전 확인 기능을 포함한 안전한 롤백 시스템

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

# 사용법 출력
usage() {
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -e, --environment ENV     환경 지정 (production|staging)"
    echo "  -r, --revision REVISION   특정 리비전으로 롤백"
    echo "  -v, --verify             롤백 후 버전 확인만 수행"
    echo "  -h, --help               도움말 출력"
    echo ""
    echo "환경변수:"
    echo "  AUTOMATED_MODE=true      자동화 모드 (확인 절차 생략)"
    echo ""
    echo "예시:"
    echo "  $0 -e production                          # 프로덕션 이전 리비전으로 롤백"
    echo "  $0 -e staging -r revision-name            # 스테이징 특정 리비전으로 롤백"
    echo "  $0 -e production -v                       # 프로덕션 현재 버전만 확인"
    echo "  $0 -e staging -f                          # 스테이징 강제 롤백 (확인 없음)"
    exit 1
}

# 파라미터 파싱
ENVIRONMENT=""
TARGET_REVISION=""
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--revision)
            TARGET_REVISION="$2"
            shift 2
            ;;
        -v|--verify)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            usage
            ;;
    esac
done

# 환경 검증
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "staging" ]]; then
    log_error "환경을 지정해야 합니다: production 또는 staging"
    usage
fi

log_info "=== XAI Community Backend Cloud Run Rollback 시작 ==="
log_info "환경: $ENVIRONMENT"
log_info "확인 모드: $VERIFY_ONLY"

# 환경별 설정
if [ "$ENVIRONMENT" = "production" ]; then
    SERVICE_NAME="xai-community-backend"
    SERVICE_URL="https://xai-community-backend-798170408536.asia-northeast3.run.app"
else
    SERVICE_NAME="xai-community-backend-staging"
    SERVICE_URL="https://xai-community-backend-staging-798170408536.asia-northeast3.run.app"
fi

GCP_PROJECT_ID="xai-community"
GCP_REGION="asia-northeast3"

log_info "서비스명: $SERVICE_NAME"
log_info "서비스 URL: $SERVICE_URL"

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

# 현재 서비스 상태 확인
log_info "=== 현재 서비스 상태 확인 ==="

# 현재 활성 리비전 확인 (실제 트래픽 기준)
CURRENT_REVISION=$(gcloud run services describe "$SERVICE_NAME" --region="$GCP_REGION" --format="value(status.traffic[0].revisionName)" 2>/dev/null)
if [ -z "$CURRENT_REVISION" ]; then
    log_error "서비스 '$SERVICE_NAME'을 찾을 수 없습니다!"
    exit 1
fi

log_success "현재 활성 리비전: $CURRENT_REVISION"

# 현재 버전 정보 확인
log_info "현재 버전 정보 확인 중..."
CURRENT_VERSION_INFO=$(curl -s "$SERVICE_URL/version" 2>/dev/null || echo '{"error": "version_api_not_available"}')
if echo "$CURRENT_VERSION_INFO" | grep -q "error"; then
    log_warning "버전 API에 접근할 수 없습니다. 기본 헬스체크로 대체합니다."
    CURRENT_VERSION_INFO=$(curl -s "$SERVICE_URL/health" 2>/dev/null || echo '{"error": "service_not_available"}')
fi

log_debug "현재 버전 정보: $CURRENT_VERSION_INFO"

# 검증 모드인 경우 여기서 종료
if [ "$VERIFY_ONLY" = true ]; then
    log_info "=== 현재 버전 정보 ==="
    echo "$CURRENT_VERSION_INFO" | jq . 2>/dev/null || echo "$CURRENT_VERSION_INFO"
    log_success "버전 확인 완료"
    exit 0
fi

# 사용 가능한 리비전 목록 조회
log_info "=== 사용 가능한 리비전 목록 조회 ==="
AVAILABLE_REVISIONS=$(gcloud run revisions list --service="$SERVICE_NAME" --region="$GCP_REGION" --format="value(metadata.name)" --limit=10)

if [ -z "$AVAILABLE_REVISIONS" ]; then
    log_error "사용 가능한 리비전이 없습니다!"
    exit 1
fi

log_info "사용 가능한 리비전들:"
echo "$AVAILABLE_REVISIONS" | while read -r revision; do
    if [ "$revision" = "$CURRENT_REVISION" ]; then
        log_info "  → $revision (현재 활성)"
    else
        log_info "  - $revision"
    fi
done

# 타겟 리비전 결정
if [ -n "$TARGET_REVISION" ]; then
    # 지정된 리비전 확인
    if ! echo "$AVAILABLE_REVISIONS" | grep -q "^$TARGET_REVISION$"; then
        log_error "지정된 리비전 '$TARGET_REVISION'을 찾을 수 없습니다!"
        exit 1
    fi
    ROLLBACK_REVISION="$TARGET_REVISION"
else
    # 이전 리비전 자동 선택 (현재 리비전 다음)
    ROLLBACK_REVISION=$(echo "$AVAILABLE_REVISIONS" | grep -A1 "^$CURRENT_REVISION$" | tail -n1)
    if [ -z "$ROLLBACK_REVISION" ] || [ "$ROLLBACK_REVISION" = "$CURRENT_REVISION" ]; then
        log_error "롤백할 이전 리비전을 찾을 수 없습니다!"
        exit 1
    fi
fi

log_info "롤백 대상 리비전: $ROLLBACK_REVISION"

# 동일한 리비전 체크
if [ "$CURRENT_REVISION" = "$ROLLBACK_REVISION" ]; then
    log_warning "현재 리비전과 롤백 대상 리비전이 동일합니다!"
    log_warning "이미 해당 리비전이 활성화되어 있습니다."
    if [ "$AUTOMATED_MODE" != "true" ]; then
        read -p "그래도 계속하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "작업이 취소되었습니다."
            exit 0
        fi
    else
        log_info "자동화 모드: 동일한 리비전이지만 계속 진행합니다."
    fi
fi

# 롤백 실행 확인
log_warning "다음 작업을 수행합니다:"
log_warning "  - 현재 리비전: $CURRENT_REVISION"
log_warning "  - 롤백 대상: $ROLLBACK_REVISION"
log_warning "  - 서비스: $SERVICE_NAME ($ENVIRONMENT)"

if [ "$AUTOMATED_MODE" != "true" ]; then
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "롤백이 취소되었습니다."
        exit 0
    fi
else
    log_info "자동화 모드: 확인 절차를 건너뛰고 롤백을 진행합니다."
fi

# 롤백 실행
log_info "=== 롤백 실행 ==="
log_info "트래픽을 $ROLLBACK_REVISION으로 전환 중..."

ROLLBACK_OUTPUT=$(gcloud run services update-traffic "$SERVICE_NAME" \
    --to-revisions="$ROLLBACK_REVISION=100" \
    --region="$GCP_REGION" \
    --project="$GCP_PROJECT_ID" 2>&1)

ROLLBACK_EXIT_CODE=$?

if [ $ROLLBACK_EXIT_CODE -ne 0 ]; then
    log_error "롤백 실패!"
    echo "$ROLLBACK_OUTPUT"
    exit 1
fi

log_success "트래픽 전환 완료!"

# 트래픽 전환 결과 즉시 확인
log_info "트래픽 전환 결과 확인 중..."
IMMEDIATE_TRAFFIC_CHECK=$(gcloud run services describe "$SERVICE_NAME" --region="$GCP_REGION" --format="value(status.traffic[0].revisionName,status.traffic[0].percent)" 2>/dev/null)
log_debug "즉시 확인 결과: $IMMEDIATE_TRAFFIC_CHECK"

# 롤백 검증
log_info "=== 롤백 검증 ==="
log_info "서비스 안정화 대기 중..."
sleep 10

# 실제 트래픽이 가는 리비전 확인 (더 정확한 방법)
ACTIVE_REVISION=$(gcloud run services describe "$SERVICE_NAME" --region="$GCP_REGION" --format="value(status.traffic[0].revisionName)" 2>/dev/null)
TRAFFIC_PERCENT=$(gcloud run services describe "$SERVICE_NAME" --region="$GCP_REGION" --format="value(status.traffic[0].percent)" 2>/dev/null)

log_debug "활성 리비전: $ACTIVE_REVISION (트래픽: $TRAFFIC_PERCENT%)"

if [ "$ACTIVE_REVISION" != "$ROLLBACK_REVISION" ]; then
    log_error "롤백 검증 실패: 예상 리비전($ROLLBACK_REVISION) != 실제 활성 리비전($ACTIVE_REVISION)"
    exit 1
fi

if [ "$TRAFFIC_PERCENT" != "100" ]; then
    log_warning "트래픽이 100%가 아닙니다: $TRAFFIC_PERCENT%"
fi

log_success "리비전 전환 확인: $ACTIVE_REVISION (트래픽: $TRAFFIC_PERCENT%)"

# 헬스체크
log_info "헬스체크 수행 중..."
HEALTH_CHECK_SUCCESS=false
for i in {1..12}; do
    log_debug "헬스체크 시도 $i/12: $SERVICE_URL/health"
    
    if curl -f -s "$SERVICE_URL/health" > /dev/null 2>&1; then
        log_success "헬스체크 성공!"
        HEALTH_CHECK_SUCCESS=true
        break
    fi
    
    if [ $i -eq 12 ]; then
        log_error "헬스체크 실패. 롤백된 서비스가 정상적으로 시작되지 않았습니다."
        break
    else
        log_debug "서비스 준비 중... 5초 후 재시도"
        sleep 5
    fi
done

# 버전 확인
log_info "롤백된 버전 정보 확인 중..."
NEW_VERSION_INFO=$(curl -s "$SERVICE_URL/version" 2>/dev/null || echo '{"error": "version_api_not_available"}')
if echo "$NEW_VERSION_INFO" | grep -q "error"; then
    log_warning "버전 API에 접근할 수 없습니다. 기본 헬스체크로 대체합니다."
    NEW_VERSION_INFO=$(curl -s "$SERVICE_URL/health" 2>/dev/null || echo '{"error": "service_not_available"}')
fi

# 롤백 완료 정보
echo ""
echo -e "${BLUE}=== 🔄 XAI Community Backend 롤백 완료 ===${NC}"
echo ""
echo -e "${GREEN}✅ 롤백 정보${NC}"
echo -e "  환경: $ENVIRONMENT"
echo -e "  서비스명: $SERVICE_NAME"
echo -e "  이전 리비전: $CURRENT_REVISION"
echo -e "  현재 활성 리비전: $ACTIVE_REVISION"
echo -e "  트래픽 분산: $TRAFFIC_PERCENT%"
echo ""
echo -e "${GREEN}✅ 서비스 상태${NC}"
echo -e "  URL: $SERVICE_URL"
echo -e "  헬스체크: $([ "$HEALTH_CHECK_SUCCESS" = true ] && echo "성공" || echo "실패")"
echo ""
echo -e "${GREEN}✅ 버전 정보${NC}"
echo "$NEW_VERSION_INFO" | jq . 2>/dev/null || echo "$NEW_VERSION_INFO"
echo ""
echo -e "${GREEN}✅ 관리 URL${NC}"
echo -e "  Google Cloud Console: https://console.cloud.google.com/run/detail/$GCP_REGION/$SERVICE_NAME/metrics?project=$GCP_PROJECT_ID"
echo ""

if [ "$HEALTH_CHECK_SUCCESS" = true ]; then
    echo -e "${GREEN}🎉 롤백 성공!${NC}"
else
    echo -e "${YELLOW}⚠️ 롤백 완료되었지만 헬스체크 실패. 수동 확인이 필요합니다.${NC}"
fi