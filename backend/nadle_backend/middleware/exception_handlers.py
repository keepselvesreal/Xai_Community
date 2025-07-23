"""
FastAPI Exception Handlers

작업 시간: 2025-07-23 14:00:00 KST
작업 버전: v1.0.0
주요 컴포넌트들:
- GlobalExceptionHandler: 전역 예외 처리 클래스
- setup_exception_handlers: FastAPI 앱에 예외 핸들러 등록 함수

주요 함수들:
- validation_exception_handler: 요청 검증 실패 (422) 처리 (line 45-80)
- http_exception_handler: HTTP 예외 (4xx, 5xx) 처리 (line 82-115)  
- starlette_http_exception_handler: Starlette HTTP 예외 처리 (line 117-150)
- generic_exception_handler: 일반 Python 예외 처리 (line 152-190)
- setup_exception_handlers: 모든 핸들러를 FastAPI 앱에 등록 (line 192-215)

관련 파일들:
- nadle_backend/middleware/sentry_middleware.py: 기존 Sentry 미들웨어와 연동
- nadle_backend/core/logging/: 로깅 시스템과 통합
- main.py: FastAPI 앱 초기화 시 등록 필요
"""

import logging
import traceback
from datetime import datetime
from typing import Union, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.logging import LogLevel, LogServiceType, LogSource, LogContext, LogMetadata

logger = logging.getLogger(__name__)


class GlobalExceptionHandler:
    """
    전역 예외 처리 클래스
    
    FastAPI에서 발생하는 모든 예외를 캐치하고 LogService에 기록합니다.
    기존 SentryMiddleware와 중복되지 않도록 설계되었습니다.
    """

    @staticmethod
    async def log_exception(
        request: Request,
        exception: Exception,
        status_code: int,
        error_type: str,
        message: str
    ):
        """예외를 LogService에 기록"""
        try:
            # 로그 컨텍스트 생성
            context = LogContext(
                endpoint=str(request.url.path),
                method=request.method,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                infrastructure="exception_handler"
            )
            
            # 로그 메타데이터 생성  
            metadata = LogMetadata(
                error_type=error_type,
                tags=["exception_handler", f"status_{status_code}", error_type.lower()],
                custom={
                    "exception_class": exception.__class__.__name__,
                    "status_code": status_code,
                    "request_url": str(request.url),
                    "query_params": str(request.url.query) if request.url.query else None
                }
            )
            
            # LogService에 기록
            from ..database.connection import get_database
            from ..logging.repositories.mongo_log_repository import MongoLogRepository
            from ..logging.services.log_service import LogService
            
            database = await get_database()
            log_repository = MongoLogRepository(database)
            log_service = LogService(log_repository=log_repository)
            
            await log_service.log_internal(
                level=LogLevel.ERROR if status_code >= 500 else LogLevel.WARN,
                service=LogServiceType.API,
                message=f"[EXCEPTION_HANDLER] {message}",
                context=context,
                metadata=metadata,
                stack_trace=traceback.format_exc(),
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"✅ Exception logged via ExceptionHandler: {error_type}")
            
        except Exception as log_error:
            logger.warning(f"⚠️ Exception handler logging failed: {log_error}")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    요청 검증 실패 (422) 예외 처리
    
    Pydantic validation error, 잘못된 request body 등을 처리합니다.
    """
    try:
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        message = f"Request validation failed: {len(error_details)} errors"
        
        # LogService에 기록
        await GlobalExceptionHandler.log_exception(
            request=request,
            exception=exc,
            status_code=422,
            error_type="RequestValidationError",
            message=message
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "요청 데이터 검증에 실패했습니다.",
                "details": error_details,
                "status_code": 422
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Validation exception handler failed: {e}")
        return JSONResponse(
            status_code=422,
            content={"error": "Validation Error", "message": "요청 데이터가 올바르지 않습니다."}
        )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    FastAPI HTTPException 처리 (4xx, 5xx)
    
    raise HTTPException으로 발생한 예외들을 처리합니다.
    """
    try:
        message = f"HTTP {exc.status_code}: {exc.detail}"
        
        # LogService에 기록 (4xx는 WARN, 5xx는 ERROR)
        await GlobalExceptionHandler.log_exception(
            request=request,
            exception=exc,
            status_code=exc.status_code,
            error_type="HTTPException",
            message=message
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Exception",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
        
    except Exception as e:
        logger.error(f"❌ HTTP exception handler failed: {e}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP Exception", "message": str(exc.detail)}
        )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Starlette HTTPException 처리
    
    Starlette 레벨에서 발생하는 HTTP 예외들을 처리합니다.
    """
    try:
        message = f"Starlette HTTP {exc.status_code}: {exc.detail}"
        
        # LogService에 기록
        await GlobalExceptionHandler.log_exception(
            request=request,
            exception=exc,
            status_code=exc.status_code,
            error_type="StarletteHTTPException",
            message=message
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Exception",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Starlette HTTP exception handler failed: {e}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP Exception", "message": "An error occurred"}
        )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    일반 Python 예외 처리 (최후의 방어선)
    
    다른 핸들러에서 잡히지 않은 모든 예외를 처리합니다.
    SentryMiddleware와 중복되지 않도록 다른 태그를 사용합니다.
    """
    try:
        error_type = exc.__class__.__name__
        message = f"Unhandled exception: {error_type} - {str(exc)}"
        
        # LogService에 기록
        await GlobalExceptionHandler.log_exception(
            request=request,
            exception=exc,
            status_code=500,
            error_type=error_type,
            message=message
        )
        
        logger.error(f"❌ Unhandled exception: {error_type} - {str(exc)}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "서버에서 예상치 못한 오류가 발생했습니다.",
                "status_code": 500,
                "error_type": error_type
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Generic exception handler failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "message": "An unexpected error occurred"}
        )


def setup_exception_handlers(app: FastAPI):
    """
    FastAPI 앱에 모든 예외 핸들러 등록
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    try:
        # 1. Request Validation Error (422)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        
        # 2. FastAPI HTTPException
        app.add_exception_handler(HTTPException, http_exception_handler)
        
        # 3. Starlette HTTPException  
        app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
        
        # 4. 일반 Python Exception (최후의 방어선)
        app.add_exception_handler(Exception, generic_exception_handler)
        
        logger.info("✅ All exception handlers registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register exception handlers: {e}")
        raise