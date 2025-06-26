# 파일 API 테스트 코드 제안 구현 개요

## 📋 문서 목차

1. [현재 기능 개발과 관련된 테스트 모듈과 함수 관계](#1-현재-기능-개발과-관련된-테스트-모듈과-함수-관계)
2. [기능 플로우와 테스트 함수 매핑](#2-기능-플로우와-테스트-함수-매핑)
3. [사용자 시나리오별 테스트 매핑](#3-사용자-시나리오별-테스트-매핑)
4. [구현 순서 제안](#4-구현-순서-제안)

---

## 1. 현재 기능 개발과 관련된 테스트 모듈과 함수 관계

### 테스트 모듈 구조 (의존성 관계)

```
tests/
├── unit/
│   ├── test_file_validator.py     # 🔵 기반 (의존성 없음)
│   │   ├── test_validate_file_type()
│   │   ├── test_validate_file_size()
│   │   ├── test_validate_file_extension()
│   │   └── test_validate_file_signature()
│   ├── test_file_storage.py       # 🟡 조합 (validator 의존)
│   │   ├── test_generate_file_path()
│   │   ├── test_save_file_to_disk()
│   │   ├── test_create_directory_structure()
│   │   └── test_handle_storage_errors()
│   ├── test_file_metadata.py      # 🔵 기반 (의존성 없음)
│   │   ├── test_extract_file_metadata()
│   │   ├── test_create_file_document()
│   │   └── test_generate_file_url()
│   └── test_file_repository.py    # 🟡 조합 (metadata 의존)
│       ├── test_save_file_metadata()
│       ├── test_find_file_by_id()
│       ├── test_delete_file_record()
│       └── test_update_file_references()
├── integration/
│   ├── test_file_upload_api.py    # 🔴 통합 (모든 기능 의존)
│   │   ├── test_upload_endpoint_success()
│   │   ├── test_upload_with_validation()
│   │   └── test_upload_error_handling()
│   ├── test_file_retrieval_api.py # 🔴 통합 (storage + repository 의존)
│   │   ├── test_get_file_endpoint()
│   │   ├── test_get_file_info_endpoint()
│   │   └── test_file_not_found_handling()
│   └── test_file_deletion_api.py  # 🔴 통합 (모든 기능 의존)
│       ├── test_delete_file_endpoint()
│       ├── test_delete_with_cleanup()
│       └── test_delete_permission_check()
└── contract/
    └── test_file_api_contract.py  # 🟠 계약 (API 의존)
        ├── test_upload_request_contract()
        ├── test_upload_response_contract()
        ├── test_error_response_contract()
        └── test_file_endpoint_contract()
```

### 모듈 간 관계 시각화

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
│  ┌─────────────────┐    ┌─────────────────┐                          │
│  │ test_file_      │    │ test_file_      │                          │
│  │ storage.py      │    │ repository.py   │                          │
│  └─────────────────┘    └─────────────────┘                          │
│           │                       │                                  │
│           └───────┬───────────────┘                                  │
│                   ▼                                                  │
│  🔴 통합 계층 (모든 기능 통합)                                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │
│  │ test_file_      │    │ test_file_      │    │ test_file_      │    │
│  │ upload_api.py   │    │ retrieval_api.py│    │ deletion_api.py │    │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘    │
│           │                       │                       │          │
│           └───────────────┬───────────────────────────────┘          │
│                           ▼                                          │
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

### 파일 업로드 플로우 시각화

```
┌────────────────────────── 파일 업로드 플로우 ──────────────────────────┐
│                                                                      │
│  📤 업로드 요청 ──→ 🔍 파일 검증 ──→ 💾 파일 저장 ──→ 📝 메타데이터 저장 ──→ 📤 응답  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 각 단계별 테스트 함수 매핑

- **📤 업로드 요청 단계**: 
  - `test_upload_request_contract()` - API 요청 형식 검증
  - `test_multipart_form_parsing()` - 멀티파트 데이터 파싱
  - `test_authentication_check()` - 사용자 인증 처리

- **🔍 파일 검증 단계**: 
  - `test_validate_file_type()` - MIME 타입 검증
  - `test_validate_file_size()` - 파일 크기 제한 검증
  - `test_validate_file_extension()` - 확장자 검증
  - `test_validate_file_signature()` - 파일 시그니처 검증

- **💾 파일 저장 단계**: 
  - `test_generate_file_path()` - 저장 경로 생성
  - `test_save_file_to_disk()` - 물리적 파일 저장
  - `test_create_directory_structure()` - 디렉토리 구조 생성
  - `test_handle_storage_errors()` - 저장 실패 처리

- **📝 메타데이터 저장 단계**: 
  - `test_extract_file_metadata()` - 메타데이터 추출
  - `test_create_file_document()` - 문서 생성
  - `test_save_file_metadata()` - DB 저장
  - `test_generate_file_url()` - 접근 URL 생성

- **📤 응답 단계**: 
  - `test_upload_response_contract()` - API 응답 형식 검증
  - `test_error_response_contract()` - 오류 응답 처리

### 파일 조회 플로우 시각화

```
┌────────────────────────── 파일 조회 플로우 ──────────────────────────┐
│                                                                    │
│  🌐 조회 요청 ──→ 🔍 파일 ID 검증 ──→ 📂 파일 검색 ──→ 📤 파일 반환      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 파일 삭제 플로우 시각화

```
┌────────────────────────── 파일 삭제 플로우 ──────────────────────────┐
│                                                                    │
│  🗑️ 삭제 요청 ──→ 🔐 권한 검증 ──→ 🔗 참조 정리 ──→ 💾 파일 삭제 ──→ 📤 응답  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**통합 테스트**
- `test_full_upload_flow()` - 전체 업로드 플로우 통합 검증
- `test_file_lifecycle_workflow()` - 업로드→조회→삭제 전체 워크플로우

---

## 3. 사용자 시나리오별 테스트 매핑

### 현재 구현 기능의 실제 사용자 시나리오

```
┌─────────────── 사용자 시나리오 → 테스트 매핑 ────────────────┐
│                                                            │
│  🌟 주 시나리오 (Happy Path)                                │
│  "사용자가 게시글에 이미지를 첨부하여 업로드"                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 로그인 → 파일 선택 → 업로드 → 게시글 작성       │ │
│  │ 테스트: test_validate_file_type()                      │ │
│  │        test_save_file_to_disk()                        │ │
│  │        test_upload_endpoint_success()                  │ │
│  │        test_upload_response_contract()                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  ⚠️ 오류 시나리오 (Error Cases)                             │
│  "잘못된 파일 형식이나 크기 초과 상황"                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 지원되지 않는 파일 → 적절한 오류 메시지 반환    │ │
│  │ 테스트: test_validate_file_extension()                │ │
│  │        test_validate_file_size()                       │ │
│  │        test_upload_error_handling()                    │ │
│  │        test_error_response_contract()                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🔧 예외 시나리오 (Edge Cases)                              │
│  "특수한 상황이나 경계값 처리"                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 동시 업로드, 빈 파일, 특수문자 파일명 등        │ │
│  │ 테스트: test_concurrent_upload_handling()              │ │
│  │        test_empty_file_handling()                      │ │
│  │        test_special_characters_filename()              │ │
│  │        test_storage_full_handling()                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  📱 사용자 경험 시나리오                                     │
│  "파일 업로드 후 게시글에서 이미지 표시"                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 업로드 → 게시글 저장 → 목록에서 이미지 표시     │ │
│  │ 테스트: test_get_file_endpoint()                       │ │
│  │        test_file_url_generation()                      │ │
│  │        test_image_display_integration()                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🗑️ 파일 관리 시나리오                                      │
│  "업로드한 파일 삭제 및 정리"                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 파일 삭제 → 게시글 참조 정리 → 물리적 파일 삭제  │ │
│  │ 테스트: test_delete_permission_check()                 │ │
│  │        test_delete_with_cleanup()                      │ │
│  │        test_update_file_references()                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 4. 구현 순서 제안

### 우선순위별 테스트 함수 분류 및 단계별 구현 로드맵

```
┌───────────────── 구현 단계별 로드맵 ─────────────────┐
│                                                   │
│  1️⃣ 1단계: 🟦 필수 (MVP) - 시스템 안정성 핵심     │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 정상 시나리오 (Happy Path)                │ │
│  │ ① test_validate_file_type() 🟢 초급 ⚡병렬    │ │
│  │ ② test_validate_file_size() 🟢 초급 ⚡병렬    │ │
│  │ ③ test_generate_file_path() 🟡 중급 ⚡병렬    │ │
│  │ ④ test_save_file_to_disk() 🟡 중급 🔄순차     │ │
│  │ ⑤ test_save_file_metadata() 🟡 중급 🔄순차   │ │
│  │                                             │ │
│  │ ⚠️ 오류 처리 (Error Handling)               │ │
│  │ ⑥ test_invalid_file_type_rejection() 🟢 초급 ⚡병렬 │ │
│  │ ⑦ test_oversized_file_rejection() 🟢 초급 ⚡병렬 │ │
│  │ ⑧ test_handle_storage_errors() 🟡 중급 🔄순차 │ │
│  │                                             │ │
│  │ 🔌 API 계약 (Contract)                     │ │
│  │ ⑨ test_upload_request_contract() 🟢 초급 🔄순차 │ │
│  │ ⑩ test_upload_response_contract() 🟢 초급 🔄순차 │ │
│  │ ⑪ test_upload_endpoint_success() 🔴 고급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│  예상 구현 시간: 1-2일                            │
│                                                   │
│  2️⃣ 2단계: 🟡 권장 (안정화) - 사용자 경험 개선    │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 정상 시나리오                             │ │
│  │ ① test_extract_file_metadata() 🟡 중급 🔄순차 │ │
│  │ ② test_get_file_endpoint() 🟡 중급 🔄순차     │ │
│  │ ③ test_get_file_info_endpoint() 🟡 중급 🔄순차 │ │
│  │                                             │ │
│  │ ⚠️ 오류 처리                                │ │
│  │ ④ test_file_not_found_handling() 🟡 중급 🔄순차 │ │
│  │ ⑤ test_authentication_check() 🟡 중급 🔄순차  │ │
│  │                                             │ │
│  │ 🔌 API 계약                                │ │
│  │ ⑥ test_file_endpoint_contract() 🟡 중급 🔄순차 │ │
│  │ ⑦ test_error_response_contract() 🟡 중급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│  예상 구현 시간: 1일                              │
│                                                   │
│  3️⃣ 3단계: 🟢 선택 (최적화) - 고급 기능          │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 정상 시나리오                             │ │
│  │ ① test_delete_file_endpoint() 🔴 고급 🔄순차  │ │
│  │ ② test_delete_with_cleanup() 🔴 고급 🔄순차   │ │
│  │ ③ test_concurrent_upload_handling() 🔴 고급 🔄순차 │ │
│  │                                             │ │
│  │ ⚠️ 오류 처리                                │ │
│  │ ④ test_delete_permission_check() 🟡 중급 🔄순차 │ │
│  │ ⑤ test_storage_full_handling() 🔴 고급 🔄순차 │ │
│  │                                             │ │
│  │ 🔧 예외 케이스                              │ │
│  │ ⑥ test_empty_file_handling() 🟡 중급 🔄순차   │ │
│  │ ⑦ test_special_characters_filename() 🟡 중급 ⚡병렬 │ │
│  │ ⑧ test_file_lifecycle_workflow() 🔴 고급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│  예상 구현 시간: 2-3일                            │
│                                                   │
│  💡 구현 팁:                                    │
│  • ⚡병렬: 독립적 실행 가능 (상태 변경 없음)        │
│  • 🔄순차: 순차 실행 필요 (공유 리소스 사용)       │
│  • 🟢 초급 → 🟡 중급 → 🔴 고급 순서로 진행       │
│  • 각 단계 완료 후 다음 단계로 이동              │
│  • 🟦 필수 완료 시점에서 MVP 배포 가능           │
│  • 프런트엔드 통합 테스트는 2단계 완료 후 진행     │
│                                                   │
└───────────────────────────────────────────────────┘
```

### 단계별 핵심 검증 포인트

**1단계 (MVP) 완료 후 검증:**
- 파일 업로드 기본 기능 동작
- 파일 형식 및 크기 제한 적용
- API 기본 계약 준수
- 데이터베이스 저장 정상 동작

**2단계 (안정화) 완료 후 검증:**
- 파일 조회 및 메타데이터 반환
- 오류 상황 적절한 처리
- 사용자 인증 및 권한 확인

**3단계 (최적화) 완료 후 검증:**
- 파일 삭제 및 정리 기능
- 동시성 처리 및 예외 상황 대응
- 전체 파일 생명주기 관리

### 프런트엔드 통합 테스트 계획

2단계 완료 후 실행할 통합 테스트:

```python
def test_frontend_file_upload_integration():
    """
    실제 HTML UI에서 파일 업로드 테스트
    
    검증 항목:
    1. 파일 선택 → 업로드 요청 → 응답 처리
    2. 업로드 진행률 표시 (구현 시)
    3. 성공/실패 메시지 표시
    4. 업로드된 파일 게시글에서 표시
    """
    pass

def test_user_workflow_post_with_images():
    """
    사용자 워크플로우: 이미지 포함 게시글 작성
    
    시나리오:
    - 로그인 → 게시글 작성 → 이미지 첨부 → 게시 → 목록에서 확인
    """
    pass
```

---

이 개요는 파일 API 구현을 위한 체계적인 테스트 전략을 제시하며, Classic TDD 원칙을 준수하여 안정적이고 실용적인 개발 프로세스를 지원합니다.