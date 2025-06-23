from fastapi import APIRouter, Path

router = APIRouter(prefix="/api/posts", tags=["통계 및 반응"])

@router.get("/{slug}/stats")
async def get_post_stats(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 통계 조회 - TODO: 구현 필요"""
    return {
        "message": f"게시글 통계 조회 - 구현 예정",
        "slug": slug
    }

@router.post("/{slug}/like")
async def toggle_post_like(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 좋아요 토글 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"게시글 좋아요 토글 - 구현 예정",
        "slug": slug
    }

@router.post("/{slug}/dislike")
async def toggle_post_dislike(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 싫어요 토글 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"게시글 싫어요 토글 - 구현 예정",
        "slug": slug
    }

@router.post("/{slug}/bookmark")
async def toggle_post_bookmark(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 북마크 토글 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"게시글 북마크 토글 - 구현 예정",
        "slug": slug
    }