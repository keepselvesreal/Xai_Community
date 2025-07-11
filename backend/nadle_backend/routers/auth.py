"""Authentication router for FastAPI endpoints."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from nadle_backend.models.core import User, UserCreate, UserUpdate, UserResponse
from nadle_backend.models.email_verification import (
    EmailVerificationCreate,
    EmailVerificationResponse,
    EmailVerificationCodeRequest,
    EmailVerificationCodeResponse
)
from nadle_backend.services.auth_service import AuthService
from nadle_backend.services.email_verification_service import EmailVerificationService
from nadle_backend.repositories.email_verification_repository import EmailVerificationRepository
from nadle_backend.dependencies.auth import (
    CurrentActiveUser, 
    AdminUser,
    CurrentToken,
    get_jwt_manager,
    get_password_manager,
    get_user_repository,
    get_current_token
)
from nadle_backend.exceptions.auth import InvalidCredentialsError, InvalidTokenError, ExpiredTokenError
from nadle_backend.exceptions.user import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    HandleAlreadyExistsError
)


# Create router
router = APIRouter(
    tags=["authentication"],
    responses={404: {"description": "Not found"}}
)


# Request/Response Models
class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response model."""
    access_token: str
    token_type: str


class EmailVerificationRequest(BaseModel):
    """Email verification request model."""
    email: EmailStr


class EmailVerificationCodeRequest(BaseModel):
    """Email verification code request model."""
    email: EmailStr
    code: str


class EmailVerificationResponse(BaseModel):
    """Email verification response model."""
    success: bool
    message: str


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    """Generic message response model."""
    message: str


class UserListResponse(BaseModel):
    """User list response model."""
    users: List[UserResponse]
    total: int


# Dependency to get auth service
def get_auth_service(
    user_repository=Depends(get_user_repository),
    jwt_manager=Depends(get_jwt_manager),
    password_manager=Depends(get_password_manager)
) -> AuthService:
    """Get auth service dependency."""
    return AuthService(user_repository, jwt_manager, password_manager)


