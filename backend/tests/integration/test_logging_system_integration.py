"""
로깅 시스템 통합 테스트

이 모듈은 로깅 시스템의 전체 플로우를 테스트합니다:
- Repository → Service → API 전체 스택 테스트
- 외부 adapter들의 실제 동작 테스트
- API 엔드포인트 통합 테스트
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from nadle_backend.core.logging import (
    LogLevel,
    LogServiceType,
    LogSource,
    LogEntry,
    LogContext,
    LogMetadata,
    LogFilter,
)
from nadle_backend.logging.services.log_service import LogService
from nadle_backend.logging.repositories.mongo_log_repository import MongoLogRepository
from nadle_backend.logging.adapters import (
    VercelLogAdapter,
    UpstashLogAdapter,
    CloudRunLogAdapter,
    AtlasLogAdapter,
)


class TestLoggingSystemIntegration:
    """로깅 시스템 전체 통합 테스트"""

    @pytest.fixture
    async def logging_service(self, test_db: AsyncIOMotorDatabase):
        """로깅 서비스 fixture"""
        repository = MongoLogRepository(test_db)
        service = LogService(repository)
        return service

    @pytest.fixture
    def sample_log_entry(self):
        """샘플 로그 엔트리 fixture"""
        return LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            service=LogServiceType.API,
            source=LogSource.INTERNAL,
            message="Integration test log entry",
            context=LogContext(
                user_id="test_user_123",
                request_id="req_12345",
                endpoint="/api/test",
                method="GET",
                status_code=200,
                response_time=150.5,
                ip_address="127.0.0.1",
                user_agent="pytest/integration-test"
            ),
            metadata=LogMetadata(
                request_id="req_12345",
                user_id="test_user_123",
                tags=["integration", "test", "api"],
                custom={
                    "test_type": "integration",
                    "test_module": "logging_system",
                    "environment": "test"
                }
            )
        )

    @pytest.mark.asyncio
    async def test_full_logging_pipeline(self, logging_service: LogService, sample_log_entry: LogEntry):
        """전체 로깅 파이프라인 테스트: Repository → Service 전체 플로우"""
        
        # 1. 로그 저장
        saved_log = await logging_service.log_internal(
            level=sample_log_entry.level,
            service=sample_log_entry.service,
            message=sample_log_entry.message,
            context=sample_log_entry.context,
            metadata=sample_log_entry.metadata
        )
        
        assert saved_log is not None
        assert saved_log.id is not None
        assert saved_log.message == sample_log_entry.message
        assert saved_log.level == sample_log_entry.level
        assert saved_log.service == sample_log_entry.service
        assert saved_log.source == LogSource.INTERNAL
        
        # 2. 로그 조회
        filter_obj = LogFilter(
            limit=10,
            service=sample_log_entry.service
        )
        search_result = await logging_service.search_logs(filter_obj)
        
        assert len(search_result.logs) >= 1
        retrieved_log = next((log for log in search_result.logs if log.id == saved_log.id), None)
        assert retrieved_log is not None
        assert retrieved_log.message == sample_log_entry.message
        
        # 3. 로그 개수 확인
        count_filter = LogFilter(service=sample_log_entry.service)
        log_count = await logging_service.count_logs(count_filter)
        assert log_count >= 1
        
        # 4. 시간 범위 필터링 테스트
        start_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        end_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        time_filter = LogFilter(
            service=sample_log_entry.service,
            start_time=start_time,
            end_time=end_time
        )
        time_filtered_result = await logging_service.search_logs(time_filter)
        
        assert len(time_filtered_result.logs) >= 1
        assert any(log.id == saved_log.id for log in time_filtered_result.logs)

    @pytest.mark.asyncio
    async def test_batch_external_log_collection(self, logging_service: LogService):
        """배치 외부 로그 수집 테스트"""
        
        # 여러 외부 서비스의 mock 로그들을 수집
        external_logs = []
        
        # Vercel 로그 수집
        vercel_adapter = VercelLogAdapter("mock_token", "mock_project", use_mock=True)
        vercel_logs = await vercel_adapter.collect_logs(hours=1)
        external_logs.extend(vercel_logs)
        
        # Upstash 로그 수집
        upstash_adapter = UpstashLogAdapter("mock_url", "mock_token", use_mock=True)
        upstash_logs = await upstash_adapter.collect_logs(hours=1)
        external_logs.extend(upstash_logs)
        
        # Cloud Run 로그 수집
        cloudrun_adapter = CloudRunLogAdapter("mock_project", use_mock=True)
        cloudrun_logs = await cloudrun_adapter.collect_logs(hours=1)
        external_logs.extend(cloudrun_logs)
        
        # Atlas 로그 수집
        atlas_adapter = AtlasLogAdapter("mock_key", "mock_group", "mock_cluster", use_mock=True)
        atlas_logs = await atlas_adapter.collect_logs(hours=1)
        external_logs.extend(atlas_logs)
        
        # 수집된 로그들 검증
        assert len(external_logs) > 0
        
        # 각 서비스 타입별로 로그가 있는지 확인
        service_types = set(log.service for log in external_logs)
        expected_services = {LogServiceType.VERCEL, LogServiceType.REDIS, LogServiceType.CLOUD_RUN, LogServiceType.DATABASE}
        assert expected_services.issubset(service_types)
        
        # 모든 로그가 EXTERNAL 소스인지 확인
        assert all(log.source == LogSource.EXTERNAL for log in external_logs)
        
        # 외부 로그들을 데이터베이스에 저장
        saved_external_logs = await logging_service.save_external_logs(external_logs)
        
        assert len(saved_external_logs) == len(external_logs)
        assert all(log.id is not None for log in saved_external_logs)
        
        # 저장된 외부 로그들 조회 확인
        for service_type in expected_services:
            service_filter = LogFilter(
                service=service_type,
                source=LogSource.EXTERNAL,
                limit=50
            )
            service_result = await logging_service.search_logs(service_filter)
            assert len(service_result.logs) > 0

    @pytest.mark.asyncio
    async def test_log_filtering_and_search(self, logging_service: LogService):
        """로그 필터링 및 검색 기능 테스트"""
        
        # 다양한 로그 레벨의 테스트 로그들 생성
        test_logs = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.ERROR,
                service=LogServiceType.API,
                source=LogSource.INTERNAL,
                message="Test error message for filtering",
                context=LogContext(user_id="user_error", endpoint="/api/error"),
                metadata=LogMetadata(tags=["error", "test", "filtering"])
            ),
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.WARN,
                service=LogServiceType.API,
                source=LogSource.INTERNAL,
                message="Test warning message for filtering",
                context=LogContext(user_id="user_warn", endpoint="/api/warn"),
                metadata=LogMetadata(tags=["warning", "test", "filtering"])
            ),
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level=LogLevel.INFO,
                service=LogServiceType.WEB,
                source=LogSource.INTERNAL,
                message="Test info message for filtering",
                context=LogContext(user_id="user_info", endpoint="/web/info"),
                metadata=LogMetadata(tags=["info", "test", "filtering"])
            )
        ]
        
        # 로그들 저장
        for log_entry in test_logs:
            await logging_service.log_internal(
                level=log_entry.level,
                service=log_entry.service,
                message=log_entry.message,
                context=log_entry.context,
                metadata=log_entry.metadata
            )
        
        # 레벨별 필터링 테스트
        error_filter = LogFilter(level=LogLevel.ERROR, limit=10)
        error_result = await logging_service.search_logs(error_filter)
        assert len(error_result.logs) >= 1
        assert all(log.level == LogLevel.ERROR for log in error_result.logs)
        
        warn_filter = LogFilter(level=LogLevel.WARN, limit=10)
        warn_result = await logging_service.search_logs(warn_filter)
        assert len(warn_result.logs) >= 1
        assert all(log.level == LogLevel.WARN for log in warn_result.logs)
        
        # 서비스별 필터링 테스트
        api_filter = LogFilter(service=LogServiceType.API, limit=10)
        api_result = await logging_service.search_logs(api_filter)
        assert len(api_result.logs) >= 2  # ERROR + WARN
        assert all(log.service == LogServiceType.API for log in api_result.logs)
        
        web_filter = LogFilter(service=LogServiceType.WEB, limit=10)
        web_result = await logging_service.search_logs(web_filter)
        assert len(web_result.logs) >= 1
        assert all(log.service == LogServiceType.WEB for log in web_result.logs)
        
        # 소스별 필터링 테스트
        internal_filter = LogFilter(source=LogSource.INTERNAL, limit=50)
        internal_result = await logging_service.search_logs(internal_filter)
        assert len(internal_result.logs) >= 3
        assert all(log.source == LogSource.INTERNAL for log in internal_result.logs)

    @pytest.mark.asyncio
    async def test_adapter_connection_health_checks(self):
        """외부 adapter들의 연결 상태 확인 테스트"""
        
        adapters = [
            ("Vercel", VercelLogAdapter("mock_token", "mock_project", use_mock=True)),
            ("Upstash", UpstashLogAdapter("mock_url", "mock_token", use_mock=True)),
            ("CloudRun", CloudRunLogAdapter("mock_project", use_mock=True)),
            ("Atlas", AtlasLogAdapter("mock_key", "mock_group", "mock_cluster", use_mock=True))
        ]
        
        health_results = {}
        
        for name, adapter in adapters:
            is_healthy = await adapter.test_connection()
            health_results[name] = is_healthy
            
            # Mock 모드에서는 모든 adapter가 건강해야 함
            assert is_healthy == True, f"{name} adapter health check failed"
        
        # 모든 adapter가 건강한지 확인
        assert all(health_results.values()), f"Some adapters failed health check: {health_results}"

    @pytest.mark.asyncio
    async def test_concurrent_log_operations(self, logging_service: LogService):
        """동시 로그 작업 테스트 (동시성 및 성능)"""
        
        # 동시에 여러 로그를 생성하는 작업들
        async def create_log(index: int):
            return await logging_service.log_internal(
                level=LogLevel.INFO,
                service=LogServiceType.API,
                message=f"Concurrent test log {index}",
                context=LogContext(
                    user_id=f"concurrent_user_{index}",
                    request_id=f"concurrent_req_{index}",
                    endpoint="/api/concurrent"
                ),
                metadata=LogMetadata(
                    tags=["concurrent", "test", f"batch_{index // 10}"],
                    custom={"index": index, "test_type": "concurrent"}
                )
            )
        
        # 50개의 동시 로그 생성 작업
        concurrent_tasks = [create_log(i) for i in range(50)]
        
        # 모든 작업을 동시에 실행
        start_time = datetime.now()
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # 실행 시간 체크 (너무 오래 걸리지 않아야 함)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 10.0, f"Concurrent operations took too long: {execution_time}s"
        
        # 모든 작업이 성공했는지 확인
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 50, f"Some concurrent operations failed: {len(successful_results)}/50"
        
        # 생성된 로그들이 올바르게 저장되었는지 확인
        for result in successful_results:
            assert result is not None
            assert result.id is not None
            assert "Concurrent test log" in result.message
        
        # 데이터베이스에서 생성된 로그들 조회
        recent_filter = LogFilter(
            limit=100,
            service=LogServiceType.API
        )
        recent_result = await logging_service.search_logs(recent_filter)
        
        concurrent_logs = [log for log in recent_result.logs if "Concurrent test log" in log.message]
        assert len(concurrent_logs) >= 50, f"Not all concurrent logs were persisted: {len(concurrent_logs)}/50"

    @pytest.mark.asyncio
    async def test_log_aggregation_and_statistics(self, logging_service: LogService):
        """로그 집계 및 통계 기능 테스트"""
        
        # 통계용 테스트 로그들 생성
        stats_logs = [
            # API 서비스 로그들
            (LogLevel.INFO, LogServiceType.API, "API info log 1"),
            (LogLevel.INFO, LogServiceType.API, "API info log 2"),
            (LogLevel.WARN, LogServiceType.API, "API warning log 1"),
            (LogLevel.ERROR, LogServiceType.API, "API error log 1"),
            
            # WEB 서비스 로그들
            (LogLevel.INFO, LogServiceType.WEB, "WEB info log 1"),
            (LogLevel.ERROR, LogServiceType.WEB, "WEB error log 1"),
            (LogLevel.ERROR, LogServiceType.WEB, "WEB error log 2"),
        ]
        
        # 로그들 저장
        for level, service, message in stats_logs:
            await logging_service.log_internal(
                level=level,
                service=service,
                message=message,
                context=LogContext(endpoint="/stats/test"),
                metadata=LogMetadata(tags=["statistics", "test"])
            )
        
        # 서비스별 로그 개수 확인
        api_filter = LogFilter(service=LogServiceType.API)
        api_count = await logging_service.count_logs(api_filter)
        
        web_filter = LogFilter(service=LogServiceType.WEB)
        web_count = await logging_service.count_logs(web_filter)
        
        assert api_count >= 4  # 최소 4개 (방금 생성한 것들)
        assert web_count >= 3  # 최소 3개 (방금 생성한 것들)
        
        # 레벨별 로그 개수 확인
        error_filter = LogFilter(level=LogLevel.ERROR)
        error_count = await logging_service.count_logs(error_filter)
        
        warn_filter = LogFilter(level=LogLevel.WARN)
        warn_count = await logging_service.count_logs(warn_filter)
        
        info_filter = LogFilter(level=LogLevel.INFO)
        info_count = await logging_service.count_logs(info_filter)
        
        assert error_count >= 3  # API 1개 + WEB 2개
        assert warn_count >= 1   # API 1개
        assert info_count >= 3   # API 2개 + WEB 1개


class TestLoggingAPIIntegration:
    """로깅 API 엔드포인트 통합 테스트"""
    
    def test_logging_api_endpoints_exist(self, client: TestClient):
        """로깅 API 엔드포인트들이 존재하는지 확인"""
        
        # Health check (로깅 시스템 상태 확인)
        response = client.get("/health")
        assert response.status_code == 200
        
        # TODO: 로깅 API 엔드포인트가 구현되면 추가 테스트
        # 현재는 로깅 시스템이 서비스 레벨에서만 구현되어 있고
        # 직접적인 로깅 API 엔드포인트는 아직 구현되지 않음
        
        # 향후 구현 예정인 엔드포인트들:
        # - GET /api/logs - 로그 조회
        # - POST /api/logs - 로그 생성  
        # - GET /api/logs/stats - 로그 통계
        # - GET /api/logs/external/collect - 외부 로그 수집


if __name__ == "__main__":
    pytest.main([__file__])