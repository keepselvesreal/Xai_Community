from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Literal, Optional, Union
from datetime import timedelta
import os
from pathlib import Path


def find_env_file() -> Optional[str]:
    """
    환경변수 파일을 우선순위에 따라 찾습니다.
    
    우선순위:
    1. ENV_FILE_PATH 환경변수 (명시적 파일 경로 지정)
    2. .env.dev (개발용 환경변수 파일) - 개발 환경에서만
    3. .env.example (템플릿 파일) - 개발 환경에서만
    
    프로덕션이나 CI 환경에서는 .env 파일을 로드하지 않습니다.
    
    Returns:
        찾은 환경변수 파일의 경로, 없으면 None
    """
    # GitHub Actions나 CI 환경에서는 .env 파일을 읽지 않음
    if os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true":
        return None
    
    # 프로덕션 환경 확인
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        return None  # 프로덕션에서는 .env 파일을 로드하지 않음
    
    # 명시적 경로 오버라이드 확인
    explicit_path = os.getenv("ENV_FILE_PATH")
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    
    # 자동 검색 우선순위 (개발 환경에서만)
    env_file_candidates = [
        ".env.dev",        # 개발용 환경변수 파일 (git에서 무시됨)
        ".env.example",    # 템플릿 파일 (git에서 추적됨)
    ]
    
    for candidate in env_file_candidates:
        env_path = Path(candidate)
        if env_path.exists():
            return str(env_path)
    
    return None


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    
    Pydantic BaseSettings를 상속받아 환경변수 기반으로 설정을 관리합니다.
    개발환경에서는 .env.dev 파일을, 프로덕션에서는 시스템 환경변수를 사용합니다.
    """
    
    def __init__(self, **kwargs):
        """초기화 시 환경변수 파일 존재 여부 검증"""
        env_file = find_env_file()
        if not env_file:
            # CI/production 환경이 아닌 경우에만 경고
            if not (os.getenv("GITHUB_ACTIONS") == "true" or 
                   os.getenv("CI") == "true" or 
                   os.getenv("ENVIRONMENT") == "production"):
                print("⚠️  WARNING: 환경변수 파일(.env.dev, .env.prod 등)이 없습니다.")
                print("   프로덕션 환경이 아닌 경우 환경변수 파일을 생성하거나")
                print("   시스템 환경변수 ENVIRONMENT를 설정해주세요.")
        else:
            print(f"✅ 환경변수 파일 로드: {env_file}")
        
        super().__init__(**kwargs)
    
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="forbid",
        # 환경변수에서 제외할 필드 없음 (단순화됨)
        env_ignore=set()
    )
    
    # === 데이터베이스 설정 ===
    mongodb_url: str = Field(
        description="MongoDB 연결 URL (Atlas 클라우드 또는 로컬) - 환경변수 MONGODB_URL 필수"
    )
    database_name: str = Field(
        default="REQUIRED_SET_IN_ENV",
        description="애플리케이션에서 사용할 데이터베이스 이름 - 환경변수 DATABASE_NAME 설정 권장"
    )
    
    # === 컬렉션 설정 ===
    users_collection: str = Field(
        default="users",
        description="사용자 문서를 저장할 컬렉션 이름"
    )
    posts_collection: str = Field(
        default="posts",
        description="게시글 문서를 저장할 컬렉션 이름"
    )
    comments_collection: str = Field(
        default="comments",
        description="댓글 문서를 저장할 컬렉션 이름"
    )
    post_stats_collection: str = Field(
        default="post_stats",
        description="게시글 통계를 저장할 컬렉션 이름"
    )
    user_reactions_collection: str = Field(
        default="user_reactions",
        description="사용자 반응(좋아요/싫어요)을 저장할 컬렉션 이름"
    )
    files_collection: str = Field(
        default="files",
        description="파일 메타데이터를 저장할 컬렉션 이름"
    )
    stats_collection: str = Field(
        default="stats",
        description="애플리케이션 통계를 저장할 컬렉션 이름"
    )
    
    # === 보안 설정 ===
    secret_key: str = Field(
        description="JWT 토큰 서명용 비밀키 (최소 32자 이상) - 환경변수 SECRET_KEY 필수",
        min_length=32
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT 서명 알고리즘"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
        description="액세스 토큰 만료 시간 (분 단위)"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        gt=0,
        description="리프레시 토큰 만료 시간 (일 단위)"
    )
    
    @property
    def access_token_expire(self) -> timedelta:
        """액세스 토큰 만료 시간을 timedelta 객체로 반환합니다."""
        return timedelta(minutes=self.access_token_expire_minutes)
    
    @property
    def refresh_token_expire(self) -> timedelta:
        """리프레시 토큰 만료 시간을 timedelta 객체로 반환합니다."""
        return timedelta(days=self.refresh_token_expire_days)
    
    # === API 설정 ===
    api_title: str = Field(
        default="Content Management API",
        description="API 서비스 제목"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API 버전 번호"
    )
    api_description: str = Field(
        default="FastAPI backend for content management system",
        description="API 서비스 설명"
    )
    
    # === CORS 설정 ===
    allowed_origins: Optional[List[str]] = Field(
        default=None,
        description="프론트엔드 접근을 허용할 CORS origins 목록 - 환경변수 ALLOWED_ORIGINS 권장"
    )
    
    # 프론트엔드 URL (프로덕션 Vercel 배포용)
    frontend_url: Optional[str] = Field(
        default=None,
        description="CORS 및 리다이렉트용 프론트엔드 URL - 환경변수 FRONTEND_URL 권장"
    )
    
    # === 환경 설정 ===
    environment: Literal["development", "staging", "production", "test"] = Field(
        description="애플리케이션 배포 환경 (development/staging/production/test) - 반드시 환경변수 파일에서 설정 필요"
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """환경변수가 명시적으로 설정되었는지 검증"""
        # 시스템 환경변수나 .env 파일에서 ENVIRONMENT가 설정되었는지 확인
        env_from_system = os.getenv("ENVIRONMENT")
        env_file = find_env_file()
        
        if env_file:
            # .env 파일에서 ENVIRONMENT 찾기
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('ENVIRONMENT='):
                            env_from_file = line.split('=', 1)[1].strip().strip('"\'')
                            print(f"✅ ENVIRONMENT 설정 확인: {env_from_file} (파일: {env_file})")
                            return v
            except Exception as e:
                print(f"⚠️  환경변수 파일 읽기 실패: {e}")
        
        if env_from_system:
            print(f"✅ ENVIRONMENT 설정 확인: {env_from_system} (시스템 환경변수)")
            return v
        
        # CI나 프로덕션 환경에서는 경고만
        if (os.getenv("GITHUB_ACTIONS") == "true" or 
            os.getenv("CI") == "true"):
            print("ℹ️  CI 환경에서 ENVIRONMENT 기본값 사용")
            return v
            
        # 개발 환경에서는 강력한 경고
        print("🚨 CRITICAL: ENVIRONMENT 환경변수가 명시적으로 설정되지 않았습니다!")
        print("   다음 중 하나를 수행해주세요:")
        print("   1. .env.dev 파일에 ENVIRONMENT=development 추가")
        print("   2. .env.prod 파일에 ENVIRONMENT=production 추가")
        print("   3. 시스템 환경변수로 export ENVIRONMENT=development 설정")
        print(f"   현재 사용 중인 기본값: {v}")
        
        return v
    
    # === 서버 설정 ===
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="서버 청취 포트 번호 (1-65535)"
    )
    host: str = Field(
        default="0.0.0.0",
        description="서버 호스트 주소 (0.0.0.0은 모든 인터페이스에서 접근 허용)"
    )
    
    # === 로깅 설정 ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="애플리케이션 로깅 레벨"
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
    
    # === Redis 설정 ===
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis 연결 URL (redis://host:port 형식)"
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis 데이터베이스 번호 (0-15)"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis 비밀번호 (설정된 경우)"
    )
    
    # Redis 캐시 설정
    cache_ttl_user: int = Field(
        default=3600,
        gt=0,
        description="사용자 정보 캐시 TTL (초 단위)"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Redis 캐시 활성화 여부"
    )
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """비밀키 길이와 안전성을 검증합니다."""
        if len(v) < 32:
            raise ValueError("비밀키는 최소 32자 이상이어야 합니다")
        
        # 개발 환경에서도 안전하지 않은 기본값 경고
        unsafe_patterns = [
            "your-secret-key-here",
            "change-in-production", 
            "default-secret",
            "test-secret",
            "dev-secret"
        ]
        
        if any(pattern in v.lower() for pattern in unsafe_patterns):
            environment = os.getenv("ENVIRONMENT", "development")
            if environment == "production":
                raise ValueError("프로덕션에서 안전하지 않은 비밀키를 사용할 수 없습니다")
            else:
                print(f"⚠️  경고: 안전하지 않은 비밀키가 감지되었습니다. 프로덕션에서는 안전한 비밀키를 사용하세요.")
        
        return v
    
    @field_validator("mongodb_url")
    @classmethod
    def validate_mongodb_url(cls, v: str) -> str:
        """MongoDB 연결 URL 형식을 검증합니다."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL은 mongodb:// 또는 mongodb+srv://로 시작해야 합니다")
        return v
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v) -> Optional[List[str]]:
        """허용된 CORS origins를 간단하게 파싱합니다."""        
        if v is None:
            return None  # _setup_cors_origins에서 환경별로 처리
        
        if isinstance(v, list):
            return v
        
        if isinstance(v, str):
            # JSON 배열 형태 처리 (예: '["http://localhost:3000", "http://localhost:5173"]')
            if v.strip().startswith("[") and v.strip().endswith("]"):
                import json
                try:
                    parsed = json.loads(v.strip())
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except json.JSONDecodeError:
                    pass
            
            # 쉼표로 구분된 문자열 처리 (예: 'url1,url2,url3')
            if "," in v:
                return [url.strip() for url in v.split(",") if url.strip()]
            else:
                return [v.strip()] if v.strip() else None
        
        return None
    
    def __init__(self, **kwargs):
        """간단한 환경변수 기반 설정으로 초기화합니다."""
        super().__init__(**kwargs)
        self._setup_cors_origins()
        if os.getenv("ENVIRONMENT") == "production":
            self.validate_production_settings()
    
    def _setup_cors_origins(self):
        """환경에 따른 CORS origins 설정 (환경변수 필수화 적용)"""
        environment = os.getenv("ENVIRONMENT", "development")
        
        print(f"=== CORS 설정 - 환경: {environment} ===")
        
        # CORS origins가 설정되지 않은 경우 환경별 기본값 적용
        if self.allowed_origins is None:
            if environment == "production":
                # 프로덕션: 환경변수 필수
                allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
                if allowed_origins_env:
                    if "," in allowed_origins_env:
                        self.allowed_origins = [url.strip() for url in allowed_origins_env.split(",") if url.strip()]
                    else:
                        self.allowed_origins = [allowed_origins_env.strip()]
                    print(f"프로덕션 CORS origins (환경변수): {self.allowed_origins}")
                else:
                    print("❌ 오류: 프로덕션에서 ALLOWED_ORIGINS 환경변수가 설정되지 않았습니다!")
                    raise ValueError("프로덕션에서 ALLOWED_ORIGINS 환경변수가 필수입니다")
            else:
                # 개발환경: 안전한 로컬 기본값
                self.allowed_origins = [
                    "http://localhost:3000", 
                    "http://127.0.0.1:3000", 
                    "http://localhost:5173", 
                    "http://127.0.0.1:5173"
                ]
                print(f"개발 환경 CORS origins (기본값): {self.allowed_origins}")
        else:
            print(f"CORS origins (설정된 값): {self.allowed_origins}")
        
        print(f"최종 CORS origins: {self.allowed_origins}")
        print("=== CORS 설정 완료 ===")
    
    def validate_production_settings(self):
        """프로덕션 환경에서 중요 설정들을 검증합니다."""
        errors = []
        
        # CORS origins 검증
        default_dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
        localhost_patterns = ["localhost", "127.0.0.1"]
        
        if not self.allowed_origins:
            errors.append("ALLOWED_ORIGINS가 설정되지 않음")
        elif self.allowed_origins == default_dev_origins:
            errors.append("ALLOWED_ORIGINS가 개발용 기본값으로 설정되어 있음")
        elif any(any(pattern in origin for pattern in localhost_patterns) for origin in self.allowed_origins):
            errors.append("ALLOWED_ORIGINS에 localhost URL이 포함되어 있음 (프로덕션 부적절)")
        
        # Database name 검증
        if self.database_name == "REQUIRED_SET_IN_ENV":
            errors.append("DATABASE_NAME이 환경변수로 설정되지 않음")
        elif self.database_name in ["test", "dev", "development"]:
            errors.append("DATABASE_NAME이 개발/테스트용 이름으로 설정되어 있음")
        
        # MongoDB URL 검증 (기본값 체크 불가 - 환경변수 필수이므로)
        if not self.mongodb_url.startswith(("mongodb://", "mongodb+srv://")):
            errors.append("MONGODB_URL 형식이 올바르지 않음")
        elif "localhost" in self.mongodb_url:
            errors.append("MONGODB_URL이 localhost를 가리키고 있음 (프로덕션 부적절)")
        
        if errors:
            print(f"❌ 프로덕션 검증 오류:")
            for error in errors:
                print(f"   - {error}")
            raise ValueError(f"프로덕션 설정 오류: {len(errors)}개 문제 발견")
        else:
            print("✅ 프로덕션 설정 검증 통과")
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """환경별 설정 소스 커스터마이징"""
        # 프로덕션에서는 dotenv 파일은 제외하고 환경변수는 사용
        if os.getenv("ENVIRONMENT") == "production":
            return (init_settings, env_settings)  # 초기화 설정과 환경변수만 사용
        else:
            # 개발 환경에서는 기본 소스들 사용
            return (init_settings, env_settings, dotenv_settings, file_secret_settings)
    
    # 참고: Config 클래스는 model_config로 대체되었습니다


