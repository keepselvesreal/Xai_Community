"""Comments router for API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from nadle_backend.models.core import (
    CommentCreate, CommentUpdate, CommentDetail, User, CommentListResponse, PaginationInfo
)
from nadle_backend.services.comments_service import CommentsService
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.dependencies.auth import (
    get_current_active_user, get_optional_current_active_user
)
from nadle_backend.exceptions.comment import (
    CommentNotFoundError, CommentPermissionError, CommentValidationError
)
from nadle_backend.exceptions.post import PostNotFoundError


# Create router
router = APIRouter(tags=["comments"])


def get_comments_service() -> CommentsService:
    """Get comments service dependency."""
    comment_repo = CommentRepository()
    post_repo = PostRepository()
    return CommentsService(comment_repo, post_repo)


@router.get("/{slug}/comments", response_model=CommentListResponse)
async def get_comments(
    slug: str = Path(..., description="Post slug"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Get comments for a post."""
    try:
        print(f"🔍 [DEBUG] Comments Router 호출 - slug: {slug}")
        comments, total = await comments_service.get_comments_with_user_data(
            post_slug=slug,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            current_user=current_user
        )
        print(f"🔍 [DEBUG] Comments Router 결과 - comments: {len(comments)}, total: {total}")
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        pagination = PaginationInfo(
            page=page,
            limit=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return CommentListResponse(
            comments=comments,
            pagination=pagination
        )
        
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {str(e)}"
        )


@router.post("/{slug}/comments", response_model=CommentDetail, status_code=status.HTTP_201_CREATED)
async def create_comment(
    slug: str = Path(..., description="Post slug"),
    comment_data: CommentCreate = ...,
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Create a new comment."""
    try:
        comment = await comments_service.create_comment(
            post_slug=slug,
            comment_data=comment_data,
            current_user=current_user
        )
        return comment
        
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except CommentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.post("/{slug}/comments/{comment_id}/replies", response_model=CommentDetail, status_code=status.HTTP_201_CREATED)
async def create_reply(
    slug: str = Path(..., description="Post slug"),
    comment_id: str = Path(..., description="Parent comment ID"),
    reply_data: CommentCreate = ...,
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Create a reply to a comment."""
    try:
        reply = await comments_service.create_reply(
            post_slug=slug,
            parent_comment_id=comment_id,
            comment_data=reply_data,
            current_user=current_user
        )
        return reply
        
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent comment not found"
        )
    except CommentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reply: {str(e)}"
        )


@router.put("/{slug}/comments/{comment_id}", response_model=CommentDetail)
async def update_comment(
    slug: str = Path(..., description="Post slug"),
    comment_id: str = Path(..., description="Comment ID"),
    comment_data: CommentUpdate = ...,
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Update a comment."""
    try:
        comment = await comments_service.update_comment_with_permission(
            comment_id=comment_id,
            content=comment_data.content,
            current_user=current_user
        )
        return comment
        
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    except CommentPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    except CommentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update comment: {str(e)}"
        )


@router.delete("/{slug}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    slug: str = Path(..., description="Post slug"),
    comment_id: str = Path(..., description="Comment ID"),
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Delete a comment."""
    try:
        await comments_service.delete_comment_with_permission(
            comment_id=comment_id,
            current_user=current_user
        )
        
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    except CommentPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete comment: {str(e)}"
        )


@router.post("/{slug}/comments/{comment_id}/like", status_code=status.HTTP_200_OK)
async def like_comment(
    slug: str = Path(..., description="Post slug"),
    comment_id: str = Path(..., description="Comment ID"),
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Like a comment."""
    try:
        result = await comments_service.toggle_comment_reaction(
            comment_id=comment_id,
            reaction_type="like",
            current_user=current_user
        )
        
        return {
            "message": "Comment liked" if result["user_reaction"]["liked"] else "Comment like removed",
            "like_count": result["like_count"],
            "dislike_count": result["dislike_count"],
            "user_reaction": result["user_reaction"]
        }
        
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to like comment: {str(e)}"
        )


@router.post("/{slug}/comments/{comment_id}/dislike", status_code=status.HTTP_200_OK)
async def dislike_comment(
    slug: str = Path(..., description="Post slug"),
    comment_id: str = Path(..., description="Comment ID"),
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Dislike a comment."""
    try:
        result = await comments_service.toggle_comment_reaction(
            comment_id=comment_id,
            reaction_type="dislike",
            current_user=current_user
        )
        
        return {
            "message": "Comment disliked" if result["user_reaction"]["disliked"] else "Comment dislike removed",
            "like_count": result["like_count"],
            "dislike_count": result["dislike_count"],
            "user_reaction": result["user_reaction"]
        }
        
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dislike comment: {str(e)}"
        )


# 🆕 TDD: 문의/후기 전용 API 엔드포인트 추가
@router.post("/{slug}/comments/inquiry", response_model=CommentDetail, status_code=status.HTTP_201_CREATED)
async def create_service_inquiry(
    slug: str = Path(..., description="Post slug"),
    comment_data: CommentCreate = ...,
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Create a service inquiry."""
    try:
        # metadata에 subtype 설정 (기존 metadata와 병합)
        if not comment_data.metadata:
            comment_data.metadata = {}
        comment_data.metadata["subtype"] = "service_inquiry"
        
        # 기존 create_comment 메서드 재사용
        inquiry = await comments_service.create_comment(
            post_slug=slug,
            comment_data=comment_data,
            current_user=current_user
        )
        return inquiry
        
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except CommentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inquiry: {str(e)}"
        )


@router.post("/{slug}/comments/review", response_model=CommentDetail, status_code=status.HTTP_201_CREATED)
async def create_service_review(
    slug: str = Path(..., description="Post slug"),
    comment_data: CommentCreate = ...,
    current_user: User = Depends(get_current_active_user),
    comments_service: CommentsService = Depends(get_comments_service)
):
    """Create a service review."""
    try:
        # metadata에 subtype 설정 (기존 metadata와 병합)
        if not comment_data.metadata:
            comment_data.metadata = {}
        comment_data.metadata["subtype"] = "service_review"
        
        # 기존 create_comment 메서드 재사용
        review = await comments_service.create_comment(
            post_slug=slug,
            comment_data=comment_data,
            current_user=current_user
        )
        return review
        
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except CommentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}"
        )