import pytest
from datetime import datetime
from pydantic import ValidationError
from nadle_backend.models.core import UserBase, UserCreate, UserResponse, UserStatus


class TestUserBaseModel:
    """Test UserBase model validation and functionality."""
    
    def test_user_base_creation(self):
        """Test creating a valid UserBase model."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "handle": "johndoe",
            "bio": "Software developer"
        }
        
        user = UserBase(**user_data)
        
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.handle == "johndoe"
        assert user.bio == "Software developer"
    
    def test_user_base_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            UserBase()  # Missing required fields
        
        with pytest.raises(ValidationError):
            UserBase(email="invalid-email")  # Invalid email format
    
    def test_user_handle_validation(self):
        """Test handle validation rules."""
        base_data = {
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        # Valid handles
        valid_handles = ["johndoe", "john_doe", "user123", "test_user_123"]
        for handle in valid_handles:
            user = UserBase(**base_data, handle=handle)
            assert user.handle == handle.lower()
        
        # Invalid handles
        invalid_handles = ["john-doe", "john.doe", "john doe", "john@doe"]
        for handle in invalid_handles:
            with pytest.raises(ValidationError):
                UserBase(**base_data, handle=handle)
    
    def test_user_handle_case_normalization(self):
        """Test that handles are normalized to lowercase."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "handle": "JohnDoe"
        }
        
        user = UserBase(**user_data)
        assert user.handle == "johndoe"
    
    def test_user_handle_optional(self):
        """Test that handle is optional."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        user = UserBase(**user_data)
        assert user.handle is None


class TestUserCreateModel:
    """Test UserCreate request model."""
    
    def test_user_create_valid(self):
        """Test creating a valid UserCreate model."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "handle": "johndoe",
            "password": "SecurePass123"
        }
        
        user_create = UserCreate(**user_data)
        assert user_create.name == "John Doe"
        assert user_create.email == "john@example.com"
        assert user_create.handle == "johndoe"
        assert user_create.password == "SecurePass123"
    
    def test_user_create_password_validation(self):
        """Test password validation rules."""
        base_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "handle": "johndoe"
        }
        
        # Valid passwords
        valid_passwords = [
            "SecurePass123",
            "MyP@ssw0rd",
            "Complex123Pass"
        ]
        for password in valid_passwords:
            user_create = UserCreate(**base_data, password=password)
            assert user_create.password == password
        
        # Invalid passwords
        invalid_passwords = [
            "short",  # too short
            "nouppercase123",  # no uppercase
            "NOLOWERCASE123",  # no lowercase
            "NoNumbers",  # no digits
            "1234567"  # too short and no letters
        ]
        for password in invalid_passwords:
            with pytest.raises(ValidationError):
                UserCreate(**base_data, password=password)
    
    def test_user_create_optional_fields(self):
        """Test optional fields in UserCreate."""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123"
        }
        
        user_create = UserCreate(**user_data)
        assert user_create.handle is None
        assert user_create.bio is None
        assert user_create.avatar_url is None


class TestUserResponseModel:
    """Test UserResponse model."""
    
    def test_user_response_creation(self):
        """Test creating UserResponse from User data."""
        user_data = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "John Doe",
            "email": "john@example.com",
            "handle": "johndoe",
            "bio": "Software developer",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user_response = UserResponse(**user_data)
        assert user_response.id == "507f1f77bcf86cd799439011"
        assert user_response.name == "John Doe"
        assert user_response.email == "john@example.com"
        assert user_response.handle == "johndoe"
        assert user_response.status == "active"
    
    def test_user_response_excludes_password(self):
        """Test that UserResponse doesn't include password fields."""
        # UserResponse should not have password_hash field
        user_response_fields = UserResponse.model_fields.keys()
        assert "password_hash" not in user_response_fields
        assert "password" not in user_response_fields