#!/usr/bin/env python3
"""
Sentry-DB 통합 검증 스크립트

2025-07-23 작업 버전: v1.0
주요 컴포넌트:
- SentryDbVerifier: Sentry 에러가 DB에 저장되는지 검증
- run_api_error_test: API 에러 테스트 실행
- check_db_logs: DB에서 Sentry 관련 로그 조회
- verify_integration: 통합 테스트 및 검증

주요 함수:
- main(): 메인 실행 함수 (line 300-350)
- run_test_and_verify(): 테스트 실행 및 검증 (line 180-250)  
- check_sentry_logs_in_db(): DB에서 Sentry 로그 조회 (line 80-150)
- generate_verification_report(): 검증 보고서 생성 (line 250-300)

코드 라인 정보:
- 설정 및 초기화: 1-80
- DB 조회 및 검증: 81-180
- 테스트 실행 및 보고서: 181-350

관련 파일:
- test_api_errors.py: API 에러 발생 테스트 스크립트
- ../backend/nadle_backend/services/sentry_monitoring_service.py: Sentry 모니터링 서비스
- ../backend/nadle_backend/logging/services/log_service.py: 로그 서비스
"""

import asyncio
import subprocess
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
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

class SentryDbVerifier:
    """Sentry-DB 통합 검증 클래스"""
    
    def __init__(self):
        self.database = None
        self.log_service = None
        self.test_start_time = None
        self.results = {}
    
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

async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Sentry-DB 통합 검증 스크립트")
    parser.add_argument("--base-url", default="http://localhost:8000", help="백엔드 API 기본 URL")
    parser.add_argument("--output", help="출력 파일명 (선택사항)")
    parser.add_argument("--check-only", action="store_true", help="테스트 실행 없이 DB 상태만 확인")
    
    args = parser.parse_args()
    
    print("🔍 Sentry-DB 통합 검증 시작")
    print(f"🎯 대상 URL: {args.base_url}")
    print(f"📊 모드: {'DB 상태 확인만' if args.check_only else '전체 테스트 및 검증'}")
    print("-" * 60)
    
    verifier = SentryDbVerifier()
    
    if args.check_only:
        # DB 상태만 확인
        if await verifier.initialize():
            logs = await verifier.check_sentry_logs_in_db(since_minutes=30)
            print(f"📊 지난 30분간 Sentry 관련 로그: {len(logs)}개")
            
            for i, log in enumerate(logs[-5:], 1):  # 최근 5개만 표시
                print(f"  {i}. {log['timestamp']} - {log['message'][:80]}...")
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