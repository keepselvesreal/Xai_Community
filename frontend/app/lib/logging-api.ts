/**
 * 로깅 시스템 API 클라이언트
 * 
 * 백엔드 로깅 API와 통신하는 클라이언트 라이브러리
 */

import {
  LogEntry,
  LogFilter,
  LogListResponse,
  LogDashboardResponse,
  LogStats,
  ErrorGrouping,
  TimeSeriesData,
  TopEndpoint,
  PerformanceSummary,
  ExternalLogHealth,
  LoggingSystemHealth,
  ApiResponse,
  LogLevel,
  ServiceType,
  LogSource
} from '~/types/logging';

// API 기본 설정 - 환경변수 사용
const API_BASE_URL = (() => {
  // 클라이언트 사이드에서 실행 시 VITE_ 환경변수 사용
  if (typeof window !== 'undefined') {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }
  
  // 서버 사이드에서 실행 시
  return process.env.VITE_API_URL || process.env.API_URL || 'http://localhost:8000';
})();

// HTTP 클라이언트 래퍼
class HttpClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = {
        ...this.defaultHeaders,
        ...options.headers,
      };

      // 토큰이 있으면 추가
      const token = this.getAuthToken();
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || 
          errorData.message || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return {
        success: false,
        error: {
          message: error instanceof Error ? error.message : 'Unknown error',
          code: 'API_ERROR',
        },
      };
    }
  }

  private getAuthToken(): string | null {
    // 클라이언트 사이드에서 토큰 가져오기
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const url = params ? `${endpoint}?${new URLSearchParams(params).toString()}` : endpoint;
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// 로깅 API 클라이언트 클래스
export class LoggingApiClient {
  private client: HttpClient;

  constructor(baseUrl: string = API_BASE_URL) {
    this.client = new HttpClient(baseUrl);
  }

  /**
   * 로그 대시보드 데이터 조회
   */
  async getDashboard(hours: number = 24): Promise<ApiResponse<LogDashboardResponse>> {
    return this.client.get<LogDashboardResponse>('/api/logs/dashboard', { hours });
  }

  /**
   * 로그 검색 및 필터링
   */
  async searchLogs(filter: LogFilter): Promise<ApiResponse<LogListResponse>> {
    const params: Record<string, any> = {};

    if (filter.start_time) params.start_time = filter.start_time;
    if (filter.end_time) params.end_time = filter.end_time;
    if (filter.levels) params.levels = filter.levels;
    if (filter.services) params.services = filter.services;
    if (filter.sources) params.sources = filter.sources;
    if (filter.search_query) params.search_query = filter.search_query;
    if (filter.user_id) params.user_id = filter.user_id;
    if (filter.endpoint) params.endpoint = filter.endpoint;
    if (filter.page) params.page = filter.page;
    if (filter.page_size) params.page_size = filter.page_size;

    return this.client.get<LogListResponse>('/api/logs/search', params);
  }

  /**
   * 특정 로그 상세 정보 조회
   */
  async getLogDetail(logId: string): Promise<ApiResponse<LogEntry>> {
    return this.client.get<LogEntry>(`/api/logs/${logId}`);
  }

  /**
   * 로그 통계 요약 정보 조회
   */
  async getLogStats(hours: number = 24): Promise<ApiResponse<{ stats: LogStats; time_range: any }>> {
    return this.client.get(`/api/logs/stats/summary`, { hours });
  }

  /**
   * 최근 에러 TOP N 조회
   */
  async getTopErrors(limit: number = 5): Promise<ApiResponse<ErrorGrouping[]>> {
    return this.client.get<ErrorGrouping[]>('/api/logs/errors/top', { limit });
  }

  /**
   * 시계열 로그 데이터 조회
   */
  async getTimeSeriesData(
    hours: number = 24,
    intervalMinutes: number = 60
  ): Promise<ApiResponse<TimeSeriesData[]>> {
    return this.client.get<TimeSeriesData[]>('/api/logs/time-series/data', {
      hours,
      interval_minutes: intervalMinutes,
    });
  }

  /**
   * 성능 요약 정보 조회
   */
  async getPerformanceSummary(hours: number = 24): Promise<ApiResponse<{
    performance: PerformanceSummary;
    time_range: any;
  }>> {
    return this.client.get(`/api/logs/performance/summary`, { hours });
  }

  /**
   * 외부 로그 수집 실행
   */
  async collectExternalLogs(hours: number = 1): Promise<ApiResponse<{
    message: string;
    hours: number;
    status: string;
  }>> {
    return this.client.post('/api/logs/external/collect', null, { hours });
  }

  /**
   * 외부 로그 수집 상태 확인
   */
  async getExternalLogHealth(): Promise<ApiResponse<ExternalLogHealth>> {
    return this.client.get<ExternalLogHealth>('/api/logs/external/health');
  }

  /**
   * 텍스트 검색
   */
  async searchLogsByText(
    query: string,
    limit: number = 100
  ): Promise<ApiResponse<LogEntry[]>> {
    return this.client.post<LogEntry[]>('/api/logs/text-search', { query, limit });
  }

  /**
   * 상위 엔드포인트 조회
   */
  async getTopEndpoints(
    hours: number = 24,
    limit: number = 10
  ): Promise<ApiResponse<TopEndpoint[]>> {
    return this.client.get<TopEndpoint[]>('/api/logs/endpoints/top', { hours, limit });
  }

  /**
   * 로깅 시스템 전체 상태 확인
   */
  async getLoggingHealth(): Promise<ApiResponse<LoggingSystemHealth>> {
    return this.client.get<LoggingSystemHealth>('/api/logs/health');
  }

  /**
   * 오래된 로그 정리
   */
  async cleanupOldLogs(days: number = 30): Promise<ApiResponse<{
    message: string;
    deleted_count: number;
    cutoff_date: string;
  }>> {
    return this.client.delete(`/api/logs/cleanup?days=${days}`);
  }
}

// 싱글톤 API 클라이언트 인스턴스
export const loggingApi = new LoggingApiClient();

// 에러 처리 유틸리티
export function handleApiError(error: ApiResponse<any>['error']): string {
  if (!error) return 'Unknown error';
  
  switch (error.code) {
    case 'API_ERROR':
      return error.message;
    case 'NETWORK_ERROR':
      return '네트워크 연결을 확인해주세요';
    case 'UNAUTHORIZED':
      return '로그인이 필요합니다';
    case 'FORBIDDEN':
      return '접근 권한이 없습니다';
    case 'NOT_FOUND':
      return '요청한 리소스를 찾을 수 없습니다';
    case 'VALIDATION_ERROR':
      return '입력 값을 확인해주세요';
    case 'SERVER_ERROR':
      return '서버 오류가 발생했습니다';
    default:
      return error.message || 'Unknown error';
  }
}

// 로그 레벨 유틸리티
export const logLevelUtils = {
  all: [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG],
  
  fromString: (level: string): LogLevel | null => {
    const normalized = level.toUpperCase();
    return Object.values(LogLevel).includes(normalized as LogLevel) 
      ? normalized as LogLevel 
      : null;
  },
  
  toString: (level: LogLevel): string => {
    return level.toString();
  },
  
  compare: (a: LogLevel, b: LogLevel): number => {
    const order = [LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG];
    return order.indexOf(a) - order.indexOf(b);
  }
};

// 서비스 타입 유틸리티
export const serviceTypeUtils = {
  all: [
    ServiceType.API,
    ServiceType.WEB,
    ServiceType.CLOUD_RUN,
    ServiceType.DATABASE,
    ServiceType.REDIS,
    ServiceType.VERCEL
  ],
  
  fromString: (service: string): ServiceType | null => {
    const normalized = service.toLowerCase().replace('_', '-');
    return Object.values(ServiceType).includes(normalized as ServiceType)
      ? normalized as ServiceType
      : null;
  },
  
  toString: (service: ServiceType): string => {
    return service.toString();
  }
};

// 로그 소스 유틸리티
export const logSourceUtils = {
  all: [LogSource.INTERNAL, LogSource.EXTERNAL],
  
  fromString: (source: string): LogSource | null => {
    const normalized = source.toLowerCase();
    return Object.values(LogSource).includes(normalized as LogSource)
      ? normalized as LogSource
      : null;
  },
  
  toString: (source: LogSource): string => {
    return source.toString();
  }
};

// UTC를 한국 시간으로 변환하는 공통 함수
function convertUtcToKorea(timestamp: string) {
  const parts = timestamp.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
  if (!parts) return null;
  
  const [, year, month, day, utcHour, minute, second] = parts;
  let koreaHour = parseInt(utcHour) + 9;
  let koreaDay = parseInt(day);
  let koreaMonth = parseInt(month);
  let koreaYear = parseInt(year);
  
  // 24시간을 넘으면 다음날로
  if (koreaHour >= 24) {
    koreaHour -= 24;
    koreaDay += 1;
    
    // 월말 처리
    const daysInMonth = new Date(koreaYear, koreaMonth, 0).getDate();
    if (koreaDay > daysInMonth) {
      koreaDay = 1;
      koreaMonth += 1;
      if (koreaMonth > 12) {
        koreaMonth = 1;
        koreaYear += 1;
      }
    }
  }
  
  return {
    year: koreaYear,
    month: koreaMonth,
    day: koreaDay,
    hour: koreaHour,
    minute: parseInt(minute),
    second: parseInt(second)
  };
}

// 시간 유틸리티
export const timeUtils = {
  formatTimestamp: (timestamp: string): string => {
    const korea = convertUtcToKorea(timestamp);
    if (!korea) return timestamp;
    
    // 오전/오후 계산
    const ampm = korea.hour >= 12 ? '오후' : '오전';
    const displayHour = korea.hour === 0 ? 12 : (korea.hour > 12 ? korea.hour - 12 : korea.hour);
    
    return `${korea.year}. ${korea.month.toString().padStart(2, '0')}. ${korea.day.toString().padStart(2, '0')}. ${ampm} ${displayHour.toString().padStart(2, '0')}:${korea.minute.toString().padStart(2, '0')}:${korea.second.toString().padStart(2, '0')}`;
  },
  
  formatDuration: (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
    return `${(ms / 3600000).toFixed(1)}h`;
  },
  
  formatRelativeTime: (timestamp: string): string => {
    const korea = convertUtcToKorea(timestamp);
    if (!korea) return timestamp;
    
    // 한국 시간으로 Date 객체 생성
    const koreaDate = new Date(korea.year, korea.month - 1, korea.day, korea.hour, korea.minute, korea.second);
    const now = new Date();
    const diff = now.getTime() - koreaDate.getTime();
    
    if (diff < 60000) return '방금 전';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
    if (diff < 2592000000) return `${Math.floor(diff / 86400000)}일 전`;
    return timeUtils.formatTimestamp(timestamp);
  },
  
  getTimeRange: (hours: number): { start_time: string; end_time: string } => {
    const end = new Date();
    const start = new Date(end.getTime() - hours * 60 * 60 * 1000);
    
    return {
      start_time: start.toISOString(),
      end_time: end.toISOString(),
    };
  }
};

// 데이터 유틸리티
export const dataUtils = {
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  },
  
  formatNumber: (num: number): string => {
    if (num < 1000) return num.toString();
    if (num < 1000000) return `${(num / 1000).toFixed(1)}K`;
    if (num < 1000000000) return `${(num / 1000000).toFixed(1)}M`;
    return `${(num / 1000000000).toFixed(1)}B`;
  },
  
  formatPercentage: (value: number, total: number): string => {
    if (total === 0) return '0%';
    return `${((value / total) * 100).toFixed(1)}%`;
  },
  
  truncateText: (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  },
  
  highlightSearchTerm: (text: string, searchTerm: string): string => {
    if (!searchTerm) return text;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }
};

