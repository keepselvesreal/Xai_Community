# KST(한국 표준시) 마이그레이션 가이드

## 개요
이 문서는 UTC 기반 시간 저장에서 KST(한국 표준시) 기반 시간 저장으로의 마이그레이션 과정을 설명합니다.

## 변경 사항

### 1. 백엔드 모델 변경
- **파일**: `backend/nadle_backend/models/core.py`
- **변경 내용**: 모든 `datetime.utcnow` → `get_kst_now`로 변경
- **영향받는 필드**:
  - `created_at`, `updated_at` (모든 모델)
  - `last_login` (User)
  - `published_at`, `resolved_at` (Post)
  - `last_viewed_at` (UserStatistics)
  - `upload_timestamp` (FileMetadata)
  - `last_calculated`, `last_updated` (UserStatistics)

### 2. 서비스 레이어 변경
- **파일들**:
  - `backend/nadle_backend/services/posts_service.py`
  - `backend/nadle_backend/services/auth_service.py`
  - `backend/nadle_backend/services/admin_service.py`
- **변경 내용**: `datetime.utcnow()`, `datetime.now()` → `get_kst_now()`

### 3. 새로운 유틸리티 함수
- **파일**: `backend/nadle_backend/utils/timezone.py`
- **주요 함수**:
  - `get_kst_now()`: 현재 한국 시간 반환
  - `utc_to_kst()`: UTC를 KST로 변환
  - `kst_to_utc()`: KST를 UTC로 변환

## 마이그레이션 절차

### 1. 미리보기 (권장)
```bash
cd backend
uv run python ../scripts/database/test_migration_preview.py
```
실제 변경 없이 변환될 데이터를 미리 확인할 수 있습니다.

### 2. 백업
프로덕션 데이터베이스를 반드시 백업하세요.

### 3. 마이그레이션 실행
```bash
cd backend
# 개발 환경
ENVIRONMENT=development uv run python ../scripts/database/migrate_utc_to_kst.py

# 스테이징 환경
ENVIRONMENT=staging uv run python ../scripts/database/migrate_utc_to_kst.py

# 프로덕션 환경 (주의!)
ENVIRONMENT=production uv run python ../scripts/database/migrate_utc_to_kst.py
```

### 4. 검증
- 새로운 게시글/댓글 작성 시 올바른 한국 시간으로 저장되는지 확인
- 기존 데이터가 정상적으로 표시되는지 확인

## 테스트 관련 주의사항

다음 테스트 파일들은 시간대 변경에 영향을 받을 수 있으므로 수정이 필요할 수 있습니다:
- `test_email_verification_model.py` - 만료 시간 검증
- `test_jwt.py` - JWT 토큰 만료 시간
- `test_token_blacklist.py` - 토큰 블랙리스트 만료
- `test_admin_service.py` - 문의 해결 시간
- 기타 `datetime.utcnow()` 사용 테스트들

## 롤백 절차

문제 발생 시:
1. 백업된 데이터베이스 복원
2. 코드를 이전 커밋으로 되돌리기
3. 서버 재시작

## 프론트엔드 영향

프론트엔드는 이미 KST로 변환하여 표시하고 있으므로 변경 불필요:
- `formatDate()` 함수: 이미 `Asia/Seoul` 타임존 사용
- `formatRelativeTime()` 함수: 정상 작동

## 모니터링

마이그레이션 후 다음 사항들을 모니터링하세요:
- 새 게시글/댓글의 작성 시간
- 사용자 로그인 시간
- 파일 업로드 시간
- API 응답의 시간 필드들

## 문의

문제 발생 시 개발팀에 연락하세요.