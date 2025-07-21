import { useState, useEffect, useCallback } from 'react';
import { useFilterAndSort } from './useFilterAndSort';
import { useDebounce } from './useDebounce';
import { apiClient } from '~/lib/api';
import { CacheManager, CACHE_KEYS } from '~/lib/cache';
import type { ListPageConfig, BaseListItem } from '~/types/listTypes';

export interface UseListDataResult<T extends BaseListItem> {
  // 데이터
  items: T[];
  loading: boolean;
  error: string | null;
  
  // 페이지네이션
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  
  // 필터링/정렬 상태
  currentFilter: string;
  sortBy: string;
  searchQuery: string;
  isSearching: boolean;
  hasSearched: boolean;
  
  // 액션
  handleCategoryFilter: (category: string) => void;
  handleSort: (sortBy: string) => void;
  handleSearch: (query: string) => void;
  handleSearchSubmit: (e: React.FormEvent) => void;
  handlePageChange: (page: number) => void;
  refetch: () => void;
}

export function useListData<T extends BaseListItem>(
  config: ListPageConfig<T>,
  initialData?: any,
  isServerRendered?: boolean
): UseListDataResult<T> {
  const [loading, setLoading] = useState(!isServerRendered);
  const [error, setError] = useState<string | null>(null);
  const [rawData, setRawData] = useState<T[]>(
    isServerRendered && initialData?.items 
      ? (config.transformData ? config.transformData(initialData.items) : initialData.items)
      : []
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchResults, setSearchResults] = useState<T[]>([]);
  
  // 페이지네이션 상태
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [pageSize] = useState(20); // 20개씩 보기
  
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  
  // 기존 useFilterAndSort 훅 활용 (검색 기능은 제외)
  const {
    sortedData: filteredAndSortedData,
    currentFilter,
    sortBy,
    handleCategoryFilter,
    handleSort,
  } = useFilterAndSort({
    initialData: hasSearched ? searchResults : rawData,
    filterFn: config.filterFn,
    sortFn: config.sortFn
  });
  
  // 캐시 키 생성 - 모든 페이지가 명확한 캐시 키를 가지도록 수정
  const getCacheKey = useCallback(() => {
    const metadata_type = config.apiFilters?.metadata_type;
    
    // 메타데이터 타입별 캐시 키 (정확한 타입명 사용)
    if (metadata_type === 'property_information') return CACHE_KEYS.INFO_POSTS;
    if (metadata_type === 'moving services') return CACHE_KEYS.SERVICES_POSTS;
    if (metadata_type === 'expert_tips') return CACHE_KEYS.TIPS_POSTS;
    
    // 게시판 페이지 (메타데이터 타입이 board인 경우)
    if (metadata_type === 'board') {
      return CACHE_KEYS.BOARD_POSTS;
    }
    
    // 다른 엔드포인트의 경우 고유한 캐시 키 생성
    const endpointKey = config.apiEndpoint.replace('/api/', '').replace('/', '-');
    const filters = config.apiFilters ? Object.keys(config.apiFilters).sort().join('-') : 'default';
    return `${endpointKey}-${filters}-cache`;
  }, [config.apiEndpoint, config.apiFilters]);

  // API 호출 함수 (캐싱 적용)
  const fetchData = useCallback(async (page: number = 1) => {
    const cacheKey = `${getCacheKey()}-page-${page}`;
    
    // 페이지별 캐시 확인
    const cachedPageData = CacheManager.getFromCache<{items: T[], total: number, page: number, pageSize: number}>(cacheKey);
    if (cachedPageData) {
      setRawData(cachedPageData.items);
      setTotalItems(cachedPageData.total);
      setTotalPages(Math.ceil(cachedPageData.total / pageSize));
      setCurrentPage(cachedPageData.page);
      setLoading(false);
      
      // 백그라운드에서 최신 데이터 업데이트
      updateDataInBackground(cacheKey, page);
      return;
    }

    // 캐시가 없으면 로딩 상태로 API 호출
    await fetchAndCacheData(cacheKey, page);
  }, [config.apiEndpoint, config.apiFilters, getCacheKey, pageSize]);

  const fetchAndCacheData = useCallback(async (cacheKey: string, page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      // 게시판의 경우 getPosts 사용
      if (config.apiEndpoint === '/api/posts') {
        const response = await apiClient.getPosts({
          ...config.apiFilters,
          page: page,
          size: pageSize
        });
        
        if (response.success && response.data) {
          console.log('🔍 API 응답 전체 구조:', response);
          console.log('📊 response.data 구조:', response.data);
          console.log('📋 response.data.items:', response.data.items);
          console.log('📋 items 개수:', response.data.items?.length || 0);
          
          // 첫 번째 아이템의 구조 상세 확인
          if (response.data.items && response.data.items.length > 0) {
            const firstItem = response.data.items[0];
            console.log('🔍 첫 번째 아이템 전체 구조:', firstItem);
            console.log('📊 첫 번째 아이템 통계 필드들:', {
              view_count: firstItem.view_count,
              like_count: firstItem.like_count,
              comment_count: firstItem.comment_count,
              bookmark_count: firstItem.bookmark_count,
              stats: firstItem.stats
            });
          }
          
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items as T[];
          
          console.log('✅ 변환된 items:', items);
          if (items && items.length > 0) {
            console.log('🔍 변환된 첫 번째 아이템:', items[0]);
          }
          
          setRawData(items);
          setTotalItems(response.data.total || 0);
          setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
          setCurrentPage(response.data.page || page);
          
          // 페이지별 캐시 저장 (5분 TTL)
          CacheManager.saveToCache(cacheKey, {
            items,
            total: response.data.total || 0,
            page: response.data.page || page,
            pageSize
          }, 5 * 60 * 1000);
        } else {
          console.error('❌ API 응답 실패:', response);
          throw new Error(response.error || '데이터를 불러올 수 없습니다');
        }
      } else if (config.apiEndpoint === '/api/posts/services') {
        // 서비스 확장 통계 API 사용
        const response = await apiClient.getServicePostsWithExtendedStats(page, pageSize, 'created_at');
        
        if (response.success && response.data) {
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items as T[];
          setRawData(items);
          setTotalItems(response.data.total || 0);
          setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
          setCurrentPage(response.data.page || page);
          
          // 페이지별 캐시 저장 (5분 TTL)
          CacheManager.saveToCache(cacheKey, {
            items,
            total: response.data.total || 0,
            page: response.data.page || page,
            pageSize
          }, 5 * 60 * 1000);
        } else {
          throw new Error(response.error || '데이터를 불러올 수 없습니다');
        }
      } else {
        // 다른 엔드포인트는 일반 request 사용
        const response = await apiClient.request(config.apiEndpoint, {
          method: 'GET',
          params: {
            ...config.apiFilters,
            page: page,
            size: pageSize
          }
        });
        
        if (response.success && response.data) {
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items;
          setRawData(items);
          setTotalItems(response.data.total || 0);
          setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
          setCurrentPage(response.data.page || page);
          
          // 페이지별 캐시 저장 (5분 TTL)
          CacheManager.saveToCache(cacheKey, {
            items,
            total: response.data.total || 0,
            page: response.data.page || page,
            pageSize
          }, 5 * 60 * 1000);
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
  }, [config.apiEndpoint, config.apiFilters, config.transformData, pageSize]);

  const updateDataInBackground = useCallback(async (cacheKey: string, page: number = 1) => {
    try {
      // 백그라운드 업데이트는 로딩 상태를 변경하지 않음
      if (config.apiEndpoint === '/api/posts') {
        const response = await apiClient.getPosts({
          ...config.apiFilters,
          page: page,
          size: pageSize
        });
        
        if (response.success && response.data) {
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items as T[];
          
          // 새로운 데이터가 있으면 부드럽게 업데이트
          setRawData(items);
          setTotalItems(response.data.total || 0);
          setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
          setCurrentPage(response.data.page || page);
          
          CacheManager.saveToCache(cacheKey, {
            items,
            total: response.data.total || 0,
            page: response.data.page || page,
            pageSize
          }, 5 * 60 * 1000);
        }
      } else if (config.apiEndpoint === '/api/posts/services') {
        // 서비스 확장 통계 API 백그라운드 업데이트
        const response = await apiClient.getServicePostsWithExtendedStats(page, pageSize, 'created_at');
        
        if (response.success && response.data) {
          const items = config.transformData 
            ? config.transformData(response.data.items)
            : response.data.items as T[];
          
          // 새로운 데이터가 있으면 부드럽게 업데이트
          setRawData(items);
          setTotalItems(response.data.total || 0);
          setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
          setCurrentPage(response.data.page || page);
          
          CacheManager.saveToCache(cacheKey, {
            items,
            total: response.data.total || 0,
            page: response.data.page || page,
            pageSize
          }, 5 * 60 * 1000);
        }
      }
    } catch (error) {
      console.warn('백그라운드 업데이트 실패:', error);
    }
  }, [config.apiEndpoint, config.apiFilters, config.transformData, pageSize]);

  // 검색 API 호출 함수
  const searchData = useCallback(async (query: string) => {
    if (!query || !query.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }

    try {
      setIsSearching(true);
      setError(null);

      const response = await apiClient.searchPosts({
        query: query.trim(),
        ...config.apiFilters
      });

      if (response.success && response.data) {
        const items = config.transformData 
          ? config.transformData(response.data.items)
          : response.data.items as T[];
        setSearchResults(items);
        setHasSearched(true);
      } else {
        throw new Error(response.error || '검색에 실패했습니다');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '검색 중 오류가 발생했습니다');
      setSearchResults([]);
      setHasSearched(true);
    } finally {
      setIsSearching(false);
    }
  }, [config.apiFilters, config.transformData]);

  // 디바운싱된 검색 실행
  useEffect(() => {
    searchData(debouncedSearchQuery);
  }, [debouncedSearchQuery, searchData]);
  
  // 초기 데이터 로드 (SSR 데이터가 없는 경우에만)
  useEffect(() => {
    if (!isServerRendered) {
      fetchData(1);
    } else {
      // SSR 데이터가 있으면 백그라운드에서 최신 데이터 체크
      const cacheKey = `${getCacheKey()}-page-1`;
      if (initialData?.items) {
        CacheManager.saveToCache(cacheKey, {
          items: initialData.items,
          total: initialData.total || 0,
          page: 1,
          pageSize
        }, 5 * 60 * 1000);
        updateDataInBackground(cacheKey, 1);
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  
  // 검색 핸들러
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const handleSearchSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    // 검색은 이미 디바운싱으로 처리되므로 별도 작업 불필요
  }, []);
  
  // 페이지 변경 핸들러
  const handlePageChange = useCallback((page: number) => {
    if (page < 1 || page > totalPages) return;
    setCurrentPage(page);
    fetchData(page);
  }, [fetchData, totalPages]);
  
  // refetch 함수
  const refetch = useCallback(() => {
    if (hasSearched) {
      searchData(searchQuery);
    } else {
      const cacheKey = `${getCacheKey()}-page-${currentPage}`;
      // refetch 시에는 캐시를 무시하고 새로운 데이터 가져오기
      fetchAndCacheData(cacheKey, currentPage);
    }
  }, [searchData, hasSearched, searchQuery, getCacheKey, fetchAndCacheData, currentPage]);
  
  return {
    // 데이터
    items: filteredAndSortedData,
    loading,
    error,
    
    // 페이지네이션
    currentPage,
    totalPages,
    totalItems,
    pageSize,
    
    // 필터링/정렬 상태
    currentFilter,
    sortBy,
    searchQuery,
    isSearching,
    hasSearched,
    
    // 액션
    handleCategoryFilter,
    handleSort,
    handleSearch,
    handleSearchSubmit,
    handlePageChange,
    refetch
  };
}