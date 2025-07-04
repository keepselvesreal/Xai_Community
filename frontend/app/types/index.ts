// 사용자 관련 타입
export interface User {
  id: string;
  _id?: string;  // 백엔드 호환성을 위한 필드
  email: string;
  user_handle?: string;
  full_name?: string;
  name?: string;  // 백엔드 UserResponse 호환
  display_name?: string;  // 백엔드 UserResponse 호환
  bio?: string;  // 백엔드 UserResponse 호환
  avatar_url?: string;  // 백엔드 UserResponse 호환
  status?: "active" | "inactive" | "suspended";  // 백엔드 UserResponse 호환
  created_at: string;
  updated_at: string;
}

export interface AuthToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  expires_in?: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  user_handle: string;
  display_name?: string;
  password: string;
}

// 게시글 관련 타입 (API v3 명세서 기준)
export interface PostMetadata {
  type: string;              // 게시판 타입 (예: "자유게시판")
  category: string;          // 카테고리 (예: "입주정보", "생활정보", "이야기")
  tags?: string[];           // 사용자 태그 (최대 3개)
  summary?: string;          // 요약
  thumbnail?: string;        // 썸네일 URL
  attachments?: string[];    // 첨부파일 URLs
  file_ids?: string[];       // 파일 업로드 IDs (백엔드 호환)
  inline_images?: string[];  // 인라인 이미지 file_ids (백엔드 호환)
  editor_type?: "plain" | "markdown" | "rich"; // 에디터 타입 (백엔드 호환)
  visibility?: "public" | "private"; // 공개 설정 (백엔드 호환)
}

export interface Post {
  id: string;
  title: string;
  content: string;
  slug: string;
  author?: User;
  author_id?: string; // 백엔드 API 응답에서 제공되는 필드
  service: ServiceType;
  metadata: PostMetadata;
  created_at: string;
  updated_at: string;
  stats?: PostStats;
}

export interface PostStats {
  // 백엔드 API v3와 호환되는 필드명 사용
  view_count: number;    // 조회수
  like_count: number;    // 좋아요
  dislike_count: number; // 싫어요
  comment_count: number; // 댓글수
  bookmark_count: number; // 북마크수
  
  // 프론트엔드 호환성을 위한 alias (옵셔널)
  views?: number;        // view_count의 alias
  likes?: number;        // like_count의 alias
  dislikes?: number;     // dislike_count의 alias
  comments?: number;     // comment_count의 alias
  bookmarks?: number;    // bookmark_count의 alias
}

export interface CreatePostRequest {
  title: string;
  content: string;
  service: ServiceType;
  metadata: PostMetadata;
}

export type PostType = "자유게시판" | "질문답변" | "공지사항" | "후기";
export type ServiceType = "residential_community";
export type CategoryType = "입주정보" | "생활정보" | "이야기";

// 댓글 작성자 타입 (백엔드 UserResponse와 동일)
export interface CommentAuthor {
  id: string;
  name?: string;
  email: string;
  user_handle: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  status: "active" | "inactive" | "suspended";
  created_at: string;
  updated_at: string;
}

// 댓글 관련 타입 (백엔드 CommentDetail과 완전 호환)
export interface Comment {
  id: string;                    // 백엔드 CommentDetail의 id
  author_id: string;             // 백엔드 CommentDetail의 author_id  
  author?: CommentAuthor;        // 백엔드 CommentDetail의 author (UserResponse)
  content: string;
  parent_comment_id?: string;    // 백엔드 CommentDetail의 parent_comment_id
  status: "active" | "deleted" | "hidden" | "pending"; // 백엔드 CommentStatus
  like_count: number;            // 백엔드 CommentDetail의 like_count
  dislike_count: number;         // 백엔드 CommentDetail의 dislike_count  
  reply_count: number;           // 백엔드 CommentDetail의 reply_count
  user_reaction?: {              // 백엔드 CommentDetail의 user_reaction
    liked?: boolean;
    disliked?: boolean;
  };
  created_at: string;
  updated_at: string;
  replies?: Comment[];           // 백엔드 CommentDetail의 replies
  
  // 프론트엔드 호환성을 위한 alias (옵셔널)
  post_id?: string;              // 호환성을 위한 필드
  likes?: number;                // like_count의 alias
  dislikes?: number;             // dislike_count의 alias
  parent_id?: string;            // parent_comment_id의 alias
}

export interface CreateCommentRequest {
  content: string;
  parent_comment_id?: string; // 백엔드 호환 필드명
  parent_id?: string;         // 호환성을 위한 alias
  metadata?: { [key: string]: any }; // 메타데이터 필드 추가
}

// 반응 관련 타입
export interface Reaction {
  id: number;
  user_id: string;
  target_id: number;
  target_type: "post" | "comment";
  reaction_type: ReactionType;
  created_at: string;
}

// 개별 반응 타입 (API 요청용)
export type ReactionType = "like" | "dislike" | "bookmark";

