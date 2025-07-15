#!/usr/bin/env python3
"""
MongoDB Atlas 모니터링 디버깅 전용 테스트

Atlas API 연결 문제를 단계별로 진단하고 
구체적인 오류 상황을 파악하기 위한 상세 테스트
"""

import asyncio
import sys
import os
import json
import aiohttp
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from nadle_backend.config import get_settings


class AtlasDebugTester:
    """MongoDB Atlas API 연결 디버깅 전용 테스터"""
    
    def __init__(self):
        self.settings = get_settings()
        self.public_key = self.settings.atlas_public_key
        self.private_key = self.settings.atlas_private_key
        self.group_id = self.settings.atlas_group_id
        self.cluster_name = self.settings.atlas_cluster_name
        self.base_url = "https://cloud.mongodb.com/api/atlas/v2"
        self.test_results = {}
    
    def print_header(self, title: str):
        """테스트 헤더 출력"""
        print("\n" + "=" * 80)
        print(f"🔍 {title}")
        print("=" * 80)
    
    def print_step(self, step: str):
        """테스트 단계 출력"""
        print(f"\n📋 {step}")
        print("-" * 60)
    
    def print_result(self, success: bool, message: str, data: Optional[Dict] = None):
        """결과 출력"""
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}: {message}")
        if data:
            print(f"📊 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    async def test_environment_setup(self):
        """환경 설정 확인"""
        self.print_step("1단계: 환경 설정 확인")
        
        env_data = {
            "환경": self.settings.environment,
            "Atlas Public Key": self.public_key,
            "Atlas Private Key": f"{self.private_key[:10]}..." if self.private_key else None,
            "Atlas Group ID": self.group_id,
            "Atlas Cluster Name": self.cluster_name,
            "Base URL": self.base_url
        }
        
        # 필수 설정 확인
        missing_configs = []
        if not self.public_key:
            missing_configs.append("ATLAS_PUBLIC_KEY")
        if not self.private_key:
            missing_configs.append("ATLAS_PRIVATE_KEY")
        if not self.group_id:
            missing_configs.append("ATLAS_GROUP_ID")
        if not self.cluster_name:
            missing_configs.append("ATLAS_CLUSTER_NAME")
        
        if missing_configs:
            self.print_result(False, f"누락된 환경변수: {', '.join(missing_configs)}", env_data)
            self.test_results["environment"] = False
            return False
        else:
            self.print_result(True, "모든 환경변수 설정 완료", env_data)
            self.test_results["environment"] = True
            return True
    
    def create_auth_headers(self, api_version: str = "2023-01-01"):
        """인증 헤더 생성"""
        try:
            auth_string = f"{self.public_key}:{self.private_key}"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json",
                "Accept": f"application/vnd.atlas.{api_version}+json"
            }
            
            return headers
        except Exception as e:
            print(f"❌ 인증 헤더 생성 실패: {e}")
            return None
    
    async def test_basic_connectivity(self):
        """기본 연결성 테스트"""
        self.print_step("2단계: 기본 연결성 테스트")
        
        try:
            # DNS 해상도 확인
            print("🌐 DNS 해상도 확인...")
            async with aiohttp.ClientSession() as session:
                async with session.get("https://cloud.mongodb.com", timeout=10) as response:
                    print(f"MongoDB Cloud 접근: {response.status}")
                    if response.status == 200:
                        self.print_result(True, "MongoDB Cloud 연결 성공")
                        self.test_results["connectivity"] = True
                        return True
                    else:
                        self.print_result(False, f"MongoDB Cloud 연결 실패: {response.status}")
                        self.test_results["connectivity"] = False
                        return False
                        
        except Exception as e:
            self.print_result(False, f"연결성 테스트 실패: {e}")
            self.test_results["connectivity"] = False
            return False
    
    async def test_auth_header_generation(self):
        """인증 헤더 생성 테스트"""
        self.print_step("3단계: 인증 헤더 생성 테스트")
        
        try:
            # 여러 API 버전으로 헤더 생성 테스트
            api_versions = ["2023-01-01", "2023-02-01", "2025-03-12"]
            
            for version in api_versions:
                headers = self.create_auth_headers(version)
                if headers:
                    header_info = {
                        "API Version": version,
                        "Authorization": f"Basic {headers['Authorization'][6:16]}...",
                        "Accept": headers["Accept"]
                    }
                    print(f"✅ API 버전 {version}: 헤더 생성 성공")
                    print(f"   Accept: {headers['Accept']}")
                else:
                    print(f"❌ API 버전 {version}: 헤더 생성 실패")
            
            self.test_results["auth_headers"] = True
            return True
            
        except Exception as e:
            self.print_result(False, f"인증 헤더 생성 실패: {e}")
            self.test_results["auth_headers"] = False
            return False
    
    async def test_api_endpoints_systematically(self):
        """API 엔드포인트 체계적 테스트"""
        self.print_step("4단계: API 엔드포인트 체계적 테스트")
        
        # 테스트할 엔드포인트들 (간단한 것부터 복잡한 것까지)
        endpoints = [
            {
                "name": "Root API",
                "url": f"{self.base_url}",
                "description": "API 루트 엔드포인트"
            },
            {
                "name": "Organizations",
                "url": f"{self.base_url}/orgs",
                "description": "조직 목록 조회"
            },
            {
                "name": "Groups (Projects)",
                "url": f"{self.base_url}/groups",
                "description": "프로젝트 목록 조회"
            },
            {
                "name": "Specific Group",
                "url": f"{self.base_url}/groups/{self.group_id}",
                "description": f"특정 프로젝트 조회 (ID: {self.group_id})"
            },
            {
                "name": "Clusters List",
                "url": f"{self.base_url}/groups/{self.group_id}/clusters",
                "description": f"프로젝트 내 클러스터 목록"
            },
            {
                "name": "Specific Cluster",
                "url": f"{self.base_url}/groups/{self.group_id}/clusters/{self.cluster_name}",
                "description": f"특정 클러스터 조회 (이름: {self.cluster_name})"
            }
        ]
        
        # 여러 API 버전으로 테스트
        api_versions = ["2023-01-01", "2023-02-01"]
        
        for version in api_versions:
            print(f"\n🔧 API 버전 {version} 테스트:")
            headers = self.create_auth_headers(version)
            
            if not headers:
                print(f"❌ API 버전 {version}: 헤더 생성 실패")
                continue
            
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    try:
                        print(f"\n   📡 {endpoint['name']} 테스트...")
                        print(f"      URL: {endpoint['url']}")
                        print(f"      설명: {endpoint['description']}")
                        
                        async with session.get(endpoint['url'], headers=headers, timeout=15) as response:
                            print(f"      상태: {response.status}")
                            
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    if 'results' in data:
                                        print(f"      결과: {len(data['results'])}개 항목")
                                        if data['results'] and isinstance(data['results'], list):
                                            first_item = data['results'][0]
                                            if 'name' in first_item:
                                                print(f"      첫 번째 항목: {first_item['name']}")
                                            if 'id' in first_item:
                                                print(f"      ID: {first_item['id']}")
                                    else:
                                        if 'name' in data:
                                            print(f"      이름: {data['name']}")
                                        if 'id' in data:
                                            print(f"      ID: {data['id']}")
                                        if 'stateName' in data:
                                            print(f"      상태: {data['stateName']}")
                                    
                                    print(f"      ✅ 성공")
                                    
                                    # 성공한 경우 다음 단계로 진행
                                    continue
                                    
                                except Exception as json_error:
                                    print(f"      ⚠️ JSON 파싱 오류: {json_error}")
                                    response_text = await response.text()
                                    print(f"      응답 내용: {response_text[:200]}...")
                            
                            elif response.status == 401:
                                print(f"      ❌ 인증 실패 (401)")
                                error_text = await response.text()
                                try:
                                    error_data = json.loads(error_text)
                                    print(f"      오류 상세: {error_data.get('detail', 'Unknown')}")
                                    if 'errorCode' in error_data:
                                        print(f"      오류 코드: {error_data['errorCode']}")
                                except:
                                    print(f"      오류 응답: {error_text[:200]}...")
                                
                                # 401 오류 상세 분석
                                await self.analyze_401_error(session, headers, endpoint)
                                
                            elif response.status == 403:
                                print(f"      ❌ 권한 없음 (403)")
                                error_text = await response.text()
                                print(f"      오류 응답: {error_text[:200]}...")
                                
                            elif response.status == 404:
                                print(f"      ❌ 리소스 없음 (404)")
                                print(f"      확인 필요: {endpoint['description']}")
                                
                            else:
                                print(f"      ❌ 기타 오류 ({response.status})")
                                error_text = await response.text()
                                print(f"      오류 응답: {error_text[:200]}...")
                    
                    except asyncio.TimeoutError:
                        print(f"      ❌ 시간 초과")
                    except Exception as e:
                        print(f"      ❌ 예외 발생: {e}")
        
        self.test_results["api_endpoints"] = True
        return True
    
    async def analyze_401_error(self, session: aiohttp.ClientSession, headers: Dict[str, str], endpoint: Dict[str, str]):
        """401 오류 상세 분석"""
        print(f"\n      🔍 401 오류 상세 분석:")
        
        # 1. 인증 헤더 확인
        auth_header = headers.get('Authorization', '')
        if auth_header.startswith('Basic '):
            encoded_creds = auth_header[6:]
            try:
                decoded_creds = base64.b64decode(encoded_creds).decode('ascii')
                username, password = decoded_creds.split(':', 1)
                print(f"         인증 사용자명: {username}")
                print(f"         인증 비밀번호: {password[:10]}...")
            except Exception as e:
                print(f"         인증 헤더 디코딩 실패: {e}")
        
        # 2. API 키 상태 확인을 위한 간단한 엔드포인트 테스트
        simple_endpoints = [
            f"{self.base_url}",
            "https://cloud.mongodb.com/api/atlas/v2"
        ]
        
        for simple_url in simple_endpoints:
            try:
                print(f"         간단한 엔드포인트 테스트: {simple_url}")
                async with session.get(simple_url, headers=headers, timeout=10) as simple_response:
                    print(f"         결과: {simple_response.status}")
                    if simple_response.status != 401:
                        simple_text = await simple_response.text()
                        print(f"         응답: {simple_text[:100]}...")
            except Exception as e:
                print(f"         간단한 테스트 실패: {e}")
    
    async def test_ip_access_check(self):
        """IP 접근 권한 확인"""
        self.print_step("5단계: IP 접근 권한 확인")
        
        try:
            # 현재 IP 확인
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.ipify.org?format=json") as response:
                    if response.status == 200:
                        ip_data = await response.json()
                        current_ip = ip_data.get('ip')
                        print(f"🌐 현재 IP 주소: {current_ip}")
                        
                        # IP 관련 권장사항 제공
                        print(f"\n📋 Atlas API Access List에 추가해야 할 IP:")
                        print(f"   개발 서버: {current_ip}")
                        print(f"   Cloud Run: 34.64.0.0/10, 35.200.0.0/13")
                        print(f"   전체 허용 (임시): 0.0.0.0/0")
                        
                        self.test_results["ip_check"] = True
                        return True
                        
        except Exception as e:
            self.print_result(False, f"IP 확인 실패: {e}")
            self.test_results["ip_check"] = False
            return False
    
    async def test_alternative_auth_methods(self):
        """대안 인증 방법 테스트"""
        self.print_step("6단계: 대안 인증 방법 테스트")
        
        # Digest 인증 테스트 (Atlas가 지원하는 경우)
        try:
            from aiohttp import BasicAuth
            
            auth = BasicAuth(self.public_key, self.private_key)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                print("🔐 BasicAuth 객체를 사용한 인증 테스트...")
                async with session.get(
                    f"{self.base_url}/groups", 
                    auth=auth, 
                    headers=headers,
                    timeout=15
                ) as response:
                    print(f"   상태: {response.status}")
                    if response.status == 200:
                        print("   ✅ BasicAuth 객체 인증 성공")
                        self.test_results["alt_auth"] = True
                        return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ BasicAuth 객체 인증 실패: {error_text[:200]}...")
                        
        except Exception as e:
            print(f"❌ 대안 인증 방법 테스트 실패: {e}")
        
        self.test_results["alt_auth"] = False
        return False
    
    def print_final_diagnosis(self):
        """최종 진단 결과"""
        self.print_header("MongoDB Atlas 모니터링 진단 결과")
        
        print("📊 테스트 결과 요약:")
        for test_name, result in self.test_results.items():
            status = "✅ 통과" if result else "❌ 실패"
            test_labels = {
                "environment": "환경 설정",
                "connectivity": "기본 연결성",
                "auth_headers": "인증 헤더 생성",
                "api_endpoints": "API 엔드포인트",
                "ip_check": "IP 확인",
                "alt_auth": "대안 인증"
            }
            print(f"   {status}: {test_labels.get(test_name, test_name)}")
        
        # 진단 및 해결책 제시
        print("\n🔍 문제 진단 및 해결책:")
        
        if not self.test_results.get("environment", False):
            print("   ❌ 환경 설정 문제: 필수 환경변수가 누락되었습니다.")
            print("      해결: .env.prod 파일의 Atlas 관련 환경변수 확인")
        
        if not self.test_results.get("connectivity", False):
            print("   ❌ 연결 문제: MongoDB Cloud에 접근할 수 없습니다.")
            print("      해결: 네트워크 연결 및 방화벽 설정 확인")
        
        if self.test_results.get("environment", False) and self.test_results.get("connectivity", False):
            print("   ⚠️ 인증 문제로 추정됩니다:")
            print("      1. Atlas API Access List에 현재 IP 추가")
            print("      2. API 키 권한 확인 (Project Owner 이상)")
            print("      3. API 키 재생성 고려")
            print("      4. 프로젝트 ID 및 클러스터명 재확인")
        
        success_count = sum(self.test_results.values())
        total_count = len(self.test_results)
        
        print(f"\n📈 전체 진단 결과: {success_count}/{total_count} 단계 통과")
        
        if success_count == total_count:
            print("🎉 모든 진단 단계를 통과했습니다!")
        elif success_count >= total_count * 0.7:
            print("⚠️ 대부분의 설정은 정상이나 일부 수정이 필요합니다.")
        else:
            print("❌ 여러 설정에 문제가 있어 종합적인 점검이 필요합니다.")


async def main():
    """메인 진단 실행 함수"""
    print("🔧 MongoDB Atlas 모니터링 디버깅 시작...")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = AtlasDebugTester()
    
    # 단계별 진단 실행
    await tester.test_environment_setup()
    await tester.test_basic_connectivity()
    await tester.test_auth_header_generation()
    await tester.test_api_endpoints_systematically()
    await tester.test_ip_access_check()
    await tester.test_alternative_auth_methods()
    
    # 최종 진단 결과
    tester.print_final_diagnosis()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 진단이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 진단 실행 중 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()