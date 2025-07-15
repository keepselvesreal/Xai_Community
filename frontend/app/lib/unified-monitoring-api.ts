/**
 * 통합 모니터링 API 클라이언트
 * 
 * 백엔드의 새로운 통합 모니터링 API와 연동
 */
import type { 
  Environment, 
  UnifiedMonitoringData, 
  ApiResponse 
} from '~/types/unified-monitoring';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API 요청 래퍼 함수
 */
async function apiRequest<T>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    return {
      success: true,
      data: data as T,
    };
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    
    return {
      success: false,
      error: {
        message: error instanceof Error ? error.message : 'Unknown error',
        details: error,
      },
    };
  }
}

/**
 * 환경별 통합 대시보드 데이터 조회
 */
export async function getUnifiedDashboardData(
  environment: Environment
): Promise<ApiResponse<UnifiedMonitoringData>> {
  return apiRequest<UnifiedMonitoringData>(`/api/monitoring/dashboard/${environment}`);
}

/**
 * 사용 가능한 환경 목록 조회
 */
export async function getEnvironments(): Promise<ApiResponse<{
  environments: string[];
  default: string;
  description: string;
}>> {
  return apiRequest(`/api/monitoring/environments`);
}

/**
 * 환경별 HetrixTools 모니터 조회
 */
export async function getHetrixMonitors(
  environment?: Environment
): Promise<ApiResponse<{
  total: number;
  environment: string;
  monitors: Array<any>;
  timestamp: string;
}>> {
  const params = environment ? `?environment=${environment}` : '';
  return apiRequest(`/api/monitoring/hetrix/monitors${params}`);
}

/**
 * 환경별 인프라 상태 조회
 */
export async function getInfrastructureStatus(
  environment?: Environment
): Promise<ApiResponse<any>> {
  const params = environment ? `?environment=${environment}` : '';
  return apiRequest(`/api/monitoring/infrastructure/status${params}`);
}

/**
 * 간단한 헬스체크
 */
export async function getSimpleHealth(): Promise<ApiResponse<{
  status: string;
  service: string;
  timestamp: string;
}>> {
  return apiRequest(`/api/monitoring/health/simple`);
}

/**
 * 종합 헬스체크
 */
export async function getComprehensiveHealth(): Promise<ApiResponse<{
  status: string;
  overall_health: string;
  checks: Record<string, any>;
  monitoring_service: string;
}>> {
  return apiRequest(`/api/monitoring/health/comprehensive`);
}

/**
 * 모니터링 에러 로깅
 */
export function logMonitoringError(
  error: any, 
  context: string, 
  additionalData?: any
): void {
  console.error(`[Monitoring Error] ${context}:`, {
    error,
    timestamp: new Date().toISOString(),
    context,
    additionalData,
  });
  
  // 프로덕션 환경에서는 Sentry나 다른 에러 추적 서비스로 전송
  if (process.env.NODE_ENV === 'production') {
    // TODO: Sentry.captureException(error);
  }
}

/**
 * 실시간 모니터링 상태 체크
 */
export async function checkMonitoringHealth(): Promise<boolean> {
  try {
    const result = await getSimpleHealth();
    return result.success && result.data?.status === 'healthy';
  } catch (error) {
    logMonitoringError(error, 'checkMonitoringHealth');
    return false;
  }
}

/**
 * 환경별 모니터링 설정
 */
export const MONITORING_CONFIG = {
  environments: [
    {
      name: 'development' as Environment,
      label: '개발',
      emoji: '🚧',
      description: '개발 환경',
      color: 'yellow' as const,
    },
    {
      name: 'staging' as Environment,
      label: '스테이징',
      emoji: '🔍',
      description: '검증 환경',
      color: 'blue' as const,
    },
    {
      name: 'production' as Environment,
      label: '프로덕션',
      emoji: '🚀',
      description: '운영 환경',
      color: 'green' as const,
    },
  ],
  statusIcons: {
    healthy: '✅',
    unhealthy: '❌',
    warning: '⚠️',
    unknown: '❓',
  },
  refreshInterval: 30000, // 30초
  autoRefresh: true,
};

export default {
  getUnifiedDashboardData,
  getEnvironments,
  getHetrixMonitors,
  getInfrastructureStatus,
  getSimpleHealth,
  getComprehensiveHealth,
  logMonitoringError,
  checkMonitoringHealth,
  MONITORING_CONFIG,
};