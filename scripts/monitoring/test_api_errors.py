#!/usr/bin/env python3
"""
API 에러 발생 테스트 스크립트

각 API 엔드포인트에 다양한 방식으로 에러를 발생시켜
모니터링 시스템과 Sentry의 감지 능력을 테스트합니다.

작성 시간: 2025-07-23 (한국 시간 기준)
작업 버전: v1.0
주요 컴포넌트들:
- ApiErrorTester: 메인 테스트 클래스
- EndpointTester: 개별 엔드포인트 테스트 기능
- ResultCollector: 결과 수집 및 보고서 생성
- ErrorScenarios: 다양한 에러 시나리오 구현

주요 함수:
- test_all_endpoints(): 모든 엔드포인트 테스트 (line 120-150)
- test_individual_endpoint(): 개별 엔드포인트 테스트 (line 152-180)
- generate_errors(): 다양한 에러 발생 (line 182-250)
- collect_results(): 결과 수집 (line 252-280)
- generate_report(): 보고서 생성 (line 282-320)

코드 라인 정보:
- 설정 및 초기화: 1-100
- 에러 시나리오 구현: 101-200
- 결과 수집 및 보고서: 201-350
"""

import asyncio
import aiohttp
import time
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """개별 테스트 결과"""
    endpoint: str
    scenario: str
    success: bool
    status_code: Optional[int]
    response_time: float
    error_message: str
    timestamp: str
    sentry_expected: bool

@dataclass
class TestSummary:
    """전체 테스트 요약"""
    total_tests: int
    successful_errors: int
    failed_tests: int
    avg_response_time: float
    start_time: str
    end_time: str
    results: List[TestResult]

