# API 엔드포인트 명세서 v3 (입주민 커뮤니티 특화)

**작성일**: 2025-06-30  
**업데이트**: 입주민 커뮤니티 전용 서비스로 특화 및 TDD 통합 완료

## 🆕 v3 주요 변경사항

### ⚠️ **Breaking Changes (v2 → v3)**

#### 1. **ServiceType 대폭 변경**
```diff
- // v2: 다중 플랫폼 지원
- type ServiceType = 
-   | "GLOABL_CHAT" 
-   | "INHA_EVERYTIME" 
-   | "INHA_NOTICE" 
-   | "INHA_BAMBOO" 
-   | "GACHON_EVERYTIME" 
-   | "GACHON_NOTICE" 
-   | "GACHON_BAMBOO" 
-   | "SUNGKYUL_EVERYTIME" 
-   | "SUNGKYUL_NOTICE" 
-   | "SUNGKYUL_BAMBOO";

+ // v3: 입주민 커뮤니티 전용
+ type ServiceType = "residential_community";
```

#### 2. **게시글 메타데이터 구조 개선**
```diff
// v2: 단순한 메타데이터
{
  title: string;
  content: string;
  service: ServiceType;
- type?: string;
- tags?: string[];
}

// v3: 구조화된 메타데이터
{
  title: string;
  content: string;
  service: ServiceType;
+ metadata: {
+   type: string;          // "board" (게시판 타입)
+   category: string;       // "입주 정보" | "생활 정보" | "이야기" (카테고리)
+   tags?: string[];       // 사용자 선택적 태그
+   summary?: string;
+   thumbnail?: string;
+   attachments?: string[];
+ }
}
```

#### 3. **입주민 커뮤니티 게시판 타입 정의**
```typescript
// v3 신규 추가: 카테고리 타입
type BoardCategoryType = "입주 정보" | "생활 정보" | "이야기";
```

### ✅ **새로운 기능**
- **TDD 통합 완료**: 프론트엔드-백엔드 API 완전 호환
- **실제 게시글 작성 기능**: `/board/write` 페이지에서 실제 API 호출
- **카테고리 기반 게시판**: 입주민 전용 카테고리 시스템 (type="board" + category)
- **MongoDB 검증 완료**: 실제 데이터 저장 및 조회 검증
- **🆕 카테고리 태그 표시**: board 페이지에서 category 기반 태그 시스템

### 🔧 **호환성 정보**
- **Frontend**: TDD 기반 완전 통합 완료
- **Backend**: `residential_community` 서비스 타입만 지원
- **Database**: MongoDB Atlas 연동 및 실제 데이터 검증 완료

---

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
├── GET    /api/posts/{slug_or_id}  ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts              ← 🆕 입주민 커뮤니티 전용
├── PUT    /api/posts/{slug_or_id}  ← 🆕 v3.2: slug 또는 ID 지원
├── DELETE /api/posts/{slug_or_id}  ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts/{slug_or_id}/like      ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts/{slug_or_id}/dislike   ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts/{slug_or_id}/bookmark  ← 🆕 v3.2: slug 또는 ID 지원
└── GET    /api/posts/{slug_or_id}/stats     ← 🆕 v3.2: slug 또는 ID 지원

