/**
 * 입주 서비스 업체 목록 페이지 확장 통계 표시 통합 테스트
 * 
 * TDD Red 단계 - 실패하는 테스트 작성
 * 목록에서 관심, 문의, 후기 통계가 API 기반으로 표시되는지 확인
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import Services from '~/routes/services';
import { ThemeProvider } from '~/contexts/ThemeContext';

// Mock API 함수들
const mockGetPosts = vi.fn();
const mockGetServicePostsWithExtendedStats = vi.fn();

// API 모킹
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPosts: (...args: any[]) => mockGetPosts(...args),
    getServicePostsWithExtendedStats: (...args: any[]) => mockGetServicePostsWithExtendedStats(...args),
  }
}));

// Mock useAuth
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

// Mock useNotification
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

// Mock @remix-run/react with importOriginal
vi.mock('@remix-run/react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@remix-run/react')>();
  return {
    ...actual,
    useLoaderData: () => ({
      initialData: null,
      isServerRendered: false
    }),
    useNavigate: () => vi.fn(),
    useLocation: () => ({
      pathname: '/services',
      search: '',
      hash: '',
      state: null,
      key: 'default'
    }),
  };
});

// 테스트용 서비스 목록 데이터 (확장 통계 포함)
const mockServicesWithExtendedStats = {
  success: true,
  data: {
    items: [
      {
        id: 'service-1',
        _id: 'service-1',
        slug: 'test-cleaning-service-1',
        title: '테스트 청소 서비스 1',
        content: JSON.stringify({
          company: {
            name: '테스트 청소업체 1',
            contact: '010-1234-5678',
            availableHours: '09:00-18:00',
            description: '전문적인 청소 서비스를 제공합니다'
          },
          services: [
            {
              name: '일반 청소',
              price: 100000,
              description: '기본 청소 서비스'
            }
          ]
        }),
        metadata: {
          type: 'moving services',
          category: '청소'
        },
        author_id: 'author-123',
        created_at: '2024-01-01T00:00:00Z',
        view_count: 150,
        like_count: 8,
        dislike_count: 2,
        comment_count: 12,
        bookmark_count: 15,
        stats: {
          view_count: 150,
          like_count: 8,
          dislike_count: 2,
          comment_count: 12,
          bookmark_count: 15
        },
        // ✅ 확장 통계 추가 (Green 단계)
        extended_stats: {
          view_count: 150,
          like_count: 8,
          dislike_count: 2,
          comment_count: 12,
          bookmark_count: 15,
          inquiry_count: 4,
          review_count: 8,
          general_comment_count: 0
        }
      },
      {
        id: 'service-2',
        _id: 'service-2',
        slug: 'test-moving-service-2',
        title: '테스트 이사 서비스 2',
        content: JSON.stringify({
          company: {
            name: '테스트 이사업체 2',
            contact: '010-9876-5432',
            availableHours: '08:00-20:00',
            description: '안전한 이사 서비스를 제공합니다'
          },
          services: [
            {
              name: '포장이사',
              price: 500000,
              description: '포장부터 이사까지'
            }
          ]
        }),
        metadata: {
          type: 'moving services',
          category: '이사'
        },
        author_id: 'author-456',
        created_at: '2024-01-02T00:00:00Z',
        view_count: 200,
        like_count: 12,
        dislike_count: 1,
        comment_count: 18,
        bookmark_count: 25,
        stats: {
          view_count: 200,
          like_count: 12,
          dislike_count: 1,
          comment_count: 18,
          bookmark_count: 25
        },
        // ✅ 확장 통계 추가 (Green 단계)
        extended_stats: {
          view_count: 200,
          like_count: 12,
          dislike_count: 1,
          comment_count: 18,
          bookmark_count: 25,
          inquiry_count: 6,
          review_count: 12,
          general_comment_count: 0
        }
      }
    ],
    total: 2,
    page: 1,
    size: 10,
    pages: 1
  }
};

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter initialEntries={['/services']}>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </MemoryRouter>
);

describe('Services 목록 페이지 확장 통계', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetPosts.mockResolvedValue(mockServicesWithExtendedStats);
    mockGetServicePostsWithExtendedStats.mockResolvedValue(mockServicesWithExtendedStats);
  });

  it('목록에서 기본 통계가 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <Services />
      </TestWrapper>
    );

    // 서비스 목록이 로드될 때까지 대기
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체 1')).toBeInTheDocument();
    });

    // 기본 통계 표시 확인 (조회수, 관심)
    expect(screen.getByText('👁️ 150')).toBeInTheDocument(); // 첫 번째 서비스 조회수
    expect(screen.getByText('관심 15')).toBeInTheDocument(); // 첫 번째 서비스 관심(북마크)수
  });

  it('목록에서 확장 통계 문의수가 API 데이터로 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <Services />
      </TestWrapper>
    );

    // 서비스 목록이 로드될 때까지 대기
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체 1')).toBeInTheDocument();
    });

    // ✅ 확장 통계에서 실제 문의수가 표시되는지 확인 (Green 단계)
    await waitFor(() => {
      expect(screen.getByText('문의 4')).toBeInTheDocument(); // 첫 번째 서비스 실제 문의수
    });
  });

  it('목록에서 확장 통계 후기수가 API 데이터로 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <Services />
      </TestWrapper>
    );

    // 서비스 목록이 로드될 때까지 대기
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체 1')).toBeInTheDocument();
    });

    // ✅ 확장 통계에서 실제 후기수가 표시되는지 확인 (Green 단계)
    await waitFor(() => {
      expect(screen.getByText('후기 8')).toBeInTheDocument(); // 첫 번째 서비스 실제 후기수
    });
  });

  it('여러 서비스의 확장 통계가 모두 표시되어야 한다', async () => {
    render(
      <TestWrapper>
        <Services />
      </TestWrapper>
    );

    // 서비스 목록이 로드될 때까지 대기
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체 1')).toBeInTheDocument();
      expect(screen.getByText('테스트 이사업체 2')).toBeInTheDocument();
    });

    // ✅ 두 번째 서비스의 확장 통계도 확인 (Green 단계)
    await waitFor(() => {
      expect(screen.getByText('문의 6')).toBeInTheDocument(); // 두 번째 서비스 문의수
      expect(screen.getByText('후기 12')).toBeInTheDocument(); // 두 번째 서비스 후기수
    });
  });

  it('확장 통계가 없는 경우 기본값 0으로 표시되어야 한다', async () => {
    // 확장 통계가 없는 데이터로 모킹
    const mockDataWithoutExtendedStats = {
      ...mockServicesWithExtendedStats,
      data: {
        ...mockServicesWithExtendedStats.data,
        items: [
          {
            ...mockServicesWithExtendedStats.data.items[0],
            // extended_stats 없음
          }
        ]
      }
    };
    
    mockGetServicePostsWithExtendedStats.mockResolvedValue(mockDataWithoutExtendedStats);

    render(
      <TestWrapper>
        <Services />
      </TestWrapper>
    );

    // 서비스 목록이 로드될 때까지 대기
    await waitFor(() => {
      expect(screen.getByText('테스트 청소업체 1')).toBeInTheDocument();
    });

    // 확장 통계가 없는 경우 기본값 0으로 표시되는지 확인
    expect(screen.getByText('문의 0')).toBeInTheDocument();
    expect(screen.getByText('후기 0')).toBeInTheDocument();
  });

  it('목록 페이지에서 올바른 API 엔드포인트가 호출되어야 한다', async () => {
    render(
      <TestWrapper>
        <Services />
      </TestWrapper>
    );

    // 목록 API가 호출되었는지 확인
    // 새로운 확장 통계 API 엔드포인트 호출 기대
    await waitFor(() => {
      expect(mockGetServicePostsWithExtendedStats).toHaveBeenCalledWith(1, 50, 'created_at');
    });
  });
});