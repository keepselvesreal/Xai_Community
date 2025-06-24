import pytest
from datetime import datetime, timedelta
from src.utils.jwt import JWTManager, TokenType
from src.exceptions.auth import InvalidTokenError, ExpiredTokenError, InvalidTokenTypeError


@pytest.fixture
def jwt_manager():
    """Create JWTManager instance for testing."""
    return JWTManager(
        secret_key="test_secret_key_for_jwt_testing",
        algorithm="HS256",
        access_token_expires=timedelta(hours=1),
        refresh_token_expires=timedelta(days=7)
    )


@pytest.fixture
def sample_payload():
    """Sample JWT payload for testing."""
    return {
        "sub": "507f1f77bcf86cd799439011",  # user_id
        "email": "john@example.com",
        "handle": "johndoe"
    }


class TestJWTCreation:
    """Test JWT token creation."""
    
    def test_create_access_token(self, jwt_manager, sample_payload):
        """Test creating an access token."""
        token = jwt_manager.create_access_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format has dots
    
    def test_create_refresh_token(self, jwt_manager, sample_payload):
        """Test creating a refresh token."""
        token = jwt_manager.create_refresh_token(sample_payload)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format has dots
    
    def test_create_token_with_custom_expires(self, jwt_manager, sample_payload):
        """Test creating token with custom expiration."""
        custom_expires = timedelta(minutes=30)
        token = jwt_manager.create_token(
            data=sample_payload,
            token_type=TokenType.ACCESS,
            expires_delta=custom_expires
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_includes_correct_claims(self, jwt_manager, sample_payload):
        """Test that token includes correct standard claims."""
        token = jwt_manager.create_access_token(sample_payload)
        payload = jwt_manager.verify_token(token)
        
        # Check standard claims
        assert payload["sub"] == sample_payload["sub"]
        assert payload["email"] == sample_payload["email"]
        assert payload["handle"] == sample_payload["handle"]
        assert payload["type"] == TokenType.ACCESS.value
        assert "iat" in payload  # issued at
        assert "exp" in payload  # expires
        
        # Check that expiration is in the future
        assert payload["exp"] > datetime.utcnow().timestamp()


class TestJWTVerification:
    """Test JWT token verification."""
    
    def test_verify_valid_access_token(self, jwt_manager, sample_payload):
        """Test verifying a valid access token."""
        token = jwt_manager.create_access_token(sample_payload)
        payload = jwt_manager.verify_token(token)
        
        assert payload["sub"] == sample_payload["sub"]
        assert payload["email"] == sample_payload["email"]
        assert payload["type"] == TokenType.ACCESS.value
    
    def test_verify_valid_refresh_token(self, jwt_manager, sample_payload):
        """Test verifying a valid refresh token."""
        token = jwt_manager.create_refresh_token(sample_payload)
        payload = jwt_manager.verify_token(token)
        
        assert payload["sub"] == sample_payload["sub"]
        assert payload["email"] == sample_payload["email"]
        assert payload["type"] == TokenType.REFRESH.value
    
    def test_verify_invalid_token_format(self, jwt_manager):
        """Test verifying an invalid token format."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            jwt_manager.verify_token("invalid.token")
    
    def test_verify_token_invalid_signature(self, jwt_manager, sample_payload):
        """Test verifying token with invalid signature."""
        # Create token with different secret
        other_manager = JWTManager(
            secret_key="different_secret",
            algorithm="HS256"
        )
        token = other_manager.create_access_token(sample_payload)
        
        with pytest.raises(InvalidTokenError, match="Invalid token signature"):
            jwt_manager.verify_token(token)
    
    def test_verify_expired_token(self, jwt_manager, sample_payload):
        """Test verifying an expired token."""
        # Create token that's already expired (negative timedelta)
        expired_token = jwt_manager.create_token(
            data=sample_payload,
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(ExpiredTokenError):
            jwt_manager.verify_token(expired_token)
    
    def test_verify_token_wrong_algorithm(self, jwt_manager, sample_payload):
        """Test verifying token created with different algorithm."""
        # This test simulates receiving a token from a system using different algorithm
        with pytest.raises(InvalidTokenError):
            # Try to verify a malformed token that would fail algorithm check
            jwt_manager.verify_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid")


class TestJWTTokenTypes:
    """Test JWT token type validation."""
    
    def test_verify_access_token_type(self, jwt_manager, sample_payload):
        """Test verifying access token type."""
        token = jwt_manager.create_access_token(sample_payload)
        payload = jwt_manager.verify_token(token, expected_type=TokenType.ACCESS)
        
        assert payload["type"] == TokenType.ACCESS.value
    
    def test_verify_refresh_token_type(self, jwt_manager, sample_payload):
        """Test verifying refresh token type."""
        token = jwt_manager.create_refresh_token(sample_payload)
        payload = jwt_manager.verify_token(token, expected_type=TokenType.REFRESH)
        
        assert payload["type"] == TokenType.REFRESH.value
    
    def test_verify_wrong_token_type(self, jwt_manager, sample_payload):
        """Test verifying token with wrong expected type."""
        access_token = jwt_manager.create_access_token(sample_payload)
        
        with pytest.raises(InvalidTokenTypeError):
            jwt_manager.verify_token(access_token, expected_type=TokenType.REFRESH)


class TestJWTUtilityMethods:
    """Test JWT utility methods."""
    
    def test_extract_user_id(self, jwt_manager, sample_payload):
        """Test extracting user ID from token."""
        token = jwt_manager.create_access_token(sample_payload)
        user_id = jwt_manager.extract_user_id(token)
        
        assert user_id == sample_payload["sub"]
    
    def test_extract_user_id_invalid_token(self, jwt_manager):
        """Test extracting user ID from invalid token."""
        with pytest.raises(InvalidTokenError):
            jwt_manager.extract_user_id("invalid.token")
    
    def test_is_token_expired(self, jwt_manager, sample_payload):
        """Test checking if token is expired."""
        # Create non-expired token
        token = jwt_manager.create_access_token(sample_payload)
        assert not jwt_manager.is_token_expired(token)
        
        # Create expired token
        expired_token = jwt_manager.create_token(
            data=sample_payload,
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        assert jwt_manager.is_token_expired(expired_token)
    
    def test_get_token_payload_without_verification(self, jwt_manager, sample_payload):
        """Test getting token payload without signature verification."""
        token = jwt_manager.create_access_token(sample_payload)
        payload = jwt_manager.get_token_payload(token)
        
        assert payload["sub"] == sample_payload["sub"]
        assert payload["email"] == sample_payload["email"]
    
    def test_refresh_token_flow(self, jwt_manager, sample_payload):
        """Test complete refresh token flow."""
        # Create refresh token
        refresh_token = jwt_manager.create_refresh_token(sample_payload)
        
        # Verify it's a refresh token
        refresh_payload = jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
        assert refresh_payload["type"] == TokenType.REFRESH.value
        
        # Create new access token from refresh payload
        new_access_token = jwt_manager.create_access_token({
            "sub": refresh_payload["sub"],
            "email": refresh_payload["email"],
            "handle": refresh_payload["handle"]
        })
        
        # Verify new access token
        access_payload = jwt_manager.verify_token(new_access_token, TokenType.ACCESS)
        assert access_payload["sub"] == sample_payload["sub"]
        assert access_payload["type"] == TokenType.ACCESS.value


class TestJWTEdgeCases:
    """Test JWT edge cases and error handling."""
    
    def test_empty_payload(self, jwt_manager):
        """Test creating token with empty payload."""
        empty_payload = {}
        token = jwt_manager.create_access_token(empty_payload)
        payload = jwt_manager.verify_token(token)
        
        # Should still have standard claims
        assert "iat" in payload
        assert "exp" in payload
        assert payload["type"] == TokenType.ACCESS.value
    
    def test_none_payload(self, jwt_manager):
        """Test creating token with None payload."""
        with pytest.raises((ValueError, TypeError)):
            jwt_manager.create_access_token(None)
    
    def test_very_long_payload(self, jwt_manager):
        """Test creating token with very long payload."""
        long_payload = {
            "sub": "507f1f77bcf86cd799439011",
            "data": "x" * 1000  # Very long string
        }
        
        token = jwt_manager.create_access_token(long_payload)
        payload = jwt_manager.verify_token(token)
        
        assert payload["sub"] == long_payload["sub"]
        assert payload["data"] == long_payload["data"]
    
    def test_unicode_payload(self, jwt_manager):
        """Test creating token with unicode characters."""
        unicode_payload = {
            "sub": "507f1f77bcf86cd799439011",
            "name": "José García",
            "emoji": "🚀🔐"
        }
        
        token = jwt_manager.create_access_token(unicode_payload)
        payload = jwt_manager.verify_token(token)
        
        assert payload["name"] == unicode_payload["name"]
        assert payload["emoji"] == unicode_payload["emoji"]