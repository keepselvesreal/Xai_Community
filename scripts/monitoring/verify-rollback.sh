#!/bin/bash

# XAI Community Rollback Verification 스크립트 v1.0
# 롤백 후 버전 확인 및 시스템 검증

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
    echo "사용법: $0 [OPTIONS] EXPECTED_BACKEND_COMMIT EXPECTED_FRONTEND_COMMIT"
    echo ""
    echo "옵션:"
    echo "  -e, --environment ENV     환경 지정 (production|staging)"
    echo "  -t, --timeout SECONDS     타임아웃 시간 (기본: 300초)"
    echo "  -r, --retry-count COUNT   재시도 횟수 (기본: 5회)"
    echo "  -s, --skip-integration   통합 테스트 건너뛰기"
    echo "  -j, --json-output        JSON 형식으로 결과 출력"
    echo "  -h, --help               도움말 출력"
    echo ""
    echo "인자:"
    echo "  EXPECTED_BACKEND_COMMIT   예상되는 백엔드 커밋 해시"
    echo "  EXPECTED_FRONTEND_COMMIT  예상되는 프론트엔드 커밋 해시"
    echo ""
    echo "예시:"
    echo "  $0 -e production abc123 def456        # 특정 커밋으로 롤백 검증"
    echo "  $0 -e staging --json-output abc123 def456  # JSON 출력으로 검증"
    echo "  $0 -e production -s abc123 def456     # 통합 테스트 없이 검증"
    exit 1
}

# 파라미터 파싱
ENVIRONMENT=""
TIMEOUT=300
RETRY_COUNT=5
SKIP_INTEGRATION=false
JSON_OUTPUT=false
EXPECTED_BACKEND_COMMIT=""
EXPECTED_FRONTEND_COMMIT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -r|--retry-count)
            RETRY_COUNT="$2"
            shift 2
            ;;
        -s|--skip-integration)
            SKIP_INTEGRATION=true
            shift
            ;;
        -j|--json-output)
            JSON_OUTPUT=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            log_error "알 수 없는 옵션: $1"
            usage
            ;;
        *)
            if [ -z "$EXPECTED_BACKEND_COMMIT" ]; then
                EXPECTED_BACKEND_COMMIT="$1"
            elif [ -z "$EXPECTED_FRONTEND_COMMIT" ]; then
                EXPECTED_FRONTEND_COMMIT="$1"
            else
                log_error "너무 많은 인자입니다: $1"
                usage
            fi
            shift
            ;;
    esac
done

# 필수 파라미터 검증
if [[ "$ENVIRONMENT" != "production" && "$ENVIRONMENT" != "staging" ]]; then
    log_error "환경을 지정해야 합니다: production 또는 staging"
    usage
fi

if [ -z "$EXPECTED_BACKEND_COMMIT" ] || [ -z "$EXPECTED_FRONTEND_COMMIT" ]; then
    log_error "예상되는 백엔드와 프론트엔드 커밋 해시를 모두 지정해야 합니다"
    usage
fi

