# 파일 API 테스트 코드 제안 개요

## 📋 문서 목차

1. [목적](#목적)
2. [파일 API 기능 분석](#파일-api-기능-분석)
3. [테스트 모듈 구조 설계](#테스트-모듈-구조-설계)
4. [기능 플로우와 테스트 함수 매핑](#기능-플로우와-테스트-함수-매핑)
5. [사용자 시나리오별 테스트 매핑](#사용자-시나리오별-테스트-매핑)
6. [구현 순서 제안](#구현-순서-제안)
7. [API 계약 테스트 설계](#api-계약-테스트-설계)
8. [테스트 환경 및 설정](#테스트-환경-및-설정)

---

## 1. 목적

파일 업로드, 조회, 삭제 등 파일 관리 API의 안정적이고 효율적인 구현을 위한 체계적인 테스트 코드를 제안합니다. Classic TDD 원칙을 준수하며, 사용자 플로우 중심의 실용적인 테스트 전략을 수립합니다.

---

## 2. 파일 API 기능 분석

### 2.1 핵심 API 엔드포인트

```
POST /api/files/upload        # 파일 업로드
GET  /api/files/{file_id}     # 파일 다운로드/조회
GET  /api/files/{file_id}/info # 파일 메타데이터 조회
DELETE /api/files/{file_id}   # 파일 삭제
GET  /api/posts/{slug}/files  # 게시글 첨부파일 목록
```

### 2.2 비즈니스 규칙

**파일 제한사항:**
- **지원 형식**: jpg, jpeg, png, gif, webp
- **최대 크기**: 5MB
- **개수 제한**: post(5개), comment(1개), profile(1개)

**보안 요구사항:**
- 파일 타입 이중 검증 (MIME + 확장자)
- 악성 파일 차단 (헤더 검증)
- Rate Limiting (1분당 10개, 1시간당 50개, 1일당 200개)

---

## 3. 테스트 모듈 구조 설계

### 3.1 테스트 모듈 의존성 계층

```
tests/
├── unit/                           # 단위 테스트
│   ├── test_file_validator.py      # 🔵 기반 (독립적)
│   │   ├── test_file_size_validation() 🟢 초급 ⚡병렬
│   │   ├── test_file_type_validation() 🟢 초급 ⚡병렬
│   │   ├── test_mime_type_security_check() 🔴 고급 ⚡병렬
│   │   └── test_malicious_file_detection() 🔴 고급 ⚡병렬
│   ├── test_file_storage.py        # 🟡 조합 (validator 의존)
│   │   ├── test_generate_file_path() 🟢 초급 ⚡병렬
│   │   ├── test_save_file_to_disk() 🟡 중급 🔄순차
│   │   ├── test_create_directory_structure() 🟡 중급 🔄순차
│   │   └── test_file_cleanup_on_error() 🟡 중급 🔄순차
│   └── test_file_metadata.py       # 🔵 기반 (독립적)
│       ├── test_extract_file_metadata() 🟡 중급 ⚡병렬
│       ├── test_generate_file_url() 🟢 초급 ⚡병렬
│       └── test_metadata_validation() 🟢 초급 ⚡병렬
├── integration/                    # 통합 테스트
│   ├── test_file_upload_api.py     # 🔴 통합 (모든 기능 의존)
│   │   ├── test_successful_file_upload() 🟡 중급 🔄순차
│   │   ├── test_multiple_files_upload() 🔴 고급 🔄순차
│   │   ├── test_file_upload_with_post_creation() 🔴 고급 🔄순차
│   │   └── test_concurrent_upload_handling() 🔴 고급 🔄순차
│   ├── test_file_retrieval_api.py  # 🔴 통합 (storage + metadata 의존)
│   │   ├── test_file_download_by_id() 🟡 중급 🔄순차
│   │   ├── test_file_info_retrieval() 🟡 중급 🔄순차
│   │   └── test_cached_file_response() 🔴 고급 🔄순차
│   └── test_file_management_api.py # 🔴 통합 (전체 의존)
│       ├── test_file_deletion_workflow() 🔴 고급 🔄순차
│       ├── test_reference_cleanup() 🔴 고급 🔄순차
│       └── test_orphaned_file_handling() 🔴 고급 🔄순차
└── contract/                       # API 계약 테스트
    └── test_file_api_contract.py   # 🟠 계약 (API 의존)
        ├── test_upload_request_contract() 🟢 초급 🔄순차
        ├── test_upload_response_contract() 🟢 초급 🔄순차
        ├── test_error_response_contract() 🟡 중급 🔄순차
        └── test_file_url_format_contract() 🟢 초급 🔄순차
```

### 3.2 모듈 간 의존성 그래프

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
│  🔴 통합 계층 (전체 기능 통합)                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ test_file_      │  │ test_file_      │  │ test_file_      │      │
│  │ upload_api.py   │  │ retrieval_api.py│  │ management_api. │      │
│  └─────────────────┘  └─────────────────┘  │ py              │      │
│           │                    │           └─────────────────┘      │
│           └────────┬───────────┘                    │               │
│                    ▼                                ▼               │
│  🟠 계약 계층 (API 인터페이스)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_file_api_  │                                                 │
│  │ contract.py     │                                                 │
│  └─────────────────┘                                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. 기능 플로우와 테스트 함수 매핑

### 4.1 파일 업로드 플로우

```
┌────────────────────── 파일 업로드 플로우 ──────────────────────┐
│                                                              │
│ 🌐 요청 수신 ──→ 🔍 파일 검증 ──→ 💾 파일 저장 ──→ 📝 메타데이터 저장 ──→ 📤 응답 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**각 단계별 테스트 함수 매핑:**

- **🌐 요청 수신 단계**:
  - `test_upload_request_contract()` - multipart/form-data 형식 검증
  - `test_authentication_required()` - Bearer Token 인증 확인

- **🔍 파일 검증 단계**:
  - `test_file_size_validation()` - 5MB 크기 제한 검증
  - `test_file_type_validation()` - 허용된 확장자 검증
  - `test_mime_type_security_check()` - MIME 타입 이중 검증
  - `test_malicious_file_detection()` - 악성 파일 차단

- **💾 파일 저장 단계**:
  - `test_generate_file_path()` - 고유 파일명 및 경로 생성
  - `test_save_file_to_disk()` - 물리적 파일 저장
  - `test_create_directory_structure()` - 년/월/타입별 디렉토리 생성

- **📝 메타데이터 저장 단계**:
  - `test_extract_file_metadata()` - 파일 정보 추출
  - `test_metadata_database_save()` - MongoDB 문서 저장
  - `test_generate_file_url()` - 접근 URL 생성

- **📤 응답 단계**:
  - `test_upload_response_contract()` - 응답 형식 검증
  - `test_error_response_format()` - 오류 응답 구조 확인

### 4.2 파일 조회 플로우

```
┌─────────────────── 파일 조회 플로우 ───────────────────┐
│                                                      │
│ 🌐 요청 수신 ──→ 🔍 파일 ID 검증 ──→ 📖 메타데이터 조회 ──→ 📤 파일 반환 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**각 단계별 테스트 함수 매핑:**

- **🌐 요청 수신**: `test_file_id_parameter_validation()`
- **🔍 파일 ID 검증**: `test_valid_object_id_format()`
- **📖 메타데이터 조회**: `test_file_metadata_retrieval()`  
- **📤 파일 반환**: `test_file_download_by_id()`

---

## 5. 사용자 시나리오별 테스트 매핑

### 5.1 주 시나리오 (Happy Path)

```
┌─────────────── 사용자 시나리오 → 테스트 매핑 ────────────────┐
│                                                            │
│  🌟 시나리오 1: "게시글 작성 시 이미지 첨부"                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 사용자 행동: 로그인 → 이미지 선택 → 게시글 작성 → 업로드    │ │
│  │ 관련 테스트:                                           │ │
│  │ • test_successful_file_upload() 🟦 필수 🟡 중급 🔄순차   │ │
│  │ • test_file_upload_with_post_creation() 🟦 필수 🔴 고급  │ │
│  │ • test_multiple_files_upload() 🟡 권장 🔴 고급 🔄순차    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🌟 시나리오 2: "댓글에 이미지 첨부"                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 사용자 행동: 댓글 작성 → 이미지 첨부 (1개 제한)          │ │
│  │ 관련 테스트:                                           │ │
│  │ • test_single_file_comment_attachment() 🟦 필수 🟡 중급  │ │
│  │ • test_comment_file_count_limit() 🟦 필수 🟢 초급 ⚡병렬  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🌟 시나리오 3: "프로필 이미지 설정"                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 사용자 행동: 설정 페이지 → 프로필 이미지 업로드           │ │
│  │ 관련 테스트:                                           │ │
│  │ • test_profile_image_upload() 🟦 필수 🟡 중급 🔄순차     │ │
│  │ • test_profile_image_replacement() 🟡 권장 🟡 중급 🔄순차 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 5.2 오류 시나리오 (Error Cases)

```
┌─────────────── 오류 시나리오 → 테스트 매핑 ────────────────┐
│                                                          │
│  ⚠️ 시나리오 1: "파일 크기 초과"                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 사용자 행동: 6MB 이미지 업로드 시도                    │ │
│  │ 관련 테스트:                                         │ │
│  │ • test_oversized_file_rejection() 🟦 필수 🟢 초급 ⚡병렬 │ │
│  │ • test_file_size_error_message() 🟦 필수 🟢 초급 ⚡병렬  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  ⚠️ 시나리오 2: "지원되지 않는 파일 형식"                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 사용자 행동: PDF, EXE 파일 업로드 시도                 │ │
│  │ 관련 테스트:                                         │ │
│  │ • test_unsupported_file_type_rejection() 🟦 필수 🟢 초급 │ │
│  │ • test_malicious_file_detection() 🟦 필수 🔴 고급 ⚡병렬  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  ⚠️ 시나리오 3: "파일 개수 제한 초과"                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 사용자 행동: 게시글에 6개 이미지 첨부 시도              │ │
│  │ 관련 테스트:                                         │ │
│  │ • test_post_file_count_limit() 🟦 필수 🟢 초급 ⚡병렬    │ │
│  │ • test_file_count_exceeded_error() 🟦 필수 🟢 초급 ⚡병렬 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 5.3 예외 시나리오 (Edge Cases)

```
┌─────────────── 예외 시나리오 → 테스트 매핑 ────────────────┐
│                                                          │
│  🔧 시나리오 1: "동시 파일 업로드"                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 상황: 여러 사용자가 동시에 파일 업로드                  │ │
│  │ 관련 테스트:                                         │ │
│  │ • test_concurrent_upload_handling() 🟡 권장 🔴 고급 🔄순차 │ │
│  │ • test_race_condition_prevention() 🟢 선택 🔴 고급 🔄순차 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  🔧 시나리오 2: "네트워크 장애 중 업로드"                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 상황: 업로드 중 연결 끊김, 타임아웃                     │ │
│  │ 관련 테스트:                                         │ │
│  │ • test_upload_timeout_handling() 🟡 권장 🟡 중급 🔄순차  │ │
│  │ • test_partial_upload_cleanup() 🟡 권장 🟡 중급 🔄순차   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  🔧 시나리오 3: "저장 공간 부족"                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 상황: 서버 디스크 공간 부족으로 저장 실패               │ │
│  │ 관련 테스트:                                         │ │
│  │ • test_storage_full_handling() 🟡 권장 🟡 중급 🔄순차    │ │
│  │ • test_graceful_storage_failure() 🟢 선택 🟡 중급 🔄순차 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 6. 구현 순서 제안

### 6.1 3단계 구현 로드맵

```
┌───────────────── 구현 단계별 로드맵 ─────────────────┐
│                                                   │
│  1️⃣ 1단계: 🟦 필수 (MVP) - 시스템 안정성 핵심     │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 파일 검증 (File Validation)               │ │
│  │ ① test_file_size_validation() 🟢 초급 ⚡병렬   │ │
│  │ ② test_file_type_validation() 🟢 초급 ⚡병렬   │ │
│  │ ③ test_mime_type_security_check() 🔴 고급 ⚡병렬 │ │
│  │                                             │ │
│  │ 💾 파일 저장 (File Storage)                 │ │
│  │ ④ test_generate_file_path() 🟢 초급 ⚡병렬     │ │
│  │ ⑤ test_save_file_to_disk() 🟡 중급 🔄순차     │ │
│  │                                             │ │
│  │ 🔌 API 엔드포인트 (Core APIs)               │ │
│  │ ⑥ test_successful_file_upload() 🟡 중급 🔄순차 │ │
│  │ ⑦ test_file_download_by_id() 🟡 중급 🔄순차   │ │
│  │ ⑧ test_upload_request_contract() 🟢 초급 🔄순차 │ │
│  │ ⑨ test_upload_response_contract() 🟢 초급 🔄순차 │ │
│  │                                             │ │
│  │ ⚠️ 기본 오류 처리 (Essential Error Handling) │ │
│  │ ⑩ test_oversized_file_rejection() 🟢 초급 ⚡병렬 │ │
│  │ ⑪ test_unsupported_file_type_rejection() 🟢 초급 │ │
│  │ ⑫ test_file_not_found_error() 🟢 초급 ⚡병렬    │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  2️⃣ 2단계: 🟡 권장 (안정화) - 사용자 경험 개선    │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 고급 파일 처리 (Advanced File Handling)   │ │
│  │ ① test_extract_file_metadata() 🟡 중급 ⚡병렬   │ │
│  │ ② test_multiple_files_upload() 🔴 고급 🔄순차  │ │
│  │ ③ test_file_upload_with_post_creation() 🔴 고급 │ │
│  │                                             │ │
│  │ 🗑️ 파일 관리 (File Management)              │ │
│  │ ④ test_file_deletion_workflow() 🔴 고급 🔄순차 │ │
│  │ ⑤ test_reference_cleanup() 🔴 고급 🔄순차     │ │
│  │                                             │ │
│  │ ⚠️ 고급 오류 처리 (Advanced Error Handling)  │ │
│  │ ⑥ test_upload_timeout_handling() 🟡 중급 🔄순차 │ │
│  │ ⑦ test_storage_full_handling() 🟡 중급 🔄순차  │ │
│  │ ⑧ test_malicious_file_detection() 🔴 고급 ⚡병렬 │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  3️⃣ 3단계: 🟢 선택 (최적화) - 고급 기능          │
│  ┌─────────────────────────────────────────────┐ │
│  │ 🚀 성능 최적화 (Performance)                │ │
│  │ ① test_concurrent_upload_handling() 🔴 고급 🔄순차 │ │
│  │ ② test_cached_file_response() 🔴 고급 🔄순차   │ │
│  │ ③ test_large_file_handling() 🔴 고급 🔄순차    │ │
│  │                                             │ │
│  │ 🔒 보안 강화 (Security Enhancement)         │ │
│  │ ④ test_rate_limiting_enforcement() 🔴 고급 🔄순차 │ │
│  │ ⑤ test_file_access_permission() 🔴 고급 🔄순차 │ │
│  │                                             │ │
│  │ 🛠️ 운영 지원 (Operations Support)           │ │
│  │ ⑥ test_orphaned_file_handling() 🔴 고급 🔄순차 │ │
│  │ ⑦ test_file_system_monitoring() 🔴 고급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  💡 구현 팁:                                    │
│  • ⚡병렬: 독립적 실행 가능 (상태 변경 없음)        │
│  • 🔄순차: 순차 실행 필요 (공유 리소스 사용)       │
│  • 🟢 초급 → 🟡 중급 → 🔴 고급 순서로 진행       │
│  • 각 단계 완료 후 프론트엔드 통합 테스트 수행      │
│  • 🟦 필수 완료 시점에서 MVP 배포 가능           │
│                                                   │
└───────────────────────────────────────────────────┘
```

### 6.2 단계별 검증 체크리스트

**1단계 완료 후 검증:**
```python
# 프론트엔드 통합 테스트 - MVP 기능 검증
def verify_mvp_file_functionality():
    """
    검증 항목:
    1. 이미지 업로드 → 게시글 작성 → 이미지 표시 전체 플로우
    2. 파일 크기/형식 제한 시 적절한 사용자 메시지
    3. 업로드된 파일 브라우저에서 정상 표시
    4. 기본적인 오류 상황 처리
    """
    pass
```

**2단계 완료 후 검증:**
```python
# 안정성 검증 - 다양한 사용자 시나리오
def verify_stability_enhancements():
    """
    검증 항목:
    1. 여러 파일 동시 업로드 시 UI 안정성
    2. 파일 삭제 후 게시글/댓글에서 정상 제거
    3. 네트워크 오류 시 사용자 경험
    4. 대용량 파일 처리 시 진행률 표시
    """
    pass
```

---

## 7. API 계약 테스트 설계

### 7.1 MVP 수준 계약 검증

```python
# MVP API 계약 검증 헬퍼
def assert_file_api_basic_contract(response, endpoint_type="upload"):
    """
    MVP API 계약 최소 검증
    
    공통 검증:
    - HTTP 상태 코드 적절성
    - Content-Type: application/json
    - 응답 시간 < 5초
    
    엔드포인트별 검증:
    - upload: file_id, file_url 필수 필드
    - info: 메타데이터 완성도
    - download: 적절한 Content-Type 헤더
    """
    pass
```

### 7.2 계약 테스트 항목

```python
# 🟦 필수 (MVP) - API 계약
def test_upload_request_contract():
    """
    업로드 요청 계약 검증 🟢 초급 🔄순차
    
    검증 항목:
    - Content-Type: multipart/form-data
    - 필수 필드: file, attachment_type
    - 선택 필드: attached_to_id
    - Authorization 헤더 필요
    """
    pass

def test_upload_response_contract():
    """
    업로드 응답 계약 검증 🟢 초급 🔄순차
    
    검증 항목:
    - HTTP 201 Created
    - 필수 필드: file_id, file_url, created_at
    - 데이터 타입: file_id(string), file_size(number)
    - ISO 8601 날짜 형식
    """
    pass

def test_error_response_contract():
    """
    오류 응답 계약 검증 🟡 중급 🔄순차
    
    검증 항목:
    - 표준 오류 구조: {error: {code, message, details}}
    - 적절한 HTTP 상태 코드
    - 사용자 친화적 메시지
    - timestamp, path 필드 포함
    """
    pass

def test_file_url_format_contract():
    """
    파일 URL 형식 계약 검증 🟢 초급 🔄순차
    
    검증 항목:
    - URL 패턴: /api/files/{file_id}
    - file_id는 유효한 MongoDB ObjectId
    - HTTP/HTTPS 프로토콜 지원
    - 브라우저에서 직접 접근 가능
    """
    pass
```

### 7.3 향후 확장 대비 계약 기록

```python
def record_api_contract_for_future(endpoint, request, response):
    """
    향후 본격 계약 테스트용 API 명세 기록
    
    기록 항목:
    - 요청/응답 스키마
    - 오류 코드 매핑
    - 성능 기준 (응답 시간)
    - 버전 호환성 정보
    """
    pass
```

---

## 8. 테스트 환경 및 설정

### 8.1 테스트 데이터 관리

```python
# 테스트 픽스처 설계
@pytest.fixture
def sample_image_files():
    """
    다양한 테스트 시나리오용 샘플 파일들
    
    포함 파일:
    - valid_image.jpg (1MB, 정상)
    - large_image.jpg (6MB, 크기 초과)
    - invalid_file.txt (텍스트 파일)
    - empty_file.jpg (0바이트)
    - malicious_file.exe (악성 파일)
    """
    pass

@pytest.fixture
def temp_upload_directory():
    """테스트용 임시 업로드 디렉토리"""
    pass

@pytest.fixture
def test_user_tokens():
    """다양한 권한 수준의 테스트 사용자 토큰"""
    pass
```

### 8.2 Mock 사용 정책

```python
# 🚨 Mock 사용 기준
def test_file_upload_with_external_service():
    """
    🚨 Mock 사용: EmailNotificationService
    이유: 외부 SMTP 서버 호출로 인한 네트워크 의존성
    대안: 실제 이메일 발송 없이 업로드 완료 알림 로직 테스트
    """
    # 이미 구현 완료된 EmailService를 Mock으로 처리
    pass

def test_virus_scanning_integration():
    """
    🚨 Mock 사용: AntiVirusService
    이유: 외부 바이러스 스캔 API 호출 비용 및 시간
    대안: 스캔 결과별 파일 처리 로직에 집중
    """
    pass
```

### 8.3 테스트 전후 상태 관리

```python
# 테스트 상태 관리 예시
def test_file_upload_state_management():
    """
    테스트 전 상태:
    - 빈 uploads/ 디렉토리
    - 빈 files 컬렉션
    - 인증된 사용자 세션
    
    실행 작업:
    - 1MB 이미지 파일 업로드
    - 메타데이터 DB 저장
    
    테스트 후 상태:
    - uploads/2024/01/posts/ 디렉토리에 파일 존재
    - files 컬렉션에 문서 1개 생성
    - 사용자 업로드 통계 +1
    
    정리 작업:
    - 업로드된 파일 삭제
    - DB 문서 삭제
    - 사용자 통계 원복
    """
    pass
```

### 8.4 병렬 실행 최적화

```python
# 병렬 실행 가능 테스트 (⚡)
def test_file_validation_parallel():
    """독립적 검증 로직, 상태 변경 없음"""
    pass

# 순차 실행 필요 테스트 (🔄)
def test_file_storage_sequential():
    """파일 시스템 및 DB 변경, 공유 리소스 사용"""
    pass
```

---

## 결론

이 테스트 코드 제안은 파일 API의 안정적이고 점진적인 구현을 위한 체계적인 접근 방식을 제공합니다. Classic TDD 원칙을 준수하면서도 실제 사용자 플로우를 중심으로 한 실용적인 테스트 전략을 통해, MVP부터 고급 기능까지 단계별로 안전하게 개발할 수 있도록 설계되었습니다.

**핵심 특징:**
- 🟦 필수 → 🟡 권장 → 🟢 선택 단계별 우선순위
- 🟢 초급 → 🟡 중급 → 🔴 고급 난이도별 접근
- ⚡ 병렬 / 🔄 순차 실행 최적화
- Classic TDD 원칙 준수 (최소 Mock 사용)
- 사용자 플로우 중심 검증