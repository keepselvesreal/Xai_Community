"""Authentication dependencies for FastAPI."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from nadle_backend.models.core import User
from nadle_backend.utils.jwt import JWTManager, TokenType
from nadle_backend.utils.password import PasswordManager
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.exceptions.auth import InvalidTokenError, ExpiredTokenError, InvalidTokenTypeError
from nadle_backend.exceptions.user import UserNotFoundError
from nadle_backend.config import get_settings


# Security scheme for Bearer token authentication
security = HTTPBearer(auto_error=False)


def get_jwt_manager() -> JWTManager:
    """Get JWT manager dependency.
    
    Returns:
        JWTManager instance configured with app settings
    """
    settings = get_settings()
    return JWTManager(
        secret_key=settings.secret_key,
        algorithm="HS256",
        access_token_expires=settings.access_token_expire,
        refresh_token_expires=settings.refresh_token_expire
    )


def get_password_manager() -> PasswordManager:
    """Get password manager dependency.
    
    Returns:
        PasswordManager instance with default configuration
    """
    return PasswordManager()


def get_user_repository() -> UserRepository:
    """Get user repository dependency.
    
    Returns:
        UserRepository instance
    """
    return UserRepository()


def extract_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Extract JWT token from Authorization header.
    
    Args:
        credentials: HTTP authorization credentials from Bearer token
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: If authorization header is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


async def get_current_user(
    token: str = Depends(extract_token_from_header),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    user_repository: UserRepository = Depends(get_user_repository)
) -> User:
    """Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from authorization header
        jwt_manager: JWT manager for token verification
        user_repository: User repository for database access
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token and extract payload
        payload = jwt_manager.verify_token(token, expected_type=TokenType.ACCESS)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ExpiredTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token expired: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Get user from database
        user = await user_repository.get_by_id(user_id)
        return user
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (user must be active status).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if current_user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    elif current_user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is suspended"
        )
    
    return current_user


def extract_optional_token_from_header(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Extract JWT token from Authorization header optionally.
    
    Args:
        credentials: HTTP authorization credentials from Bearer token
        
    Returns:
        JWT token string or None if not provided
    """
    if credentials is None or not credentials.credentials:
        return None
    return credentials.credentials


async def get_optional_current_user(
    token: Optional[str] = Depends(extract_optional_token_from_header),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
    user_repository: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """Get current user optionally (returns None if not authenticated).
    
    This dependency is useful for endpoints that work both with and without
    authentication, providing different functionality based on auth status.
    
    Args:
        token: JWT token from authorization header (optional)
        jwt_manager: JWT manager for token verification
        user_repository: User repository for database access
        
    Returns:
        Current authenticated user or None if not authenticated
    """
    if token is None:
        return None
    
    try:
        # Verify token and extract payload
        payload = jwt_manager.verify_token(token, expected_type=TokenType.ACCESS)
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
            
        # Get user from database
        user = await user_repository.get_by_id(user_id)
        return user
        
    except (InvalidTokenError, ExpiredTokenError, InvalidTokenTypeError, UserNotFoundError):
        # If any authentication error occurs, return None instead of raising
        return None


async def get_optional_current_active_user(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Optional[User]:
    """Get current active user optionally.
    
    Args:
        current_user: Current authenticated user (optional)
        
    Returns:
        Current active user or None if not authenticated or not active
    """
    if current_user is None:
        return None
    
    if current_user.status != "active":
        return None
    
    return current_user


async def require_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require current user to be an admin.
    
    Args:
        current_user: Current active authenticated user
        
    Returns:
        Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Check if user has admin privileges
    is_admin = getattr(current_user, 'is_admin', False)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def get_current_token(
    token: str = Depends(extract_token_from_header)
) -> str:
    """Get current JWT token for logout purposes.
    
    Args:
        token: JWT token from authorization header
        
    Returns:
        JWT token string
    """
    return token


# Convenience dependencies for common auth patterns
CurrentUser = Depends(get_current_user)
CurrentActiveUser = Depends(get_current_active_user)
OptionalCurrentUser = Depends(get_optional_current_user)
OptionalCurrentActiveUser = Depends(get_optional_current_active_user)
AdminUser = Depends(require_admin_user)
CurrentToken = Depends(get_current_token)