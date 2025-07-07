#!/bin/bash

# 빠른 헬스체크 스크립트
# 사용법: ./health-check.sh [VM_NAME] [ZONE]

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 환경변수 로드
if [ -f ".env.prod" ]; then
    set -a
    source .env.prod
    set +a
fi

VM_NAME="${1:-${VM_NAME:-xai-community-vm}}"
VM_ZONE="${2:-${VM_ZONE:-asia-northeast3-a}}"

echo -e "${BLUE}=== 빠른 헬스체크 $(date '+%Y-%m-%d %H:%M:%S') ===${NC}"

# VM 상태 확인
echo -n "VM 상태 확인... "
VM_STATUS=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "RUNNING" ]; then
    echo -e "${GREEN}정상 (RUNNING)${NC}"
    
    # VM IP 가져오기
    VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$VM_ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null)
    echo "VM IP: $VM_IP"
    
    # 애플리케이션 헬스체크
    echo -n "애플리케이션 상태 확인... "
    if curl -s --max-time 5 "http://$VM_IP:8080/health" > /dev/null 2>&1; then
        echo -e "${GREEN}정상${NC}"
        
        # API 응답 테스트
        echo -n "API 응답 테스트... "
        if curl -s --max-time 5 "http://$VM_IP:8080/docs" > /dev/null 2>&1; then
            echo -e "${GREEN}정상${NC}"
        else
            echo -e "${YELLOW}부분적${NC}"
        fi
        
    elif curl -s --max-time 5 "http://$VM_IP:8080/" > /dev/null 2>&1; then
        echo -e "${YELLOW}부분적 (헬스체크 엔드포인트 없음)${NC}"
    else
        echo -e "${RED}실패${NC}"
        
        # Docker 컨테이너 상태 확인
        echo -n "Docker 컨테이너 상태 확인... "
        DOCKER_STATUS=$(gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo docker ps --filter name=xai-backend --format 'table {{.Status}}'" 2>/dev/null | tail -n +2)
        if [ -n "$DOCKER_STATUS" ]; then
            echo -e "${YELLOW}$DOCKER_STATUS${NC}"
        else
            echo -e "${RED}컨테이너 없음${NC}"
        fi
    fi
    
elif [ "$VM_STATUS" = "STOPPED" ]; then
    echo -e "${RED}중지됨 (STOPPED)${NC}"
elif [ "$VM_STATUS" = "NOT_FOUND" ]; then
    echo -e "${RED}VM을 찾을 수 없음${NC}"
else
    echo -e "${YELLOW}$VM_STATUS${NC}"
fi

# 최근 로그 확인
if [ "$VM_STATUS" = "RUNNING" ]; then
    echo -e "\n${BLUE}최근 애플리케이션 로그:${NC}"
    gcloud compute ssh "$VM_NAME" --zone="$VM_ZONE" --command="sudo docker logs --tail 5 xai-backend" 2>/dev/null || echo "로그를 가져올 수 없습니다"
fi

echo -e "\n${BLUE}=== 헬스체크 완료 ===${NC}"