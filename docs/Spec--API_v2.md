# API 엔드포인트 명세서 v2 (실제 구현 반영)

**작성일**: 2025-06-29  
**업데이트**: 실제 구현된 FastAPI 엔드포인트 및 누락된 기능 반영

## 📝 실제 구현된 API 엔드포인트 구조

### 라우터별 구조
```
Authentication (/auth):
├── POST   /auth/register
├── POST   /auth/login
├── POST   /auth/refresh
├── GET    /auth/profile
├── PUT    /auth/profile
├── POST   /auth/change-password
├── POST   /auth/deactivate
├── GET    /auth/admin/users
├── POST   /auth/admin/users/{id}/suspend
├── POST   /auth/admin/users/{id}/activate
└── DELETE /auth/admin/users/{id}

Posts (/api/posts):
├── GET    /api/posts/search
├── GET    /api/posts
├── GET    /api/posts/{slug}
├── POST   /api/posts
├── PUT    /api/posts/{slug}
├── DELETE /api/posts/{slug}
├── POST   /api/posts/{slug}/like
├── POST   /api/posts/{slug}/dislike
├── POST   /api/posts/{slug}/bookmark
└── GET    /api/posts/{slug}/stats

Comments (/api/posts/{slug}/comments):
├── GET    /api/posts/{slug}/comments
├── POST   /api/posts/{slug}/comments
├── POST   /api/posts/{slug}/comments/{id}/replies
├── PUT    /api/posts/{slug}/comments/{id}
├── DELETE /api/posts/{slug}/comments/{id}
├── POST   /api/posts/{slug}/comments/{id}/like
└── POST   /api/posts/{slug}/comments/{id}/dislike

Files (/api/files):
├── POST   /api/files/upload
├── GET    /api/files/{file_id}
├── GET    /api/files/{file_id}/info
└── GET    /api/files/health

Content (/api/content):
├── POST   /api/content/preview
└── GET    /api/content/test
```

---

## 1. 인증 API (Authentication)

### POST /auth/register (회원가입)

**Request Body:**
```typescript
interface RegisterRequest {
  email: string;                // required, email format
  user_handle: string;          // required, unique
  password: string;             // required, min 8자
  full_name?: string;           // optional
}
```

**Response:**
```typescript
interface UserResponse {
  id: string;
  email: string;
  user_handle: string;
  full_name?: string;
  role: "USER" | "ADMIN";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### POST /auth/login (로그인)

**Request Body:**
```typescript
interface LoginRequest {
  email: string;                // required
  password: string;             // required
}
```

**Response:**
```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;           // seconds
  user: UserResponse;
}
```

### POST /auth/refresh (토큰 갱신)

**Request Body:**
```typescript
interface RefreshRequest {
  refresh_token: string;        // required
}
```

**Response:**
```typescript
interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}
```

### GET /auth/profile (프로필 조회)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface UserResponse {
  // 위와 동일
}
```

### PUT /auth/profile (프로필 수정)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface ProfileUpdateRequest {
  user_handle?: string;         // optional, unique
  full_name?: string;           // optional
}
```

**Response:**
```typescript
interface UserResponse {
  // 위와 동일
}
```

### POST /auth/change-password (비밀번호 변경)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface ChangePasswordRequest {
  current_password: string;     // required
  new_password: string;         // required, min 8자
}
```

**Response:**
```typescript
interface MessageResponse {
  message: string;
}
```

