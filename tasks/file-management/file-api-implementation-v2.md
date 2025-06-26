# File Management - File API Implementation v2

**Feature Group**: File Management  
**Task List 제목**: 파일 API 구현 v2 (File API Implementation v2)  
**최초 작성 시각**: 2025-06-26 15:00:00 KST  
**버전**: 2.0 - 사용자 플로우 검증 기반 단계별 구현

## 개요

파일 업로드, 조회, 삭제 기능을 포함한 완전한 파일 관리 API를 TDD 방식으로 구현합니다. 제공된 테스트 코드 제안서와 HTML UI 분석을 바탕으로 실제 사용자 플로우를 검증하면서 단계별로 구현하는 전략을 채택합니다.

## 3가지 구상 버전

### 🔹 Version A: 기능 중심 구현 (Function-First)
- 모든 기능 모듈을 완전히 구현한 후 통합
- 빠른 기능 완성도 달성
- 통합 시점에서 오류 발견 위험

### 🔹 Version B: 계층별 구현 (Layer-First)  
- 검증→저장→메타데이터→API 순으로 계층별 완전 구현
- 구조적 안정성 확보
- 사용자 검증이 늦어져 방향 수정 어려움

### 🔹 Version C: 사용자 플로우 검증 기반 (User-Flow-First) **⭐ 권장**
- MVP 핵심 기능 구현 → 즉시 사용자 검증 → 피드백 반영
- 각 단계 완료 시마다 HTML UI로 실제 사용성 테스트
- 사용자 요구사항 변화에 빠른 대응 가능

## 🎯 최종 제안: Version C (사용자 플로우 검증 기반)

### 선택 이유
1. **실용적 가치 우선**: 각 단계에서 사용자에게 즉시 가치 제공
2. **리스크 최소화**: 조기 검증으로 잘못된 방향 진행 방지
3. **HTML UI 활용**: 제공된 UI.html을 활용한 실제 사용성 검증
4. **피드백 기반 최적화**: 사용자 피드백을 다음 단계 우선순위에 반영

---

## Task 목록 (사용자 플로우 검증 기반)

### 🚀 1단계: MVP 핵심 기능 (즉시 사용자 검증)

#### Task 1: File Validator Module (기반)
**파일**: `src/services/file_validator.py`  
**설명**: 파일 업로드 전 필수 검증 로직  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟢 낮음 - 순수 함수, 외부 의존성 없음  
**실행 방식**: ⚡ 병렬 가능

##### Subtasks
- **Subtask 1.1**: `validate_file_type()` 함수 구현
  - 대응 테스트: `test_validate_file_type()`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 허용된 이미지 형식 검증 (jpg, jpeg, png, gif, webp)
  
- **Subtask 1.2**: `validate_file_size()` 함수 구현
  - 대응 테스트: `test_validate_file_size()`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 파일 크기 제한 검증 (최대 5MB)
  
- **Subtask 1.3**: `validate_file_extension()` 함수 구현
  - 대응 테스트: `test_validate_file_extension()`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 확장자와 MIME 타입 일치성 검증

#### Task 2: File Storage Module (기반)
**파일**: `src/services/file_storage.py`  
**설명**: 파일 시스템 저장 및 경로 관리  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟡 중간 - 파일 시스템 I/O 의존성  
**실행 방식**: 🔄 순차 (파일 시스템 안전성)

##### Subtasks
- **Subtask 2.1**: `generate_file_path()` 함수 구현
  - 대응 테스트: `test_generate_file_path()`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: UUID 기반 고유 파일명 및 년/월별 디렉토리 경로 생성
  
- **Subtask 2.2**: `save_file_to_disk()` 함수 구현
  - 대응 테스트: `test_save_file_to_disk()`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 실제 파일 데이터를 디스크에 저장
  
- **Subtask 2.3**: `create_directory_structure()` 함수 구현
  - 대응 테스트: `test_create_directory_structure()`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 년/월/타입별 디렉토리 자동 생성

