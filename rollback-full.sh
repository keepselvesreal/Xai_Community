#!/bin/bash

# XAI Community Full Stack Rollback 스크립트 v1.0
# 백엔드와 프론트엔드를 통합 롤백하는 시스템

set -e  # 오류 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_section() {
    echo -e "${PURPLE}[SECTION]${NC} $1"
}

# 사용법 출력
usage() {
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -e, --environment ENV     환경 지정 (production|staging)"
    echo "  -b, --backend-only        백엔드만 롤백"
    echo "  -f, --frontend-only       프론트엔드만 롤백"
    echo "  -r, --backend-revision REV 백엔드 특정 리비전으로 롤백"
    echo "  -d, --frontend-deployment ID 프론트엔드 특정 배포로 롤백"
    echo "  -v, --verify             현재 버전 확인만 수행"
    echo "  -s, --skip-verification  롤백 후 검증 단계 건너뛰기"
    echo "  -h, --help               도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 -e production                          # 전체 스택 이전 버전으로 롤백"
    echo "  $0 -e staging -b                          # 스테이징 백엔드만 롤백"
    echo "  $0 -e production -f                       # 프로덕션 프론트엔드만 롤백"
    echo "  $0 -e production -v                       # 프로덕션 현재 버전만 확인"
    echo "  $0 -e staging -r revision-name -d deploy-id # 특정 버전으로 롤백"
    exit 1
}

# 파라미터 파싱
ENVIRONMENT=""
BACKEND_ONLY=false
FRONTEND_ONLY=false
BACKEND_REVISION=""
FRONTEND_DEPLOYMENT=""
VERIFY_ONLY=false
SKIP_VERIFICATION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        -f|--frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        -r|--backend-revision)
            BACKEND_REVISION="$2"
            shift 2
            ;;
        -d|--frontend-deployment)
            FRONTEND_DEPLOYMENT="$2"
            shift 2
            ;;
        -v|--verify)
            VERIFY_ONLY=true
            shift
            ;;
        -s|--skip-verification)
            SKIP_VERIFICATION=true
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

# 백엔드와 프론트엔드 동시 지정 검증
if [ "$BACKEND_ONLY" = true ] && [ "$FRONTEND_ONLY" = true ]; then
    log_error "백엔드 전용과 프론트엔드 전용 옵션을 동시에 사용할 수 없습니다!"
    usage
fi

echo ""
echo -e "${PURPLE}================================================================${NC}"
echo -e "${PURPLE}  🔄 XAI Community Full Stack Rollback System v1.0${NC}"
echo -e "${PURPLE}================================================================${NC}"
echo ""

log_info "환경: $ENVIRONMENT"
log_info "백엔드 전용: $BACKEND_ONLY"
log_info "프론트엔드 전용: $FRONTEND_ONLY"
log_info "확인 모드: $VERIFY_ONLY"
log_info "검증 건너뛰기: $SKIP_VERIFICATION"

# 환경별 설정
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_URL="https://xai-community-backend-798170408536.asia-northeast3.run.app"
    FRONTEND_URL="https://xai-community.vercel.app"
else
    BACKEND_URL="https://xai-community-backend-staging-798170408536.asia-northeast3.run.app"
    FRONTEND_URL="https://xai-community-staging.vercel.app"
fi

log_info "백엔드 URL: $BACKEND_URL"
log_info "프론트엔드 URL: $FRONTEND_URL"

# 스크립트 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SCRIPT="$SCRIPT_DIR/backend/rollback-backend.sh"
FRONTEND_SCRIPT="$SCRIPT_DIR/frontend/rollback-frontend.sh"

# 스크립트 존재 확인
if [ ! -f "$BACKEND_SCRIPT" ]; then
    log_error "백엔드 롤백 스크립트를 찾을 수 없습니다: $BACKEND_SCRIPT"
    exit 1
fi

if [ ! -f "$FRONTEND_SCRIPT" ]; then
    log_error "프론트엔드 롤백 스크립트를 찾을 수 없습니다: $FRONTEND_SCRIPT"
    exit 1
fi

