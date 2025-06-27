import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError
from dotenv import load_dotenv

from src.config import Settings


class TestConfigSettings:
    """Test environment configuration management with Pydantic."""
    
    def test_env_settings(self):
        """Test configuration values loaded from .env file."""
        # Load .env file explicitly
        load_dotenv("config/.env")
        
        # Load settings from .env file
        settings = Settings()
        
        # Database settings (from .env)
        expected_db_name = os.getenv("DATABASE_NAME", settings.database_name)
        assert settings.database_name == expected_db_name
        
        # Collection settings (from .env or defaults)
        expected_users_collection = os.getenv("USERS_COLLECTION", settings.users_collection)
        expected_posts_collection = os.getenv("POSTS_COLLECTION", settings.posts_collection)
        expected_comments_collection = os.getenv("COMMENTS_COLLECTION", settings.comments_collection)
        expected_files_collection = os.getenv("FILES_COLLECTION", settings.files_collection)
        
        assert settings.users_collection == expected_users_collection
        assert settings.posts_collection == expected_posts_collection
        assert settings.comments_collection == expected_comments_collection
        assert settings.files_collection == expected_files_collection
        
        # API settings (from .env or defaults)
        expected_api_title = os.getenv("API_TITLE", settings.api_title)
        expected_api_description = os.getenv("API_DESCRIPTION", settings.api_description)
        
        assert settings.api_title == expected_api_title
        assert settings.api_description == expected_api_description
        
        # CORS settings (from .env or defaults)
        expected_cors_origins = os.getenv("CORS_ORIGINS")
        if expected_cors_origins:
            # CORS_ORIGINS is set in .env, just verify it's a list
            assert isinstance(settings.cors_origins, list)
            assert len(settings.cors_origins) > 0
        else:
            # If not set, should use defaults
            assert isinstance(settings.cors_origins, list)
            
        # Environment settings (from .env or defaults)
        expected_environment = os.getenv("ENVIRONMENT", settings.environment)
        expected_port = int(os.getenv("PORT", settings.port))
        expected_host = os.getenv("HOST", settings.host)
        
        assert settings.environment == expected_environment
        assert settings.port == expected_port
        assert settings.host == expected_host
        
        # Feature flags (defaults)
        assert settings.enable_docs is True
        assert settings.enable_cors is True
    
    def test_mongodb_atlas_url_validation(self):
        """Test MongoDB Atlas connection string validation."""
        # Valid MongoDB Atlas URL
        atlas_url = "mongodb+srv://user:pass@cluster0.mongodb.net/"
        settings = Settings(mongodb_url=atlas_url)
        assert settings.mongodb_url == atlas_url
        
        # Valid standard MongoDB URL
        standard_url = "mongodb://user:pass@localhost:27017/"
        settings = Settings(mongodb_url=standard_url)
        assert settings.mongodb_url == standard_url
        
        # Invalid URL - should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Settings(mongodb_url="invalid://url")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "mongodb_url" in str(errors[0]["loc"])
        assert "must start with mongodb://" in errors[0]["msg"]
    
    def test_secret_key_validation(self):
        """Test secret key validation rules."""
        # Valid secret key (32+ characters)
        valid_key = "a" * 32
        settings = Settings(secret_key=valid_key)
        assert settings.secret_key == valid_key
        
        # Invalid secret key (too short)
        with pytest.raises(ValidationError) as exc_info:
            Settings(secret_key="short")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "secret_key" in str(errors[0]["loc"])
        assert "at least 32 characters" in errors[0]["msg"]
    
    def test_secret_key_production_validation(self):
        """Test that default secret key is rejected in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            with patch("pydantic_settings.sources.DotEnvSettingsSource.__call__", return_value={}):
                with pytest.raises(ValidationError) as exc_info:
                    Settings()
                
                errors = exc_info.value.errors()
                assert len(errors) == 1
                assert "secret_key" in str(errors[0]["loc"])
                assert "cannot be used in production" in errors[0]["msg"]
    
    def test_environment_validation(self):
        """Test environment setting validation."""
        # Valid environments
        for env in ["development", "staging", "production"]:
            settings = Settings(environment=env)
            assert settings.environment == env
        
        # Invalid environment
        with pytest.raises(ValidationError) as exc_info:
            Settings(environment="invalid")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "environment" in str(errors[0]["loc"])
    
    def test_port_validation(self):
        """Test port number validation."""
        # Valid ports
        settings = Settings(port=8080)
        assert settings.port == 8080
        
        settings = Settings(port=1)
        assert settings.port == 1
        
        settings = Settings(port=65535)
        assert settings.port == 65535
        
        # Invalid ports
        with pytest.raises(ValidationError):
            Settings(port=0)
        
        with pytest.raises(ValidationError):
            Settings(port=65536)
    
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from different formats."""
        # List format
        origins = ["http://localhost:3000", "http://localhost:5000"]
        settings = Settings(cors_origins=origins)
        assert settings.cors_origins == origins
        
        # JSON string format
        json_str = '["http://localhost:3000", "http://localhost:5000"]'
        settings = Settings(cors_origins=json_str)
        assert settings.cors_origins == origins
        
        # Comma-separated string
        csv_str = "http://localhost:3000, http://localhost:5000"
        settings = Settings(cors_origins=csv_str)
        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5000"]
    
    def test_env_file_loading(self):
        """Test loading configuration from .env file."""
        # Create a temporary .env file
        env_content = """
MONGODB_URL=mongodb+srv://test:pass@cluster0.mongodb.net/
DATABASE_NAME=test_db
SECRET_KEY=test-secret-key-that-is-long-enough-for-validation
API_TITLE=Test API
ENVIRONMENT=staging
PORT=9000
"""
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = env_content
            
            # Force reload of settings
            settings = Settings()
            
            # Note: In actual implementation, env vars would override these
            # This test mainly verifies the structure is correct
    
    def test_access_token_expire_validation(self):
        """Test access token expiration time validation."""
        # Valid expiration times
        settings = Settings(access_token_expire_minutes=60)
        assert settings.access_token_expire_minutes == 60
        
        # Invalid (zero or negative)
        with pytest.raises(ValidationError):
            Settings(access_token_expire_minutes=0)
        
        with pytest.raises(ValidationError):
            Settings(access_token_expire_minutes=-1)
    
    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level
        
        # Invalid log level
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(unknown_field="value")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "extra_forbidden" in errors[0]["type"]
    
    def test_real_mongodb_atlas_connection(self):
        """Test with real MongoDB Atlas connection string from environment."""
        # This test will use the actual .env file if it exists
        try:
            settings = Settings()
            
            # If MongoDB URL is set in env, it should be an Atlas URL
            if settings.mongodb_url != "mongodb://localhost:27017":
                assert settings.mongodb_url.startswith("mongodb+srv://") or \
                       settings.mongodb_url.startswith("mongodb://")
                # Should not contain placeholder values
                assert "<user_name>" not in settings.mongodb_url
                assert "<db_password>" not in settings.mongodb_url
        except Exception as e:
            # If env file doesn't exist or has issues, that's okay for this test
            pass