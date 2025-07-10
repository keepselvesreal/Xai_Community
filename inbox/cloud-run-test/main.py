"""
간단한 Cloud Run 테스트용 FastAPI 서버

이 서버는 Google Cloud Run 배포를 테스트하기 위한 최소한의 FastAPI 애플리케이션입니다.
디버깅과 모니터링 기능을 포함하여 배포 과정에서 발생할 수 있는 문제를 쉽게 파악할 수 있도록 구성되었습니다.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Cloud Run Test API",
    description="Google Cloud Run 배포 테스트용 FastAPI 서버",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (개발 및 테스트용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 테스트용이므로 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 시작 시간 저장
start_time = time.time()

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time_req = time.time()
    
    # 요청 정보 로깅
    logger.info(f"📥 요청: {request.method} {request.url.path}")
    if request.query_params:
        logger.info(f"📝 Query Params: {dict(request.query_params)}")
    
    # 요청 처리
    response = await call_next(request)
    
    # 응답 시간 계산
    process_time = time.time() - start_time_req
    
    # 응답 정보 로깅
    logger.info(f"📤 응답: {response.status_code} - {process_time:.3f}초")
    
    return response

@app.get("/")
async def root():
    """루트 엔드포인트 - 서버 기본 정보"""
    return {
        "message": "Cloud Run 테스트 서버가 정상적으로 실행 중입니다! 🚀",
        "status": "running",
        "service": "cloud-run-test",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2)
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2),
        "checks": {
            "server": "ok",
            "memory": "ok",
            "cpu": "ok"
        }
    }

@app.get("/env")
async def get_environment():
    """환경변수 정보 (민감한 정보 제외)"""
    safe_env_vars = {}
    
    # 표시할 환경변수들 (민감하지 않은 정보만)
    display_vars = [
        "PORT", "HOST", "ENVIRONMENT", "GOOGLE_CLOUD_PROJECT", 
        "K_SERVICE", "K_REVISION", "K_CONFIGURATION",
        "GAE_SERVICE", "GAE_VERSION", "GAE_INSTANCE",
        "CLOUD_RUN_JOB", "CLOUD_RUN_TASK_INDEX", "CLOUD_RUN_TASK_COUNT"
    ]
    
    for var in display_vars:
        value = os.getenv(var)
        if value:
            safe_env_vars[var] = value
    
    # 시스템 정보 추가
    system_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "cwd": os.getcwd(),
        "hostname": os.getenv("HOSTNAME", "unknown")
    }
    
    return {
        "environment_variables": safe_env_vars,
        "system_info": system_info,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/all-env")
async def get_all_environment():
    """모든 환경변수 정보 (디버깅용 - 민감한 정보는 마스킹)"""
    masked_env = {}
    
    # 민감한 정보가 포함될 수 있는 키워드들
    sensitive_keywords = [
        "password", "secret", "key", "token", "credential", "auth",
        "private", "cert", "ssl", "tls", "oauth", "api_key"
    ]
    
    for key, value in os.environ.items():
        # 민감한 키워드가 포함된 경우 마스킹
        if any(keyword in key.lower() for keyword in sensitive_keywords):
            if len(value) > 4:
                masked_env[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                masked_env[key] = "***"
        else:
            masked_env[key] = value
    
    return {
        "all_environment_variables": masked_env,
        "total_count": len(os.environ),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/request-info")
async def get_request_info(request: Request):
    """요청 정보 디버깅 엔드포인트"""
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "client_host": request.client.host if request.client else None,
        "client_port": request.client.port if request.client else None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/debug/echo")
async def echo_request(request: Request):
    """요청 데이터 에코 엔드포인트"""
    try:
        # 요청 본문 읽기
        body = await request.body()
        
        # JSON 파싱 시도
        try:
            json_data = json.loads(body.decode()) if body else None
        except json.JSONDecodeError:
            json_data = None
        
        return {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "body_raw": body.decode() if body else None,
            "body_json": json_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Echo 요청 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Echo 처리 오류: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """서버 메트릭 정보"""
    return {
        "uptime_seconds": round(time.time() - start_time, 2),
        "memory_info": {
            "note": "메모리 정보는 psutil 라이브러리가 필요하므로 기본 정보만 제공"
        },
        "server_info": {
            "python_version": sys.version,
            "platform": sys.platform,
            "port": os.getenv("PORT", "8080"),
            "hostname": os.getenv("HOSTNAME", "unknown")
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test/error")
async def test_error():
    """에러 테스트 엔드포인트"""
    logger.error("의도적인 테스트 에러 발생")
    raise HTTPException(status_code=500, detail="테스트용 에러입니다")

@app.get("/test/log")
async def test_logging():
    """로그 테스트 엔드포인트"""
    logger.debug("디버그 로그 메시지")
    logger.info("정보 로그 메시지")
    logger.warning("경고 로그 메시지")
    logger.error("에러 로그 메시지")
    
    return {
        "message": "다양한 레벨의 로그 메시지가 출력되었습니다",
        "timestamp": datetime.now().isoformat()
    }

# 글로벌 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """글로벌 예외 처리기"""
    logger.error(f"예외 발생: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "서버 내부 오류",
            "detail": str(exc),
            "type": type(exc).__name__,
            "timestamp": datetime.now().isoformat()
        }
    )

# 서버 시작 시 로그
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger.info("🚀 Cloud Run 테스트 서버 시작됨")
    logger.info(f"🐍 Python 버전: {sys.version}")
    logger.info(f"🌐 포트: {os.getenv('PORT', '8080')}")
    logger.info(f"🔧 환경: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"☁️ Google Cloud Project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'N/A')}")
    logger.info(f"🎯 Cloud Run Service: {os.getenv('K_SERVICE', 'N/A')}")

# 서버 종료 시 로그
@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트"""
    logger.info("🛑 Cloud Run 테스트 서버 종료됨")

if __name__ == "__main__":
    import uvicorn
    
    # 포트 설정 (Cloud Run은 PORT 환경변수 사용)
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"🏃 서버 시작 중... 포트: {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )