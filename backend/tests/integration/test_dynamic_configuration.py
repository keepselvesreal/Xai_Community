"""
Integration tests for dynamic database and collection configuration.

Tests verify that the packageization implementation works correctly:
- Phase 1: Configuration file extensions
- Phase 2: Dynamic model collection names  
- Phase 3: Hardcoding removal
- Phase 4: MongoDB Atlas verification
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import patch
import os

from src.config import settings
from src.database.connection import database
from src.models.core import User, Post, Comment, FileRecord, PostStats, UserReaction, Stats
from src.utils.password import PasswordManager


class TestPhase1ConfigurationExtension:
    """Test Phase 1: Configuration file extensions."""
    
    def test_collection_settings_exist(self):
        """Test that all dynamic collection settings are available."""
        # Verify all collection settings are defined
        assert hasattr(settings, 'users_collection')
        assert hasattr(settings, 'posts_collection')
        assert hasattr(settings, 'comments_collection')
        assert hasattr(settings, 'post_stats_collection')
        assert hasattr(settings, 'user_reactions_collection')
        assert hasattr(settings, 'files_collection')
        assert hasattr(settings, 'stats_collection')
        
        # Verify they have values
        assert settings.users_collection
        assert settings.posts_collection
        assert settings.comments_collection
        assert settings.post_stats_collection
        assert settings.user_reactions_collection
        assert settings.files_collection
        assert settings.stats_collection
    
    def test_api_branding_settings(self):
        """Test that API branding settings are configurable."""
        assert hasattr(settings, 'api_title')
        assert hasattr(settings, 'api_description')
        assert hasattr(settings, 'api_version')
        
        # Verify they have values
        assert settings.api_title
        assert settings.api_description
        assert settings.api_version
    
    def test_environment_variable_loading(self):
        """Test that environment variables are properly loaded."""
        # These should match the values from .env file
        assert settings.database_name == "dynamic_config_db"
        assert settings.users_collection == "members"
        assert settings.posts_collection == "articles"
        assert settings.comments_collection == "discussions"
        assert settings.files_collection == "uploads"
        assert settings.api_title == "My Custom API"


class TestPhase2DynamicModels:
    """Test Phase 2: Dynamic model collection names."""
    
    def test_user_model_dynamic_collection(self):
        """Test that User model uses dynamic collection name."""
        assert User.Settings.name == settings.users_collection
        assert User.Settings.name == "members"
    
    def test_post_model_dynamic_collection(self):
        """Test that Post model uses dynamic collection name."""
        assert Post.Settings.name == settings.posts_collection
        assert Post.Settings.name == "articles"
    
    def test_comment_model_dynamic_collection(self):
        """Test that Comment model uses dynamic collection name."""
        assert Comment.Settings.name == settings.comments_collection
        assert Comment.Settings.name == "discussions"
    
    def test_file_model_dynamic_collection(self):
        """Test that FileRecord model uses dynamic collection name."""
        assert FileRecord.Settings.name == settings.files_collection
        assert FileRecord.Settings.name == "uploads"
    
    def test_all_models_use_settings(self):
        """Test that all models use settings for collection names."""
        models_and_settings = [
            (User, settings.users_collection),
            (Post, settings.posts_collection),
            (Comment, settings.comments_collection),
            (PostStats, settings.post_stats_collection),
            (UserReaction, settings.user_reactions_collection),
            (FileRecord, settings.files_collection),
            (Stats, settings.stats_collection)
        ]
        
        for model_class, expected_collection in models_and_settings:
            assert model_class.Settings.name == expected_collection


class TestPhase3HardcodingRemoval:
    """Test Phase 3: Hardcoding removal verification."""
    
    def test_main_app_uses_dynamic_settings(self):
        """Test that main app uses dynamic API settings."""
        from main import create_app
        
        app = create_app()
        assert app.title == settings.api_title
        assert app.description == settings.api_description
        assert app.version == settings.api_version
    
    def test_index_manager_uses_dynamic_collections(self):
        """Test that IndexManager uses dynamic collection names."""
        from src.database.manager import IndexManager
        
        # Mock database to test index creation logic
        class MockDatabase:
            def __init__(self):
                self.collections = {}
            
            def __getitem__(self, collection_name):
                if collection_name not in self.collections:
                    self.collections[collection_name] = MockCollection(collection_name)
                return self.collections[collection_name]
        
        class MockCollection:
            def __init__(self, name):
                self.name = name
                self.indexes_created = []
            
            async def create_indexes(self, indexes):
                self.indexes_created = indexes
                return [f"index_{i}" for i in range(len(indexes))]
        
        async def test_index_creation():
            mock_db = MockDatabase()
            await IndexManager.create_all_indexes(mock_db)
            
            # Verify that dynamic collection names are used
            expected_collections = {
                settings.users_collection,
                settings.posts_collection,
                settings.comments_collection,
                settings.user_reactions_collection,
                settings.stats_collection
            }
            
            created_collections = set(mock_db.collections.keys())
            assert expected_collections.issubset(created_collections)
        
        asyncio.run(test_index_creation())


@pytest.mark.asyncio
class TestPhase4MongoDBVerification:
    """Test Phase 4: MongoDB Atlas integration verification."""
    
    async def test_database_connection_with_dynamic_name(self):
        """Test database connection uses dynamic database name."""
        await database.connect()
        assert database.database.name == settings.database_name
        assert database.database.name == "dynamic_config_db"
        await database.disconnect()
    
    async def test_model_initialization_with_dynamic_collections(self):
        """Test that models initialize with dynamic collection names."""
        await database.connect()
        await database.init_beanie_models([User, Post, Comment, FileRecord])
        
        # Models should be ready to use with dynamic collections
        assert User.Settings.name == "members"
        assert Post.Settings.name == "articles"
        assert Comment.Settings.name == "discussions"
        assert FileRecord.Settings.name == "uploads"
        
        await database.disconnect()
    
    async def test_crud_operations_with_dynamic_collections(self):
        """Test CRUD operations work with dynamic collection names."""
        await database.connect()
        await database.init_beanie_models([User, Post, Comment])
        
        # Create test user
        password_manager = PasswordManager()
        user_data = {
            'email': 'regression@test.com',
            'user_handle': 'regressionuser',
            'password_hash': password_manager.hash_password('test123'),
            'name': 'Regression User'
        }
        user = User(**user_data)
        await user.insert()
        
        # Verify user is stored in correct collection
        mongo_collection = database.database[settings.users_collection]
        user_doc = await mongo_collection.find_one({'_id': user.id})
        assert user_doc is not None
        assert user_doc['email'] == 'regression@test.com'
        
        # Create test post
        post_data = {
            'title': 'Regression Test Post',
            'content': 'Testing dynamic collections',
            'slug': 'regression-test-post',
            'author_id': str(user.id),
            'service': 'community',
            'metadata': {'type': 'test'}
        }
        post = Post(**post_data)
        await post.insert()
        
        # Verify post is stored in correct collection
        post_collection = database.database[settings.posts_collection]
        post_doc = await post_collection.find_one({'_id': post.id})
        assert post_doc is not None
        assert post_doc['title'] == 'Regression Test Post'
        
        # Cleanup
        await user.delete()
        await post.delete()
        await database.disconnect()
    
    async def test_collection_names_in_database(self):
        """Test that collections are created with correct dynamic names."""
        await database.connect()
        await database.init_beanie_models([User, Post, Comment, FileRecord])
        
        # Create one document in each collection to ensure they exist
        password_manager = PasswordManager()
        
        # User
        user = User(
            email='collection@test.com',
            user_handle='collectiontest',
            password_hash=password_manager.hash_password('test123'),
            name='Collection Test'
        )
        await user.insert()
        
        # Post
        post = Post(
            title='Collection Test',
            content='Testing collection names',
            slug='collection-test',
            author_id=str(user.id),
            service='community',
            metadata={'type': 'test'}
        )
        await post.insert()
        
        # Get all collection names
        collections = await database.database.list_collection_names()
        
        # Verify dynamic collection names exist
        assert settings.users_collection in collections  # "members"
        assert settings.posts_collection in collections  # "articles"
        
        # Cleanup
        await user.delete()
        await post.delete()
        await database.disconnect()


class TestRegressionCompatibility:
    """Test that changes don't break existing functionality."""
    
    def test_settings_backwards_compatibility(self):
        """Test that all required settings still exist."""
        required_settings = [
            'mongodb_url', 'database_name', 'secret_key', 'algorithm',
            'access_token_expire_minutes', 'api_title', 'api_version',
            'api_description', 'cors_origins', 'environment'
        ]
        
        for setting_name in required_settings:
            assert hasattr(settings, setting_name), f"Missing setting: {setting_name}"
            assert getattr(settings, setting_name) is not None, f"None value for: {setting_name}"
    
    def test_model_structure_preserved(self):
        """Test that model structures are preserved."""
        # User model should still have all required fields
        user_fields = User.model_fields.keys()
        required_user_fields = ['email', 'user_handle', 'password_hash']
        for field in required_user_fields:
            assert field in user_fields
        
        # Post model should still have all required fields
        post_fields = Post.model_fields.keys()
        required_post_fields = ['title', 'content', 'slug', 'author_id', 'service']
        for field in required_post_fields:
            assert field in post_fields
    
    @pytest.mark.asyncio
    async def test_database_operations_still_work(self):
        """Test that basic database operations still function."""
        await database.connect()
        await database.init_beanie_models([User])
        
        # Test basic operations
        password_manager = PasswordManager()
        user = User(
            email='compatibility@test.com',
            user_handle='compattest',
            password_hash=password_manager.hash_password('test123'),
            name='Compatibility Test'
        )
        
        # Create
        await user.insert()
        assert user.id is not None
        
        # Read
        found_user = await User.get(user.id)
        assert found_user is not None
        assert found_user.email == 'compatibility@test.com'
        
        # Update
        found_user.name = 'Updated Name'
        await found_user.save()
        
        # Verify update
        updated_user = await User.get(user.id)
        assert updated_user.name == 'Updated Name'
        
        # Delete
        await updated_user.delete()
        
        # Verify deletion
        deleted_user = await User.get(user.id)
        assert deleted_user is None
        
        await database.disconnect()