# 파일 API 테스트 코드 제안 개요

## 📋 문서 개요

파일 API 구현을 위한 체계적인 테스트 코드 제안서입니다. TDD 원칙을 준수하며 실제 사용자 플로우 중심의 테스트 구성을 제시합니다.

---

## 1. 테스트 모듈 구조 및 의존성 관계

### 테스트 모듈 계층 구조

```
backend/tests/
├── unit/
│   ├── test_file_validator.py       # 🔵 기반 (의존성 없음)
│   │   ├── test_validate_file_type() 🟢 초급 ⚡병렬
│   │   ├── test_validate_file_size() 🟢 초급 ⚡병렬
│   │   ├── test_validate_malicious_file() 🔴 고급 ⚡병렬
│   │   └── test_validate_rate_limit() 🟡 중급 🔄순차
│   ├── test_file_storage.py         # 🟡 조합 (validator 의존)
│   │   ├── test_generate_file_path() 🟢 초급 ⚡병렬
│   │   ├── test_save_file_to_disk() 🟡 중급 🔄순차
│   │   ├── test_cleanup_temp_files() 🟡 중급 🔄순차
│   │   └── test_handle_storage_errors() 🟡 중급 🔄순차
│   └── test_file_metadata.py        # 🔵 기반 (의존성 없음)
│       ├── test_extract_file_info() 🟢 초급 ⚡병렬
│       ├── test_generate_stored_filename() 🟢 초급 ⚡병렬
│       └── test_create_file_document() 🟡 중급 ⚡병렬
├── integration/
│   ├── test_file_upload_api.py      # 🔴 통합 (모든 기능 의존)
│   │   ├── test_successful_upload_flow() 🔴 고급 🔄순차
│   │   ├── test_upload_with_post_attachment() 🔴 고급 🔄순차
│   │   ├── test_multiple_files_upload() 🔴 고급 🔄순차
│   │   └── test_upload_error_scenarios() 🟡 중급 🔄순차
│   ├── test_file_retrieval_api.py   # 🟡 조합 (storage 의존)
│   │   ├── test_get_file_by_id() 🟡 중급 🔄순차
│   │   ├── test_get_file_metadata() 🟡 중급 🔄순차
│   │   └── test_get_files_by_post() 🟡 중급 🔄순차
│   └── test_file_deletion_api.py    # 🔴 통합 (모든 기능 의존)
│       ├── test_delete_file_success() 🔴 고급 🔄순차
│       ├── test_delete_unauthorized() 🟡 중급 🔄순차
│       └── test_cleanup_references() 🔴 고급 🔄순차
└── contract/
    └── test_file_api_contract.py    # 🟠 계약 (API 의존)
        ├── test_upload_request_contract() 🟢 초급 🔄순차
        ├── test_upload_response_contract() 🟢 초급 🔄순차
        └── test_error_response_contract() 🟢 초급 🔄순차
```

### 의존성 그래프

```
┌─────────────────────── 테스트 모듈 의존성 그래프 ────────────────────────┐
│                                                                      │
│  🔵 기반 계층 (독립적)                                                   │
│  ┌─────────────────┐    ┌─────────────────┐                          │
│  │ test_file_      │    │ test_file_      │                          │
│  │ validator.py    │    │ metadata.py     │                          │
│  └─────────────────┘    └─────────────────┘                          │
│           │                       │                                  │
│           └───────┬───────────────┘                                  │
│                   ▼                                                  │
│  🟡 조합 계층 (기반 기능 활용)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_file_      │                                                 │
│  │ storage.py      │                                                 │
│  └─────────────────┘                                                 │
│           │                                                          │
│           ▼                                                          │
│  🔴 통합 계층 (모든 기능 통합)                                           │
│  ┌─────────────────┐    ┌─────────────────┐                          │
│  │ test_file_      │    │ test_file_      │                          │
│  │ upload_api.py   │    │ deletion_api.py │                          │
│  └─────────────────┘    └─────────────────┘                          │
│           │                       │                                  │
│           └───────┬───────────────┘                                  │
│                   ▼                                                  │
│  🟠 계약 계층 (API 인터페이스)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_file_api_  │                                                 │
│  │ contract.py     │                                                 │
│  └─────────────────┘                                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. 기능 플로우와 테스트 함수 매핑

### 파일 업로드 플로우

```
┌──────────────────────── 파일 업로드 플로우 ────────────────────────┐
│                                                                │
│  🌐 요청 → 🔐 인증 → 🔍 검증 → 💾 저장 → 📝 DB기록 → 🔗 연결 → 📤 응답  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**각 단계별 테스트 함수 매핑:**

