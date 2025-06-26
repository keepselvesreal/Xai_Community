# File API 테스트 계획서

## 📋 문서 목차

1. [테스트 개요](#1-테스트-개요)
2. [테스트 모듈 구조 및 의존성](#2-테스트-모듈-구조-및-의존성)
3. [기능 플로우와 테스트 함수 매핑](#3-기능-플로우와-테스트-함수-매핑)
4. [사용자 시나리오별 테스트 매핑](#4-사용자-시나리오별-테스트-매핑)
5. [구현 순서 제안](#5-구현-순서-제안)
6. [테스트 환경 및 Mock 정책](#6-테스트-환경-및-mock-정책)

---

## 1. 테스트 개요

File API의 핵심 기능인 파일 업로드, 조회, 삭제 시스템에 대한 체계적인 테스트 코드를 제안합니다. TDD 원칙을 준수하며, 실제 사용자 플로우 기반의 실용적인 테스트를 구성합니다.

**테스트 대상 기능:**
- 파일 업로드 및 검증
- 파일 메타데이터 관리
- 파일 조회 및 서빙
- 파일 삭제 및 참조 정리
- 권한 및 보안 검증

---

## 2. 테스트 모듈 구조 및 의존성

### 테스트 모듈 구조 (의존성 관계)

```
tests/
├── unit/
│   ├── test_file_validator.py        # 🔵 기반 (의존성 없음)
│   │   ├── test_validate_file_type()
│   │   ├── test_validate_file_size()
│   │   ├── test_validate_file_count()
│   │   └── test_validate_security_rules()
│   ├── test_file_storage.py          # 🔵 기반 (의존성 없음)
│   │   ├── test_generate_file_path()
│   │   ├── test_save_physical_file()
│   │   └── test_cleanup_file_system()
│   ├── test_file_metadata.py         # 🟡 조합 (validator 의존)
│   │   ├── test_extract_file_metadata()
│   │   ├── test_create_file_document()
│   │   └── test_update_file_references()
│   └── test_file_permissions.py      # 🔵 기반 (의존성 없음)
│       ├── test_check_upload_permission()
│       ├── test_check_delete_permission()
│       └── test_validate_user_quota()
├── integration/
│   ├── test_file_upload_service.py   # 🔴 통합 (모든 기능 의존)
│   │   ├── test_full_upload_flow()
│   │   ├── test_upload_with_metadata()
│   │   └── test_upload_error_handling()
│   ├── test_file_retrieval_service.py # 🔴 통합 (storage + metadata 의존)
│   │   ├── test_file_serving_flow()
│   │   ├── test_metadata_retrieval()
│   │   └── test_file_not_found_handling()
│   └── test_file_deletion_service.py # 🔴 통합 (모든 기능 의존)
│       ├── test_complete_deletion_flow()
│       ├── test_reference_cleanup()
│       └── test_deletion_permission_flow()
└── contract/
    └── test_file_api_contract.py     # 🟠 계약 (API 의존)
        ├── test_upload_api_contract()
        ├── test_retrieval_api_contract()
        └── test_deletion_api_contract()
```

### 모듈 간 관계 시각화

```
┌─────────────────────── 테스트 모듈 의존성 그래프 ────────────────────────┐
│                                                                      │
│  🔵 기반 계층 (독립적)                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ test_file_      │  │ test_file_      │  │ test_file_      │      │
│  │ validator.py    │  │ storage.py      │  │ permissions.py  │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│           │                     │                     │             │
│           └─────────┬───────────┴───────────┬─────────┘             │
│                     ▼                       ▼                       │
│  🟡 조합 계층 (기반 기능 활용)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_file_      │                                                 │
│  │ metadata.py     │                                                 │
│  └─────────────────┘                                                 │
│           │                                                          │
│           ▼                                                          │
│  🔴 통합 계층 (모든 기능 통합)                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ test_file_      │  │ test_file_      │  │ test_file_      │      │
│  │ upload_service  │  │ retrieval_      │  │ deletion_       │      │
│  │ .py             │  │ service.py      │  │ service.py      │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│           │                     │                     │             │
│           └─────────┬───────────┴───────────┬─────────┘             │
│                     ▼                       ▼                       │
│  🟠 계약 계층 (API 인터페이스)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_file_api_  │                                                 │
│  │ contract.py     │                                                 │
│  └─────────────────┘                                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. 기능 플로우와 테스트 함수 매핑

### 플로우 시각화

```
┌────────────────────────── File API 플로우 ──────────────────────────┐
│                                                                     │
│  📤 파일 업로드: 요청 → 검증 → 저장 → 메타데이터 → 응답                   │
│  📥 파일 조회: 요청 → 권한확인 → 파일검색 → 서빙                          │
│  🗑️ 파일 삭제: 요청 → 권한확인 → 참조정리 → 물리삭제 → 응답                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Upload Flow 단계별 테스트 함수 매핑

- **📤 파일 업로드 요청 단계**: 
  - `test_upload_api_contract()` - API 요청 형식 검증
  - `test_multipart_parsing()` - multipart/form-data 파싱

- **🔍 파일 검증 단계**: 
  - `test_validate_file_type()` - MIME 타입 및 확장자 검증
  - `test_validate_file_size()` - 파일 크기 제한 검증
  - `test_validate_file_count()` - 첨부 개수 제한 검증
  - `test_validate_security_rules()` - 악성 파일 차단

- **💾 파일 저장 단계**: 
  - `test_generate_file_path()` - 저장 경로 생성
  - `test_save_physical_file()` - 물리적 파일 저장
  - `test_create_file_document()` - 메타데이터 DB 저장

- **📤 응답 단계**: 
  - `test_upload_response_contract()` - API 응답 형식 검증
  - `test_upload_error_handling()` - 오류 응답 처리

### Retrieval Flow 단계별 테스트 함수 매핑

- **📥 파일 조회 요청**: 
  - `test_retrieval_api_contract()` - API 요청 형식
  - `test_file_id_validation()` - 파일 ID 유효성

- **🔍 파일 검색**: 
  - `test_find_file_by_id()` - DB에서 파일 검색
  - `test_file_not_found_handling()` - 파일 없음 처리

- **📤 파일 서빙**: 
  - `test_file_serving_flow()` - 실제 파일 반환
  - `test_cache_headers()` - 캐시 헤더 설정

### Deletion Flow 단계별 테스트 함수 매핑

- **🗑️ 삭제 요청**: 
  - `test_deletion_api_contract()` - API 요청 형식
  - `test_check_delete_permission()` - 삭제 권한 검증

- **🔗 참조 정리**: 
  - `test_reference_cleanup()` - posts/comments에서 file_id 제거
  - `test_cleanup_file_system()` - 물리적 파일 삭제

- **📤 삭제 응답**: 
  - `test_deletion_response()` - 삭제 결과 응답
  - `test_cleanup_report()` - 정리된 참조 보고

---

## 4. 사용자 시나리오별 테스트 매핑

```
┌─────────────── 사용자 시나리오 → 테스트 매핑 ────────────────┐
│                                                            │
│  🌟 주 시나리오 (Happy Path)                                │
│  "인증된 사용자가 유효한 이미지를 게시글에 첨부"              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 로그인 → 파일선택 → 업로드 → 게시글작성 → 표시   │ │
│  │ 테스트: test_validate_file_type()                      │ │
│  │        test_save_physical_file()                       │ │
│  │        test_full_upload_flow()                         │ │
│  │        test_file_serving_flow()                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  ⚠️ 오류 시나리오 (Error Cases)                             │
│  "잘못된 파일이나 권한 문제로 업로드 실패"                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 대용량파일 → 크기초과 오류 → 사용자 안내          │ │
│  │ 테스트: test_validate_file_size()                      │ │
│  │        test_file_size_error_handling()                 │ │
│  │        test_upload_error_handling()                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🔧 예외 시나리오 (Edge Cases)                              │
│  "동시 업로드, 권한 변경, 파일 삭제 등 복합 상황"              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 같은 사용자가 동시에 여러 파일 업로드             │ │
│  │ 테스트: test_concurrent_upload_handling()              │ │
│  │        test_validate_user_quota()                      │ │
│  │        test_rate_limiting()                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🔐 보안 시나리오 (Security Cases)                          │
│  "악성 파일 업로드 시도, 권한 우회 시도"                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 악성코드 파일 → 보안검증 → 업로드 차단           │ │
│  │ 테스트: test_validate_security_rules()                 │ │
│  │        test_malicious_file_detection()                 │ │
│  │        test_unauthorized_deletion_attempt()            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 5. 구현 순서 제안

```
┌───────────────── 구현 단계별 로드맵 ─────────────────┐
│                                                   │
│  1️⃣ 1단계: 🟦 필수 (MVP) - 핵심 파일 기능          │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 파일 검증 (기반 기능)                     │ │
│  │ ① test_validate_file_type() 🟢 초급 ⚡병렬    │ │
│  │ ② test_validate_file_size() 🟢 초급 ⚡병렬    │ │
│  │ ③ test_validate_security_rules() 🟡 중급 ⚡병렬 │ │
│  │                                             │ │
│  │ 📋 파일 저장 (기반 기능)                     │ │
│  │ ④ test_generate_file_path() 🟢 초급 ⚡병렬    │ │
│  │ ⑤ test_save_physical_file() 🟡 중급 🔄순차   │ │
│  │                                             │ │
│  │ 📋 업로드 통합 플로우                        │ │
│  │ ⑥ test_full_upload_flow() 🔴 고급 🔄순차     │ │
│  │ ⑦ test_upload_error_handling() 🟡 중급 🔄순차 │ │
│  │                                             │ │
│  │ 🔌 API 계약 검증                           │ │
│  │ ⑧ test_upload_api_contract() 🟢 초급 🔄순차  │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  2️⃣ 2단계: 🟡 권장 (안정화) - 조회 및 삭제 기능    │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 파일 조회 기능                            │ │
│  │ ① test_file_serving_flow() 🟡 중급 🔄순차    │ │
│  │ ② test_metadata_retrieval() 🟢 초급 ⚡병렬   │ │
│  │ ③ test_file_not_found_handling() 🟢 초급 ⚡병렬 │ │
│  │                                             │ │
│  │ 📋 파일 삭제 기능                            │ │
│  │ ④ test_check_delete_permission() 🟡 중급 ⚡병렬 │ │
│  │ ⑤ test_complete_deletion_flow() 🔴 고급 🔄순차 │ │
│  │ ⑥ test_reference_cleanup() 🔴 고급 🔄순차    │ │
│  │                                             │ │
│  │ 🔌 API 계약 확장                           │ │
│  │ ⑦ test_retrieval_api_contract() 🟢 초급 🔄순차 │ │
│  │ ⑧ test_deletion_api_contract() 🟢 초급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  3️⃣ 3단계: 🟢 선택 (최적화) - 고급 기능 및 최적화   │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 성능 및 보안 강화                         │ │
│  │ ① test_concurrent_upload_handling() 🔴 고급 🔄순차 │ │
│  │ ② test_malicious_file_detection() 🔴 고급 🔄순차 │ │
│  │ ③ test_rate_limiting() 🟡 중급 🔄순차        │ │
│  │                                             │ │
│  │ 📋 사용자 경험 개선                          │ │
│  │ ④ test_validate_user_quota() 🟡 중급 ⚡병렬   │ │
│  │ ⑤ test_cache_headers() 🟢 초급 ⚡병렬        │ │
│  │ ⑥ test_file_metadata_extraction() 🟡 중급 ⚡병렬 │ │
│  │                                             │ │
│  │ 🔌 고급 계약 테스트                         │ │
│  │ ⑦ test_error_response_contracts() 🟡 중급 🔄순차 │ │
│  │ ⑧ test_security_response_contracts() 🔴 고급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  💡 구현 팁:                                    │
│  • ⚡병렬: 독립적 실행 가능 (상태 변경 없음)        │
│  • 🔄순차: 순차 실행 필요 (파일시스템/DB 사용)     │
│  • 🟢 초급 → 🟡 중급 → 🔴 고급 순서로 진행       │
│  • 1단계 완료 시점에서 기본 파일 업로드 기능 동작    │
│  • 2단계 완료 시점에서 완전한 파일 관리 시스템 구축  │
│                                                   │
└───────────────────────────────────────────────────┘
```

---

## 6. 테스트 환경 및 Mock 정책

### Mock 사용 정책

**허용 조건**: 이미 구현 완료된 기능 중 호출 비용이 높은 경우

```python
def test_file_upload_with_notification():
    """
    🚨 Mock 사용: NotificationService
    이유: 외부 이메일 서비스 호출로 인한 네트워크 의존성
    대안 없이 진행 시: 테스트 불안정성, 실행 시간 증가
    """
    # 이미 구현 완료된 NotificationService를 Mock으로 처리
    pass

def test_file_storage_without_mock():
    """
    Mock 미사용: 로컬 파일시스템 저장
    이유: 빠른 실행, 실제 파일 I/O 검증 필요
    """
    # 실제 임시 디렉토리에 파일 저장/삭제로 테스트
    pass
```

### 테스트 환경 구성

```python
# conftest.py 설정
@pytest.fixture
def temp_upload_dir():
    """테스트용 임시 업로드 디렉토리"""
    temp_dir = Path("test_uploads")
    temp_dir.mkdir(exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)  # 테스트 후 정리

@pytest.fixture  
def sample_image_file():
    """테스트용 샘플 이미지 파일"""
    # 1x1 PNG 이미지 생성
    img_data = base64.b64decode(MINIMAL_PNG_BASE64)
    return BytesIO(img_data)

@pytest.fixture
def mock_db_collection():
    """테스트용 MongoDB 컬렉션 Mock"""
    # 실제 DB 연결 없이 MongoDB 동작 시뮬레이션
    pass
```

### 프론트엔드 통합 테스트 연계

```python
def test_frontend_integration_checklist():
    """
    실제 사용자 플로우 기반 통합 테스트 체크리스트
    
    ✅ API 구현 완료 후 즉시 수행:
    1. HTML UI에서 파일 선택 → 업로드 요청 → 성공 응답
    2. 업로드된 파일 → 게시글에 이미지 표시 → 정상 렌더링
    3. 오류 상황 → 적절한 사용자 메시지 → UI 상태 복구
    4. 파일 삭제 → UI에서 이미지 제거 → 깨진 링크 없음
    
    🔍 발견된 이슈 기반 우선순위 재조정:
    - 사용자가 자주 겪는 오류 → 관련 테스트 우선순위 상향
    - UI 렌더링 문제 → API 응답 형식 테스트 강화
    - 성능 이슈 → 파일 크기/처리 시간 테스트 추가
    """
    pass
```

이 테스트 계획서는 File API의 체계적인 테스트 구현을 위한 로드맵을 제공하며, 실제 사용자 플로우와 연계된 실용적인 테스트 설계를 지원합니다.