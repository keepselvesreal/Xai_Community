# 테스트 코드 종합 문서

## 📋 목차

1. [테스트 아키텍처 개요](#테스트-아키텍처-개요)
2. [Epic/Feature/User Story 매핑](#epicfeatureuser-story-매핑)
3. [테스트 폴더 조직화](#테스트-폴더-조직화)
4. [테스트 모듈 관계도](#테스트-모듈-관계도)
5. [Mock 사용 정책](#mock-사용-정책)
6. [회귀 테스트 사용법](#회귀-테스트-사용법)
7. [테스트 실행 가이드](#테스트-실행-가이드)

---

## 🏗️ 테스트 아키텍처 개요

### 테스트 전략
**실제 구현 우선 검증 → 필요시에만 Mock 적용**
- Service/Utils 계층: 실제 구현 직접 테스트
- Repository 계층: DB 호출 비용으로 Mock 사용
- Infrastructure 계층: 외부 의존성만 Mock

### 테스트 피라미드 구조
```
        🔺 E2E/Contract Tests (Few)
       🔺🔺 Integration Tests (Some)  
    🔺🔺🔺🔺 Unit Tests (Many)
```

---

## 🗺️ Epic/Feature/User Story 매핑

### 🎯 Epic 1: 사용자 인증 및 권한 관리
**목표**: 안전하고 확장 가능한 인증 시스템 구축

#### 📦 Feature 1.1: 사용자 인증
- **User Story**: 사용자가 안전하게 로그인/로그아웃할 수 있다
- **테스트 모듈**:
  - `test_auth_service.py` - 인증 비즈니스 로직
  - `test_jwt.py` - JWT 토큰 관리
  - `test_password.py` - 비밀번호 보안
  - `test_auth_router.py` - 인증 API 엔드포인트
  - `test_refresh_token.py` - 토큰 갱신 보안

#### 📦 Feature 1.2: 권한 관리
- **User Story**: 사용자가 자신의 콘텐츠만 수정/삭제할 수 있다
- **테스트 모듈**:
  - `test_permissions.py` - 권한 검사 로직
  - `test_auth_dependency.py` - FastAPI 의존성 주입

### 🎯 Epic 2: 콘텐츠 관리 시스템
**목표**: 포스트와 댓글을 통한 커뮤니티 플랫폼 구축

#### 📦 Feature 2.1: 포스트 관리
- **User Story**: 사용자가 포스트를 작성, 수정, 삭제, 조회할 수 있다
- **테스트 모듈**:
  - `test_posts_service.py` - 포스트 비즈니스 로직
  - `test_post_repository.py` - 포스트 데이터 액세스
  - `test_posts_router.py` - 포스트 API 엔드포인트

#### 📦 Feature 2.2: 댓글 시스템
- **User Story**: 사용자가 포스트에 댓글을 달고 답글을 작성할 수 있다
- **테스트 모듈**:
  - `test_comments_service.py` - 댓글 비즈니스 로직
  - `test_comment_repository.py` - 댓글 데이터 액세스
  - `test_comments_router.py` - 댓글 API 엔드포인트

### 🎯 Epic 3: 파일 및 미디어 관리
**목표**: 안전하고 효율적인 파일 업로드 및 관리 시스템

#### 📦 Feature 3.1: 파일 업로드
- **User Story**: 사용자가 이미지와 첨부파일을 업로드할 수 있다
- **테스트 모듈**:
  - `test_file_validator.py` - 파일 검증
  - `test_file_storage.py` - 파일 저장 관리
  - `test_file_metadata.py` - 파일 메타데이터
  - `test_file_repository.py` - 파일 데이터 액세스
  - `test_file_upload_api.py` - 파일 업로드 API

#### 📦 Feature 3.2: 리치 텍스트 에디터
- **User Story**: 사용자가 리치 텍스트로 콘텐츠를 작성할 수 있다
- **테스트 모듈**:
  - `test_content_service.py` - 콘텐츠 처리 로직
  - `test_editor_api.py` - 에디터 API 통합

### 🎯 Epic 4: 시스템 인프라스트럭처
**목표**: 안정적이고 확장 가능한 시스템 기반 구축

#### 📦 Feature 4.1: 데이터베이스 연결
- **User Story**: 시스템이 MongoDB와 안정적으로 연결되어야 한다
- **테스트 모듈**:
  - `test_database_connection.py` - DB 연결 관리
  - `test_indexes_creation.py` - 인덱스 최적화
  - `test_config_settings.py` - 설정 관리

#### 📦 Feature 4.2: 데이터 모델
- **User Story**: 데이터가 정확하게 검증되고 저장되어야 한다
- **테스트 모듈**:
  - `test_user_model.py` - 사용자 모델
  - `test_models_validation.py` - 모델 검증
  - `test_models_extended.py` - 확장 모델

---

## 📁 테스트 폴더 조직화

### 🔧 Unit Tests (`tests/unit/`)
**원리**: 개별 컴포넌트의 독립적 기능 검증
**특징**: 빠른 실행, 외부 의존성 최소화

#### 🏗️ Infrastructure Layer
- `test_database_connection.py` - DB 연결 관리
- `test_config_settings.py` - 환경 설정
- `test_indexes_creation.py` - DB 인덱스 관리

#### 📊 Model Layer  
- `test_user_model.py` - 사용자 데이터 모델
- `test_models_validation.py` - Pydantic 검증
- `test_models_extended.py` - 확장 모델

#### 💾 Repository Layer
- `test_user_repository.py` - 사용자 데이터 액세스
- `test_post_repository.py` - 포스트 데이터 액세스
- `test_comment_repository.py` - 댓글 데이터 액세스
- `test_file_repository.py` - 파일 데이터 액세스

#### 🔧 Service Layer
- `test_auth_service.py` - 인증 비즈니스 로직
- `test_posts_service.py` - 포스트 비즈니스 로직
- `test_comments_service.py` - 댓글 비즈니스 로직
- `test_content_service.py` - 콘텐츠 처리 로직

#### 🛠️ Utils Layer
- `test_jwt.py` - JWT 토큰 관리
- `test_password.py` - 비밀번호 보안
- `test_permissions.py` - 권한 검사
- `test_auth_dependency.py` - FastAPI 의존성

#### 📁 File Management
- `test_file_validator.py` - 파일 검증
- `test_file_storage.py` - 파일 저장
- `test_file_metadata.py` - 파일 메타데이터
- `test_file_upload_api.py` - 파일 업로드 API

### 🔗 Integration Tests (`tests/integration/`)
**원리**: 여러 컴포넌트 간 상호작용 검증
**특징**: 실제 환경과 유사한 조건, 시나리오 기반

- `test_auth_router.py` - 인증 API 통합
- `test_posts_router.py` - 포스트 API 통합
- `test_comments_router.py` - 댓글 API 통합
- `test_editor_api.py` - 에디터 API 통합
- `test_dynamic_configuration.py` - 동적 설정
- `test_atlas_data_verification.py` - MongoDB Atlas 검증

### 📄 Contract Tests (`tests/contract/`)
**원리**: API 계약 준수 검증
**특징**: 클라이언트-서버 간 인터페이스 보장

- `test_file_api_contract.py` - 파일 API 계약
- `test_editor_api_contract.py` - 에디터 API 계약

### 🔒 Security Tests (`tests/security/`)
**원리**: 보안 취약점 검증
**특징**: 공격 시나리오, 보안 정책 준수

- `test_refresh_token.py` - 토큰 보안 검증

---

## 🔗 테스트 모듈 관계도

### 의존성 계층 구조
```
📱 API Layer (Router Tests)
    ↓ 의존
🏢 Service Layer (Service Tests)  
    ↓ 의존
💾 Repository Layer (Repository Tests)
    ↓ 의존
📊 Model Layer (Model Tests)
    ↓ 의존
🏗️ Infrastructure Layer (DB, Config Tests)
```

### 수평적 관계
```
🔐 Auth Service ←→ 🛡️ Permission Utils
📝 Posts Service ←→ 💬 Comments Service  
📁 File Service ←→ 📝 Content Service
```

### 테스트 간 데이터 흐름
```
Unit Tests → Integration Tests → Contract Tests → Security Tests
   ↑              ↑                   ↑              ↑
Mock 사용     실제 DB 연결        API 계약      보안 정책
```

---

## 🎭 Mock 사용 정책

### ✅ Mock 사용이 적절한 경우

#### 🚨 DB/외부 의존성 (고비용)
```python
# Repository 계층 - MongoDB 연결
@pytest.fixture
def mock_post_repository():
    """
    🚨 Mock 사용 이유: MongoDB 호출 비용 높음
    🔄 대안 검토: 실제 DB 사용 시 테스트 불안정성
    """
    return Mock(spec=PostRepository)
```

#### 🌐 네트워크 호출
```python
# 외부 API 호출
@patch('requests.post')
def test_external_api_call(mock_post):
    """
    🚨 Mock 사용 이유: 외부 서비스 의존성 제거
    🔄 대안 검토: 네트워크 지연 및 불안정성
    """
```

#### 📁 파일 시스템
```python
# 파일 I/O 작업
@patch('builtins.open')
def test_file_upload(mock_open):
    """
    🚨 Mock 사용 이유: 파일 시스템 I/O 비용
    🔄 대안 검토: 임시 파일 관리 복잡성
    """
```

### ❌ Mock 사용을 피해야 하는 경우

#### 🔧 Service 계층 (이미 구현됨)
```python
# ❌ 잘못된 사용
@pytest.fixture
def mock_posts_service():
    return Mock(spec=PostsService)

# ✅ 올바른 사용  
@pytest.fixture
def posts_service(mock_post_repository):
    """실제 PostsService + Repository Mock만"""
    return PostsService(post_repository=mock_post_repository)
```

#### 🛠️ Utils 계층 (순수 함수)
```python
# ❌ 잘못된 사용
@patch('nadle_backend.utils.jwt.JWTManager')

# ✅ 올바른 사용
@pytest.fixture
def jwt_manager():
    """실제 JWT 암호화/복호화 로직 테스트"""
    return JWTManager(secret_key="test-key")
```

### 📋 Mock 사용 체크리스트
- [ ] Mock 대상이 이미 구현 완료된 기능인가?
- [ ] Mock 사용 조건이 "호출 비용이 높은 경우"에 해당하는가?
- [ ] Mock 사용 대안을 검토하고 문서화했는가?
- [ ] Mock 없이 진행 시의 문제점을 명시했는가?

---

## 🔄 회귀 테스트 사용법

### 1. 기능 개발 후 테스트 실행
```bash
# 특정 기능 테스트
uv run pytest tests/unit/test_posts_service.py -v

# 전체 Unit 테스트
uv run pytest tests/unit/ -v

# 통합 테스트
uv run pytest tests/integration/ -v
```

### 2. 코드 변경 시 영향도 분석
```bash
# 관련 테스트만 실행
uv run pytest tests/unit/test_posts_service.py tests/unit/test_comments_service.py -v

# 커버리지 확인
uv run pytest tests/unit/ --cov=nadle_backend --cov-report=html
```

### 3. 배포 전 전체 검증
```bash
# 모든 테스트 실행
uv run pytest tests/ -v

# 병렬 실행 (빠른 검증)
uv run pytest tests/unit/ -n auto

# 순차 실행 (안정성 중시)
uv run pytest tests/integration/ --maxfail=1
```

### 4. 지속적 통합 (CI) 설정
```yaml
# GitHub Actions 예시
- name: Run Tests
  run: |
    uv run pytest tests/unit/ -v --cov=nadle_backend
    uv run pytest tests/integration/ -v
    uv run pytest tests/contract/ -v
    uv run pytest tests/security/ -v
```

---

## 🚀 테스트 실행 가이드

### 테스트 분류별 실행

#### 🔧 Unit Tests (빠른 피드백)
```bash
# 전체 Unit 테스트
uv run pytest tests/unit/ -v

# 특정 계층별
uv run pytest tests/unit/test_*_service.py -v    # Service 계층
uv run pytest tests/unit/test_*_repository.py -v # Repository 계층
uv run pytest tests/unit/test_*_model.py -v      # Model 계층
```

#### 🔗 Integration Tests (시나리오 검증)
```bash
# API 통합 테스트
uv run pytest tests/integration/ -v

# 특정 API
uv run pytest tests/integration/test_auth_router.py -v
```

#### 📄 Contract Tests (API 계약)
```bash
# API 계약 검증
uv run pytest tests/contract/ -v
```

#### 🔒 Security Tests (보안 검증)
```bash
# 보안 테스트
uv run pytest tests/security/ -v
```

### 테스트 옵션

#### 상세 정보 출력
```bash
uv run pytest tests/ -v --tb=short
```

#### 실패 시 즉시 중단
```bash
uv run pytest tests/ --maxfail=1
```

#### 커버리지 리포트
```bash
uv run pytest tests/ --cov=nadle_backend --cov-report=html
```

#### 병렬 실행
```bash
uv run pytest tests/unit/ -n auto
```

### 테스트 환경 설정
```bash
# 테스트 환경 변수
export TEST_ENV=true
export DATABASE_URL="mongodb://localhost:27017/test_db"

# 테스트 실행
uv run pytest tests/
```

---

## 📊 테스트 메트릭스

### 현재 테스트 현황
- **Unit Tests**: 35+ 모듈
- **Integration Tests**: 8+ 모듈  
- **Contract Tests**: 2+ 모듈
- **Security Tests**: 1+ 모듈

### 커버리지 목표
- **Unit Tests**: 90%+ 코드 커버리지
- **Integration Tests**: 핵심 API 엔드포인트 100%
- **Contract Tests**: 외부 API 계약 100%
- **Security Tests**: 주요 보안 시나리오 100%

### 성능 목표
- **Unit Tests**: < 30초 전체 실행
- **Integration Tests**: < 2분 전체 실행
- **Contract Tests**: < 1분 전체 실행
- **Security Tests**: < 30초 전체 실행

---

**📝 마지막 업데이트**: 2025년 06월 28일
**🔄 다음 업데이트**: 새로운 테스트 모듈 추가 시