// 상태 관리 유틸리티
export const stateUtils = {
  createInitialFilter: (): LogFilter => ({
    page: 1,
    page_size: 50,
    ...timeUtils.getTimeRange(24), // 기본 24시간
  }),
  
  mergeFilters: (current: LogFilter, updates: Partial<LogFilter>): LogFilter => ({
    ...current,
    ...updates,
    page: updates.page || 1, // 필터 변경 시 첫 페이지로 리셋
  }),
  
  validateFilter: (filter: LogFilter): string[] => {
    const errors: string[] = [];
    
    if (filter.page && filter.page < 1) {
      errors.push('페이지 번호는 1 이상이어야 합니다');
    }
    
    if (filter.page_size && (filter.page_size < 1 || filter.page_size > 100)) {
      errors.push('페이지 크기는 1-100 사이여야 합니다');
    }
    
    if (filter.start_time && filter.end_time) {
      const start = new Date(filter.start_time);
      const end = new Date(filter.end_time);
      if (start >= end) {
        errors.push('시작 시간은 종료 시간보다 빨라야 합니다');
      }
    }
    
    return errors;
  }
};

// 로그 통계 유틸리티
export const statsUtils = {
  calculateTotalLogs: (stats: LogStats): number => {
    return stats.error_count + stats.warn_count + stats.info_count + stats.debug_count;
  },
  
  calculateErrorRate: (stats: LogStats): number => {
    const total = statsUtils.calculateTotalLogs(stats);
    return total > 0 ? (stats.error_count / total) * 100 : 0;
  },
  
  getTopServices: (stats: LogStats, limit: number = 5): Array<{ service: string; count: number }> => {
    return Object.entries(stats.service_stats)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit)
      .map(([service, count]) => ({ service, count }));
  }
};

export default loggingApi;