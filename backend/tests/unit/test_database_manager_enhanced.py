"""Enhanced unit tests for database manager functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.database.manager import DatabaseManager, IndexManager


class TestIndexManager:
    """Test index management functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def index_manager(self, mock_db):
        """Create index manager instance."""
        return IndexManager(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_user_indexes_success(self, index_manager, mock_db):
        """Test successful user indexes creation."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.create_index = AsyncMock(return_value="index_created")
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        await index_manager.create_user_indexes()
        
        # Assert
        mock_db.__getitem__.assert_called_with("users")
        assert mock_collection.create_index.call_count >= 2  # email and user_handle indexes
    
    @pytest.mark.asyncio
    async def test_create_post_indexes_success(self, index_manager, mock_db):
        """Test successful post indexes creation."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.create_index = AsyncMock(return_value="index_created")
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        await index_manager.create_post_indexes()
        
        # Assert
        mock_db.__getitem__.assert_called_with("posts")
        assert mock_collection.create_index.call_count >= 3  # slug, author_id, and compound indexes
    
    @pytest.mark.asyncio
    async def test_create_comment_indexes_success(self, index_manager, mock_db):
        """Test successful comment indexes creation."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.create_index = AsyncMock(return_value="index_created")
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        await index_manager.create_comment_indexes()
        
        # Assert
        mock_db.__getitem__.assert_called_with("comments")
        assert mock_collection.create_index.call_count >= 2  # parent_id and author_id indexes
    
    @pytest.mark.asyncio
    async def test_create_text_search_indexes_success(self, index_manager, mock_db):
        """Test successful text search indexes creation."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.create_index = AsyncMock(return_value="index_created")
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        await index_manager.create_text_search_indexes()
        
        # Assert
        mock_db.__getitem__.assert_called_with("posts")
        # Should create text index on title and content
        mock_collection.create_index.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_all_indexes_success(self, index_manager):
        """Test creating all indexes successfully."""
        # Arrange
        with patch.object(index_manager, 'create_user_indexes', new_callable=AsyncMock) as mock_user, \
             patch.object(index_manager, 'create_post_indexes', new_callable=AsyncMock) as mock_post, \
             patch.object(index_manager, 'create_comment_indexes', new_callable=AsyncMock) as mock_comment, \
             patch.object(index_manager, 'create_text_search_indexes', new_callable=AsyncMock) as mock_text:
            
            # Act
            await index_manager.create_all_indexes()
            
            # Assert
            mock_user.assert_called_once()
            mock_post.assert_called_once()
            mock_comment.assert_called_once()
            mock_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_index_failure(self, index_manager, mock_db):
        """Test index creation failure handling."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.create_index = AsyncMock(side_effect=Exception("Index creation failed"))
        mock_db.__getitem__.return_value = mock_collection
        
        # Act & Assert
        with pytest.raises(Exception):
            await index_manager.create_user_indexes()
    
    @pytest.mark.asyncio
    async def test_list_indexes_success(self, index_manager, mock_db):
        """Test successful index listing."""
        # Arrange
        mock_collection = MagicMock()
        mock_indexes = [
            {"name": "_id_", "key": [("_id", 1)]},
            {"name": "email_1", "key": [("email", 1)]},
            {"name": "user_handle_1", "key": [("user_handle", 1)]}
        ]
        mock_collection.list_indexes = AsyncMock(return_value=mock_indexes)
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        result = await index_manager.list_indexes("users")
        
        # Assert
        assert result == mock_indexes
        mock_collection.list_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_drop_index_success(self, index_manager, mock_db):
        """Test successful index dropping."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.drop_index = AsyncMock(return_value=True)
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        result = await index_manager.drop_index("users", "email_1")
        
        # Assert
        assert result is True
        mock_collection.drop_index.assert_called_once_with("email_1")
    
    @pytest.mark.asyncio
    async def test_drop_index_failure(self, index_manager, mock_db):
        """Test index dropping failure."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.drop_index = AsyncMock(side_effect=Exception("Index not found"))
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        result = await index_manager.drop_index("users", "non_existent_index")
        
        # Assert
        assert result is False


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database instance."""
        db = MagicMock()
        db.db = MagicMock()
        db.client = MagicMock()
        return db
    
    @pytest.fixture
    def database_manager(self, mock_database):
        """Create database manager instance."""
        return DatabaseManager(mock_database)
    
    @pytest.mark.asyncio
    async def test_initialize_database_success(self, database_manager, mock_database):
        """Test successful database initialization."""
        # Arrange
        with patch.object(database_manager, 'create_collections', new_callable=AsyncMock) as mock_collections, \
             patch.object(database_manager, 'create_indexes', new_callable=AsyncMock) as mock_indexes, \
             patch.object(database_manager, 'setup_validation', new_callable=AsyncMock) as mock_validation:
            
            # Act
            await database_manager.initialize_database()
            
            # Assert
            mock_collections.assert_called_once()
            mock_indexes.assert_called_once()
            mock_validation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_collections_success(self, database_manager, mock_database):
        """Test successful collections creation."""
        # Arrange
        mock_db = mock_database.db
        mock_db.create_collection = AsyncMock(return_value=True)
        mock_db.list_collection_names = AsyncMock(return_value=[])
        
        # Act
        await database_manager.create_collections()
        
        # Assert
        mock_db.list_collection_names.assert_called_once()
        # Should create collections for users, posts, comments, etc.
        assert mock_db.create_collection.call_count >= 4
    
    @pytest.mark.asyncio
    async def test_create_collections_already_exist(self, database_manager, mock_database):
        """Test collections creation when they already exist."""
        # Arrange
        mock_db = mock_database.db
        existing_collections = ["users", "posts", "comments", "files"]
        mock_db.list_collection_names = AsyncMock(return_value=existing_collections)
        mock_db.create_collection = AsyncMock()
        
        # Act
        await database_manager.create_collections()
        
        # Assert
        # Should not create collections that already exist
        mock_db.create_collection.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_indexes_success(self, database_manager, mock_database):
        """Test successful indexes creation."""
        # Arrange
        with patch('src.database.manager.IndexManager') as mock_index_manager_class:
            mock_index_manager = MagicMock()
            mock_index_manager.create_all_indexes = AsyncMock()
            mock_index_manager_class.return_value = mock_index_manager
            
            # Act
            await database_manager.create_indexes()
            
            # Assert
            mock_index_manager_class.assert_called_once_with(mock_database.db)
            mock_index_manager.create_all_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_validation_success(self, database_manager, mock_database):
        """Test successful validation setup."""
        # Arrange
        mock_db = mock_database.db
        mock_db.command = AsyncMock(return_value={"ok": 1})
        
        # Act
        await database_manager.setup_validation()
        
        # Assert
        # Should set up JSON schema validation for collections
        assert mock_db.command.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_backup_database_success(self, database_manager, mock_database):
        """Test successful database backup."""
        # Arrange
        mock_client = mock_database.client
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        
        backup_options = {
            "backup_name": "test_backup",
            "include_collections": ["users", "posts"]
        }
        
        # Act
        result = await database_manager.backup_database(backup_options)
        
        # Assert
        assert result is True
        mock_client.admin.command.assert_called()
    
    @pytest.mark.asyncio
    async def test_restore_database_success(self, database_manager, mock_database):
        """Test successful database restore."""
        # Arrange
        mock_client = mock_database.client
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        
        restore_options = {
            "backup_name": "test_backup",
            "target_database": "restored_db"
        }
        
        # Act
        result = await database_manager.restore_database(restore_options)
        
        # Assert
        assert result is True
        mock_client.admin.command.assert_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_database_success(self, database_manager, mock_database):
        """Test successful database cleanup."""
        # Arrange
        mock_db = mock_database.db
        mock_collection = MagicMock()
        mock_collection.delete_many = AsyncMock(return_value=MagicMock(deleted_count=10))
        mock_db.__getitem__.return_value = mock_collection
        mock_db.list_collection_names = AsyncMock(return_value=["users", "posts", "comments"])
        
        # Act
        result = await database_manager.cleanup_database()
        
        # Assert
        assert result["total_cleaned"] >= 0
        assert "collections_cleaned" in result
    
    @pytest.mark.asyncio
    async def test_get_database_info_success(self, database_manager, mock_database):
        """Test successful database info retrieval."""
        # Arrange
        mock_db = mock_database.db
        mock_db.command = AsyncMock(return_value={
            "db": "test_db",
            "collections": 5,
            "dataSize": 1024000,
            "indexSize": 204800
        })
        mock_db.list_collection_names = AsyncMock(return_value=["users", "posts", "comments"])
        
        # Act
        result = await database_manager.get_database_info()
        
        # Assert
        assert "db_stats" in result
        assert "collections" in result
        assert result["collections"] == ["users", "posts", "comments"]
    
    @pytest.mark.asyncio
    async def test_verify_database_integrity_success(self, database_manager, mock_database):
        """Test successful database integrity verification."""
        # Arrange
        mock_db = mock_database.db
        mock_db.command = AsyncMock(return_value={"ok": 1, "valid": True})
        mock_db.list_collection_names = AsyncMock(return_value=["users", "posts", "comments"])
        
        # Act
        result = await database_manager.verify_database_integrity()
        
        # Assert
        assert result["overall_status"] == "healthy"
        assert "collection_checks" in result
    
    @pytest.mark.asyncio
    async def test_optimize_database_success(self, database_manager, mock_database):
        """Test successful database optimization."""
        # Arrange
        mock_db = mock_database.db
        mock_collection = MagicMock()
        mock_collection.reindex = AsyncMock(return_value={"ok": 1})
        mock_db.__getitem__.return_value = mock_collection
        mock_db.list_collection_names = AsyncMock(return_value=["users", "posts"])
        
        # Act
        result = await database_manager.optimize_database()
        
        # Assert
        assert result["status"] == "completed"
        assert "optimized_collections" in result