# Render에서 GCloud VM으로 백엔드 마이그레이션 완전 기록

**작업 일시**: 2025년 7월 7일  
**작업자**: nadle  
**작업 목표**: Render 환경에서 Google Cloud VM으로 백엔드 애플리케이션 마이그레이션  

## 📋 작업 개요

### 초기 상황
- **기존 환경**: Render 클라우드 플랫폼에서 백엔드 호스팅
- **목표 환경**: Google Cloud Platform의 Compute Engine VM
- **마이그레이션 이유**: 비용 최적화 및 더 나은 제어권 확보

### 사전 준비 상태
- ✅ 완전한 VM 배포 스크립트 세트 (`deploy-vm.sh`, `setup-vm.sh`, `monitor-vm.sh` 등)
- ✅ `.env.prod` 운영 환경 설정 파일
- ✅ Docker 기반 애플리케이션 컨테이너화
- ✅ MongoDB Atlas 클라우드 데이터베이스 연결

## 🚀 작업 진행 과정

### 1단계: 환경 검증 및 준비 (16:13-16:16)

#### 수행 작업
```bash
# Google Cloud SDK 인증 상태 확인
gcloud auth list
gcloud config list

# 환경변수 검증
grep -E "(PROJECT_ID|SECRET_KEY|MONGODB_URL)" .env.prod
```

#### 결과
- ✅ Google Cloud SDK 정상 설치 및 인증 완료
- ✅ 프로젝트 `xai-community` 설정 확인
- ✅ 필수 환경변수 모두 설정 완료

### 2단계: 초기 VM 배포 시도 및 문제 발생 (16:16-16:18)

#### 수행 명령
```bash
chmod +x deploy-vm.sh
./deploy-vm.sh
```

#### 발생한 문제 #1: SCP 전송 실패
**에러 메시지**: 
```
scp: error: unexpected filename: .
ERROR: (gcloud.compute.scp) [/usr/bin/scp] exited with return code [1].
```

**원인 분석**:
1. `gcloud compute scp --recurse . "$VM_NAME:/app/"` 명령에서 현재 디렉토리(`.`) 경로 해석 문제
2. 대상 VM의 `/app/` 디렉토리가 존재하지 않음
3. 숨겨진 파일들(`.env.prod` 등) 전송 누락

### 3단계: SCP 문제 근본적 해결 (16:18-16:23)

#### 문제 해결 접근법
**임시방편 거부**: 압축 파일 생성 등의 우회 방법 대신 근본 원인 해결

#### 구체적 수정 사항

**수정 전 코드**:
```bash
# VM에 연결하여 애플리케이션 배포
log_info "VM에 소스 코드 전송 중..."
if ! gcloud compute scp --recurse . "$VM_NAME:/app/" --zone="$VM_ZONE" --quiet; then
    log_error "소스 코드 전송 실패!"
    exit 1
fi
```

**수정 후 코드**:
```bash
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
```

#### 해결 전략
1. **사전 디렉토리 생성**: VM에서 `/app` 디렉토리를 미리 생성하고 권한 설정
2. **명시적 파일 전송**: `.` 대신 `*`로 명시적 파일 리스트 전송
3. **숨겨진 파일 개별 처리**: `.env.prod` 등 중요한 숨겨진 파일들을 별도로 전송

### 4단계: VM 생성 및 초기 설정 완료 (16:23-16:29)

#### VM 생성 결과
```
VM 설정:
- 이름: xai-community-vm
- 존: asia-northeast3-a
- 머신 타입: e2-micro
- 외부 IP: 34.47.125.147
- 디스크 크기: 20GB
```

#### 시작 스크립트 실행 상태
- **상태**: `google-startup-scripts.service` 정상 실행
- **진행 과정**: Docker 설치, 시스템 업데이트, 환경 설정
- **소요 시간**: 약 5분

### 5단계: Docker 설치 대기 및 상태 확인 (16:29-16:30)

#### 발생한 문제 #2: Docker 명령어 실패
**에러 메시지**: 
```
sudo: docker: command not found
```

**원인**: VM 시작 스크립트가 아직 완료되지 않음

#### 상태 모니터링
```bash
# 시작 스크립트 상태 확인
gcloud compute ssh xai-community-vm --zone=asia-northeast3-a --command="sudo systemctl status google-startup-scripts"

# 진행 과정 확인
gcloud compute ssh xai-community-vm --zone=asia-northeast3-a --command="ps aux | grep startup"
```

