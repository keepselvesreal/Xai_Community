# 게시글 API 문제 해결 및 TDD 분석 종합 기록

**날짜**: 2025-06-24  
**작업자**: Claude Code  
**작업 범위**: Task 3 게시글 시스템 - API 연동 문제 해결 및 개선 방안 분석

## 📋 작업 개요

게시글 생성 시 발생한 CORS 오류와 500 Internal Server Error 문제를 체계적으로 분석하고 해결했으며, TDD가 이러한 문제를 예방하지 못한 원인을 분석했습니다.

## 🔍 발생한 문제 상세 분석

### 1. 초기 문제: 422 Unprocessable Entity
- **증상**: 게시글 작성 시 422 오류 발생
- **원인**: 
  - UI의 서비스 필드 값("community", "shopping")이 ServiceType enum("X", "Threads", "Bluesky", "Mastodon")과 불일치
  - PostBase 모델이 요구하는 metadata.type 필드가 UI에서 누락

### 2. CORS 정책 차단
- **증상**: "No 'Access-Control-Allow-Origin' header is present" 오류
- **원인**: 
  - 개발 환경에서 CORS origins가 "*"로 설정되었으나 실제로는 작동하지 않음
  - 500 에러 발생 시 CORS 헤더가 응답에 포함되지 않아 브라우저가 CORS 오류로 표시

### 3. JWT 인증 실패  
- **증상**: 401 Unauthorized - "Invalid token signature"
- **원인**: 
  - 서버 재시작으로 JWT 시크릿 키가 기본값에서 .env 파일 값으로 변경
  - 기존에 발급된 토큰이 새로운 시크릿 키로 검증 실패

### 4. 500 Internal Server Error (핵심 문제)
- **증상**: 
  - curl 테스트: 401 응답과 CORS 헤더 정상 반환
  - 브라우저: 500 에러 발생, CORS 헤더 누락으로 CORS 차단 메시지 표시
- **근본 원인**: 
  ```python
  PydanticSerializationError: Unable to serialize unknown type: <class 'beanie.odm.fields.PydanticObjectId'>
  ```
  - Beanie ODM의 `PydanticObjectId`가 FastAPI의 기본 JSON encoder로 직렬화되지 않음

## 🛠️ 문제 해결 과정

### 1단계: UI 데이터 구조 수정
```javascript
// metadata 필드 추가 및 service 값 수정
const postData = {
    title: formData.get('title'),
    content: formData.get('content'),
    service: formData.get('service') || 'X',  // enum 값과 일치
    tags: formData.get('tags') ? formData.get('tags').split(',').map(tag => tag.trim()) : [],
    metadata: {
        type: formData.get('type') || '자유게시판',
        visibility: 'public'
    }
};
```

### 2단계: CORS 설정 개선
```python
# 개발 환경에서도 명시적 origin 목록 사용
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]
```

### 3단계: ObjectId 직렬화 문제 해결

모든 엔드포인트에서 ObjectId를 문자열로 변환:

```python
# POST /api/posts/ 엔드포인트
return PostResponse(
    id=str(post.id),  # ObjectId → string
    author_id=str(post.author_id),  # ObjectId → string
    # ... 나머지 필드들
)

# GET /api/posts/ 엔드포인트  
if "items" in result:
    for item in result["items"]:
        if "_id" in item:
            item["_id"] = str(item["_id"])
        if "id" in item:
            item["id"] = str(item["id"])
        if "author_id" in item:
            item["author_id"] = str(item["author_id"])
```

### 4단계: 프론트엔드 에러 핸들링 개선
```javascript
// 401 에러 시 자동으로 토큰 삭제 및 재로그인 유도
if (response.status === 401) {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    currentUser = null;
    updateAuthUI();
    showNotification('인증이 만료되었습니다. 다시 로그인해주세요.', 'error');
    showPage('login');
    return;
}
```

## 🧪 TDD가 문제를 예방하지 못한 이유 분석

### 1. 테스트 범위의 한계

**Unit Tests (`test_posts_service.py`)**:
- Mock 객체 사용으로 실제 MongoDB 문서의 동작 재현 실패
- `model_dump()` 메서드가 이미 직렬화된 딕셔너리 반환
- 실제 ObjectId → string 변환 과정이 테스트되지 않음

**Integration Tests (`test_posts_router.py`)**:
- 서비스 레이어까지 Mock 처리
- 실제 데이터베이스 왕복 과정 없음
- CORS 미들웨어 동작 테스트 누락

### 2. Mock과 실제 동작의 차이

```python
# 테스트에서 사용한 Mock
post = Mock()
post.id = "507f1f77bcf86cd799439012"  # 이미 문자열

# 실제 Beanie 문서
post = Post(...)
post.id  # PydanticObjectId 타입 반환
```

### 3. 누락된 테스트 카테고리

- **End-to-End 테스트**: HTTP 요청 → 데이터베이스 → HTTP 응답 전체 플로우
- **직렬화 테스트**: 실제 MongoDB 객체의 JSON 변환 검증
- **인프라 테스트**: CORS, 미들웨어, 서버 설정
- **프론트엔드 통합 테스트**: HTML UI에서의 실제 API 호출

