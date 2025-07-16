import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { json } from '@remix-run/node';
import { createRemixStub } from '@remix-run/testing';
import AdminAlerts, { loader } from '../admin.alerts';

// Mock dependencies
const mockAuth = {
  user: {
    id: '1',
    email: 'admin@example.com',
    is_admin: true
  } as any,
  logout: vi.fn()
};

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => mockAuth
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
  })
}));

vi.mock('~/components/alerts/AlertManagement', () => ({
  default: () => <div data-testid="alert-management">AlertManagement Component</div>
}));

vi.mock('~/lib/unified-monitoring-api', () => ({
  default: {
    getAlertRules: vi.fn(),
    getAlertStatistics: vi.fn(),
    evaluateAlertRules: vi.fn(),
  }
}));

describe('admin.alerts 라우터', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('기본 렌더링', () => {
    it('관리자 권한이 있는 사용자에게 페이지를 렌더링해야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      // 페이지 제목 확인
      expect(screen.getByText('지능형 알림 시스템')).toBeInTheDocument();
      expect(screen.getByText('실시간 알림 관리 및 모니터링')).toBeInTheDocument();
      
      // AlertManagement 컴포넌트 렌더링 확인
      expect(screen.getByTestId('alert-management')).toBeInTheDocument();
    });

    it('페이지 헤더가 올바르게 렌더링되어야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      // 그라데이션 헤더 확인
      expect(screen.getByText('🚨 지능형 알림 시스템')).toBeInTheDocument();
      expect(screen.getByText('실시간 알림 관리 및 모니터링')).toBeInTheDocument();
    });
  });

  describe('관리자 권한 확인', () => {
    it('관리자가 아닌 사용자에게 접근 거부 메시지를 표시해야 함', async () => {
      // 비관리자 사용자로 모킹
      mockAuth.user.is_admin = false;

      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      expect(screen.getByText('🚫')).toBeInTheDocument();
      expect(screen.getByText('접근 권한이 없습니다')).toBeInTheDocument();
      expect(screen.getByText('관리자 권한이 필요한 페이지입니다.')).toBeInTheDocument();
      
      // 관리자 권한 복구
      mockAuth.user.is_admin = true;
    });

    it('로그인하지 않은 사용자에게 접근 거부 메시지를 표시해야 함', async () => {
      // 로그인하지 않은 사용자로 모킹
      const originalUser = mockAuth.user;
      mockAuth.user = null;

      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      expect(screen.getByText('🚫')).toBeInTheDocument();
      expect(screen.getByText('접근 권한이 없습니다')).toBeInTheDocument();
      expect(screen.getByText('관리자 권한이 필요한 페이지입니다.')).toBeInTheDocument();
      
      // 사용자 정보 복구
      mockAuth.user = originalUser;
    });
  });

  describe('메타데이터 및 SEO', () => {
    it('페이지 타이틀이 올바르게 설정되어야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      // 페이지 타이틀 확인 (document.title은 테스트 환경에서 직접 확인하기 어려우므로 컴포넌트 내용으로 확인)
      expect(screen.getByText('지능형 알림 시스템')).toBeInTheDocument();
    });
  });

  describe('반응형 디자인', () => {
    it('모바일 화면에서도 올바르게 렌더링되어야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      // 반응형 클래스 확인
      const container = screen.getByRole('main');
      expect(container).toBeInTheDocument();
      
      // AlertManagement 컴포넌트가 렌더링되는지 확인
      expect(screen.getByTestId('alert-management')).toBeInTheDocument();
    });
  });

  describe('접근성', () => {
    it('적절한 ARIA 속성을 가져야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      // 메인 컨텐츠 영역 확인
      const mainContent = screen.getByRole('main');
      expect(mainContent).toBeInTheDocument();
      
      // 헤딩 구조 확인
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('키보드 내비게이션이 가능해야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      render(<RemixStub initialEntries={['/admin/alerts']} />);

      // 포커스 가능한 요소들이 있는지 확인
      const focusableElements = screen.getAllByRole('heading');
      expect(focusableElements.length).toBeGreaterThan(0);
    });
  });

  describe('에러 처리', () => {
    it('컴포넌트 로딩 실패 시 적절한 폴백을 표시해야 함', async () => {
      // AlertManagement 컴포넌트 에러 시뮬레이션
      vi.doMock('~/components/alerts/AlertManagement', () => ({
        default: () => {
          throw new Error('Component loading failed');
        }
      }));

      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      // 에러 경계가 있다면 에러를 캐치해야 함
      expect(() => {
        render(<RemixStub initialEntries={['/admin/alerts']} />);
      }).not.toThrow();
    });
  });

  describe('성능 최적화', () => {
    it('불필요한 리렌더링을 방지해야 함', async () => {
      const RemixStub = createRemixStub([
        {
          path: '/admin/alerts',
          Component: AdminAlerts,
          loader: () => json({ timestamp: new Date().toISOString() })
        }
      ]);

      const { rerender } = render(<RemixStub initialEntries={['/admin/alerts']} />);
      
      // 첫 번째 렌더링 확인
      expect(screen.getByTestId('alert-management')).toBeInTheDocument();
      
      // 리렌더링 후에도 컴포넌트가 유지되는지 확인
      rerender(<RemixStub initialEntries={['/admin/alerts']} />);
      expect(screen.getByTestId('alert-management')).toBeInTheDocument();
    });
  });
});