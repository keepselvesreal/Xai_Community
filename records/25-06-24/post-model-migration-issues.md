# 게시글 모델 마이그레이션 이슈 분석 보고서

**작성일**: 2025-06-24
**작성자**: Claude Code
**관련 태스크**: Task 3 - 게시글 기능 완전 구현

## 1. 작업 요약

### 수행한 작업
1. **백엔드 모델 수정**
   - `ServiceType`을 문서 스펙에 맞게 변경 (`"shopping"`, `"apartment"`, `"community"`)
   - 게시글 통계를 위한 `PostStats`, `UserReaction` 모델 추가
   - API 응답을 위한 `PostListItem`, `PostDetailResponse` 모델 추가
   - `PostMetadata` 구조 도입 (type, tags, attachments, visibility)

2. **프론트엔드 수정**
   - 게시글 목록 필터를 아파트 서비스 타입으로 변경
   - 비추천수 표시 추가
   - 실제 데이터 구조에 맞게 표시 로직 수정
   - 게시글 클릭시 상세 페이지 이동 구현

## 2. 발생한 문제들

### 문제 1: 데이터베이스 마이그레이션 이슈
- **증상**: `HTTP 500: Input should be 'shopping', 'apartment' or 'community' [type=literal_error, input_value='X']`
- **원인**: 기존 데이터베이스에 저장된 게시글들이 이전 서비스 타입(`'X'`, `'Threads'` 등)을 사용
- **해결**: 백워드 호환성을 위해 `ServiceType`에 이전 값들도 포함

### 문제 2: 모델 필드 불일치
- **증상**: `Failed to create post: metadata.type Field required`
- **원인**: 새로운 `PostMetadata` 구조에서 `type` 필드가 필수였으나, 기존 데이터나 요청에는 없음
- **해결**: `type` 필드를 옵셔널로 변경하고 기본값 처리 로직 추가

### 문제 3: Post 모델 필드 참조 오류
- **증상**: 라우터와 서비스에서 `post.view_count`, `post.like_count` 등 참조시 오류
- **원인**: 초기에 이 필드들을 `PostStats` 모델로 분리했으나, 코드에서는 여전히 Post 모델에서 직접 참조
- **해결**: Post 모델에 denormalized 필드로 추가 (성능 최적화)

### 문제 4: API 응답 구조 불일치
- **증상**: 프론트엔드에서 `stats` 객체 형태로 데이터를 기대하나 서버는 평면적 구조로 반환
- **원인**: 서비스 레이어에서 응답 포맷팅 누락
- **해결**: 서비스에서 `stats` 객체 구조로 변환하는 로직 추가

## 3. TDD가 문제를 예방하지 못한 이유 분석

### 3.1. 테스트 범위의 한계
- **단위 테스트 중심**: Task 3의 TDD는 새로운 기능 구현에 초점
- **마이그레이션 테스트 부재**: 기존 데이터와의 호환성 테스트가 없었음
- **통합 테스트 부족**: 실제 데이터베이스의 기존 데이터를 고려한 테스트 미비

### 3.2. 스키마 진화 고려 부족
- **Breaking Change 미고려**: `ServiceType` 변경이 기존 데이터에 미치는 영향 간과
- **점진적 마이그레이션 전략 부재**: 기존 데이터를 새 스키마로 이전하는 계획 없음

### 3.3. API 계약 테스트 부재
- **응답 구조 검증 누락**: 프론트엔드가 기대하는 응답 형태에 대한 명세와 테스트 부족
- **E2E 테스트 부재**: 프론트엔드와 백엔드 간 실제 통합 테스트 없음

## 4. 문제 해결을 위한 실용적 방법들

### 4.1. 스키마 버전 관리
```python
# 스키마 버전별 호환성 처리
class SchemaVersion:
    V1_SERVICE_TYPES = ["X", "Threads", "Bluesky", "Mastodon"]
    V2_SERVICE_TYPES = ["shopping", "apartment", "community"]
    
    @classmethod
    def migrate_service_type(cls, old_type: str) -> str:
        migration_map = {
            "X": "community",
            "Threads": "community",
            "Bluesky": "community",
            "Mastodon": "community"
        }
        return migration_map.get(old_type, old_type)
```

### 4.2. 데이터베이스 마이그레이션 스크립트
```python
# migrations/001_migrate_service_types.py
async def migrate_posts():
    """기존 게시글의 서비스 타입을 새 형식으로 마이그레이션"""
    posts = await Post.find(Post.service.in_(["X", "Threads", "Bluesky", "Mastodon"])).to_list()
    
    for post in posts:
        post.service = "community"
        if not post.metadata:
            post.metadata = PostMetadata(type="자유게시판")
        await post.save()
```

### 4.3. API 버전 관리
```python
# API 버전별 라우터
@router.get("/v1/posts")  # 기존 API 유지
async def list_posts_v1():
    # 기존 응답 형식 유지

@router.get("/v2/posts")  # 새로운 API
async def list_posts_v2():
    # 새로운 응답 형식
```

### 4.4. 점진적 마이그레이션 전략
1. **Phase 1**: 백워드 호환성 유지 (현재 적용한 방법)
2. **Phase 2**: 데이터 마이그레이션 스크립트 실행
3. **Phase 3**: 클라이언트 업데이트 후 이전 타입 지원 제거

### 4.5. 통합 테스트 강화
```python
# tests/integration/test_schema_migration.py
async def test_legacy_post_compatibility():
    """기존 형식의 게시글이 새 API에서도 조회되는지 테스트"""
    # 레거시 데이터 생성
    legacy_post = Post(
        service="X",  # 이전 서비스 타입
        metadata={}   # metadata 없음
    )
    await legacy_post.save()
    
    # API 호출
    response = await client.get("/api/posts")
    assert response.status_code == 200
```

### 4.6. API 계약 테스트
```python
# tests/contract/test_api_responses.py
def test_post_list_response_structure():
    """API 응답이 프론트엔드 기대 구조와 일치하는지 검증"""
    expected_structure = {
        "posts": [
            {
                "id": str,
                "title": str,
                "stats": {
                    "view_count": int,
                    "like_count": int,
                    "dislike_count": int,
                    "comment_count": int
                }
            }
        ]
    }
    # 구조 검증 로직
```

### 4.7. 환경별 설정 관리
```python
# config/settings.py
class Settings:
    # 마이그레이션 모드 설정
    ENABLE_LEGACY_SUPPORT = env.bool("ENABLE_LEGACY_SUPPORT", default=True)
    
    # 개발 환경에서는 더 관대하게
    if ENVIRONMENT == "development":
        STRICT_VALIDATION = False
```

## 5. 권장사항

1. **마이그레이션 전략 수립**: 스키마 변경 전 항상 마이그레이션 계획 작성
2. **버전 관리 정책**: API와 스키마 버전 관리 정책 수립
3. **통합 테스트 강화**: 실제 데이터와 클라이언트 시나리오 기반 테스트
4. **모니터링**: 프로덕션 환경에서 스키마 관련 오류 모니터링
5. **문서화**: 스키마 변경 사항과 마이그레이션 가이드 문서화

## 6. 교훈

- **Breaking Change는 신중하게**: 특히 프로덕션 데이터가 있는 경우
- **TDD의 한계 인식**: 모든 시나리오를 커버할 수 없음
- **점진적 접근**: 한 번에 모든 것을 바꾸지 말고 단계적으로
- **호환성 우선**: 새 기능보다 기존 시스템 안정성이 우선