"""Enhanced unit tests for database manager functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nadle_backend.database.manager import IndexManager


class TestIndexManager:
    """Test index management functionality."""
    
    def test_get_user_indexes(self):
        """Test user indexes definition."""
        # Act
        indexes = IndexManager.get_user_indexes()
        
        # Assert
        assert len(indexes) > 0
        assert any("email" in str(idx.document) for idx in indexes)
    
    def test_get_post_indexes(self):
        """Test post indexes definition."""
        # Act
        indexes = IndexManager.get_post_indexes()
        
        # Assert
        assert len(indexes) > 0
        assert any("slug" in str(idx.document) for idx in indexes)
    
    def test_get_comment_indexes(self):
        """Test comment indexes definition."""
        # Act
        indexes = IndexManager.get_comment_indexes()
        
        # Assert
        assert len(indexes) > 0
        assert any("parent_id" in str(idx.document) for idx in indexes)
    
    def test_get_reaction_indexes(self):
        """Test reaction indexes definition."""
        # Act
        indexes = IndexManager.get_reaction_indexes()
        
        # Assert
        assert len(indexes) > 0
        assert any("user_id" in str(idx.document) for idx in indexes)
    
    def test_get_stats_indexes(self):
        """Test stats indexes definition."""
        # Act
        indexes = IndexManager.get_stats_indexes()
        
        # Assert
        assert len(indexes) > 0
        assert any("entity_id" in str(idx.document) for idx in indexes)
    
    @pytest.mark.asyncio
    async def test_create_all_indexes(self):
        """Test creating all indexes."""
        # Arrange
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.create_indexes = AsyncMock(return_value=["index1", "index2"])
        mock_db.__getitem__.return_value = mock_collection
        
        # Act
        result = await IndexManager.create_all_indexes(mock_db)
        
        # Assert
        assert isinstance(result, dict)
        assert len(result) > 0