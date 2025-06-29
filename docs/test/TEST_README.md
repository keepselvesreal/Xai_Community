# 테스트 코드 문서화 시스템

## 📋 문서 체계 개요

이 디렉토리는 **체계적이고 실용적인 테스트 문서화**를 위한 완전한 가이드를 제공합니다.

### 📚 문서 구성

#### 🎯 핵심 문서
1. **[README_TEST_COMPREHENSIVE.md](./README_TEST_COMPREHENSIVE.md)** - 테스트 코드 종합 문서
   - 전체 테스트 아키텍처 개요
   - Epic/Feature/User Story 매핑
   - 테스트 폴더 조직화 원리
   - Mock 사용 정책

2. **[EPIC_FEATURE_MAPPING.md](./EPIC_FEATURE_MAPPING.md)** - 비즈니스 요구사항 매핑
   - Epic → Feature → User Story → Test 연결
   - 요구사항 추적 가능성 매트릭스
   - 변경 영향도 분석

3. **[TEST_USAGE_GUIDE.md](./TEST_USAGE_GUIDE.md)** - 실용적 사용법 가이드
   - 테스트 모듈 관계 시각화
   - 회귀 테스트 체계
   - Mock 사용법 상세 가이드
   - CI/CD 통합 및 트러블슈팅

4. **[README_TEST_REFACTORING.md](./README_TEST_REFACTORING.md)** - Mock 재설계 보고서
   - Mock 사용 기준에 따른 테스트 재설계
   - 실제 구현 우선 검증 원칙 적용
   - 재설계 완료 보고서

## 🚀 빠른 시작

### 💡 테스트 실행하기
```bash
# 전체 테스트 실행
uv run pytest tests/ -v

# 계층별 테스트 실행
uv run pytest tests/unit/ -v          # Unit Tests
uv run pytest tests/integration/ -v   # Integration Tests
uv run pytest tests/contract/ -v      # Contract Tests
uv run pytest tests/security/ -v      # Security Tests
```

### 🔍 테스트 찾기
```bash
# 특정 기능 테스트
uv run pytest tests/unit/test_posts_service.py -v
uv run pytest tests/unit/test_auth_service.py -v

# 키워드로 테스트 검색
uv run pytest tests/ -k "login" -v
uv run pytest tests/ -k "create_post" -v
```

### 📊 커버리지 확인
```bash
# 커버리지 리포트 생성
uv run pytest tests/ --cov=src --cov-report=html
# 결과: htmlcov/index.html 확인
```

## 🏗️ 테스트 아키텍처

### 계층별 테스트 구조
```
📱 Frontend (Manual Testing)
    ↓
🔗 Integration Tests (API 통합)
    ↓  
🏢 Service Tests (비즈니스 로직)
    ↓
💾 Repository Tests (데이터 액세스) 
    ↓
📊 Model Tests (데이터 검증)
    ↓
🏗️ Infrastructure Tests (DB, 설정)
```

### 🎭 Mock 사용 원칙
- **✅ 실제 구현 우선**: Service/Utils 계층은 실제 인스턴스 사용
- **🚨 적절한 Mock**: Repository/DB는 호출 비용으로 Mock 사용
- **📝 사용 근거 명시**: 모든 Mock 사용 시 이유와 대안 검토 결과 문서화

## 📖 Epic/Feature 매핑

### 🎯 주요 Epic
1. **사용자 인증 및 권한 관리** (Epic 1)
   - 로그인/로그아웃, 토큰 관리, 권한 검사
   - 테스트: `test_auth_*`, `test_jwt.py`, `test_permissions.py`

2. **콘텐츠 관리 시스템** (Epic 2)
   - 포스트/댓글 CRUD, 검색, 계층구조
   - 테스트: `test_posts_*`, `test_comments_*`

3. **파일 및 미디어 관리** (Epic 3)
   - 파일 업로드, 검증, 리치 텍스트 에디터
   - 테스트: `test_file_*`, `test_content_*`

4. **시스템 인프라스트럭처** (Epic 4)
   - DB 연결, 설정 관리, 데이터 모델
   - 테스트: `test_database_*`, `test_config_*`, `test_models_*`

## 🔄 회귀 테스트 시나리오

### ⚡ 빠른 피드백 (< 30초)
```bash
# 핵심 비즈니스 로직만
uv run pytest tests/unit/test_*_service.py -x --tb=short
```

### 🔧 개발자 피드백 (< 5분)
```bash
# Service + Utils 계층
uv run pytest tests/unit/test_*_service.py tests/unit/test_jwt.py tests/unit/test_password.py -v
```

### 🔗 통합 검증 (< 15분)
```bash
# Unit + Integration
uv run pytest tests/unit/ tests/integration/ -v --maxfail=5
```

### 🎯 전체 검증 (< 30분)
```bash
# 모든 테스트 + 커버리지
uv run pytest tests/ -v --cov=src --cov-report=html
```

## 📊 테스트 현황

### 테스트 분포
- **Unit Tests**: 35+ 모듈
- **Integration Tests**: 8+ 모듈
- **Contract Tests**: 2+ 모듈
- **Security Tests**: 1+ 모듈

### 커버리지 목표
- **Unit Tests**: 90%+ 코드 커버리지
- **Integration Tests**: 핵심 API 100%
- **Security Tests**: 주요 시나리오 100%

## 🛠️ 개발 워크플로우

### 🔨 새 기능 개발
1. **TDD 사이클**: Red → Green → Refactor
2. **테스트 우선 작성**
3. **최소 구현으로 통과**
4. **리팩터링 및 전체 테스트**

### 🐛 버그 수정
1. **버그 재현 테스트 작성**
2. **실패 확인**
3. **수정 후 통과 확인**
4. **관련 기능 회귀 테스트**

### 🔄 리팩터링
1. **리팩터링 전 베이스라인**
2. **리팩터링 수행**
3. **동일 테스트 결과 확인**

## 🚨 트러블슈팅

### 일반적인 문제
- **Mock 오류**: `spec` 파라미터 사용 또는 실제 구현 사용
- **비동기 오류**: `pytest-asyncio` 설정 확인
- **DB 연결 오류**: 환경 변수 및 MongoDB 서비스 확인

### 성능 최적화
```bash
# 병렬 실행
uv run pytest tests/unit/ -n auto

# 실행 시간 측정
uv run pytest tests/ --durations=10
```

## 📞 지원 및 문의

### 📚 상세 문서
- **전체 가이드**: [README_TEST_COMPREHENSIVE.md](./README_TEST_COMPREHENSIVE.md)
- **비즈니스 매핑**: [EPIC_FEATURE_MAPPING.md](./EPIC_FEATURE_MAPPING.md)
- **사용법 가이드**: [TEST_USAGE_GUIDE.md](./TEST_USAGE_GUIDE.md)
- **재설계 보고서**: [README_TEST_REFACTORING.md](./README_TEST_REFACTORING.md)

### 🔧 도구 및 환경
- **Python**: 3.11+
- **테스트 프레임워크**: pytest
- **의존성 관리**: uv
- **비동기 테스트**: pytest-asyncio
- **커버리지**: pytest-cov

---

**🎯 목표**: 신뢰할 수 있고 유지보수 가능한 테스트 코드로 안정적인 서비스 제공
**📈 전략**: 실제 구현 우선 검증 → 적절한 Mock 사용 → 체계적 문서화

**📝 마지막 업데이트**: 2025년 06월 28일