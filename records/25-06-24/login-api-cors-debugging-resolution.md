# 로그인 API CORS 오류 해결 과정 기록

**날짜**: 2025-06-24  
**문제**: 대시보드에서 로그인 API 호출 시 422 오류 및 CORS 차단 발생  
**최종 결과**: ✅ 성공적으로 해결됨

## 🔍 발생한 문제점들

### 1. 초기 422 Unprocessable Entity 오류
```json
{
  "status": 422,
  "statusText": "Unprocessable Entity",
  "data": {
    "detail": [
      {
        "type": "missing",
        "loc": ["body", "username"],
        "msg": "Field required"
      },
      {
        "type": "missing", 
        "loc": ["body", "password"],
        "msg": "Field required"
      }
    ]
  }
}
```

**원인**: 프론트엔드에서 JSON 형식으로 `email`과 `password`를 보냈지만, 백엔드 OAuth2는 FormData 형식의 `username`과 `password`를 기대함

### 2. CORS 정책 차단 오류
```
Access to fetch at 'http://localhost:8000/auth/login' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**원인**: 
- CORS 설정이 하드코딩되어 실제 설정 파일을 읽지 않음
- `localhost:3000` 포트가 허용 목록에 없음
- 설정 시스템이 제대로 연결되지 않음

### 3. JWT 직렬화 오류
```
TypeError: Object of type PydanticObjectId is not JSON serializable
```

**원인**: Beanie의 `ObjectId` 타입이 JWT 토큰 생성 시 JSON으로 직렬화되지 않음

### 4. UserResponse 검증 오류
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for UserResponse
id: Input should be a valid string [type=string_type, input_value=ObjectId('...')]
```

**원인**: API 응답에서 `ObjectId`를 문자열로 변환하지 않음

## 🛠️ 해결 과정

### 1단계: 서버 시작 문제 해결
**문제**: deprecated된 `@app.on_event()` 사용으로 서버 시작 실패  
**해결**: 새로운 FastAPI `lifespan` 이벤트 핸들러로 변경

```python
# 변경 전
@app.on_event("startup")
async def startup_event():
    # ...

# 변경 후  
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    yield
    # shutdown logic

app = FastAPI(lifespan=lifespan)
```

### 2단계: CORS 설정 근본 해결
**문제**: `main.py`에서 하드코딩된 CORS 설정 사용  
**해결**: 실제 설정 시스템 연결

```python
# main.py에 추가
from src.config import settings

# CORS 설정을 설정 파일에서 읽어오기
cors_origins = settings.cors_origins
if settings.environment == "development":
    cors_origins = ["*"]  # 개발 환경에서는 모든 origin 허용
```

### 3단계: OAuth2 형식 맞춤
**문제**: JSON 형식 vs FormData 형식 불일치  
**해결**: 프론트엔드에서 OAuth2 표준 FormData 사용

```javascript
// 변경 전: JSON
body: JSON.stringify({email: "...", password: "..."})

// 변경 후: FormData
const formData = new FormData();
formData.append('username', 'test@test.com');  // OAuth2는 username 필드 사용
formData.append('password', 'password123');
```

### 4단계: JWT ObjectId 직렬화 해결
**문제**: `PydanticObjectId`가 JWT에서 직렬화되지 않음  
**해결**: `str()` 변환 추가

```python
# auth_service.py
payload = {
    "sub": str(user.id),  # ObjectId를 문자열로 변환
    "email": user.email
}
```

### 5단계: API 응답 ObjectId 변환
**문제**: `UserResponse`에서 ObjectId 타입 오류  
**해결**: 응답 생성 시 문자열 변환

```python
# auth.py
user_data = login_result["user"].model_dump()
user_data["id"] = str(user_data["id"])  # ObjectId를 문자열로 변환
return LoginResponse(..., user=UserResponse(**user_data))
```

### 6단계: 테스트 사용자 생성
**문제**: 로그인할 사용자가 DB에 없음  
**해결**: 테스트 사용자 생성 스크립트 실행

```python
# create_test_user.py (임시 파일, 사용 후 삭제)
user = User(
    email="test@test.com",
    user_handle="testuser", 
    display_name="Test User",
    password_hash=password_manager.hash_password("password123")
)
```

## 📋 최종 해결 결과

### ✅ 성공한 부분들
1. **CORS 정책**: `localhost:3000`에서 정상 접근 가능
2. **OAuth2 인증**: FormData 형식으로 올바른 요청
3. **JWT 토큰**: ObjectId 직렬화 문제 해결
4. **API 응답**: 올바른 UserResponse 형식
5. **설정 시스템**: 환경별 CORS 설정 자동 적용

### 🔧 적용된 근본적 수정사항
1. **설정 시스템 연결**: `main.py`에서 실제 `settings` 사용
2. **Lifespan 이벤트**: FastAPI 최신 표준 적용  
3. **타입 변환**: ObjectId → 문자열 자동 변환
4. **OAuth2 표준**: 프론트엔드에서 올바른 FormData 사용

### 📝 주요 교훈
1. **설정 파일 변경만으로는 부족**: 실제 코드에서 설정을 읽어와야 함
2. **OAuth2 표준 준수**: `username`/`password` FormData 형식 필수
3. **타입 직렬화**: MongoDB ObjectId는 JSON 직렬화 전 문자열 변환 필요
4. **FastAPI 버전 호환성**: deprecated API는 즉시 최신 표준으로 변경

## 🚀 이후 개발 참고사항

### 1. CORS 설정
- 개발 환경: `["*"]` (모든 origin 허용)
- 프로덕션 환경: `config/.env`의 `CORS_ORIGINS` 설정 사용
- 새 포트 추가 시: `config/.env` 파일 수정

### 2. 인증 API 사용법
```javascript
// 올바른 로그인 요청 형식
const formData = new FormData();
formData.append('username', email);  // 이메일을 username 필드로
formData.append('password', password);

fetch('/auth/login', {
    method: 'POST',
    body: formData  // Content-Type 자동 설정됨
});
```

### 3. ObjectId 처리
- JWT 토큰: `str(user.id)` 사용
- API 응답: `user_data["id"] = str(user_data["id"])` 변환
- 새 모델 추가 시: ObjectId 필드는 항상 문자열로 변환

이 기록을 통해 향후 유사한 문제 발생 시 빠른 해결이 가능할 것입니다.