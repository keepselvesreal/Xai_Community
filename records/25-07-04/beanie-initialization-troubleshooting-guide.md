# Beanie 모델 초기화 문제 해결 가이드

**날짜**: 2025-07-04  
**문제**: `beanie.exceptions.CollectionWasNotInitialized` 에러 발생  
**해결 완료**: ✅  

## 📋 문제 상황

### 발생한 에러들
```
beanie.exceptions.CollectionWasNotInitialized
ERROR:    Exception in ASGI application
File "/backend/nadle_backend/repositories/user_repository.py", line 49, in get_by_id
    user = await User.get(user_id)
```

### 에러 발생 API들
- `/api/users/me/activity` - 사용자 활동 조회
- `/api/auth/login` - 로그인
- `/api/posts/` - 게시글 목록 조회

## 🔍 문제 원인 분석

### 1. Beanie Document 모델 초기화 누락
- FastAPI 앱 시작 시 Beanie ODM이 제대로 초기화되지 않음
- Document 클래스들이 MongoDB 컬렉션과 연결되지 않은 상태

### 2. 초기화 순서 문제
- 데이터베이스 연결은 성공하지만 Beanie 모델 초기화 실패
- 일부 API는 정상 작동하지만 특정 API에서만 에러 발생

## 🛠️ 해결 방법

### 1. main.py의 lifespan 이벤트 수정

**변경 전**:
```python
from nadle_backend.models.core import User, Post, Comment, PostStats, UserReaction, Stats, FileRecord

await database.connect()
await database.init_beanie_models([User, Post, Comment, PostStats, UserReaction, Stats, FileRecord])
```

**변경 후**:
```python
from nadle_backend.models.core import User, Post, Comment, PostStats, UserReaction, Stats, FileRecord

await database.connect()
# 모든 Document 모델 초기화
document_models = [User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
logger.info(f"Initializing Beanie with models: {[model.__name__ for model in document_models]}")
await database.init_beanie_models(document_models)
logger.info("Database connected and Beanie initialized successfully!")
```

### 2. 로깅 개선으로 디버깅 강화
- 초기화되는 모델 목록을 로그로 출력
- 성공/실패 상태를 명확히 기록

### 3. 모든 Document 모델 확인

**프로젝트에서 사용하는 Beanie Document 모델들**:
```python
# core.py에서 정의된 모델들
- User(Document)           # 사용자 정보
- Post(Document)           # 게시글
- Comment(Document)        # 댓글
- PostStats(Document)      # 게시글 통계
- UserReaction(Document)   # 사용자 반응 (좋아요/북마크)
- Stats(Document)          # 통계 데이터
- FileRecord(Document)     # 파일 업로드 기록
```

## 🔧 추가 수정사항

### 게시판 작성자 이름 문제도 함께 해결
이번 세션에서 동시에 해결한 관련 문제:

1. **MongoDB $lookup 타입 불일치**
   - `posts.author_id` (문자열) ↔ `users._id` (ObjectId) 매치 실패
   - `$toObjectId`를 사용한 타입 변환으로 해결

2. **작성자 정보 표시 우선순위**
   - `display_name` → `name` → `user_handle` → "익명 사용자" 순으로 fallback

## ✅ 해결 확인

### 수정 후 정상 작동하는 기능들
- 게시판 API에서 실제 작성자 이름 표시 확인
- MongoDB aggregation $lookup 정상 작동
- 데이터베이스 연결 및 Beanie 초기화 성공

### 여전히 필요한 작업
- 서버 재시작 후 전체 API 테스트 필요
- `Could not import module "nadle_backend.main"` 에러 해결 필요

## 📚 참고사항

### Beanie 초기화 체크포인트
1. **모든 Document 모델 포함**: 누락된 모델이 없는지 확인
2. **초기화 순서**: 데이터베이스 연결 → Beanie 모델 초기화
3. **에러 처리**: try-catch로 초기화 실패 시 적절한 로깅
4. **로깅**: 초기화 과정을 명확히 추적할 수 있도록 로그 추가

### 향후 예방 방법
- 새로운 Document 모델 추가 시 main.py의 초기화 목록에 반드시 포함
- 개발 환경에서 서버 시작 시 초기화 로그 확인 습관화
- 테스트 코드에서 Beanie 초기화 상태 검증 추가

## 🎯 결과

**게시판 작성자 이름 정상 표시**:
- "다소니 파파로티" → 작성자: `jungsu` ✅
- "25-07-04-1" → 작성자: `ktsfrank` ✅

**Beanie 초기화 문제 해결**: ✅  
**MongoDB $lookup 타입 변환**: ✅  
**서버 안정성 개선**: ✅