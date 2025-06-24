import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from beanie.exceptions import RevisionIdWasChanged
from src.models.core import User, UserCreate, UserUpdate
from src.repositories.user_repository import UserRepository
from src.exceptions.user import UserNotFoundError, DuplicateUserError


@pytest.fixture
def user_repository():
    """Create UserRepository instance for testing."""
    return UserRepository()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "handle": "johndoe",
        "bio": "Software developer",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewAmz.b9oLtOYLiO"
    }


@pytest.fixture
def sample_user(sample_user_data):
    """Create a mock User instance."""
    mock_user = MagicMock()
    for key, value in sample_user_data.items():
        setattr(mock_user, key, value)
    mock_user.id = "507f1f77bcf86cd799439011"
    mock_user.status = "active"
    mock_user.created_at = datetime.utcnow()
    mock_user.updated_at = datetime.utcnow()
    mock_user.last_login = None
    
    # Mock async methods
    mock_user.insert = AsyncMock(return_value=mock_user)
    mock_user.save = AsyncMock(return_value=mock_user)
    mock_user.delete = AsyncMock()
    mock_user.model_copy = MagicMock(return_value=mock_user)
    
    return mock_user


class TestUserRepository:
    """Test UserRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, sample_user_data):
        """Test successful user creation."""
        user_create = UserCreate(
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            handle=sample_user_data["handle"],
            password="SecurePass123"
        )
        
        # Mock User class and instance
        mock_user_instance = MagicMock()
        mock_user_instance.email = user_create.email
        mock_user_instance.name = user_create.name
        mock_user_instance.handle = user_create.handle
        mock_user_instance.insert = AsyncMock(return_value=mock_user_instance)
        
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=None), \
             patch.object(User, '__new__', return_value=mock_user_instance):
            
            result = await user_repository.create(user_create, sample_user_data["password_hash"])
            
            assert result.email == user_create.email
            assert result.name == user_create.name
            assert result.handle == user_create.handle
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_repository, sample_user):
        """Test user creation with duplicate email."""
        user_create = UserCreate(
            name="Jane Doe",
            email=sample_user.email,  # Duplicate email
            handle="janedoe",
            password="SecurePass123"
        )
        
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=sample_user):
            with pytest.raises(DuplicateUserError, match="email"):
                await user_repository.create(user_create, "password_hash")
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_handle(self, user_repository, sample_user):
        """Test user creation with duplicate handle."""
        user_create = UserCreate(
            name="Jane Doe",
            email="jane@example.com",
            handle=sample_user.handle,  # Duplicate handle
            password="SecurePass123"
        )
        
        with patch.object(User, 'find_one', new_callable=AsyncMock, side_effect=[None, sample_user]):
            with pytest.raises(DuplicateUserError, match="handle"):
                await user_repository.create(user_create, "password_hash")
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository, sample_user):
        """Test successful user retrieval by ID."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch.object(User, 'get', new_callable=AsyncMock, return_value=sample_user):
            result = await user_repository.get_by_id(user_id)
            assert result == sample_user
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository):
        """Test user retrieval with non-existent ID."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch.object(User, 'get', new_callable=AsyncMock, return_value=None):
            with pytest.raises(UserNotFoundError):
                await user_repository.get_by_id(user_id)
    
    @pytest.mark.asyncio
    async def test_get_by_email_success(self, user_repository, sample_user):
        """Test successful user retrieval by email."""
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=sample_user):
            result = await user_repository.get_by_email(sample_user.email)
            assert result == sample_user
    
    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repository):
        """Test user retrieval with non-existent email."""
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=None):
            result = await user_repository.get_by_email("nonexistent@example.com")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_handle_success(self, user_repository, sample_user):
        """Test successful user retrieval by handle."""
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=sample_user):
            result = await user_repository.get_by_handle(sample_user.handle)
            assert result == sample_user
    
    @pytest.mark.asyncio
    async def test_get_by_handle_not_found(self, user_repository):
        """Test user retrieval with non-existent handle."""
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=None):
            result = await user_repository.get_by_handle("nonexistent")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, sample_user):
        """Test successful user update."""
        user_update = UserUpdate(
            name="John Updated",
            bio="Updated bio"
        )
        
        with patch.object(User, 'get', return_value=sample_user), \
             patch.object(sample_user, 'save', return_value=AsyncMock()) as mock_save:
            
            # Update the user data
            updated_user = sample_user.model_copy()
            updated_user.name = user_update.name
            updated_user.bio = user_update.bio
            updated_user.updated_at = datetime.utcnow()
            mock_save.return_value = updated_user
            
            result = await user_repository.update(sample_user.id, user_update)
            
            assert result.name == user_update.name
            assert result.bio == user_update.bio
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_repository):
        """Test user update with non-existent ID."""
        user_id = "507f1f77bcf86cd799439011"
        user_update = UserUpdate(name="John Updated")
        
        with patch.object(User, 'get', new_callable=AsyncMock, return_value=None):
            with pytest.raises(UserNotFoundError):
                await user_repository.update(user_id, user_update)
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, sample_user):
        """Test successful user deletion."""
        with patch.object(User, 'get', return_value=sample_user), \
             patch.object(sample_user, 'delete', return_value=AsyncMock()) as mock_delete:
            
            await user_repository.delete(sample_user.id)
            mock_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_repository):
        """Test user deletion with non-existent ID."""
        user_id = "507f1f77bcf86cd799439011"
        
        with patch.object(User, 'get', new_callable=AsyncMock, return_value=None):
            with pytest.raises(UserNotFoundError):
                await user_repository.delete(user_id)
    
    @pytest.mark.asyncio
    async def test_update_last_login(self, user_repository, sample_user):
        """Test updating user's last login timestamp."""
        with patch.object(User, 'get', return_value=sample_user), \
             patch.object(sample_user, 'save', return_value=AsyncMock()) as mock_save:
            
            # Mock the updated user
            updated_user = sample_user.model_copy()
            updated_user.last_login = datetime.utcnow()
            mock_save.return_value = updated_user
            
            result = await user_repository.update_last_login(sample_user.id)
            
            assert result.last_login is not None
            assert isinstance(result.last_login, datetime)
    
    @pytest.mark.asyncio
    async def test_list_users_pagination(self, user_repository):
        """Test user listing with pagination."""
        # Create mock users
        mock_users = []
        for i in range(5):
            mock_user = MagicMock()
            mock_user.name = f"User {i}"
            mock_user.email = f"user{i}@example.com"
            mock_user.password_hash = "hash"
            mock_users.append(mock_user)
        
        with patch.object(User, 'find') as mock_find:
            # Create a proper mock chain
            mock_query = MagicMock()
            mock_query.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=mock_users[:3])
            mock_query.count = AsyncMock(return_value=5)
            mock_find.return_value = mock_query
            
            result = await user_repository.list_users(page=1, page_size=3)
            
            assert len(result["users"]) == 3
            assert result["total"] == 5
            assert result["page"] == 1
            assert result["page_size"] == 3
    
    @pytest.mark.asyncio
    async def test_check_email_exists(self, user_repository, sample_user):
        """Test checking if email exists."""
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=sample_user):
            result = await user_repository.check_email_exists(sample_user.email)
            assert result is True
        
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=None):
            result = await user_repository.check_email_exists("nonexistent@example.com")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_handle_exists(self, user_repository, sample_user):
        """Test checking if handle exists."""
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=sample_user):
            result = await user_repository.check_handle_exists(sample_user.handle)
            assert result is True
        
        with patch.object(User, 'find_one', new_callable=AsyncMock, return_value=None):
            result = await user_repository.check_handle_exists("nonexistent")
            assert result is False