// API 응답 타입
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CommentListResponse {
  comments: Comment[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// UI 상태 타입
export interface NotificationState {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
  duration?: number;
}

export interface ModalState {
  isOpen: boolean;
  title?: string;
  content?: React.ReactNode;
  onClose?: () => void;
}

export interface LoadingState {
  [key: string]: boolean;
}

// 폼 관련 타입
export interface FormState {
  isSubmitting: boolean;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}

// 세션 정보 타입
export interface SessionInfo {
  loginTime: Date | null;
  refreshCount: number;
  maxRefreshCount: number;
  isExpired: boolean;
  showWarning: boolean;
  timeRemaining: number; // 시간 단위
  maxSessionHours: number;
}

// 인증 컨텍스트 타입
export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
  // 세션 관리 기능들
  showSessionWarning: boolean;
  sessionExpiryReason: string | null;
  extendSession: () => boolean;
  getSessionInfo: () => SessionInfo;
  dismissSessionWarning: () => void;
  getSessionExpiryMessage: () => string;
}

// API 테스트 관련 타입
export interface ApiTestRequest {
  method: "GET" | "POST" | "PUT" | "DELETE";
  endpoint: string;
  headers?: Record<string, string>;
  body?: any;
  queryParams?: Record<string, string>;
}

export interface ApiTestResponse {
  status: number;
  data: any;
  headers: Record<string, string>;
  duration: number;
  timestamp: string;
}

export interface ApiEndpoint {
  id: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  name: string;
  description?: string;
  parameters?: ApiParameter[];
  requestBody?: any;
  isExpanded?: boolean;
}

export interface ApiParameter {
  name: string;
  type: "string" | "number" | "boolean" | "object";
  required: boolean;
  description?: string;
  defaultValue?: any;
}

// 대시보드 통계 타입
export interface DashboardStats {
  completedApis: number;
  inProgressApis: number;
  totalProgress: number;
  testCases: number;
}

// 필터 및 검색 타입
export interface PostFilters {
  type?: PostType;
  service?: ServiceType;
  metadata_type?: string; // 메타데이터 타입 필터링 추가
  category?: string; // 카테고리 필터링 추가
  sortBy?: "created_at" | "views" | "likes";
  search?: string;
  query?: string; // 검색 쿼리 (search의 alias)
  page?: number;
  size?: number;
}

// 컴포넌트 Props 타입
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: "primary" | "secondary" | "danger" | "outline";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: "button" | "submit" | "reset";
}

export interface InputProps extends BaseComponentProps {
  type?: string;
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  label?: string;
  name?: string;
}

// Route Loader 데이터 타입
export interface DashboardLoaderData {
  stats: DashboardStats;
  recentPosts: Post[];
  apiEndpoints: ApiEndpoint[];
}

export interface PostsLoaderData {
  posts: PaginatedResponse<Post>;
  filters: PostFilters;
}

export interface PostDetailLoaderData {
  post: Post;
  comments: PaginatedResponse<Comment>;
  userReactions: Reaction[];
}

// @deprecated - 이 Mock 인터페이스들은 실제 API 타입들로 대체되어 더 이상 사용되지 않음
// 현재 사용 중인 타입들: Post, InfoItem, Service
// Legacy compatibility를 위해 유지하되, 새로운 코드에서는 사용하지 말 것

export interface ServiceStats {
  views: number;
  inquiries: number;
  reviews: number;
  bookmarks: number;
}

export interface ServiceItem {
  name: string;
  price: string;
  originalPrice?: string;
  description: string;
}

export interface ContactInfo {
  phone: string;
  hours: string;
  address: string;
  email: string;
}

export interface ServiceReview {
  author: string;
  rating: number;
  text: string;
}

export interface Tip {
  id: string | number;
  title: string;
  content: string;
  slug: string;
  expert_name: string;
  expert_title: string;
  created_at: string;
  category: string;
  tags: string[];
  views_count: number;
  likes_count: number;
  dislikes_count: number;
  comments_count: number;
  saves_count: number;
  is_new: boolean;
}

// 공통 반응 시스템 인터페이스
export interface ItemReactions {
  views: number;
  likes: number;
  dislikes: number;
  comments: number;
  saves?: number;
}

export interface ReactionBarProps {
  reactions: ItemReactions;
  onReactionClick?: (type: 'like' | 'dislike' | 'save') => void;
  showSave?: boolean;
  itemId?: number;
  itemType?: 'post' | 'info' | 'service' | 'tip';
}

// 콘텐츠 타입 정의
export type ContentType = "interactive_chart" | "ai_article" | "data_visualization" | "mixed_content";

// 정보 페이지 관련 타입
export interface InfoMetadata {
  type: string;
  category: string;
  tags?: string[];
  content_type?: ContentType;
  summary?: string;
  data_source?: string;
  chart_config?: any;
  ai_prompt?: string;
}

export interface InfoItem {
  id: string;
  title: string;
  content: string;
  slug: string;
  author_id: string;
  content_type: ContentType;
  metadata: InfoMetadata;
  created_at: string;
  updated_at?: string;
  stats?: PostStats;
}

