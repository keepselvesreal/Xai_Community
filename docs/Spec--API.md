# API 엔드포인트 명세서

## 1. 게시글 기본 API

| Method | Endpoint | 설명 | 인증 필요 |
|--------|----------|------|-----------|
| GET | `/api/posts` | 게시글 목록 조회 | No |
| GET | `/api/posts/search` | 게시글 검색 | No |
| GET | `/api/posts/:slug` | 게시글 상세 조회 | No |
| POST | `/api/posts` | 게시글 생성 | Yes |
| PUT | `/api/posts/:slug` | 게시글 수정 | Yes |
| DELETE | `/api/posts/:slug` | 게시글 삭제 | Yes |

### GET /api/posts (게시글 목록 조회)

**Query Parameters:**
```typescript
interface PostListQuery {
  type?: string;                // 게시글 타입 필터링 (예: "입주 정보", "생활 정보", "이야기")
  author?: string;              // 작성자 user_handle 필터링
  visibility?: "public" | "private"; // 공개 여부
  page?: number;                // 페이지 번호 (default: 1)
  limit?: number;               // 페이지 크기 (default: 20, max: 100)
  sortBy?: "createdAt" | "updatedAt" | "viewCount" | "likeCount"; // 정렬 기준
  sortOrder?: "asc" | "desc";   // 정렬 순서 (default: desc)
}
```

**Response:**
```typescript
interface PostListResponse {
  posts: PostListItem[];
  pagination: PaginationInfo;
}
```

### GET /api/posts/search (게시글 검색)

