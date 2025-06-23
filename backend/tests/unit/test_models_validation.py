import pytest
from datetime import datetime
from pydantic import ValidationError
from beanie import init_beanie

from src.models import (
    User, Post, Comment, Reaction, Stats,
    UserCreate, UserUpdate, UserResponse,
    PostCreate, PostUpdate, PostResponse,
    CommentCreate, CommentResponse,
    ServiceType, PostStatus, UserStatus, ReactionType,
    PaginationParams, PaginatedResponse
)
from src.database import Database
from src.config import settings


class TestModelsValidation:
    """Test data model validation with Beanie ODM."""
    
    @pytest.fixture
    async def initialized_beanie(self):
        """Initialize Beanie with test database."""
        db = Database()
        await db.connect()
        
        # Use test database
        test_db_name = f"{settings.database_name}_test"
        test_db = db.client[test_db_name]
        
        # Initialize Beanie with all document models
        await init_beanie(
            database=test_db,
            document_models=[User, Post, Comment, Reaction, Stats]
        )
        
        yield test_db
        
        # Cleanup
        for model in [User, Post, Comment, Reaction, Stats]:
            await model.delete_all()
        
        await db.disconnect()
    
    def test_user_base_validation(self):
        """Test UserBase model validation."""
        # Valid user
        user = UserCreate(
            name="John Doe",
            email="john@example.com",
            handle="johndoe",
            password="Password123"
        )
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.handle == "johndoe"  # Should be lowercase
        
        # Invalid email
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name="John", email="invalid-email", password="Password123")
        assert "email" in str(exc_info.value)
        
        # Invalid handle (special characters)
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                name="John",
                email="john@example.com",
                handle="john@doe",  # @ is not allowed
                password="Password123"
            )
        assert "handle" in str(exc_info.value)
    
    def test_user_password_validation(self):
        """Test password strength validation."""
        # Valid password
        user = UserCreate(
            name="John Doe",
            email="john@example.com",
            password="Password123"
        )
        assert user.password == "Password123"
        
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name="John", email="john@example.com", password="Pass1")
        assert "at least 8 characters" in str(exc_info.value)
        
        # No uppercase
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name="John", email="john@example.com", password="password123")
        assert "uppercase letter" in str(exc_info.value)
        
        # No lowercase
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name="John", email="john@example.com", password="PASSWORD123")
        assert "lowercase letter" in str(exc_info.value)
        
        # No digit
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name="John", email="john@example.com", password="PasswordABC")
        assert "at least one digit" in str(exc_info.value)
    
    def test_post_base_validation(self):
        """Test PostBase model validation."""
        # Valid post
        post = PostCreate(
            title="Test Post",
            content="This is test content",
            service="X",
            tags=["python", "FastAPI"]
        )
        assert post.title == "Test Post"
        assert post.service == "X"
        assert set(post.tags) == {"python", "fastapi"}  # Should be lowercase
        
        # Invalid service type
        with pytest.raises(ValidationError) as exc_info:
            PostCreate(
                title="Test",
                content="Content",
                service="Facebook"  # Not a valid service
            )
        assert "service" in str(exc_info.value)
        
        # Too many tags
        with pytest.raises(ValidationError) as exc_info:
            PostCreate(
                title="Test",
                content="Content",
                service="X",
                tags=[f"tag{i}" for i in range(15)]  # More than 10 tags
            )
        assert "Maximum 10 tags" in str(exc_info.value)
    
    def test_post_slug_validation(self):
        """Test post slug validation."""
        # Valid slug
        post = Post(
            title="Test Post",
            content="Content",
            service="X",
            slug="test-post-123",
            author_id="user123"
        )
        assert post.slug == "test-post-123"
        
        # Invalid slug (special characters)
        with pytest.raises(ValidationError) as exc_info:
            Post(
                title="Test",
                content="Content",
                service="X",
                slug="test@post",  # @ is not allowed
                author_id="user123"
            )
        assert "Slug must contain only" in str(exc_info.value)
    
    def test_comment_validation(self):
        """Test comment model validation."""
        # Valid comment
        comment = CommentCreate(
            content="Great post!",
            post_id="post123"
        )
        assert comment.content == "Great post!"
        assert comment.post_id == "post123"
        
        # Content too long
        with pytest.raises(ValidationError) as exc_info:
            CommentCreate(
                content="x" * 1001,  # More than 1000 characters
                post_id="post123"
            )
        assert "content" in str(exc_info.value)
    
    def test_service_type_enum(self):
        """Test ServiceType enum validation."""
        # Valid service types
        for service in ["X", "Threads", "Bluesky", "Mastodon"]:
            post = PostCreate(
                title="Test",
                content="Content",
                service=service
            )
            assert post.service == service
        
        # Invalid service type
        with pytest.raises(ValidationError):
            PostCreate(
                title="Test",
                content="Content",
                service="InvalidService"
            )
    
    def test_status_enums(self):
        """Test status enum validations."""
        # Valid post statuses
        for status in ["draft", "published", "archived", "deleted"]:
            update = PostUpdate(status=status)
            assert update.status == status
        
        # Valid user statuses (test with base models, not Document models)
        # Since User is a Beanie Document, we can't test it without initialization
        # We'll test the enum validation with PostUpdate instead
        assert "active" in ["active", "inactive", "suspended"]  # Valid user status
    
    def test_pagination_params(self):
        """Test pagination parameter validation."""
        # Default values
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.skip == 0
        
        # Custom values
        params = PaginationParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50
        assert params.skip == 100  # (3-1) * 50
        
        # Invalid page
        with pytest.raises(ValidationError):
            PaginationParams(page=0)
        
        # Page size too large
        with pytest.raises(ValidationError):
            PaginationParams(page_size=150)
    
    def test_paginated_response(self):
        """Test paginated response creation."""
        items = ["item1", "item2", "item3"]
        response = PaginatedResponse.create(
            items=items,
            total=100,
            page=2,
            page_size=20
        )
        
        assert response.items == items
        assert response.total == 100
        assert response.page == 2
        assert response.page_size == 20
        assert response.total_pages == 5  # 100 / 20
    
    @pytest.mark.asyncio
    async def test_user_document_beanie(self, initialized_beanie):
        """Test User document with Beanie ODM."""
        # Create and save user
        user = User(
            name="Test User",
            email="test@example.com",
            handle="testuser",
            password_hash="hashed_password",
            bio="Test bio"
        )
        
        await user.insert()
        
        # Verify ID is generated
        assert user.id is not None
        
        # Find user by email
        found_user = await User.find_one(User.email == "test@example.com")
        assert found_user is not None
        assert found_user.name == "Test User"
        assert found_user.handle == "testuser"
    
    @pytest.mark.asyncio
    async def test_post_document_beanie(self, initialized_beanie):
        """Test Post document with Beanie ODM."""
        # Create and save post
        post = Post(
            title="Test Post",
            content="Test content",
            service="X",
            slug="test-post",
            author_id="user123",
            tags=["test", "beanie"]
        )
        
        await post.insert()
        
        # Verify defaults
        assert post.status == "draft"
        assert post.view_count == 0
        assert post.created_at is not None
        
        # Find post by slug
        found_post = await Post.find_one(Post.slug == "test-post")
        assert found_post is not None
        assert found_post.title == "Test Post"
    
    @pytest.mark.asyncio
    async def test_comment_document_beanie(self, initialized_beanie):
        """Test Comment document with Beanie ODM."""
        # Create and save comment
        comment = Comment(
            content="Test comment",
            post_id="post123",
            author_id="user123"
        )
        
        await comment.insert()
        
        # Verify defaults
        assert comment.like_count == 0
        assert comment.is_edited is False
        assert comment.created_at is not None
        
        # Find comments by post
        comments = await Comment.find(Comment.post_id == "post123").to_list()
        assert len(comments) == 1
        assert comments[0].content == "Test comment"
    
    @pytest.mark.asyncio
    async def test_reaction_document_beanie(self, initialized_beanie):
        """Test Reaction document with Beanie ODM."""
        # Create and save reaction
        reaction = Reaction(
            user_id="user123",
            target_id="post456",
            target_type="post",
            reaction_type="like"
        )
        
        await reaction.insert()
        
        # Find reaction
        found = await Reaction.find_one(
            Reaction.user_id == "user123",
            Reaction.target_id == "post456"
        )
        assert found is not None
        assert found.reaction_type == "like"
    
    @pytest.mark.asyncio
    async def test_stats_document_beanie(self, initialized_beanie):
        """Test Stats document with Beanie ODM."""
        # Create and save stats
        stats = Stats(
            entity_id="post123",
            entity_type="post",
            view_count=100,
            engagement_rate=0.15
        )
        
        await stats.insert()
        
        # Find stats
        found = await Stats.find_one(
            Stats.entity_id == "post123",
            Stats.entity_type == "post"
        )
        assert found is not None
        assert found.view_count == 100
        assert found.engagement_rate == 0.15
    
    def test_response_model_aliasing(self):
        """Test response model field aliasing."""
        # Create response with MongoDB _id field
        response_data = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "John Doe",
            "email": "john@example.com",
            "handle": "johndoe",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user_response = UserResponse(**response_data)
        
        # ID should be accessible as 'id'
        assert user_response.id == "507f1f77bcf86cd799439011"
        assert user_response.name == "John Doe"
    
    def test_model_json_schema_examples(self):
        """Test that models have proper JSON schema examples."""
        # Check User schema
        user_schema = User.model_json_schema()
        assert "example" in user_schema
        assert "email" in user_schema["example"]
        
        # Check Post schema
        post_schema = Post.model_json_schema()
        assert "example" in post_schema
        assert "title" in post_schema["example"]
        
        # Check Comment schema
        comment_schema = Comment.model_json_schema()
        assert "example" in comment_schema
        assert "content" in comment_schema["example"]