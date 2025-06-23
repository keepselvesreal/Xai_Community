from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Backend API",
    description="FastAPI backend for the development environment",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Hello World", "status": "success"}


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "backend-api"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """사용자 정보 조회 엔드포인트"""
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
    }


@app.post("/api/users")
async def create_user(user_data: dict):
    """사용자 생성 엔드포인트"""
    return {
        "id": 123,
        "name": user_data.get("name", "Unknown"),
        "email": user_data.get("email", "unknown@example.com"),
        "created": True,
    }
