"""
API 요청 로깅 미들웨어

모든 API 요청을 자동으로 로깅하는 미들웨어
"""

import time
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import (
    LogEntry,
    LogLevel,
    LogServiceType,
    LogSource,
    LogContext,
    LogMetadata,
)
from ..logging.dependencies import get_log_service

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    API 요청을 자동으로 로깅하는 미들웨어

    모든 HTTP 요청에 대해:
    - 요청 시작 시간
    - 응답 시간
    - 상태 코드
    - 에러 정보
    - 사용자 컨텍스트
    를 자동으로 로깅합니다.
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        # 로깅에서 제외할 경로들 (헬스체크, 정적 파일, 로깅 API, 인증 상태 확인 등)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/api/logs",  # 로깅 API 자체는 로깅하지 않음 (무한 루프 방지)
            "/api/auth/profile",  # 사용자 프로필 확인 API 제외 (자동 호출)
            "/api/auth/me",  # 사용자 정보 확인 API 제외 (자동 호출)
        ]

    async def dispatch(self, request: Request, call_next):
        # 제외 경로 확인
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # 요청 시작 시간 기록
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # 요청 정보 수집
        method = request.method
        endpoint = str(request.url.path)
        query_params = str(request.url.query) if request.url.query else None
        user_agent = request.headers.get("user-agent")
        ip_address = self._get_client_ip(request)

        # 사용자 정보 추출 (Authorization 헤더에서)
        user_id = await self._extract_user_id(request)

        response = None
        error_info = None

        try:
            # 요청 처리
            response = await call_next(request)

        except Exception as e:
            # 에러 발생 시 처리
            logger.error(f"Request {request_id} failed: {str(e)}")
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
            }
            # 500 에러 응답 생성
            from fastapi.responses import JSONResponse

            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

        finally:
            # 응답 시간 계산
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 밀리초

            # 로그 생성
            await self._create_log_entry(
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                query_params=query_params,
                status_code=response.status_code if response else 500,
                response_time=response_time,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_info=error_info,
            )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 뒤에 있는 경우)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 기본 클라이언트 IP
        return request.client.host if request.client else "unknown"

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Authorization 헤더에서 사용자 ID 추출"""
        try:
            # Authorization 헤더에서 JWT 토큰 추출
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.split(" ")[1]

            # JWT 토큰 디코딩 (간단한 방법)
            import jwt
            from ..config import settings

            # JWT 시크릿이 없으면 디코딩 건너뛰기
            if not hasattr(settings, "jwt_secret") or not settings.jwt_secret:
                return None

            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            return payload.get("sub")  # 사용자 ID

        except Exception:
            # JWT 디코딩 실패는 조용히 처리
            return None

    async def _create_log_entry(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        query_params: Optional[str],
        status_code: int,
        response_time: float,
        user_id: Optional[str],
        ip_address: str,
        user_agent: Optional[str],
        error_info: Optional[Dict[str, Any]],
    ):
        """로그 엔트리 생성 및 저장"""
        try:
            # 로그 레벨 결정
            if status_code >= 500:
                level = LogLevel.ERROR
            elif status_code >= 400:
                level = LogLevel.WARN
            else:
                level = LogLevel.INFO

            # 로그 메시지 생성
            message = f"{method} {endpoint}"
            if query_params:
                message += f"?{query_params}"
            message += f" - {status_code} ({response_time:.1f}ms)"

            # 로그 컨텍스트 생성
            context = LogContext(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                infrastructure="api",
            )

            # 로그 메타데이터 생성
            metadata = LogMetadata(
                tags=["api_request", f"status_{status_code // 100}xx"],
                custom={
                    "query_params": query_params,
                    "endpoint_category": self._categorize_endpoint(endpoint),
                },
            )

            # 에러 정보 추가
            if error_info:
                metadata.error_type = error_info.get("error_type")
                metadata.custom["error_message"] = error_info.get("error_message")

            # UTC 시간으로 타임스탬프 생성 (MongoDB 표준)
            utc_time = datetime.utcnow()

            # 로그 엔트리 생성
            log_entry = LogEntry(
                timestamp=utc_time,
                level=level,
                service=LogServiceType.API,
                source=LogSource.INTERNAL,
                message=message,
                context=context,
                metadata=metadata,
                stack_trace=error_info.get("stack_trace") if error_info else None,
            )

            # 로그 서비스를 통해 저장 (의존성 주입 없이 직접 생성)
            from ..database.connection import get_database
            from ..logging.repositories.mongo_log_repository import MongoLogRepository
            from ..logging.services.log_service import LogService

            database = await get_database()
            log_repository = MongoLogRepository(database)
            await log_repository.setup_indexes()

            log_service = LogService(
                log_repository=log_repository,
                cache_service=None,  # 캐시 없이 직접 저장
                cache_ttl=300,
            )
            await log_service.setup()

            await log_service.log_internal(
                level=level,
                service=LogServiceType.API,
                message=message,
                context=context.dict(),
                metadata=metadata.dict(),
                stack_trace=log_entry.stack_trace,
                timestamp=utc_time,
            )

        except Exception as e:
            # 로깅 실패는 조용히 처리 (무한 루프 방지)
            logger.error(
                f"Failed to create log entry for request {request_id}: {str(e)}"
            )

    def _categorize_endpoint(self, endpoint: str) -> str:
        """엔드포인트 카테고리 분류"""
        if endpoint.startswith("/api/auth"):
            return "authentication"
        elif endpoint.startswith("/api/posts"):
            return "posts"
        elif endpoint.startswith("/api/users"):
            return "users"
        elif endpoint.startswith("/api/files"):
            return "files"
        elif endpoint.startswith("/api/logs"):
            return "logging"
        elif endpoint.startswith("/api/admin"):
            return "admin"
        else:
            return "other"
