"""JWT token management utilities."""

from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
from nadle_backend.exceptions.auth import InvalidTokenError, ExpiredTokenError, InvalidTokenTypeError


class TokenType(Enum):
    """JWT token types."""
    ACCESS = "access"
    REFRESH = "refresh"


class JWTManager:
    """JWT token manager for creating and verifying tokens."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expires: timedelta = timedelta(hours=1),
        refresh_token_expires: timedelta = timedelta(days=7)
    ):
        """Initialize JWT manager.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm to use
            access_token_expires: Access token expiration time
            refresh_token_expires: Refresh token expiration time
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expires = access_token_expires
        self.refresh_token_expires = refresh_token_expires
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create an access token.
        
        Args:
            data: Payload data to include in token
            
        Returns:
            JWT access token string
        """
        return self.create_token(
            data=data,
            token_type=TokenType.ACCESS,
            expires_delta=self.access_token_expires
        )
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token.
        
        Args:
            data: Payload data to include in token
            
        Returns:
            JWT refresh token string
        """
        return self.create_token(
            data=data,
            token_type=TokenType.REFRESH,
            expires_delta=self.refresh_token_expires
        )
    
    def create_token(
        self,
        data: Dict[str, Any],
        token_type: TokenType,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT token with specified type and expiration.
        
        Args:
            data: Payload data to include in token
            token_type: Type of token (access or refresh)
            expires_delta: Custom expiration time
            
        Returns:
            JWT token string
            
        Raises:
            ValueError: If data is None
            TypeError: If data is not a dictionary
        """
        if data is None:
            raise ValueError("Token data cannot be None")
        
        if not isinstance(data, dict):
            raise TypeError("Token data must be a dictionary")
        
        # Create payload copy to avoid modifying original
        payload = data.copy()
        
        # Add standard claims
        now = datetime.utcnow()
        payload.update({
            "iat": now,  # issued at
            "type": token_type.value
        })
        
        # Add expiration
        if expires_delta:
            payload["exp"] = now + expires_delta
        elif token_type == TokenType.ACCESS:
            payload["exp"] = now + self.access_token_expires
        else:
            payload["exp"] = now + self.refresh_token_expires
        
        # Create and return token
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None
    ) -> Dict[str, Any]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            expected_type: Expected token type for validation
            
        Returns:
            Decoded token payload
            
        Raises:
            InvalidTokenError: If token is invalid or malformed
            ExpiredTokenError: If token is expired
            InvalidTokenTypeError: If token type doesn't match expected
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Validate token type if specified
            if expected_type:
                token_type = payload.get("type")
                if token_type != expected_type.value:
                    raise InvalidTokenTypeError(expected_type.value, token_type)
            
            return payload
            
        except ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except JWTError as e:
            error_msg = str(e).lower()
            if "signature" in error_msg:
                raise InvalidTokenError("Invalid token signature")
            else:
                raise InvalidTokenError("Invalid token format")
    
    def extract_user_id(self, token: str) -> str:
        """Extract user ID from token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID from token subject
            
        Raises:
            InvalidTokenError: If token is invalid
        """
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise InvalidTokenError("Token missing user ID")
        
        return user_id
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without raising exception.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            # Try to verify the token - if it raises ExpiredTokenError, it's expired
            self.verify_token(token)
            return False  # If verification succeeds, token is not expired
            
        except ExpiredTokenError:
            return True  # Token is expired
        except Exception:
            return True  # Any other error means token is invalid
    
    def get_token_payload(self, token: str) -> Dict[str, Any]:
        """Get token payload without signature verification.
        
        This method is useful for extracting information from tokens
        when you need to check expiration before verification.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload (unverified)
            
        Raises:
            InvalidTokenError: If token format is invalid
        """
        try:
            # Decode without verification
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": False, "verify_exp": False}
            )
        except Exception:
            raise InvalidTokenError("Invalid token format")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            ExpiredTokenError: If refresh token is expired
            InvalidTokenTypeError: If token is not a refresh token
        """
        # Verify it's a valid refresh token
        payload = self.verify_token(refresh_token, TokenType.REFRESH)
        
        # Extract user data for new access token
        user_data = {
            "sub": payload["sub"],
            "email": payload.get("email"),
            "handle": payload.get("handle")
        }
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        # Create new access token
        return self.create_access_token(user_data)
    
    def get_remaining_time(self, token: str) -> Optional[timedelta]:
        """Get remaining time before token expires.
        
        Args:
            token: JWT token string
            
        Returns:
            Remaining time as timedelta, or None if expired/invalid
        """
        try:
            payload = self.get_token_payload(token)
            exp = payload.get("exp")
            
            if not exp:
                return None
            
            remaining_seconds = exp - datetime.utcnow().timestamp()
            
            if remaining_seconds <= 0:
                return None  # Already expired
            
            return timedelta(seconds=remaining_seconds)
            
        except Exception:
            return None