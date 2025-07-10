#!/bin/bash

# XAI Community Frontend Vercel Rollback 스크립트 v1.0
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
    echo "  -d, --deployment ID       특정 배포 ID로 롤백"
    echo "  -v, --verify             롤백 후 버전 확인만 수행"
    echo "  -h, --help               도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 -e production                          # 프로덕션 이전 배포로 롤백"
    echo "  $0 -e staging -d deployment-id            # 스테이징 특정 배포로 롤백"
    echo "  $0 -e production -v                       # 프로덕션 현재 버전만 확인"
    exit 1
}

# 파라미터 파싱
ENVIRONMENT=""
TARGET_DEPLOYMENT=""
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--deployment)
            TARGET_DEPLOYMENT="$2"
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

log_info "=== XAI Community Frontend Vercel Rollback 시작 ==="
log_info "환경: $ENVIRONMENT"
log_info "확인 모드: $VERIFY_ONLY"

# 환경별 설정
if [ "$ENVIRONMENT" = "production" ]; then
    PROJECT_NAME="xai-community"
    SERVICE_URL="https://xai-community.vercel.app"
else
    PROJECT_NAME="xai-community-staging"
    SERVICE_URL="https://xai-community-staging.vercel.app"
fi

log_info "프로젝트명: $PROJECT_NAME"
log_info "서비스 URL: $SERVICE_URL"

# Vercel CLI 인증 확인
log_info "Vercel CLI 인증 상태 확인 중..."
if ! vercel whoami > /dev/null 2>&1; then
    log_error "Vercel CLI 인증이 필요합니다! 'vercel login' 실행 후 다시 시도해주세요."
    exit 1
fi

VERCEL_USER=$(vercel whoami)
log_success "Vercel CLI 인증 확인 완료: $VERCEL_USER"

# 현재 서비스 상태 확인
log_info "=== 현재 서비스 상태 확인 ==="

# 현재 버전 정보 확인
log_info "현재 버전 정보 확인 중..."
CURRENT_VERSION_INFO=$(curl -s "$SERVICE_URL/version" 2>/dev/null || echo '{"error": "version_page_not_available"}')
if echo "$CURRENT_VERSION_INFO" | grep -q "error"; then
    log_warning "버전 페이지에 접근할 수 없습니다. HTML 메타태그로 확인을 시도합니다."
    # HTML 페이지에서 메타태그 정보 추출
    CURRENT_VERSION_INFO=$(curl -s "$SERVICE_URL" | grep -o '<meta name="build-[^"]*" content="[^"]*"' | sed 's/<meta name="build-/{"/' | sed 's/" content="/": "/' | sed 's/"$/"}/' | tr '\n' ',' | sed 's/,$//' | sed 's/^/[/' | sed 's/$/]/' 2>/dev/null || echo '{"error": "meta_tags_not_available"}')
fi

log_debug "현재 버전 정보: $CURRENT_VERSION_INFO"

# 검증 모드인 경우 여기서 종료
if [ "$VERIFY_ONLY" = true ]; then
    log_info "=== 현재 버전 정보 ==="
    echo "$CURRENT_VERSION_INFO" | jq . 2>/dev/null || echo "$CURRENT_VERSION_INFO"
    log_success "버전 확인 완료"
    exit 0
fi

# 배포 목록 조회
log_info "=== 사용 가능한 배포 목록 조회 ==="

# 현재 디렉토리가 Vercel 프로젝트인지 확인
if [ ! -f "vercel.json" ] && [ ! -f "package.json" ]; then
    log_error "현재 디렉토리가 Vercel 프로젝트가 아닙니다!"
    exit 1
fi

# 배포 목록 가져오기
log_info "배포 목록을 가져오는 중..."
DEPLOYMENTS_OUTPUT=$(vercel ls 2>&1)

# 배포가 있는지 확인 (https:// URL이 있으면 배포가 존재)
if ! echo "$DEPLOYMENTS_OUTPUT" | grep -q "https://xai-community-"; then
    log_error "사용 가능한 배포가 없습니다!"
    exit 1
fi

# 최근 배포들 표시
log_info "최근 배포들:"
echo "$DEPLOYMENTS_OUTPUT" | grep "https://xai-community-" | head -5 | while read line; do
    echo "  - $line"
done

# 현재 활성 배포 확인 (첫 번째 배포 URL에서 deployment ID 추출)
CURRENT_DEPLOYMENT_URL=$(echo "$DEPLOYMENTS_OUTPUT" | grep "https://xai-community-" | head -1 | awk '{print $2}')
if [ -n "$CURRENT_DEPLOYMENT_URL" ]; then
    # URL에서 deployment ID 추출 (xai-community-XXXXXXX 형식)
    CURRENT_DEPLOYMENT=$(echo "$CURRENT_DEPLOYMENT_URL" | sed -n 's/.*xai-community-\([^-]*\)-.*/\1/p')
    if [ -z "$CURRENT_DEPLOYMENT" ]; then
        # 전체 URL을 deployment ID로 사용
        CURRENT_DEPLOYMENT="$CURRENT_DEPLOYMENT_URL"
    fi
else
    CURRENT_DEPLOYMENT="unknown"
fi
log_success "현재 활성 배포: $CURRENT_DEPLOYMENT"

# 타겟 배포 결정
if [ -n "$TARGET_DEPLOYMENT" ]; then
    # 지정된 배포 확인
    if ! echo "$DEPLOYMENTS_OUTPUT" | grep -q "$TARGET_DEPLOYMENT"; then
        log_error "지정된 배포 '$TARGET_DEPLOYMENT'을 찾을 수 없습니다!"
        exit 1
    fi
    ROLLBACK_DEPLOYMENT="$TARGET_DEPLOYMENT"
