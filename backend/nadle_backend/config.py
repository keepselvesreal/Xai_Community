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
    
    # config.py 파일이 위치한 디렉토리 (backend 디렉토리)를 기준으로 .env 파일 검색
    config_dir = Path(__file__).parent.parent  # nadle_backend의 상위 디렉토리 (backend)
    
    # 자동 검색 우선순위 (개발 환경에서만)
    env_file_candidates = [
        ".env.dev",        # 개발용 환경변수 파일 (git에서 무시됨)
        ".env.example",    # 템플릿 파일 (git에서 추적됨)
    ]
    
    for candidate in env_file_candidates:
        env_path = config_dir / candidate
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
        extra="ignore",  # Cloud Run 환경변수 허용을 위해 임시로 ignore 사용
        # Cloud Run에서 문제되는 환경변수들 무시
        env_ignore={"google_application_credentials", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "K_SERVICE", "K_REVISION", "K_CONFIGURATION"}
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
        default="development",
        description="애플리케이션 배포 환경 (development/staging/production/test) - 반드시 환경변수 파일에서 설정 필요"
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """환경변수가 명시적으로 설정되었는지 검증"""
        # 시스템 환경변수나 .env 파일에서 ENVIRONMENT가 설정되었는지 확인
        env_from_system = os.getenv("ENVIRONMENT")
        env_file = find_env_file()
        
        # 환경변수 파일이나 시스템 환경변수에서 명시적으로 설정되었는지 확인
        explicitly_set = False
        
        if env_file:
            # .env 파일에서 ENVIRONMENT 찾기
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('ENVIRONMENT='):
                            env_from_file = line.split('=', 1)[1].strip().strip('"\'')
                            print(f"✅ ENVIRONMENT 설정 확인: {env_from_file} (파일: {env_file})")
                            explicitly_set = True
                            break
            except Exception as e:
                print(f"⚠️  환경변수 파일 읽기 실패: {e}")
        
        if env_from_system:
            print(f"✅ ENVIRONMENT 설정 확인: {env_from_system} (시스템 환경변수)")
            explicitly_set = True
        
        # CI/테스트 환경에서는 예외 처리
        if (os.getenv("GITHUB_ACTIONS") == "true" or 
            os.getenv("CI") == "true" or
            os.getenv("PYTEST_CURRENT_TEST")):  # pytest 환경 감지
            print("ℹ️  CI/테스트 환경에서 ENVIRONMENT 기본값 사용")
            return v
        
        # 개발/프로덕션 환경에서는 강제
        if not explicitly_set:
            raise ValueError(
                "ENVIRONMENT는 반드시 환경변수 파일(.env.dev, .env.prod) 또는 "
                "시스템 환경변수에서 명시적으로 설정되어야 합니다. "
                "다음 중 하나를 수행해주세요: "
                "1. .env.dev 파일에 ENVIRONMENT=development 추가, "
                "2. .env.prod 파일에 ENVIRONMENT=production 추가, "
                "3. 시스템 환경변수로 export ENVIRONMENT=development 설정"
            )
        
        return v
    
    # === 서버 설정 ===
    port: int = Field(
        default=8080,  # Cloud Run 기본 포트
        ge=1,
        le=65535,
        description="서버 청취 포트 번호 (1-65535) - Cloud Run에서는 PORT 환경변수로 자동 설정",
        env="PORT"  # 명시적으로 PORT 환경변수 사용
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
    
    @field_validator('smtp_port', mode='before')
    @classmethod
    def parse_smtp_port(cls, v):
        """SMTP 포트 파싱 - 빈 문자열 처리"""
        if v == '' or v is None:
            return 587  # 기본값
        return int(v)
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
    
    @field_validator('smtp_use_tls', mode='before')
    @classmethod
    def parse_smtp_use_tls(cls, v):
        """SMTP TLS 설정 파싱 - 빈 문자열 처리"""
        if v == '' or v is None:
            return True  # 기본값
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    from_email: str = Field(
        default="noreply@example.com",
        description="Email address for sending emails"
    )
    from_name: str = Field(
        default="XAI Community",
        description="Display name for sender"
    )
    
    # Email Verification Settings
    email_verification_expire_minutes: int = Field(
        default=5,
        gt=0,
        description="Email verification token expiration time in minutes"
    )
    email_verification_code_length: int = Field(
        default=6,
        ge=4,
        le=8,
        description="Length of email verification code"
    )
    email_verification_max_attempts: int = Field(
        default=5,
        gt=0,
        description="Maximum verification attempts before blocking"
    )
    
    # Comment Configuration
    max_comment_depth: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum depth for nested comment replies (1-10)"
    )
    
    # === Redis 설정 ===
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis 연결 URL (redis://host:port 형식) - 개발환경용"
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
    
    # === Upstash Redis 설정 (staging/production) ===
    upstash_redis_rest_url: Optional[str] = Field(
        default=None,
        description="Upstash Redis REST API URL - staging/production환경용"
    )
    upstash_redis_rest_token: Optional[str] = Field(
        default=None,
        description="Upstash Redis REST API 토큰 - staging/production환경용"
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
    
    @property
    def use_upstash_redis(self) -> bool:
        """Upstash Redis 사용 여부 결정"""
        # staging 또는 production 환경에서 Upstash 설정이 있으면 사용
        return (
            self.environment in ["staging", "production"] and
            self.upstash_redis_rest_url is not None and
            self.upstash_redis_rest_token is not None
        )
    
    @property
    def redis_key_prefix(self) -> str:
        """환경별 Redis 키 프리픽스 반환"""
        if self.environment == "staging":
            return "stage:"
        elif self.environment == "production":
            return "prod:"
        elif self.environment == "development":
            return "dev:"
        elif self.environment == "test":
            return "test:"
        else:
            # 알 수 없는 환경은 기본값
            return "unknown:"
    
    # === Sentry 모니터링 설정 ===
    sentry_dsn: Optional[str] = Field(
        default=None,
        env="SENTRY_DSN",
        description="Sentry DSN (에러 추적 및 성능 모니터링) - 환경변수 SENTRY_DSN"
    )
    sentry_environment: Optional[str] = Field(
        default=None,
        env="SENTRY_ENVIRONMENT",
        description="Sentry 환경 설정 (자동으로 ENVIRONMENT 값 사용)"
    )
    sentry_traces_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        env="SENTRY_TRACES_SAMPLE_RATE",
        description="Sentry 성능 추적 샘플링 비율 (0.0-1.0)"
    )
    sentry_send_default_pii: bool = Field(
        default=True,
        env="SENTRY_SEND_DEFAULT_PII",
        description="Sentry에 개인정보 전송 여부"
    )
    
    # === 보안 설정 ===
    security_headers_enabled: bool = Field(
        default=True,
        description="보안 헤더 미들웨어 활성화 여부"
    )
    hsts_max_age: int = Field(
        default=31536000,  # 1년
        gt=0,
        description="HSTS 헤더 max-age 값 (초 단위)"
    )
    csp_report_uri: Optional[str] = Field(
        default=None,
        description="CSP 위반 보고서 수집 URI"
    )
    
    # === 환경변수 보안 설정 ===
    mask_sensitive_logs: bool = Field(
        default=True,
        description="로그에서 민감한 정보 마스킹 여부"
    )
    environment_security_check: bool = Field(
        default=True,
        description="시작시 환경변수 보안 검증 여부"
    )
    
    
    # === 디스코드 웹훅 설정 ===
    discord_webhook_url: Optional[str] = Field(
        default=None,
        description="디스코드 웹훅 URL"
    )
    
    # === 업타임 모니터링 설정 ===
    # UptimeRobot에서 HetrixTools로 마이그레이션
    uptimerobot_api_key: Optional[str] = Field(
        default=None,
        description="UptimeRobot API 키 (deprecated, use hetrixtools_api_token)"
    )
    
    hetrixtools_api_token: Optional[str] = Field(
        default=None,
        description="HetrixTools API 토큰"
    )
    
    # === 인프라 모니터링 설정 ===
    # Google Cloud Run
    gcp_project_id: Optional[str] = Field(
        default=None,
        description="Google Cloud 프로젝트 ID - Cloud Run 모니터링용"
    )
    gcp_service_account_path: Optional[str] = Field(
        default=None,
        description="Google Cloud 서비스 계정 JSON 파일 경로"
    )
    gcp_service_name: Optional[str] = Field(
        default=None,
        description="Google Cloud Run 서비스 이름"
    )
    gcp_region: Optional[str] = Field(
        default=None,
        description="Google Cloud Run 서비스 리전"
    )
    
    # Vercel
    vercel_api_token: Optional[str] = Field(
        default=None,
        description="Vercel API 토큰"
    )
    vercel_team_id: Optional[str] = Field(
        default=None,
        description="Vercel 팀 ID"
    )
    vercel_project_id: Optional[str] = Field(
        default=None,
        description="Vercel 프로젝트 ID"
    )
    
    # MongoDB Atlas
    atlas_public_key: Optional[str] = Field(
        default=None,
        description="MongoDB Atlas API 공개키"
    )
    atlas_private_key: Optional[str] = Field(
        default=None,
        description="MongoDB Atlas API 비밀키"
    )
    atlas_group_id: Optional[str] = Field(
        default=None,
        description="MongoDB Atlas 그룹(프로젝트) ID"
    )
    atlas_cluster_name: Optional[str] = Field(
        default=None,
        description="MongoDB Atlas 클러스터 이름"
    )
    
    # Upstash Redis (추가 - 기존 REST API 외에 Dashboard API)
    upstash_email: Optional[str] = Field(
        default=None,
        description="Upstash 계정 이메일 - API 인증용"
    )
    upstash_api_key: Optional[str] = Field(
        default=None,
        description="Upstash Dashboard API 키"
    )
    upstash_database_id: Optional[str] = Field(
        default=None,
        description="Upstash Redis 데이터베이스 ID"
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
        
        # 환경변수 보안 검증 (활성화된 경우)
        if self.environment_security_check:
            self._perform_security_check()
        
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
    
    def _perform_security_check(self):
        """환경변수 보안 검증 수행"""
        try:
            from nadle_backend.utils.security import verify_environment_security, mask_sensitive_data
            
            security_results = verify_environment_security()
            
            if security_results["overall_status"] != "secure":
                print("⚠️  보안 검증 경고:")
                
                for violation in security_results.get("environment_variables", []):
                    print(f"   - {violation['message']}")
                
                for issue in security_results.get("file_permissions", []):
                    print(f"   - {issue['message']}")
                
                if self.environment == "production":
                    raise ValueError("프로덕션 환경에서 보안 위험이 감지되었습니다.")
            else:
                print("✅ 환경변수 보안 검증 통과")
                
        except ImportError:
            print("ℹ️  보안 유틸리티를 찾을 수 없어 보안 검증을 건너뜁니다.")
        except Exception as e:
            print(f"⚠️  보안 검증 중 오류 발생: {e}")
            if self.environment == "production":
                raise
    
    def get_masked_config(self) -> dict:
        """민감한 정보가 마스킹된 설정 반환"""
        try:
            from nadle_backend.utils.security import mask_sensitive_data
            return mask_sensitive_data(self.__dict__.copy())
        except ImportError:
            # 폴백: 간단한 마스킹
            config = self.__dict__.copy()
            sensitive_keys = ['secret_key', 'mongodb_url', 'smtp_password', 'sentry_dsn']
            
            for key in sensitive_keys:
                if key in config and config[key]:
                    value = str(config[key])
                    if len(value) > 8:
                        config[key] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                    else:
                        config[key] = "*" * len(value)
            
            return config
    
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