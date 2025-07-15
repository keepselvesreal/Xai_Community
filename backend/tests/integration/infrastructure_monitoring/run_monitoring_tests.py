#!/usr/bin/env python3
"""
인프라 모니터링 통합 테스트 실행 스크립트

각 인프라 서비스(Cloud Run, Vercel, Atlas, Upstash)의 
모니터링 기능을 실제 환경에서 테스트
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from nadle_backend.services.monitoring import (
    CloudRunMonitoringService,
    VercelMonitoringService, 
    AtlasMonitoringService,
    UpstashMonitoringService,
    UnifiedMonitoringService
)
from nadle_backend.models.monitoring import ServiceStatus, InfrastructureType
from nadle_backend.config import get_settings


class InfrastructureMonitoringTester:
    """인프라 모니터링 테스트 실행기"""
    
    def __init__(self):
        self.settings = get_settings()
        self.test_results = {
            'cloud_run': False,
            'vercel': False,
            'atlas': False,
            'upstash': False,
            'unified': False
        }
        
    def print_header(self, title):
        """테스트 헤더 출력"""
        print("\n" + "="*60)
        print(f"🔍 {title}")
        print("="*60)
    
    def print_result(self, service, success, details=None):
        """테스트 결과 출력"""
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} - {service}")
        if details:
            for key, value in details.items():
                print(f"  📊 {key}: {value}")
        print()
    
    async def test_cloud_run_monitoring(self):
        """Google Cloud Run 모니터링 테스트"""
        self.print_header("Google Cloud Run 모니터링 테스트")
        
        try:
            service = CloudRunMonitoringService()
            
            # 설정 확인
            is_configured = service.is_configured()
            print(f"설정 상태: {is_configured}")
            
            if not is_configured:
                print("⚠️  Cloud Run 설정이 불완전합니다. 테스트를 건너뜁니다.")
                return False
            
            # 상태 확인
            status = await service.get_service_status()
            print(f"서비스 상태: {status.value}")
            
            # 메트릭 수집
            metrics = await service.get_metrics()
            details = {
                "서비스명": metrics.service_name,
                "리전": metrics.region,
                "상태": metrics.status.value,
                "응답시간": f"{metrics.response_time_ms}ms" if metrics.response_time_ms else "N/A",
                "CPU 사용률": f"{metrics.cpu_utilization}%" if metrics.cpu_utilization else "N/A",
                "메모리 사용률": f"{metrics.memory_utilization}%" if metrics.memory_utilization else "N/A",
                "인스턴스 수": metrics.instance_count if metrics.instance_count else "N/A"
            }
            
            # 헬스체크
            health = await service.health_check()
            details["헬스체크"] = health.get("status", "N/A")
            
            self.print_result("Google Cloud Run", True, details)
            self.test_results['cloud_run'] = True
            return True
            
        except Exception as e:
            self.print_result("Google Cloud Run", False, {"오류": str(e)})
            return False
    
    async def test_vercel_monitoring(self):
        """Vercel 모니터링 테스트"""
        self.print_header("Vercel 모니터링 테스트")
        
        try:
            service = VercelMonitoringService()
            
            # 설정 확인
            is_configured = service.is_configured()
            print(f"설정 상태: {is_configured}")
            
            if not is_configured:
                print("⚠️  Vercel 설정이 불완전합니다. 테스트를 건너뜁니다.")
                return False
            
            # 상태 확인
            status = await service.get_project_status()
            print(f"프로젝트 상태: {status.value}")
            
            # 메트릭 수집
            metrics = await service.get_metrics()
            details = {
                "프로젝트 ID": metrics.project_id,
                "상태": metrics.status.value,
                "배포 상태": metrics.deployment_status or "N/A",
                "배포 URL": metrics.deployment_url or "N/A",
                "응답시간": f"{metrics.response_time_ms}ms" if metrics.response_time_ms else "N/A",
                "함수 호출 수": metrics.function_invocations if metrics.function_invocations else "N/A",
                "Core Web Vitals": f"{metrics.core_web_vitals_score}" if metrics.core_web_vitals_score else "N/A"
            }
            
            # 헬스체크
            health = await service.health_check()
            details["헬스체크"] = health.get("status", "N/A")
            
            self.print_result("Vercel", True, details)
            self.test_results['vercel'] = True
            return True
            
        except Exception as e:
            self.print_result("Vercel", False, {"오류": str(e)})
            return False
    
    async def test_atlas_monitoring(self):
        """MongoDB Atlas 모니터링 테스트"""
        self.print_header("MongoDB Atlas 모니터링 테스트")
        
        try:
            service = AtlasMonitoringService()
            
            # 설정 확인
            is_configured = service.is_configured()
            print(f"설정 상태: {is_configured}")
            
            if not is_configured:
                print("⚠️  Atlas 설정이 불완전합니다. 테스트를 건너뜁니다.")
                return False
            
            # 상태 확인
            status = await service.get_cluster_status()
            print(f"클러스터 상태: {status.value}")
            
            # 메트릭 수집
            metrics = await service.get_metrics()
            details = {
                "클러스터명": metrics.cluster_name,
                "클러스터 타입": metrics.cluster_type or "N/A",
                "상태": metrics.status.value,
                "현재 연결 수": metrics.connections_current if metrics.connections_current else "N/A",
                "사용 가능한 연결 수": metrics.connections_available if metrics.connections_available else "N/A",
                "CPU 사용률": f"{metrics.cpu_usage_percent}%" if metrics.cpu_usage_percent else "N/A",
                "메모리 사용률": f"{metrics.memory_usage_percent}%" if metrics.memory_usage_percent else "N/A",
                "초당 연산 수": f"{metrics.operations_per_second}" if metrics.operations_per_second else "N/A"
            }
            
            # 헬스체크
            health = await service.health_check()
            details["헬스체크"] = health.get("status", "N/A")
            
            self.print_result("MongoDB Atlas", True, details)
            self.test_results['atlas'] = True
            return True
            
        except Exception as e:
            self.print_result("MongoDB Atlas", False, {"오류": str(e)})
            return False
    
    async def test_upstash_monitoring(self):
        """Upstash Redis 모니터링 테스트"""
        self.print_header("Upstash Redis 모니터링 테스트")
        
        try:
            service = UpstashMonitoringService()
            
            # 설정 확인
            is_configured = service.is_configured()
            print(f"설정 상태: {is_configured}")
            
            if not is_configured:
                print("⚠️  Upstash 설정이 불완전합니다. 테스트를 건너뜁니다.")
                return False
            
            # 상태 확인
            status = await service.get_redis_status()
            print(f"Redis 상태: {status.value}")
            
            # 메트릭 수집
            metrics = await service.get_metrics()
            details = {
                "데이터베이스 ID": metrics.database_id,
                "데이터베이스명": metrics.database_name or "N/A",
                "리전": metrics.region or "N/A",
                "상태": metrics.status.value,
                "연결 수": metrics.connection_count if metrics.connection_count else "N/A",
                "키스페이스": metrics.keyspace if metrics.keyspace else "N/A",
                "Hit Rate": f"{metrics.hit_rate}%" if metrics.hit_rate else "N/A",
                "메모리 사용률": f"{metrics.memory_usage_percent}%" if metrics.memory_usage_percent else "N/A",
                "응답시간": f"{metrics.response_time_ms}ms" if metrics.response_time_ms else "N/A"
            }
            
            # 헬스체크
            health = await service.health_check()
            details["헬스체크"] = health.get("status", "N/A")
            
            self.print_result("Upstash Redis", True, details)
            self.test_results['upstash'] = True
            return True
            
        except Exception as e:
            self.print_result("Upstash Redis", False, {"오류": str(e)})
            return False
    
    async def test_unified_monitoring(self):
        """통합 모니터링 서비스 테스트"""
        self.print_header("통합 모니터링 서비스 테스트")
        
        try:
            service = UnifiedMonitoringService()
            
            # 설정된 서비스 확인
            configured_services = service.get_configured_services()
            print(f"설정된 서비스들: {[s.value for s in configured_services]}")
            
            if not configured_services:
                print("⚠️  설정된 인프라 서비스가 없습니다. 테스트를 건너뜁니다.")
                return False
            
            # 통합 헬스체크
            health_response = await service.health_check()
            print(f"통합 헬스체크 상태: {health_response.status.value}")
            
            # 전체 인프라 상태 조회
            infrastructure_status = await service.get_all_infrastructure_status()
            
            details = {
                "전체 상태": infrastructure_status.overall_status.value,
                "전체 인프라 수": infrastructure_status.infrastructure_count,
                "정상 서비스 수": infrastructure_status.healthy_count,
                "비정상 서비스 수": infrastructure_status.unhealthy_count,
                "가동률": f"{infrastructure_status.uptime_percentage:.2f}%"
            }
            
            # 개별 서비스 상태
            print("\n📊 개별 서비스 상태:")
            for infrastructure in infrastructure_status.infrastructures:
                print(f"  • {infrastructure.infrastructure_type.value}: {infrastructure.status.value}")
                print(f"    서비스명: {infrastructure.service_name}")
                print(f"    마지막 체크: {infrastructure.last_check}")
            
            self.print_result("통합 모니터링 서비스", True, details)
            self.test_results['unified'] = True
            return True
            
        except Exception as e:
            self.print_result("통합 모니터링 서비스", False, {"오류": str(e)})
            return False
    
    def print_final_summary(self):
        """최종 테스트 요약 출력"""
        print("\n" + "="*60)
        print("🎯 인프라 모니터링 통합 테스트 최종 결과")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for service, result in self.test_results.items():
            status = "✅ 통과" if result else "❌ 실패"
            service_name = {
                'cloud_run': 'Google Cloud Run',
                'vercel': 'Vercel',
                'atlas': 'MongoDB Atlas', 
                'upstash': 'Upstash Redis',
                'unified': '통합 모니터링'
            }.get(service, service)
            print(f"{status} - {service_name}")
        
        print("-" * 60)
        print(f"📈 전체 결과: {passed_tests}/{total_tests} 테스트 통과")
        
        if passed_tests == total_tests:
            print("🚀 모든 인프라 모니터링 테스트가 성공했습니다!")
            print("✅ GitHub Secrets 적용 준비 완료")
        else:
            print("⚠️  일부 테스트가 실패했습니다. 설정을 확인해주세요.")
        
        print("="*60)
        
        return passed_tests == total_tests


async def main():
    """메인 테스트 실행 함수"""
    print("🔧 환경변수 확인...")
    
    tester = InfrastructureMonitoringTester()
    
    print(f"테스트 환경: {tester.settings.environment}")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 각 테스트 실행
    await tester.test_cloud_run_monitoring()
    await tester.test_vercel_monitoring() 
    await tester.test_atlas_monitoring()
    await tester.test_upstash_monitoring()
    await tester.test_unified_monitoring()
    
    # 최종 결과 요약
    success = tester.print_final_summary()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예상치 못한 오류: {e}")
        sys.exit(1)