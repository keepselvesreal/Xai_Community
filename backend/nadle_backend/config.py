from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Literal, Optional, Union
from datetime import timedelta
import os
from pathlib import Path


def find_env_file() -> Optional[str]:
    """
    Find environment file with priority order:
    1. ENV_FILE_PATH environment variable (explicit override)
    2. .env.local (local development overrides) - only in development
    3. .env (main environment file) - only in development
    4. .env.example (template file) - only in development
    
    In production, no .env file is loaded to rely on environment variables.
    
    Returns:
        Path to the first found environment file, or None if none found
    """
    # Check if we're in production
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        return None  # Don't load any .env file in production
    
    # Check for explicit path override
    explicit_path = os.getenv("ENV_FILE_PATH")
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    
    # Priority order for automatic discovery (development only)
    env_file_candidates = [
        ".env.local",      # Local overrides (git ignored)
        ".env",            # Main environment file (git ignored)
        ".env.example",    # Template file (git tracked)
    ]
    
    for candidate in env_file_candidates:
        env_path = Path(candidate)
        if env_path.exists():
            return str(env_path)
    
    return None


class Settings(BaseSettings):
    """Application configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="forbid",
        # CORS origins는 환경변수에서 읽지 않음 (JSON 파싱 오류 방지)
        env_ignore={"cors_origins"}
    )
    
    # Database Configuration
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL (Atlas or local)"
    )
    database_name: str = Field(
        default="xai_community",
        description="Database name for the application"
    )
    
    # Collection Configuration
    users_collection: str = Field(
        default="users",
        description="Collection name for user documents"
    )
    posts_collection: str = Field(
        default="posts",
        description="Collection name for post documents"
    )
    comments_collection: str = Field(
        default="comments",
        description="Collection name for comment documents"
    )
    post_stats_collection: str = Field(
        default="post_stats",
        description="Collection name for post statistics"
    )
    user_reactions_collection: str = Field(
        default="user_reactions",
        description="Collection name for user reactions"
    )
    files_collection: str = Field(
        default="files",
        description="Collection name for file metadata"
    )
    stats_collection: str = Field(
        default="stats",
        description="Collection name for application statistics"
    )
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production-32-characters",
        description="Secret key for JWT token signing (min 32 chars)",
        min_length=32
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
        description="Access token expiration time in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        gt=0,
        description="Refresh token expiration time in days"
    )
    
    @property
    def access_token_expire(self) -> timedelta:
        """Get access token expiration as timedelta."""
        return timedelta(minutes=self.access_token_expire_minutes)
    
    @property
    def refresh_token_expire(self) -> timedelta:
        """Get refresh token expiration as timedelta."""
        return timedelta(days=self.refresh_token_expire_days)
    
    # API Configuration
    api_title: str = Field(
        default="Content Management API",
        description="API service title"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version number"
    )
    api_description: str = Field(
        default="FastAPI backend for content management system",
        description="API service description"
    )
    
    # CORS Configuration - GitHub Actions 호환성을 위해 단순화
    cors_origins: Optional[List[str]] = Field(
        default=None,
        description="List of allowed CORS origins for frontend access"
    )
    
    # Frontend URL for production (Vercel deployment)
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS and redirects (automatically added to cors_origins)"
    )
    
    # Environment Configuration
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application deployment environment"
    )
    
    # Server Configuration
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server listening port number"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host address (0.0.0.0 for all interfaces)"
    )
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application logging level"
    )
    
    # Feature Flags
    enable_docs: bool = Field(
        default=True,
        description="Enable automatic API documentation (Swagger/OpenAPI)"
    )
    enable_cors: bool = Field(
        default=True,
        description="Enable Cross-Origin Resource Sharing (CORS)"
    )
    
    # Email Configuration
    smtp_server: str = Field(
        default="smtp.gmail.com",
        description="SMTP server for sending emails"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port (587 for TLS, 465 for SSL)"
    )
    smtp_username: str = Field(
        default="",
        description="SMTP username for authentication"
    )
    smtp_password: str = Field(
        default="",
        description="SMTP password or app password"
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP connection"
    )
    from_email: str = Field(
        default="noreply@example.com",
        description="Email address for sending emails"
    )
    from_name: str = Field(
        default="XAI Community",
        description="Display name for sender"
    )
    
    # Email Verification Settings
    email_verification_expire_hours: int = Field(
        default=24,
        gt=0,
        description="Email verification token expiration time in hours"
    )
    email_verification_code_length: int = Field(
        default=6,
        ge=4,
        le=8,
        description="Length of email verification code"
    )
    
    # Comment Configuration
    max_comment_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum depth for nested comment replies (1-10)"
    )
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length and production safety."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # Check if using default key in production - but be more lenient during manual setup
        environment = os.getenv("ENVIRONMENT", "development")
        if (v == "your-secret-key-here-change-in-production-32-characters" and 
            environment == "production"):
            print(f"WARNING: Using default secret key in production!")
            print(f"Environment variables check:")
            print(f"  ENVIRONMENT: {environment}")
            print(f"  SECRET_KEY env var exists: {bool(os.getenv('SECRET_KEY'))}")
            print(f"  SECRET_KEY env var value (first 10): {os.getenv('SECRET_KEY', '')[:10]}...")
            
            # 환경변수에서 실제 값을 읽을 수 있다면 사용
            env_secret = os.getenv('SECRET_KEY')
            if env_secret and len(env_secret) >= 32:
                print("Using SECRET_KEY from environment variable")
                return env_secret
            
            raise ValueError("Default secret key cannot be used in production")
        
        return v
    
    @field_validator("mongodb_url")
    @classmethod
    def validate_mongodb_url(cls, v: str) -> str:
        """Validate MongoDB connection URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from string or list with robust error handling."""
        # 기본 fallback 값들
        default_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
        
        try:
            # 이미 리스트인 경우
            if isinstance(v, list):
                return v
            
            # None이거나 빈 값인 경우
            if v is None or (isinstance(v, str) and not v.strip()):
                return default_origins
            
            # 문자열 처리
            if isinstance(v, str):
                # 와일드카드 처리
                if v.strip() == "*":
                    return ["*"]
                
                # JSON 배열 형태 문자열 처리 (더 안전하게)
                if v.strip().startswith("[") and v.strip().endswith("]"):
                    import json
                    try:
                        parsed = json.loads(v.strip())
                        if isinstance(parsed, list):
                            return [str(origin).strip() for origin in parsed if str(origin).strip()]
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # JSON 파싱 실패 시 수동으로 파싱
                        try:
                            content = v.strip()[1:-1]  # 대괄호 제거
                            if content:
                                return [origin.strip().strip('"\'') for origin in content.split(",") if origin.strip()]
                        except Exception:
                            pass
                
                # 쉼표로 구분된 문자열 처리
                if "," in v:
                    origins = [origin.strip().strip('"\'') for origin in v.split(",") if origin.strip()]
                    return origins if origins else default_origins
                
                # 단일 URL 문자열
                cleaned_url = v.strip().strip('"\'')
                if cleaned_url and cleaned_url.startswith("http"):
                    return [cleaned_url]
            
            # 다른 타입이거나 파싱 실패 시 기본값 반환
            return default_origins
            
        except Exception as e:
            # 모든 예외 상황에서 안전한 기본값 반환
            import os
            if os.getenv("ENVIRONMENT") == "production":
                # 프로덕션에서는 로그만 남기고 기본값 사용
                print(f"Warning: CORS origins parsing failed, using defaults. Error: {e}")
            return default_origins
    
    def __init__(self, **kwargs):
        """Initialize settings and configure CORS origins."""
        super().__init__(**kwargs)
        self._configure_cors_origins()
        self._apply_deployment_safety_overrides()
    
    def _configure_cors_origins(self):
        """Configure CORS origins based on environment and frontend URL."""
        try:
            # 기본 로컬 개발 origins
            default_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
            
            # CORS origins가 None이거나 기본값이거나 비어있는 경우
            if self.cors_origins is None or not self.cors_origins or self.cors_origins == default_origins:
                origins = set(default_origins)
                
                # 프로덕션 환경에서 frontend_url이 설정되어 있으면 추가
                if self.environment == "production" and self.frontend_url and self.frontend_url != "http://localhost:3000":
                    origins.add(self.frontend_url)
                    # HTTPS 변형도 추가
                    if self.frontend_url.startswith("http://"):
                        https_url = self.frontend_url.replace("http://", "https://", 1)
                        origins.add(https_url)
                
                self.cors_origins = list(origins)
                print(f"CORS origins configured: {self.cors_origins}")
                
        except Exception as e:
            print(f"Warning: Failed to configure CORS origins automatically: {e}")
            # 실패 시 안전한 기본값 유지
            if not hasattr(self, 'cors_origins') or not self.cors_origins:
                self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
    def _apply_deployment_safety_overrides(self):
        """Apply deployment-specific overrides as a safety measure."""
        try:
            # 프로덕션 환경에서 수동으로 환경변수 설정
            if os.getenv("ENVIRONMENT") == "production":
                print("Production environment detected - applying manual environment variable configuration")
                self._apply_manual_env_vars()
                
                # 배포 설정도 적용
                from .deploy_config import apply_deployment_overrides
                apply_deployment_overrides(self)
        except ImportError:
            print("Warning: deploy_config module not found, skipping deployment overrides")
        except Exception as e:
            print(f"Warning: Failed to apply deployment overrides: {e}")
    
    def _apply_manual_env_vars(self):
        """Manually apply environment variables in production to avoid parsing issues."""
        try:
            print("=== Manual Environment Variable Application ===")
            
            # 안전하게 환경변수를 하나씩 설정
            env_mappings = {
                'MONGODB_URL': 'mongodb_url',
                'DATABASE_NAME': 'database_name',
                'SECRET_KEY': 'secret_key',
                'API_TITLE': 'api_title',
                'API_VERSION': 'api_version',
                'API_DESCRIPTION': 'api_description',
                'ALGORITHM': 'algorithm',
                'PORT': 'port',
                'HOST': 'host',
                'LOG_LEVEL': 'log_level',
            }
            
            print(f"Environment check - SECRET_KEY exists: {bool(os.getenv('SECRET_KEY'))}")
            print(f"Environment check - SECRET_KEY value (first 10 chars): {os.getenv('SECRET_KEY', '')[:10]}...")
            print(f"Environment check - ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
            
            # 숫자형 환경변수
            numeric_vars = {
                'ACCESS_TOKEN_EXPIRE_MINUTES': 'access_token_expire_minutes',
                'REFRESH_TOKEN_EXPIRE_DAYS': 'refresh_token_expire_days',
                'PORT': 'port',
            }
            
            # 문자열 환경변수 적용
            for env_var, attr_name in env_mappings.items():
                env_value = os.getenv(env_var)
                if env_value and hasattr(self, attr_name):
                    setattr(self, attr_name, env_value)
                    print(f"Set {attr_name} from environment")
            
            # 숫자형 환경변수 적용
            for env_var, attr_name in numeric_vars.items():
                env_value = os.getenv(env_var)
                if env_value and hasattr(self, attr_name):
                    try:
                        setattr(self, attr_name, int(env_value))
                        print(f"Set {attr_name} from environment (numeric)")
                    except ValueError:
                        print(f"Warning: Invalid numeric value for {env_var}: {env_value}")
            
            # CORS origins 수동 설정 (가장 중요)
            cors_value = os.getenv('CORS_ORIGINS')
            frontend_url = os.getenv('FRONTEND_URL')
            
            if cors_value:
                # 단순 문자열로 처리
                if cors_value.strip() == "*":
                    self.cors_origins = ["*"]
                elif cors_value.startswith("http"):
                    self.cors_origins = [cors_value.strip()]
                else:
                    # 쉼표로 분리된 경우
                    self.cors_origins = [url.strip() for url in cors_value.split(",") if url.strip()]
                print(f"CORS origins set manually: {self.cors_origins}")
            
            if frontend_url and hasattr(self, 'frontend_url'):
                self.frontend_url = frontend_url
                # frontend_url이 cors_origins에 없으면 추가
                if frontend_url not in self.cors_origins:
                    self.cors_origins.append(frontend_url)
                print(f"Frontend URL set: {frontend_url}")
                
        except Exception as e:
            print(f"Warning: Error in manual environment variable application: {e}")
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Custom source configuration to disable env parsing in production."""
        # 프로덕션에서는 환경변수 소스 완전 제거
        if os.getenv("ENVIRONMENT") == "production":
            return (init_settings,)  # 초기화 설정만 사용
        else:
            # 개발 환경에서는 기본 소스들 사용
            return (init_settings, env_settings, dotenv_settings, file_secret_settings)
    
    # Config 클래스는 model_config로 대체됨


# Create global settings instance with error handling
try:
    settings = Settings()
except Exception as e:
    # GitHub Actions나 다른 환경에서 환경변수 파싱 오류 발생 시 폴백
    import os
    from .deploy_config import DeploymentConfig
    
    print(f"Warning: Settings initialization failed: {e}")
    print("Using fallback configuration...")
    
    # 안전한 폴백 설정으로 다시 시도
    os.environ.pop("CORS_ORIGINS", None)  # 문제가 될 수 있는 환경변수 제거
    
    # 배포 설정에서 안전한 설정 가져오기
    deploy_config = DeploymentConfig.get_safe_environment_config()
    
    # 기본값으로 재시도
    settings = Settings(
        cors_origins=deploy_config.get("cors_origins", ["http://localhost:3000"]),
        environment=deploy_config.get("environment", "development"),
        mongodb_url=deploy_config.get("mongodb_url", "mongodb://localhost:27017"),
        database_name=deploy_config.get("database_name", "xai_community"),
    )


def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings instance
    """
    return settings