# JSON 출력이 아닌 경우에만 일반 로그 출력
if [ "$JSON_OUTPUT" != true ]; then
    echo ""
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE}  🔍 XAI Community Rollback Verification v1.0${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
    
    log_info "환경: $ENVIRONMENT"
    log_info "타임아웃: ${TIMEOUT}초"
    log_info "재시도 횟수: ${RETRY_COUNT}회"
    log_info "예상 백엔드 커밋: $EXPECTED_BACKEND_COMMIT"
    log_info "예상 프론트엔드 커밋: $EXPECTED_FRONTEND_COMMIT"
fi

# 환경별 설정
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_URL="https://xai-community-backend-798170408536.asia-northeast3.run.app"
    FRONTEND_URL="https://xai-community.vercel.app"
else
    BACKEND_URL="https://xai-community-backend-staging-798170408536.asia-northeast3.run.app"
    FRONTEND_URL="https://xai-community-staging.vercel.app"
fi

# 검증 결과 저장용 변수들
VERIFICATION_START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BACKEND_VERSION_MATCH=false
FRONTEND_VERSION_MATCH=false
BACKEND_HEALTH_OK=false
FRONTEND_HEALTH_OK=false
INTEGRATION_OK=false
OVERALL_SUCCESS=false

BACKEND_ACTUAL_COMMIT=""
FRONTEND_ACTUAL_COMMIT=""
BACKEND_VERSION_INFO=""
FRONTEND_VERSION_INFO=""
ERROR_MESSAGES=()

# 백엔드 버전 검증
verify_backend_version() {
    if [ "$JSON_OUTPUT" != true ]; then
        log_section "=== 백엔드 버전 검증 ==="
    fi
    
    for i in $(seq 1 $RETRY_COUNT); do
        if [ "$JSON_OUTPUT" != true ]; then
            log_info "백엔드 버전 확인 시도 $i/$RETRY_COUNT"
        fi
        
        BACKEND_VERSION_INFO=$(curl -s --max-time 30 "$BACKEND_URL/version" 2>/dev/null || echo '{"error": "request_failed"}')
        
        if echo "$BACKEND_VERSION_INFO" | grep -q "error"; then
            if [ "$JSON_OUTPUT" != true ]; then
                log_warning "백엔드 /version API 접근 실패, /status로 재시도"
            fi
            BACKEND_VERSION_INFO=$(curl -s --max-time 30 "$BACKEND_URL/status" 2>/dev/null || echo '{"error": "status_failed"}')
        fi
        
        if ! echo "$BACKEND_VERSION_INFO" | grep -q "error"; then
            BACKEND_HEALTH_OK=true
            BACKEND_ACTUAL_COMMIT=$(echo "$BACKEND_VERSION_INFO" | jq -r '.commit_hash // "unknown"' 2>/dev/null || echo "unknown")
            
            if [ "$BACKEND_ACTUAL_COMMIT" != "unknown" ] && [ "$BACKEND_ACTUAL_COMMIT" != "null" ]; then
                # 커밋 해시 비교 (처음 8자리만)
                EXPECTED_SHORT=$(echo "$EXPECTED_BACKEND_COMMIT" | cut -c1-8)
                ACTUAL_SHORT=$(echo "$BACKEND_ACTUAL_COMMIT" | cut -c1-8)
                
                if [ "$EXPECTED_SHORT" = "$ACTUAL_SHORT" ]; then
                    BACKEND_VERSION_MATCH=true
                    if [ "$JSON_OUTPUT" != true ]; then
                        log_success "백엔드 버전 일치: $ACTUAL_SHORT"
                    fi
                    break
                else
                    if [ "$JSON_OUTPUT" != true ]; then
                        log_warning "백엔드 버전 불일치: 예상($EXPECTED_SHORT) != 실제($ACTUAL_SHORT)"
                    fi
                    ERROR_MESSAGES+=("Backend version mismatch: expected $EXPECTED_SHORT, got $ACTUAL_SHORT")
                fi
            else
                if [ "$JSON_OUTPUT" != true ]; then
                    log_warning "백엔드 커밋 해시를 가져올 수 없음"
                fi
                ERROR_MESSAGES+=("Backend commit hash not available")
            fi
            break
        else
            if [ "$JSON_OUTPUT" != true ]; then
                log_warning "백엔드 접근 실패, 재시도 중... ($i/$RETRY_COUNT)"
            fi
            ERROR_MESSAGES+=("Backend request failed on attempt $i")
            
            if [ $i -lt $RETRY_COUNT ]; then
                sleep 10
            fi
        fi
    done
}

# 프론트엔드 버전 검증
verify_frontend_version() {
    if [ "$JSON_OUTPUT" != true ]; then
        log_section "=== 프론트엔드 버전 검증 ==="
    fi
    
    for i in $(seq 1 $RETRY_COUNT); do
        if [ "$JSON_OUTPUT" != true ]; then
            log_info "프론트엔드 버전 확인 시도 $i/$RETRY_COUNT"
        fi
        
        FRONTEND_VERSION_INFO=$(curl -s --max-time 30 "$FRONTEND_URL/version" 2>/dev/null || echo '{"error": "request_failed"}')
        
        if echo "$FRONTEND_VERSION_INFO" | grep -q "error"; then
            if [ "$JSON_OUTPUT" != true ]; then
                log_warning "프론트엔드 /version 페이지 접근 실패, HTML 메타태그로 재시도"
            fi
            
            # HTML에서 메타태그 추출
            HTML_CONTENT=$(curl -s --max-time 30 "$FRONTEND_URL" 2>/dev/null || echo "")
            if [ -n "$HTML_CONTENT" ]; then
                FRONTEND_HEALTH_OK=true
                FRONTEND_ACTUAL_COMMIT=$(echo "$HTML_CONTENT" | grep -o 'name="build-commit" content="[^"]*"' | sed 's/.*content="//;s/".*//' || echo "unknown")
            else
                FRONTEND_ACTUAL_COMMIT="unknown"
            fi
        else
            FRONTEND_HEALTH_OK=true
            FRONTEND_ACTUAL_COMMIT=$(echo "$FRONTEND_VERSION_INFO" | jq -r '.commit_hash // "unknown"' 2>/dev/null || echo "unknown")
        fi
        
        if [ "$FRONTEND_ACTUAL_COMMIT" != "unknown" ] && [ "$FRONTEND_ACTUAL_COMMIT" != "null" ]; then
            # 커밋 해시 비교 (처음 8자리만)
            EXPECTED_SHORT=$(echo "$EXPECTED_FRONTEND_COMMIT" | cut -c1-8)
            ACTUAL_SHORT=$(echo "$FRONTEND_ACTUAL_COMMIT" | cut -c1-8)
            
            if [ "$EXPECTED_SHORT" = "$ACTUAL_SHORT" ]; then
                FRONTEND_VERSION_MATCH=true
                if [ "$JSON_OUTPUT" != true ]; then
                    log_success "프론트엔드 버전 일치: $ACTUAL_SHORT"
                fi
                break
            else
                if [ "$JSON_OUTPUT" != true ]; then
                    log_warning "프론트엔드 버전 불일치: 예상($EXPECTED_SHORT) != 실제($ACTUAL_SHORT)"
                fi
                ERROR_MESSAGES+=("Frontend version mismatch: expected $EXPECTED_SHORT, got $ACTUAL_SHORT")
            fi
        else
            if [ "$JSON_OUTPUT" != true ]; then
                log_warning "프론트엔드 커밋 해시를 가져올 수 없음"
            fi
            ERROR_MESSAGES+=("Frontend commit hash not available")
        fi
        
        if [ $i -lt $RETRY_COUNT ]; then
            sleep 10
        fi
    done
}

# 통합 테스트
verify_integration() {
    if [ "$SKIP_INTEGRATION" = true ]; then
        INTEGRATION_OK=true
        return
    fi
    
    if [ "$JSON_OUTPUT" != true ]; then
        log_section "=== 통합 테스트 ==="
    fi
    
    # CORS 테스트
    if [ "$JSON_OUTPUT" != true ]; then
        log_info "CORS 연결 테스트 중..."
    fi
    
    if curl -f -s --max-time 30 -H "Origin: $FRONTEND_URL" "$BACKEND_URL/status" > /dev/null 2>&1; then
        INTEGRATION_OK=true
        if [ "$JSON_OUTPUT" != true ]; then
            log_success "CORS 연결 테스트 성공"
        fi
    else
        if [ "$JSON_OUTPUT" != true ]; then
            log_warning "CORS 연결 테스트 실패"
        fi
        ERROR_MESSAGES+=("CORS integration test failed")
    fi
    
    # API 엔드포인트 테스트
    if [ "$JSON_OUTPUT" != true ]; then
        log_info "API 엔드포인트 테스트 중..."
    fi
    
    if curl -f -s --max-time 30 "$BACKEND_URL/status" > /dev/null 2>&1; then
        if [ "$JSON_OUTPUT" != true ]; then
            log_success "API 엔드포인트 테스트 성공"
        fi
    else
        INTEGRATION_OK=false
        if [ "$JSON_OUTPUT" != true ]; then
            log_warning "API 엔드포인트 테스트 실패"
        fi
        ERROR_MESSAGES+=("API endpoint test failed")
    fi
}

# 검증 실행
verify_backend_version
verify_frontend_version
verify_integration

# 전체 성공 여부 결정
if [ "$BACKEND_VERSION_MATCH" = true ] && [ "$FRONTEND_VERSION_MATCH" = true ] && [ "$INTEGRATION_OK" = true ]; then
    OVERALL_SUCCESS=true
fi

VERIFICATION_END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 결과 출력
if [ "$JSON_OUTPUT" = true ]; then
    # JSON 출력
    cat <<EOF
{
  "verification": {
    "start_time": "$VERIFICATION_START_TIME",
    "end_time": "$VERIFICATION_END_TIME",
    "environment": "$ENVIRONMENT",
    "overall_success": $OVERALL_SUCCESS,
    "backend": {
      "health_ok": $BACKEND_HEALTH_OK,
      "version_match": $BACKEND_VERSION_MATCH,
      "expected_commit": "$EXPECTED_BACKEND_COMMIT",
      "actual_commit": "$BACKEND_ACTUAL_COMMIT",
      "version_info": $BACKEND_VERSION_INFO
    },
    "frontend": {
      "health_ok": $FRONTEND_HEALTH_OK,
      "version_match": $FRONTEND_VERSION_MATCH,
      "expected_commit": "$EXPECTED_FRONTEND_COMMIT",
      "actual_commit": "$FRONTEND_ACTUAL_COMMIT"
    },
    "integration": {
      "test_ok": $INTEGRATION_OK,
      "skipped": $SKIP_INTEGRATION
    },
    "errors": [$(printf '"%s",' "${ERROR_MESSAGES[@]}" | sed 's/,$//')]
  }
}
EOF
else
    # 텍스트 출력
    echo ""
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE}  📊 롤백 검증 결과${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
    
    echo -e "${GREEN}✅ 검증 정보${NC}"
    echo -e "  환경: $ENVIRONMENT"
    echo -e "  시작 시간: $VERIFICATION_START_TIME"
    echo -e "  완료 시간: $VERIFICATION_END_TIME"
    echo ""
    
    echo -e "${GREEN}✅ 백엔드 검증${NC}"
    echo -e "  상태: $([ "$BACKEND_HEALTH_OK" = true ] && echo "정상" || echo "실패")"
    echo -e "  버전 일치: $([ "$BACKEND_VERSION_MATCH" = true ] && echo "일치" || echo "불일치")"
    echo -e "  예상 커밋: $EXPECTED_BACKEND_COMMIT"
    echo -e "  실제 커밋: $BACKEND_ACTUAL_COMMIT"
    echo ""
    
    echo -e "${GREEN}✅ 프론트엔드 검증${NC}"
    echo -e "  상태: $([ "$FRONTEND_HEALTH_OK" = true ] && echo "정상" || echo "실패")"
    echo -e "  버전 일치: $([ "$FRONTEND_VERSION_MATCH" = true ] && echo "일치" || echo "불일치")"
    echo -e "  예상 커밋: $EXPECTED_FRONTEND_COMMIT"
    echo -e "  실제 커밋: $FRONTEND_ACTUAL_COMMIT"
    echo ""
    
    echo -e "${GREEN}✅ 통합 테스트${NC}"
    echo -e "  CORS 연결: $([ "$INTEGRATION_OK" = true ] && echo "성공" || echo "실패")"
    echo -e "  건너뛰기: $([ "$SKIP_INTEGRATION" = true ] && echo "예" || echo "아니오")"
    echo ""
    
    if [ ${#ERROR_MESSAGES[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️ 오류 메시지${NC}"
        for error in "${ERROR_MESSAGES[@]}"; do
            echo -e "  - $error"
        done
        echo ""
    fi
    
    if [ "$OVERALL_SUCCESS" = true ]; then
        echo -e "${GREEN}🎉 롤백 검증 성공!${NC}"
        echo -e "${GREEN}모든 서비스가 예상된 버전으로 정상 롤백되었습니다.${NC}"
    else
        echo -e "${RED}❌ 롤백 검증 실패${NC}"
        echo -e "${RED}일부 서비스가 예상된 버전과 다르거나 정상 작동하지 않습니다.${NC}"
    fi
fi

# 종료 코드 설정
if [ "$OVERALL_SUCCESS" = true ]; then
    exit 0
else
    exit 1
fi