### POST /auth/deactivate (계정 비활성화)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface DeactivateRequest {
  password: string;             // required
  reason?: string;              // optional
}
```

**Response:**
```typescript
interface MessageResponse {
  message: string;
}
```

## 1.1 관리자 API (Admin Only)

### GET /auth/admin/users (사용자 목록 조회)

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
```typescript
interface AdminUserListQuery {
  page?: number;                // default: 1
  limit?: number;               // default: 20, max: 100
  is_active?: boolean;          // 활성 상태 필터
  role?: "USER" | "ADMIN";      // 역할 필터
}
```

**Response:**
```typescript
interface AdminUserListResponse {
  users: UserResponse[];
  pagination: PaginationInfo;
}
```

### POST /auth/admin/users/{id}/suspend (사용자 정지)

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```typescript
interface SuspendUserRequest {
  reason: string;               // required
  duration_days?: number;       // optional, permanent if not provided
}
```

### POST /auth/admin/users/{id}/activate (사용자 활성화)

**Headers:** `Authorization: Bearer <admin_token>`

### DELETE /auth/admin/users/{id} (사용자 삭제)

**Headers:** `Authorization: Bearer <admin_token>`

---

## 2. 게시글 API (Posts)

### GET /api/posts/search (게시글 검색)

**Query Parameters:**
```typescript
interface SearchQuery {
  q: string;                    // 검색어 (required)
  service?: ServiceType;        // 서비스 타입 필터
  page?: number;                // 페이지 번호
  limit?: number;               // 페이지 크기
}
```

**Response:**
```typescript
interface PostListResponse {
  posts: PostListItem[];
  pagination: PaginationInfo;
}
```

### GET /api/posts (게시글 목록 조회)

**Query Parameters:**
```typescript
interface PostListQuery {
  service?: ServiceType;        // 서비스 타입 필터
  author_id?: string;           // 작성자 ID 필터
  page?: number;                // 페이지 번호 (default: 1)
  limit?: number;               // 페이지 크기 (default: 20, max: 100)
}
```

**Response:**
```typescript
interface PostListResponse {
  posts: PostListItem[];
  pagination: PaginationInfo;
}

interface PostListItem {
  id: string;
  title: string;
  slug: string;
  author_id: string;
  service: ServiceType;
  metadata: PostMetadata;
  stats: {
    view_count: number;
    like_count: number;
    dislike_count: number;
    comment_count: number;
    bookmark_count: number;
  };
  created_at: string;
  updated_at: string;
}
```

### GET /api/posts/{slug} (게시글 상세 조회)

**Response:**
```typescript
interface PostDetailResponse {
  id: string;
  title: string;
  slug: string;
  author_id: string;
  content: string;
  service: ServiceType;
  metadata: PostMetadata;
  stats: {
    view_count: number;
    like_count: number;
    dislike_count: number;
    comment_count: number;
    bookmark_count: number;
  };
  user_reaction?: {             // 로그인한 사용자인 경우
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
  created_at: string;
  updated_at: string;
}
```

### POST /api/posts (게시글 생성)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface CreatePostRequest {
  title: string;                // required, max 200자
  content: string;              // required, min 1자
  service: ServiceType;         // required
  metadata: PostMetadata;       // required
}

interface PostMetadata {
  type: string;
  category?: string;
  tags?: string[];
  summary?: string;
  thumbnail?: string;
  attachments?: string[];
}
```

**Response:**
```typescript
interface PostDetailResponse {
  // 위와 동일
}
```

### PUT /api/posts/{slug} (게시글 수정)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface UpdatePostRequest {
  title?: string;               // optional, max 200자
  content?: string;             // optional, min 1자
  metadata?: PostMetadata;      // optional
}
```

**Response:**
```typescript
interface PostDetailResponse {
  // 위와 동일
}
```

### DELETE /api/posts/{slug} (게시글 삭제)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface DeleteResponse {
  message: string;
  deleted_slug: string;
}
```

### POST /api/posts/{slug}/like (좋아요 토글)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface ReactionResponse {
  action: "liked" | "unliked";
  like_count: number;
  dislike_count: number;
  user_reaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

### POST /api/posts/{slug}/dislike (싫어요 토글)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface ReactionResponse {
  action: "disliked" | "undisliked";
  like_count: number;
  dislike_count: number;
  user_reaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

### POST /api/posts/{slug}/bookmark (북마크 토글)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface ReactionResponse {
  action: "bookmarked" | "unbookmarked";
  bookmark_count: number;
  user_reaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

### GET /api/posts/{slug}/stats (게시글 통계 조회)

