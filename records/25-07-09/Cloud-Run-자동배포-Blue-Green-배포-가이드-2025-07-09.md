# Cloud Run 자동 배포 & Blue/Green 배포 완전 가이드 (2025-07-09)

## 질문 1: CI/CD 파일 복구 및 Cloud Run 자동 배포 방법

### 태수의 질문
> 태수야! CI/CD 파일 원래대로 복구했어. 이제 Cloud Run 자동 배포 방법을 안내해줄게.

### Claude의 답변

🚀 **GitHub Actions로 Cloud Run 자동 배포 구성 방법**

#### 1. Google Cloud 사전 설정

**1.1 Service Account 생성**
```bash
# Google Cloud Console에서 진행
1. IAM & Admin → Service Accounts
2. "Create Service Account" 클릭
3. 이름: "github-actions-deploy"
4. 다음 권한 부여:
   - Cloud Run Admin
   - Cloud Build Editor
   - Artifact Registry Administrator
   - Storage Admin
   - Service Account User
```

**1.2 Service Account 키 생성**
```bash
# JSON 키 다운로드
- Service Account → Keys → Add Key → Create New Key → JSON
- 다운로드한 JSON 파일 내용을 복사
```

**1.3 Cloud Run 서비스 미리 생성**
```bash
# 스테이징 서비스
gcloud run deploy xai-community-backend-staging \
  --image gcr.io/PROJECT_ID/xai-community-backend-staging \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated

# 프로덕션 서비스  
gcloud run deploy xai-community-backend \
  --image gcr.io/PROJECT_ID/xai-community-backend \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

#### 2. GitHub Repository Secrets 설정

GitHub Repository → Settings → Secrets and variables → Actions에서 추가:
- **GCP_PROJECT_ID**: "your-gcp-project-id"
- **GCP_SA_KEY**: "{ service-account-json-key-content }"
- **GCP_REGION**: "asia-northeast3"

#### 3. CI/CD 파이프라인 Job 추가

**3.1 스테이징 배포 Job (develop 브랜치)**
```yaml
# 스테이징 자동 배포 (develop 브랜치)
staging-deploy:
  needs: [backend-safe-checks, frontend-safe-checks]
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/develop' && github.event_name == 'push'

  steps:
  - name: 📥 Checkout code
    uses: actions/checkout@v4

  - name: 🔐 Authenticate to Google Cloud
    uses: google-github-actions/auth@v1
    with:
      credentials_json: ${{ secrets.GCP_SA_KEY }}

  - name: 🔧 Set up Cloud SDK
    uses: google-github-actions/setup-gcloud@v1
    with:
      project_id: ${{ secrets.GCP_PROJECT_ID }}

  - name: 🐳 Configure Docker for GCR
    run: gcloud auth configure-docker

  - name: 🏗️ Build and push Docker image
    run: |
      cd backend
      docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend-staging:${{ github.sha }} .
      docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend-staging:${{ github.sha }}

  - name: 🚀 Deploy to Cloud Run (Staging)
    run: |
      gcloud run deploy xai-community-backend-staging \
        --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend-staging:${{ github.sha }} \
        --platform managed \
        --region ${{ secrets.GCP_REGION }} \
        --allow-unauthenticated \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 10 \
        --set-env-vars ENVIRONMENT=staging