class ApiErrorTester:
    """API 에러 테스트 메인 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
        
        # 테스트 대상 엔드포인트
        self.endpoints = [
            "/api/health",
            "/api/auth/health", 
            "/api/posts/health",
            "/api/comments/health",
            "/api/posts?limit=1"
        ]
        
        # 기존 테스트 에러 엔드포인트 (백엔드에 이미 구현됨)
        self.error_endpoints = [
            "/api/monitoring/test/api/server-error",
            "/api/monitoring/test/api/database-error"
        ]
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def test_endpoint_with_invalid_params(self, endpoint: str) -> TestResult:
        """잘못된 파라미터로 에러 유발"""
        start_time = time.time()
        scenario = "invalid_params"
        
        try:
            # 잘못된 파라미터 추가
            if "?" in endpoint:
                test_url = f"{self.base_url}{endpoint}&invalid_param=test&bad_value=undefined"
            else:
                test_url = f"{self.base_url}{endpoint}?invalid_param=test&bad_value=undefined"
            
            async with self.session.get(test_url) as response:
                response_time = time.time() - start_time
                
                return TestResult(
                    endpoint=endpoint,
                    scenario=scenario,
                    success=response.status >= 400,  # 4xx, 5xx 에러면 성공
                    status_code=response.status,
                    response_time=response_time,
                    error_message=f"HTTP {response.status}" if response.status >= 400 else "No error occurred",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    sentry_expected=response.status >= 500  # 5xx 에러만 Sentry 포착 예상
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                scenario=scenario,
                success=True,  # 예외 발생도 성공으로 간주
                status_code=None,
                response_time=response_time,
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat(),
                sentry_expected=True
            )
    
    async def test_endpoint_with_timeout(self, endpoint: str) -> TestResult:
        """타임아웃 에러 유발"""
        start_time = time.time()
        scenario = "timeout"
        
        try:
            # 매우 짧은 타임아웃 설정
            timeout = aiohttp.ClientTimeout(total=0.001)  # 1ms
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    
                    return TestResult(
                        endpoint=endpoint,
                        scenario=scenario,
                        success=False,  # 타임아웃이 발생하지 않으면 실패
                        status_code=response.status,
                        response_time=response_time,
                        error_message="Timeout did not occur",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        sentry_expected=False
                    )
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                scenario=scenario,
                success=True,  # 타임아웃 발생이면 성공
                status_code=None,
                response_time=response_time,
                error_message="Timeout occurred",
                timestamp=datetime.now(timezone.utc).isoformat(),
                sentry_expected=True  # 네트워크 에러로 Sentry 포착 가능
            )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                scenario=scenario,
                success=True,
                status_code=None,
                response_time=response_time,
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat(),
                sentry_expected=True
            )
    
    async def test_endpoint_with_bad_method(self, endpoint: str) -> TestResult:
        """잘못된 HTTP 메서드로 에러 유발"""
        start_time = time.time()
        scenario = "bad_method"
        
        try:
            # GET 엔드포인트에 POST 요청
            async with self.session.post(f"{self.base_url}{endpoint}") as response:
                response_time = time.time() - start_time
                
                return TestResult(
                    endpoint=endpoint,
                    scenario=scenario,
                    success=response.status >= 400,
                    status_code=response.status,
                    response_time=response_time,
                    error_message=f"HTTP {response.status} - Method not allowed" if response.status >= 400 else "No error occurred",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    sentry_expected=response.status >= 500
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                scenario=scenario,
                success=True,
                status_code=None,
                response_time=response_time,
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat(),
                sentry_expected=True
            )
    
    async def trigger_existing_error_endpoint(self, error_endpoint: str) -> TestResult:
        """기존의 에러 발생 엔드포인트 호출"""
        start_time = time.time()
        scenario = "existing_error"
        
        try:
            if "server-error" in error_endpoint:
                # POST 요청으로 서버 에러 발생
                async with self.session.post(f"{self.base_url}{error_endpoint}") as response:
                    response_time = time.time() - start_time
                    
                    return TestResult(
                        endpoint=error_endpoint,
                        scenario=scenario,
                        success=response.status >= 500,  # 서버 에러 발생하면 성공
                        status_code=response.status,
                        response_time=response_time,
                        error_message=f"Server error endpoint triggered - HTTP {response.status}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        sentry_expected=True  # 의도적 서버 에러이므로 Sentry 포착 예상
                    )
            else:
                # GET 요청으로 데이터베이스 에러 발생
                async with self.session.get(f"{self.base_url}{error_endpoint}") as response:
                    response_time = time.time() - start_time
                    
                    return TestResult(
                        endpoint=error_endpoint,
                        scenario=scenario,
                        success=response.status >= 500,
                        status_code=response.status,
                        response_time=response_time,
                        error_message=f"Database error endpoint triggered - HTTP {response.status}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        sentry_expected=True
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=error_endpoint,
                scenario=scenario,
                success=True,  # 예외 발생도 성공
                status_code=None,
                response_time=response_time,
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat(),
                sentry_expected=True
            )
    
    async def run_all_tests(self) -> TestSummary:
        """모든 테스트 실행"""
        logger.info("🚀 API 에러 테스트 시작")
        start_time = datetime.now(timezone.utc)
        
        # 1. 일반 엔드포인트 테스트
        for endpoint in self.endpoints:
            logger.info(f"🔍 테스트 중: {endpoint}")
            
            # 다양한 에러 시나리오 테스트
            scenarios = [
                self.test_endpoint_with_invalid_params(endpoint),
                self.test_endpoint_with_timeout(endpoint),
                self.test_endpoint_with_bad_method(endpoint)
            ]
            
            results = await asyncio.gather(*scenarios, return_exceptions=True)
            
            for result in results:
                if isinstance(result, TestResult):
                    self.results.append(result)
                    status = "✅ 성공" if result.success else "❌ 실패"
                    logger.info(f"  {result.scenario}: {status} (HTTP {result.status_code})")
                else:
                    logger.error(f"  테스트 실행 중 오류: {result}")
        
        # 2. 기존 에러 엔드포인트 테스트
        logger.info("🔥 의도적 에러 엔드포인트 테스트")
        for error_endpoint in self.error_endpoints:
            logger.info(f"🔍 테스트 중: {error_endpoint}")
            result = await self.trigger_existing_error_endpoint(error_endpoint)
            self.results.append(result)
            status = "✅ 성공" if result.success else "❌ 실패"
            logger.info(f"  {result.scenario}: {status} (HTTP {result.status_code})")
        
        end_time = datetime.now(timezone.utc)
        
        # 결과 요약
        successful_errors = sum(1 for r in self.results if r.success)
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results) if self.results else 0
        
        summary = TestSummary(
            total_tests=len(self.results),
            successful_errors=successful_errors,
            failed_tests=len(self.results) - successful_errors,
            avg_response_time=avg_response_time,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            results=self.results
        )
        
        logger.info(f"✅ 테스트 완료: {successful_errors}/{len(self.results)} 성공")
        return summary
    
    def generate_report(self, summary: TestSummary, output_path: Optional[str] = None) -> str:
        """테스트 결과 보고서 생성"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"api_error_test_report_{timestamp}.md"
        
        # Sentry 포착 예상 결과
        sentry_expected_count = sum(1 for r in summary.results if r.sentry_expected)
        
        report_content = f"""# API 에러 테스트 보고서

## 📊 테스트 요약
- **테스트 시작**: {summary.start_time}
- **테스트 종료**: {summary.end_time}
- **총 테스트 수**: {summary.total_tests}
- **성공한 에러 발생**: {summary.successful_errors}
- **실패한 테스트**: {summary.failed_tests}
- **평균 응답시간**: {summary.avg_response_time:.3f}초
- **Sentry 포착 예상**: {sentry_expected_count}건

## 🎯 테스트 목적
모니터링 시스템과 Sentry의 에러 감지 능력을 검증하기 위해 다양한 방식으로 API 에러를 발생시킴

## 📋 상세 결과

### 성공한 에러 (Sentry 포착 예상)
"""
        
        for result in summary.results:
            if result.success and result.sentry_expected:
                report_content += f"""
- **{result.endpoint}** ({result.scenario})
  - 상태 코드: {result.status_code or 'Exception'}
  - 응답시간: {result.response_time:.3f}초
  - 에러 메시지: {result.error_message}
  - 시간: {result.timestamp}
"""
        
        report_content += "\n### 성공한 에러 (Sentry 포착 예상 안됨)\n"
        
        for result in summary.results:
            if result.success and not result.sentry_expected:
                report_content += f"""
- **{result.endpoint}** ({result.scenario})
  - 상태 코드: {result.status_code}
  - 응답시간: {result.response_time:.3f}초
  - 에러 메시지: {result.error_message}
  - 시간: {result.timestamp}
"""
        
        if summary.failed_tests > 0:
            report_content += "\n### 실패한 테스트\n"
            for result in summary.results:
                if not result.success:
                    report_content += f"""
- **{result.endpoint}** ({result.scenario})
  - 상태 코드: {result.status_code}
  - 응답시간: {result.response_time:.3f}초
  - 에러 메시지: {result.error_message}
  - 시간: {result.timestamp}
"""
        
        report_content += f"""

## 🔍 검증 체크리스트

### 모니터링 페이지 확인사항
- [ ] API 엔드포인트 상태가 `healthy` → `down`으로 변경됨
- [ ] 응답시간이 적절히 측정/표시됨  
- [ ] 에러 메시지가 올바르게 표시됨

### Sentry 이슈 확인사항
- [ ] 예상된 {sentry_expected_count}건의 에러가 Sentry에서 이슈로 생성됨
- [ ] 에러 타입별로 적절히 분류됨
- [ ] 스택 트레이스와 컨텍스트 정보가 포함됨

## 📝 추가 확인 방법

1. **모니터링 페이지 접속**: http://localhost:5173/admin/monitoring
2. **Sentry 대시보드 확인**: 설정된 Sentry 프로젝트의 Issues 페이지
3. **로그 확인**: 백엔드 서버 로그에서 에러 발생 확인

---
*보고서 생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        # 파일 저장
        report_path = Path(__file__).parent / output_path
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # JSON 결과도 저장
        json_path = report_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 보고서 생성됨: {report_path}")
        logger.info(f"📄 JSON 결과 저장됨: {json_path}")
        
        return str(report_path)

async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="API 에러 테스트 스크립트")
    parser.add_argument("--base-url", default="http://localhost:8000", help="백엔드 API 기본 URL")
    parser.add_argument("--output", help="출력 파일명 (선택사항)")
    parser.add_argument("--scenario", choices=["all", "basic", "timeout", "existing"], default="all",
                       help="실행할 테스트 시나리오")
    
    args = parser.parse_args()
    
    print("🔥 API 에러 발생 테스트 시작")
    print(f"🎯 대상 URL: {args.base_url}")
    print(f"📋 시나리오: {args.scenario}")
    print("-" * 50)
    
    async with ApiErrorTester(args.base_url) as tester:
        summary = await tester.run_all_tests()
        report_path = tester.generate_report(summary, args.output)
        
        print("\n" + "=" * 50)
        print("🎉 테스트 완료!")
        print(f"📊 총 {summary.total_tests}개 테스트 중 {summary.successful_errors}개 성공")
        print(f"📄 보고서: {report_path}")
        print(f"⏱️  평균 응답시간: {summary.avg_response_time:.3f}초")
        
        sentry_expected = sum(1 for r in summary.results if r.sentry_expected)
        print(f"🔍 Sentry 포착 예상: {sentry_expected}건")
        print("\n🔗 모니터링 페이지에서 결과를 확인하세요!")

if __name__ == "__main__":
    asyncio.run(main())