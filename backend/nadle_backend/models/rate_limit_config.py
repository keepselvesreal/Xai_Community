from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional
from enum import Enum


class RateLimitStrategy(str, Enum):
    """Rate limiting 키 생성 전략"""
    IP = "ip"
    USER = "user"
    COMPOSITE = "composite"


class RateLimitConfig(BaseModel):
    """Rate limiting 설정 모델"""
    
    endpoint: str = Field(
        description="Rate limiting을 적용할 엔드포인트 패턴 (예: /auth/*, /posts/*)"
    )
    limit: int = Field(
        gt=0,
        description="제한 횟수 (예: 5회)"
    )
    window: int = Field(
        gt=0,
        description="시간 윈도우 (초 단위, 예: 60초)"
    )
    key_strategy: RateLimitStrategy = Field(
        default=RateLimitStrategy.IP,
        description="키 생성 전략: ip(IP 기반), user(사용자 기반), composite(IP+사용자)"
    )
    enabled: bool = Field(
        default=True,
        description="Rate limiting 활성화 여부"
    )
    custom_error_message: Optional[str] = Field(
        default=None,
        description="제한 초과 시 사용자 정의 에러 메시지"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/auth/*",
                "limit": 3,
                "window": 60,
                "key_strategy": "ip",
                "enabled": True,
                "custom_error_message": "로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요."
            }
        }


class RateLimitConfigRegistry:
    """Rate limiting 설정 레지스트리"""
    
    # 기본 Rate Limiting 설정들
    DEFAULT_CONFIGS: Dict[str, RateLimitConfig] = {
        "auth_login": RateLimitConfig(
            endpoint="/auth/login",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP,
            custom_error_message="로그인 시도가 너무 많습니다. 1분 후 다시 시도해주세요."
        ),
        "auth_register": RateLimitConfig(
            endpoint="/auth/register",
            limit=2,
            window=300,  # 5분
            key_strategy=RateLimitStrategy.IP,
            custom_error_message="회원가입 시도가 너무 많습니다. 5분 후 다시 시도해주세요."
        ),
        "posts_create": RateLimitConfig(
            endpoint="/posts",
            limit=5,
            window=60,
            key_strategy=RateLimitStrategy.USER,
            custom_error_message="게시글 작성이 너무 빈번합니다. 1분 후 다시 시도해주세요."
        ),
        "posts_list": RateLimitConfig(
            endpoint="/posts/list",
            limit=20,
            window=60,
            key_strategy=RateLimitStrategy.IP,
        ),
        "comments_create": RateLimitConfig(
            endpoint="/comments",
            limit=10,
            window=60,
            key_strategy=RateLimitStrategy.USER,
            custom_error_message="댓글 작성이 너무 빈번합니다. 1분 후 다시 시도해주세요."
        ),
        "files_upload": RateLimitConfig(
            endpoint="/files/upload",
            limit=3,
            window=60,
            key_strategy=RateLimitStrategy.IP,
            custom_error_message="파일 업로드가 너무 빈번합니다. 1분 후 다시 시도해주세요."
        ),
        "email_verification": RateLimitConfig(
            endpoint="/auth/send-verification-email",
            limit=3,
            window=300,  # 5분
            key_strategy=RateLimitStrategy.IP,
            custom_error_message="이메일 인증 요청이 너무 많습니다. 5분 후 다시 시도해주세요."
        ),
    }
    
    @classmethod
    def get_config(cls, endpoint_key: str) -> Optional[RateLimitConfig]:
        """특정 엔드포인트의 Rate Limiting 설정 반환"""
        return cls.DEFAULT_CONFIGS.get(endpoint_key)
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, RateLimitConfig]:
        """모든 Rate Limiting 설정 반환"""
        return cls.DEFAULT_CONFIGS.copy()
    
    @classmethod
    def is_enabled(cls, endpoint_key: str) -> bool:
        """특정 엔드포인트의 Rate Limiting 활성화 여부 확인"""
        config = cls.get_config(endpoint_key)
        return config.enabled if config else False


class RateLimitResult(BaseModel):
    """Rate limiting 결과 모델"""
    
    allowed: bool = Field(description="요청 허용 여부")
    limit: int = Field(description="제한 횟수")
    remaining: int = Field(description="남은 요청 횟수")
    reset_time: int = Field(description="제한 리셋 시간 (Unix timestamp)")
    retry_after: Optional[int] = Field(
        default=None,
        description="재시도 가능 시간 (초)"
    )
    key: str = Field(description="Rate limiting에 사용된 키")
    
    class Config:
        json_schema_extra = {
            "example": {
                "allowed": False,
                "limit": 3,
                "remaining": 0,
                "reset_time": 1721548860,
                "retry_after": 45,
                "key": "dev:rate_limit:auth:192.168.1.1:1721548800"
            }
        }