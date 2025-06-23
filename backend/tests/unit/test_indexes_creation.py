import pytest
from pymongo import ASCENDING, DESCENDING, TEXT
from typing import Dict, List, Any

from src.database import Database, IndexManager
from src.config import settings


class TestIndexesCreation:
    """Test MongoDB collection index creation with real database."""
    
    @pytest.fixture
    async def db_connection(self):
        """Provide a real database connection for testing."""
        db = Database()
        await db.connect()
        
        # Use test database
        test_db_name = f"{settings.database_name}_test"
        test_db = db.client[test_db_name]
        
        yield test_db
        
        # Cleanup: drop test collections
        for collection_name in ["users", "posts", "comments", "reactions", "stats"]:
            await test_db[collection_name].drop()
        
        await db.disconnect()
    
    def test_user_indexes_definition(self):
        """Test user collection index definitions."""
        indexes = IndexManager.get_user_indexes()
        
        # Should have 4 indexes
        assert len(indexes) == 4
        
        # Check email unique index
        email_idx = next(idx for idx in indexes if idx.document["name"] == "email_unique_idx")
        assert email_idx.document["key"] == {"email": ASCENDING}
        assert email_idx.document["unique"] is True
        
        # Check handle unique index
        handle_idx = next(idx for idx in indexes if idx.document["name"] == "handle_unique_idx")
        assert handle_idx.document["key"] == {"handle": ASCENDING}
        assert handle_idx.document["unique"] is True
        assert handle_idx.document.get("sparse") is True
        
        # Check compound index
        compound_idx = next(idx for idx in indexes if idx.document["name"] == "status_created_idx")
        assert compound_idx.document["key"] == {"status": ASCENDING, "created_at": DESCENDING}
        
        # Check text search index
        text_idx = next(idx for idx in indexes if idx.document["name"] == "user_text_search_idx")
        assert text_idx.document["key"] == {"name": TEXT, "bio": TEXT}
        assert "weights" in text_idx.document
    
    def test_post_indexes_definition(self):
        """Test post collection index definitions."""
        indexes = IndexManager.get_post_indexes()
        
        # Should have 5 indexes
        assert len(indexes) == 5
        
        # Check slug unique index
        slug_idx = next(idx for idx in indexes if idx.document["name"] == "slug_unique_idx")
        assert slug_idx.document["key"] == {"slug": ASCENDING}
        assert slug_idx.document["unique"] is True
        
        # Check service-status compound index
        service_idx = next(idx for idx in indexes if idx.document["name"] == "service_status_created_idx")
        assert service_idx.document["key"] == {
            "service": ASCENDING,
            "status": ASCENDING,
            "created_at": DESCENDING
        }
        
        # Check partial index for published posts
        published_idx = next(idx for idx in indexes if idx.document["name"] == "published_posts_idx")
        assert "partialFilterExpression" in published_idx.document
        assert published_idx.document["partialFilterExpression"] == {"status": "published"}
    
    def test_comment_indexes_definition(self):
        """Test comment collection index definitions."""
        indexes = IndexManager.get_comment_indexes()
        
        # Should have 4 indexes
        assert len(indexes) == 4
        
        # Check post comments index
        post_idx = next(idx for idx in indexes if idx.document["name"] == "post_comments_idx")
        assert post_idx.document["key"] == {"post_id": ASCENDING, "created_at": ASCENDING}
        
        # Check parent comment index (sparse)
        parent_idx = next(idx for idx in indexes if idx.document["name"] == "parent_comment_idx")
        assert parent_idx.document["key"] == {"parent_id": ASCENDING}
        assert parent_idx.document.get("sparse") is True
    
    def test_reaction_indexes_definition(self):
        """Test reaction collection index definitions."""
        indexes = IndexManager.get_reaction_indexes()
        
        # Should have 3 indexes
        assert len(indexes) == 3
        
        # Check unique constraint index
        unique_idx = next(idx for idx in indexes if idx.document["name"] == "user_target_unique_idx")
        assert unique_idx.document["key"] == {
            "user_id": ASCENDING,
            "target_id": ASCENDING,
            "target_type": ASCENDING
        }
        assert unique_idx.document["unique"] is True
    
    def test_stats_indexes_definition(self):
        """Test stats collection index definitions."""
        indexes = IndexManager.get_stats_indexes()
        
        # Should have 3 indexes
        assert len(indexes) == 3
        
        # Check entity unique constraint
        entity_idx = next(idx for idx in indexes if idx.document["name"] == "entity_stats_unique_idx")
        assert entity_idx.document["key"] == {"entity_id": ASCENDING, "entity_type": ASCENDING}
        assert entity_idx.document["unique"] is True
    
    @pytest.mark.asyncio
    async def test_create_all_indexes_real_db(self, db_connection):
        """Test creating all indexes in real MongoDB Atlas."""
        # Skip if using localhost (no real Atlas connection)
        if settings.mongodb_url == "mongodb://localhost:27017":
            pytest.skip("MongoDB Atlas URL not configured")
        
        # Create all indexes
        created = await IndexManager.create_all_indexes(db_connection)
        
        # Verify indexes were created for each collection
        assert "users" in created
        assert "posts" in created
        assert "comments" in created
        assert "reactions" in created
        assert "stats" in created
        
        # Verify actual index creation in database
        for collection_name in created:
            indexes = await IndexManager.get_index_info(db_connection, collection_name)
            
            # Should have at least the _id index plus our custom indexes
            assert len(indexes) > 1
            
            # Check that index names match what we expect
            index_names = [idx["name"] for idx in indexes]
            
            if collection_name == "users":
                assert "email_unique_idx" in index_names
                assert "handle_unique_idx" in index_names
                assert "user_text_search_idx" in index_names
            elif collection_name == "posts":
                assert "slug_unique_idx" in index_names
                assert "post_text_search_idx" in index_names
    
    @pytest.mark.asyncio
    async def test_drop_all_indexes(self, db_connection):
        """Test dropping all indexes."""
        # First create indexes
        await IndexManager.create_all_indexes(db_connection)
        
        # Then drop them
        await IndexManager.drop_all_indexes(db_connection)
        
        # Verify only _id index remains
        for collection_name in ["users", "posts", "comments", "reactions", "stats"]:
            indexes = await IndexManager.get_index_info(db_connection, collection_name)
            
            # Should only have the default _id index
            assert len(indexes) == 1
            assert indexes[0]["name"] == "_id_"
    
    @pytest.mark.asyncio
    async def test_ensure_indexes_idempotent(self, db_connection):
        """Test that ensure_indexes is safe to call multiple times."""
        # Call ensure_indexes multiple times
        await IndexManager.ensure_indexes(db_connection)
        await IndexManager.ensure_indexes(db_connection)
        
        # Should not raise any errors and indexes should exist
        users_indexes = await IndexManager.get_index_info(db_connection, "users")
        assert len(users_indexes) > 1
    
    @pytest.mark.asyncio
    async def test_text_search_index_weights(self, db_connection):
        """Test that text search indexes have proper weights."""
        await IndexManager.create_all_indexes(db_connection)
        
        # Check posts text index
        posts_indexes = await IndexManager.get_index_info(db_connection, "posts")
        text_index = next(idx for idx in posts_indexes if idx["name"] == "post_text_search_idx")
        
        # Verify weights are set correctly
        assert "weights" in text_index
        weights = text_index["weights"]
        assert weights.get("title") == 10
        assert weights.get("tags") == 5
        assert weights.get("content") == 3
    
    @pytest.mark.asyncio
    async def test_partial_index_filter(self, db_connection):
        """Test partial index with filter expression."""
        await IndexManager.create_all_indexes(db_connection)
        
        # Check published posts partial index
        posts_indexes = await IndexManager.get_index_info(db_connection, "posts")
        published_idx = next(idx for idx in posts_indexes if idx["name"] == "published_posts_idx")
        
        # Verify partial filter expression
        assert "partialFilterExpression" in published_idx
        assert published_idx["partialFilterExpression"] == {"status": "published"}
    
    @pytest.mark.asyncio
    async def test_compound_index_order(self, db_connection):
        """Test that compound indexes maintain correct field order."""
        await IndexManager.create_all_indexes(db_connection)
        
        # Check posts service-status-created compound index
        posts_indexes = await IndexManager.get_index_info(db_connection, "posts")
        compound_idx = next(idx for idx in posts_indexes if idx["name"] == "service_status_created_idx")
        
        # Verify field order is preserved
        key_list = list(compound_idx["key"].items())
        assert key_list[0] == ("service", 1)  # ASCENDING = 1
        assert key_list[1] == ("status", 1)
        assert key_list[2] == ("created_at", -1)  # DESCENDING = -1
    
    @pytest.mark.asyncio
    async def test_unique_constraint_indexes(self, db_connection):
        """Test that unique constraint indexes are properly created."""
        await IndexManager.create_all_indexes(db_connection)
        
        # Test users email unique index
        users_indexes = await IndexManager.get_index_info(db_connection, "users")
        email_idx = next(idx for idx in users_indexes if idx["name"] == "email_unique_idx")
        assert email_idx.get("unique") is True
        
        # Test reactions unique constraint
        reactions_indexes = await IndexManager.get_index_info(db_connection, "reactions")
        unique_idx = next(idx for idx in reactions_indexes if idx["name"] == "user_target_unique_idx")
        assert unique_idx.get("unique") is True
    
    @pytest.mark.asyncio
    async def test_sparse_indexes(self, db_connection):
        """Test that sparse indexes are properly configured."""
        await IndexManager.create_all_indexes(db_connection)
        
        # Check users handle sparse index
        users_indexes = await IndexManager.get_index_info(db_connection, "users")
        handle_idx = next(idx for idx in users_indexes if idx["name"] == "handle_unique_idx")
        assert handle_idx.get("sparse") is True
        
        # Check comments parent_id sparse index
        comments_indexes = await IndexManager.get_index_info(db_connection, "comments")
        parent_idx = next(idx for idx in comments_indexes if idx["name"] == "parent_comment_idx")
        assert parent_idx.get("sparse") is True