/**
 * 로깅 시스템 타입 정의
 * 
 * 백엔드 로깅 시스템과 일치하는 TypeScript 타입 정의
 */

// 로그 레벨 열거형
export enum LogLevel {
  ERROR = 'ERROR',
  WARN = 'WARN',
  INFO = 'INFO',
  DEBUG = 'DEBUG'
}

// 로그 소스 열거형
export enum LogSource {
  INTERNAL = 'internal',
  EXTERNAL = 'external'
}

// 서비스 타입 열거형
export enum ServiceType {
  API = 'api',
  WEB = 'web',
  CLOUD_RUN = 'cloud-run',
  DATABASE = 'database',
  REDIS = 'redis',
  VERCEL = 'vercel'
}

// 로그 컨텍스트 타입
export interface LogContext {
  user_id?: string;
  endpoint?: string;
  method?: string;
  status_code?: number;
  response_time?: number;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  request_id?: string;
  infrastructure?: string;
  instance_id?: string;
  region?: string;
  version?: string;
}

// 로그 메타데이터 타입
export interface LogMetadata {
  tags?: string[];
  severity?: string;
  error_code?: string;
  correlation_id?: string;
  memory_usage?: number;
  cpu_usage?: number;
  disk_usage?: number;
  cloud_trace_id?: string;
  atlas_cluster?: string;
  vercel_deployment_id?: string;
}

// 로그 엔트리 타입
export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  service: ServiceType;
  source: LogSource;
  message: string;
  context?: LogContext;
  metadata?: LogMetadata;
  stack_trace?: string;
}

// 로그 필터 타입
export interface LogFilter {
  start_time?: string;
  end_time?: string;
  levels?: LogLevel[];
  services?: ServiceType[];
  sources?: LogSource[];
  search_query?: string;
  user_id?: string;
  endpoint?: string;
  status_codes?: number[];
  regions?: string[];
  instance_ids?: string[];
  deployment_ids?: string[];
  page?: number;
  page_size?: number;
}

// 고급 로그 필터 타입 (UI 확장용)
export interface AdvancedLogFilter extends LogFilter {
  infrastructure_types?: string[];
  performance_filters?: {
    min_response_time?: number;
    max_response_time?: number;
    min_memory_usage?: number;
    max_memory_usage?: number;
    min_cpu_usage?: number;
    max_cpu_usage?: number;
  };
  error_filters?: {
    has_stack_trace?: boolean;
    error_codes?: string[];
    correlation_ids?: string[];
  };
}

// 로그 통계 타입
export interface LogStats {
  total_count: number;
  error_count: number;
  warn_count: number;
  info_count: number;
  debug_count: number;
  service_stats: Record<string, number>;
  start_time: string;
  end_time: string;
}

// 에러 그룹핑 타입
export interface ErrorGrouping {
  id: string;
  error_hash: string;
  service: ServiceType;
  endpoint?: string;
  error_type?: string;
  count: number;
  first_seen: string;
  last_seen: string;
  sample_message: string;
  sample_stack_trace?: string;
  severity?: string;
  is_resolved: boolean;
  resolution_notes?: string;
}

// 로그 목록 응답 타입
export interface LogListResponse {
  logs: LogEntry[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

// 시계열 데이터 타입
export interface TimeSeriesData {
  timestamp: string;
  error: number;
  warn: number;
  info: number;
  debug: number;
}

// 상위 엔드포인트 타입
export interface TopEndpoint {
  endpoint: string;
  total_requests: number;
  error_count: number;
  error_rate: number;
  avg_response_time: number;
}

// 성능 요약 타입
export interface PerformanceSummary {
  services: Record<string, {
    avg_response_time: number;
    max_response_time: number;
    request_count: number;
  }>;
  overall: {
    avg_response_time: number;
    max_response_time: number;
    total_requests: number;
  };
}

// 로그 대시보드 응답 타입
export interface LogDashboardResponse {
  stats: LogStats;
  recent_errors: ErrorGrouping[];
  time_series: TimeSeriesData[];
  top_endpoints: TopEndpoint[];
  performance_summary: PerformanceSummary;
}

// 외부 로그 수집 상태 타입
export interface ExternalLogHealth {
  collectors: Record<string, {
    status: 'healthy' | 'warning' | 'error';
    last_collection_hours_ago?: number;
    error?: string;
  }>;
  last_collection_times: Record<string, string>;
  total_logs_24h: number;
  error?: string;
}

// 로깅 시스템 전체 상태 타입
export interface LoggingSystemHealth {
  status: 'healthy' | 'warning' | 'error';
  internal_logging: {
    status: 'healthy' | 'warning' | 'error';
    logs_24h: number;
  };
  external_logging: {
    status: 'healthy' | 'warning' | 'error';
    logs_24h: number;
    collectors: Record<string, any>;
  };
  total_logs_24h: number;
  timestamp: string;
}

// API 응답 공통 타입
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code?: string;
    details?: any;
  };
}

