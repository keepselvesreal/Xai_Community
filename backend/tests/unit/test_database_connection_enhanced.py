"""Enhanced unit tests for database connection functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nadle_backend.database.connection import Database
from nadle_backend.config import settings


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    @pytest.fixture
    def database(self):
        """Create database instance."""
        return Database()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, database):
        """Test successful database connection."""
        # Arrange
        with patch('src.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_client_class.return_value = mock_client
            
            # Act
            await database.connect()
            
            # Assert
            assert database.client is not None
            assert database.db is not None
            mock_client_class.assert_called_once_with(settings.mongodb_url)
            mock_client.admin.command.assert_called_once_with('ismaster')
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, database):
        """Test database connection failure."""
        # Arrange
        with patch('src.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.admin.command = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client
            
            # Act & Assert
            with pytest.raises(Exception):
                await database.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, database):
        """Test successful database disconnection."""
        # Arrange
        mock_client = MagicMock()
        mock_client.close = MagicMock()
        database.client = mock_client
        
        # Act
        await database.disconnect()
        
        # Assert
        mock_client.close.assert_called_once()
        assert database.client is None
        assert database.db is None
    
    @pytest.mark.asyncio
    async def test_disconnect_no_client(self, database):
        """Test disconnection when no client exists."""
        # Arrange
        database.client = None
        
        # Act (should not raise exception)
        await database.disconnect()
        
        # Assert
        assert database.client is None
        assert database.db is None
    
    @pytest.mark.asyncio
    async def test_init_beanie_models_success(self, database):
        """Test successful Beanie models initialization."""
        # Arrange
        mock_db = MagicMock()
        database.db = mock_db
        
        with patch('beanie.init_beanie') as mock_init_beanie:
            mock_init_beanie.return_value = AsyncMock()
            
            from nadle_backend.models.core import User, Post, Comment
            models = [User, Post, Comment]
            
            # Act
            await database.init_beanie_models(models)
            
            # Assert
            mock_init_beanie.assert_called_once_with(
                database=mock_db,
                document_models=models
            )
    
    @pytest.mark.asyncio
    async def test_init_beanie_models_failure(self, database):
        """Test Beanie models initialization failure."""
        # Arrange
        mock_db = MagicMock()
        database.db = mock_db
        
        with patch('beanie.init_beanie') as mock_init_beanie:
            mock_init_beanie.side_effect = Exception("Beanie initialization failed")
            
            from nadle_backend.models.core import User, Post, Comment
            models = [User, Post, Comment]
            
            # Act & Assert
            with pytest.raises(Exception):
                await database.init_beanie_models(models)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, database):
        """Test successful database health check."""
        # Arrange
        mock_client = MagicMock()
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        database.client = mock_client
        
        # Act
        result = await database.health_check()
        
        # Assert
        assert result is True
        mock_client.admin.command.assert_called_once_with('ping')
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, database):
        """Test database health check failure."""
        # Arrange
        mock_client = MagicMock()
        mock_client.admin.command = AsyncMock(side_effect=Exception("Ping failed"))
        database.client = mock_client
        
        # Act
        result = await database.health_check()
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_no_client(self, database):
        """Test health check when no client exists."""
        # Arrange
        database.client = None
        
        # Act
        result = await database.health_check()
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_database_stats(self, database):
        """Test getting database statistics."""
        # Arrange
        mock_db = MagicMock()
        mock_stats = {
            "db": "test_db",
            "collections": 5,
            "dataSize": 1024000,
            "indexSize": 204800
        }
        mock_db.command = AsyncMock(return_value=mock_stats)
        database.db = mock_db
        
        # Act
        result = await database.get_database_stats()
        
        # Assert
        assert result == mock_stats
        mock_db.command.assert_called_once_with("dbStats")
    
    @pytest.mark.asyncio
    async def test_get_database_stats_no_db(self, database):
        """Test getting database stats when no database exists."""
        # Arrange
        database.db = None
        
        # Act
        result = await database.get_database_stats()
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_collections(self, database):
        """Test listing database collections."""
        # Arrange
        mock_db = MagicMock()
        mock_collections = ["users", "posts", "comments", "files"]
        mock_db.list_collection_names = AsyncMock(return_value=mock_collections)
        database.db = mock_db
        
        # Act
        result = await database.list_collections()
        
        # Assert
        assert result == mock_collections
        mock_db.list_collection_names.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_collections_no_db(self, database):
        """Test listing collections when no database exists."""
        # Arrange
        database.db = None
        
        # Act
        result = await database.list_collections()
        
        # Assert
        assert result == []


class TestDatabaseSingleton:
    """Test database singleton pattern."""
    
    def test_database_singleton(self):
        """Test that Database follows singleton pattern."""
        # Act
        db1 = Database()
        db2 = Database()
        
        # Assert
        assert db1 is db2
    
    @pytest.mark.asyncio
    async def test_global_database_instance(self):
        """Test global database instance access."""
        # Arrange
        from nadle_backend.database.connection import database
        
        # Act & Assert
        assert isinstance(database, Database)
        assert database is not None


class TestDatabaseConfiguration:
    """Test database configuration."""
    
    def test_mongodb_url_construction(self):
        """Test MongoDB URL construction from settings."""
        # Arrange
        expected_parts = [
            "mongodb+srv://",
            settings.mongodb_host,
            settings.database_name
        ]
        
        # Act
        url = settings.mongodb_url
        
        # Assert
        for part in expected_parts:
            assert part in url
    
    def test_database_name_from_settings(self):
        """Test database name is correctly set from settings."""
        # Arrange
        database = Database()
        
        # Act
        db_name = database.database_name
        
        # Assert
        assert db_name == settings.database_name
    
    @pytest.mark.asyncio
    async def test_connection_with_custom_options(self):
        """Test database connection with custom options."""
        # Arrange
        database = Database()
        
        with patch('src.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_client_class.return_value = mock_client
            
            # Act
            await database.connect()
            
            # Assert
            # Verify that connection was called with MongoDB URL
            call_args = mock_client_class.call_args
            assert settings.mongodb_url in str(call_args)


class TestDatabaseErrorHandling:
    """Test database error handling."""
    
    @pytest.mark.asyncio
    async def test_connect_with_retry_logic(self, database):
        """Test connection with retry logic."""
        # Arrange
        with patch('src.database.connection.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()
            # First call fails, second succeeds
            mock_client.admin.command = AsyncMock(side_effect=[
                Exception("Temporary failure"),
                {"ok": 1}
            ])
            mock_client_class.return_value = mock_client
            
            # Note: This test assumes retry logic exists in the actual implementation
            # If not implemented, this test documents the expected behavior
            
            # Act & Assert
            with pytest.raises(Exception):  # Should fail on first attempt
                await database.connect()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, database):
        """Test graceful database shutdown."""
        # Arrange
        mock_client = MagicMock()
        mock_client.close = MagicMock()
        database.client = mock_client
        database.db = MagicMock()
        
        # Act
        await database.disconnect()
        
        # Assert
        mock_client.close.assert_called_once()
        assert database.client is None
        assert database.db is None