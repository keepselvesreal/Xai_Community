"""
Cloud Run 디버깅을 위한 최소한의 FastAPI 애플리케이션

이 파일은 Container 시작 문제를 격리하고 디버깅하기 위해
모든 복잡한 기능들을 제거한 최소 버전입니다.
"""
from fastapi import FastAPI
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("🔍 Cloud Run 디버그 모드 시작")

# Config 클래스 import 테스트 (가장 문제 발생 가능성 높음)
logger.info("📥 Config 클래스 import 시도 중...")
try:
    from nadle_backend.config import settings
    logger.info("✅ Config 클래스 import 성공!")
    logger.info(f"📊 Settings environment: {settings.environment}")
    logger.info(f"🔌 Settings port: {settings.port}")
    logger.info(f"🏠 Settings host: {settings.host}")
    
    # settings 사용
    PORT = settings.port
    HOST = settings.host
    ENVIRONMENT = settings.environment
    
    logger.info("✅ Config 기반 설정 완료")
    
except Exception as e:
    logger.error(f"❌ Config 클래스 import 실패: {e}")
    logger.error(f"🔍 에러 타입: {type(e).__name__}")
    logger.error(f"🔍 에러 메시지: {str(e)}")
    logger.info("🔄 환경변수 폴백 사용")
    
    # 폴백: 환경변수 직접 사용
    PORT = int(os.getenv("PORT", "8080"))
    HOST = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "staging")

logger.info(f"🔌 Server configuration: {HOST}:{PORT}")
logger.info(f"📊 Environment: {ENVIRONMENT}")
logger.info(f"🐍 Python path: {os.getenv('PYTHONPATH', 'Not set')}")

# Sentry 초기화 테스트
logger.info("🔍 Sentry 초기화 시도 중...")
try:
    from nadle_backend.monitoring.sentry_config import init_sentry_for_fastapi, get_sentry_config
    
    sentry_config = get_sentry_config()
    if sentry_config.get('dsn'):
        logger.info(f"✅ Sentry DSN 발견: {sentry_config['dsn'][:20]}...")
        logger.info(f"🌍 Sentry Environment: {sentry_config['environment']}")
    else:
        logger.info("ℹ️  Sentry DSN이 설정되지 않음 - 개발 모드에서는 정상")
        
except Exception as e:
    logger.error(f"❌ Sentry 초기화 실패: {e}")

