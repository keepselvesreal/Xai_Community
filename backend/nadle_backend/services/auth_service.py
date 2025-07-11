"""Authentication service layer for business logic."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from nadle_backend.models.core import User, UserCreate, UserUpdate
from nadle_backend.repositories.user_repository import UserRepository
from nadle_backend.utils.jwt import JWTManager, TokenType
from nadle_backend.utils.password import PasswordManager
from nadle_backend.exceptions.auth import InvalidCredentialsError
from nadle_backend.exceptions.user import (
    UserNotFoundError, 
    EmailAlreadyExistsError, 
    HandleAlreadyExistsError,
    UserNotActiveError,
    UserSuspendedError
)
from nadle_backend.services.email_service import EmailService
from nadle_backend.services.cache_service import get_cache_service
from nadle_backend.services.session_service import get_session_service, SessionData
from nadle_backend.services.token_blacklist_service import get_token_blacklist_service
from nadle_backend.config import get_settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for handling user authentication and management."""
    
    def __init__(
        self, 
        user_repository: UserRepository = None,
        jwt_manager: JWTManager = None,
        password_manager: PasswordManager = None,
        email_service: EmailService = None
    ):
        """Initialize auth service with dependencies.
        
        Args:
            user_repository: User repository instance
            jwt_manager: JWT manager instance  
            password_manager: Password manager instance
            email_service: Email service instance
        """
        self.user_repository = user_repository or UserRepository()
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager or PasswordManager()
        self.email_service = email_service or EmailService(self.user_repository)
        self.settings = get_settings()
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            EmailAlreadyExistsError: If email already exists
            HandleAlreadyExistsError: If handle already exists
        """
        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise EmailAlreadyExistsError(user_data.email)
        
        # Check if user_handle already exists
        existing_user = await self.user_repository.get_by_user_handle(user_data.user_handle)
        if existing_user:
            raise HandleAlreadyExistsError(user_data.user_handle)
        
        # Hash password
        password_hash = self.password_manager.hash_password(user_data.password)
        
        # Create user using repository
        user = await self.user_repository.create(user_data, password_hash)
        
        # Return user data without sensitive fields
        return {
            "id": str(user.id),
            "email": user.email,
            "user_handle": user.user_handle,
            "display_name": user.display_name,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authenticated user
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        try:
            user = await self.user_repository.get_by_email(email)
        except UserNotFoundError:
            raise InvalidCredentialsError()
        
        # Verify password
        if not user.password_hash:
            raise InvalidCredentialsError("Account requires password reset")
        if not self.password_manager.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        
        # Check user status
        if user.status != "active":
            raise InvalidCredentialsError("Account is not active")
        
        return user
    
    async def create_access_token(self, user: User) -> str:
        """Create access token for user.
        
        Args:
            user: User instance
            
        Returns:
            JWT access token
        """
        payload = {
            "sub": str(user.id),  # ObjectId를 문자열로 변환
            "email": user.email
        }
        return self.jwt_manager.create_token(payload, TokenType.ACCESS)
    
    async def create_refresh_token(self, user: User) -> str:
        """Create refresh token for user.
        
        Args:
            user: User instance
            
        Returns:
            JWT refresh token
        """
        payload = {
            "sub": str(user.id),  # ObjectId를 문자열로 변환
            "email": user.email
        }
        return self.jwt_manager.create_token(payload, TokenType.REFRESH)
    
    async def login(self, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Login user and return tokens with session management.
        
        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with user, access_token, refresh_token, token_type, and session_id
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        # Authenticate user
        user = await self.authenticate_user(email, password)
        
        # Update last login
        await self.user_repository.update_last_login(user.id)
        
        # Create tokens
        access_token = await self.create_access_token(user)
        refresh_token = await self.create_refresh_token(user)
        
        # Create session
        session_id = await self._create_user_session(
            user, access_token, refresh_token, ip_address, user_agent
        )
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "session_id": session_id
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access_token and token_type
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            UserNotFoundError: If user not found
        """
        # Verify refresh token
        payload = self.jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
        user_id = payload.get("sub")
        
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        
        # Create new access token
        access_token = await self.create_access_token(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    async def get_user_profile(self, user_id: str) -> User:
        """Get user profile by ID with caching.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # 캐시에서 사용자 정보 확인
        cache_service = await get_cache_service()
        cached_user = await cache_service.get_user_cache(user_id)
        
        if cached_user:
            # 캐시된 데이터를 User 객체로 변환
            return User(**cached_user)
        
        # 캐시에 없으면 DB에서 조회
        user = await self.user_repository.get_by_id(user_id)
        
        # 조회된 데이터를 캐시에 저장
        user_dict = user.model_dump()
        await cache_service.set_user_cache(user_id, user_dict)
        
        return user
    
    async def update_user_profile(self, user_id: str, user_update: UserUpdate) -> User:
        """Update user profile and invalidate cache.
        
        Args:
            user_id: User ID
            user_update: Updated user data
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update user
        updated_user = await self.user_repository.update(user_id, user_update)
        
        # 캐시 무효화
        cache_service = await get_cache_service()
        await cache_service.delete_user_cache(user_id)
        
        return updated_user
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> User:
        """Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
            InvalidCredentialsError: If old password is wrong
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Hash new password
        new_password_hash = self.password_manager.hash_password(new_password)
        
        # Update password
        return await self.user_repository.update_password(user_id, new_password_hash)
    
    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update status
        return await self.user_repository.update_status(user_id, "inactive")
    
    async def activate_user(self, user_id: str) -> User:
        """Activate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update status
        return await self.user_repository.update_status(user_id, "active")
    
    async def suspend_user(self, user_id: str) -> User:
        """Suspend user account (admin operation).
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user instance
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Update status
        return await self.user_repository.update_status(user_id, "suspended")
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account (admin operation).
        
        Args:
            user_id: User ID
            
        Returns:
            True if deletion successful
            
        Raises:
            UserNotFoundError: If user not found
        """
        # Check if user exists
        await self.user_repository.get_by_id(user_id)
        
        # Delete user
        await self.user_repository.delete(user_id)
        return True
    
    async def list_users(self) -> List[User]:
        """List all users (admin operation).
        
        Returns:
            List of all users
        """
        return await self.user_repository.list_all()
    
    async def check_email_exists(self, email: str) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        try:
            await self.user_repository.get_by_email(email)
            return True
        except UserNotFoundError:
            return False
    
    async def check_user_handle_exists(self, user_handle: str) -> bool:
        """Check if user_handle already exists.
        
        Args:
            user_handle: Handle to check
            
        Returns:
            True if user_handle exists, False otherwise
        """
        try:
            await self.user_repository.get_by_user_handle(user_handle)
            return True
        except UserNotFoundError:
            return False
    
    # Email verification methods
    async def send_verification_email(self, email: str) -> tuple[bool, str]:
        """Send email verification code.
        
        Args:
            email: Email address to send verification code
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return await self.email_service.send_verification_email(email)
    
    async def verify_email_code(self, email: str, code: str) -> tuple[bool, str]:
        """Verify email verification code.
        
        Args:
            email: Email address
            code: Verification code
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return await self.email_service.verify_email_code(email, code)
    
    async def resend_verification_email(self, email: str) -> tuple[bool, str]:
        """Resend email verification code.
        
        Args:
            email: Email address to resend verification code
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return await self.email_service.resend_verification_email(email)
    
    async def is_email_verified(self, email: str) -> bool:
        """Check if email is verified.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email is verified, False otherwise
        """
        return await self.email_service.is_email_verified(email)
    
    # Session and token management methods
    async def _create_user_session(
        self, 
        user: User, 
        access_token: str, 
        refresh_token: str, 
        ip_address: str = None, 
        user_agent: str = None
    ) -> Optional[str]:
        """Create user session with Redis storage."""
        try:
            session_service = await get_session_service()
            
            # 토큰 만료 시간 계산
            expires_at = datetime.now() + self.settings.refresh_token_expire
            
            # 세션 데이터 생성
            session_data = SessionData(
                user_id=str(user.id),
                email=user.email,
                access_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                expires_at=expires_at
            )
            
            # 세션 생성 (동시 로그인 제한 3개)
            session_id = await session_service.create_session(
                session_data, 
                max_concurrent_sessions=3
            )
            
            if session_id:
                logger.info(f"세션 생성 성공: {user.email} ({session_id})")
            else:
                logger.warning(f"세션 생성 실패: {user.email}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"세션 생성 오류: {e}")
            return None
    
    async def logout(self, access_token: str, refresh_token: str = None, user_id: str = None) -> Dict[str, Any]:
        """Logout user and invalidate tokens.
        
        Args:
            access_token: User's access token
            refresh_token: User's refresh token (optional)
            user_id: User ID (optional, for session cleanup)
            
        Returns:
            Dictionary with logout status and message
        """
        try:
            blacklist_service = await get_token_blacklist_service()
            session_service = await get_session_service()
            
            # 토큰 만료 시간 계산
            access_expires_at = datetime.now() + self.settings.access_token_expire
            refresh_expires_at = datetime.now() + self.settings.refresh_token_expire
            
            # Access token 블랙리스트 추가
            await blacklist_service.blacklist_token(
                access_token, 
                access_expires_at, 
                "user_logout", 
                user_id
            )
            
            # Refresh token 블랙리스트 추가 (있는 경우)
            if refresh_token:
                await blacklist_service.blacklist_token(
                    refresh_token, 
                    refresh_expires_at, 
                    "user_logout", 
                    user_id
                )
            
            # 사용자 세션 삭제 (있는 경우)
            if user_id:
                deleted_sessions = await session_service.delete_user_sessions(user_id)
                logger.info(f"사용자 세션 삭제: {user_id}, 삭제된 세션 수: {deleted_sessions}")
            
            # 사용자 캐시 무효화
            if user_id:
                cache_service = await get_cache_service()
                await cache_service.delete_user_cache(user_id)
            
            logger.info(f"로그아웃 성공: 사용자 {user_id}")
            
            return {
                "status": "success",
                "message": "Successfully logged out",
                "tokens_invalidated": True,
                "sessions_cleared": True
            }
            
        except Exception as e:
            logger.error(f"로그아웃 오류: {e}")
            return {
                "status": "partial",
                "message": "Logout completed with some errors",
                "error": str(e)
            }
    
    async def logout_all_sessions(self, user_id: str) -> Dict[str, Any]:
        """Logout user from all sessions and devices.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with logout status and statistics
        """
        try:
            blacklist_service = await get_token_blacklist_service()
            session_service = await get_session_service()
            cache_service = await get_cache_service()
            
            # 사용자의 모든 토큰 블랙리스트 추가
            expires_at = datetime.now() + self.settings.refresh_token_expire
            blacklisted_count = await blacklist_service.blacklist_user_tokens(
                user_id, 
                expires_at, 
                "logout_all_sessions"
            )
            
            # 모든 세션 삭제
            deleted_sessions = await session_service.delete_user_sessions(user_id)
            
            # 사용자 캐시 무효화
            await cache_service.delete_user_cache(user_id)
            
            logger.info(f"전체 로그아웃 성공: {user_id}, 세션: {deleted_sessions}, 블랙리스트: {blacklisted_count}")
            
            return {
                "status": "success",
                "message": "Successfully logged out from all sessions",
                "deleted_sessions": deleted_sessions,
                "blacklisted_tokens": blacklisted_count
            }
            
        except Exception as e:
            logger.error(f"전체 로그아웃 오류: {e}")
            return {
                "status": "error",
                "message": "Failed to logout from all sessions",
                "error": str(e)
            }
    
    async def verify_token_validity(self, token: str) -> bool:
        """Verify if token is valid and not blacklisted.
        
        Args:
            token: JWT token to verify
            
        Returns:
            True if token is valid and not blacklisted
        """
        try:
            # JWT 토큰 검증
            payload = self.jwt_manager.verify_token(token, TokenType.ACCESS)
            
            # 블랙리스트 확인
            blacklist_service = await get_token_blacklist_service()
            is_blacklisted = await blacklist_service.is_blacklisted(token)
            
            if is_blacklisted:
                logger.debug(f"토큰이 블랙리스트에 있음: {token[:20]}...")
                return False
            
            # 사용자 전체 블랙리스트 확인
            user_id = payload.get("sub")
            if user_id:
                is_user_blacklisted = await blacklist_service.is_user_blacklisted(user_id)
                if is_user_blacklisted:
                    logger.debug(f"사용자 전체 블랙리스트: {user_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"토큰 검증 실패: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active sessions.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active session information
        """
        try:
            session_service = await get_session_service()
            sessions = await session_service.get_user_sessions(user_id)
            return sessions
            
        except Exception as e:
            logger.error(f"사용자 세션 조회 오류: {e}")
            return []
    
    # === 보안 쿠키 기반 인증 메서드 ===
    
    async def login_with_secure_cookies(
        self, 
        response, 
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """보안 쿠키를 사용한 로그인 응답 생성
        
        Args:
            response: FastAPI Response 객체
            user_data: 사용자 데이터
            
        Returns:
            로그인 응답 (토큰은 쿠키에만 저장)
        """
        try:
            from nadle_backend.utils.token_security import create_secure_token_response, CSRFProtectionManager
            
            # 사용자 객체 가져오기
            if isinstance(user_data, dict):
                user_id = user_data.get("user_id") or user_data.get("id")
            else:
                user_id = str(user_data.id)
            
            user = await self.user_repository.get_by_id(user_id)
            
            # 토큰 생성
            access_token = await self.create_access_token(user)
            refresh_token = await self.create_refresh_token(user)
            
            # CSRF 토큰 생성 (세션 기반)
            csrf_manager = CSRFProtectionManager()
            session_id = f"session_{user.id}_{datetime.now().timestamp()}"
            csrf_token = csrf_manager.generate_csrf_token(session_id)
            
            # 보안 쿠키 응답 생성
            token_response = create_secure_token_response(
                response=response,
                access_token=access_token,
                refresh_token=refresh_token,
                csrf_token=csrf_token
            )
            
            # 사용자 정보와 함께 반환 (토큰은 제외)
            return {
                **token_response,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "user_handle": user.user_handle,
                    "display_name": user.display_name,
                    "role": user.role
                }
            }
            
        except Exception as e:
            logger.error(f"보안 쿠키 로그인 실패: {e}")
            raise
    
    async def verify_token_from_cookie(self, request) -> Optional[Dict[str, Any]]:
        """쿠키에서 토큰을 추출하여 검증
        
        Args:
            request: FastAPI Request 객체
            
        Returns:
            검증된 사용자 데이터 또는 None
        """
        try:
            from nadle_backend.utils.token_security import SecureTokenManager
            
            token_manager = SecureTokenManager()
            token = token_manager.extract_token_from_cookie(request)
            
            if not token:
                return None
            
            # 토큰 유효성 검증
            if not await self.verify_token_validity(token):
                return None
            
            # 토큰에서 사용자 정보 추출
            payload = self.jwt_manager.verify_token(token, TokenType.ACCESS)
            user_id = payload.get("sub")
            
            if not user_id:
                return None
            
            # 사용자 정보 조회
            user = await self.get_user_profile(user_id)
            
            return {
                "user_id": str(user.id),
                "email": user.email,
                "user_handle": user.user_handle,
                "role": user.role
            }
            
        except Exception as e:
            logger.debug(f"쿠키 토큰 검증 실패: {e}")
            return None
    
    async def verify_csrf_token(self, request) -> bool:
        """CSRF 토큰 검증
        
        Args:
            request: FastAPI Request 객체
            
        Returns:
            CSRF 토큰이 유효한지 여부
        """
        try:
            from nadle_backend.utils.token_security import CSRFProtectionManager
            
            # CSRF 토큰 추출 (헤더 또는 폼 데이터에서)
            csrf_token = request.headers.get("X-CSRF-Token")
            if not csrf_token:
                # 폼 데이터에서 확인
                if hasattr(request, 'form'):
                    form_data = await request.form()
                    csrf_token = form_data.get("csrf_token")
            
            if not csrf_token:
                return False
            
            # 세션 ID 추출 (쿠키 토큰에서)
            user_data = await self.verify_token_from_cookie(request)
            if not user_data:
                return False
            
            session_id = f"session_{user_data['user_id']}"
            
            # CSRF 토큰 검증
            csrf_manager = CSRFProtectionManager()
            return csrf_manager.verify_csrf_token(csrf_token, session_id)
            
        except Exception as e:
            logger.debug(f"CSRF 토큰 검증 실패: {e}")
            return False
    
    async def logout_with_secure_cookies(self, request, response) -> Dict[str, Any]:
        """보안 쿠키를 사용한 로그아웃
        
        Args:
            request: FastAPI Request 객체
            response: FastAPI Response 객체
            
        Returns:
            로그아웃 결과
        """
        try:
            from nadle_backend.utils.token_security import SecureTokenManager
            
            token_manager = SecureTokenManager()
            
            # 현재 토큰들 추출
            access_token = token_manager.extract_token_from_cookie(request, "access_token")
            refresh_token = token_manager.extract_token_from_cookie(request, "refresh_token")
            
            # 토큰들을 블랙리스트에 추가
            if access_token:
                blacklist_service = await get_token_blacklist_service()
                await blacklist_service.add_to_blacklist(access_token, "access_token_logout")
            
            if refresh_token:
                blacklist_service = await get_token_blacklist_service()
                await blacklist_service.add_to_blacklist(refresh_token, "refresh_token_logout")
            
            # 쿠키 삭제
            token_manager.clear_secure_cookie(response, "access_token")
            token_manager.clear_secure_cookie(response, "refresh_token")
            token_manager.clear_secure_cookie(response, "csrf_token")
            
            return {
                "message": "로그아웃 성공",
                "authentication": "cookies_cleared"
            }
            
        except Exception as e:
            logger.error(f"보안 쿠키 로그아웃 실패: {e}")
            return {
                "message": "로그아웃 중 오류 발생",
                "error": str(e)
            }
    
    async def refresh_token_with_secure_cookies(self, request, response) -> Dict[str, Any]:
        """보안 쿠키를 사용한 토큰 갱신
        
        Args:
            request: FastAPI Request 객체
            response: FastAPI Response 객체
            
        Returns:
            토큰 갱신 결과
        """
        try:
            from nadle_backend.utils.token_security import SecureTokenManager
            
            token_manager = SecureTokenManager()
            
            # Refresh Token 추출
            refresh_token = token_manager.extract_token_from_cookie(request, "refresh_token")
            if not refresh_token:
                raise InvalidCredentialsError("Refresh token not found")
            
            # 기존 Access Token 추출 (블랙리스트 추가용)
            old_access_token = token_manager.extract_token_from_cookie(request, "access_token")
            
            # 토큰 갱신
            token_data = await self.refresh_access_token(refresh_token)
            new_access_token = token_data["access_token"]
            
            # 토큰 로테이션
            if old_access_token:
                token_manager.rotate_token(
                    response=response,
                    old_token=old_access_token,
                    new_token=new_access_token,
                    cookie_name="access_token"
                )
            else:
                token_manager.set_secure_cookie(
                    response=response,
                    token=new_access_token,
                    cookie_name="access_token"
                )
            
            return {
                "message": "토큰 갱신 성공",
                "authentication": "secure_cookies"
            }
            
        except Exception as e:
            logger.error(f"보안 쿠키 토큰 갱신 실패: {e}")
            raise