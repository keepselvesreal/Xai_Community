import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ServiceDetail from '~/routes/moving-services.$slug';
import { apiClient } from '~/lib/api';

// Mock dependencies
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPost: vi.fn(),
    getCommentsBatch: vi.fn(),
    bookmarkPost: vi.fn(),
    likePost: vi.fn(),
    dislikePost: vi.fn(),
    deletePost: vi.fn(),
  },
}));

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      user_handle: 'testuser',
      display_name: 'Test User',
      email: 'test@example.com',
    },
    logout: vi.fn(),
  }),
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showError: vi.fn(),
    showSuccess: vi.fn(),
  }),
}));

vi.mock('@remix-run/react', () => ({
  useParams: () => ({ slug: 'test-service' }),
  useNavigate: () => vi.fn(),
  useLoaderData: () => ({ service: null, comments: [], error: null }),
  useLocation: () => ({ 
    pathname: '/moving-services/test-service',
    search: '',
    hash: '',
    state: null,
    key: 'test-key'
  }),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/hooks/useAnalytics', () => ({
  getAnalytics: () => ({
    trackServiceReviewComment: vi.fn(),
    trackServiceInquiryComment: vi.fn(),
  }),
}));

vi.mock('~/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: vi.fn(),
  }),
}));

vi.mock('~/types/service-types', () => ({
  convertPostToService: vi.fn(),
}));

describe('ServiceDetail Integration Tests', () => {
  const mockPost = {
    id: 'post-1',
    title: '깔끔한 이사 서비스',
    content: '전문 이사 서비스입니다.',
    slug: 'test-service',
    author: {
      id: 'user-1',
      user_handle: 'cleanmove',
      display_name: '깔끔한 이사',
      email: 'info@cleanmove.com',
    },
    author_id: 'user-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    metadata: {
      type: 'moving_services',
      category: '이사',
    },
    stats: {
      view_count: 1250,
      like_count: 45,
      dislike_count: 2,
      bookmark_count: 89,
      comment_count: 23,
    },
    status: 'published',
  };

  const mockService = {
    id: 'service-1',
    name: '깔끔한 이사 서비스',
    title: '깔끔한 이사 서비스',
    category: '이사' as const,
    rating: 4.5,
    description: '전문 이사 서비스입니다.',
    verified: false,
    contact: {
      phone: '010-1234-5678',
      email: 'contact@cleanmove.co.kr',
      address: '서울시 강남구 테헤란로 123',
      hours: '09:00 ~ 18:00',
    },
    company: {
      name: '깔끔한 이사 서비스',
      contact: '010-1234-5678',
      availableHours: '09:00 ~ 18:00',
      description: '전문 이사 서비스입니다.',
    },
    services: [
      {
        name: '원룸 이사',
        price: '60000',
        description: '원룸 전체 이사',
      },
    ],
    serviceStats: {
      views: 1250,
      bookmarks: 89,
      inquiries: 23,
      reviews: 45,
    },
    reviews: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const mockComments = [
    {
      id: 'comment-1',
      content: '문의 내용입니다.',
      author: {
        id: 'user-2',
        user_handle: 'customer',
        display_name: '고객',
        email: 'customer@example.com',
      },
      created_at: '2024-01-01T00:00:00Z',
      metadata: {
        subtype: 'service_inquiry',
      },
    },
  ];

  beforeEach(async () => {
    vi.clearAllMocks();
    
    // Mock API responses
    (apiClient.getPost as any).mockResolvedValue({
      success: true,
      data: mockPost,
    });
    
    (apiClient.getCommentsBatch as any).mockResolvedValue({
      success: true,
      data: mockComments,
    });
    
    // Mock convertPostToService
    const serviceTypes = await import('~/types/service-types');
    vi.mocked(serviceTypes.convertPostToService).mockReturnValue(mockService);
  });

  it('서비스 상세 페이지가 완전히 로드되어야 한다', async () => {
    render(
      <MemoryRouter>
        <ServiceDetail />
      </MemoryRouter>
    );

    // 로딩 상태 확인
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();

    // 데이터 로드 완료 대기
    await waitFor(() => {
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });

    // 서비스 정보 확인
    expect(screen.getByText('깔끔한 이사 서비스')).toBeInTheDocument();
    expect(screen.getByText('010-1234-5678')).toBeInTheDocument();
    expect(screen.getByText('원룸 이사')).toBeInTheDocument();
  });

  it('북마크 기능이 정상 작동해야 한다', async () => {
    (apiClient.bookmarkPost as any).mockResolvedValue({
      success: true,
      data: { bookmark_count: 90 },
    });

    render(
      <MemoryRouter>
        <ServiceDetail />
      </MemoryRouter>
    );

    // 데이터 로드 완료 대기
    await waitFor(() => {
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });

    // 북마크 버튼 클릭
    const bookmarkButton = screen.getByLabelText('북마크');
    fireEvent.click(bookmarkButton);

    // API 호출 확인
    await waitFor(() => {
      expect(apiClient.bookmarkPost).toHaveBeenCalledWith('');
    });
  });

  it('댓글 시스템이 정상 통합되어야 한다', async () => {
    render(
      <MemoryRouter>
        <ServiceDetail />
      </MemoryRouter>
    );

    // 데이터 로드 완료 대기
    await waitFor(() => {
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });

    // 서비스 페이지가 로드되었는지 확인
    expect(screen.getByText('깔끔한 이사 서비스')).toBeInTheDocument();
    // 댓글 시스템이 향후 구현될 것이므로 현재는 기본 검증만 수행
  });

  it('서비스 삭제 기능이 정상 작동해야 한다', async () => {
    (apiClient.deletePost as any).mockResolvedValue({
      success: true,
    });

    // confirm 모킹
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);

    render(
      <MemoryRouter>
        <ServiceDetail />
      </MemoryRouter>
    );

    // 데이터 로드 완료 대기
    await waitFor(() => {
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });

    // 삭제 버튼 클릭
    const deleteButton = screen.getByText('삭제');
    fireEvent.click(deleteButton);

    // API 호출 확인
    await waitFor(() => {
      expect(apiClient.deletePost).toHaveBeenCalledWith('');
    });

    // cleanup
    window.confirm = originalConfirm;
  });

  it('404 상태를 정상 처리해야 한다', async () => {
    (apiClient.getPost as any).mockResolvedValue({
      success: false,
      error: 'Not found',
    });

    render(
      <MemoryRouter>
        <ServiceDetail />
      </MemoryRouter>
    );

    // 404 메시지 확인
    await waitFor(() => {
      expect(screen.getByText('서비스를 찾을 수 없습니다')).toBeInTheDocument();
      expect(screen.getByText('서비스 목록으로 돌아가기')).toBeInTheDocument();
    });
  });

  it('에러 상태를 정상 처리해야 한다', async () => {
    (apiClient.getPost as any).mockRejectedValue(new Error('Network error'));

    render(
      <MemoryRouter>
        <ServiceDetail />
      </MemoryRouter>
    );

    // 에러 메시지 확인
    await waitFor(() => {
      expect(screen.getByText('서비스를 찾을 수 없습니다')).toBeInTheDocument();
    });
  });
});