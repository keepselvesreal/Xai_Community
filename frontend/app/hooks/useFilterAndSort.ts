import { useState, useCallback, useMemo } from "react";

export interface UseFilterAndSortOptions<T> {
  initialData: T[];
  filterFn: (item: T, category: string, query: string) => boolean;
  sortFn: (a: T, b: T, sortBy: string) => number;
}

export function useFilterAndSort<T>({
  initialData,
  filterFn,
  sortFn
}: UseFilterAndSortOptions<T>) {
  const [currentFilter, setCurrentFilter] = useState("all");
  const [sortBy, setSortBy] = useState("latest");
  const [searchQuery, setSearchQuery] = useState("");

  // 필터링된 데이터
  const filteredData = useMemo(() => {
    let filtered = [...initialData];
    
    // 카테고리 필터링
    if (currentFilter !== "all") {
      filtered = filtered.filter(item => filterFn(item, currentFilter, ""));
    }
    
    // 검색 필터링
    if (searchQuery.trim()) {
      filtered = filtered.filter(item => filterFn(item, "", searchQuery));
    }
    
    return filtered;
  }, [initialData, currentFilter, searchQuery, filterFn]);

  // 정렬된 데이터
  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => sortFn(a, b, sortBy));
  }, [filteredData, sortBy, sortFn]);

  // 필터 변경 핸들러
  const handleCategoryFilter = useCallback((category: string) => {
    setCurrentFilter(category);
  }, []);

  // 정렬 변경 핸들러
  const handleSort = useCallback((sort: string) => {
    setSortBy(sort);
  }, []);

  // 검색 핸들러
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // 검색 폼 제출 핸들러
  const handleSearchSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    // 검색은 이미 useMemo에서 처리되므로 별도 작업 불필요
  }, []);

  // 리셋 핸들러
  const reset = useCallback(() => {
    setCurrentFilter("all");
    setSortBy("latest");
    setSearchQuery("");
  }, []);

  return {
    // 데이터
    filteredData,
    sortedData,
    
    // 현재 상태
    currentFilter,
    sortBy,
    searchQuery,
    
    // 핸들러
    handleCategoryFilter,
    handleSort,
    handleSearch,
    handleSearchSubmit,
    reset,
    
    // 상태 설정 함수
    setCurrentFilter,
    setSortBy,
    setSearchQuery
  };
}