#### Task 3: File Metadata Module (조합)
**파일**: `src/services/file_metadata.py`  
**설명**: 파일 메타데이터 추출 및 관리  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟡 중간 - Task 1 의존성  
**의존성**: Task 1 완료 필요  
**실행 방식**: ⚡ 병렬 가능

##### Subtasks
- **Subtask 3.1**: `extract_file_metadata()` 함수 구현
  - 대응 테스트: `test_extract_file_metadata()`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: 파일 크기, 형식, 수정 시간 등 메타데이터 추출
  
- **Subtask 3.2**: `create_file_document()` 함수 구현
  - 대응 테스트: `test_create_file_document()`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: MongoDB 저장용 파일 문서 구조 생성

#### Task 4: File Repository Module (데이터 계층)
**파일**: `src/repositories/file_repository.py`  
**설명**: 파일 데이터 접근 계층  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟡 중간 - Task 2,3 의존성, MongoDB 연동  
**의존성**: Task 2, 3 완료 필요  
**Social Unit**: Task 3과 함께 구현 권장  
**실행 방식**: 🔄 순차 (데이터 일관성)

##### Subtasks
- **Subtask 4.1**: `save_file_record()` 함수 구현
  - 대응 테스트: `test_save_file_record()`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 파일 메타데이터를 MongoDB에 저장
  
- **Subtask 4.2**: `find_file_by_id()` 함수 구현
  - 대응 테스트: `test_find_file_by_id()`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 파일 ID로 메타데이터 조회

#### Task 5: File Upload API Module (통합)
**파일**: `src/routers/file_upload.py`  
**설명**: 파일 업로드 REST API 엔드포인트  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🔴 높음 - 모든 하위 모듈 의존성  
**의존성**: Task 1, 2, 3, 4 완료 필요  
**Integration Test**: 전체 업로드 워크플로우 통합  
**실행 방식**: 🔄 순차 (통합 복잡성)

##### Subtasks
- **Subtask 5.1**: `upload_file()` API 엔드포인트 구현
  - 대응 테스트: `test_successful_upload_flow()`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: POST /api/files/upload 전체 워크플로우
  
- **Subtask 5.2**: `upload_request_validation()` 구현
  - 대응 테스트: `test_upload_request_contract()`
  - 난이도: 🟢 초급 | 실행: 🔄 순차
  - 기능: multipart/form-data 요청 검증

#### Task 6: API Contract Validation (품질 보증)
**파일**: `tests/contract/test_file_api_contract.py`  
**설명**: API 응답 계약 검증  
**우선순위**: 🟦 필수 (MVP)  
**리스크**: 🟢 낮음 - 스키마 검증만  
**의존성**: Task 5 완료 필요  
**실행 방식**: ⚡ 병렬 가능

##### Subtasks
- **Subtask 6.1**: `validate_upload_response()` 함수 구현
  - 대응 테스트: `test_upload_response_contract()`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 업로드 성공 응답 스키마 검증
  
- **Subtask 6.2**: `validate_error_response()` 함수 구현
  - 대응 테스트: `test_error_response_contract()`
  - 난이도: 🟢 초급 | 실행: ⚡ 병렬
  - 기능: 오류 응답 표준 형식 검증

### 🎯 1단계 완료 시점 - 즉시 사용자 플로우 검증

#### 📱 HTML UI 통합 테스트 (필수)
1. **기본 업로드 테스트**: UI.html에서 파일 선택 → 업로드 → 성공 응답 확인
2. **오류 처리 테스트**: 크기/형식 초과 파일 업로드 시 적절한 오류 메시지 표시
3. **사용자 경험 평가**: 업로드 속도, UI 반응성, 메시지 명확성

#### 🔍 발견 문제점 기반 2단계 우선순위 조정
- **API 응답 누락 필드** → 즉시 추가 (우선순위 최상)
- **불친절한 오류 메시지** → 2단계 우선순위 상향
- **성능 이슈** → 최적화 기능 우선순위 상향

