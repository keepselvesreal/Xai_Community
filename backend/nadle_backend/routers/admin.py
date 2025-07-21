"""Admin router for administrative endpoints."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from nadle_backend.models.core import User, Post
from nadle_backend.services.admin_service import AdminService
from nadle_backend.dependencies.auth import AdminUser
from nadle_backend.exceptions.post import PostNotFoundError


router = APIRouter(prefix="/admin", tags=["admin"])


class InquiryStatusUpdate(BaseModel):
    """Request model for updating inquiry status."""

    status: str  # "resolved" or "rejected"


class UserPermissionUpdate(BaseModel):
    """Request model for updating user permissions."""

    can_write_moving_services: Optional[bool] = None
    can_write_expert_tips: Optional[bool] = None


class InquiryListResponse(BaseModel):
    """Response model for inquiry list."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class PostListResponse(BaseModel):
    """Response model for post list."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


def get_admin_service() -> AdminService:
    """Get admin service dependency."""
    return AdminService()


@router.get("/inquiries", response_model=InquiryListResponse)
async def get_inquiries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    inquiry_type: Optional[str] = Query(None, description="Filter by inquiry type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    """
    Get list of inquiries/reports for admin management.

    - **inquiry_type**: moving-services-register-inquiry, expert-tips-register-inquiry, suggestions, report
    - **status**: pending, resolved, rejected
    """
    try:
        result = await admin_service.get_inquiries_list(
            current_user=current_user,
            page=page,
            page_size=page_size,
            inquiry_type=inquiry_type,
            status=status,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get inquiries list: {str(e)}"
        )


@router.get("/inquiries/{inquiry_id}")
async def get_inquiry_by_id(
    inquiry_id: str,
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> Post:
    """
    Get specific inquiry by ID.
    """
    try:
        inquiry = await admin_service.get_inquiry_by_id(
            inquiry_id=inquiry_id, current_user=current_user
        )
        return inquiry
    except PostNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Inquiry with ID {inquiry_id} not found"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get inquiry: {str(e)}")


@router.put("/inquiries/{inquiry_id}/status")
async def update_inquiry_status(
    inquiry_id: str,
    status_update: InquiryStatusUpdate,
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> Post:
    """
    Update inquiry status.

    - **status**: "resolved" or "rejected"
    """
    # Validate status
    if status_update.status not in ["resolved", "rejected"]:
        raise HTTPException(
            status_code=400, detail="Status must be 'resolved' or 'rejected'"
        )

    try:
        updated_inquiry = await admin_service.update_inquiry_status(
            inquiry_id=inquiry_id,
            new_status=status_update.status,
            current_user=current_user,
        )
        return updated_inquiry
    except PostNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Inquiry with ID {inquiry_id} not found"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update inquiry status: {str(e)}"
        )


@router.get("/posts", response_model=PostListResponse)
async def get_all_posts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    """
    Get all posts for admin management (including deleted ones).

    - **status**: draft, published, archived, deleted, pending, resolved, rejected
    """
    try:
        result = await admin_service.get_all_posts(
            current_user=current_user, page=page, page_size=page_size, status=status
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get posts list: {str(e)}"
        )


@router.post("/posts/{post_id}/status")
async def update_post_status(
    post_id: str,
    status_update: InquiryStatusUpdate,  # Reuse the same model
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> Post:
    """
    Update post status.

    - **status**: draft, published, archived, deleted, pending, resolved, rejected
    """
    # Validate status
    valid_statuses = [
        "draft",
        "published",
        "archived",
        "deleted",
        "pending",
        "resolved",
        "rejected",
    ]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(valid_statuses)}",
        )

    try:
        updated_post = await admin_service.update_inquiry_status(  # Same method works for all posts
            inquiry_id=post_id,
            new_status=status_update.status,
            current_user=current_user,
        )
        return updated_post
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update post status: {str(e)}"
        )


@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: str,
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> User:
    """
    Get user information by ID for admin management.
    """
    try:
        user = await admin_service.get_user_by_id(
            user_id=user_id, current_user=current_user
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Failed to get user: {str(e)}",
        )


@router.put("/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    permission_update: UserPermissionUpdate,
    current_user: User = AdminUser,
    admin_service: AdminService = Depends(get_admin_service),
) -> User:
    """
    Update user permissions for specific pages.

    - **can_write_moving_services**: Allow writing to moving services page
    - **can_write_expert_tips**: Allow writing to expert tips page
    """
    # 최소 하나의 권한 필드가 제공되어야 함
    if (
        permission_update.can_write_moving_services is None
        and permission_update.can_write_expert_tips is None
    ):
        raise HTTPException(
            status_code=400, detail="At least one permission field must be provided"
        )

    try:
        updated_user = await admin_service.update_user_permissions(
            user_id=user_id,
            permission_update=permission_update,
            current_user=current_user,
        )
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Failed to update user permissions: {str(e)}",
        )