Comments (/api/posts/{slug_or_id}/comments):
├── GET    /api/posts/{slug_or_id}/comments          ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts/{slug_or_id}/comments          ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts/{slug_or_id}/comments/{id}/replies ← 🆕 v3.2: slug 또는 ID 지원
├── PUT    /api/posts/{slug_or_id}/comments/{id}     ← 🆕 v3.2: slug 또는 ID 지원
├── DELETE /api/posts/{slug_or_id}/comments/{id}     ← 🆕 v3.2: slug 또는 ID 지원
├── POST   /api/posts/{slug_or_id}/comments/{id}/like ← 🆕 v3.2: slug 또는 ID 지원
└── POST   /api/posts/{slug_or_id}/comments/{id}/dislike ← 🆕 v3.2: slug 또는 ID 지원

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
  full_name?: string;           // optional (v3: display_name → full_name)
}
```

**Response:**
```typescript
interface UserResponse {
  id: string;
  email: string;
  user_handle: string;
  full_name?: string;           // v3: display_name → full_name
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
  full_name?: string;           // optional (v3: display_name → full_name)
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

## 2. 게시글 API (Posts) - 🆕 입주민 커뮤니티 전용

### GET /api/posts/search (게시글 검색)

**Query Parameters:**
```typescript
interface SearchQuery {
  q: string;                    // 검색어 (required)
  service?: ServiceType;        // v3: "residential_community" only
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
  service?: ServiceType;        // v3: "residential_community" only
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
  id: string;                   // v3: number → string (MongoDB ObjectId)
  title: string;
  slug: string;
  author_id: string;
  service: ServiceType;         // v3: "residential_community"
  metadata: PostMetadata;       // v3: 구조화된 메타데이터
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

### GET /api/posts/{slug_or_id} (게시글 상세 조회)

**Response:**
```typescript
interface PostDetailResponse {
  id: string;                   // v3: number → string
  title: string;
  slug: string;
  author_id: string;
  content: string;
  service: ServiceType;         // v3: "residential_community"
  metadata: PostMetadata;       // v3: 구조화된 메타데이터
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

### 🆕 POST /api/posts (게시글 생성) - 입주민 커뮤니티 전용

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface CreatePostRequest {
  title: string;                // required, max 200자
  content: string;              // required, min 1자
  service: ServiceType;         // required, v3: "residential_community" only
  metadata: PostMetadata;       // required, v3: 구조화된 메타데이터
}

interface PostMetadata {
  type: string;                 // v3: "board" (입주민 게시판)
  category: BoardCategoryType;  // v3: "입주 정보" | "생활 정보" | "이야기"
  tags?: string[];              // optional, max 3개
  summary?: string;             // optional
  thumbnail?: string;           // optional
  attachments?: string[];       // optional
}

// v3 신규: 입주민 커뮤니티 카테고리
type BoardCategoryType = "입주 정보" | "생활 정보" | "이야기";
```

**Response:**
```typescript
interface PostDetailResponse {
  // 위와 동일
}
```

**실제 사용 예시:**
```typescript
// v3: 입주민 커뮤니티 게시글 작성 (카테고리 기반)
{
  "title": "엘리베이터 점검 안내",
  "content": "다음 주 화요일 오전 9시부터 12시까지 엘리베이터 정기점검이 있습니다.",
  "service": "residential_community",
  "metadata": {
    "type": "board",
    "category": "입주 정보",  // ← 카테고리 필수
    "tags": ["점검", "엘리베이터"]
  }
}
```

### PUT /api/posts/{slug_or_id} (게시글 수정)

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```typescript
interface UpdatePostRequest {
  title?: string;               // optional, max 200자
  content?: string;             // optional, min 1자
  metadata?: PostMetadata;      // optional, v3: 구조화된 메타데이터
}
```

**Response:**
```typescript
interface PostDetailResponse {
  // 위와 동일
}
```

### DELETE /api/posts/{slug_or_id} (게시글 삭제)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface DeleteResponse {
  message: string;
  deleted_slug: string;
}
```

### POST /api/posts/{slug_or_id}/like (좋아요 토글)

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

### POST /api/posts/{slug_or_id}/dislike (싫어요 토글)

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

### POST /api/posts/{slug_or_id}/bookmark (북마크 토글)

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

### GET /api/posts/{slug_or_id}/stats (게시글 통계 조회)

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

### GET /api/posts/{slug_or_id}/comments (댓글 목록 조회)

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
  id: string;                   // v3: number → string
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

### POST /api/posts/{slug_or_id}/comments (댓글 생성)

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

### POST /api/posts/{slug_or_id}/comments/{id}/replies (대댓글 생성)

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

### PUT /api/posts/{slug_or_id}/comments/{id} (댓글 수정)

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

### DELETE /api/posts/{slug_or_id}/comments/{id} (댓글 삭제)

**Headers:** `Authorization: Bearer <token>`

**Response:**
```typescript
interface DeleteResponse {
  message: string;
  deleted_id: string;
}
```

### POST /api/posts/{slug_or_id}/comments/{id}/like (댓글 좋아요 토글)

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

### POST /api/posts/{slug_or_id}/comments/{id}/dislike (댓글 싫어요 토글)

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

### 🆕 ServiceType (v3)
```typescript
// v3: 입주민 커뮤니티 전용
type ServiceType = "residential_community";
```

### 🆕 BoardCategoryType (v3 신규)
```typescript
// v3 신규: 입주민 커뮤니티 게시판 카테고리
type BoardCategoryType = "입주 정보" | "생활 정보" | "이야기";
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

## 9. v3 실제 구현 특징

### ✅ 구현 완료된 기능
1. **완전한 인증 시스템**: 회원가입, 로그인, 토큰 갱신, 프로필 관리
2. **관리자 기능**: 사용자 관리, 정지, 활성화, 삭제
3. **🆕 입주민 커뮤니티 게시판**: TDD 기반 완전 통합
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
7. **🆕 TDD 통합**: 테스트 주도 개발로 검증된 안정성

### 🎯 v3 전용 기능
1. **입주민 커뮤니티 특화**: `residential_community` 서비스만 지원
2. **카테고리 시스템**: 입주정보, 생활정보, 이야기 분류
3. **실제 데이터 검증**: MongoDB Atlas 연동 및 실제 저장 확인
4. **프론트엔드 통합**: `/board/write` 페이지에서 실제 API 호출
5. **타입 안전성**: TypeScript 기반 완전한 타입 시스템

### 🔄 마이그레이션 가이드 (v2 → v3)

#### ServiceType 변경
```typescript
// Before (v2)
service: "INHA_EVERYTIME"

// After (v3)
service: "residential_community"
```

#### 게시글 생성 요청 변경
```typescript
// Before (v2)
{
  title: "제목",
  content: "내용",
  service: "INHA_EVERYTIME",
  type: "자유게시판",
  tags: ["태그1", "태그2"]
}

// After (v3)
{
  title: "제목",
  content: "내용",
  service: "residential_community",
  metadata: {
    type: "board",
    category: "입주정보",
    tags: ["태그1", "태그2"]
  }
}
```

---

## 10. 🆕 v3.1 업데이트 (2025-06-30)

### **카테고리 기반 태그 시스템 구현**

#### 변경 사항
1. **Backend PostMetadata 모델 업데이트**:
   ```typescript
   // 기존
   interface PostMetadata {
     type: string;
     tags?: string[];
     // ...
   }