---

### 🚀 2단계: 사용자 경험 개선 (1단계 피드백 반영)

#### Task 7: Enhanced File Validation (보안 강화)
**파일**: `src/services/file_validator.py` (확장)  
**설명**: 고급 파일 검증 기능 추가  
**우선순위**: 🟡 권장 (1단계 검증 결과에 따라 조정)  
**리스크**: 🟡 중간 - 보안 검증 복잡성  
**조건부 구현**: 1단계에서 보안 이슈 발견 시 우선 처리

##### Subtasks
- **Subtask 7.1**: `validate_mime_type()` 함수 구현
  - 대응 테스트: `test_validate_mime_type()`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: MIME 타입 보안 검증
  
- **Subtask 7.2**: `validate_file_signature()` 함수 구현
  - 대응 테스트: `test_validate_file_signature()`
  - 난이도: 🔴 고급 | 실행: ⚡ 병렬
  - 기능: 파일 헤더 시그니처 검증

#### Task 8: Multiple File Upload (다중 업로드)
**파일**: `src/routers/file_upload.py` (확장)  
**설명**: 다중 파일 업로드 기능  
**우선순위**: 🟡 권장 (1단계 검증 결과에 따라 조정)  
**리스크**: 🔴 높음 - 복잡한 트랜잭션 처리  
**조건부 구현**: 1단계에서 다중 업로드 요구 발견 시 우선 처리

##### Subtasks
- **Subtask 8.1**: `upload_multiple_files()` API 구현
  - 대응 테스트: `test_multiple_files_upload()`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 여러 파일 동시 업로드 처리
  
- **Subtask 8.2**: `validate_attachment_limits()` 함수 구현
  - 대응 테스트: `test_upload_with_attachment()`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 첨부 유형별 개수 제한 검증 (게시글: 5개, 댓글: 1개)

#### Task 9: File Retrieval API (조회 기능)
**파일**: `src/routers/file_retrieval.py`  
**설명**: 파일 조회 REST API  
**우선순위**: 🟡 권장  
**리스크**: 🟢 낮음 - 읽기 전용 작업  
**의존성**: Task 4 완료 필요

##### Subtasks
- **Subtask 9.1**: `get_file_by_id()` API 구현
  - 대응 테스트: `test_get_file_by_id()`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: GET /api/files/{file_id} 파일 바이너리 반환
  
- **Subtask 9.2**: `get_file_metadata()` API 구현
  - 대응 테스트: `test_get_file_metadata()`
  - 난이도: 🟡 중급 | 실행: ⚡ 병렬
  - 기능: GET /api/files/{file_id}/info 메타데이터 조회

#### Task 10: Enhanced Error Handling (오류 처리 개선)
**파일**: `src/services/error_handler.py`  
**설명**: 향상된 오류 처리 및 사용자 메시지  
**우선순위**: 🟡 권장 (1단계 검증 결과에 따라 조정)  
**리스크**: 🟢 낮음 - 메시지 처리만  
**조건부 구현**: 1단계에서 오류 메시지 개선 필요 발견 시 우선 처리

##### Subtasks
- **Subtask 10.1**: `format_error_messages()` 함수 구현
  - 대응 테스트: `test_upload_error_scenarios()`
  - 난이도: 🟡 중급 | 실행: 🔄 순차
  - 기능: 다양한 오류 상황별 사용자 친화적 메시지

### 🎯 2단계 완료 시점 - 사용자 경험 재검증

#### 📱 개선된 기능의 사용성 재검증
1. **다중 파일 업로드** 사용자 직관성 확인
2. **개선된 오류 메시지** 실제 도움 여부 검증
3. **파일 조회 속도** 사용자 기대 수준 확인

