# 현업 수준 CI/CD 파이프라인 구축 가이드 (2025)

> 작성일: 2025-07-06  
> 대상: 초보자부터 중급자까지  
> 목표: 실험용 CI/CD를 현업 수준으로 개선

## 📋 목차
1. [현재 상태 분석](#현재-상태-분석)
2. [보안 강화](#보안-강화)
3. [품질 게이트 구현](#품질-게이트-구현)
4. [환경별 배포 전략](#환경별-배포-전략)
5. [모니터링 및 알림](#모니터링-및-알림)
6. [고급 기능](#고급-기능)
7. [실제 구현 예시](#실제-구현-예시)

---

## 현재 상태 분석

### 기존 파이프라인의 문제점
- ✅ 기본 테스트는 있지만 보안 검사 부족
- ✅ 단순한 배포 검증만 존재
- ❌ 코드 품질 관리 미흡
- ❌ 환경별 배포 전략 부재
- ❌ 모니터링 및 알림 시스템 없음

### 현업에서 요구하는 수준
- 🔒 **보안**: 자동 취약점 스캐닝, 의존성 관리
- 📊 **품질**: 코드 커버리지, 정적 분석, 품질 게이트
- 🚀 **배포**: 무중단 배포, 롤백 전략, 환경 분리
- 📢 **모니터링**: 실시간 알림, 성능 메트릭, 에러 추적

---

## 보안 강화

### 1. CodeQL 보안 분석 설정

**2025년 업데이트: CodeQL v2 deprecated → v3 사용 필수**

```yaml
# .github/workflows/security-scan.yml
name: 🔒 Security Scanning

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # 매주 월요일 새벽 2시

jobs:
  codeql-analysis:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'javascript', 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3  # v3 사용
      with:
        languages: ${{ matrix.language }}
        queries: security-extended,security-and-quality

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
```

### 2. Dependabot 자동 의존성 업데이트

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Python 백엔드 의존성
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    reviewers:
      - "nadle"
    assignees:
      - "nadle"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
    
  # Node.js 프론트엔드 의존성
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    reviewers:
      - "nadle"
    assignees:
      - "nadle"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
```

### 3. 시크릿 스캐닝 및 액션 버전 고정

```yaml
# 액션 버전 고정 예시
- name: Checkout
  uses: actions/checkout@v4.1.1  # 정확한 버전 명시

- name: Setup Node.js
  uses: actions/setup-node@v4.0.2  # SHA 사용 권장: @sha256:xxx
  with:
    node-version: '20'
```

**중요**: 프로덕션 환경에서는 SHA 해시를 사용하여 액션을 고정하세요.

---

## 품질 게이트 구현

### 1. SonarQube 연동 설정

```yaml
# .github/workflows/quality-gate.yml
name: 📊 Code Quality Gate

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  sonarqube-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # 전체 히스토리 필요

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies and run tests
      run: |
        cd backend
        pip install -r requirements.txt
        pytest --cov=nadle_backend --cov-report=xml tests/

    - name: SonarQube Scan
      uses: sonarqube-quality-gate-action@v1.3.0
      with:
        scanMetadataReportFile: backend/coverage.xml
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

    - name: Quality Gate Check
      uses: sonarqube-quality-gate-action@v1.3.0
      timeout-minutes: 5
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

### 2. 코드 커버리지 임계값 설정

```yaml
# sonar-project.properties
sonar.projectKey=xai-community
sonar.projectName=XAI Community
sonar.sources=backend/nadle_backend,frontend/app
sonar.tests=backend/tests,frontend/tests
sonar.python.coverage.reportPaths=backend/coverage.xml
sonar.javascript.lcov.reportPaths=frontend/coverage/lcov.info

# 품질 게이트 조건
sonar.coverage.exclusions=**/*test*/**,**/*__pycache__*/**
sonar.cpd.exclusions=**/*test*/**

# 임계값 설정
sonar.qualitygate.wait=true
```

### 3. 린트 및 포맷 검사 자동화

```yaml
# .github/workflows/lint-and-format.yml
name: 🧹 Lint and Format

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./backend
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install black flake8 mypy
        pip install -r requirements.txt
    
    - name: Run Black (formatting)
      run: black --check nadle_backend/ tests/
    
    - name: Run Flake8 (linting)
      run: flake8 nadle_backend/ tests/
    
    - name: Run MyPy (type checking)
      run: mypy nadle_backend/

  frontend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run ESLint
      run: npm run lint
    
    - name: Run TypeScript check
      run: npm run typecheck
    
    - name: Run Prettier check
      run: npx prettier --check "app/**/*.{ts,tsx,js,jsx}"
```

---

## 환경별 배포 전략

### 1. 환경 분리 및 보호 규칙

```yaml
# .github/workflows/deploy-environments.yml
name: 🚀 Environment Deployment

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # 개발 환경 (develop 브랜치)
  deploy-development:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: development
    
    steps:
    - name: Deploy to Development
      run: |
        echo "🚀 Deploying to Development Environment"
        # 개발 환경 배포 로직

  # 스테이징 환경 (main 브랜치)
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    needs: [backend-tests, frontend-tests]
    
    steps:
    - name: Deploy to Staging
      run: |
        echo "🚀 Deploying to Staging Environment"
        # 스테이징 환경 배포 로직

  # 프로덕션 환경 (수동 승인 필요)
  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    needs: [deploy-staging]
    
    steps:
    - name: Deploy to Production
      run: |
        echo "🚀 Deploying to Production Environment"
        # 프로덕션 배포 로직
```

### 2. Blue-Green 배포 구현

```yaml
# .github/workflows/blue-green-deployment.yml
name: 🔄 Blue-Green Deployment

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - staging

jobs:
  blue-green-deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Build Docker Image
      run: |
        docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
        docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    
    - name: Deploy to Green Environment
      run: |
        echo "🟢 Deploying to Green Environment"
        # Green 환경에 새 버전 배포
        kubectl set image deployment/app-green app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        kubectl rollout status deployment/app-green
    
    - name: Run Health Checks
      run: |
        echo "🔍 Running Health Checks on Green Environment"
        # Green 환경 헬스체크
        curl -f http://green.example.com/health || exit 1
    
    - name: Switch Traffic to Green
      run: |
        echo "🔄 Switching Traffic from Blue to Green"
        # 트래픽을 Green으로 전환
        kubectl patch service app-service -p '{"spec":{"selector":{"version":"green"}}}'
    
    - name: Monitor for Issues
      run: |
        echo "📊 Monitoring for 5 minutes"
        sleep 300
        # 5분간 모니터링
    
    - name: Cleanup Blue Environment
      run: |
        echo "🧹 Cleaning up Blue Environment"
        # Blue 환경 정리 (선택사항)
```

### 3. 자동 롤백 메커니즘

```yaml
# .github/workflows/rollback.yml
name: 🔄 Automatic Rollback

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rollback'
        required: true
        type: choice
        options:
        - production
        - staging

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    
    steps:
    - name: Get Previous Deployment
      id: previous
      run: |
        # 이전 배포 버전 조회
        PREVIOUS_VERSION=$(kubectl get deployment app -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}' | awk '{print $1-1}')
        echo "previous_version=$PREVIOUS_VERSION" >> $GITHUB_OUTPUT
    
    - name: Rollback to Previous Version
      run: |
        echo "🔄 Rolling back to version ${{ steps.previous.outputs.previous_version }}"
        kubectl rollout undo deployment/app --to-revision=${{ steps.previous.outputs.previous_version }}
        kubectl rollout status deployment/app
    
    - name: Verify Rollback
      run: |
        echo "✅ Verifying rollback"
        curl -f http://app.example.com/health || exit 1
```

---

## 모니터링 및 알림

### 1. Slack 알림 설정 (2025년 업데이트 반영)

```yaml
# .github/workflows/notifications.yml
name: 📢 Notifications

on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types: [completed]

jobs:
  notify-slack:
    runs-on: ubuntu-latest
    
    steps:
    - name: Get workflow conclusion
      id: workflow
      run: |
        echo "conclusion=${{ github.event.workflow_run.conclusion }}" >> $GITHUB_OUTPUT
        echo "name=${{ github.event.workflow_run.name }}" >> $GITHUB_OUTPUT
    
    - name: Notify Success
      if: steps.workflow.outputs.conclusion == 'success'
      uses: slackapi/slack-github-action@v1.24.0
      with:
        payload: |
          {
            "text": "✅ ${{ steps.workflow.outputs.name }} succeeded",
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*✅ Deployment Successful*\n\n*Repository:* ${{ github.repository }}\n*Branch:* ${{ github.ref_name }}\n*Commit:* <${{ github.event.workflow_run.html_url }}|${{ github.sha }}>\n*Author:* ${{ github.actor }}"
                }
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
    
    - name: Notify Failure
      if: steps.workflow.outputs.conclusion == 'failure'
      uses: slackapi/slack-github-action@v1.24.0
      with:
        payload: |
          {
            "text": "❌ ${{ steps.workflow.outputs.name }} failed",
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*❌ Deployment Failed*\n\n*Repository:* ${{ github.repository }}\n*Branch:* ${{ github.ref_name }}\n*Commit:* <${{ github.event.workflow_run.html_url }}|${{ github.sha }}>\n*Author:* ${{ github.actor }}\n\n*Action Required:* Please check the workflow logs"
                }
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 2. 성능 메트릭 수집

```yaml
# .github/workflows/performance-monitoring.yml
name: 📊 Performance Monitoring

on:
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다
  workflow_dispatch:

jobs:
  performance-check:
    runs-on: ubuntu-latest
    
    steps:
    - name: API Response Time Check
      run: |
        echo "🔍 Checking API response times"
        
        # 백엔드 API 응답 시간 측정
        BACKEND_TIME=$(curl -w "%{time_total}" -s -o /dev/null ${{ env.PROD_BACKEND_URL }}/health)
        
        # 프론트엔드 로딩 시간 측정
        FRONTEND_TIME=$(curl -w "%{time_total}" -s -o /dev/null ${{ env.PROD_FRONTEND_URL }})
        
        echo "Backend response time: ${BACKEND_TIME}s"
        echo "Frontend response time: ${FRONTEND_TIME}s"
        
        # 임계값 확인 (2초 이상이면 알림)
        if (( $(echo "$BACKEND_TIME > 2.0" | bc -l) )); then
          echo "⚠️ Backend response time too high: ${BACKEND_TIME}s"
          exit 1
        fi
        
        if (( $(echo "$FRONTEND_TIME > 3.0" | bc -l) )); then
          echo "⚠️ Frontend response time too high: ${FRONTEND_TIME}s"
          exit 1
        fi
    
    - name: Send Performance Alert
      if: failure()
      uses: slackapi/slack-github-action@v1.24.0
      with:
        payload: |
          {
            "text": "⚠️ Performance Alert",
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*⚠️ Performance Alert*\n\nResponse times exceed threshold.\nPlease investigate immediately."
                }
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 고급 기능

### 1. 재사용 가능한 워크플로우

```yaml
# .github/workflows/reusable-test.yml
name: Reusable Test Workflow

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      node-version:
        required: false
        type: string
        default: '20'
    secrets:
      SLACK_WEBHOOK_URL:
        required: true

jobs:
  test:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
    
    - name: Run Tests
      run: |
        npm ci
        npm test
```

### 2. 브랜치 보호 규칙 설정

GitHub 저장소 설정에서 다음 규칙을 적용하세요:

```yaml
# .github/branch-protection.yml (GitHub CLI 사용)
# gh api repos/:owner/:repo/branches/main/protection --method PUT --input protection.json

{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "backend-safe-checks",
      "frontend-safe-checks",
      "security-scan"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

### 3. 자동 릴리즈 노트 생성

```yaml
# .github/workflows/release.yml
name: 🏷️ Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Generate Release Notes
      run: |
        # 이전 태그부터 현재까지의 커밋 로그 생성
        PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD^)
        echo "# Release Notes" > release-notes.md
        echo "" >> release-notes.md
        echo "## Changes since $PREVIOUS_TAG" >> release-notes.md
        echo "" >> release-notes.md
        git log --pretty=format:"- %s (%h)" $PREVIOUS_TAG..HEAD >> release-notes.md
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        body_path: release-notes.md
        draft: false
        prerelease: false
```

---

## 실제 구현 예시

### 완성된 현업 수준 CI/CD 파이프라인

```yaml
# .github/workflows/enterprise-pipeline.yml
name: 🚀 Enterprise CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  PROD_BACKEND_URL: https://xai-community.onrender.com
  PROD_FRONTEND_URL: https://xai-community.vercel.app

jobs:
  # 1단계: 보안 검사
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run CodeQL Analysis
      uses: github/codeql-action/analyze@v3
    
    - name: Run Secret Scanning
      uses: trufflesecurity/trufflehog@v3.63.2
      with:
        path: ./
        base: ${{ github.event.repository.default_branch }}
        head: HEAD

  # 2단계: 품질 검사
  quality-gate:
    runs-on: ubuntu-latest
    needs: security-scan
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Backend Quality Check
      run: |
        cd backend
        uv sync --frozen
        uv run pytest --cov=nadle_backend --cov-report=xml
        uv run black --check nadle_backend/
        uv run flake8 nadle_backend/
    
    - name: Frontend Quality Check
      run: |
        cd frontend
        npm ci
        npm run lint
        npm run typecheck
        npm run test:run
    
    - name: SonarQube Analysis
      uses: sonarqube-quality-gate-action@v1.3.0
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

  # 3단계: 환경별 배포
  deploy:
    runs-on: ubuntu-latest
    needs: [security-scan, quality-gate]
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy with Blue-Green Strategy
      run: |
        echo "🔄 Executing Blue-Green Deployment"
        # 실제 배포 로직
    
    - name: Run Smoke Tests
      run: |
        echo "🧪 Running Smoke Tests"
        curl -f ${{ env.PROD_BACKEND_URL }}/health
        curl -f ${{ env.PROD_FRONTEND_URL }}
    
    - name: Monitor Performance
      run: |
        echo "📊 Monitoring Performance for 5 minutes"
        for i in {1..5}; do
          curl -w "Response time: %{time_total}s\n" -s -o /dev/null ${{ env.PROD_BACKEND_URL }}/health
          sleep 60
        done

  # 4단계: 배포 후 알림
  notify:
    runs-on: ubuntu-latest
    needs: deploy
    if: always()
    
    steps:
    - name: Send Slack Notification
      uses: slackapi/slack-github-action@v1.24.0
      with:
        payload: |
          {
            "text": "${{ needs.deploy.result == 'success' && '✅ Deployment Successful' || '❌ Deployment Failed' }}",
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*${{ needs.deploy.result == 'success' && '✅ Deployment Successful' || '❌ Deployment Failed' }}*\n\n*Repository:* ${{ github.repository }}\n*Branch:* ${{ github.ref_name }}\n*Commit:* ${{ github.sha }}\n*Author:* ${{ github.actor }}"
                }
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 🎯 실행 체크리스트

### 필수 설정 사항
- [ ] GitHub Secrets 설정
  - [ ] `SONAR_TOKEN`
  - [ ] `SONAR_HOST_URL`
  - [ ] `SLACK_WEBHOOK_URL`
- [ ] 브랜치 보호 규칙 설정
- [ ] 환경별 배포 환경 구성
- [ ] Dependabot 활성화
- [ ] CodeQL 기본 설정 활성화

### 단계별 적용 방법
1. **1주차**: 보안 스캐닝 도입
2. **2주차**: 품질 게이트 구현
3. **3주차**: 환경별 배포 전략 적용
4. **4주차**: 모니터링 및 알림 구축
5. **5주차**: 고급 기능 추가

---

## 📚 참고 자료

- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [CodeQL 분석 가이드](https://docs.github.com/en/code-security/code-scanning)
- [SonarQube 연동 가이드](https://docs.sonarsource.com/sonarqube/)
- [Slack 알림 설정](https://github.com/marketplace/actions/slack-notify)

---

> **💡 팁**: 한 번에 모든 것을 적용하지 말고, 단계별로 도입하여 팀이 적응할 수 있도록 하세요. 각 단계마다 측정 가능한 지표를 설정하여 개선 효과를 확인하는 것이 중요합니다.