#!/bin/bash

# VM 초기 설정 스크립트 (VM 내부에서 실행)
# 이 스크립트는 VM에 SSH 접속 후 실행됩니다.

set -e

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

# 시스템 업데이트
log_info "시스템 업데이트 중..."
sudo apt-get update -y
sudo apt-get upgrade -y
log_success "시스템 업데이트 완료"

# 필수 패키지 설치
log_info "필수 패키지 설치 중..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    htop \
    ufw \
    unzip \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release
log_success "필수 패키지 설치 완료"

# Docker 설치
log_info "Docker 설치 중..."
if ! command -v docker &> /dev/null; then
    # Docker 공식 GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Docker 리포지토리 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Docker 서비스 시작
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # 현재 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER
    
    log_success "Docker 설치 완료"
else
    log_info "Docker가 이미 설치되어 있습니다"
fi

# Docker Compose 설치
log_info "Docker Compose 설치 중..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K[^"]*')
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose 설치 완료"
else
    log_info "Docker Compose가 이미 설치되어 있습니다"
fi

# 방화벽 설정
log_info "방화벽 설정 중..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 8080/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
log_success "방화벽 설정 완료"

# 작업 디렉토리 생성
log_info "작업 디렉토리 생성 중..."
sudo mkdir -p /app
sudo chown -R $USER:$USER /app
mkdir -p /app/uploads
mkdir -p /app/logs
mkdir -p /app/ssl
log_success "작업 디렉토리 생성 완료"

# 환경변수 로드 함수
load_metadata() {
    log_info "메타데이터에서 환경변수 로드 중..."
    
    # 메타데이터에서 환경변수 가져오기
    export MONGODB_URL=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url" -H "Metadata-Flavor: Google" || echo "")
    export SECRET_KEY=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key" -H "Metadata-Flavor: Google" || echo "")
    export DATABASE_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name" -H "Metadata-Flavor: Google" || echo "")
    export ENVIRONMENT=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/environment" -H "Metadata-Flavor: Google" || echo "production")
    
    # .env 파일 생성
    cat > /app/.env << EOF
MONGODB_URL=$MONGODB_URL
SECRET_KEY=$SECRET_KEY
DATABASE_NAME=$DATABASE_NAME
ENVIRONMENT=$ENVIRONMENT
PORT=8080
HOST=0.0.0.0
LOG_LEVEL=INFO
MAX_COMMENT_DEPTH=3
ENABLE_DOCS=false
ENABLE_CORS=true
USERS_COLLECTION=users
POSTS_COLLECTION=posts
COMMENTS_COLLECTION=comments
POST_STATS_COLLECTION=post_stats
USER_REACTIONS_COLLECTION=user_reactions
FILES_COLLECTION=files
STATS_COLLECTION=stats
EOF
    
    log_success "환경변수 로드 완료"
}

# SSL 인증서 생성 (자체 서명 - 개발용)
setup_ssl() {
    log_info "SSL 인증서 생성 중..."
    if [ ! -f "/app/ssl/cert.pem" ]; then
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /app/ssl/key.pem \
            -out /app/ssl/cert.pem \
            -subj "/C=KR/ST=Seoul/L=Seoul/O=XaiCommunity/CN=localhost"
        sudo chown -R $USER:$USER /app/ssl
        log_success "SSL 인증서 생성 완료"
    else
        log_info "SSL 인증서가 이미 존재합니다"
    fi
}

# 시스템 정보 출력
system_info() {
    log_info "시스템 정보:"
    echo "  - OS: $(lsb_release -d | cut -f2)"
    echo "  - 커널: $(uname -r)"
    echo "  - 아키텍처: $(uname -m)"
    echo "  - 메모리: $(free -h | grep Mem | awk '{print $2}')"
    echo "  - 디스크: $(df -h / | tail -1 | awk '{print $2}')"
    echo "  - Docker: $(docker --version)"
    echo "  - Docker Compose: $(docker-compose --version)"
}

# 애플리케이션 배포 함수
deploy_app() {
    log_info "애플리케이션 배포 중..."
    
    cd /app
    
    # Docker 이미지 빌드
    if [ -f "Dockerfile" ]; then
        log_info "Docker 이미지 빌드 중..."
        docker build -t xai-backend:latest .
        log_success "Docker 이미지 빌드 완료"
    else
        log_error "Dockerfile이 없습니다!"
        return 1
    fi
    
    # 기존 컨테이너 정리
    docker stop xai-backend || true
    docker rm xai-backend || true
    
    # 새 컨테이너 실행
    log_info "컨테이너 실행 중..."
    docker run -d \
        --name xai-backend \
        --restart unless-stopped \
        -p 8080:8080 \
        --env-file /app/.env \
        -v /app/uploads:/app/uploads \
        -v /app/logs:/app/logs \
        xai-backend:latest
    
    log_success "애플리케이션 배포 완료!"
}

# 상태 확인 함수
check_status() {
    log_info "애플리케이션 상태 확인 중..."
    
    # 컨테이너 상태 확인
    if docker ps | grep -q xai-backend; then
        log_success "컨테이너가 실행 중입니다"
    else
        log_error "컨테이너가 실행되지 않았습니다"
        return 1
    fi
    
    # 애플리케이션 응답 확인
    sleep 5
    if curl -f http://localhost:8080/ -o /dev/null -s; then
        log_success "애플리케이션이 정상적으로 응답합니다"
    else
        log_warning "애플리케이션 응답 확인 실패"
        log_info "로그를 확인하세요: docker logs xai-backend"
    fi
}

# 메인 실행 함수
main() {
    log_info "VM 설정 시작..."
    
    # 메타데이터 로드
    load_metadata
    
    # SSL 설정
    setup_ssl
    
    # 시스템 정보 출력
    system_info
    
    # 애플리케이션 배포 (소스 코드가 있는 경우)
    if [ -f "/app/Dockerfile" ]; then
        deploy_app
        check_status
    else
        log_info "소스 코드가 없습니다. 수동으로 배포하세요."
        log_info "사용 방법:"
        log_info "1. 소스 코드를 /app 디렉토리에 업로드"
        log_info "2. cd /app && bash setup-vm.sh deploy"
    fi
    
    log_success "VM 설정 완료!"
    log_info "애플리케이션 URL: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google'):8080"
}

# 명령어 처리
case "${1:-setup}" in
    setup)
        main
        ;;
    deploy)
        load_metadata
        deploy_app
        check_status
        ;;
    status)
        check_status
        ;;
    logs)
        docker logs xai-backend
        ;;
    restart)
        docker restart xai-backend
        log_success "애플리케이션 재시작 완료"
        ;;
    stop)
        docker stop xai-backend
        log_success "애플리케이션 중지 완료"
        ;;
    start)
        docker start xai-backend
        log_success "애플리케이션 시작 완료"
        ;;
    *)
        echo "사용법: $0 {setup|deploy|status|logs|restart|stop|start}"
        exit 1
        ;;
esac