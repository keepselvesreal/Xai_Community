"""Users router for user-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from nadle_backend.services.user_activity_service import UserActivityService
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository
from nadle_backend.dependencies.auth import get_current_user
from nadle_backend.models.core import User
from pydantic import BaseModel


# Response models
class PaginationInfo(BaseModel):
    """Pagination information model."""
    total_count: int
    page: int
    limit: int
    has_more: bool


class ActivityItem(BaseModel):
    """Activity item model."""
    id: str
    title: str | None = None
    content: str | None = None
    slug: str | None = None
    created_at: str
    view_count: int | None = None
    like_count: int | None = None
    dislike_count: int | None = None
    comment_count: int | None = None
    route_path: str
    subtype: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    target_title: str | None = None


class UserActivityResponse(BaseModel):
    """User activity response model with simplified structure."""
    posts: Dict[str, list[ActivityItem]]  # DB native types: board, property_information, expert_tips, services
    comments: list[ActivityItem]
    # Simplified reaction structure with reaction-* prefix
    # Dynamic keys: reaction-likes, reaction-dislikes, reaction-bookmarks
    pagination: Dict[str, PaginationInfo]
    
    class Config:
        extra = "allow"  # Allow dynamic reaction-* keys


router = APIRouter()


def get_user_activity_service() -> UserActivityService:
    """Get user activity service instance."""
    post_repo = PostRepository()
    comment_repo = CommentRepository()
    user_reaction_repo = UserReactionRepository()
    
    return UserActivityService(
        post_repository=post_repo,
        comment_repository=comment_repo,
        user_reaction_repository=user_reaction_repo
    )


@router.get("/me/activity", response_model=UserActivityResponse)
async def get_user_activity(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    user_activity_service: UserActivityService = Depends(get_user_activity_service)
) -> UserActivityResponse:
    """Get current user's activity summary with pagination.
    
    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 10, max: 50)
    
    Returns comprehensive activity data including:
    - Posts grouped by page type (board, info, services, tips)
    - Comments with subtype information (inquiry/review for services)
    - Reactions grouped by type (likes, bookmarks, dislikes)
    - Pagination information for each data type
    
    All items include routing information for frontend navigation.
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 50:
            limit = 10
        
        # Get activity data from service with pagination
        activity_data = await user_activity_service.get_user_activity_summary(
            user_id=str(current_user.id),
            page=page,
            limit=limit
        )
        
        # Convert posts to ActivityItem format
        posts_formatted = {}
        for page_type, posts in activity_data["posts"].items():
            posts_formatted[page_type] = [
                ActivityItem(
                    id=post["id"],
                    title=post["title"],
                    slug=post["slug"],
                    created_at=post["created_at"],
                    view_count=post["view_count"],
                    like_count=post["like_count"],
                    dislike_count=post["dislike_count"],
                    comment_count=post["comment_count"],
                    route_path=post["route_path"]
                )
                for post in posts
            ]
        
        # Convert comments to ActivityItem format
        comments_formatted = [
            ActivityItem(
                id=comment["id"],
                content=comment["content"],
                created_at=comment["created_at"],
                route_path=comment["route_path"],
                subtype=comment["subtype"],
                title=comment.get("post_title")  # 댓글의 경우 해당 게시글 제목 표시
            )
            for comment in activity_data["comments"]
        ]
        
        # Convert reactions to ActivityItem format (reaction-* prefix structure)
        reactions_formatted = {}
        for reaction_key, page_groups in activity_data["reactions"].items():
            reactions_formatted[reaction_key] = {}
            for page_type, reactions in page_groups.items():
                reactions_formatted[reaction_key][page_type] = [
                    ActivityItem(
                        id=reaction["id"],
                        target_type=reaction["target_type"],
                        target_id=reaction["target_id"],
                        target_title=reaction["target_title"],
                        title=reaction.get("title"),  # 반응한 게시글 제목
                        created_at=reaction["created_at"],
                        route_path=reaction["route_path"]
                    )
                    for reaction in reactions
                ]
        
        # Convert pagination info
        pagination_formatted = {}
        for data_type, pagination_data in activity_data["pagination"].items():
            pagination_formatted[data_type] = PaginationInfo(
                total_count=pagination_data["total_count"],
                page=pagination_data["page"],
                limit=pagination_data["limit"],
                has_more=pagination_data["has_more"]
            )
        
        # Build response with dynamic reaction keys
        response_data = {
            "posts": posts_formatted,
            "comments": comments_formatted,
            "pagination": pagination_formatted
        }
        
        # Add reaction data with reaction-* keys
        response_data.update(reactions_formatted)
        
        return UserActivityResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user activity: {str(e)}"
        )