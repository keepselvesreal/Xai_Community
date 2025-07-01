import { useState, useEffect, useCallback, useMemo } from 'react';
import { useFilterAndSort } from './useFilterAndSort';
import { apiClient } from '~/lib/api';
import type { ListPageConfig, BaseListItem } from '~/types/listTypes';

export interface UseListDataResult<T extends BaseListItem> {
  // 데이터
  items: T[];
  loading: boolean;
  error: string | null;
  
  // 필터링/정렬 상태
  currentFilter: string;
  sortBy: string;
  searchQuery: string;
  
  // 액션
  handleCategoryFilter: (category: string) => void;
  handleSort: (sortBy: string) => void;
  handleSearch: (query: string) => void;
  handleSearchSubmit: (e: React.FormEvent) => void;
  refetch: () => void;
}

export function useListData<T extends BaseListItem>(
  config: ListPageConfig<T>
): UseListDataResult<T> {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rawData, setRawData] = useState<T[]>([]);
  
  // 기존 useFilterAndSort 훅 활용
  const {
    sortedData,
    currentFilter,
    sortBy,
    searchQuery,
    handleCategoryFilter,
    handleSort,
    handleSearch,
    handleSearchSubmit,
  } = useFilterAndSort({
    initialData: rawData,
    filterFn: config.filterFn,
    sortFn: config.sortFn
  });
  
  // API 호출 함수
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 게시판의 경우 getPosts 사용
      if (config.apiEndpoint === '/api/posts') {
        const response = await apiClient.getPosts({
          ...config.apiFilters,
          page: 1,
          size: 50
        });
        
        if (response.success && response.data) {
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items as T[];
          setRawData(items);
        } else {
          throw new Error(response.error || '데이터를 불러올 수 없습니다');
        }
      } else {
        // 다른 엔드포인트는 일반 request 사용
        const response = await apiClient.request(config.apiEndpoint, {
          method: 'GET',
          params: {
            ...config.apiFilters,
            page: 1,
            size: 50
          }
        });
        
        if (response.success && response.data) {
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items;
          setRawData(items);
        } else {
          throw new Error(response.error || '데이터를 불러올 수 없습니다');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다');
      setRawData([]);
    } finally {
      setLoading(false);
    }
  }, [config.apiEndpoint, config.apiFilters]);
  
  // 초기 데이터 로드
  useEffect(() => {
    fetchData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  
  // refetch 함수
  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);
  
  return {
    // 데이터
    items: sortedData,
    loading,
    error,
    
    // 필터링/정렬 상태
    currentFilter,
    sortBy,
    searchQuery,
    
    // 액션
    handleCategoryFilter,
    handleSort,
    handleSearch,
    handleSearchSubmit,
    refetch
  };
}