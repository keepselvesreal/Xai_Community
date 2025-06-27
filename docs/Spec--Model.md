# 데이터 모델 정의서

## 1. 기본 타입 정의

### ServiceType
```typescript
type ServiceType = "shopping" | "apartment" | "community";
```

### CommentStatus
```typescript
type CommentStatus = "active" | "deleted" | "hidden" | "pending";
```

## 2. Core 모델

### Post 모델
```typescript
interface Post {
  id: string;                    // UUID
  title: string;                 // required, max 200자
  authorId: string;              // required (UUID)
  content: string;               // required, min 30자 (권장) - 원본 에디터 데이터
  slug: string;                  // URL 친화적 식별자, unique
  service: ServiceType;          // required: 서비스 구분
  createdAt: Date;               // 자동 생성
  updatedAt: Date;               // 자동 업데이트
  metadata: PostMetadata;
  // 에디터 확장 필드 (Rich Text Editor 지원)
  content_type?: "text" | "markdown" | "html"; // optional, default "text"
  content_rendered?: string;     // optional, 렌더링된 HTML (content_type이 markdown인 경우)
  word_count?: number;           // optional, 단어 수 자동 계산
  reading_time?: number;         // optional, 예상 읽기 시간 (분)
}

interface PostMetadata {
  type: string;                  // required: 서비스별 게시글 타입
  tags?: string[];              // optional, max 3개, 각각 max 10자
  attachments?: string[];       // 이미지 URL 배열 (.jpg/.png/.gif/.webp)
  thumbnail?: string;           // optional, 대표 이미지 URL
  visibility?: "public" | "private"; // optional, default "public"
}
```

### Comment 모델
```typescript
interface Comment {
  id: string;                   // UUID
  parentType: "post";           // 확장성을 위한 필드
  parentId: string;             // 게시글 ID (slug 아님)
  authorId: string;             // required (UUID)
  content: string;              // required, max 1000자
  parentCommentId?: string;     // 대댓글인 경우 부모 댓글 ID
  createdAt: Date;              // 자동 생성
  updatedAt: Date;              // 자동 업데이트
  status: CommentStatus;        // default "active"
  likeCount: number;            // 좋아요 수 (UserReaction에서 집계)
  dislikeCount: number;         // 싫어요 수 (UserReaction에서 집계)
  replyCount: number;           // 대댓글 수 (자식 댓글 개수)
  metadata?: Record<string, any>; // 확장 가능한 메타데이터
}
```

### PostStats 모델
```typescript
interface PostStats {
  postId: string;
  viewCount: number;            // 조회수 (Post 모델에서 관리)
  likeCount: number;            // 좋아요 수 (UserReaction에서 실시간 집계)
  dislikeCount: number;         // 싫어요 수 (UserReaction에서 실시간 집계)
  commentCount: number;         // 댓글+대댓글 총 개수 (Comment에서 실시간 집계)
  bookmarkCount: number;        // 북마크 수 (UserReaction에서 실시간 집계)
  lastViewedAt: Date;           // 마지막 조회 시간
}
```

**집계 방식**:
- `likeCount`: `UserReaction` 컬렉션에서 `targetType: "post"`, `targetId: postId`, `liked: true` 개수
- `dislikeCount`: `UserReaction` 컬렉션에서 `targetType: "post"`, `targetId: postId`, `disliked: true` 개수  
- `commentCount`: `Comment` 컬렉션에서 `parentId: postId`, `status: "active"` 개수 (대댓글 포함)
- `bookmarkCount`: `UserReaction` 컬렉션에서 `targetType: "post"`, `targetId: postId`, `bookmarked: true` 개수

### UserReaction 모델 (통합형)
```typescript
interface UserReaction {
  userId: string;
  targetType: "post" | "comment"; // 대상 타입 (게시글 또는 댓글)
  targetId: string;             // 대상 ID (게시글 ID 또는 댓글 ID)
  liked: boolean;               // 좋아요 여부
  disliked: boolean;            // 싫어요 여부
  bookmarked: boolean;          // 북마크 여부 (게시글만 해당)
  createdAt: Date;
  updatedAt: Date;
}
```

**설명**: 
- `targetType`으로 게시글과 댓글 반응을 통합 관리
- `targetId`는 게시글 ID 또는 댓글 ID를 저장
- `bookmarked`는 게시글(`targetType: "post"`)에만 적용

## 3. 서비스별 게시글 타입 예시

### 쇼핑몰 Q&A
```typescript
type ShoppingPostType = "상품 문의" | "배송 문의" | "교환/환불" | "기타";
```

### 아파트 커뮤니티
```typescript
type ApartmentPostType = "입주 정보" | "생활 정보" | "이야기";
```

### 일반 커뮤니티
```typescript
type CommunityPostType = "자유게시판" | "질문답변" | "공지사항" | "후기";
```

## 4. API 응답 모델

### PostListItem (목록용)
```typescript
interface PostListItem {
  id: string;
  title: string;
  slug: string;
  authorId: string;
  service: ServiceType;
  metadata: {
    type: string;
    tags?: string[];
    thumbnail?: string;
    visibility: "public" | "private";
  };
  stats: {
    viewCount: number;
    likeCount: number;
    dislikeCount: number;
    commentCount: number;
  };
  createdAt: Date;
  updatedAt: Date;
}
```

### PostDetail (상세용)
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

### CommentDetail
```typescript
interface CommentDetail {
  id: string;
  authorId: string;
  content: string;
  parentCommentId?: string;
  status: CommentStatus;
  likeCount: number;
  dislikeCount: number;
  replyCount: number;           // 대댓글 수
  userReaction?: {
    liked: boolean;
    disliked: boolean;
  };
  createdAt: Date;
  updatedAt: Date;
  replies?: CommentDetail[];    // 대댓글 목록 (1레벨만)
}
```

## 5. 요청 모델

### CreatePostRequest
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

### CreateCommentRequest
```typescript
interface CreateCommentRequest {
  content: string;              // required, max 1000자
  parentCommentId?: string;     // 대댓글인 경우
}
```

## 6. 공통 응답 모델

### PaginationInfo
```typescript
interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}
```

### PostListResponse
```typescript
interface PostListResponse {
  posts: PostListItem[];
  pagination: PaginationInfo;
}
```

### CommentListResponse
```typescript
interface CommentListResponse {
  comments: CommentDetail[];
  pagination: PaginationInfo;
}
```

### StatsResponse
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

### ReactionResponse
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