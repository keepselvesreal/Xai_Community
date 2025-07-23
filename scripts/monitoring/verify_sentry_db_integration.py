#!/usr/bin/env python3
"""
종합적인 Sentry-DB-모니터링 통합 검증 스크립트

작업 시간: 2025-07-23 14:35:00 KST
작업 버전: v2.0 (완전 확장됨)
주요 컴포넌트:
- ComprehensiveSentryVerifier: 종합적인 Sentry 검증 클래스
- VerificationResult: 검증 결과 데이터 클래스
- SentryMonitoringComparison: Sentry-모니터링 비교 결과 
- ComprehensiveVerificationReport: 종합 검증 보고서

주요 함수:
- main(): 메인 실행 함수 (line 919-1022)
- run_comprehensive_verification(): 종합 검증 실행 (line 690-793)
- verify_sentry_db_synchronization(): Sentry-DB 동기화 검증 (line 135-198)
- verify_monitoring_page_display(): 모니터링 페이지 표시 검증 (line 200-270)
- verify_comprehensive_logging_coverage(): 로깅 시스템 포괄적 포착 검증 (line 272-359)
- generate_comprehensive_report(): 종합 보고서 생성 (line 795-917)

코드 라인 정보:
- 데이터 클래스 및 설정: 1-100
- ComprehensiveSentryVerifier 클래스: 90-917
- Sentry-DB 동기화 검증: 135-198
- 모니터링 페이지 검증: 200-270  
- 로깅 포괄성 검증: 272-359
- 종합 실행 및 보고서: 690-917
- 메인 함수 및 CLI: 919-1022

관련 파일:
- comprehensive_error_test.py: 종합 에러 테스트 스크립트
- ../backend/nadle_backend/services/sentry_monitoring_service.py: Sentry 모니터링 서비스
- ../backend/nadle_backend/logging/services/log_service.py: 로그 서비스
- ../frontend/app/components/monitoring/LayeredMonitoring.tsx: 모니터링 대시보드
- ../backend/nadle_backend/routers/client_errors.py: 클라이언트 에러 수집 라우터
"""

import asyncio
import subprocess
import time
import json
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
import argparse

# 백엔드 모듈 import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from nadle_backend.database.connection import get_database
from nadle_backend.logging.dependencies import get_log_service
from nadle_backend.core.logging import LogLevel, LogFilter, LogSource
from nadle_backend.config import get_settings

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """검증 결과 데이터 클래스"""
    test_name: str
    success: bool
    expected_count: int
    actual_count: int
    details: List[Dict[str, Any]]
    timestamp: str
    message: str

@dataclass
class SentryMonitoringComparison:
    """Sentry와 모니터링 페이지 비교 결과"""
    sentry_errors: List[Dict[str, Any]]
    monitoring_errors: List[Dict[str, Any]]
    matched_count: int
    sentry_only_count: int
    monitoring_only_count: int
    sync_status: str

@dataclass
class ComprehensiveVerificationReport:
    """종합 검증 보고서"""
    test_start_time: str
    test_end_time: str
    sentry_db_sync: VerificationResult
    monitoring_display: VerificationResult
    logging_coverage: VerificationResult
    overall_success: bool
    recommendations: List[str]

