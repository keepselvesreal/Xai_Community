import { describe, test, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useListData } from '~/hooks/useListData';
import type { ListPageConfig, BaseListItem } from '~/types/listTypes';
import { apiClient } from '~/lib/api';

// Mock API client
vi.mock('~/lib/api', () => ({
  apiClient: {
    request: vi.fn()
  }
}));

// Mock data
interface TestItem extends BaseListItem {
  category: string;
  content: string;
}

const mockItems: TestItem[] = [
  {
    id: '1',
    title: '첫 번째 아이템',
    created_at: '2024-01-03T00:00:00Z',
    category: 'cat1',
    content: '내용 1',
    stats: {
      view_count: 100,
      like_count: 20
    }
  },
  {
    id: '2',
    title: '두 번째 아이템',
    created_at: '2024-01-02T00:00:00Z',
    category: 'cat2',
    content: '내용 2',
    stats: {
      view_count: 200,
      like_count: 10
    }
  },
  {
    id: '3',
    title: '세 번째 아이템',
    created_at: '2024-01-01T00:00:00Z',
    category: 'cat1',
    content: '내용 3',
    stats: {
      view_count: 50,
      like_count: 30
    }
  }
];

const mockConfig: ListPageConfig<TestItem> = {
  title: '테스트 페이지',
  writeButtonText: '작성하기',
  writeButtonLink: '/test/write',
  searchPlaceholder: '검색...',
  
  apiEndpoint: '/api/test',
  apiFilters: {
    type: 'test'
  },
  
  categories: [
    { value: 'all', label: '전체' },
    { value: 'cat1', label: '카테고리1' },
    { value: 'cat2', label: '카테고리2' }
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    { value: 'likes', label: '좋아요' }
  ],
  
  cardLayout: 'list',
  
  renderCard: (item) => null as any,
  
  filterFn: (item, category, query) => {
    if (category !== 'all' && item.category !== category) {
      return false;
    }
    if (query && !item.title.toLowerCase().includes(query.toLowerCase())) {
      return false;
    }
    return true;
  },
  
  sortFn: (a, b, sortBy) => {
    switch (sortBy) {
      case 'latest':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case 'views':
        return (b.stats?.view_count || 0) - (a.stats?.view_count || 0);
      case 'likes':
        return (b.stats?.like_count || 0) - (a.stats?.like_count || 0);
      default:
        return 0;
    }
  }
};