- **🌐 사용자 요청 단계**:
  - `test_multipart_form_parsing()` - multipart/form-data 파싱
  - `test_upload_request_contract()` - API 요청 형식 검증

- **🔐 인증 단계**:
  - `test_bearer_token_validation()` - JWT 토큰 검증
  - `test_unauthorized_upload_rejection()` - 미인증 요청 거부

- **🔍 입력 검증 단계**:
  - `test_validate_file_type()` - 파일 형식 검증 (MIME + 확장자)
  - `test_validate_file_size()` - 파일 크기 제한 검증
  - `test_validate_malicious_file()` - 악성 파일 차단
  - `test_validate_rate_limit()` - 업로드 빈도 제한

- **💾 저장 단계**:
  - `test_generate_file_path()` - 파일 경로 생성
  - `test_save_file_to_disk()` - 실제 파일 저장
  - `test_create_directory_structure()` - 디렉토리 생성

- **📝 DB 기록 단계**:
  - `test_create_file_document()` - 파일 메타데이터 생성
  - `test_insert_file_metadata()` - MongoDB 문서 저장

- **🔗 연결 단계**:
  - `test_attach_to_post()` - 게시글에 파일 연결
  - `test_attach_to_comment()` - 댓글에 파일 연결

- **📤 응답 단계**:
  - `test_upload_response_contract()` - API 응답 형식 검증
  - `test_success_response_format()` - 성공 응답 구조

### 파일 조회 플로우

```
┌──────────────────────── 파일 조회 플로우 ────────────────────────┐
│                                                              │
│  🌐 요청 → 🔍 ID검증 → 📝 DB조회 → 📁 파일확인 → 📤 파일반환     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**각 단계별 테스트 함수:**

- **🔍 ID 검증**: `test_validate_file_id()`
- **📝 DB 조회**: `test_get_file_metadata()`
- **📁 파일 확인**: `test_check_file_exists()`
- **📤 파일 반환**: `test_serve_file_response()`

---

## 3. 사용자 시나리오별 테스트 매핑

### 🌟 주 시나리오 (Happy Path)

```
┌─────────────── 주 시나리오: 게시글 작성 시 이미지 첨부 ────────────────┐
│                                                                  │
│  시나리오: 사용자가 게시글 작성 시 이미지 3개 첨부                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. 로그인 → 2. 게시글 작성 페이지 → 3. 이미지 선택 (3개)      │ │
│  │ 4. 파일 업로드 → 5. 게시글 내용 작성 → 6. 게시글 저장         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  관련 테스트:                                                    │
│  • test_multiple_files_upload() - 다중 파일 업로드               │
│  • test_upload_with_post_attachment() - 게시글 연결             │
│  • test_successful_upload_flow() - 전체 성공 플로우              │
│  • test_post_creation_with_files() - 게시글 생성과 파일 연동     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### ⚠️ 오류 시나리오 (Error Cases)

