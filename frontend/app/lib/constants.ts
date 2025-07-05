// 앱 설정 상수
export const APP_CONFIG = {
  name: 'FastAPI UI Dashboard',
  version: '1.0.0',
  description: 'FastAPI 완전 UI 시스템',
  author: 'Xai Community',
} as const;

// API 엔드포인트 상수
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    REFRESH: '/auth/refresh',
  },
  POSTS: {
    LIST: '/posts',
    CREATE: '/posts',
    GET: (slug: string) => `/posts/${slug}`,
    UPDATE: (slug: string) => `/posts/${slug}`,
    DELETE: (slug: string) => `/posts/${slug}`,
  },
  COMMENTS: {
    LIST: (postSlug: string) => `/posts/${postSlug}/comments`,
    CREATE: (postSlug: string) => `/posts/${postSlug}/comments`,
    UPDATE: (id: number) => `/comments/${id}`,
    DELETE: (id: number) => `/comments/${id}`,
  },
  REACTIONS: {
    TOGGLE: '/reactions',
    LIST: '/reactions',
  },
} as const;

// 게시글 타입 상수
export const POST_TYPES = [
  { value: '자유게시판', label: '자유게시판' },
  { value: '질문답변', label: '질문답변' },
  { value: '공지사항', label: '공지사항' },
  { value: '후기', label: '후기' },
] as const;

// 서비스 타입 상수
export const SERVICE_TYPES = [
  { value: 'community', label: '커뮤니티' },
  { value: 'shopping', label: '쇼핑' },
  { value: 'apartment', label: '아파트' },
] as const;

// 폼 옵션 내보내기
export const POST_TYPE_OPTIONS = POST_TYPES;
export const SERVICE_OPTIONS = SERVICE_TYPES;

// 정렬 옵션 상수
export const SORT_OPTIONS = [
  { value: 'created_at', label: '최신순' },
  { value: 'views', label: '조회수순' },
  { value: 'likes', label: '좋아요순' },
] as const;

// 페이지네이션 상수
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_SIZE: 10,
  MAX_SIZE: 100,
  SIZE_OPTIONS: [10, 20, 50],
} as const;

// 알림 타입 상수
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info',
  WARNING: 'warning',
} as const;

// 알림 지속 시간 상수 (밀리초)
export const NOTIFICATION_DURATION = {
  SHORT: 3000,
  MEDIUM: 5000,
  LONG: 7000,
} as const;

// 반응 타입 상수
export const REACTION_TYPES = {
  LIKE: 'like',
  DISLIKE: 'dislike',
  BOOKMARK: 'bookmark',
} as const;

// 반응 아이콘 매핑
export const REACTION_ICONS = {
  [REACTION_TYPES.LIKE]: '👍',
  [REACTION_TYPES.DISLIKE]: '👎',
  [REACTION_TYPES.BOOKMARK]: '🔖',
} as const;

// HTTP 메서드 상수
export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
  PATCH: 'PATCH',
} as const;

// HTTP 상태 코드 상수
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// 로컬 스토리지 키 상수
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken',
  REFRESH_TOKEN: 'refreshToken',
  LOGIN_TIME: 'loginTime',
  REFRESH_COUNT: 'refreshCount',
  USER_PREFERENCES: 'userPreferences',
  SIDEBAR_STATE: 'sidebarState',
  THEME: 'theme',
  RECENT_SEARCHES: 'recentSearches',
} as const;

// 폼 유효성 검사 상수
export const VALIDATION = {
  EMAIL: {
    MIN_LENGTH: 5,
    MAX_LENGTH: 254,
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  PASSWORD: {
    MIN_LENGTH: 8,
    MAX_LENGTH: 128,
    PATTERN: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
  },
  USER_HANDLE: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 20,
    PATTERN: /^[a-zA-Z0-9_]{3,20}$/,
  },
  POST_TITLE: {
    MIN_LENGTH: 5,
    MAX_LENGTH: 200,
  },
  POST_CONTENT: {
    MIN_LENGTH: 10,
    MAX_LENGTH: 10000,
  },
  COMMENT_CONTENT: {
    MIN_LENGTH: 1,
    MAX_LENGTH: 1000,
  },
} as const;

