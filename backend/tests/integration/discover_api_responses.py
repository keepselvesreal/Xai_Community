"""
실제 외부 시스템 API 응답 탐색 스크립트

이 스크립트는 실제 외부 인프라 API를 호출하여 응답 형식을 수집하고 분석합니다.
수집된 응답 데이터는 Mock 데이터 생성의 기반이 됩니다.
"""

import asyncio
import json
import os
import sys
import base64
import gzip
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import httpx
except ImportError:
    print("❌ httpx 라이브러리를 설치해주세요: uv add httpx")
    sys.exit(1)

try:
    from google.cloud import logging_v2
    from google.oauth2 import service_account
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    print("⚠️  Google Cloud 라이브러리를 찾을 수 없습니다. Cloud Run 로그 수집을 건너뜁니다.")
    GOOGLE_CLOUD_AVAILABLE = False

# 환경변수 로드 (프로덕션 설정 사용)
import os
from dotenv import load_dotenv

# 프로덕션 환경변수 파일 로드
env_file_path = Path(__file__).parent.parent.parent / ".env.prod"
if env_file_path.exists():
    load_dotenv(env_file_path)
    print(f"✅ 환경변수 파일 로드: {env_file_path}")
else:
    print(f"⚠️  환경변수 파일을 찾을 수 없습니다: {env_file_path}")

# 설정 로드
try:
    from nadle_backend.config import settings
    SETTINGS_AVAILABLE = True
except Exception as e:
    print(f"⚠️  설정 로드 실패: {e}")
    SETTINGS_AVAILABLE = False
    
    # 환경변수에서 직접 읽기
    class MockSettings:
        atlas_public_key = os.getenv('ATLAS_PUBLIC_KEY')
        atlas_private_key = os.getenv('ATLAS_PRIVATE_KEY') 
        atlas_group_id = os.getenv('ATLAS_GROUP_ID')
        atlas_cluster_name = os.getenv('ATLAS_CLUSTER_NAME')
        upstash_redis_rest_url = os.getenv('UPSTASH_REDIS_REST_URL')
        upstash_redis_rest_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        vercel_api_token = os.getenv('VERCEL_API_TOKEN')
        vercel_project_id = os.getenv('VERCEL_PROJECT_ID')
    
    settings = MockSettings()


