"""Comment repository for data access layer."""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from beanie import PydanticObjectId
from src.models.core import Comment, CommentCreate, CommentDetail, PaginationParams
from src.exceptions.comment import CommentNotFoundError, CommentDepthExceededError


class CommentRepository:
    """Repository for comment data access operations."""
    
    async def create(self, comment_data: CommentCreate, author_id: str, parent_id: str) -> Comment:
        """Create a new comment.
        
        Args:
            comment_data: Comment creation data
            author_id: ID of the comment author
            parent_id: ID of the parent post
            
        Returns:
            Created comment instance
            
        Raises:
            CommentDepthExceededError: If reply depth exceeds limit
        """
        # Check reply depth if this is a reply to another comment
        if comment_data.parent_comment_id:
            await self._validate_reply_depth(comment_data.parent_comment_id)
        
        # Create comment document
        comment = Comment(
            content=comment_data.content,
            parent_type="post",
            parent_id=parent_id,
            parent_comment_id=comment_data.parent_comment_id,
            author_id=author_id,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={}
        )
        
        # Save to database
        await comment.save()
        return comment
    
    async def get_by_id(self, comment_id: str) -> Comment:
        """Get comment by ID.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            Comment instance
            
        Raises:
            CommentNotFoundError: If comment not found
        """
        try:
            comment = await Comment.get(PydanticObjectId(comment_id))
            if comment is None:
                raise CommentNotFoundError(comment_id=comment_id)
            return comment
        except Exception:
            raise CommentNotFoundError(comment_id=comment_id)
    
    async def update(self, comment_id: str, content: str) -> Comment:
        """Update comment content.
        
        Args:
            comment_id: Comment ID
            content: New content
            
        Returns:
            Updated comment instance
            
        Raises:
            CommentNotFoundError: If comment not found
        """
        comment = await self.get_by_id(comment_id)
        
        # Update content and timestamp
        update_dict = {
            "content": content,
            "updated_at": datetime.utcnow()
        }
        
        await comment.update({"$set": update_dict})
        
        # Refresh comment data
        updated_comment = await self.get_by_id(comment_id)
        return updated_comment
    
    async def delete(self, comment_id: str) -> bool:
        """Soft delete comment by setting status to 'deleted'.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            True if deletion successful
            
        Raises:
            CommentNotFoundError: If comment not found
        """
        comment = await self.get_by_id(comment_id)
        
        # Soft delete by updating status
        update_dict = {
            "status": "deleted",
            "updated_at": datetime.utcnow()
        }
        
        await comment.update({"$set": update_dict})
        return True
    
    async def list_by_post(
        self, 
        post_id: str,
        page: int = 1, 
        page_size: int = 20,
        status: str = "active",
        sort_by: str = "created_at"
    ) -> Tuple[List[Comment], int]:
        """List comments for a post with pagination.
        
        Args:
            post_id: Post ID
            page: Page number (1-based)
            page_size: Number of items per page
            status: Filter by status
            sort_by: Sort field
            
        Returns:
            Tuple of (comments list, total count)
        """
        # Build query for top-level comments (no parent_comment_id)
        query = {
            "parent_id": post_id,
            "status": status,
            "parent_comment_id": None  # Only top-level comments
        }
        
        # Count total
        total = await Comment.find(query).count()
        
        # Get comments with pagination
        skip = (page - 1) * page_size
        sort_field = f"-{sort_by}" if sort_by in ["created_at", "updated_at"] else sort_by
        
        comments = await Comment.find(query).sort(sort_field).skip(skip).limit(page_size).to_list()
        
        return comments, total
    
    async def get_replies(self, parent_comment_id: str, status: str = "active") -> List[Comment]:
        """Get replies to a comment.
        
        Args:
            parent_comment_id: Parent comment ID
            status: Filter by status
            
        Returns:
            List of reply comments
        """
        query = {
            "parent_comment_id": parent_comment_id,
            "status": status
        }
        
        replies = await Comment.find(query).sort("created_at").to_list()
        return replies
    
    async def get_comments_with_replies(
        self,
        post_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str = "active"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get comments with their replies in hierarchical structure.
        
        Args:
            post_id: Post ID
            page: Page number
            page_size: Number of items per page
            status: Filter by status
            
        Returns:
            Tuple of (comments with replies, total count)
        """
        # Get top-level comments
        top_comments, total = await self.list_by_post(
            post_id=post_id,
            page=page,
            page_size=page_size,
            status=status
        )
        
        comments_with_replies = []
        
        for comment in top_comments:
            # Get replies for this comment
            replies = await self.get_replies(str(comment.id), status=status)
            
            comment_dict = {
                "comment": comment,
                "replies": replies
            }
            comments_with_replies.append(comment_dict)
        
        return comments_with_replies, total
    
    async def count_by_post(self, post_id: str, status: str = "active") -> int:
        """Count comments for a post.
        
        Args:
            post_id: Post ID
            status: Filter by status
            
        Returns:
            Total comment count
        """
        query = {
            "parent_id": post_id,
            "status": status
        }
        
        return await Comment.find(query).count()
    
    async def increment_reply_count(self, comment_id: str) -> bool:
        """Increment reply count for a parent comment.
        
        Args:
            comment_id: Parent comment ID
            
        Returns:
            True if successful
        """
        try:
            await Comment.find_one(Comment.id == PydanticObjectId(comment_id)).update(
                {"$inc": {"reply_count": 1}}
            )
            return True
        except Exception:
            return False
    
    async def _validate_reply_depth(self, parent_comment_id: str, max_depth: int = 2) -> None:
        """Validate that reply depth doesn't exceed maximum.
        
        Args:
            parent_comment_id: Parent comment ID
            max_depth: Maximum allowed depth
            
        Raises:
            CommentDepthExceededError: If depth exceeds limit
            CommentNotFoundError: If parent comment not found
        """
        current_depth = 1
        current_comment_id = parent_comment_id
        
        while current_comment_id and current_depth < max_depth:
            parent_comment = await self.get_by_id(current_comment_id)
            if parent_comment.parent_comment_id:
                current_depth += 1
                current_comment_id = parent_comment.parent_comment_id
            else:
                break
        
        if current_depth >= max_depth:
            raise CommentDepthExceededError(
                max_depth=max_depth, 
                current_depth=current_depth + 1
            )
    
    async def get_user_reactions(self, user_id: str, comment_ids: List[str]) -> Dict[str, Dict[str, bool]]:
        """Get user reactions for comments.
        
        Args:
            user_id: User ID
            comment_ids: List of comment IDs
            
        Returns:
            Dictionary mapping comment_id to reaction data
        """
        # This would typically query the Reaction collection
        # For now, return empty dict as placeholder
        return {}