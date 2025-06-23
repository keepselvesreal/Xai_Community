from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings
from database.connection import connect_to_mongo, close_mongo_connection, init_database
from routers import posts, comments, stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    logger.info("Starting up application...")
    await connect_to_mongo()
    await init_database()
    logger.info("Application startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    logger.info("Shutting down application...")
    await close_mongo_connection()
    logger.info("Application shutdown completed")

app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(stats.router)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Xai Community API",
        "version": settings.api_version,
        "status": "running",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "xai-community-api",
        "version": settings.api_version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
