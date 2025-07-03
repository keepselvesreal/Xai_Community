"""Posts router for API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from nadle_backend.models.core import (
    PostCreate, PostUpdate, PostResponse, PaginatedResponse, User
)
from nadle_backend.services.posts_service import PostsService
from nadle_backend.dependencies.auth import (
    get_current_active_user, get_optional_current_active_user
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
    posts_service: PostsService = Depends(get_posts_service)
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
            current_user=current_user
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
            detail=f"Search failed: {str(e)}"
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
    posts_service: PostsService = Depends(get_posts_service)
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
            current_user=current_user
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
            detail=f"Failed to list posts: {str(e)}"
        )


@router.get("/{slug_or_id}", response_model=Dict[str, Any])
async def get_post(
    slug_or_id: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Get post by slug or ID."""
    try:
        post = await posts_service.get_post(slug_or_id, current_user)
        print(f"🔍 백엔드 게시글 조회 - slug: {slug_or_id}")
        if post.metadata:
            print(f"📝 메타데이터: {post.metadata.model_dump()}")
            if hasattr(post.metadata, 'tags') and post.metadata.tags:
                print(f"🏷️ 조회된 태그: {post.metadata.tags}")
        else:
            print("📝 메타데이터 없음")
        
        # 🔍 서비스 포스트인 경우 확장 통계 포함
        if post.metadata and post.metadata.type == "moving services":
            print("📊 서비스 포스트 - 확장 통계 포함")
            return await posts_service.get_service_post_with_extended_stats(slug_or_id, current_user)
        
        # ✅ Use denormalized stats from Post model (no real-time calculation)
        real_stats = {
            "view_count": post.view_count,
            "like_count": post.like_count,
            "dislike_count": post.dislike_count,
            "comment_count": post.comment_count,
            "bookmark_count": post.bookmark_count
        }
        
        # Get user reaction if authenticated
        user_reaction = None
        if current_user:
            from nadle_backend.models.core import UserReaction
            reaction = await UserReaction.find_one({
                "user_id": str(current_user.id),
                "target_type": "post",
                "target_id": str(post.id)
            })
            if reaction:
                user_reaction = {
                    "liked": reaction.liked,
                    "disliked": reaction.disliked,
                    "bookmarked": reaction.bookmarked
                }
        
        # Get author information
        author_info = None
        try:
            author = await User.get(post.author_id)
            if author:
                author_info = {
                    "id": str(author.id),
                    "user_handle": author.user_handle,
                    "display_name": author.display_name,
                    "name": author.name
                }
        except Exception as e:
            print(f"Failed to get author info: {e}")
            author_info = {
                "id": str(post.author_id),
                "user_handle": "익명",
                "display_name": "익명",
                "name": "익명"
            }
        
        # Build response with stats
        response = {
            "id": str(post.id),
            "_id": str(post.id),
            "title": post.title,
            "content": post.content,
            "slug": post.slug,
            "service": post.service,
            "metadata": post.metadata,
            "file_ids": post.metadata.file_ids if post.metadata else [],  # 파일 IDs 추가
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
            "bookmark_count": post.bookmark_count
        }
        
        if user_reaction:
            response["user_reaction"] = user_reaction
            
        return response
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get post: {str(e)}"
        )


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Create a new post."""
    try:
        print(f"🚀 백엔드 게시글 생성 요청 - 받은 데이터: {post_data.model_dump()}")
        if post_data.metadata:
            print(f"📝 메타데이터: {post_data.metadata.model_dump()}")
            if hasattr(post_data.metadata, 'tags') and post_data.metadata.tags:
                print(f"🏷️ 태그: {post_data.metadata.tags}")
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
            published_at=post.published_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create post: {str(e)}"
        )


@router.put("/{slug}", response_model=PostResponse)
async def update_post(
    slug: str,
    update_data: PostUpdate,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Update post by slug."""
    try:
        print(f"🚀 백엔드 게시글 수정 요청 - 받은 데이터: {update_data.model_dump()}")
        if update_data.metadata:
            print(f"📝 메타데이터: {update_data.metadata.model_dump()}")
            if hasattr(update_data.metadata, 'tags') and update_data.metadata.tags:
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
            published_at=post.published_at
        )
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except PostPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update this post"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update post: {str(e)}"
        )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Delete post by slug."""
    try:
        await posts_service.delete_post(slug, current_user)
        return {"success": True, "message": "게시글이 삭제되었습니다"}
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except PostPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this post"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete post: {str(e)}"
        )


@router.post("/{slug_or_id}/like", status_code=status.HTTP_200_OK)
async def like_post(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Like a post."""
    try:
        result = await posts_service.toggle_post_reaction(slug_or_id, "like", current_user)
        return {
            "message": "Post liked" if result["user_reaction"]["liked"] else "Post like removed",
            "like_count": result["like_count"],
            "dislike_count": result["dislike_count"],
            "user_reaction": result["user_reaction"]
        }
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to like post: {str(e)}"
        )


@router.post("/{slug_or_id}/dislike", status_code=status.HTTP_200_OK)
async def dislike_post(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Dislike a post."""
    try:
        result = await posts_service.toggle_post_reaction(slug_or_id, "dislike", current_user)
        return {
            "message": "Post disliked" if result["user_reaction"]["disliked"] else "Post dislike removed",
            "like_count": result["like_count"],
            "dislike_count": result["dislike_count"],
            "user_reaction": result["user_reaction"]
        }
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dislike post: {str(e)}"
        )


@router.post("/{slug_or_id}/bookmark", status_code=status.HTTP_200_OK)
async def bookmark_post(
    slug_or_id: str,
    current_user: User = Depends(get_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Bookmark a post."""
    try:
        result = await posts_service.toggle_post_reaction(slug_or_id, "bookmark", current_user)
        return {
            "action": "bookmarked" if result["user_reaction"]["bookmarked"] else "unbookmarked",
            "bookmark_count": result["bookmark_count"],
            "user_reaction": result["user_reaction"]
        }
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bookmark post: {str(e)}"
        )


@router.get("/{slug_or_id}/stats", status_code=status.HTTP_200_OK)
async def get_post_stats(
    slug_or_id: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
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
            "bookmark_count": post.bookmark_count
        }
        
        # Add user reaction if authenticated
        if current_user:
            from nadle_backend.models.core import UserReaction
            user_reaction = await UserReaction.find_one({
                "user_id": str(current_user.id),
                "target_type": "post",
                "target_id": str(post.id)
            })
            
            if user_reaction:
                result["user_reaction"] = {
                    "liked": user_reaction.liked,
                    "disliked": user_reaction.disliked,
                    "bookmarked": user_reaction.bookmarked
                }
        
        return result
        
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get post stats: {str(e)}"
        )