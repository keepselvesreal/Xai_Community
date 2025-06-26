# Task 3: 파일 업로드 API 확장

**Feature Group**: editor-integration  
**Task 제목**: 파일 업로드 API 확장  
**작성 시각**: 2025-06-26  
**대상 파일**: `backend/src/routers/content_upload.py` (신규 생성)

## 개요

에디터 통합을 위한 전용 파일 업로드 API를 구현합니다. 기존 파일 업로드 시스템을 기반으로 인라인 이미지 업로드, 다중 파일 업로드, 에디터 전용 응답 형식 등을 지원합니다.

## 리스크 정보

**리스크 레벨**: 중간

**리스크 설명**:
- 기존 파일 API와의 일관성 유지 필요
- 업로드 보안 강화 (에디터에서 직접 업로드)
- 동시 업로드 처리 시 성능 이슈
- 임시 파일 관리 및 정리 필요

## Subtask 구성

### Subtask 3.1: 인라인 이미지 업로드

**테스트 함수**: `test_inline_image_upload_endpoint()`

**설명**: 
- 에디터에서 즉시 사용할 수 있는 인라인 이미지 업로드
- 업로드 완료 즉시 마크다운/HTML 형식 응답
- 기존 파일 업로드 로직 재사용

**구현 요구사항**:
```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from src.dependencies.auth import get_current_active_user
from src.services.file_service import FileService
from src.models.core import User

router = APIRouter(prefix="/api/content", tags=["content-upload"])

@router.post("/upload/inline")
async def upload_inline_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    file_service: FileService = Depends(get_file_service)
):
    """인라인 이미지 업로드"""
    try:
        # 기존 파일 업로드 로직 사용
        file_record = await file_service.upload_file(
            file, 
            attachment_type="inline", 
            uploaded_by=str(current_user.id)
        )
        
        # 에디터용 응답 형식
        return {
            "success": True,
            "file_id": file_record.file_id,
            "url": f"/api/files/{file_record.file_id}",
            "filename": file_record.original_filename,
            "size": file_record.file_size,
            "markdown": f"![{file_record.original_filename}](/api/files/{file_record.file_id})",
            "html": f'<img src="/api/files/{file_record.file_id}" alt="{file_record.original_filename}">',
            "timestamp": file_record.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inline upload failed: {str(e)}"
        )
```

**검증 조건**:
- 이미지 파일만 업로드 허용 (jpg, jpeg, png, gif, webp)
- 파일 크기 제한 (5MB)
- 인증된 사용자만 업로드 가능
- 즉시 사용 가능한 URL 반환

### Subtask 3.2: 배치 파일 업로드

**테스트 함수**: `test_batch_file_upload_endpoint()`

**설명**: 
- 여러 파일을 동시에 업로드
- 각 파일별 성공/실패 상태 개별 반환
- 부분 실패 시에도 성공한 파일은 유지

**구현 요구사항**:
```python
from typing import List

@router.post("/upload/batch")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    file_service: FileService = Depends(get_file_service)
):
    """다중 파일 업로드"""
    results = []
    
    for file in files:
        try:
            # 개별 파일 업로드 처리
            file_record = await file_service.upload_file(
                file, 
                attachment_type="batch",
                uploaded_by=str(current_user.id)
            )
            
            results.append({
                "success": True,
                "file_id": file_record.file_id,
                "filename": file_record.original_filename,
                "url": f"/api/files/{file_record.file_id}",
                "markdown": f"![{file_record.original_filename}](/api/files/{file_record.file_id})"
            })
            
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
    
    # 전체 결과 반환
    success_count = sum(1 for r in results if r["success"])
    return {
        "total_files": len(files),
        "success_count": success_count,
        "failure_count": len(files) - success_count,
        "results": results
    }
```

**검증 조건**:
- 최대 10개 파일 동시 업로드
- 개별 파일 검증 (타입, 크기)
- 부분 실패 허용
- 전체 업로드 상태 요약 제공

### Subtask 3.3: 에디터 전용 응답 포맷

**테스트 함수**: `test_editor_response_format()`

**설명**: 
- 다양한 에디터에서 사용할 수 있는 표준 응답 형식
- 마크다운, HTML, JSON 형식 동시 제공
- 메타데이터 포함 (파일 크기, 타입, 업로드 시간)

**구현 요구사항**:
```python
from pydantic import BaseModel
from typing import Optional

class EditorUploadResponse(BaseModel):
    """에디터 업로드 응답 모델"""
    success: bool
    file_id: str
    url: str
    filename: str
    size: int
    content_type: str
    
    # 에디터별 형식
    markdown: str
    html: str
    
    # 메타데이터
    timestamp: str
    uploaded_by: str
    
    # 에러 정보 (실패 시)
    error: Optional[str] = None

class BatchUploadResponse(BaseModel):
    """배치 업로드 응답 모델"""
    total_files: int
    success_count: int
    failure_count: int
    results: List[EditorUploadResponse]
    processing_time: float
```

