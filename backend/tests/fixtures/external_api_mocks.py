"""
실제 API 응답 기반 Mock 데이터

이 파일은 실제 외부 시스템 API 응답을 기반으로 생성된 Mock 데이터를 제공합니다.
2025-07-19에 실제 API를 호출하여 수집된 응답 구조를 따릅니다.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List


class VercelMockData:
    """Vercel API Mock 데이터 (실제 응답 기반)"""
    
    @staticmethod
    def get_deployment_list() -> Dict[str, Any]:
        """배포 목록 API 응답 Mock"""
        return {
            "deployments": [
                {
                    "uid": "dpl_mock_deployment_001",
                    "name": "xai-community",
                    "url": "xai-community-mock-deployment.vercel.app",
                    "state": "READY",
                    "type": "LAMBDAS",
                    "target": None,
                    "created": int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000),
                    "creator": "mock-user",
                    "meta": {
                        "githubCommitAuthorName": "nadle",
                        "githubCommitAuthorEmail": "nadle@go-getter.com",
                        "githubCommitMessage": "feat: 로깅 시스템 TDD 구현 완료\\n\\n🤖 Generated with [Claude Code](https://claude.ai/code)",
                        "githubCommitOrg": "keepselvesreal",
                        "githubCommitRef": "staging",
                        "githubCommitRepo": "Xai_Community",
                        "githubCommitSha": "abc123def456",
                        "githubDeployment": "1",
                        "githubOrg": "keepselvesreal",
                        "githubRepo": "Xai_Community",
                        "githubRepoOwnerType": "User",
                        "githubCommitRepoId": "1014067188",
                        "githubRepoId": "1014067188",
                        "githubRepoVisibility": "public",
                        "githubHost": "github.com",
                        "branchAlias": "xai-community-git-staging-mock.vercel.app"
                    }
                },
                {
                    "uid": "dpl_mock_deployment_002",
                    "name": "xai-community",
                    "url": "xai-community-mock-prev.vercel.app",
                    "state": "ERROR",
                    "type": "LAMBDAS",
                    "target": None,
                    "created": int((datetime.utcnow() - timedelta(hours=3)).timestamp() * 1000),
                    "creator": "mock-user",
                    "meta": {
                        "githubCommitAuthorName": "nadle",
                        "githubCommitMessage": "fix: 빌드 오류 수정 시도",
                        "githubCommitRef": "staging",
                        "githubCommitSha": "def456ghi789"
                    }
                }
            ],
            "pagination": {
                "count": 2,
                "next": None,
                "prev": None
            }
        }
    
    @staticmethod
    def get_deployment_events(deployment_id: str, event_count: int = 5) -> List[Dict[str, Any]]:
        """배포 이벤트 로그 Mock"""
        base_time = int(datetime.utcnow().timestamp() * 1000)
        
        events = []
        
        # 빌드 시작 이벤트
        events.append({
            "type": "stdout",
            "created": base_time - 300000,  # 5분 전
            "payload": {
                "deploymentId": deployment_id,
                "info": {
                    "type": "build",
                    "name": "bld_mock_build_001",
                    "entrypoint": "."
                },
                "text": "Running build in Washington, D.C., USA (East) – iad1",
                "id": f"{base_time}987253780600000",
                "date": base_time - 300000,
                "serial": f"{base_time}987253780600000"
            }
        })
        
        # 의존성 설치 이벤트
        events.append({
            "type": "stdout", 
            "created": base_time - 250000,
            "payload": {
                "deploymentId": deployment_id,
                "info": {
                    "type": "build",
                    "name": "bld_mock_build_001",
                    "entrypoint": "."
                },
                "text": "Installing dependencies...",
                "id": f"{base_time}987253780600001",
                "date": base_time - 250000,
                "serial": f"{base_time}987253780600001"
            }
        })
        
        # 빌드 완료 이벤트
        events.append({
            "type": "stdout",
            "created": base_time - 100000,
            "payload": {
                "deploymentId": deployment_id,
                "info": {
                    "type": "build",
                    "name": "bld_mock_build_001",
                    "entrypoint": "."
                },
                "text": "Build completed successfully",
                "id": f"{base_time}987253780600002",
                "date": base_time - 100000,
                "serial": f"{base_time}987253780600002"
            }
        })
        
        # 배포 완료 이벤트
        events.append({
            "type": "ready",
            "created": base_time - 50000,
            "payload": {
                "deploymentId": deployment_id,
                "text": "Deployment ready",
                "id": f"{base_time}987253780600003",
                "date": base_time - 50000,
                "serial": f"{base_time}987253780600003"
            }
        })
        
        # 에러 이벤트 (실패한 배포의 경우)
        if "error" in deployment_id:
            events.append({
                "type": "stderr",
                "created": base_time - 80000,
                "payload": {
                    "deploymentId": deployment_id,
                    "info": {
                        "type": "build",
                        "name": "bld_mock_build_001",
                        "entrypoint": "."
                    },
                    "text": "Error: Module not found: lucide-react",
                    "id": f"{base_time}987253780600004",
                    "date": base_time - 80000,
                    "serial": f"{base_time}987253780600004"
                }
            })
        
        return events[:event_count]
    
    @staticmethod
    def get_project_info() -> Dict[str, Any]:
        """프로젝트 정보 Mock"""
        return {
            "id": "prj_mock_project_id",
            "name": "xai-community",
            "accountId": "mock_account_id",
            "createdAt": 1640995200000,
            "updatedAt": int(datetime.utcnow().timestamp() * 1000),
            "framework": "remix",
            "devCommand": "npm run dev",
            "buildCommand": "npm run build",
            "outputDirectory": "build",
            "rootDirectory": "frontend",
            "directoryListing": False,
            "env": [],
            "settings": {},
            "link": {
                "type": "github",
                "repo": "keepselvesreal/Xai_Community",
                "org": "keepselvesreal",
                "repoId": 1014067188,
                "gitBranch": "staging"
            },
            "targets": {
                "production": {
                    "domain": "xai-community.vercel.app",
                    "alias": ["xai-community.vercel.app"]
                }
            }
        }


class UpstashMockData:
    """Upstash Redis API Mock 데이터 (실제 응답 기반)"""
    
    @staticmethod
    def get_ping_response() -> Dict[str, Any]:
        """PING 명령 응답 Mock"""
        return {
            "result": "PONG"
        }
    
    @staticmethod
    def get_info_response() -> Dict[str, Any]:
        """INFO 명령 응답 Mock"""
        info_text = (
            "# Server\\r\\n"
            "upstash_version:1.13.3\\r\\n"
            "redis_version:6.2.6\\r\\n"
            "redis_git_sha1:b8ef06c\\r\\n"
            "redis_build_id:20250422\\r\\n"
            "redis_mode:standalone\\r\\n"
            "\\r\\n"
            "# Clients\\r\\n"
            "connected_clients:1\\r\\n"
            "maxclients:10000\\r\\n"
            "\\r\\n"
            "# Memory\\r\\n"
            "used_memory:1024\\r\\n"
            "used_memory_human:1.000KB\\r\\n"
            "maxmemory:67108864\\r\\n"
            "maxmemory_human:64.000MB\\r\\n"
            "maxmemory_policy:noeviction\\r\\n"
            "\\r\\n"
            "# Persistence\\r\\n"
            "total_keys:15\\r\\n"
            "total_data_size:2048\\r\\n"
            "total_data_size_human:2.000KB\\r\\n"
            "max_data_size:268435456\\r\\n"
            "max_data_size_human:256.000MB\\r\\n"
            "\\r\\n"
            "# Stats\\r\\n"
            "total_connections_received:50\\r\\n"
            "total_commands_processed:1500\\r\\n"
            "instantaneous_ops_per_sec:5\\r\\n"
            "max_ops_per_sec:10000\\r\\n"
            "evicted_clients:0\\r\\n"
            "expired_keys:3\\r\\n"
            "evicted_keys:0\\r\\n"
            "keyspace_hits:350\\r\\n"
            "keyspace_misses:85\\r\\n"
            "total_reads_processed:800\\r\\n"
            "total_writes_processed:200\\r\\n"
            "\\r\\n"
            "# Keyspace\\r\\n"
            "db0:keys=15,expires=5,avg_ttl=3600\\r\\n"
            "\\r\\n"
            "# Cluster\\r\\n"
            "cluster_enabled:0\\r\\n"
            "local_member:10.16.8.4\\r\\n"
            "primary_member:10.16.8.4\\r\\n"
        )
        return {
            "result": info_text
        }
    
    @staticmethod
    def get_dbsize_response() -> Dict[str, Any]:
        """DBSIZE 명령 응답 Mock"""
        return {
            "result": 15
        }
    
    @staticmethod
    def get_memory_usage_response(key: str = "*") -> Dict[str, Any]:
        """MEMORY USAGE 명령 응답 Mock"""
        if key == "*":
            return {
                "result": None  # 와일드카드는 지원하지 않음
            }
        else:
            return {
                "result": 256  # 특정 키의 메모리 사용량 (bytes)
            }
    
    @staticmethod
    def get_keys_pattern_response(pattern: str = "cache:*") -> Dict[str, Any]:
        """KEYS 패턴 명령 응답 Mock"""
        if pattern == "cache:*":
            return {
                "result": [
                    "cache:user:123",
                    "cache:post:456", 
                    "cache:session:789",
                    "cache:stats:daily"
                ]
            }
        elif pattern == "session:*":
            return {
                "result": [
                    "session:user_123_token_abc",
                    "session:user_456_token_def"
                ]
            }
        else:
            return {
                "result": []
            }
    
    @staticmethod
    def get_command_error_response(error_msg: str) -> Dict[str, Any]:
        """명령 에러 응답 Mock"""
        return {
            "error": error_msg
        }


class CloudRunMockData:
    """Google Cloud Run 로그 Mock 데이터 (실제 API 응답 기반)"""
    
    @staticmethod
    def get_log_entries() -> List[Dict[str, Any]]:
        """Cloud Run 로그 엔트리 Mock (실제 수집된 구조 기반)"""
        base_time = datetime.utcnow()
        
        return [
            {
                "timestamp": (base_time - timedelta(minutes=5)).isoformat() + "+00:00",
                "severity": "INFO",
                "insert_id": "6879b1ba000b2fa7f34c88e7",
                "resource": {
                    "type": "cloud_run_revision",
                    "labels": {
                        "revision_name": "xai-community-backend-00010-kb7",
                        "configuration_name": "xai-community-backend",
                        "service_name": "xai-community-backend",
                        "project_id": "xai-community",
                        "location": "asia-northeast3"
                    }
                },
                "payload_type": "str",
                "payload": "Application started successfully on port 8080",
                "http_request": {
                    "request_method": "GET",
                    "request_url": "https://xai-community-backend-123456789-xx.a.run.app/health",
                    "request_size": 0,
                    "status": 200,
                    "response_size": 45,
                    "user_agent": "GoogleHC/1.0",
                    "remote_ip": "169.254.1.1",
                    "server_ip": "10.4.0.1",
                    "referer": None,
                    "latency": "25ms",
                    "cache_lookup": False,
                    "cache_hit": False
                },
                "trace": "projects/xai-community/traces/c4a91ba24e09ea503af1625359e2e8db",
                "span_id": "02e9a71872c63c08",
                "source_location": None,
                "operation": None,
                "labels": {
                    "instanceId": "0069c7a98871a594bc6b2d445f662d1f3a561e217d7a17ca6930d70b90c95c1cae77525436fb0712589f9160720caeefe1a473f86f02344681da1c9510ba81051c66d0eb1966ddb7432729f087c362a871ce"
                },
                "receive_timestamp": None
            },
            {
                "timestamp": (base_time - timedelta(minutes=3)).isoformat() + "+00:00",
                "severity": "ERROR",
                "insert_id": "6879b1ba000b2cd465a9da98",
                "resource": {
                    "type": "cloud_run_revision",
                    "labels": {
                        "revision_name": "xai-community-backend-00010-kb7",
                        "configuration_name": "xai-community-backend",
                        "service_name": "xai-community-backend",
                        "project_id": "xai-community",
                        "location": "asia-northeast3"
                    }
                },
                "payload_type": "str",
                "payload": "Database connection timeout after 30 seconds",
                "http_request": {
                    "request_method": "POST",
                    "request_url": "https://xai-community-backend-123456789-xx.a.run.app/api/posts",
                    "request_size": 1024,
                    "status": 500,
                    "response_size": 128,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "remote_ip": "203.0.113.1",
                    "server_ip": "10.4.0.1",
                    "referer": "https://xai-community.vercel.app",
                    "latency": "30125ms",
                    "cache_lookup": False,
                    "cache_hit": False
                },
                "trace": "projects/xai-community/traces/d5b82ca35f1afb614bf2636468f3f9ec",
                "span_id": "15fa8e2983d74d09",
                "source_location": {
                    "file": "/app/nadle_backend/services/posts_service.py",
                    "line": 45,
                    "function": "create_post"
                },
                "operation": {
                    "id": "operation_001",
                    "producer": "cloud-run-service",
                    "first": True,
                    "last": True
                },
                "labels": {
                    "instanceId": "0069c7a98871a594bc6b2d445f662d1f3a561e217d7a17ca6930d70b90c95c1cae77525436fb0712589f9160720caeefe1a473f86f02344681da1c9510ba81051c66d0eb1966ddb7432729f087c362a871ce",
                    "error_type": "database_timeout"
                },
                "receive_timestamp": None
            }
        ]


class AtlasMockData:
    """MongoDB Atlas 로그 Mock 데이터 (예상 구조)"""
    
    @staticmethod
    def get_mongod_logs() -> List[str]:
        """mongod 로그 라인 Mock"""
        return [
            '{"t":{"$date":"2025-07-19T02:00:00.000+00:00"},"s":"I","c":"NETWORK","id":22943,"ctx":"listener","msg":"Connection accepted","attr":{"remote":"203.0.113.1:54321","uuid":"12345678-1234-5678-9012-123456789abc","connectionId":123,"connectionCount":5}}',
            '{"t":{"$date":"2025-07-19T02:00:01.500+00:00"},"s":"I","c":"COMMAND","id":51803,"ctx":"conn123","msg":"Slow query","attr":{"type":"command","ns":"xai_community.posts","command":{"find":"posts","filter":{"status":"published"},"sort":{"created_at":-1},"limit":20},"planSummary":"IXSCAN { status: 1, created_at: -1 }","durationMillis":1250}}',
            '{"t":{"$date":"2025-07-19T02:00:05.000+00:00"},"s":"E","c":"STORAGE","id":28551,"ctx":"conn123","msg":"WiredTiger error","attr":{"error":"cache eviction stalled due to too many requests: Operation timed out","file":"WT_SESSION.checkpoint","line":123}}',
            '{"t":{"$date":"2025-07-19T02:01:00.000+00:00"},"s":"I","c":"INDEX","id":20345,"ctx":"IndexBuildsCoordinatorMongod-0","msg":"Index build completed","attr":{"buildUUID":"87654321-4321-8765-4321-876543210fed","namespace":"xai_community.posts","index":"status_1_created_at_-1","commitTimestamp":"1752822060"}}'
        ]
    
    @staticmethod
    def get_mongos_logs() -> List[str]:
        """mongos 로그 라인 Mock (클러스터용)"""
        return [
            '{"t":{"$date":"2025-07-19T02:00:00.000+00:00"},"s":"I","c":"SHARDING","id":22070,"ctx":"conn456","msg":"Request targeting","attr":{"command":{"find":"posts","filter":{"user_id":"user123"}},"clientInfo":{"application":"node.js driver","driver":"Node.js|4.5.0"},"targetedShards":["shard01"]}}',
            '{"t":{"$date":"2025-07-19T02:00:02.000+00:00"},"s":"W","c":"NETWORK","id":22944,"ctx":"conn456","msg":"Connection ended","attr":{"remote":"203.0.113.1:54321","connectionId":456,"reason":"client disconnected"}}'
        ]
    
    @staticmethod
    def get_audit_logs() -> List[str]:
        """감사 로그 Mock"""
        return [
            '{"atype":"authenticate","ts":{"$date":"2025-07-19T02:00:00.000+00:00"},"local":{"ip":"10.0.0.1","port":27017},"remote":{"ip":"203.0.113.1","port":54321},"users":[{"user":"app_user","db":"xai_community"}],"roles":[{"role":"readWrite","db":"xai_community"}],"result":0}',
            '{"atype":"createCollection","ts":{"$date":"2025-07-19T02:05:00.000+00:00"},"local":{"ip":"10.0.0.1","port":27017},"remote":{"ip":"203.0.113.1","port":54321},"users":[{"user":"admin_user","db":"admin"}],"roles":[{"role":"dbAdminAnyDatabase","db":"admin"}],"param":{"ns":"xai_community.logs"},"result":0}',
            '{"atype":"dropCollection","ts":{"$date":"2025-07-19T02:10:00.000+00:00"},"local":{"ip":"10.0.0.1","port":27017},"remote":{"ip":"203.0.113.1","port":54321},"users":[{"user":"admin_user","db":"admin"}],"roles":[{"role":"dbAdminAnyDatabase","db":"admin"}],"param":{"ns":"xai_community.temp_collection"},"result":0}'
        ]
    
    @staticmethod
    def get_access_history() -> Dict[str, Any]:
        """데이터베이스 액세스 히스토리 Mock (실제 API 응답 기반)"""
        # 실제 수집된 응답은 빈 배열이었지만, 예상되는 구조로 Mock 데이터 제공
        return {
            "accessLogs": [
                {
                    "authSource": "xai_community",
                    "authResult": True,
                    "hostname": "cluster0-shard-00-01.bh7mhfi.mongodb.net",
                    "ipAddress": "218.154.40.110",  # 실제 서버 IP 반영
                    "logLevel": "INFO",
                    "timestamp": "2025-07-19T02:00:00.000Z",
                    "username": "nadle"  # 실제 사용자명 반영
                },
                {
                    "authSource": "admin",
                    "authResult": False,
                    "hostname": "cluster0-shard-00-01.bh7mhfi.mongodb.net",
                    "ipAddress": "198.51.100.1",
                    "logLevel": "WARN",
                    "timestamp": "2025-07-19T01:55:00.000Z",
                    "username": "unknown_user",
                    "failureReason": "Authentication failed"
                }
            ],
            "totalCount": 2
        }
    
    @staticmethod
    def get_logs_api_error_response() -> Dict[str, Any]:
        """mongod/mongos 로그 406 오류 응답 (실제 수집됨)"""
        return {
            "detail": "The Atlas Administration API doesn't support media-type json. Please use: gzip.",
            "error": 406,
            "errorCode": "MEDIA_TYPE_NOT_SUPPORTED_FOR_VERSION",
            "parameters": ["json", "gzip"],
            "reason": "Not Acceptable"
        }


def get_mock_http_headers() -> Dict[str, str]:
    """공통 HTTP 헤더 Mock"""
    return {
        "content-type": "application/json; charset=utf-8",
        "date": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "server": "Mock-Server/1.0.0",
        "access-control-allow-credentials": "true",
        "access-control-allow-origin": "*"
    }


def get_mock_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """에러 응답 Mock"""
    error_responses = {
        400: {"error": "Bad Request", "message": message},
        401: {"error": "Unauthorized", "message": message},
        403: {"error": "Forbidden", "message": message},
        404: {"error": "Not Found", "message": message},
        429: {"error": "Too Many Requests", "message": message},
        500: {"error": "Internal Server Error", "message": message},
        502: {"error": "Bad Gateway", "message": message},
        503: {"error": "Service Unavailable", "message": message}
    }
    
    return error_responses.get(status_code, {
        "error": f"HTTP {status_code}",
        "message": message
    })


# 편의 함수들
def get_vercel_deployment_mock(deployment_id: str = "dpl_mock_001") -> Dict[str, Any]:
    """단일 Vercel 배포 Mock 데이터"""
    deployments = VercelMockData.get_deployment_list()["deployments"]
    return next((d for d in deployments if d["uid"] == deployment_id), deployments[0])


def get_vercel_events_mock(deployment_id: str = "dpl_mock_001", count: int = 5) -> List[Dict[str, Any]]:
    """Vercel 이벤트 Mock 데이터"""
    return VercelMockData.get_deployment_events(deployment_id, count)


def get_upstash_mock_response(command: str, *args) -> Dict[str, Any]:
    """Upstash 명령별 Mock 응답"""
    if command.lower() == "ping":
        return UpstashMockData.get_ping_response()
    elif command.lower() == "info":
        return UpstashMockData.get_info_response()
    elif command.lower() == "dbsize":
        return UpstashMockData.get_dbsize_response()
    elif command.lower() == "memory" and args and args[0] == "usage":
        key = args[1] if len(args) > 1 else "*"
        return UpstashMockData.get_memory_usage_response(key)
    elif command.lower() == "keys":
        pattern = args[0] if args else "*"
        return UpstashMockData.get_keys_pattern_response(pattern)
    else:
        return UpstashMockData.get_command_error_response(f"Unknown command: {command}")


if __name__ == "__main__":
    # Mock 데이터 테스트
    print("=== Vercel Mock 데이터 테스트 ===")
    deployments = VercelMockData.get_deployment_list()
    print(f"배포 개수: {len(deployments['deployments'])}")
    
    events = VercelMockData.get_deployment_events("dpl_test")
    print(f"이벤트 개수: {len(events)}")
    
    print("\\n=== Upstash Mock 데이터 테스트 ===")
    ping = UpstashMockData.get_ping_response()
    print(f"PING 응답: {ping}")
    
    info = UpstashMockData.get_info_response()
    print(f"INFO 응답 길이: {len(info['result'])} 문자")
    
    print("\\n=== Mock 데이터 검증 완료 ===")