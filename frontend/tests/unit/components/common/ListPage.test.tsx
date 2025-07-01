import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ListPage } from '~/components/common/ListPage';
import type { ListPageConfig, BaseListItem } from '~/types/listTypes';
import type { User } from '~/types';

// Mock 훅
vi.mock('~/hooks/useListData', () => ({
  useListData: vi.fn()
}));

// Mock 컴포넌트
vi.mock('~/components/layout/AppLayout', () => ({
  default: ({ children }: any) => <div data-testid="app-layout">{children}</div>
}));

vi.mock('~/components/common/LoadingSpinner', () => ({
  default: () => <div data-testid="loading-spinner">Loading...</div>
}));

// 테스트용 아이템 타입
interface TestItem extends BaseListItem {
  category: string;
}

// 테스트 데이터
const mockItems: TestItem[] = [
  {
    id: '1',
    title: '아이템 1',
    created_at: '2024-01-01T00:00:00Z',
    category: 'cat1',
    stats: {
      view_count: 100,
      like_count: 20
    }
  },
  {
    id: '2',
    title: '아이템 2',
    created_at: '2024-01-02T00:00:00Z',
    category: 'cat2',
    stats: {
      view_count: 50,
      like_count: 10
    }
  }
];

// 테스트 설정
const mockConfig: ListPageConfig<TestItem> = {
  title: '테스트 페이지',
  writeButtonText: '작성하기',
  writeButtonLink: '/test/write',
  searchPlaceholder: '검색...',
  
  apiEndpoint: '/api/test',
  apiFilters: { type: 'test' },
  
  categories: [
    { value: 'all', label: '전체' },
    { value: 'cat1', label: '카테고리1' },
    { value: 'cat2', label: '카테고리2' }
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' }
  ],
  
  cardLayout: 'list',
  
  renderCard: (item) => <div data-testid={`item-${item.id}`}>{item.title}</div>,
  filterFn: vi.fn(),
  sortFn: vi.fn()
};

describe('ListPage 컴포넌트', () => {
  const mockUser: User = {
    id: 'user1',
    email: 'test@example.com',
    user_handle: 'testuser',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  };

  test('설정 기반 렌더링', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    useListData.mockReturnValue({
      items: mockItems,
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
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // AppLayout이 렌더링되는지 확인
    expect(screen.getByTestId('app-layout')).toBeInTheDocument();

    // 검색 입력창 확인
    expect(screen.getByPlaceholderText('검색...')).toBeInTheDocument();

    // 글쓰기 버튼 확인
    expect(screen.getByText('작성하기')).toBeInTheDocument();

    // 카테고리 필터 버튼들 확인
    expect(screen.getByRole('button', { name: '전체' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '카테고리1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '카테고리2' })).toBeInTheDocument();

    // 정렬 옵션 확인
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  test('아이템 목록 표시', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    useListData.mockReturnValue({
      items: mockItems,
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
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // 아이템들이 렌더링되는지 확인
    expect(screen.getByTestId('item-1')).toBeInTheDocument();
    expect(screen.getByTestId('item-2')).toBeInTheDocument();
    expect(screen.getByText('아이템 1')).toBeInTheDocument();
    expect(screen.getByText('아이템 2')).toBeInTheDocument();
  });

  test('로딩 상태', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    useListData.mockReturnValue({
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
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // 로딩 스피너가 표시되는지 확인
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('에러 상태', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    const mockRefetch = vi.fn();
    
    useListData.mockReturnValue({
      items: [],
      loading: false,
      error: '네트워크 오류가 발생했습니다',
      currentFilter: 'all',
      sortBy: 'latest',
      searchQuery: '',
      handleCategoryFilter: vi.fn(),
      handleSort: vi.fn(),
      handleSearch: vi.fn(),
      handleSearchSubmit: vi.fn(),
      refetch: mockRefetch
    });

    render(
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // 에러 메시지가 표시되는지 확인
    expect(screen.getByText(/오류가 발생했습니다/)).toBeInTheDocument();
    expect(screen.getByText(/네트워크 오류가 발생했습니다/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '다시 시도' })).toBeInTheDocument();
  });

  test('빈 목록 상태', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    useListData.mockReturnValue({
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
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // 빈 상태 메시지가 표시되는지 확인
    expect(screen.getByText(/아이템이 없습니다/)).toBeInTheDocument();
  });

  test('필터 선택시 활성 상태 표시', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    useListData.mockReturnValue({
      items: mockItems,
      loading: false,
      error: null,
      currentFilter: 'cat1', // cat1이 선택된 상태
      sortBy: 'latest',
      searchQuery: '',
      handleCategoryFilter: vi.fn(),
      handleSort: vi.fn(),
      handleSearch: vi.fn(),
      handleSearchSubmit: vi.fn(),
      refetch: vi.fn()
    });

    render(
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // cat1 버튼이 활성 상태인지 확인 (클래스명으로 체크)
    const cat1Button = screen.getByRole('button', { name: '카테고리1' });
    expect(cat1Button.className).toContain('bg-accent-primary');
  });

  test('검색 중 표시', () => {
    const { useListData } = vi.mocked(await import('~/hooks/useListData'));
    useListData.mockReturnValue({
      items: [],
      loading: false,
      error: null,
      currentFilter: 'all',
      sortBy: 'latest',
      searchQuery: '검색중',
      handleCategoryFilter: vi.fn(),
      handleSort: vi.fn(),
      handleSearch: vi.fn(),
      handleSearchSubmit: vi.fn(),
      refetch: vi.fn()
    });

    render(
      <BrowserRouter>
        <ListPage config={mockConfig} user={mockUser} />
      </BrowserRouter>
    );

    // 검색어가 입력창에 표시되는지 확인
    const searchInput = screen.getByPlaceholderText('검색...') as HTMLInputElement;
    expect(searchInput.value).toBe('검색중');
  });
});