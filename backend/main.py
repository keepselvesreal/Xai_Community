from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from nadle_backend.config import settings
from nadle_backend.deploy_config import DeploymentConfig

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
    
    # 요청 로깅 미들웨어 (CORS 처리는 FastAPI CORSMiddleware에 위임)
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """요청 로깅 및 모니터링 (CORS 처리 없음)."""
        origin = request.headers.get("origin")
        method = request.method
        
        logger.info(f"🔍 Request: {method} {request.url.path} from origin: {origin}")
        
        # Origin 분류 로깅만 수행 (CORS 처리는 FastAPI CORSMiddleware에서 담당)
        if origin:
            if origin == DeploymentConfig.PRODUCTION_DOMAIN:
                logger.info(f"🎯 Production domain request: {origin}")
            elif "vercel.app" in origin:
                logger.info(f"🌐 Vercel frontend request: {origin}")
            elif any(dev_url in origin for dev_url in ["localhost", "127.0.0.1"]):
                logger.debug(f"🔧 Development request: {origin}")
            else:
                logger.debug(f"🌍 External origin: {origin}")
        
        # FastAPI CORSMiddleware에서 CORS 처리하도록 위임
        response = await call_next(request)
        
        # CORS 헤더가 설정되었는지 로깅 (Simple Request는 헤더가 없을 수 있음)
        if origin:
            if "access-control-allow-origin" in response.headers:
                allowed_origin = response.headers.get("access-control-allow-origin")
                logger.info(f"✅ CORS processed by FastAPI: {origin} -> {allowed_origin}")
            else:
                # Simple Request나 preflight가 아닌 경우 CORS 헤더가 없을 수 있음
                logger.debug(f"🔍 No CORS header (possibly Simple Request): {origin}")
        
        return response
    
    # FastAPI CORSMiddleware 활성화 - 동적 CORS 기능 포함
    logger.info("🔧 Using FastAPI CORSMiddleware with dynamic origin support")
    
    # 동적 CORS Origins 생성 함수
    def get_dynamic_cors_origins():
        """동적으로 CORS Origins를 생성하는 함수."""
        origins = []
        
        if settings.environment == "production":
            # Production Domain 우선
            origins.append(DeploymentConfig.PRODUCTION_DOMAIN)
            # Legacy URLs 추가
            origins.extend(DeploymentConfig.LEGACY_DEPLOYMENT_URLS)
            logger.info(f"Production mode: Primary domain {DeploymentConfig.PRODUCTION_DOMAIN}")
            logger.info(f"Production CORS origins: {origins}")
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
    
    # 단순화: allow_origin_regex만 사용 (와일드카드 문제 회피)
    # Production에서는 Vercel 패턴으로 모든 배포 허용
    if settings.environment == "production":
        vercel_pattern = r"^https://xai-community.*\.vercel\.app$"
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=vercel_pattern,  # 패턴만 사용
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        logger.info(f"Production: Using regex pattern only: {vercel_pattern}")
    else:
        # Development에서는 명시적 origins 사용
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        logger.info(f"Development: Using explicit origins: {cors_origins}")
    
    logger.info("✅ FastAPI CORSMiddleware configured successfully")
    
    # 기본 라우트
    @app.get("/")
    async def root():
        return {"message": settings.api_title, "status": "running"}
    
    # 헬스 체크 엔드포인트
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "xai-community-backend"}
    
    # 정적 파일 서빙 (프론트엔드용)
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-prototypes")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"Static files mounted from: {frontend_path}")
    
    # 라우터 등록 (안전하게)
    try:
        from nadle_backend.routers import auth, posts, comments, file_upload, content, users
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
