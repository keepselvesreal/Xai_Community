#!/usr/bin/env python3
"""
외부 인프라 API 키 설정 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ''))

from nadle_backend.config import get_settings

def main():
    print("=== 외부 인프라 API 키 설정 상태 ===")
    
    try:
        settings = get_settings()
        print(f"Environment: {settings.environment}")
        print(f"Env file: {getattr(settings, '_env_file', 'N/A')}")
        print()
        
        print("Vercel:")
        print(f"  API Token: {'✅' if settings.vercel_api_token else '❌'} {settings.vercel_api_token[:8] + '...' if settings.vercel_api_token else 'None'}")
        print(f"  Team ID: {'✅' if settings.vercel_team_id else '❌'} {settings.vercel_team_id or 'None'}")
        print(f"  Project ID: {'✅' if settings.vercel_project_id else '❌'} {settings.vercel_project_id or 'None'}")
        print()
        
        print("MongoDB Atlas:")
        print(f"  Public Key: {'✅' if settings.atlas_public_key else '❌'} {settings.atlas_public_key or 'None'}")
        print(f"  Private Key: {'✅' if settings.atlas_private_key else '❌'} {'***' if settings.atlas_private_key else 'None'}")
        print(f"  Group ID: {'✅' if settings.atlas_group_id else '❌'} {settings.atlas_group_id or 'None'}")
        print(f"  Cluster Name: {'✅' if settings.atlas_cluster_name else '❌'} {settings.atlas_cluster_name or 'None'}")
        print()
        
        print("Upstash Redis:")
        print(f"  API Key: {'✅' if settings.upstash_api_key else '❌'} {settings.upstash_api_key[:8] + '...' if settings.upstash_api_key else 'None'}")
        print(f"  Email: {'✅' if settings.upstash_email else '❌'} {settings.upstash_email or 'None'}")
        print()
        
        print("HetrixTools:")
        print(f"  API Token: {'✅' if settings.hetrixtools_api_token else '❌'} {settings.hetrixtools_api_token[:8] + '...' if settings.hetrixtools_api_token else 'None'}")
        print()
        
        # 모니터링 서비스 설정 상태 확인
        print("=== 모니터링 서비스 설정 상태 ===")
        
        from nadle_backend.services.monitoring.vercel_monitor import VercelMonitoringService
        from nadle_backend.services.monitoring.atlas_monitor import AtlasMonitoringService
        from nadle_backend.services.monitoring.upstash_monitor import UpstashMonitoringService
        
        vercel_service = VercelMonitoringService()
        atlas_service = AtlasMonitoringService()
        upstash_service = UpstashMonitoringService()
        
        print(f"Vercel 설정 완료: {'✅' if vercel_service.is_configured() else '❌'}")
        print(f"Atlas 설정 완료: {'✅' if atlas_service.is_configured() else '❌'}")
        print(f"Upstash 설정 완료: {'✅' if upstash_service.is_configured() else '❌'}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()