**Response:**
```typescript
interface StatsResponse {
  view_count: number;
  like_count: number;
  dislike_count: number;
  comment_count: number;
  bookmark_count: number;
  user_reaction?: {             // 로그인한 사용자인 경우
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

---

## 3. 댓글 API (Comments)

### GET /api/posts/{slug}/comments (댓글 목록 조회)

**Query Parameters:**
```typescript
interface CommentListQuery {
  page?: number;                // 페이지 번호 (default: 1)
  limit?: number;               // 페이지 크기 (default: 50, max: 100)
}
```

**Response:**
```typescript
interface CommentListResponse {
  comments: CommentDetail[];
  pagination: PaginationInfo;
}

interface CommentDetail {
  id: string;
  author_id: string;
  content: string;
  parent_id?: string;
  status: CommentStatus;
  like_count: number;
  dislike_count: number;
  reply_count: number;
  user_reaction?: {
    liked: boolean;
    disliked: boolean;
  };
  created_at: string;
  updated_at: string;
}
```

### POST /api/posts/{slug}/comments (댓글 생성)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface CreateCommentRequest {
  content: string;              // required, max 1000자
}
```

**Response:**
```typescript
interface CommentDetail {
  // 위와 동일
}
```

### POST /api/posts/{slug}/comments/{id}/replies (대댓글 생성)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface CreateReplyRequest {
  content: string;              // required, max 1000자
}
```

**Response:**
```typescript
interface CommentDetail {
  // 위와 동일 (parent_id가 설정됨)
}
```

### PUT /api/posts/{slug}/comments/{id} (댓글 수정)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface UpdateCommentRequest {
  content: string;              // required, max 1000자
}
```

**Response:**
```typescript
interface CommentDetail {
  // 위와 동일
}
```

### DELETE /api/posts/{slug}/comments/{id} (댓글 삭제)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface DeleteResponse {
  message: string;
  deleted_id: string;
}
```

### POST /api/posts/{slug}/comments/{id}/like (댓글 좋아요 토글)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface CommentReactionResponse {
  action: "liked" | "unliked";
  like_count: number;
  dislike_count: number;
  user_reaction: {
    liked: boolean;
    disliked: boolean;
  };
}
```

### POST /api/posts/{slug}/comments/{id}/dislike (댓글 싫어요 토글)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface CommentReactionResponse {
  action: "disliked" | "undisliked";
  like_count: number;
  dislike_count: number;
  user_reaction: {
    liked: boolean;
    disliked: boolean;
  };
}
```

---

## 4. 파일 API (Files)

### POST /api/files/upload (파일 업로드)

**Headers:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data`
```typescript
interface FileUploadRequest {
  file: File;                   // required, max 10MB
  description?: string;         // optional
}
```

**Response:**
```typescript
interface FileUploadResponse {
  file_id: string;
  filename: string;
  content_type: string;
  size: number;
  url: string;
  created_at: string;
}
```

### GET /api/files/{file_id} (파일 다운로드)

**Response:** Binary file content

### GET /api/files/{file_id}/info (파일 정보 조회)

**Response:**
```typescript
interface FileInfoResponse {
  file_id: string;
  filename: string;
  content_type: string;
  size: number;
  uploader_id: string;
  created_at: string;
  metadata?: {
    width?: number;
    height?: number;
    duration?: number;
  };
}
```

### GET /api/files/health (파일 서비스 상태 확인)

**Response:**
```typescript
interface HealthResponse {
  status: "healthy" | "unhealthy";
  storage_available: boolean;
  upload_limit: number;         // bytes
}
```

---

## 5. 콘텐츠 API (Content)

### POST /api/content/preview (콘텐츠 미리보기)

**Request Body:**
```typescript
interface ContentPreviewRequest {
  content: string;              // HTML content
  format?: "html" | "markdown"; // default: "html"
}
```

**Response:**
```typescript
interface ContentPreviewResponse {
  processed_content: string;
  word_count: number;
  estimated_read_time: number;  // minutes
  has_images: boolean;
  has_links: boolean;
}
```

### GET /api/content/test (콘텐츠 처리 테스트)

