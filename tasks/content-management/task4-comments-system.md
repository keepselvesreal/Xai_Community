# Task 4: 댓글 기능 완전 구현

**Feature Group**: Content Management  
**Task List 제목**: 댓글 기능 완전 구현  
**최초 작성 시각**: 2024-12-19 15:30:00

## 📋 Task 개요

### 리스크 레벨: 중간
- **이유**: 게시글 + 인증 의존성, 계층형 데이터 구조
- **대응**: 대댓글 로직 단계별 구현, 무한 깊이 방지

### 대상 파일
- `backend/src/models/comment.py`
- `backend/src/repositories/comment_repository.py`
- `backend/src/services/comments_service.py`
- `backend/src/routers/comments_router.py`

## 🎯 Subtasks

### 1. 댓글 생성 서비스
- **테스트 함수**: `test_create_comment_with_auth`
- **구현 내용**: 인증된 사용자의 댓글 작성
- **검증 항목**:
  - authorId 자동 설정 (current_user.id)
  - parentId 설정 (게시글 연결)
  - parentCommentId 설정 (대댓글인 경우)
  - 댓글 내용 검증 (최소/최대 길이)
  - 게시글 댓글 수 자동 증가
- **테스트 명령어**: `uv run pytest tests/unit/test_comments_service.py::test_create_comment_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 2. 댓글 조회 서비스
- **테스트 함수**: `test_get_comments_with_user_data`
- **구현 내용**: 게시글별 댓글 목록 조회, 사용자 정보 포함
- **검증 항목**:
  - 게시글별 댓글 페이지네이션
  - 계층형 구조 (댓글 → 대댓글)
  - 사용자별 좋아요 정보 포함 (로그인한 경우)
  - 댓글 상태별 필터링 (active/deleted)
  - 정렬 옵션 (시간순, 좋아요순)
- **테스트 명령어**: `uv run pytest tests/unit/test_comments_service.py::test_get_comments_with_user_data -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 3. 대댓글 처리 서비스
- **테스트 함수**: `test_reply_comments`
- **구현 내용**: 대댓글 작성 및 계층 구조 관리
- **검증 항목**:
  - parentCommentId 유효성 확인
  - 대댓글 깊이 제한 (최대 2단계)
  - 상위 댓글의 replyCount 자동 증가
  - 대댓글 알림 처리 (향후 확장)
- **테스트 명령어**: `uv run pytest tests/unit/test_comments_service.py::test_reply_comments -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 4. 댓글 수정/삭제 서비스
- **테스트 함수**: `test_update_comment_with_permission`, `test_delete_comment_with_permission`
- **구현 내용**: 권한 기반 댓글 수정/삭제
- **검증 항목**:
  - 소유자 권한 확인 (작성자 또는 관리자)
  - 댓글 내용 수정 (부분 업데이트)
  - 소프트 삭제 (status를 'deleted'로 변경)
  - 대댓글이 있는 댓글 삭제 처리
  - 게시글 댓글 수 자동 감소
- **테스트 명령어**: `uv run pytest tests/unit/test_comments_service.py::test_update_comment_with_permission tests/unit/test_comments_service.py::test_delete_comment_with_permission -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 5. 댓글 API 라우터
- **테스트 함수**: `test_comments_router_with_auth`
- **구현 내용**: 게시글 하위 리소스 API
- **검증 항목**:
  - GET /posts/{slug}/comments (목록 조회)
  - POST /posts/{slug}/comments (댓글 생성) - 인증 필요
  - POST /posts/{slug}/comments/{comment_id}/replies (대댓글 생성) - 인증 필요
  - PUT /posts/{slug}/comments/{comment_id} (수정) - 권한 확인
  - DELETE /posts/{slug}/comments/{comment_id} (삭제) - 권한 확인
- **테스트 명령어**: `uv run pytest tests/integration/test_comments_router.py::test_comments_router_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 task 완료 가능

## 🔗 의존성
- **선행 조건**: 
  - Task 1 (데이터베이스 기반)
  - Task 2 (인증/권한 시스템)
  - Task 3 (게시글 시스템)
- **후행 의존성**: Task 5 (반응 시스템 - 댓글 좋아요)

## 📊 Social Units 및 통합 포인트

### 게시글 시스템 통합
- 댓글 작성 시 게시글 댓글 수 증가
- 댓글 삭제 시 게시글 댓글 수 감소
- 게시글 삭제 시 모든 댓글 정리

### 인증 시스템 통합
- 댓글 작성: `authorId = current_user.id` 자동 설정
- 댓글 수정/삭제: 소유자 권한 확인
- 댓글 조회: 사용자별 좋아요 정보 포함

### 데이터 모델 연관
- Comment ↔ Post (게시글 관계)
- Comment ↔ User (작성자 관계)
- Comment ↔ Comment (대댓글 관계)

## 🎯 API 명세 준수
- **댓글 목록**: GET /api/posts/{slug}/comments
- **댓글 생성**: POST /api/posts/{slug}/comments (인증 필요)
- **대댓글 생성**: POST /api/posts/{slug}/comments/{comment_id}/replies (인증 필요)
- **댓글 수정**: PUT /api/posts/{slug}/comments/{comment_id} (권한 확인)
- **댓글 삭제**: DELETE /api/posts/{slug}/comments/{comment_id} (권한 확인)
- **댓글 좋아요**: POST /api/posts/{slug}/comments/{comment_id}/like (인증 필요)

## 🗂️ 계층형 구조 처리
```json
{
  "comments": [
    {
      "id": "comment1",
      "content": "댓글 내용",
      "replies": [
        {
          "id": "reply1", 
          "content": "대댓글 내용",
          "parentCommentId": "comment1"
        }
      ]
    }
  ]
}
```

## ✅ 완료 조건

### 개별 Subtask 검증 (순차 진행 필수)
```bash
# Subtask 1: 댓글 생성 서비스
uv run pytest tests/unit/test_comments_service.py::test_create_comment_with_auth -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 2: 댓글 조회 서비스
uv run pytest tests/unit/test_comments_service.py::test_get_comments_with_user_data -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 3: 대댓글 처리 서비스
uv run pytest tests/unit/test_comments_service.py::test_reply_comments -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 4: 댓글 수정/삭제 서비스
uv run pytest tests/unit/test_comments_service.py::test_update_comment_with_permission tests/unit/test_comments_service.py::test_delete_comment_with_permission -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 5: 댓글 API 라우터
uv run pytest tests/integration/test_comments_router.py::test_comments_router_with_auth -v
# ↑ exit code 0 확인 후 task 완료
```

### Task 전체 성공 판단
```bash
# 모든 subtask 테스트 한번에 실행 (모든 subtask 개별 통과 후)
uv run pytest tests/unit/test_comments_service.py tests/integration/test_comments_router.py -v

# 또는 comments 관련 테스트 전체 실행
uv run pytest tests/ -k "comments" -v
```

**성공 기준**:
- [ ] 모든 subtask 테스트가 순차적으로 exit code 0으로 통과
- [ ] 어떤 이유든 테스트 실패 시 해당 subtask 실패로 간주
- [ ] 이전 subtask 통과 없이 다음 subtask 진행 금지
- [ ] 모든 subtask 완료 후에만 다음 task 진행 가능
- [ ] Task 1, 2, 3 선행 완료 필수

**실패 처리**:
- 네트워크, 환경 설정, 외부 의존성 등 어떤 이유든 테스트 실패 시 subtask 실패
- 실패한 subtask는 문제 해결 후 재테스트 필요
- 순차 진행 원칙 준수 (이전 subtask 성공 후 다음 진행)