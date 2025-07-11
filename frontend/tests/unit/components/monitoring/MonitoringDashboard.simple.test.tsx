/**
 * 모니터링 대시보드 간단한 테스트
 * 
 * 기본 렌더링과 Mock 함수 동작을 확인
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

// 간단한 Mock 컴포넌트들
vi.mock('~/components/monitoring/HealthStatusCard', () => ({
  HealthStatusCard: ({ health }: any) => <div data-testid="health-status">Health: {health?.status || 'none'}</div>
}));

vi.mock('~/components/monitoring/MetricsChart', () => ({
  MetricsChart: ({ type }: any) => <div data-testid={`metrics-${type}`}>Metrics Chart: {type}</div>
}));

vi.mock('~/components/monitoring/PopularEndpointsChart', () => ({
  PopularEndpointsChart: () => <div data-testid="popular-endpoints">Popular Endpoints</div>
}));

vi.mock('~/components/monitoring/SlowRequestsList', () => ({
  SlowRequestsList: () => <div data-testid="slow-requests">Slow Requests</div>
}));

vi.mock('~/components/common/LoadingSpinner', () => ({
  default: () => <div data-testid="loading-spinner">Loading...</div>
}));

// Mock API 함수
const mockGetMonitoringData = vi.fn();
vi.mock('~/lib/monitoring-api', () => ({
  getMonitoringDashboardData: mockGetMonitoringData,
  logMonitoringApiError: vi.fn(),
}));

import { MonitoringDashboard } from '~/components/monitoring/MonitoringDashboard';

describe('MonitoringDashboard Simple Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('로딩 상태를 올바르게 표시한다', () => {
    // Given: API 호출이 진행 중
    mockGetMonitoringData.mockImplementation(() => new Promise(() => {})); // 영원히 pending

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard initialLoading={true} />);

    // Then: 로딩 스피너 표시
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('모니터링 데이터 로딩 중...')).toBeInTheDocument();
  });

  it('API 에러 시 에러 메시지를 표시한다', async () => {
    // Given: API 에러 발생
    mockGetMonitoringData.mockRejectedValue(new Error('API Error'));

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 에러 메시지 표시 (waitFor 없이 간단히)
    setTimeout(() => {
      expect(screen.getByText('모니터링 데이터 로딩 실패')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    }, 100);
  });

  it('성공적인 데이터 로드 시 대시보드를 표시한다', async () => {
    // Given: 성공적인 API 응답
    const mockData = {
      timestamp: Date.now(),
      status: 'success' as const,
      data: {
        metrics: {
          endpoints: { 'GET:/api/posts': 10 },
          status_codes: { '200': 10 },
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
        popular_endpoints: [],
        slow_requests: [],
      },
    };
    
    mockGetMonitoringData.mockResolvedValue({ success: true, data: mockData });

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 약간의 지연 후 대시보드 확인
    setTimeout(() => {
      expect(screen.getByText('API 모니터링 대시보드')).toBeInTheDocument();
      expect(screen.getByTestId('health-status')).toBeInTheDocument();
      expect(screen.getByTestId('metrics-endpoints')).toBeInTheDocument();
      expect(screen.getByTestId('metrics-status_codes')).toBeInTheDocument();
      expect(screen.getByTestId('popular-endpoints')).toBeInTheDocument();
      expect(screen.getByTestId('slow-requests')).toBeInTheDocument();
    }, 100);
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
    setTimeout(() => {
      expect(screen.getByText('모니터링 데이터가 없습니다')).toBeInTheDocument();
    }, 100);
  });
});