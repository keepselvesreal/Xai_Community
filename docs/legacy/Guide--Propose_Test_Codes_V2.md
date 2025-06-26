# 테스트 코드 제안 안내

## 📋 문서 목차

1. [목적](#목적)
2. [테스트 코드 제안 가이드라인](#테스트-코드-제안-가이드라인)
   - 2.1 [Classic TDD 원칙 준수](#21-classic-tdd-원칙-준수)
   - 2.2 [기능 간 선후 관계와 의존성 고려](#22-기능-간-선후-관계와-의존성-고려)
   - 2.3 [구현 후 즉시 사용자 플로우 검증](#23-구현-후-즉시-사용자-플로우-검증)
   - 2.4 [테스트 함수 우선순위 분류](#24-테스트-함수-우선순위-분류)
   - 2.5 [테스트 함수 난이도 표시](#25-테스트-함수-난이도-표시)
   - 2.6 [통합 및 E2E 테스트 연계성 제시](#26-통합-및-e2e-테스트-연계성-제시)
   - 2.7 [테스트 전후 상태 명시](#27-테스트-전후-상태-명시)
   - 2.8 [병렬 실행 가능 여부 명시](#28-병렬-실행-가능-여부-명시)
   - 2.9 [API 계약 테스트 포함 (MVP 수준)](#29-api-계약-테스트-포함-mvp-수준)
3. [테스트 코드 제안 개요](#테스트-코드-제안-개요)
   - 3.1 [현재 기능 개발과 관련된 테스트 모듈과 함수 관계](#31-현재-기능-개발과-관련된-테스트-모듈과-함수-관계)
   - 3.2 [기능 플로우와 테스트 함수 매핑](#32-기능-플로우와-테스트-함수-매핑)
   - 3.3 [사용자 시나리오별 테스트 매핑](#33-사용자-시나리오별-테스트-매핑)
   - 3.4 [구현 순서 제안](#34-구현-순서-제안)
4. [테스트 코드 제안 시 점검 목록](#테스트-코드-제안-시-점검-목록)
   - 4.1 [Classic TDD 원칙 준수](#41-classic-tdd-원칙-준수)
   - 4.2 [기능 간 선후 관계와 의존성 고려](#42-기능-간-선후-관계와-의존성-고려)
   - 4.3 [구현 후 즉시 사용자 플로우 검증](#43-구현-후-즉시-사용자-플로우-검증)
   - 4.4 [테스트 함수 우선순위 분류](#44-테스트-함수-우선순위-분류)
   - 4.5 [테스트 함수 난이도 표시](#45-테스트-함수-난이도-표시)
   - 4.6 [통합 및 E2E 테스트 연계성 제시](#46-통합-및-e2e-테스트-연계성-제시)
   - 4.7 [테스트 전후 상태 명시](#47-테스트-전후-상태-명시)
   - 4.8 [병렬 실행 가능 여부 명시](#48-병렬-실행-가능-여부-명시)
   - 4.9 [API 계약 테스트 포함 (MVP 수준)](#49-api-계약-테스트-포함-mvp-수준)

---

## 1. 목적

개발자가 효과적이고 실용적인 테스트 코드를 구상할 수 있도록 체계적인 구성 방향과 예시를 제안합니다.

---

## 2. 테스트 코드 제안 가이드라인

### 2.1 Classic TDD 원칙 준수

**Mock 사용 정책**

- **허용 조건**: 이미 구현 완료된 기능 중 호출 비용이 높은 경우
- **명시 방법**: 테스트 코드에 Mock 사용 이유 기재

```python
def test_file_upload_with_external_service():
    """
    🚨 Mock 사용: EmailNotificationService
    이유: 외부 SMTP 서버 호출로 인한 네트워크 의존성
    대안 없이 진행 시: 테스트 불안정성, 실행 시간 증가
    """
    # 이미 구현 완료된 EmailService를 Mock으로 처리
    pass
```

### 2.2 기능 간 선후 관계와 의존성 고려

**계층적 누적 테스트 설계**

```python
# 1단계: 기반 기능 (의존성 없음)
class TestFileValidator:
    """파일 검증 - 다른 기능에 의존하지 않음"""
    def test_file_size_validation():
        # 순수 함수, 독립적 실행 가능
        pass
        
# 2단계: 기반 기능 활용
class TestFileStorage:
    """파일 저장 - FileValidator에 의존"""
    def test_file_save_with_validation():
        # FileValidator 기능이 정상 작동 전제
        pass
        
# 3단계: 통합 기능
class TestFileUploadAPI:
    """API - FileValidator, FileStorage에 의존"""
    def test_upload_endpoint():
        # 하위 계층 기능들이 모두 정상 작동 전제
        pass
```

### 2.3 구현 후 즉시 사용자 플로우 검증

**API 구현 직후 프런트엔드 통합 테스트 수행**

API가 구현되면, 이를 사용하는 프런트엔드와의 통합 테스트를 즉시 수행하여, 실제 유저 플로우 기반에서의 오류와 누락을 조기에 식별하고, 그 결과를 바탕으로 향후 테스트 및 개발 우선순위를 설정함으로써 실용적이고 집중된 개선이 가능하도록 한다.

**프런트엔드 통합 테스트 체크리스트**

```python
def test_frontend_api_integration():
    """
    실제 사용자 플로우 기반 통합 테스트
    
    검증 항목:
    1. API 응답 형식이 프런트엔드 기대 구조와 일치
    2. 오류 상황 시 적절한 사용자 메시지 표시
    3. 로딩 상태 및 진행률 표시 정상 동작
    4. 성공/실패 시나리오별 UI 상태 변화 확인
    """
    pass

def test_user_workflow_end_to_end():
    """
    실제 사용자 행동 패턴 기반 테스트
    
    시나리오:
    - 로그인 → 데이터 입력 → 처리 요청 → 결과 확인
    - 각 단계별 사용자 경험 검증
    - 오류 발생 시 사용자 가이드 적절성 확인
    """
    pass
```

**우선순위 재설정 기준**

```python
# 통합 테스트 결과 기반 우선순위 조정
if frontend_integration_issues_found:
    # 발견된 이슈를 바탕으로 테스트 우선순위 재조정
    prioritize_tests_for_critical_user_flows()
    add_missing_error_handling_tests()
    update_api_contract_tests()
```

### 2.4 테스트 함수 우선순위 분류

**모든 테스트 함수에 개발 단계별 중요도 및 유형 표시**

```python
# 🟦 필수 (MVP) - 시스템 안정성 직결

## 정상 시나리오 (Happy Path)
def test_file_size_validation():
    """파일 크기 검증 - 기본 입력 검증"""
    pass

def test_file_save_operation():
    """파일 저장 기능 - 핵심 비즈니스 로직"""
    pass

def test_successful_upload_flow():
    """정상 업로드 플로우 - 전체 성공 시나리오"""
    pass

## 실패 시나리오 (Failure Cases)
def test_oversized_file_rejection():
    """파일 크기 제한 초과 시 거부 - 서버 리소스 보호"""
    pass
    
def test_malicious_file_detection():
    """악성 파일 업로드 차단 - 보안 필수 사항"""
    pass

def test_invalid_format_rejection():
    """지원하지 않는 파일 형식 거부"""
    pass

## 예외 케이스 (Edge Cases)
def test_empty_file_handling():
    """빈 파일 처리 - 0바이트 파일"""
    pass

def test_filename_special_characters():
    """특수문자 포함 파일명 처리"""
    pass

# 🟡 권장 (안정화) - 사용자 경험 개선

## 정상 시나리오
def test_file_metadata_extraction():
    """파일 메타데이터 추출 - 향상된 사용자 정보 제공"""
    pass

def test_progress_tracking():
    """업로드 진행률 추적 - 사용자 피드백"""
    pass

## 실패 시나리오
def test_network_timeout_recovery():
    """네트워크 타임아웃 시 적절한 오류 메시지"""
    pass

def test_storage_full_handling():
    """저장 공간 부족 시 처리"""
    pass

## 예외 케이스
def test_concurrent_upload_handling():
    """동시 업로드 시 충돌 방지 - 멀티유저 환경 안정성"""
    pass

def test_duplicate_filename_resolution():
    """중복 파일명 자동 해결"""
    pass

# 🟢 선택 (최적화) - 고급 기능

## 정상 시나리오
def test_file_compression():
    """자동 파일 압축 - 저장 공간 최적화"""
    pass

def test_thumbnail_generation():
    """이미지 썸네일 자동 생성"""
    pass

## 실패 시나리오
def test_compression_failure_fallback():
    """압축 실패 시 원본 파일로 폴백"""
    pass

## 예외 케이스
def test_automatic_virus_scanning():
    """업로드 파일 자동 바이러스 스캔 - 추가 보안 계층"""
    pass

def test_large_file_chunked_upload():
    """대용량 파일 청크 업로드"""
    pass
```

### 2.5 테스트 함수 난이도 표시

**모든 테스트 함수에 구현 복잡도 및 기술적 난이도 표시**

```python
# 난이도 분류 기준:
# 🟢 초급 (Beginner): 단순 입출력, 기본 검증, 직관적 로직
# 🟡 중급 (Intermediate): 상태 관리, 조건부 로직, 외부 의존성
# 🔴 고급 (Advanced): 복잡한 로직, 멀티스레드, 성능 최적화

# 🔴 필수 (MVP) - 시스템 안정성 직결

## 정상 시나리오 (Happy Path)
def test_file_size_validation():
    """
    파일 크기 검증 - 기본 입력 검증
    🟢 초급: 단순 숫자 비교, 조건문
    """
    pass

def test_file_save_operation():
    """
    파일 저장 기능 - 핵심 비즈니스 로직
    🟡 중급: 파일 I/O, 오류 처리, 상태 관리
    """
    pass

def test_successful_upload_flow():
    """
    정상 업로드 플로우 - 전체 성공 시나리오
    🔴 고급: 다중 컴포넌트 통합, 트랜잭션 관리
    """
    pass

## 실패 시나리오 (Failure Cases)
def test_oversized_file_rejection():
    """
    파일 크기 제한 초과 시 거부 - 서버 리소스 보호
    🟢 초급: 크기 체크, 간단한 예외 처리
    """
    pass
    
def test_malicious_file_detection():
    """
    악성 파일 업로드 차단 - 보안 필수 사항
    🔴 고급: 파일 시그니처 분석, 보안 알고리즘
    """
    pass

## 예외 케이스 (Edge Cases)
def test_empty_file_handling():
    """
    빈 파일 처리 - 0바이트 파일
    🟡 중급: 경계값 처리, 특수 상황 로직
    """
    pass

def test_concurrent_upload_handling():
    """
    동시 업로드 시 충돌 방지 - 멀티유저 환경 안정성
    🔴 고급: 동시성 제어, 락 메커니즘, 경쟁 상태 처리
    """
    pass

# 🟡 권장 (안정화) - 사용자 경험 개선

def test_file_metadata_extraction():
    """
    파일 메타데이터 추출 - 향상된 사용자 정보 제공
    🟡 중급: 파일 파싱, 메타데이터 구조 이해
    """
    pass

def test_progress_tracking():
    """
    업로드 진행률 추적 - 사용자 피드백
    🔴 고급: 비동기 처리, 실시간 상태 업데이트
    """
    pass

# 🟢 선택 (최적화) - 고급 기능

def test_file_compression():
    """
    자동 파일 압축 - 저장 공간 최적화
    🔴 고급: 압축 알고리즘, 성능 최적화
    """
    pass

def test_large_file_chunked_upload():
    """
    대용량 파일 청크 업로드
    🔴 고급: 스트리밍, 메모리 관리, 재개 가능 업로드
    """
    pass
```

**난이도별 개발 접근 방식**

```python
# 🟢 초급 테스트 특징
def test_simple_validation():
    """
    - 단일 함수 호출, 명확한 입출력
    - 조건문, 반복문 수준의 기본 로직
    - Mock 없이 순수 함수로 테스트 가능
    - 예상 구현 시간: 30분 이내
    """
    pass

# 🟡 중급 테스트 특징  
def test_business_logic():
    """
    - 여러 함수/클래스 조합
    - 상태 변경, 조건부 분기 포함
    - 제한적 Mock 사용 (1-2개 외부 의존성)
    - 예상 구현 시간: 1-3시간
    """
    pass

# 🔴 고급 테스트 특징
def test_complex_integration():
    """
    - 복잡한 비즈니스 로직, 다중 시스템 통합
    - 동시성, 성능, 보안 고려사항
    - 다수의 Mock, 복잡한 테스트 환경 설정
    - 예상 구현 시간: 반나절 이상
    """
    pass
```

### 2.6 통합 및 E2E 테스트 연계성 제시

**단위 테스트와 상위 테스트 연계**

```python
# 현재 제안하는 단위 테스트
def test_file_metadata_extraction():
    """
    단위 테스트: 메타데이터 추출 함수
    
    🔗 실제 통합 시나리오:
    1. 사용자가 파일 업로드 → API에서 이 함수 호출
    2. 추출된 메타데이터 → 데이터베이스 저장
    3. 프론트엔드에서 파일 정보 표시 → 이 메타데이터 사용
    
    🚨 주의: 단위 테스트에서 검증하는 메타데이터 필드가
           실제 API 응답에도 포함되는지 통합 테스트에서 확인 필요
    
    관련 통합 테스트:
    - test_upload_api_with_metadata(): API 엔드포인트에서 메타데이터 추출 동작
    - test_metadata_database_storage(): 추출된 메타데이터 DB 저장 검증
    
    관련 E2E 테스트:
    - test_user_upload_with_file_info_display(): 브라우저에서 업로드 후 파일 정보 표시
    - test_file_list_with_metadata(): 파일 목록에서 메타데이터 정보 확인
    """
    pass
```

### 2.7 테스트 전후 상태 명시

### 2.8 병렬 실행 가능 여부 명시

### 2.9 API 계약 테스트 포함 (MVP 수준)

**최소 검증 헬퍼 활용**

```python
def assert_api_basic_contract(response, required_fields=None):
    """MVP API 계약 최소 검증 - 상태코드, JSON형식, 필수필드, 타입"""
    pass
    
def record_api_contract(endpoint, response):
    """향후 본격 계약 테스트용 응답 구조 기록"""
    pass

# 적용 예시
def test_upload_api_mvp_contract():
    """
    MVP 계약 검증:
    - 상태 코드: 200 (성공)
    - 응답 형식: JSON
    - 필수 필드: file_id (프론트엔드에서 파일 참조용)
    - 데이터 타입: file_id는 문자열
    
    기록 사항 (향후 활용):
    - 전체 응답 필드: [file_id, filename, size, upload_time]
    - 오류 응답 형식: {detail: "error message"}
    """
    pass
```

---

## 3. 테스트 코드 제안 개요

**⚠️ 중요: 아래는 일반적 안내이며, 실제 문서 작성 시에는 현재 구현하려는 기능과 관련하여 구체적으로 서술해야 합니다.**

**테스트 코드 제안 시 다음 형식으로 핵심 정보를 먼저 제공합니다:**

### 3.1 현재 기능 개발과 관련된 테스트 모듈과 함수 관계

**테스트 모듈 구조 (의존성 관계)**
```
tests/
├── unit/
│   ├── test_core_validator.py     # 🔵 기반 (의존성 없음)
│   │   ├── test_validate_input_format()
│   │   ├── test_validate_business_rules()
│   │   └── test_validate_constraints()
│   ├── test_data_processor.py     # 🟡 조합 (validator 의존)
│   │   ├── test_process_valid_data()
│   │   ├── test_handle_processing_errors()
│   │   └── test_data_transformation()
│   └── test_business_logic.py     # 🔵 기반 (의존성 없음)
│       ├── test_calculate_business_value()
│       └── test_apply_business_rules()
├── integration/
│   ├── test_service_api.py        # 🔴 통합 (모든 기능 의존)
│   │   ├── test_full_request_flow()
│   │   └── test_error_handling_flow()
│   └── test_workflow.py           # 🔴 통합 (API + DB 의존)
│       ├── test_multi_step_workflow()
│       └── test_rollback_scenario()
└── contract/
    └── test_api_contract.py        # 🟠 계약 (API 의존)
        ├── test_request_contract()
        └── test_response_contract()
```

**모듈 간 관계 시각화**
```
┌─────────────────────── 테스트 모듈 의존성 그래프 ────────────────────────┐
│                                                                      │
│  🔵 기반 계층 (독립적)                                                   │
│  ┌─────────────────┐    ┌─────────────────┐                          │
│  │ test_core_      │    │ test_business_  │                          │
│  │ validator.py    │    │ logic.py        │                          │
│  └─────────────────┘    └─────────────────┘                          │
│           │                       │                                  │
│           └───────┬───────────────┘                                  │
│                   ▼                                                  │
│  🟡 조합 계층 (기반 기능 활용)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_data_      │                                                 │
│  │ processor.py    │                                                 │
│  └─────────────────┘                                                 │
│           │                                                          │
│           ▼                                                          │
│  🔴 통합 계층 (모든 기능 통합)                                           │
│  ┌─────────────────┐    ┌─────────────────┐                          │
│  │ test_service_   │    │ test_workflow.  │                          │
│  │ api.py          │    │ py              │                          │
│  └─────────────────┘    └─────────────────┘                          │
│           │                       │                                  │
│           └───────┬───────────────┘                                  │
│                   ▼                                                  │
│  🟠 계약 계층 (API 인터페이스)                                           │
│  ┌─────────────────┐                                                 │
│  │ test_api_       │                                                 │
│  │ contract.py     │                                                 │
│  └─────────────────┘                                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 기능 플로우와 테스트 함수 매핑

**플로우 시각화**
```
┌──────────────────────── 기능 플로우 ────────────────────────┐
│                                                            │
│  🌐 사용자 요청 ──→ 🔍 입력 검증 ──→ ⚙️ 비즈니스 처리 ──→ 💾 저장 ──→ 📤 응답  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**각 단계별 테스트 함수 매핑**
- **🌐 사용자 요청 단계**: 
  - `test_request_contract()` - API 요청 형식 검증
  - `test_authentication()` - 사용자 인증 처리

- **🔍 입력 검증 단계**: 
  - `test_validate_input_format()` - 데이터 형식 검증
  - `test_validate_business_rules()` - 비즈니스 규칙 적용
  - `test_validate_constraints()` - 시스템 제약 검증

- **⚙️ 비즈니스 처리 단계**: 
  - `test_process_valid_data()` - 핵심 데이터 처리
  - `test_calculate_business_value()` - 비즈니스 로직 계산
  - `test_data_transformation()` - 데이터 변환

- **💾 저장 단계**: 
  - `test_database_transaction()` - 데이터 저장 트랜잭션
  - `test_file_storage()` - 파일 시스템 저장
  - `test_rollback_scenario()` - 실패 시 롤백

- **📤 응답 단계**: 
  - `test_response_contract()` - API 응답 형식 검증
  - `test_error_handling_flow()` - 오류 응답 처리

**통합 테스트**
- `test_full_request_flow()` - 전체 플로우 통합 검증
- `test_multi_step_workflow()` - 복합 워크플로우 검증

### 3.3 사용자 시나리오별 테스트 매핑

**현재 구현 기능의 실제 사용자 시나리오를 구체적으로 명시하고 테스트 함수 연결**

```
┌─────────────── 사용자 시나리오 → 테스트 매핑 ────────────────┐
│                                                            │
│  🌟 주 시나리오 (Happy Path)                                │
│  "정상적인 사용자가 올바른 데이터로 성공적 처리"              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 인증된 사용자 → 유효 데이터 입력 → 처리 성공     │ │
│  │ 테스트: test_validate_input_format()                  │ │
│  │        test_process_valid_data()                      │ │
│  │        test_full_request_flow()                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  ⚠️ 오류 시나리오 (Error Cases)                             │
│  "잘못된 입력이나 시스템 오류 상황"                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 무효 데이터 → 적절한 오류 메시지 반환          │ │
│  │ 테스트: test_invalid_format_rejection()               │ │
│  │        test_handle_processing_errors()                │ │
│  │        test_error_handling_flow()                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  🔧 예외 시나리오 (Edge Cases)                              │
│  "경계값이나 특수한 상황"                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 시나리오: 동시 접근, 큰 데이터, 네트워크 장애 등          │ │
│  │ 테스트: test_concurrent_handling()                    │ │
│  │        test_large_data_processing()                   │ │
│  │        test_rollback_scenario()                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.4 구현 순서 제안

**우선순위별 테스트 함수 분류 및 단계별 구현 로드맵**

```
┌───────────────── 구현 단계별 로드맵 ─────────────────┐
│                                                   │
│  1️⃣ 1단계: 🟦 필수 (MVP) - 시스템 안정성 핵심     │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 정상 시나리오 (Happy Path)                │ │
│  │ ① test_validate_input_format() 🟢 초급 ⚡병렬 │ │
│  │ ② test_process_valid_data() 🟡 중급 🔄순차   │ │
│  │ ③ test_calculate_business_value() 🟡 중급 ⚡병렬 │ │
│  │                                             │ │
│  │ ⚠️ 오류 처리 (Error Handling)               │ │
│  │ ④ test_invalid_format_rejection() 🟢 초급 ⚡병렬 │ │
│  │ ⑤ test_oversized_data_rejection() 🟢 초급 ⚡병렬 │ │
│  │                                             │ │
│  │ 🔌 API 계약 (Contract)                     │ │
│  │ ⑥ test_request_contract() 🟢 초급 🔄순차     │ │
│  │ ⑦ test_response_contract() 🟢 초급 🔄순차    │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  2️⃣ 2단계: 🟡 권장 (안정화) - 사용자 경험 개선    │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 정상 시나리오                             │ │
│  │ ① test_metadata_extraction() 🟡 중급 🔄순차   │ │
│  │ ② test_progress_tracking() 🔴 고급 🔄순차     │ │
│  │                                             │ │
│  │ ⚠️ 오류 처리                                │ │
│  │ ③ test_network_timeout_recovery() 🟡 중급 🔄순차 │ │
│  │ ④ test_storage_full_handling() 🟡 중급 🔄순차 │ │
│  │                                             │ │
│  │ 🔌 API 계약                                │ │
│  │ ⑤ test_error_response_contract() 🟡 중급 🔄순차 │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  3️⃣ 3단계: 🟢 선택 (최적화) - 고급 기능          │
│  ┌─────────────────────────────────────────────┐ │
│  │ 📋 정상 시나리오                             │ │
│  │ ① test_file_compression() 🔴 고급 🔄순차      │ │
│  │ ② test_thumbnail_generation() 🟡 중급 🔄순차  │ │
│  │                                             │ │
│  │ ⚠️ 오류 처리                                │ │
│  │ ③ test_compression_failure() 🔴 고급 🔄순차   │ │
│  │ ④ test_rollback_scenario() 🔴 고급 🔄순차     │ │
│  │                                             │ │
│  │ 🔌 API 계약                                │ │
│  │ ⑤ test_advanced_contract() 🔴 고급 🔄순차     │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  💡 구현 팁:                                    │
│  • ⚡병렬: 독립적 실행 가능 (상태 변경 없음)        │
│  • 🔄순차: 순차 실행 필요 (공유 리소스 사용)       │
│  • 🟢 초급 → 🟡 중급 → 🔴 고급 순서로 진행       │
│  • 각 단계 완료 후 다음 단계로 이동              │
│  • 🟦 필수 완료 시점에서 MVP 배포 가능           │
│                                                   │
└───────────────────────────────────────────────────┘
```

---

## 4. 테스트 코드 제안 시 점검 목록

**테스트 코드 제안 시 가이드라인 준수 여부를 점검하세요:**

### 4.1 Classic TDD 원칙 준수

- [ ] **Mock 사용에 대한 명확한 기준을 제시했는가?**
  - Mock 사용 조건 (이미 구현 완료된 기능, 호출 비용 높음)을 명시했는가?
  - 각 Mock 사용 시 구체적인 이유를 기재했는가?

### 4.2 기능 간 선후 관계와 의존성 고려

- [ ] **기능 간 의존성을 고려한 계층적 테스트 설계를 제시했는가?**
  - 기반 → 조합 → 통합 계층 순서로 테스트를 구성했는가?
  - 각 계층 간 의존성을 명확히 표시했는가?

### 4.3 구현 후 즉시 사용자 플로우 검증

- [ ] **구현 후 즉시 사용자 플로우 검증 방안을 포함했는가?**
  - 프런트엔드 통합 테스트 체크리스트를 제공했는가?
  - 사용자 워크플로우 기반 테스트 방안을 제시했는가?
  - 통합 테스트 결과 기반 우선순위 재설정 기준을 명시했는가?

### 4.4 테스트 함수 우선순위 분류

- [ ] **테스트 함수별 우선순위를 명확히 분류했는가?**
  - 🟦 필수 (MVP), 🟡 권장 (안정화), 🟢 선택 (최적화)로 구분했는가?
  - 각 우선순위 내에서도 정상/실패/예외 시나리오로 세분화했는가?

### 4.5 테스트 함수 난이도 표시

- [ ] **테스트 함수별 난이도를 표시했는가?**
  - 🟢 초급, 🟡 중급, 🔴 고급으로 구분했는가?
  - 각 난이도별 특징과 예상 구현 시간을 제시했는가?

### 4.6 통합 및 E2E 테스트 연계성 제시

- [ ] **단위 테스트와 상위 테스트 연계성을 제시했는가?**
  - 각 단위 테스트가 실제 통합 시나리오에서 어떻게 활용되는지 명시했는가?
  - 관련 통합 테스트와 E2E 테스트를 연결했는가?

### 4.7 테스트 전후 상태 명시

- [ ] **테스트 전후 상태를 명시했는가?**
  - 각 테스트 함수별로 테스트 전 상태, 실행 작업, 테스트 후 상태를 명확히 기술했는가?

### 4.8 병렬 실행 가능 여부 명시

- [ ] **병렬 실행 가능 여부를 명시했는가?**
  - ⚡ 병렬 (독립적 실행) 또는 🔄 순차 (공유 리소스 사용) 표시를 했는가?

### 4.9 API 계약 테스트 포함 (MVP 수준)

- [ ] **API 계약 테스트를 포함했는가?**
  - MVP 수준의 기본 계약 검증을 포함했는가?
  - 향후 확장 가능한 계약 테스트 구조를 제시했는가?