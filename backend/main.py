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

def create_app() -> FastAPI:
    """Database 연결 테스트를 포함한 FastAPI 앱 생성"""
    logger.info("🚀 Creating FastAPI app with Database test...")
    
    app = FastAPI(
        title="XAI Community Backend - Database Test Mode",
        description="FastAPI app testing Database connection",
        version="1.0.0-db-test"
    )
    
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
        from nadle_backend.models.user import User
        from nadle_backend.models.post import Post
        from nadle_backend.models.comment import Comment
        from nadle_backend.models.file import File
        from nadle_backend.models.user_reaction import UserReaction
        from nadle_backend.models.post_stats import PostStats
        from nadle_backend.models.stats import Stats
        logger.info("✅ Models import 성공")
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
        from nadle_backend.services.user_service import UserService
        from nadle_backend.services.post_service import PostService
        from nadle_backend.services.auth_service import AuthService
        logger.info("✅ Repository/Service 계층 import 성공")
        services_status = "imported"
    except Exception as e:
        logger.error(f"❌ Repository/Service import 실패: {e}")
        services_status = "import_failed"
        services_error = str(e)
    
    # 상태 정보를 앱에 저장
    app.state.db_status = db_status
    app.state.db_error = db_error
    app.state.models_status = models_status
    app.state.models_error = models_error
    app.state.services_status = services_status
    app.state.services_error = services_error
    
    @app.get("/")
    async def root():
        logger.info("📥 Root endpoint accessed")
        return {
            "message": "XAI Community Backend - Debug Mode", 
            "status": "running",
            "environment": ENVIRONMENT,
            "port": PORT,
            "host": HOST,
            "debug": True,
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
                }
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