# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

이것은 FastAPI 백엔드와 Remix React 프론트엔드를 가진 풀스택 웹 애플리케이션입니다. 백엔드는 Domain-Driven Design 원칙을 따르며 MongoDB와 Motor를 사용한 비동기 데이터베이스 운영을 합니다. 프로젝트는 TDD 관행과 태스크 기반 개발을 구현합니다.

### 전체 프로젝트 구조

```
v5/
├── backend/               # FastAPI 백엔드 애플리케이션 (nadle_backend 패키지)
│   ├── nadle_backend/     # 메인 백엔드 소스 코드
│   ├── tests/             # 종합적인 테스트 스위트 (unit/integration/e2e/performance)
│   ├── deploy/            # 배포 설정 (Cloud Run, VM)
│   ├── uploads/           # 파일 업로드 저장소
│   └── main.py           # FastAPI 애플리케이션 진입점
├── frontend/              # Remix React 앱 (메인 프로덕션 UI)
│   ├── app/              # Remix 애플리케이션 소스
│   ├── tests/            # 프론트엔드 테스트 (unit/integration/e2e/performance)
│   └── deploy/           # 프론트엔드 배포 설정
├── frontend-prototypes/   # HTML UI (API 통합 및 테스트용)
│   └── UI.html           # 완성된 대시보드 인터페이스 (API 테스트용)
├── scripts/              # 자동화 스크립트
│   ├── deployment/       # 배포 스크립트 (staging/production)
│   ├── database/         # 데이터베이스 관리 스크립트
│   ├── development/      # 개발용 스크립트 및 데이터 생성
│   └── monitoring/       # 모니터링 및 헬스체크
├── deploy/               # 글로벌 배포 설정
├── docs/                 # 문서 파일들
├── tasks/                # 태스크 관리 시스템
├── records/              # 프로젝트 기록 및 로그
├── references/           # 참고 자료
└── design-prototype/     # UI/UX 프로토타입
```

### 백엔드 아키텍처 계층

**API 계층** (`routers/`) → **서비스 계층** (`services/`) → **레포지토리 계층** (`repositories/`) → **모델 계층** (`models/`) → **데이터베이스** (MongoDB)

- 의존성은 아래 방향으로만 흐름 (순환 의존성 없음)
- 각 계층은 단일 책임을 가짐
- 비즈니스 로직은 서비스 계층에 포함
- 데이터 접근은 레포지토리를 통해 추상화
- Redis를 통한 캐싱 시스템 구현 (환경별 분리된 키 네임스페이싱)

### 프론트엔드 전략

- **메인 UI**: `frontend/` (Remix React) - 메인 프로덕션 UI 애플리케이션
- **API 개발 도구**: `frontend-prototypes/UI.html` - API 테스트 및 개발용 HTML 대시보드
- **프론트엔드 아키텍처**: TypeScript, Tailwind CSS, Vitest를 사용한 완전한 기능의 Remix React 애플리케이션
- **개발 상태**: `frontend/` 워크스페이스를 사용한 활발한 프로덕션 서비스 UI 개발
- **API 통합**: 종합적인 API 계층을 통한 FastAPI 백엔드 통합

### 현재 구현 상태

- ✅ **인프라 계층**: 데이터베이스 연결, 모델, 설정, 인덱스
- ✅ **API 계층**: 7개 라우터를 가진 완전한 REST API (auth, posts, comments, files, content, users, health)
- ✅ **서비스 계층**: 모든 도메인에 걸친 완전한 비즈니스 로직 구현
- ✅ **레포지토리 계층**: CRUD 작업을 가진 완전한 데이터 접근 계층
- ✅ **파일 관리**: 검증을 포함한 완전한 파일 업로드/처리 시스템
- ✅ **리치 텍스트 에디터**: 콘텐츠 처리 파이프라인을 가진 TDD 기반 에디터
- ✅ **HTML UI**: API 테스트 기능을 가진 완전한 대시보드 인터페이스
- ✅ **Remix 프론트엔드**: 종합적인 컴포넌트 라이브러리와 라우팅 시스템을 가진 메인 프로덕션 UI
- ✅ **캐싱 시스템**: 하이브리드 Redis 아키텍처 (로컬 + Upstash 클라우드, 환경별 키 네임스페이싱)
- ✅ **배포 시스템**: Cloud Run 자동배포, VM 배포, 롤백 시스템
- ✅ **테스트 시스템**: 유닛/통합/E2E/성능 테스트 포괄적 구현
- ✅ **모니터링**: 성능 모니터링, 헬스체크, 로그 시스템

### 기술 스택 및 도구

#### 백엔드 (nadle_backend)
- **Framework**: FastAPI (v0.115.12+)
- **데이터베이스**: MongoDB with Motor (비동기 ODM)
- **ODM**: Beanie (v1.27.0+)
- **인증**: JWT (python-jose) + bcrypt password hashing
- **캐싱**: 하이브리드 Redis 시스템 (로컬 Redis + Upstash Cloud Redis)
- **파일 처리**: Pillow, python-multipart
- **콘텐츠 처리**: Markdown, BeautifulSoup4, bleach
- **테스팅**: pytest, pytest-asyncio, pytest-cov
- **성능 테스트**: Locust
- **브라우저 테스트**: Playwright