**검증 조건**:
- 일관된 응답 형식
- 에러 시 명확한 메시지
- 타임스탬프 ISO 형식
- 응답 시간 최적화

### Subtask 3.4: 임시 파일 관리

**테스트 함수**: `test_temporary_file_cleanup()`

**설명**: 
- 업로드 중 생성되는 임시 파일 관리
- 실패한 업로드의 정리
- 정기적인 정리 작업

**구현 요구사항**:
```python
import asyncio
from datetime import datetime, timedelta

class TemporaryFileManager:
    def __init__(self):
        self.temp_files = set()
        
    async def register_temp_file(self, file_path: str):
        """임시 파일 등록"""
        self.temp_files.add(file_path)
        
    async def cleanup_temp_file(self, file_path: str):
        """임시 파일 정리"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            self.temp_files.discard(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    async def cleanup_old_temp_files(self):
        """오래된 임시 파일 정리"""
        # 1시간 이상 된 임시 파일 삭제
        cutoff_time = datetime.now() - timedelta(hours=1)
        # 정리 로직 구현
        pass

# 업로드 엔드포인트에서 사용
temp_manager = TemporaryFileManager()

@router.post("/upload/inline")
async def upload_inline_image(...):
    temp_file_path = None
    try:
        # 임시 파일 생성
        temp_file_path = await create_temp_file(file)
        await temp_manager.register_temp_file(temp_file_path)
        
        # 업로드 처리
        result = await process_upload(temp_file_path)
        
        # 성공 시 임시 파일 정리
        await temp_manager.cleanup_temp_file(temp_file_path)
        
        return result
        
    except Exception as e:
        # 실패 시에도 임시 파일 정리
        if temp_file_path:
            await temp_manager.cleanup_temp_file(temp_file_path)
        raise e
```

**검증 조건**:
- 임시 파일 생성/삭제 추적
- 메모리 누수 방지
- 실패 시 확실한 정리
- 정기적인 정리 작업

## 의존성 정보

**선행 조건**: 
- 기존 파일 업로드 시스템 (`file_upload.py`)
- Task 1 (콘텐츠 모델) - 응답 형식에서 사용

**외부 라이브러리**:
- `fastapi` - 웹 프레임워크
- `python-multipart` - 멀티파트 파일 업로드

**후속 작업**: 
- Task 7에서 프론트엔드 통합
- Task 4, 5에서 인라인 이미지 연결

## 테스트 요구사항

### 단위 테스트
```python
def test_inline_image_upload_endpoint():
    """인라인 이미지 업로드 테스트"""
    # 정상 이미지 업로드
    # 응답 형식 검증
    # 마크다운/HTML 형식 확인
    # 인증 필요 확인
    pass

def test_batch_file_upload_endpoint():
    """배치 업로드 테스트"""
    # 다중 파일 업로드
    # 부분 실패 처리
    # 파일 개수 제한 확인
    # 전체 상태 요약 검증
    pass

def test_editor_response_format():
    """에디터 응답 형식 테스트"""
    # 응답 스키마 검증
    # 메타데이터 포함 확인
    # 에러 응답 형식 확인
    pass

def test_temporary_file_cleanup():
    """임시 파일 정리 테스트"""
    # 임시 파일 생성/삭제
    # 실패 시 정리 확인
    # 메모리 누수 확인
    pass
```

### 통합 테스트
```python
def test_content_upload_integration():
    """콘텐츠 업로드 통합 테스트"""
    # 실제 파일 업로드 플로우
    # 기존 파일 시스템과의 호환성
    # 데이터베이스 연동 확인
    pass

def test_upload_security():
    """업로드 보안 테스트"""
    # 파일 타입 검증
    # 크기 제한 확인
    # 인증 권한 검증
    # 악성 파일 업로드 시도
    pass

def test_upload_performance():
    """업로드 성능 테스트"""
    # 대용량 파일 업로드
    # 동시 업로드 처리
    # 메모리 사용량 모니터링
    pass
```

### API 테스트
```python
def test_api_endpoints():
    """API 엔드포인트 테스트"""
    # POST /api/content/upload/inline
    # POST /api/content/upload/batch
    # 각 엔드포인트의 HTTP 상태 코드
    # 에러 응답 형식
    pass
```

## 구현 참고사항

### 1. 기존 시스템 통합
- 기존 `FileService` 클래스 재사용
- 동일한 파일 저장 구조 유지
- 기존 검증 로직 활용

### 2. 성능 최적화
- 비동기 파일 처리
- 스트리밍 업로드 지원
- 임시 파일 최소화

### 3. 에러 처리
- 명확한 에러 메시지
- 부분 실패 허용
- 복구 가능한 에러 구분

### 4. 모니터링
- 업로드 성공/실패 로깅
- 성능 메트릭 수집
- 용량 사용량 추적

이 Task는 에디터와 파일 시스템을 연결하는 중요한 역할을 하므로 안정성과 사용성을 모두 고려해야 합니다.