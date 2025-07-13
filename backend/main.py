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

# 간소화된 Lifespan 이벤트 핸들러 - Cloud Run 빠른 시작 최적화
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 - 최소한의 작업만 수행
    logger.info("🚀 Application starting... (Cloud Run optimized)")
    logger.info(f"📊 Environment: {settings.environment}")
    logger.info(f"🔌 Listening on port: {settings.port}")
    
    # Cloud Run에서는 DB 연결을 아예 건너뛰고 시작 (헬스체크 통과 우선)
    if settings.environment in ["staging", "production"]:
        logger.info("⚡ Cloud Run mode: DB connection deferred for fast startup")
        logger.info("🔗 Database will connect on first API request")
    else:
        # 개발환경에서만 즉시 DB 연결 시도
        logger.info("🛠️ Development mode: attempting immediate DB connection")
        try:
            from nadle_backend.database.connection import database
            await database.connect()
            logger.info("✅ Development database connection completed!")
        except Exception as e:
            logger.error(f"⚠️ Development database connection failed: {e}")
            logger.info("🔄 Will retry on first API request")
    
    yield
    
    # 종료 시 - 안전하게 정리
    logger.info("🔄 Application shutting down...")
    try:
        from nadle_backend.database.connection import database
        if hasattr(database, 'client') and database.client:
            await database.disconnect()
            logger.info("📦 Database disconnected")
    except Exception as e:
        logger.warning(f"⚠️ Database disconnect warning: {e}")
    logger.info("✅ Application shutdown complete")

def create_app() -> FastAPI:
    logger.info("🚀 Creating FastAPI app...")
    
    # Sentry 초기화 (조건부 및 안전)
    sentry_initialized = False
    if settings.sentry_dsn:
        try:
            from nadle_backend.monitoring.sentry_config import init_sentry
            init_sentry(
                dsn=settings.sentry_dsn,
                environment=settings.sentry_environment or settings.environment
            )
            sentry_initialized = True
            logger.info(f"✅ Sentry monitoring initialized for environment: {settings.environment}")
        except ImportError as e:
            logger.warning(f"⚠️ Sentry module not found: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Sentry initialization failed: {e}")
    
    if not sentry_initialized:
        logger.info("ℹ️ Sentry monitoring disabled (DSN not configured or initialization failed)")
    
    # Cloud Run 환경에서는 추가 모니터링 건너뛰기
    if settings.environment in ["staging", "production"]:
        logger.info("⚡ Cloud Run mode: Minimal monitoring for fast startup")
    
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
    
    # 커스텀 미들웨어 등록 (Cloud Run 최적화 - 선택적 로드)
    middleware_count = 0
    
    # Sentry 미들웨어 (조건부)
    if settings.sentry_dsn:
        try:
            from nadle_backend.middleware import SentryRequestMiddleware
            app.add_middleware(SentryRequestMiddleware)
            middleware_count += 1
            logger.info("✅ SentryRequestMiddleware added")
        except Exception as e:
            logger.warning(f"⚠️ SentryRequestMiddleware failed: {e}")
    else:
        logger.info("ℹ️ Sentry DSN not configured, skipping SentryRequestMiddleware")
    
    # 기타 커스텀 미들웨어들은 Cloud Run 빠른 시작을 위해 비활성화
    # MonitoringMiddleware 등은 Redis 연결이 필요하므로 제외
    logger.info(f"📊 Middleware loading complete: {middleware_count} custom middlewares loaded")
    logger.info("⚡ Heavy middlewares disabled for faster Cloud Run startup")
    
    # 기본 라우트
    @app.get("/")
    async def root():
        return {"message": settings.api_title, "status": "running"}
    
    # 상태 확인 엔드포인트 추가
    @app.get("/status")
    async def status():
        return {
            "status": "running",
            "message": "XAI Community Backend is healthy",
            "environment": settings.environment,
            "version": settings.api_version
        }
    
    # 정적 파일 서빙 (프론트엔드용)
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-prototypes")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"Static files mounted from: {frontend_path}")
    
    # 라우터 등록 (단계별 안전 처리)
    router_count = 0
    
    # 1. 필수 헬스체크 라우터 (최우선, 실패하면 앱 시작 중단)
    try:
        from nadle_backend.routers import health
        app.include_router(health.router, tags=["Health"])
        router_count += 1
        logger.info("✅ Health router loaded")
    except Exception as e:
        logger.error(f"❌ Critical: Health router failed: {e}")
        raise e  # 헬스체크는 필수이므로 실패시 앱 시작 중단
    
    # 2. 기본 API 라우터들 (개별적으로 안전하게 로드)
    optional_routers = [
        ("auth", "/api/auth", "Authentication"),
        ("posts", "/api/posts", "Posts"),
        ("comments", "/api/posts", "Comments"), 
        ("file_upload", "/api/files", "Files"),
        ("content", "/api/content", "Content"),
        ("users", "/api/users", "Users")
    ]
    
    for router_name, prefix, tag in optional_routers:
        try:
            router_module = __import__(f"nadle_backend.routers.{router_name}", fromlist=[router_name])
            app.include_router(router_module.router, prefix=prefix, tags=[tag])
            router_count += 1
            logger.info(f"✅ {router_name} router loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {router_name} router: {e}")
            # 개별 라우터 실패는 앱 시작을 막지 않음
    
    logger.info(f"📊 Router loading complete: {router_count}/7 routers loaded")
    
    if router_count == 0:
        logger.error("❌ No routers loaded! App may not function properly")
    elif router_count < 7:
        logger.warning(f"⚠️ Some routers failed to load ({router_count}/7)")
    else:
        logger.info("🎉 All routers loaded successfully!")
    
    # 모니터링 라우터들은 Cloud Run 빠른 시작을 위해 비활성화
    logger.info("⚡ Monitoring routers disabled for faster Cloud Run startup")
    
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
    
    # Sentry 테스트 엔드포인트
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    logger.info("🐍 Starting uvicorn server...")
    logger.info(f"📊 Environment: {settings.environment}")
    logger.info(f"🌐 Host: {settings.host}, Port: {settings.port}")
    logger.info(f"🔌 PORT 환경변수: {os.getenv('PORT', 'Not set')}")
    
    # Environment에 따른 uvicorn 설정
    if settings.environment in ["staging", "production"]:
        # Production/Staging: 최적화된 설정
        logger.info("🚀 Production/Staging mode: reload=False, workers=1")
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=False,
            workers=1,
            log_level=settings.log_level.lower(),
            access_log=True
        )
    else:
        # Development: 개발자 친화적 설정
        logger.info("🛠️ Development mode: reload=True")
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=True,
            log_level=settings.log_level.lower()
        )