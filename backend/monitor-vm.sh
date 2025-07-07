#!/bin/bash

# VM 실시간 모니터링 스크립트
# 사용법: ./monitor-vm.sh [VM_NAME] [ZONE]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_debug() {
    echo -e "${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG]${NC} $1"
}

# 환경변수 로드
if [ -f ".env.prod" ]; then
    set -a
    source .env.prod
    set +a
fi

# 기본값 설정
VM_NAME="${1:-${VM_NAME:-xai-community-vm}}"
VM_ZONE="${2:-${VM_ZONE:-asia-northeast3-a}}"
MONITOR_INTERVAL="${MONITOR_INTERVAL:-5}"
LOG_FILE="vm-monitor-$(date +%Y%m%d-%H%M%S).log"

# 로그 파일 생성
exec > >(tee -a "$LOG_FILE")
exec 2>&1

log_info "=== VM 실시간 모니터링 시작 ==="
log_info "VM 이름: $VM_NAME"
log_info "Zone: $VM_ZONE"
log_info "모니터링 간격: ${MONITOR_INTERVAL}초"
log_info "로그 파일: $LOG_FILE"
log_info "종료하려면 Ctrl+C를 누르세요"

# VM 상태 확인 함수
check_vm_status() {
    local vm_status
    vm_status=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(status)" 2>/dev/null || echo "NOT_FOUND")
    echo "$vm_status"
}

# VM 외부 IP 확인 함수
get_vm_ip() {
    local vm_ip
    vm_ip=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null || echo "")
    echo "$vm_ip"
}

# 애플리케이션 헬스체크 함수
check_app_health() {
    local vm_ip="$1"
    local health_status="DOWN"
    
    if [ -n "$vm_ip" ]; then
        if curl -s --max-time 5 "http://$vm_ip:8080/health" > /dev/null 2>&1; then
            health_status="UP"
        elif curl -s --max-time 5 "http://$vm_ip:8080/" > /dev/null 2>&1; then
            health_status="PARTIAL"
        fi
    fi
    
    echo "$health_status"
}

# Docker 컨테이너 상태 확인 함수
check_docker_status() {
    local container_status
    container_status=$(gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo docker ps --filter name=xai-backend --format '{{.Status}}'" 2>/dev/null || echo "UNKNOWN")
    echo "$container_status"
}

# 시스템 리소스 확인 함수
check_system_resources() {
    local cpu_usage mem_usage disk_usage
    
    # VM에서 시스템 리소스 정보 가져오기
    local resources=$(gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="
        cpu=\$(top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | sed 's/%us,//')
        mem=\$(free | grep Mem | awk '{printf \"%.1f\", \$3/\$2 * 100.0}')
        disk=\$(df -h / | awk 'NR==2 {print \$5}' | sed 's/%//')
        echo \"\$cpu|\$mem|\$disk\"
    " 2>/dev/null || echo "0|0|0")
    
    echo "$resources"
}

# 애플리케이션 로그 확인 함수
get_app_logs() {
    local log_lines="${1:-10}"
    gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo docker logs --tail $log_lines xai-backend 2>/dev/null" 2>/dev/null || echo "로그를 가져올 수 없습니다"
}

# 메인 모니터링 루프
monitor_vm() {
    local previous_status=""
    local previous_app_status=""
    local error_count=0
    local max_errors=5
    
    while true; do
        echo -e "\n${CYAN}=== 모니터링 체크 $(date '+%Y-%m-%d %H:%M:%S') ===${NC}"
        
        # VM 상태 확인
        local vm_status=$(check_vm_status)
        local vm_ip=$(get_vm_ip)
        
        if [ "$vm_status" != "$previous_status" ]; then
            if [ "$vm_status" = "RUNNING" ]; then
                log_success "VM이 실행 중입니다 (IP: $vm_ip)"
            elif [ "$vm_status" = "STOPPED" ]; then
                log_error "VM이 중지되었습니다"
            elif [ "$vm_status" = "NOT_FOUND" ]; then
                log_error "VM을 찾을 수 없습니다"
            else
                log_warning "VM 상태: $vm_status"
            fi
            previous_status="$vm_status"
        fi
        
        if [ "$vm_status" = "RUNNING" ] && [ -n "$vm_ip" ]; then
            # 애플리케이션 헬스체크
            local app_status=$(check_app_health "$vm_ip")
            
            if [ "$app_status" != "$previous_app_status" ]; then
                if [ "$app_status" = "UP" ]; then
                    log_success "애플리케이션이 정상 작동 중입니다"
                    error_count=0
                elif [ "$app_status" = "PARTIAL" ]; then
                    log_warning "애플리케이션이 부분적으로 작동 중입니다"
                else
                    log_error "애플리케이션에 접근할 수 없습니다"
                    ((error_count++))
                fi
                previous_app_status="$app_status"
            fi
            
            # Docker 컨테이너 상태
            local docker_status=$(check_docker_status)
            if [[ "$docker_status" == *"Up"* ]]; then
                log_debug "Docker 컨테이너 상태: 정상"
            else
                log_warning "Docker 컨테이너 상태: $docker_status"
            fi
            
            # 시스템 리소스 확인
            local resources=$(check_system_resources)
            IFS='|' read -r cpu_usage mem_usage disk_usage <<< "$resources"
            
            if [ "$cpu_usage" != "0" ]; then
                log_debug "시스템 리소스 - CPU: ${cpu_usage}%, MEM: ${mem_usage}%, DISK: ${disk_usage}%"
                
                # 리소스 경고
                if (( $(echo "$cpu_usage > 80" | bc -l) )); then
                    log_warning "높은 CPU 사용률: ${cpu_usage}%"
                fi
                if (( $(echo "$mem_usage > 80" | bc -l) )); then
                    log_warning "높은 메모리 사용률: ${mem_usage}%"
                fi
                if (( disk_usage > 80 )); then
                    log_warning "높은 디스크 사용률: ${disk_usage}%"
                fi
            fi
            
            # 연속적인 오류 발생 시 조치
            if [ $error_count -ge $max_errors ]; then
                log_error "연속적인 오류 발생! 애플리케이션 재시작을 시도합니다..."
                restart_application
                error_count=0
            fi
        fi
        
        sleep "$MONITOR_INTERVAL"
    done
}

# 애플리케이션 재시작 함수
restart_application() {
    log_info "애플리케이션 재시작 중..."
    
    # 환경변수 다시 로드
    local restart_script="
        export MONGODB_URL=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url' -H 'Metadata-Flavor: Google')
        export SECRET_KEY=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key' -H 'Metadata-Flavor: Google')
        export DATABASE_NAME=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name' -H 'Metadata-Flavor: Google')
        
        sudo docker stop xai-backend || true
        sudo docker rm xai-backend || true
        
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
    "
    
    if gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="$restart_script" 2>/dev/null; then
        log_success "애플리케이션 재시작 완료"
    else
        log_error "애플리케이션 재시작 실패"
    fi
}

# 신호 처리 함수
cleanup() {
    log_info "모니터링을 종료합니다..."
    log_info "로그 파일: $LOG_FILE"
    exit 0
}

# 신호 처리 등록
trap cleanup SIGINT SIGTERM

# 모니터링 시작
monitor_vm