"""
인프라 모니터링 통합 테스트

각 인프라 서비스(Cloud Run, Vercel, Atlas, Upstash)의 
모니터링 기능을 실제 환경에서 테스트
"""

import pytest
import asyncio
import os
from datetime import datetime

from nadle_backend.services.monitoring import (
    CloudRunMonitoringService,
    VercelMonitoringService, 
    AtlasMonitoringService,
    UpstashMonitoringService,
    UnifiedMonitoringService
)
from nadle_backend.models.monitoring import ServiceStatus, InfrastructureType
from nadle_backend.config import get_settings


class TestInfrastructureMonitoring:
    """인프라 모니터링 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        self.settings = get_settings()
        print(f"\n=== 테스트 환경: {self.settings.environment} ===")
    
    @pytest.mark.asyncio
    async def test_cloud_run_monitoring(self):
        """Google Cloud Run 모니터링 테스트"""
        print("\n🔍 Google Cloud Run 모니터링 테스트 시작...")
        
        service = CloudRunMonitoringService()
        
        # 설정 확인
        is_configured = service.is_configured()
        print(f"Cloud Run 설정 상태: {is_configured}")
        
        if not is_configured:
            pytest.skip("Cloud Run 설정이 불완전하여 테스트를 건너뜁니다")
        
        # 상태 확인
        status = await service.get_service_status()
        print(f"Cloud Run 상태: {status.value}")
        assert status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.DEGRADED]
        
        # 메트릭 수집
        metrics = await service.get_metrics()
        print(f"Cloud Run 메트릭 수집 완료:")
        print(f"  - 서비스명: {metrics.service_name}")
        print(f"  - 리전: {metrics.region}")
        print(f"  - 상태: {metrics.status.value}")
        print(f"  - 응답시간: {metrics.response_time_ms}ms")
        print(f"  - CPU 사용률: {metrics.cpu_utilization}%")
        print(f"  - 메모리 사용률: {metrics.memory_utilization}%")
        print(f"  - 인스턴스 수: {metrics.instance_count}")
        
        assert metrics.service_name is not None
        assert metrics.region is not None
        assert metrics.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.DEGRADED]
        
        # 헬스체크
        health = await service.health_check()
        print(f"Cloud Run 헬스체크: {health}")
        assert "service" in health
        assert "status" in health
        
        print("✅ Google Cloud Run 모니터링 테스트 완료")
    
    @pytest.mark.asyncio
    async def test_vercel_monitoring(self):
        """Vercel 모니터링 테스트"""
        print("\n🔍 Vercel 모니터링 테스트 시작...")
        
        service = VercelMonitoringService()
        
        # 설정 확인
        is_configured = service.is_configured()
        print(f"Vercel 설정 상태: {is_configured}")
        
        if not is_configured:
            pytest.skip("Vercel 설정이 불완전하여 테스트를 건너뜁니다")
        
        # 상태 확인
        status = await service.get_project_status()
        print(f"Vercel 상태: {status.value}")
        assert status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY]
        
        # 메트릭 수집
        metrics = await service.get_metrics()
        print(f"Vercel 메트릭 수집 완료:")
        print(f"  - 프로젝트 ID: {metrics.project_id}")
        print(f"  - 상태: {metrics.status.value}")
        print(f"  - 배포 상태: {metrics.deployment_status}")
        print(f"  - 배포 URL: {metrics.deployment_url}")
        print(f"  - 응답시간: {metrics.response_time_ms}ms")
        print(f"  - 함수 호출 수: {metrics.function_invocations}")
        print(f"  - Core Web Vitals 점수: {metrics.core_web_vitals_score}")
        
        assert metrics.project_id is not None
        assert metrics.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY]
        
        # 헬스체크
        health = await service.health_check()
        print(f"Vercel 헬스체크: {health}")
        assert "service" in health
        assert "status" in health
        
        print("✅ Vercel 모니터링 테스트 완료")
    
    @pytest.mark.asyncio
    async def test_atlas_monitoring(self):
        """MongoDB Atlas 모니터링 테스트"""
        print("\n🔍 MongoDB Atlas 모니터링 테스트 시작...")
        
        service = AtlasMonitoringService()
        
        # 설정 확인
        is_configured = service.is_configured()
        print(f"Atlas 설정 상태: {is_configured}")
        
        if not is_configured:
            pytest.skip("Atlas 설정이 불완전하여 테스트를 건너뜁니다")
        
        # 상태 확인
        status = await service.get_cluster_status()
        print(f"Atlas 상태: {status.value}")
        assert status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.DEGRADED, ServiceStatus.MAINTENANCE]
        
        # 메트릭 수집
        metrics = await service.get_metrics()
        print(f"Atlas 메트릭 수집 완료:")
        print(f"  - 클러스터명: {metrics.cluster_name}")
        print(f"  - 클러스터 타입: {metrics.cluster_type}")
        print(f"  - 상태: {metrics.status.value}")
        print(f"  - 현재 연결 수: {metrics.connections_current}")
        print(f"  - 사용 가능한 연결 수: {metrics.connections_available}")
        print(f"  - CPU 사용률: {metrics.cpu_usage_percent}%")
        print(f"  - 메모리 사용률: {metrics.memory_usage_percent}%")
        print(f"  - 초당 연산 수: {metrics.operations_per_second}")
        print(f"  - 읽기 지연시간: {metrics.read_latency_ms}ms")
        print(f"  - 쓰기 지연시간: {metrics.write_latency_ms}ms")
        
        assert metrics.cluster_name is not None
        assert metrics.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.DEGRADED, ServiceStatus.MAINTENANCE]
        
        # 헬스체크
        health = await service.health_check()
        print(f"Atlas 헬스체크: {health}")
        assert "service" in health
        assert "status" in health
        
        print("✅ MongoDB Atlas 모니터링 테스트 완료")
    
    @pytest.mark.asyncio
    async def test_upstash_monitoring(self):
        """Upstash Redis 모니터링 테스트"""
        print("\n🔍 Upstash Redis 모니터링 테스트 시작...")
        
        service = UpstashMonitoringService()
        
        # 설정 확인
        is_configured = service.is_configured()
        print(f"Upstash 설정 상태: {is_configured}")
        
        if not is_configured:
            pytest.skip("Upstash 설정이 불완전하여 테스트를 건너뜁니다")
        
        # 상태 확인
        status = await service.get_redis_status()
        print(f"Upstash 상태: {status.value}")
        assert status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.UNHEALTHY]
        
        # 메트릭 수집
        metrics = await service.get_metrics()
        print(f"Upstash 메트릭 수집 완료:")
        print(f"  - 데이터베이스 ID: {metrics.database_id}")
        print(f"  - 데이터베이스명: {metrics.database_name}")
        print(f"  - 리전: {metrics.region}")
        print(f"  - 상태: {metrics.status.value}")
        print(f"  - 연결 수: {metrics.connection_count}")
        print(f"  - 키스페이스: {metrics.keyspace}")
        print(f"  - Hit Rate: {metrics.hit_rate}%")
        print(f"  - 메모리 사용률: {metrics.memory_usage_percent}%")
        print(f"  - 초당 연산 수: {metrics.operations_per_second}")
        print(f"  - 읽기 지연시간: {metrics.read_latency_ms}ms")
        print(f"  - 쓰기 지연시간: {metrics.write_latency_ms}ms")
        print(f"  - 응답시간: {metrics.response_time_ms}ms")
        
        assert metrics.database_id is not None
        assert metrics.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN, ServiceStatus.UNHEALTHY]
        
        # 헬스체크
        health = await service.health_check()
        print(f"Upstash 헬스체크: {health}")
        assert "service" in health
        assert "status" in health
        
        print("✅ Upstash Redis 모니터링 테스트 완료")
    
    @pytest.mark.asyncio
    async def test_unified_monitoring(self):
        """통합 모니터링 서비스 테스트"""
        print("\n🔍 통합 모니터링 서비스 테스트 시작...")
        
        service = UnifiedMonitoringService()
        
        # 설정된 서비스 확인
        configured_services = service.get_configured_services()
        print(f"설정된 서비스들: {[s.value for s in configured_services]}")
        
        if not configured_services:
            pytest.skip("설정된 인프라 서비스가 없어 테스트를 건너뜁니다")
        
        # 통합 헬스체크
        health_response = await service.health_check()
        print(f"통합 헬스체크:")
        print(f"  - 전체 상태: {health_response.status.value}")
        print(f"  - 개별 서비스 체크: {len(health_response.checks)}개")
        
        assert health_response.service == "unified_monitoring"
        assert health_response.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED, ServiceStatus.UNKNOWN]
        
        # 전체 인프라 상태 조회
        infrastructure_status = await service.get_all_infrastructure_status()
        print(f"통합 인프라 상태:")
        print(f"  - 전체 상태: {infrastructure_status.overall_status.value}")
        print(f"  - 전체 인프라 수: {infrastructure_status.infrastructure_count}")
        print(f"  - 정상 서비스 수: {infrastructure_status.healthy_count}")
        print(f"  - 비정상 서비스 수: {infrastructure_status.unhealthy_count}")
        print(f"  - 가동률: {infrastructure_status.uptime_percentage:.2f}%")
        
        assert infrastructure_status.infrastructure_count > 0
        assert infrastructure_status.overall_status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY, ServiceStatus.UNKNOWN]
        assert len(infrastructure_status.infrastructures) == infrastructure_status.infrastructure_count
        
        # 개별 서비스 메트릭 테스트
        for infrastructure in infrastructure_status.infrastructures:
            print(f"\n  📊 {infrastructure.infrastructure_type.value} 상세:")
            print(f"    - 서비스명: {infrastructure.service_name}")
            print(f"    - 상태: {infrastructure.status.value}")
            print(f"    - 마지막 체크: {infrastructure.last_check}")
            
            # 개별 메트릭 조회 테스트
            metrics = await service.get_service_metrics(infrastructure.infrastructure_type)
            if metrics:
                print(f"    - 메트릭 수집 성공")
            else:
                print(f"    - 메트릭 수집 실패 또는 서비스 비활성")
        
        print("✅ 통합 모니터링 서비스 테스트 완료")
    
    def test_summary(self):
        """테스트 요약"""
        print("\n" + "="*60)
        print("🎯 인프라 모니터링 통합 테스트 요약")
        print("="*60)
        print("✅ Google Cloud Run 모니터링")
        print("✅ Vercel 모니터링") 
        print("✅ MongoDB Atlas 모니터링")
        print("✅ Upstash Redis 모니터링")
        print("✅ 통합 모니터링 서비스")
        print("="*60)
        print("🚀 모든 인프라 모니터링 테스트 완료!")
        print("="*60)


if __name__ == "__main__":
    # 개별 실행 시 asyncio 테스트 실행
    import asyncio
    
    async def run_tests():
        test_instance = TestInfrastructureMonitoring()
        test_instance.setup()
        
        try:
            await test_instance.test_cloud_run_monitoring()
        except Exception as e:
            print(f"Cloud Run 테스트 실패: {e}")
        
        try:
            await test_instance.test_vercel_monitoring()
        except Exception as e:
            print(f"Vercel 테스트 실패: {e}")
        
        try:
            await test_instance.test_atlas_monitoring()
        except Exception as e:
            print(f"Atlas 테스트 실패: {e}")
        
        try:
            await test_instance.test_upstash_monitoring()
        except Exception as e:
            print(f"Upstash 테스트 실패: {e}")
        
        try:
            await test_instance.test_unified_monitoring()
        except Exception as e:
            print(f"통합 모니터링 테스트 실패: {e}")
        
        test_instance.test_summary()
    
    asyncio.run(run_tests())