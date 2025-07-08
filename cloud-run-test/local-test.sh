#!/bin/bash

# 로컬 테스트 스크립트
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="cloud-run-test-local"
CONTAINER_NAME="cloud-run-test-container"
PORT=8080

log_info "========================================="
log_info "    로컬 테스트 스크립트 시작"
log_info "========================================="

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    exit 1
fi

# 기존 컨테이너 정리
log_info "기존 컨테이너 정리 중..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Docker 이미지 빌드
log_info "Docker 이미지 빌드 시작..."
cd "$SCRIPT_DIR"

if ! docker build -t $IMAGE_NAME .; then
    log_error "Docker 이미지 빌드 실패"
    exit 1
fi

log_success "Docker 이미지 빌드 완료: $IMAGE_NAME"

# 컨테이너 실행
log_info "컨테이너 실행 중..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:$PORT \
    -e PORT=$PORT \
    -e ENVIRONMENT=development \
    $IMAGE_NAME

log_success "컨테이너 실행 완료"

# 서비스 시작 대기
log_info "서비스 시작 대기 중..."
sleep 5

# 헬스체크
log_info "헬스체크 수행 중..."
if command -v curl &> /dev/null; then
    if curl -s -f "http://localhost:$PORT/health" > /dev/null; then
        log_success "헬스체크 성공!"
    else
        log_error "헬스체크 실패"
        docker logs $CONTAINER_NAME
        exit 1
    fi
else
    log_warning "curl이 설치되지 않아 헬스체크를 수행할 수 없습니다."
fi

echo ""
log_success "로컬 테스트 서버 실행 완료!"
echo "========================================="
echo "테스트 URL들:"
echo "  - 기본: http://localhost:$PORT"
echo "  - 헬스체크: http://localhost:$PORT/health"
echo "  - 환경 정보: http://localhost:$PORT/env"
echo "  - API 문서: http://localhost:$PORT/docs"
echo ""
echo "컨테이너 관리 명령:"
echo "  - 로그 확인: docker logs $CONTAINER_NAME"
echo "  - 컨테이너 정지: docker stop $CONTAINER_NAME"
echo "  - 컨테이너 삭제: docker rm $CONTAINER_NAME"
echo "========================================="