```

**3.2 프로덕션 배포 Job (main 브랜치)**
```yaml
# 프로덕션 자동 배포 (main 브랜치)
production-deploy:
  needs: [backend-safe-checks, frontend-safe-checks]
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'

  steps:
  - name: 📥 Checkout code
    uses: actions/checkout@v4

  - name: 🔐 Authenticate to Google Cloud
    uses: google-github-actions/auth@v1
    with:
      credentials_json: ${{ secrets.GCP_SA_KEY }}

  - name: 🔧 Set up Cloud SDK
    uses: google-github-actions/setup-gcloud@v1
    with:
      project_id: ${{ secrets.GCP_PROJECT_ID }}

  - name: 🐳 Configure Docker for GCR
    run: gcloud auth configure-docker

  - name: 🏗️ Build and push Docker image
    run: |
      cd backend
      docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }} .
      docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }}

  - name: 🚀 Deploy to Cloud Run (Production)
    run: |
      gcloud run deploy xai-community-backend \
        --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }} \
        --platform managed \
        --region ${{ secrets.GCP_REGION }} \
        --allow-unauthenticated \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --min-instances 1 \
        --max-instances 100 \
        --set-env-vars ENVIRONMENT=production
```

#### 4. 배포 후 검증 단계

```yaml
- name: 🔍 Verify deployment
  run: |
    sleep 30  # 배포 완료 대기

    # 헬스체크 확인
    HEALTH_URL="https://xai-community-backend-staging-798170408536.asia-northeast3.run.app/health"
    if curl -f -m 30 "$HEALTH_URL"; then
      echo "✅ 배포 성공 및 헬스체크 통과"
    else
      echo "❌ 배포 실패 또는 헬스체크 실패"
      exit 1
    fi
```

#### 5. 환경별 환경변수 설정

```bash
# 스테이징 환경 변수
gcloud run services update xai-community-backend-staging \
  --set-env-vars ENVIRONMENT=staging,DATABASE_URL=staging-db-url,CORS_ORIGINS=https://xai-community-staging.vercel.app \
  --region asia-northeast3

# 프로덕션 환경 변수
gcloud run services update xai-community-backend \
  --set-env-vars ENVIRONMENT=production,DATABASE_URL=prod-db-url,CORS_ORIGINS=https://xai-community.vercel.app \
  --region asia-northeast3
