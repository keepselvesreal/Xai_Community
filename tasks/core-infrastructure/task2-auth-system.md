# Task 2: 인증/권한 시스템 구현

**Feature Group**: Core Infrastructure  
**Task List 제목**: 인증/권한 시스템 구현  
**최초 작성 시각**: 2024-12-19 15:30:00

## 📋 Task 개요

### 리스크 레벨: 중간
- **이유**: 보안 기반 시스템, 모든 기능의 전제 조건
- **대응**: 표준 보안 패턴 준수, 단계별 테스트

### 대상 파일
- `backend/src/models/user.py`
- `backend/src/repositories/user_repository.py`
- `backend/src/services/auth_service.py`
- `backend/src/utils/jwt.py`
- `backend/src/utils/password.py`
- `backend/src/dependencies/auth.py`
- `backend/src/utils/permissions.py`
- `backend/src/routers/auth.py`

## 🎯 Subtasks

### 1. 사용자 모델 및 저장소
- **테스트 함수**: `test_user_model`, `test_user_repository`
- **구현 내용**: User 모델, UserRepository 클래스
- **검증 항목**: 이메일/핸들 중복 확인, CRUD 연산, 데이터 검증
- **테스트 명령어**: `uv run pytest tests/unit/test_user_model.py tests/unit/test_user_repository.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 2. JWT 토큰 시스템
- **테스트 함수**: `test_jwt_creation`, `test_jwt_verification`
- **구현 내용**: 토큰 생성/검증, 만료 시간 관리
- **검증 항목**: 토큰 유효성, 만료 처리, 페이로드 검증
- **테스트 명령어**: `uv run pytest tests/unit/test_jwt.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 3. 패스워드 해싱
- **테스트 함수**: `test_password_hashing`
- **구현 내용**: bcrypt 기반 패스워드 해싱/검증
- **검증 항목**: 해싱 강도, 검증 정확성, 보안성
- **테스트 명령어**: `uv run pytest tests/unit/test_password.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 4. 인증 미들웨어
- **테스트 함수**: `test_auth_dependency`
- **구현 내용**: FastAPI Dependency를 활용한 인증 처리
- **검증 항목**: 토큰 추출, 사용자 인증, 선택적 인증
- **테스트 명령어**: `uv run pytest tests/unit/test_auth_dependency.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 5. 권한 체크 유틸리티
- **테스트 함수**: `test_permission_checker`
- **구현 내용**: 리소스 소유권, 역할 기반 권한 확인
- **검증 항목**: 소유자 권한, 관리자 권한, 접근 제어
- **테스트 명령어**: `uv run pytest tests/unit/test_permissions.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 6. 인증 서비스 로직
- **테스트 함수**: `test_auth_service`
- **구현 내용**: 회원가입, 로그인, 프로필 관리
- **검증 항목**: 중복 검사, 인증 플로우, 비즈니스 로직
- **테스트 명령어**: `uv run pytest tests/unit/test_auth_service.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 7. 인증 API 라우터
- **테스트 함수**: `test_auth_router`
- **구현 내용**: /auth 엔드포인트 구현
- **검증 항목**: API 응답, 에러 처리, 보안 헤더
- **테스트 명령어**: `uv run pytest tests/integration/test_auth_router.py -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 task 완료 가능

## 🔗 의존성
- **선행 조건**: Task 1 (데이터베이스 기반 설정)
- **후행 의존성**: Task 3-6의 모든 CUD 작업이 이 Task에 의존

## 📊 Social Units
- JWT 유틸리티 ↔ 인증 미들웨어 (토큰 처리)
- 사용자 저장소 ↔ 인증 서비스 (데이터 연동)
- 권한 체크 ↔ API 라우터 (접근 제어)

## 🔐 보안 고려사항
- JWT 토큰 만료 시간 관리
- 패스워드 복잡성 검증
- 브루트포스 공격 방지
- 사용자 상태 관리 (active/inactive)

## ✅ 완료 조건

### 개별 Subtask 검증 (순차 진행 필수)
```bash
# Subtask 1: 사용자 모델 및 저장소
uv run pytest tests/unit/test_user_model.py tests/unit/test_user_repository.py -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 2: JWT 토큰 시스템
uv run pytest tests/unit/test_jwt.py -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 3: 패스워드 해싱
uv run pytest tests/unit/test_password.py -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 4: 인증 미들웨어
uv run pytest tests/unit/test_auth_dependency.py -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 5: 권한 체크 유틸리티
uv run pytest tests/unit/test_permissions.py -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 6: 인증 서비스 로직
uv run pytest tests/unit/test_auth_service.py -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 7: 인증 API 라우터
uv run pytest tests/integration/test_auth_router.py -v
# ↑ exit code 0 확인 후 task 완료
```

### Task 전체 성공 판단
```bash
# 모든 subtask 테스트 한번에 실행 (모든 subtask 개별 통과 후)
uv run pytest tests/unit/test_user_model.py tests/unit/test_user_repository.py tests/unit/test_jwt.py tests/unit/test_password.py tests/unit/test_auth_dependency.py tests/unit/test_permissions.py tests/unit/test_auth_service.py tests/integration/test_auth_router.py -v

# 또는 auth 관련 테스트 전체 실행
uv run pytest tests/ -k "auth" -v
```

**성공 기준**:
- [ ] 모든 subtask 테스트가 순차적으로 exit code 0으로 통과
- [ ] 어떤 이유든 테스트 실패 시 해당 subtask 실패로 간주
- [ ] 이전 subtask 통과 없이 다음 subtask 진행 금지
- [ ] 모든 subtask 완료 후에만 다음 task 진행 가능

**실패 처리**:
- 네트워크, 환경 설정, 외부 의존성 등 어떤 이유든 테스트 실패 시 subtask 실패
- 실패한 subtask는 문제 해결 후 재테스트 필요
- 순차 진행 원칙 준수 (이전 subtask 성공 후 다음 진행)