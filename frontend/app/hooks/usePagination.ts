import { useState, useCallback, useMemo } from "react";

interface UsePaginationOptions {
  initialPage?: number;
  initialSize?: number;
  totalItems?: number;
}

export function usePagination({
  initialPage = 1,
  initialSize = 10,
  totalItems = 0,
}: UsePaginationOptions = {}) {
  const [page, setPage] = useState(initialPage);
  const [size, setSize] = useState(initialSize);

  const totalPages = useMemo(() => {
    return Math.ceil(totalItems / size);
  }, [totalItems, size]);

  const hasNext = useMemo(() => {
    return page < totalPages;
  }, [page, totalPages]);

  const hasPrevious = useMemo(() => {
    return page > 1;
  }, [page]);

  const startIndex = useMemo(() => {
    return (page - 1) * size;
  }, [page, size]);

  const endIndex = useMemo(() => {
    return Math.min(startIndex + size, totalItems);
  }, [startIndex, size, totalItems]);

  const goToPage = useCallback((targetPage: number) => {
    const clampedPage = Math.max(1, Math.min(targetPage, totalPages));
    setPage(clampedPage);
  }, [totalPages]);

  const goToNext = useCallback(() => {
    if (hasNext) {
      setPage(prev => prev + 1);
    }
  }, [hasNext]);

  const goToPrevious = useCallback(() => {
    if (hasPrevious) {
      setPage(prev => prev - 1);
    }
  }, [hasPrevious]);

  const goToFirst = useCallback(() => {
    setPage(1);
  }, []);

  const goToLast = useCallback(() => {
    setPage(totalPages);
  }, [totalPages]);

  const changeSize = useCallback((newSize: number) => {
    setSize(newSize);
    // 페이지 크기 변경 시 첫 페이지로 이동
    setPage(1);
  }, []);

  const reset = useCallback(() => {
    setPage(initialPage);
    setSize(initialSize);
  }, [initialPage, initialSize]);

  // 페이지 번호 배열 생성 (페이지네이션 UI용)
  const getPageNumbers = useCallback((maxVisible: number = 5) => {
    const pages: number[] = [];
    const half = Math.floor(maxVisible / 2);
    
    let start = Math.max(1, page - half);
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    // 끝에서 시작점 조정
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  }, [page, totalPages]);

  return {
    // 상태
    page,
    size,
    totalPages,
    totalItems,
    hasNext,
    hasPrevious,
    startIndex,
    endIndex,
    
    // 액션
    goToPage,
    goToNext,
    goToPrevious,
    goToFirst,
    goToLast,
    changeSize,
    reset,
    getPageNumbers,
    
    // 계산된 값들
    isEmpty: totalItems === 0,
    isFirstPage: page === 1,
    isLastPage: page === totalPages,
  };
}

export default usePagination;