```

#### 6. 완성된 워크플로우 동작

1. **develop 브랜치 푸시** → 스테이징 환경 자동 배포
2. **main 브랜치 푸시** → 프로덕션 환경 자동 배포
3. **테스트 통과** → 자동 배포 진행
4. **배포 후 검증** → 헬스체크 및 상태 확인

---

## 질문 2: Blue/Green 배포 구현 방법

### 태수의 질문
> production 자동 배포에서 cloud run의 blue/green 배포 반영하려면 어떻게 해야 해?

### Claude의 답변

🔄 **Cloud Run Blue/Green 배포 구현 방법**

#### 1. Cloud Run Blue/Green 배포 전략

**1.1 기본 개념**
- **Blue (현재 버전)**: 기존 운영 중인 revision
- **Green (새 버전)**: 새로 배포하는 revision
- **트래픽 분산**: 0% → 100% 점진적 전환

#### 2. Blue/Green 배포 워크플로우

**2.1 Production Blue/Green 배포 Job**
```yaml
# 프로덕션 Blue/Green 배포 (main 브랜치)
production-blue-green-deploy:
  needs: [backend-safe-checks, frontend-safe-checks]
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'

  steps:
  - name: 📥 Checkout code
    uses: actions/checkout@v4

  - name: 🔐 Authenticate to Google Cloud
    uses: google-github-actions/auth@v1
    with:
      credentials_json: ${{ secrets.GCP_SA_KEY }}

  - name: 🔧 Set up Cloud SDK
    uses: google-github-actions/setup-gcloud@v1
    with:
      project_id: ${{ secrets.GCP_PROJECT_ID }}

  - name: 🐳 Configure Docker for GCR
    run: gcloud auth configure-docker

  - name: 🏗️ Build and push Docker image
    run: |
      cd backend
      docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }} .
      docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }}

  # 🔵 Step 1: Deploy Green version with 0% traffic
  - name: 🟢 Deploy Green version (0% traffic)
    run: |
      gcloud run deploy xai-community-backend \
        --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }} \
        --platform managed \
        --region ${{ secrets.GCP_REGION }} \
        --allow-unauthenticated \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --min-instances 1 \
        --max-instances 100 \
        --set-env-vars ENVIRONMENT=production \
        --no-traffic \
        --tag green-${{ github.sha }}
        
  # 🔍 Step 2: Health check on Green version
  - name: 🔍 Health check Green version
    run: |
      # Green version의 직접 URL로 헬스체크
      GREEN_URL="https://green-${{ github.sha }}---xai-community-backend-798170408536.asia-northeast3.run.app"

      echo "🔍 Green version 헬스체크 시작: $GREEN_URL"

      # 최대 5분 대기하며 헬스체크
      for i in {1..10}; do
        echo "시도 $i/10..."
        if curl -f -m 30 "$GREEN_URL/health"; then
          echo "✅ Green version 헬스체크 성공"
          break
        else
          echo "⚠️ Green version 헬스체크 실패, 30초 후 재시도..."
          sleep 30
        fi

        if [ $i -eq 10 ]; then
          echo "❌ Green version 헬스체크 최종 실패"
          exit 1
        fi
      done

  # 🔄 Step 3: Gradual traffic shift (Blue → Green)
  - name: 🔄 Gradual traffic shift to Green
    run: |
      echo "🔄 점진적 트래픽 이동 시작"

      # 10% 트래픽을 Green으로 이동
      echo "📊 10% 트래픽 → Green"
      gcloud run services update-traffic xai-community-backend \
        --to-tags green-${{ github.sha }}=10 \
        --region ${{ secrets.GCP_REGION }}

      # 2분 대기 후 모니터링
      echo "⏳ 2분 대기 중..."
      sleep 120

      # Green version 모니터링
      GREEN_URL="https://green-${{ github.sha }}---xai-community-backend-798170408536.asia-northeast3.run.app"
      if curl -f -m 30 "$GREEN_URL/health"; then
        echo "✅ Green version 10% 트래픽 처리 정상"
      else
        echo "❌ Green version 10% 트래픽 처리 실패"
        # 롤백 실행
        gcloud run services update-traffic xai-community-backend \
          --to-latest \
          --region ${{ secrets.GCP_REGION }}
        exit 1
      fi

      # 50% 트래픽을 Green으로 이동
      echo "📊 50% 트래픽 → Green"
      gcloud run services update-traffic xai-community-backend \
        --to-tags green-${{ github.sha }}=50 \
        --region ${{ secrets.GCP_REGION }}

      # 2분 대기 후 모니터링
      echo "⏳ 2분 대기 중..."
      sleep 120

      # Green version 모니터링
      if curl -f -m 30 "$GREEN_URL/health"; then
        echo "✅ Green version 50% 트래픽 처리 정상"
      else
        echo "❌ Green version 50% 트래픽 처리 실패"
        # 롤백 실행
        gcloud run services update-traffic xai-community-backend \
          --to-latest \
          --region ${{ secrets.GCP_REGION }}
        exit 1
      fi

      # 100% 트래픽을 Green으로 이동
      echo "📊 100% 트래픽 → Green"
      gcloud run services update-traffic xai-community-backend \
        --to-tags green-${{ github.sha }}=100 \
        --region ${{ secrets.GCP_REGION }}

  # ✅ Step 4: Final verification
  - name: ✅ Final verification
    run: |
      echo "🔍 최종 검증 시작"

      # 메인 URL로 최종 헬스체크
      MAIN_URL="https://xai-community-backend-798170408536.asia-northeast3.run.app"

      for i in {1..5}; do
        echo "최종 검증 시도 $i/5..."
        if curl -f -m 30 "$MAIN_URL/health"; then
          echo "✅ Blue/Green 배포 완료 - 모든 트래픽이 Green version으로 이동"
          break
        else
          echo "⚠️ 최종 검증 실패, 30초 후 재시도..."
          sleep 30
        fi

        if [ $i -eq 5 ]; then
          echo "❌ 최종 검증 실패 - 롤백 필요"
          exit 1
        fi
      done

  # 🧹 Step 5: Cleanup old revisions (optional)
  - name: 🧹 Cleanup old revisions
    run: |
      echo "🧹 이전 revision 정리"

      # 현재 활성 revision 제외하고 이전 것들 삭제 (최근 3개 유지)
      gcloud run revisions list \
        --service xai-community-backend \
        --region ${{ secrets.GCP_REGION }} \
        --format="value(metadata.name)" \
        --sort-by="~metadata.creationTimestamp" \
        --limit=100 | tail -n +4 | while read revision; do
        echo "삭제할 revision: $revision"
        gcloud run revisions delete $revision \
          --region ${{ secrets.GCP_REGION }} \
          --quiet || true
      done