### 4. Task 명세의 한계

Task 3 명세서에는 다음 내용이 누락:
- MongoDB ObjectId 처리 방법
- CORS 요구사항
- 프론트엔드 통합 시나리오
- JSON 응답 형식의 세부 사항

## 💡 문제 해결/예방을 위한 실용적 방법들

### 1. 테스트 전략 개선

**실제 객체 사용 테스트**:
```python
async def test_post_response_serialization():
    """실제 Beanie 문서가 JSON으로 올바르게 직렬화되는지 테스트"""
    post = Post(title="Test", service="X", ...)
    # 실제 ObjectId를 가진 문서 생성
    await post.save()
    
    # JSON 직렬화 시도
    response_data = PostResponse(
        id=str(post.id),
        # ... 나머지 필드
    )
    json_str = response_data.json()  # 실패하면 안됨
```

**실제 데이터베이스 사용 통합 테스트**:
```python
async def test_create_post_e2e(test_db):
    """실제 데이터베이스를 사용한 전체 플로우 테스트"""
    response = client.post("/api/posts", 
                          json={"title": "Test", ...},
                          headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["id"], str)  # ObjectId가 문자열로 변환되었는지
```

### 2. 개발 프로세스 개선

**1) 프론트엔드 우선 통합**:
- API 개발 초기부터 프론트엔드와 연동 테스트
- Postman/Thunder Client 대신 실제 UI로 테스트

**2) 타입 안전성 강화**:
```python
# Response 모델에 명시적 변환 메서드 추가
class PostResponse(BaseModel):
    @classmethod
    def from_document(cls, doc: Post) -> "PostResponse":
        return cls(
            id=str(doc.id),
            author_id=str(doc.author_id),
            # ... 자동 변환 로직
        )
```

**3) 미들웨어 테스트 추가**:
```python
def test_cors_preflight():
    """CORS preflight 요청 테스트"""
    response = client.options("/api/posts",
                            headers={
                                "Origin": "http://localhost:3000",
                                "Access-Control-Request-Method": "POST"
                            })
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
```

### 3. 도구 및 자동화

**1) Pre-commit Hook**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: test-serialization
        name: Test API Serialization
        entry: pytest tests/test_serialization.py
        language: system
        files: '^src/models/|^src/routers/'
```

**2) 자동 직렬화 검증**:
```python
# 모든 Response 모델에 대한 자동 검증
def validate_serializable(model_class):
    """데코레이터로 모델의 직렬화 가능성 검증"""
    original_init = model_class.__init__
    
    def new_init(self, **data):
        original_init(self, **data)
        try:
            self.json()  # 직렬화 가능한지 즉시 확인
        except Exception as e:
            raise ValueError(f"Model not serializable: {e}")
    
    model_class.__init__ = new_init
    return model_class
```

**3) 개발 환경 설정 검증**:
```python
# startup 시 설정 검증
@app.on_event("startup")
async def validate_configuration():
    # CORS 설정 검증
    assert settings.cors_origins, "CORS origins not configured"
    
    # JWT 설정 검증
    assert len(settings.secret_key) >= 32, "Secret key too short"
    
    # 데이터베이스 연결 테스트
    await database.ping()
```

### 4. 문서화 및 명세 개선

**API 명세에 추가할 내용**:
```yaml
# api-spec.yaml
responses:
  PostResponse:
    description: 게시글 응답
    content:
      application/json:
        schema:
          properties:
            id:
              type: string
              description: "MongoDB ObjectId를 문자열로 변환"
              example: "507f1f77bcf86cd799439012"
```

**개발 가이드 추가**:
```markdown
## MongoDB ObjectId 처리

모든 API 응답에서 ObjectId는 문자열로 변환해야 합니다:
- `_id` → `id` (문자열)
- 관련 ID 필드들도 모두 문자열로 변환
- Response 모델에서 명시적 변환 필요
```

### 5. 모니터링 및 디버깅

**1) 에러 로깅 강화**:
```python
@app.exception_handler(PydanticSerializationError)
async def serialization_error_handler(request, exc):
    logger.error(f"Serialization error: {exc}")
    logger.error(f"Problematic data: {exc.args}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Data serialization error"},
        headers={"Access-Control-Allow-Origin": "*"}  # CORS 헤더 포함
    )
```

**2) 개발 모드 디버깅**:
```python
if settings.environment == "development":
    @app.middleware("http")
    async def debug_middleware(request, call_next):
        logger.debug(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.debug(f"Response: {response.status_code}")
        return response
```

## 📊 교훈 및 개선 방향

1. **TDD는 비즈니스 로직에는 효과적이지만, 인프라 및 통합 문제는 놓치기 쉽다**
2. **Mock 사용은 신중히 - 실제 객체와의 차이를 인지해야 함**
3. **프론트엔드 통합은 개발 초기부터 진행**
4. **직렬화 문제는 별도의 테스트 카테고리로 관리**
5. **CORS 같은 인프라 설정도 테스트 대상에 포함**

---

**작성 시각**: 2025-06-24 16:50:00  
**총 소요 시간**: 약 2시간  
**최종 상태**: 모든 문제 해결 완료, 개선 방안 도출