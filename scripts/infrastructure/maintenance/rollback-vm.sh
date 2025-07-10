#!/bin/bash

# VM 롤백 스크립트
# 사용법: ./rollback-vm.sh [VM_NAME] [ZONE]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 환경변수 로드
if [ -f ".env.prod" ]; then
    set -a
    source .env.prod
    set +a
fi

VM_NAME="${1:-${VM_NAME:-xai-community-vm}}"
VM_ZONE="${2:-${VM_ZONE:-asia-northeast3-a}}"

log_info "=== VM 롤백 시작 ==="
log_info "VM 이름: $VM_NAME"
log_info "Zone: $VM_ZONE"

# VM 상태 확인
log_info "VM 상태 확인 중..."
VM_STATUS=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "NOT_FOUND" ]; then
    log_error "VM을 찾을 수 없습니다!"
    exit 1
fi

log_info "현재 VM 상태: $VM_STATUS"

# 현재 컨테이너 상태 백업
log_info "현재 컨테이너 상태 백업 중..."
gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
    sudo docker ps -a > /tmp/containers_backup.txt 2>/dev/null || true
    sudo docker images > /tmp/images_backup.txt 2>/dev/null || true
    sudo docker logs xai-backend > /tmp/app_logs_backup.txt 2>/dev/null || true
    echo 'Container backup completed at $(date)' >> /tmp/rollback.log
" 2>/dev/null

# 애플리케이션 컨테이너 중지 및 제거
log_info "현재 애플리케이션 컨테이너 중지 중..."
gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
    sudo docker stop xai-backend 2>/dev/null || true
    sudo docker rm xai-backend 2>/dev/null || true
    echo 'Container stopped and removed at $(date)' >> /tmp/rollback.log
" 2>/dev/null

log_success "애플리케이션 컨테이너 중지 완료"

