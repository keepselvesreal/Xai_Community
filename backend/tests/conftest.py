import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import os
import sys
from io import BytesIO

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Provide a test database connection.
    Uses the actual MongoDB Atlas connection from environment variables.
    """
    from nadle_backend.config import settings
    
    # Use test database name
    test_db_name = f"{settings.database_name}_test"
    
    # Create test client
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[test_db_name]
    
    # Ensure connection is established
    await client.admin.command("ping")
    
    yield db
    
    # Cleanup: Drop all collections in test database after tests
    collections = await db.list_collection_names()
    for collection_name in collections:
        await db[collection_name].drop()
    
    # Close connection
    client.close()


@pytest.fixture
async def clean_db(test_db: AsyncIOMotorDatabase) -> AsyncIOMotorDatabase:
    """
    Provide a clean test database by dropping all collections before the test.
    """
    # Drop all collections before test
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].drop()
    
    # Initialize Beanie models for testing
    from nadle_backend.models.core import User, Post, Comment, PostStats, UserReaction, Stats, FileRecord
    import beanie
    
    await beanie.init_beanie(
        database=test_db,
        document_models=[User, Post, Comment, PostStats, UserReaction, Stats, FileRecord]
    )
    
    return test_db


@pytest.fixture
def client():
    """Provide a test client for API testing."""
    from main import app
    
    with TestClient(app) as tc:
        yield tc


@pytest.fixture
async def test_user(clean_db: AsyncIOMotorDatabase):
    """Create a test user."""
    from nadle_backend.models.core import User
    from nadle_backend.utils.password import PasswordManager
    
    password_manager = PasswordManager()
    
    user_data = {
        "email": "test@example.com",
        "user_handle": "testuser",
        "password_hash": password_manager.hash_password("testpass123"),
        "is_admin": False
    }
    
    user = User(**user_data)
    await user.insert()
    
    return user

@pytest.fixture
async def test_user_dict(clean_db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Create a test user and return dict for legacy compatibility."""
    from nadle_backend.models.core import User
    from nadle_backend.utils.password import PasswordManager
    
    password_manager = PasswordManager()
    
    user_data = {
        "email": "test@example.com",
        "user_handle": "testuser",
        "password_hash": password_manager.hash_password("testpass123"),
        "is_admin": False
    }
    
    user = User(**user_data)
    await user.insert()
    
    return {
        "id": str(user.id),
        "email": user.email,
        "user_handle": user.user_handle,
        "password": "testpass123"  # Plain password for login tests
    }


@pytest.fixture
async def admin_user(clean_db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """Create a test admin user."""
    from nadle_backend.models.core import User
    from nadle_backend.utils.password import PasswordManager
    
    password_manager = PasswordManager()
    
    user_data = {
        "email": "admin@example.com",
        "user_handle": "adminuser",
        "password_hash": password_manager.hash_password("adminpass123"),
        "is_admin": True
    }
    
    user = User(**user_data)
    await user.insert()
    
    return {
        "id": str(user.id),
        "email": user.email,
        "user_handle": user.user_handle,
        "password": "adminpass123"
    }


@pytest.fixture
def authenticated_client(client: TestClient, test_user: Dict[str, Any]) -> TestClient:
    """Provide an authenticated test client."""
    # Login to get token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client


@pytest.fixture
def admin_client(client: TestClient, admin_user: Dict[str, Any]) -> TestClient:
    """Provide an authenticated admin client."""
    # Login to get token
    login_data = {
        "username": admin_user["email"],
        "password": admin_user["password"]
    }
    
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client


@pytest.fixture
def test_post(authenticated_client: TestClient, test_user: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test post."""
    post_data = {
        "title": "Test Post",
        "content": "This is a test post content.",
        "service_type": "general"
    }
    
    response = authenticated_client.post("/api/posts", json=post_data)
    assert response.status_code == 201
    
    return response.json()


@pytest.fixture
def test_comment(authenticated_client: TestClient, test_post: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test comment."""
    comment_data = {
        "content": "This is a test comment."
    }
    
    response = authenticated_client.post(
        f"/api/posts/{test_post['slug']}/comments", 
        json=comment_data
    )
    assert response.status_code == 201
    
    comment = response.json()
    comment["post_slug"] = test_post["slug"]
    return comment


def create_test_image(format="JPEG", size=(100, 100)):
    """Create a test image file."""
    try:
        from PIL import Image
        
        image = Image.new("RGB", size, color="red")
        img_bytes = BytesIO()
        image.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes
    except ImportError:
        # Fallback if PIL is not available
        return BytesIO(b"fake_image_data")


@pytest.fixture
def test_image():
    """Provide a test image file."""
    return create_test_image()


@pytest.fixture
def large_test_image():
    """Provide a large test image file (for size limit testing)."""
    return create_test_image(size=(2000, 2000))


@pytest.fixture
async def async_client(clean_db: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for API testing."""
    from main import app
    import httpx
    
    # Create a proper async transport for the FastAPI app
    transport = httpx.ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def test_post(clean_db: AsyncIOMotorDatabase, test_user):
    """Create a test post."""
    from nadle_backend.models.core import Post, PostCreate
    from nadle_backend.services.posts_service import PostsService
    
    posts_service = PostsService()
    
    post_data = PostCreate(
        title="Test Post for Detail Page",
        content="This is a test post content for detail page testing.",
        service="residential_community",
        metadata={
            "type": "자유게시판",
            "category": "생활정보",
            "tags": ["테스트", "상세페이지"]
        }
    )
    
    post = await posts_service.create_post(post_data, test_user)
    return post


@pytest.fixture
async def auth_headers(test_user_dict: Dict[str, Any]) -> Dict[str, str]:
    """Provide authentication headers for API testing."""
    from nadle_backend.utils.jwt import JWTManager
    from nadle_backend.config import settings
    
    jwt_manager = JWTManager(settings.secret_key)
    
    token_data = {
        "sub": test_user_dict["id"],
        "email": test_user_dict["email"]
    }
    
    access_token = jwt_manager.create_access_token(token_data)
    
    return {"Authorization": f"Bearer {access_token}"}