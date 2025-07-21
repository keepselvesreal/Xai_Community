"""
Report schemas for request/response validation.
신고 기능을 위한 스키마 정의
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ReportCreate(BaseModel):
    """신고 생성 요청 스키마"""
    content: str = Field(..., min_length=1, max_length=1000, description="신고 내용")


class ReportResponse(BaseModel):
    """신고 응답 스키마"""
    id: str = Field(..., description="신고 ID")
    target_type: str = Field(default="unknown", description="신고 대상 타입 (post/comment)")
    target_id: str = Field(default="", description="신고 대상 ID")
    content: str = Field(..., description="신고 내용")
    reporter_id: str = Field(..., description="신고자 ID")
    created_at: datetime = Field(..., description="신고 생성 시간")
    status: str = Field(..., description="신고 처리 상태")
    author: Optional[Dict[str, Any]] = Field(None, description="신고자 정보")

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """신고 목록 응답 스키마"""
    items: list[ReportResponse] = Field(..., description="신고 목록")
    total: int = Field(..., description="총 신고 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="총 페이지 수")

    class Config:
        from_attributes = True