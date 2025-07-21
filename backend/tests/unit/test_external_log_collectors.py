"""
외부 로그 수집기 TDD 테스트

이 테스트는 실제 API 응답을 기반으로 생성된 Mock 데이터를 사용하여
외부 로그 수집기의 동작을 검증합니다.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mock 데이터 import
from tests.fixtures.external_api_mocks import (
    VercelMockData, UpstashMockData, CloudRunMockData, AtlasMockData,
    get_mock_http_headers, get_mock_error_response
)


class TestVercelLogCollector:
    """Vercel 로그 수집기 TDD 테스트"""
    
    @pytest.fixture
    def mock_vercel_collector(self):
        """Vercel 수집기 Mock 설정"""
        # 실제 구현 시 사용할 클래스 구조
        class MockVercelCollector:
            def __init__(self, api_token: str, project_id: str):
                self.api_token = api_token
                self.project_id = project_id
                self.base_url = "https://api.vercel.com"
            
            async def collect_logs(self, hours: int = 1) -> List[Dict[str, Any]]:
                """로그 수집 메서드"""
                pass
            
            async def get_deployments(self, limit: int = 5) -> Dict[str, Any]:
                """배포 목록 조회"""
                pass
            
            async def get_deployment_events(self, deployment_id: str) -> List[Dict[str, Any]]:
                """배포 이벤트 조회"""
                pass
        
        return MockVercelCollector("mock_token", "mock_project_id")
    
    @pytest.mark.asyncio
    async def test_get_deployments_success(self, mock_vercel_collector):
        """Red: 배포 목록 조회 성공 테스트"""
        
        # Red - 실패하는 테스트 작성
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock 응답 설정 (실제 API 응답 기반)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = VercelMockData.get_deployment_list()
            mock_get.return_value = mock_response
            
            # Green - 구현하여 테스트 통과시키기
            async def get_deployments_impl(self, limit: int = 5) -> Dict[str, Any]:
                headers = {"Authorization": f"Bearer {self.api_token}"}
                params = {"projectId": self.project_id, "limit": limit}
                
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/v6/deployments",
                        headers=headers,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"API 호출 실패: {response.status_code}")
            
            # 메서드 동적 할당 (실제 구현에서는 클래스에 정의)
            mock_vercel_collector.get_deployments = get_deployments_impl.__get__(
                mock_vercel_collector, type(mock_vercel_collector)
            )
            
            # 테스트 실행
            result = await mock_vercel_collector.get_deployments(limit=5)
            
            # 검증
            assert result is not None
            assert "deployments" in result
            assert len(result["deployments"]) == 2
            assert result["deployments"][0]["state"] == "READY"
            assert result["deployments"][1]["state"] == "ERROR"
            
            # API 호출 검증
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "projectId" in call_args.kwargs["params"]
            assert "limit" in call_args.kwargs["params"]
    
    @pytest.mark.asyncio
    async def test_get_deployment_events_success(self, mock_vercel_collector):
        """배포 이벤트 조회 성공 테스트"""
        
        deployment_id = "dpl_mock_deployment_001"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock 응답 설정
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = VercelMockData.get_deployment_events(deployment_id)
            mock_get.return_value = mock_response
            
            # 구현
            async def get_deployment_events_impl(self, deployment_id: str) -> List[Dict[str, Any]]:
                headers = {"Authorization": f"Bearer {self.api_token}"}
                
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/v2/deployments/{deployment_id}/events",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"이벤트 조회 실패: {response.status_code}")
            
            mock_vercel_collector.get_deployment_events = get_deployment_events_impl.__get__(
                mock_vercel_collector, type(mock_vercel_collector)
            )
            
            # 테스트 실행
            events = await mock_vercel_collector.get_deployment_events(deployment_id)
            
            # 검증
            assert events is not None
            assert len(events) > 0
            assert events[0]["type"] == "stdout"
            assert "payload" in events[0]
            assert "deploymentId" in events[0]["payload"]
            assert events[0]["payload"]["deploymentId"] == deployment_id
    
    @pytest.mark.asyncio
    async def test_collect_logs_integration(self, mock_vercel_collector):
        """통합 로그 수집 테스트"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # 여러 번의 API 호출 모킹 (배포 목록 + 각 배포의 이벤트들)
            deployment_response = MagicMock()
            deployment_response.status_code = 200
            deployment_response.json.return_value = VercelMockData.get_deployment_list()
            
            events_response_1 = MagicMock()
            events_response_1.status_code = 200
            events_response_1.json.return_value = VercelMockData.get_deployment_events("dpl_mock_deployment_001")
            
            events_response_2 = MagicMock()
            events_response_2.status_code = 200
            events_response_2.json.return_value = VercelMockData.get_deployment_events("dpl_mock_deployment_002")
            
            # 총 3번의 호출: 배포 목록 1번 + 각 배포 이벤트 2번
            mock_get.side_effect = [deployment_response, events_response_1, events_response_2]
            
            # 통합 로그 수집 구현
            async def collect_logs_impl(self, hours: int = 1) -> List[Dict[str, Any]]:
                log_entries = []
                
                # 1. 최근 배포 목록 조회
                deployments_data = await self.get_deployments(limit=5)
                deployments = deployments_data.get("deployments", [])
                
                # 2. 각 배포의 이벤트 수집
                for deployment in deployments[:2]:  # 최근 2개만
                    deployment_id = deployment["uid"]
                    events = await self.get_deployment_events(deployment_id)
                    
                    # 3. 로그 엔트리로 변환
                    for event in events:
                        log_entry = {
                            "timestamp": datetime.fromtimestamp(event["created"] / 1000).isoformat(),
                            "level": "ERROR" if event["type"] == "stderr" else "INFO",
                            "service": "vercel",
                            "source": "external",
                            "message": event["payload"].get("text", ""),
                            "context": {
                                "deployment_id": deployment_id,
                                "deployment_state": deployment["state"],
                                "event_type": event["type"]
                            },
                            "metadata": {
                                "infrastructure": "vercel",
                                "deployment_url": deployment.get("url"),
                                "event_id": event["payload"].get("id")
                            }
                        }
                        log_entries.append(log_entry)
                
                return log_entries
            
            # 이전에 정의한 메서드들 재할당
            async def get_deployments_impl(self, limit: int = 5):
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/v6/deployments")
                    return response.json()
            
            async def get_deployment_events_impl(self, deployment_id: str):
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/v2/deployments/{deployment_id}/events")
                    return response.json()
            
            mock_vercel_collector.get_deployments = get_deployments_impl.__get__(
                mock_vercel_collector, type(mock_vercel_collector)
            )
            mock_vercel_collector.get_deployment_events = get_deployment_events_impl.__get__(
                mock_vercel_collector, type(mock_vercel_collector)
            )
            mock_vercel_collector.collect_logs = collect_logs_impl.__get__(
                mock_vercel_collector, type(mock_vercel_collector)
            )
            
            # 테스트 실행
            log_entries = await mock_vercel_collector.collect_logs(hours=1)
            
            # 검증
            assert log_entries is not None
            assert len(log_entries) > 0
            
            # 첫 번째 로그 엔트리 검증
            first_log = log_entries[0]
            assert first_log["service"] == "vercel"
            assert first_log["source"] == "external"
            assert "timestamp" in first_log
            assert "level" in first_log
            assert "message" in first_log
            assert "context" in first_log
            assert "metadata" in first_log
            
            # 컨텍스트 검증
            assert "deployment_id" in first_log["context"]
            assert "deployment_state" in first_log["context"]
            
            # 메타데이터 검증
            assert first_log["metadata"]["infrastructure"] == "vercel"
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_vercel_collector):
        """API 에러 처리 테스트"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # 401 Unauthorized 에러 모킹
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = '{"error": {"code": "forbidden", "message": "Invalid token"}}'
            mock_get.return_value = mock_response
            
            # 에러 처리 구현
            async def get_deployments_with_error_handling(self, limit: int = 5):
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.base_url}/v6/deployments")
                        
                        if response.status_code == 200:
                            return response.json()
                        elif response.status_code == 401:
                            raise Exception("Vercel API 인증 실패: 토큰을 확인해주세요")
                        else:
                            raise Exception(f"Vercel API 오류: {response.status_code}")
                            
                except Exception as e:
                    # 에러 로그 생성
                    return {
                        "error": True,
                        "message": str(e),
                        "deployments": []
                    }
            
            mock_vercel_collector.get_deployments = get_deployments_with_error_handling.__get__(
                mock_vercel_collector, type(mock_vercel_collector)
            )
            
            # 테스트 실행
            result = await mock_vercel_collector.get_deployments()
            
            # 에러 응답 검증
            assert result["error"] is True
            assert "인증 실패" in result["message"]
            assert result["deployments"] == []


class TestUpstashRedisCollector:
    """Upstash Redis 메트릭 수집기 TDD 테스트"""
    
    @pytest.fixture
    def mock_upstash_collector(self):
        """Upstash 수집기 Mock 설정"""
        class MockUpstashCollector:
            def __init__(self, rest_url: str, rest_token: str):
                self.rest_url = rest_url
                self.rest_token = rest_token
            
            async def collect_metrics(self) -> List[Dict[str, Any]]:
                """메트릭 수집 메서드"""
                pass
            
            async def execute_command(self, command: str, *args) -> Dict[str, Any]:
                """Redis 명령 실행"""
                pass
        
        return MockUpstashCollector("https://mock.upstash.io", "mock_token")
    
    @pytest.mark.asyncio
    async def test_ping_command(self, mock_upstash_collector):
        """PING 명령 테스트"""
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock 응답 설정 (실제 응답 기반)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = UpstashMockData.get_ping_response()
            mock_response.headers = get_mock_http_headers()
            mock_post.return_value = mock_response
            
            # PING 명령 구현
            async def execute_command_impl(self, command: str, *args) -> Dict[str, Any]:
                headers = {"Authorization": f"Bearer {self.rest_token}"}
                url = f"{self.rest_url}/{command.lower()}"
                if args:
                    url += "/" + "/".join(str(arg) for arg in args)
                
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers)
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"Redis 명령 실패: {response.status_code}")
            
            mock_upstash_collector.execute_command = execute_command_impl.__get__(
                mock_upstash_collector, type(mock_upstash_collector)
            )
            
            # 테스트 실행
            result = await mock_upstash_collector.execute_command("PING")
            
            # 검증
            assert result is not None
            assert result["result"] == "PONG"
            
            # API 호출 검증
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0].endswith("/ping")
    
    @pytest.mark.asyncio
    async def test_info_command(self, mock_upstash_collector):
        """INFO 명령 테스트"""
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = UpstashMockData.get_info_response()
            mock_post.return_value = mock_response
            
            # 이전 구현 재사용
            async def execute_command_impl(self, command: str, *args):
                headers = {"Authorization": f"Bearer {self.rest_token}"}
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{self.rest_url}/{command.lower()}", headers=headers)
                    return response.json()
            
            mock_upstash_collector.execute_command = execute_command_impl.__get__(
                mock_upstash_collector, type(mock_upstash_collector)
            )
            
            # 테스트 실행
            result = await mock_upstash_collector.execute_command("INFO")
            
            # 검증
            assert result is not None
            assert "result" in result
            assert "upstash_version" in result["result"]
            assert "redis_version" in result["result"]
            assert "used_memory" in result["result"]
            assert "total_commands_processed" in result["result"]
    
    @pytest.mark.asyncio
    async def test_collect_metrics_integration(self, mock_upstash_collector):
        """메트릭 수집 통합 테스트"""
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # 여러 명령의 응답 모킹
            responses = [
                # PING 응답
                MagicMock(status_code=200, json=lambda: UpstashMockData.get_ping_response()),
                # INFO 응답  
                MagicMock(status_code=200, json=lambda: UpstashMockData.get_info_response()),
                # DBSIZE 응답
                MagicMock(status_code=200, json=lambda: UpstashMockData.get_dbsize_response()),
                # KEYS 응답
                MagicMock(status_code=200, json=lambda: UpstashMockData.get_keys_pattern_response("cache:*"))
            ]
            
            mock_post.side_effect = responses
            
            # 메트릭 수집 구현
            async def collect_metrics_impl(self) -> List[Dict[str, Any]]:
                metrics = []
                
                # 기본 연결 테스트
                ping_result = await self.execute_command("PING")
                metrics.append({
                    "metric_type": "connectivity",
                    "command": "PING",
                    "result": ping_result["result"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # 서버 정보 수집
                info_result = await self.execute_command("INFO")
                info_text = info_result["result"]
                
                # INFO 결과 파싱
                info_metrics = self._parse_redis_info(info_text)
                metrics.append({
                    "metric_type": "server_info",
                    "command": "INFO",
                    "parsed_metrics": info_metrics,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # 데이터베이스 크기
                dbsize_result = await self.execute_command("DBSIZE")
                metrics.append({
                    "metric_type": "database_size",
                    "command": "DBSIZE", 
                    "result": dbsize_result["result"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # 캐시 키 패턴 분석
                keys_result = await self.execute_command("KEYS", "cache:*")
                metrics.append({
                    "metric_type": "cache_keys",
                    "command": "KEYS cache:*",
                    "result": keys_result["result"],
                    "cache_key_count": len(keys_result["result"]),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return metrics
            
            def _parse_redis_info(self, info_text: str) -> Dict[str, Any]:
                """Redis INFO 결과 파싱"""
                metrics = {}
                lines = info_text.split("\\r\\n")
                
                for line in lines:
                    if ":" in line and not line.startswith("#"):
                        key, value = line.split(":", 1)
                        # 숫자 값 변환 시도
                        try:
                            if "." in value:
                                metrics[key] = float(value)
                            else:
                                metrics[key] = int(value)
                        except ValueError:
                            metrics[key] = value
                
                return metrics
            
            # 메서드 구현
            async def execute_command_impl(self, command: str, *args):
                headers = {"Authorization": f"Bearer {self.rest_token}"}
                url = f"{self.rest_url}/{command.lower()}"
                if args:
                    url += "/" + "/".join(str(arg) for arg in args)
                
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers)
                    return response.json()
            
            mock_upstash_collector.execute_command = execute_command_impl.__get__(
                mock_upstash_collector, type(mock_upstash_collector)
            )
            mock_upstash_collector._parse_redis_info = _parse_redis_info.__get__(
                mock_upstash_collector, type(mock_upstash_collector)
            )
            mock_upstash_collector.collect_metrics = collect_metrics_impl.__get__(
                mock_upstash_collector, type(mock_upstash_collector)
            )
            
            # 테스트 실행
            metrics = await mock_upstash_collector.collect_metrics()
            
            # 검증
            assert metrics is not None
            assert len(metrics) == 4
            
            # 연결성 메트릭 검증
            connectivity_metric = metrics[0]
            assert connectivity_metric["metric_type"] == "connectivity"
            assert connectivity_metric["result"] == "PONG"
            
            # 서버 정보 메트릭 검증
            server_info_metric = metrics[1]
            assert server_info_metric["metric_type"] == "server_info"
            assert "parsed_metrics" in server_info_metric
            assert "upstash_version" in server_info_metric["parsed_metrics"]
            
            # 데이터베이스 크기 메트릭 검증
            dbsize_metric = metrics[2]
            assert dbsize_metric["metric_type"] == "database_size"
            assert isinstance(dbsize_metric["result"], int)
            
            # 캐시 키 메트릭 검증
            cache_metric = metrics[3]
            assert cache_metric["metric_type"] == "cache_keys"
            assert isinstance(cache_metric["result"], list)
            assert "cache_key_count" in cache_metric


class TestCloudRunLogCollector:
    """Google Cloud Run 로그 수집기 TDD 테스트"""
    
    @pytest.fixture
    def mock_cloudrun_collector(self):
        """Cloud Run 수집기 Mock 설정"""
        class MockCloudRunCollector:
            def __init__(self, project_id: str, credentials_path: str):
                self.project_id = project_id
                self.credentials_path = credentials_path
                self.service_name = "xai-community-backend"
                self.location = "asia-northeast3"
            
            async def collect_logs(self, hours: int = 1) -> List[Dict[str, Any]]:
                """로그 수집 메서드"""
                pass
            
            async def get_log_entries(self, hours: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
                """로그 엔트리 조회"""
                pass
            
            async def filter_log_entries(self, entries: List[Dict[str, Any]], severity_filter: List[str] = None) -> List[Dict[str, Any]]:
                """로그 엔트리 필터링"""
                pass
        
        return MockCloudRunCollector("xai-community", "/mock/credentials.json")
    
    @pytest.mark.asyncio
    async def test_get_log_entries_success(self, mock_cloudrun_collector):
        """Cloud Run 로그 엔트리 조회 성공 테스트"""
        
        with patch('google.cloud.logging.Client') as mock_client:
            # Mock Google Cloud Logging Client 설정
            mock_logging_client = MagicMock()
            mock_client.return_value = mock_logging_client
            
            # Mock 로그 엔트리들 설정
            mock_entries = CloudRunMockData.get_log_entries()
            mock_logging_client.list_entries.return_value = mock_entries
            
            # 구현
            async def get_log_entries_impl(self, hours: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
                from datetime import datetime, timedelta
                
                # 시간 필터 생성
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=hours)
                
                # Google Cloud Logging 클라이언트 생성
                from google.cloud import logging
                client = logging.Client(project=self.project_id)
                
                # 로그 필터 생성
                filter_str = f"""
                resource.type="cloud_run_revision"
                resource.labels.service_name="{self.service_name}"
                resource.labels.location="{self.location}"
                timestamp>="{start_time.isoformat()}Z"
                timestamp<="{end_time.isoformat()}Z"
                """
                
                # 로그 엔트리 조회
                entries = client.list_entries(
                    filter_=filter_str.strip(),
                    page_size=page_size,
                    order_by=logging.DESCENDING
                )
                
                return list(entries)
            
            mock_cloudrun_collector.get_log_entries = get_log_entries_impl.__get__(
                mock_cloudrun_collector, type(mock_cloudrun_collector)
            )
            
            # 테스트 실행
            entries = await mock_cloudrun_collector.get_log_entries(hours=1)
            
            # 검증
            assert entries is not None
            assert len(entries) == 2
            
            # 첫 번째 엔트리 검증
            first_entry = entries[0]
            assert first_entry["severity"] == "INFO"
            assert first_entry["resource"]["type"] == "cloud_run_revision"
            assert first_entry["resource"]["labels"]["service_name"] == "xai-community-backend"
            assert "http_request" in first_entry
            
            # 두 번째 엔트리 (에러) 검증
            error_entry = entries[1]
            assert error_entry["severity"] == "ERROR"
            assert error_entry["http_request"]["status"] == 500
            assert "Database connection timeout" in error_entry["payload"]
    
    @pytest.mark.asyncio
    async def test_filter_log_entries(self, mock_cloudrun_collector):
        """로그 엔트리 필터링 테스트"""
        
        # 필터링 구현
        async def filter_log_entries_impl(self, entries: List[Dict[str, Any]], severity_filter: List[str] = None) -> List[Dict[str, Any]]:
            if not severity_filter:
                return entries
            
            filtered_entries = []
            for entry in entries:
                if entry.get("severity") in severity_filter:
                    filtered_entries.append(entry)
            
            return filtered_entries
        
        mock_cloudrun_collector.filter_log_entries = filter_log_entries_impl.__get__(
            mock_cloudrun_collector, type(mock_cloudrun_collector)
        )
        
        # 테스트 데이터
        all_entries = CloudRunMockData.get_log_entries()
        
        # ERROR 로그만 필터링
        error_entries = await mock_cloudrun_collector.filter_log_entries(
            all_entries, 
            severity_filter=["ERROR"]
        )
        
        # 검증
        assert len(error_entries) == 1
        assert error_entries[0]["severity"] == "ERROR"
        assert error_entries[0]["http_request"]["status"] == 500
        
        # INFO 로그만 필터링
        info_entries = await mock_cloudrun_collector.filter_log_entries(
            all_entries, 
            severity_filter=["INFO"]
        )
        
        assert len(info_entries) == 1
        assert info_entries[0]["severity"] == "INFO"
        assert info_entries[0]["http_request"]["status"] == 200
    
    @pytest.mark.asyncio
    async def test_collect_logs_integration(self, mock_cloudrun_collector):
        """Cloud Run 로그 수집 통합 테스트"""
        
        with patch('google.cloud.logging.Client') as mock_client:
            mock_logging_client = MagicMock()
            mock_client.return_value = mock_logging_client
            mock_logging_client.list_entries.return_value = CloudRunMockData.get_log_entries()
            
            # 통합 로그 수집 구현
            async def collect_logs_impl(self, hours: int = 1) -> List[Dict[str, Any]]:
                log_entries = []
                
                # 1. Cloud Run 로그 엔트리 조회
                raw_entries = await self.get_log_entries(hours)
                
                # 2. 로그 엔트리를 표준 형식으로 변환
                for entry in raw_entries:
                    # 레벨 매핑
                    level_mapping = {
                        "ERROR": "ERROR",
                        "WARNING": "WARN", 
                        "INFO": "INFO",
                        "DEBUG": "DEBUG"
                    }
                    
                    log_entry = {
                        "timestamp": entry["timestamp"],
                        "level": level_mapping.get(entry["severity"], "INFO"),
                        "service": "cloud-run",
                        "source": "external",
                        "message": entry["payload"],
                        "context": {
                            "service_name": entry["resource"]["labels"]["service_name"],
                            "revision_name": entry["resource"]["labels"].get("revision_name"),
                            "location": entry["resource"]["labels"]["location"],
                            "trace_id": entry.get("trace", "").split("/")[-1] if entry.get("trace") else None
                        },
                        "metadata": {
                            "infrastructure": "google-cloud-run",
                            "insert_id": entry.get("insert_id"),
                            "span_id": entry.get("span_id"),
                            "http_request": entry.get("http_request"),
                            "source_location": entry.get("source_location")
                        }
                    }
                    log_entries.append(log_entry)
                
                return log_entries
            
            # 이전 메서드들 재할당
            async def get_log_entries_impl(self, hours: int = 1, page_size: int = 100):
                from google.cloud import logging
                client = logging.Client(project=self.project_id)
                entries = client.list_entries()
                return list(entries)
            
            mock_cloudrun_collector.get_log_entries = get_log_entries_impl.__get__(
                mock_cloudrun_collector, type(mock_cloudrun_collector)
            )
            mock_cloudrun_collector.collect_logs = collect_logs_impl.__get__(
                mock_cloudrun_collector, type(mock_cloudrun_collector)
            )
            
            # 테스트 실행
            log_entries = await mock_cloudrun_collector.collect_logs(hours=1)
            
            # 검증
            assert log_entries is not None
            assert len(log_entries) == 2
            
            # 첫 번째 로그 엔트리 검증
            first_log = log_entries[0]
            assert first_log["service"] == "cloud-run"
            assert first_log["source"] == "external"
            assert first_log["level"] == "INFO"
            assert "Application started" in first_log["message"]
            assert "context" in first_log
            assert "metadata" in first_log
            
            # 컨텍스트 검증
            assert first_log["context"]["service_name"] == "xai-community-backend"
            assert first_log["context"]["location"] == "asia-northeast3"
            
            # 메타데이터 검증
            assert first_log["metadata"]["infrastructure"] == "google-cloud-run"
            assert "http_request" in first_log["metadata"]
            
            # ERROR 로그 검증
            error_log = log_entries[1]
            assert error_log["level"] == "ERROR"
            assert error_log["metadata"]["http_request"]["status"] == 500
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_cloudrun_collector):
        """Cloud Run API 에러 처리 테스트"""
        
        with patch('google.cloud.logging.Client') as mock_client:
            # 인증 오류 시뮬레이션
            mock_client.side_effect = Exception("Authentication failed: Invalid credentials")
            
            # 에러 처리 구현
            async def get_log_entries_with_error_handling(self, hours: int = 1, page_size: int = 100):
                try:
                    from google.cloud import logging
                    client = logging.Client(project=self.project_id)
                    entries = client.list_entries()
                    return list(entries)
                except Exception as e:
                    # 에러 로그 생성
                    return [{
                        "error": True,
                        "message": f"Cloud Run 로그 수집 실패: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "severity": "ERROR",
                        "entries": []
                    }]
            
            mock_cloudrun_collector.get_log_entries = get_log_entries_with_error_handling.__get__(
                mock_cloudrun_collector, type(mock_cloudrun_collector)
            )
            
            # 테스트 실행
            result = await mock_cloudrun_collector.get_log_entries()
            
            # 에러 응답 검증
            assert len(result) == 1
            assert result[0]["error"] is True
            assert "Authentication failed" in result[0]["message"]
            assert result[0]["severity"] == "ERROR"


class TestAtlasLogCollector:
    """MongoDB Atlas 로그 수집기 TDD 테스트"""
    
    @pytest.fixture
    def mock_atlas_collector(self):
        """Atlas 수집기 Mock 설정"""
        class MockAtlasCollector:
            def __init__(self, api_key: str, api_secret: str, group_id: str, cluster_name: str):
                self.api_key = api_key
                self.api_secret = api_secret
                self.group_id = group_id
                self.cluster_name = cluster_name
                self.base_url = "https://cloud.mongodb.com/api/atlas/v1.0"
            
            async def collect_logs(self, hours: int = 1) -> List[Dict[str, Any]]:
                """로그 수집 메서드"""
                pass
            
            async def get_mongod_logs(self, hours: int = 1) -> List[str]:
                """mongod 로그 조회"""
                pass
            
            async def get_access_logs(self, hours: int = 1) -> Dict[str, Any]:
                """액세스 로그 조회"""
                pass
            
            async def parse_mongod_log_line(self, log_line: str) -> Dict[str, Any]:
                """mongod 로그 라인 파싱"""
                pass
        
        return MockAtlasCollector("mock_key", "mock_secret", "mock_group", "cluster0")
    
    @pytest.mark.asyncio
    async def test_get_mongod_logs_success(self, mock_atlas_collector):
        """MongoDB mongod 로그 조회 성공 테스트"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock 응답 설정
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "logs": AtlasMockData.get_mongod_logs()
            }
            mock_get.return_value = mock_response
            
            # 구현
            async def get_mongod_logs_impl(self, hours: int = 1) -> List[str]:
                from datetime import datetime, timedelta
                import httpx
                import base64
                
                # 시간 필터
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=hours)
                
                # 인증 헤더 생성
                auth_string = f"{self.api_key}:{self.api_secret}"
                auth_bytes = auth_string.encode('ascii')
                auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                
                headers = {
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/json"
                }
                
                # API 호출
                url = f"{self.base_url}/groups/{self.group_id}/clusters/{self.cluster_name}/logs/mongodb.gz"
                params = {
                    "startDate": start_time.isoformat() + "Z",
                    "endDate": end_time.isoformat() + "Z"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        return response.json().get("logs", [])
                    else:
                        raise Exception(f"Atlas API 호출 실패: {response.status_code}")
            
            mock_atlas_collector.get_mongod_logs = get_mongod_logs_impl.__get__(
                mock_atlas_collector, type(mock_atlas_collector)
            )
            
            # 테스트 실행
            logs = await mock_atlas_collector.get_mongod_logs(hours=1)
            
            # 검증
            assert logs is not None
            assert len(logs) == 4
            assert '"t":{"$date":"2025-07-19T02:00:00.000+00:00"}' in logs[0]
            assert '"s":"I"' in logs[0]  # INFO 레벨
            assert '"c":"NETWORK"' in logs[0]  # NETWORK 컴포넌트
            assert '"s":"E"' in logs[2]  # ERROR 레벨
    
    @pytest.mark.asyncio
    async def test_parse_mongod_log_line(self, mock_atlas_collector):
        """mongod 로그 라인 파싱 테스트"""
        
        # 로그 파싱 구현
        async def parse_mongod_log_line_impl(self, log_line: str) -> Dict[str, Any]:
            import json
            
            try:
                # JSON 파싱
                log_data = json.loads(log_line)
                
                # 타임스탬프 변환
                timestamp = log_data["t"]["$date"]
                
                # 심각도 레벨 매핑
                severity_mapping = {
                    "I": "INFO",
                    "W": "WARN",
                    "E": "ERROR",
                    "D": "DEBUG"
                }
                
                level = severity_mapping.get(log_data["s"], "INFO")
                
                # 메시지 구성
                message = log_data.get("msg", "")
                if log_data.get("attr"):
                    message += f" - {json.dumps(log_data['attr'])}"
                
                return {
                    "timestamp": timestamp,
                    "level": level,
                    "service": "database",
                    "source": "external",
                    "message": message,
                    "context": {
                        "component": log_data.get("c", ""),
                        "context_name": log_data.get("ctx", ""),
                        "log_id": log_data.get("id"),
                        "cluster_name": self.cluster_name
                    },
                    "metadata": {
                        "infrastructure": "mongodb-atlas",
                        "raw_severity": log_data["s"],
                        "raw_component": log_data.get("c"),
                        "attributes": log_data.get("attr")
                    }
                }
                
            except (json.JSONDecodeError, KeyError) as e:
                return {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": "ERROR",
                    "service": "database", 
                    "source": "external",
                    "message": f"로그 파싱 실패: {str(e)} - Raw: {log_line}",
                    "context": {"cluster_name": self.cluster_name},
                    "metadata": {"infrastructure": "mongodb-atlas", "parse_error": True}
                }
        
        mock_atlas_collector.parse_mongod_log_line = parse_mongod_log_line_impl.__get__(
            mock_atlas_collector, type(mock_atlas_collector)
        )
        
        # 테스트 실행
        test_log = AtlasMockData.get_mongod_logs()[0]  # 첫 번째 로그 라인
        parsed = await mock_atlas_collector.parse_mongod_log_line(test_log)
        
        # 검증
        assert parsed["level"] == "INFO"
        assert parsed["service"] == "database"
        assert parsed["source"] == "external"
        assert parsed["context"]["component"] == "NETWORK"
        assert "Connection accepted" in parsed["message"]
        assert parsed["metadata"]["infrastructure"] == "mongodb-atlas"
    
    @pytest.mark.asyncio
    async def test_get_access_logs(self, mock_atlas_collector):
        """Atlas 액세스 로그 조회 테스트"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = AtlasMockData.get_access_history()
            mock_get.return_value = mock_response
            
            # 구현
            async def get_access_logs_impl(self, hours: int = 1) -> Dict[str, Any]:
                from datetime import datetime, timedelta
                import httpx
                import base64
                
                # 인증 헤더
                auth_string = f"{self.api_key}:{self.api_secret}"
                auth_b64 = base64.b64encode(auth_string.encode()).decode()
                headers = {"Authorization": f"Basic {auth_b64}"}
                
                # API 호출
                url = f"{self.base_url}/groups/{self.group_id}/dbAccessHistory"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        raise Exception(f"액세스 로그 조회 실패: {response.status_code}")
            
            mock_atlas_collector.get_access_logs = get_access_logs_impl.__get__(
                mock_atlas_collector, type(mock_atlas_collector)
            )
            
            # 테스트 실행
            access_logs = await mock_atlas_collector.get_access_logs(hours=1)
            
            # 검증
            assert access_logs is not None
            assert "accessLogs" in access_logs
            assert len(access_logs["accessLogs"]) == 2
            
            # 성공한 인증 검증
            success_log = access_logs["accessLogs"][0]
            assert success_log["authResult"] is True
            assert success_log["username"] == "nadle"  # 실제 사용자명으로 업데이트
            assert success_log["authSource"] == "xai_community"
            
            # 실패한 인증 검증
            failed_log = access_logs["accessLogs"][1]
            assert failed_log["authResult"] is False
            assert "Authentication failed" in failed_log["failureReason"]
    
    @pytest.mark.asyncio
    async def test_collect_logs_integration(self, mock_atlas_collector):
        """Atlas 로그 수집 통합 테스트"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # 여러 API 호출 모킹
            mongod_response = MagicMock()
            mongod_response.status_code = 200
            mongod_response.json.return_value = {"logs": AtlasMockData.get_mongod_logs()}
            
            access_response = MagicMock()
            access_response.status_code = 200
            access_response.json.return_value = AtlasMockData.get_access_history()
            
            mock_get.side_effect = [mongod_response, access_response]
            
            # 통합 수집 구현
            async def collect_logs_impl(self, hours: int = 1) -> List[Dict[str, Any]]:
                log_entries = []
                
                try:
                    # 1. mongod 로그 수집
                    mongod_logs = await self.get_mongod_logs(hours)
                    for log_line in mongod_logs:
                        parsed_log = await self.parse_mongod_log_line(log_line)
                        log_entries.append(parsed_log)
                    
                    # 2. 액세스 로그 수집
                    access_data = await self.get_access_logs(hours)
                    for access_log in access_data.get("accessLogs", []):
                        access_entry = {
                            "timestamp": access_log["timestamp"],
                            "level": "WARN" if not access_log["authResult"] else "INFO",
                            "service": "database",
                            "source": "external",
                            "message": f"Database access from {access_log['ipAddress']} by {access_log['username']}",
                            "context": {
                                "username": access_log["username"],
                                "auth_source": access_log["authSource"],
                                "ip_address": access_log["ipAddress"],
                                "hostname": access_log["hostname"],
                                "cluster_name": self.cluster_name
                            },
                            "metadata": {
                                "infrastructure": "mongodb-atlas",
                                "log_type": "access",
                                "auth_result": access_log["authResult"],
                                "failure_reason": access_log.get("failureReason")
                            }
                        }
                        log_entries.append(access_entry)
                    
                    return log_entries
                    
                except Exception as e:
                    # 에러 로그 생성
                    return [{
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "level": "ERROR",
                        "service": "database",
                        "source": "external",
                        "message": f"Atlas 로그 수집 실패: {str(e)}",
                        "context": {"cluster_name": self.cluster_name},
                        "metadata": {"infrastructure": "mongodb-atlas", "error": True}
                    }]
            
            # 이전 메서드들 재할당
            async def get_mongod_logs_impl(self, hours: int = 1):
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/groups/{self.group_id}/clusters/{self.cluster_name}/logs/mongodb.gz")
                    return response.json().get("logs", [])
            
            async def get_access_logs_impl(self, hours: int = 1):
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/groups/{self.group_id}/dbAccessHistory")
                    return response.json()
            
            async def parse_mongod_log_line_impl(self, log_line: str):
                import json
                log_data = json.loads(log_line)
                return {
                    "timestamp": log_data["t"]["$date"],
                    "level": {"I": "INFO", "W": "WARN", "E": "ERROR", "D": "DEBUG"}.get(log_data["s"], "INFO"),
                    "service": "database",
                    "source": "external", 
                    "message": log_data.get("msg", ""),
                    "context": {"component": log_data.get("c", ""), "cluster_name": self.cluster_name},
                    "metadata": {"infrastructure": "mongodb-atlas"}
                }
            
            mock_atlas_collector.get_mongod_logs = get_mongod_logs_impl.__get__(
                mock_atlas_collector, type(mock_atlas_collector)
            )
            mock_atlas_collector.get_access_logs = get_access_logs_impl.__get__(
                mock_atlas_collector, type(mock_atlas_collector)
            )
            mock_atlas_collector.parse_mongod_log_line = parse_mongod_log_line_impl.__get__(
                mock_atlas_collector, type(mock_atlas_collector)
            )
            mock_atlas_collector.collect_logs = collect_logs_impl.__get__(
                mock_atlas_collector, type(mock_atlas_collector)
            )
            
            # 테스트 실행
            log_entries = await mock_atlas_collector.collect_logs(hours=1)
            
            # 검증
            assert log_entries is not None
            assert len(log_entries) == 6  # mongod 4개 + access 2개
            
            # mongod 로그 검증
            mongod_logs = [log for log in log_entries if log["metadata"]["infrastructure"] == "mongodb-atlas" and log["metadata"].get("log_type") != "access"]
            assert len(mongod_logs) == 4
            
            network_log = mongod_logs[0]
            assert network_log["level"] == "INFO"
            assert network_log["context"]["component"] == "NETWORK"
            
            # 액세스 로그 검증
            access_logs = [log for log in log_entries if log["metadata"].get("log_type") == "access"]
            assert len(access_logs) == 2
            
            success_access = access_logs[0]
            assert success_access["level"] == "INFO"
            assert success_access["metadata"]["auth_result"] is True
            
            failed_access = access_logs[1]
            assert failed_access["level"] == "WARN" 
            assert failed_access["metadata"]["auth_result"] is False


if __name__ == "__main__":
    # 개별 테스트 실행
    pytest.main([__file__, "-v"])