describe('useListData 훅', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('API 데이터 로딩', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({
      success: true,
      data: {
        items: mockItems,
        total: mockItems.length,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const { result } = renderHook(() => useListData(mockConfig));

    // 초기 로딩 상태
    expect(result.current.loading).toBe(true);
    expect(result.current.items).toEqual([]);
    expect(result.current.error).toBeNull();

    // API 응답 대기
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 데이터 로드 확인
    expect(result.current.items).toHaveLength(3);
    expect(result.current.items[0].title).toBe('첫 번째 아이템');
    
    // API 호출 확인
    expect(apiClient.request).toHaveBeenCalledWith('/api/test', {
      method: 'GET',
      params: {
        type: 'test',
        page: 1,
        size: 50
      }
    });
  });

  test('필터링 동작', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({
      success: true,
      data: {
        items: mockItems,
        total: mockItems.length,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const { result } = renderHook(() => useListData(mockConfig));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 초기 상태: 전체 표시
    expect(result.current.items).toHaveLength(3);
    expect(result.current.currentFilter).toBe('all');

    // 카테고리1 필터 적용
    act(() => {
      result.current.handleCategoryFilter('cat1');
    });

    expect(result.current.currentFilter).toBe('cat1');
    expect(result.current.items).toHaveLength(2);
    expect(result.current.items[0].category).toBe('cat1');
    expect(result.current.items[1].category).toBe('cat1');

    // 카테고리2 필터 적용
    act(() => {
      result.current.handleCategoryFilter('cat2');
    });

    expect(result.current.currentFilter).toBe('cat2');
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].category).toBe('cat2');

    // 전체로 복귀
    act(() => {
      result.current.handleCategoryFilter('all');
    });

    expect(result.current.items).toHaveLength(3);
  });

  test('정렬 동작', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({
      success: true,
      data: {
        items: mockItems,
        total: mockItems.length,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const { result } = renderHook(() => useListData(mockConfig));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 초기 정렬: 최신순
    expect(result.current.sortBy).toBe('latest');
    expect(result.current.items[0].id).toBe('1'); // 가장 최신

    // 조회수순 정렬
    act(() => {
      result.current.handleSort('views');
    });

    expect(result.current.sortBy).toBe('views');
    expect(result.current.items[0].id).toBe('2'); // 조회수 200
    expect(result.current.items[1].id).toBe('1'); // 조회수 100
    expect(result.current.items[2].id).toBe('3'); // 조회수 50

    // 좋아요순 정렬
    act(() => {
      result.current.handleSort('likes');
    });

    expect(result.current.sortBy).toBe('likes');
    expect(result.current.items[0].id).toBe('3'); // 좋아요 30
    expect(result.current.items[1].id).toBe('1'); // 좋아요 20
    expect(result.current.items[2].id).toBe('2'); // 좋아요 10
  });

  test('검색 기능', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({
      success: true,
      data: {
        items: mockItems,
        total: mockItems.length,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const { result } = renderHook(() => useListData(mockConfig));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 검색어 입력
    act(() => {
      result.current.handleSearch('두 번째');
    });

    // 검색 결과 확인
    expect(result.current.searchQuery).toBe('두 번째');
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].title).toBe('두 번째 아이템');

    // 검색어 비우기
    act(() => {
      result.current.handleSearch('');
    });

    expect(result.current.items).toHaveLength(3);
  });

  test('에러 처리', async () => {
    const errorMessage = '네트워크 오류';
    vi.mocked(apiClient.request).mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useListData(mockConfig));

    // 로딩 상태
    expect(result.current.loading).toBe(true);

    // 에러 발생 대기
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.items).toEqual([]);
  });

  test('리페치 기능', async () => {
    vi.mocked(apiClient.request)
      .mockResolvedValueOnce({
        success: true,
        data: {
          items: mockItems.slice(0, 2),
          total: 2,
          page: 1,
          size: 50,
          pages: 1
        },
        timestamp: new Date().toISOString()
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          items: mockItems,
          total: mockItems.length,
          page: 1,
          size: 50,
          pages: 1
        },
        timestamp: new Date().toISOString()
      });

    const { result } = renderHook(() => useListData(mockConfig));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 초기 데이터
    expect(result.current.items).toHaveLength(2);

    // 리페치
    act(() => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.items).toHaveLength(3);
    });

    expect(apiClient.request).toHaveBeenCalledTimes(2);
  });

  test('필터와 검색 조합', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({
      success: true,
      data: {
        items: mockItems,
        total: mockItems.length,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const { result } = renderHook(() => useListData(mockConfig));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 카테고리 필터 적용
    act(() => {
      result.current.handleCategoryFilter('cat1');
    });

    expect(result.current.items).toHaveLength(2);

    // 검색어 추가
    act(() => {
      result.current.handleSearch('세 번째');
    });

    // cat1 카테고리 중에서 '세 번째'를 포함하는 아이템만
    expect(result.current.items).toHaveLength(1);
    expect(result.current.items[0].title).toBe('세 번째 아이템');
  });

  test('검색 제출 핸들러', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({
      success: true,
      data: {
        items: mockItems,
        total: mockItems.length,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const { result } = renderHook(() => useListData(mockConfig));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const mockEvent = {
      preventDefault: vi.fn()
    } as any;

    act(() => {
      result.current.handleSearchSubmit(mockEvent);
    });

    expect(mockEvent.preventDefault).toHaveBeenCalled();
  });
});