   // 신규 (v3.1)
   interface PostMetadata {
     type: string;          // "board" (게시판 타입)
     category: string;      // "입주 정보" | "생활 정보" | "이야기" (카테고리)
     tags?: string[];       // 사용자 선택적 태그
     // ...
   }
   ```

2. **Frontend board 페이지 개선**:
   - 태그 표시를 `type` 대신 `category` 기반으로 변경
   - 카테고리별 필터링 로직 구현
   - 카테고리별 색상 구분 시스템

#### 데이터 구조 명확화
```typescript
// v3.1 board 페이지 게시글 구조
{
  "metadata": {
    "type": "board",                    // 모든 board 페이지 게시글은 "board"
    "category": "입주 정보",            // 카테고리로 실제 분류
    "tags": ["점검", "엘리베이터"]      // 사용자가 선택적으로 입력
  }
}
```

#### API 응답 예시
```json
{
  "items": [
    {
      "title": "엘리베이터 점검 안내",
      "metadata": {
        "type": "board",
        "category": "입주 정보",
        "tags": ["점검", "시설"]
      }
    }
  ]
}
```

#### 구현 특징
- **type vs category**: `type`은 게시판 종류("board"), `category`는 게시글 분류
- **필터링**: 카테고리 기반 필터링으로 게시글 분류 조회
- **태그 표시**: UI에서 category 값을 태그로 표시
- **하위 호환성**: 기존 게시글은 category=null로 처리

---

## 11. 🆕 v3.2 업데이트 (2025-06-30)

### **ID + 한글 Slug 구현 및 API 엔드포인트 개선**

#### 🔧 주요 변경사항

##### 1. **ID + 한글 Slug 생성 시스템**
```typescript
// 새로운 Slug 형식
// 기존: "엘리베이터-점검-안내" (충돌 가능)
// 신규: "68629582dd98c7381c6b7d19-엘리베이터-점검-안내" (ID + 한글 제목)

interface Post {
  id: string;                    // MongoDB ObjectId
  slug: string;                  // "{id}-{korean-title}" 형식
  title: string;
  // ...
}
```

##### 2. **Slug 생성 규칙**
- **형식**: `{mongodb_objectid}-{korean_title}`
- **한글 지원**: 정규식 `[^a-z0-9\s\-가-힣]`로 한글 문자 보존
- **고유성 보장**: MongoDB ObjectId 접두사로 완전한 고유성
- **URL 안전성**: 특수문자 제거, 공백을 하이픈으로 변환
- **SEO 친화적**: URL에 한글 제목 포함으로 가독성 향상

##### 3. **API 엔드포인트 개선**
모든 게시글 관련 엔드포인트가 **slug와 ID 모두 지원**:

```typescript
// 기존: slug만 지원
GET /api/posts/{slug}

// 신규: slug 또는 ID 모두 지원
GET /api/posts/{slug_or_id}
PUT /api/posts/{slug_or_id}
DELETE /api/posts/{slug_or_id}
POST /api/posts/{slug_or_id}/like
POST /api/posts/{slug_or_id}/dislike
POST /api/posts/{slug_or_id}/bookmark
GET /api/posts/{slug_or_id}/stats
```

#### 📋 업데이트된 API 엔드포인트

##### **GET /api/posts/{slug_or_id} (게시글 상세 조회)**
```typescript
// 요청 예시 (두 방식 모두 동일한 결과)
GET /api/posts/68629582dd98c7381c6b7d19-엘리베이터-점검-안내  // slug
GET /api/posts/68629582dd98c7381c6b7d19                      // id

interface PostDetailResponse {
  id: string;                    // "68629582dd98c7381c6b7d19"
  slug: string;                  // "68629582dd98c7381c6b7d19-엘리베이터-점검-안내"
  title: string;                 // "엘리베이터 점검 안내"
  // ... 기존 필드들
}
```

##### **POST /api/posts/{slug_or_id}/like (반응 시스템)**
```typescript
// 한글 slug로 접근 가능
POST /api/posts/68629582dd98c7381c6b7d19-입주민-커뮤니티-이용-안내/like

interface ReactionResponse {
  message: "Post liked" | "Post like removed";
  like_count: number;
  dislike_count: number;
  user_reaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

#### 🧪 TDD 검증 결과

##### **테스트 커버리지**
- ✅ **17개 단위 테스트**: 한글 slug 생성 로직 검증
- ✅ **7개 통합 테스트**: 게시글 상세 조회 기능 검증
- ✅ **slug 생성 시나리오**: 
  - 한글 제목 처리
  - 영문+한글 혼합 제목
  - 특수문자 제거
  - 공백 하이픈 변환
  - 빈 제목 처리
  - URL 안전성 검증

##### **실제 테스트 데이터**
```json
{
  "id": "68629582dd98c7381c6b7d19",
  "slug": "68629582dd98c7381c6b7d19-입주민-커뮤니티-이용-안내",
  "title": "입주민 커뮤니티 이용 안내"
}

{
  "id": "686296f554b90ab2ea1ab1f2", 
  "slug": "686296f554b90ab2ea1ab1f2-25-06-30-점검5",
  "title": "25-06-30 점검5"
}
```

#### 🔄 마이그레이션 고려사항

##### **기존 게시글 호환성**
- 기존 slug 형식도 계속 지원
- 새로운 게시글은 ID + 한글 형식으로 자동 생성
- API에서 slug/ID 모두 허용하여 하위 호환성 보장

##### **프론트엔드 통합**
```typescript
// 프론트엔드에서 간소화된 접근
// 기존: post.slug || post.id (fallback 로직)
// 신규: post.slug (항상 존재)

<Link to={`/posts/${post.slug}`}>  {/* 단순화 */}
```

#### 💡 구현 특징

##### **백엔드 구현**
1. **PostRepository.create()**: 임시 slug로 생성 후 ID 확정되면 최종 slug 업데이트
2. **한글 정규식**: `[^a-z0-9\s\-가-힣]`로 한글 문자 보존
3. **서비스 레이어**: slug 또는 ID로 조회하는 통합 로직

##### **프론트엔드 통합**
1. **PostCard 컴포넌트**: 불필요한 fallback 로직 제거
2. **Board 페이지**: Remix navigate 사용한 안정적 라우팅
3. **타입 정의**: slug 필드를 필수로 변경

#### 🎯 v3.2 장점

1. **SEO 최적화**: URL에 한글 제목 포함으로 검색 엔진 친화적
2. **사용자 경험**: 의미있는 URL로 접근성 향상  
3. **고유성 보장**: MongoDB ObjectId로 충돌 방지
4. **하위 호환성**: 기존 시스템과 완전 호환
5. **개발 편의성**: slug/ID 양방향 접근으로 유연성 증대

이 명세서는 **실제 구현되고 TDD로 검증된 v3.2 API**의 정확한 반영이며, 입주민 커뮤니티 전용 서비스로 특화된 신뢰할 수 있는 참조 문서입니다.