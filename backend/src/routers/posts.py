from fastapi import APIRouter, Query, Path
from typing import Optional

router = APIRouter(prefix="/api/posts", tags=["게시글"])

@router.get("/")
async def get_posts(
    type: Optional[str] = Query(None, description="게시글 타입 필터링"),
    author: Optional[str] = Query(None, description="작성자 user_handle 필터링"),
    visibility: Optional[str] = Query("public", description="공개 여부"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sortBy: str = Query("createdAt", description="정렬 기준"),
    sortOrder: str = Query("desc", description="정렬 순서")
):
    """게시글 목록 조회 - TODO: 구현 필요"""
    return {
        "message": "게시글 목록 조회 - 구현 예정",
        "params": {
            "type": type,
            "author": author,
            "visibility": visibility,
            "page": page,
            "limit": limit,
            "sortBy": sortBy,
            "sortOrder": sortOrder
        }
    }

@router.get("/search")
async def search_posts(
    q: str = Query(..., description="검색어"),
    type: Optional[str] = Query(None, description="게시글 타입 필터링"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기")
):
    """게시글 검색 - TODO: 구현 필요"""
    return {
        "message": "게시글 검색 - 구현 예정",
        "params": {
            "q": q,
            "type": type,
            "page": page,
            "limit": limit
        }
    }

@router.get("/{slug}")
async def get_post_detail(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 상세 조회 - TODO: 구현 필요"""
    return {
        "message": f"게시글 상세 조회 - 구현 예정",
        "slug": slug
    }

@router.post("/create")
async def create_post():
    """게시글 생성 - TODO: 구현 필요 (인증 필요)"""
    return {"message": "게시글 생성 - 구현 예정"}

@router.put("/{slug}/update")
async def update_post(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 수정 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"게시글 수정 - 구현 예정",
        "slug": slug
    }

@router.delete("/{slug}/delete")
async def delete_post(
    slug: str = Path(..., description="게시글 슬러그")
):
    """게시글 삭제 - TODO: 구현 필요 (인증 필요)"""
    return {
        "message": f"게시글 삭제 - 구현 예정",
        "slug": slug
    }