#### 🔍 3단계 우선순위 최종 결정
- 사용자가 실제 필요로 하는 고급 기능만 3단계에서 구현
- 파일 삭제 기능 필수 여부 재확인
- 성능 최적화 기능의 실제 필요성 검증

---

### 🚀 3단계: 고급 기능 (사용자 검증 완료된 것만)

#### Task 11: File Deletion API (파일 관리)
**파일**: `src/routers/file_management.py`  
**설명**: 파일 삭제 및 관리 API  
**우선순위**: 🟢 선택 (2단계 검증 결과에 따라 결정)  
**리스크**: 🔴 높음 - 복잡한 참조 관리  
**조건부 구현**: 2단계 검증에서 파일 관리 기능 필요 시에만

##### Subtasks
- **Subtask 11.1**: `delete_file()` API 구현
  - 대응 테스트: `test_delete_file_success()`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: DELETE /api/files/{file_id} 파일 삭제
  
- **Subtask 11.2**: `cleanup_file_references()` 함수 구현
  - 대응 테스트: `test_delete_with_cleanup()`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 파일 삭제 시 모든 참조 정리

#### Task 12: Security Enhancement (보안 강화)
**파일**: `src/services/security_validator.py`  
**설명**: 고급 보안 검증 기능  
**우선순위**: 🟢 선택  
**리스크**: 🔴 높음 - 복잡한 보안 로직  
**조건부 구현**: 보안 요구사항 발견 시에만

##### Subtasks
- **Subtask 12.1**: `detect_malicious_files()` 함수 구현
  - 대응 테스트: `test_malicious_file_detection()`
  - 난이도: 🔴 고급 | 실행: ⚡ 병렬
  - 기능: 악성 파일 감지 및 차단

#### Task 13: Performance Optimization (성능 최적화)
**파일**: `src/services/file_optimizer.py`  
**설명**: 파일 처리 성능 최적화  
**우선순위**: 🟢 선택  
**리스크**: 🔴 높음 - 복잡한 최적화 로직  
**조건부 구현**: 2단계 검증에서 성능 이슈 발견 시에만

##### Subtasks
- **Subtask 13.1**: `optimize_concurrent_uploads()` 함수 구현
  - 대응 테스트: `test_concurrent_upload_handling()`
  - 난이도: 🔴 고급 | 실행: 🔄 순차
  - 기능: 동시 업로드 성능 최적화

---

## 구현 순서 및 검증 전략

### 🎯 각 단계별 필수 검증 항목

#### 🔍 1단계 완료 후 즉시 검증
- ✅ HTML UI에서 파일 선택 후 업로드 정상 작동
- ✅ 업로드된 이미지가 게시글에서 올바르게 표시
- ✅ 파일 크기/형식 오류 시 사용자 이해 가능한 메시지
- ✅ API 응답에 프런트엔드 필요 데이터 모두 포함
- ✅ 업로드 속도가 사용자 기대 수준

#### 🔍 2단계 완료 후 재검증
- ✅ 다중 파일 업로드 사용자 직관성
- ✅ 개선된 오류 메시지 실제 도움 여부
- ✅ 파일 조회 기능 사용자 워크플로우 적합성
- ✅ 전체적인 파일 관리 경험 만족도

#### 🔍 3단계 완료 후 최종 검증
- ✅ 모든 파일 기능 실제 업무 활용도
- ✅ 보안 기능 적절한 수준 유지
- ✅ 성능 최적화 체감 가능한 개선
- ✅ 시스템 전체 안정적 운영

## 리스크 관리 및 대응 방안

### 모듈 간 관계와 리스크 분석

