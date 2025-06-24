# Task 6: 메인 앱 통합

**Feature Group**: System Integration  
**Task List 제목**: 메인 앱 통합  
**최초 작성 시각**: 2024-12-19 15:30:00

## 📋 Task 개요

### 리스크 레벨: 낮음
- **이유**: 기존 구성요소 조합, 설정 중심, 단순 통합 작업
- **대응**: 통합 테스트로 검증, 단계별 라우터 등록

### 대상 파일
- `backend/src/main.py`
- `backend/requirements.txt`
- `backend/pyproject.toml`

## 🎯 Subtasks

### 1. FastAPI 앱 설정
- **테스트 함수**: `test_app_startup`
- **구현 내용**: FastAPI 인스턴스 생성 및 기본 설정
- **검증 항목**:
  - FastAPI 앱 생성 (title, version, description)
  - 데이터베이스 연결 시작/종료 이벤트 핸들러
  - 애플리케이션 메타데이터 설정
  - 환경별 설정 로드
- **테스트 명령어**: `uv run pytest tests/integration/test_main_app.py::test_app_startup -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 2. 라우터 등록 및 미들웨어
- **테스트 함수**: `test_router_registration`
- **구현 내용**: 모든 API 라우터 등록 및 미들웨어 설정
- **검증 항목**:
  - 인증 라우터 등록 (/auth)
  - 게시글 라우터 등록 (/posts)
  - 댓글 라우터 등록 (/posts/{slug}/comments)
  - 에러 핸들러 미들웨어
  - 로깅 미들웨어
- **테스트 명령어**: `uv run pytest tests/integration/test_main_app.py::test_router_registration -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 3. CORS 및 보안 설정
- **테스트 함수**: `test_security_config`
- **구현 내용**: 프로덕션 준비 보안 설정
- **검증 항목**:
  - CORS 설정 (허용 도메인, 메서드, 헤더)
  - 보안 헤더 추가 (X-Frame-Options, X-Content-Type-Options)
  - Rate Limiting 설정 (선택적)
  - Request/Response 로깅
- **테스트 명령어**: `uv run pytest tests/integration/test_main_app.py::test_security_config -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 4. 전체 API 통합 테스트
- **테스트 함수**: `test_api_integration_with_auth`
- **구현 내용**: End-to-End 테스트 시나리오
- **검증 항목**:
  - 회원가입 → 로그인 → 게시글 작성 플로우
  - 게시글 조회 → 댓글 작성 → 반응 추가 플로우
  - 권한 기반 수정/삭제 플로우
  - 에러 처리 및 예외 상황 대응
  - API 응답 시간 및 성능 검증
- **테스트 명령어**: `uv run pytest tests/integration/test_main_app.py::test_api_integration_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 task 완료 가능

## 🔗 의존성
- **선행 조건**: Task 1-5 모든 구성요소 완료
- **후행 의존성**: 없음 (최종 통합 단계)

## 📊 Social Units 및 통합 포인트

### 라우터 간 연동
- 인증 라우터의 토큰이 다른 모든 라우터에서 사용
- 게시글 라우터와 댓글 라우터의 연계 동작
- 반응 시스템과 게시글/댓글의 통계 연동

### 미들웨어 체인
- 인증 미들웨어 → 권한 확인 → 비즈니스 로직 → 응답
- 에러 핸들링 미들웨어의 전역 적용
- 로그 미들웨어를 통한 요청/응답 추적

## 🚀 FastAPI 애플리케이션 구조
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="콘텐츠 관리 API",
    version="1.0.0",
    description="멀티 서비스 지원 콘텐츠 관리 시스템"
)

# 미들웨어 설정
app.add_middleware(CORSMiddleware, ...)

# 라우터 등록
app.include_router(auth_router, prefix="/api/auth", tags=["인증"])
app.include_router(posts_router, prefix="/api/posts", tags=["게시글"])
app.include_router(comments_router, prefix="/api", tags=["댓글"])

# 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
```

## 🔧 환경별 설정 관리
- **개발 환경**: DEBUG=True, 상세 로깅, CORS 허용
- **테스트 환경**: 테스트 데이터베이스, Mock 외부 서비스
- **프로덕션 환경**: 보안 강화, 제한적 CORS, 성능 최적화

## 📋 API 문서 자동 생성
- **Swagger UI**: `/docs` 엔드포인트
- **ReDoc**: `/redoc` 엔드포인트
- **OpenAPI JSON**: `/openapi.json` 엔드포인트

## 🎯 헬스 체크 엔드포인트
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": "connected"
    }
```

## 📊 모니터링 및 로깅
- 구조화된 JSON 로깅
- 요청/응답 시간 측정
- 에러 발생 시 상세 로깅
- 데이터베이스 연결 상태 모니터링

## ✅ 완료 조건

### 개별 Subtask 검증 (순차 진행 필수)
```bash
# Subtask 1: FastAPI 앱 설정
uv run pytest tests/integration/test_main_app.py::test_app_startup -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 2: 라우터 등록 및 미들웨어
uv run pytest tests/integration/test_main_app.py::test_router_registration -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 3: CORS 및 보안 설정
uv run pytest tests/integration/test_main_app.py::test_security_config -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 4: 전체 API 통합 테스트
uv run pytest tests/integration/test_main_app.py::test_api_integration_with_auth -v
# ↑ exit code 0 확인 후 task 완료
```

### Task 전체 성공 판단
```bash
# 모든 subtask 테스트 한번에 실행 (모든 subtask 개별 통과 후)
uv run pytest tests/integration/test_main_app.py -v

# 전체 프로젝트 통합 테스트 실행 (모든 이전 task 완료 후)
uv run pytest tests/integration -v

# 전체 테스트 실행 (모든 task 완료 후)
uv run pytest tests/ -v
```

**성공 기준**:
- [ ] 모든 subtask 테스트가 순차적으로 exit code 0으로 통과
- [ ] 어떤 이유든 테스트 실패 시 해당 subtask 실패로 간주
- [ ] 이전 subtask 통과 없이 다음 subtask 진행 금지
- [ ] 모든 subtask 완료 후에만 전체 프로젝트 완료
- [ ] Task 1-5 모든 선행 task 완료 필수

**실패 처리**:
- 네트워크, 환경 설정, 외부 의존성 등 어떤 이유든 테스트 실패 시 subtask 실패
- 실패한 subtask는 문제 해결 후 재테스트 필요
- 순차 진행 원칙 준수 (이전 subtask 성공 후 다음 진행)
- 전체 프로젝트의 최종 통합 단계이므로 모든 의존성 해결 후 실행