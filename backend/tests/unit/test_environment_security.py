"""
환경변수 보안 검증 테스트

민감한 정보가 환경변수에 올바르게 저장되고 노출되지 않는지 검증
"""

import pytest
import os
import tempfile
from unittest.mock import patch, mock_open
from pathlib import Path

from nadle_backend.config import settings
from nadle_backend.utils.security import EnvironmentSecurityValidator


class TestEnvironmentSecurityValidator:
    """환경변수 보안 검증기 테스트"""
    
    @pytest.fixture
    def security_validator(self):
        """보안 검증기 인스턴스"""
        return EnvironmentSecurityValidator()
    
    def test_detect_sensitive_data_in_env_file(self, security_validator):
        """환경변수 파일에서 민감한 데이터 탐지"""
        sensitive_content = """
DATABASE_URL=mongodb://admin:password123@localhost:27017/test
SECRET_KEY=super-secret-key-123
JWT_SECRET=another-secret
SMTP_PASSWORD=email-password
API_KEY=sk-1234567890abcdef
        """
        
        violations = security_validator.scan_env_content(sensitive_content)
        
        assert len(violations) > 0
        assert any("PASSWORD" in v["field"] for v in violations)
        assert any("SECRET" in v["field"] for v in violations)
        assert any("API_KEY" in v["field"] for v in violations)
    
    def test_validate_environment_variables(self, security_validator):
        """현재 환경변수 검증"""
        with patch.dict(os.environ, {
            'SAFE_VARIABLE': 'safe_value',
            'DANGEROUS_PASSWORD': 'exposed_password',
            'SECRET_KEY': 'exposed_secret'
        }):
            violations = security_validator.validate_current_environment()
            
            # 민감한 변수들이 감지되어야 함
            dangerous_vars = [v["variable"] for v in violations]
            assert "DANGEROUS_PASSWORD" in dangerous_vars
            assert "SECRET_KEY" in dangerous_vars
            assert "SAFE_VARIABLE" not in dangerous_vars
    
    def test_check_env_file_permissions(self, security_validator):
        """환경변수 파일 권한 검증"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("SECRET_KEY=test")
            temp_file_path = temp_file.name
        
        try:
            # 파일 권한을 777로 설정 (보안상 위험)
            os.chmod(temp_file_path, 0o777)
            
            issues = security_validator.check_file_permissions(temp_file_path)
            assert len(issues) > 0
            assert "권한이 너무 열려있음" in issues[0]["message"]
            
            # 파일 권한을 600으로 설정 (안전)
            os.chmod(temp_file_path, 0o600)
            
            issues = security_validator.check_file_permissions(temp_file_path)
            assert len(issues) == 0
            
        finally:
            os.unlink(temp_file_path)
    
    def test_detect_hardcoded_secrets_in_code(self, security_validator):
        """코드에서 하드코딩된 시크릿 탐지"""
        code_content = '''
import os

# 나쁜 예시 - 하드코딩된 시크릿
DATABASE_URL = "mongodb://admin:password123@localhost:27017/prod"
SECRET_KEY = "hard-coded-secret-key"

# 좋은 예시 - 환경변수 사용
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
        '''
        
        violations = security_validator.scan_code_for_secrets(code_content)
        
        assert len(violations) >= 2
        hardcoded_secrets = [v for v in violations if v["type"] == "hardcoded_secret"]
        assert len(hardcoded_secrets) >= 2


class TestEnvironmentConfiguration:
    """환경 설정 보안 테스트"""
    
    def test_production_environment_security(self):
        """프로덕션 환경 보안 설정 검증"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'SECRET_KEY': 'prod-secret-key'
        }):
            # 설정을 다시 로드
            from nadle_backend.config import Settings
            prod_settings = Settings()
            
            assert prod_settings.environment == "production"
            assert prod_settings.debug is False
            # 프로덕션에서는 디버그가 비활성화되어야 함
    
    def test_development_environment_isolation(self):
        """개발 환경 격리 검증"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DATABASE_URL': 'mongodb://localhost:27017/dev_db'
        }):
            from nadle_backend.config import Settings
            dev_settings = Settings()
            
            assert dev_settings.environment == "development"
            # 개발 DB URL은 프로덕션 패턴과 달라야 함
            assert "dev" in dev_settings.database_url.lower() or "localhost" in dev_settings.database_url
    
    def test_sensitive_settings_not_exposed(self):
        """민감한 설정이 로그나 응답에 노출되지 않는지 검증"""
        # 설정 객체를 직렬화했을 때 민감한 정보가 포함되지 않아야 함
        settings_dict = settings.__dict__.copy()
        
        # 민감한 필드들이 마스킹되거나 제외되어야 함
        sensitive_fields = ['secret_key', 'jwt_secret', 'database_url', 'smtp_password']
        
        for field in sensitive_fields:
            if hasattr(settings, field):
                value = getattr(settings, field)
                if value:
                    # 실제 값이 노출되지 않고 마스킹되어야 함
                    assert not any(secret in str(settings_dict) for secret in [value[:4], value[-4:]])


class TestSecretManagement:
    """시크릿 관리 테스트"""
    
    def test_secret_rotation_capability(self):
        """시크릿 로테이션 기능 테스트"""
        from nadle_backend.utils.security import SecretManager
        
        secret_manager = SecretManager()
        
        # 새 시크릿 생성
        new_secret = secret_manager.generate_secret()
        assert len(new_secret) >= 32
        assert new_secret != secret_manager.generate_secret()  # 매번 다른 값
    
    def test_secret_validation(self):
        """시크릿 강도 검증"""
        from nadle_backend.utils.security import SecretManager
        
        secret_manager = SecretManager()
        
        # 약한 시크릿들
        weak_secrets = ["password", "123456", "secret", "key"]
        for weak in weak_secrets:
            assert not secret_manager.is_strong_secret(weak)
        
        # 강한 시크릿
        strong_secret = secret_manager.generate_secret()
        assert secret_manager.is_strong_secret(strong_secret)
    
    def test_environment_variable_encryption(self):
        """환경변수 암호화 기능 테스트"""
        from nadle_backend.utils.security import EnvironmentEncryption
        
        encryptor = EnvironmentEncryption()
        
        original_value = "sensitive-database-password"
        encrypted_value = encryptor.encrypt(original_value)
        decrypted_value = encryptor.decrypt(encrypted_value)
        
        assert encrypted_value != original_value
        assert decrypted_value == original_value


class TestConfigurationValidation:
    """설정 검증 테스트"""
    
    def test_required_environment_variables(self):
        """필수 환경변수 검증"""
        from nadle_backend.utils.security import validate_required_env_vars
        
        required_vars = [
            "SECRET_KEY",
            "DATABASE_URL", 
            "ENVIRONMENT"
        ]
        
        missing_vars = validate_required_env_vars(required_vars)
        
        # 누락된 필수 변수가 있으면 실패해야 함
        if missing_vars:
            pytest.fail(f"Missing required environment variables: {missing_vars}")
    
    def test_environment_variable_format_validation(self):
        """환경변수 형식 검증"""
        from nadle_backend.utils.security import validate_env_var_format
        
        # DATABASE_URL 형식 검증
        valid_db_urls = [
            "mongodb://username:password@host:port/database",
            "mongodb+srv://username:password@cluster.mongodb.net/database"
        ]
        
        invalid_db_urls = [
            "invalid-url",
            "http://not-mongodb-url",
            ""
        ]
        
        for valid_url in valid_db_urls:
            assert validate_env_var_format("DATABASE_URL", valid_url)
        
        for invalid_url in invalid_db_urls:
            assert not validate_env_var_format("DATABASE_URL", invalid_url)
    
    def test_cors_origins_validation(self):
        """CORS Origins 보안 검증"""
        from nadle_backend.utils.security import validate_cors_origins
        
        # 안전한 origins
        safe_origins = [
            "https://mydomain.com",
            "https://app.mydomain.com",
            "https://api.mydomain.com"
        ]
        
        # 위험한 origins
        dangerous_origins = [
            "*",  # 모든 origin 허용
            "http://",  # 불완전한 URL
            "javascript:",  # 스크립트 URL
            "data:",  # 데이터 URL
        ]
        
        assert validate_cors_origins(safe_origins)
        assert not validate_cors_origins(dangerous_origins)