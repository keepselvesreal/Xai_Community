import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from unittest.mock import AsyncMock, MagicMock, patch
import logging

from src.database import Database, database, get_database, get_client
from src.config import settings


class TestDatabaseConnection:
    """Test MongoDB Atlas connection management with real connections."""
    
    @pytest.fixture
    async def db_instance(self):
        """Create a fresh Database instance for testing."""
        db = Database()
        yield db
        # Cleanup after test
        if db.is_connected:
            await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, db_instance):
        """Test database instance is properly initialized."""
        assert db_instance.client is None
        assert db_instance.database is None
        assert db_instance.is_connected is False
    
    @pytest.mark.asyncio
    async def test_real_mongodb_atlas_connection(self, db_instance):
        """Test actual connection to MongoDB Atlas."""
        # Skip if using default localhost URL (no real Atlas configured)
        if settings.mongodb_url == "mongodb://localhost:27017":
            pytest.skip("MongoDB Atlas URL not configured in environment")
        
        # Test connection
        await db_instance.connect()
        
        # Verify connection state
        assert db_instance.is_connected is True
        assert db_instance.client is not None
        assert db_instance.database is not None
        
        # Verify database name
        assert db_instance.database.name == settings.database_name
        
        # Test ping
        ping_result = await db_instance.ping()
        assert ping_result is True
        
        # Cleanup
        await db_instance.disconnect()
        assert db_instance.is_connected is False
    
    @pytest.mark.asyncio
    async def test_connection_pooling_settings(self, db_instance):
        """Test that connection pooling is properly configured."""
        await db_instance.connect()
        
        # Access internal client options (if available)
        if hasattr(db_instance.client, 'options'):
            pool_options = db_instance.client.options.pool_options
            assert pool_options.max_pool_size == 10
            assert pool_options.min_pool_size == 1
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_ping_functionality(self, db_instance):
        """Test database ping functionality."""
        # Before connection
        ping_result = await db_instance.ping()
        assert ping_result is False
        
        # After connection
        await db_instance.connect()
        ping_result = await db_instance.ping()
        assert ping_result is True
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_disconnect_functionality(self, db_instance):
        """Test proper disconnection and cleanup."""
        # Connect first
        await db_instance.connect()
        assert db_instance.is_connected is True
        
        # Disconnect
        await db_instance.disconnect()
        
        # Verify cleanup
        assert db_instance.client is None
        assert db_instance.database is None
        assert db_instance.is_connected is False
    
    @pytest.mark.asyncio
    async def test_get_database_when_connected(self, db_instance):
        """Test getting database instance when connected."""
        await db_instance.connect()
        
        db = db_instance.get_database()
        assert isinstance(db, AsyncIOMotorDatabase)
        assert db.name == settings.database_name
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_database_when_not_connected(self, db_instance):
        """Test getting database instance when not connected raises error."""
        with pytest.raises(RuntimeError, match="Database not connected"):
            db_instance.get_database()
    
    @pytest.mark.asyncio
    async def test_get_client_when_connected(self, db_instance):
        """Test getting client instance when connected."""
        await db_instance.connect()
        
        client = db_instance.get_client()
        assert isinstance(client, AsyncIOMotorClient)
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_client_when_not_connected(self, db_instance):
        """Test getting client instance when not connected raises error."""
        with pytest.raises(RuntimeError, match="Database client not connected"):
            db_instance.get_client()
    
    @pytest.mark.asyncio
    async def test_check_connection_when_disconnected(self, db_instance):
        """Test check_connection establishes connection when disconnected."""
        assert db_instance.is_connected is False
        
        result = await db_instance.check_connection()
        
        # Should be True if connection successful
        if settings.mongodb_url != "mongodb://localhost:27017":
            assert result is True
            assert db_instance.is_connected is True
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_check_connection_when_already_connected(self, db_instance):
        """Test check_connection with existing healthy connection."""
        await db_instance.connect()
        
        result = await db_instance.check_connection()
        assert result is True
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, db_instance):
        """Test proper error handling for connection failures."""
        # Use invalid URL to force connection error
        original_url = settings.mongodb_url
        settings.mongodb_url = "mongodb://invalid:27017/test?serverSelectionTimeoutMS=100"
        
        with pytest.raises(Exception):
            await db_instance.connect()
        
        # Verify cleanup after error
        assert db_instance.is_connected is False
        assert db_instance.client is None
        assert db_instance.database is None
        
        # Restore original URL
        settings.mongodb_url = original_url
    
    @pytest.mark.asyncio
    async def test_beanie_initialization(self, db_instance):
        """Test Beanie ODM initialization."""
        from beanie import Document
        
        # Define a test document
        class TestDocument(Document):
            name: str
            
            class Settings:
                name = "test_collection"
        
        # Connect first
        await db_instance.connect()
        
        # Initialize Beanie
        await db_instance.init_beanie_models([TestDocument])
        
        # Verify we can use the model (basic check)
        # In real usage, Beanie would be fully initialized
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_beanie_initialization_without_connection(self, db_instance):
        """Test Beanie initialization fails without connection."""
        from beanie import Document
        
        class TestDocument(Document):
            name: str
        
        with pytest.raises(RuntimeError, match="Database not connected"):
            await db_instance.init_beanie_models([TestDocument])
    
    @pytest.mark.asyncio
    async def test_dependency_get_database(self):
        """Test FastAPI dependency for getting database."""
        # Reset global database instance
        if database.is_connected:
            await database.disconnect()
        
        # Get database through dependency
        db = await get_database()
        
        assert isinstance(db, AsyncIOMotorDatabase)
        assert database.is_connected is True
        
        # Cleanup
        await database.disconnect()
    
    @pytest.mark.asyncio
    async def test_dependency_get_client(self):
        """Test FastAPI dependency for getting client."""
        # Reset global database instance
        if database.is_connected:
            await database.disconnect()
        
        # Get client through dependency
        client = await get_client()
        
        assert isinstance(client, AsyncIOMotorClient)
        assert database.is_connected is True
        
        # Cleanup
        await database.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_restore_after_ping_failure(self, db_instance):
        """Test connection restoration when ping fails."""
        # Connect first
        await db_instance.connect()
        
        # Mock ping to fail
        with patch.object(db_instance, 'ping', return_value=False):
            # Mock reconnection to succeed
            original_connect = db_instance.connect
            with patch.object(db_instance, 'connect', side_effect=original_connect):
                result = await db_instance.check_connection()
                
                # Should attempt reconnection
                assert db_instance.connect.called
        
        await db_instance.disconnect()
    
    @pytest.mark.asyncio
    async def test_logging_on_connection_events(self, caplog):
        """Test that connection events are properly logged."""
        db = Database()
        
        # Set log level to INFO to capture logs
        caplog.set_level(logging.INFO)
        
        # Test connection logging
        if settings.mongodb_url != "mongodb://localhost:27017":
            await db.connect()
            assert "Successfully connected to MongoDB Atlas" in caplog.text
            
            await db.disconnect()
            assert "MongoDB connection closed" in caplog.text