def create_app() -> FastAPI:
    """Routers와 Database 연결을 포함한 FastAPI 앱 생성"""
    logger.info("🚀 Creating FastAPI app with Routers and Database...")
    
    app = FastAPI(
        title="XAI Community Backend - Progressive Restore Mode",
        description="FastAPI app testing Routers and Database connection",
        version="1.0.0-progressive"
    )
    
    # Sentry 초기화 및 미들웨어 추가
    logger.info("🚨 Sentry 초기화 중...")
    try:
        from nadle_backend.monitoring.sentry_config import init_sentry_for_fastapi
        from nadle_backend.middleware.sentry_middleware import SentryRequestMiddleware, SentryUserMiddleware
        
        # Sentry 초기화
        init_sentry_for_fastapi(app, dsn=sentry_config.get('dsn'), environment=sentry_config.get('environment'))
        
        # Sentry 미들웨어 추가
        app.add_middleware(SentryRequestMiddleware)
        app.add_middleware(SentryUserMiddleware)
        
        logger.info("✅ Sentry 초기화 및 미들웨어 추가 완료")
        
    except Exception as e:
        logger.error(f"❌ Sentry 초기화 실패: {e}")
    
    # 1. Database 연결 테스트
    db_status = "not_tested"
    db_error = None
    
    logger.info("🗄️ Database 연결 테스트 시작...")
    try:
        from nadle_backend.database.connection import database
        logger.info("✅ Database module import 성공")
        db_status = "imported"
    except Exception as e:
        logger.error(f"❌ Database import 실패: {e}")
        db_status = "import_failed"
        db_error = str(e)
    
    # 2. Models import 테스트  
    models_status = "not_tested"
    models_error = None
    
    logger.info("📝 Models import 테스트 시작...")
    try:
        from nadle_backend.models.core import User, Post, Comment, FileRecord, UserReaction, PostStats, Stats
        from nadle_backend.models.email_verification import EmailVerification, EmailVerificationToken
        logger.info("✅ Models import 성공 (EmailVerificationToken 포함)")
        models_status = "imported"
    except Exception as e:
        logger.error(f"❌ Models import 실패: {e}")
        models_status = "import_failed" 
        models_error = str(e)
    
    # 3. Repository/Service 계층 테스트
    services_status = "not_tested"
    services_error = None
    
    logger.info("🔧 Repository/Service 계층 테스트 시작...")
    try:
        from nadle_backend.repositories.user_repository import UserRepository
        from nadle_backend.repositories.post_repository import PostRepository
        from nadle_backend.services.posts_service import PostsService
        from nadle_backend.services.auth_service import AuthService
        from nadle_backend.services.admin_service import AdminService
        logger.info("✅ Repository/Service 계층 import 성공")
        services_status = "imported"
    except Exception as e:
        logger.error(f"❌ Repository/Service import 실패: {e}")
        services_status = "import_failed"
        services_error = str(e)
    
    # 4. Routers 추가 테스트
    routers_status = "not_tested"
    routers_error = None
    
    logger.info("🛣️ Routers 추가 테스트 시작...")
    try:
        from nadle_backend.routers import auth, posts, comments, users, file_upload, content, health, monitoring, alerts, admin, analytics, reports
        from nadle_backend.logging.routers import logging_router
        
        # API 라우터들 추가
        app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
        app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
        app.include_router(comments.router, prefix="/api/posts", tags=["comments"])
        app.include_router(users.router, prefix="/api/users", tags=["users"])
        app.include_router(file_upload.router, prefix="/api/files", tags=["files"])
        app.include_router(content.router, prefix="/api/content", tags=["content"])
        app.include_router(health.router, tags=["health"])
        app.include_router(monitoring.router, tags=["monitoring"])  # HetrixTools 모니터링 라우터 추가
        app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])  # 지능형 알림 라우터 추가
        app.include_router(admin.router, prefix="/api", tags=["admin"])  # 관리자 라우터 추가
        app.include_router(analytics.router, prefix="/api", tags=["analytics"])  # 분석 라우터 추가
        app.include_router(reports.router, prefix="/api/reports", tags=["reports"])  # 신고 라우터 추가
        app.include_router(logging_router, prefix="/api", tags=["logging"])  # 로깅 시스템 라우터 추가
        
        # 클라이언트 에러 수집 라우터 추가
        from nadle_backend.routers.client_errors import router as client_errors_router
        app.include_router(client_errors_router, tags=["client-errors"])
        
        logger.info("✅ Routers 추가 성공 (HetrixTools 모니터링, 로깅 시스템, 클라이언트 에러 수집 포함)")
        routers_status = "added"
    except Exception as e:
        logger.error(f"❌ Routers 추가 실패: {e}")
        routers_status = "add_failed"
        routers_error = str(e)
    
    # 5. Database 연결 이벤트 추가
    events_status = "not_tested"
    events_error = None
    
    logger.info("⚡ Database 연결 이벤트 추가 중...")
    try:
        @app.on_event("startup")
        async def startup_event():
            logger.info("🚀 App startup - Database 연결 시작...")
            try:
                from nadle_backend.database.connection import database
                from nadle_backend.models.core import User, Post, Comment, FileRecord, UserReaction, PostStats, Stats
                
                await database.connect()
                logger.info("✅ Database 연결 성공!")
                
                # Beanie 모델 초기화 (EmailVerificationToken 포함)
                from nadle_backend.models.email_verification import EmailVerification, EmailVerificationToken
                await database.init_beanie_models([
                    User, Post, Comment, FileRecord, UserReaction, PostStats, Stats,
                    EmailVerification, EmailVerificationToken
                ])
                logger.info("✅ Beanie 모델 초기화 성공!")
            except Exception as e:
                logger.error(f"❌ Database 연결 또는 모델 초기화 실패: {e}")
                # 연결 실패해도 앱은 계속 실행 (디버깅 목적)
        
        @app.on_event("shutdown")
        async def shutdown_event():
            logger.info("🔌 App shutdown - Database 연결 해제 중...")
            try:
                from nadle_backend.database.connection import database
                await database.disconnect()
                logger.info("✅ Database 연결 해제 완료")
            except Exception as e:
                logger.error(f"❌ Database 연결 해제 실패: {e}")
        
        logger.info("✅ Database 이벤트 등록 성공")
        events_status = "registered"
    except Exception as e:
        logger.error(f"❌ Database 이벤트 등록 실패: {e}")
        events_status = "register_failed"
        events_error = str(e)
    
    # 6. MonitoringMiddleware 추가 테스트
    monitoring_status = "not_tested"
    monitoring_error = None
    
    logger.info("📊 MonitoringMiddleware 추가 중...")
    try:
        from nadle_backend.middleware.monitoring import MonitoringMiddleware
        
        # MonitoringMiddleware 추가 (Redis 연결 필요)
        app.add_middleware(MonitoringMiddleware)
        
        logger.info("✅ MonitoringMiddleware 추가 성공")
        monitoring_status = "added"
    except Exception as e:
        logger.error(f"❌ MonitoringMiddleware 추가 실패: {e}")
        monitoring_status = "add_failed"
        monitoring_error = str(e)
    
    # 7. SentryMiddleware 추가 테스트
    sentry_status = "not_tested"
    sentry_error = None
    
    logger.info("🔍 SentryMiddleware 추가 중...")
    try:
        from nadle_backend.middleware.sentry_middleware import SentryRequestMiddleware
        
        # SentryMiddleware 추가
        app.add_middleware(SentryRequestMiddleware)
        
        logger.info("✅ SentryMiddleware 추가 성공")
        sentry_status = "added"
    except Exception as e:
        logger.error(f"❌ SentryMiddleware 추가 실패: {e}")
        sentry_status = "add_failed"
        sentry_error = str(e)
    
    # 8. LoggingMiddleware 추가 테스트
    logging_middleware_status = "not_tested"
    logging_middleware_error = None
    
    logger.info("📝 LoggingMiddleware 추가 중...")
    try:
        from nadle_backend.middleware.logging_middleware import LoggingMiddleware
        
        # LoggingMiddleware 추가 (API 요청 자동 로깅)
        app.add_middleware(LoggingMiddleware)
        
        logger.info("✅ LoggingMiddleware 추가 성공")
        logging_middleware_status = "added"
    except Exception as e:
        logger.error(f"❌ LoggingMiddleware 추가 실패: {e}")
        logging_middleware_status = "add_failed"
        logging_middleware_error = str(e)
    
    # 9. Rate Limiting 미들웨어 추가
    rate_limiting_status = "not_tested"
    rate_limiting_error = None
    
    logger.info("🚦 Rate Limiting 미들웨어 추가 중...")
    try:
        from nadle_backend.middleware.rate_limiting_middleware import RateLimitingMiddleware
        
        # Rate Limiting 미들웨어 추가
        app.add_middleware(RateLimitingMiddleware)
        
        logger.info("✅ Rate Limiting 미들웨어 추가 성공")
        rate_limiting_status = "added"
    except Exception as e:
        logger.error(f"❌ Rate Limiting 미들웨어 추가 실패: {e}")
        rate_limiting_status = "add_failed"
        rate_limiting_error = str(e)
    
    # 10. CORS 및 기타 설정 추가 (최종 단계)
    final_setup_status = "not_tested"
    final_setup_error = None
    
    logger.info("🎯 최종 애플리케이션 설정 적용 중...")
    try:
        # CORS 설정 추가
        from fastapi.middleware.cors import CORSMiddleware
        logger.info("📦 CORSMiddleware import 성공")
        
        from nadle_backend.config import settings
        logger.info("⚙️ Settings 재import 성공")
        
        # 현재 설정된 origins 확인
        origins = settings.allowed_origins or ["*"]
        logger.info(f"🌐 CORS allowed_origins: {origins}")
        logger.info(f"🔧 Settings environment: {settings.environment}")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("✅ CORS 미들웨어 추가 완료!")
        
        # 앱 메타데이터 업데이트 (완전 복원됨을 표시)
        app.title = "XAI Community Backend - Full Restore"
        app.description = "완전히 복원된 XAI Community FastAPI Backend"
        app.version = "1.0.0-restored"
        
        # Exception Handlers 등록 (마지막에 등록)
        logger.info("⚠️ Exception Handlers 등록 중...")
        try:
            from nadle_backend.middleware.exception_handlers import setup_exception_handlers
            setup_exception_handlers(app)
            logger.info("✅ Exception Handlers 등록 완료")
        except Exception as handler_error:
            logger.error(f"❌ Exception Handlers 등록 실패: {handler_error}")
        
        logger.info("✅ 최종 애플리케이션 설정 완료")
        logger.info("🎉 모든 컴포넌트 점진적 복원 성공!")
        final_setup_status = "completed"
    except Exception as e:
        logger.error(f"❌ 최종 설정 실패: {e}")
        logger.error(f"🔍 에러 타입: {type(e).__name__}")
        logger.error(f"🔍 에러 메시지: {str(e)}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        final_setup_status = "failed"
        final_setup_error = str(e)
    
    # 상태 정보를 앱에 저장
    app.state.db_status = db_status
    app.state.db_error = db_error
    app.state.models_status = models_status
    app.state.models_error = models_error
    app.state.services_status = services_status
    app.state.services_error = services_error
    app.state.routers_status = routers_status
    app.state.routers_error = routers_error
    app.state.events_status = events_status
    app.state.events_error = events_error
    app.state.monitoring_status = monitoring_status
    app.state.monitoring_error = monitoring_error
    app.state.sentry_status = sentry_status
    app.state.sentry_error = sentry_error
    app.state.rate_limiting_status = rate_limiting_status
    app.state.rate_limiting_error = rate_limiting_error
    app.state.final_setup_status = final_setup_status
    app.state.final_setup_error = final_setup_error
    
    @app.get("/")
    async def root():
        logger.info("📥 Root endpoint accessed")
        return {
            "message": "XAI Community Backend - Progressive Restoration Complete!", 
            "status": "running",
            "environment": ENVIRONMENT,
            "port": PORT,
            "host": HOST,
            "restoration_mode": True,
            "all_components_loaded": True,
            "timestamp": "2025-07-13"
        }
    
    @app.get("/health")
    async def health():
        logger.info("🏥 Health check accessed")
        return {
            "status": "healthy",
            "service": "xai-community-backend-debug",
            "environment": ENVIRONMENT,
            "port": PORT,
            "message": "Container started successfully!"
        }
    
    @app.get("/status")
    async def status():
        logger.info("📊 Status check accessed")
        return {
            "status": "running",
            "message": "XAI Community Backend is healthy",
            "environment": ENVIRONMENT,
            "version": "1.0.0-debug",
            "port": PORT,
            "service": "xai-community-backend-debug"
        }
    
    @app.get("/debug")
    async def debug():
        logger.info("🔧 Debug endpoint accessed")
        return {
            "environment_variables": {
                "PORT": os.getenv("PORT"),
                "HOST": os.getenv("HOST"),
                "ENVIRONMENT": os.getenv("ENVIRONMENT"),
                "PYTHONPATH": os.getenv("PYTHONPATH"),
            },
            "server_config": {
                "host": HOST,
                "port": PORT,
                "environment": ENVIRONMENT
            },
            "component_status": {
                "database": {
                    "import_status": app.state.db_status,
                    "error": app.state.db_error
                },
                "models": {
                    "import_status": app.state.models_status,
                    "error": app.state.models_error
                },
                "services": {
                    "import_status": app.state.services_status,
                    "error": app.state.services_error
                },
                "routers": {
                    "status": app.state.routers_status,
                    "error": app.state.routers_error
                },
                "database_events": {
                    "status": app.state.events_status,
                    "error": app.state.events_error
                },
                "monitoring_middleware": {
                    "status": app.state.monitoring_status,
                    "error": app.state.monitoring_error
                },
                "sentry_middleware": {
                    "status": app.state.sentry_status,
                    "error": app.state.sentry_error
                },
                "rate_limiting_middleware": {
                    "status": app.state.rate_limiting_status,
                    "error": app.state.rate_limiting_error
                },
                "final_setup": {
                    "status": app.state.final_setup_status,
                    "error": app.state.final_setup_error
                }
            },
            "restoration_summary": {
                "total_components": 9,
                "completed_steps": [
                    "✅ 1. Database import",
                    "✅ 2. Models import", 
                    "✅ 3. Repository/Service layers",
                    "✅ 4. API Routers",
                    "✅ 5. Database events",
                    "✅ 6. MonitoringMiddleware",
                    "✅ 7. SentryMiddleware",
                    "✅ 8. LoggingMiddleware",
                    "✅ 9. RateLimitingMiddleware",
                    "✅ 10. Final CORS & Setup"
                ]
            },
            "status": "debug_mode_active"
        }
    
    @app.get("/test-db")
    async def test_database():
        """실제 Database 연결 테스트"""
        logger.info("🗄️ 실제 Database 연결 테스트 시작...")
        
        if app.state.db_status == "import_failed":
            return {
                "status": "failed",
                "message": "Database import failed",
                "error": app.state.db_error
            }
        
        try:
            # 실제 Database 연결 시도
            from nadle_backend.database.connection import database
            await database.connect()
            logger.info("✅ Database 연결 성공!")
            
            # 연결 해제
            await database.disconnect()
            logger.info("✅ Database 연결 해제 완료")
            
            return {
                "status": "success",
                "message": "Database connection test passed",
                "connection_url": "***masked***"
            }
            
        except Exception as e:
            logger.error(f"❌ Database 연결 실패: {e}")
            return {
                "status": "failed", 
                "message": "Database connection failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    logger.info("✅ Minimal FastAPI app created with debug endpoints")
    return app

# 앱 생성
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🐍 Starting uvicorn server...")
    logger.info(f"🔌 Binding to {HOST}:{PORT}")
    
    # Cloud Run 최적화 설정
    uvicorn_config = {
        "host": HOST,
        "port": PORT,
        "log_level": "info",
        "access_log": True,
        "reload": False,  # Production에서는 항상 False
        "workers": 1      # Cloud Run에서는 1개 워커 권장
    }
    
    logger.info(f"⚙️ Uvicorn config: {uvicorn_config}")
    
    try:
        uvicorn.run("main:app", **uvicorn_config)
    except Exception as e:
        logger.error(f"❌ Uvicorn start failed: {e}")
        raise