```

#### 3. 고급 Blue/Green 배포 전략

**3.1 자동 롤백 기능**
```yaml
# 자동 롤백 Job
production-rollback:
  runs-on: ubuntu-latest
  if: failure() && github.ref == 'refs/heads/main'
  needs: [production-blue-green-deploy]

  steps:
  - name: 🔄 Automatic rollback
    run: |
      echo "🚨 배포 실패 감지 - 자동 롤백 시작"

      # 이전 stable revision으로 롤백
      gcloud run services update-traffic xai-community-backend \
        --to-latest \
        --region ${{ secrets.GCP_REGION }}

      echo "✅ 자동 롤백 완료"
```

**3.2 Canary 배포 변형**
```yaml
# Canary 배포 (더 세밀한 트래픽 제어)
- name: 🐤 Canary deployment
  run: |
    # 1% → 5% → 10% → 25% → 50% → 100% 순차적 배포
    for traffic in 1 5 10 25 50 100; do
      echo "📊 ${traffic}% 트래픽 → Green"
      
      gcloud run services update-traffic xai-community-backend \
        --to-tags green-${{ github.sha }}=${traffic} \
        --region ${{ secrets.GCP_REGION }}
      
      # 각 단계별 검증
      sleep 60
      if ! curl -f -m 30 "$GREEN_URL/health"; then
        echo "❌ ${traffic}% 단계에서 실패 - 롤백"
        gcloud run services update-traffic xai-community-backend \
          --to-latest \
          --region ${{ secrets.GCP_REGION }}
        exit 1
      fi
      
      echo "✅ ${traffic}% 단계 성공"
    done
```

#### 4. 모니터링 및 알림

```yaml
# 배포 상태 모니터링
- name: 📊 Deployment monitoring
  run: |
    # Cloud Run 서비스 상태 확인
    gcloud run services describe xai-community-backend \
      --region ${{ secrets.GCP_REGION }} \
      --format="table(status.conditions[0].type:label=STATUS,
                     status.conditions[0].status:label=READY,
                     spec.template.spec.containers[0].image:label=IMAGE)"

    # 트래픽 분산 현황 확인
    gcloud run services describe xai-community-backend \
      --region ${{ secrets.GCP_REGION }} \
      --format="table(status.traffic[].revisionName:label=REVISION,
                     status.traffic[].percent:label=TRAFFIC_PERCENT,
                     status.traffic[].tag:label=TAG)"
```

#### 5. 수동 제어 명령어

```bash
# 수동 트래픽 제어
# 특정 revision으로 트래픽 이동
gcloud run services update-traffic xai-community-backend \
  --to-revisions xai-community-backend-00001-abc=100 \
  --region asia-northeast3

# 태그 기반 트래픽 제어
gcloud run services update-traffic xai-community-backend \
  --to-tags green-abc123=50,blue-def456=50 \
  --region asia-northeast3

# 즉시 이전 버전으로 롤백
gcloud run services update-traffic xai-community-backend \
  --to-latest \
  --region asia-northeast3