// 로깅 컴포넌트 Props 타입들
export interface LogStatsCardsProps {
  stats: LogStats;
  loading?: boolean;
  className?: string;
}

export interface LogErrorTopListProps {
  errors: ErrorGrouping[];
  loading?: boolean;
  className?: string;
  maxItems?: number;
}

export interface LogFilterPanelProps {
  filter: LogFilter;
  onFilterChange: (filter: LogFilter) => void;
  loading?: boolean;
  className?: string;
}

export interface LogTableProps {
  logs: LogEntry[];
  loading?: boolean;
  className?: string;
  onLogClick?: (log: LogEntry) => void;
}

export interface LogDetailModalProps {
  log: LogEntry | null;
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export interface LoggingDashboardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  initialLoading?: boolean;
  className?: string;
}

// 로그 레벨별 색상 및 아이콘 매핑
export const LOG_LEVEL_CONFIG = {
  [LogLevel.ERROR]: {
    color: 'red',
    bgColor: 'bg-red-50',
    textColor: 'text-red-800',
    borderColor: 'border-red-200',
    icon: '🔴',
    label: 'ERROR'
  },
  [LogLevel.WARN]: {
    color: 'yellow',
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-800',
    borderColor: 'border-yellow-200',
    icon: '🟡',
    label: 'WARN'
  },
  [LogLevel.INFO]: {
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-200',
    icon: '🔵',
    label: 'INFO'
  },
  [LogLevel.DEBUG]: {
    color: 'gray',
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-800',
    borderColor: 'border-gray-200',
    icon: '⚪',
    label: 'DEBUG'
  }
} as const;

// 서비스 타입별 색상 및 아이콘 매핑
export const SERVICE_TYPE_CONFIG = {
  [ServiceType.API]: {
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-200',
    icon: '🔧',
    label: 'API'
  },
  [ServiceType.WEB]: {
    color: 'green',
    bgColor: 'bg-green-50',
    textColor: 'text-green-800',
    borderColor: 'border-green-200',
    icon: '🌐',
    label: 'Web'
  },
  [ServiceType.CLOUD_RUN]: {
    color: 'purple',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-800',
    borderColor: 'border-purple-200',
    icon: '☁️',
    label: 'Cloud Run'
  },
  [ServiceType.DATABASE]: {
    color: 'indigo',
    bgColor: 'bg-indigo-50',
    textColor: 'text-indigo-800',
    borderColor: 'border-indigo-200',
    icon: '🗄️',
    label: 'Database'
  },
  [ServiceType.REDIS]: {
    color: 'red',
    bgColor: 'bg-red-50',
    textColor: 'text-red-800',
    borderColor: 'border-red-200',
    icon: '⚡',
    label: 'Redis'
  },
  [ServiceType.VERCEL]: {
    color: 'gray',
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-800',
    borderColor: 'border-gray-200',
    icon: '🚀',
    label: 'Vercel'
  }
} as const;

// 서비스 타입 옵션 (필터용)
export const SERVICE_OPTIONS = [
  { value: ServiceType.API, label: 'API', icon: '🔧' },
  { value: ServiceType.WEB, label: 'Web', icon: '🌐' },
  { value: ServiceType.CLOUD_RUN, label: 'Cloud Run', icon: '☁️' },
  { value: ServiceType.DATABASE, label: 'Database', icon: '🗄️' },
  { value: ServiceType.REDIS, label: 'Redis', icon: '⚡' },
  { value: ServiceType.VERCEL, label: 'Vercel', icon: '🚀' }
];