**Query Parameters:**
```typescript
interface SearchQuery {
  q: string;                    // 검색어 (required)
  type?: string;                // 게시글 타입 필터링 (예: "입주 정보", "생활 정보")
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

### GET /api/posts/:slug (게시글 상세 조회)

**Response:**
```typescript
interface PostDetailResponse {
  id: string;
  title: string;
  slug: string;
  authorId: string;
  content: string;
  service: ServiceType;
  metadata: PostMetadata;
  stats: {
    viewCount: number;
    likeCount: number;
    dislikeCount: number;
    commentCount: number;
    bookmarkCount: number;
  };
  userReaction?: {              // 로그인한 사용자인 경우
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
  createdAt: Date;
  updatedAt: Date;
}
```

### POST /api/posts (게시글 생성)

**Request Body:**
```typescript
interface CreatePostRequest {
  title: string;                // required, max 200자
  content: string;              // required, min 30자
  service: ServiceType;         // required
  metadata: {
    type: string;               // required
    tags?: string[];            // max 3개
    attachments?: string[];     // 이미지 URL 배열
    thumbnail?: string;
    visibility?: "public" | "private";
  };
}
```

**Response:**
```typescript
interface PostDetailResponse {
  // 위와 동일
}
```

### PUT /api/posts/:slug (게시글 수정)

**Request Body:**
```typescript
interface UpdatePostRequest {
  title?: string;               // optional, max 200자
  content?: string;             // optional, min 30자
  metadata?: {
    type?: string;
    tags?: string[];
    attachments?: string[];
    thumbnail?: string;
    visibility?: "public" | "private";
  };
}
```

**Response:**
```typescript
interface PostDetailResponse {
  // 위와 동일
}
```

### DELETE /api/posts/:slug (게시글 삭제)

**Response:**
```typescript
interface DeleteResponse {
  message: string;
  deletedId: string;
}
```

## 2. 게시글 반응 API (좋아요/싫어요/북마크)

| Method | Endpoint | 설명 | 인증 필요 |
|--------|----------|------|-----------|
| GET | `/api/posts/:slug/stats` | 게시글 통계 조회 | No |
| POST | `/api/posts/:slug/like` | 좋아요 토글 (좋아요↔취소) | Yes |
| POST | `/api/posts/:slug/dislike` | 싫어요 토글 (싫어요↔취소) | Yes |
| POST | `/api/posts/:slug/bookmark` | 북마크 토글 (북마크↔취소) | Yes |

### GET /api/posts/:slug/stats (통계 조회)

**Response:**
```typescript
interface StatsResponse {
  viewCount: number;
  likeCount: number;
  dislikeCount: number;
  commentCount: number;
  bookmarkCount: number;
  userReaction?: {              // 로그인한 사용자인 경우
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

### POST /api/posts/:slug/like (좋아요 토글)

**기능**: 현재 상태에 따라 좋아요 추가/제거 자동 처리
- 좋아요 안 된 상태 → 좋아요 추가
- 좋아요 된 상태 → 좋아요 제거
- 싫어요 된 상태 → 싫어요 제거 후 좋아요 추가

**Response:**
```typescript
interface ReactionResponse {
  action: "liked" | "unliked";  // 수행된 액션
  likeCount: number;
  dislikeCount: number;
  userReaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

### POST /api/posts/:slug/dislike (싫어요 토글)

**기능**: 현재 상태에 따라 싫어요 추가/제거 자동 처리
- 싫어요 안 된 상태 → 싫어요 추가
- 싫어요 된 상태 → 싫어요 제거  
- 좋아요 된 상태 → 좋아요 제거 후 싫어요 추가

**Response:**
```typescript
interface ReactionResponse {
  action: "disliked" | "undisliked";
  likeCount: number;
  dislikeCount: number;
  userReaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

### POST /api/posts/:slug/bookmark (북마크 토글)

**기능**: 현재 상태에 따라 북마크 추가/제거 자동 처리
- 북마크 안 된 상태 → 북마크 추가
- 북마크 된 상태 → 북마크 제거

**Response:**
```typescript
interface ReactionResponse {
  action: "bookmarked" | "unbookmarked";
  bookmarkCount: number;
  userReaction: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
}
```

## 3. 댓글 API

| Method | Endpoint | 설명 | 인증 필요 |
|--------|----------|------|-----------|
| GET | `/api/posts/:slug/comments` | 댓글 목록 조회 | No |
| POST | `/api/posts/:slug/comments` | 댓글 생성 | Yes |
| PUT | `/api/posts/:slug/comments/:commentId` | 댓글 수정 | Yes |
| DELETE | `/api/posts/:slug/comments/:commentId` | 댓글 삭제 | Yes |
| POST | `/api/posts/:slug/comments/:commentId/replies` | 대댓글 생성 | Yes |
| POST | `/api/posts/:slug/comments/:commentId/like` | 댓글 좋아요 | Yes |
| POST | `/api/posts/:slug/comments/:commentId/dislike` | 댓글 싫어요 | Yes |

### GET /api/posts/:slug/comments (댓글 목록 조회)

**Query Parameters:**
```typescript
interface CommentListQuery {
  page?: number;                // 페이지 번호 (default: 1)
  limit?: number;               // 페이지 크기 (default: 50, max: 100)
  sortBy?: "createdAt" | "likeCount"; // 정렬 기준
  sortOrder?: "asc" | "desc";   // 정렬 순서
}
```

**Response:**
```typescript
interface CommentListResponse {
  comments: CommentDetail[];
  pagination: PaginationInfo;
}
```

### POST /api/posts/:slug/comments (댓글 생성)

**Request Body:**
```typescript
interface CreateCommentRequest {
  content: string;              // required, max 1000자
  parentCommentId?: string;     // 대댓글인 경우
}
```

**Response:**
```typescript
interface CommentDetail {
  id: string;
  authorId: string;
  content: string;
  parentCommentId?: string;
  status: CommentStatus;
  likeCount: number;
  dislikeCount: number;
  replyCount: number;
  userReaction?: {
    liked: boolean;
    disliked: boolean;
  };
  createdAt: Date;
  updatedAt: Date;
}
```

### PUT /api/posts/:slug/comments/:commentId (댓글 수정)

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

### DELETE /api/posts/:slug/comments/:commentId (댓글 삭제)

**Response:**
```typescript
interface DeleteResponse {
  message: string;
  deletedId: string;
}
```

### POST /api/posts/:slug/comments/:commentId/replies (대댓글 생성)

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

### POST /api/posts/:slug/comments/:commentId/like (댓글 좋아요)

**Response:**
```typescript
interface CommentReactionResponse {
  action: "liked" | "unliked";
  likeCount: number;
  dislikeCount: number;
  userReaction: {
    liked: boolean;
    disliked: boolean;
  };
}
```

### POST /api/posts/:slug/comments/:commentId/dislike (댓글 싫어요)

**Response:**
```typescript
interface CommentReactionResponse {
  // 위와 동일
}
```

## 4. 에러 응답

### 표준 에러 형식 (FastAPI 기본 형식 사용)
```typescript
interface ErrorResponse {
  detail: string;               // 에러 메시지 (FastAPI 표준)
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

### 주요 HTTP 상태 코드 및 응답 예시

| HTTP Status | 설명 | 응답 예시 |
|-------------|------|-----------|
| 400 | 잘못된 요청 | `{"detail": "Invalid request format"}` |
| 401 | 인증 필요 | `{"detail": "Not authenticated"}` |
| 403 | 권한 없음 | `{"detail": "게시글 작성자만 접근할 수 있습니다"}` |
| 404 | 리소스 없음 | `{"detail": "Post not found"}` |
| 409 | 리소스 충돌 | `{"detail": "이미 등록된 이메일입니다"}` |
| 422 | 입력 검증 실패 | ValidationErrorResponse 형식 |
| 500 | 서버 오류 | `{"detail": "Internal server error"}` |

## 5. 인증 헤더

### 인증 방식
- Bearer Token (JWT) 사용
- Header: `Authorization: Bearer <token>`

### 권한 규칙
- **게시글 수정/삭제**: 작성자만 가능
- **댓글 수정/삭제**: 작성자만 가능
- **관리자**: 모든 게시글/댓글 관리 가능
- **반응 기능**: 로그인한 사용자만 가능

## 6. 검색 및 필터링

### 검색 기능
- 제목, 내용에서 전문 검색
- 게시글 타입별 필터링 (UI 태그 버튼을 통한 선별)

### 정렬 옵션
- **최신순**: `createdAt desc` (기본값)
- **인기순**: `likeCount desc`
- **조회순**: `viewCount desc`
- **댓글순**: `commentCount desc`

### 페이지네이션
- 기본 페이지 크기: 20개 (게시글), 50개 (댓글)
- 최대 페이지 크기: 100개
- 오프셋 기반 페이지네이션 사용