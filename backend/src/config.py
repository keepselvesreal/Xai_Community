from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "xai_community"
    
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    api_title: str = "Xai Community API"
    api_version: str = "1.0.0"
    api_description: str = "Content Management API for Xai Community"
    
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    environment: str = "development"
    
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()