// Post를 InfoItem으로 변환하는 함수
export function convertPostToInfoItem(post: Post): InfoItem {
  return {
    id: post.id,
    title: post.title,
    content: post.content,
    slug: post.slug,
    author_id: post.author_id || '',
    content_type: (post.metadata?.content_type as ContentType) || 'ai_article',
    metadata: {
      type: post.metadata?.type || 'property_information',
      category: post.metadata?.category || '',
      tags: post.metadata?.tags || [],
      content_type: (post.metadata?.content_type as ContentType) || 'ai_article',
      summary: post.metadata?.summary,
      data_source: post.metadata?.data_source,
      chart_config: post.metadata?.chart_config,
      ai_prompt: post.metadata?.ai_prompt
    },
    created_at: post.created_at,
    updated_at: post.updated_at,
    stats: post.stats
  };
}

// InfoItem 필터링 함수
export function infoFilterFunction(item: InfoItem, category: string, query: string): boolean {
  // 카테고리 필터
  if (category !== 'all') {
    if (item.metadata.category !== category) {
      return false;
    }
  }
  
  // 검색 필터
  if (query && query.trim()) {
    const searchLower = query.toLowerCase();
    return (
      item.title.toLowerCase().includes(searchLower) ||
      item.content.toLowerCase().includes(searchLower) ||
      (item.metadata.tags && item.metadata.tags.some(tag => 
        tag.toLowerCase().includes(searchLower)
      ))
    );
  }
  
  return true;
}

// InfoItem 정렬 함수
export function infoSortFunction(a: InfoItem, b: InfoItem, sortBy: string): number {
  switch(sortBy) {
    case 'latest':
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    case 'views':
      return (b.stats?.view_count || 0) - (a.stats?.view_count || 0);
    case 'likes':
      return (b.stats?.like_count || 0) - (a.stats?.like_count || 0);
    case 'comments':
      return (b.stats?.comment_count || 0) - (a.stats?.comment_count || 0);
    case 'saves':
      return (b.stats?.bookmark_count || 0) - (a.stats?.bookmark_count || 0);
    default:
      return 0;
  }
}

// 필터링 및 정렬 관련 인터페이스
export interface CategoryOption {
  value: string;
  label: string;
}

export interface SortOption {
  value: string;
  label: string;
}

export interface FilterAndSortState<T> {
  items: T[];
  filteredItems: T[];
  sortedItems: T[];
  currentFilter: string;
  sortBy: string;
  searchQuery: string;
}

// 사용자 활동 조회 API 타입 정의
export interface ActivitySummary {
  total_posts: number;
  total_comments: number;
  total_reactions: number;
  most_active_page_type?: string;
}

// DB 원시 타입 정의 (Phase 5: 백엔드와 완전 일치, URL 패턴과도 일치)
export type DbPageType = 'board' | 'property_information' | 'expert_tips' | 'moving_services';
export type ReactionTypePrefix = 'reaction-likes' | 'reaction-dislikes' | 'reaction-bookmarks';

// 타입 안전성을 위한 헬퍼 타입
export type PageTypeGroups<T> = {
  [K in DbPageType]: T[];
};

export type ReactionGroups = {
  [K in ReactionTypePrefix]: PageTypeGroups<ActivityItem>;
};

export interface ActivityItem {
  // 필수 필드
  id: string;
  created_at: string;
  route_path: string;
  
  // 게시글 관련 optional 필드
  title?: string;
  slug?: string;
  like_count?: number;
  comment_count?: number;
  view_count?: number;
  dislike_count?: number;
  bookmark_count?: number;
  
  // 댓글 관련 optional 필드
  content?: string;
  subtype?: 'inquiry' | 'review' | 'service_inquiry' | 'service_review';
  
  // 반응 관련 optional 필드
  target_type?: string;
  target_id?: string;
  target_title?: string;
  reaction_type?: 'like' | 'dislike' | 'bookmark';
}

export interface UserActivityResponse {
  // Posts using DB native types (Phase 5: 완전 통일)
  posts: {
    board: ActivityItem[];
    property_information: ActivityItem[];
    expert_tips: ActivityItem[];
    moving_services: ActivityItem[];  // Phase 5: DB 원시 타입으로 통일
  };
  comments: ActivityItem[];
  
  // Simplified reactions structure with reaction-* prefix (Phase 5: 완전 통일)
  "reaction-likes": {
    board: ActivityItem[];
    property_information: ActivityItem[];
    expert_tips: ActivityItem[];
    moving_services: ActivityItem[];
  };
  "reaction-dislikes": {
    board: ActivityItem[];
    property_information: ActivityItem[];
    expert_tips: ActivityItem[];
    moving_services: ActivityItem[];
  };
  "reaction-bookmarks": {
    board: ActivityItem[];
    property_information: ActivityItem[];
    expert_tips: ActivityItem[];
    moving_services: ActivityItem[];
  };
  
  summary?: ActivitySummary;  // Optional for compatibility
  pagination?: {
    posts: {
      total_count: number;
      page: number;
      limit: number;
      has_more: boolean;
    };
    comments: {
      total_count: number;
      page: number;
      limit: number;
      has_more: boolean;
    };
    reactions: {
      total_count: number;
      page: number;
      limit: number;
      has_more: boolean;
    };
  };
}