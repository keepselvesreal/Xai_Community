# FastAPI Docs에서 새로운 문의/신고 기능 테스트 가이드

**작성일**: 2025-07-18  
**작성자**: Claude Code  
**프로젝트**: XAI Community v5 백엔드  
**구현 기능**: 새로운 문의/신고 시스템 (TDD 구현 완료)

## 🎯 개요

이 가이드는 FastAPI의 `/docs` 페이지에서 새로 구현된 4가지 문의/신고 기능을 테스트하는 방법을 설명합니다.

## 🔗 접속 방법

1. 백엔드 서버 실행: `uv run uvicorn main:app --reload`
2. 브라우저에서 접속: `http://localhost:8000/docs`

## 📋 새로운 문의/신고 타입들

### 1. **입주 서비스 업체 등록 문의** (`moving-services-register-inquiry`)
### 2. **전문가 꿀정보 등록 문의** (`expert-tips-register-inquiry`)
### 3. **건의함** (`suggestions`)
### 4. **신고** (`report`)

## 🧪 테스트 방법

### 1. 입주 서비스 업체 등록 문의 테스트

**엔드포인트**: `POST /posts/`

**요청 JSON 예시**:
```json
{
  "title": "입주 서비스 업체 등록 문의",
  "content": "{\"content\": \"저희 ABC 이사업체를 플랫폼에 등록하고 싶습니다. 15년 경력의 전문 이사 서비스를 제공하고 있습니다.\", \"contact\": \"010-1234-5678\", \"website_url\": \"https://abc-moving.com\"}",
  "service": "residential_community",
  "metadata": {
    "type": "moving-services-register-inquiry",
    "editor_type": "plain"
  }
}
```

### 2. 전문가 꿀정보 등록 문의 테스트

**엔드포인트**: `POST /posts/`

**요청 JSON 예시**:
```json
{
  "title": "전문가 꿀정보 등록 문의",
  "content": "{\"content\": \"10년 경력의 부동산 전문가입니다. 입주 관련 꿀정보를 공유하고 싶어서 문의드립니다.\", \"contact\": \"010-9876-5432\", \"website_url\": \"https://realestate-expert.com\"}",
  "service": "residential_community",
  "metadata": {
    "type": "expert-tips-register-inquiry",
    "editor_type": "plain"
  }
}
```

### 3. 건의함 테스트

**엔드포인트**: `POST /posts/`

**요청 JSON 예시**:
```json
{
  "title": "앱 개선 건의사항",
  "content": "{\"content\": \"앱에 다크모드 기능을 추가해주시면 좋겠습니다. 밤에 사용할 때 눈이 피로해요.\"}",
  "service": "residential_community",
  "metadata": {
    "type": "suggestions",
    "editor_type": "plain"
  }
}
```

### 4. 신고 테스트

**엔드포인트**: `POST /posts/`

**요청 JSON 예시**:
```json
{
  "title": "부적절한 게시물 신고",
  "content": "{\"content\": \"게시판에 스팸성 광고 게시물이 지속적으로 올라오고 있습니다. 확인해주세요.\"}",
  "service": "residential_community",
  "metadata": {
    "type": "report",
    "editor_type": "plain"
  }
}
```

## 🔍 익명 사용자 테스트

### 인증 토큰 없이 테스트하기

1. **Authorize 버튼을 클릭하지 않고** 바로 테스트
2. 또는 이미 로그인된 상태라면 **Logout** 후 테스트
3. 익명 사용자의 경우 `author_id`가 `anonymous_xxxxxxxxx` 형태로 자동 생성됨

### 인증된 사용자로 테스트하기

1. **Authorize 버튼 클릭**
2. JWT 토큰 입력 (형식: `Bearer your_jwt_token`)
3. 인증된 상태에서 게시글 작성

## 📊 응답 확인 사항

