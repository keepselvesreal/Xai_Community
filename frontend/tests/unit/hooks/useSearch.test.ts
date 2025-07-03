import { describe, test, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSearch } from '~/hooks/useSearch';
import { apiClient } from '~/lib/api';

// Mock API client
vi.mock('~/lib/api', () => ({
  apiClient: {
    searchPosts: vi.fn()
  }
}));

// Mock timers for debouncing tests
vi.useFakeTimers();

describe('useSearch 훅', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  test('초기 상태 확인', () => {
    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    expect(result.current.query).toBe('');
    expect(result.current.results).toEqual([]);
    expect(result.current.isSearching).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.hasSearched).toBe(false);
  });

  test('검색어 설정', () => {
    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    act(() => {
      result.current.setQuery('테스트 검색어');
    });

    expect(result.current.query).toBe('테스트 검색어');
  });

  test('디바운싱 동작 확인', async () => {
    const mockSearchResponse = {
      success: true,
      data: {
        items: [
          { id: '1', title: '검색 결과 1', created_at: '2024-01-01T00:00:00Z' },
          { id: '2', title: '검색 결과 2', created_at: '2024-01-02T00:00:00Z' }
        ],
        total: 2,
        page: 1,
        size: 20,
        pages: 1
      },
      timestamp: new Date().toISOString()
    };

    vi.mocked(apiClient.searchPosts).mockResolvedValue(mockSearchResponse);

    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    // 빠르게 연속으로 검색어 입력
    act(() => {
      result.current.setQuery('테');
    });

    act(() => {
      result.current.setQuery('테스');
    });

    act(() => {
      result.current.setQuery('테스트');
    });

    // 아직 API 호출되지 않음 (디바운싱 중)
    expect(apiClient.searchPosts).not.toHaveBeenCalled();
    expect(result.current.isSearching).toBe(false);

    // 300ms 후 실행
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // 이제 검색 시작
    expect(result.current.isSearching).toBe(true);

    // API 응답 대기
    await waitFor(() => {
      expect(result.current.isSearching).toBe(false);
    });

    // API가 한 번만 호출되었는지 확인 (디바운싱 효과)
    expect(apiClient.searchPosts).toHaveBeenCalledTimes(1);
    expect(apiClient.searchPosts).toHaveBeenCalledWith({
      query: '테스트',
      service: 'test'
    });

    expect(result.current.results).toHaveLength(2);
    expect(result.current.hasSearched).toBe(true);
    expect(result.current.error).toBeNull();
  });

  test('빈 검색어 처리', () => {
    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    act(() => {
      result.current.setQuery('검색어');
    });

    // 300ms 후
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // 검색어를 빈 문자열로 변경
    act(() => {
      result.current.setQuery('');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    // 빈 검색어에 대해서는 API 호출하지 않음
    expect(apiClient.searchPosts).not.toHaveBeenCalled();
    expect(result.current.results).toEqual([]);
    expect(result.current.hasSearched).toBe(false);
  });

  test('공백만 있는 검색어 처리', () => {
    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    act(() => {
      result.current.setQuery('   ');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    // 공백만 있는 검색어에 대해서는 API 호출하지 않음
    expect(apiClient.searchPosts).not.toHaveBeenCalled();
    expect(result.current.results).toEqual([]);
  });

  test('API 에러 처리', async () => {
    const errorMessage = '검색 서버 오류';
    vi.mocked(apiClient.searchPosts).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    act(() => {
      result.current.setQuery('에러 테스트');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(result.current.isSearching).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.results).toEqual([]);
    expect(result.current.hasSearched).toBe(true);
  });

  test('검색 초기화', async () => {
    const mockSearchResponse = {
      success: true,
      data: {
        items: [{ id: '1', title: '검색 결과', created_at: '2024-01-01T00:00:00Z' }],
        total: 1,
        page: 1,
        size: 20,
        pages: 1
      },
      timestamp: new Date().toISOString()
    };

    vi.mocked(apiClient.searchPosts).mockResolvedValue(mockSearchResponse);

    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    // 검색 실행
    act(() => {
      result.current.setQuery('검색어');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(result.current.results).toHaveLength(1);
    });

    // 검색 초기화
    act(() => {
      result.current.clearSearch();
    });

    expect(result.current.query).toBe('');
    expect(result.current.results).toEqual([]);
    expect(result.current.hasSearched).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test('수동 검색 실행', async () => {
    const mockSearchResponse = {
      success: true,
      data: {
        items: [{ id: '1', title: '수동 검색 결과', created_at: '2024-01-01T00:00:00Z' }],
        total: 1,
        page: 1,
        size: 20,
        pages: 1
      },
      timestamp: new Date().toISOString()
    };

    vi.mocked(apiClient.searchPosts).mockResolvedValue(mockSearchResponse);

    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    act(() => {
      result.current.setQuery('수동 검색');
    });

    // 디바운싱 기다리지 않고 즉시 검색
    await act(async () => {
      await result.current.executeSearch();
    });

    expect(apiClient.searchPosts).toHaveBeenCalledWith({
      query: '수동 검색',
      service: 'test'
    });

    expect(result.current.results).toHaveLength(1);
    expect(result.current.hasSearched).toBe(true);
  });

  test('여러 API 필터 조합', async () => {
    const mockSearchResponse = {
      success: true,
      data: {
        items: [],
        total: 0,
        page: 1,
        size: 20,
        pages: 0
      },
      timestamp: new Date().toISOString()
    };

    vi.mocked(apiClient.searchPosts).mockResolvedValue(mockSearchResponse);

    const { result } = renderHook(() => useSearch({
      apiFilters: { 
        service: 'residential_community',
        metadata_type: 'expert_tips',
        sortBy: 'latest'
      },
      debounceMs: 300
    }));

    act(() => {
      result.current.setQuery('복합 필터 검색');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(result.current.isSearching).toBe(false);
    });

    expect(apiClient.searchPosts).toHaveBeenCalledWith({
      query: '복합 필터 검색',
      service: 'residential_community',
      metadata_type: 'expert_tips',
      sortBy: 'latest'
    });
  });

  test('검색 중 다른 검색어 입력 시 이전 요청 취소', async () => {
    const mockResponse1 = {
      success: true,
      data: { items: [{ id: '1', title: '첫 번째 검색', created_at: '2024-01-01T00:00:00Z' }], total: 1, page: 1, size: 20, pages: 1 },
      timestamp: new Date().toISOString()
    };

    const mockResponse2 = {
      success: true,
      data: { items: [{ id: '2', title: '두 번째 검색', created_at: '2024-01-02T00:00:00Z' }], total: 1, page: 1, size: 20, pages: 1 },
      timestamp: new Date().toISOString()
    };

    vi.mocked(apiClient.searchPosts)
      .mockResolvedValueOnce(mockResponse1)
      .mockResolvedValueOnce(mockResponse2);

    const { result } = renderHook(() => useSearch({
      apiFilters: { service: 'test' },
      debounceMs: 300
    }));

    // 첫 번째 검색
    act(() => {
      result.current.setQuery('첫 번째');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    // 검색 중에 두 번째 검색어 입력
    act(() => {
      result.current.setQuery('두 번째');
    });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(result.current.isSearching).toBe(false);
    });

    // 두 번째 검색 결과만 표시되어야 함
    expect(result.current.results[0].title).toBe('두 번째 검색');
  });
});