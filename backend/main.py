from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import auth
from src.database.connection import database
from src.models.core import User, Post, Comment, Reaction, Stats
from src.config import Settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Xai Community API",
        description="Community platform API with authentication, posts, and comments",
        version="1.0.0"
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발용, 프로덕션에서는 제한 필요
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우터 등록
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    
    @app.on_event("startup")
    async def startup_event():
        await database.connect()
        # Beanie ODM 초기화
        await database.init_beanie_models([User, Post, Comment, Reaction, Stats])
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await database.disconnect()
    
    @app.get("/")
    async def root():
        return {"message": "Xai Community API", "status": "running"}
    
    @app.get("/debug/users")
    async def debug_users():
        """임시 디버그용 - 모든 사용자 목록 확인"""
        users = await User.find_all().to_list()
        return {"users": [{"email": user.email, "user_handle": user.user_handle} for user in users]}
    
    @app.delete("/debug/users/{email}")
    async def debug_delete_user(email: str):
        """임시 디버그용 - 사용자 삭제"""
        user = await User.find_one({"email": email})
        if user:
            await user.delete()
            return {"message": f"User {email} deleted"}
        return {"message": "User not found"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
