/**
 * 모니터링 대시보드 컴포넌트 단위 테스트
 * 
 * TDD 방식으로 API 모니터링 대시보드 UI 테스트
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MonitoringDashboard } from '~/components/monitoring/MonitoringDashboard';
import type { MonitoringData } from '~/types/monitoring';

// Mock API 함수
vi.mock('~/lib/monitoring-api', () => ({
  getMonitoringDashboardData: vi.fn(),
  logMonitoringApiError: vi.fn(),
}));

// Mock된 함수들 가져오기
import { getMonitoringDashboardData } from '~/lib/monitoring-api';
const mockGetMonitoringData = vi.mocked(getMonitoringDashboardData);

describe('MonitoringDashboard', () => {
  const mockMonitoringData: MonitoringData = {
    timestamp: Date.now(),
    status: 'success',
    data: {
      metrics: {
        endpoints: {
          'GET:/api/posts': 150,
          'POST:/api/posts': 25,
          'GET:/api/users': 75,
        },
        status_codes: {
          '200': 220,
          '201': 25,
          '404': 3,
          '500': 2,
        },
        timestamp: Date.now(),
      },
      health: {
        status: 'healthy',
        total_requests: 250,
        success_requests: 245,
        error_requests: 5,
        error_rate: 0.02,
        availability: 0.98,
        timestamp: Date.now(),
      },
      popular_endpoints: [
        { endpoint: 'GET:/api/posts', requests: 150 },
        { endpoint: 'GET:/api/users', requests: 75 },
        { endpoint: 'POST:/api/posts', requests: 25 },
      ],
      slow_requests: [
        {
          endpoint: 'GET:/api/posts/heavy',
          response_time: 2.5,
          timestamp: Date.now() - 300000,
          status_code: 200,
        },
        {
          endpoint: 'POST:/api/files/upload',
          response_time: 3.1,
          timestamp: Date.now() - 600000,
          status_code: 201,
        },
      ],
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('성공적으로 대시보드 데이터를 로드하고 표시한다', async () => {
    // Given: API가 성공적인 응답을 반환
    mockGetMonitoringData.mockResolvedValue(mockMonitoringData);

    // When: 대시보드 컴포넌트를 렌더링
    render(<MonitoringDashboard />);

    // Then: 로딩 상태가 표시됨
    expect(screen.getByText('모니터링 데이터 로딩 중...')).toBeInTheDocument();

    // 데이터 로딩 완료 후 대시보드 표시
    await waitFor(() => {
      expect(screen.getByText('API 모니터링 대시보드')).toBeInTheDocument();
    });

    // 헬스 상태 표시
    expect(screen.getByText('시스템 상태: 정상')).toBeInTheDocument();
    expect(screen.getByText('총 요청: 250')).toBeInTheDocument();
    expect(screen.getByText('에러율: 2.0%')).toBeInTheDocument();

    // API 호출 확인
    expect(mockGetMonitoringData).toHaveBeenCalledTimes(1);
  });

  it('헬스 상태에 따라 적절한 색상과 상태를 표시한다', async () => {
    // Given: 경고 상태의 헬스 데이터
    const warningData = {
      ...mockMonitoringData,
      data: {
        ...mockMonitoringData.data,
        health: {
          ...mockMonitoringData.data.health,
          status: 'warning',
          error_rate: 0.03, // 3%
        },
      },
    };
    mockGetMonitoringData.mockResolvedValue(warningData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 경고 상태 표시
    await waitFor(() => {
      expect(screen.getByText('시스템 상태: 주의')).toBeInTheDocument();
    });

    const statusElement = screen.getByText('시스템 상태: 주의');
    expect(statusElement).toHaveClass('text-yellow-600'); // 경고 색상
  });

  it('치명적 상태에서 적절한 경고를 표시한다', async () => {
    // Given: 치명적 상태의 헬스 데이터
    const criticalData = {
      ...mockMonitoringData,
      data: {
        ...mockMonitoringData.data,
        health: {
          ...mockMonitoringData.data.health,
          status: 'critical',
          error_rate: 0.07, // 7%
        },
      },
    };
    mockGetMonitoringData.mockResolvedValue(criticalData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 치명적 상태 표시
    await waitFor(() => {
      expect(screen.getByText('시스템 상태: 위험')).toBeInTheDocument();
    });

    const statusElement = screen.getByText('시스템 상태: 위험');
    expect(statusElement).toHaveClass('text-red-600'); // 위험 색상
  });

  it('인기 엔드포인트 차트를 표시한다', async () => {
    // Given: 모니터링 데이터
    mockGetMonitoringData.mockResolvedValue(mockMonitoringData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 인기 엔드포인트 차트 표시
    await waitFor(() => {
      expect(screen.getByText('인기 엔드포인트')).toBeInTheDocument();
    });

    // 엔드포인트별 요청 수 표시
    expect(screen.getByText('GET:/api/posts')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument(); // 요청 수
    expect(screen.getByText('GET:/api/users')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();
  });

  it('상태코드 분포 차트를 표시한다', async () => {
    // Given: 모니터링 데이터
    mockGetMonitoringData.mockResolvedValue(mockMonitoringData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 상태코드 분포 차트 표시
    await waitFor(() => {
      expect(screen.getByText('응답 상태코드 분포')).toBeInTheDocument();
    });

    // 상태코드별 수 표시
    expect(screen.getByText('200: 220')).toBeInTheDocument();
    expect(screen.getByText('201: 25')).toBeInTheDocument();
    expect(screen.getByText('404: 3')).toBeInTheDocument();
    expect(screen.getByText('500: 2')).toBeInTheDocument();
  });

  it('느린 요청 목록을 표시한다', async () => {
    // Given: 모니터링 데이터
    mockGetMonitoringData.mockResolvedValue(mockMonitoringData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 느린 요청 목록 표시
    await waitFor(() => {
      expect(screen.getByText('느린 요청 목록')).toBeInTheDocument();
    });

    // 느린 요청 항목들 표시
    expect(screen.getByText('GET:/api/posts/heavy')).toBeInTheDocument();
    expect(screen.getByText('2.5초')).toBeInTheDocument();
    expect(screen.getByText('POST:/api/files/upload')).toBeInTheDocument();
    expect(screen.getByText('3.1초')).toBeInTheDocument();
  });

  it('API 에러 발생 시 에러 메시지를 표시한다', async () => {
    // Given: API 에러 발생
    const errorMessage = 'Failed to fetch monitoring data';
    mockGetMonitoringData.mockRejectedValue(new Error(errorMessage));

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 에러 메시지 표시
    await waitFor(() => {
      expect(screen.getByText('모니터링 데이터 로딩 실패')).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('새로고침 버튼 클릭 시 데이터를 다시 로드한다', async () => {
    // Given: 초기 데이터 로드
    mockGetMonitoringData.mockResolvedValue(mockMonitoringData);

    render(<MonitoringDashboard />);

    await waitFor(() => {
      expect(screen.getByText('API 모니터링 대시보드')).toBeInTheDocument();
    });

    // When: 새로고침 버튼 클릭
    const refreshButton = screen.getByText('새로고침');
    refreshButton.click();

    // Then: API가 다시 호출됨
    await waitFor(() => {
      expect(mockGetMonitoringData).toHaveBeenCalledTimes(2);
    });
  });

  it('자동 새로고침 기능이 작동한다', async () => {
    // Given: 자동 새로고침 활성화
    vi.useFakeTimers();
    mockGetMonitoringData.mockResolvedValue(mockMonitoringData);

    render(<MonitoringDashboard autoRefresh={true} refreshInterval={5000} />);

    // 초기 로드
    await waitFor(() => {
      expect(mockGetMonitoringData).toHaveBeenCalledTimes(1);
    });

    // When: 5초 경과
    vi.advanceTimersByTime(5000);

    // Then: 자동으로 다시 로드됨
    await waitFor(() => {
      expect(mockGetMonitoringData).toHaveBeenCalledTimes(2);
    });

    vi.useRealTimers();
  });

  it('빈 데이터일 때 적절한 메시지를 표시한다', async () => {
    // Given: 빈 데이터
    const emptyData = {
      ...mockMonitoringData,
      data: {
        metrics: { endpoints: {}, status_codes: {}, timestamp: Date.now() },
        health: null,
        popular_endpoints: [],
        slow_requests: [],
      },
    };
    mockGetMonitoringData.mockResolvedValue(emptyData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 빈 데이터 메시지 표시
    await waitFor(() => {
      expect(screen.getByText('모니터링 데이터가 없습니다')).toBeInTheDocument();
    });
  });

  it('실시간 타임스탬프를 표시한다', async () => {
    // Given: 현재 시간의 모니터링 데이터
    const currentTime = Date.now();
    const timestampData = {
      ...mockMonitoringData,
      timestamp: currentTime,
    };
    mockGetMonitoringData.mockResolvedValue(timestampData);

    // When: 컴포넌트 렌더링
    render(<MonitoringDashboard />);

    // Then: 타임스탬프 표시
    await waitFor(() => {
      expect(screen.getByText(/마지막 업데이트:/)).toBeInTheDocument();
    });

    // 시간 형식이 올바르게 표시되는지 확인
    const timeElement = screen.getByText(/\d{2}:\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });
});