```

🎯 **Blue/Green 배포 장점**
1. **무중단 배포**: 트래픽 점진적 이동으로 다운타임 제로
2. **빠른 롤백**: 문제 발생시 즉시 이전 버전으로 복구
3. **안전한 검증**: 실제 트래픽 이전에 Green version 검증
4. **트래픽 제어**: 세밀한 트래픽 분산 제어

---

## 질문 3: Cloud Run URL 구조 및 트래픽 분산 원리

### 태수의 질문
> MAIN_URL="https://xai-community-backend-798170408536.asia-northeast3.run.app" 는 트래픽 점차적으로 이동 후에도 문제없이 동작하는 green 버전의 cloud run 배포 url이야? 이 url을 어떻게 알 수 있어? 현재 MAIN_URL에 입력한 값은 임의로 넣은 거 아냐? 현재 활성 revision 은 롤백에 사용하기 위한 용도야?

### Claude의 답변

🔍 **Cloud Run URL 구조 및 동작 원리**

#### 1. Cloud Run URL 종류

**1.1 Main Service URL (고정)**
```
https://xai-community-backend-798170408536.asia-northeast3.run.app
```
- 항상 동일한 URL
- 트래픽 분산 설정에 따라 자동으로 적절한 revision으로 라우팅
- 100% Green으로 이동 완료 후에는 Green revision으로 연결

**1.2 Tagged URL (Green 버전 직접 접근)**
```
https://green-{commit-hash}---xai-community-backend-798170408536.asia-northeast3.run.app
```
- Green 버전에만 직접 접근
- 트래픽 분산과 무관하게 특정 revision에 바로 연결
- 헬스체크 및 테스트용

#### 2. URL 동적 생성 방법

```yaml
# 올바른 URL 생성 방법
- name: 🔍 Get service URLs
  run: |
    # Main service URL 가져오기
    MAIN_URL=$(gcloud run services describe xai-community-backend \
      --region ${{ secrets.GCP_REGION }} \
      --format="value(status.url)")

    # Green tagged URL 생성
    GREEN_URL="https://green-${{ github.sha }}---xai-community-backend-798170408536.asia-northeast3.run.app"

    echo "📍 Main URL: $MAIN_URL"
    echo "🟢 Green URL: $GREEN_URL"

    # 환경변수로 저장
    echo "MAIN_URL=$MAIN_URL" >> $GITHUB_ENV
    echo "GREEN_URL=$GREEN_URL" >> $GITHUB_ENV
```

#### 3. 트래픽 분산 동작 원리

**3.1 트래픽 분산 과정**
```bash
# 초기 상태 (Blue 100%)
MAIN_URL → Blue revision (100%)

# Green 배포 후 (Green 0%)
MAIN_URL → Blue revision (100%)
GREEN_URL → Green revision (직접 접근)

# 트래픽 10% 이동
MAIN_URL → Blue revision (90%) + Green revision (10%)
GREEN_URL → Green revision (직접 접근)

# 트래픽 100% 이동 완료
MAIN_URL → Green revision (100%)
GREEN_URL → Green revision (직접 접근)
```

**3.2 실제 동작 확인**
```yaml
- name: 🔍 Traffic distribution verification
  run: |
    # 현재 트래픽 분산 상태 확인
    gcloud run services describe xai-community-backend \
      --region ${{ secrets.GCP_REGION }} \
      --format="table(status.traffic[].revisionName:label=REVISION,
                     status.traffic[].percent:label=TRAFFIC_PERCENT,
                     status.traffic[].tag:label=TAG,
                     status.traffic[].url:label=URL)"

    # Main URL이 어떤 revision들로 분산되는지 확인
    echo "📊 Main URL 트래픽 분산:"
    for i in {1..10}; do
      curl -s $MAIN_URL/health | grep -o '"revision":"[^"]*"' || echo "Health check $i"
      sleep 1
    done
