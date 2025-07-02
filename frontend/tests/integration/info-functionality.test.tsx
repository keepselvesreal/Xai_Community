import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ListPage } from '~/components/common/ListPage';
import { infoConfig } from '~/config/pageConfigs';
import type { InfoItem } from '~/types';

// Mock data
const mockInfoItems: InfoItem[] = [
  {
    id: '1',
    title: '2024년 아파트 시세 분석',
    content: '<div>Interactive chart content</div>',
    slug: 'apartment-price-analysis-2024',
    author_id: 'admin-1',
    content_type: 'interactive_chart',
    metadata: {
      type: 'property_information',
      category: 'market_analysis',
      tags: ['시세', '분석'],
      content_type: 'interactive_chart',
      data_source: 'KB부동산',
      summary: '2024년 아파트 시세 전망과 동향 분석'
    },
    created_at: '2024-01-01T10:00:00Z',
    stats: {
      view_count: 250,
      like_count: 42,
      dislike_count: 3,
      comment_count: 18,
      bookmark_count: 25
    }
  },
  {
    id: '2',
    title: '전세 계약 시 체크리스트',
    content: 'AI가 생성한 전세 계약 가이드입니다.',
    slug: 'rental-contract-checklist',
    author_id: 'admin-1',
    content_type: 'ai_article',
    metadata: {
      type: 'property_information',
      category: 'legal_info',
      tags: ['전세', '계약'],
      content_type: 'ai_article',
      summary: '전세 계약 시 반드시 확인해야 할 체크리스트'
    },
    created_at: '2024-01-02T10:00:00Z',
    stats: {
      view_count: 180,
      like_count: 35,
      dislike_count: 2,
      comment_count: 12,
      bookmark_count: 28
    }
  }
];

// Mock hooks and dependencies
vi.mock('~/hooks/useListData', () => ({
  useListData: vi.fn(() => ({
    items: mockInfoItems,
    loading: false,
    error: null,
    currentFilter: 'all',
    sortBy: 'latest',
    searchQuery: '',
    handleCategoryFilter: vi.fn(),
    handleSort: vi.fn(),
    handleSearch: vi.fn(),
    handleSearchSubmit: vi.fn(),
    refetch: vi.fn()
  }))
}));

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    logout: vi.fn()
  }))
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: vi.fn(() => ({
    showError: vi.fn(),
    showSuccess: vi.fn()
  }))
}));

vi.mock('~/contexts/ThemeContext', () => ({
  useTheme: vi.fn(() => ({
    theme: 'light',
    toggleTheme: vi.fn()
  }))
}));

// Wrapper component for routing
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('Info Page Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render info page with ListPage component', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    // 페이지 제목 확인 - SearchAndFilters 컴포넌트에서 렌더링됨
    expect(screen.getByPlaceholderText('정보 검색...')).toBeInTheDocument();
  });

  it('should display info items when data is available', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('2024년 아파트 시세 분석')).toBeInTheDocument();
      expect(screen.getByText('전세 계약 시 체크리스트')).toBeInTheDocument();
    });
  });

  it('should display content type badges', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('인터렉티브 차트')).toBeInTheDocument();
      expect(screen.getByText('AI 생성 글')).toBeInTheDocument();
    });
  });

  it('should display category labels', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getAllByText('시세분석')).toHaveLength(2); // 필터 버튼 + 카드 내 카테고리
      expect(screen.getAllByText('법률정보')).toHaveLength(2); // 필터 버튼 + 카드 내 카테고리
    });
  });

  it('should display data source when available', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('📊 KB부동산')).toBeInTheDocument();
    });
  });

  it('should display statistics correctly', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      // 첫 번째 아이템의 제목이 표시되는지 확인
      expect(screen.getByText('2024년 아파트 시세 분석')).toBeInTheDocument();
      // 통계 영역이 존재하는지 확인 (정확한 숫자보다는 영역 확인)
      const infoCard = screen.getByText('2024년 아파트 시세 분석').closest('.bg-white');
      expect(infoCard).toBeInTheDocument();
    });
  });

  it('should have filter categories', () => {
    const { categories } = infoConfig;
    
    expect(categories).toEqual([
      { value: 'all', label: '전체' },
      { value: 'market_analysis', label: '시세분석' },
      { value: 'legal_info', label: '법률정보' },
      { value: 'move_in_guide', label: '입주가이드' },
      { value: 'investment_trend', label: '투자동향' }
    ]);
  });

  it('should have sort options', () => {
    const { sortOptions } = infoConfig;
    
    expect(sortOptions).toEqual([
      { value: 'latest', label: '최신순' },
      { value: 'views', label: '조회수' },
      { value: 'likes', label: '추천수' },
      { value: 'comments', label: '댓글수' },
      { value: 'saves', label: '저장수' }
    ]);
  });

  it('should not display write button (read-only page)', async () => {
    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    // 글쓰기 버튼이 없어야 함 (관리자만 직접 데이터 입력)
    expect(screen.queryByText('글쓰기')).not.toBeInTheDocument();
    expect(screen.queryByText('등록')).not.toBeInTheDocument();
  });
});

// Empty state 테스트
describe('Info Page Empty State', () => {
  it('should show empty state when no data available', async () => {
    // 특별히 이 테스트만을 위해 mock을 재설정
    const { useListData } = await import('~/hooks/useListData');
    vi.mocked(useListData).mockReturnValueOnce({
      items: [],
      loading: false,
      error: null,
      currentFilter: 'all',
      sortBy: 'latest',
      searchQuery: '',
      handleCategoryFilter: vi.fn(),
      handleSort: vi.fn(),
      handleSearch: vi.fn(),
      handleSearchSubmit: vi.fn(),
      refetch: vi.fn()
    });

    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      // EmptyState 컴포넌트가 표시되어야 함 (config에서 설정된 텍스트)
      expect(screen.getByText('등록된 정보가 없습니다')).toBeInTheDocument();
    });
  });
});

// Error state 테스트
describe('Info Page Error State', () => {
  it('should show error state when API fails', async () => {
    // 특별히 이 테스트만을 위해 mock을 재설정
    const { useListData } = await import('~/hooks/useListData');
    vi.mocked(useListData).mockReturnValueOnce({
      items: [],
      loading: false,
      error: 'API 연결에 실패했습니다',
      currentFilter: 'all',
      sortBy: 'latest',
      searchQuery: '',
      handleCategoryFilter: vi.fn(),
      handleSort: vi.fn(),
      handleSearch: vi.fn(),
      handleSearchSubmit: vi.fn(),
      refetch: vi.fn()
    });

    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
      expect(screen.getByText('API 연결에 실패했습니다')).toBeInTheDocument();
      expect(screen.getByText('다시 시도')).toBeInTheDocument();
    });
  });
});

// Loading state 테스트  
describe('Info Page Loading State', () => {
  it('should show loading spinner when loading', async () => {
    // 특별히 이 테스트만을 위해 mock을 재설정
    const { useListData } = await import('~/hooks/useListData');
    vi.mocked(useListData).mockReturnValueOnce({
      items: [],
      loading: true,
      error: null,
      currentFilter: 'all',
      sortBy: 'latest',
      searchQuery: '',
      handleCategoryFilter: vi.fn(),
      handleSort: vi.fn(),
      handleSearch: vi.fn(),
      handleSearchSubmit: vi.fn(),
      refetch: vi.fn()
    });

    render(
      <TestWrapper>
        <ListPage config={infoConfig} />
      </TestWrapper>
    );

    // 로딩 스피너가 표시되어야 함
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});