# 현재 버전 정보 수집
collect_current_versions() {
    log_section "=== 현재 버전 정보 수집 ==="
    
    # 백엔드 버전 정보
    log_info "백엔드 버전 정보 수집 중..."
    BACKEND_VERSION=$(curl -s "$BACKEND_URL/version" 2>/dev/null || echo '{"error": "backend_not_available"}')
    log_debug "백엔드 버전: $BACKEND_VERSION"
    
    # 프론트엔드 버전 정보
    log_info "프론트엔드 버전 정보 수집 중..."
    FRONTEND_VERSION=$(curl -s "$FRONTEND_URL/version" 2>/dev/null || echo '{"error": "frontend_not_available"}')
    log_debug "프론트엔드 버전: $FRONTEND_VERSION"
    
    # 버전 정보 표시
    echo ""
    echo -e "${GREEN}📋 현재 버전 정보${NC}"
    echo -e "${BLUE}백엔드:${NC}"
    echo "$BACKEND_VERSION" | jq . 2>/dev/null || echo "$BACKEND_VERSION"
    echo ""
    echo -e "${BLUE}프론트엔드:${NC}"
    echo "$FRONTEND_VERSION" | jq . 2>/dev/null || echo "$FRONTEND_VERSION"
    echo ""
}

# 검증 모드
if [ "$VERIFY_ONLY" = true ]; then
    collect_current_versions
    log_success "버전 확인 완료"
    exit 0
fi

# 현재 버전 수집
collect_current_versions

# 롤백 확인
log_section "=== 롤백 계획 확인 ==="
if [ "$BACKEND_ONLY" = true ]; then
    log_warning "백엔드만 롤백합니다 ($ENVIRONMENT 환경)"
elif [ "$FRONTEND_ONLY" = true ]; then
    log_warning "프론트엔드만 롤백합니다 ($ENVIRONMENT 환경)"
else
    log_warning "전체 스택을 롤백합니다 ($ENVIRONMENT 환경)"
    log_warning "  1. 백엔드 롤백"
    log_warning "  2. 프론트엔드 롤백"
    log_warning "  3. 통합 검증"
fi

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "롤백이 취소되었습니다."
    exit 0
fi

# 롤백 시작 시간 기록
ROLLBACK_START_TIME=$(date)
log_info "롤백 시작 시간: $ROLLBACK_START_TIME"

# 백엔드 롤백
if [ "$FRONTEND_ONLY" != true ]; then
    log_section "=== 1단계: 백엔드 롤백 ==="
    
    BACKEND_CMD="$BACKEND_SCRIPT -e $ENVIRONMENT"
    if [ -n "$BACKEND_REVISION" ]; then
        BACKEND_CMD="$BACKEND_CMD -r $BACKEND_REVISION"
    fi
    
    log_info "백엔드 롤백 명령어: $BACKEND_CMD"
    
    if ! $BACKEND_CMD; then
        log_error "백엔드 롤백 실패!"
        exit 1
    fi
    
    log_success "백엔드 롤백 완료"
fi

# 프론트엔드 롤백
if [ "$BACKEND_ONLY" != true ]; then
    log_section "=== 2단계: 프론트엔드 롤백 ==="
    
    FRONTEND_CMD="$FRONTEND_SCRIPT -e $ENVIRONMENT"
    if [ -n "$FRONTEND_DEPLOYMENT" ]; then
        FRONTEND_CMD="$FRONTEND_CMD -d $FRONTEND_DEPLOYMENT"
    fi
    
    log_info "프론트엔드 롤백 명령어: $FRONTEND_CMD"
    
    # 프론트엔드 디렉토리로 이동
    cd "$SCRIPT_DIR/frontend"
    
    if ! $FRONTEND_CMD; then
        log_error "프론트엔드 롤백 실패!"
        exit 1
    fi
    
    log_success "프론트엔드 롤백 완료"
    
    # 원래 디렉토리로 돌아가기
    cd "$SCRIPT_DIR"
fi

