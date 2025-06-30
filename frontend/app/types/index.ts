// 사용자 관련 타입
export interface User {
  id: string;
  email: string;
  username?: string;
  user_handle?: string;
  display_name?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
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

// 게시글 관련 타입
export interface Post {
  id: number;
  title: string;
  content: string;
  slug: string;
  author?: User;
  type: PostType;
  service: ServiceType;
  created_at: string;
  updated_at: string;
  stats?: PostStats;
  tags?: string[];
}

export interface PostStats {
  views: number;
  likes: number;
  dislikes: number;
  comments: number;
  bookmarks: number;
}

export interface CreatePostRequest {
  title: string;
  content: string;
  service: ServiceType;
  type?: PostType;
  tags?: string[];
}

export type PostType = "자유게시판" | "질문답변" | "공지사항" | "후기";
export type ServiceType = "community" | "shopping" | "apartment";

// 댓글 관련 타입
export interface Comment {
  id: number;
  post_id: number;
  author?: User;
  content: string;
  created_at: string;
  updated_at: string;
  likes?: number;
  dislikes?: number;
  parent_id?: number;
  replies?: Comment[];
}

export interface CreateCommentRequest {
  content: string;
  parent_id?: number;
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

// 인증 컨텍스트 타입
export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
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
  sortBy?: "created_at" | "views" | "likes";
  search?: string;
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

// Mock 데이터용 추가 인터페이스 정의
export interface MockPost {
  id: number;
  title: string;
  author: string;
  time: string;
  timeValue: number;
  tag: string;
  tagText: string;
  views: number;
  likes: number;
  dislikes: number;
  comments: number;
  isNew: boolean;
  content: string;
}

export interface MockInfoItem {
  id: number;
  title: string;
  author: string;
  time: string;
  timeValue: number;
  tag: string;
  tagText: string;
  views: number;
  likes: number;
  dislikes: number;
  comments: number;
  isNew: boolean;
  content: string;
}

export interface MockService {
  id: number;
  name: string;
  category: string;
  rating: number;
  description: string;
  services: ServiceItem[];
  stats: ServiceStats;
  verified: boolean;
  contact: ContactInfo;
  reviews: ServiceReview[];
}

export interface ServiceStats {
  views: number;
  inquiries: number;
  reviews: number;
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

export interface MockTip {
  id: number;
  title: string;
  content: string;
  expert_name: string;
  expert_title: string;
  created_at: string;
  category: string;
  tags: string[];
  views_count: number;
  likes_count: number;
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