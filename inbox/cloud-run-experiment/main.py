"""
간단한 FastAPI 앱 - Cloud Run 배포 실험용
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="Cloud Run 실험용 FastAPI",
    description="간단한 FastAPI 앱으로 Cloud Run 배포 테스트",
    version="1.0.0"
)

@app.get("/")
async def root():
    """기본 엔드포인트"""
    return {
        "message": "Cloud Run 실험용 FastAPI 앱이 정상 작동중입니다!",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "port": os.getenv("PORT", "8080")
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "cloud-run-experiment"
        }
    )

@app.get("/test")
async def test_endpoint():
    """테스트 엔드포인트"""
    return {
        "message": "테스트 성공!",
        "data": {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "info"),
            "port": os.getenv("PORT", "8080")
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )