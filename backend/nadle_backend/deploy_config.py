"""
Deployment-specific configuration for production environments.
This file serves as a fallback when environment variables fail to parse correctly.
"""

import os
import re
from typing import List, Dict, Any


class DeploymentConfig:
    """Static deployment configuration as a fallback."""
    
    # Primary Production Domain (권장 - 고정 도메인)
    PRODUCTION_DOMAIN = "https://xai-community.vercel.app"
    
    # Vercel URL 패턴 정의 (Preview/Branch 배포용)
    VERCEL_PATTERNS = [
        r"https://xai-community.*-ktsfrank-navercoms-projects\.vercel\.app",
        r"https://xai-community-git-.*-ktsfrank-navercoms-projects\.vercel\.app", 
        r"https://xai-community.*\.vercel\.app"
    ]
    
    # 기존 배포별 URLs (하위 호환성 - 레거시)
    LEGACY_DEPLOYMENT_URLS = [
        "https://xai-community-beda86vwl-ktsfrank-navercoms-projects.vercel.app",
        "https://xai-community-git-main-ktsfrank-navercoms-projects.vercel.app",
        "https://xai-community-ktsfrank-navercoms-projects.vercel.app",
        "https://xai-community-2biahwrqh-ktsfrank-navercoms-projects.vercel.app",
        "https://xai-community-id0m2v4f8-ktsfrank-navercoms-projects.vercel.app",
    ]
    
    # Development origins
    DEVELOPMENT_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    
    @classmethod
    def is_allowed_vercel_url(cls, url: str) -> bool:
        """Vercel URL이 허용된 패턴과 매치되는지 확인."""
        if not url:
            return False
            
        # 1. Primary Production Domain (최우선)
        if url == cls.PRODUCTION_DOMAIN:
            return True
            
        # 2. 레거시 URL들 (하위 호환성)
        if url in cls.LEGACY_DEPLOYMENT_URLS:
            return True
            
        # 3. 패턴 기반 매칭 (Preview/Branch 배포)
        for pattern in cls.VERCEL_PATTERNS:
            if re.match(pattern, url):
                return True
                
        return False
    
    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """Get CORS origins based on environment."""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        if environment == "production":
            # 프로덕션에서는 Primary Domain 우선, 레거시 URL들 포함
            origins = [cls.PRODUCTION_DOMAIN] + cls.LEGACY_DEPLOYMENT_URLS.copy()
            
            # 환경변수에서 추가 frontend URL이 있다면 포함
            frontend_url = os.getenv("FRONTEND_URL")
            if frontend_url and frontend_url not in origins:
                origins.append(frontend_url)
                # HTTPS 변형도 추가
                if frontend_url.startswith("http://"):
                    https_variant = frontend_url.replace("http://", "https://", 1)
                    if https_variant not in origins:
                        origins.append(https_variant)
            
            return origins
        else:
            # 개발 환경에서는 기본 개발용 origins
            return cls.DEVELOPMENT_ORIGINS.copy()
    
    @classmethod
    def get_safe_environment_config(cls) -> Dict[str, Any]:
        """Get safe configuration values that don't rely on problematic parsing."""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        config = {
            "cors_origins": cls.get_cors_origins(),
            "environment": environment,
            "enable_cors": True,
            "enable_docs": environment != "production",
            "log_level": "INFO" if environment == "production" else "DEBUG",
        }
        
        # 안전한 환경변수들만 포함
        safe_env_vars = {
            "MONGODB_URL": os.getenv("MONGODB_URL"),
            "DATABASE_NAME": os.getenv("DATABASE_NAME", "xai_community_prod" if environment == "production" else "xai_community"),
            "SECRET_KEY": os.getenv("SECRET_KEY"),
            "PORT": os.getenv("PORT", "8000"),
            "HOST": os.getenv("HOST", "0.0.0.0"),
        }
        
        # None이 아닌 값들만 추가
        for key, value in safe_env_vars.items():
            if value is not None:
                config[key.lower()] = value
        
        return config


def apply_deployment_overrides(settings_instance):
    """Apply deployment configuration overrides to settings instance."""
    try:
        deploy_config = DeploymentConfig.get_safe_environment_config()
        
        # CORS origins 강제 설정
        settings_instance.cors_origins = deploy_config["cors_origins"]
        
        # 기타 안전한 설정들 적용
        for key, value in deploy_config.items():
            if hasattr(settings_instance, key) and key != "cors_origins":
                setattr(settings_instance, key, value)
        
        print(f"Deployment overrides applied successfully. CORS origins: {settings_instance.cors_origins}")
        return True
        
    except Exception as e:
        print(f"Warning: Failed to apply deployment overrides: {e}")
        return False