# File Management - File API Implementation

**Feature Group**: File Management  
**Task List 제목**: 파일 API 구현 (File API Implementation)  
**최초 작성 시각**: 2025-06-25 12:00:00 KST

## 개요

파일 업로드, 조회, 삭제 기능을 포함한 완전한 파일 관리 API를 TDD 방식으로 구현합니다. 이미지 파일 첨부를 통한 게시글 및 댓글 기능 강화가 주요 목표입니다.

## Task 목록

### Task 1: File Validation Module
**파일**: `src/services/file_validation.py`  
**설명**: 파일 업로드 전 필수 검증 로직 구현  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟢 낮음 - 순수 함수, 외부 의존성 없음

#### Subtasks
- **Subtask 1.1**: `test_validate_file_type()` 
  - 대응 테스트: `TestFileValidation.test_validate_file_type`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: MIME 타입과 확장자 이중 검증 (jpg, png, gif, webp)
  
- **Subtask 1.2**: `test_validate_file_size()` 
  - 대응 테스트: `TestFileValidation.test_validate_file_size`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 파일 크기 제한 검증 (5MB 제한)
  
- **Subtask 1.3**: `test_validate_file_count()` 
  - 대응 테스트: `TestFileValidation.test_validate_file_count`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: 첨부 개수 제한 (post: 5개, comment: 1개, profile: 1개)
  
- **Subtask 1.4**: `test_validate_file_security()` 
  - 대응 테스트: `TestFileValidation.test_validate_file_security`
  - 난이도: 🔴 고급 | 실행: ⚡ 병렬
  - 기능: 악성 파일 차단 및 보안 검증

---

### Task 2: File Storage Module
**파일**: `src/services/file_storage.py`  
**설명**: 파일 시스템 저장 및 경로 관리  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟡 중간 - 파일 시스템 의존성, I/O 오류 가능성

#### Subtasks
- **Subtask 2.1**: `test_generate_file_path()` 
  - 대응 테스트: `TestFileStorage.test_generate_file_path`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: UUID 기반 고유 파일명 및 월별 디렉토리 경로 생성
  
- **Subtask 2.2**: `test_store_file_data()` 
  - 대응 테스트: `TestFileStorage.test_store_file_data`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 실제 파일 데이터 저장 및 디렉토리 관리
  
- **Subtask 2.3**: `test_cleanup_temp_files()` 
  - 대응 테스트: `TestFileStorage.test_cleanup_temp_files`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 임시 파일 정리 및 저장 공간 관리

---

### Task 3: File Metadata Module
**파일**: `src/services/file_metadata.py`  
**설명**: 파일 메타데이터 추출 및 관리  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟡 중간 - Task 1(검증) 의존성, 데이터 구조 복잡성  
**의존성**: Task 1 완료 필요

#### Subtasks
- **Subtask 3.1**: `test_extract_file_metadata()` 
  - 대응 테스트: `TestFileMetadata.test_extract_file_metadata`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: 파일 속성 추출 및 메타데이터 구조화
  
- **Subtask 3.2**: `test_create_file_record()` 
  - 대응 테스트: `TestFileMetadata.test_create_file_record`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: MongoDB 문서 구조로 메타데이터 변환
  
- **Subtask 3.3**: `test_update_attachment_references()` 
  - 대응 테스트: `TestFileMetadata.test_update_attachment_references`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 게시글/댓글과 파일 간 양방향 참조 관리

---

### Task 4: File Repository Module
**파일**: `src/repositories/file_repository.py`  
**설명**: 파일 데이터 접근 계층 구현  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟡 중간 - Task 2,3 의존성, MongoDB 연동 복잡성  
**의존성**: Task 2, 3 완료 필요  
**Social Unit**: Task 3과 함께 구현 권장

#### Subtasks
- **Subtask 4.1**: `test_save_file_document()` 
  - 대응 테스트: `TestFileRepository.test_save_file_document`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 파일 문서 MongoDB 저장 및 인덱스 적용
  
- **Subtask 4.2**: `test_find_files_by_attachment()` 
  - 대응 테스트: `TestFileRepository.test_find_files_by_attachment`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: 첨부 대상별 파일 목록 조회
  
- **Subtask 4.3**: `test_delete_file_references()` 
  - 대응 테스트: `TestFileRepository.test_delete_file_references`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 파일 삭제 시 모든 참조 정리

---

### Task 5: File Upload API Module
**파일**: `src/routers/file_upload.py`  
**설명**: 파일 업로드 REST API 엔드포인트  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🔴 높음 - 모든 하위 모듈 의존성, HTTP 처리 복잡성  
**의존성**: Task 1, 2, 3, 4 완료 필요  
**Integration Test**: 전체 업로드 워크플로우 통합

#### Subtasks
- **Subtask 5.1**: `test_upload_file_flow()` 
  - 대응 테스트: `TestFileUploadAPI.test_upload_file_flow`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: POST /api/files/upload 전체 워크플로우
  
- **Subtask 5.2**: `test_upload_with_attachment()` 
  - 대응 테스트: `TestFileUploadAPI.test_upload_with_attachment`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 게시글/댓글 첨부와 함께 업로드 처리
  
