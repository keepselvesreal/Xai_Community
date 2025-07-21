"""Posts router for API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from nadle_backend.models.core import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PaginatedResponse,
    User,
)
from nadle_backend.services.posts_service import PostsService
from nadle_backend.dependencies.auth import (
    get_current_active_user,
    get_optional_current_active_user,
)
from nadle_backend.exceptions.post import PostNotFoundError, PostPermissionError


# Create router
router = APIRouter(tags=["posts"])


def get_posts_service() -> PostsService:
    """Get posts service dependency."""
    return PostsService()


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "posts"}


@router.get("/search", response_model=Dict[str, Any])
async def search_posts(
    q: str = Query(..., description="Search query"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    metadata_type: Optional[str] = Query(None, description="Filter by metadata type"),
    sort_by: str = Query("created_at", description="Sort field"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Search posts with filters."""
    try:
        result = await posts_service.search_posts(
            query=q,
            service_type=service_type,
            metadata_type=metadata_type,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            current_user=current_user,
        )

        # Convert ObjectIds to strings in the response
        if "items" in result:
            for item in result["items"]:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
                if "id" in item:
                    item["id"] = str(item["id"])
                if "author_id" in item:
                    item["author_id"] = str(item["author_id"])
                # file_ids 추가
                if "metadata" in item and item["metadata"]:
                    item["file_ids"] = item["metadata"].get("file_ids", [])

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/", response_model=Dict[str, Any])
async def list_posts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    metadata_type: Optional[str] = Query(None, description="Filter by metadata type"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    sort_by: str = Query("created_at", description="Sort field"),
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """List posts with pagination and filters."""
    try:
        result = await posts_service.list_posts(
            page=page,
            page_size=page_size,
            service_type=service_type,
            metadata_type=metadata_type,
            author_id=author_id,
            sort_by=sort_by,
            current_user=current_user,
        )

        # Convert ObjectIds to strings in the response
        if "items" in result:
            for item in result["items"]:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
                if "id" in item:
                    item["id"] = str(item["id"])
                if "author_id" in item:
                    item["author_id"] = str(item["author_id"])
                # file_ids 추가
                if "metadata" in item and item["metadata"]:
                    item["file_ids"] = item["metadata"].get("file_ids", [])

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list posts: {str(e)}",
        )


@router.get("/{slug}/complete", status_code=status.HTTP_200_OK)
async def get_post_complete_aggregated(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """🚀 완전 통합 Aggregation으로 게시글 + 작성자 + 댓글 + 댓글작성자 + 사용자반응을 모두 한 번의 쿼리로 조회"""
    try:
        # 완전 통합 Aggregation으로 모든 데이터 한 번에 조회
        complete_data = await posts_service.get_post_with_everything_aggregated(
            slug, str(current_user.id) if current_user else None
        )

        if not complete_data:
            raise PostNotFoundError("Post not found")

        # 기존 API와 동일한 응답 구조로 반환 (UI 변경 최소화)
        return complete_data

    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get complete post data: {str(e)}",
        )


