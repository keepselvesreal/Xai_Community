"""
보안 유틸리티 모듈

환경변수 보안, 시크릿 관리, 데이터 검증 등의 보안 관련 기능
"""

import os
import re
import stat
import secrets
import string
import hashlib
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class EnvironmentSecurityValidator:
    """환경변수 보안 검증기"""
    
    # 민감한 키워드 패턴
    SENSITIVE_PATTERNS = [
        r'password',
        r'secret',
        r'key',
        r'token',
        r'credential',
        r'auth',
        r'api_key',
        r'private',
        r'smtp.*pass',
        r'db.*pass',
        r'database.*pass'
    ]
    
    # 하드코딩된 시크릿 패턴
    HARDCODED_SECRET_PATTERNS = [
        r'["\']([a-zA-Z0-9+/]{40,})["\']',  # Base64 패턴
        r'["\']([a-fA-F0-9]{32,})["\']',    # Hex 패턴
        r'sk-[a-zA-Z0-9]{20,}',             # API 키 패턴
        r'mongodb://[^:]+:[^@]+@',          # MongoDB 연결 문자열
        r'postgres://[^:]+:[^@]+@',         # PostgreSQL 연결 문자열
    ]
    
    def __init__(self):
        self.sensitive_regex = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.SENSITIVE_PATTERNS
        ]
        self.secret_regex = [
            re.compile(pattern) 
            for pattern in self.HARDCODED_SECRET_PATTERNS
        ]
    
    def scan_env_content(self, content: str) -> List[Dict[str, Any]]:
        """환경변수 파일 내용에서 민감한 데이터 탐지"""
        violations = []
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                # 민감한 키 확인
                for pattern in self.sensitive_regex:
                    if pattern.search(key):
                        violations.append({
                            "type": "sensitive_variable",
                            "line": line_num,
                            "field": key,
                            "message": f"민감한 환경변수가 평문으로 저장됨: {key}",
                            "severity": "high"
                        })
                        break
                
                # 값이 너무 단순한지 확인
                if self._is_weak_value(value):
                    violations.append({
                        "type": "weak_value",
                        "line": line_num,
                        "field": key,
                        "message": f"약한 값이 설정됨: {key}",
                        "severity": "medium"
                    })
        
        return violations
    
    def validate_current_environment(self) -> List[Dict[str, Any]]:
        """현재 환경변수 검증"""
        violations = []
        
        for var_name, var_value in os.environ.items():
            # 민감한 변수명 확인
            for pattern in self.sensitive_regex:
                if pattern.search(var_name):
                    violations.append({
                        "type": "exposed_sensitive_var",
                        "variable": var_name,
                        "message": f"민감한 환경변수가 노출됨: {var_name}",
                        "severity": "high"
                    })
                    break
        
        return violations
    
    def check_file_permissions(self, file_path: str) -> List[Dict[str, Any]]:
        """환경변수 파일 권한 검증"""
        issues = []
        
        try:
            file_stat = os.stat(file_path)
            file_mode = stat.filemode(file_stat.st_mode)
            
            # 파일 권한이 너무 열려있는지 확인 (644보다 열려있으면 위험)
            if file_stat.st_mode & 0o077:  # others나 group에게 write 권한이 있음
                issues.append({
                    "type": "file_permissions",
                    "file": file_path,
                    "permissions": file_mode,
                    "message": "환경변수 파일의 권한이 너무 열려있음 (권장: 600)",
                    "severity": "high"
                })
        
        except OSError as e:
            issues.append({
                "type": "file_access_error",
                "file": file_path,
                "message": f"파일 접근 오류: {e}",
                "severity": "medium"
            })
        
        return issues
    
    def scan_code_for_secrets(self, code_content: str) -> List[Dict[str, Any]]:
        """코드에서 하드코딩된 시크릿 탐지"""
        violations = []
        
        for line_num, line in enumerate(code_content.split('\n'), 1):
            for pattern in self.secret_regex:
                matches = pattern.finditer(line)
                for match in matches:
                    violations.append({
                        "type": "hardcoded_secret",
                        "line": line_num,
                        "match": match.group(0)[:20] + "...",  # 일부만 표시
                        "message": "하드코딩된 시크릿 발견",
                        "severity": "critical"
                    })
        
        return violations
    
    def _is_weak_value(self, value: str) -> bool:
        """값이 약한지 확인"""
        if not value:
            return True
        
        weak_patterns = [
            r'^(password|secret|key|admin|test|demo)$',
            r'^(123|abc|qwe|pass)',
            r'^.{1,5}$'  # 너무 짧음
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return True
        
        return False


class SecretManager:
    """시크릿 관리 클래스"""
    
    def generate_secret(self, length: int = 32) -> str:
        """강한 시크릿 생성"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_api_key(self, prefix: str = "sk") -> str:
        """API 키 생성"""
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        return f"{prefix}-{random_part}"
    
    def is_strong_secret(self, secret: str) -> bool:
        """시크릿이 강한지 검증"""
        if len(secret) < 16:
            return False
        
        # 다양한 문자 타입 포함 확인
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret)
        
        # 최소 3가지 타입 포함
        score = sum([has_upper, has_lower, has_digit, has_special])
        return score >= 3
    
    def hash_secret(self, secret: str) -> str:
        """시크릿 해시화"""
        return hashlib.sha256(secret.encode()).hexdigest()


class EnvironmentEncryption:
    """환경변수 암호화 클래스"""
    
    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            # 마스터 키가 없으면 환경변수에서 가져오거나 생성
            master_key = os.getenv("MASTER_ENCRYPTION_KEY")
            if master_key:
                self.key = base64.urlsafe_b64decode(master_key.encode())
            else:
                self.key = Fernet.generate_key()
                logger.warning("MASTER_ENCRYPTION_KEY not set, using temporary key")
        else:
            self.key = key
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, value: str) -> str:
        """값 암호화"""
        encrypted_bytes = self.cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """값 복호화"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    
    def get_key_string(self) -> str:
        """키를 문자열로 반환 (환경변수 저장용)"""
        return base64.urlsafe_b64encode(self.key).decode()


def validate_required_env_vars(required_vars: List[str]) -> List[str]:
    """필수 환경변수 검증"""
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars


def validate_env_var_format(var_name: str, value: str) -> bool:
    """환경변수 형식 검증"""
    if not value:
        return False
    
    validators = {
        "DATABASE_URL": _validate_database_url,
        "EMAIL": _validate_email,
        "URL": _validate_url,
        "PORT": _validate_port,
    }
    
    # 변수명에서 타입 추론
    for var_type, validator in validators.items():
        if var_type.lower() in var_name.lower():
            return validator(value)
    
    return True  # 특별한 검증이 없으면 통과


def _validate_database_url(url: str) -> bool:
    """데이터베이스 URL 검증"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['mongodb', 'mongodb+srv', 'postgresql', 'mysql']
    except:
        return False


def _validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def _validate_url(url: str) -> bool:
    """URL 형식 검증"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and parsed.netloc
    except:
        return False


def _validate_port(port: str) -> bool:
    """포트 번호 검증"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except:
        return False


def validate_cors_origins(origins: List[str]) -> bool:
    """CORS Origins 보안 검증"""
    dangerous_patterns = [
        r'^\*$',          # 모든 origin 허용
        r'^javascript:',  # 스크립트 URL
        r'^data:',        # 데이터 URL
        r'^file:',        # 파일 URL
        r'^ftp:',         # FTP URL
    ]
    
    for origin in origins:
        for pattern in dangerous_patterns:
            if re.match(pattern, origin, re.IGNORECASE):
                return False
        
        # HTTP는 개발 환경에서만 허용
        if origin.startswith('http://') and 'localhost' not in origin and '127.0.0.1' not in origin:
            return False
    
    return True


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """민감한 데이터 마스킹"""
    masked_data = data.copy()
    
    sensitive_keys = [
        'password', 'secret', 'key', 'token', 'credential',
        'auth', 'api_key', 'private', 'smtp_password'
    ]
    
    def mask_value(value: str) -> str:
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]
    
    for key, value in masked_data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str):
                masked_data[key] = mask_value(value)
    
    return masked_data


def secure_random_string(length: int = 32) -> str:
    """보안적으로 안전한 랜덤 문자열 생성"""
    return secrets.token_urlsafe(length)


def verify_environment_security() -> Dict[str, Any]:
    """전체 환경 보안 검증"""
    validator = EnvironmentSecurityValidator()
    
    results = {
        "environment_variables": validator.validate_current_environment(),
        "file_permissions": [],
        "overall_status": "secure"
    }
    
    # 환경변수 파일들 검증
    env_files = ['.env', '.env.local', '.env.production', '.env.development']
    for env_file in env_files:
        if os.path.exists(env_file):
            file_issues = validator.check_file_permissions(env_file)
            if file_issues:
                results["file_permissions"].extend(file_issues)
    
    # 전체 상태 결정
    total_issues = len(results["environment_variables"]) + len(results["file_permissions"])
    if total_issues > 0:
        results["overall_status"] = "issues_found"
    
    return results