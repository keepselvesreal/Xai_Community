# Task 1: 데이터베이스 기반 설정

**Feature Group**: Core Infrastructure  
**Task List 제목**: 데이터베이스 기반 설정  
**최초 작성 시각**: 2024-12-19 15:30:00  
**완료 시각**: (미완료)

## 📋 Task 개요

### 리스크 레벨: 낮음
- **이유**: 독립적 인프라 구성, 문서화된 패턴
- **대응**: 기존 가이드 문서 활용

### 대상 파일
- `backend/src/config.py`
- `backend/src/database.py`
- `backend/src/models.py`
- `backend/src/indexes.py`

## 🎯 Subtasks

### 1. 환경 설정 관리
- **테스트 함수**: `test_config_settings`
- **구현 내용**: Pydantic을 활용한 타입 안전한 설정 관리
- **검증 항목**: 
  - MongoDB Atlas 연결 문자열 검증 (mongodb+srv:// 형식)
  - 환경 변수 로드 (config/.env 파일)
  - 기본값 설정 및 검증 규칙
- **테스트 명령어**: `uv run pytest tests/unit/test_config_settings.py -v`
- **성공 기준**: 모든 테스트 케이스 통과 (pytest exit code 0)

### 2. MongoDB 연결 관리
- **테스트 함수**: `test_database_connection`
- **구현 내용**: Motor를 사용한 비동기 MongoDB 연결
- **검증 항목**: 
  - 실제 MongoDB Atlas 연결 (Mock 사용 안함)
  - 연결 풀링 설정 확인
  - ping 테스트로 실제 연결 상태 확인
  - 에러 처리 및 재연결 로직
- **테스트 명령어**: `uv run pytest tests/unit/test_database_connection.py -v`
- **성공 기준**: MongoDB Atlas 실제 연결 테스트 통과 (pytest exit code 0)

### 3. 컬렉션 인덱스 생성
- **테스트 함수**: `test_indexes_creation`
- **구현 내용**: 성능 최적화된 MongoDB 인덱스 설정
- **검증 항목**: 
  - MongoDB Atlas에 실제 인덱스 생성
  - 복합 인덱스 (created_at + status)
  - 텍스트 검색 인덱스 (title, content)
  - 유니크 제약 (email, slug)
- **테스트 명령어**: `uv run pytest tests/unit/test_indexes_creation.py -v`
- **성공 기준**: MongoDB Atlas에 인덱스 생성 확인 (pytest exit code 0)

### 4. 기본 데이터 모델 정의
- **테스트 함수**: `test_models_validation`
- **구현 내용**: Beanie ODM 기반 데이터 모델 구조
- **검증 항목**: 
  - User, Post, Comment 모델 필드 검증
  - Pydantic 타입 변환 및 직렬화
  - Beanie Document 설정 (collection 이름, 인덱스)
  - 커스텀 validator 동작
- **테스트 명령어**: `uv run pytest tests/unit/test_models_validation.py -v`
- **성공 기준**: 모든 모델 검증 테스트 통과 (pytest exit code 0)

## 🔗 의존성
- **선행 조건**: 
  - MongoDB Atlas 계정 및 클러스터 설정
  - config/.env 파일에 실제 연결 정보 설정
- **후행 의존성**: Task 2-6의 모든 작업이 이 Task에 의존

## 📊 테스트 환경 설정
- **데이터베이스**: MongoDB Atlas (무료 티어 가능)
- **테스트 DB**: `xai_community_test` (프로덕션과 분리)
- **환경 변수**: `config/.env` 파일 사용
- **실제 연결**: Mock 데이터 사용하지 않음
- **데이터 정리**: 각 테스트 후 자동 정리 (teardown)

## ✅ 완료 조건

### 개별 Subtask 검증
```bash
# Subtask 1: 환경 설정 관리
uv run pytest tests/unit/test_config_settings.py -v

# Subtask 2: MongoDB 연결 관리  
uv run pytest tests/unit/test_database_connection.py -v

# Subtask 3: 컬렉션 인덱스 생성
uv run pytest tests/unit/test_indexes_creation.py -v

# Subtask 4: 기본 데이터 모델 정의
uv run pytest tests/unit/test_models_validation.py -v
```

### Task 전체 성공 판단
```bash
# 모든 subtask 테스트 한번에 실행
uv run pytest tests/unit/test_config_settings.py tests/unit/test_database_connection.py tests/unit/test_indexes_creation.py tests/unit/test_models_validation.py -v

# 또는 unit 테스트 전체 실행
uv run pytest tests/unit -v
```

**성공 기준**: 
- [ ] 모든 테스트 케이스 통과 (exit code 0)
- [ ] MongoDB Atlas 실제 연결 확인
- [ ] 테스트 DB에 인덱스 생성 완료
- [ ] 데이터 모델 검증 완료
- [ ] 테스트 실행 후 DB 정리 확인