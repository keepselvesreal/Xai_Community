#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 17:04:00 KST
작업 버전: 통합 테스트 프레임워크 기본 실행기 v1.0
주요 컴포넌트들:
- UnifiedPageTestRunner: 모든 페이지 테스트의 기본 클래스 (77-280라인)
  - run_tests(): 테스트 실행 메인 로직 (120-180라인)
  - _execute_test_mode(): 모드별 테스트 실행 (182-220라인)
  - _run_auto_mode(): 자동화 모드 실행 (222-250라인)
  - _run_manual_mode(): 수동 확인 모드 실행 (252-280라인)

- RateLimitManager: API 호출 제한 관리자 (15-75라인)
  - wait_before_request(): Rate limiting 방지 대기 (25-40라인)
  - handle_rate_limit_error(): 오류 발생시 대기 시간 증가 (42-55라인)
  - handle_success(): 성공시 대기 시간 감소 (57-65라인)

- OAuth2APIManager: OAuth2 인증 기반 API 관리자 (282-420라인)
  - authenticate_user(): 사용자 인증 (320-360라인)
  - api_request(): 인증된 API 요청 (362-400라인)
  - register_user(): 사용자 등록 (402-420라인)

핵심 기능:
- 두 가지 테스트 모드 지원 (auto: 데이터 정리, manual: 수동 확인용)
- Rate limiting 지능형 관리
- OAuth2 인증 시스템 통합
- 페이지별 테스트 시나리오 추상화
- 통합 보고서 생성 시스템

