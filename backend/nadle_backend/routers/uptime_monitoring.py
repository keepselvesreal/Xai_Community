"""
업타임 모니터링 API 라우터

외부 업타임 모니터링 및 헬스체크 엔드포인트
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from nadle_backend.services.uptime_monitoring import (
    HealthCheckService,
    UptimeMonitoringService,
    get_health_check_service,
    get_uptime_monitoring_service
)
from nadle_backend.services.notification_service import (
    NotificationService,
    get_notification_service
)

router = APIRouter(tags=["uptime-monitoring"])


class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str
    timestamp: str
    uptime: float
    service: str


class ComprehensiveHealthResponse(BaseModel):
    """종합 헬스체크 응답 모델"""
    status: str
    overall_health: bool
    checks: Dict[str, Any]
    total_response_time: float
    timestamp: str
    version: str


class MonitorCreateRequest(BaseModel):
    """모니터 생성 요청 모델"""
    name: str
    url: str
    interval: int = 300


class NotificationTestRequest(BaseModel):
    """알림 테스트 요청 모델"""
    message: str
    title: Optional[str] = None
    notification_type: str = "info"  # info, warning, error


@router.get(
    "/status",
    response_model=HealthResponse,
    summary="시스템 상태 체크",
    description="외부 업타임 모니터링 서비스용 간단한 상태 체크 엔드포인트"
)
async def simple_health_check(
    health_service: HealthCheckService = Depends(get_health_check_service)
) -> HealthResponse:
    """
    간단한 헬스체크 엔드포인트
    
    외부 모니터링 서비스(UptimeRobot 등)에서 호출할 수 있는 
    간단하고 빠른 헬스체크 엔드포인트입니다.
    """
    try:
        result = await health_service.simple_health_check()
        return HealthResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )


@router.get(
    "/health/detailed",
    response_model=ComprehensiveHealthResponse,
    summary="상세 헬스체크",
    description="데이터베이스, Redis, 외부 API 등 모든 의존성을 포함한 상세 헬스체크"
)
async def comprehensive_health_check(
    health_service: HealthCheckService = Depends(get_health_check_service)
) -> ComprehensiveHealthResponse:
    """
    종합 헬스체크 엔드포인트
    
    시스템의 모든 의존성(데이터베이스, Redis, 외부 API)을 검사하여
    전체적인 시스템 상태를 반환합니다.
    """
    try:
        result = await health_service.comprehensive_health_check()
        return ComprehensiveHealthResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Comprehensive health check failed: {str(e)}"
        )


@router.get(
    "/monitoring/monitors",
    summary="모니터 목록 조회",
    description="UptimeRobot에 등록된 모든 모니터 목록을 조회합니다"
)
async def get_monitors(
    uptime_service: UptimeMonitoringService = Depends(get_uptime_monitoring_service)
):
    """UptimeRobot 모니터 목록 조회"""
    try:
        monitors = uptime_service.get_monitors()
        return {
            "status": "success",
            "count": len(monitors),
            "monitors": [
                {
                    "id": monitor.id,
                    "name": monitor.name,
                    "url": monitor.url,
                    "status": monitor.status.value,
                    "created_at": monitor.created_at.isoformat()
                }
                for monitor in monitors
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get monitors: {str(e)}"
        )


@router.post(
    "/monitoring/monitors",
    summary="새 모니터 생성",
    description="UptimeRobot에 새로운 모니터를 생성합니다"
)
async def create_monitor(
    request: MonitorCreateRequest,
    uptime_service: UptimeMonitoringService = Depends(get_uptime_monitoring_service)
):
    """UptimeRobot에 새 모니터 생성"""
    try:
        monitor = uptime_service.create_monitor(
            name=request.name,
            url=request.url,
            interval=request.interval
        )
        
        return {
            "status": "success",
            "message": "Monitor created successfully",
            "monitor": {
                "id": monitor.id,
                "name": monitor.name,
                "url": monitor.url,
                "status": monitor.status.value,
                "created_at": monitor.created_at.isoformat(),
                "interval": monitor.interval
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to create monitor: {str(e)}"
        )


@router.delete(
    "/monitoring/monitors/{monitor_id}",
    summary="모니터 삭제",
    description="UptimeRobot에서 지정된 모니터를 삭제합니다"
)
async def delete_monitor(
    monitor_id: int,
    uptime_service: UptimeMonitoringService = Depends(get_uptime_monitoring_service)
):
    """UptimeRobot 모니터 삭제"""
    try:
        success = uptime_service.delete_monitor(monitor_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Monitor {monitor_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitor {monitor_id} not found or already deleted"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to delete monitor: {str(e)}"
        )


@router.get(
    "/monitoring/monitors/{monitor_id}/logs",
    summary="모니터 로그 조회",
    description="특정 모니터의 업타임/다운타임 로그를 조회합니다"
)
async def get_monitor_logs(
    monitor_id: int,
    days: int = 7,
    uptime_service: UptimeMonitoringService = Depends(get_uptime_monitoring_service)
):
    """모니터 로그 조회"""
    try:
        logs = uptime_service.get_monitor_logs(monitor_id, days)
        
        return {
            "status": "success",
            "monitor_id": monitor_id,
            "days": days,
            "log_count": len(logs),
            "logs": logs
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get monitor logs: {str(e)}"
        )


@router.post(
    "/monitoring/notifications/test",
    summary="알림 테스트",
    description="Discord 웹훅과 이메일 알림 시스템을 테스트합니다"
)
async def test_notifications(
    request: NotificationTestRequest,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """알림 시스템 테스트"""
    try:
        # 알림 타입에 따른 색상 설정
        color_map = {
            "info": 0x0099FF,    # 파란색
            "warning": 0xFFA500, # 주황색
            "error": 0xFF0000    # 빨간색
        }
        
        color = color_map.get(request.notification_type, 0x0099FF)
        
        # Discord와 이메일 알림 동시 전송
        results = {}
        
        # Discord 알림
        discord_result = await notification_service.send_discord_notification(
            message=request.message,
            title=request.title or "알림 테스트",
            color=color,
            username="Uptime Monitor Test"
        )
        results['discord'] = discord_result
        
        # 이메일 알림 (SMTP 사용자에게)
        if notification_service.smtp_user:
            email_result = await notification_service.send_email_notification(
                to_email=notification_service.smtp_user,
                subject=request.title or "알림 테스트",
                message=request.message
            )
            results['email'] = email_result
        else:
            results['email'] = False
            results['email_note'] = "SMTP 설정이 되지 않음"
        
        return {
            "status": "success",
            "message": "Notification test completed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Notification test failed: {str(e)}"
        )


@router.post(
    "/monitoring/alerts/uptime",
    summary="업타임 알림 전송",
    description="업타임 모니터링 알림을 수동으로 전송합니다 (테스트용)"
)
async def send_uptime_alert(
    monitor_name: str,
    status: str,
    url: str,
    duration: Optional[int] = None,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """업타임 알림 수동 전송 (테스트용)"""
    try:
        results = await notification_service.send_uptime_alert(
            monitor_name=monitor_name,
            status=status,
            url=url,
            duration=duration
        )
        
        return {
            "status": "success",
            "message": "Uptime alert sent",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send uptime alert: {str(e)}"
        )


@router.get(
    "/monitoring/info",
    summary="모니터링 시스템 정보",
    description="모니터링 시스템 자체의 상태와 설정 정보를 반환합니다"
)
async def monitoring_system_status():
    """모니터링 시스템 상태 확인"""
    try:
        from nadle_backend.config import settings
        
        # 설정 상태 확인
        from datetime import datetime
        
        status_info = {
            "monitoring_system": "operational",
            "timestamp": datetime.now().isoformat(),
            "configurations": {
                "uptimerobot_configured": bool(getattr(settings, 'uptimerobot_api_key', None)),
                "discord_webhook_configured": bool(getattr(settings, 'discord_webhook_url', None)),
                "smtp_configured": bool(getattr(settings, 'smtp_host', None) and 
                                     getattr(settings, 'smtp_user', None)),
                "redis_configured": bool(getattr(settings, 'redis_url', None)),
                "sentry_configured": bool(getattr(settings, 'sentry_dsn', None))
            },
            "endpoints": {
                "simple_status": "/status",
                "detailed_health": "/health/detailed",
                "monitors_api": "/monitoring/monitors",
                "notification_test": "/monitoring/notifications/test"
            }
        }
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get monitoring system status: {str(e)}"
        )