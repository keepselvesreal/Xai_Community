from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from src.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan 이벤트 핸들러 (새로운 FastAPI 표준)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    logger.info("Application starting...")
    try:
        # 데이터베이스 연결 시도
        from src.database.connection import database
        from src.models.core import User, Post, Comment, PostStats, UserReaction, Stats
        
        await database.connect()
        await database.init_beanie_models([User, Post, Comment, PostStats, UserReaction, Stats])
        logger.info("Database connected successfully!")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # 데이터베이스 없이도 서버는 시작되도록 함
    
    yield
    
    # 종료 시
    try:
        from src.database.connection import database
        await database.disconnect()
        logger.info("Database disconnected")
    except:
        pass
    logger.info("Application shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Xai Community API",
        description="Community platform API with authentication, posts, and comments",
        version="1.0.0",
        lifespan=lifespan  # 새로운 lifespan 이벤트 사용
    )
    
    # CORS 설정 - 설정 파일에서 읽어오기
    cors_origins = settings.cors_origins
    if settings.environment == "development":
        # 개발 환경에서는 더 관대하게
        cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080"
        ]
        logger.info("Development mode: CORS set for local development")
    
    logger.info(f"CORS Origins: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # 기본 라우트
    @app.get("/")
    async def root():
        return {"message": "Xai Community API", "status": "running"}
    
    # 라우터 등록 (안전하게)
    try:
        from src.routers import auth, posts, comments
        app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
        app.include_router(posts.router, tags=["Posts"])
        app.include_router(comments.router, tags=["Comments"])
        logger.info("Routers loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load routers: {e}")
        # 라우터 로드 실패해도 서버는 시작
    
    # 디버그 엔드포인트들
    @app.get("/debug/users")
    async def debug_users():
        """임시 디버그용 - 모든 사용자 목록 확인"""
        try:
            from src.models.core import User
            users = await User.find_all().to_list()
            return {"users": [{"email": user.email, "user_handle": user.user_handle} for user in users]}
        except Exception as e:
            return {"error": str(e)}
    
    @app.delete("/debug/users/{email}")
    async def debug_delete_user(email: str):
        """임시 디버그용 - 사용자 삭제"""
        try:
            from src.models.core import User
            user = await User.find_one({"email": email})
            if user:
                await user.delete()
                return {"message": f"User {email} deleted"}
            return {"message": "User not found"}
        except Exception as e:
            return {"error": str(e)}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
