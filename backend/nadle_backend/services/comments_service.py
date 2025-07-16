"""Comments service for business logic layer."""

from typing import List, Dict, Optional, Tuple, Any
from nadle_backend.models.core import Comment, CommentCreate, CommentDetail, User, UserReaction
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.exceptions.comment import CommentNotFoundError, CommentPermissionError, CommentValidationError
from nadle_backend.exceptions.post import PostNotFoundError
from nadle_backend.services.user_activity_service import normalize_post_type
from beanie import PydanticObjectId


class CommentsService:
    """Service for comment business logic."""
    
    def __init__(self, comment_repo: CommentRepository, post_repo: PostRepository):
        self.comment_repo = comment_repo
        self.post_repo = post_repo
    
    async def create_comment(
        self, 
        post_slug: str, 
        comment_data: CommentCreate, 
        current_user: User
    ) -> CommentDetail:
        """Create a new comment with authentication.
        
        Args:
            post_slug: Post slug
            comment_data: Comment creation data
            current_user: Authenticated user
            
        Returns:
            Created comment detail
            
        Raises:
            PostNotFoundError: If post not found
            CommentValidationError: If validation fails
        """
        # Validate comment content
        self._validate_comment_content(comment_data.content)
        
        # Get post by slug to get post ID
        post = await self.post_repo.get_by_slug(post_slug)
        
        # 🆕 metadata 처리: 모든 댓글에 post_title과 라우팅 정보 자동 추가
        if not comment_data.metadata:
            comment_data.metadata = {}
        comment_data.metadata["post_title"] = post.title
        
        # 라우팅 정보 추가
        original_type = getattr(post.metadata, "type", "board") if post.metadata else "board"
        normalized_type = normalize_post_type(original_type) or "board"
        comment_data.metadata["route_path"] = self._generate_route_path(normalized_type, post.slug)
        
        # Create comment
        comment = await self.comment_repo.create(
            comment_data=comment_data,
            author_id=str(current_user.id),
            parent_id=str(post.id)
        )
        
        # Increment post comment count
        await self._increment_post_comment_count(str(post.id))
        
        # 🚀 댓글 작성 후 캐시 무효화
        await self._invalidate_comments_cache(post_slug)
        print(f"🔄 댓글 작성 후 캐시 무효화 완료 - {post_slug}")
        
        # Convert to response format
        comment_detail = await self._convert_to_comment_detail(comment)
        return comment_detail
    
    async def get_comments_with_user_data(
        self,
        post_slug: str,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        current_user: Optional[User] = None
    ) -> Tuple[List[CommentDetail], int]:
        """Get comments for a post with user data and reactions.
        
        Args:
            post_slug: Post slug
            page: Page number
            page_size: Number of items per page
            sort_by: Sort field
            current_user: Current authenticated user (optional)
            
        Returns:
            Tuple of (comment details list, total count)
            
        Raises:
            PostNotFoundError: If post not found
        """
        # Get post by slug to get post ID
        post = await self.post_repo.get_by_slug(post_slug)
        
        # Get comments with replies
        from nadle_backend.config import get_settings
        settings = get_settings()
        comments_with_replies, total = await self.comment_repo.get_comments_with_replies(
            post_id=str(post.id),
            page=page,
            page_size=page_size,
            status="active",
            max_depth=settings.max_comment_depth
        )
        
        # 🔍 디버깅: 댓글 구조 확인
        print(f"🔍 [DEBUG] 댓글 조회 - post_slug: {post_slug}")
        print(f"🔍 [DEBUG] comments_with_replies 수: {len(comments_with_replies)}")
        for i, item in enumerate(comments_with_replies):
            comment = item["comment"]
            replies = item["replies"]
            print(f"🔍 [DEBUG] 댓글 {i+1}: id={comment.id}, content={comment.content[:30]}..., replies={len(replies)}")
            for j, reply_item in enumerate(replies):
                reply_comment = reply_item["comment"]
                print(f"    답글 {j+1}: id={reply_comment.id}, content={reply_comment.content[:30]}...")
        
        # Convert to comment details with user reactions
        comment_details = []
        all_comment_ids = []
        
        # Collect all comment IDs for batch reaction lookup (recursive)
        def collect_comment_ids(item):
            """Recursively collect comment IDs from nested structure."""
            comment = item["comment"]
            replies = item["replies"]
            ids = [str(comment.id)]
            
            for reply_item in replies:
                ids.extend(collect_comment_ids(reply_item))
            
            return ids
        
        for item in comments_with_replies:
            all_comment_ids.extend(collect_comment_ids(item))
        
        # Get user reactions if authenticated
        user_reactions = {}
        if current_user:
            # Get user reactions from UserReaction documents
            reactions = await UserReaction.find({
                "user_id": str(current_user.id),
                "target_type": "comment",
                "target_id": {"$in": all_comment_ids}
            }).to_list()
            
            user_reactions = {
                reaction.target_id: {
                    "liked": reaction.liked,
                    "disliked": reaction.disliked
                }
                for reaction in reactions
            }
        
        # Convert to response format (recursive)
        async def convert_comment_item(item):
            """Recursively convert comment item with nested replies."""
            comment = item["comment"]
            replies = item["replies"]
            
            # Convert nested replies
            reply_details = []
            for reply_item in replies:
                reply_detail = await convert_comment_item(reply_item)
                reply_details.append(reply_detail)
            
            # Convert main comment
            comment_detail = await self._convert_to_comment_detail(
                comment, user_reactions.get(str(comment.id))
            )
            comment_detail.replies = reply_details
            
            return comment_detail
        
        for item in comments_with_replies:
            comment_detail = await convert_comment_item(item)
            comment_details.append(comment_detail)
        
        return comment_details, total
    
    async def create_reply(
        self,
        post_slug: str,
        parent_comment_id: str,
        comment_data: CommentCreate,
        current_user: User
    ) -> CommentDetail:
        """Create a reply to a comment.
        
        Args:
            post_slug: Post slug
            parent_comment_id: Parent comment ID
            comment_data: Comment creation data
            current_user: Authenticated user
            
        Returns:
            Created reply detail
            
        Raises:
            PostNotFoundError: If post not found
            CommentNotFoundError: If parent comment not found
            CommentValidationError: If validation fails
        """
        # Validate comment content
        self._validate_comment_content(comment_data.content)
        
        # Get post by slug
        post = await self.post_repo.get_by_slug(post_slug)
        
        # Verify parent comment exists
        parent_comment = await self.comment_repo.get_by_id(parent_comment_id)
        
        # Set parent_comment_id in comment data
        reply_data = CommentCreate(
            content=comment_data.content,
            parent_comment_id=parent_comment_id
        )
        
        # Create reply
        print(f"🔍 [DEBUG] 답글 생성: parent_comment_id={parent_comment_id}, content={comment_data.content[:30]}...")
        reply = await self.comment_repo.create(
            comment_data=reply_data,
            author_id=str(current_user.id),
            parent_id=str(post.id)
        )
        print(f"🔍 [DEBUG] 답글 생성 완료: reply_id={reply.id}, parent_comment_id={reply.parent_comment_id}")
        
        # Increment parent comment reply count
        await self.comment_repo.increment_reply_count(parent_comment_id)
        
        # Increment post comment count
        await self._increment_post_comment_count(str(post.id))
        
        # 🚀 답글 작성 후 캐시 무효화
        await self._invalidate_comments_cache(post_slug)
        print(f"🔄 답글 작성 후 캐시 무효화 완료 - {post_slug}")
        
        # Convert to response format
        reply_detail = await self._convert_to_comment_detail(reply)
        return reply_detail
    
    async def update_comment_with_permission(
        self,
        comment_id: str,
        content: str,
        current_user: User
    ) -> CommentDetail:
        """Update comment with permission check.
        
        Args:
            comment_id: Comment ID
            content: New content
            current_user: Authenticated user
            
        Returns:
            Updated comment detail
            
        Raises:
            CommentNotFoundError: If comment not found
            CommentPermissionError: If user lacks permission
            CommentValidationError: If validation fails
        """
        # Validate content
        self._validate_comment_content(content)
        
        # Get comment and check permission
        comment = await self.comment_repo.get_by_id(comment_id)
        if not self._check_comment_permission(comment, current_user, "update"):
            raise CommentPermissionError(
                action="update",
                comment_id=comment_id,
                user_id=str(current_user.id)
            )
        
        # Update comment
        updated_comment = await self.comment_repo.update(comment_id, content)
        
        # 🚀 댓글 수정 후 캐시 무효화
        try:
            post = await self.post_repo.get_by_id(str(comment.post_id))
            if post:
                await self._invalidate_comments_cache(post.slug)
                print(f"🔄 댓글 수정 후 캐시 무효화 완료 - {post.slug}")
        except Exception as e:
            print(f"❌ 댓글 수정 후 캐시 무효화 실패: {e}")
        
        # Convert to response format
        comment_detail = await self._convert_to_comment_detail(updated_comment)
        return comment_detail
    
    async def toggle_comment_reaction(
        self,
        comment_id: str,
        reaction_type: str,  # "like" or "dislike"
        current_user: User
    ) -> Dict[str, Any]:
        """Toggle comment reaction (like/dislike) for a user.
        
        Args:
            comment_id: Comment ID
            reaction_type: "like" or "dislike"
            current_user: Authenticated user
            
        Returns:
            Dict with reaction counts and user reaction state
            
        Raises:
            CommentNotFoundError: If comment not found
        """
        # Validate comment exists
        comment = await self.comment_repo.get_by_id(comment_id)
        
        # Find or create user reaction
        user_reaction = await UserReaction.find_one({
            "user_id": str(current_user.id),
            "target_type": "comment",
            "target_id": comment_id
        })
        
        if not user_reaction:
            # Get post information for routing
            post = await self.post_repo.get_by_id(comment.parent_id)
            original_type = getattr(post.metadata, "type", "board") if post.metadata else "board"
            normalized_type = normalize_post_type(original_type) or "board"
            route_path = self._generate_route_path(normalized_type, post.slug)
            
            user_reaction = UserReaction(
                user_id=str(current_user.id),
                target_type="comment",
                target_id=comment_id,
                metadata={
                    "route_path": route_path,
                    "target_title": comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
                }
            )
        
        # Toggle reaction
        if reaction_type == "like":
            # Toggle like, clear dislike if setting like
            was_liked = user_reaction.liked
            user_reaction.liked = not was_liked
            if user_reaction.liked:
                user_reaction.disliked = False
        elif reaction_type == "dislike":
            # Toggle dislike, clear like if setting dislike
            was_disliked = user_reaction.disliked
            user_reaction.disliked = not was_disliked
            if user_reaction.disliked:
                user_reaction.liked = False
        
        # Save user reaction
        await user_reaction.save()
        
        # Update comment aggregate counts
        await self._update_comment_reaction_counts(comment_id)
        
        # Get updated comment for response
        updated_comment = await self.comment_repo.get_by_id(comment_id)
        
        # 🚀 댓글 반응 후 캐시 무효화
        try:
            post = await self.post_repo.get_by_id(str(comment.post_id))
            if post:
                await self._invalidate_comments_cache(post.slug)
                print(f"🔄 댓글 반응 후 캐시 무효화 완료 - {post.slug}")
        except Exception as e:
            print(f"❌ 댓글 반응 후 캐시 무효화 실패: {e}")
        
        return {
            "like_count": updated_comment.like_count,
            "dislike_count": updated_comment.dislike_count,
            "user_reaction": {
                "liked": user_reaction.liked,
                "disliked": user_reaction.disliked
            }
        }
    
    async def delete_comment_with_permission(
        self,
        comment_id: str,
        current_user: User
    ) -> bool:
        """Delete comment with permission check.
        
        Args:
            comment_id: Comment ID
            current_user: Authenticated user
            
        Returns:
            True if successful
            
        Raises:
            CommentNotFoundError: If comment not found
            CommentPermissionError: If user lacks permission
        """
        # Get comment and check permission
        comment = await self.comment_repo.get_by_id(comment_id)
        if not self._check_comment_permission(comment, current_user, "delete"):
            raise CommentPermissionError(
                action="delete",
                comment_id=comment_id,
                user_id=str(current_user.id)
            )
        
        # Get post to decrement comment count
        post = await self.post_repo.get_by_id(comment.parent_id)
        
        # Delete comment (soft delete)
        success = await self.comment_repo.delete(comment_id)
        
        if success:
            # Decrement post comment count
            await self._decrement_post_comment_count(str(post.id))
            
            # 🚀 댓글 삭제 후 캐시 무효화
            try:
                await self._invalidate_comments_cache(post.slug)
                print(f"🔄 댓글 삭제 후 캐시 무효화 완료 - {post.slug}")
            except Exception as e:
                print(f"❌ 댓글 삭제 후 캐시 무효화 실패: {e}")
        
        return success
    
    async def _update_comment_reaction_counts(self, comment_id: str) -> None:
        """Update comment aggregate reaction counts from UserReaction documents.
        
        Args:
            comment_id: Comment ID
        """
        try:
            # Count likes and dislikes for this comment
            like_count = await UserReaction.find({
                "target_type": "comment",
                "target_id": comment_id,
                "liked": True
            }).count()
            
            dislike_count = await UserReaction.find({
                "target_type": "comment",
                "target_id": comment_id,
                "disliked": True
            }).count()
            
            # Update comment document
            await Comment.find_one({"_id": PydanticObjectId(comment_id)}).update(
                {
                    "$set": {
                        "like_count": like_count,
                        "dislike_count": dislike_count
                    }
                }
            )
            
        except Exception as e:
            # Log error but don't fail the reaction update
            print(f"Error updating comment reaction counts: {e}")
            pass
    
    def _validate_comment_content(self, content: str) -> None:
        """Validate comment content.
        
        Args:
            content: Comment content
            
        Raises:
            CommentValidationError: If validation fails
        """
        if not content or not content.strip():
            raise CommentValidationError(field="content", value=content)
        
        if len(content) > 1000:
            raise CommentValidationError(
                field="content", 
                value=content,
                reason="Content exceeds maximum length of 1000 characters"
            )
    
    def _check_comment_permission(self, comment: Comment, user: User, action: str) -> bool:
        """Check if user has permission for comment action.
        
        Args:
            comment: Comment instance
            user: User instance
            action: Action to check (update, delete)
            
        Returns:
            True if user has permission
        """
        # Owner can always update/delete
        if comment.author_id == str(user.id):
            return True
        
        # Admin can always update/delete
        if getattr(user, 'is_admin', False):
            return True
        
        return False
    
    async def _convert_to_comment_detail(
        self, 
        comment: Comment, 
        user_reaction: Optional[Dict[str, bool]] = None
    ) -> CommentDetail:
        """Convert Comment to CommentDetail.
        
        Args:
            comment: Comment instance
            user_reaction: User reaction data
            
        Returns:
            CommentDetail instance
        """
        # Get author information
        author = None
        if comment.author_id:
            try:
                from nadle_backend.models.core import User
                from beanie import PydanticObjectId
                user = await User.get(PydanticObjectId(comment.author_id))
                if user:
                    from nadle_backend.models.core import UserResponse
                    author = UserResponse(
                        id=str(user.id),
                        name=user.name,
                        email=user.email,
                        user_handle=user.user_handle,
                        display_name=user.display_name,
                        bio=user.bio,
                        avatar_url=user.avatar_url,
                        status=user.status,
                        created_at=user.created_at,
                        updated_at=user.updated_at
                    )
            except Exception:
                # If user not found, leave author as None
                pass
        
        return CommentDetail(
            id=str(comment.id),
            author_id=comment.author_id,
            author=author,
            content=comment.content,
            parent_comment_id=comment.parent_comment_id,
            status=comment.status,
            like_count=comment.like_count,
            dislike_count=comment.dislike_count,
            reply_count=comment.reply_count,
            user_reaction=user_reaction,
            metadata=comment.metadata or {},  # 🆕 metadata 필드 추가
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=None  # Will be populated by caller if needed
        )
    
    async def _increment_post_comment_count(self, post_id: str) -> None:
        """Increment comment count for a post.
        
        Args:
            post_id: Post ID
        """
        try:
            # This would typically update the post's comment_count field
            # For now, we'll implement a simple increment operation
            from nadle_backend.models.core import Post
            from beanie import PydanticObjectId
            
            await Post.find_one(Post.id == PydanticObjectId(post_id)).update(
                {"$inc": {"comment_count": 1}}
            )
        except Exception:
            # Log error but don't fail the comment creation
            pass
    
    async def _decrement_post_comment_count(self, post_id: str) -> None:
        """Decrement comment count for a post.
        
        Args:
            post_id: Post ID
        """
        try:
            # This would typically update the post's comment_count field
            from nadle_backend.models.core import Post
            from beanie import PydanticObjectId
            
            await Post.find_one(Post.id == PydanticObjectId(post_id)).update(
                {"$inc": {"comment_count": -1}}
            )
        except Exception:
            # Log error but don't fail the comment deletion
            pass
    
    def _generate_route_path(self, page_type: str, slug: str) -> str:
        """Generate route path based on page type and slug.
        
        Args:
            page_type: Page type (normalized or raw)
            slug: Post slug
            
        Returns:
            Route path string
        """
        # Ensure page type is normalized
        normalized_type = normalize_post_type(page_type) or "board"
        
        route_mapping = {
            "board": f"/board/{slug}",
            "property_information": f"/property-information/{slug}",
            "moving_services": f"/moving-services/{slug}",
            "expert_tips": f"/expert-tips/{slug}"
        }
        
        return route_mapping.get(normalized_type, f"/post/{slug}")
    
    async def _invalidate_comments_cache(self, post_slug: str) -> None:
        """댓글 캐시 무효화
        
        Args:
            post_slug: 게시글 slug
        """
        try:
            from nadle_backend.database.redis_factory import get_redis_manager
            from nadle_backend.database.cache_utils import get_prefixed_key
            
            redis_manager = await get_redis_manager()
            cache_key = get_prefixed_key(f"comments_batch_v2:{post_slug}")
            
            # 캐시 삭제
            await redis_manager.delete(cache_key)
            print(f"🗑️ 댓글 캐시 삭제 완료 - {cache_key}")
            
        except Exception as e:
            print(f"❌ 댓글 캐시 무효화 실패: {e}")
            # 캐시 무효화 실패는 치명적이지 않으므로 예외를 발생시키지 않음