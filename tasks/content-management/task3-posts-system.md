# Task 3: 게시글 기능 완전 구현

**Feature Group**: Content Management  
**Task List 제목**: 게시글 기능 완전 구현  
**최초 작성 시각**: 2024-12-19 15:30:00

## 📋 Task 개요

### 리스크 레벨: 중간
- **이유**: 핵심 비즈니스 로직, 인증 시스템 의존성
- **대응**: 단계별 TDD, API 명세서 준수

### 대상 파일
- `backend/src/models/post.py`
- `backend/src/repositories/post_repository.py`
- `backend/src/services/posts_service.py`
- `backend/src/routers/posts_router.py`

## 🎯 Subtasks

### 1. 게시글 생성 서비스
- **테스트 함수**: `test_create_post_with_auth`
- **구현 내용**: 인증된 사용자의 게시글 작성
- **검증 항목**: 
  - authorId 자동 설정 (current_user.id)
  - 게시글 데이터 검증 (제목, 내용, 서비스 타입)
  - slug 자동 생성 및 중복 처리
  - 초기 통계 설정 (views: 0, likes: 0 등)
- **테스트 명령어**: `uv run pytest tests/unit/test_posts_service.py::test_create_post_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 2. 게시글 조회 서비스
- **테스트 함수**: `test_get_post`, `test_list_posts_with_user_data`
- **구현 내용**: 단일/목록 조회, 사용자별 개인화 정보 포함
- **검증 항목**:
  - 게시글 상세 조회 (slug 기반)
  - 페이지네이션 목록 조회
  - 사용자별 반응 정보 포함 (로그인한 경우)
  - 조회수 자동 증가
- **테스트 명령어**: `uv run pytest tests/unit/test_posts_service.py::test_get_post tests/unit/test_posts_service.py::test_list_posts_with_user_data -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 3. 게시글 수정/삭제 서비스
- **테스트 함수**: `test_update_post_with_permission`, `test_delete_post_with_permission`
- **구현 내용**: 권한 기반 게시글 수정/삭제
- **검증 항목**:
  - 소유자 권한 확인 (작성자 또는 관리자)
  - 부분 업데이트 지원 (PATCH 방식)
  - 삭제 시 관련 데이터 정리 (댓글, 반응, 통계)
  - 수정 이력 관리 (updatedAt)
- **테스트 명령어**: `uv run pytest tests/unit/test_posts_service.py::test_update_post_with_permission tests/unit/test_posts_service.py::test_delete_post_with_permission -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 4. 게시글 검색 서비스
- **테스트 함수**: `test_search_posts`
- **구현 내용**: 전문 검색 및 필터링
- **검증 항목**:
  - 제목/내용 텍스트 검색
  - 타입별 필터링 (자유게시판, 질문답변 등)
  - 정렬 옵션 (최신순, 인기순, 조회순)
  - 검색 결과 페이지네이션
- **테스트 명령어**: `uv run pytest tests/unit/test_posts_service.py::test_search_posts -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 5. 게시글 API 라우터
- **테스트 함수**: `test_posts_router_with_auth`
- **구현 내용**: RESTful API 엔드포인트
- **검증 항목**:
  - GET /posts (목록 조회)
  - GET /posts/search (검색)
  - GET /posts/{slug} (상세 조회)
  - POST /posts (생성) - 인증 필요
  - PUT /posts/{slug} (수정) - 권한 확인
  - DELETE /posts/{slug} (삭제) - 권한 확인
- **테스트 명령어**: `uv run pytest tests/integration/test_posts_router.py::test_posts_router_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 task 완료 가능

## 🔗 의존성
- **선행 조건**: 
  - Task 1 (데이터베이스 기반)
  - Task 2 (인증/권한 시스템)
- **후행 의존성**: Task 4 (댓글 시스템), Task 5 (반응 시스템)

## 📊 Social Units 및 통합 포인트

### 인증 시스템 통합
- 게시글 작성: `authorId = current_user.id` 자동 설정
- 게시글 수정/삭제: 소유자 권한 확인
- 게시글 조회: 사용자별 반응 정보 포함

### 데이터 모델 연관
- Post ↔ User (작성자 관계)
- Post ↔ PostStats (통계 정보)
- Post ↔ UserReactions (사용자 반응)

## 🎯 API 명세 준수
- **게시글 목록**: GET /api/posts (쿼리 파라미터: type, page, limit, sortBy)
- **게시글 검색**: GET /api/posts/search (쿼리 파라미터: q, type, page)
- **게시글 상세**: GET /api/posts/{slug}
- **게시글 생성**: POST /api/posts (인증 필요)
- **게시글 수정**: PUT /api/posts/{slug} (권한 확인)
- **게시글 삭제**: DELETE /api/posts/{slug} (권한 확인)

## ✅ 완료 조건

### 개별 Subtask 검증 (순차 진행 필수)
```bash
# Subtask 1: 게시글 생성 서비스
uv run pytest tests/unit/test_posts_service.py::test_create_post_with_auth -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 2: 게시글 조회 서비스
uv run pytest tests/unit/test_posts_service.py::test_get_post tests/unit/test_posts_service.py::test_list_posts_with_user_data -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 3: 게시글 수정/삭제 서비스
uv run pytest tests/unit/test_posts_service.py::test_update_post_with_permission tests/unit/test_posts_service.py::test_delete_post_with_permission -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 4: 게시글 검색 서비스
uv run pytest tests/unit/test_posts_service.py::test_search_posts -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 5: 게시글 API 라우터
uv run pytest tests/integration/test_posts_router.py::test_posts_router_with_auth -v
# ↑ exit code 0 확인 후 task 완료
```

### Task 전체 성공 판단
```bash
# 모든 subtask 테스트 한번에 실행 (모든 subtask 개별 통과 후)
uv run pytest tests/unit/test_posts_service.py tests/integration/test_posts_router.py -v

# 또는 posts 관련 테스트 전체 실행
uv run pytest tests/ -k "posts" -v
```

**성공 기준**:
- [ ] 모든 subtask 테스트가 순차적으로 exit code 0으로 통과
- [ ] 어떤 이유든 테스트 실패 시 해당 subtask 실패로 간주
- [ ] 이전 subtask 통과 없이 다음 subtask 진행 금지
- [ ] 모든 subtask 완료 후에만 다음 task 진행 가능
- [ ] Task 1, 2 선행 완료 필수

**실패 처리**:
- 네트워크, 환경 설정, 외부 의존성 등 어떤 이유든 테스트 실패 시 subtask 실패
- 실패한 subtask는 문제 해결 후 재테스트 필요
- 순차 진행 원칙 준수 (이전 subtask 성공 후 다음 진행)