@router.post("/register", 
             response_model=Dict[str, Any], 
             status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user.
    
    Args:
        user_data: User registration data
        auth_service: Authentication service
        
    Returns:
        Dictionary with success message and user data
        
    Raises:
        HTTPException: If email or handle already exists
    """
    try:
        user = await auth_service.register_user(user_data)
        return {
            "message": "User registered successfully",
            "user": user
        }
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HandleAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return tokens.
    
    Args:
        form_data: OAuth2 form data (username=email, password)
        auth_service: Authentication service
        
    Returns:
        Login response with tokens and user data
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        login_result = await auth_service.login(form_data.username, form_data.password)
        
        # 사용자 정보에서 ObjectId를 문자열로 변환
        user_data = login_result["user"].model_dump()
        user_data["id"] = str(user_data["id"])  # ObjectId를 문자열로 변환
        
        return LoginResponse(
            access_token=login_result["access_token"],
            refresh_token=login_result["refresh_token"],
            token_type=login_result["token_type"],
            user=UserResponse(**user_data)
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        auth_service: Authentication service
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        result = await auth_service.refresh_access_token(refresh_data.refresh_token)
        
        return RefreshTokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
    except (InvalidTokenError, ExpiredTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user profile.
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        User profile data
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user = await auth_service.get_user_profile(current_user.id)
        user_data = user.model_dump()
        user_data["id"] = str(user_data["id"])  # ObjectId를 문자열로 변환
        return UserResponse(**user_data)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update current user profile.
    
    Args:
        user_update: Updated user data
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        Updated user profile data
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user = await auth_service.update_user_profile(current_user.id, user_update)
        user_data = user.model_dump()
        user_data["id"] = str(user_data["id"])  # ObjectId를 문자열로 변환
        return UserResponse(**user_data)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is wrong or user not found
    """
    try:
        await auth_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        return MessageResponse(message="Password changed successfully")
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/deactivate", response_model=MessageResponse)
async def deactivate_account(
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Deactivate current user account.
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        await auth_service.deactivate_user(current_user.id)
        return MessageResponse(message="Account deactivated successfully")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Email verification endpoints (old version - using auth service)
# @router.post("/send-verification-email", response_model=EmailVerificationResponse)
# async def send_verification_email_old(
#     request: EmailVerificationRequest,
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     """Send email verification code.
#     
#     Args:
#         request: Email verification request
#         auth_service: Authentication service
#         
#     Returns:
#         Success status and message
#         
#     Raises:
#         HTTPException: If email sending fails
#     """
#     try:
#         success, message = await auth_service.send_verification_email(request.email)
#         return EmailVerificationResponse(success=success, message=message)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to send verification email: {str(e)}"
#         )


# @router.post("/verify-email", response_model=EmailVerificationResponse)
# async def verify_email_old(
#     request: EmailVerificationCodeRequest,
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     """Verify email with verification code.
#     
#     Args:
#         request: Email verification code request
#         auth_service: Authentication service
#         
#     Returns:
#         Success status and message
#         
#     Raises:
#         HTTPException: If verification fails
#     """
#     try:
#         success, message = await auth_service.verify_email_code(request.email, request.code)
#         return EmailVerificationResponse(success=success, message=message)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to verify email: {str(e)}"
#         )


# @router.post("/resend-verification-email", response_model=EmailVerificationResponse)
# async def resend_verification_email_old(
#     request: EmailVerificationRequest,
#     auth_service: AuthService = Depends(get_auth_service)
# ):
#     """Resend email verification code.
#     
#     Args:
#         request: Email verification request
#         auth_service: Authentication service
#         
#     Returns:
#         Success status and message
#         
#     Raises:
#         HTTPException: If email sending fails
#     """
#     try:
#         success, message = await auth_service.resend_verification_email(request.email)
#         return EmailVerificationResponse(success=success, message=message)
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to resend verification email: {str(e)}"
#         )


# Admin endpoints
@router.get("/admin/users", response_model=UserListResponse)
async def list_users(
    admin_user: User = AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """List all users (admin only).
    
    Args:
        admin_user: Current admin user
        auth_service: Authentication service
        
    Returns:
        List of all users
    """
    users = await auth_service.list_users()
    user_responses = [UserResponse(**user.model_dump()) for user in users]
    
    return UserListResponse(
        users=user_responses,
        total=len(user_responses)
    )


@router.post("/admin/users/{user_id}/suspend", response_model=MessageResponse)
async def suspend_user(
    user_id: str,
    admin_user: User = AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Suspend user account (admin only).
    
    Args:
        user_id: ID of user to suspend
        admin_user: Current admin user
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        await auth_service.suspend_user(user_id)
        return MessageResponse(message="User suspended successfully")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/admin/users/{user_id}/activate", response_model=MessageResponse)
async def activate_user(
    user_id: str,
    admin_user: User = AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Activate user account (admin only).
    
    Args:
        user_id: ID of user to activate
        admin_user: Current admin user
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        await auth_service.activate_user(user_id)
        return MessageResponse(message="User activated successfully")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/admin/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    admin_user: User = AdminUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Delete user account (admin only).
    
    Args:
        user_id: ID of user to delete
        admin_user: Current admin user
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        await auth_service.delete_user(user_id)
        return MessageResponse(message="User deleted successfully")
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Logout endpoints
class LogoutRequest(BaseModel):
    """Logout request model."""
    refresh_token: str = None


class LogoutResponse(BaseModel):
    """Logout response model."""
    status: str
    message: str
    tokens_invalidated: bool = False
    sessions_cleared: bool = False


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    logout_request: LogoutRequest,
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service),
    access_token: str = CurrentToken
):
    """
    Logout user and invalidate tokens.
    
    Args:
        logout_request: Logout request with optional refresh token
        current_user: Currently authenticated user
        auth_service: Auth service instance
        access_token: Current access token
        
    Returns:
        Logout confirmation with status
    """
    try:
        result = await auth_service.logout(
            access_token=access_token,
            refresh_token=logout_request.refresh_token,
            user_id=str(current_user.id)
        )
        
        return LogoutResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/logout/all", response_model=Dict[str, Any])
async def logout_all_sessions(
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user from all sessions and devices.
    
    Args:
        current_user: Currently authenticated user
        auth_service: Auth service instance
        
    Returns:
        Logout confirmation with statistics
    """
    try:
        result = await auth_service.logout_all_sessions(str(current_user.id))
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout all sessions failed: {str(e)}"
        )


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_user_sessions(
    current_user: User = CurrentActiveUser,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user's active sessions.
    
    Args:
        current_user: Currently authenticated user
        auth_service: Auth service instance
        
    Returns:
        List of active session information
    """
    try:
        sessions = await auth_service.get_user_sessions(str(current_user.id))
        return sessions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


# Dependency injection functions
async def get_email_verification_repository() -> EmailVerificationRepository:
    """Get email verification repository instance."""
    return EmailVerificationRepository()


async def get_email_verification_service(
    repository: EmailVerificationRepository = Depends(get_email_verification_repository)
) -> EmailVerificationService:
    """Get email verification service instance."""
    return EmailVerificationService(repository=repository)


# Email verification endpoints
@router.post("/send-verification-email", response_model=EmailVerificationResponse)
async def send_verification_email(
    request: EmailVerificationCreate,
    service: EmailVerificationService = Depends(get_email_verification_service)
):
    """Send verification email for signup process."""
    try:
        result = await service.send_verification_email(request)
        
        if not result.code_sent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": result.message,
                    "email": result.email,
                    "can_resend": result.can_resend
                }
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {str(e)}"
        )


@router.post("/verify-email-code", response_model=EmailVerificationCodeResponse)
async def verify_email_code(
    request: EmailVerificationCodeRequest,
    service: EmailVerificationService = Depends(get_email_verification_service)
):
    """Verify email verification code."""
    try:
        result = await service.verify_email_code(request)
        
        if not result.verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": result.message,
                    "email": result.email,
                    "can_proceed": result.can_proceed
                }
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify email code: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for auth service."""
    return {"status": "healthy", "service": "authentication"}