else
    # 이전 배포 자동 선택 (두 번째 배포 URL에서 ID 추출)
    ROLLBACK_DEPLOYMENT_URL=$(echo "$DEPLOYMENTS_OUTPUT" | grep "https://xai-community-" | sed -n '2p' | awk '{print $2}')
    if [ -n "$ROLLBACK_DEPLOYMENT_URL" ]; then
        # URL에서 deployment ID 추출
        ROLLBACK_DEPLOYMENT=$(echo "$ROLLBACK_DEPLOYMENT_URL" | sed -n 's/.*xai-community-\([^-]*\)-.*/\1/p')
        if [ -z "$ROLLBACK_DEPLOYMENT" ]; then
            # 전체 URL을 사용
            ROLLBACK_DEPLOYMENT="$ROLLBACK_DEPLOYMENT_URL"
        fi
    else
        ROLLBACK_DEPLOYMENT=""
    fi
    
    if [ -z "$ROLLBACK_DEPLOYMENT" ]; then
        log_error "롤백할 이전 배포를 찾을 수 없습니다!"
        exit 1
    fi
fi

log_info "롤백 대상 배포: $ROLLBACK_DEPLOYMENT"

# 롤백 실행 확인
log_warning "다음 작업을 수행합니다:"
log_warning "  - 현재 배포: $CURRENT_DEPLOYMENT"
log_warning "  - 롤백 대상: $ROLLBACK_DEPLOYMENT"
log_warning "  - 프로젝트: $PROJECT_NAME ($ENVIRONMENT)"

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "롤백이 취소되었습니다."
    exit 0
fi

# 롤백 실행
log_info "=== 롤백 실행 ==="
log_info "배포 $ROLLBACK_DEPLOYMENT로 롤백 중..."

ROLLBACK_OUTPUT=$(vercel promote "$ROLLBACK_DEPLOYMENT" --yes 2>&1)
ROLLBACK_EXIT_CODE=$?

if [ $ROLLBACK_EXIT_CODE -ne 0 ]; then
    log_error "롤백 실패!"
    echo "$ROLLBACK_OUTPUT"
    exit 1
fi

log_success "배포 롤백 완료!"

# 롤백 검증
log_info "=== 롤백 검증 ==="
log_info "배포 안정화 대기 중..."
sleep 15

# DNS 전파 및 CDN 캐시 클리어 대기
log_info "DNS 전파 및 CDN 캐시 클리어 대기 중..."
sleep 30

# 서비스 접근성 확인
log_info "서비스 접근성 확인 중..."
ACCESS_CHECK_SUCCESS=false
for i in {1..12}; do
    log_debug "접근성 확인 시도 $i/12: $SERVICE_URL"
    
    if curl -f -s "$SERVICE_URL" > /dev/null 2>&1; then
        log_success "서비스 접근 성공!"
        ACCESS_CHECK_SUCCESS=true
        break
    fi
    
    if [ $i -eq 12 ]; then
        log_error "서비스 접근 실패. 롤백된 배포가 정상적으로 작동하지 않을 수 있습니다."
        break
    else
        log_debug "서비스 준비 중... 10초 후 재시도"
        sleep 10
    fi
done

# 롤백된 버전 정보 확인
log_info "롤백된 버전 정보 확인 중..."
NEW_VERSION_INFO=$(curl -s "$SERVICE_URL/version" 2>/dev/null || echo '{"error": "version_page_not_available"}')
if echo "$NEW_VERSION_INFO" | grep -q "error"; then
    log_warning "버전 페이지에 접근할 수 없습니다. HTML 메타태그로 확인을 시도합니다."
    NEW_VERSION_INFO=$(curl -s "$SERVICE_URL" | grep -o '<meta name="build-[^"]*" content="[^"]*"' | sed 's/<meta name="build-/{"/' | sed 's/" content="/": "/' | sed 's/"$/"}/' | tr '\n' ',' | sed 's/,$//' | sed 's/^/[/' | sed 's/$/]/' 2>/dev/null || echo '{"error": "meta_tags_not_available"}')
fi

# 최종 배포 상태 확인
log_info "최종 배포 상태 확인 중..."
FINAL_DEPLOYMENT_INFO=$(vercel ls 2>&1 | grep "https://xai-community-" | head -1 || echo "no deployment info")

# 롤백 완료 정보
echo ""
echo -e "${BLUE}=== 🔄 XAI Community Frontend 롤백 완료 ===${NC}"
echo ""
echo -e "${GREEN}✅ 롤백 정보${NC}"
echo -e "  환경: $ENVIRONMENT"
echo -e "  프로젝트명: $PROJECT_NAME"
echo -e "  이전 배포: $CURRENT_DEPLOYMENT"
echo -e "  현재 배포: $ROLLBACK_DEPLOYMENT"
echo ""
echo -e "${GREEN}✅ 서비스 상태${NC}"
echo -e "  URL: $SERVICE_URL"
echo -e "  접근성: $([ "$ACCESS_CHECK_SUCCESS" = true ] && echo "성공" || echo "실패")"
echo ""
echo -e "${GREEN}✅ 버전 정보${NC}"
echo "$NEW_VERSION_INFO" | jq . 2>/dev/null || echo "$NEW_VERSION_INFO"
echo ""
echo -e "${GREEN}✅ 관리 URL${NC}"
echo -e "  Vercel Dashboard: https://vercel.com/dashboard"
echo ""

if [ "$ACCESS_CHECK_SUCCESS" = true ]; then
    echo -e "${GREEN}🎉 롤백 성공!${NC}"
else
    echo -e "${YELLOW}⚠️ 롤백 완료되었지만 접근성 확인 실패. 수동 확인이 필요합니다.${NC}"
fi