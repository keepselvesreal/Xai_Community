"""
최소한의 FastAPI 앱 - Cloud Run 컨테이너 시작 디버깅용
점진적으로 기능을 추가하여 문제 지점 파악
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 기본 설정
try:
    from nadle_backend.config import settings
    logger.info(f"✅ Settings loaded: environment={settings.environment}")
except Exception as e:
    logger.error(f"❌ Failed to load settings: {e}")
    # 폴백 설정
    class FallbackSettings:
        environment = os.getenv("ENVIRONMENT", "development")
        enable_docs = True
    settings = FallbackSettings()

def create_minimal_app() -> FastAPI:
    logger.info("🚀 Creating MINIMAL FastAPI app for debugging...")
    
    # 기본 앱 생성
    app = FastAPI(
        title="XAI Community API - DEBUG",
        description="Minimal app for debugging",
        version="1.0.0-debug",
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None
    )
    
    # 기본 CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 테스트용으로 모든 오리진 허용
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    logger.info("✅ Basic CORS middleware added")
    
    @app.get("/")
    async def root():
        logger.info("📞 Root endpoint called")
        return {"message": "Minimal FastAPI app is running!", "status": "OK"}
    
    @app.get("/health")
    async def health():
        logger.info("🏥 Health endpoint called")
        return {"status": "healthy", "message": "Minimal app health check"}
    
    @app.get("/status")
    async def status():
        logger.info("📊 Status endpoint called")
        return {"status": "running", "message": "Minimal app status check", "version": "1.0.0-debug"}
    
    # 실제 헬스체크 라우터 추가 시도
    try:
        from nadle_backend.routers import health
        app.include_router(health.router, tags=["Health"])
        logger.info("✅ Health router loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load health router: {e}")
        # 폴백으로 기본 엔드포인트 유지
    
    logger.info("✅ Minimal FastAPI app created successfully")
    return app

app = create_minimal_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("🐍 Starting minimal uvicorn server...")
    uvicorn.run("main_minimal:app", host="0.0.0.0", port=8000, reload=True)