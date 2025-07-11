/**
 * 모니터링 관련 타입 정의
 * 
 * API 모니터링 대시보드에서 사용되는 모든 타입들
 */

export interface SystemMetrics {
  /** 엔드포인트별 요청 수 */
  endpoints: Record<string, number>;
  /** 상태코드별 요청 수 */
  status_codes: Record<string, number>;
  /** 메트릭 수집 시간 */
  timestamp: number;
}

export interface HealthStatus {
  /** 시스템 상태: healthy, warning, critical */
  status: 'healthy' | 'warning' | 'critical';
  /** 총 요청 수 */
  total_requests: number;
  /** 성공 요청 수 */
  success_requests: number;
  /** 에러 요청 수 */
  error_requests: number;
  /** 에러율 (0-1 사이의 소수) */
  error_rate: number;
  /** 가용성 (0-1 사이의 소수) */
  availability: number;
  /** 헬스 체크 시간 */
  timestamp: number;
}

export interface PopularEndpoint {
  /** 엔드포인트 (예: "GET:/api/posts") */
  endpoint: string;
  /** 요청 수 */
  requests: number;
}

export interface SlowRequest {
  /** 엔드포인트 (예: "GET:/api/posts") */
  endpoint: string;
  /** 응답 시간 (초) */
  response_time: number;
  /** 요청 발생 시간 */
  timestamp: number;
  /** HTTP 상태코드 */
  status_code: number;
  /** 사용자 에이전트 (선택적) */
  user_agent?: string;
  /** 클라이언트 IP (선택적) */
  client_ip?: string;
}

export interface EndpointStats {
  /** 평균 응답시간 (초) */
  avg_response_time: number;
  /** 최소 응답시간 (초) */
  min_response_time: number;
  /** 최대 응답시간 (초) */
  max_response_time: number;
  /** 요청 수 */
  request_count: number;
}

export interface TimeSeriesData {
  /** 타임스탬프 배열 */
  timestamps: number[];
  /** 응답시간 배열 */
  response_times: number[];
}

export interface AggregatedMetrics {
  /** 총 요청 수 */
  total_requests: number;
  /** 성공률 (0-1 사이의 소수) */
  success_rate: number;
  /** 엔드포인트 수 */
  endpoints_count: number;
  /** 집계 시간 */
  timestamp: number;
}

export interface MonitoringDashboardData {
  /** 시스템 전체 메트릭 */
  metrics: SystemMetrics | null;
  /** 헬스 상태 */
  health: HealthStatus | null;
  /** 인기 엔드포인트 목록 */
  popular_endpoints: PopularEndpoint[];
  /** 느린 요청 목록 */
  slow_requests: SlowRequest[];
}

export interface MonitoringData {
  /** 데이터 수집 시간 */
  timestamp: number;
  /** 응답 상태 */
  status: 'success' | 'error';
  /** 대시보드 데이터 */
  data: MonitoringDashboardData | null;
}

export interface MonitoringError {
  /** 에러 메시지 */
  message: string;
  /** 에러 코드 (선택적) */
  code?: string;
  /** 에러 발생 시간 */
  timestamp: number;
}

export interface MonitoringApiResponse<T = any> {
  /** 응답 데이터 */
  data?: T;
  /** 에러 정보 */
  error?: MonitoringError;
  /** 응답 상태 */
  success: boolean;
}

// 컴포넌트 Props 타입들
export interface MonitoringDashboardProps {
  /** 자동 새로고침 활성화 여부 */
  autoRefresh?: boolean;
  /** 새로고침 간격 (밀리초) */
  refreshInterval?: number;
  /** 초기 로딩 상태 */
  initialLoading?: boolean;
  /** 커스텀 클래스명 */
  className?: string;
}

export interface HealthStatusCardProps {
  /** 헬스 상태 데이터 */
  health: HealthStatus | null;
  /** 로딩 상태 */
  loading?: boolean;
}

export interface MetricsChartProps {
  /** 메트릭 데이터 */
  metrics: SystemMetrics | null;
  /** 차트 타입 */
  type: 'endpoints' | 'status_codes';
  /** 로딩 상태 */
  loading?: boolean;
}

export interface SlowRequestsListProps {
  /** 느린 요청 목록 */
  slowRequests: SlowRequest[];
  /** 로딩 상태 */
  loading?: boolean;
  /** 최대 표시 개수 */
  maxItems?: number;
}

export interface PopularEndpointsChartProps {
  /** 인기 엔드포인트 목록 */
  popularEndpoints: PopularEndpoint[];
  /** 로딩 상태 */
  loading?: boolean;
  /** 최대 표시 개수 */
  maxItems?: number;
}

// 헬스 상태 유틸리티 타입
export type HealthStatusColor = {
  healthy: 'text-green-600 bg-green-100';
  warning: 'text-yellow-600 bg-yellow-100';
  critical: 'text-red-600 bg-red-100';
};

// API 엔드포인트 관련 타입
export interface MonitoringApiEndpoints {
  /** 시스템 메트릭 조회 */
  metrics: '/api/monitoring/metrics';
  /** 헬스 상태 조회 */
  health: '/api/monitoring/health';
  /** 엔드포인트 통계 조회 */
  endpointStats: '/api/monitoring/endpoints';
  /** 느린 요청 목록 조회 */
  slowRequests: '/api/monitoring/slow-requests';
  /** 시간별 데이터 조회 */
  timeSeries: '/api/monitoring/timeseries';
  /** 인기 엔드포인트 조회 */
  popularEndpoints: '/api/monitoring/popular-endpoints';
  /** 요약 대시보드 데이터 조회 */
  summary: '/api/monitoring/summary';
  /** 실시간 대시보드 데이터 조회 */
  dashboard: '/api/monitoring/dashboard';
}

// 쿼리 파라미터 타입
export interface SlowRequestsQueryParams {
  /** 조회할 최대 개수 (1-200) */
  limit?: number;
}

export interface TimeSeriesQueryParams {
  /** 조회할 시간 범위 (분, 1-1440) */
  minutes?: number;
}

export interface PopularEndpointsQueryParams {
  /** 조회할 최대 개수 (1-50) */
  limit?: number;
}