관련 파일들:
- /scripts/development/testing/unified/report_generator.py: 통합 보고서 생성기
- /scripts/development/testing/unified/data_manager.py: 테스트 데이터 관리자
- /scripts/development/testing/pages/*/: 각 페이지별 구현체
"""

import asyncio
import aiohttp
import time
import uuid
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from rate_limit_controller import RateLimitTestContext, RateLimitController


class RateLimitManager:
    """Rate Limiting 관리자 - API 호출 간격 지능형 관리"""
    
    def __init__(self, base_delay: float = 1.5):
        self.base_delay = base_delay
        self.current_delay = self.base_delay
        self.max_delay = 15.0
        self.min_delay = 0.5
        self.consecutive_errors = 0
        self.last_request_time = 0
        self.success_streak = 0
        
    async def wait_before_request(self):
        """요청 전 적절한 대기 시간 적용"""
        now = time.time()
        
        if self.last_request_time > 0:
            elapsed = now - self.last_request_time
            if elapsed < self.current_delay:
                wait_time = self.current_delay - elapsed
                print(f"⏱️ API 호출 간격 조절 - {wait_time:.1f}초 대기...")
                await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def handle_rate_limit_error(self, retry_after: Optional[int] = None):
        """Rate limit 오류 발생 시 대기 시간 증가"""
        self.consecutive_errors += 1
        self.success_streak = 0
        
        if retry_after:
            self.current_delay = min(retry_after + 2, self.max_delay)
        else:
            # 지수적 백오프
            self.current_delay = min(self.current_delay * 1.4, self.max_delay)
        
        print(f"⚠️ Rate limit 감지 - 대기 시간을 {self.current_delay:.1f}초로 증가")
    
    def handle_success(self):
        """성공 시 대기 시간 점진적 감소"""
        self.success_streak += 1
        
        if self.consecutive_errors > 0:
            self.consecutive_errors = 0
        elif self.success_streak >= 3:
            # 연속 성공 시 점진적 감소
            self.current_delay = max(self.min_delay, self.current_delay * 0.9)
            self.success_streak = 0
    
    def get_current_delay(self) -> float:
        """현재 대기 시간 조회"""
        return self.current_delay


class UnifiedPageTestRunner(ABC):
    """모든 페이지 테스트의 통합 기본 클래스"""
    
    def __init__(self, page_name: str, base_url: str = "http://localhost:8000", auto_disable_rate_limit: bool = True):
        self.page_name = page_name
        self.base_url = base_url
        self.frontend_url = "http://localhost:5173"
        self.auto_disable_rate_limit = auto_disable_rate_limit
        
        # 세션 ID 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"{page_name.upper()}_{timestamp}_{random_suffix}"
        
        # 컴포넌트들 초기화
        self.rate_manager = RateLimitManager()
        self.rate_limit_controller = RateLimitController(api_base_url=base_url) if auto_disable_rate_limit else None
        self.rate_limit_context = None  # RateLimitTestContext 저장용
        self.api_manager = None
        self.report_generator = None
        self.data_manager = None
        
        # 테스트 모드 (auto: 자동화, manual: 수동 확인용)
        self.test_mode = "auto"
        
        # 테스트 데이터 저장
        self.created_posts = []
        self.created_comments = []
        self.created_reactions = []
        self.test_users = {}
        
        # 테스트 실행 통계
        self.test_stats = {
            "start_time": None,
            "end_time": None,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 0
        }
    
    async def run_tests(self, mode: str = "auto") -> bool:
        """테스트 실행 메인 함수 (Rate Limiting 자동 제어 포함)"""
        self.test_mode = mode
        self.test_stats["start_time"] = datetime.now()
        
        print(f"🚀 {self.page_name} 페이지 통합 테스트 시작!")
        print(f"🆔 세션 ID: {self.session_id}")
        print(f"🌐 API 베이스 URL: {self.base_url}")
        print(f"🎯 테스트 모드: {'자동화 (데이터 정리)' if mode == 'auto' else '수동 확인용 (데이터 보존)'}")
        if self.auto_disable_rate_limit:
            print(f"🚦 Rate Limiting: 테스트 중 자동 비활성화")
        print("=" * 80)
        
        success = False
        
        # Rate Limiting 제어 컨텍스트를 사용할지 결정
        if self.auto_disable_rate_limit and self.rate_limit_controller:
            # Rate Limiting 비활성화된 상태로 테스트 실행
            async with RateLimitTestContext(self.rate_limit_controller) as controller:
                success = await self._run_tests_internal()
        else:
            # Rate Limiting 제어 없이 기본 테스트 실행
            success = await self._run_tests_internal()
        
        self.test_stats["end_time"] = datetime.now()
        duration = self.test_stats["end_time"] - self.test_stats["start_time"]
        
        print(f"\n🏁 {self.page_name} 테스트 완료!")
        print(f"⏱️ 실행 시간: {duration}")
        print(f"📊 결과: 성공 {self.test_stats['passed_tests']}, 실패 {self.test_stats['failed_tests']}, 경고 {self.test_stats['warnings']}")
        
        return success
        
    async def _run_tests_internal(self) -> bool:
        """내부 테스트 실행 로직"""
        success = False
        try:
            # 컴포넌트들 초기화
            await self._initialize_components()
            
            # 모드별 테스트 실행
            success = await self._execute_test_mode()
            
        except KeyboardInterrupt:
            print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # 컴포넌트들 정리
            await self._cleanup_components()
            
        return success
    
    async def _execute_test_mode(self) -> bool:
        """모드별 테스트 실행"""
        if self.test_mode == "auto":
            return await self._run_auto_mode()
        elif self.test_mode == "manual":
            return await self._run_manual_mode()
        else:
            raise ValueError(f"지원하지 않는 테스트 모드: {self.test_mode}")
    
    async def _run_auto_mode(self) -> bool:
        """자동화 모드 실행 (데이터 정리)"""
        print("🤖 자동화 모드: API 테스트 실행 후 데이터 자동 정리")
        
        # 1. 테스트 사용자 생성 및 인증
        auth_success = await self._setup_test_users()
        if not auth_success:
            return False
        
        # 2. 페이지별 테스트 실행
        test_success = await self.run_page_specific_tests()
        
        # 3. 테스트 데이터 정리
        await self._cleanup_test_data()
        
        # 4. 보고서 생성 (간단한 버전)
        await self._generate_auto_mode_report()
        
        return test_success
    
    async def _run_manual_mode(self) -> bool:
        """수동 확인 모드 실행 (데이터 보존)"""
        print("👤 수동 확인 모드: API로 데이터 생성 후 수동 확인용 보고서 생성")
        
        # 1. 테스트 사용자 생성 및 인증
        auth_success = await self._setup_test_users()
        if not auth_success:
            return False
        
        # 2. 페이지별 테스트 실행 (데이터 보존)
        test_success = await self.run_page_specific_tests()
        
        # 3. 수동 확인용 종합 보고서 생성
        await self._generate_manual_verification_report()
        
        print(f"\n✨ 수동 확인 모드 완료!")
        print(f"📋 브라우저에서 {self.frontend_url}/{self.get_page_url()} 에서 기능을 직접 확인하세요.")
        
        return test_success
    
    # 추상 메소드들 - 각 페이지별로 구현해야 함
    @abstractmethod
    async def run_page_specific_tests(self) -> bool:
        """페이지별 특화 테스트 실행 (각 페이지에서 구현)"""
        pass
    
    @abstractmethod
    def get_page_url(self) -> str:
        """페이지 URL 조회 (각 페이지에서 구현)"""
        pass
    
    @abstractmethod
    def get_test_scenarios(self) -> List[Dict[str, Any]]:
        """테스트 시나리오 목록 조회 (각 페이지에서 구현)"""
        pass
    
    # 헬퍼 메소드들
    async def _initialize_components(self):
        """컴포넌트들 초기화"""
        # 절대 임포트 방식으로 수정
        import sys
        from pathlib import Path
        
        # unified 디렉토리를 sys.path에 추가
        unified_dir = Path(__file__).parent
        if str(unified_dir) not in sys.path:
            sys.path.insert(0, str(unified_dir))
        
        from report_generator import UnifiedReportGenerator
        from data_manager import UnifiedDataManager
        
        self.api_manager = OAuth2APIManager(self.base_url)
        await self.api_manager.__aenter__()
        
        self.report_generator = UnifiedReportGenerator(
            self.session_id, 
            self.page_name,
            self.test_mode
        )
        
        self.data_manager = UnifiedDataManager(
            self.session_id,
            self.api_manager
        )
    
    async def _cleanup_components(self):
        """컴포넌트들 정리"""
        if self.api_manager:
            await self.api_manager.__aexit__(None, None, None)
    
    async def _setup_test_users(self) -> bool:
        """테스트 사용자 생성 및 인증"""
        return True  # 기본 구현, 각 페이지에서 오버라이드
    
    async def _cleanup_test_data(self):
        """테스트 데이터 정리"""
        if self.data_manager:
            await self.data_manager.cleanup_session_data(self.session_id)
    
    async def _generate_auto_mode_report(self):
        """자동화 모드 보고서 생성"""
        if self.report_generator:
            await self.report_generator.generate_auto_report()
    
    async def _generate_manual_verification_report(self):
        """수동 확인용 종합 보고서 생성"""
        if self.report_generator:
            await self.report_generator.generate_manual_verification_report()


class OAuth2APIManager:
    """OAuth2 인증 기반 API 관리자"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.authenticated_users = {}
        
        # API 엔드포인트들
        self.endpoints = {
            "register": f"{base_url}/api/auth/register",
            "login": f"{base_url}/api/auth/login",
            "posts": f"{base_url}/api/posts",
            "comments": f"{base_url}/api/comments",
            "reactions": f"{base_url}/api/reactions",
            "users": f"{base_url}/api/users",
            "admin": f"{base_url}/api/admin",
            "health": f"{base_url}/health"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """OAuth2 인증으로 사용자 로그인"""
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('username', email)
            form_data.add_field('password', password)
            
            async with self.session.post(self.endpoints["login"], data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    access_token = result.get("access_token")
                    user_data = result.get("user", {})
                    user_id = user_data.get("id") or user_data.get("_id") or email
                    
                    self.authenticated_users[user_id] = {
                        "token": access_token,
                        "user_data": user_data,
                        "email": email
                    }
                    
                    return {"success": True, "token": access_token, "user": user_data}
                else:
                    error_text = await response.text()
                    print(f"      디버그 - 인증 실패: status={response.status}, error={error_text}")
                    return {"success": False, "status": response.status, "error": error_text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def api_request(self, method: str, endpoint: str, user_token: str = None, 
                         json_data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """인증된 API 요청"""
        try:
            headers = {"Content-Type": "application/json"}
            if user_token:
                headers["Authorization"] = f"Bearer {user_token}"
            
            kwargs = {"headers": headers}
            if json_data:
                kwargs["json"] = json_data
            if params:
                kwargs["params"] = params
                
            async with self.session.request(method, endpoint, **kwargs) as response:
                status = response.status
                try:
                    result = await response.json()
                except:
                    result = {"error": await response.text()}
                
                return {
                    "success": 200 <= status < 300,
                    "status": status,
                    "data": result
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 등록"""
        try:
            async with self.session.post(self.endpoints["register"], json=user_data) as response:
                if response.status == 201:
                    result = await response.json()
                    return {"success": True, "data": result}
                elif response.status == 409:
                    # 사용자가 이미 존재하는 경우도 성공으로 간주
                    return {"success": True, "data": {"message": "User already exists"}}
                else:
                    error_text = await response.text()
                    print(f"      디버그 - 등록 실패: status={response.status}, error={error_text}")
                    return {"success": False, "status": response.status, "error": error_text}
        except Exception as e:
            print(f"      디버그 - 등록 예외: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_user_token(self, user_id: str = None, email: str = None) -> Optional[str]:
        """사용자 토큰 조회"""
        if user_id and user_id in self.authenticated_users:
            return self.authenticated_users[user_id]["token"]
        
        if email:
            for user_data in self.authenticated_users.values():
                if user_data["email"] == email:
                    return user_data["token"]
        
        return None


def create_test_runner_args_parser() -> argparse.ArgumentParser:
    """테스트 실행기용 명령행 인수 파서 생성"""
    parser = argparse.ArgumentParser(description='통합 페이지 테스트 실행기')
    
    parser.add_argument(
        '--mode', 
        choices=['auto', 'manual'],
        default='auto',
        help='테스트 모드: auto (자동화/데이터정리) 또는 manual (수동확인용/데이터보존)'
    )
    
    parser.add_argument(
        '--base-url',
        default='http://localhost:8000',
        help='API 서버 기본 URL (기본값: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--frontend-url',
        default='http://localhost:5173',
        help='프론트엔드 서버 URL (기본값: http://localhost:5173)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세한 출력 표시'
    )
    
    parser.add_argument(
        '--open-browser',
        action='store_true',
        help='수동 확인 모드에서 자동으로 브라우저 열기'
    )
    
    return parser


if __name__ == "__main__":
    print("🔧 통합 테스트 프레임워크 기본 클래스")
    print("이 파일은 직접 실행할 수 없습니다. 각 페이지별 테스트 실행기를 사용하세요.")
    print()
    print("사용 가능한 페이지별 테스트:")
    print("- python pages/board/api_test.py")
    print("- python pages/expert_tips/api_test.py") 
    print("- python pages/property_info/api_test.py")
    print("- python pages/service_provider/api_test.py")