class ComprehensiveSentryVerifier:
    """종합적인 Sentry 검증 클래스 (확장됨)"""
    
    def __init__(self, backend_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:5173"):
        self.backend_url = backend_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        self.database = None
        self.log_service = None
        self.test_start_time = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.results = {}
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def initialize(self):
        """DB 및 LogService 초기화"""
        try:
            self.database = await get_database()
            
            # LogService 초기화
            from nadle_backend.logging.repositories.mongo_log_repository import MongoLogRepository
            from nadle_backend.logging.services.log_service import LogService
            
            log_repository = MongoLogRepository(self.database)
            await log_repository.setup_indexes()
            
            self.log_service = LogService(log_repository=log_repository)
            await self.log_service.setup()
            
            logger.info("✅ DB 및 LogService 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 초기화 실패: {e}")
            return False
    
    async def verify_sentry_db_synchronization(self, test_errors_count: int = 5) -> VerificationResult:
        """Sentry 에러와 DB 저장 동기화 검증"""
        logger.info("🔄 Sentry-DB 동기화 검증 시작")
        
        try:
            # 1. 테스트 에러 발생 전 상태 확인
            initial_db_logs = await self.check_sentry_logs_in_db(since_minutes=5)
            initial_count = len(initial_db_logs)
            
            # 2. 테스트 에러 발생
            logger.info(f"🔥 {test_errors_count}개의 테스트 에러 발생")
            generated_errors = []
            
            for i in range(test_errors_count):
                async with self.session.post(f"{self.backend_url}/api/monitoring/test/sentry/error") as response:
                    if response.status == 200:
                        response_data = await response.json()
                        generated_errors.append({
                            "sequence": i + 1,
                            "timestamp": response_data.get("timestamp"),
                            "status": "success"
                        })
                    else:
                        generated_errors.append({
                            "sequence": i + 1,
                            "timestamp": datetime.now().isoformat(),
                            "status": "failed",
                            "error": f"HTTP {response.status}"
                        })
                    
                    await asyncio.sleep(1)  # 에러 간 간격
            
            # 3. 잠시 대기 (DB 저장 시간 확보)
            await asyncio.sleep(3)
            
            # 4. 테스트 에러 발생 후 상태 확인
            final_db_logs = await self.check_sentry_logs_in_db(since_minutes=2)
            final_count = len(final_db_logs)
            new_logs_count = final_count - initial_count
            
            # 5. 결과 분석
            success = new_logs_count >= test_errors_count
            
            return VerificationResult(
                test_name="Sentry-DB 동기화",
                success=success,
                expected_count=test_errors_count,
                actual_count=new_logs_count,
                details=generated_errors,
                timestamp=datetime.now().isoformat(),
                message=f"예상: {test_errors_count}개, 실제 DB 저장: {new_logs_count}개"
            )
            
        except Exception as e:
            logger.error(f"❌ Sentry-DB 동기화 검증 실패: {e}")
            return VerificationResult(
                test_name="Sentry-DB 동기화",
                success=False,
                expected_count=test_errors_count,
                actual_count=0,
                details=[{"error": str(e)}],
                timestamp=datetime.now().isoformat(),
                message=f"검증 중 오류 발생: {str(e)}"
            )
    
    async def verify_monitoring_page_display(self) -> VerificationResult:
        """모니터링 페이지 "최근 에러" 표시 검증"""
        logger.info("📊 모니터링 페이지 표시 검증 시작")
        
        try:
            # 1. Sentry API에서 최근 에러 조회
            async with self.session.get(f"{self.backend_url}/api/monitoring/sentry/errors") as response:
                if response.status != 200:
                    raise Exception(f"Sentry API 호출 실패: HTTP {response.status}")
                
                sentry_data = await response.json()
                sentry_recent_errors = sentry_data.get("recent_errors", [])
            
            # 2. DB에서 Sentry 관련 로그 조회
            db_logs = await self.check_sentry_logs_in_db(since_minutes=30)
            
            # 3. 비교 분석
            sentry_count = len(sentry_recent_errors)
            db_count = len(db_logs)
            
            # 시간 기준으로 매칭 시도
            matched_errors = 0
            comparison_details = []
            
            for sentry_error in sentry_recent_errors:
                sentry_time = sentry_error.get("timestamp", "")
                sentry_message = sentry_error.get("message", "")
                
                # DB에서 유사한 시간대의 로그 찾기
                matching_db_log = None
                for db_log in db_logs:
                    try:
                        # 시간 파싱 시 timezone 정보 일관성 확보
                        sentry_dt = datetime.fromisoformat(sentry_time.replace('Z', '+00:00'))
                        db_dt = datetime.fromisoformat(db_log["timestamp"].replace('Z', '+00:00'))
                        
                        # 둘 다 UTC로 변환하여 비교
                        if sentry_dt.tzinfo is None:
                            sentry_dt = sentry_dt.replace(tzinfo=None)
                        else:
                            sentry_dt = sentry_dt.replace(tzinfo=None)
                            
                        if db_dt.tzinfo is None:
                            db_dt = db_dt.replace(tzinfo=None)
                        else:
                            db_dt = db_dt.replace(tzinfo=None)
                        
                        if abs((sentry_dt - db_dt).total_seconds()) < 5:
                            matching_db_log = db_log
                            matched_errors += 1
                            break
                    except Exception as e:
                        logger.warning(f"⚠️ 시간 비교 중 오류: {e}")
                        continue
                
                comparison_details.append({
                    "sentry_error": {
                        "time": sentry_time,
                        "message": sentry_message[:50] + "..."
                    },
                    "db_match": matching_db_log is not None,
                    "db_message": matching_db_log["message"][:50] + "..." if matching_db_log else None
                })
            
            # 4. 성공 기준: Sentry에 표시된 에러의 80% 이상이 DB에 저장되어 있어야 함
            success_rate = (matched_errors / sentry_count) if sentry_count > 0 else 1.0
            success = success_rate >= 0.8
            
            return VerificationResult(
                test_name="모니터링 페이지 표시",
                success=success,
                expected_count=sentry_count,
                actual_count=matched_errors,
                details=comparison_details,
                timestamp=datetime.now().isoformat(),
                message=f"Sentry 표시: {sentry_count}개, DB 매칭: {matched_errors}개 (매칭률: {success_rate:.1%})"
            )
            
        except Exception as e:
            logger.error(f"❌ 모니터링 페이지 표시 검증 실패: {e}")
            return VerificationResult(
                test_name="모니터링 페이지 표시",
                success=False,
                expected_count=0,
                actual_count=0,
                details=[{"error": str(e)}],
                timestamp=datetime.now().isoformat(),
                message=f"검증 중 오류 발생: {str(e)}"
            )
    
    async def verify_comprehensive_logging_coverage(self) -> VerificationResult:
        """로깅 시스템의 포괄적 에러 포착 검증"""
        logger.info("📝 로깅 시스템 포괄적 포착 검증 시작")
        
        try:
            # 1. 다양한 타입의 에러 발생
            test_scenarios = [
                ("sentry_error", "/api/monitoring/test/sentry/error", "POST"),
                ("server_error", "/api/monitoring/test/api/server-error", "POST"),
                ("validation_error", "/api/posts?limit=invalid", "GET"),
                ("not_found_error", "/api/nonexistent-endpoint", "GET"),
                ("method_error", "/api/health", "POST")
            ]
            
            # 테스트 전 로그 수집
            initial_logs = await self.get_all_recent_logs(since_minutes=2)
            initial_count = len(initial_logs)
            
            # 에러 발생
            generated_scenarios = []
            for scenario_name, endpoint, method in test_scenarios:
                try:
                    if method == "POST":
                        async with self.session.post(f"{self.backend_url}{endpoint}") as response:
                            generated_scenarios.append({
                                "scenario": scenario_name,
                                "endpoint": endpoint,
                                "method": method,
                                "status_code": response.status,
                                "expected_logged": True
                            })
                    else:
                        async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                            generated_scenarios.append({
                                "scenario": scenario_name,
                                "endpoint": endpoint,
                                "method": method,
                                "status_code": response.status,
                                "expected_logged": response.status >= 400
                            })
                except Exception as e:
                    generated_scenarios.append({
                        "scenario": scenario_name,
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": None,
                        "error": str(e),
                        "expected_logged": True
                    })
                
                await asyncio.sleep(1)
            
            # 잠시 대기
            await asyncio.sleep(3)
            
            # 테스트 후 로그 수집
            final_logs = await self.get_all_recent_logs(since_minutes=1)  
            final_count = len(final_logs)
            new_logs_count = final_count - initial_count
            
            # 예상 로그 수 계산
            expected_logs = sum(1 for s in generated_scenarios if s.get("expected_logged", False))
            
            # 성공 기준: 예상 로그의 70% 이상 포착
            success_rate = (new_logs_count / expected_logs) if expected_logs > 0 else 1.0
            success = success_rate >= 0.7
            
            return VerificationResult(
                test_name="로깅 시스템 포괄적 포착",
                success=success,
                expected_count=expected_logs,
                actual_count=new_logs_count,
                details=generated_scenarios,
                timestamp=datetime.now().isoformat(),
                message=f"예상 로그: {expected_logs}개, 실제 포착: {new_logs_count}개 (포착률: {success_rate:.1%})"
            )
            
        except Exception as e:
            logger.error(f"❌ 로깅 시스템 포괄적 포착 검증 실패: {e}")
            return VerificationResult(
                test_name="로깅 시스템 포괄적 포착",
                success=False,
                expected_count=0,
                actual_count=0,
                details=[{"error": str(e)}],
                timestamp=datetime.now().isoformat(),
                message=f"검증 중 오류 발생: {str(e)}"
            )
    
    async def get_all_recent_logs(self, since_minutes: int = 5) -> List[Dict[str, Any]]:
        """최근 모든 로그 조회 (레벨 무관)"""
        try:
            if not self.log_service:
                logger.error("LogService가 초기화되지 않았습니다")
                return []
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=since_minutes)
            
            log_filter = LogFilter(
                start_time=start_time,
                end_time=end_time,
                levels=[LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG],
                page_size=200,
                page=1
            )
            
            log_response = await self.log_service.search_logs(log_filter)
            
            all_logs = []
            for log_entry in log_response.logs:
                all_logs.append({
                    'id': log_entry.id,
                    'timestamp': log_entry.timestamp.isoformat(),
                    'level': log_entry.level.value,
                    'service': log_entry.service.value,
                    'source': log_entry.source.value,
                    'message': log_entry.message
                })
            
            return all_logs
            
        except Exception as e:
            logger.error(f"❌ 전체 로그 조회 실패: {e}")
            return []
    
    async def check_sentry_logs_in_db(self, since_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        DB에서 Sentry 관련 로그를 조회합니다.
        
        Args:
            since_minutes: 몇 분 전부터 조회할지
            
        Returns:
            Sentry 관련 로그 목록
        """
        try:
            if not self.log_service:
                logger.error("LogService가 초기화되지 않았습니다")
                return []
            
            # 조회 시간 범위 설정
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=since_minutes)
            
            # Sentry 관련 로그 필터
            log_filter = LogFilter(
                start_time=start_time,
                end_time=end_time,
                levels=[LogLevel.ERROR],
                page_size=100,
                page=1
            )
            
            # 로그 조회
            log_response = await self.log_service.search_logs(log_filter)
            
            # Sentry 관련 로그만 필터링
            sentry_logs = []
            for log_entry in log_response.logs:
                if self._is_sentry_related_log(log_entry):
                    sentry_logs.append({
                        'id': log_entry.id,
                        'timestamp': log_entry.timestamp.isoformat(),
                        'level': log_entry.level.value,
                        'service': log_entry.service.value,
                        'source': log_entry.source.value,
                        'message': log_entry.message,
                        'context': log_entry.context.model_dump() if log_entry.context else None,
                        'metadata': log_entry.metadata.model_dump() if log_entry.metadata else None,
                        'has_stack_trace': bool(log_entry.stack_trace)
                    })
            
            logger.info(f"📊 DB에서 {len(sentry_logs)}개의 Sentry 관련 로그 발견")
            return sentry_logs
            
        except Exception as e:
            logger.error(f"❌ DB 로그 조회 실패: {e}")
            return []
    
    def _is_sentry_related_log(self, log_entry) -> bool:
        """로그가 Sentry 관련인지 확인"""
        # 메시지에 [Sentry] 포함
        if "[Sentry]" in log_entry.message:
            return True
            
        # 메타데이터에 sentry 태그 포함
        if log_entry.metadata and hasattr(log_entry.metadata, 'tags'):
            if log_entry.metadata.tags and any('sentry' in tag.lower() for tag in log_entry.metadata.tags):
                return True
        
        # 컨텍스트에 sentry infrastructure 포함
        if log_entry.context and hasattr(log_entry.context, 'infrastructure'):
            if log_entry.context.infrastructure and 'sentry' in log_entry.context.infrastructure.lower():
                return True
                
        # API 미들웨어에서 기록된 에러 (Sentry 미들웨어를 통해)
        if log_entry.message.startswith("[API]") and log_entry.metadata:
            if hasattr(log_entry.metadata, 'tags') and log_entry.metadata.tags:
                if any('sentry' in tag.lower() for tag in log_entry.metadata.tags):
                    return True
        
        return False
    
    async def run_api_error_test(self, base_url: str = "http://localhost:8000") -> bool:
        """
        API 에러 테스트를 실행합니다.
        
        Args:
            base_url: 백엔드 API URL
            
        Returns:
            테스트 실행 성공 여부
        """
        try:
            logger.info("🚀 API 에러 테스트 시작")
            self.test_start_time = datetime.utcnow()
            
            # test_api_errors.py 스크립트 실행
            script_path = Path(__file__).parent / "test_api_errors.py"
            
            cmd = [
                sys.executable, str(script_path),
                "--base-url", base_url,
                "--scenario", "all"
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60초 타임아웃
            )
            
            if process.returncode == 0:
                logger.info("✅ API 에러 테스트 완료")
                logger.info(f"테스트 출력: {process.stdout[-500:]}")  # 마지막 500자만
                return True
            else:
                logger.error(f"❌ API 에러 테스트 실패: {process.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ API 에러 테스트 타임아웃")
            return False
        except Exception as e:
            logger.error(f"❌ API 에러 테스트 실행 오류: {e}")
            return False
    
    async def run_test_and_verify(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """
        API 에러 테스트를 실행하고 DB에 저장된 결과를 검증합니다.
        """
        verification_results = {
            'test_executed': False,
            'db_logs_before': 0,
            'db_logs_after': 0,
            'new_sentry_logs': 0,
            'sentry_logs_details': [],
            'verification_passed': False,
            'errors': []
        }
        
        try:
            # 1. 초기화
            if not await self.initialize():
                verification_results['errors'].append("초기화 실패")
                return verification_results
            
            # 2. 테스트 전 DB 상태 확인
            logger.info("📊 테스트 전 DB 상태 확인")
            logs_before = await self.check_sentry_logs_in_db(since_minutes=10)
            verification_results['db_logs_before'] = len(logs_before)
            logger.info(f"테스트 전 Sentry 로그: {len(logs_before)}개")
            
            # 3. API 에러 테스트 실행
            logger.info("🔥 API 에러 테스트 실행")
            test_success = await self.run_api_error_test(base_url)
            verification_results['test_executed'] = test_success
            
            if not test_success:
                verification_results['errors'].append("API 에러 테스트 실행 실패")
                return verification_results
            
            # 4. 잠시 대기 (로그 저장 시간 확보)
            logger.info("⏱️  로그 저장 대기 중... (5초)")
            await asyncio.sleep(5)
            
            # 5. 테스트 후 DB 상태 확인
            logger.info("📊 테스트 후 DB 상태 확인")
            logs_after = await self.check_sentry_logs_in_db(since_minutes=2)
            verification_results['db_logs_after'] = len(logs_after)
            verification_results['new_sentry_logs'] = len(logs_after) - len(logs_before)
            verification_results['sentry_logs_details'] = logs_after
            
            logger.info(f"테스트 후 Sentry 로그: {len(logs_after)}개")
            logger.info(f"새로 생성된 Sentry 로그: {verification_results['new_sentry_logs']}개")
            
            # 6. 검증 결과 판정
            if verification_results['new_sentry_logs'] > 0:
                verification_results['verification_passed'] = True
                logger.info("✅ 검증 성공: Sentry 에러가 DB에 저장됨")
            else:
                verification_results['verification_passed'] = False
                verification_results['errors'].append("새로운 Sentry 로그가 DB에 저장되지 않음")
                logger.warning("⚠️  검증 실패: 새로운 Sentry 로그가 발견되지 않음")
            
        except Exception as e:
            logger.error(f"❌ 검증 과정 중 오류: {e}")
            verification_results['errors'].append(f"검증 오류: {str(e)}")
        
        return verification_results
    
    def generate_verification_report(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """검증 보고서 생성"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"sentry_db_integration_report_{timestamp}.md"
        
        status_emoji = "✅" if results['verification_passed'] else "❌"
        
        report_content = f"""# Sentry-DB 통합 검증 보고서 {status_emoji}

## 📊 검증 요약
- **검증 시간**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **API 테스트 실행**: {'✅ 성공' if results['test_executed'] else '❌ 실패'}
- **테스트 전 Sentry 로그**: {results['db_logs_before']}개
- **테스트 후 Sentry 로그**: {results['db_logs_after']}개
- **새로 생성된 로그**: {results['new_sentry_logs']}개
- **통합 검증 결과**: {'✅ 성공' if results['verification_passed'] else '❌ 실패'}

## 🎯 검증 목적
Sentry 에러 발생 시 LogService를 통해 MongoDB에 자동으로 저장되는지 확인

## 📋 상세 검증 결과

### 1. API 에러 테스트
{'✅ API 에러 테스트가 성공적으로 실행됨' if results['test_executed'] else '❌ API 에러 테스트 실행 실패'}

### 2. DB 저장 확인
"""
        
        if results['new_sentry_logs'] > 0:
            report_content += f"""
✅ **{results['new_sentry_logs']}개의 새로운 Sentry 로그가 DB에 저장됨**

#### 저장된 로그 상세:
"""
            for i, log in enumerate(results['sentry_logs_details'][-results['new_sentry_logs']:], 1):
                report_content += f"""
**{i}. {log['timestamp']}**
- **메시지**: {log['message']}
- **레벨**: {log['level']}
- **서비스**: {log['service']}
- **소스**: {log['source']}
- **스택 트레이스**: {'있음' if log['has_stack_trace'] else '없음'}
- **메타데이터**: {json.dumps(log['metadata'], ensure_ascii=False, indent=2) if log['metadata'] else '없음'}
"""
        else:
            report_content += """
❌ **새로운 Sentry 로그가 DB에 저장되지 않음**

### 가능한 원인:
1. Sentry 미들웨어가 올바르게 작동하지 않음
2. LogService 연동이 제대로 구현되지 않음  
3. API 에러가 실제로 발생하지 않음
4. DB 연결 문제
"""
        
        if results['errors']:
            report_content += f"""

### ⚠️ 발생한 오류들:
"""
            for error in results['errors']:
                report_content += f"- {error}\n"
        
        report_content += f"""

## 🔍 검증 체크리스트

### ✅ 성공 조건
- [{'x' if results['test_executed'] else ' '}] API 에러 테스트 실행 성공
- [{'x' if results['new_sentry_logs'] > 0 else ' '}] 새로운 Sentry 로그가 DB에 저장됨
- [{'x' if results['verification_passed'] else ' '}] 통합 기능이 정상 작동함

### 📝 추가 확인사항
- [ ] Sentry 대시보드에서도 동일한 에러 확인
- [ ] 로깅 대시보드에서 통합된 에러 표시 확인
- [ ] 에러 통계가 올바르게 집계되는지 확인

## 🛠️ 문제 해결 가이드

### 새로운 로그가 저장되지 않는 경우:
1. **백엔드 서버 로그 확인**: 에러 발생 및 저장 과정 로그 확인
2. **Sentry 설정 확인**: DSN 및 환경 변수 설정 점검
3. **MongoDB 연결 확인**: 데이터베이스 연결 상태 점검
4. **LogService 초기화 확인**: 서비스 의존성 주입 정상 여부 확인

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
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 검증 보고서 생성됨: {report_path}")
        logger.info(f"📄 JSON 결과 저장됨: {json_path}")
        
        return str(report_path)
    
    async def run_comprehensive_verification(self) -> ComprehensiveVerificationReport:
        """종합적인 검증 실행"""
        logger.info("🚀 종합적인 Sentry-DB-모니터링 검증 시작")
        start_time = datetime.now().isoformat()
        
        recommendations = []
        
        try:
            # 초기화
            if not await self.initialize():
                return ComprehensiveVerificationReport(
                    test_start_time=start_time,
                    test_end_time=datetime.now().isoformat(),
                    sentry_db_sync=VerificationResult(
                        test_name="초기화", success=False, expected_count=0, actual_count=0,
                        details=[], timestamp=datetime.now().isoformat(),
                        message="DB 또는 LogService 초기화 실패"
                    ),
                    monitoring_display=VerificationResult(
                        test_name="초기화", success=False, expected_count=0, actual_count=0,
                        details=[], timestamp=datetime.now().isoformat(),
                        message="초기화 실패로 인한 스킵"
                    ),
                    logging_coverage=VerificationResult(
                        test_name="초기화", success=False, expected_count=0, actual_count=0,
                        details=[], timestamp=datetime.now().isoformat(),
                        message="초기화 실패로 인한 스킵"
                    ),
                    overall_success=False,
                    recommendations=["DB 연결 및 LogService 설정 확인 필요"]
                )
            
            # 1. Sentry-DB 동기화 검증
            logger.info("1️⃣ Sentry-DB 동기화 검증")
            sentry_db_result = await self.verify_sentry_db_synchronization(test_errors_count=3)
            
            if not sentry_db_result.success:
                recommendations.append("Sentry 에러 발생 시 DB 저장 프로세스 점검 필요")
                if sentry_db_result.actual_count == 0:
                    recommendations.append("LogService와 SentryMonitoringService 연동 확인 필요")
            
            # 2. 모니터링 페이지 표시 검증
            logger.info("2️⃣ 모니터링 페이지 표시 검증")
            monitoring_result = await self.verify_monitoring_page_display()
            
            if not monitoring_result.success:
                recommendations.append("모니터링 페이지의 Sentry API 연동 상태 확인 필요")
                if monitoring_result.actual_count < monitoring_result.expected_count * 0.5:
                    recommendations.append("Sentry API와 DB 간 데이터 동기화 지연 문제 확인 필요")
            
            # 3. 로깅 시스템 포괄적 포착 검증
            logger.info("3️⃣ 로깅 시스템 포괄적 포착 검증")
            logging_result = await self.verify_comprehensive_logging_coverage()
            
            if not logging_result.success:
                recommendations.append("로깅 시스템의 에러 포착 범위 확장 필요")
                if logging_result.actual_count < logging_result.expected_count * 0.3:
                    recommendations.append("미들웨어 및 Exception Handler 설정 점검 필요")
            
            # 종합 성공 여부 판정
            overall_success = all([
                sentry_db_result.success,
                monitoring_result.success, 
                logging_result.success
            ])
            
            if overall_success:
                recommendations.append("✅ 모든 검증이 성공적으로 완료되었습니다!")
            
            end_time = datetime.now().isoformat()
            
            return ComprehensiveVerificationReport(
                test_start_time=start_time,
                test_end_time=end_time,
                sentry_db_sync=sentry_db_result,
                monitoring_display=monitoring_result,
                logging_coverage=logging_result,
                overall_success=overall_success,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ 종합 검증 중 오류 발생: {e}")
            return ComprehensiveVerificationReport(
                test_start_time=start_time,
                test_end_time=datetime.now().isoformat(),
                sentry_db_sync=VerificationResult(
                    test_name="오류", success=False, expected_count=0, actual_count=0,
                    details=[{"error": str(e)}], timestamp=datetime.now().isoformat(),
                    message=f"검증 중 오류: {str(e)}"
                ),
                monitoring_display=VerificationResult(
                    test_name="오류", success=False, expected_count=0, actual_count=0,
                    details=[], timestamp=datetime.now().isoformat(),
                    message="오류로 인한 스킵"
                ),
                logging_coverage=VerificationResult(
                    test_name="오류", success=False, expected_count=0, actual_count=0,
                    details=[], timestamp=datetime.now().isoformat(),
                    message="오류로 인한 스킵"
                ),
                overall_success=False,
                recommendations=[f"검증 프로세스 오류 해결 필요: {str(e)}"]
            )
    
    def generate_comprehensive_report(self, report: ComprehensiveVerificationReport, output_path: Optional[str] = None) -> str:
        """종합 검증 보고서 생성"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"comprehensive_sentry_verification_report_{timestamp}.md"
        
        status_emoji = "✅" if report.overall_success else "❌"
        
        report_content = f"""# 종합적인 Sentry-DB-모니터링 검증 보고서 {status_emoji}

## 📊 검증 요약
- **검증 시작**: {report.test_start_time}
- **검증 종료**: {report.test_end_time}
- **전체 결과**: {'✅ 성공' if report.overall_success else '❌ 실패'}

## 🔍 개별 검증 결과

### 1. Sentry-DB 동기화 검증 {'✅' if report.sentry_db_sync.success else '❌'}
- **결과**: {report.sentry_db_sync.message}
- **예상/실제**: {report.sentry_db_sync.expected_count}개 / {report.sentry_db_sync.actual_count}개
- **성공률**: {(report.sentry_db_sync.actual_count / report.sentry_db_sync.expected_count * 100) if report.sentry_db_sync.expected_count > 0 else 0:.1f}%

### 2. 모니터링 페이지 표시 검증 {'✅' if report.monitoring_display.success else '❌'}
- **결과**: {report.monitoring_display.message}
- **예상/실제**: {report.monitoring_display.expected_count}개 / {report.monitoring_display.actual_count}개
- **매칭률**: {(report.monitoring_display.actual_count / report.monitoring_display.expected_count * 100) if report.monitoring_display.expected_count > 0 else 0:.1f}%

### 3. 로깅 시스템 포괄적 포착 검증 {'✅' if report.logging_coverage.success else '❌'}
- **결과**: {report.logging_coverage.message}
- **예상/실제**: {report.logging_coverage.expected_count}개 / {report.logging_coverage.actual_count}개
- **포착률**: {(report.logging_coverage.actual_count / report.logging_coverage.expected_count * 100) if report.logging_coverage.expected_count > 0 else 0:.1f}%

## 🎯 상세 분석

### Sentry-DB 동기화 상세
"""
        
        if report.sentry_db_sync.details:
            for detail in report.sentry_db_sync.details:
                if isinstance(detail, dict):
                    if detail.get("sequence"):
                        report_content += f"- 에러 {detail['sequence']}: {detail.get('status', 'unknown')} ({detail.get('timestamp', 'N/A')})\n"
                    elif detail.get("error"):
                        report_content += f"- 오류: {detail['error']}\n"
        
        report_content += f"""
### 모니터링 페이지 표시 상세
"""
        
        if report.monitoring_display.details:
            for i, detail in enumerate(report.monitoring_display.details[:5], 1):  # 최대 5개만 표시
                if isinstance(detail, dict) and detail.get("sentry_error"):
                    sentry_msg = detail["sentry_error"].get("message", "N/A")
                    db_match = "✅" if detail.get("db_match") else "❌"
                    report_content += f"- {i}. {sentry_msg} → DB 매칭: {db_match}\n"
        
        report_content += f"""
### 로깅 시스템 포괄적 포착 상세
"""
        
        if report.logging_coverage.details:
            for detail in report.logging_coverage.details:
                if isinstance(detail, dict) and detail.get("scenario"):
                    scenario = detail["scenario"]
                    endpoint = detail.get("endpoint", "N/A")
                    status = detail.get("status_code", "N/A")
                    expected = "✅" if detail.get("expected_logged") else "❌"
                    report_content += f"- {scenario} ({endpoint}): HTTP {status} → 로깅 예상: {expected}\n"
        
        report_content += f"""

## 💡 개선 권장사항

"""
        
        for i, recommendation in enumerate(report.recommendations, 1):
            report_content += f"{i}. {recommendation}\n"
        
        report_content += f"""

## 🔗 추가 확인사항

### 즉시 확인할 수 있는 항목들
1. **모니터링 페이지**: http://localhost:5173/admin/monitoring
2. **Sentry 대시보드**: 설정된 Sentry 프로젝트의 Issues 페이지  
3. **로깅 대시보드**: 로그 검색 및 필터링 기능

### 명령어를 통한 추가 검증
```bash
# 현재 DB 상태 확인
python verify_sentry_db_integration.py --check-only

# 새로운 에러 발생 및 검증
python verify_sentry_db_integration.py --test-errors 5

# 종합 검증 재실행
python verify_sentry_db_integration.py --comprehensive
```

## 📈 성능 지표

- **Sentry 에러 → DB 저장**: {(report.sentry_db_sync.actual_count / report.sentry_db_sync.expected_count * 100) if report.sentry_db_sync.expected_count > 0 else 0:.1f}%
- **DB → 모니터링 페이지 표시**: {(report.monitoring_display.actual_count / report.monitoring_display.expected_count * 100) if report.monitoring_display.expected_count > 0 else 0:.1f}%
- **전체 로깅 시스템 포착**: {(report.logging_coverage.actual_count / report.logging_coverage.expected_count * 100) if report.logging_coverage.expected_count > 0 else 0:.1f}%

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
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 종합 검증 보고서 생성됨: {report_path}")
        logger.info(f"📄 JSON 결과 저장됨: {json_path}")
        
        return str(report_path)

async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Sentry-DB 통합 검증 스크립트")
    parser.add_argument("--base-url", default="http://localhost:8000", help="백엔드 API 기본 URL")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="프론트엔드 URL")
    parser.add_argument("--output", help="출력 파일명 (선택사항)")
    parser.add_argument("--check-only", action="store_true", help="테스트 실행 없이 DB 상태만 확인")
    parser.add_argument("--comprehensive", action="store_true", help="종합적인 검증 모드 실행")
    parser.add_argument("--test-errors", type=int, default=3, help="테스트할 에러 개수 (기본값: 3)")
    
    args = parser.parse_args()
    
    print("🔍 Sentry-DB 통합 검증 시작")
    print(f"🎯 백엔드 URL: {args.base_url}")
    print(f"🎯 프론트엔드 URL: {args.frontend_url}")
    
    if args.comprehensive:
        print("📊 모드: 종합적인 검증 (Sentry-DB 동기화 + 모니터링 페이지 표시 + 로깅 시스템 포괄성)")
    elif args.check_only:
        print("📊 모드: DB 상태 확인만")
    else:
        print("📊 모드: 기본 테스트 및 검증")
    
    print("-" * 60)
    
    if args.comprehensive:
        # 종합적인 검증 모드
        async with ComprehensiveSentryVerifier(args.base_url, args.frontend_url) as verifier:
            print("🚀 종합적인 검증 시작...")
            report = await verifier.run_comprehensive_verification()
            
            # 종합 보고서 생성
            report_path = verifier.generate_comprehensive_report(report, args.output)
            
            print("\n" + "=" * 60)
            print("📊 종합 검증 결과")
            print("=" * 60)
            
            # 개별 검증 결과 출력
            status_emoji = "✅" if report.sentry_db_sync.success else "❌"
            print(f"{status_emoji} 1. Sentry-DB 동기화: {report.sentry_db_sync.message}")
            
            status_emoji = "✅" if report.monitoring_display.success else "❌"
            print(f"{status_emoji} 2. 모니터링 페이지 표시: {report.monitoring_display.message}")
            
            status_emoji = "✅" if report.logging_coverage.success else "❌"
            print(f"{status_emoji} 3. 로깅 시스템 포괄적 포착: {report.logging_coverage.message}")
            
            print("-" * 40)
            
            if report.overall_success:
                print("🎉 전체 검증 성공!")
                print("✅ 모든 검증 항목이 통과했습니다.")
            else:
                print("❌ 전체 검증 실패!")
                print("⚠️  일부 검증 항목에서 문제가 발견되었습니다.")
            
            print(f"📄 상세 보고서: {report_path}")
            
            # 권장사항 출력
            if report.recommendations:
                print("\n💡 개선 권장사항:")
                for i, rec in enumerate(report.recommendations, 1):
                    print(f"  {i}. {rec}")
    
    else:
        # 기존 모드 (호환성 유지)
        verifier = ComprehensiveSentryVerifier(args.base_url, args.frontend_url)
        
        if args.check_only:
            # DB 상태만 확인
            if await verifier.initialize():
                logs = await verifier.check_sentry_logs_in_db(since_minutes=30)
                print(f"📊 지난 30분간 Sentry 관련 로그: {len(logs)}개")
                
                if logs:
                    print("\n최근 로그 목록:")
                    for i, log in enumerate(logs[-5:], 1):  # 최근 5개만 표시
                        print(f"  {i}. {log['timestamp']} - {log['message'][:80]}...")
                else:
                    print("📝 최근 Sentry 관련 로그가 없습니다.")
            else:
                print("❌ DB 초기화 실패")
        else:
            # 전체 테스트 및 검증
            results = await verifier.run_test_and_verify(args.base_url)
            report_path = verifier.generate_verification_report(results, args.output)
            
            print("\n" + "=" * 60)
            if results['verification_passed']:
                print("🎉 검증 성공!")
                print(f"✅ {results['new_sentry_logs']}개의 새로운 Sentry 로그가 DB에 저장됨")
            else:
                print("❌ 검증 실패!")
                if results['errors']:
                    print("오류 목록:")
                    for error in results['errors']:
                        print(f"  - {error}")
            
            print(f"📄 상세 보고서: {report_path}")
            print(f"📊 테스트 전: {results['db_logs_before']}개 → 테스트 후: {results['db_logs_after']}개")

if __name__ == "__main__":
    asyncio.run(main())