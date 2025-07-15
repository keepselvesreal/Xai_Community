"""
통합 모니터링 서비스

4개 인프라(Cloud Run, Vercel, MongoDB Atlas, Upstash Redis)의 
모니터링을 통합하여 제공하는 서비스
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio

from ...config import get_settings
from ...models.monitoring.monitoring_models import (
    UnifiedMonitoringResponse, 
    InfrastructureStatus, 
    InfrastructureType,
    ServiceStatus,
    HealthCheckResponse,
    MonitoringError
)
from .cloud_run_monitor import CloudRunMonitoringService
from .vercel_monitor import VercelMonitoringService
from .atlas_monitor import AtlasMonitoringService
from .upstash_monitor import UpstashMonitoringService


logger = logging.getLogger(__name__)


class UnifiedMonitoringService:
    """통합 모니터링 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self._cloud_run_service = CloudRunMonitoringService()
        self._vercel_service = VercelMonitoringService()
        self._atlas_service = AtlasMonitoringService()
        self._upstash_service = UpstashMonitoringService()
    
    async def get_all_infrastructure_status(self) -> UnifiedMonitoringResponse:
        """모든 인프라의 상태를 통합하여 반환"""
        try:
            logger.info("통합 인프라 모니터링 시작")
            
            # 모든 인프라 모니터링을 병렬로 실행
            tasks = []
            
            # 설정된 인프라만 모니터링
            if self._cloud_run_service.is_configured():
                tasks.append(self._monitor_cloud_run())
            
            if self._vercel_service.is_configured():
                tasks.append(self._monitor_vercel())
            
            if self._atlas_service.is_configured():
                tasks.append(self._monitor_atlas())
            
            if self._upstash_service.is_configured():
                tasks.append(self._monitor_upstash())
            
            # 모든 태스크 실행
            infrastructure_statuses = []
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, InfrastructureStatus):
                        infrastructure_statuses.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"인프라 모니터링 중 오류: {result}")
                        # 오류가 발생한 경우에도 UNKNOWN 상태로 추가
                        error_status = InfrastructureStatus(
                            infrastructure_type=InfrastructureType.CLOUD_RUN,  # 기본값
                            service_name="unknown",
                            status=ServiceStatus.UNKNOWN,
                            metrics=None
                        )
                        infrastructure_statuses.append(error_status)
            
            # 전체 상태 계산
            overall_status = self._calculate_overall_status(infrastructure_statuses)
            healthy_count = sum(1 for status in infrastructure_statuses if status.status == ServiceStatus.HEALTHY)
            unhealthy_count = len(infrastructure_statuses) - healthy_count
            
            # 요약 정보 생성
            summary = self._generate_summary(infrastructure_statuses)
            
            response = UnifiedMonitoringResponse(
                overall_status=overall_status,
                infrastructure_count=len(infrastructure_statuses),
                healthy_count=healthy_count,
                unhealthy_count=unhealthy_count,
                infrastructures=infrastructure_statuses,
                summary=summary
            )
            
            logger.info(f"통합 모니터링 완료: {len(infrastructure_statuses)}개 인프라, 전체 상태: {overall_status.value}")
            return response
            
        except Exception as e:
            logger.error(f"통합 모니터링 실패: {e}")
            
            # 실패시 기본 응답 반환
            return UnifiedMonitoringResponse(
                overall_status=ServiceStatus.UNKNOWN,
                infrastructure_count=0,
                healthy_count=0,
                unhealthy_count=0,
                infrastructures=[],
                summary={"error": str(e)}
            )
    
    async def _monitor_cloud_run(self) -> InfrastructureStatus:
        """Cloud Run 모니터링"""
        try:
            metrics = await self._cloud_run_service.get_metrics()
            
            return InfrastructureStatus(
                infrastructure_type=InfrastructureType.CLOUD_RUN,
                service_name=metrics.service_name,
                status=metrics.status,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Cloud Run 모니터링 실패: {e}")
            raise
    
    async def _monitor_vercel(self) -> InfrastructureStatus:
        """Vercel 모니터링"""
        try:
            metrics = await self._vercel_service.get_metrics()
            
            return InfrastructureStatus(
                infrastructure_type=InfrastructureType.VERCEL,
                service_name=f"project-{metrics.project_id}",
                status=metrics.status,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Vercel 모니터링 실패: {e}")
            raise
    
    async def _monitor_atlas(self) -> InfrastructureStatus:
        """MongoDB Atlas 모니터링"""
        try:
            metrics = await self._atlas_service.get_metrics()
            
            return InfrastructureStatus(
                infrastructure_type=InfrastructureType.MONGODB_ATLAS,
                service_name=metrics.cluster_name,
                status=metrics.status,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"MongoDB Atlas 모니터링 실패: {e}")
            raise
    
    async def _monitor_upstash(self) -> InfrastructureStatus:
        """Upstash Redis 모니터링"""
        try:
            metrics = await self._upstash_service.get_metrics()
            
            return InfrastructureStatus(
                infrastructure_type=InfrastructureType.UPSTASH_REDIS,
                service_name=f"redis-{metrics.database_id}",
                status=metrics.status,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Upstash Redis 모니터링 실패: {e}")
            raise
    
    def _calculate_overall_status(self, statuses: List[InfrastructureStatus]) -> ServiceStatus:
        """전체 상태 계산"""
        if not statuses:
            return ServiceStatus.UNKNOWN
        
        # 상태별 개수 계산
        status_counts = {}
        for status in statuses:
            current_status = status.status
            status_counts[current_status] = status_counts.get(current_status, 0) + 1
        
        total_count = len(statuses)
        healthy_count = status_counts.get(ServiceStatus.HEALTHY, 0)
        unhealthy_count = status_counts.get(ServiceStatus.UNHEALTHY, 0)
        degraded_count = status_counts.get(ServiceStatus.DEGRADED, 0)
        
        # 전체 상태 결정 로직
        if unhealthy_count > 0:
            # 하나라도 UNHEALTHY면 DEGRADED 또는 UNHEALTHY
            if unhealthy_count >= total_count / 2:  # 절반 이상이 문제
                return ServiceStatus.UNHEALTHY
            else:
                return ServiceStatus.DEGRADED
        elif degraded_count > 0:
            # UNHEALTHY는 없지만 DEGRADED가 있으면 DEGRADED
            return ServiceStatus.DEGRADED
        elif healthy_count == total_count:
            # 모두 HEALTHY
            return ServiceStatus.HEALTHY
        else:
            # 알 수 없는 상태
            return ServiceStatus.UNKNOWN
    
    def _generate_summary(self, statuses: List[InfrastructureStatus]) -> Dict[str, Any]:
        """요약 정보 생성"""
        summary = {
            "services": {},
            "metrics_summary": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            # 서비스별 요약
            for status in statuses:
                service_key = status.infrastructure_type.value
                summary["services"][service_key] = {
                    "name": status.service_name,
                    "status": status.status.value,
                    "last_check": status.last_check.isoformat()
                }
                
                # 메트릭 요약 (기본적인 것들만)
                if status.metrics:
                    metrics = status.metrics
                    service_metrics = {}
                    
                    # 응답시간
                    if hasattr(metrics, 'response_time_ms') and metrics.response_time_ms:
                        service_metrics["response_time_ms"] = metrics.response_time_ms
                    
                    # Cloud Run 특화 메트릭
                    if status.infrastructure_type == InfrastructureType.CLOUD_RUN:
                        if hasattr(metrics, 'cpu_utilization') and metrics.cpu_utilization:
                            service_metrics["cpu_utilization"] = metrics.cpu_utilization
                        if hasattr(metrics, 'memory_utilization') and metrics.memory_utilization:
                            service_metrics["memory_utilization"] = metrics.memory_utilization
                        if hasattr(metrics, 'instance_count') and metrics.instance_count:
                            service_metrics["instance_count"] = metrics.instance_count
                    
                    # Vercel 특화 메트릭
                    elif status.infrastructure_type == InfrastructureType.VERCEL:
                        if hasattr(metrics, 'deployment_status') and metrics.deployment_status:
                            service_metrics["deployment_status"] = metrics.deployment_status
                        if hasattr(metrics, 'core_web_vitals_score') and metrics.core_web_vitals_score:
                            service_metrics["core_web_vitals_score"] = metrics.core_web_vitals_score
                    
                    # Atlas 특화 메트릭
                    elif status.infrastructure_type == InfrastructureType.MONGODB_ATLAS:
                        if hasattr(metrics, 'connections_current') and metrics.connections_current:
                            service_metrics["connections_current"] = metrics.connections_current
                        if hasattr(metrics, 'cpu_usage_percent') and metrics.cpu_usage_percent:
                            service_metrics["cpu_usage_percent"] = metrics.cpu_usage_percent
                        if hasattr(metrics, 'operations_per_second') and metrics.operations_per_second:
                            service_metrics["operations_per_second"] = metrics.operations_per_second
                    
                    # Upstash 특화 메트릭
                    elif status.infrastructure_type == InfrastructureType.UPSTASH_REDIS:
                        if hasattr(metrics, 'hit_rate') and metrics.hit_rate:
                            service_metrics["hit_rate"] = metrics.hit_rate
                        if hasattr(metrics, 'memory_usage_percent') and metrics.memory_usage_percent:
                            service_metrics["memory_usage_percent"] = metrics.memory_usage_percent
                        if hasattr(metrics, 'operations_per_second') and metrics.operations_per_second:
                            service_metrics["operations_per_second"] = metrics.operations_per_second
                    
                    if service_metrics:
                        summary["metrics_summary"][service_key] = service_metrics
            
            # 전체 통계
            summary["statistics"] = {
                "total_services": len(statuses),
                "healthy_services": sum(1 for s in statuses if s.status == ServiceStatus.HEALTHY),
                "unhealthy_services": sum(1 for s in statuses if s.status == ServiceStatus.UNHEALTHY),
                "degraded_services": sum(1 for s in statuses if s.status == ServiceStatus.DEGRADED),
                "unknown_services": sum(1 for s in statuses if s.status == ServiceStatus.UNKNOWN)
            }
            
        except Exception as e:
            logger.error(f"요약 정보 생성 실패: {e}")
            summary["error"] = str(e)
        
        return summary
    
    async def health_check(self) -> HealthCheckResponse:
        """통합 헬스체크"""
        try:
            # 빠른 헬스체크 (각 서비스의 기본 연결만 확인)
            checks = {}
            
            # 설정된 서비스만 체크
            if self._cloud_run_service.is_configured():
                cloud_run_health = await self._cloud_run_service.health_check()
                checks["cloud_run"] = cloud_run_health
            
            if self._vercel_service.is_configured():
                vercel_health = await self._vercel_service.health_check()
                checks["vercel"] = vercel_health
            
            if self._atlas_service.is_configured():
                atlas_health = await self._atlas_service.health_check()
                checks["atlas"] = atlas_health
            
            if self._upstash_service.is_configured():
                upstash_health = await self._upstash_service.health_check()
                checks["upstash"] = upstash_health
            
            # 전체 상태 판단
            all_healthy = all(
                check.get("status") == ServiceStatus.HEALTHY.value 
                for check in checks.values()
            )
            
            overall_status = ServiceStatus.HEALTHY if all_healthy else ServiceStatus.DEGRADED
            
            return HealthCheckResponse(
                service="unified_monitoring",
                status=overall_status,
                checks=checks
            )
            
        except Exception as e:
            logger.error(f"통합 헬스체크 실패: {e}")
            return HealthCheckResponse(
                service="unified_monitoring",
                status=ServiceStatus.UNKNOWN,
                checks={"error": str(e)}
            )
    
    async def get_service_metrics(self, infrastructure_type: InfrastructureType):
        """특정 인프라의 메트릭만 조회"""
        try:
            if infrastructure_type == InfrastructureType.CLOUD_RUN:
                if self._cloud_run_service.is_configured():
                    return await self._cloud_run_service.get_metrics()
            elif infrastructure_type == InfrastructureType.VERCEL:
                if self._vercel_service.is_configured():
                    return await self._vercel_service.get_metrics()
            elif infrastructure_type == InfrastructureType.MONGODB_ATLAS:
                if self._atlas_service.is_configured():
                    return await self._atlas_service.get_metrics()
            elif infrastructure_type == InfrastructureType.UPSTASH_REDIS:
                if self._upstash_service.is_configured():
                    return await self._upstash_service.get_metrics()
            
            return None
            
        except Exception as e:
            logger.error(f"{infrastructure_type.value} 메트릭 조회 실패: {e}")
            return None
    
    def get_configured_services(self) -> List[InfrastructureType]:
        """설정된 서비스 목록 반환"""
        configured = []
        
        if self._cloud_run_service.is_configured():
            configured.append(InfrastructureType.CLOUD_RUN)
        
        if self._vercel_service.is_configured():
            configured.append(InfrastructureType.VERCEL)
        
        if self._atlas_service.is_configured():
            configured.append(InfrastructureType.MONGODB_ATLAS)
        
        if self._upstash_service.is_configured():
            configured.append(InfrastructureType.UPSTASH_REDIS)
        
        return configured