```

#### 4. Revision 관리 전략

**4.1 Revision의 역할**
```yaml
# 현재 활성 revision 확인
- name: 📋 Get current active revision
  run: |
    # 현재 100% 트래픽을 받는 revision (Blue)
    CURRENT_REVISION=$(gcloud run services describe xai-community-backend \
      --region ${{ secrets.GCP_REGION }} \
      --format="value(status.traffic[0].revisionName)")

    echo "🔵 Current active revision (Blue): $CURRENT_REVISION"
    echo "BLUE_REVISION=$CURRENT_REVISION" >> $GITHUB_ENV

    # 롤백용으로 저장
    echo "ROLLBACK_REVISION=$CURRENT_REVISION" >> $GITHUB_ENV
```

**4.2 롤백 메커니즘**
```yaml
# 롤백 실행
- name: 🔄 Rollback to previous revision
  if: failure()
  run: |
    echo "🚨 배포 실패 - 롤백 실행"
    echo "🔄 롤백 대상: $ROLLBACK_REVISION"

    # 이전 revision으로 트래픽 100% 이동
    gcloud run services update-traffic xai-community-backend \
      --to-revisions $ROLLBACK_REVISION=100 \
      --region ${{ secrets.GCP_REGION }}

    echo "✅ 롤백 완료"
```

#### 5. 수정된 올바른 워크플로우

```yaml
# 수정된 올바른 Blue/Green 배포 워크플로우
production-blue-green-deploy:
  needs: [backend-safe-checks, frontend-safe-checks]
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'

  steps:
  - name: 📥 Checkout code
    uses: actions/checkout@v4

  - name: 🔐 Authenticate to Google Cloud
    uses: google-github-actions/auth@v1
    with:
      credentials_json: ${{ secrets.GCP_SA_KEY }}

  - name: 🔧 Set up Cloud SDK
    uses: google-github-actions/setup-gcloud@v1
    with:
      project_id: ${{ secrets.GCP_PROJECT_ID }}

  # 현재 상태 확인 및 URL 설정
  - name: 📋 Get current state and URLs
    run: |
      # Main service URL 가져오기
      MAIN_URL=$(gcloud run services describe xai-community-backend \
        --region ${{ secrets.GCP_REGION }} \
        --format="value(status.url)")

      # 현재 활성 revision (Blue) 가져오기
      CURRENT_REVISION=$(gcloud run services describe xai-community-backend \
        --region ${{ secrets.GCP_REGION }} \
        --format="value(status.traffic[0].revisionName)")

      # Green tagged URL 생성
      GREEN_URL="https://green-${{ github.sha }}---xai-community-backend-798170408536.asia-northeast3.run.app"

      echo "📍 Main URL: $MAIN_URL"
      echo "🔵 Current revision (Blue): $CURRENT_REVISION"
      echo "🟢 Green URL: $GREEN_URL"

      # 환경변수로 저장
      echo "MAIN_URL=$MAIN_URL" >> $GITHUB_ENV
      echo "BLUE_REVISION=$CURRENT_REVISION" >> $GITHUB_ENV
      echo "GREEN_URL=$GREEN_URL" >> $GITHUB_ENV

  - name: 🐳 Configure Docker for GCR
    run: gcloud auth configure-docker

  - name: 🏗️ Build and push Docker image
    run: |
      cd backend
      docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }} .
      docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }}

  # Green version 배포 (0% 트래픽)
  - name: 🟢 Deploy Green version (0% traffic)
    run: |
      gcloud run deploy xai-community-backend \
        --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/xai-community-backend:${{ github.sha }} \
        --platform managed \
        --region ${{ secrets.GCP_REGION }} \
        --allow-unauthenticated \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --min-instances 1 \
        --max-instances 100 \
        --set-env-vars ENVIRONMENT=production \
        --no-traffic \
        --tag green-${{ github.sha }}
        
  # Green version 직접 헬스체크
  - name: 🔍 Health check Green version
    run: |
      echo "🔍 Green version 헬스체크: $GREEN_URL"

      for i in {1..10}; do
        echo "시도 $i/10..."
        if curl -f -m 30 "$GREEN_URL/health"; then
          echo "✅ Green version 헬스체크 성공"
          break
        else
          echo "⚠️ Green version 헬스체크 실패, 30초 후 재시도..."
          sleep 30
        fi

        if [ $i -eq 10 ]; then
          echo "❌ Green version 헬스체크 최종 실패"
          exit 1
        fi
      done

  # 점진적 트래픽 이동
  - name: 🔄 Gradual traffic shift
    run: |
      # 10% 트래픽 이동
      echo "📊 10% 트래픽 → Green"
      gcloud run services update-traffic xai-community-backend \
        --to-tags green-${{ github.sha }}=10 \
        --region ${{ secrets.GCP_REGION }}

      sleep 120

      # Main URL 헬스체크 (10% Green 트래픽 포함)
      if curl -f -m 30 "$MAIN_URL/health"; then
        echo "✅ 10% 트래픽 이동 성공"
      else
        echo "❌ 10% 트래픽 이동 실패 - 롤백"
        gcloud run services update-traffic xai-community-backend \
          --to-revisions $BLUE_REVISION=100 \
          --region ${{ secrets.GCP_REGION }}
        exit 1
      fi

      # 100% 트래픽 이동
      echo "📊 100% 트래픽 → Green"
      gcloud run services update-traffic xai-community-backend \
        --to-tags green-${{ github.sha }}=100 \
        --region ${{ secrets.GCP_REGION }}

  # 최종 검증
  - name: ✅ Final verification
    run: |
      echo "🔍 최종 검증 - Main URL이 Green version으로 완전 이동"

      for i in {1..5}; do
        echo "최종 검증 시도 $i/5..."
        if curl -f -m 30 "$MAIN_URL/health"; then
          echo "✅ Blue/Green 배포 완료"
          echo "📍 Main URL: $MAIN_URL"
          echo "🟢 이제 Main URL이 Green version으로 연결됨"
          break
        else
          echo "⚠️ 최종 검증 실패, 30초 후 재시도..."
          sleep 30
        fi

        if [ $i -eq 5 ]; then
          echo "❌ 최종 검증 실패 - 롤백"
          gcloud run services update-traffic xai-community-backend \
            --to-revisions $BLUE_REVISION=100 \
            --region ${{ secrets.GCP_REGION }}
          exit 1
        fi
      done
