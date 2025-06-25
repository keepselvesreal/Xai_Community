# 테스트 코드 제안 가이드

## 📋 문서 목차

1. [목적](#목적)
2. [테스트 코드 제안 가이드라인](#테스트-코드-제안-가이드라인)
   - 2.1 [기능 간 선후 관계와 의존성 고려](#기능-간-선후-관계와-의존성-고려)
   - 2.2 [Classic TDD 원칙 준수](#classic-tdd-원칙-준수)
   - 2.3 [테스트 전후 상태 명시](#테스트-전후-상태-명시)
   - 2.4 [실패 시나리오 우선순위](#실패-시나리오-우선순위)
   - 2.5 [병렬 실행 최적화](#병렬-실행-최적화)
   - 2.6 [통합 및 E2E 테스트 연계성](#통합-및-e2e-테스트-연계성)
   - 2.7 [API 계약 테스트 (MVP 수준)](#api-계약-테스트-mvp-수준)
3. [테스트 코드 제안 형식](#테스트-코드-제안-형식)
   - 3.1 [핵심 정보 압축 제시](#핵심-정보-압축-제시)
   - 3.2 [실제 테스트 코드 제안](#실제-테스트-코드-제안)
4. [주의사항](#주의사항)

---

## 목적

개발자가 효과적이고 실용적인 테스트 코드를 구상할 수 있도록 체계적인 구성 방향과 예시를 제안합니다.

---

## 테스트 코드 제안 가이드라인

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

**의존성 실패 격리**

```python
# ✅ 하위 계층 실패 시에도 상위 계층 테스트는 독립적 실행
def test_file_validation_independent():
    """파일 검증 로직 - 다른 기능 실패와 무관하게 테스트"""
    pass
    
def test_storage_with_mock_validation():
    """
    저장 로직 - 검증 기능이 실패해도 저장 자체 로직은 테스트 가능
    Mock을 통해 검증 기능 성공 가정하고 저장 로직만 집중 테스트
    """
    pass
```

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

### 테스트 전후 상태 명시

**상태 변화 명확히 기술**

```python
def test_file_upload_state_change():
    """
    테스트 전 상태:
    - uploads/ 디렉토리: 빈 상태 (0개 파일)
    - files 테이블: 0개 레코드
    - 사용자: 인증된 상태 (valid JWT 토큰)
    
    실행 작업:
    - 5MB 이미지 파일 업로드 요청
    
    테스트 후 상태:
    - uploads/ 디렉토리: 1개 파일 생성 (UUID_filename.jpg)
    - files 테이블: 1개 레코드 추가 (파일 메타데이터)
    - 응답: {"file_id": "uuid-string", "status": "uploaded"}
    """
    pass
```

### 실패 시나리오 우선순위

**개발 단계별 중요도 표시**

```python
# 🔴 필수 (MVP) - 시스템 안정성 직결
def test_oversized_file_rejection():
    """파일 크기 제한 초과 시 거부 - 서버 리소스 보호"""
    pass
    
def test_malicious_file_detection():
    """악성 파일 업로드 차단 - 보안 필수 사항"""
    pass

# 🟡 권장 (안정화) - 사용자 경험 개선
def test_concurrent_upload_handling():
    """동시 업로드 시 충돌 방지 - 멀티유저 환경 안정성"""
    pass
    
def test_network_timeout_recovery():
    """네트워크 타임아웃 시 적절한 오류 메시지"""
    pass

# 🟢 선택 (최적화) - 고급 기능
def test_automatic_virus_scanning():
    """업로드 파일 자동 바이러스 스캔 - 추가 보안 계층"""
    pass
```

### 병렬 실행 최적화

**실행 그룹 분류**

```python
# 병렬 실행 가능 (독립적)
@pytest.mark.parallel
class TestFileValidation:
    """순수 함수, 상태 변경 없음"""
    pass
    
@pytest.mark.parallel  
class TestFileUtils:
    """유틸리티 함수, 메모리 내 처리만"""
    pass

# 순차 실행 필요 (공유 리소스)
class TestFileUploadAPI:
    """데이터베이스, 파일 시스템 사용"""
    pass
    
class TestFileCleanup:
    """파일 시스템 정리 작업"""
    pass
```

### 통합 및 E2E 테스트 연계성

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

### API 계약 테스트 (MVP 수준)

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

## 테스트 코드 제안 형식

### 핵심 정보 압축 제시

**테스트 코드 제안 시 다음 형식으로 핵심 정보를 먼저 제공합니다:**

#### 📚 테스트 코드 구성 개요

**테스트 모듈 구조 (의존성 관계)**
```
tests/
├── unit/
│   ├── test_core_validator.py     # 🔵 기반 (의존성 없음)
│   ├── test_data_processor.py     # 🟡 조합 (validator 의존)
│   └── test_business_logic.py     # 🔵 기반 (의존성 없음)
├── integration/
│   ├── test_service_api.py        # 🔴 통합 (모든 기능 의존)
│   └── test_workflow.py           # 🔴 통합 (API + DB 의존)
└── contract/
    └── test_api_contract.py        # 🟠 계약 (API 의존)
```

**기능 플로우와의 관계**
- **사용자 플로우**: [입력 → 검증 → 처리 → 저장 → 응답]
- `test_core_validator.py`: "검증" 단계
- `test_data_processor.py`: "처리" 단계  
- `test_service_api.py`: 전체 플로우 통합

**시퀀스 다이어그램과의 관계**
- **시스템 흐름**: Client → API → Validator → Processor → Database
- 단위 테스트: 각 컴포넌트 개별 검증
- 통합 테스트: 컴포넌트 간 상호작용 검증
- 계약 테스트: Client-API 인터페이스 검증

**사용자 시나리오와의 관계**
- **주 시나리오**: 비즈니스 사용자의 데이터 처리 요청
  - `test_core_validator.py`: 입력 데이터 형식/제한 검증
  - `test_service_api.py`: 성공적인 처리 플로우
- **예외 시나리오**: 시스템 오류, 데이터 충돌
  - `test_workflow.py`: 재시도, 복구 시나리오

**각 모듈 상세 정보**

| 모듈 | 우선순위 | 실행 그룹 | Mock 사용 |
|------|----------|-----------|-----------|
| `test_core_validator.py` | 🔴 필수 (입력검증), 🟡 권장 (형식검증) | 병렬 (독립적 순수 함수) | 불필요 (빠른 실행) |
| `test_data_processor.py` | 🔴 필수 (핵심처리), 🟡 권장 (중복처리) | 순차 (상태 변경) | 🚨 ExternalService |
| `test_service_api.py` | 🔴 필수 (기본 API), 🟡 권장 (오류처리) | 순차 (데이터베이스 사용) | 🚨 NotificationService |

### 실제 테스트 코드 제안

**테스트 코드 제안 시 다음 가이드라인을 반영하여 제시합니다:**

#### 🏗️ 계층적 의존성 설계
- **1단계 (기반)**: 독립적 핵심 로직 → 다른 기능에 의존하지 않음
- **2단계 (조합)**: 기반 기능 활용 → 1단계 기능들의 조합
- **3단계 (통합)**: 전체 시스템 통합 → 모든 하위 기능 의존

#### 🎯 우선순위 기반 구성
- **🔴 필수 (MVP)**: 핵심 비즈니스 로직, 시스템 안정성 직결
- **🟡 권장 (안정화)**: 사용자 경험 개선, 오류 처리 강화
- **🟢 선택 (최적화)**: 고급 기능, 성능 최적화

#### 📋 테스트 전후 상태 명시
- **테스트 전 상태**: 초기 데이터, 시스템 상태, 전제 조건
- **실행 작업**: 구체적인 테스트 수행 내용
- **테스트 후 상태**: 예상 결과, 상태 변화, 부작용

#### ⚡ 실행 최적화 고려
- **병렬 실행**: 독립적 순수 함수, 상태 변경 없는 테스트
- **순차 실행**: 데이터베이스, 파일 시스템 등 공유 리소스 사용

#### 🚨 Mock 사용 정책
- **Mock 필요**: 외부 서비스, 네트워크 호출, 고비용 연산
- **Mock 불필요**: 순수 함수, 빠른 실행, 단순 로직
- **명시 방법**: Mock 사용 이유와 대안 없을 시 문제점 기술

#### 🔗 상위 테스트 연계성
- **통합 테스트**: 단위 테스트가 통합될 실제 시나리오
- **E2E 테스트**: 사용자 관점의 전체 워크플로우
- **탈맥락화 방지**: 실제 사용 시나리오와 연결점 명시

#### 📱 API 계약 테스트 (MVP)
- **최소 검증**: 상태 코드, 응답 형식, 필수 필드, 기본 타입
- **헬퍼 활용**: `assert_api_basic_contract()`, `record_api_contract()`
- **향후 확장**: 응답 구조 기록으로 본격 계약 테스트 토대 마련

#### 💡 테스트 코드 구조 예시
```python
class TestCoreLogic:
    """🔵 기반 계층 - 독립적 핵심 로직"""
    def test_business_rule_validation(self):
        """
        테스트 전: 유효하지 않은 입력 데이터
        테스트 후: 검증 실패 및 적절한 오류 메시지 반환
        🔗 통합: API에서 이 검증 로직 사용
        우선순위: 🔴 필수
        """

class TestIntegratedService:
    """🔴 통합 계층 - 전체 기능 조합"""
    def test_end_to_end_workflow(self):
        """
        🚨 Mock: ExternalPaymentService (외부 결제 API)
        테스트 전: 초기 상태, DB 레코드 0개
        테스트 후: 성공 처리, DB에 결과 저장
        우선순위: 🔴 필수
        """
```

---

## 주의사항

1. **테스트 모듈 구성 개요를 항상 먼저 제공하여 전체 맥락 이해 지원**
2. **기능 간 의존성을 고려한 계층적 테스트 설계**  
3. **단위 테스트가 실제 통합 시나리오와 연계되도록 맥락 제공**
4. **Mock 사용 시 명확한 이유 제시로 개발자 판단 지원**
5. **현재 구현 기능 수준에 맞는 적절한 테스트 범위 제안**

이 가이드를 통해 개발자가 체계적이고 실용적인 TDD 테스트 코드를 구상할 수 있도록 지원해주세요.