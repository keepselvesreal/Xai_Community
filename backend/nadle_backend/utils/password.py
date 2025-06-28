"""Password hashing and validation utilities."""

import re
from passlib.context import CryptContext
from typing import Optional


class PasswordManager:
    """Password manager for hashing and verifying passwords using bcrypt."""
    
    def __init__(
        self,
        bcrypt_rounds: int = 12,
        min_password_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special_char: bool = True
    ):
        """Initialize password manager.
        
        Args:
            bcrypt_rounds: Number of bcrypt rounds (4-31, default 12)
            min_password_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special_char: Require at least one special character
        """
        self.bcrypt_rounds = bcrypt_rounds
        self.min_password_length = min_password_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special_char = require_special_char
        
        # Create password context with bcrypt
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=self.bcrypt_rounds
        )
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Bcrypt hashed password string
            
        Raises:
            ValueError: If password is None or empty
        """
        if password is None:
            raise ValueError("Password cannot be None")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        return self.pwd_context.hash(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Bcrypt hashed password to verify against
            
        Returns:
            True if password matches hash, False otherwise
            
        Raises:
            ValueError: If password or hash is None or empty
        """
        if password is None:
            raise ValueError("Password cannot be None")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        if hashed_password is None:
            raise ValueError("Hash cannot be None")
        
        if not hashed_password:
            raise ValueError("Hash cannot be empty")
        
        try:
            return self.pwd_context.verify(password, hashed_password)
        except Exception:
            # If verification fails due to invalid hash format, return False
            return False
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password meets strength requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets all requirements, False otherwise
        """
        if not password:
            return False
        
        # Check minimum length
        if len(password) < self.min_password_length:
            return False
        
        # Check character requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            return False
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            return False
        
        if self.require_digit and not re.search(r'\d', password):
            return False
        
        if self.require_special_char and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            return False
        
        return True
    
    def get_password_requirements(self) -> dict:
        """Get current password requirements.
        
        Returns:
            Dictionary describing password requirements
        """
        requirements = {
            "min_length": self.min_password_length,
            "require_uppercase": self.require_uppercase,
            "require_lowercase": self.require_lowercase,
            "require_digit": self.require_digit,
            "require_special_char": self.require_special_char
        }
        
        return requirements
    
    def get_password_strength_errors(self, password: str) -> list[str]:
        """Get list of password strength requirement violations.
        
        Args:
            password: Password to check
            
        Returns:
            List of error messages for unmet requirements
        """
        errors = []
        
        if not password:
            errors.append("Password is required")
            return errors
        
        if len(password) < self.min_password_length:
            errors.append(f"Password must be at least {self.min_password_length} characters long")
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special_char and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """Check if password hash needs to be updated.
        
        This is useful when you change bcrypt rounds and want to
        upgrade existing hashes on next login.
        
        Args:
            hashed_password: Existing hash to check
            
        Returns:
            True if hash should be updated, False otherwise
        """
        try:
            return self.pwd_context.needs_update(hashed_password)
        except Exception:
            # If we can't determine, assume it needs rehashing
            return True
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure random password.
        
        Args:
            length: Length of password to generate (minimum 8)
            
        Returns:
            Randomly generated secure password
        """
        import secrets
        import string
        
        if length < 8:
            length = 8
        
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character from each required set
        password_chars = []
        
        if self.require_lowercase:
            password_chars.append(secrets.choice(lowercase))
        if self.require_uppercase:
            password_chars.append(secrets.choice(uppercase))
        if self.require_digit:
            password_chars.append(secrets.choice(digits))
        if self.require_special_char:
            password_chars.append(secrets.choice(special))
        
        # Fill remaining length with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        remaining_length = length - len(password_chars)
        
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(all_chars))
        
        # Shuffle the characters to avoid predictable patterns
        secrets.SystemRandom().shuffle(password_chars)
        
        return ''.join(password_chars)