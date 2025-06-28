# 테스트 커버리지 리포트

## 생성일: 2025-06-28

### 전체 요약
- **총 소스 라인 수**: 2,245
- **테스트된 라인 수**: 496 (22%)
- **미테스트 라인 수**: 1,749 (78%)

### 모듈별 커버리지 현황

#### 높은 커버리지 (80% 이상)
- `src/models/core.py`: 93% (282 중 19 라인 미테스트)
- `src/config.py`: 81% (81 중 15 라인 미테스트)
- `src/exceptions/base.py`: 100%
- `src/exceptions/__init__.py`: 100%

#### 중간 커버리지 (40-80%)
- `src/exceptions/post.py`: 68% (28 중 9 라인 미테스트)
- `src/exceptions/user.py`: 61% (28 중 11 라인 미테스트)
- `src/repositories/comment_repository.py`: 53% (72 중 34 라인 미테스트)
- `src/exceptions/auth.py`: 48% (31 중 16 라인 미테스트)
- `src/exceptions/comment.py`: 48% (42 중 22 라인 미테스트)
- `src/repositories/post_repository.py`: 41% (86 중 51 라인 미테스트)

#### 낮은 커버리지 (40% 미만)
- **0% 커버리지 모듈들**:
  - `src/database/connection.py`: 87 라인
  - `src/database/manager.py`: 58 라인
  - `src/dependencies/auth.py`: 80 라인
  - `src/models/content.py`: 28 라인
  - `src/repositories/file_repository.py`: 40 라인
  - `src/repositories/user_repository.py`: 66 라인
  - `src/routers/*`: 모든 라우터 파일 (427 라인)
  - `src/services/*`: 모든 서비스 파일 (457 라인)
  - `src/utils/*`: 모든 유틸리티 파일 (304 라인)

### 우선순위별 개선 계획

#### 1. 즉시 개선 필요 (HIGH)
- **Repository 계층**: post_repository, comment_repository 완전 테스트
- **Service 계층**: 핵심 비즈니스 로직 테스트 추가
- **Database 연결**: connection.py, manager.py 테스트

#### 2. 중기 개선 (MEDIUM) 
- **Router 계층**: API 엔드포인트 통합 테스트
- **Authentication**: auth.py 의존성 및 서비스 테스트
- **Utils**: JWT, password, permissions 유틸리티 테스트

#### 3. 장기 개선 (LOW)
- **File 처리**: 파일 관련 서비스 및 리포지토리
- **Content 처리**: 콘텐츠 서비스 및 모델

### 회귀 테스트 권장사항

1. **핵심 기능 보장**: Repository와 Service 계층 100% 커버리지 목표
2. **API 계약 보장**: Router 계층 주요 엔드포인트 테스트
3. **데이터 무결성**: Database 연결 및 모델 검증
4. **보안 기능**: 인증/인가 관련 완전 테스트

### 테스트 실행 명령어

```bash
# 전체 테스트 및 커버리지
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# 특정 모듈 테스트
uv run pytest tests/unit/test_*_repository.py --cov=src/repositories

# 빠른 커버리지 확인
uv run pytest --cov=src --cov-report=term-missing --tb=no -q
```

### 다음 단계
1. Repository 계층 테스트 완성 (목표: 90%+)
2. Service 계층 핵심 비즈니스 로직 테스트 추가
3. Database 연결 및 설정 테스트 강화
4. API 엔드포인트 통합 테스트 구축