"""
에디터 콘텐츠 처리 관련 API 라우터
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from nadle_backend.models.content import PreviewRequest, PreviewResponse
from nadle_backend.services.content_service import ContentService

router = APIRouter(prefix="/api/content", tags=["content"])

@router.post("/preview", response_model=PreviewResponse)
async def preview_content(request: PreviewRequest):
    """
    콘텐츠 미리보기 API
    
    마크다운 콘텐츠를 HTML로 렌더링하여 미리보기 제공
    """
    try:
        content_service = ContentService()
        
        # 콘텐츠 처리
        processed = content_service.process_content(
            request.content, 
            request.content_type
        )
        
        return PreviewResponse(
            content_rendered=processed.rendered_html,
            word_count=processed.metadata.word_count,
            reading_time=processed.metadata.reading_time,
            inline_images=processed.metadata.inline_images
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/test")
async def test_content_api():
    """테스트용 간단한 엔드포인트"""
    return {"message": "Content API is working", "status": "ok"}