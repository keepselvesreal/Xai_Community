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
class ActivitySummary(BaseModel):
    """Activity summary model."""
    total_posts: int
    total_comments: int
    total_reactions: int
    most_active_page_type: str | None = None


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
    """User activity response model."""
    posts: Dict[str, list[ActivityItem]]
    comments: list[ActivityItem]
    reactions: Dict[str, list[ActivityItem]]
    summary: ActivitySummary


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
    current_user: User = Depends(get_current_user),
    user_activity_service: UserActivityService = Depends(get_user_activity_service)
) -> UserActivityResponse:
    """Get current user's activity summary.
    
    Returns comprehensive activity data including:
    - Posts grouped by page type (board, info, services, tips)
    - Comments with subtype information (inquiry/review for services)
    - Reactions grouped by type (likes, bookmarks, dislikes)
    - Summary statistics
    
    All items include routing information for frontend navigation.
    """
    try:
        # Get activity data from service
        activity_data = await user_activity_service.get_user_activity_summary(str(current_user.id))
        
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
                title=comment.get("post_title"),  # 댓글의 경우 해당 게시글 제목 표시
                view_count=comment.get("view_count"),
                like_count=comment.get("like_count"),
                dislike_count=comment.get("dislike_count"),
                comment_count=comment.get("comment_count")
            )
            for comment in activity_data["comments"]
        ]
        
        # Convert reactions to ActivityItem format
        reactions_formatted = {}
        for reaction_type, reactions in activity_data["reactions"].items():
            reactions_formatted[reaction_type] = [
                ActivityItem(
                    id=reaction["id"],
                    target_type=reaction["target_type"],
                    target_id=reaction["target_id"],
                    target_title=reaction["target_title"],
                    title=reaction.get("title"),  # 반응한 게시글 제목
                    created_at=reaction["created_at"],
                    route_path=reaction["route_path"],
                    view_count=reaction.get("view_count"),
                    like_count=reaction.get("like_count"),
                    dislike_count=reaction.get("dislike_count"),
                    comment_count=reaction.get("comment_count")
                )
                for reaction in reactions
            ]
        
        # Convert summary
        summary = ActivitySummary(
            total_posts=activity_data["summary"]["total_posts"],
            total_comments=activity_data["summary"]["total_comments"],
            total_reactions=activity_data["summary"]["total_reactions"],
            most_active_page_type=activity_data["summary"]["most_active_page_type"]
        )
        
        return UserActivityResponse(
            posts=posts_formatted,
            comments=comments_formatted,
            reactions=reactions_formatted,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user activity: {str(e)}"
        )