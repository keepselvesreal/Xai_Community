from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from nadle_backend.config import settings
# DeploymentConfig removed - using settings instead

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
        from nadle_backend.database.connection import database
        from nadle_backend.models.core import User, Post, Comment, PostStats, UserReaction, Stats, FileRecord
        
        await database.connect()
        # 모든 Document 모델 초기화
        document_models = [User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
        logger.info(f"Initializing Beanie with models: {[model.__name__ for model in document_models]}")
        await database.init_beanie_models(document_models)
        logger.info("Database connected and Beanie initialized successfully!")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # 데이터베이스 없이도 서버는 시작되도록 함
    
    yield
    
    # 종료 시
    try:
        from nadle_backend.database.connection import database
        await database.disconnect()
        logger.info("Database disconnected")
    except:
        pass
    logger.info("Application shutting down...")

def create_app() -> FastAPI:
    # Swagger UI 설정 - 환경별 제어
    docs_url = "/docs" if settings.enable_docs and settings.environment != "production" else None
    redoc_url = "/redoc" if settings.enable_docs and settings.environment != "production" else None
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,  # 새로운 lifespan 이벤트 사용
        # OpenAPI 메타데이터 추가
        contact={
            "name": "API Support",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": f"http://localhost:{settings.port}",
                "description": "Development server"
            },
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ] if settings.environment == "development" else [],
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "사용자 인증 및 계정 관리 API - 회원가입, 로그인, 프로필 관리, 관리자 기능"
            },
            {
                "name": "Posts",
                "description": "게시글 관리 API - CRUD 작업, 검색, 정렬, 좋아요/북마크 등 상호작용"
            },
            {
                "name": "Comments",
                "description": "댓글 시스템 API - 댓글 작성/수정/삭제, 대댓글, 좋아요/싫어요"
            },
            {
                "name": "Files",
                "description": "파일 업로드 및 관리 API - 이미지 업로드, 파일 다운로드, 메타데이터 조회"
            },
            {
                "name": "Content",
                "description": "컨텐츠 처리 API - 마크다운 미리보기, 리치 텍스트 변환"
            },
            {
                "name": "Users",
                "description": "사용자 활동 조회 API - 마이페이지, 사용자 활동 통계, 네비게이션 정보"
            }
        ]
    )
    
    # CORS 미들웨어를 먼저 등록하고, 나중에 로깅 미들웨어를 등록할 예정
    
    # FastAPI CORSMiddleware 활성화 - 동적 CORS 기능 포함
    logger.info("🔧 Using FastAPI CORSMiddleware with dynamic origin support")
    
    # 동적 CORS Origins 생성 함수
    def get_dynamic_cors_origins():
        """동적으로 CORS Origins를 생성하는 함수."""
        origins = []
        
        if settings.environment in ["production", "staging"]:
            # 프로덕션과 스테이징에서는 설정된 origins 사용
            if settings.allowed_origins:
                origins.extend(settings.allowed_origins)
                logger.info(f"{settings.environment.capitalize()} CORS origins from settings: {origins}")
            else:
                logger.warning(f"{settings.environment.capitalize()} 환경에서 ALLOWED_ORIGINS가 설정되지 않았습니다!")
        elif settings.environment == "development":
            # Development URLs
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000", 
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ])
            logger.info("Development mode: CORS set for local development")
        
        return origins
    
    cors_origins = get_dynamic_cors_origins()
    
    logger.info(f"CORS Origins: {cors_origins}")
    
    # 환경변수 기반 CORS 설정 (GitHub Secrets 사용)
    if settings.environment in ["production", "staging"]:
        # 프로덕션/스테이징에서는 환경변수로 설정된 origins 사용
        if cors_origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins,  # GitHub Secrets의 ALLOWED_ORIGINS 사용
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["*"],
            )
            logger.info(f"{settings.environment.capitalize()}: Using explicit origins from ALLOWED_ORIGINS: {cors_origins}")
        else:
            # 폴백: Vercel 패턴 사용
            vercel_pattern = r"^https://xai-community[a-zA-Z0-9\-]*\.vercel\.app$"
            app.add_middleware(
                CORSMiddleware,
                allow_origin_regex=vercel_pattern,
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=["*"],
            )
            logger.warning(f"{settings.environment.capitalize()}: ALLOWED_ORIGINS not set, using fallback regex: {vercel_pattern}")
    else:
        # Development에서는 로컬 개발용 origins 사용
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        logger.info(f"Development: Using explicit origins: {cors_origins}")
    
    logger.info("✅ FastAPI CORSMiddleware configured successfully")
    
    # 🎯 커스텀 미들웨어 제거 - CORS 문제 해결 및 성능 향상
    # FastAPI는 이미 기본 요청 로깅을 제공하므로 별도 미들웨어 불필요
    
    # 기본 라우트
    @app.get("/")
    async def root():
        return {"message": settings.api_title, "status": "running"}
    
    # 헬스 체크 엔드포인트
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "xai-community-backend"}
    
    # 버전 정보 엔드포인트
    @app.get("/version")
    async def version_info():
        return {
            "version": os.getenv("BUILD_VERSION", "unknown"),
            "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
            "build_time": os.getenv("BUILD_TIME", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "service": "xai-community-backend"
        }
    
    # 정적 파일 서빙 (프론트엔드용)
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-prototypes")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"Static files mounted from: {frontend_path}")
    
    # 라우터 등록 (안전하게)
    try:
        from nadle_backend.routers import auth, posts, comments, file_upload, content, users, health
        app.include_router(health.router, tags=["Health"])
        app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
        app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])
        app.include_router(comments.router, prefix="/api/posts", tags=["Comments"])
        app.include_router(file_upload.router, prefix="/api/files", tags=["Files"])
        app.include_router(content.router, prefix="/api/content", tags=["Content"])
        app.include_router(users.router, prefix="/api/users", tags=["Users"])
        logger.info("Routers loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load routers: {e}")
        # 라우터 로드 실패해도 서버는 시작
    
    # 디버그 엔드포인트들
    @app.get("/debug/users")
    async def debug_users():
        """임시 디버그용 - 모든 사용자 목록 확인"""
        try:
            from nadle_backend.models.core import User
            users = await User.find_all().to_list()
            return {"users": [{"email": user.email, "user_handle": user.user_handle} for user in users]}
        except Exception as e:
            return {"error": str(e)}
    
    @app.delete("/debug/users/{email}")
    async def debug_delete_user(email: str):
        """임시 디버그용 - 사용자 삭제"""
        try:
            from nadle_backend.models.core import User
            user = await User.find_one({"email": email})
            if user:
                await user.delete()
                return {"message": f"User {email} deleted"}
            return {"message": "User not found"}
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/debug/posts")
    async def debug_posts():
        """임시 디버그용 - 모든 게시글 목록 확인"""
        try:
            from nadle_backend.models.core import Post
            posts = await Post.find_all().to_list()
            return {
                "total": len(posts),
                "posts": [{"title": post.title, "slug": post.slug, "service": post.service, "metadata": post.metadata.__dict__ if hasattr(post.metadata, '__dict__') else post.metadata} for post in posts[:10]]
            }
        except Exception as e:
            return {"error": str(e)}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)