### 성공적인 응답 예시
```json
{
  "id": "507f1f77bcf86cd799439012",
  "title": "입주 서비스 업체 등록 문의",
  "content": "{\"content\": \"저희 ABC 이사업체를...\", \"contact\": \"010-1234-5678\", \"website_url\": \"https://abc-moving.com\"}",
  "slug": "입주-서비스-업체-등록-문의-abc123",
  "author_id": "anonymous_1a2b3c4d5e6f7890",
  "service": "residential_community",
  "metadata": {
    "type": "moving-services-register-inquiry",
    "editor_type": "plain",
    "visibility": "public"
  },
  "status": "published",
  "created_at": "2025-07-18T11:30:00Z"
}
```

## 🔎 생성된 게시글 조회 테스트

### 1. 전체 목록에서 확인

**엔드포인트**: `GET /posts/`

**파라미터**:
- `metadata_type`: `moving-services-register-inquiry` (또는 다른 타입)
- `page`: 1
- `page_size`: 20

### 2. 개별 게시글 조회

**엔드포인트**: `GET /posts/{slug}`

생성된 게시글의 `slug` 값을 사용하여 상세 조회

## ⚠️ 오류 케이스 테스트

### 1. 잘못된 JSON 형태 테스트

**잘못된 예시**:
```json
{
  "title": "테스트",
  "content": "그냥 텍스트",  // JSON이 아님
  "service": "residential_community",
  "metadata": {
    "type": "moving-services-register-inquiry"
  }
}
```

**예상 응답**: `422 Validation Error` - "Content must be valid JSON for moving-services-register-inquiry"

### 2. 필수 필드 누락 테스트

**잘못된 예시**:
```json
{
  "title": "테스트",
  "content": "{\"content\": \"내용만 있음\"}",  // contact, website_url 누락
  "service": "residential_community",
  "metadata": {
    "type": "moving-services-register-inquiry"
  }
}
```

**예상 응답**: `422 Validation Error` - "Missing required 'contact' field"

## 🎉 성공 기준

✅ **성공적인 테스트 완료 시 확인사항**:

1. 4가지 타입 모두 성공적으로 생성됨
2. 익명 사용자와 인증된 사용자 모두 테스트 완료
3. 생성된 게시글이 목록에서 조회됨
4. Content 필드가 올바른 JSON 구조로 저장됨
5. 오류 케이스에서 적절한 검증 메시지 출력

## 📝 추가 확인사항

- **Database 확인**: MongoDB에서 실제 데이터 저장 확인
- **캐싱 확인**: Redis에서 캐시 데이터 확인
- **로그 확인**: 서버 로그에서 처리 과정 확인

## 📋 구현 완료 사항 (TDD)

### ✅ 완료된 기능들

1. **TDD 테스트 케이스**: 8개의 새로운 테스트 작성 및 통과
2. **새로운 타입 정의**: 4개의 문의/신고 타입 추가 (core.py)
3. **익명 사용자 지원**: 임시 ID 자동 생성 로직 (`anonymous_xxxxxxxxx`)
4. **JSON 구조 검증**: 타입별 content 필드 검증 로직
5. **서비스 로직 확장**: PostsService에 새로운 기능 통합

### 🧪 통과된 테스트들

- `test_create_moving_services_inquiry`
- `test_create_expert_tips_inquiry`  
- `test_create_suggestions`
- `test_create_report`
- `test_create_inquiry_anonymous_user`
- `test_anonymous_author_id_generation`
- `test_content_field_json_validation_for_inquiries`
- `test_content_field_json_validation_for_suggestions_and_reports`

### 📂 수정된 파일들

1. **`nadle_backend/models/core.py`**: 새로운 타입 정의 추가
2. **`nadle_backend/services/posts_service.py`**: 
   - 익명 사용자 ID 생성 로직
   - JSON content 검증 로직
   - 새로운 타입 처리 로직
3. **`tests/unit/test_posts_service.py`**: 8개의 새로운 테스트 케이스

---

💡 **Tip**: 각 테스트 후 다른 타입으로 연속 테스트할 때는 `title`을 다르게 설정하여 구분하기 쉽게 만드세요!

**다음 단계**: 프론트엔드 공통 모달 컴포넌트 구현