# 이전 백업 이미지 확인
log_info "이전 백업 이미지 확인 중..."
BACKUP_IMAGES=$(gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo docker images --format 'table {{.Repository}}:{{.Tag}}' | grep 'xai-backend' | grep -v 'latest' | head -3" 2>/dev/null || echo "")

if [ -n "$BACKUP_IMAGES" ]; then
    log_info "사용 가능한 백업 이미지:"
    echo "$BACKUP_IMAGES"
    
    # 가장 최근 백업 이미지 선택
    LATEST_BACKUP=$(echo "$BACKUP_IMAGES" | head -1)
    log_info "롤백할 이미지: $LATEST_BACKUP"
    
    # 백업 이미지로 롤백
    log_info "백업 이미지로 롤백 중..."
    ROLLBACK_SCRIPT="
        export MONGODB_URL=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url' -H 'Metadata-Flavor: Google')
        export SECRET_KEY=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key' -H 'Metadata-Flavor: Google')
        export DATABASE_NAME=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name' -H 'Metadata-Flavor: Google')
        
        sudo docker run -d \
            --name xai-backend \
            --restart unless-stopped \
            -p 8080:8080 \
            -e MONGODB_URL=\"\$MONGODB_URL\" \
            -e SECRET_KEY=\"\$SECRET_KEY\" \
            -e DATABASE_NAME=\"\$DATABASE_NAME\" \
            -e ENVIRONMENT=production \
            -e PORT=8080 \
            $LATEST_BACKUP
        
        echo 'Rollback completed at \$(date)' >> /tmp/rollback.log
    "
    
    if gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="$ROLLBACK_SCRIPT" 2>/dev/null; then
        log_success "백업 이미지로 롤백 완료"
    else
        log_error "백업 이미지 롤백 실패"
        
        # 긴급 복구 시도
        log_info "긴급 복구 시도 중..."
        emergency_recovery
    fi
else
    log_warning "사용 가능한 백업 이미지가 없습니다"
    
    # 기본 복구 시도
    log_info "기본 복구 시도 중..."
    basic_recovery
fi

# 롤백 후 헬스체크
log_info "롤백 후 애플리케이션 헬스체크 중..."
VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

# 헬스체크
HEALTH_CHECK_COUNT=0
MAX_HEALTH_CHECKS=12  # 1분 대기

while [ $HEALTH_CHECK_COUNT -lt $MAX_HEALTH_CHECKS ]; do
    if curl -s --max-time 5 "http://$VM_IP:8080/health" > /dev/null 2>&1; then
        log_success "애플리케이션이 정상적으로 복구되었습니다!"
        break
    elif curl -s --max-time 5 "http://$VM_IP:8080/" > /dev/null 2>&1; then
        log_success "애플리케이션이 복구되었습니다 (헬스체크 엔드포인트 없음)"
        break
    else
        echo -n "."
        sleep 5
        ((HEALTH_CHECK_COUNT++))
    fi
done

if [ $HEALTH_CHECK_COUNT -eq $MAX_HEALTH_CHECKS ]; then
    log_error "롤백 후에도 애플리케이션이 정상적으로 작동하지 않습니다"
    
    # 디버깅 정보 수집
    log_info "디버깅 정보 수집 중..."
    gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
        echo '=== Docker 컨테이너 상태 ===' >> /tmp/debug.log
        sudo docker ps -a >> /tmp/debug.log 2>&1
        echo '=== 애플리케이션 로그 ===' >> /tmp/debug.log
        sudo docker logs xai-backend >> /tmp/debug.log 2>&1
        echo '=== 시스템 로그 ===' >> /tmp/debug.log
        sudo journalctl -u docker.service --no-pager -n 20 >> /tmp/debug.log 2>&1
        cat /tmp/debug.log
    " 2>/dev/null
    
    exit 1
fi

# 롤백 완료 메시지
log_success "롤백 완료!"
echo -e "\n${BLUE}=== 롤백 완료 정보 ===${NC}"
echo -e "${GREEN}VM 이름:${NC} $VM_NAME"
echo -e "${GREEN}VM 존:${NC} $VM_ZONE"
echo -e "${GREEN}VM 외부 IP:${NC} $VM_IP"
echo -e "${GREEN}애플리케이션 URL:${NC} http://$VM_IP:8080"
echo -e "${GREEN}API 문서:${NC} http://$VM_IP:8080/docs"

# 긴급 복구 함수
emergency_recovery() {
    log_info "긴급 복구 시도 중..."
    
    # 최신 이미지 재빌드 시도
    gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
        cd /app
        sudo docker build -t xai-backend:emergency .
        
        export MONGODB_URL=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url' -H 'Metadata-Flavor: Google')
        export SECRET_KEY=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key' -H 'Metadata-Flavor: Google')
        export DATABASE_NAME=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name' -H 'Metadata-Flavor: Google')
        
        sudo docker run -d \
            --name xai-backend \
            --restart unless-stopped \
            -p 8080:8080 \
            -e MONGODB_URL=\"\$MONGODB_URL\" \
            -e SECRET_KEY=\"\$SECRET_KEY\" \
            -e DATABASE_NAME=\"\$DATABASE_NAME\" \
            -e ENVIRONMENT=production \
            -e PORT=8080 \
            xai-backend:emergency
    " 2>/dev/null
    
    log_info "긴급 복구 완료"
}

# 기본 복구 함수
basic_recovery() {
    log_info "기본 복구 시도 중..."
    
    # 현재 latest 이미지로 재시작
    gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
        export MONGODB_URL=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url' -H 'Metadata-Flavor: Google')
        export SECRET_KEY=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key' -H 'Metadata-Flavor: Google')
        export DATABASE_NAME=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name' -H 'Metadata-Flavor: Google')
        
        sudo docker run -d \
            --name xai-backend \
            --restart unless-stopped \
            -p 8080:8080 \
            -e MONGODB_URL=\"\$MONGODB_URL\" \
            -e SECRET_KEY=\"\$SECRET_KEY\" \
            -e DATABASE_NAME=\"\$DATABASE_NAME\" \
            -e ENVIRONMENT=production \
            -e PORT=8080 \
            xai-backend:latest
    " 2>/dev/null
    
    log_info "기본 복구 완료"
}