```
┌─────────────── 오류 시나리오: 파일 크기 초과 ─────────────────┐
│                                                          │
│  시나리오: 사용자가 5MB 초과 이미지 업로드 시도            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 1. 로그인 → 2. 대용량 파일 선택 (8MB)              │ │
│  │ 3. 업로드 시도 → 4. 오류 메시지 표시               │ │
│  │ 5. 사용자 안내 → 6. 적절한 크기 파일로 재시도       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  관련 테스트:                                            │
│  • test_oversized_file_rejection() - 크기 초과 거부      │
│  • test_file_size_error_message() - 적절한 오류 메시지   │
│  • test_upload_error_scenarios() - 업로드 실패 처리     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 🔧 예외 시나리오 (Edge Cases)

```
┌─────────────── 예외 시나리오: 동시 업로드 및 중복 처리 ─────────────────┐
│                                                                    │
│  시나리오: 여러 사용자가 동시에 같은 이름 파일 업로드                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 1. 사용자A와 사용자B가 동시에 "image.jpg" 업로드             │ │
│  │ 2. 고유 파일명 생성으로 충돌 방지                            │ │
│  │ 3. 각각 다른 경로에 저장 (UUID 기반)                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  관련 테스트:                                                      │
│  • test_concurrent_upload_handling() - 동시 업로드 처리           │
│  • test_unique_filename_generation() - 고유 파일명 생성           │
│  • test_duplicate_filename_resolution() - 중복 파일명 해결        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. 구현 순서 제안

### 1️⃣ 1단계: MVP 필수 테스트 (🟦 필수)

```
┌───────────────── 1단계: MVP 시스템 안정성 핵심 ─────────────────┐
│                                                             │
│  📋 정상 시나리오 (Happy Path) - 3일 예상                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ① test_validate_file_type() 🟢 초급 ⚡병렬          │ │
│  │    - MIME 타입과 확장자 검증                        │ │
│  │    - 허용된 이미지 형식만 통과                      │ │
│  │                                                     │ │
│  │ ② test_validate_file_size() 🟢 초급 ⚡병렬          │ │
│  │    - 5MB 이하 파일만 허용                          │ │
│  │    - 경계값 테스트 (5MB 정확히)                    │ │
│  │                                                     │ │
│  │ ③ test_generate_file_path() 🟢 초급 ⚡병렬          │ │
│  │    - 년/월/타입별 디렉토리 구조                     │ │
│  │    - UUID 기반 고유 파일명                         │ │
│  │                                                     │ │
│  │ ④ test_save_file_to_disk() 🟡 중급 🔄순차          │ │
│  │    - 실제 파일 저장 검증                           │ │
│  │    - 디렉토리 자동 생성                            │ │
│  │                                                     │ │
│  │ ⑤ test_create_file_document() 🟡 중급 ⚡병렬        │ │
│  │    - MongoDB 문서 구조 검증                        │ │
│  │    - 메타데이터 필드 완성도                        │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
│  ⚠️ 오류 처리 (Error Handling) - 2일 예상                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ① test_oversized_file_rejection() 🟢 초급 ⚡병렬     │ │
│  │    - 5MB 초과 파일 거부                            │ │
│  │    - 적절한 오류 메시지 반환                       │ │
│  │                                                     │ │
│  │ ② test_unsupported_format_rejection() 🟢 초급 ⚡병렬 │ │
│  │    - .exe, .pdf 등 차단                           │ │
│  │    - 허용 형식 목록 제공                          │ │
│  │                                                     │ │
│  │ ③ test_malicious_file_detection() 🔴 고급 ⚡병렬     │ │
│  │    - 파일 헤더 검증                               │ │
│  │    - 실행 파일 위장 차단                          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
│  🔌 API 계약 (Contract) - 1일 예상                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ① test_upload_request_contract() 🟢 초급 🔄순차     │ │
│  │    - multipart/form-data 형식                      │ │
│  │    - 필수 필드 검증                               │ │
│  │                                                     │ │
│  │ ② test_upload_response_contract() 🟢 초급 🔄순차    │ │
│  │    - JSON 응답 구조                               │ │
│  │    - 필수 반환 필드 (file_id, file_url)          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2️⃣ 2단계: 사용자 경험 안정화 (🟡 권장)

```
┌───────────────── 2단계: 사용자 경험 개선 ───────────────────┐
│                                                         │
│  📋 정상 시나리오 - 4일 예상                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ① test_multiple_files_upload() 🔴 고급 🔄순차       │ │
│  │    - 게시글 5개, 댓글 1개 제한                    │ │
│  │    - 트랜잭션 처리                               │ │
│  │                                                   │ │
│  │ ② test_upload_with_post_attachment() 🔴 고급 🔄순차 │ │
│  │    - 게시글과 파일 연동                          │ │
│  │    - 메타데이터 연결                             │ │
│  │                                                   │ │
│  │ ③ test_get_file_by_id() 🟡 중급 🔄순차           │ │
│  │    - 파일 ID로 이미지 반환                       │ │
│  │    - 캐시 헤더 설정                             │ │
│  │                                                   │ │
│  │ ④ test_get_files_by_post() 🟡 중급 🔄순차        │ │
│  │    - 게시글 첨부 파일 목록                       │ │
│  │    - 메타데이터 포함 응답                        │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ⚠️ 오류 처리 - 3일 예상                                │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ① test_file_count_limit_exceeded() 🟡 중급 🔄순차  │ │
│  │    - 첨부 개수 제한 초과                         │ │
│  │    - 타입별 제한 적용                           │ │
│  │                                                   │ │
│  │ ② test_unauthorized_file_access() 🟡 중급 🔄순차   │ │
│  │    - 인증 없는 업로드 차단                       │ │
│  │    - 적절한 401 응답                            │ │
│  │                                                   │ │
│  │ ③ test_rate_limit_exceeded() 🟡 중급 🔄순차       │ │
│  │    - 분당 업로드 제한                           │ │
│  │    - 429 응답과 재시도 안내                     │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3️⃣ 3단계: 고급 기능 최적화 (🟢 선택)