```
┌─────────────────── 모듈 의존성 및 리스크 맵 ──────────────────┐
│                                                             │
│  🔵 기반 계층 (독립적 - 리스크 낮음)                          │
│  ┌─────────────────┐                                        │
│  │ File Validator  │ 🟢 낮음 - 순수 함수                     │
│  │ File Storage    │ 🟡 중간 - 파일 I/O 의존성               │
│  └─────────────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  🟡 조합 계층 (기반 기능 활용 - 리스크 중간)                   │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ File Metadata   │    │ File Repository │                 │
│  │ 🟡 중간 - 데이터 │    │ 🟡 중간 - DB 의존성│                 │
│  └─────────────────┘    └─────────────────┘                 │
│           │                       │                         │
│           └───────┬───────────────┘                         │
│                   ▼                                         │
│  🔴 통합 계층 (모든 기능 통합 - 리스크 높음)                    │
│  ┌─────────────────┐                                        │
│  │ File Upload API │ 🔴 높음 - 전체 워크플로우 복잡성          │
│  └─────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 리스크별 대응 전략

| 리스크 레벨 | 대상 Task | 대응 방안 |
|------------|----------|----------|
| 🔴 높음 | Task 5, 8, 11, 12, 13 | 충분한 사전 테스트, 단계별 검증, 롤백 계획 |
| 🟡 중간 | Task 2, 3, 4, 7, 10 | Mock 활용, 격리된 테스트 환경, 의존성 관리 |
| 🟢 낮음 | Task 1, 6, 9 | 병렬 개발 가능, 빠른 구현 |

## MVP 완료 기준

### 🟦 필수 기능 (1단계 - MVP)
- ✅ 기본 파일 검증 (Task 1)
- ✅ 파일 저장 시스템 (Task 2)
- ✅ 메타데이터 관리 (Task 3)
- ✅ 데이터베이스 연동 (Task 4)
- ✅ 업로드 API (Task 5)
- ✅ API 계약 검증 (Task 6)
- ✅ HTML UI 통합 검증 완료

### 🟡 권장 기능 (2단계 - 안정화)
- 고급 검증 기능 (Task 7)
- 다중 파일 업로드 (Task 8)
- 파일 조회 API (Task 9)
- 향상된 오류 처리 (Task 10)

### 🟢 선택 기능 (3단계 - 최적화)
- 파일 삭제 기능 (Task 11)
- 보안 강화 (Task 12)
- 성능 최적화 (Task 13)

## 핵심 구현 원칙

### 사용자 플로우 검증 우선
- 🔄 각 단계 완료 → 즉시 HTML UI에서 실제 사용자 환경 테스트
- 📊 사용자 관점 피드백 → 다음 단계 우선순위 재조정
- 🎯 사용자가 실제로 필요하지 않는 기능은 구현하지 않음

### TDD 원칙 준수
- **신뢰성**: 모든 함수는 테스트 통과를 전제로 신뢰성 보장
- **누적 가능성**: 의존성 고려한 순차 개발로 안정성 누적
- **오류 국지성**: 독립적 단위 테스트로 문제 범위 명확화

### 효율적 개발 전략
- ⚡ 병렬 가능한 테스트는 동시 진행으로 효율성 확보
- 🟦 1단계(MVP) 완료만으로도 실용적 가치 제공 가능
- 📱 HTML UI를 활용한 지속적 사용자 경험 검증

## 성공 지표

### 1단계 성공 지표
- HTML UI에서 파일 업로드 성공률 95% 이상
- 오류 메시지 사용자 이해도 100%
- 업로드 응답 시간 3초 이내

### 2단계 성공 지표
- 다중 파일 업로드 성공률 90% 이상
- 사용자 만족도 조사 결과 4.0/5.0 이상
- 파일 조회 응답 시간 1초 이내

### 3단계 성공 지표
- 전체 파일 관리 시스템 안정성 99% 이상
- 보안 검증 기능 오탐률 5% 이하
- 성능 최적화로 처리 속도 50% 이상 개선

---

**이 Task List v2는 사용자 플로우 검증을 중심으로 한 단계별 구현 전략을 제시하며, 실제 사용자 요구사항에 기반한 우선순위 조정을 통해 최적의 개발 효율성과 사용자 만족도를 달성하는 것을 목표로 합니다.**