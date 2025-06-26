# File API 테스트 모듈 명세서

## 📋 문서 목차

1. [단위 테스트 모듈](#1-단위-테스트-모듈)
   - 1.1 [test_file_validator.py](#11-test_file_validatorpy)
   - 1.2 [test_file_storage.py](#12-test_file_storagepy)
   - 1.3 [test_file_metadata.py](#13-test_file_metadatapy)
   - 1.4 [test_file_permissions.py](#14-test_file_permissionspy)
2. [통합 테스트 모듈](#2-통합-테스트-모듈)
   - 2.1 [test_file_upload_service.py](#21-test_file_upload_servicepy)
   - 2.2 [test_file_retrieval_service.py](#22-test_file_retrieval_servicepy)
   - 2.3 [test_file_deletion_service.py](#23-test_file_deletion_servicepy)
3. [계약 테스트 모듈](#3-계약-테스트-모듈)
   - 3.1 [test_file_api_contract.py](#31-test_file_api_contractpy)

---

## 1. 단위 테스트 모듈

### 1.1 test_file_validator.py

#### 📝 모듈 목차: test_file_validator.py

**주요 컴포넌트들**
- `FileTypeValidator`: 파일 형식 및 MIME 타입 검증
- `FileSizeValidator`: 파일 크기 제한 검증  
- `FileCountValidator`: 첨부 파일 개수 제한 검증
- `SecurityValidator`: 악성 파일 및 보안 위험 검증

**구성 함수와 핵심 내용**
- `test_validate_file_type()`: MIME 타입 및 확장자 이중 검증
- `test_validate_file_size()`: 크기 제한 및 오류 메시지 검증
- `test_validate_file_count()`: attachment_type별 개수 제한 검증
- `test_validate_security_rules()`: 파일 헤더 및 악성 코드 검증

```python
class TestFileValidator:
    """🔵 기반 계층 - 독립적 파일 검증 로직"""
    
    def test_validate_file_type(self):
        """
        파일 형식 검증 - MIME 타입과 확장자 이중 검증
        
        테스트 전: 다양한 파일 형식 (jpg, png, gif, webp, 기타)
        실행 작업: 파일 타입 검증 함수 호출
        테스트 후: 허용된 형식은 통과, 금지된 형식은 구체적 오류 메시지
        
        🔗 통합 시나리오: 파일 업로드 시 첫 번째 보안 검증 단계
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (MIME 타입 비교, 확장자 체크)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: UploadFile (filename, content_type)
        출력: ValidationResult (is_valid: bool, error_code: str, message: str)
        """
        pass
    
    def test_validate_file_size(self):
        """
        파일 크기 제한 검증
        
        테스트 전: 다양한 크기의 파일 (1KB ~ 10MB)
        실행 작업: 파일 크기 검증 함수 호출
        테스트 후: 5MB 이하는 통과, 초과시 정확한 크기 정보 포함 오류
        
        🔗 통합 시나리오: 서버 리소스 보호 및 사용자 경험 개선
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (숫자 비교, 단위 변환)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: int (file_size_bytes)
        출력: ValidationResult (is_valid, max_size, actual_size, message)
        """
        pass
    
    def test_validate_file_count(self):
        """
        첨부 파일 개수 제한 검증
        
        테스트 전: attachment_type별 기존 파일 개수 (0~10개)
        실행 작업: 파일 개수 제한 검증 함수 호출
        테스트 후: 제한 내는 통과, 초과시 타입별 제한 안내
        
        🔗 통합 시나리오: 게시글/댓글별 첨부 파일 관리
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (조건문, 개수 계산)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (attachment_type), int (current_count)
        출력: ValidationResult (is_valid, max_count, current_count, message)
        """
        pass
    
    def test_validate_security_rules(self):
        """
        파일 보안 규칙 검증
        
        테스트 전: 정상 이미지 파일 및 위장된 악성 파일
        실행 작업: 파일 헤더 분석 및 보안 검증
        테스트 후: 정상 파일은 통과, 위험 파일은 구체적 위험 요소 명시
        
        🔗 통합 시나리오: 시스템 보안 및 사용자 보호
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (파일 헤더 분석, 시그니처 비교)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: bytes (file_header), str (filename)
        출력: SecurityResult (is_safe, risk_factors, recommendations)
        """
        pass

    def test_malicious_file_detection(self):
        """
        악성 파일 탐지 고급 검증
        
        테스트 전: 실행 가능한 확장자, 스크립트 삽입 파일
        실행 작업: 고급 파일 분석 및 패턴 매칭
        테스트 후: 모든 악성 패턴 차단, 탐지 근거 제공
        
        🔗 통합 시나리오: 고급 보안 계층
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (패턴 매칭, 휴리스틱 분석)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: bytes (file_content), FileMetadata
        출력: ThreatAnalysis (threat_level, detected_patterns, actions)
        """
        pass
```

### 1.2 test_file_storage.py

#### 📝 모듈 목차: test_file_storage.py

**주요 컴포넌트들**
- `FilePathGenerator`: 저장 경로 및 파일명 생성
- `PhysicalFileManager`: 실제 파일 시스템 I/O 처리
- `DirectoryManager`: 디렉토리 생성 및 관리
- `FileSystemCleaner`: 파일 삭제 및 정리 작업

**구성 함수와 핵심 내용**
- `test_generate_file_path()`: 유니크 파일 경로 생성 및 충돌 방지
- `test_save_physical_file()`: 실제 파일 저장 및 I/O 오류 처리
- `test_cleanup_file_system()`: 파일 삭제 및 디렉토리 정리
- `test_concurrent_file_operations()`: 동시 파일 작업 안전성

```python
class TestFileStorage:
    """🔵 기반 계층 - 독립적 파일 시스템 관리"""
    
    def test_generate_file_path(self):
        """
        파일 저장 경로 생성
        
        테스트 전: 다양한 attachment_type 및 원본 파일명
        실행 작업: 유니크 저장 경로 생성 함수 호출
        테스트 후: 중복 없는 경로, 올바른 디렉토리 구조, 안전한 파일명
        
        🔗 통합 시나리오: 파일 업로드 시 저장 위치 결정
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (문자열 조작, UUID 생성)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (attachment_type), str (original_filename)
        출력: FilePathResult (file_path, stored_filename, directory)
        """
        pass
    
    def test_save_physical_file(self):
        """
        물리적 파일 저장
        
        테스트 전: 임시 디렉토리, 테스트 파일 바이너리 데이터
        실행 작업: 파일 시스템에 실제 파일 저장
        테스트 후: 파일 정상 저장, 디렉토리 자동 생성, 권한 설정
        
        🔗 통합 시나리오: 업로드된 파일의 영구 저장
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (파일 I/O, 예외 처리, 권한 관리)
        실행 그룹: 🔄 순차 (파일시스템 상태 변경)
        
        입력: str (file_path), bytes (file_data)
        출력: SaveResult (success, file_size, permissions, error)
        """
        pass
    
    def test_cleanup_file_system(self):
        """
        파일 시스템 정리
        
        테스트 전: 저장된 테스트 파일들, 빈 디렉토리
        실행 작업: 파일 삭제 및 빈 디렉토리 정리
        테스트 후: 파일 완전 삭제, 빈 디렉토리 제거, 권한 오류 처리
        
        🔗 통합 시나리오: 파일 삭제 시 물리적 파일 정리
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (파일 삭제, 디렉토리 관리, 오류 처리)
        실행 그룹: 🔄 순차 (파일시스템 상태 변경)
        
        입력: str (file_path), bool (cleanup_empty_dirs)
        출력: CleanupResult (deleted_files, cleaned_dirs, errors)
        """
        pass
    
    def test_concurrent_file_operations(self):
        """
        동시 파일 작업 안전성
        
        테스트 전: 멀티스레드 환경, 같은 디렉토리 대상
        실행 작업: 동시 파일 저장/삭제 작업 실행
        테스트 후: 모든 작업 성공, 파일 무결성 보장, 경쟁 상태 없음
        
        🔗 통합 시나리오: 다중 사용자 동시 업로드 환경
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (동시성 제어, 락 메커니즘, 경쟁 상태)
        실행 그룹: 🔄 순차 (동시성 테스트)
        
        입력: List[FileOperation] (concurrent_operations)
        출력: ConcurrencyResult (success_count, conflicts, integrity_check)
        """
        pass
```

### 1.3 test_file_metadata.py

#### 📝 모듈 목차: test_file_metadata.py

**주요 컴포넌트들**
- `MetadataExtractor`: 파일에서 메타데이터 추출
- `FileDocumentCreator`: MongoDB 문서 생성 및 검증
- `ReferenceManager`: 파일 참조 관계 관리
- `MetadataValidator`: 메타데이터 유효성 검증

**구성 함수와 핵심 내용**
- `test_extract_file_metadata()`: 파일 속성 추출 및 구조화
- `test_create_file_document()`: MongoDB 문서 생성 및 스키마 검증
- `test_update_file_references()`: posts/comments 연결 관리
- `test_metadata_consistency()`: 메타데이터 일관성 검증

```python
class TestFileMetadata:
    """🟡 조합 계층 - 검증된 파일의 메타데이터 처리"""
    
    def test_extract_file_metadata(self):
        """
        파일 메타데이터 추출
        
        테스트 전: 다양한 형식의 유효한 파일 (jpg, png, gif, webp)
        실행 작업: 파일 속성 추출 및 메타데이터 구조화
        테스트 후: 정확한 파일 정보, 표준화된 메타데이터 형식
        
        전제 조건: test_validate_file_type() 통과한 파일만 처리
        🔗 통합 시나리오: 업로드된 파일의 상세 정보 생성
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (파일 파싱, 메타데이터 구조화)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: ValidatedFile (file_path, file_type)
        출력: FileMetadata (dimensions, color_depth, creation_date, camera_info)
        """
        pass
    
    def test_create_file_document(self):
        """
        MongoDB 파일 문서 생성
        
        테스트 전: 추출된 메타데이터, 사용자 정보, 저장 경로
        실행 작업: MongoDB 문서 스키마에 맞는 데이터 구조 생성
        테스트 후: 스키마 준수, 필수 필드 완성, 인덱스 최적화
        
        전제 조건: test_extract_file_metadata() 성공 결과 활용
        🔗 통합 시나리오: 파일 정보 데이터베이스 저장
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (스키마 검증, 데이터 변환)
        실행 그rouping: ⚡ 병렬 (순수 함수)
        
        입력: FileMetadata, UserInfo, StorageInfo
        출력: FileDocument (compliant with MongoDB schema)
        """
        pass
    
    def test_update_file_references(self):
        """
        파일 참조 관계 업데이트
        
        테스트 전: 저장된 파일 문서, 연결할 게시글/댓글 ID
        실행 작업: posts/comments 컬렉션의 file_ids 배열 업데이트
        테스트 후: 양방향 참조 정상 설정, 참조 무결성 보장
        
        전제 조건: test_create_file_document() 완료 후 실행
        🔗 통합 시나리오: 게시글/댓글과 파일 연결
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (관계형 데이터 관리, 트랜잭션)
        실행 그룹: 🔄 순차 (DB 상태 변경)
        
        입력: str (file_id), str (attached_to_id), str (attachment_type)
        출력: ReferenceResult (updated_documents, integrity_check)
        """
        pass
    
    def test_metadata_consistency(self):
        """
        메타데이터 일관성 검증
        
        테스트 전: 파일 시스템의 실제 파일, DB의 메타데이터
        실행 작업: 실제 파일과 DB 정보 간 일치성 검증
        테스트 후: 모든 메타데이터 정확성 확인, 불일치 항목 보고
        
        🔗 통합 시나리오: 데이터 무결성 보장 및 디버깅 지원
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (무결성 검증, 복합 데이터 비교)
        실행 그룹: 🔄 순차 (DB 및 파일시스템 접근)
        
        입력: str (file_id)
        출력: ConsistencyReport (matches, mismatches, recommendations)
        """
        pass
```

### 1.4 test_file_permissions.py

#### 📝 모듈 목차: test_file_permissions.py

**주요 컴포넌트들**
- `UploadPermissionChecker`: 파일 업로드 권한 검증
- `DeletePermissionChecker`: 파일 삭제 권한 검증
- `UserQuotaManager`: 사용자별 할당량 관리
- `RateLimitValidator`: 업로드 속도 제한 검증

**구성 함수와 핵심 내용**
- `test_check_upload_permission()`: 업로드 권한 및 제약 검증
- `test_check_delete_permission()`: 삭제 권한 (소유자/관리자) 검증
- `test_validate_user_quota()`: 사용자별 저장 공간 및 파일 개수 제한
- `test_rate_limiting()`: 시간당 업로드 제한 검증

```python
class TestFilePermissions:
    """🔵 기반 계층 - 독립적 권한 및 제한 검증"""
    
    def test_check_upload_permission(self):
        """
        파일 업로드 권한 검증
        
        테스트 전: 다양한 사용자 역할 (일반/프리미엄/관리자)
        실행 작업: 사용자별 업로드 권한 및 제약 조건 검증
        테스트 후: 권한 있는 사용자는 통과, 제한 사용자는 구체적 제약 안내
        
        🔗 통합 시나리오: 파일 업로드 요청 시 권한 게이트
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (역할 기반 권한, 조건부 로직)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: User (role, subscription), FileRequest (type, size)
        출력: PermissionResult (allowed, restrictions, upgrade_options)
        """
        pass
    
    def test_check_delete_permission(self):
        """
        파일 삭제 권한 검증
        
        테스트 전: 파일 소유자, 다른 사용자, 관리자 계정
        실행 작업: 파일 삭제 권한 검증 (소유자 또는 관리자만)
        테스트 후: 권한 있는 사용자만 삭제 허용, 명확한 권한 오류 메시지
        
        🔗 통합 시나리오: 파일 삭제 요청 시 권한 검증
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (소유권 검증, 역할 기반 권한)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: User (id, role), FileDocument (uploaded_by)
        출력: PermissionResult (can_delete, reason, alternative_actions)
        """
        pass
    
    def test_validate_user_quota(self):
        """
        사용자 할당량 검증
        
        테스트 전: 사용자별 현재 사용량 (파일 개수, 총 크기)
        실행 작업: 계정 타입별 할당량 대비 사용량 검증
        테스트 후: 여유 있는 사용자는 통과, 초과 사용자는 업그레이드 안내
        
        🔗 통합 시나리오: 파일 업로드 전 용량 확인
        우선순위: 🟢 선택 (최적화)
        난이도: 🟡 중급 (할당량 계산, 사용량 집계)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: User (subscription), CurrentUsage (file_count, total_size)
        출력: QuotaResult (within_limit, usage_percent, recommendations)
        """
        pass
    
    def test_rate_limiting(self):
        """
        업로드 속도 제한 검증
        
        테스트 전: 사용자별 최근 업로드 기록 (1분, 1시간, 1일)
        실행 작업: 시간 단위별 업로드 제한 검증
        테스트 후: 제한 내 사용자는 통과, 초과 사용자는 대기 시간 안내
        
        🔗 통합 시나리오: 서버 부하 방지 및 남용 차단
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (시계열 데이터, 슬라이딩 윈도우)
        실행 그룹: 🔄 순차 (시간 의존적 상태)
        
        입력: User (id), TimeWindow (duration), RequestCount
        출력: RateLimitResult (allowed, remaining_quota, reset_time)
        """
        pass
```

---

## 2. 통합 테스트 모듈

### 2.1 test_file_upload_service.py

#### 📝 모듈 목차: test_file_upload_service.py

**주요 컴포넌트들**
- `FileUploadOrchestrator`: 전체 업로드 플로우 조정
- `ValidationPipeline`: 단계별 검증 파이프라인
- `StoragePipeline`: 저장 및 메타데이터 처리 파이프라인
- `ErrorRecoveryHandler`: 오류 상황 복구 처리

**구성 함수와 핵심 내용**
- `test_full_upload_flow()`: 요청부터 응답까지 전체 플로우 검증
- `test_upload_with_metadata()`: 메타데이터 포함 업로드 시나리오
- `test_upload_error_handling()`: 다양한 오류 상황별 처리 검증
- `test_upload_rollback_scenarios()`: 실패 시 롤백 처리 검증

```python
class TestFileUploadService:
    """🔴 통합 계층 - 전체 파일 업로드 시스템 통합"""
    
    def test_full_upload_flow(self):
        """
        완전한 파일 업로드 플로우
        
        테스트 전: 인증된 사용자, 유효한 이미지 파일, 클린 시스템 상태
        실행 작업: 업로드 요청 → 검증 → 저장 → 메타데이터 생성 → 응답
        테스트 후: 파일 정상 저장, DB 문서 생성, 올바른 API 응답
        
        전제 조건: 모든 하위 단위 테스트 통과
        🚨 Mock 사용: NotificationService (업로드 완료 알림)
        🔗 E2E 시나리오: 사용자 파일 업로드 워크플로우
        우선순위: 🟦 필수 (MVP)
        난이도: 🔴 고급 (다중 시스템 통합, 트랜잭션 관리)
        실행 그룹: 🔄 순차 (DB, 파일시스템 사용)
        
        입력: UploadRequest (file, attachment_type, user_token)
        출력: UploadResponse (file_id, file_url, metadata)
        """
        pass
    
    def test_upload_with_metadata(self):
        """
        메타데이터 포함 업로드 처리
        
        테스트 전: 메타데이터가 풍부한 이미지 파일 (EXIF 정보 포함)
        실행 작업: 파일 업로드 + 메타데이터 추출 + 구조화된 저장
        테스트 후: 파일과 메타데이터 모두 정상 저장, 검색 가능한 형태
        
        전제 조건: test_extract_file_metadata() 통과
        🔗 통합 시나리오: 고급 파일 정보 활용 기능
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (메타데이터 처리, 구조화)
        실행 그룹: 🔄 순차 (DB 상태 변경)
        
        입력: RichImageFile (with EXIF, GPS, camera info)
        출력: EnhancedUploadResponse (file_info, extracted_metadata)
        """
        pass
    
    def test_upload_error_handling(self):
        """
        업로드 오류 상황별 처리
        
        테스트 전: 다양한 오류 유발 조건 (크기초과, 잘못된 형식, 권한 없음)
        실행 작업: 오류별 적절한 HTTP 상태코드 및 메시지 반환
        테스트 후: 사용자 친화적 오류 메시지, 시스템 상태 일관성 유지
        
        🔗 통합 시나리오: 사용자 오류 상황 경험 개선
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (오류 처리, 상태 관리)
        실행 그룹: 🔄 순차 (오류 상태 생성)
        
        입력: InvalidUploadRequest (various error conditions)
        출력: ErrorResponse (status_code, error_code, user_message, details)
        """
        pass
    
    def test_upload_rollback_scenarios(self):
        """
        업로드 실패 시 롤백 처리
        
        테스트 전: 부분적으로 성공한 업로드 상태 (파일 저장 완료, DB 저장 실패)
        실행 작업: 오류 발생 시 이미 수행된 작업들의 롤백 처리
        테스트 후: 모든 부분 작업 완전 취소, 시스템 상태 원복
        
        🔗 통합 시나리오: 시스템 안정성 및 데이터 일관성 보장
        우선순위: 🟡 권장 (안정화)
        난이도: 🔴 고급 (트랜잭션 관리, 복구 로직)
        실행 그룹: 🔄 순차 (복합 상태 관리)
        
        입력: PartialUploadState (completed_steps, failed_step)
        출력: RollbackResult (reverted_operations, final_state)
        """
        pass
```

### 2.2 test_file_retrieval_service.py

#### 📝 모듈 목차: test_file_retrieval_service.py

**주요 컴포넌트들**
- `FileLocator`: 파일 ID로 실제 파일 위치 검색
- `FileStreamer`: 파일 스트리밍 및 응답 처리
- `CacheManager`: 파일 캐싱 및 성능 최적화
- `AccessLogger`: 파일 접근 로그 및 통계

**구성 함수와 핵심 내용**
- `test_file_serving_flow()`: 파일 요청부터 응답까지 전체 플로우
- `test_metadata_retrieval()`: 파일 메타데이터 조회 및 반환
- `test_file_not_found_handling()`: 존재하지 않는 파일 요청 처리
- `test_cache_optimization()`: 파일 캐싱 및 성능 최적화

```python
class TestFileRetrievalService:
    """🔴 통합 계층 - 파일 조회 및 서빙 시스템"""
    
    def test_file_serving_flow(self):
        """
        파일 서빙 전체 플로우
        
        테스트 전: 업로드된 파일, 유효한 file_id
        실행 작업: 파일 ID 검증 → DB 조회 → 파일 스트리밍 → 응답 헤더 설정
        테스트 후: 올바른 파일 반환, 적절한 Content-Type, 캐시 헤더 설정
        
        전제 조건: test_full_upload_flow() 완료된 파일 존재
        🔗 통합 시나리오: 브라우저에서 이미지 표시
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (파일 스트리밍, HTTP 헤더)
        실행 그룹: 🔄 순차 (파일시스템 접근)
        
        입력: str (file_id)
        출력: FileResponse (binary_data, content_type, headers)
        """
        pass
    
    def test_metadata_retrieval(self):
        """
        파일 메타데이터 조회
        
        테스트 전: 메타데이터가 저장된 파일들
        실행 작업: 파일 ID로 메타데이터 조회 및 JSON 응답 생성
        테스트 후: 정확한 메타데이터 반환, 구조화된 JSON 형식
        
        전제 조건: test_create_file_document() 완료
        🔗 통합 시나리오: 파일 정보 표시, 관리 도구
        우선순위: 🟡 권장 (안정화)
        난이도: 🟢 초급 (DB 조회, JSON 변환)
        실행 그룹: ⚡ 병렬 (읽기 전용)
        
        입력: str (file_id)
        출력: FileInfoResponse (metadata, upload_info, usage_stats)
        """
        pass
    
    def test_file_not_found_handling(self):
        """
        존재하지 않는 파일 요청 처리
        
        테스트 전: 존재하지 않는 file_id, 삭제된 파일 ID
        실행 작업: 파일 부재 상황 감지 및 적절한 404 응답
        테스트 후: 명확한 404 오류, 도움이 되는 오류 메시지
        
        🔗 통합 시나리오: 깨진 링크 처리, 사용자 경험 개선
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (예외 처리, HTTP 상태코드)
        실행 그룹: ⚡ 병렬 (순수 함수)
        
        입력: str (nonexistent_file_id)
        출력: NotFoundResponse (404, helpful_message, suggestions)
        """
        pass
    
    def test_cache_optimization(self):
        """
        파일 캐싱 최적화
        
        테스트 전: 반복 요청되는 파일들, 다양한 파일 크기
        실행 작업: 캐시 헤더 설정, ETag 생성, 조건부 요청 처리
        테스트 후: 적절한 캐시 동작, 대역폭 절약, 성능 개선
        
        🔗 통합 시나리오: 사이트 성능 최적화, 서버 부하 감소
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (HTTP 캐싱, 성능 측정)
        실행 그룹: 🔄 순차 (캐시 상태 관리)
        
        입력: RepeatedFileRequest (file_id, if_none_match)
        출력: CachedResponse (304_or_200, cache_headers, performance_metrics)
        """
        pass
```

### 2.3 test_file_deletion_service.py

#### 📝 모듈 목차: test_file_deletion_service.py

**주요 컴포넌트들**
- `DeletionOrchestrator`: 전체 삭제 프로세스 조정
- `ReferenceManager`: 관련 문서들의 참조 정리
- `PhysicalCleaner`: 실제 파일 시스템 정리
- `DeletionAuditor`: 삭제 작업 감사 및 로깅

**구성 함수와 핵심 내용**
- `test_complete_deletion_flow()`: 권한 확인부터 완전 삭제까지 전체 플로우
- `test_reference_cleanup()`: posts/comments에서 파일 참조 제거
- `test_deletion_permission_flow()`: 삭제 권한 검증 및 오류 처리
- `test_cascade_deletion_handling()`: 연쇄 삭제 및 고아 참조 처리

```python
class TestFileDeletionService:
    """🔴 통합 계층 - 파일 삭제 및 정리 시스템"""
    
    def test_complete_deletion_flow(self):
        """
        완전한 파일 삭제 플로우
        
        테스트 전: 업로드된 파일, 게시글/댓글에 연결된 상태
        실행 작업: 권한 확인 → 참조 정리 → 물리 파일 삭제 → DB 문서 삭제
        테스트 후: 파일 완전 제거, 모든 참조 정리, 일관된 시스템 상태
        
        전제 조건: test_check_delete_permission() 통과
        🔗 통합 시나리오: 사용자 파일 삭제 워크플로우
        우선순위: 🟦 필수 (MVP)
        난이도: 🔴 고급 (다단계 삭제, 트랜잭션 관리)
        실행 그룹: 🔄 순차 (DB 및 파일시스템 변경)
        
        입력: DeletionRequest (file_id, user_token)
        출력: DeletionResponse (success, cleaned_references, audit_log)
        """
        pass
    
    def test_reference_cleanup(self):
        """
        파일 참조 정리
        
        테스트 전: 파일이 연결된 posts, comments 문서들
        실행 작업: 모든 관련 문서에서 file_id 제거 및 배열 정리
        테스트 후: 모든 참조 완전 제거, 참조 무결성 복원
        
        전제 조건: test_update_file_references() 로직 활용
        🔗 통합 시나리오: 데이터 일관성 보장
        우선순위: 🟦 필수 (MVP)
        난이도: 🔴 고급 (관계형 데이터 정리, 무결성 검증)
        실행 그룹: 🔄 순차 (DB 상태 변경)
        
        입력: str (file_id), List[str] (related_document_ids)
        출력: CleanupReport (updated_posts, updated_comments, orphaned_refs)
        """
        pass
    
    def test_deletion_permission_flow(self):
        """
        삭제 권한 검증 플로우
        
        테스트 전: 다양한 사용자 (소유자, 타인, 관리자, 비로그인)
        실행 작업: 사용자별 삭제 권한 검증 및 적절한 응답
        테스트 후: 권한 있는 사용자만 삭제 성공, 명확한 권한 오류
        
        전제 조건: test_check_delete_permission() 통과
        🔗 통합 시나리오: 보안 및 사용자 권한 관리
        우선순위: 🟦 필수 (MVP)
        난이도: 🟡 중급 (권한 검증, 오류 처리)
        실행 그룹: ⚡ 병렬 (권한 검증)
        
        입력: DeletionRequest (file_id, various_users)
        출력: PermissionResponse (allowed/denied, reason, alternatives)
        """
        pass
    
    def test_cascade_deletion_handling(self):
        """
        연쇄 삭제 및 고아 참조 처리
        
        테스트 전: 복잡한 참조 관계 (게시글 삭제 시 첨부 파일들)
        실행 작업: 상위 엔티티 삭제 시 관련 파일들의 연쇄 삭제 처리
        테스트 후: 모든 관련 파일 정리, 고아 참조 없음, 무결성 보장
        
        🔗 통합 시나리오: 게시글/댓글 삭제 시 파일 정리
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (복잡한 관계 관리, 연쇄 작업)
        실행 그룹: 🔄 순차 (복합 삭제 작업)
        
        입력: CascadeDeletionRequest (parent_entity_id, deletion_scope)
        출력: CascadeResult (deleted_files, preserved_files, integrity_report)
        """
        pass
```

---

## 3. 계약 테스트 모듈

### 3.1 test_file_api_contract.py

#### 📝 모듈 목차: test_file_api_contract.py

**주요 컴포넌트들**
- `UploadContractValidator`: 업로드 API 계약 검증
- `RetrievalContractValidator`: 조회 API 계약 검증
- `DeletionContractValidator`: 삭제 API 계약 검증
- `ErrorContractValidator`: 오류 응답 계약 검증

**구성 함수와 핵심 내용**
- `test_upload_api_contract()`: 업로드 API 요청/응답 형식 검증
- `test_retrieval_api_contract()`: 파일 조회 API 계약 준수 검증
- `test_deletion_api_contract()`: 삭제 API 계약 및 응답 검증
- `test_error_response_contracts()`: 모든 오류 상황별 응답 형식 검증

```python
class TestFileAPIContract:
    """🟠 계약 계층 - API 인터페이스 계약 검증"""
    
    def test_upload_api_contract(self):
        """
        파일 업로드 API 계약 검증
        
        테스트 전: 다양한 업로드 요청 (정상, 오류 케이스)
        실행 작업: API 요청/응답 형식의 계약 준수 검증
        테스트 후: 모든 응답이 명세서와 정확히 일치
        
        MVP 계약 검증:
        - 상태 코드: 201 (성공), 400/413/415 (오류)
        - 응답 형식: JSON
        - 필수 필드: file_id, file_url (프론트엔드 연동 필수)
        - 데이터 타입: 명세서 TypeScript 인터페이스와 일치
        
        🔗 통합 시나리오: 프론트엔드와 백엔드 간 API 계약 보장
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (스키마 검증, 형식 확인)
        실행 그룹: 🔄 순차 (실제 API 호출)
        
        입력: Various UploadRequests (valid/invalid)
        출력: ContractValidationResult (compliance_check, violations)
        """
        pass
    
    def test_retrieval_api_contract(self):
        """
        파일 조회 API 계약 검증
        
        테스트 전: 저장된 파일들, 다양한 조회 요청
        실행 작업: 파일 조회 및 메타데이터 API의 응답 형식 검증
        테스트 후: 모든 응답 헤더 및 데이터 형식 명세서 준수
        
        검증 항목:
        - Content-Type: 파일 형식에 따른 올바른 MIME 타입
        - Cache-Control: 적절한 캐시 헤더 설정
        - 메타데이터 API: JSON 응답 스키마 준수
        - 404 응답: 일관된 오류 형식
        
        🔗 통합 시나리오: 브라우저 호환성 및 캐싱 최적화
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (HTTP 헤더, 응답 검증)
        실행 그룹: 🔄 순차 (HTTP 응답 검증)
        
        입력: Various RetrievalRequests (existing/missing files)
        출력: ResponseContractResult (headers_check, content_validation)
        """
        pass
    
    def test_deletion_api_contract(self):
        """
        파일 삭제 API 계약 검증
        
        테스트 전: 삭제 가능한 파일들, 다양한 권한 사용자
        실행 작업: 삭제 API의 요청 처리 및 응답 형식 검증
        테스트 후: 성공/실패 시나리오별 일관된 응답 형식
        
        검증 항목:
        - 성공 (200): 삭제 결과 및 정리된 참조 정보
        - 권한 오류 (403): 명확한 권한 부족 메시지
        - 파일 없음 (404): 일관된 오류 응답
        - 응답 구조: TypeScript 인터페이스 준수
        
        🔗 통합 시나리오: 파일 관리 UI 연동
        우선순위: 🟦 필수 (MVP)
        난이도: 🟢 초급 (응답 스키마 검증)
        실행 그룹: 🔄 순차 (실제 삭제 작업)
        
        입력: Various DeletionRequests (authorized/unauthorized)
        출력: DeletionContractResult (response_format, status_codes)
        """
        pass
    
    def test_error_response_contracts(self):
        """
        오류 응답 계약 검증
        
        테스트 전: 모든 오류 유발 조건 (파일 크기, 형식, 권한 등)
        실행 작업: 오류 상황별 응답 형식의 일관성 검증
        테스트 후: 모든 오류 응답이 표준 형식 준수
        
        검증 항목:
        - 오류 구조: { error: { code, message, details } }
        - HTTP 상태코드: 오류 유형에 따른 적절한 코드
        - 사용자 메시지: 이해하기 쉬운 한국어 메시지
        - 개발자 정보: details 필드의 추가 정보
        
        🔗 통합 시나리오: 사용자 경험 개선 및 디버깅 지원
        우선순위: 🟡 권장 (안정화)
        난이도: 🟡 중급 (다양한 오류 케이스 커버)
        실행 그룹: 🔄 순차 (오류 상황 생성)
        
        입력: All ErrorTriggerConditions
        출력: ErrorContractReport (consistency_check, message_quality)
        """
        pass
    
    def test_api_versioning_compatibility(self):
        """
        API 버전 호환성 검증
        
        테스트 전: 현재 API 버전 및 향후 확장 계획
        실행 작업: API 변경 시 하위 호환성 보장 검증
        테스트 후: 기존 클라이언트 코드 호환성 확인
        
        🔍 향후 활용: API 진화 시 안정성 보장
        우선순위: 🟢 선택 (최적화)
        난이도: 🔴 고급 (버전 관리, 호환성 테스트)
        실행 그룹: 🔄 순차 (버전별 테스트)
        
        입력: MultiVersionRequests (v1, v2, legacy)
        출력: CompatibilityReport (breaking_changes, migration_guide)
        """
        pass
```

---

## 구현 실행 체크리스트

### 1단계: 🟦 필수 (MVP) 구현 순서

```
□ test_validate_file_type() 🟢 초급 ⚡병렬
□ test_validate_file_size() 🟢 초급 ⚡병렬
□ test_generate_file_path() 🟢 초급 ⚡병렬
□ test_save_physical_file() 🟡 중급 🔄순차
□ test_create_file_document() 🟡 중급 ⚡병렬
□ test_full_upload_flow() 🔴 고급 🔄순차
□ test_upload_api_contract() 🟢 초급 🔄순차
```

### 2단계: 🟡 권장 (안정화) 구현 순서

```
□ test_file_serving_flow() 🟡 중급 🔄순차
□ test_check_delete_permission() 🟡 중급 ⚡병렬
□ test_complete_deletion_flow() 🔴 고급 🔄순차
□ test_retrieval_api_contract() 🟢 초급 🔄순차
□ test_deletion_api_contract() 🟢 초급 🔄순차
```

### 3단계: 🟢 선택 (최적화) 구현 순서

```
□ test_validate_security_rules() 🟡 중급 ⚡병렬
□ test_concurrent_file_operations() 🔴 고급 🔄순차
□ test_cache_optimization() 🔴 고급 🔄순차
□ test_error_response_contracts() 🟡 중급 🔄순차
```

이 테스트 모듈 명세서는 File API의 체계적이고 실용적인 테스트 구현을 위한 구체적인 가이드를 제공합니다.