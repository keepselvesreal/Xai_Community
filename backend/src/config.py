from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal, Optional, Union
from datetime import timedelta
import os
from pathlib import Path


def find_env_file() -> Optional[str]:
    """
    Find environment file with priority order:
    1. ENV_FILE_PATH environment variable (explicit override)
    2. .env.local (local development overrides)
    3. .env (main environment file)
    4. .env.example (template/example file)
    
    Returns:
        Path to the first found environment file, or None if none found
    """
    # Check for explicit path override
    explicit_path = os.getenv("ENV_FILE_PATH")
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    
    # Priority order for automatic discovery
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
    
    # Database Configuration
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL (Atlas or local)"
    )
    database_name: str = Field(
        default="app_database",
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
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="List of allowed CORS origins for frontend access"
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
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length and production safety."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # Check if using default key in production
        if (v == "your-secret-key-here-change-in-production-32-characters" and 
            os.getenv("ENVIRONMENT", "development") == "production"):
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
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle string representation of list
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [origin.strip() for origin in v.strip("[]").split(",")]
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = find_env_file()  # Use auto-discovery
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings instance
    """
    return settings