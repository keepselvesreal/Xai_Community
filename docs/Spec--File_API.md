# 파일 API 명세서

## 목차

1. [파일 업로드 API](#1-파일-업로드-api)
2. [파일 조회 API](#2-파일-조회-api)
3. [파일 메타데이터 API](#3-파일-메타데이터-api)
4. [파일 삭제 API](#4-파일-삭제-api)
5. [연관 파일 조회 API](#5-연관-파일-조회-api)
6. [파일 저장 및 경로 관리](#6-파일-저장-및-경로-관리)
7. [보안 및 검증](#7-보안-및-검증)
8. [에러 처리 및 응답 코드](#8-에러-처리-및-응답-코드)
9. [사용 예시](#9-사용-예시)
10. [추후 고려사항 (MVP 이후)](#10-추후-고려사항-mvp-이후)

---

## 1. 파일 업로드 API

### POST /api/files/upload

**설명**: 이미지 파일을 서버에 업로드하고 파일 메타데이터를 데이터베이스에 저장

**인증**: 필요 (Bearer Token)

**Content-Type**: `multipart/form-data`

**Request Parameters:**
```typescript
interface FileUploadRequest {
  file: File;                   // required, 업로드할 파일
  attachment_type: "post" | "comment" | "profile"; // required
  attached_to_id?: string;      // optional, 미리 연결할 게시글/댓글 ID
}
```

**파일 제한사항:**
- **지원 형식**: jpg, jpeg, png, gif, webp
- **최대 크기**: 5MB
- **개수 제한**: 
  - post: 최대 5개
  - comment: 최대 1개  
  - profile: 최대 1개

**Response (성공 - 201 Created):**
```typescript
interface FileUploadResponse {
  file_id: string;              // MongoDB _id
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  file_type: string;            // MIME type
  attachment_type: string;
  uploaded_by: string;
  created_at: string;           // ISO 8601
  file_url: string;             // 접근 URL (/api/files/{file_id})
}
```

**Response (실패):**
```typescript
// 파일 크기 초과 (413)
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "파일 크기가 5MB를 초과합니다",
    "details": { "max_size": 5242880, "actual_size": 6291456 }
  }
}

// 지원되지 않는 형식 (415)
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE", 
    "message": "지원되지 않는 파일 형식입니다",
    "details": { "allowed_types": ["jpg", "jpeg", "png", "gif", "webp"] }
  }
}

// 개수 제한 초과 (400)
{
  "error": {
    "code": "FILE_COUNT_EXCEEDED",
    "message": "게시글당 최대 5개 파일까지 첨부 가능합니다"
  }
}
```

---

## 2. 파일 조회 API

### GET /api/files/{file_id}

**설명**: 파일 ID로 실제 이미지 파일을 반환 (브라우저에서 이미지 표시용)

**인증**: 불필요 (공개 파일의 경우)

**Path Parameters:**
- `file_id`: string (required) - 파일의 MongoDB _id

**Response Headers:**
```
Content-Type: image/jpeg (파일 형식에 따라)
Content-Length: 1024000
Cache-Control: public, max-age=31536000
ETag: "file_id_hash"
```

**Response:**
- **성공 (200)**: 실제 이미지 파일 바이너리
- **실패 (404)**: 파일을 찾을 수 없음

**Example:**
```html
<!-- HTML에서 사용 예시 -->
<img src="/api/files/64f8a1b2c3d4e5f6789012ab" alt="첨부 이미지">
```

---

## 3. 파일 메타데이터 API

### GET /api/files/{file_id}/info

**설명**: 파일의 메타데이터 정보를 JSON으로 반환

**인증**: 불필요

**Response (성공 - 200):**
```typescript
interface FileInfoResponse {
  file_id: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  attachment_type: string;
  attached_to_id?: string;
  uploaded_by: string;          // 업로더 user_id
  created_at: string;
  file_url: string;
}
```

---

## 4. 파일 삭제 API

### DELETE /api/files/{file_id}

**설명**: 파일을 삭제하고 관련 데이터를 정리

**인증**: 필요 (업로더 본인 또는 관리자만)

**삭제 프로세스:**
1. 권한 검사 (업로더인지 확인)
2. 연관된 posts/comments에서 file_id 제거
3. files 컬렉션에서 문서 삭제
4. 물리적 파일 삭제

**Response (성공 - 200):**
```typescript
interface FileDeleteResponse {
  message: string;              // "파일이 삭제되었습니다"
  deleted_file_id: string;
  cleaned_references: {         // 정리된 참조들
    posts: string[];            // 영향받은 게시글 ID들
    comments: string[];         // 영향받은 댓글 ID들
  }
}
```

**Response (실패):**
```typescript
// 권한 없음 (403)
{
  "error": {
    "code": "FORBIDDEN",
    "message": "파일을 삭제할 권한이 없습니다"
  }
}

// 파일 없음 (404)
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "파일을 찾을 수 없습니다"
  }
}
```

---

## 5. 연관 파일 조회 API

### GET /api/posts/{slug}/files

**설명**: 특정 게시글에 첨부된 모든 파일 목록 조회

**인증**: 불필요

**Response:**
```typescript
interface PostFilesResponse {
  post_id: string;
  files: FileInfoResponse[];
}
```

### GET /api/posts/{slug}/comments/{comment_id}/files

**설명**: 특정 댓글에 첨부된 파일 목록 조회

**Response:**
```typescript
interface CommentFilesResponse {
  comment_id: string;
  files: FileInfoResponse[];
}
```

### GET /api/users/{user_id}/profile-image

**설명**: 사용자 프로필 이미지 조회

**Response:**
```typescript
interface ProfileImageResponse {
  user_id: string;
  profile_image?: FileInfoResponse;  // null이면 기본 이미지 사용
}
```

---

## 6. 파일 저장 및 경로 관리

### 디렉토리 구조
```
uploads/
├── 2024/
│   ├── 01/          # 월별 디렉토리
│   │   ├── posts/
│   │   ├── comments/
│   │   └── profiles/
│   └── 02/
└── temp/            # 임시 업로드 (정리용)
```

### 파일명 규칙
```python
# 저장 파일명 생성 규칙
stored_filename = f"{uuid4()}_{timestamp}.{extension}"
# 예: "a1b2c3d4-e5f6-7890-abcd-ef1234567890_1640995200.jpg"

# 전체 경로
file_path = f"/uploads/{year}/{month:02d}/{attachment_type}/{stored_filename}"
```

### FastAPI 구현 예시
```python
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

def generate_file_path(attachment_type: str, original_filename: str) -> tuple:
    """파일 저장 경로와 파일명 생성"""
    now = datetime.now()
    extension = Path(original_filename).suffix.lower()
    
    # 고유 파일명 생성
    stored_filename = f"{uuid4()}_{int(now.timestamp())}{extension}"
    
    # 디렉토리 경로
    dir_path = f"uploads/{now.year}/{now.month:02d}/{attachment_type}"
    file_path = f"{dir_path}/{stored_filename}"
    
    # 디렉토리 생성
    os.makedirs(dir_path, exist_ok=True)
    
    return file_path, stored_filename
```

---

## 7. 보안 및 검증

### 파일 타입 검증
```python
ALLOWED_MIME_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp']
}

def validate_file_type(file: UploadFile) -> bool:
    """MIME 타입과 확장자 이중 검증"""
    content_type = file.content_type
    filename = file.filename.lower()
    
    if content_type not in ALLOWED_MIME_TYPES:
        return False
        
    allowed_extensions = ALLOWED_MIME_TYPES[content_type]
    return any(filename.endswith(ext) for ext in allowed_extensions)
```

### 악성 파일 차단
- 파일 헤더 검증 (실제 이미지인지 확인)
- 파일명에서 경로 조작 문자 제거
- 실행 가능한 확장자 차단

### Rate Limiting
```python
# 업로드 제한 (사용자당)
- 1분당 10개 파일
- 1시간당 50개 파일  
- 1일당 200개 파일
```

---

## 8. 에러 처리 및 응답 코드

### 표준 에러 형식
```typescript
interface FileErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
  path: string;
}
```

### 파일 관련 에러 코드

| HTTP Status | Error Code | 설명 | 해결 방법 |
|-------------|------------|------|-----------|
| 400 | `INVALID_FILE` | 파일이 첨부되지 않음 | 파일을 선택하세요 |
| 400 | `FILE_COUNT_EXCEEDED` | 첨부 가능 개수 초과 | 파일 개수를 줄이세요 |
| 401 | `UNAUTHORIZED` | 인증 필요 | 로그인하세요 |
| 403 | `FORBIDDEN` | 삭제 권한 없음 | 업로더만 삭제 가능 |
| 404 | `FILE_NOT_FOUND` | 파일을 찾을 수 없음 | 올바른 파일 ID 확인 |
| 413 | `FILE_TOO_LARGE` | 파일 크기 초과 | 5MB 이하 파일 사용 |
| 415 | `UNSUPPORTED_FILE_TYPE` | 지원되지 않는 형식 | jpg, png, gif, webp만 가능 |
| 422 | `VALIDATION_ERROR` | 입력 검증 실패 | 요청 형식 확인 |
| 429 | `RATE_LIMIT_EXCEEDED` | 업로드 제한 초과 | 잠시 후 재시도 |
| 500 | `UPLOAD_FAILED` | 서버 업로드 실패 | 다시 시도하세요 |

---

## 9. 사용 예시

### 프론트엔드 구현 예시

```javascript
// 1. 파일 업로드
async function uploadFile(file, attachmentType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('attachment_type', attachmentType);
  
  const response = await fetch('/api/files/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }
  
  return await response.json();
}

// 2. 게시글 작성 (파일 포함)
async function createPost(title, content, files) {
  // 먼저 모든 파일 업로드
  const fileIds = [];
  for (const file of files) {
    const uploadResult = await uploadFile(file, 'post');
    fileIds.push(uploadResult.file_id);
  }
  
  // 게시글 생성 (파일 ID 포함)
  const response = await fetch('/api/posts/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      title,
      content,
      metadata: {
        file_ids: fileIds
      }
    })
  });
  
  return await response.json();
}
```

### FastAPI 구현 예시

```python
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
import shutil
from pathlib import Path

app = FastAPI()

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    attachment_type: str = Form(...),
    attached_to_id: str = Form(None),
    current_user = Depends(get_current_user)
):
    # 파일 검증
    if not validate_file_type(file):
        raise HTTPException(400, detail="지원되지 않는 파일 형식입니다")
    
    if file.size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(413, detail="파일 크기가 5MB를 초과합니다")
    
    # 파일 저장
    file_path, stored_filename = generate_file_path(attachment_type, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # DB에 메타데이터 저장
    file_doc = {
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "file_path": file_path,
        "file_size": file.size,
        "file_type": file.content_type,
        "attachment_type": attachment_type,
        "attached_to_id": attached_to_id,
        "uploaded_by": current_user.id,
        "created_at": datetime.utcnow()
    }
    
    result = await files_collection.insert_one(file_doc)
    file_doc["file_id"] = str(result.inserted_id)
    file_doc["file_url"] = f"/api/files/{result.inserted_id}"
    
    return file_doc

@app.get("/api/files/{file_id}")
async def get_file(file_id: str):
    # DB에서 파일 정보 조회
    file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
    if not file_doc:
        raise HTTPException(404, detail="파일을 찾을 수 없습니다")
    
    # 파일 반환
    return FileResponse(
        file_doc["file_path"],
        media_type=file_doc["file_type"],
        headers={"Cache-Control": "public, max-age=31536000"}
    )
```

---

## 10. 추후 고려사항 (MVP 이후)

### 클라우드 스토리지 마이그레이션
- AWS S3, Google Cloud Storage 연동
- CDN 적용으로 성능 개선
- 다중 리전 지원

### 이미지 처리
- 썸네일 자동 생성
- 이미지 리사이징/압축
- WebP 자동 변환

### 고급 기능
- 파일 버전 관리
- 임시 저장 (draft) 지원
- 일괄 업로드 API
- 진행률 추적 API