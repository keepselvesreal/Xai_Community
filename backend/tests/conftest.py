import pytest
import asyncio
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import sys

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
    from src.config import settings
    
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
    
    return test_db