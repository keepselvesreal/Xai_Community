"""
Google Cloud Run 모니터링 서비스

Cloud Monitoring API를 사용하여 Cloud Run 서비스의 
성능 메트릭, 상태, 자원 사용량을 모니터링
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
from google.cloud import monitoring_v3
from google.auth import default
import os
import aiohttp

from ...config import get_settings
from ...models.monitoring.monitoring_models import CloudRunMetrics, ServiceStatus, MonitoringError


logger = logging.getLogger(__name__)


class CloudRunMonitoringService:
    """Google Cloud Run 모니터링 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self._monitoring_client = None
        self._project_id = self.settings.gcp_project_id
        self._service_name = self.settings.gcp_service_name
        self._region = self.settings.gcp_region
        self._credentials = None
        
        # 서비스 계정 키 설정
        if self.settings.gcp_service_account_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.settings.gcp_service_account_path
    
    def _get_monitoring_client(self) -> monitoring_v3.MetricServiceClient:
        """Cloud Monitoring 클라이언트 반환"""
        if self._monitoring_client is None:
            try:
                credentials, project = default()
                self._monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)
                self._credentials = credentials
                if not self._project_id:
                    self._project_id = project
                logger.info(f"Cloud Monitoring 클라이언트 초기화 완료 (프로젝트: {self._project_id})")
            except Exception as e:
                logger.error(f"Cloud Monitoring 클라이언트 초기화 실패: {e}")
                raise
        return self._monitoring_client
    
    async def get_service_status(self) -> ServiceStatus:
        """Cloud Run 서비스 상태 확인"""
        try:
            if not all([self._project_id, self._service_name, self._region]):
                logger.warning("Cloud Run 설정이 불완전합니다")
                return ServiceStatus.UNKNOWN
            
            # 메트릭을 통한 간접적 상태 확인
            # 최근 요청이 있으면 서비스가 활성 상태로 간주
            loop = asyncio.get_event_loop()
            has_recent_activity = await loop.run_in_executor(
                None, self._check_recent_activity
            )
            
            if has_recent_activity:
                return ServiceStatus.HEALTHY
            else:
                # 활동이 없어도 UNKNOWN으로 처리 (서비스가 유휴 상태일 수 있음)
                return ServiceStatus.UNKNOWN
                
        except Exception as e:
            logger.error(f"Cloud Run 서비스 상태 확인 실패: {e}")
            return ServiceStatus.UNKNOWN
    
    def _check_recent_activity(self) -> bool:
        """최근 활동 확인 (간접적 상태 체크)"""
        try:
            client = self._get_monitoring_client()
            project_name = f"projects/{self._project_id}"
            
            # 최근 5분간의 요청 수 확인
            now = datetime.utcnow()
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": int(now.timestamp())},
                "start_time": {"seconds": int((now - timedelta(minutes=5)).timestamp())},
            })
            
            service_filter = f'resource.label.service_name="{self._service_name}"'
            if self._region:
                service_filter += f' AND resource.label.location="{self._region}"'
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": project_name,
                "filter": f'metric.type="run.googleapis.com/request_count" AND {service_filter}',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            })
            
            results = client.list_time_series(request=request)
            
            # 결과가 있으면 최근 활동이 있다고 간주
            for result in results:
                if result.points:
                    return True
            
            # 메트릭이 없으면 서비스가 설정되어 있지만 활동이 없거나 문제가 있을 수 있음
            return False
            
        except Exception as e:
            logger.debug(f"최근 활동 확인 실패: {e}")
            return False
    
    async def get_metrics(self) -> CloudRunMetrics:
        """Cloud Run 메트릭 수집"""
        try:
            status = await self.get_service_status()
            
            # 메트릭 데이터 수집 (비동기)
            loop = asyncio.get_event_loop()
            metrics_data = await loop.run_in_executor(
                None, self._collect_metrics
            )
            
            # CloudRunMetrics 객체 생성
            metrics = CloudRunMetrics(
                service_name=self._service_name or "unknown",
                region=self._region or "unknown",
                status=status,
                **metrics_data
            )
            
            logger.info(f"Cloud Run 메트릭 수집 완료: {self._service_name}")
            return metrics
            
        except Exception as e:
            logger.error(f"Cloud Run 메트릭 수집 실패: {e}")
            return CloudRunMetrics(
                service_name=self._service_name or "unknown",
                region=self._region or "unknown", 
                status=ServiceStatus.UNKNOWN,
                error_message=str(e)
            )
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """실제 메트릭 데이터 수집"""
        metrics_data = {}
        
        try:
            client = self._get_monitoring_client()
            project_name = f"projects/{self._project_id}"
            
            # 조회 시간 범위 (최근 5분)
            now = datetime.utcnow()
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": int(now.timestamp())},
                "start_time": {"seconds": int((now - timedelta(minutes=5)).timestamp())},
            })
            
            # 필터 조건
            service_filter = f'resource.label.service_name="{self._service_name}"'
            if self._region:
                service_filter += f' AND resource.label.location="{self._region}"'
            
            # 1. Request Count (요청 수)
            try:
                request_count = self._get_metric_value(
                    client, project_name, interval,
                    "run.googleapis.com/request_count",
                    service_filter
                )
                if request_count is not None:
                    metrics_data['request_count'] = int(request_count)
            except Exception as e:
                logger.debug(f"Request count 메트릭 수집 실패: {e}")
            
            # 2. Request Latency (요청 지연시간)
            try:
                request_latency = self._get_metric_value(
                    client, project_name, interval,
                    "run.googleapis.com/request_latencies", 
                    service_filter
                )
                if request_latency is not None:
                    metrics_data['request_latency_ms'] = float(request_latency) * 1000  # seconds to ms
                    metrics_data['response_time_ms'] = metrics_data['request_latency_ms']
            except Exception as e:
                logger.debug(f"Request latency 메트릭 수집 실패: {e}")
            
            # 3. CPU Utilization (CPU 사용률)
            try:
                cpu_utilization = self._get_metric_value(
                    client, project_name, interval,
                    "run.googleapis.com/container/cpu/utilizations",
                    service_filter
                )
                if cpu_utilization is not None:
                    metrics_data['cpu_utilization'] = float(cpu_utilization) * 100  # ratio to percentage
            except Exception as e:
                logger.debug(f"CPU utilization 메트릭 수집 실패: {e}")
            
            # 4. Memory Utilization (메모리 사용률)
            try:
                memory_utilization = self._get_metric_value(
                    client, project_name, interval,
                    "run.googleapis.com/container/memory/utilizations",
                    service_filter
                )
                if memory_utilization is not None:
                    metrics_data['memory_utilization'] = float(memory_utilization) * 100
            except Exception as e:
                logger.debug(f"Memory utilization 메트릭 수집 실패: {e}")
            
            # 5. Instance Count (인스턴스 수)
            try:
                instance_count = self._get_metric_value(
                    client, project_name, interval,
                    "run.googleapis.com/container/instance_count",
                    service_filter
                )
                if instance_count is not None:
                    metrics_data['instance_count'] = int(instance_count)
            except Exception as e:
                logger.debug(f"Instance count 메트릭 수집 실패: {e}")
            
            # 6. Billable Instance Time (과금 인스턴스 시간)
            try:
                billable_time = self._get_metric_value(
                    client, project_name, interval,
                    "run.googleapis.com/container/billable_instance_time",
                    service_filter
                )
                if billable_time is not None:
                    metrics_data['billable_instance_time'] = float(billable_time)
            except Exception as e:
                logger.debug(f"Billable instance time 메트릭 수집 실패: {e}")
            
            logger.debug(f"수집된 메트릭: {len(metrics_data)}개")
            
        except Exception as e:
            logger.error(f"메트릭 수집 중 오류: {e}")
            metrics_data['error_message'] = str(e)
        
        return metrics_data
    
    def _get_metric_value(
        self, 
        client: monitoring_v3.MetricServiceClient,
        project_name: str,
        interval: monitoring_v3.TimeInterval,
        metric_type: str,
        filter_str: str
    ) -> Optional[float]:
        """특정 메트릭 값 조회"""
        try:
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": project_name,
                "filter": f'metric.type="{metric_type}" AND {filter_str}',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            })
            
            results = client.list_time_series(request=request)
            
            # 최신 값 반환
            for result in results:
                if result.points:
                    latest_point = result.points[0]  # 최신 포인트
                    if hasattr(latest_point.value, 'double_value'):
                        return latest_point.value.double_value
                    elif hasattr(latest_point.value, 'int64_value'):
                        return float(latest_point.value.int64_value)
            
            return None
            
        except Exception as e:
            logger.debug(f"메트릭 '{metric_type}' 조회 실패: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Cloud Run 헬스체크"""
        try:
            status = await self.get_service_status()
            
            return {
                "service": "cloud_run",
                "status": status.value,
                "project_id": self._project_id,
                "service_name": self._service_name,
                "region": self._region,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cloud Run 헬스체크 실패: {e}")
            return {
                "service": "cloud_run",
                "status": ServiceStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def is_configured(self) -> bool:
        """Cloud Run 모니터링 설정 여부 확인"""
        return all([
            self._project_id,
            self._service_name,
            self._region
        ])