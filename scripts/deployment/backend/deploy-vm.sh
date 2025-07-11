#!/bin/bash

# GCP VM 배포 스크립트
# 사용법: ./deploy-vm.sh

set -e  # 오류 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

# 실시간 상태 체크 함수
check_vm_ready() {
    local vm_name="$1"
    local zone="$2"
    local max_wait=300  # 5분 대기
    local count=0
    
    log_info "VM 준비 상태 확인 중..."
    
    while [ $count -lt $max_wait ]; do
        local status=$(gcloud compute instances describe "$vm_name" --zone="$zone" --format="value(status)" 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$status" = "RUNNING" ]; then
            log_success "VM이 실행 중입니다"
            return 0
        elif [ "$status" = "NOT_FOUND" ]; then
            log_error "VM을 찾을 수 없습니다"
            return 1
        else
            echo -n "."
            sleep 2
            ((count+=2))
        fi
    done
    
    log_error "VM 준비 시간 초과"
    return 1
}

# 애플리케이션 헬스체크 함수
wait_for_app() {
    local vm_ip="$1"
    local max_wait=180  # 3분 대기
    local count=0
    
    log_info "애플리케이션 시작 대기 중..."
    
    while [ $count -lt $max_wait ]; do
        if curl -s --max-time 5 "http://$vm_ip:8080/status" > /dev/null 2>&1; then
            log_success "애플리케이션이 정상적으로 시작되었습니다"
            return 0
        elif curl -s --max-time 5 "http://$vm_ip:8080/" > /dev/null 2>&1; then
            log_success "애플리케이션이 시작되었습니다 (헬스체크 엔드포인트 없음)"
            return 0
        else
            echo -n "."
            sleep 5
            ((count+=5))
        fi
    done
    
    log_error "애플리케이션 시작 시간 초과"
    return 1
}

# 배포 상태 실시간 모니터링 함수
monitor_deployment() {
    local vm_name="$1"
    local zone="$2"
    local step="$3"
    
    log_info "[$step] 배포 진행 상황 모니터링 중..."
    
    # VM 상태 확인
    local vm_status=$(gcloud compute instances describe "$vm_name" --zone="$zone" --format="value(status)" 2>/dev/null || echo "NOT_FOUND")
    log_info "VM 상태: $vm_status"
    
    # 시스템 로그 확인 (최근 5줄)
    if [ "$vm_status" = "RUNNING" ]; then
        log_info "시스템 로그 확인 중..."
        gcloud compute ssh "$vm_name" --zone="$zone" --command="sudo journalctl -n 5 --no-pager" 2>/dev/null || log_warning "시스템 로그를 가져올 수 없습니다"
    fi
}

# .env.prod 파일에서 환경변수 로드
if [ -f ".env.prod" ]; then
    log_info ".env.prod 파일에서 환경변수 로드 중..."
    set -a
    source .env.prod
    set +a
    log_success "환경변수 로드 완료"
else
    log_error ".env.prod 파일이 없습니다!"
    exit 1
fi

# VM 설정 기본값
VM_NAME="${VM_NAME:-xai-community-vm}"
VM_ZONE="${VM_ZONE:-asia-northeast3-a}"
VM_MACHINE_TYPE="${VM_MACHINE_TYPE:-e2-micro}"
VM_IMAGE="${VM_IMAGE:-ubuntu-2204-jammy-v20240927}"
VM_IMAGE_PROJECT="${VM_IMAGE_PROJECT:-ubuntu-os-cloud}"
VM_DISK_SIZE="${VM_DISK_SIZE:-20GB}"
VM_TAGS="${VM_TAGS:-http-server,https-server}"

# 필수 환경변수 확인
log_info "필수 환경변수 확인 중..."
required_vars=("PROJECT_ID" "MONGODB_URL" "SECRET_KEY" "DATABASE_NAME")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "환경변수 $var가 설정되지 않았습니다!"
        exit 1
    fi
done
log_success "필수 환경변수 확인 완료"

# Google Cloud 인증 상태 확인
log_info "Google Cloud 인증 상태 확인 중..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "Google Cloud 인증이 필요합니다! 'gcloud auth login' 실행 후 다시 시도해주세요."
    exit 1
fi
log_success "Google Cloud 인증 확인 완료"

# Google Cloud 프로젝트 설정
log_info "Google Cloud 프로젝트 설정 중..."
gcloud config set project "$PROJECT_ID"
log_success "프로젝트 설정 완료: $PROJECT_ID"

# 필요한 서비스 활성화
log_info "Google Cloud 서비스 활성화 중..."
gcloud services enable compute.googleapis.com
log_success "Compute Engine API 활성화 완료"

# 방화벽 규칙 생성 (필요한 경우)
log_info "방화벽 규칙 확인 중..."
if ! gcloud compute firewall-rules describe allow-backend-port --quiet 2>/dev/null; then
    log_info "백엔드 포트용 방화벽 규칙 생성 중..."
    gcloud compute firewall-rules create allow-backend-port \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow backend port 8080" \
        --target-tags http-server
    log_success "방화벽 규칙 생성 완료"
else
    log_info "방화벽 규칙이 이미 존재합니다"
fi

# VM 인스턴스 생성
log_info "VM 인스턴스 생성 중..."
log_info "VM 설정:"
log_info "  - 이름: $VM_NAME"
log_info "  - 존: $VM_ZONE"
log_info "  - 머신 타입: $VM_MACHINE_TYPE"
log_info "  - 이미지: $VM_IMAGE"
log_info "  - 디스크 크기: $VM_DISK_SIZE"

# 시작 스크립트 생성
STARTUP_SCRIPT=$(cat <<'EOF'
#!/bin/bash
# 시스템 업데이트
apt-get update
apt-get install -y docker.io git curl

# Docker 서비스 시작
systemctl enable docker
systemctl start docker

# Docker 사용자 권한 설정
usermod -aG docker $USER

# 프로젝트 클론 및 배포 준비
mkdir -p /app
cd /app

# Docker로 애플리케이션 실행 (환경변수는 VM 메타데이터에서 가져옴)
echo "VM 준비 완료" > /tmp/setup.log
EOF
)

if gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --quiet 2>/dev/null; then
    log_warning "VM $VM_NAME이 이미 존재합니다. 재생성하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "기존 VM 삭제 중..."
        gcloud compute instances delete "$VM_NAME" --zone="$VM_ZONE" --quiet
        log_success "기존 VM 삭제 완료"
    else
        log_info "기존 VM을 사용합니다"
        VM_EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
        log_success "VM 외부 IP: $VM_EXTERNAL_IP"
        echo -e "${GREEN}VM 접속 명령어: gcloud compute ssh $VM_NAME --zone=$VM_ZONE${NC}"
        exit 0
    fi
fi

gcloud compute instances create "$VM_NAME" \
    --zone="$VM_ZONE" \
    --machine-type="$VM_MACHINE_TYPE" \
    --image="$VM_IMAGE" \
    --image-project="$VM_IMAGE_PROJECT" \
    --boot-disk-size="$VM_DISK_SIZE" \
    --boot-disk-type="pd-standard" \
    --tags="$VM_TAGS" \
    --metadata-from-file startup-script=<(echo "$STARTUP_SCRIPT") \
    --metadata="mongodb-url=$MONGODB_URL,secret-key=$SECRET_KEY,database-name=$DATABASE_NAME,environment=production"

if [ $? -eq 0 ]; then
    log_success "VM 인스턴스 생성 완료!"
    monitor_deployment "$VM_NAME" "$VM_ZONE" "VM 생성 후"
else
    log_error "VM 인스턴스 생성 실패!"
    exit 1
fi

# VM 준비 상태 확인
if ! check_vm_ready "$VM_NAME" "$VM_ZONE"; then
    log_error "VM 준비 실패"
    exit 1
fi

# VM 외부 IP 확인
log_info "VM 외부 IP 확인 중..."
VM_EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
log_success "VM 외부 IP: $VM_EXTERNAL_IP"

# 애플리케이션 배포 스크립트 생성
log_info "애플리케이션 배포 스크립트 생성 중..."
cat > deploy-app-to-vm.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
# VM에 애플리케이션 배포하는 스크립트

set -e

# 환경변수 설정
export MONGODB_URL=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url" -H "Metadata-Flavor: Google")
export SECRET_KEY=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key" -H "Metadata-Flavor: Google")
export DATABASE_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name" -H "Metadata-Flavor: Google")

# 애플리케이션 디렉토리로 이동
cd /app

# 기존 컨테이너 정리
docker stop xai-backend || true
docker rm xai-backend || true

# 새 컨테이너 실행
docker run -d \
    --name xai-backend \
    --restart unless-stopped \
    -p 8080:8080 \
    -e MONGODB_URL="$MONGODB_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    -e DATABASE_NAME="$DATABASE_NAME" \
    -e ENVIRONMENT=production \
    -e PORT=8080 \
    xai-backend:latest

echo "애플리케이션 배포 완료!"
DEPLOY_SCRIPT

chmod +x deploy-app-to-vm.sh

# 소스 코드 전송 및 Docker 이미지 빌드
log_info "소스 코드 전송 및 Docker 이미지 빌드 중..."
monitor_deployment "$VM_NAME" "$VM_ZONE" "소스 코드 전송 전"

# VM에 연결하여 애플리케이션 배포
log_info "VM에서 /app 디렉토리 생성 중..."
if ! gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo mkdir -p /app && sudo chown -R \$USER:\$USER /app" --quiet; then
    log_error "/app 디렉토리 생성 실패!"
    exit 1
fi

log_info "VM에 소스 코드 전송 중..."
# 먼저 모든 파일을 전송 (숨겨진 파일 제외)
if ! gcloud compute scp --recurse * "$VM_NAME:/app/" --zone="$VM_ZONE" --quiet; then
    log_error "소스 코드 전송 실패!"
    exit 1
fi

# 중요한 숨겨진 파일들 개별 전송
log_info "환경 파일 전송 중..."
if ! gcloud compute scp .env.prod "$VM_NAME:/app/" --zone="$VM_ZONE" --quiet; then
    log_error "환경 파일 전송 실패!"
    exit 1
fi
log_success "소스 코드 전송 완료"

log_info "VM에서 Docker 이미지 빌드 중..."

# 기존 이미지 백업 생성
log_info "기존 이미지 백업 생성 중..."
BACKUP_TAG="backup-$(date +%Y%m%d-%H%M%S)"
gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
    if sudo docker images | grep -q 'xai-backend.*latest'; then
        sudo docker tag xai-backend:latest xai-backend:$BACKUP_TAG
        echo 'Backup created: xai-backend:$BACKUP_TAG'
    fi
    
    # 오래된 백업 정리 (최근 5개만 유지)
    sudo docker images --format 'table {{.Repository}}:{{.Tag}}' | grep 'xai-backend:backup-' | tail -n +6 | xargs -r sudo docker rmi 2>/dev/null || true
" 2>/dev/null

if ! gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="cd /app && sudo docker build -t xai-backend:latest . 2>&1"; then
    log_error "Docker 이미지 빌드 실패!"
    monitor_deployment "$VM_NAME" "$VM_ZONE" "Docker 빌드 실패"
    
    # 자동 롤백 시도
    log_info "자동 롤백 시도 중..."
    if [ -f "rollback-vm.sh" ]; then
        chmod +x rollback-vm.sh
        ./rollback-vm.sh "$VM_NAME" "$VM_ZONE"
    fi
    
    exit 1
fi
log_success "Docker 이미지 빌드 완료"

log_info "VM에서 애플리케이션 실행 중..."
if ! gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="cd /app && sudo bash deploy-app-to-vm.sh"; then
    log_error "애플리케이션 실행 실패!"
    monitor_deployment "$VM_NAME" "$VM_ZONE" "애플리케이션 실행 실패"
    
    # 자동 롤백 시도
    log_info "자동 롤백 시도 중..."
    if [ -f "rollback-vm.sh" ]; then
        chmod +x rollback-vm.sh
        ./rollback-vm.sh "$VM_NAME" "$VM_ZONE"
    fi
    
    exit 1
fi
log_success "애플리케이션 실행 완료"

# 애플리케이션 헬스체크
log_info "애플리케이션 헬스체크 중..."
if wait_for_app "$VM_EXTERNAL_IP"; then
    log_success "애플리케이션이 정상적으로 시작되었습니다!"
else
    log_error "애플리케이션 시작 실패!"
    monitor_deployment "$VM_NAME" "$VM_ZONE" "애플리케이션 헬스체크 실패"
    
    # 디버깅 정보 출력
    log_info "디버깅 정보 수집 중..."
    gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo docker logs xai-backend" 2>/dev/null || log_warning "Docker 로그를 가져올 수 없습니다"
    
    # 자동 롤백 시도
    log_info "자동 롤백 시도 중..."
    if [ -f "rollback-vm.sh" ]; then
        chmod +x rollback-vm.sh
        ./rollback-vm.sh "$VM_NAME" "$VM_ZONE"
    fi
    
    exit 1
fi

# 배포 완료 메시지
log_success "VM 배포 완료!"
echo -e "\n${BLUE}=== 배포 완료 정보 ===${NC}"
echo -e "${GREEN}VM 이름:${NC} $VM_NAME"
echo -e "${GREEN}VM 존:${NC} $VM_ZONE"
echo -e "${GREEN}VM 외부 IP:${NC} $VM_EXTERNAL_IP"
echo -e "${GREEN}애플리케이션 URL:${NC} http://$VM_EXTERNAL_IP:8080"
echo -e "${GREEN}API 문서:${NC} http://$VM_EXTERNAL_IP:8080/docs"

echo -e "\n${YELLOW}VM 관리 명령어:${NC}"
echo -e "VM 접속: gcloud compute ssh $VM_NAME --zone=$VM_ZONE"
echo -e "VM 상태 확인: gcloud compute instances describe $VM_NAME --zone=$VM_ZONE"
echo -e "VM 중지: gcloud compute instances stop $VM_NAME --zone=$VM_ZONE"
echo -e "VM 시작: gcloud compute instances start $VM_NAME --zone=$VM_ZONE"
echo -e "VM 삭제: gcloud compute instances delete $VM_NAME --zone=$VM_ZONE"

echo -e "\n${YELLOW}애플리케이션 로그 확인:${NC}"
echo -e "gcloud compute ssh $VM_NAME --zone=$VM_ZONE --command='sudo docker logs xai-backend'"

echo -e "\n${GREEN}배포 완료!${NC}"