#### 해결 과정
1. **정상 상황 확인**: 시작 스크립트가 정상적으로 실행 중임을 확인
2. **자동 완료 대기**: 약 2분 후 시작 스크립트 성공적으로 완료
3. **Docker 서비스 활성화**: `docker.service` 정상 실행 확인

### 6단계: Docker 이미지 빌드 및 실행 (16:30-16:40)

#### Docker 빌드 수행
```bash
# 백그라운드에서 빌드 실행 (리소스 제약으로 인한 긴 빌드 시간 대응)
cd /app && nohup sudo docker build -t xai-backend:latest . > build.log 2>&1 &
```

#### 빌드 결과
- **빌드 시간**: 약 7분 (e2-micro VM의 제한된 리소스로 인함)
- **이미지 크기**: 1.02GB
- **빌드 상태**: 성공

#### 컨테이너 실행
```bash
sudo docker run -d \
    --name xai-backend \
    --restart unless-stopped \
    -p 8080:8080 \
    [환경변수 설정] \
    xai-backend:latest
```

### 7단계: 환경변수 문제 해결 (16:40-16:43)

#### 발생한 문제 #3: 환경변수 누락
**에러 메시지**: 
```
ValueError: 프로덕션에서 ALLOWED_ORIGINS 환경변수가 필수입니다
```

**원인**: 컨테이너 실행 시 필수 환경변수가 전달되지 않음

#### 해결 방법
VM 메타데이터와 `.env.prod` 파일의 모든 환경변수를 포함하여 컨테이너 재시작:

```bash
# 완전한 환경변수 설정으로 컨테이너 재시작
sudo docker run -d \
    --name xai-backend \
    --restart unless-stopped \
    -p 8080:8080 \
    -e MONGODB_URL="$MONGODB_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    -e DATABASE_NAME="$DATABASE_NAME" \
    -e ENVIRONMENT=production \
    -e PORT=8080 \
    -e HOST=0.0.0.0 \
    -e LOG_LEVEL=INFO \
    -e MAX_COMMENT_DEPTH=3 \
    -e ENABLE_DOCS=false \
    -e ENABLE_CORS=true \
    -e ALLOWED_ORIGINS=https://xai-community.vercel.app \
    -e FRONTEND_URL=https://xai-community.vercel.app \
    -e USERS_COLLECTION=users \
    -e POSTS_COLLECTION=posts \
    -e COMMENTS_COLLECTION=comments \
    -e POST_STATS_COLLECTION=post_stats \
    -e USER_REACTIONS_COLLECTION=user_reactions \
    -e FILES_COLLECTION=files \
    -e STATS_COLLECTION=stats \
    xai-backend:latest
```

### 8단계: 최종 검증 및 완료 (16:43-16:45)

#### 애플리케이션 상태 확인
```bash
# 컨테이너 상태
sudo docker ps
# 로그 확인
sudo docker logs xai-backend --tail 5
# 외부 접근 테스트
curl -s "http://34.47.125.147:8080/"
```

#### 최종 결과
- ✅ **애플리케이션 정상 실행**: `{"message":"Content Management API","status":"running"}`
- ✅ **데이터베이스 연결 성공**: MongoDB Atlas 연결 확인
- ✅ **서버 응답 정상**: Uvicorn 서버 8080 포트에서 실행 중
- ⚠️ **Redis 경고**: 로컬 Redis 없음 (정상, 캐시 없이 동작)

## 🔧 기술적 세부사항

### 발생한 주요 문제와 해결책

#### 1. SCP 파일 전송 문제
**문제**: `gcloud compute scp --recurse . "$VM_NAME:/app/"` 실패
**근본 원인**: 
- 현재 디렉토리(`.`) 경로 해석 문제
- 대상 디렉토리 미존재
- 숨겨진 파일 전송 누락

**해결책**:
1. 사전 디렉토리 생성: `sudo mkdir -p /app && sudo chown -R $USER:$USER /app`
2. 명시적 파일 전송: `*` 패턴 사용
3. 숨겨진 파일 개별 전송: `.env.prod` 별도 전송

#### 2. VM 시작 스크립트 타이밍 문제
**문제**: Docker 명령어 실행 시점에 Docker 미설치
**근본 원인**: VM 시작 스크립트의 비동기적 실행

**해결책**:
1. 시작 스크립트 상태 모니터링
2. 자동 완료 대기 로직
3. Docker 서비스 상태 확인 후 진행

