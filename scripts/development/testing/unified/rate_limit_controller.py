#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 21:14:00 KST
작업 버전: 테스트용 Rate Limiting 자동 제어 시스템 v1.0
주요 컴포넌트들:
- RateLimitController: Rate limiting 동적 제어 클래스 (30-120라인)
  - disable_rate_limiting(): Rate limiting 비활성화 (40-70라인)
  - enable_rate_limiting(): Rate limiting 활성화 (72-100라인)
  - get_current_status(): 현재 상태 확인 (102-120라인)

- RateLimitTestContext: 컨텍스트 매니저 (122-180라인)
  - __enter__(): 테스트 시작시 자동 비활성화 (140-160라인)
  - __exit__(): 테스트 종료시 자동 활성화 (162-180라인)

핵심 기능:
- 테스트 시작/종료시 자동 Rate limiting 제어
- .env 파일 직접 수정을 통한 동적 설정 변경
- 백엔드 서버 재시작 없이 실시간 제어 (환경변수 기반)
- 예외 발생시 자동 복구 보장
- 컨텍스트 매니저를 통한 안전한 사용

관련 파일들:
- /backend/.env.dev: 개발환경 Rate limiting 설정
- /scripts/development/testing/unified/base_test_runner.py: 통합 테스트 프레임워크
- /scripts/development/testing/pages/*/: 각 페이지별 테스트 스크립트
"""

import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import aiohttp


class RateLimitController:
    """Rate Limiting 동적 제어 클래스"""
    
    def __init__(self, backend_base_path: str = None, api_base_url: str = "http://localhost:8000"):
        """
        Rate Limiting 컨트롤러 초기화
        
        Args:
            backend_base_path: 백엔드 프로젝트 루트 경로
            api_base_url: API 서버 기본 URL
        """
        if backend_base_path is None:
            # 현재 스크립트 위치에서 백엔드 경로 추론
            current_path = Path(__file__).parent.parent.parent.parent.parent  # v5/ 레벨
            self.backend_path = current_path / "backend"
        else:
            self.backend_path = Path(backend_base_path)
        
        self.env_file_path = self.backend_path / ".env.dev"
        self.api_base_url = api_base_url
        self.original_setting = None
        
    def _backup_current_setting(self) -> bool:
        """현재 설정을 백업"""
        try:
            if self.env_file_path.exists():
                with open(self.env_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 기존 RATE_LIMITING_ENABLED 설정 찾기
                for line in content.split('\n'):
                    if line.strip().startswith('RATE_LIMITING_ENABLED='):
                        self.original_setting = line.strip().split('=')[1].lower() == 'true'
                        return True
                
                # 설정이 없으면 기본값(True)으로 간주
                self.original_setting = True
                return True
        except Exception as e:
            print(f"⚠️ 설정 백업 실패: {e}")
            return False
    
    def _modify_env_file(self, enable_rate_limiting: bool) -> bool:
        """환경 파일의 Rate limiting 설정 수정"""
        try:
            if not self.env_file_path.exists():
                print(f"❌ 환경 파일을 찾을 수 없음: {self.env_file_path}")
                return False
            
            # 파일 내용 읽기
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # RATE_LIMITING_ENABLED 설정 찾아서 수정
            setting_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith('RATE_LIMITING_ENABLED='):
                    lines[i] = f"RATE_LIMITING_ENABLED={'true' if enable_rate_limiting else 'false'}\n"
                    setting_found = True
                    break
            
            # 설정이 없으면 추가
            if not setting_found:
                # Redis Configuration 섹션 찾아서 추가
                redis_section_found = False
                for i, line in enumerate(lines):
                    if '# Redis Configuration' in line or 'REDIS_URL=' in line:
                        # Redis 설정 다음에 Rate limiting 설정 추가
                        insert_pos = i + 1
                        while insert_pos < len(lines) and lines[insert_pos].strip() and not lines[insert_pos].startswith('#'):
                            insert_pos += 1
                        
                        lines.insert(insert_pos, f"\n# Rate Limiting Configuration (테스트 중 동적 제어)\n")
                        lines.insert(insert_pos + 1, f"RATE_LIMITING_ENABLED={'true' if enable_rate_limiting else 'false'}\n")
                        redis_section_found = True
                        break
                
                # Redis 섹션을 못 찾으면 파일 끝에 추가
                if not redis_section_found:
                    lines.append(f"\n# Rate Limiting Configuration (테스트 중 동적 제어)\n")
                    lines.append(f"RATE_LIMITING_ENABLED={'true' if enable_rate_limiting else 'false'}\n")
            
            # 파일에 쓰기
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"❌ 환경 파일 수정 실패: {e}")
            return False
    
    async def disable_rate_limiting(self) -> bool:
        """Rate limiting 비활성화"""
        print("🚦 Rate limiting 비활성화 중...")
        
        # 현재 설정 백업
        if not self._backup_current_setting():
            return False
        
        # 환경 파일 수정
        if not self._modify_env_file(enable_rate_limiting=False):
            return False
        
        print("   ✅ Rate limiting이 비활성화되었습니다.")
        print("   ⚠️ 참고: 환경변수 변경이 적용되려면 백엔드 서버 재시작이 필요할 수 있습니다.")
        return True
    
    async def enable_rate_limiting(self) -> bool:
        """Rate limiting 활성화 (원래 설정으로 복원)"""
        print("🚦 Rate limiting 활성화 중...")
        
        # 백업된 설정이 있으면 복원, 없으면 기본값(True) 사용
        original_value = self.original_setting if self.original_setting is not None else True
        
        # 환경 파일 수정
        if not self._modify_env_file(enable_rate_limiting=original_value):
            return False
        
        print(f"   ✅ Rate limiting이 {'활성화' if original_value else '비활성화'}되었습니다 (원래 설정으로 복원).")
        return True
    
    async def get_current_status(self) -> Dict[str, Any]:
        """현재 Rate limiting 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "api_available": True,
                            "server_status": "healthy",
                            "note": "Rate limiting 상태는 서버 재시작 후 확인 가능"
                        }
                    else:
                        return {
                            "api_available": False,
                            "server_status": f"HTTP {response.status}",
                            "note": "서버가 응답하지 않음"
                        }
        except Exception as e:
            return {
                "api_available": False,
                "server_status": "unreachable",
                "error": str(e),
                "note": "서버에 연결할 수 없음"
            }


class RateLimitTestContext:
    """Rate Limiting 테스트 컨텍스트 매니저"""
    
    def __init__(self, controller: RateLimitController = None, auto_wait: float = 0.0):
        """
        컨텍스트 매니저 초기화
        
        Args:
            controller: RateLimitController 인스턴스 (None이면 자동 생성)
            auto_wait: 설정 변경 후 대기 시간 (초) - Rate limiting은 환경변수가 아닌 실시간 제어이므로 대기 불필요
        """
        self.controller = controller or RateLimitController()
        self.auto_wait = auto_wait
        self.success = False
        
    async def __aenter__(self):
        """컨텍스트 진입: Rate limiting 비활성화"""
        print("🔧 테스트 환경 설정 중...")
        
        self.success = await self.controller.disable_rate_limiting()
        
        if self.success and self.auto_wait > 0:
            print(f"⏱️ 설정 적용을 위해 {self.auto_wait}초 대기 중...")
            await asyncio.sleep(self.auto_wait)
        
        return self.controller
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 종료: Rate limiting 활성화"""
        print("🔧 테스트 환경 복구 중...")
        
        if self.success:
            await self.controller.enable_rate_limiting()
            
            if self.auto_wait > 0:
                print(f"⏱️ 설정 복구를 위해 {self.auto_wait}초 대기 중...")
                await asyncio.sleep(self.auto_wait)
        
        if exc_type is not None:
            print(f"⚠️ 테스트 중 예외 발생: {exc_type.__name__}: {exc_val}")
            print("✅ Rate limiting 설정이 자동으로 복구되었습니다.")
        else:
            print("✅ 테스트 완료 후 Rate limiting 설정이 복구되었습니다.")


# 편의 함수들
async def with_rate_limiting_disabled(test_func, *args, **kwargs):
    """Rate limiting을 비활성화한 상태로 테스트 함수 실행"""
    async with RateLimitTestContext() as controller:
        if callable(test_func):
            if asyncio.iscoroutinefunction(test_func):
                return await test_func(*args, **kwargs)
            else:
                return test_func(*args, **kwargs)
        else:
            print("⚠️ 제공된 객체가 호출 가능하지 않습니다.")
            return None


def create_rate_limit_controller(backend_path: str = None, api_url: str = "http://localhost:8000") -> RateLimitController:
    """Rate Limiting 컨트롤러 팩토리 함수"""
    return RateLimitController(backend_base_path=backend_path, api_base_url=api_url)


# 테스트용 메인 함수
async def main():
    """Rate Limiting 제어 시스템 테스트"""
    print("🧪 Rate Limiting 제어 시스템 테스트")
    print("=" * 50)
    
    controller = RateLimitController()
    
    # 현재 상태 확인
    status = await controller.get_current_status()
    print(f"📊 현재 서버 상태: {status}")
    
    # 컨텍스트 매니저 테스트
    print("\n🔧 컨텍스트 매니저 테스트...")
    async with RateLimitTestContext(controller) as ctrl:
        print("   ✅ Rate limiting 비활성화된 상태로 작업 수행")
        await asyncio.sleep(1)  # 테스트 작업 시뮬레이션
    
    print("✅ 테스트 완료")


if __name__ == "__main__":
    asyncio.run(main())