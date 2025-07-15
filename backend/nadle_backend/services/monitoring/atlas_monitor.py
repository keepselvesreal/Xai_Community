"""
MongoDB Atlas 모니터링 서비스

Atlas Administration API를 사용하여 클러스터 상태,
성능 메트릭, 자원 사용량을 모니터링
Digest Authentication 사용
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
import requests
from requests.auth import HTTPDigestAuth
from urllib.parse import urlencode, quote

from ...config import get_settings
from ...models.monitoring.monitoring_models import AtlasMetrics, ServiceStatus, MonitoringError


logger = logging.getLogger(__name__)


class AtlasMonitoringService:
    """MongoDB Atlas 모니터링 서비스 (Digest Authentication 사용)"""
    
    def __init__(self):
        self.settings = get_settings()
        self._public_key = self.settings.atlas_public_key
        self._private_key = self.settings.atlas_private_key
        self._group_id = self.settings.atlas_group_id
        self._cluster_name = self.settings.atlas_cluster_name
        self._base_url = "https://cloud.mongodb.com/api/atlas/v2"
        
        # Digest Authentication 설정
        self._auth = HTTPDigestAuth(self._public_key, self._private_key) if self._public_key and self._private_key else None
        self._headers = {
            "Accept": "application/vnd.atlas.2023-01-01+json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Digest Auth를 사용한 동기 HTTP 요청"""
        if not self._auth:
            raise ValueError("Atlas API 인증 정보가 설정되지 않았습니다")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self._auth,
                headers=self._headers,
                timeout=15,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Atlas API 요청 실패: {e}")
            raise
    
    def _get_cluster_info_sync(self) -> Optional[Dict[str, Any]]:
        """클러스터 정보 조회 (동기)"""
        try:
            # 먼저 클러스터 목록을 조회하여 정확한 이름 확인
            clusters_url = f"{self._base_url}/groups/{self._group_id}/clusters"
            clusters_response = self._make_request("GET", clusters_url)
            
            if clusters_response.status_code == 200:
                clusters_data = clusters_response.json()
                clusters = clusters_data.get('results', [])
                logger.info(f"프로젝트 내 클러스터 수: {len(clusters)}")
                
                for cluster in clusters:
                    cluster_name = cluster.get('name', '')
                    logger.info(f"발견된 클러스터: '{cluster_name}'")
                    
                    # 설정된 이름과 일치하는 클러스터 찾기
                    if cluster_name == self._cluster_name:
                        logger.info(f"일치하는 클러스터 발견: {cluster_name}")
                        return cluster
                
                # 정확히 일치하는 것이 없으면 첫 번째 클러스터 사용
                if clusters:
                    first_cluster = clusters[0]
                    logger.warning(f"설정된 클러스터명 '{self._cluster_name}'을 찾을 수 없어 첫 번째 클러스터 사용: '{first_cluster.get('name')}'")
                    return first_cluster
                else:
                    logger.error("프로젝트에 클러스터가 없습니다")
                    return None
            else:
                logger.error(f"클러스터 목록 조회 실패: {clusters_response.status_code}")
                logger.debug(f"오류 응답: {clusters_response.text}")
                
                # 목록 조회 실패 시 기존 방식으로 시도
                encoded_cluster_name = quote(self._cluster_name, safe='')
                url = f"{self._base_url}/groups/{self._group_id}/clusters/{encoded_cluster_name}"
                logger.info(f"직접 클러스터 정보 조회 시도: {url}")
                response = self._make_request("GET", url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"클러스터 정보 조회 성공: {data.get('name', 'Unknown')}")
                    return data
                else:
                    logger.error(f"클러스터 정보 조회 실패: {response.status_code}")
                    logger.debug(f"오류 응답: {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"클러스터 정보 조회 실패: {e}")
            return None
    
    async def get_cluster_status(self) -> ServiceStatus:
        """Atlas 클러스터 상태 확인"""
        try:
            if not all([self._public_key, self._private_key, self._group_id, self._cluster_name]):
                logger.warning("Atlas 설정이 불완전합니다")
                return ServiceStatus.UNKNOWN
            
            # 비동기에서 동기 호출로 변경
            loop = asyncio.get_event_loop()
            cluster_info = await loop.run_in_executor(None, self._get_cluster_info_sync)
            
            if cluster_info:
                state = cluster_info.get('stateName', '').upper()
                logger.info(f"Atlas 클러스터 상태: {state}")
                
                if state == 'IDLE':
                    return ServiceStatus.HEALTHY
                elif state in ['UPDATING', 'REPAIRING']:
                    return ServiceStatus.DEGRADED
                elif state in ['CREATING', 'DELETING']:
                    return ServiceStatus.MAINTENANCE
                else:
                    return ServiceStatus.UNKNOWN
            else:
                return ServiceStatus.UNKNOWN
                    
        except Exception as e:
            logger.error(f"Atlas 클러스터 상태 확인 실패: {e}")
            return ServiceStatus.UNKNOWN
    
    def _get_cluster_metrics_sync(self, metric_name: str, granularity: str = "PT1M") -> List[Dict[str, Any]]:
        """클러스터 메트릭 조회 (동기)"""
        try:
            # 시간 범위 설정 (최근 5분)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            params = {
                "granularity": granularity,  # PT1M = 1분 간격
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "m": metric_name
            }
            
            # Atlas 메트릭 API는 processes 엔드포인트 사용
            # 실제 호스트 이름이 필요하므로 먼저 클러스터 정보에서 호스트 정보 조회
            cluster_info = self._get_cluster_info_sync()
            if not cluster_info:
                return []
            
            # 간단한 메트릭은 클러스터 레벨에서 조회 시도
            url = f"{self._base_url}/groups/{self._group_id}/clusters/{self._cluster_name}/measurements"
            response = self._make_request("GET", url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('measurements', [])
            else:
                logger.debug(f"메트릭 '{metric_name}' 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.debug(f"메트릭 '{metric_name}' 조회 실패: {e}")
            return []
    
    async def get_metrics(self) -> AtlasMetrics:
        """Atlas 메트릭 수집"""
        try:
            status = await self.get_cluster_status()
            
            # 클러스터 기본 정보 수집
            loop = asyncio.get_event_loop()
            cluster_info = await loop.run_in_executor(None, self._get_cluster_info_sync)
            
            metrics_data = {}
            
            if cluster_info:
                metrics_data.update({
                    'cluster_type': cluster_info.get('clusterType'),
                    'mongodb_version': cluster_info.get('mongoDBVersion'),
                    'provider_name': cluster_info.get('providerSettings', {}).get('providerName')
                })
                
                # 연결 정보 조회 시도
                try:
                    connections_current = await loop.run_in_executor(
                        None, 
                        lambda: self._get_simple_metric_value('CONNECTIONS')
                    )
                    if connections_current is not None:
                        metrics_data['connections_current'] = connections_current
                except Exception as e:
                    logger.debug(f"연결 수 메트릭 조회 실패: {e}")
                
                # CPU 사용률 조회 시도
                try:
                    cpu_usage = await loop.run_in_executor(
                        None,
                        lambda: self._get_simple_metric_value('PROCESS_CPU_USER')
                    )
                    if cpu_usage is not None:
                        metrics_data['cpu_usage_percent'] = cpu_usage
                except Exception as e:
                    logger.debug(f"CPU 사용률 메트릭 조회 실패: {e}")
            
            # AtlasMetrics 객체 생성
            metrics = AtlasMetrics(
                cluster_name=self._cluster_name or "unknown",
                status=status,
                **metrics_data
            )
            
            logger.info(f"Atlas 메트릭 수집 완료: {self._cluster_name}")
            return metrics
            
        except Exception as e:
            logger.error(f"Atlas 메트릭 수집 실패: {e}")
            return AtlasMetrics(
                cluster_name=self._cluster_name or "unknown",
                status=ServiceStatus.UNKNOWN,
                error_message=str(e)
            )
    
    def _get_simple_metric_value(self, metric_name: str) -> Optional[float]:
        """간단한 메트릭 값 조회"""
        try:
            measurements = self._get_cluster_metrics_sync(metric_name)
            
            for measurement in measurements:
                if measurement.get('name') == metric_name:
                    data_points = measurement.get('dataPoints', [])
                    if data_points:
                        # 최신 데이터 포인트의 값 반환
                        latest_point = data_points[-1]
                        return latest_point.get('value')
            
            return None
            
        except Exception as e:
            logger.debug(f"메트릭 '{metric_name}' 값 조회 실패: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Atlas 헬스체크"""
        try:
            status = await self.get_cluster_status()
            
            return {
                "service": "mongodb_atlas",
                "status": status.value,
                "cluster_name": self._cluster_name,
                "group_id": self._group_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Atlas 헬스체크 실패: {e}")
            return {
                "service": "mongodb_atlas",
                "status": ServiceStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def is_configured(self) -> bool:
        """Atlas 모니터링 설정 여부 확인"""
        return all([
            self._public_key,
            self._private_key,
            self._group_id,
            self._cluster_name
        ])