#### 3. 환경변수 설정 누락
**문제**: 컨테이너 실행 시 `ALLOWED_ORIGINS` 등 필수 환경변수 누락
**근본 원인**: 메타데이터 환경변수와 `.env.prod` 파일의 불완전한 통합

**해결책**:
1. 모든 필수 환경변수 명시적 전달
2. 메타데이터와 설정 파일 값 동기화
3. 환경변수 누락 시 명확한 에러 메시지 활용

### 성능 최적화 고려사항

#### e2-micro VM의 제약사항
- **메모리**: 1GB (Docker 빌드 시 제약)
- **CPU**: 1 vCPU (빌드 시간 약 7분)
- **네트워크**: 제한적 대역폭

#### 빌드 최적화 전략
1. **백그라운드 빌드**: `nohup` 사용으로 연결 끊김 방지
2. **빌드 로그 모니터링**: `build.log` 파일을 통한 진행 상황 추적
3. **단계별 확인**: 빌드 완료 후 이미지 확인

### 보안 설정

#### 방화벽 규칙
```bash
# 백엔드 포트 허용
gcloud compute firewall-rules create allow-backend-port \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server
```

#### 환경변수 보안
- VM 메타데이터를 통한 민감 정보 전달
- 컨테이너 런타임에만 환경변수 노출
- 로그에서 민감 정보 마스킹

## 📊 최종 배포 결과

### 배포 성공 지표
- **VM 상태**: RUNNING
- **애플리케이션 상태**: 정상 실행
- **API 응답**: 200 OK
- **데이터베이스 연결**: 성공
- **외부 접근**: 가능

### 접근 정보
- **애플리케이션 URL**: http://34.47.125.147:8080
- **VM SSH 접속**: `gcloud compute ssh xai-community-vm --zone=asia-northeast3-a`
- **Docker 로그**: `sudo docker logs xai-backend`

### 관리 도구
- **실시간 모니터링**: `./monitor-vm.sh`
- **헬스체크**: `./health-check.sh`
- **롤백**: `./rollback-vm.sh`

## 🎯 교훈 및 개선사항

### 성공 요인
1. **근본적 문제 해결**: 임시방편 대신 원인 분석 및 해결
2. **체계적 접근**: 단계별 검증 및 문제 격리
3. **완전한 자동화**: 사전 준비된 스크립트들의 효과적 활용

### 향후 개선사항
1. **빌드 최적화**: 멀티스테이지 Docker 빌드로 이미지 크기 최적화
2. **모니터링 강화**: Prometheus/Grafana 연동
3. **백업 자동화**: 정기적 데이터 백업 스케줄링
4. **로드밸런싱**: 트래픽 증가 대비 다중 인스턴스 구성

### 예상 비용 절감
- **Render 대비**: 월 $7-25 → GCP 무료 티어 활용
- **연간 절감액**: 약 $84-300

## 📝 체크리스트

### 마이그레이션 완료 확인
- [x] VM 생성 및 설정 완료
- [x] Docker 환경 구축 완료
- [x] 애플리케이션 빌드 및 배포 완료
- [x] 데이터베이스 연결 확인
- [x] 외부 접근 가능성 확인
- [x] 환경변수 설정 완료
- [x] 모니터링 도구 준비 완료

### 후속 작업 필요
- [ ] SSL/TLS 인증서 설정 (Let's Encrypt)
- [ ] 도메인 연결 및 DNS 설정
- [ ] 백업 스케줄 설정
- [ ] 로그 로테이션 설정
- [ ] 모니터링 알림 설정

## 🔗 관련 파일

### 수정된 파일
- `deploy-vm.sh`: SCP 문제 해결을 위한 파일 전송 로직 개선
- `.env.prod`: 운영 환경 설정 검증 완료

### 생성된 파일
- VM 내부: `build.log` (Docker 빌드 로그)
- VM 내부: `deploy-app-to-vm.sh` (애플리케이션 배포 스크립트)

### 활용 가능한 도구
- `monitor-vm.sh`: 실시간 VM 및 애플리케이션 모니터링
- `health-check.sh`: 정기적 헬스체크
- `rollback-vm.sh`: 문제 발생 시 롤백
- `setup-vm.sh`: VM 추가 설정

---

**작업 완료 시간**: 2025-07-07 16:45  
**총 소요 시간**: 약 32분  
**최종 상태**: ✅ 성공적 마이그레이션 완료