/**
 * 모니터링 대시보드 고정된 테스트
 * 
 * Mock 호이스팅 문제를 해결한 버전
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

// Mock API 함수를 변수 없이 정의
vi.mock('~/lib/monitoring-api', () => ({
  getMonitoringDashboardData: vi.fn(),
  logMonitoringApiError: vi.fn(),
}));

// Mock 컴포넌트들
vi.mock('~/components/monitoring/HealthStatusCard', () => ({
  HealthStatusCard: ({ health }: any) => (
    <div data-testid="health-status">
      Health: {health?.status || 'none'}
    </div>
  )
}));

vi.mock('~/components/monitoring/MetricsChart', () => ({
  MetricsChart: ({ type }: any) => (
    <div data-testid={`metrics-${type}`}>
      Metrics Chart: {type}
    </div>
  )
}));

vi.mock('~/components/monitoring/PopularEndpointsChart', () => ({
  PopularEndpointsChart: () => (
    <div data-testid="popular-endpoints">Popular Endpoints</div>
  )
}));

vi.mock('~/components/monitoring/SlowRequestsList', () => ({
  SlowRequestsList: () => (
    <div data-testid="slow-requests">Slow Requests</div>
  )
}));

vi.mock('~/components/common/LoadingSpinner', () => ({
  default: () => <div data-testid="loading-spinner">Loading...</div>
}));

// 컴포넌트 import
import { MonitoringDashboard } from '~/components/monitoring/MonitoringDashboard';
import { getMonitoringDashboardData } from '~/lib/monitoring-api';

// Mock 함수 타입 캐스팅
const mockGetMonitoringData = vi.mocked(getMonitoringDashboardData);

describe('MonitoringDashboard Fixed Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('로딩 상태를 올바르게 표시한다', () => {
    // Given: API 호출이 진행 중 (영원히 pending)
    mockGetMonitoringData.mockImplementation(() => new Promise(() => {}));

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard initialLoading={true} />);

    // Then: 로딩 스피너 표시
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('모니터링 데이터 로딩 중...')).toBeInTheDocument();
  });

  it('API 에러 시 에러 메시지를 표시한다', async () => {
    // Given: API 에러 발생
    mockGetMonitoringData.mockRejectedValue(new Error('API Connection Failed'));

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 에러 메시지 표시
    await waitFor(() => {
      expect(screen.getByText('모니터링 데이터 로딩 실패')).toBeInTheDocument();
    });
    
    expect(screen.getByText('API Connection Failed')).toBeInTheDocument();
    expect(screen.getByText('다시 시도')).toBeInTheDocument();
  });

  it('성공적인 데이터 로드 시 대시보드를 표시한다', async () => {
    // Given: 성공적인 API 응답
    const mockData = {
      timestamp: Date.now(),
      status: 'success' as const,
      data: {
        metrics: {
          endpoints: { 'GET:/api/posts': 100 },
          status_codes: { '200': 95, '404': 5 },
          timestamp: Date.now(),
        },
        health: {
          status: 'healthy' as const,
          total_requests: 100,
          success_requests: 95,
          error_requests: 5,
          error_rate: 0.05,
          availability: 0.95,
          timestamp: Date.now(),
        },
        popular_endpoints: [
          { endpoint: 'GET:/api/posts', requests: 100 }
        ],
        slow_requests: [],
      },
    };
    
    mockGetMonitoringData.mockResolvedValue({ success: true, data: mockData });

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 대시보드 컴포넌트들 표시
    await waitFor(() => {
      expect(screen.getByText('API 모니터링 대시보드')).toBeInTheDocument();
    });
    
    expect(screen.getByTestId('health-status')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-endpoints')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-status_codes')).toBeInTheDocument();
    expect(screen.getByTestId('popular-endpoints')).toBeInTheDocument();
    expect(screen.getByTestId('slow-requests')).toBeInTheDocument();
  });

  it('빈 데이터 시 적절한 메시지를 표시한다', async () => {
    // Given: 빈 데이터
    const emptyData = {
      timestamp: Date.now(),
      status: 'success' as const,
      data: {
        metrics: {
          endpoints: {},
          status_codes: {},
          timestamp: Date.now(),
        },
        health: null,
        popular_endpoints: [],
        slow_requests: [],
      },
    };
    
    mockGetMonitoringData.mockResolvedValue({ success: true, data: emptyData });

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 빈 데이터 메시지 표시
    await waitFor(() => {
      expect(screen.getByText('모니터링 데이터가 없습니다')).toBeInTheDocument();
    });
    
    expect(screen.getByText('시스템에 아직 충분한 활동이 없거나 데이터 수집이 시작되지 않았습니다.')).toBeInTheDocument();
  });

  it('API 호출 실패 후 성공 시 정상 표시된다', async () => {
    // Given: 처음에는 실패, 두 번째에는 성공
    mockGetMonitoringData
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce({
        success: true,
        data: {
          timestamp: Date.now(),
          status: 'success' as const,
          data: {
            metrics: {
              endpoints: { 'GET:/api/posts': 50 },
              status_codes: { '200': 50 },
              timestamp: Date.now(),
            },
            health: {
              status: 'healthy' as const,
              total_requests: 50,
              success_requests: 50,
              error_requests: 0,
              error_rate: 0,
              availability: 1.0,
              timestamp: Date.now(),
            },
            popular_endpoints: [],
            slow_requests: [],
          },
        },
      });

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 먼저 에러 메시지 표시
    await waitFor(() => {
      expect(screen.getByText('모니터링 데이터 로딩 실패')).toBeInTheDocument();
    });

    // When: 다시 시도 버튼 클릭
    const retryButton = screen.getByText('다시 시도');
    retryButton.click();

    // Then: 성공적으로 대시보드 표시
    await waitFor(() => {
      expect(screen.getByText('API 모니터링 대시보드')).toBeInTheDocument();
    });
  });
});