```

🎯 **정리**

1. **Main URL**: 트래픽 분산 설정에 따라 자동 라우팅, 최종적으로 Green version으로 연결
2. **Green URL**: Green version에 직접 접근하여 헬스체크 및 테스트
3. **Blue Revision**: 롤백용으로 저장된 이전 stable revision
4. **URL 동적 생성**: gcloud 명령어로 실제 URL 조회

이제 정확한 구조로 Blue/Green 배포가 가능합니다!

---

## 주요 특징 및 장점

### 자동 배포 시스템
- **Branch-based 배포**: develop → 스테이징, main → 프로덕션
- **자동 검증**: 테스트 통과 후 배포 진행
- **환경 분리**: 각 환경별 독립적인 설정

### Blue/Green 배포 전략
- **무중단 배포**: 트래픽 점진적 이동으로 다운타임 제로
- **안전한 검증**: Green version 헬스체크 후 트래픽 이동
- **빠른 롤백**: 문제 발생시 즉시 이전 버전으로 복구
- **세밀한 제어**: 10% → 50% → 100% 단계별 트래픽 이동

### 모니터링 및 관리
- **실시간 모니터링**: 각 단계별 헬스체크 및 상태 확인
- **자동 롤백**: 실패 감지시 자동으로 이전 버전으로 복구
- **Revision 관리**: 이전 버전 추적 및 정리

이 가이드를 통해 안전하고 신뢰할 수 있는 Cloud Run 자동 배포 시스템을 구축할 수 있습니다.