@router.get("/{slug_or_id}", response_model=Dict[str, Any])
async def get_post(
    slug_or_id: str,
    include_comments: bool = Query(
        False, description="Include comments in response for faster loading"
    ),
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Get post by slug or ID."""
    try:
        post = await posts_service.get_post(slug_or_id, current_user)
        print(f"🔍 백엔드 게시글 조회 - slug: {slug_or_id}")
        if post.metadata:
            print(f"📝 메타데이터: {post.metadata.model_dump()}")
            if hasattr(post.metadata, "tags") and post.metadata.tags:
                print(f"🏷️ 조회된 태그: {post.metadata.tags}")
        else:
            print("📝 메타데이터 없음")

        # 🔍 서비스 포스트인 경우 확장 통계 포함 (이미 조회된 post 객체 재사용하여 조회수 중복 증가 방지)
        if post.metadata and post.metadata.type == "moving services":
            print("📊 서비스 포스트 - 확장 통계 포함")
            return await posts_service.get_service_post_with_extended_stats_from_post(
                post, current_user
            )

        # ✅ Use denormalized stats from Post model (no real-time calculation)
        real_stats = {
            "view_count": post.view_count,
            "like_count": post.like_count,
            "dislike_count": post.dislike_count,
            "comment_count": post.comment_count,
            "bookmark_count": post.bookmark_count,
        }

        # 🚀 1단계: 캐시된 사용자 반응 조회
        user_reaction = None
        if current_user:
            user_reaction = await posts_service.get_user_reaction_cached(
                str(current_user.id), str(post.id)
            )

        # 🚀 1단계: 캐시된 작성자 정보 조회
        author_info = await posts_service.get_author_info_cached(str(post.author_id))

        # Build response with stats
        response = {
            "id": str(post.id),
            "_id": str(post.id),
            "title": post.title,
            "content": post.content,
            "slug": post.slug,
            "service": post.service,
            "metadata": post.metadata,
            "file_ids": (
                post.metadata.file_ids if post.metadata else []
            ),  # 파일 IDs 추가
            "author_id": str(post.author_id),
            "author": author_info,  # 작성자 정보 추가
            "status": post.status,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at,
            "stats": real_stats,
            "view_count": real_stats["view_count"],
            "like_count": real_stats["like_count"],
            "dislike_count": real_stats["dislike_count"],
            "comment_count": real_stats["comment_count"],
            "bookmark_count": post.bookmark_count,
        }

        if user_reaction:
            response["user_reaction"] = user_reaction

        return response
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get post: {str(e)}",
        )


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Create a new post."""
    try:
        print(f"🚀 백엔드 게시글 생성 요청 - 받은 데이터: {post_data.model_dump()}")
        if post_data.metadata:
            print(f"📝 메타데이터: {post_data.metadata.model_dump()}")
            if hasattr(post_data.metadata, "tags") and post_data.metadata.tags:
                print(f"🏷️ 태그: {post_data.metadata.tags}")

        # 권한 체크: 특정 타입의 게시글 작성 권한 확인
        if post_data.metadata and post_data.metadata.type:
            post_type = post_data.metadata.type

            # 입주 업체 서비스 글쓰기 권한 체크
            if post_type == "moving services":
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="로그인이 필요합니다",
                    )
                if not (
                    current_user.is_admin or current_user.can_write_moving_services
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="입주 업체 서비스 페이지에 글을 작성할 권한이 없습니다",
                    )

            # 전문가 꿀정보 글쓰기 권한 체크
            elif post_type == "expert_tips":
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="로그인이 필요합니다",
                    )
                if not (current_user.is_admin or current_user.can_write_expert_tips):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="전문가 꿀정보 페이지에 글을 작성할 권한이 없습니다",
                    )

        post = await posts_service.create_post(post_data, current_user)
        # Convert Post document to PostResponse with proper field mapping
        return PostResponse(
            id=str(post.id),
            title=post.title,
            content=post.content,
            slug=post.slug,
            service=post.service,
            metadata=post.metadata,
            author_id=str(post.author_id),
            status=post.status,
            created_at=post.created_at,
            updated_at=post.updated_at,
            published_at=post.published_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create post: {str(e)}",
        )


@router.put("/{slug}", response_model=PostResponse)
async def update_post(
    slug: str,
    update_data: PostUpdate,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Update post by slug."""
    try:
        print(f"🚀 백엔드 게시글 수정 요청 - 받은 데이터: {update_data.model_dump()}")
        if update_data.metadata:
            print(f"📝 메타데이터: {update_data.metadata.model_dump()}")
            if hasattr(update_data.metadata, "tags") and update_data.metadata.tags:
                print(f"🏷️ 태그: {update_data.metadata.tags}")
        post = await posts_service.update_post(slug, update_data, current_user)
        # Convert Post document to PostResponse with proper field mapping
        return PostResponse(
            id=str(post.id),
            title=post.title,
            content=post.content,
            slug=post.slug,
            service=post.service,
            metadata=post.metadata,
            author_id=str(post.author_id),
            status=post.status,
            created_at=post.created_at,
            updated_at=post.updated_at,
            published_at=post.published_at,
        )
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except PostPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this post",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update post: {str(e)}",
        )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Delete post by slug."""
    try:
        await posts_service.delete_post(slug, current_user)
        return {"success": True, "message": "게시글이 삭제되었습니다"}
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except PostPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this post",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete post: {str(e)}",
        )


