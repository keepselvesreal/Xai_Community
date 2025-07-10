"""Comment repository for data access layer."""

from typing import List, Dict, Optional, Tuple, Any, Literal
from datetime import datetime
from beanie import PydanticObjectId
from nadle_backend.models.core import Comment, CommentCreate, CommentDetail, PaginationParams
from nadle_backend.exceptions.comment import CommentNotFoundError, CommentDepthExceededError
from nadle_backend.config import get_settings

# 댓글 서브타입 상수 정의
CommentSubtype = Literal["service_inquiry", "service_review"]
COMMENT_SUBTYPES = {
    "service_inquiry": "service_inquiry",
    "service_review": "service_review"
}


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
            settings = get_settings()
            await self._validate_reply_depth(comment_data.parent_comment_id, settings.max_comment_depth)
        
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
            metadata=comment_data.metadata or {}
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
        
        print(f"🔍 [DEBUG] get_replies 쿼리: parent_comment_id={parent_comment_id}, status={status}")
        replies = await Comment.find(query).sort("created_at").to_list()
        print(f"🔍 [DEBUG] get_replies 결과: {len(replies)}개 답글 발견")
        for reply in replies:
            print(f"    답글: id={reply.id}, content={reply.content[:30]}..., parent_comment_id={reply.parent_comment_id}")
        
        return replies
    
    async def get_replies_recursive(self, parent_comment_id: str, status: str = "active", max_depth: int = 3, current_depth: int = 0) -> List[Dict[str, Any]]:
        """Get replies to a comment recursively with nested structure.
        
        Args:
            parent_comment_id: Parent comment ID
            status: Filter by status
            max_depth: Maximum depth for nested replies
            current_depth: Current recursion depth
            
        Returns:
            List of reply comment dictionaries with nested replies
        """
        if current_depth >= max_depth:
            return []
            
        # Get direct replies to this comment
        replies = await self.get_replies(parent_comment_id, status)
        
        replies_with_nested = []
        for reply in replies:
            # Get nested replies for each reply
            nested_replies = await self.get_replies_recursive(
                str(reply.id), 
                status, 
                max_depth, 
                current_depth + 1
            )
            
            reply_dict = {
                "comment": reply,
                "replies": nested_replies
            }
            replies_with_nested.append(reply_dict)
        
        return replies_with_nested
    
    async def get_comments_with_replies(
        self,
        post_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str = "active",
        max_depth: int = 3
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get comments with their replies in hierarchical structure.
        
        Args:
            post_id: Post ID
            page: Page number
            page_size: Number of items per page
            status: Filter by status
            max_depth: Maximum depth for nested replies
            
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
            # Get replies for this comment recursively
            replies = await self.get_replies_recursive(str(comment.id), status=status, max_depth=max_depth)
            
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
    
    async def _validate_reply_depth(self, parent_comment_id: str, max_depth: int = 3) -> None:
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
    
    async def find_by_author(self, author_id: str) -> List[Comment]:
        """Find all comments by author ID.
        
        Args:
            author_id: Author ID
            
        Returns:
            List of comments by the author
        """
        try:
            comments = await Comment.find({
                "author_id": author_id,
                "status": {"$ne": "deleted"}
            }).sort("-created_at").to_list()
            return comments
        except Exception:
            return []
    
    async def find_by_author_paginated(self, author_id: str, limit: int = 10, skip: int = 0) -> List[Comment]:
        """Find comments by author ID with pagination.
        
        Args:
            author_id: Author ID
            limit: Maximum number of comments to return (default: 10)
            skip: Number of comments to skip (default: 0)
            
        Returns:
            List of comments by the author with pagination (excluding deleted comments)
        """
        try:
            comments = await Comment.find({
                "author_id": author_id,
                "status": {"$ne": "deleted"}
            }).sort("-created_at").skip(skip).limit(limit).to_list()
            return comments
        except Exception:
            return []
    
    async def count_by_author(self, author_id: str) -> int:
        """Count total comments by author ID.
        
        Args:
            author_id: Author ID
            
        Returns:
            Total number of comments by the author (excluding deleted comments)
        """
        try:
            count = await Comment.find({
                "author_id": author_id,
                "status": {"$ne": "deleted"}
            }).count()
            return count
        except Exception:
            return 0
    
    async def count_comments_by_subtype(self, post_id: str, subtype: CommentSubtype) -> int:
        """특정 게시글의 subtype별 댓글 수 집계.
        
        Args:
            post_id: 게시글 ID
            subtype: 댓글 서브타입 (service_inquiry, service_review)
            
        Returns:
            해당 subtype의 댓글 수
        """
        try:
            # 인덱스 최적화된 쿼리 사용
            query = {
                "parent_id": post_id,
                "metadata.subtype": subtype,
                "status": "active"
            }
            
            count = await Comment.find(query).count()
            return count
            
        except Exception as e:
            print(f"Error counting comments by subtype {subtype} for post {post_id}: {e}")
            return 0

    async def get_comment_stats_by_post(self, post_id: str) -> Dict[str, int]:
        """게시글의 모든 댓글 통계를 한 번에 집계.
        
        MongoDB aggregation을 사용하여 효율적으로 모든 댓글 타입별 통계를 계산합니다.
        
        Args:
            post_id: 게시글 ID
            
        Returns:
            댓글 타입별 통계 딕셔너리:
            - general: 일반 댓글 수 (subtype 없음)
            - service_inquiry: 문의 댓글 수  
            - service_review: 후기 댓글 수
        """
        # 기본 통계 구조 정의
        default_stats = {
            "general": 0,
            "service_inquiry": 0,
            "service_review": 0
        }
        
        try:
            # MongoDB aggregation 파이프라인 (인덱스 최적화)
            pipeline = [
                {
                    "$match": {
                        "parent_id": post_id,
                        "status": "active"
                    }
                },
                {
                    "$group": {
                        "_id": "$metadata.subtype",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            result = await Comment.aggregate(pipeline).to_list()
            
            # 결과를 딕셔너리로 변환
            stats = default_stats.copy()
            
            for item in result:
                subtype = item["_id"]
                count = item["count"]
                
                if subtype == "service_inquiry":
                    stats["service_inquiry"] = count
                elif subtype == "service_review":
                    stats["service_review"] = count
                elif subtype is None:
                    stats["general"] = count
                    
            return stats
            
        except Exception as e:
            print(f"Error getting comment stats for post {post_id}: {e}")
            return default_stats