#### 프론트엔드 (xai-community-frontend)
- **Framework**: Remix React (v2.16.8)
- **타입스크립트**: TypeScript (v5.1.6+)
- **스타일링**: Tailwind CSS (v3.4.4+)
- **상태 관리**: React Context API
- **테스팅**: Vitest (v3.2.4), Testing Library
- **빌드 도구**: Vite (v6.0.0+)
- **보안**: isomorphic-dompurify (XSS 방지)

#### 배포 및 인프라
- **프로덕션 배포**: Google Cloud Run (자동배포)
- **스테이징 배포**: Google Cloud Run (Preview Environment)
- **VM 배포**: Google Compute Engine (대체 배포)
- **CI/CD**: GitHub Actions (자동배포, 롤백 시스템)
- **모니터링**: 커스텀 헬스체크, 성능 모니터링

### Redis 캐싱 아키텍처

#### 하이브리드 Redis 시스템
프로젝트는 환경에 따라 다른 Redis 전략을 사용합니다:

**환경별 Redis 사용 전략:**
- **개발환경** (`development`): 로컬 Redis + `dev:` 키 프리픽스
- **테스트환경** (`test`): 로컬 Redis + `test:` 키 프리픽스
- **스테이징환경** (`staging`): Upstash Cloud Redis + `stage:` 키 프리픽스
- **프로덕션환경** (`production`): Upstash Cloud Redis + `prod:` 키 프리픽스

#### 키 네임스페이싱 시스템
모든 Redis 키는 환경별 프리픽스를 사용하여 데이터 분리:
```
개발: dev:cache:user:123
스테이징: stage:cache:user:123
프로덕션: prod:cache:user:123
```

#### 팩토리 패턴 구현
- `RedisFactory`: 환경에 따른 자동 Redis 클라이언트 선택
- `UpstashRedisManager`: REST API 기반 Upstash Redis 클라이언트
- `RedisManager`: 로컬 Redis 클라이언트 (기존)

#### 캐싱 서비스들
- `CacheService`: 기본 캐싱 작업
- `SessionService`: 사용자 세션 관리
- `PopularPostsCacheService`: 인기 게시글 캐싱
- `PostStatsCacheService`: 게시글 통계 캐싱
- `TokenBlacklistService`: JWT 토큰 블랙리스트

### Frontend Workspace
- 현재 작업하는 UI 프로젝트 폴더는 `frontend/`
- API 테스트 및 개발용 도구: `frontend-prototypes/UI.html`

### 개발 명령어

#### 백엔드
```bash
# 종속성 설치
cd backend && uv sync

# 개발 서버 실행
cd backend && uv run python main.py

# 테스트 실행
cd backend && uv run pytest

# 커버리지 포함 테스트
cd backend && uv run pytest --cov=nadle_backend

# 성능 테스트
cd backend && uv run python -m pytest tests/performance/

# Redis 통합 테스트
cd backend && uv run python tests/integration/test_simple_namespacing.py

# 코드 포맷팅
cd backend && uv run black nadle_backend

# 린팅
cd backend && uv run flake8 nadle_backend
```

#### 프론트엔드
```bash
# 종속성 설치
cd frontend && npm install

# 개발 서버 실행
cd frontend && npm run dev

# 빌드
cd frontend && npm run build

# 테스트 실행
cd frontend && npm test

# 타입 체크
cd frontend && npm run typecheck

# 린팅
cd frontend && npm run lint
```

### 환경 설정

#### Redis 환경변수 설정

**로컬 Redis (개발/테스트)**
```bash
# .env.dev 또는 .env.test
REDIS_URL=redis://localhost:6379
CACHE_ENABLED=true
```

**Upstash Redis (스테이징/프로덕션)**
```bash
# .env.staging 또는 .env.prod
UPSTASH_REDIS_REST_URL=https://your-upstash-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
CACHE_ENABLED=true
```

#### 환경별 설정 파일
- `.env.dev`: 개발환경 설정
- `.env.staging`: 스테이징환경 설정  
- `.env.prod`: 프로덕션환경 설정
- `.env.test`: 테스트환경 설정

#### Redis 연결 확인
```bash
# Redis 상태 확인 API 엔드포인트
GET /health
# 응답에서 redis_type과 key_prefix 확인
```

## Custom rules
### Communication 
- 모든 답변은 한국어로 작성해야 한다.
- 사용자 이름은 "태수"이고, 친구처럼 대한다.
- 사용자 요청에서 확실히 이해하지 못한 부분이 있다면 마음대로 해석해 작업을 진행하면 안된다. 헷갈리는 부분에 대해 사용자에게 질문하여 수행할 작업을 확실히 이해해야 한다.

### Execution 
- docs 폴더 내 파일 수정 시 기존 파일을 수정하지 않고, 새로운 버전의 파일을 만들어 수정 사항을 반영한다.
- 서버 실행 전에 이미 동작 중인 서버가 있는지 확인한다.
- 사용자가 제공한 정보도 비판적으로 검토하며, 무조건 신뢰하지 않는다.
- 패키지 설치 시 가상환경 등이 있는지 반드시 확인한다. 

### Coding
- 폴더나 파일을 만들 때는 기존 프로젝트 구조의 체계를 반영한다.
- 타입 검사를 활용하여 런타임 이전에 감지 가능한 오류를 사전에 방지한다.
- 오류 발생 가능성이 있는 부분에는 디버깅을 위한 코드 또는 로깅을 적절히 삽입한다.