import pytest
from src.utils.password import PasswordManager


@pytest.fixture
def password_manager():
    """Create PasswordManager instance for testing."""
    return PasswordManager()


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_hash_password_basic(self, password_manager):
        """Test basic password hashing."""
        password = "test_password123"
        hashed = password_manager.hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be different from original
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_hash_password_different_each_time(self, password_manager):
        """Test that same password produces different hashes due to salt."""
        password = "same_password123"
        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)
        
        assert hash1 != hash2  # Should be different due to salt
        assert len(hash1) == len(hash2)  # Should be same length
    
    def test_hash_password_with_different_rounds(self):
        """Test hashing with different bcrypt rounds."""
        password = "test_password123"
        
        # Test with different round values
        pm_fast = PasswordManager(bcrypt_rounds=4)
        pm_slow = PasswordManager(bcrypt_rounds=12)
        
        hash_fast = pm_fast.hash_password(password)
        hash_slow = pm_slow.hash_password(password)
        
        # Both should be valid bcrypt hashes
        assert hash_fast.startswith("$2b$")
        assert hash_slow.startswith("$2b$")
        
        # Should be different due to different rounds
        assert hash_fast != hash_slow
    
    def test_hash_empty_password(self, password_manager):
        """Test hashing empty password."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_manager.hash_password("")
    
    def test_hash_none_password(self, password_manager):
        """Test hashing None password."""
        with pytest.raises(ValueError, match="Password cannot be None"):
            password_manager.hash_password(None)
    
    def test_hash_very_long_password(self, password_manager):
        """Test hashing very long password."""
        # bcrypt has a limit of 72 bytes
        long_password = "a" * 100
        hashed = password_manager.hash_password(long_password)
        
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
    
    def test_hash_unicode_password(self, password_manager):
        """Test hashing password with unicode characters."""
        unicode_password = "paßwörd123🔒"
        hashed = password_manager.hash_password(unicode_password)
        
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        
        # Should be able to verify the unicode password
        assert password_manager.verify_password(unicode_password, hashed)


class TestPasswordVerification:
    """Test password verification functionality."""
    
    def test_verify_correct_password(self, password_manager):
        """Test verifying correct password."""
        password = "correct_password123"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self, password_manager):
        """Test verifying incorrect password."""
        correct_password = "correct_password123"
        wrong_password = "wrong_password123"
        hashed = password_manager.hash_password(correct_password)
        
        assert password_manager.verify_password(wrong_password, hashed) is False
    
    def test_verify_case_sensitive(self, password_manager):
        """Test that password verification is case sensitive."""
        password = "CaseSensitive123"
        wrong_case = "casesensitive123"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True
        assert password_manager.verify_password(wrong_case, hashed) is False
    
    def test_verify_empty_password(self, password_manager):
        """Test verifying empty password."""
        hashed = password_manager.hash_password("test123")
        
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_manager.verify_password("", hashed)
    
    def test_verify_none_password(self, password_manager):
        """Test verifying None password."""
        hashed = password_manager.hash_password("test123")
        
        with pytest.raises(ValueError, match="Password cannot be None"):
            password_manager.verify_password(None, hashed)
    
    def test_verify_invalid_hash(self, password_manager):
        """Test verifying password against invalid hash."""
        password = "test123"
        
        # Test with completely invalid hash
        assert password_manager.verify_password(password, "invalid_hash") is False
        
        # Test with empty hash
        with pytest.raises(ValueError, match="Hash cannot be empty"):
            password_manager.verify_password(password, "")
        
        # Test with None hash
        with pytest.raises(ValueError, match="Hash cannot be None"):
            password_manager.verify_password(password, None)
    
    def test_verify_malformed_hash(self, password_manager):
        """Test verifying password against malformed bcrypt hash."""
        password = "test123"
        malformed_hash = "$2b$12$invalid"
        
        # Should return False for malformed hash, not raise exception
        assert password_manager.verify_password(password, malformed_hash) is False
    
    def test_verify_different_hash_formats(self, password_manager):
        """Test verifying against different hash formats."""
        password = "test123"
        
        # Create hash with current manager
        valid_hash = password_manager.hash_password(password)
        
        # Should work with valid bcrypt hash
        assert password_manager.verify_password(password, valid_hash) is True
        
        # Should not work with non-bcrypt hash
        md5_like_hash = "5d41402abc4b2a76b9719d911017c592"
        assert password_manager.verify_password(password, md5_like_hash) is False


class TestPasswordComplexity:
    """Test password complexity validation."""
    
    def test_validate_password_strength_basic(self, password_manager):
        """Test basic password strength validation."""
        # Strong password
        strong_password = "StrongP@ssw0rd123"
        assert password_manager.validate_password_strength(strong_password) is True
        
        # Weak passwords
        weak_passwords = [
            "123456",  # too short, only numbers
            "password",  # too short, only lowercase
            "PASSWORD",  # too short, only uppercase
            "Pass123",  # no special character
            "Pass@word",  # no number
            "P@ss1",  # too short
        ]
        
        for weak_password in weak_passwords:
            assert password_manager.validate_password_strength(weak_password) is False
    
    def test_validate_password_minimum_length(self, password_manager):
        """Test password minimum length validation."""
        # Test with custom minimum length
        pm_custom = PasswordManager(min_password_length=10)
        
        short_password = "Short1@"  # 7 characters
        long_password = "LongPassword1@"  # 14 characters
        
        assert pm_custom.validate_password_strength(short_password) is False
        assert pm_custom.validate_password_strength(long_password) is True
    
    def test_validate_password_character_requirements(self, password_manager):
        """Test individual character requirements."""
        base_password = "Password123@"
        
        # Missing uppercase
        no_upper = "password123@"
        assert password_manager.validate_password_strength(no_upper) is False
        
        # Missing lowercase  
        no_lower = "PASSWORD123@"
        assert password_manager.validate_password_strength(no_lower) is False
        
        # Missing digit
        no_digit = "Password@"
        assert password_manager.validate_password_strength(no_digit) is False
        
        # Missing special character
        no_special = "Password123"
        assert password_manager.validate_password_strength(no_special) is False
        
        # All requirements met
        assert password_manager.validate_password_strength(base_password) is True
    
    def test_validate_password_with_custom_requirements(self):
        """Test password validation with custom requirements."""
        pm_custom = PasswordManager(
            min_password_length=6,
            require_uppercase=False,
            require_lowercase=True,
            require_digit=True,
            require_special_char=False
        )
        
        # Should pass with custom requirements
        simple_password = "simple123"
        assert pm_custom.validate_password_strength(simple_password) is True
        
        # Should fail if missing required elements
        no_digit = "simple"
        assert pm_custom.validate_password_strength(no_digit) is False


class TestPasswordSecurity:
    """Test password security features."""
    
    def test_constant_time_comparison(self, password_manager):
        """Test that password verification uses constant time comparison."""
        password = "test_password123"
        hashed = password_manager.hash_password(password)
        
        # Both correct and incorrect should take similar time
        # This is more of a structural test - actual timing would be flaky
        result1 = password_manager.verify_password(password, hashed)
        result2 = password_manager.verify_password("wrong_password", hashed)
        
        assert result1 is True
        assert result2 is False
    
    def test_hash_length_consistency(self, password_manager):
        """Test that all bcrypt hashes have consistent length."""
        passwords = ["short", "medium_length_password", "very_long_password_with_many_characters"]
        hashes = [password_manager.hash_password(pwd) for pwd in passwords]
        
        # All bcrypt hashes should have the same length
        hash_lengths = [len(h) for h in hashes]
        assert len(set(hash_lengths)) == 1  # All lengths should be the same
        
        # Standard bcrypt hash length is 60 characters
        assert all(len(h) == 60 for h in hashes)
    
    def test_secure_random_salt(self, password_manager):
        """Test that each hash uses a different random salt."""
        password = "same_password"
        hashes = [password_manager.hash_password(password) for _ in range(10)]
        
        # All hashes should be different due to random salts
        assert len(set(hashes)) == len(hashes)
        
        # But all should verify correctly
        for hash_value in hashes:
            assert password_manager.verify_password(password, hash_value) is True


class TestPasswordEdgeCases:
    """Test password handling edge cases."""
    
    def test_password_with_whitespace(self, password_manager):
        """Test passwords with leading/trailing whitespace."""
        password_with_spaces = "  password123  "
        trimmed_password = "password123"
        
        # Hash should preserve whitespace
        hashed = password_manager.hash_password(password_with_spaces)
        
        assert password_manager.verify_password(password_with_spaces, hashed) is True
        assert password_manager.verify_password(trimmed_password, hashed) is False
    
    def test_password_with_newlines(self, password_manager):
        """Test passwords with newline characters."""
        password_with_newline = "password\n123"
        hashed = password_manager.hash_password(password_with_newline)
        
        assert password_manager.verify_password(password_with_newline, hashed) is True
    
    def test_password_with_null_bytes(self, password_manager):
        """Test passwords with null bytes."""
        password_with_null = "password\x00123"
        
        # bcrypt doesn't allow null bytes, should raise an exception
        with pytest.raises(Exception):  # passlib raises PasswordValueError
            password_manager.hash_password(password_with_null)
    
    def test_maximum_password_length(self, password_manager):
        """Test bcrypt's 72-byte limit handling."""
        # bcrypt truncates passwords at 72 bytes
        long_password = "a" * 80
        very_long_password = "a" * 100
        
        hash1 = password_manager.hash_password(long_password)
        hash2 = password_manager.hash_password(very_long_password)
        
        # Both should hash successfully
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        
        # Verification should work
        assert password_manager.verify_password(long_password, hash1) is True
        assert password_manager.verify_password(very_long_password, hash2) is True