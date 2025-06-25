# 파일 API 테스트 코드 구성 개요

## 📚 테스트 모듈 구조와 의존성 관계

### 전체 테스트 모듈 계층
```
tests/
├── unit/
│   ├── test_file_validation.py       # 🔵 기반 (의존성 없음)
│   ├── test_file_storage.py          # 🔵 기반 (의존성 없음)
│   ├── test_file_metadata.py         # 🟡 조합 (validation 의존)
│   └── test_file_repository.py       # 🟡 조합 (metadata + storage 의존)
├── integration/
│   ├── test_file_upload_api.py       # 🔴 통합 (모든 기능 의존)
│   ├── test_file_retrieve_api.py     # 🔴 통합 (storage + metadata 의존)
│   └── test_file_management_api.py   # 🔴 통합 (모든 기능 의존)
└── contract/
    └── test_file_api_contract.py     # 🟠 계약 (API 의존)
```

### 🔗 기능 플로우와 테스트 함수 매핑

**파일 업로드 플로우**: [파일 선택 → 검증 → 저장 → 메타데이터 생성 → DB 저장 → 응답]
- `test_validate_file_type()`: 파일 선택 후 첫 번째 검증
- `test_validate_file_size()`: 크기 제한 검증
- `test_store_file_data()`: 실제 파일 저장
- `test_extract_file_metadata()`: 메타데이터 생성
- `test_save_file_document()`: DB 저장
- `test_upload_file_flow()`: 전체 플로우 통합

**파일 조회 플로우**: [요청 → ID 검증 → 파일 조회 → 권한 확인 → 파일 반환]
- `test_find_files_by_attachment()`: DB에서 파일 정보 조회
- `test_get_file_by_id()`: 실제 파일 반환

**파일 삭제 플로우**: [요청 → 권한 확인 → 참조 정리 → 파일 삭제 → 응답]
- `test_delete_file_references()`: 참조 관계 정리
- `test_delete_file_flow()`: 전체 삭제 워크플로우

### 📋 우선순위별 테스트 함수 분류

#### 🟦 필수 (MVP) - 시스템 안정성 직결
**정상 시나리오**
- `test_validate_file_type()` 🟢 초급: 파일 형식 기본 검증
- `test_validate_file_size()` 🟢 초급: 파일 크기 제한 검증
- `test_store_file_data()` 🟡 중급: 핵심 파일 저장 로직
- `test_extract_file_metadata()` 🟡 중급: 메타데이터 추출
- `test_save_file_document()` 🟡 중급: DB 저장
- `test_find_files_by_attachment()` 🟡 중급: 파일 조회
- `test_upload_file_flow()` 🔴 고급: 전체 업로드 동작
- `test_upload_with_attachment()` 🔴 고급: 첨부 대상 연결

**API 계약**
- `test_upload_contract()` 🟢 초급: 업로드 API 기본 계약
- `test_retrieve_contract()` 🟢 초급: 조회 API 기본 계약

#### 🟡 권장 (안정화) - 사용자 경험 개선
**오류 처리**
- `test_validate_file_count()` 🟡 중급: 첨부 개수 제한 검증
- `test_validate_file_security()` 🔴 고급: 악성 파일 차단
- `test_upload_error_handling()` 🔴 고급: API 오류 처리
- `test_delete_file_flow()` 🔴 고급: 파일 삭제 워크플로우

**데이터 관리**
- `test_create_file_record()` 🟡 중급: 메타데이터 관리 강화
- `test_delete_file_references()` 🔴 고급: 참조 관계 정리

#### 🟢 선택 (최적화) - 고급 기능
**성능 최적화**
- `test_generate_file_path()` 🟢 초급: 경로 생성 최적화
- `test_cleanup_temp_files()` 🟡 중급: 임시 파일 정리
- `test_update_attachment_references()` 🟡 중급: 참조 관계 관리

### ⚡ 병렬/순차 실행 그룹

#### 병렬 실행 그룹 (독립적, 상태 변경 없음)
- **검증 함수들**: `test_validate_file_type()`, `test_validate_file_size()`, `test_validate_file_count()`
- **순수 함수들**: `test_generate_file_path()`, `test_extract_file_metadata()`
- **읽기 전용**: `test_find_files_by_attachment()`

#### 순차 실행 그룹 (공유 리소스, 상태 변경)
- **파일 시스템**: `test_store_file_data()`, `test_cleanup_temp_files()`
- **DB 변경**: `test_save_file_document()`, `test_delete_file_references()`
- **API 통합**: `test_upload_file_flow()`, `test_upload_error_handling()`

### 🚨 Mock 사용 정책

#### Mock 필요한 경우
- `ExternalNotificationService`: 이메일/푸시 알림 (네트워크 의존성)
- `DatabaseConnection`: 테스트 DB 분리 필요 시
- `CloudStorageService`: 외부 클라우드 연동 (비용/지연 고려)

#### Mock 불필요한 경우
- 파일 검증 함수들 (순수 함수)
- 경로 생성 함수 (계산 로직)
- 로컬 파일 시스템 조작 (테스트 환경에서 격리 가능)

### 🔄 사용자 시나리오별 테스트 매핑

#### 주 시나리오: 게시글 작성 시 이미지 첨부
1. **파일 선택**: `test_validate_file_type()`, `test_validate_file_size()`
2. **업로드 진행**: `test_upload_file_flow()`
3. **게시글 연결**: `test_upload_with_attachment()`
4. **완료 확인**: `test_find_files_by_attachment()`

#### 예외 시나리오: 다양한 오류 상황
1. **형식 오류**: `test_validate_file_type()` (UNSUPPORTED_FILE_TYPE)
2. **크기 초과**: `test_validate_file_size()` (FILE_TOO_LARGE)
3. **개수 초과**: `test_validate_file_count()` (FILE_COUNT_EXCEEDED)
4. **보안 위협**: `test_validate_file_security()` (MALICIOUS_FILE)
5. **저장 실패**: `test_upload_error_handling()` (UPLOAD_FAILED)

### 📊 구현 순서 제안

#### 1단계: 기반 계층 (🔵)
1. `test_validate_file_type()` 🟢
2. `test_validate_file_size()` 🟢
3. `test_generate_file_path()` 🟢
4. `test_store_file_data()` 🟡

#### 2단계: 조합 계층 (🟡)
1. `test_extract_file_metadata()` 🟡
2. `test_save_file_document()` 🟡
3. `test_find_files_by_attachment()` 🟡

#### 3단계: 통합 계층 (🔴)
1. `test_upload_file_flow()` 🔴
2. `test_upload_with_attachment()` 🔴
3. `test_upload_contract()` 🟢

#### 4단계: 안정화 (권장)
1. `test_validate_file_count()` 🟡
2. `test_upload_error_handling()` 🔴
3. `test_delete_file_flow()` 🔴

### 🎯 MVP 완료 기준

#### 핵심 기능 동작 확인
- ✅ 파일 업로드 (정상 시나리오)
- ✅ 파일 조회 (ID 기반)
- ✅ 기본 검증 (형식, 크기)
- ✅ API 계약 준수

#### 안정성 확보
- ✅ 기본 오류 처리
- ✅ 파일 저장 안정성
- ✅ DB 저장 무결성

이 구조를 통해 TDD 방식으로 체계적이고 안정적인 파일 API를 구현할 수 있습니다.