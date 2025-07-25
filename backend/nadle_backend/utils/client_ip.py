"""
작업 시간: 2025-07-25 12:20:00 KST
작업 버전: v1.0.0
주요 컴포넌트들: get_client_ip
주요 함수들:
- get_client_ip: FastAPI Request에서 실제 클라이언트 IP 추출 (L15-60)
- _extract_ip_from_forwarded: X-Forwarded-For 헤더에서 IP 추출 (L62-75)
관련 파일들:
- routers/auth.py: 이 함수를 사용하여 클라이언트 IP 추출
- config.py: 환경별 설정
"""

import logging
from fastapi import Request
from typing import Optional

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    FastAPI Request에서 실제 클라이언트 IP를 추출합니다.
    
    Cloud Run, 로드밸런서, 프록시 환경을 고려하여 올바른 IP를 반환합니다.
    
    우선순위:
    1. X-Forwarded-For (가장 앞의 IP - 실제 클라이언트)
    2. X-Real-IP (Nginx 등에서 설정)
    3. X-Client-IP (일부 프록시에서 사용)
    4. CF-Connecting-IP (Cloudflare)
    5. request.client.host (직접 연결)
    6. "unknown" (모든 방법 실패 시)
    
    Args:
        request: FastAPI Request 객체
        
    Returns:
        클라이언트 IP 주소 문자열
    """
    
    # 1. X-Forwarded-For 헤더 확인 (가장 일반적)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 첫 번째 IP가 실제 클라이언트 IP (프록시 체인에서 가장 앞)
        client_ip = _extract_ip_from_forwarded(forwarded_for)
        if client_ip:
            logger.debug(f"🌐 Client IP from X-Forwarded-For: {client_ip}")
            return client_ip
    
    # 2. X-Real-IP 헤더 (Nginx 등에서 설정)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        logger.debug(f"🌐 Client IP from X-Real-IP: {real_ip}")
        return real_ip.strip()
    
    # 3. X-Client-IP 헤더 (일부 프록시에서 사용)
    client_ip_header = request.headers.get("X-Client-IP")
    if client_ip_header and client_ip_header.strip():
        logger.debug(f"🌐 Client IP from X-Client-IP: {client_ip_header}")
        return client_ip_header.strip()
    
    # 4. CF-Connecting-IP (Cloudflare)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and cf_ip.strip():
        logger.debug(f"🌐 Client IP from CF-Connecting-IP: {cf_ip}")
        return cf_ip.strip()
    
    # 5. 직접 연결된 클라이언트 (개발환경 등)
    if request.client and request.client.host:
        logger.debug(f"🌐 Client IP from request.client.host: {request.client.host}")
        return request.client.host
    
    # 6. 모든 방법 실패 시
    logger.warning("⚠️ Could not determine client IP, using 'unknown'")
    return "unknown"


def _extract_ip_from_forwarded(forwarded_for: str) -> Optional[str]:
    """
    X-Forwarded-For 헤더에서 실제 클라이언트 IP를 추출합니다.
    
    X-Forwarded-For 형식: "client_ip, proxy1_ip, proxy2_ip"
    첫 번째 IP가 실제 클라이언트 IP입니다.
    
    Args:
        forwarded_for: X-Forwarded-For 헤더 값
        
    Returns:
        클라이언트 IP 또는 None
    """
    if not forwarded_for:
        return None
    
    # 쉼표로 분리하고 첫 번째 IP 사용
    ips = [ip.strip() for ip in forwarded_for.split(",")]
    first_ip = ips[0] if ips else None
    
    # 기본적인 IP 형식 검증 (단순)
    if first_ip and first_ip != "unknown":
        return first_ip
    
    return None


def log_request_headers(request: Request, client_ip: str) -> None:
    """
    디버깅용: 요청 헤더와 클라이언트 IP 정보를 로깅합니다.
    
    Args:
        request: FastAPI Request 객체
        client_ip: 추출된 클라이언트 IP
    """
    logger.info(f"📍 Request IP Info:")
    logger.info(f"   Extracted Client IP: {client_ip}")
    logger.info(f"   X-Forwarded-For: {request.headers.get('X-Forwarded-For', 'None')}")
    logger.info(f"   X-Real-IP: {request.headers.get('X-Real-IP', 'None')}")
    logger.info(f"   X-Client-IP: {request.headers.get('X-Client-IP', 'None')}")
    logger.info(f"   CF-Connecting-IP: {request.headers.get('CF-Connecting-IP', 'None')}")
    logger.info(f"   request.client.host: {request.client.host if request.client else 'None'}")