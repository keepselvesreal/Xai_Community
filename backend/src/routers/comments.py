from fastapi import APIRouter, Query, Path
from typing import Optional

router = APIRouter(prefix="/api/posts", tags=["댓글"])

@router.get("/{slug}/comments")
async def get_comments(
    slug: str = Path(..., description="게시글 슬러그"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=100, description="페이지 크기"),
    sortBy: str = Query("createdAt", description="정렬 기준"),
    sortOrder: str = Query("asc", description="정렬 순서")
):
    """댓글 목록 조회 - TODO: 구현 필요"""
    return {
        "message": f"댓글 목록 조회 - 구현 예정",
        "slug": slug,
        "params": {
            "page": page,
            "limit": limit,
            "sortBy": sortBy,
            "sortOrder": sortOrder
        }
    }

@router.post("/{slug}/comments/create")
async def create_comment(
    slug: str = Path(..., description="게시글 슬러그")
):
    """댓글 생성 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"댓글 생성 - 구현 예정",
        "slug": slug
    }

@router.put("/{slug}/comments/{comment_id}/update")
async def update_comment(
    slug: str = Path(..., description="게시글 슬러그"),
    comment_id: str = Path(..., description="댓글 ID")
):
    """댓글 수정 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"댓글 수정 - 구현 예정",
        "slug": slug,
        "comment_id": comment_id
    }

@router.delete("/{slug}/comments/{comment_id}/delete") 
async def delete_comment(
    slug: str = Path(..., description="게시글 슬러그"),
    comment_id: str = Path(..., description="댓글 ID")
):
    """댓글 삭제 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"댓글 삭제 - 구현 예정",
        "slug": slug,
        "comment_id": comment_id
    }

@router.post("/{slug}/comments/{comment_id}/replies/create")
async def create_reply(
    slug: str = Path(..., description="게시글 슬러그"),
    comment_id: str = Path(..., description="부모 댓글 ID")
):
    """대댓글 생성 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"대댓글 생성 - 구현 예정",
        "slug": slug,
        "parent_comment_id": comment_id
    }

@router.post("/{slug}/comments/{comment_id}/like")
async def like_comment(
    slug: str = Path(..., description="게시글 슬러그"),
    comment_id: str = Path(..., description="댓글 ID")
):
    """댓글 좋아요 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"댓글 좋아요 - 구현 예정",
        "slug": slug,
        "comment_id": comment_id
    }

@router.post("/{slug}/comments/{comment_id}/dislike")
async def dislike_comment(
    slug: str = Path(..., description="게시글 슬러그"),
    comment_id: str = Path(..., description="댓글 ID")
):
    """댓글 싫어요 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"댓글 싫어요 - 구현 예정",
        "slug": slug,
        "comment_id": comment_id
    }