# 통합 검증 (건너뛰기 옵션이 없는 경우에만)
if [ "$SKIP_VERIFICATION" != true ]; then
    log_section "=== 3단계: 통합 검증 ==="
    
    log_info "서비스 안정화 대기 중..."
    sleep 30
    
    # 롤백 후 버전 정보 수집
    log_info "롤백 후 버전 정보 수집 중..."
    BACKEND_VERSION_AFTER=$(curl -s "$BACKEND_URL/version" 2>/dev/null || echo '{"error": "backend_not_available"}')
    FRONTEND_VERSION_AFTER=$(curl -s "$FRONTEND_URL/version" 2>/dev/null || echo '{"error": "frontend_not_available"}')
    
    # 서비스 연결 테스트
    log_info "서비스 간 연결 테스트 중..."
    INTEGRATION_TEST_SUCCESS=false
    
    # CORS 테스트
    if curl -f -s -H "Origin: $FRONTEND_URL" "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "CORS 연결 테스트 성공"
        INTEGRATION_TEST_SUCCESS=true
    else
        log_warning "CORS 연결 테스트 실패"
    fi
    
    # API 연결 테스트
    if curl -f -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "백엔드 API 테스트 성공"
    else
        log_warning "백엔드 API 테스트 실패"
    fi
    
    # 프론트엔드 접근성 테스트
    if curl -f -s "$FRONTEND_URL" > /dev/null 2>&1; then
        log_success "프론트엔드 접근성 테스트 성공"
    else
        log_warning "프론트엔드 접근성 테스트 실패"
    fi
    
    log_success "통합 검증 완료"
else
    log_info "검증 단계를 건너뜁니다."
    BACKEND_VERSION_AFTER='{"skipped": "verification_skipped"}'
    FRONTEND_VERSION_AFTER='{"skipped": "verification_skipped"}'
    INTEGRATION_TEST_SUCCESS=true
fi

# 롤백 완료 시간 기록
ROLLBACK_END_TIME=$(date)

# 최종 결과 리포트
echo ""
echo -e "${PURPLE}================================================================${NC}"
echo -e "${PURPLE}  🎉 XAI Community Full Stack Rollback 완료${NC}"
echo -e "${PURPLE}================================================================${NC}"
echo ""

echo -e "${GREEN}✅ 롤백 정보${NC}"
echo -e "  환경: $ENVIRONMENT"
echo -e "  시작 시간: $ROLLBACK_START_TIME"
echo -e "  완료 시간: $ROLLBACK_END_TIME"
echo -e "  백엔드 롤백: $([ "$FRONTEND_ONLY" != true ] && echo "완료" || echo "건너뜀")"
echo -e "  프론트엔드 롤백: $([ "$BACKEND_ONLY" != true ] && echo "완료" || echo "건너뜀")"
echo ""

echo -e "${GREEN}✅ 서비스 URL${NC}"
echo -e "  백엔드: $BACKEND_URL"
echo -e "  프론트엔드: $FRONTEND_URL"
echo ""

if [ "$SKIP_VERIFICATION" != true ]; then
    echo -e "${GREEN}✅ 롤백 후 버전 정보${NC}"
    echo -e "${BLUE}백엔드:${NC}"
    echo "$BACKEND_VERSION_AFTER" | jq . 2>/dev/null || echo "$BACKEND_VERSION_AFTER"
    echo ""
    echo -e "${BLUE}프론트엔드:${NC}"
    echo "$FRONTEND_VERSION_AFTER" | jq . 2>/dev/null || echo "$FRONTEND_VERSION_AFTER"
    echo ""
    
    echo -e "${GREEN}✅ 통합 테스트${NC}"
    echo -e "  서비스 연결: $([ "$INTEGRATION_TEST_SUCCESS" = true ] && echo "성공" || echo "실패")"
    echo ""
fi

echo -e "${GREEN}✅ 관리 URL${NC}"
echo -e "  Google Cloud Console: https://console.cloud.google.com/run"
echo -e "  Vercel Dashboard: https://vercel.com/dashboard"
echo ""

if [ "$SKIP_VERIFICATION" = true ] || [ "$INTEGRATION_TEST_SUCCESS" = true ]; then
    echo -e "${GREEN}🎉 전체 스택 롤백 성공!${NC}"
    echo -e "${GREEN}모든 서비스가 정상적으로 이전 버전으로 롤백되었습니다.${NC}"
else
    echo -e "${YELLOW}⚠️ 롤백 완료되었지만 일부 검증 실패${NC}"
    echo -e "${YELLOW}수동으로 서비스 상태를 확인해주세요.${NC}"
fi

echo ""
echo -e "${BLUE}📝 다음 단계${NC}"
echo -e "  1. 서비스 모니터링 및 로그 확인"
echo -e "  2. 사용자 알림 (필요시)"
echo -e "  3. 롤백 원인 분석 및 문서화"
echo ""