// 애니메이션 지속시간 상수
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

// 색상 팔레트 상수
export const COLORS = {
  PRIMARY: '#2563eb',
  SECONDARY: '#64748b',
  SUCCESS: '#059669',
  WARNING: '#d97706',
  ERROR: '#dc2626',
  INFO: '#0891b2',
} as const;

// 브레이크포인트 상수
export const BREAKPOINTS = {
  SM: '640px',
  MD: '768px',
  LG: '1024px',
  XL: '1280px',
  '2XL': '1536px',
} as const;

// 미디어 쿼리 상수
export const MEDIA_QUERIES = {
  MOBILE: `(max-width: ${BREAKPOINTS.MD})`,
  TABLET: `(min-width: ${BREAKPOINTS.MD}) and (max-width: ${BREAKPOINTS.LG})`,
  DESKTOP: `(min-width: ${BREAKPOINTS.LG})`,
} as const;

// API 테스트 기본 엔드포인트
export const API_TEST_ENDPOINTS = [
  {
    id: 'auth-login',
    method: 'POST',
    path: '/auth/login',
    name: '로그인',
    description: '사용자 로그인',
    parameters: [
      { name: 'email', type: 'string', required: true, description: '이메일 주소' },
      { name: 'password', type: 'string', required: true, description: '비밀번호' },
    ],
  },
  {
    id: 'auth-register',
    method: 'POST',
    path: '/auth/register',
    name: '회원가입',
    description: '새 사용자 등록',
    parameters: [
      { name: 'email', type: 'string', required: true, description: '이메일 주소' },
      { name: 'user_handle', type: 'string', required: true, description: '사용자 핸들' },
      { name: 'display_name', type: 'string', required: false, description: '표시 이름' },
      { name: 'password', type: 'string', required: true, description: '비밀번호' },
    ],
  },
  {
    id: 'posts-list',
    method: 'GET',
    path: '/posts',
    name: '게시글 목록',
    description: '게시글 목록 조회',
    parameters: [
      { name: 'page', type: 'number', required: false, description: '페이지 번호', defaultValue: 1 },
      { name: 'size', type: 'number', required: false, description: '페이지 크기', defaultValue: 10 },
      { name: 'type', type: 'string', required: false, description: '게시글 타입' },
      { name: 'service', type: 'string', required: false, description: '서비스 타입' },
    ],
  },
  {
    id: 'posts-create',
    method: 'POST',
    path: '/posts',
    name: '게시글 작성',
    description: '새 게시글 작성',
    parameters: [
      { name: 'title', type: 'string', required: true, description: '게시글 제목' },
      { name: 'content', type: 'string', required: true, description: '게시글 내용' },
      { name: 'service', type: 'string', required: true, description: '서비스 타입' },
      { name: 'type', type: 'string', required: false, description: '게시글 타입' },
    ],
  },
  {
    id: 'comments-list',
    method: 'GET',
    path: '/posts/{slug}/comments',
    name: '댓글 목록',
    description: '게시글 댓글 목록 조회',
    parameters: [
      { name: 'slug', type: 'string', required: true, description: '게시글 슬러그' },
      { name: 'page', type: 'number', required: false, description: '페이지 번호', defaultValue: 1 },
    ],
  },
] as const;

