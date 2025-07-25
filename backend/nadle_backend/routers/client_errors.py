"""
클라이언트 에러 수집 라우터

작업 시간: 2025-07-23 14:15:00 KST  
작업 버전: v1.0.0
주요 컴포넌트들:
- ClientErrorRequest: 클라이언트 에러 요청 모델
- client_error_handler: 클라이언트 에러 처리 엔드포인트

주요 함수들:
- report_client_error: 클라이언트에서 발생한 에러를 서버에 보고 (line 45-120)

관련 파일들:
- nadle_backend/core/logging/: 로깅 시스템과 통합
- frontend/: 프론트엔드에서 이 API로 에러 전송
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse

from ..core.logging import LogLevel, LogServiceType, LogSource, LogContext, LogMetadata
from ..dependencies.auth import get_optional_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/client-errors", tags=["client-errors"])


class ClientErrorRequest(BaseModel):
    """클라이언트 에러 리포트 요청 모델"""
    
    error_type: str = Field(..., description="에러 타입 (TypeError, NetworkError, TimeoutError 등)")
    error_message: str = Field(..., description="에러 메시지")
    stack_trace: Optional[str] = Field(None, description="스택 트레이스 (있는 경우)")
    
    # 브라우저/환경 정보
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    url: Optional[str] = Field(None, description="에러 발생 URL")
    browser: Optional[str] = Field(None, description="브라우저 정보")
    browser_version: Optional[str] = Field(None, description="브라우저 버전")
    os: Optional[str] = Field(None, description="운영체제")
    
    # 네트워크 에러 관련
    network_status: Optional[str] = Field(None, description="네트워크 상태 (online/offline)")
    request_url: Optional[str] = Field(None, description="실패한 API 요청 URL")
    response_status: Optional[int] = Field(None, description="HTTP 응답 코드")
    timeout_duration: Optional[int] = Field(None, description="타임아웃 시간 (ms)")
    
    # 컴포넌트/페이지 정보
    component_name: Optional[str] = Field(None, description="에러 발생 컴포넌트")
    page_path: Optional[str] = Field(None, description="페이지 경로")
    action: Optional[str] = Field(None, description="수행 중이던 액션")
    
    # 추가 컨텍스트
    additional_info: Optional[Dict[str, Any]] = Field(None, description="추가 정보")
    timestamp: Optional[str] = Field(None, description="클라이언트 측 타임스탬프")


@router.post("/report")
async def report_client_error(
    error_data: ClientErrorRequest,
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    클라이언트에서 발생한 에러를 서버에 보고
    
    JavaScript 에러, 네트워크 타임아웃, 연결 실패 등
    클라이언트 측에서 발생하는 모든 에러를 수집합니다.
    """
    try:
        # 사용자 ID 추출
        user_id = None
        if current_user:
            user_id = current_user.get("user_id") or current_user.get("id")
        
        # 클라이언트 IP 추출
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # 로그 컨텍스트 생성
        context = LogContext(
            user_id=user_id,
            endpoint="/api/client-errors/report",
            method="POST",
            ip_address=client_ip,
            user_agent=error_data.user_agent or request.headers.get("user-agent"),
            infrastructure="client_error_reporter"
        )
        
        # 에러 타입별 분류
        error_category = _categorize_client_error(error_data.error_type)
        
        # 로그 메타데이터 생성
        metadata = LogMetadata(
            error_type=error_data.error_type,
            tags=["client_error", error_category, "frontend"],
            custom={
                "client_url": error_data.url,
                "browser": error_data.browser,
                "browser_version": error_data.browser_version,
                "os": error_data.os,
                "network_status": error_data.network_status,
                "request_url": error_data.request_url,
                "response_status": error_data.response_status,
                "timeout_duration": error_data.timeout_duration,
                "component_name": error_data.component_name,
                "page_path": error_data.page_path,
                "action": error_data.action,
                "client_timestamp": error_data.timestamp,
                "additional_info": error_data.additional_info
            }
        )
        
        # 로그 메시지 생성
        message = f"[CLIENT_ERROR] {error_data.error_type}: {error_data.error_message}"
        if error_data.component_name:
            message += f" (component: {error_data.component_name})"
        if error_data.action:
            message += f" (action: {error_data.action})"
        
        # LogService에 기록
        from ..database.connection import get_database
        from ..logging.repositories.mongo_log_repository import MongoLogRepository
        from ..logging.services.log_service import LogService
        
        database = await get_database()
        log_repository = MongoLogRepository(database)
        log_service = LogService(log_repository=log_repository)
        
        # 에러의 심각도에 따라 로그 레벨 결정
        log_level = _determine_log_level(error_data)
        
        await log_service.log_internal(
            level=log_level,
            service=LogServiceType.FRONTEND,
            message=message,
            context=context,
            metadata=metadata,
            stack_trace=error_data.stack_trace,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"✅ Client error logged: {error_data.error_type} from {client_ip}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "에러가 성공적으로 기록되었습니다.",
                "error_id": f"client_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to log client error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "에러 기록에 실패했습니다."
            }
        )


def _categorize_client_error(error_type: str) -> str:
    """클라이언트 에러를 카테고리별로 분류"""
    error_type_lower = error_type.lower()
    
    if any(keyword in error_type_lower for keyword in ["network", "fetch", "xhr", "ajax"]):
        return "network"
    elif any(keyword in error_type_lower for keyword in ["timeout", "abort"]):
        return "timeout"  
    elif any(keyword in error_type_lower for keyword in ["syntax", "reference", "type"]):
        return "javascript"
    elif any(keyword in error_type_lower for keyword in ["chunk", "loading", "import"]):
        return "loading"
    elif any(keyword in error_type_lower for keyword in ["permission", "security", "cors"]):
        return "security"
    else:
        return "other"


def _determine_log_level(error_data: ClientErrorRequest) -> LogLevel:
    """에러 데이터를 기반으로 로그 레벨 결정"""
    error_type_lower = error_data.error_type.lower()
    
    # 심각한 에러들 (ERROR 레벨)
    if any(keyword in error_type_lower for keyword in [
        "chunk", "syntax", "reference", "security", "cors"
    ]):
        return LogLevel.ERROR
    
    # HTTP 에러 코드 기반 판단
    if error_data.response_status:
        if error_data.response_status >= 500:
            return LogLevel.ERROR
        elif error_data.response_status >= 400:
            return LogLevel.WARN
    
    # 네트워크/타임아웃 에러 (WARN 레벨)
    if any(keyword in error_type_lower for keyword in [
        "network", "timeout", "fetch", "xhr", "ajax"
    ]):
        return LogLevel.WARN
    
    # 기타 에러 (INFO 레벨)
    return LogLevel.INFO


@router.get("/health")
async def client_error_health():
    """클라이언트 에러 수집 서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "client-error-collector",
        "message": "Client error collection service is operational"
    }