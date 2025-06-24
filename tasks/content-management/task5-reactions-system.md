# Task 5: 반응 시스템 완전 구현

**Feature Group**: Content Management  
**Task List 제목**: 반응 시스템 완전 구현  
**최초 작성 시각**: 2024-12-19 15:30:00

## 📋 Task 개요

### 리스크 레벨: 높음
- **이유**: 복잡한 상태 전환 로직, 동시성 이슈 가능성, 실시간 통계 업데이트
- **대응**: 상태 다이어그램 기반 테스트, 트랜잭션 처리, 원자성 보장

### 대상 파일
- `backend/src/models/reaction.py`
- `backend/src/repositories/reaction_repository.py`
- `backend/src/services/reactions_service.py`
- `backend/src/routers/reactions_router.py` (posts_router.py 내 통합)

## 🎯 Subtasks

### 1. 좋아요/싫어요 토글 로직
- **테스트 함수**: `test_like_toggle_with_auth`, `test_dislike_toggle_with_auth`
- **구현 내용**: 복잡한 상태 전환을 처리하는 토글 시스템
- **검증 항목**:
  - 좋아요 상태 전환: 없음 → 좋아요 → 없음
  - 싫어요 상태 전환: 없음 → 싫어요 → 없음
  - 상호 배타적 처리: 좋아요 ↔ 싫어요 전환
  - 사용자별 중복 반응 방지
  - 실시간 카운트 업데이트
- **테스트 명령어**: `uv run pytest tests/unit/test_reactions_service.py::test_like_toggle_with_auth tests/unit/test_reactions_service.py::test_dislike_toggle_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 2. 북마크 시스템
- **테스트 함수**: `test_bookmark_toggle_with_auth`
- **구현 내용**: 독립적인 북마크 토글 시스템
- **검증 항목**:
  - 북마크 상태 전환: 없음 → 북마크 → 없음
  - 다른 반응과 독립적 동작 (좋아요/싫어요와 별개)
  - 사용자별 북마크 목록 관리
  - 북마크 카운트 실시간 업데이트
- **테스트 명령어**: `uv run pytest tests/unit/test_reactions_service.py::test_bookmark_toggle_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 3. 통계 집계 및 업데이트
- **테스트 함수**: `test_stats_aggregation`
- **구현 내용**: 원자적 통계 업데이트 시스템
- **검증 항목**:
  - PostStats 컬렉션 실시간 업데이트
  - 동시 접근 시 데이터 일관성 보장
  - 카운트 정확성 (음수 방지, 최대값 제한)
  - 배치 통계 재계산 기능
  - 성능 최적화 (불필요한 DB 호출 방지)
- **테스트 명령어**: `uv run pytest tests/unit/test_reactions_service.py::test_stats_aggregation -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 다음 subtask 진행 가능

### 4. 반응 API 라우터
- **테스트 함수**: `test_reactions_router_with_auth`
- **구현 내용**: 직관적인 토글 API 엔드포인트
- **검증 항목**:
  - POST /posts/{slug}/like (좋아요 토글)
  - POST /posts/{slug}/dislike (싫어요 토글)
  - POST /posts/{slug}/bookmark (북마크 토글)
  - GET /posts/{slug}/stats (통계 조회)
  - 일관된 응답 형식 (action, counts, userReaction)
- **테스트 명령어**: `uv run pytest tests/integration/test_reactions_router.py::test_reactions_router_with_auth -v`
- **성공 기준**: 테스트 명령어 실행 시 exit code 0 (어떤 이유든 실패 시 subtask 실패로 간주)
- **진행 조건**: 이 subtask 테스트 통과 후에만 task 완료 가능

## 🔗 의존성
- **선행 조건**: 
  - Task 1 (데이터베이스 기반)
  - Task 2 (인증/권한 시스템)
  - Task 3 (게시글 시스템)
- **후행 의존성**: 없음 (독립적 기능)

## 📊 Social Units 및 통합 포인트

### 게시글 시스템 통합
- 게시글 조회 시 통계 정보 포함
- 게시글 상세 페이지에서 사용자별 반응 상태 표시
- 게시글 삭제 시 모든 반응 데이터 정리

### 인증 시스템 통합
- 모든 반응 기능은 로그인 사용자만 접근 가능
- 사용자별 반응 상태 관리
- 사용자 삭제 시 반응 기록 정리

## 🎯 상태 전환 다이어그램

### 좋아요/싫어요 상태 전환
```
없음 ←→ 좋아요
 ↕      ↕
싫어요 ←→ (상호 배타적)
```

### 북마크 상태 전환
```
없음 ←→ 북마크 (독립적)
```

## 🔄 API 응답 형식
```json
{
  "action": "liked", // liked, unliked, disliked, undisliked, bookmarked, unbookmarked
  "likeCount": 15,
  "dislikeCount": 2,
  "bookmarkCount": 8,
  "userReaction": {
    "liked": true,
    "disliked": false,
    "bookmarked": false
  }
}
```

## ⚡ 성능 최적화 전략
- **원자적 업데이트**: MongoDB의 $inc 연산자 활용
- **중복 처리 방지**: 유니크 인덱스 활용
- **배치 처리**: 대량 통계 업데이트 시 배치 연산
- **캐싱 전략**: 인기 게시글 통계 캐싱 (향후 확장)

## 🛡️ 동시성 및 일관성 보장
- UserReactions 컬렉션의 userId + postId 유니크 제약
- 낙관적 잠금을 통한 동시 수정 처리
- 트랜잭션을 통한 반응 상태와 통계의 원자적 업데이트

## ✅ 완료 조건

### 개별 Subtask 검증 (순차 진행 필수)
```bash
# Subtask 1: 좋아요/싫어요 토글 로직
uv run pytest tests/unit/test_reactions_service.py::test_like_toggle_with_auth tests/unit/test_reactions_service.py::test_dislike_toggle_with_auth -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 2: 북마크 시스템
uv run pytest tests/unit/test_reactions_service.py::test_bookmark_toggle_with_auth -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 3: 통계 집계 및 업데이트
uv run pytest tests/unit/test_reactions_service.py::test_stats_aggregation -v
# ↑ exit code 0 확인 후 다음 진행

# Subtask 4: 반응 API 라우터
uv run pytest tests/integration/test_reactions_router.py::test_reactions_router_with_auth -v
# ↑ exit code 0 확인 후 task 완료
```

### Task 전체 성공 판단
```bash
# 모든 subtask 테스트 한번에 실행 (모든 subtask 개별 통과 후)
uv run pytest tests/unit/test_reactions_service.py tests/integration/test_reactions_router.py -v

# 또는 reactions 관련 테스트 전체 실행
uv run pytest tests/ -k "reactions" -v
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
- 상태 전환 복잡성과 동시성 이슈 주의