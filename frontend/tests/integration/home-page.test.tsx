import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Home from '~/routes/_index';
import { AuthProvider } from '~/contexts/AuthContext';
import { NotificationProvider } from '~/contexts/NotificationContext';
import { ThemeProvider } from '~/contexts/ThemeContext';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock modules
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPosts: vi.fn().mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: '1',
            title: '아파트 관리비 절약법',
            content: '유용한 절약 팁입니다',
            created_at: '2024-01-01',
            author: { display_name: '관리사무소' },
            metadata_type: 'property-info'
          },
          {
            id: '2', 
            title: '엘리베이터 점검 안내',
            content: '정기 점검 일정 공지',
            created_at: '2024-01-02',
            author: { display_name: '시설팀' },
            metadata_type: 'property-info'
          }
        ]
      }
    })
  }
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <ThemeProvider>
      <NotificationProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </NotificationProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe('Home Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('환영 메시지를 표시한다', async () => {
    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    expect(screen.getByText(/XAI 아파트 커뮤니티에 오신 것을 환영합니다/)).toBeInTheDocument();
  });

  it('주요 서비스 링크들을 표시한다', async () => {
    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    expect(screen.getByText('정보')).toBeInTheDocument();
    expect(screen.getByText('입주 업체 서비스')).toBeInTheDocument();
    expect(screen.getByText('전문가 꿀정보')).toBeInTheDocument();
  });

  it('최근 게시글 미리보기를 표시한다', async () => {
    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    // 최근 게시글 섹션이 존재하는지 확인
    expect(screen.getByText('최근 게시글')).toBeInTheDocument();
  });

  it('복잡한 API 테스트 도구가 표시되지 않는다', () => {
    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    // 기존 대시보드의 복잡한 요소들이 없는지 확인
    expect(screen.queryByText('API 테스트')).not.toBeInTheDocument();
    expect(screen.queryByText('완료된 API')).not.toBeInTheDocument();
    expect(screen.queryByText('진행중 API')).not.toBeInTheDocument();
  });

  it('주요 서비스 링크가 올바른 경로를 가진다', () => {
    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    // 정확한 링크 텍스트로 찾기
    const infoLink = screen.getByText('정보').closest('a');
    const servicesLink = screen.getByText('입주 업체 서비스').closest('a');
    const tipsLink = screen.getByText('전문가 꿀정보').closest('a');

    expect(infoLink).toHaveAttribute('href', '/info');
    expect(servicesLink).toHaveAttribute('href', '/services');
    expect(tipsLink).toHaveAttribute('href', '/tips');
  });
});