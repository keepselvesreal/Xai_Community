"""
최소한의 FastAPI 앱 - Cloud Run 컨테이너 시작 디버깅용
"""
from fastapi import FastAPI
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_minimal_app() -> FastAPI:
    logger.info("🚀 Creating MINIMAL FastAPI app for debugging...")
    
    app = FastAPI(
        title="XAI Community API - DEBUG",
        description="Minimal app for debugging",
        version="1.0.0-debug"
    )
    
    @app.get("/")
    async def root():
        logger.info("📞 Root endpoint called")
        return {"message": "Minimal FastAPI app is running!", "status": "OK"}
    
    @app.get("/health")
    async def health():
        logger.info("🏥 Health endpoint called")
        return {"status": "healthy", "message": "Minimal app health check"}
    
    logger.info("✅ Minimal FastAPI app created successfully")
    return app

app = create_minimal_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("🐍 Starting minimal uvicorn server...")
    uvicorn.run("main_minimal:app", host="0.0.0.0", port=8000, reload=True)