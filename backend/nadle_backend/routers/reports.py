"""Reports router for API endpoints."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from nadle_backend.models.core import User
from nadle_backend.schemas.reports import ReportCreate, ReportResponse, ReportListResponse
from nadle_backend.services.reports_service import ReportsService
from nadle_backend.dependencies.auth import (
    get_current_active_user,
    get_optional_current_active_user,
)
from nadle_backend.exceptions.post import PostNotFoundError
from nadle_backend.exceptions.comment import CommentNotFoundError


# Create router
router = APIRouter(tags=["reports"])


def get_reports_service() -> ReportsService:
    """Get reports service dependency."""
    return ReportsService()


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "reports"}


@router.post("/post/{post_id}", response_model=ReportResponse)
async def report_post(
    post_id: str,
    report_data: ReportCreate,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    reports_service: ReportsService = Depends(get_reports_service),
):
    """게시글 신고하기
    
    Args:
        post_id: 신고할 게시글 ID
        report_data: 신고 내용
        current_user: 현재 사용자 (선택적, 비로그인 사용자도 신고 가능)
    
    Returns:
        생성된 신고 정보
    """
    try:
        report_post = await reports_service.create_post_report(
            post_id=post_id,
            content=report_data.content,
            current_user=current_user
        )
        
        return ReportResponse(
            id=str(report_post.id),
            target_type="post",
            target_id=post_id,
            content=report_post.content,
            reporter_id=report_post.author_id,
            created_at=report_post.created_at,
            status=report_post.status
        )
        
    except PostNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create post report: {str(e)}"
        )


@router.post("/comment/{comment_id}", response_model=ReportResponse)
async def report_comment(
    comment_id: str,
    report_data: ReportCreate,
    current_user: Optional[User] = Depends(get_optional_current_active_user),
    reports_service: ReportsService = Depends(get_reports_service),
):
    """댓글 신고하기
    
    Args:
        comment_id: 신고할 댓글 ID
        report_data: 신고 내용
        current_user: 현재 사용자 (선택적, 비로그인 사용자도 신고 가능)
    
    Returns:
        생성된 신고 정보
    """
    try:
        report_post = await reports_service.create_comment_report(
            comment_id=comment_id,
            content=report_data.content,
            current_user=current_user
        )
        
        return ReportResponse(
            id=str(report_post.id),
            target_type="comment",
            target_id=comment_id,
            content=report_post.content,
            reporter_id=report_post.author_id,
            created_at=report_post.created_at,
            status=report_post.status
        )
        
    except CommentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment report: {str(e)}"
        )


@router.get("/", response_model=ReportListResponse)
async def get_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    target_type: Optional[str] = Query(None, description="Filter by target type (post/comment)"),
    current_user: User = Depends(get_current_active_user),
    reports_service: ReportsService = Depends(get_reports_service),
):
    """신고 목록 조회 (관리자용)
    
    Args:
        page: 페이지 번호
        page_size: 페이지 크기
        status_filter: 상태 필터
        target_type: 신고 대상 타입 필터
        current_user: 현재 사용자 (관리자 권한 필요)
    
    Returns:
        페이지네이션된 신고 목록
    """
    # 관리자 권한 체크
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        result = await reports_service.get_reports(
            page=page,
            page_size=page_size,
            status=status_filter,
            target_type=target_type
        )
        
        # Post 객체들을 ReportResponse로 변환
        report_responses = []
        for post in result["items"]:
            # 메타데이터에서 target 정보 추출 (호환성 고려)
            target_type = "unknown"
            target_id = ""
            metadata = post.get("metadata")
            if metadata:
                if isinstance(metadata, dict):
                    target_type = metadata.get("target_type") or "unknown"
                    target_id = metadata.get("target_id") or ""
                else:
                    target_type = getattr(metadata, "target_type", None) or "unknown"
                    target_id = getattr(metadata, "target_id", None) or ""
            
            # None 값 체크 및 기본값 설정
            if not target_type:
                target_type = "unknown"
            if not target_id:
                target_id = ""
                
            report_responses.append(ReportResponse(
                id=str(post.get("id")),
                target_type=target_type,
                target_id=target_id,
                content=post.get("content"),
                reporter_id=post.get("author_id"),
                created_at=post.get("created_at"),
                status=post.get("status"),
                author=post.get("author")  # author 정보 추가
            ))
        
        return ReportListResponse(
            items=report_responses,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reports: {str(e)}"
        )


@router.put("/{report_id}/status")
async def update_report_status(
    report_id: str,
    new_status: str,
    current_user: User = Depends(get_current_active_user),
    reports_service: ReportsService = Depends(get_reports_service),
):
    """신고 상태 업데이트 (관리자용)
    
    Args:
        report_id: 신고 ID
        new_status: 새로운 상태
        current_user: 현재 사용자 (관리자 권한 필요)
    
    Returns:
        업데이트된 신고 정보
    """
    # 관리자 권한 체크
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        updated_report = await reports_service.update_report_status(
            report_id=report_id,
            new_status=new_status
        )
        
        # 메타데이터에서 target 정보 추출 (호환성 고려)
        target_type = "unknown"
        target_id = ""
        try:
            if updated_report.metadata:
                target_type = getattr(updated_report.metadata, "target_type", None) or "unknown"
                target_id = getattr(updated_report.metadata, "target_id", None) or ""
        except (AttributeError, TypeError):
            # metadata 접근 실패 시 기본값 유지
            pass
            
        return ReportResponse(
            id=str(updated_report.id),
            target_type=target_type,
            target_id=target_id,
            content=updated_report.content,
            reporter_id=updated_report.author_id,
            created_at=updated_report.created_at,
            status=updated_report.status
        )
        
    except PostNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report status: {str(e)}"
        )