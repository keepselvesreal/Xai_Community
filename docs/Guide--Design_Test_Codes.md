# 테스트 코드 제안 가이드

## 📋 문서 목차

1. [목적](#목적)
2. [테스트 코드 제안 가이드라인](#테스트-코드-제안-가이드라인)
   - 2.1 [Classic TDD 원칙 준수](#classic-tdd-원칙-준수)
   - 2.2 [기능 간 선후 관계와 의존성 고려](#기능-간-선후-관계와-의존성-고려)
   - 2.3 [테스트 함수 우선순위 분류](#테스트-함수-우선순위-분류)
   - 2.4 [테스트 함수 난이도 표시](#테스트-함수-난이도-표시)
   - 2.5 [통합 및 E2E 테스트 연계성 제시](#통합-및-e2e-테스트-연계성-제시)
   - 2.6 [테스트 전후 상태 명시](#테스트-전후-상태-명시)
   - 2.7 [병렬 실행 가능 여부 명시](#병렬-실행-가능-여부-명시)
   - 2.8 [API 계약 테스트 포함 (MVP 수준)](#api-계약-테스트-포함-mvp-수준)
3. [수행할 작업](#테스트-코드-제안-형식)
   - 3.1 [핵심 정보 압축 제시](#핵심-정보-압축-제시)
   - 3.2 [실제 각 테스트 모듈과 함수 제시](#실제-각-테스트-모듈과-함수)
4. [주의사항](#주의사항)

---

## 목적

개발자가 효과적이고 실용적인 테스트 코드를 구상할 수 있도록 체계적인 구성 방향과 예시를 제안합니다.

---

## 테스트 코드 제안 가이드라인

### Classic TDD 원칙 준수

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

### 기능 간 선후 관계와 의존성 고려

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

### 테스트 함수 우선순위 분류

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

### 테스트 함수 난이도 표시

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

### API 계약 테스트 포함 (MVP 수준)

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

## 수행할 작업

**⚠️ 중요: 아래는 일반적 안내이며, 실제 테스트 코드 제안 시에는 현재 구현하려는 기능과 관련하여 구체적으로 서술해야 합니다.**

### 1. 핵심 정보 압축 제시

**테스트 코드 제안 시 다음 형식으로 핵심 정보를 먼저 제공합니다:**

#### 📚 현재 기능 개발과 관련된 테스트 모듈과 함수 관계

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

#### 🔗 테스트 모듈과 함수의 맥락

**기능 플로우와의 관계**
- **현재 구현 기능의 사용자 플로우를 구체적으로 명시**: [구체적 단계1 → 구체적 단계2 → ...]
- **각 테스트 함수가 플로우의 어느 단계를 검증하는지 명확히 연결**
- **예시 (일반적)**: [입력 → 검증 → 처리 → 저장 → 응답]
- `test_core_validator.py` → `test_validate_input_format()`: "입력 검증" 단계
- `test_data_processor.py` → `test_process_valid_data()`: "처리" 단계  
- `test_service_api.py` → `test_full_request_flow()`: 전체 플로우 통합

**시퀀스 다이어그램과의 관계**
- **현재 구현 시스템의 실제 컴포넌트와 상호작용을 구체적으로 명시**
- **각 테스트 함수가 시퀀스의 어느 상호작용을 검증하는지 연결**
- **예시 (일반적)**: Client → API → Validator → Processor → Database
- `test_validate_business_rules()`: Validator 컴포넌트 개별 검증
- `test_process_valid_data()`: Processor 컴포넌트 개별 검증
- `test_full_request_flow()`: 컴포넌트 간 상호작용 검증
- `test_request_contract()`: Client-API 인터페이스 검증

**사용자 시나리오와의 관계**
- **현재 구현 기능의 실제 사용자 시나리오를 구체적으로 명시**
- **각 테스트 함수가 어떤 사용자 행동/상황을 검증하는지 연결**
- **예시 (일반적)**: 
  - **주 시나리오**: 비즈니스 사용자의 데이터 처리 요청
    - `test_validate_input_format()`: 사용자 입력 데이터 형식 검증
    - `test_calculate_business_value()`: 비즈니스 로직 계산 검증
    - `test_full_request_flow()`: 성공적인 처리 플로우
  - **예외 시나리오**: 시스템 오류, 데이터 충돌, 복구
    - `test_handle_processing_errors()`: 처리 중 오류 상황
    - `test_rollback_scenario()`: 실패 시 복구 시나리오

#### 📋 각 모듈과 테스트 함수 상세 정보

**의존성 관련 정보**
- **🔵 기반 계층**: `test_core_validator.py`, `test_business_logic.py`
  - 다른 기능에 의존하지 않음, 순수 함수 중심
- **🟡 조합 계층**: `test_data_processor.py`
  - 기반 계층 기능(validator) 의존성 있음
- **🔴 통합 계층**: `test_service_api.py`, `test_workflow.py`
  - 모든 하위 계층 기능에 의존성 있음
- **🟠 계약 계층**: `test_api_contract.py`
  - API 서비스 기능에 의존성 있음

**우선순위 및 난이도 기반 테스트 함수 분류**

🟦 **필수 (MVP)**
- `test_validate_input_format()` 🟢 초급: 입력 데이터 기본 검증
- `test_process_valid_data()` 🟡 중급: 핵심 데이터 처리
- `test_calculate_business_value()` 🟡 중급: 비즈니스 핵심 로직
- `test_full_request_flow()` 🔴 고급: 기본 API 동작
- `test_request_contract()` 🟢 초급: API 기본 계약

🟡 **권장 (안정화)**
- `test_validate_business_rules()` 🟡 중급: 고급 비즈니스 규칙 검증
- `test_handle_processing_errors()` 🟡 중급: 오류 처리 강화
- `test_error_handling_flow()` 🔴 고급: API 오류 응답
- `test_response_contract()` 🟢 초급: API 응답 계약

🟢 **선택 (최적화)**
- `test_validate_constraints()` 🟢 초급: 추가 제약 조건 검증
- `test_data_transformation()` 🟡 중급: 데이터 변환 최적화
- `test_multi_step_workflow()` 🔴 고급: 복합 워크플로우
- `test_rollback_scenario()` 🔴 고급: 고급 복구 시나리오

**병렬/순차 실행 및 난이도 그룹 분류**

⚡ **병렬 실행 그룹** (독립적, 상태 변경 없음)
- `test_validate_input_format()` 🟢 초급, `test_validate_business_rules()` 🟡 중급, `test_validate_constraints()` 🟢 초급
- `test_calculate_business_value()` 🟡 중급, `test_apply_business_rules()` 🟡 중급

🔄 **순차 실행 그룹** (공유 리소스, 상태 변경)
- `test_process_valid_data()` 🟡 중급, `test_handle_processing_errors()` 🟡 중급, `test_data_transformation()` 🟡 중급
- `test_full_request_flow()` 🔴 고급, `test_error_handling_flow()` 🔴 고급
- `test_multi_step_workflow()` 🔴 고급, `test_rollback_scenario()` 🔴 고급
- `test_request_contract()` 🟢 초급, `test_response_contract()` 🟢 초급

### 2. 실제 각 테스트 모듈과 함수 제시

**테스트 모듈 제시 시 다음 목차를 각 모듈 위에 작성합니다:**

#### 📝 모듈 목차: test_core_validator.py

**주요 컴포넌트들**
- `InputValidator`: 사용자 입력 데이터 검증
- `BusinessRuleValidator`: 비즈니스 규칙 적용 검증  
- `ConstraintValidator`: 시스템 제약 조건 검증

**구성 함수와 핵심 내용**
- `test_validate_input_format()`: 데이터 형식 검증 (타입, 길이, 패턴)
- `test_validate_business_rules()`: 비즈니스 로직 규칙 적용 (권한, 정책)
- `test_validate_constraints()`: 시스템 제약 검증 (용량, 한도, 중복)

#### 🏗️ 테스트 코드 구조 예시

**실제 코드 작성 시 테스트 코드 제안 가이드라인을 준수하며, 구현 내용은 포함하지 않고 함수명과 입출력, 문서화만 제시합니다:**

```python
class TestCoreValidator:
    """🔵 기반 계층 - 독립적 핵심 검증 로직"""
    
    def test_validate_input_format(self):
        """
        입력 데이터 형식 검증
        
        테스트 전: 다양한 형식의 입력 데이터 (유효/무효)
        실행 작업: 데이터 형식 검증 함수 호출
        테스트 후: 유효 데이터는 통과, 무효 데이터는 명확한 오류 메시지
        
        🔗 통합 시나리오: API 요청 시 첫 번째 검증 단계
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (단순 형식 체크, 조건문)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: dict (user_input_data)
        출력: tuple (is_valid: bool, error_message: str)
        """
        pass
    
    def test_validate_business_rules(self):
        """
        비즈니스 규칙 검증
        
        테스트 전: 형식은 올바르지만 비즈니스 규칙 위반 데이터
        실행 작업: 비즈니스 규칙 검증 함수 호출
        테스트 후: 규칙 위반 시 적절한 오류 코드와 메시지
        
        🔗 통합 시나리오: 권한 체크, 정책 적용 단계
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (복합 조건, 규칙 엔진)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: dict (business_context), dict (user_data)
        출력: ValidationResult (status, violations, suggestions)
        """
        pass

class TestDataProcessor:
    """🟡 조합 계층 - 검증된 데이터 처리"""
    
    def test_process_valid_data(self):
        """
        검증된 데이터 핵심 처리
        
        테스트 전: 검증 통과한 유효 데이터, 초기 상태 DB
        실행 작업: 데이터 처리 파이프라인 실행
        테스트 후: 처리된 결과 데이터, DB 상태 변경
        
        🚨 Mock: ExternalAPIService (네트워크 의존성)
        🔗 통합 시나리오: 전체 데이터 처리 워크플로우 핵심
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (상태 관리, 외부 API 연동)
        실행 그룹: 🔄 순차 (상태 변경)
        
        입력: ValidatedData
        출력: ProcessedResult (data, metadata, status)
        """
        pass

class TestServiceAPI:
    """🔴 통합 계층 - 전체 시스템 통합"""
    
    def test_full_request_flow(self):
        """
        전체 요청 처리 플로우
        
        테스트 전: 클린 시스템 상태, 테스트 사용자 인증
        실행 작업: HTTP 요청 → 검증 → 처리 → 응답
        테스트 후: 성공 응답, 모든 하위 시스템 적절히 동작
        
        🚨 Mock: NotificationService, ExternalAPIService
        🔗 E2E 시나리오: 사용자 전체 워크플로우
        우선순위: 🟦 필수 (MVP)
        난이도: 🔴 고급 (다중 시스템 통합, 트랜잭션)
        실행 그룹: 🔄 순차 (DB, 파일시스템 사용)
        
        입력: HTTPRequest
        출력: HTTPResponse (status_code, body, headers)
        """
        pass
```

---

## 주의사항

1. **테스트 모듈 구성 개요를 항상 먼저 제공하여 전체 맥락 이해 지원**
2. **기능 간 의존성을 고려한 계층적 테스트 설계**  
3. **단위 테스트가 실제 통합 시나리오와 연계되도록 맥락 제공**
4. **Mock 사용 시 명확한 이유 제시로 개발자 판단 지원**
5. **현재 구현 기능 수준에 맞는 적절한 테스트 범위 제안**
6. **각 테스트 모듈 제시 전 목차를 통해 구조와 핵심 내용 사전 안내**
7. **실제 테스트 함수는 구현 내용 없이 함수명, 입출력, 문서화만 제시**

이 가이드를 통해 개발자가 체계적이고 실용적인 TDD 테스트 코드를 구상할 수 있도록 지원해주세요.