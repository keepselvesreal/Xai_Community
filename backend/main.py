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

# 환경변수에서 포트 설정 (Cloud Run 최적화)
PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "staging")

logger.info(f"🔌 Server configuration: {HOST}:{PORT}")
logger.info(f"📊 Environment: {ENVIRONMENT}")
logger.info(f"🐍 Python path: {os.getenv('PYTHONPATH', 'Not set')}")

def create_app() -> FastAPI:
    """최소한의 FastAPI 앱 생성"""
    logger.info("🚀 Creating minimal FastAPI app...")
    
    app = FastAPI(
        title="XAI Community Backend - Debug Mode",
        description="Minimal FastAPI app for Cloud Run troubleshooting",
        version="1.0.0-debug"
    )
    
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
            "status": "debug_mode_active"
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