// 네비게이션 메뉴 상수
export const NAV_ITEMS = [
  {
    id: 'dashboard',
    label: '대시보드',
    icon: '📊',
    path: '/dashboard',
    section: '메인',
  },
  {
    id: 'board',
    label: '게시판',
    icon: '📝',
    path: '/board',
    section: '커뮤니티',
  },
  {
    id: 'info',
    label: '정보',
    icon: '📋',
    path: '/info',
    section: '커뮤니티',
  },
  {
    id: 'services',
    label: '입주 업체 서비스',
    icon: '🏢',
    path: '/services',
    section: '커뮤니티',
  },
  {
    id: 'tips',
    label: '전문가 꿀정보',
    icon: '💡',
    path: '/tips',
    section: '커뮤니티',
  },
  {
    id: 'mypage',
    label: '회원정보',
    icon: '👤',
    path: '/mypage',
    section: '계정',
  },
  {
    id: 'login',
    label: '로그인',
    icon: '🔐',
    path: '/auth/login',
    section: '인증',
    requiresGuest: true,
  },
  {
    id: 'register',
    label: '회원가입',
    icon: '📝',
    path: '/auth/register',
    section: '인증',
    requiresGuest: true,
  },
  {
    id: 'posts',
    label: '게시글 목록',
    icon: '📄',
    path: '/posts',
    section: '개발 도구',
  },
  {
    id: 'post-create',
    label: '게시글 작성',
    icon: '✍️',
    path: '/posts/create',
    section: '개발 도구',
    requiresAuth: true,
  },
] as const;

// 에러 메시지 상수
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '네트워크 오류가 발생했습니다. 연결을 확인해주세요.',
  UNAUTHORIZED: '로그인이 필요합니다.',
  FORBIDDEN: '권한이 없습니다.',
  NOT_FOUND: '요청한 리소스를 찾을 수 없습니다.',
  VALIDATION_ERROR: '입력 정보를 다시 확인해주세요.',
  SERVER_ERROR: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
  UNKNOWN_ERROR: '알 수 없는 오류가 발생했습니다.',
} as const;

// 성공 메시지 상수
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: '로그인되었습니다.',
  LOGOUT_SUCCESS: '로그아웃되었습니다.',
  REGISTER_SUCCESS: '회원가입이 완료되었습니다.',
  POST_CREATED: '게시글이 작성되었습니다.',
  POST_UPDATED: '게시글이 수정되었습니다.',
  POST_DELETED: '게시글이 삭제되었습니다.',
  COMMENT_CREATED: '댓글이 작성되었습니다.',
  COMMENT_UPDATED: '댓글이 수정되었습니다.',
  COMMENT_DELETED: '댓글이 삭제되었습니다.',
  REACTION_ADDED: '반응이 추가되었습니다.',
  REACTION_REMOVED: '반응이 취소되었습니다.',
} as const;

// 세션 관리 상수 (하이브리드 방식)
export const SESSION_CONFIG = {
  // 최대 세션 지속 시간 (시간)
  MAX_SESSION_HOURS: 8,
  // 최대 토큰 갱신 횟수 (30분 × 16회 = 8시간)
  MAX_REFRESH_COUNT: 16,
  // 로그아웃 경고 시간 (분) - 30분 전 경고
  WARNING_BEFORE_LOGOUT_MINUTES: 30,
  // 토큰 만료 임박 확인 시간 (분) - 10분 전에 갱신
  TOKEN_REFRESH_THRESHOLD_MINUTES: 10,
  // 세션 확인 주기 (분) - 5분마다 확인
  SESSION_CHECK_INTERVAL_MINUTES: 5,
} as const;

// 세션 만료 사유 상수
export const SESSION_EXPIRY_REASONS = {
  TIME_LIMIT: 'time_limit',
  REFRESH_LIMIT: 'refresh_limit',
  TOKEN_INVALID: 'token_invalid',
  MANUAL_LOGOUT: 'manual_logout',
} as const;

// 세션 관련 메시지 상수
export const SESSION_MESSAGES = {
  WARNING_TITLE: '세션 만료 알림',
  WARNING_MESSAGE: '30분 후 자동으로 로그아웃됩니다.\n계속 사용하시겠습니까?',
  EXTEND_SESSION: '세션 연장',
  LOGOUT_NOW: '지금 로그아웃',
  EXPIRED_TIME_LIMIT: '8시간 사용 제한으로 인해 로그아웃되었습니다.\n다시 로그인해주세요.',
  EXPIRED_REFRESH_LIMIT: '보안을 위해 로그아웃되었습니다.\n다시 로그인해주세요.',
  EXPIRED_TOKEN_INVALID: '인증이 만료되어 로그아웃되었습니다.\n다시 로그인해주세요.',
} as const;