import { useState, useEffect, useCallback } from 'react';
import { useDebounce } from './useDebounce';
import { apiClient } from '~/lib/api';
import type { Post, PostFilters } from '~/types';

export interface UseSearchOptions {
  apiFilters?: Partial<PostFilters>;
  debounceMs?: number;
}

export interface UseSearchResult {
  // 상태
  query: string;
  results: Post[];
  isSearching: boolean;
  error: string | null;
  hasSearched: boolean;
  
  // 액션
  setQuery: (query: string) => void;
  clearSearch: () => void;
  executeSearch: () => Promise<void>;
}

export function useSearch(options: UseSearchOptions = {}): UseSearchResult {
  const { apiFilters = {}, debounceMs = 300 } = options;
  
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Post[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  
  const debouncedQuery = useDebounce(query, debounceMs);
  
  // 검색 실행 함수
  const executeSearch = useCallback(async (searchQuery?: string) => {
    const queryToSearch = searchQuery !== undefined ? searchQuery : query;
    
    // 빈 검색어나 공백만 있는 경우 검색하지 않음
    if (!queryToSearch || !queryToSearch.trim()) {
      setResults([]);
      setHasSearched(false);
      setError(null);
      return;
    }
    
    try {
      setIsSearching(true);
      setError(null);
      
      const searchParams = {
        query: queryToSearch.trim(),
        ...apiFilters
      };
      
      const response = await apiClient.searchPosts(searchParams);
      
      if (response.success && response.data) {
        setResults(response.data.items);
        setHasSearched(true);
      } else {
        throw new Error(response.error || '검색에 실패했습니다');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다';
      setError(errorMessage);
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsSearching(false);
    }
  }, [query, apiFilters]);
  
  // 디바운싱된 검색어로 자동 검색
  useEffect(() => {
    if (!debouncedQuery || !debouncedQuery.trim()) {
      setResults([]);
      setHasSearched(false);
      setError(null);
      return;
    }
    
    const searchParams = {
      query: debouncedQuery.trim(),
      ...apiFilters
    };
    
    setIsSearching(true);
    setError(null);
    
    apiClient.searchPosts(searchParams)
      .then(response => {
        if (response.success && response.data) {
          setResults(response.data.items);
          setHasSearched(true);
        } else {
          throw new Error(response.error || '검색에 실패했습니다');
        }
      })
      .catch(err => {
        const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다';
        setError(errorMessage);
        setResults([]);
        setHasSearched(true);
      })
      .finally(() => {
        setIsSearching(false);
      });
  }, [debouncedQuery, apiFilters]);
  
  // 검색 초기화 함수
  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setHasSearched(false);
    setError(null);
    setIsSearching(false);
  }, []);
  
  return {
    // 상태
    query,
    results,
    isSearching,
    error,
    hasSearched,
    
    // 액션
    setQuery,
    clearSearch,
    executeSearch: () => executeSearch()
  };
}