class APIResponseDiscovery:
    """외부 시스템 API 응답 탐색 클래스"""
    
    def __init__(self):
        self.results = {}
        self.output_dir = Path(__file__).parent / "api_samples"
        self.output_dir.mkdir(exist_ok=True)
        
    async def discover_all(self) -> Dict[str, Any]:
        """모든 외부 시스템 API 응답 탐색"""
        
        print("🔍 외부 시스템 API 응답 탐색 시작...")
        print(f"📁 결과 저장 경로: {self.output_dir}")
        print("-" * 60)
        
        # 각 시스템별 탐색 실행
        systems = [
            ("cloud_run", self.discover_cloud_run_logs),
            ("atlas", self.discover_atlas_logs),
            ("vercel", self.discover_vercel_logs),
            ("upstash", self.discover_upstash_metrics)
        ]
        
        for system_name, discovery_func in systems:
            print(f"\n🔍 {system_name.upper()} API 탐색 중...")
            try:
                result = await discovery_func()
                self.results[system_name] = {
                    "success": len(result) > 0 if isinstance(result, list) else bool(result),
                    "sample_count": len(result) if isinstance(result, list) else 1,
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # 개별 결과 저장
                with open(self.output_dir / f"{system_name}_samples.json", "w") as f:
                    json.dump(result, f, indent=2, default=str, ensure_ascii=False)
                    
                status = "✅ 성공" if self.results[system_name]["success"] else "❌ 실패"
                count = self.results[system_name]["sample_count"]
                print(f"   {status} ({count}개 샘플 수집)")
                
            except Exception as e:
                print(f"   ❌ 실패: {str(e)}")
                self.results[system_name] = {
                    "success": False,
                    "error": str(e),
                    "data": [],
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # 전체 결과 저장
        with open(self.output_dir / "discovery_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str, ensure_ascii=False)
        
        self._print_summary()
        return self.results
    
    async def discover_cloud_run_logs(self) -> List[Dict[str, Any]]:
        """Google Cloud Run 로그 응답 형식 탐색"""
        
        if not GOOGLE_CLOUD_AVAILABLE:
            print("   ⚠️  Google Cloud 라이브러리가 없어 건너뜁니다.")
            return []
        
        try:
            # Service Account 인증
            credentials_path = "/home/nadle/projects/Xai_Community/v5/.secrets/service-account-key.json"
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Service Account 파일을 찾을 수 없습니다: {credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = logging_v2.Client(credentials=credentials, project="xai-community")
            
            # 최근 24시간 로그 조회
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            filter_str = f'''
            resource.type="cloud_run_revision"
            resource.labels.service_name="xai-community-backend"
            timestamp >= "{start_time.isoformat()}Z"
            '''
            
            sample_logs = []
            entries = client.list_entries(filter_=filter_str, max_results=10)
            
            for entry in entries:
                # severity 처리 개선
                severity_value = "INFO"
                if hasattr(entry, 'severity') and entry.severity:
                    if hasattr(entry.severity, 'name'):
                        severity_value = entry.severity.name
                    else:
                        severity_value = str(entry.severity)
                
                log_data = {
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                    "severity": severity_value,
                    "insert_id": entry.insert_id,
                    "resource": {
                        "type": entry.resource.type,
                        "labels": dict(entry.resource.labels)
                    },
                    "payload_type": type(entry.payload).__name__,
                    "payload": str(entry.payload),
                    "http_request": self._extract_http_request(entry),
                    "trace": getattr(entry, 'trace', None),
                    "span_id": getattr(entry, 'span_id', None),
                    "source_location": self._extract_source_location(entry),
                    "operation": self._extract_operation(entry),
                    "labels": dict(entry.labels) if entry.labels else {},
                    "receive_timestamp": entry.receive_timestamp.isoformat() if hasattr(entry, 'receive_timestamp') and entry.receive_timestamp else None
                }
                sample_logs.append(log_data)
            
            print(f"   📊 Cloud Run 로그 {len(sample_logs)}개 수집 완료")
            return sample_logs
            
        except Exception as e:
            print(f"   ❌ Cloud Run 로그 수집 실패: {e}")
            raise
    
    async def discover_atlas_logs(self) -> List[Dict[str, Any]]:
        """MongoDB Atlas 로그 응답 형식 탐색"""
        
        try:
            # Atlas API 설정
            public_key = settings.atlas_public_key
            private_key = settings.atlas_private_key
            group_id = settings.atlas_group_id
            cluster_name = settings.atlas_cluster_name
            
            if not all([public_key, private_key, group_id, cluster_name]):
                raise ValueError("Atlas API 설정이 완전하지 않습니다.")
            
            # HTTPDigestAuth 방식으로 변경 (기존 모니터링 시스템과 동일)
            from requests.auth import HTTPDigestAuth
            auth = HTTPDigestAuth(public_key, private_key)
            headers = {
                "Accept": "application/vnd.atlas.2023-01-01+json",
                "Content-Type": "application/json"
            }
            
            sample_logs = []
            
            # HTTPDigestAuth는 requests 라이브러리와 함께 사용해야 함
            import requests
            from urllib.parse import quote
            
            # 먼저 클러스터 정보 확인
            cluster_url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{group_id}/clusters"
            cluster_resp = requests.get(cluster_url, auth=auth, headers=headers, timeout=15)
            
            if cluster_resp.status_code != 200:
                raise Exception(f"클러스터 정보 조회 실패: {cluster_resp.status_code} - {cluster_resp.text}")
            
            clusters = cluster_resp.json()
            print(f"   📊 Atlas 클러스터 {len(clusters.get('results', []))}개 확인")
            
            # 로그 타입별 수집 시도
            log_types = ["mongod", "mongos"]
            end_time = int(datetime.utcnow().timestamp())
            start_time = int((datetime.utcnow() - timedelta(hours=6)).timestamp())
            
            for log_type in log_types:
                try:
                    # URL 인코딩 처리 (클러스터 이름에 공백이 있을 수 있음)
                    encoded_cluster_name = quote(cluster_name, safe='')
                    log_url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{group_id}/clusters/{encoded_cluster_name}/logs/{log_type}.gz"
                    
                    params = {
                        "startDate": start_time,
                        "endDate": end_time
                    }
                    
                    log_resp = requests.get(log_url, auth=auth, headers=headers, params=params, timeout=15)
                    
                    log_sample = {
                        "log_type": log_type,
                        "status_code": log_resp.status_code,
                        "headers": dict(log_resp.headers),
                        "content_length": len(log_resp.content),
                        "is_gzipped": log_resp.headers.get("content-encoding") == "gzip",
                        "start_time": start_time,
                        "end_time": end_time
                    }
                    
                    # 성공한 경우 내용 샘플 추가
                    if log_resp.status_code == 200 and log_resp.content:
                        try:
                            # gzip 압축 해제 시도
                            if log_sample["is_gzipped"]:
                                content = gzip.decompress(log_resp.content).decode('utf-8')
                            else:
                                content = log_resp.text
                            
                            # 처음 몇 줄만 샘플로 저장
                            lines = content.split('\n')[:5]
                            log_sample["sample_lines"] = lines
                            log_sample["total_lines"] = len(content.split('\n'))
                            
                        except Exception as decode_error:
                            log_sample["decode_error"] = str(decode_error)
                            log_sample["raw_content_preview"] = str(log_resp.content[:200])
                    else:
                        log_sample["error_response"] = log_resp.text
                    
                    sample_logs.append(log_sample)
                    print(f"   📊 Atlas {log_type} 로그: {log_resp.status_code}")
                    
                except Exception as log_error:
                    print(f"   ⚠️  Atlas {log_type} 로그 수집 중 오류: {log_error}")
                    sample_logs.append({
                        "log_type": log_type,
                        "error": str(log_error)
                    })
            
            # 액세스 로그도 시도
            try:
                encoded_cluster_name = quote(cluster_name, safe='')
                access_url = f"https://cloud.mongodb.com/api/atlas/v2/groups/{group_id}/dbAccessHistory/clusters/{encoded_cluster_name}"
                access_resp = requests.get(access_url, auth=auth, headers=headers, timeout=15)
                
                access_sample = {
                    "log_type": "access_history",
                    "status_code": access_resp.status_code,
                    "response": access_resp.json() if access_resp.status_code == 200 else access_resp.text
                }
                sample_logs.append(access_sample)
                print(f"   📊 Atlas 액세스 히스토리: {access_resp.status_code}")
                
            except Exception as access_error:
                print(f"   ⚠️  Atlas 액세스 히스토리 수집 중 오류: {access_error}")
            
            return sample_logs
            
        except Exception as e:
            print(f"   ❌ Atlas 로그 수집 실패: {e}")
            raise
    
    async def discover_vercel_logs(self) -> List[Dict[str, Any]]:
        """Vercel 로그 응답 형식 탐색"""
        
        try:
            token = settings.vercel_api_token if hasattr(settings, 'vercel_api_token') else os.getenv('VERCEL_API_TOKEN')
            project_id = settings.vercel_project_id if hasattr(settings, 'vercel_project_id') else os.getenv('VERCEL_PROJECT_ID')
            
            if not token or not project_id:
                raise ValueError("Vercel API 토큰 또는 프로젝트 ID가 설정되지 않았습니다.")
            
            headers = {"Authorization": f"Bearer {token}"}
            sample_logs = []
            
            async with httpx.AsyncClient() as client:
                # 최근 배포 목록 조회
                deployments_url = f"https://api.vercel.com/v6/deployments"
                params = {"projectId": project_id, "limit": 5}
                
                deployments_resp = await client.get(deployments_url, headers=headers, params=params)
                
                if deployments_resp.status_code != 200:
                    raise Exception(f"배포 목록 조회 실패: {deployments_resp.status_code} - {deployments_resp.text}")
                
                deployments_data = deployments_resp.json()
                deployments = deployments_data.get("deployments", [])
                
                print(f"   📊 Vercel 최근 배포 {len(deployments)}개 확인")
                
                for i, deployment in enumerate(deployments[:3]):  # 최근 3개 배포만
                    deployment_id = deployment["uid"]
                    
                    # 배포 이벤트 로그 조회
                    events_url = f"https://api.vercel.com/v2/deployments/{deployment_id}/events"
                    events_resp = await client.get(events_url, headers=headers)
                    
                    deployment_sample = {
                        "deployment_info": {
                            "uid": deployment.get("uid"),
                            "name": deployment.get("name"),
                            "url": deployment.get("url"),
                            "state": deployment.get("state"),
                            "type": deployment.get("type"),
                            "target": deployment.get("target"),
                            "created": deployment.get("created"),
                            "creator": deployment.get("creator", {}).get("username"),
                            "meta": deployment.get("meta", {})
                        },
                        "events": {
                            "status_code": events_resp.status_code,
                            "data": events_resp.json() if events_resp.status_code == 200 else events_resp.text,
                            "event_count": len(events_resp.json()) if events_resp.status_code == 200 and isinstance(events_resp.json(), list) else 0
                        }
                    }
                    
                    sample_logs.append(deployment_sample)
                    print(f"   📊 배포 {i+1}: {deployment_sample['events']['event_count']}개 이벤트")
                
                # 프로젝트 정보도 수집
                project_url = f"https://api.vercel.com/v9/projects/{project_id}"
                project_resp = await client.get(project_url, headers=headers)
                
                if project_resp.status_code == 200:
                    project_info = {
                        "project_info": project_resp.json(),
                        "status_code": project_resp.status_code
                    }
                    sample_logs.append(project_info)
                    print(f"   📊 프로젝트 정보 수집 완료")
            
            return sample_logs
            
        except Exception as e:
            print(f"   ❌ Vercel 로그 수집 실패: {e}")
            raise
    
    async def discover_upstash_metrics(self) -> List[Dict[str, Any]]:
        """Upstash Redis 메트릭 응답 형식 탐색"""
        
        try:
            rest_url = settings.upstash_redis_rest_url
            rest_token = settings.upstash_redis_rest_token
            
            if not rest_url or not rest_token:
                raise ValueError("Upstash Redis 설정이 완전하지 않습니다.")
            
            headers = {"Authorization": f"Bearer {rest_token}"}
            sample_data = []
            
            async with httpx.AsyncClient() as client:
                # 기본 Redis 명령어들로 상태 확인
                commands = [
                    {"cmd": "ping", "url": f"{rest_url}/ping"},
                    {"cmd": "info", "url": f"{rest_url}/info"},
                    {"cmd": "dbsize", "url": f"{rest_url}/dbsize"},
                    {"cmd": "memory_usage_key", "url": f"{rest_url}/memory/usage/*"}  # 모든 키의 메모리 사용량
                ]
                
                for cmd_info in commands:
                    try:
                        response = await client.post(cmd_info["url"], headers=headers)
                        
                        sample = {
                            "command": cmd_info["cmd"],
                            "url": cmd_info["url"],
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "response_raw": response.text,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # JSON 파싱 시도
                        try:
                            sample["response_json"] = response.json()
                        except:
                            sample["response_text"] = response.text
                        
                        sample_data.append(sample)
                        print(f"   📊 Upstash {cmd_info['cmd']}: {response.status_code}")
                        
                    except Exception as cmd_error:
                        print(f"   ⚠️  Upstash {cmd_info['cmd']} 실행 중 오류: {cmd_error}")
                        sample_data.append({
                            "command": cmd_info["cmd"],
                            "error": str(cmd_error)
                        })
                
                # 추가로 일부 키 조회 시도
                try:
                    # 캐시 키 패턴으로 조회
                    keys_response = await client.post(f"{rest_url}/keys/cache:*", headers=headers)
                    sample_data.append({
                        "command": "keys_cache_pattern",
                        "status_code": keys_response.status_code,
                        "response": keys_response.json() if keys_response.status_code == 200 else keys_response.text
                    })
                    print(f"   📊 Upstash 캐시 키 패턴: {keys_response.status_code}")
                    
                except Exception as keys_error:
                    print(f"   ⚠️  Upstash 키 조회 중 오류: {keys_error}")
            
            return sample_data
            
        except Exception as e:
            print(f"   ❌ Upstash 메트릭 수집 실패: {e}")
            raise
    
    def _extract_http_request(self, entry) -> Optional[Dict[str, Any]]:
        """로그 엔트리에서 HTTP 요청 정보 추출"""
        if hasattr(entry, 'http_request') and entry.http_request:
            http_req = entry.http_request
            return {
                "request_method": getattr(http_req, 'request_method', None),
                "request_url": getattr(http_req, 'request_url', None),
                "request_size": getattr(http_req, 'request_size', None),
                "status": getattr(http_req, 'status', None),
                "response_size": getattr(http_req, 'response_size', None),
                "user_agent": getattr(http_req, 'user_agent', None),
                "remote_ip": getattr(http_req, 'remote_ip', None),
                "server_ip": getattr(http_req, 'server_ip', None),
                "referer": getattr(http_req, 'referer', None),
                "latency": str(getattr(http_req, 'latency', None)),
                "cache_lookup": getattr(http_req, 'cache_lookup', None),
                "cache_hit": getattr(http_req, 'cache_hit', None)
            }
        return None
    
    def _extract_source_location(self, entry) -> Optional[Dict[str, Any]]:
        """로그 엔트리에서 소스 위치 정보 추출"""
        if hasattr(entry, 'source_location') and entry.source_location:
            source_loc = entry.source_location
            return {
                "file": getattr(source_loc, 'file', None),
                "line": getattr(source_loc, 'line', None),
                "function": getattr(source_loc, 'function', None)
            }
        return None
    
    def _extract_operation(self, entry) -> Optional[Dict[str, Any]]:
        """로그 엔트리에서 오퍼레이션 정보 추출"""
        if hasattr(entry, 'operation') and entry.operation:
            operation = entry.operation
            return {
                "id": getattr(operation, 'id', None),
                "producer": getattr(operation, 'producer', None),
                "first": getattr(operation, 'first', None),
                "last": getattr(operation, 'last', None)
            }
        return None
    
    def _print_summary(self):
        """탐색 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 API 응답 탐색 결과 요약")
        print("=" * 60)
        
        total_success = 0
        total_samples = 0
        
        for system, result in self.results.items():
            status = "✅ 성공" if result["success"] else "❌ 실패"
            count = result.get("sample_count", 0)
            error = result.get("error", "")
            
            print(f"{system.upper():>12}: {status} ({count}개 샘플)")
            if error:
                print(f"              오류: {error}")
            
            if result["success"]:
                total_success += 1
                total_samples += count
        
        print("-" * 60)
        print(f"전체 결과: {total_success}/{len(self.results)}개 시스템 성공, 총 {total_samples}개 샘플 수집")
        print(f"저장 위치: {self.output_dir}")
        print("=" * 60)


async def main():
    """메인 실행 함수"""
    
    print("🔍 외부 시스템 API 응답 탐색 도구")
    print("=" * 60)
    print("이 스크립트는 실제 외부 인프라 API를 호출하여")
    print("응답 형식을 수집하고 Mock 데이터 생성을 위한")
    print("기반 데이터를 제공합니다.")
    print("=" * 60)
    
    # 환경 확인
    print("\n🔧 환경 설정 확인 중...")
    
    # 필요한 환경변수들 체크
    required_settings = [
        ("MongoDB Atlas", ["atlas_public_key", "atlas_private_key", "atlas_group_id"]),
        ("Upstash Redis", ["upstash_redis_rest_url", "upstash_redis_rest_token"]),
    ]
    
    for service, setting_names in required_settings:
        missing = [name for name in setting_names if not hasattr(settings, name) or not getattr(settings, name)]
        if missing:
            print(f"   ⚠️  {service}: 누락된 설정 - {', '.join(missing)}")
        else:
            print(f"   ✅ {service}: 설정 완료")
    
    # GCP 서비스 계정 확인
    gcp_credentials_path = "/home/nadle/projects/Xai_Community/v5/.secrets/service-account-key.json"
    if os.path.exists(gcp_credentials_path):
        print(f"   ✅ Google Cloud: Service Account 파일 확인")
    else:
        print(f"   ⚠️  Google Cloud: Service Account 파일 없음 - {gcp_credentials_path}")
    
    print("\n▶️  API 탐색을 시작합니다...")
    
    # API 응답 탐색 실행
    discovery = APIResponseDiscovery()
    results = await discovery.discover_all()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())