- **Subtask 5.3**: `test_upload_error_handling()` 
  - 대응 테스트: `TestFileUploadAPI.test_upload_error_handling`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 다양한 오류 상황별 적절한 응답 처리

---

### Task 6: File Retrieve API Module
**파일**: `src/routers/file_retrieve.py`  
**설명**: 파일 조회 REST API 엔드포인트  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟢 낮음 - Task 2,4 의존성, 읽기 전용 작업  
**의존성**: Task 2, 4 완료 필요

#### Subtasks
- **Subtask 6.1**: `test_get_file_by_id()` 
  - 대응 테스트: `TestFileRetrieveAPI.test_get_file_by_id`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: GET /api/files/{file_id} 파일 바이너리 반환
  
- **Subtask 6.2**: `test_get_file_info()` 
  - 대응 테스트: `TestFileRetrieveAPI.test_get_file_info`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: GET /api/files/{file_id}/info 메타데이터 조회
  
- **Subtask 6.3**: `test_get_attachment_files()` 
  - 대응 테스트: `TestFileRetrieveAPI.test_get_attachment_files`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: GET /api/posts/{slug}/files 첨부 파일 목록

---

### Task 7: File Management API Module
**파일**: `src/routers/file_management.py`  
**설명**: 파일 삭제 및 관리 REST API 엔드포인트  
**우선순위**: 🟡 권장 (안정화)  
**리스크**: 🔴 높음 - 모든 모듈 의존성, 트랜잭션 복잡성  
**의존성**: 모든 Task 완료 필요

#### Subtasks
- **Subtask 7.1**: `test_delete_file_flow()` 
  - 대응 테스트: `TestFileManagementAPI.test_delete_file_flow`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: DELETE /api/files/{file_id} 전체 삭제 워크플로우
  
- **Subtask 7.2**: `test_cleanup_references()` 
  - 대응 테스트: `TestFileManagementAPI.test_cleanup_references`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 파일 삭제 시 모든 참조 일관성 유지

---

### Task 8: API Contract Validation Module
**파일**: `tests/contract/test_file_api_contract.py`  
**설명**: API 응답 형식 및 계약 검증  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟢 낮음 - API 의존성만, 스키마 검증  
**의존성**: Task 5, 6 완료 필요

#### Subtasks
- **Subtask 8.1**: `test_upload_contract()` 
  - 대응 테스트: `TestFileAPIContract.test_upload_contract`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 업로드 API 응답 스키마 검증
  
- **Subtask 8.2**: `test_retrieve_contract()` 
  - 대응 테스트: `TestFileAPIContract.test_retrieve_contract`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 조회 API 응답 및 헤더 검증
  
- **Subtask 8.3**: `test_error_contract()` 
  - 대응 테스트: `TestFileAPIContract.test_error_contract`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 오류 응답 표준 형식 검증

## 구현 순서

### 1단계: 기반 계층 (병렬 개발 가능)
- Task 1.1, 1.2: 기본 파일 검증
- Task 2.1: 경로 생성 로직

### 2단계: 조합 계층
- Task 2.2: 파일 저장 (Task 1 완료 후)
- Task 3.1: 메타데이터 추출 (Task 1 완료 후)

### 3단계: 데이터 계층
- Task 4.1, 4.2: DB 저장/조회 (Task 2,3 완료 후)

### 4단계: API 계층
- Task 5.1: 업로드 API (Task 4 완료 후)
- Task 6.1: 조회 API (Task 4 완료 후)

### 5단계: 계약 검증
- Task 8.1, 8.2: API 계약 (Task 5,6 완료 후)

## MVP 완료 기준

### 핵심 기능 동작 (🟦 필수)
- ✅ 기본 파일 검증 (Task 1.1, 1.2)
- ✅ 안정적 파일 저장 (Task 2.2)
- ✅ 메타데이터 추출 (Task 3.1)
- ✅ DB 저장/조회 (Task 4.1, 4.2)
- ✅ 업로드 API (Task 5.1, 5.2)
- ✅ 조회 API (Task 6.1, 6.3)
- ✅ API 계약 검증 (Task 8.1, 8.2)

### 안정성 확보 (🟡 권장)
- 고급 검증 (Task 1.3, 1.4)
- 오류 처리 (Task 5.3)
- 삭제 기능 (Task 7.1)

## 리스크 관리

| 리스크 레벨 | Task | 대응 방안 |
|------------|------|----------|
| 🔴 높음 | Task 5, 7 | 충분한 사전 테스트, 단계별 검증 |
| 🟡 중간 | Task 2, 3, 4 | Mock 활용, 격리된 테스트 환경 |
| 🟢 낮음 | Task 1, 6, 8 | 병렬 개발 가능 |

## 주요 특징

- **신뢰성**: 모든 함수는 테스트 통과를 전제로 신뢰성 보장
- **누적 가능성**: 의존성 고려한 순차 개발로 안정성 누적
- **오류 국지성**: 독립적 단위 테스트로 문제 범위 명확화
- **TDD 원칙**: 테스트 우선 개발로 견고한 구현