**Response:**
```typescript
interface ContentTestResponse {
  status: "ok";
  processor_version: string;
  supported_formats: string[];
}
```

---

## 6. 공통 데이터 타입

### ServiceType
```typescript
type ServiceType = 
  | "GLOABL_CHAT" 
  | "INHA_EVERYTIME" 
  | "INHA_NOTICE" 
  | "INHA_BAMBOO" 
  | "GACHON_EVERYTIME" 
  | "GACHON_NOTICE" 
  | "GACHON_BAMBOO" 
  | "SUNGKYUL_EVERYTIME" 
  | "SUNGKYUL_NOTICE" 
  | "SUNGKYUL_BAMBOO";
```

### CommentStatus
```typescript
type CommentStatus = "ACTIVE" | "DELETED" | "HIDDEN";
```

### PaginationInfo
```typescript
interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}
```

---

## 7. 에러 응답

### 표준 에러 형식 (FastAPI 기본 형식)
```typescript
interface ErrorResponse {
  detail: string;               // 에러 메시지
}

// 422 Validation Error의 경우
interface ValidationErrorResponse {
  detail: Array<{
    loc: Array<string | number>;  // 에러 위치
    msg: string;                  // 에러 메시지
    type: string;                 // 에러 타입
  }>;
}
```

### HTTP 상태 코드

| Status | 설명 | 예시 |
|--------|------|------|
| 200 | 성공 | 정상 응답 |
| 201 | 생성됨 | 게시글/댓글 생성 성공 |
| 400 | 잘못된 요청 | `{"detail": "Invalid request format"}` |
| 401 | 인증 필요 | `{"detail": "Not authenticated"}` |
| 403 | 권한 없음 | `{"detail": "작성자만 수정할 수 있습니다"}` |
| 404 | 리소스 없음 | `{"detail": "Post not found"}` |
| 409 | 충돌 | `{"detail": "이미 등록된 이메일입니다"}` |
| 422 | 입력 검증 실패 | ValidationErrorResponse |
| 500 | 서버 오류 | `{"detail": "Internal server error"}` |

---

## 8. 인증 및 권한

### 인증 방식
- **JWT Bearer Token**: `Authorization: Bearer <access_token>`
- **토큰 만료**: Access Token (30분), Refresh Token (7일)
- **자동 갱신**: `/auth/refresh` 엔드포인트 사용

### 권한 규칙
- **게시글 수정/삭제**: 작성자 또는 관리자
- **댓글 수정/삭제**: 작성자 또는 관리자
- **관리자 기능**: ADMIN 역할만 접근 가능
- **반응 기능**: 로그인한 사용자만 가능
- **파일 업로드**: 로그인한 사용자만 가능

---

## 9. 실제 구현 특징

### ✅ 구현 완료된 기능
1. **완전한 인증 시스템**: 회원가입, 로그인, 토큰 갱신, 프로필 관리
2. **관리자 기능**: 사용자 관리, 정지, 활성화, 삭제
3. **게시글 CRUD**: 생성, 조회, 수정, 삭제, 검색
4. **반응 시스템**: 좋아요, 싫어요, 북마크 토글
5. **댓글 시스템**: 댓글, 대댓글, 반응 기능
6. **파일 업로드**: 이미지 및 파일 업로드, 메타데이터 관리
7. **콘텐츠 처리**: 리치 텍스트 에디터, 미리보기

### 🔧 기술적 특징
1. **FastAPI 기반**: 자동 API 문서화, 타입 검증
2. **JWT 인증**: 액세스/리프레시 토큰 기반 보안
3. **MongoDB + Beanie**: 비동기 ODM, 타입 안전성
4. **Pydantic 검증**: 요청/응답 데이터 자동 검증
5. **CORS 지원**: 프론트엔드 통합 지원
6. **에러 처리**: 일관된 에러 응답 형식

이 명세서는 **실제 구현된 백엔드 API**의 정확한 반영이며, 프론트엔드 개발 시 신뢰할 수 있는 참조 문서입니다.