@router.post("/{slug_or_id}/like", status_code=status.HTTP_200_OK)
async def like_post(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Like a post."""
    try:
        result = await posts_service.toggle_post_reaction(
            slug_or_id, "like", current_user
        )
        return {
            "message": (
                "Post liked"
                if result["user_reaction"]["liked"]
                else "Post like removed"
            ),
            "like_count": result["like_count"],
            "dislike_count": result["dislike_count"],
            "user_reaction": result["user_reaction"],
        }
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to like post: {str(e)}",
        )


@router.post("/{slug_or_id}/dislike", status_code=status.HTTP_200_OK)
async def dislike_post(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Dislike a post."""
    try:
        result = await posts_service.toggle_post_reaction(
            slug_or_id, "dislike", current_user
        )
        return {
            "message": (
                "Post disliked"
                if result["user_reaction"]["disliked"]
                else "Post dislike removed"
            ),
            "like_count": result["like_count"],
            "dislike_count": result["dislike_count"],
            "user_reaction": result["user_reaction"],
        }
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dislike post: {str(e)}",
        )


@router.post("/{slug_or_id}/bookmark", status_code=status.HTTP_200_OK)
async def bookmark_post(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Bookmark a post."""
    try:
        result = await posts_service.toggle_post_reaction(
            slug_or_id, "bookmark", current_user
        )
        return {
            "action": (
                "bookmarked"
                if result["user_reaction"]["bookmarked"]
                else "unbookmarked"
            ),
            "bookmark_count": result["bookmark_count"],
            "user_reaction": result["user_reaction"],
        }
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bookmark post: {str(e)}",
        )


@router.get("/{slug_or_id}/stats", status_code=status.HTTP_200_OK)
async def get_post_stats(
    slug_or_id: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """Get post statistics."""
    try:
        # Get post by slug or ID
        post = await posts_service.get_post(slug_or_id)

        # ✅ Use denormalized stats from Post model (no real-time calculation)
        result = {
            "view_count": post.view_count,
            "like_count": post.like_count,
            "dislike_count": post.dislike_count,
            "comment_count": post.comment_count,
            "bookmark_count": post.bookmark_count,
        }

        # Add user reaction if authenticated
        if current_user:
            from nadle_backend.models.core import UserReaction

            user_reaction = await UserReaction.find_one(
                {
                    "user_id": str(current_user.id),
                    "target_type": "post",
                    "target_id": str(post.id),
                }
            )

            if user_reaction:
                result["user_reaction"] = {
                    "liked": user_reaction.liked,
                    "disliked": user_reaction.disliked,
                    "bookmarked": user_reaction.bookmarked,
                }

        return result

    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get post stats: {str(e)}",
        )


@router.get("/{slug}/comments", status_code=status.HTTP_200_OK)
async def get_post_comments_batch(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """🚀 2단계: 배치 조회로 게시글 댓글 조회"""
    try:
        # 배치 조회로 댓글과 작성자 정보 함께 조회
        comments_with_authors = await posts_service.get_comments_with_batch_authors(
            slug
        )

        return {
            "success": True,
            "data": {
                "comments": comments_with_authors,
                "total": len(comments_with_authors),
            },
        }

    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {str(e)}",
        )


@router.get("/{slug}/full", status_code=status.HTTP_200_OK)
async def get_post_full_aggregated(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """🚀 3단계: Aggregation으로 게시글 + 댓글 + 작성자 정보 모두 한 번에 조회"""
    try:
        # Aggregation으로 모든 데이터 한 번에 조회
        full_data = await posts_service.get_post_with_comments_aggregated(slug)

        if not full_data:
            raise PostNotFoundError("Post not found")

        # 사용자 반응 정보 추가 (캐시된 방식 사용)
        if current_user:
            user_reaction = await posts_service.get_user_reaction_cached(
                str(current_user.id), str(full_data["id"])
            )
            full_data["user_reaction"] = user_reaction

        return {"success": True, "data": full_data}

    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get full post data: {str(e)}",
        )


@router.get("/{slug}/aggregated", status_code=status.HTTP_200_OK)
async def get_post_aggregated(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service),
):
    """🚀 3단계: Aggregation으로 게시글 + 작성자 정보만 조회 (성능 비교용)"""
    try:
        # Aggregation으로 게시글 + 작성자 정보만 조회
        post_data = await posts_service.get_post_with_author_aggregated(slug)

        if not post_data:
            raise PostNotFoundError("Post not found")

        # 사용자 반응 정보 추가 (캐시된 방식 사용)
        if current_user:
            user_reaction = await posts_service.get_user_reaction_cached(
                str(current_user.id), str(post_data["id"])
            )
            post_data["user_reaction"] = user_reaction

        return {"success": True, "data": post_data}

    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get aggregated post: {str(e)}",
        )
