"""Enhanced unit tests for utility functions.

🎯 테스트 전략: 순수 함수 직접 테스트 (비용 효율적)
- Utils 계층: JWT, Password, Permission 실제 함수 호출
- Mock 사용 제거: 순수 함수는 직접 테스트 가능
- 실제 구현 검증: 비즈니스 로직 옵의 동작 보장
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.utils.jwt import JWTManager, TokenType
from src.utils.password import PasswordManager
from src.utils.permissions import PermissionChecker
from src.exceptions.auth import InvalidTokenError, ExpiredTokenError
from src.exceptions.post import PostPermissionError
from src.exceptions.comment import CommentPermissionError


class TestJWTManager:
    """Test JWT token management functionality."""
    
    @pytest.fixture
    def jwt_manager(self):
        """Create JWT manager instance.
        
        ✅ 실제 구현 사용: JWTManager 순수 함수 특성 활용
        🔄 Mock 제거 이유: 호출 비용 낮음, 실제 암호화 로직 검증 필요
        """
        return JWTManager(
            secret_key="test-secret-key-minimum-32-characters-required",
            algorithm="HS256"
        )
    
    def test_create_access_token_success(self, jwt_manager):
        """Test successful access token creation.
        
        🎯 테스트 전략: JWT 암호화 실제 동작 검증
        🔑 우선순위: 🔵 필수 (MVP) - 인증 핵심 기능
        🎓 난이도: 🟢 초급 - 순수 함수
        ⚡ 실행 그룹: 병렬 가능 - 상태 비저장
        """
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        
        # Act
        token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token_success(self, jwt_manager):
        """Test successful refresh token creation."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        
        # Act
        token = jwt_manager.create_token(payload, TokenType.REFRESH)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_success(self, jwt_manager):
        """Test successful token verification."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Act
        decoded_payload = jwt_manager.verify_token(token, TokenType.ACCESS)
        
        # Assert
        assert decoded_payload["sub"] == "user123"
        assert decoded_payload["email"] == "test@example.com"
    
    def test_verify_token_invalid(self, jwt_manager):
        """Test token verification with invalid token."""
        # Arrange
        invalid_token = "invalid.jwt.token"
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token(invalid_token, TokenType.ACCESS)
    
    def test_verify_token_expired(self, jwt_manager):
        """Test token verification with expired token.
        
        ✅ 실제 구현 검증: JWTManager 만료 처리 로직 직접 테스트
        """
        # Arrange - 실제로 만료된 토큰 생성
        payload = {"sub": "user123", "email": "test@example.com"}
        
        with patch.object(jwt_manager, 'access_token_expire_minutes', 0):
            token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Act & Assert - 실제 JWTManager의 만료 검증 로직 테스트
        with pytest.raises(ExpiredTokenError):
            jwt_manager.verify_token(token, TokenType.ACCESS)
    
    def test_verify_token_wrong_type(self, jwt_manager):
        """Test token verification with wrong token type."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        access_token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Act & Assert (trying to verify access token as refresh token)
        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token(access_token, TokenType.REFRESH)
    
    def test_get_token_claims_success(self, jwt_manager):
        """Test extracting token claims without verification."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com", "custom": "data"}
        token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Act
        claims = jwt_manager.get_token_claims(token)
        
        # Assert
        assert claims["sub"] == "user123"
        assert claims["email"] == "test@example.com"
        assert claims["custom"] == "data"
    
    def test_is_token_expired_false(self, jwt_manager):
        """Test checking if token is not expired."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Act
        is_expired = jwt_manager.is_token_expired(token)
        
        # Assert
        assert is_expired is False
    
    def test_is_token_expired_true(self, jwt_manager):
        """Test checking if token is expired."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        
        with patch.object(jwt_manager, 'access_token_expire_minutes', 0):
            token = jwt_manager.create_token(payload, TokenType.ACCESS)
        
        # Act
        is_expired = jwt_manager.is_token_expired(token)
        
        # Assert
        assert is_expired is True
    
    def test_refresh_access_token_success(self, jwt_manager):
        """Test successful access token refresh."""
        # Arrange
        payload = {"sub": "user123", "email": "test@example.com"}
        refresh_token = jwt_manager.create_token(payload, TokenType.REFRESH)
        
        # Act
        new_access_token = jwt_manager.refresh_access_token(refresh_token)
        
        # Assert
        assert new_access_token is not None
        decoded = jwt_manager.verify_token(new_access_token, TokenType.ACCESS)
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
    
    def test_refresh_access_token_invalid_refresh(self, jwt_manager):
        """Test access token refresh with invalid refresh token."""
        # Arrange
        invalid_refresh_token = "invalid.refresh.token"
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            jwt_manager.refresh_access_token(invalid_refresh_token)


class TestPasswordManager:
    """Test password management functionality."""
    
    @pytest.fixture
    def password_manager(self):
        """Create password manager instance.
        
        ✅ 실제 구현 사용: PasswordManager 순수 함수 특성 활용
        🔄 Mock 제거 이유: 비밀번호 해싱 알고리즘 실제 동작 검증 필요
        """
        return PasswordManager()
    
    def test_hash_password_success(self, password_manager):
        """Test successful password hashing.
        
        🎯 테스트 전략: 비밀번호 해싱 실제 동작 검증
        🔑 우선순위: 🔵 필수 (MVP) - 보안 핵심 기능
        🎓 난이도: 🟢 초급 - 순수 함수
        ⚡ 실행 그룹: 병렬 가능
        """
        # Arrange
        password = "testpassword123"
        
        # Act
        hashed = password_manager.hash_password(password)
        
        # Assert
        assert hashed is not None
        assert hashed != password  # Should be hashed, not plain text
        assert isinstance(hashed, str)
        assert len(hashed) > len(password)
    
    def test_verify_password_success(self, password_manager):
        """Test successful password verification."""
        # Arrange
        password = "testpassword123"
        hashed = password_manager.hash_password(password)
        
        # Act
        is_valid = password_manager.verify_password(password, hashed)
        
        # Assert
        assert is_valid is True
    
    def test_verify_password_failure(self, password_manager):
        """Test password verification failure."""
        # Arrange
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = password_manager.hash_password(password)
        
        # Act
        is_valid = password_manager.verify_password(wrong_password, hashed)
        
        # Assert
        assert is_valid is False
    
    def test_verify_password_empty(self, password_manager):
        """Test password verification with empty password."""
        # Arrange
        hashed = password_manager.hash_password("testpassword123")
        
        # Act
        is_valid = password_manager.verify_password("", hashed)
        
        # Assert
        assert is_valid is False
    
    def test_hash_password_empty(self, password_manager):
        """Test hashing empty password."""
        # Act & Assert
        with pytest.raises(ValueError):
            password_manager.hash_password("")
    
    def test_hash_password_consistency(self, password_manager):
        """Test that same password produces different hashes (salt)."""
        # Arrange
        password = "testpassword123"
        
        # Act
        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)
        
        # Assert
        assert hash1 != hash2  # Different salts should produce different hashes
        assert password_manager.verify_password(password, hash1)
        assert password_manager.verify_password(password, hash2)
    
    def test_generate_random_password(self, password_manager):
        """Test random password generation."""
        # Act
        random_password = password_manager.generate_random_password(length=12)
        
        # Assert
        assert len(random_password) == 12
        assert isinstance(random_password, str)
    
    def test_generate_random_password_default_length(self, password_manager):
        """Test random password generation with default length."""
        # Act
        random_password = password_manager.generate_random_password()
        
        # Assert
        assert len(random_password) == 16  # Default length
        assert isinstance(random_password, str)
    
    def test_check_password_strength_weak(self, password_manager):
        """Test password strength check for weak password."""
        # Arrange
        weak_passwords = ["123", "password", "abc123", "qwerty"]
        
        # Act & Assert
        for password in weak_passwords:
            strength = password_manager.check_password_strength(password)
            assert strength["score"] < 3  # Weak password
            assert strength["is_strong"] is False
    
    def test_check_password_strength_strong(self, password_manager):
        """Test password strength check for strong password."""
        # Arrange
        strong_passwords = [
            "MyStrongP@ssw0rd123",
            "C0mpl3x!P@ssw0rd#2024",
            "Str0ng&Secure!Pass123"
        ]
        
        # Act & Assert
        for password in strong_passwords:
            strength = password_manager.check_password_strength(password)
            assert strength["score"] >= 3  # Strong password
            assert strength["is_strong"] is True


class TestPermissionChecker:
    """Test permission checking functionality."""
    
    @pytest.fixture
    def permission_checker(self):
        """Create permission checker instance.
        
        ✅ 실제 구현 사용: PermissionChecker 비즈니스 로직 직접 테스트
        🔄 Mock 제거 이유: 권한 검사 로직 단순, 외부 의존성 없음
        """
        return PermissionChecker()
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = "user123"
        user.email = "test@example.com"
        user.user_handle = "testuser"
        user.is_admin = False
        user.status = "active"
        return user
    
    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = "admin123"
        user.email = "admin@example.com"
        user.user_handle = "adminuser"
        user.is_admin = True
        user.status = "active"
        return user
    
    @pytest.fixture
    def mock_post(self):
        """Create mock post."""
        post = MagicMock()
        post.id = "post123"
        post.title = "Test Post"
        post.author_id = "user123"
        post.status = "published"
        return post
    
    @pytest.fixture
    def mock_comment(self):
        """Create mock comment."""
        comment = MagicMock()
        comment.id = "comment123"
        comment.content = "Test comment"
        comment.author_id = "user123"
        comment.status = "active"
        return comment
    
    def test_check_post_permission_owner_success(self, permission_checker, mock_user, mock_post):
        """Test post permission check for post owner.
        
        🎯 테스트 전략: 권한 검사 비즈니스 로직 직접 검증
        🔑 우선순위: 🔵 필수 (MVP) - 보안 핵심 기능
        🎓 난이도: 🟡 중급 - 비즈니스 로직
        ⚡ 실행 그룹: 병렬 가능
        """
        # Act
        result = permission_checker.check_post_permission(mock_user, mock_post, "edit")
        
        # Assert
        assert result is True
    
    def test_check_post_permission_admin_success(self, permission_checker, mock_admin_user, mock_post):
        """Test post permission check for admin user."""
        # Arrange
        mock_post.author_id = "other_user"  # Different from admin user
        
        # Act
        result = permission_checker.check_post_permission(mock_admin_user, mock_post, "delete")
        
        # Assert
        assert result is True  # Admin can perform any action
    
    def test_check_post_permission_denied(self, permission_checker, mock_user, mock_post):
        """Test post permission check denial for non-owner."""
        # Arrange
        mock_post.author_id = "other_user"  # Different from user
        mock_user.is_admin = False
        
        # Act & Assert
        with pytest.raises(PostPermissionError):
            permission_checker.check_post_permission(mock_user, mock_post, "edit")
    
    def test_check_comment_permission_owner_success(self, permission_checker, mock_user, mock_comment):
        """Test comment permission check for comment owner."""
        # Act
        result = permission_checker.check_comment_permission(mock_user, mock_comment, "edit")
        
        # Assert
        assert result is True
    
    def test_check_comment_permission_admin_success(self, permission_checker, mock_admin_user, mock_comment):
        """Test comment permission check for admin user."""
        # Arrange
        mock_comment.author_id = "other_user"  # Different from admin user
        
        # Act
        result = permission_checker.check_comment_permission(mock_admin_user, mock_comment, "delete")
        
        # Assert
        assert result is True  # Admin can perform any action
    
    def test_check_comment_permission_denied(self, permission_checker, mock_user, mock_comment):
        """Test comment permission check denial for non-owner."""
        # Arrange
        mock_comment.author_id = "other_user"  # Different from user
        mock_user.is_admin = False
        
        # Act & Assert
        with pytest.raises(CommentPermissionError):
            permission_checker.check_comment_permission(mock_user, mock_comment, "edit")
    
    def test_check_user_permission_self_success(self, permission_checker, mock_user):
        """Test user permission check for self."""
        # Act
        result = permission_checker.check_user_permission(mock_user, mock_user.id, "edit_profile")
        
        # Assert
        assert result is True
    
    def test_check_user_permission_admin_success(self, permission_checker, mock_admin_user):
        """Test user permission check for admin."""
        # Act
        result = permission_checker.check_user_permission(mock_admin_user, "other_user", "suspend")
        
        # Assert
        assert result is True  # Admin can manage other users
    
    def test_check_user_permission_denied(self, permission_checker, mock_user):
        """Test user permission check denial."""
        # Act
        result = permission_checker.check_user_permission(mock_user, "other_user", "edit_profile")
        
        # Assert
        assert result is False  # User cannot edit other users' profiles
    
    def test_is_admin_true(self, permission_checker, mock_admin_user):
        """Test admin check for admin user."""
        # Act
        result = permission_checker.is_admin(mock_admin_user)
        
        # Assert
        assert result is True
    
    def test_is_admin_false(self, permission_checker, mock_user):
        """Test admin check for regular user."""
        # Act
        result = permission_checker.is_admin(mock_user)
        
        # Assert
        assert result is False
    
    def test_is_owner_true(self, permission_checker, mock_user):
        """Test ownership check for owner."""
        # Act
        result = permission_checker.is_owner(mock_user, mock_user.id)
        
        # Assert
        assert result is True
    
    def test_is_owner_false(self, permission_checker, mock_user):
        """Test ownership check for non-owner."""
        # Act
        result = permission_checker.is_owner(mock_user, "other_user")
        
        # Assert
        assert result is False
    
    def test_check_resource_access_public(self, permission_checker, mock_user):
        """Test resource access check for public resource."""
        # Arrange
        resource = {"visibility": "public", "author_id": "other_user"}
        
        # Act
        result = permission_checker.check_resource_access(mock_user, resource)
        
        # Assert
        assert result is True
    
    def test_check_resource_access_private_owner(self, permission_checker, mock_user):
        """Test resource access check for private resource by owner."""
        # Arrange
        resource = {"visibility": "private", "author_id": mock_user.id}
        
        # Act
        result = permission_checker.check_resource_access(mock_user, resource)
        
        # Assert
        assert result is True
    
    def test_check_resource_access_private_denied(self, permission_checker, mock_user):
        """Test resource access check for private resource by non-owner."""
        # Arrange
        resource = {"visibility": "private", "author_id": "other_user"}
        
        # Act
        result = permission_checker.check_resource_access(mock_user, resource)
        
        # Assert
        assert result is False
    
    def test_get_user_permissions_admin(self, permission_checker, mock_admin_user):
        """Test getting permissions for admin user."""
        # Act
        permissions = permission_checker.get_user_permissions(mock_admin_user)
        
        # Assert
        assert "admin" in permissions
        assert "create_post" in permissions
        assert "delete_any_post" in permissions
        assert "manage_users" in permissions
    
    def test_get_user_permissions_regular(self, permission_checker, mock_user):
        """Test getting permissions for regular user."""
        # Act
        permissions = permission_checker.get_user_permissions(mock_user)
        
        # Assert
        assert "admin" not in permissions
        assert "create_post" in permissions
        assert "edit_own_posts" in permissions
        assert "delete_any_post" not in permissions