# GitHub Actions 지원과 함께 전역 설정 인스턴스 생성
if os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI") == "true":
    # CI 환경에서는 모든 환경변수를 무시하고 안전한 기본값만 사용
    print("CI 환경 감지 - 안전한 기본값 사용")
    
    # 문제가 될 수 있는 환경변수들을 임시 제거
    problematic_env_vars = [
        "SECRET_KEY", "MONGODB_URL", "DATABASE_NAME", "PORT", "LOG_LEVEL",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_USE_TLS",
        "ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS", "ENVIRONMENT"
    ]
    
    original_env = {}
    for var in problematic_env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    try:
        settings = Settings()
        print("✅ CI 모드에서 설정 초기화 성공")
    except Exception as e:
        print(f"❌ CI 설정 실패: {e}")
        # 최후의 폴백: 완전 기본값 사용
        settings = Settings(
            mongodb_url="mongodb://localhost:27017",
            database_name="xai_community_test",
            secret_key="test-secret-key-for-ci-environment-32-chars-long",
            environment="development"
        )
        print("✅ 최소 CI 설정 사용")
    
    # 환경변수 복원 (나중에 필요할 수 있음)
    for var, value in original_env.items():
        os.environ[var] = value

else:
    # 일반 환경에서는 기존 방식 사용
    try:
        settings = Settings()
    except Exception as e:
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            # 프로덕션에서는 폴백 사용하지 않고 바로 실패
            print(f"❌ 프로덕션 환경 설정 오류: {e}")
            print("프로덕션에서는 모든 필수 환경변수가 설정되어야 합니다:")
            print("- MONGODB_URL: MongoDB 연결 URL")
            print("- SECRET_KEY: JWT 서명용 비밀키")
            print("- DATABASE_NAME: 데이터베이스 이름")
            print("- ALLOWED_ORIGINS: CORS 허용 도메인")
            
            # 환경변수 상태 확인
            print("\n현재 환경변수 상태:")
            required_vars = ["MONGODB_URL", "SECRET_KEY", "DATABASE_NAME", "ALLOWED_ORIGINS"]
            for var in required_vars:
                value = os.getenv(var)
                if value:
                    # 민감한 정보는 일부만 표시
                    if var in ["MONGODB_URL", "SECRET_KEY"]:
                        masked = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
                        print(f"✅ {var}: {masked}")
                    else:
                        print(f"✅ {var}: {value}")
                else:
                    print(f"❌ {var}: 설정되지 않음")
            
            raise e
        else:
            # 개발 환경에서만 폴백 사용
            print(f"경고: 설정 초기화 실패: {e}")
            print("안전한 폴백 설정 사용... (개발 환경만)")
            
            settings = Settings(
                mongodb_url="mongodb://localhost:27017",
                secret_key="fallback-dev-secret-key-32-chars-minimum-length",
                database_name="xai_community_fallback",
                environment="development",
            )


def get_settings() -> Settings:
    """애플리케이션 설정을 반환합니다.
    
    Returns:
        Settings 인스턴스
    """
    return settings