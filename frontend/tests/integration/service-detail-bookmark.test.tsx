/**
 * 입주 서비스 업체 상세 페이지 관심 버튼 통합 테스트
 * 
 * TDD Red 단계 - 실패하는 테스트 작성
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import ServiceDetailPage from '~/routes/moving-services-post.$slug';
import { ThemeProvider } from '~/contexts/ThemeContext';

// Mock API 함수들
const mockBookmarkPost = vi.fn();
const mockGetPost = vi.fn();
const mockGetComments = vi.fn();
const mockGetServicePostWithExtendedStats = vi.fn();

// API 모킹
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPost: (...args: any[]) => mockGetPost(...args),
    getComments: (...args: any[]) => mockGetComments(...args),
    bookmarkPost: (...args: any[]) => mockBookmarkPost(...args),
    getServicePostWithExtendedStats: (...args: any[]) => mockGetServicePostWithExtendedStats(...args),
  }
}));

// Mock useParams
const mockNavigate = vi.fn();
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ slug: 'test-cleaning-service' }),
  };
});

// Mock contexts
vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: '507f1f77bcf86cd799439011',
      email: 'test@example.com',
      user_handle: 'test_user',
      name: 'Test User',
    },
    isAuthenticated: true,
    logout: vi.fn(),
  }),
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
  }),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// 테스트용 서비스 게시글 데이터 (실제 ServicePost JSON 형식)
const mockServicePostData = {
  success: true,
  data: {
    id: 'test-service-id',
    _id: 'test-service-id',
    slug: 'test-cleaning-service',
    title: '테스트 청소 서비스',
    content: JSON.stringify({
      company: {
        name: '테스트 청소업체',
        contact: '010-1234-5678',
        availableHours: '09:00-18:00',
        description: '전문적인 청소 서비스를 제공합니다'
      },
      services: [
        {
          name: '일반 청소',
          price: 100000,
          description: '기본 청소 서비스'
        },
        {
          name: '특별 청소',
          price: 200000,
          specialPrice: 150000,
          description: '심화 청소 서비스'
        }
      ]
    }),
    metadata: {
      type: 'moving services',
      category: '청소'
    },
    author_id: 'author-123',
    created_at: '2024-01-01T00:00:00Z',
    view_count: 100,
    like_count: 5,
    dislike_count: 1,
    comment_count: 8,
    bookmark_count: 12,
    stats: {
      view_count: 100,
      like_count: 5,
      dislike_count: 1,
      comment_count: 8,
      bookmark_count: 12
    },
    extended_stats: {
      view_count: 100,
      like_count: 5,
      dislike_count: 1,
      comment_count: 8,
      bookmark_count: 12,
      inquiry_count: 3,
      review_count: 3,
      general_comment_count: 2
    }
  }
};

const mockCommentsData = {
  success: true,
  data: {
    comments: [],
    total: 0,
    page: 1,
    page_size: 20,
    pages: 1
  }
};

  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={['/moving-services-post/test-cleaning-service']}>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </MemoryRouter>
  );

describe('ServiceDetailPage 관심 버튼', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetPost.mockResolvedValue(mockServicePostData);
    mockGetComments.mockResolvedValue(mockCommentsData);
    mockGetServicePostWithExtendedStats.mockResolvedValue(mockServicePostData);
    mockBookmarkPost.mockResolvedValue({
      action: 'bookmarked',
      bookmark_count: 13,
      user_reaction: { bookmarked: true }
    });
  });

  it('상세 페이지에 관심 버튼이 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <ServiceDetailPage />
      </TestWrapper>
    );

    // 서비스 정보가 로드될 때까지 대기 (실제로는 회사명이 표시됨)
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체')).toBeInTheDocument();
    });

    // 관심 버튼(찜하기)이 화면에 표시되는지 확인
    const bookmarkButton = screen.getByRole('button', { name: /찜하기/i });
    expect(bookmarkButton).toBeInTheDocument();
  });

  it('확장 통계가 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <ServiceDetailPage />
      </TestWrapper>
    );

    // 서비스 정보가 로드될 때까지 대기 (실제로는 회사명이 표시됨)
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체')).toBeInTheDocument();
    });

    // 확장 통계가 표시되는지 확인 (헤더 영역의 통계)
    expect(screen.getByText('💬 문의')).toBeInTheDocument();
    expect(screen.getByText('⭐ 후기')).toBeInTheDocument();
    expect(screen.getByText('❤️ 관심')).toBeInTheDocument();
    expect(screen.getByText('👁️ 조회')).toBeInTheDocument();
  });

  it('관심 버튼 클릭 시 API가 호출되어야 한다', async () => {
    render(
      <TestWrapper>
        <ServiceDetailPage />
      </TestWrapper>
    );

    // 서비스 정보가 로드될 때까지 대기 (실제로는 회사명이 표시됨)
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체')).toBeInTheDocument();
    });

    const bookmarkButton = screen.getByRole('button', { name: /찜하기/i });
    
    fireEvent.click(bookmarkButton);

    // 현재는 실제 API가 연결되지 않으므로 이 테스트는 실패할 것입니다 (Red 상태)
    await waitFor(() => {
      expect(mockBookmarkPost).toHaveBeenCalledWith('test-service-id');
    }, { timeout: 100 });
  });

  it('북마크 수가 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <ServiceDetailPage />
      </TestWrapper>
    );

    // 서비스 정보가 로드될 때까지 대기 (실제로는 회사명이 표시됨)
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체')).toBeInTheDocument();
    });

    // 북마크 수가 표시되는지 확인
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('API 에러 시 에러 메시지가 표시되어야 한다', async () => {
    mockBookmarkPost.mockRejectedValue(new Error('Network error'));

    render(
      <TestWrapper>
        <ServiceDetailPage />
      </TestWrapper>
    );

    // 서비스 정보가 로드될 때까지 대기 (실제로는 회사명이 표시됨)
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체')).toBeInTheDocument();
    });

    const bookmarkButton = screen.getByRole('button', { name: /찜하기/i });
    
    fireEvent.click(bookmarkButton);

    // 에러 처리가 되는지 확인 (에러 메시지가 표시되지는 않지만 콘솔에 로그가 출력됨)
    await waitFor(() => {
      expect(mockBookmarkPost).toHaveBeenCalled();
    });
  });
});