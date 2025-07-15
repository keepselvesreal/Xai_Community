/**
 * 모니터링 API 클라이언트
 * 
 * 백엔드 모니터링 API와 통신하는 함수들
 */
import type {
  MonitoringData,
  SystemMetrics,
  HealthStatus,
  EndpointStats,
  SlowRequest,
  TimeSeriesData,
  PopularEndpoint,
  AggregatedMetrics,
  MonitoringApiResponse,
  SlowRequestsQueryParams,
  TimeSeriesQueryParams,
  PopularEndpointsQueryParams,
} from '~/types/monitoring';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MONITORING_API_BASE = `${API_BASE_URL}/api/internal`;

/**
 * HTTP 요청을 수행하는 기본 함수
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<MonitoringApiResponse<T>> {
  try {
    const response = await fetch(`${MONITORING_API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return {
      success: false,
      error: {
        message: errorMessage,
        timestamp: Date.now(),
      },
    };
  }
}

/**
 * 쿼리 파라미터를 URL에 추가하는 헬퍼 함수
 */
function buildQueryString(params: Record<string, any>): string {
  const queryParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value));
    }
  }
  const queryString = queryParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * 시스템 전체 메트릭 조회
 */
export async function getSystemMetrics(): Promise<MonitoringApiResponse<SystemMetrics>> {
  return apiRequest<SystemMetrics>('/metrics');
}

/**
 * 시스템 헬스 상태 조회
 */
export async function getHealthStatus(): Promise<MonitoringApiResponse<HealthStatus>> {
  return apiRequest<HealthStatus>('/health');
}

/**
 * 특정 엔드포인트 통계 조회
 */
export async function getEndpointStats(endpoint: string): Promise<MonitoringApiResponse<EndpointStats>> {
  const encodedEndpoint = encodeURIComponent(endpoint);
  return apiRequest<EndpointStats>(`/endpoints/${encodedEndpoint}`);
}

/**
 * 느린 요청 목록 조회
 */
export async function getSlowRequests(
  params: SlowRequestsQueryParams = {}
): Promise<MonitoringApiResponse<{ slow_requests: SlowRequest[] }>> {
  const queryString = buildQueryString(params);
  return apiRequest<{ slow_requests: SlowRequest[] }>(`/slow-requests${queryString}`);
}

/**
 * 시간별 시계열 데이터 조회
 */
export async function getTimeSeriesData(
  endpoint: string,
  params: TimeSeriesQueryParams = {}
): Promise<MonitoringApiResponse<TimeSeriesData>> {
  const encodedEndpoint = encodeURIComponent(endpoint);
  const queryString = buildQueryString(params);
  return apiRequest<TimeSeriesData>(`/timeseries/${encodedEndpoint}${queryString}`);
}

/**
 * 인기 엔드포인트 조회
 */
export async function getPopularEndpoints(
  params: PopularEndpointsQueryParams = {}
): Promise<MonitoringApiResponse<{ popular_endpoints: PopularEndpoint[] }>> {
  const queryString = buildQueryString(params);
  return apiRequest<{ popular_endpoints: PopularEndpoint[] }>(`/popular-endpoints${queryString}`);
}

/**
 * 집계된 메트릭 조회 (summary 엔드포인트 사용)
 */
export async function getAggregatedMetrics(): Promise<MonitoringApiResponse<{
  health: HealthStatus;
  aggregated_metrics: AggregatedMetrics;
  popular_endpoints: PopularEndpoint[];
  recent_slow_requests: SlowRequest[];
}>> {
  return apiRequest('/summary');
}

/**
 * 실시간 대시보드 데이터 조회 (모든 주요 데이터 한 번에)
 */
export async function getMonitoringDashboardData(): Promise<MonitoringApiResponse<MonitoringData>> {
  return apiRequest<MonitoringData>('/dashboard');
}

/**
 * 여러 API를 병렬로 호출하여 대시보드 데이터 구성
 */
export async function getComprehensiveDashboardData(): Promise<MonitoringApiResponse<{
  metrics: SystemMetrics | null;
  health: HealthStatus | null;
  popular_endpoints: PopularEndpoint[];
  slow_requests: SlowRequest[];
}>> {
  try {
    const [metricsResult, healthResult, popularResult, slowResult] = await Promise.allSettled([
      getSystemMetrics(),
      getHealthStatus(),
      getPopularEndpoints({ limit: 10 }),
      getSlowRequests({ limit: 20 }),
    ]);

    const data = {
      metrics: metricsResult.status === 'fulfilled' && metricsResult.value.success 
        ? metricsResult.value.data! 
        : null,
      health: healthResult.status === 'fulfilled' && healthResult.value.success 
        ? healthResult.value.data! 
        : null,
      popular_endpoints: popularResult.status === 'fulfilled' && popularResult.value.success 
        ? popularResult.value.data!.popular_endpoints 
        : [],
      slow_requests: slowResult.status === 'fulfilled' && slowResult.value.success 
        ? slowResult.value.data!.slow_requests 
        : [],
    };

    return { success: true, data };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch comprehensive dashboard data';
    return {
      success: false,
      error: {
        message: errorMessage,
        timestamp: Date.now(),
      },
    };
  }
}

/**
 * API 응답 시간 측정을 위한 래퍼 함수
 */
export async function measureApiResponseTime<T>(
  apiCall: () => Promise<MonitoringApiResponse<T>>
): Promise<{ result: MonitoringApiResponse<T>; responseTime: number }> {
  const startTime = performance.now();
  const result = await apiCall();
  const endTime = performance.now();
  const responseTime = endTime - startTime;

  return { result, responseTime };
}

/**
 * 모니터링 API 헬스 체크
 */
export async function checkMonitoringApiHealth(): Promise<{
  isHealthy: boolean;
  responseTime: number;
  error?: string;
}> {
  const { result, responseTime } = await measureApiResponseTime(() => getHealthStatus());
  
  return {
    isHealthy: result.success,
    responseTime,
    error: result.error?.message,
  };
}

/**
 * 에러 리포팅을 위한 유틸리티 함수
 */
export function logMonitoringApiError(error: MonitoringApiResponse<any>['error'], context: string): void {
  if (error) {
    console.error(`[Monitoring API Error] ${context}:`, {
      message: error.message,
      code: error.code,
      timestamp: new Date(error.timestamp).toISOString(),
    });
  }
}

/**
 * 자동 재시도를 지원하는 API 호출 래퍼
 */
export async function apiCallWithRetry<T>(
  apiCall: () => Promise<MonitoringApiResponse<T>>,
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<MonitoringApiResponse<T>> {
  let lastError: MonitoringApiResponse<T>['error'];

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const result = await apiCall();
    
    if (result.success) {
      return result;
    }

    lastError = result.error;
    
    if (attempt < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
    }
  }

  return {
    success: false,
    error: lastError || {
      message: 'All retry attempts failed',
      timestamp: Date.now(),
    },
  };
}