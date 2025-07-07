# GCP VM 배포 가이드

## 개요

이 가이드는 Google Cloud Platform의 Compute Engine VM에 Xai Community 백엔드를 배포하는 방법을 설명합니다.

## 배포 방법

### 1. 사전 준비사항

#### Google Cloud SDK 설치
```bash
# Google Cloud SDK 설치 (Ubuntu/Debian)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 인증
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 환경변수 설정
`.env.prod` 파일에 다음 변수들이 설정되어 있는지 확인:
```bash
# 필수 환경변수
PROJECT_ID=your-project-id
MONGODB_URL=mongodb+srv://...
SECRET_KEY=your-secret-key
DATABASE_NAME=xai_community

# VM 설정 (선택사항)
VM_NAME=xai-community-vm
VM_ZONE=asia-northeast3-a
VM_MACHINE_TYPE=e2-micro
VM_DISK_SIZE=20GB
```

### 2. 자동 배포 (추천)

```bash
# 백엔드 디렉토리로 이동
cd backend

# 배포 스크립트 실행
./deploy-vm.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
- VM 인스턴스 생성
- 방화벽 규칙 설정
- Docker 설치 및 설정
- 애플리케이션 배포
- 상태 확인

### 3. 수동 배포

#### 3.1 VM 인스턴스 생성

```bash
# VM 인스턴스 생성
gcloud compute instances create xai-community-vm \
    --zone=asia-northeast3-a \
    --machine-type=e2-micro \
    --image=ubuntu-2204-jammy-v20240927 \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=http-server,https-server
```

#### 3.2 방화벽 규칙 설정

```bash
# 백엔드 포트 허용
gcloud compute firewall-rules create allow-backend-port \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server
```

#### 3.3 VM 접속 및 설정

```bash
# VM에 SSH 접속
gcloud compute ssh xai-community-vm --zone=asia-northeast3-a

# VM 내부에서 실행
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### 3.4 소스 코드 전송

```bash
# 로컬에서 실행
gcloud compute scp --recurse . xai-community-vm:/home/$USER/app/ --zone=asia-northeast3-a
```

#### 3.5 애플리케이션 배포

```bash
# VM에서 실행
cd /home/$USER/app
sudo docker build -t xai-backend:latest .
sudo docker run -d \
    --name xai-backend \
    --restart unless-stopped \
    -p 8080:8080 \
    -e MONGODB_URL="your-mongodb-url" \
    -e SECRET_KEY="your-secret-key" \
    -e DATABASE_NAME="xai_community" \
    -e ENVIRONMENT="production" \
    xai-backend:latest
```

## 배포 옵션

### 옵션 1: 기본 Docker 배포

가장 간단한 배포 방법입니다.

```bash
# 컨테이너 실행
docker run -d \
    --name xai-backend \
    --restart unless-stopped \
    -p 8080:8080 \
    --env-file .env.prod \
    -v $(pwd)/uploads:/app/uploads \
    xai-backend:latest
```

### 옵션 2: Docker Compose 배포

더 복잡한 설정과 관리 기능을 원할 때 사용합니다.

```bash
# Docker Compose로 실행
docker-compose -f docker-compose.vm.yml up -d
```

### 옵션 3: Nginx 리버스 프록시 포함

SSL 종단점과 로드 밸런싱이 필요한 경우:

```bash
# Nginx 프로필 포함하여 실행
docker-compose -f docker-compose.vm.yml --profile nginx up -d
```

## 관리 명령어

### 애플리케이션 관리

```bash
# 상태 확인
docker ps
docker logs xai-backend

# 재시작
docker restart xai-backend

# 중지/시작
docker stop xai-backend
docker start xai-backend

# 업데이트 배포
docker stop xai-backend
docker rm xai-backend
docker build -t xai-backend:latest .
docker run -d --name xai-backend --restart unless-stopped -p 8080:8080 --env-file .env.prod xai-backend:latest
```

### VM 관리

```bash
# VM 상태 확인
gcloud compute instances describe xai-community-vm --zone=asia-northeast3-a

# VM 중지/시작
gcloud compute instances stop xai-community-vm --zone=asia-northeast3-a
gcloud compute instances start xai-community-vm --zone=asia-northeast3-a

