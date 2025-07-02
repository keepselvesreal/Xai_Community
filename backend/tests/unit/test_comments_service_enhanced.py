"""Enhanced unit tests for comments service functionality.

## 📋 모듈 목차

### 🎯 역할 및 기능
- **역할**: CommentsService 비즈니스 로직 검증
- **범위**: 댓글 CRUD, 답글 계층, 금기어 필터링
- **Epic**: 콘텐츠 관리 시스템 > 댓글 시스템

### 🔗 관련 모듈
- **상위 도메인**: `test_comments_router.py` (API 통합)
- **하위 의존성**: `test_comment_repository.py` (Repository)
- **연관 서비스**: `test_posts_service.py` (포스트 연결)
- **유틸리티**: `test_permissions.py` (권한 검사)

### 🔄 함수 관계
```
create_comment() → validate_post() → check_depth() → save_comment()
get_comments() → build_tree() → apply_user_data() → filter_content()
update_comment() → check_permission() → validate_content() → save_changes()
```

### 🎭 Mock 사용 정책
- **✅ 실제 구현**: CommentsService (비즈니스 로직 검증)
- **🚨 Mock 사용**: CommentRepository, PostRepository (DB 호출 비용)
- **🔄 대안 검토**: 실제 DB 사용 시 테스트 불안정성

🎯 테스트 전략: Mock 사용 기준에 따른 실제 구현 검증
- Service 계층: 실제 CommentsService 인스턴스 사용 (비즈니스 로직 검증)
- Repository 계층: Mock 사용 (🚨 DB 호출 비용 높음)
- 실제 구현 우선 검증 후 Mock 적용
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from nadle_backend.models.core import User, Post, Comment, CommentCreate, CommentDetail
from nadle_backend.services.comments_service import CommentsService
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.exceptions.comment import CommentNotFoundError, CommentPermissionError, CommentDepthExceededError
from nadle_backend.exceptions.post import PostNotFoundError


class TestCommentsServiceEnhanced:
    """Enhanced test comments service functionality."""
    
    @pytest.fixture
    def mock_comment_repository(self):
        """Create mock comment repository."""
        repo = Mock(spec=CommentRepository)
        return repo
    
    @pytest.fixture
    def mock_post_repository(self):
        """Create mock post repository."""
        repo = Mock(spec=PostRepository)
        return repo
    
    @pytest.fixture
    def comments_service(self, mock_comment_repository, mock_post_repository):
        """Create comments service instance.
        
        🚨 Mock 사용 이유: Repository 계층 (DB 호출 비용 높음)
        ✅ 실제 구현 검증: CommentsService 비즈니스 로직 직접 테스트
        🔄 대안 검토: 실제 DB 사용 시 테스트 불안정성
        """
        return CommentsService(
            comment_repo=mock_comment_repository,
            post_repo=mock_post_repository
        )
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        user = Mock(spec=User)
        user.id = "user123"
        user.email = "test@example.com"
        user.user_handle = "testuser"
        user.is_admin = False
        return user
    
    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        user = Mock(spec=User)
        user.id = "admin123"
        user.email = "admin@example.com"
        user.user_handle = "adminuser"
        user.is_admin = True
        return user
    
    @pytest.fixture
    def sample_post(self):
        """Create sample post."""
        post = Mock(spec=Post)
        post.id = "post123"
        post.title = "Test Post"
        post.slug = "test-post"
        post.author_id = "user123"
        post.status = "published"
        return post
    
    @pytest.fixture
    def sample_comment(self):
        """Create sample comment."""
        comment = Mock(spec=Comment)
        comment.id = "comment123"
        comment.content = "Test comment"
        comment.author_id = "user123"
        comment.parent_id = "post123"
        comment.parent_comment_id = None
        comment.status = "active"
        comment.created_at = datetime.utcnow()
        comment.updated_at = datetime.utcnow()
        return comment
    
    @pytest.fixture
    def sample_comment_data(self):
        """Create sample comment creation data."""
        return CommentCreate(
            content="This is a test comment",
            parent_comment_id=None
        )
    
    @pytest.mark.asyncio
    async def test_create_comment_success(self, comments_service, mock_comment_repository, 
                                        mock_post_repository, sample_comment_data, sample_user, sample_post):
        """Test successful comment creation.
        
        ## 📝 함수 설명
        댓글 생성 성공 시나리오를 검증합니다.
        CommentsService의 create_comment 메서드가 올바른 비즈니스 로직으로 동작하는지 확인합니다.
        
        ## 🤝 테스트 분류
        **Sociable Unit Test** - Repository Mock들과 상호작용
        
        ## 🔄 테스트 전후 상태
        - **사전 조건**: 유효한 CommentCreate 데이터, 인증된 사용자, 존재하는 포스트
        - **실행 작업**: CommentsService.create_comment() 호출
        - **사후 조건**: CommentDetail 객체 반환, Repository.create() 호출 확인
        
        🎯 테스트 전략: 실제 CommentsService 비즈니스 로직 검증
        🔑 우선순위: 🔵 필수 (MVP) - 핵심 기능
        🎓 난이도: 🟢 초급 - 단순 비즈니스 로직
        ⚡ 실행 그룹: 병렬 가능
        """
        # Arrange - Pydantic 모델 검증을 위한 실제 값 사용
        post_slug = "test-post"
        mock_post_repository.get_by_slug.return_value = sample_post
        
        # 실제 Service 동작 검증을 위해 Mock 객체 사용 (Repository 응답)
        mock_comment = Mock()
        mock_comment.id = "comment123"
        mock_comment.author_id = "user123"
        mock_comment.post_id = "post123"
        mock_comment.content = "Test comment"
        mock_comment.parent_comment_id = None
        mock_comment.status = "active"
        mock_comment.like_count = 0
        mock_comment.dislike_count = 0
        mock_comment.reply_count = 0
        from datetime import datetime
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()
        mock_comment_repository.create.return_value = mock_comment
        
        # Act
        result = await comments_service.create_comment(post_slug, sample_comment_data, sample_user)
        
        # Assert - 실제 CommentsService 비즈니스 로직 검증
        assert result is not None
        assert hasattr(result, 'id')
        assert hasattr(result, 'content')
        mock_post_repository.get_by_slug.assert_called_once_with(post_slug)
        mock_comment_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_comment_post_not_found(self, comments_service, mock_post_repository, 
                                                sample_comment_data, sample_user):
        """Test comment creation when post not found."""
        # Arrange
        post_slug = "non-existent-post"
        mock_post_repository.get_by_slug.side_effect = PostNotFoundError(slug=post_slug)
        
        # Act & Assert
        with pytest.raises(PostNotFoundError):
            await comments_service.create_comment(post_slug, sample_comment_data, sample_user)
    
    @pytest.mark.asyncio
    async def test_create_reply_comment(self, comments_service, mock_comment_repository,
                                      mock_post_repository, sample_user, sample_post):
        """Test creating a reply comment."""
        # Arrange
        post_slug = "test-post"
        parent_comment_id = "parent_comment_123"
        comment_data = CommentCreate(
            content="This is a reply",
            parent_comment_id=parent_comment_id
        )
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_comment = Mock()
        mock_comment_repository.create.return_value = mock_comment
        
        # Act
        result = await comments_service.create_comment(post_slug, comment_data, sample_user)
        
        # Assert
        assert result == mock_comment
        mock_comment_repository.create.assert_called_once_with(
            comment_data, str(sample_user.id), str(sample_post.id)
        )
    
    @pytest.mark.asyncio
    async def test_create_comment_depth_exceeded(self, comments_service, mock_comment_repository,
                                               mock_post_repository, sample_user, sample_post):
        """Test comment creation with depth exceeded."""
        # Arrange
        post_slug = "test-post"
        comment_data = CommentCreate(
            content="Deep reply",
            parent_comment_id="deep_comment_id"
        )
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_comment_repository.create.side_effect = CommentDepthExceededError(max_depth=3)
        
        # Act & Assert
        with pytest.raises(CommentDepthExceededError):
            await comments_service.create_comment(post_slug, comment_data, sample_user)
    
    @pytest.mark.asyncio
    async def test_get_comment_success(self, comments_service, mock_comment_repository, sample_comment):
        """Test successful comment retrieval."""
        # Arrange
        comment_id = "comment123"
        mock_comment_repository.get_by_id.return_value = sample_comment
        
        # Act
        result = await comments_service.get_comment(comment_id)
        
        # Assert
        assert result == sample_comment
        mock_comment_repository.get_by_id.assert_called_once_with(comment_id)
    
    @pytest.mark.asyncio
    async def test_get_comment_not_found(self, comments_service, mock_comment_repository):
        """Test comment retrieval when comment not found."""
        # Arrange
        comment_id = "non_existent_comment"
        mock_comment_repository.get_by_id.side_effect = CommentNotFoundError(comment_id=comment_id)
        
        # Act & Assert
        with pytest.raises(CommentNotFoundError):
            await comments_service.get_comment(comment_id)
    
    @pytest.mark.asyncio
    async def test_update_comment_success(self, comments_service, mock_comment_repository, 
                                        sample_comment, sample_user):
        """Test successful comment update."""
        # Arrange
        comment_id = "comment123"
        new_content = "Updated comment content"
        mock_comment_repository.get_by_id.return_value = sample_comment
        mock_comment_repository.update.return_value = sample_comment
        
        with patch('src.utils.permissions.check_comment_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Act
            result = await comments_service.update_comment(comment_id, new_content, sample_user)
            
            # Assert
            assert result == sample_comment
            mock_comment_repository.get_by_id.assert_called_once_with(comment_id)
            mock_comment_repository.update.assert_called_once_with(comment_id, new_content)
    
    @pytest.mark.asyncio
    async def test_update_comment_permission_denied(self, comments_service, mock_comment_repository, 
                                                  sample_comment, sample_user):
        """Test comment update with permission denied."""
        # Arrange
        comment_id = "comment123"
        new_content = "Updated content"
        sample_comment.author_id = "other_user_id"
        mock_comment_repository.get_by_id.return_value = sample_comment
        
        with patch('src.utils.permissions.check_comment_permission') as mock_permission:
            mock_permission.side_effect = CommentPermissionError("Permission denied")
            
            # Act & Assert
            with pytest.raises(CommentPermissionError):
                await comments_service.update_comment(comment_id, new_content, sample_user)
    
    @pytest.mark.asyncio
    async def test_delete_comment_success(self, comments_service, mock_comment_repository, 
                                        sample_comment, sample_user):
        """Test successful comment deletion."""
        # Arrange
        comment_id = "comment123"
        mock_comment_repository.get_by_id.return_value = sample_comment
        mock_comment_repository.delete.return_value = True
        
        with patch('src.utils.permissions.check_comment_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Act
            result = await comments_service.delete_comment(comment_id, sample_user)
            
            # Assert
            assert result is True
            mock_comment_repository.get_by_id.assert_called_once_with(comment_id)
            mock_comment_repository.delete.assert_called_once_with(comment_id)
    
    @pytest.mark.asyncio
    async def test_delete_comment_admin_permission(self, comments_service, mock_comment_repository, 
                                                  sample_comment, admin_user):
        """Test comment deletion by admin user."""
        # Arrange
        comment_id = "comment123"
        sample_comment.author_id = "other_user_id"
        mock_comment_repository.get_by_id.return_value = sample_comment
        mock_comment_repository.delete.return_value = True
        
        with patch('src.utils.permissions.check_comment_permission') as mock_permission:
            mock_permission.return_value = True  # Admin can delete any comment
            
            # Act
            result = await comments_service.delete_comment(comment_id, admin_user)
            
            # Assert
            assert result is True
            mock_comment_repository.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_comments_with_user_data(self, comments_service, mock_comment_repository,
                                             mock_post_repository, sample_post, sample_user):
        """Test getting comments with user data."""
        # Arrange
        post_slug = "test-post"
        page = 1
        page_size = 10
        sort_by = "created_at"
        
        mock_post_repository.get_by_slug.return_value = sample_post
        
        comments_with_replies = [
            {
                "id": "comment123",
                "content": "Test comment",
                "author_id": "user123",
                "replies": []
            }
        ]
        total_count = 1
        
        mock_comment_repository.get_comments_with_replies.return_value = (comments_with_replies, total_count)
        
        # Act
        result, total = await comments_service.get_comments_with_user_data(
            post_slug, page, page_size, sort_by, sample_user
        )
        
        # Assert
        assert len(result) == 1
        assert total == total_count
        mock_post_repository.get_by_slug.assert_called_once_with(post_slug)
        mock_comment_repository.get_comments_with_replies.assert_called_once_with(
            post_id=str(sample_post.id),
            page=page,
            page_size=page_size,
            status="active"
        )
    
    @pytest.mark.asyncio
    async def test_get_comments_without_user(self, comments_service, mock_comment_repository,
                                           mock_post_repository, sample_post):
        """Test getting comments without authenticated user."""
        # Arrange
        post_slug = "test-post"
        
        mock_post_repository.get_by_slug.return_value = sample_post
        
        comments_with_replies = [
            {
                "id": "comment123",
                "content": "Test comment",
                "author_id": "user123",
                "replies": []
            }
        ]
        total_count = 1
        
        mock_comment_repository.get_comments_with_replies.return_value = (comments_with_replies, total_count)
        
        # Act
        result, total = await comments_service.get_comments_with_user_data(
            post_slug, page=1, page_size=10, sort_by="created_at", current_user=None
        )
        
        # Assert
        assert len(result) == 1
        assert total == total_count
        mock_comment_repository.get_comments_with_replies.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_comments_by_user(self, comments_service, mock_comment_repository, sample_user):
        """Test listing comments by specific user."""
        # Arrange
        user_id = str(sample_user.id)
        page = 1
        page_size = 20
        
        comments = [Mock(id="comment1"), Mock(id="comment2")]
        total = 2
        mock_comment_repository.list_by_author.return_value = (comments, total)
        
        # Act
        result = await comments_service.list_comments_by_user(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        
        # Assert
        assert result["total"] == total
        assert len(result["items"]) == 2
        mock_comment_repository.list_by_author.assert_called_once_with(
            author_id=user_id,
            page=page,
            page_size=page_size,
            status="active"
        )
    
    # 🆕 TDD: 문의/후기 기능 테스트 추가
    @pytest.mark.asyncio
    async def test_create_service_inquiry_with_metadata(self, comments_service, mock_comment_repository, 
                                                       mock_post_repository, sample_user, sample_post):
        """Test creating service inquiry with metadata."""
        # Arrange
        post_slug = "test-service-post"
        sample_post.title = "이사 서비스"  # 서비스 제목
        comment_data = CommentCreate(
            content="이사 비용 문의드립니다",
            metadata={"subtype": "service_inquiry"}
        )
        
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_comment = Mock()
        mock_comment.id = "inquiry123"
        mock_comment.author_id = "user123"
        mock_comment.content = "이사 비용 문의드립니다"
        mock_comment.parent_comment_id = None
        mock_comment.status = "active"
        mock_comment.like_count = 0
        mock_comment.dislike_count = 0
        mock_comment.reply_count = 0
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()
        mock_comment.metadata = {
            "subtype": "service_inquiry",
            "post_title": "이사 서비스"
        }
        mock_comment_repository.create.return_value = mock_comment
        
        # Act
        result = await comments_service.create_comment(post_slug, comment_data, sample_user)
        
        # Assert
        assert result is not None
        mock_post_repository.get_by_slug.assert_called_once_with(post_slug)
        mock_comment_repository.create.assert_called_once()
        
        # metadata에 post_title이 추가되었는지 확인
        # 키워드 인수로 호출되므로 call_kwargs 확인
        call_args, call_kwargs = mock_comment_repository.create.call_args
        created_comment_data = call_kwargs.get("comment_data")
        assert created_comment_data is not None
        assert created_comment_data.metadata.get("post_title") == "이사 서비스"
    
    @pytest.mark.asyncio
    async def test_create_service_review_with_metadata(self, comments_service, mock_comment_repository, 
                                                      mock_post_repository, sample_user, sample_post):
        """Test creating service review with metadata."""
        # Arrange
        post_slug = "test-service-post"
        sample_post.title = "청소 서비스"  # 서비스 제목
        comment_data = CommentCreate(
            content="서비스 정말 만족합니다!",
            metadata={"subtype": "service_review"}
        )
        
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_comment = Mock()
        mock_comment.id = "review123"
        mock_comment.author_id = "user123"
        mock_comment.content = "서비스 정말 만족합니다!"
        mock_comment.parent_comment_id = None
        mock_comment.status = "active"
        mock_comment.like_count = 0
        mock_comment.dislike_count = 0
        mock_comment.reply_count = 0
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()
        mock_comment.metadata = {
            "subtype": "service_review",
            "post_title": "청소 서비스"
        }
        mock_comment_repository.create.return_value = mock_comment
        
        # Act
        result = await comments_service.create_comment(post_slug, comment_data, sample_user)
        
        # Assert
        assert result is not None
        mock_post_repository.get_by_slug.assert_called_once_with(post_slug)
        mock_comment_repository.create.assert_called_once()
        
        # metadata에 post_title이 추가되었는지 확인
        call_args, call_kwargs = mock_comment_repository.create.call_args
        created_comment_data = call_kwargs.get("comment_data")
        assert created_comment_data is not None
        assert created_comment_data.metadata.get("post_title") == "청소 서비스"
    
    @pytest.mark.asyncio
    async def test_metadata_post_title_auto_addition(self, comments_service, mock_comment_repository, 
                                                    mock_post_repository, sample_user, sample_post):
        """Test automatic post_title addition when subtype exists in metadata."""
        # Arrange
        post_slug = "test-post"
        sample_post.title = "테스트 포스트"
        comment_data = CommentCreate(
            content="일반 댓글",
            metadata={}  # subtype 없음
        )
        
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_comment = Mock()
        mock_comment.id = "comment123"
        mock_comment.author_id = "user123"
        mock_comment.content = "일반 댓글"
        mock_comment.parent_comment_id = None
        mock_comment.status = "active"
        mock_comment.like_count = 0
        mock_comment.dislike_count = 0
        mock_comment.reply_count = 0
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()
        mock_comment_repository.create.return_value = mock_comment
        
        # Act
        await comments_service.create_comment(post_slug, comment_data, sample_user)
        
        # Assert
        call_args, call_kwargs = mock_comment_repository.create.call_args
        created_comment_data = call_kwargs.get("comment_data")
        assert created_comment_data is not None
        # subtype이 없으면 post_title도 추가되지 않아야 함
        assert "post_title" not in created_comment_data.metadata
    
    @pytest.mark.asyncio
    async def test_regular_comment_without_metadata_modification(self, comments_service, mock_comment_repository, 
                                                               mock_post_repository, sample_user, sample_post):
        """Test regular comment creation without metadata modification."""
        # Arrange
        post_slug = "test-post"
        sample_post.title = "테스트 포스트"
        comment_data = CommentCreate(
            content="일반 댓글입니다",
            metadata=None  # metadata 없음
        )
        
        mock_post_repository.get_by_slug.return_value = sample_post
        mock_comment = Mock()
        mock_comment.id = "comment123"
        mock_comment.author_id = "user123"
        mock_comment.content = "일반 댓글입니다"
        mock_comment.parent_comment_id = None
        mock_comment.status = "active"
        mock_comment.like_count = 0
        mock_comment.dislike_count = 0
        mock_comment.reply_count = 0
        mock_comment.created_at = datetime.utcnow()
        mock_comment.updated_at = datetime.utcnow()
        mock_comment_repository.create.return_value = mock_comment
        
        # Act
        await comments_service.create_comment(post_slug, comment_data, sample_user)
        
        # Assert
        call_args, call_kwargs = mock_comment_repository.create.call_args
        created_comment_data = call_kwargs.get("comment_data")
        assert created_comment_data is not None
        # metadata가 None이면 수정하지 않아야 함
        assert created_comment_data.metadata is None