// 로그 소스 옵션 (필터용)
export const SOURCE_OPTIONS = [
  { value: LogSource.INTERNAL, label: 'Internal', icon: '🏠' },
  { value: LogSource.EXTERNAL, label: 'External', icon: '🌍' }
];

// 지역 옵션 (필터용)
export const REGION_OPTIONS = [
  { value: 'asia-northeast3', label: 'Asia Northeast 3 (Seoul)', icon: '🇰🇷' },
  { value: 'asia-northeast1', label: 'Asia Northeast 1 (Tokyo)', icon: '🇯🇵' },
  { value: 'us-central1', label: 'US Central 1', icon: '🇺🇸' },
  { value: 'europe-west1', label: 'Europe West 1', icon: '🇪🇺' },
  { value: 'unknown', label: 'Unknown', icon: '❓' }
];

// 인프라 타입 옵션 (필터용)
export const INFRASTRUCTURE_OPTIONS = [
  { value: 'gcp', label: 'Google Cloud Platform', icon: '☁️' },
  { value: 'vercel', label: 'Vercel', icon: '🚀' },
  { value: 'upstash', label: 'Upstash', icon: '⚡' },
  { value: 'atlas', label: 'MongoDB Atlas', icon: '🗄️' },
  { value: 'local', label: 'Local', icon: '🏠' }
];

// 로그 소스별 색상 및 아이콘 매핑
export const LOG_SOURCE_CONFIG = {
  [LogSource.INTERNAL]: {
    color: 'blue',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-200',
    icon: '🏠',
    label: 'Internal'
  },
  [LogSource.EXTERNAL]: {
    color: 'orange',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-800',
    borderColor: 'border-orange-200',
    icon: '🌍',
    label: 'External'
  }
} as const;

// 유틸리티 함수 타입
export interface LogUtils {
  formatTimestamp: (timestamp: string) => string;
  formatDuration: (ms: number) => string;
  formatFileSize: (bytes: number) => string;
  getLogLevelConfig: (level: LogLevel) => typeof LOG_LEVEL_CONFIG[LogLevel];
  getServiceTypeConfig: (service: ServiceType) => typeof SERVICE_TYPE_CONFIG[ServiceType];
  getLogSourceConfig: (source: LogSource) => typeof LOG_SOURCE_CONFIG[LogSource];
  truncateMessage: (message: string, maxLength?: number) => string;
  highlightSearchTerm: (text: string, searchTerm: string) => string;
}

// 로그 검색 및 필터링 관련 타입
export interface LogSearchState {
  query: string;
  filters: LogFilter;
  results: LogEntry[];
  totalCount: number;
  loading: boolean;
  error: string | null;
  hasMore: boolean;
}

export interface LogSearchActions {
  setQuery: (query: string) => void;
  setFilters: (filters: Partial<LogFilter>) => void;
  search: () => Promise<void>;
  loadMore: () => Promise<void>;
  reset: () => void;
}

// 로그 대시보드 상태 타입
export interface LogDashboardState {
  data: LogDashboardResponse | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  autoRefresh: boolean;
  refreshInterval: number;
}

export interface LogDashboardActions {
  fetchDashboard: (hours?: number) => Promise<void>;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (interval: number) => void;
  refresh: () => Promise<void>;
}

// 외부 로그 수집 관련 타입
export interface ExternalLogCollectionState {
  status: 'idle' | 'collecting' | 'success' | 'error';
  progress: number;
  message: string;
  results: Record<string, number>;
  error: string | null;
}

export interface ExternalLogCollectionActions {
  collectLogs: (hours?: number) => Promise<void>;
  checkHealth: () => Promise<void>;
  reset: () => void;
}

// 로그 정리 관련 타입
export interface LogCleanupState {
  status: 'idle' | 'cleaning' | 'success' | 'error';
  progress: number;
  deletedCount: number;
  error: string | null;
}

export interface LogCleanupActions {
  cleanup: (days: number) => Promise<void>;
  reset: () => void;
}