# VM 삭제
gcloud compute instances delete xai-community-vm --zone=asia-northeast3-a
```

## 모니터링

### 로그 확인

```bash
# 애플리케이션 로그
docker logs xai-backend -f

# 시스템 로그
sudo journalctl -u docker -f
```

### 리소스 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats xai-backend

# 시스템 리소스
htop
df -h
free -h
```

## 성능 최적화

### VM 인스턴스 크기 조정

```bash
# 더 큰 인스턴스 타입으로 변경
gcloud compute instances stop xai-community-vm --zone=asia-northeast3-a
gcloud compute instances set-machine-type xai-community-vm \
    --machine-type=e2-small \
    --zone=asia-northeast3-a
gcloud compute instances start xai-community-vm --zone=asia-northeast3-a
```

### Docker 최적화

```bash
# 불필요한 이미지 정리
docker system prune -a

# 로그 로테이션 설정
sudo tee /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
sudo systemctl restart docker
```

## 트러블슈팅

### 일반적인 문제

#### 1. 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker logs xai-backend

# 환경변수 확인
docker exec xai-backend env | grep -E "(MONGODB_URL|SECRET_KEY)"
```

#### 2. 외부에서 접근되지 않는 경우
```bash
# 방화벽 상태 확인
gcloud compute firewall-rules list

# 포트 바인딩 확인
docker port xai-backend
```

#### 3. 메모리 부족 문제
```bash
# 메모리 사용량 확인
free -h
docker stats

# 스왑 설정
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 디버깅 명령어

```bash
# 컨테이너 내부 접속
docker exec -it xai-backend /bin/bash

# 네트워크 연결 확인
curl -f http://localhost:8080/

# 데이터베이스 연결 확인
docker exec xai-backend python -c "from nadle_backend.database.connection import get_database; print('DB connection:', get_database())"
```

## 보안 고려사항

### 방화벽 설정

```bash
# 특정 IP만 허용
gcloud compute firewall-rules create allow-backend-restricted \
    --allow tcp:8080 \
    --source-ranges YOUR_IP_RANGE \
    --target-tags http-server

# 기본 규칙 삭제
gcloud compute firewall-rules delete allow-backend-port
```

### SSL 인증서 설정

```bash
# Let's Encrypt 인증서 발급
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d your-domain.com

# Nginx 설정 업데이트
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /app/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /app/ssl/key.pem
```

## 백업 및 복원

### 데이터 백업

```bash
# 업로드 파일 백업
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz /app/uploads

# 데이터베이스 백업 (MongoDB Atlas 웹 콘솔 사용)
```

### 자동 백업 스크립트

```bash
#!/bin/bash
# /app/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /app/backups/uploads-$DATE.tar.gz /app/uploads
find /app/backups -name "uploads-*.tar.gz" -mtime +7 -delete
```

## 비용 최적화

### 인스턴스 스케줄링

```bash
# 야간 자동 중지 스케줄
gcloud compute instances add-metadata xai-community-vm \
    --metadata shutdown-script='docker stop xai-backend' \
    --zone=asia-northeast3-a
```

### 프리미엄 기능 비활성화

```bash
# 외부 IP 비활성화 (NAT 게이트웨이 사용)
gcloud compute instances delete-access-config xai-community-vm \
    --access-config-name="External NAT" \
    --zone=asia-northeast3-a
```

## 자주 묻는 질문

### Q: VM 크기를 어떻게 선택해야 하나요?
A: 
- 개발/테스트: e2-micro (1 vCPU, 1GB RAM)
- 소규모 운영: e2-small (2 vCPU, 2GB RAM)
- 중규모 운영: e2-medium (2 vCPU, 4GB RAM)

### Q: 데이터베이스를 VM에 함께 설치할 수 있나요?
A: 가능하지만 권장하지 않습니다. MongoDB Atlas와 같은 관리형 서비스를 사용하는 것이 좋습니다.

### Q: 무중단 배포는 어떻게 구현하나요?
A: 로드 밸런서 뒤에 여러 VM을 배치하고 순차적으로 업데이트하는 방식을 사용합니다.

## 추가 리소스

- [Google Cloud 공식 문서](https://cloud.google.com/compute/docs)
- [Docker 공식 문서](https://docs.docker.com)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [프로젝트 GitHub](https://github.com/your-repo)

---

이 가이드에 대한 피드백이나 질문이 있으시면 이슈를 등록해 주세요.