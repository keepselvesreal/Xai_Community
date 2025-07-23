#!/usr/bin/env python3
"""
작성 시간: 2025-07-23 10:16 KST
작업 버전: v1.0
주요 컴포넌트들:
- CacheSystemTester: 캐싱 시스템 종합 테스트 클래스
- RedisFactoryTester: Redis 팩토리 패턴 테스트
- CacheServiceTester: 캐시 서비스 테스트
- SessionServiceTester: 세션 서비스 테스트 
- TokenBlacklistTester: 토큰 블랙리스트 서비스 테스트
- CacheTestReportGenerator: 테스트 결과 보고서 생성기

주요 함수들:
- test_redis_factory_selection: Redis 팩토리 환경별 선택 테스트 (lines 45-80)
- test_cache_service_operations: 캐시 서비스 CRUD 작업 테스트 (lines 95-150)
- test_session_management: 세션 관리 기능 테스트 (lines 165-220)
- test_token_blacklist_operations: 토큰 블랙리스트 작업 테스트 (lines 235-290)
- test_environment_namespacing: 환경별 키 네임스페이싱 테스트 (lines 305-350)
- generate_test_report: HTML 형식 테스트 보고서 생성 (lines 365-420)

관련 파일들:
- redis_factory.py: Redis 팩토리 패턴 구현
- cache_service.py: 기본 캐싱 서비스
- session_service.py: 세션 관리 서비스
- token_blacklist_service.py: 토큰 블랙리스트 서비스
- redis.py, upstash_redis.py: Redis 매니저 구현체들
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import uuid
import logging

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 백엔드 모듈 import
try:
    from nadle_backend.database.redis_factory import (
        get_redis_manager, 
        ensure_redis_connection, 
        get_prefixed_key,
        get_redis_health,
        redis_factory
    )
    from nadle_backend.services.cache_service import cache_service
    from nadle_backend.services.session_service import session_service, SessionData
    from nadle_backend.services.token_blacklist_service import token_blacklist_service
    from nadle_backend.config import get_settings
except ImportError as e:
    logger.error(f"백엔드 모듈 import 실패: {e}")
    sys.exit(1)

@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    duration: float
    message: str
    details: Dict[str, Any] = None
    error: Optional[str] = None

@dataclass
class TestSuite:
    """테스트 스위트 데이터 클래스"""
    name: str
    results: List[TestResult]
    total_duration: float
    start_time: datetime
    end_time: datetime

class CacheSystemTester:
    """캐싱 시스템 종합 테스트 클래스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.test_suites: List[TestSuite] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 캐싱 시스템 테스트 실행"""
        logger.info("🚀 캐싱 시스템 종합 테스트 시작")
        
        overall_start = datetime.now()
        
        # 1. Redis 팩토리 테스트
        factory_suite = await self._test_redis_factory()
        self.test_suites.append(factory_suite)
        
        # 2. 캐시 서비스 테스트
        cache_suite = await self._test_cache_service()
        self.test_suites.append(cache_suite)
        
        # 3. 세션 서비스 테스트
        session_suite = await self._test_session_service()
        self.test_suites.append(session_suite)
        
        # 4. 토큰 블랙리스트 테스트
        blacklist_suite = await self._test_token_blacklist()
        self.test_suites.append(blacklist_suite)
        
        # 5. 환경별 네임스페이싱 테스트
        namespacing_suite = await self._test_environment_namespacing()
        self.test_suites.append(namespacing_suite)
        
        # 6. 성능 테스트
        performance_suite = await self._test_performance()
        self.test_suites.append(performance_suite)
        
        overall_end = datetime.now()
        
        # 통계 계산
        for suite in self.test_suites:
            for result in suite.results:
                self.total_tests += 1
                if result.status == "PASS":
                    self.passed_tests += 1
                elif result.status == "FAIL":
                    self.failed_tests += 1
                else:
                    self.skipped_tests += 1
        
        summary = {
            "test_summary": {
                "total_tests": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                "total_duration": (overall_end - overall_start).total_seconds(),
                "start_time": overall_start.isoformat(),
                "end_time": overall_end.isoformat()
            },
            "environment_info": {
                "environment": self.settings.environment,
                "redis_type": "upstash" if self.settings.use_upstash_redis else "local",
                "cache_enabled": self.settings.cache_enabled,
                "key_prefix": self.settings.redis_key_prefix
            },
            "test_suites": self.test_suites
        }
        
        logger.info(f"✅ 캐싱 시스템 종합 테스트 완료: {self.passed_tests}/{self.total_tests} 통과")
        return summary

    async def _test_redis_factory(self) -> TestSuite:
        """Redis 팩토리 패턴 테스트"""
        suite_name = "Redis Factory Pattern Tests"
        logger.info(f"🔧 {suite_name} 시작")
        
        start_time = datetime.now()
        results = []
        
        # 테스트 1: Redis 매니저 인스턴스 획득
        test_start = time.time()
        try:
            manager = await get_redis_manager()
            assert manager is not None, "Redis 매니저 인스턴스가 None입니다"
            
            results.append(TestResult(
                test_name="Redis Manager Instance Retrieval",
                status="PASS",
                duration=time.time() - test_start,
                message="Redis 매니저 인스턴스 정상 획득",
                details={"manager_type": type(manager).__name__}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Redis Manager Instance Retrieval",
                status="FAIL",
                duration=time.time() - test_start,
                message="Redis 매니저 인스턴스 획득 실패",
                error=str(e)
            ))
        
        # 테스트 2: Redis 연결 테스트
        test_start = time.time()
        try:
            connected = await ensure_redis_connection()
            
            results.append(TestResult(
                test_name="Redis Connection Test",
                status="PASS" if connected else "FAIL",
                duration=time.time() - test_start,
                message="Redis 연결 성공" if connected else "Redis 연결 실패",
                details={"connected": connected}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Redis Connection Test",
                status="FAIL",
                duration=time.time() - test_start,
                message="Redis 연결 테스트 중 오류",
                error=str(e)
            ))
        
        # 테스트 3: Redis 상태 확인
        test_start = time.time()
        try:
            health = await get_redis_health()
            assert health is not None, "Redis 상태 정보가 None입니다"
            assert "status" in health, "Redis 상태 정보에 status 필드가 없습니다"
            
            results.append(TestResult(
                test_name="Redis Health Check",
                status="PASS",
                duration=time.time() - test_start,
                message=f"Redis 상태 확인 성공: {health.get('status')}",
                details=health
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Redis Health Check",
                status="FAIL",
                duration=time.time() - test_start,
                message="Redis 상태 확인 실패",
                error=str(e)
            ))
        
        # 테스트 4: 키 프리픽스 확인
        test_start = time.time()
        try:
            test_key = "test_key"
            prefixed_key = get_prefixed_key(test_key)
            expected_prefix = self.settings.redis_key_prefix
            
            if expected_prefix:
                assert prefixed_key.startswith(expected_prefix), f"키 프리픽스가 올바르지 않습니다: {prefixed_key}"
            
            results.append(TestResult(
                test_name="Key Prefix Validation",
                status="PASS",
                duration=time.time() - test_start,
                message="키 프리픽스 정상 적용",
                details={
                    "original_key": test_key,
                    "prefixed_key": prefixed_key,
                    "expected_prefix": expected_prefix
                }
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Key Prefix Validation",
                status="FAIL",
                duration=time.time() - test_start,
                message="키 프리픽스 검증 실패",
                error=str(e)
            ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        return TestSuite(
            name=suite_name,
            results=results,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )

    async def _test_cache_service(self) -> TestSuite:
        """캐시 서비스 테스트"""
        suite_name = "Cache Service Tests"
        logger.info(f"💾 {suite_name} 시작")
        
        start_time = datetime.now()
        results = []
        
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        test_user_data = {
            "id": test_user_id,
            "email": "test@example.com",
            "user_handle": "testuser",
            "display_name": "Test User",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }
        
        # 테스트 1: 사용자 캐시 저장
        test_start = time.time()
        try:
            success = await cache_service.set_user_cache(test_user_id, test_user_data)
            assert success, "사용자 캐시 저장 실패"
            
            results.append(TestResult(
                test_name="User Cache Set Operation",
                status="PASS",
                duration=time.time() - test_start,
                message="사용자 캐시 저장 성공",
                details={"user_id": test_user_id, "success": success}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="User Cache Set Operation",
                status="FAIL",
                duration=time.time() - test_start,
                message="사용자 캐시 저장 실패",
                error=str(e)
            ))
        
        # 테스트 2: 사용자 캐시 조회
        test_start = time.time()
        try:
            cached_data = await cache_service.get_user_cache(test_user_id)
            assert cached_data is not None, "캐시된 사용자 데이터를 찾을 수 없습니다"
            assert cached_data["id"] == test_user_id, "캐시된 사용자 ID가 일치하지 않습니다"
            
            results.append(TestResult(
                test_name="User Cache Get Operation",
                status="PASS",
                duration=time.time() - test_start,
                message="사용자 캐시 조회 성공",
                details={"user_id": test_user_id, "data_found": cached_data is not None}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="User Cache Get Operation",
                status="FAIL",
                duration=time.time() - test_start,
                message="사용자 캐시 조회 실패",
                error=str(e)
            ))
        
        # 테스트 3: 사용자 캐시 삭제
        test_start = time.time()
        try:
            deleted = await cache_service.delete_user_cache(test_user_id)
            assert deleted, "사용자 캐시 삭제 실패"
            
            # 삭제 후 조회하여 삭제 확인
            cached_after_delete = await cache_service.get_user_cache(test_user_id)
            assert cached_after_delete is None, "캐시 삭제 후에도 데이터가 남아있습니다"
            
            results.append(TestResult(
                test_name="User Cache Delete Operation",
                status="PASS",
                duration=time.time() - test_start,
                message="사용자 캐시 삭제 성공",
                details={"user_id": test_user_id, "deleted": deleted}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="User Cache Delete Operation",
                status="FAIL",
                duration=time.time() - test_start,
                message="사용자 캐시 삭제 실패",
                error=str(e)
            ))
        
        # 테스트 4: 캐시 통계 조회
        test_start = time.time()
        try:
            stats = await cache_service.get_cache_stats()
            assert stats is not None, "캐시 통계 정보가 None입니다"
            assert "cache_enabled" in stats, "캐시 통계에 cache_enabled 필드가 없습니다"
            
            results.append(TestResult(
                test_name="Cache Statistics Retrieval",
                status="PASS",
                duration=time.time() - test_start,
                message="캐시 통계 조회 성공",
                details=stats
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Cache Statistics Retrieval",
                status="FAIL",
                duration=time.time() - test_start,
                message="캐시 통계 조회 실패",
                error=str(e)
            ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        return TestSuite(
            name=suite_name,
            results=results,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )

    async def _test_session_service(self) -> TestSuite:
        """세션 서비스 테스트"""
        suite_name = "Session Service Tests"
        logger.info(f"🔐 {suite_name} 시작")
        
        start_time = datetime.now()
        results = []
        
        test_user_id = f"session_user_{uuid.uuid4().hex[:8]}"
        session_data = SessionData(
            user_id=test_user_id,
            email="session@example.com",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        session_id = None
        
        # 테스트 1: 세션 생성
        test_start = time.time()
        try:
            session_id = await session_service.create_session(session_data, ttl=3600)
            assert session_id is not None, "세션 생성 실패"
            
            results.append(TestResult(
                test_name="Session Creation",
                status="PASS",
                duration=time.time() - test_start,
                message="세션 생성 성공",
                details={"session_id": session_id, "user_id": test_user_id}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Session Creation",
                status="FAIL",
                duration=time.time() - test_start,
                message="세션 생성 실패",
                error=str(e)
            ))
        
        # 테스트 2: 세션 조회
        if session_id:
            test_start = time.time()
            try:
                retrieved_session = await session_service.get_session(session_id)
                assert retrieved_session is not None, "세션 조회 실패"
                assert retrieved_session.user_id == test_user_id, "세션 사용자 ID 불일치"
                
                results.append(TestResult(
                    test_name="Session Retrieval",
                    status="PASS",
                    duration=time.time() - test_start,
                    message="세션 조회 성공",
                    details={"session_id": session_id, "user_id": retrieved_session.user_id}
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name="Session Retrieval",
                    status="FAIL",
                    duration=time.time() - test_start,
                    message="세션 조회 실패",
                    error=str(e)
                ))
        
        # 테스트 3: 사용자 세션 목록 조회
        test_start = time.time()
        try:
            user_sessions = await session_service.get_user_sessions(test_user_id)
            assert isinstance(user_sessions, list), "사용자 세션 목록이 리스트가 아닙니다"
            
            results.append(TestResult(
                test_name="User Sessions List",
                status="PASS",
                duration=time.time() - test_start,
                message="사용자 세션 목록 조회 성공",
                details={"user_id": test_user_id, "session_count": len(user_sessions)}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="User Sessions List",
                status="FAIL",
                duration=time.time() - test_start,
                message="사용자 세션 목록 조회 실패",
                error=str(e)
            ))
        
        # 테스트 4: 세션 삭제
        if session_id:
            test_start = time.time()
            try:
                deleted = await session_service.delete_session(session_id)
                assert deleted, "세션 삭제 실패"
                
                # 삭제 후 조회하여 삭제 확인
                deleted_session = await session_service.get_session(session_id)
                assert deleted_session is None, "세션 삭제 후에도 세션이 남아있습니다"
                
                results.append(TestResult(
                    test_name="Session Deletion",
                    status="PASS",
                    duration=time.time() - test_start,
                    message="세션 삭제 성공",
                    details={"session_id": session_id, "deleted": deleted}
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name="Session Deletion",
                    status="FAIL",
                    duration=time.time() - test_start,
                    message="세션 삭제 실패",
                    error=str(e)
                ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        return TestSuite(
            name=suite_name,
            results=results,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )

    async def _test_token_blacklist(self) -> TestSuite:
        """토큰 블랙리스트 서비스 테스트"""
        suite_name = "Token Blacklist Service Tests"
        logger.info(f"🚫 {suite_name} 시작")
        
        start_time = datetime.now()
        results = []
        
        test_token = f"test_token_{uuid.uuid4().hex}"
        test_jti = f"test_jti_{uuid.uuid4().hex[:16]}"
        test_user_id = f"blacklist_user_{uuid.uuid4().hex[:8]}"
        expires_at = datetime.now() + timedelta(hours=1)
        
        # 테스트 1: 토큰 블랙리스트 추가
        test_start = time.time()
        try:
            success = await token_blacklist_service.blacklist_token(
                test_token, expires_at, "test_reason", test_user_id
            )
            assert success, "토큰 블랙리스트 추가 실패"
            
            results.append(TestResult(
                test_name="Token Blacklist Addition",
                status="PASS",
                duration=time.time() - test_start,
                message="토큰 블랙리스트 추가 성공",
                details={"token_prefix": test_token[:20], "user_id": test_user_id}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Token Blacklist Addition",
                status="FAIL",
                duration=time.time() - test_start,
                message="토큰 블랙리스트 추가 실패",
                error=str(e)
            ))
        
        # 테스트 2: 토큰 블랙리스트 확인
        test_start = time.time()
        try:
            is_blacklisted = await token_blacklist_service.is_blacklisted(test_token)
            assert is_blacklisted, "블랙리스트된 토큰이 확인되지 않습니다"
            
            results.append(TestResult(
                test_name="Token Blacklist Check",
                status="PASS",
                duration=time.time() - test_start,
                message="토큰 블랙리스트 확인 성공",
                details={"is_blacklisted": is_blacklisted}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Token Blacklist Check",
                status="FAIL",
                duration=time.time() - test_start,
                message="토큰 블랙리스트 확인 실패",
                error=str(e)
            ))
        
        # 테스트 3: JTI 블랙리스트 추가 및 확인
        test_start = time.time()
        try:
            jti_success = await token_blacklist_service.blacklist_token_by_jti(
                test_jti, expires_at, "jti_test_reason"
            )
            assert jti_success, "JTI 블랙리스트 추가 실패"
            
            is_jti_blacklisted = await token_blacklist_service.is_blacklisted_by_jti(test_jti)
            assert is_jti_blacklisted, "블랙리스트된 JTI가 확인되지 않습니다"
            
            results.append(TestResult(
                test_name="JTI Blacklist Operations",
                status="PASS",
                duration=time.time() - test_start,
                message="JTI 블랙리스트 작업 성공",
                details={"jti": test_jti, "is_blacklisted": is_jti_blacklisted}
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="JTI Blacklist Operations",
                status="FAIL",
                duration=time.time() - test_start,
                message="JTI 블랙리스트 작업 실패",
                error=str(e)
            ))
        
        # 테스트 4: 블랙리스트 정보 조회
        test_start = time.time()
        try:
            blacklist_info = await token_blacklist_service.get_blacklist_info(test_token)
            assert blacklist_info is not None, "블랙리스트 정보 조회 실패"
            assert "reason" in blacklist_info, "블랙리스트 정보에 reason 필드가 없습니다"
            
            results.append(TestResult(
                test_name="Blacklist Info Retrieval",
                status="PASS",
                duration=time.time() - test_start,
                message="블랙리스트 정보 조회 성공",
                details=blacklist_info
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Blacklist Info Retrieval",
                status="FAIL",
                duration=time.time() - test_start,
                message="블랙리스트 정보 조회 실패",
                error=str(e)
            ))
        
        # 테스트 5: 블랙리스트 통계
        test_start = time.time()
        try:
            stats = await token_blacklist_service.get_blacklist_stats()
            assert stats is not None, "블랙리스트 통계 조회 실패"
            assert "status" in stats, "블랙리스트 통계에 status 필드가 없습니다"
            
            results.append(TestResult(
                test_name="Blacklist Statistics",
                status="PASS",
                duration=time.time() - test_start,
                message="블랙리스트 통계 조회 성공",
                details=stats
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Blacklist Statistics",
                status="FAIL",
                duration=time.time() - test_start,
                message="블랙리스트 통계 조회 실패",
                error=str(e)
            ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        return TestSuite(
            name=suite_name,
            results=results,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )

    async def _test_environment_namespacing(self) -> TestSuite:
        """환경별 키 네임스페이싱 테스트"""
        suite_name = "Environment Namespacing Tests"
        logger.info(f"🏷️ {suite_name} 시작")
        
        start_time = datetime.now()
        results = []
        
        # 테스트 1: 키 프리픽스 적용 확인
        test_start = time.time()
        try:
            test_keys = ["user:123", "session:abc", "cache:data"]
            expected_prefix = self.settings.redis_key_prefix
            
            for key in test_keys:
                prefixed_key = get_prefixed_key(key)
                if expected_prefix:
                    assert prefixed_key.startswith(expected_prefix), f"키 {key}에 프리픽스가 올바르게 적용되지 않음"
                    assert prefixed_key == f"{expected_prefix}{key}", f"키 형식이 잘못됨: {prefixed_key}"
                else:
                    assert prefixed_key == key, f"프리픽스가 없을 때 원본 키가 반환되어야 함: {prefixed_key}"
            
            results.append(TestResult(
                test_name="Key Prefix Application",
                status="PASS",
                duration=time.time() - test_start,
                message="키 프리픽스 적용 확인 성공",
                details={
                    "test_keys": test_keys,
                    "expected_prefix": expected_prefix,
                    "prefixed_keys": [get_prefixed_key(k) for k in test_keys]
                }
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Key Prefix Application",
                status="FAIL",
                duration=time.time() - test_start,
                message="키 프리픽스 적용 확인 실패",
                error=str(e)
            ))
        
        # 테스트 2: 환경별 격리 테스트
        test_start = time.time()
        try:
            manager = await get_redis_manager()
            test_key = "isolation_test"
            test_value = {"env": self.settings.environment, "timestamp": datetime.now().isoformat()}
            
            # 데이터 저장
            prefixed_key = get_prefixed_key(test_key)
            success = await manager.set(prefixed_key, test_value, ttl=300)
            assert success, "테스트 데이터 저장 실패"
            
            # 데이터 조회
            retrieved = await manager.get(prefixed_key)
            assert retrieved is not None, "저장된 데이터 조회 실패"
            assert retrieved["env"] == self.settings.environment, "환경 정보 불일치"
            
            # 정리
            await manager.delete(prefixed_key)
            
            results.append(TestResult(
                test_name="Environment Isolation Test",
                status="PASS",
                duration=time.time() - test_start,
                message="환경별 격리 테스트 성공",
                details={
                    "environment": self.settings.environment,
                    "test_key": test_key,
                    "prefixed_key": prefixed_key,
                    "data_match": retrieved["env"] == self.settings.environment
                }
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Environment Isolation Test",
                status="FAIL",
                duration=time.time() - test_start,
                message="환경별 격리 테스트 실패",
                error=str(e)
            ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        return TestSuite(
            name=suite_name,
            results=results,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )

    async def _test_performance(self) -> TestSuite:
        """캐싱 시스템 성능 테스트"""
        suite_name = "Performance Tests"
        logger.info(f"⚡ {suite_name} 시작")
        
        start_time = datetime.now()
        results = []
        
        # 테스트 1: 대량 데이터 처리 성능
        test_start = time.time()
        try:
            manager = await get_redis_manager()
            test_count = 100
            test_data = {"data": "performance_test", "index": 0}
            
            # 대량 저장 테스트
            store_start = time.time()
            for i in range(test_count):
                test_data["index"] = i
                key = get_prefixed_key(f"perf_test:{i}")
                await manager.set(key, test_data, ttl=300)
            store_duration = time.time() - store_start
            
            # 대량 조회 테스트
            retrieve_start = time.time()
            retrieved_count = 0
            for i in range(test_count):
                key = get_prefixed_key(f"perf_test:{i}")
                data = await manager.get(key)
                if data:
                    retrieved_count += 1
            retrieve_duration = time.time() - retrieve_start
            
            # 정리
            for i in range(test_count):
                key = get_prefixed_key(f"perf_test:{i}")
                await manager.delete(key)
            
            results.append(TestResult(
                test_name="Bulk Operations Performance",
                status="PASS",
                duration=time.time() - test_start,
                message="대량 데이터 처리 성능 테스트 완료",
                details={
                    "test_count": test_count,
                    "store_duration": store_duration,
                    "retrieve_duration": retrieve_duration,
                    "store_ops_per_sec": test_count / store_duration,
                    "retrieve_ops_per_sec": test_count / retrieve_duration,
                    "retrieved_count": retrieved_count
                }
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="Bulk Operations Performance",
                status="FAIL",
                duration=time.time() - test_start,
                message="대량 데이터 처리 성능 테스트 실패",
                error=str(e)
            ))
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        return TestSuite(
            name=suite_name,
            results=results,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )

class CacheTestReportGenerator:
    """캐시 테스트 결과 보고서 생성기"""
    
    @staticmethod
    def generate_html_report(test_results: Dict[str, Any], output_path: str) -> str:
        """HTML 형식 테스트 보고서 생성"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>캐싱 시스템 테스트 보고서</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .metric {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        .metric.success {{ background: #d4edda; color: #155724; }}
        .metric.warning {{ background: #fff3cd; color: #856404; }}
        .metric.danger {{ background: #f8d7da; color: #721c24; }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .environment-info {{
            padding: 20px 30px;
            background: #e9ecef;
            border-left: 4px solid #007bff;
        }}
        .test-suite {{
            margin: 20px 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        .suite-header {{
            background: #343a40;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
        }}
        .test-result {{
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-result:last-child {{
            border-bottom: none;
        }}
        .test-name {{
            font-weight: 500;
        }}
        .test-status {{
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        .status-pass {{ background: #28a745; color: white; }}
        .status-fail {{ background: #dc3545; color: white; }}
        .status-skip {{ background: #6c757d; color: white; }}
        .test-details {{
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .error {{
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 캐싱 시스템 테스트 보고서</h1>
            <p>생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}</p>
        </div>
        
        <div class="summary">
            <div class="metric success">
                <div class="metric-value">{test_results['test_summary']['passed']}</div>
                <div>통과</div>
            </div>
            <div class="metric danger">
                <div class="metric-value">{test_results['test_summary']['failed']}</div>
                <div>실패</div>
            </div>
            <div class="metric warning">
                <div class="metric-value">{test_results['test_summary']['skipped']}</div>
                <div>건너뜀</div>
            </div>
            <div class="metric">
                <div class="metric-value">{test_results['test_summary']['success_rate']:.1f}%</div>
                <div>성공률</div>
            </div>
            <div class="metric">
                <div class="metric-value">{test_results['test_summary']['total_duration']:.2f}s</div>
                <div>총 소요시간</div>
            </div>
        </div>
        
        <div class="environment-info">
            <h3>🌍 환경 정보</h3>
            <ul>
                <li><strong>환경:</strong> {test_results['environment_info']['environment']}</li>
                <li><strong>Redis 타입:</strong> {test_results['environment_info']['redis_type']}</li>
                <li><strong>캐시 활성화:</strong> {test_results['environment_info']['cache_enabled']}</li>
                <li><strong>키 프리픽스:</strong> {test_results['environment_info']['key_prefix'] or 'None'}</li>
            </ul>
        </div>
"""
        
        # 테스트 스위트별 결과 추가
        for suite in test_results['test_suites']:
            suite_pass_count = sum(1 for r in suite.results if r.status == "PASS")
            suite_total_count = len(suite.results)
            
            html_content += f"""
        <div class="test-suite">
            <div class="suite-header">
                {suite.name} ({suite_pass_count}/{suite_total_count} 통과, {suite.total_duration:.2f}s)
            </div>
"""
            
            for result in suite.results:
                status_class = f"status-{result.status.lower()}"
                html_content += f"""
            <div class="test-result">
                <div>
                    <div class="test-name">{result.test_name}</div>
                    <div style="font-size: 0.9em; color: #6c757d;">
                        {result.message} (소요시간: {result.duration:.3f}s)
                    </div>
"""
                
                if result.details:
                    html_content += f"""
                    <div class="test-details">
                        <strong>상세 정보:</strong><br>
                        <pre>{json.dumps(result.details, indent=2, ensure_ascii=False)}</pre>
                    </div>
"""
                
                if result.error:
                    html_content += f"""
                    <div class="error">
                        <strong>오류:</strong> {result.error}
                    </div>
"""
                
                html_content += f"""
                </div>
                <div class="test-status {status_class}">{result.status}</div>
            </div>
"""
            
            html_content += "        </div>\n"
        
        html_content += f"""
        <div class="footer">
            <p>이 보고서는 캐싱 시스템 종합 테스트 스크립트에 의해 자동 생성되었습니다.</p>
            <p>테스트 시간: {test_results['test_summary']['start_time']} ~ {test_results['test_summary']['end_time']}</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    @staticmethod
    def generate_json_report(test_results: Dict[str, Any], output_path: str) -> str:
        """JSON 형식 테스트 보고서 생성"""
        
        # TestSuite와 TestResult 객체를 딕셔너리로 변환
        serializable_results = {}
        serializable_results.update(test_results)
        
        # test_suites를 직렬화 가능한 형태로 변환
        serializable_suites = []
        for suite in test_results['test_suites']:
            suite_dict = {
                "name": suite.name,
                "total_duration": suite.total_duration,
                "start_time": suite.start_time.isoformat(),
                "end_time": suite.end_time.isoformat(),
                "results": []
            }
            
            for result in suite.results:
                result_dict = {
                    "test_name": result.test_name,
                    "status": result.status,
                    "duration": result.duration,
                    "message": result.message,
                    "details": result.details,
                    "error": result.error
                }
                suite_dict["results"].append(result_dict)
            
            serializable_suites.append(suite_dict)
        
        serializable_results['test_suites'] = serializable_suites
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        return output_path

async def main():
    """메인 함수"""
    logger.info("🚀 캐싱 시스템 종합 테스트 시작")
    
    # 출력 디렉터리 생성
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    # 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # 테스트 실행
        tester = CacheSystemTester()
        test_results = await tester.run_comprehensive_test()
        
        # 보고서 생성
        report_generator = CacheTestReportGenerator()
        
        # HTML 보고서
        html_path = output_dir / f"cache_system_test_report_{timestamp}.html"
        html_report = report_generator.generate_html_report(test_results, str(html_path))
        
        # JSON 보고서
        json_path = output_dir / f"cache_system_test_report_{timestamp}.json"
        json_report = report_generator.generate_json_report(test_results, str(json_path))
        
        # 결과 출력
        summary = test_results['test_summary']
        logger.info(f"✅ 테스트 완료!")
        logger.info(f"   총 테스트: {summary['total_tests']}")
        logger.info(f"   통과: {summary['passed']}")
        logger.info(f"   실패: {summary['failed']}")
        logger.info(f"   건너뜀: {summary['skipped']}")
        logger.info(f"   성공률: {summary['success_rate']:.1f}%")
        logger.info(f"   소요시간: {summary['total_duration']:.2f}초")
        logger.info(f"📊 HTML 보고서: {html_report}")
        logger.info(f"📁 JSON 보고서: {json_report}")
        
        # 실패한 테스트가 있으면 종료 코드 1 반환
        if summary['failed'] > 0:
            logger.warning(f"⚠️ {summary['failed']}개의 테스트가 실패했습니다.")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 심각한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)