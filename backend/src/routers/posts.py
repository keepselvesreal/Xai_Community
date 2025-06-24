"""Posts router for API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.models.core import (
    PostCreate, PostUpdate, PostResponse, PaginatedResponse, User
)
from src.services.posts_service import PostsService
from src.dependencies.auth import (
    get_current_active_user, get_optional_current_active_user
)
from src.exceptions.post import PostNotFoundError, PostPermissionError


# Create router
router = APIRouter(prefix="/api/posts", tags=["posts"])


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
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list posts: {str(e)}"
        )


@router.get("/{slug}", response_model=PostResponse)
async def get_post(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    posts_service: PostsService = Depends(get_posts_service)
):
    """Get post by slug."""
    try:
        post = await posts_service.get_post(slug, current_user)
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
        return None
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