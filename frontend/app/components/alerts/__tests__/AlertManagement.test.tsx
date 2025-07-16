import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AlertManagement from '../AlertManagement';
import type { AlertRule, AlertStatistics } from '~/types';

// Mock dependencies
vi.mock('~/lib/api', () => ({
  default: {
    getAlertRules: vi.fn(),
    createAlertRule: vi.fn(),
    updateAlertRule: vi.fn(),
    deleteAlertRule: vi.fn(),
    getAlertStatistics: vi.fn(),
    getAlertHistory: vi.fn(),
    evaluateAlertRules: vi.fn(),
  }
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
  })
}));

const mockAlertRules: AlertRule[] = [
  {
    id: '1',
    name: 'CPU 사용률 경고',
    description: 'CPU 사용률이 80% 이상일 때 알림',
    condition: 'greater_than',
    threshold: {
      metric: 'cpu_usage',
      value: 80,
      duration_minutes: 5
    },
    severity: 'high',
    channels: ['email', 'discord'],
    cooldown_minutes: 30,
    escalation_minutes: 60,
    enabled: true,
    tags: { environment: 'production' },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: '2',
    name: '메모리 부족 경고',
    description: '메모리 사용률이 90% 이상일 때 알림',
    condition: 'greater_than',
    threshold: {
      metric: 'memory_usage',
      value: 90,
      duration_minutes: 3
    },
    severity: 'critical',
    channels: ['email'],
    cooldown_minutes: 15,
    escalation_minutes: 30,
    enabled: true,
    tags: { environment: 'production' },
    created_at: '2024-01-01T00:00:00Z'
  }
];

const mockStatistics: AlertStatistics = {
  total_rules: 2,
  active_rules: 2,
  total_alerts: 10,
  alerts_sent_today: 5,
  alerts_by_severity: {
    low: 1,
    medium: 2,
    high: 1,
    critical: 1
  },
  alerts_by_channel: {
    email: 3,
    discord: 2
  },
  alert_rate_per_hour: 0.5
};