```
┌───────────────── 3단계: 고급 기능 ─────────────────────┐
│                                                       │
│  📋 정상 시나리오 - 5일 예상                           │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ① test_delete_file_success() 🔴 고급 🔄순차       │ │
│  │    - 파일 삭제 및 참조 정리                     │ │
│  │    - posts/comments에서 file_id 제거           │ │
│  │                                                 │ │
│  │ ② test_cleanup_references() 🔴 고급 🔄순차       │ │
│  │    - 연관 데이터 일관성 유지                    │ │
│  │    - 트랜잭션 롤백 처리                        │ │
│  │                                                 │ │
│  │ ③ test_concurrent_upload_handling() 🔴 고급 🔄순차 │ │
│  │    - 동시 업로드 시 충돌 방지                   │ │
│  │    - 락 메커니즘 검증                          │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ⚠️ 오류 처리 - 3일 예상                              │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ① test_delete_unauthorized() 🟡 중급 🔄순차      │ │
│  │    - 업로더가 아닌 사용자 삭제 시도             │ │
│  │    - 403 Forbidden 응답                        │ │
│  │                                                 │ │
│  │ ② test_storage_error_handling() 🔴 고급 🔄순차   │ │
│  │    - 디스크 공간 부족 상황                      │ │
│  │    - 파일 시스템 오류 복구                      │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 5. 프론트엔드 통합 테스트 연계

### API 구현 후 즉시 검증 항목

```python
def test_frontend_integration_upload():
    """
    실제 프론트엔드 사용자 플로우 기반 통합 테스트
    
    검증 항목:
    1. HTML 파일 선택 → FormData 생성 → API 호출
    2. 성공 시 file_id 반환 → 게시글 작성에 포함
    3. 실패 시 사용자 친화적 오류 메시지 표시
    4. 진행률 표시 및 취소 기능 동작
    
    🚨 중요: API 응답 구조가 frontend-prototypes/UI.html의
           JavaScript 코드와 정확히 일치하는지 확인
    """
    pass

def test_image_display_integration():
    """
    업로드된 이미지 표시 기능 검증
    
    시나리오:
    1. 파일 업로드 → file_id 획득
    2. 게시글에 <img src="/api/files/{file_id}"> 삽입
    3. 브라우저에서 이미지 정상 로딩 확인
    4. 캐시 헤더로 성능 최적화 동작
    """
    pass
