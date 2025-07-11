#!/bin/bash

# XAI Community 부하 테스트 실행 스크립트

echo "🚀 XAI Community 부하 테스트 시작"
echo "=================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 기본 설정
DEFAULT_HOST="http://localhost:8000"
DEFAULT_USERS=10
DEFAULT_SPAWN_RATE=2
DEFAULT_TIME="60s"

# 프로젝트 루트 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOCUST_FILE="$BACKEND_DIR/tests/load/locust_basic_scenarios.py"

# 함수 정의
print_usage() {
    echo -e "${BLUE}사용법:${NC}"
    echo "  $0 [옵션]"
    echo ""
    echo -e "${BLUE}옵션:${NC}"
    echo "  -h, --host HOST        대상 호스트 (기본값: $DEFAULT_HOST)"
    echo "  -u, --users USERS      동시 사용자 수 (기본값: $DEFAULT_USERS)"
    echo "  -r, --spawn-rate RATE  사용자 생성 속도 (기본값: $DEFAULT_SPAWN_RATE)"
    echo "  -t, --time TIME        테스트 실행 시간 (기본값: $DEFAULT_TIME)"
    echo "  -w, --web             웹 UI 모드로 실행"
    echo "  --help                도움말 표시"
    echo ""
    echo -e "${BLUE}예시:${NC}"
    echo "  $0                                    # 기본 설정으로 실행"
    echo "  $0 -u 50 -r 5 -t 300s                # 50명 사용자, 5명/초 생성, 5분 실행"
    echo "  $0 -w                                 # 웹 UI 모드"
    echo "  $0 -h http://example.com -u 100       # 다른 호스트 대상"
}

check_requirements() {
    echo -e "${YELLOW}환경 요구사항 확인 중...${NC}"
    
    # Python 확인
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python이 설치되지 않았습니다.${NC}"
        return 1
    fi
    
    # Locust 확인
    cd "$BACKEND_DIR"
    if ! python -c "import locust" &> /dev/null; then
        echo -e "${RED}❌ Locust가 설치되지 않았습니다.${NC}"
        echo -e "${YELLOW}설치 명령: cd backend && pip install locust${NC}"
        return 1
    fi
    
    # 테스트 파일 확인
    if [ ! -f "$LOCUST_FILE" ]; then
        echo -e "${RED}❌ 테스트 파일을 찾을 수 없습니다: $LOCUST_FILE${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ 모든 요구사항이 충족되었습니다.${NC}"
    return 0
}

check_server() {
    echo -e "${YELLOW}서버 상태 확인 중...${NC}"
    
    # 헬스 체크
    if curl -s -o /dev/null -w "%{http_code}" "$HOST/status" | grep -q "200"; then
        echo -e "${GREEN}✅ 서버가 정상적으로 동작 중입니다.${NC}"
        return 0
    else
        echo -e "${RED}❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.${NC}"
        echo -e "${YELLOW}서버 시작 명령: cd backend && python -m uvicorn main:app --reload${NC}"
        return 1
    fi
}

run_load_test() {
    echo -e "${BLUE}부하 테스트 설정:${NC}"
    echo "  - 대상 호스트: $HOST"
    echo "  - 동시 사용자 수: $USERS"
    echo "  - 사용자 생성 속도: $SPAWN_RATE/초"
    echo "  - 테스트 시간: $TIME"
    echo "  - 웹 UI 모드: $WEB_MODE"
    echo "  - 테스트 파일: $LOCUST_FILE"
    echo ""
    
    # 백엔드 디렉터리로 이동
    cd "$BACKEND_DIR"
    
    # Locust 실행
    if [ "$WEB_MODE" = true ]; then
        echo -e "${GREEN}🌐 웹 UI 모드로 실행 중...${NC}"
        echo -e "${YELLOW}브라우저에서 http://localhost:8089 를 열어주세요${NC}"
        echo -e "${YELLOW}Ctrl+C로 중단할 수 있습니다${NC}"
        locust -f "$LOCUST_FILE" --host="$HOST" --web-host=0.0.0.0 --web-port=8089
    else
        echo -e "${GREEN}🔥 부하 테스트 실행 중...${NC}"
        locust -f "$LOCUST_FILE" --host="$HOST" --users="$USERS" --spawn-rate="$SPAWN_RATE" --run-time="$TIME" --headless --print-stats
    fi
}

# 기본값 설정
HOST=$DEFAULT_HOST
USERS=$DEFAULT_USERS
SPAWN_RATE=$DEFAULT_SPAWN_RATE
TIME=$DEFAULT_TIME
WEB_MODE=false

# 명령행 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            TIME="$2"
            shift 2
            ;;
        -w|--web)
            WEB_MODE=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}알 수 없는 옵션: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# 메인 실행
echo -e "${BLUE}XAI Community 부하 테스트 도구${NC}"
echo "=============================="
echo "프로젝트 루트: $PROJECT_ROOT"
echo "백엔드 경로: $BACKEND_DIR"
echo ""

# 환경 요구사항 확인
if ! check_requirements; then
    exit 1
fi

# 서버 상태 확인
if ! check_server; then
    exit 1
fi

# 부하 테스트 실행
run_load_test

echo ""
echo -e "${GREEN}🎉 부하 테스트 완료!${NC}"
echo -e "${BLUE}결과 분석을 위한 추가 정보:${NC}"
echo "  - 테스트 로그는 콘솔에서 확인하세요"
echo "  - 웹 UI 모드에서는 http://localhost:8089 에서 실시간 모니터링 가능"
echo "  - 서버 로그도 함께 확인하여 성능 분석을 진행하세요"
echo "  - 결과는 tests/results/ 폴더에 저장할 수 있습니다"