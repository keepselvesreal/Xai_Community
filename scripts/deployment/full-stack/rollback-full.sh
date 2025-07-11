#!/bin/bash

# XAI Community Full Stack Rollback 스크립트 v2.0
# 간단하고 안정적인 통합 롤백 시스템

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

log_section() {
    echo -e "${PURPLE}[SECTION]${NC} $1"
}

# 사용법 출력
usage() {
    echo "사용법: $0 [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  -e, --environment ENV     환경 지정 (production|staging)"
    echo "  -v, --verify             현재 버전 확인만 수행"
    echo "  -h, --help               도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 -e staging                          # 스테이징 전체 스택 롤백"
    echo "  $0 -e production                       # 프로덕션 전체 스택 롤백"
    echo "  $0 -e staging -v                       # 스테이징 현재 버전만 확인"
    exit 1
}

# 파라미터 파싱
ENVIRONMENT=""
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
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

echo ""
echo -e "${PURPLE}================================================================${NC}"
echo -e "${PURPLE}  🔄 XAI Community Full Stack Rollback System v2.0${NC}"
echo -e "${PURPLE}================================================================${NC}"
echo ""

log_info "환경: $ENVIRONMENT"
log_info "확인 모드: $VERIFY_ONLY"

# 환경별 설정
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_URL="https://xai-community-backend-798170408536.asia-northeast3.run.app"
    FRONTEND_URL="https://xai-community.vercel.app"
else
    BACKEND_URL="https://xai-community-backend-staging-798170408536.asia-northeast3.run.app"
    FRONTEND_URL="https://xai-community-git-staging-ktsfrank-navercoms-projects.vercel.app"
fi

log_info "백엔드 URL: $BACKEND_URL"
log_info "프론트엔드 URL: $FRONTEND_URL"

# 스크립트 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SCRIPT="$SCRIPT_DIR/../backend/rollback-backend.sh"
FRONTEND_SCRIPT="$SCRIPT_DIR/../frontend/rollback-frontend.sh"

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
    
    # 프론트엔드 배포 정보 (Vercel CLI 사용)
    log_info "프론트엔드 배포 정보 수집 중..."
    cd "$SCRIPT_DIR/frontend"
    FRONTEND_DEPLOYMENTS=$(vercel ls 2>/dev/null | head -5 || echo "vercel_cli_error")
    cd "$SCRIPT_DIR"
    
    # 버전 정보 표시
    echo ""
    echo -e "${GREEN}📋 현재 버전 정보${NC}"
    echo -e "${BLUE}백엔드:${NC}"
    echo "$BACKEND_VERSION" | jq . 2>/dev/null || echo "$BACKEND_VERSION"
    echo ""
    echo -e "${BLUE}프론트엔드 (최근 배포):${NC}"
    echo "$FRONTEND_DEPLOYMENTS"
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
log_warning "전체 스택을 롤백합니다 ($ENVIRONMENT 환경)"
log_warning "  1. 백엔드 롤백 (자동 force 모드)"
log_warning "  2. 프론트엔드 롤백"
log_warning "  3. 기본 검증"

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "롤백이 취소되었습니다."
    exit 0
fi

# 롤백 시작 시간 기록
ROLLBACK_START_TIME=$(date)
log_info "롤백 시작 시간: $ROLLBACK_START_TIME"

# 백엔드 롤백 (자동화 모드)
log_section "=== 1단계: 백엔드 롤백 ==="
log_info "백엔드 롤백 명령어: AUTOMATED_MODE=true $BACKEND_SCRIPT -e $ENVIRONMENT"

if ! AUTOMATED_MODE=true $BACKEND_SCRIPT -e $ENVIRONMENT; then
    log_error "백엔드 롤백 실패!"
    exit 1
fi

log_success "백엔드 롤백 완료"

# 프론트엔드 롤백
log_section "=== 2단계: 프론트엔드 롤백 ==="
log_info "프론트엔드 롤백 명령어: AUTOMATED_MODE=true $FRONTEND_SCRIPT -e $ENVIRONMENT"

# 프론트엔드 디렉토리로 이동
cd "$SCRIPT_DIR/frontend"

if ! AUTOMATED_MODE=true $FRONTEND_SCRIPT -e $ENVIRONMENT; then
    log_error "프론트엔드 롤백 실패!"
    exit 1
fi

log_success "프론트엔드 롤백 완료"

# 원래 디렉토리로 돌아가기
cd "$SCRIPT_DIR"

# 기본 검증
log_section "=== 3단계: 기본 검증 ==="

log_info "서비스 안정화 대기 중..."
sleep 20

# 백엔드 헬스체크
log_info "백엔드 헬스체크 중..."
if curl -f -s "$BACKEND_URL/status" > /dev/null 2>&1; then
    log_success "백엔드 헬스체크 성공"
    BACKEND_HEALTH=true
else
    log_warning "백엔드 헬스체크 실패"
    BACKEND_HEALTH=false
fi

# 프론트엔드 접근성 확인 (인증 페이지도 정상 응답으로 간주)
log_info "프론트엔드 접근성 확인 중..."
if curl -f -s "$FRONTEND_URL" > /dev/null 2>&1; then
    log_success "프론트엔드 접근성 확인 성공"
    FRONTEND_ACCESS=true
else
    log_warning "프론트엔드 접근성 확인 실패"
    FRONTEND_ACCESS=false
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
echo -e "  백엔드 롤백: 완료"
echo -e "  프론트엔드 롤백: 완료"
echo ""

echo -e "${GREEN}✅ 서비스 URL${NC}"
echo -e "  백엔드: $BACKEND_URL"
echo -e "  프론트엔드: $FRONTEND_URL"
echo ""

echo -e "${GREEN}✅ 기본 검증 결과${NC}"
echo -e "  백엔드 헬스체크: $([ "$BACKEND_HEALTH" = true ] && echo "성공" || echo "실패")"
echo -e "  프론트엔드 접근성: $([ "$FRONTEND_ACCESS" = true ] && echo "성공" || echo "실패")"
echo ""

echo -e "${GREEN}✅ 관리 URL${NC}"
echo -e "  Google Cloud Console: https://console.cloud.google.com/run"
echo -e "  Vercel Dashboard: https://vercel.com/dashboard"
echo ""

if [ "$BACKEND_HEALTH" = true ] && [ "$FRONTEND_ACCESS" = true ]; then
    echo -e "${GREEN}🎉 전체 스택 롤백 성공!${NC}"
    echo -e "${GREEN}모든 서비스가 정상적으로 이전 버전으로 롤백되었습니다.${NC}"
else
    echo -e "${YELLOW}⚠️ 롤백 완료되었지만 일부 검증 실패${NC}"
    echo -e "${YELLOW}서비스 상태를 수동으로 확인해주세요.${NC}"
fi

echo ""
echo -e "${BLUE}📝 다음 단계${NC}"
echo -e "  1. 서비스 모니터링 및 로그 확인"
echo -e "  2. 사용자 알림 (필요시)"
echo -e "  3. 롤백 원인 분석 및 문서화"
echo ""