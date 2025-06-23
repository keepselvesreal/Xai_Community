from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Literal
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database Configuration
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB Atlas connection URL"
    )
    database_name: str = Field(
        default="xai_community",
        description="MongoDB database name"
    )
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production-32-characters",
        description="Secret key for JWT tokens",
        min_length=32
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
        description="JWT token expiration time in minutes"
    )
    
    # API Configuration
    api_title: str = Field(
        default="Xai Community API",
        description="API title"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_description: str = Field(
        default="Content Management API for Xai Community",
        description="API description"
    )
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    
    # Environment Configuration
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )
    
    # Server Configuration
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Feature Flags
    enable_docs: bool = Field(
        default=True,
        description="Enable API documentation"
    )
    enable_cors: bool = Field(
        default=True,
        description="Enable CORS"
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
        env_file = "config/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"


# Create global settings instance
settings = Settings()