describe('AlertManagement 컴포넌트', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('기본 렌더링', () => {
    it('컴포넌트가 올바르게 렌더링되어야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      expect(screen.getByText('알림 관리')).toBeInTheDocument();
      expect(screen.getByText('새 알림 규칙')).toBeInTheDocument();
      expect(screen.getByText('통계')).toBeInTheDocument();
    });

    it('로딩 중일 때 로딩 스피너를 표시해야 함', () => {
      render(<AlertManagement />);
      
      expect(screen.getByText('알림 규칙을 불러오는 중...')).toBeInTheDocument();
    });
  });

  describe('알림 규칙 목록 표시', () => {
    it('알림 규칙 목록을 올바르게 표시해야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
        expect(screen.getByText('메모리 부족 경고')).toBeInTheDocument();
      });

      // 심각도 표시 확인
      expect(screen.getByText('HIGH')).toBeInTheDocument();
      expect(screen.getByText('CRITICAL')).toBeInTheDocument();

      // 활성/비활성 상태 확인
      const enabledButtons = screen.getAllByText('활성');
      expect(enabledButtons).toHaveLength(2);
    });

    it('빈 상태일 때 적절한 메시지를 표시해야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: [] }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('설정된 알림 규칙이 없습니다')).toBeInTheDocument();
        expect(screen.getByText('첫 번째 알림 규칙을 생성해보세요!')).toBeInTheDocument();
      });
    });
  });

  describe('알림 규칙 생성', () => {
    it('새 알림 규칙 버튼을 클릭하면 생성 모달이 열려야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      });

      const createButton = screen.getByText('새 알림 규칙');
      fireEvent.click(createButton);

      expect(screen.getByText('알림 규칙 생성')).toBeInTheDocument();
      expect(screen.getByLabelText('규칙 이름')).toBeInTheDocument();
      expect(screen.getByLabelText('설명')).toBeInTheDocument();
      expect(screen.getByLabelText('조건')).toBeInTheDocument();
      expect(screen.getByLabelText('심각도')).toBeInTheDocument();
    });

    it('생성 폼에서 모든 필드를 입력하고 제출할 수 있어야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });
      mockApiClient.default.createAlertRule.mockResolvedValue({
        success: true,
        data: { id: '3', name: '디스크 공간 경고' }
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      });

      // 생성 모달 열기
      const createButton = screen.getByText('새 알림 규칙');
      await user.click(createButton);

      // 폼 입력
      await user.type(screen.getByLabelText('규칙 이름'), '디스크 공간 경고');
      await user.type(screen.getByLabelText('설명'), '디스크 공간 부족 시 알림');
      await user.selectOptions(screen.getByLabelText('조건'), 'greater_than');
      await user.type(screen.getByLabelText('메트릭'), 'disk_usage');
      await user.type(screen.getByLabelText('임계값'), '90');
      await user.selectOptions(screen.getByLabelText('심각도'), 'high');

      // 제출
      const submitButton = screen.getByText('생성');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockApiClient.default.createAlertRule).toHaveBeenCalledWith({
          name: '디스크 공간 경고',
          description: '디스크 공간 부족 시 알림',
          condition: 'greater_than',
          threshold: {
            metric: 'disk_usage',
            value: 90,
            duration_minutes: 5
          },
          severity: 'high',
          channels: ['email'],
          enabled: true
        });
      });
    });
  });

  describe('알림 규칙 수정', () => {
    it('수정 버튼을 클릭하면 수정 모달이 열려야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('수정');
      await user.click(editButtons[0]);

      expect(screen.getByText('알림 규칙 수정')).toBeInTheDocument();
      expect(screen.getByDisplayValue('CPU 사용률 경고')).toBeInTheDocument();
      expect(screen.getByDisplayValue('CPU 사용률이 80% 이상일 때 알림')).toBeInTheDocument();
    });

    it('수정된 데이터로 API를 호출해야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });
      mockApiClient.default.updateAlertRule.mockResolvedValue({
        success: true,
        data: { id: '1', name: '수정된 CPU 경고' }
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('수정');
      await user.click(editButtons[0]);

      // 이름 수정
      const nameInput = screen.getByDisplayValue('CPU 사용률 경고');
      await user.clear(nameInput);
      await user.type(nameInput, '수정된 CPU 경고');

      // 제출
      const submitButton = screen.getByText('수정');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockApiClient.default.updateAlertRule).toHaveBeenCalledWith('1', {
          name: '수정된 CPU 경고',
          description: 'CPU 사용률이 80% 이상일 때 알림',
          condition: 'greater_than',
          threshold: {
            metric: 'cpu_usage',
            value: 80,
            duration_minutes: 5
          },
          severity: 'high',
          channels: ['email', 'discord'],
          cooldown_minutes: 30,
          escalation_minutes: 60,
          enabled: true,
          tags: { environment: 'production' }
        });
      });
    });
  });

  describe('알림 규칙 삭제', () => {
    it('삭제 버튼을 클릭하면 확인 다이얼로그가 나타나야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByText('삭제');
      await user.click(deleteButtons[0]);

      expect(screen.getByText('알림 규칙 삭제')).toBeInTheDocument();
      expect(screen.getByText('정말로 이 알림 규칙을 삭제하시겠습니까?')).toBeInTheDocument();
      expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
    });

    it('삭제 확인 시 API를 호출해야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });
      mockApiClient.default.deleteAlertRule.mockResolvedValue({
        success: true,
        data: { message: '삭제되었습니다' }
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByText('삭제');
      await user.click(deleteButtons[0]);

      const confirmButton = screen.getByText('삭제');
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockApiClient.default.deleteAlertRule).toHaveBeenCalledWith('1');
      });
    });
  });

  describe('필터링 및 정렬', () => {
    it('심각도별 필터링이 작동해야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
        expect(screen.getByText('메모리 부족 경고')).toBeInTheDocument();
      });

      // 심각도 필터 선택
      const severityFilter = screen.getByLabelText('심각도 필터');
      await user.selectOptions(severityFilter, 'critical');

      // critical 항목만 표시되어야 함
      expect(screen.getByText('메모리 부족 경고')).toBeInTheDocument();
      expect(screen.queryByText('CPU 사용률 경고')).not.toBeInTheDocument();
    });

    it('활성/비활성 필터링이 작동해야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      const rulesWithDisabled = [
        ...mockAlertRules,
        {
          ...mockAlertRules[0],
          id: '3',
          name: '비활성 규칙',
          enabled: false
        }
      ];
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: rulesWithDisabled }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
        expect(screen.getByText('비활성 규칙')).toBeInTheDocument();
      });

      // 활성 규칙만 필터링
      const statusFilter = screen.getByLabelText('상태 필터');
      await user.selectOptions(statusFilter, 'active');

      // 활성 규칙만 표시되어야 함
      expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      expect(screen.queryByText('비활성 규칙')).not.toBeInTheDocument();
    });

    it('검색 기능이 작동해야 함', async () => {
      const user = userEvent.setup();
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
        expect(screen.getByText('메모리 부족 경고')).toBeInTheDocument();
      });

      // 검색
      const searchInput = screen.getByPlaceholderText('알림 규칙 검색...');
      await user.type(searchInput, 'CPU');

      // CPU 관련 항목만 표시되어야 함
      expect(screen.getByText('CPU 사용률 경고')).toBeInTheDocument();
      expect(screen.queryByText('메모리 부족 경고')).not.toBeInTheDocument();
    });
  });

  describe('통계 표시', () => {
    it('알림 통계를 올바르게 표시해야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockResolvedValue({
        success: true,
        data: { rules: mockAlertRules }
      });
      mockApiClient.default.getAlertStatistics.mockResolvedValue({
        success: true,
        data: mockStatistics
      });

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('총 규칙 수')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('활성 규칙')).toBeInTheDocument();
        expect(screen.getByText('오늘 전송된 알림')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });
  });

  describe('에러 처리', () => {
    it('API 에러 시 에러 메시지를 표시해야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockRejectedValue(new Error('API 에러'));
      mockApiClient.default.getAlertStatistics.mockRejectedValue(new Error('API 에러'));

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('알림 규칙을 불러오는 중 오류가 발생했습니다')).toBeInTheDocument();
      });
    });

    it('네트워크 에러 시 적절한 메시지를 표시해야 함', async () => {
      const mockApiClient = await import('~/lib/api');
      mockApiClient.default.getAlertRules.mockRejectedValue(new Error('Network Error'));
      mockApiClient.default.getAlertStatistics.mockRejectedValue(new Error('Network Error'));

      render(<AlertManagement />);

      await waitFor(() => {
        expect(screen.getByText('네트워크 연결을 확인해주세요')).toBeInTheDocument();
      });
    });
  });
});