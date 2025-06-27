# 데이터베이스/컬렉션 동적 생성 TDD 계획

## 목표
MongoDB Atlas에서 데이터베이스명과 컬렉션명을 사용자가 환경변수로 동적 설정 가능하도록 구현

## 🎯 점진적 TDD 단계별 실행 계획

### Phase 1: 설정 및 기본 구조 변경
**TDD 접근**: 기존 테스트가 통과하는 상태에서 설정만 확장

#### Step 1.1: 설정 파일 확장 (config.py)
- 새 컬렉션 설정 필드 추가:
  ```python
  users_collection: str = Field(default="users")
  posts_collection: str = Field(default="posts") 
  comments_collection: str = Field(default="comments")
  post_stats_collection: str = Field(default="post_stats")
  user_reactions_collection: str = Field(default="user_reactions")
  files_collection: str = Field(default="files")
  stats_collection: str = Field(default="stats")
  ```
- API 브랜딩 기본값을 일반적으로 변경
- **검증**: `test_config_settings.py` 실행하여 새 필드 검증

#### Step 1.2: 환경변수 파일 업데이트
- `.env.example`에 새 설정들 추가
- **검증**: 설정 로딩 테스트 통과 확인

### Phase 2: 모델 동적 설정 (점진적 변경)
**TDD 접근**: 한 번에 하나씩 모델 변경하고 테스트

#### Step 2.1: User 모델 동적화
- `User.Settings.name`을 `settings.users_collection`으로 변경
- **검증**: `test_user_model.py`, `test_auth_service.py` 실행
- **실제 DB 테스트**: MongoDB Atlas에 새 컬렉션 생성 확인

#### Step 2.2-2.7: 나머지 모델들 순차 변경
- Post → Comment → PostStats → UserReaction → FileRecord → Stats 순서
- 각 단계마다 해당 모델 테스트 실행
- **실제 DB 검증**: 새 컬렉션명으로 데이터 CRUD 동작 확인

### Phase 3: 하드코딩 제거
**TDD 접근**: 변경 후 즉시 관련 테스트 실행

#### Step 3.1: 모델 초기화 동적화 (main.py)
- 현재: `[User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]` 하드코딩
- 변경: 동적 모델 리스트 생성
- **검증**: 서버 시작 테스트, 모든 integration 테스트

#### Step 3.2: API 브랜딩 동적화 (main.py)
- FastAPI 생성자에서 `settings.api_title`, `settings.api_description` 사용
- **검증**: API 문서 확인, 기본 엔드포인트 테스트

#### Step 3.3: 파일 저장소 수정 (file_repository.py)
- `FILES_COLLECTION = "files"` 제거하고 `settings.files_collection` 사용
- **검증**: `test_file_repository.py`, 파일 업로드 API 테스트

#### Step 3.4: 인덱스 관리자 동적화 (database/manager.py)
- 하드코딩된 컬렉션 딕셔너리를 설정값 기반으로 변경
- **검증**: `test_indexes_creation.py` 실행

### Phase 4: MongoDB Atlas 실제 검증
**TDD 접근**: 실제 환경에서 전체 워크플로우 테스트

#### 현재 테스트 환경변수 설정:
```bash
DATABASE_NAME=dynamic_config_db
USERS_COLLECTION=members
POSTS_COLLECTION=articles
COMMENTS_COLLECTION=discussions
FILES_COLLECTION=uploads
API_TITLE=My Custom API
API_DESCRIPTION=Custom API for my application
```

#### Step 4.1: 실제 MongoDB Atlas 연결 테스트
- 새 DB/컬렉션 생성 확인
- 인덱스 생성 검증
- **검증**: `make test-integration` 실행

#### Step 4.2: 전체 API 워크플로우 테스트
- 사용자 등록/로그인 → members 컬렉션 사용
- 게시물 CRUD → articles 컬렉션 사용
- 댓글 시스템 → discussions 컬렉션 사용
- 파일 업로드 → uploads 컬렉션 사용
- **검증**: contract 테스트 모두 통과

## 🔍 수정 필요 파일 목록

### 1. 설정 파일
- `src/config.py` - 컬렉션명 설정 필드 추가
- `config/.env.example` - 새 환경변수 예시 추가

### 2. 모델 정의
- `src/models/core.py` - 7개 Document 클래스의 `Settings.name` 동적화

### 3. 애플리케이션 초기화
- `main.py` - 모델 초기화 및 API 브랜딩 동적화

### 4. 데이터베이스 관련
- `src/repositories/file_repository.py` - 하드코딩된 컬렉션명 제거
- `src/database/manager.py` - 인덱스 관리 동적화

### 5. 테스트 설정
- `tests/conftest.py` - 테스트 데이터베이스명 생성 로직 개선

## 🎯 TDD 검증 전략

### 실제 MongoDB Atlas 사용 방식
1. **기존 DB 보존**: 테스트용 별도 DB 사용
2. **점진적 검증**: 각 단계마다 실제 DB 연결 테스트
3. **롤백 가능**: 언제든 기존 설정으로 복원 가능

### 테스트 실행 순서
```bash
# 각 Phase별로 순차 실행
cd backend && make test-unit     # Phase 1-2 검증
cd backend && make test-integration  # Phase 3-4 검증  
cd backend && make test          # 전체 검증
```

## 📝 진행 상황 체크리스트

### Phase 1: 설정 확장 ⏳
- [ ] config.py 컬렉션 필드 추가
- [ ] .env.example 업데이트
- [ ] test_config_settings.py 테스트 통과

### Phase 2: 모델 동적화  
- [ ] User 모델 → members 컬렉션
- [ ] Post 모델 → articles 컬렉션
- [ ] Comment 모델 → discussions 컬렉션
- [ ] FileRecord 모델 → uploads 컬렉션
- [ ] 기타 모델들 동적화

### Phase 3: 하드코딩 제거
- [ ] main.py 모델 초기화 동적화
- [ ] main.py API 브랜딩 동적화
- [ ] file_repository.py 컬렉션명 동적화
- [ ] database/manager.py 인덱스 관리 동적화

### Phase 4: 실제 검증
- [ ] MongoDB Atlas 새 DB/컬렉션 생성 확인
- [ ] 전체 API 워크플로우 테스트

이 계획으로 **데이터베이스와 컬렉션의 완전한 동적 생성**을 달성할 수 있습니다.