```

### 통합 테스트 후 우선순위 재조정

프론트엔드 통합 테스트에서 발견된 이슈를 바탕으로 다음 테스트들의 우선순위를 상향 조정:

- **오류 메시지 개선**: 사용자가 실제로 이해할 수 있는 메시지
- **API 응답 구조 수정**: 프론트엔드에서 필요한 추가 필드
- **성능 최적화**: 실제 사용량에서 발견된 병목점

---

## 6. 테스트 실행 전략

### 병렬 vs 순차 실행

```python
# ⚡ 병렬 실행 가능 (독립적)
PARALLEL_TESTS = [
    "test_validate_file_type",
    "test_validate_file_size", 
    "test_generate_file_path",
    "test_create_file_document",
    "test_oversized_file_rejection",
    "test_unsupported_format_rejection"
]

# 🔄 순차 실행 필요 (공유 리소스)
SEQUENTIAL_TESTS = [
    "test_save_file_to_disk",           # 파일 시스템 접근
    "test_multiple_files_upload",       # DB 트랜잭션
    "test_delete_file_success",         # 파일 정리
    "test_rate_limit_exceeded",         # 시간 기반 제한
    "test_concurrent_upload_handling"   # 동시성 테스트
]
```

### Mock 사용 정책

```python
# 🚨 Mock 사용 허용 사례
def test_email_notification_on_upload():
    """
    파일 업로드 시 이메일 알림 기능
    
    🚨 Mock 사용: EmailService
    이유: SMTP 서버 의존성으로 인한 테스트 불안정성
    대안: 실제 이메일 발송은 E2E 테스트에서 검증
    """
    with patch('src.services.email_service.EmailService') as mock_email:
        # 파일 업로드 로직 테스트
        # 이메일 서비스 호출 여부만 검증
        pass

# ❌ Mock 사용 금지 사례  
def test_file_storage():
    """
    파일 저장 기능은 Mock 없이 실제 파일 시스템 사용
    - 임시 디렉토리에 실제 파일 저장
    - 테스트 후 정리 (tearDown)
    """
    pass
```

---

## 7. API 계약 테스트 (MVP 수준)

### 최소 검증 헬퍼

```python
def assert_file_api_basic_contract(response, endpoint_type="upload"):
    """
    파일 API MVP 계약 최소 검증
    
    공통 검증:
    - HTTP 상태 코드 적절성
    - Content-Type: application/json
    - 응답 시간 < 5초 (파일 업로드 기준)
    
    업로드 API 필수 필드:
    - file_id (string): 프론트엔드에서 파일 참조용
    - file_url (string): 이미지 표시용 URL
    - file_size (number): 사용자 정보 표시용
    """
    pass
    
def record_file_api_contract(endpoint, request, response):
    """
    향후 본격 계약 테스트용 API 스키마 기록
    
    기록 항목:
    - 요청 스키마: multipart/form-data 구조
    - 응답 스키마: 성공/실패별 JSON 구조  
    - 헤더 요구사항: Authorization, Content-Type
    - 오류 코드 매핑: 상황별 HTTP 상태 코드
    """
    pass
```

---

## 8. 구현 완료 기준

### 각 단계별 완료 조건

**1단계 (MVP) 완료 기준:**
- ✅ 모든 🟦 필수 테스트 통과
- ✅ 기본 파일 업로드/조회 기능 동작
- ✅ 프론트엔드 통합 테스트 1회 성공
- ✅ 보안 검증 테스트 통과

**2단계 (안정화) 완료 기준:**
- ✅ 모든 🟡 권장 테스트 통과  
- ✅ 다중 파일 업로드 안정성 확인
- ✅ 오류 처리 사용자 경험 검증
- ✅ 성능 기준선 설정 (업로드 5초 이내)

**3단계 (최적화) 완료 기준:**
- ✅ 모든 🟢 선택 테스트 통과
- ✅ 파일 삭제 및 정리 기능 완성
- ✅ 동시성 처리 안정성 확인  
- ✅ 프로덕션 배포 준비 완료

---

이 제안서를 바탕으로 체계적인 TDD 개발을 진행하여 안정적이고 사용자 친화적인 파일 API를 구현할 수 있습니다.