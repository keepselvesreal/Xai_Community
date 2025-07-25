/**
 * 작업 시간: 2025-07-25
 * 작업 버전: v1.0.0
 * 주요 컴포넌트: useInfiniteScroll 훅
 * 주요 기능: Intersection Observer API를 활용한 자동 무한 스크롤 구현
 * 코드 라인: 1-120
 * 관련 파일: 
 * - useListData.ts (데이터 로딩 로직과 연동)
 * - GridPageLayout.tsx (UI 컴포넌트에서 사용)
 */

import { useEffect, useRef, useCallback } from 'react';

interface UseInfiniteScrollOptions {
  /** 더 불러올 데이터가 있는지 여부 */
  hasMore: boolean;
  /** 현재 로딩 중인지 여부 */
  loading: boolean;
  /** 다음 페이지를 로드하는 함수 */
  onLoadMore: () => void;
  /** 감지 영역과 뷰포트 하단의 거리 (기본값: 100px) */
  threshold?: number;
  /** 디바운싱 딜레이 (기본값: 300ms) */
  debounceDelay?: number;
  /** 무한 스크롤 활성화 여부 (기본값: true) */
  enabled?: boolean;
}

interface UseInfiniteScrollResult {
  /** 감지 영역에 연결할 ref */
  sentinelRef: React.RefObject<HTMLDivElement>;
  /** 수동으로 트리거할 때 사용하는 함수 */
  triggerLoadMore: () => void;
}

/**
 * 무한 스크롤 기능을 제공하는 커스텀 훅
 * 
 * @example
 * ```tsx
 * const { sentinelRef } = useInfiniteScroll({
 *   hasMore: hasMoreData,
 *   loading: isLoading,
 *   onLoadMore: loadNextPage,
 *   threshold: 100
 * });
 * 
 * return (
 *   <div>
 *     {items.map(item => <Item key={item.id} data={item} />)}
 *     <div ref={sentinelRef} className="h-1" />
 *   </div>
 * );
 * ```
 */
export function useInfiniteScroll({
  hasMore,
  loading,
  onLoadMore,
  threshold = 100,
  debounceDelay = 300,
  enabled = true
}: UseInfiniteScrollOptions): UseInfiniteScrollResult {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false);
  const debounceTimeoutRef = useRef<NodeJS.Timeout>();
  
  // 디바운싱된 로드 함수
  const debouncedLoadMore = useCallback(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    
    debounceTimeoutRef.current = setTimeout(() => {
      if (!loadingRef.current && hasMore && enabled) {
        loadingRef.current = true;
        onLoadMore();
      }
    }, debounceDelay);
  }, [hasMore, enabled, onLoadMore, debounceDelay]);
  
  // 수동 트리거 함수
  const triggerLoadMore = useCallback(() => {
    if (!loading && hasMore && enabled) {
      onLoadMore();
    }
  }, [loading, hasMore, enabled, onLoadMore]);
  
  // 로딩 상태가 변경되면 내부 로딩 플래그 업데이트
  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);
  
  // Intersection Observer 설정
  useEffect(() => {
    if (!enabled || !sentinelRef.current) {
      return;
    }
    
    const sentinelElement = sentinelRef.current;
    
    // Intersection Observer 생성
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        
        // 감지 영역이 뷰포트에 들어왔고, 더 불러올 데이터가 있으며, 로딩 중이 아닐 때
        if (entry.isIntersecting && hasMore && !loading) {
          console.log('🔄 무한 스크롤 트리거됨');
          debouncedLoadMore();
        }
      },
      {
        // 뷰포트 기준으로 threshold만큼 미리 감지
        rootMargin: `0px 0px ${threshold}px 0px`,
        threshold: 0.1
      }
    );
    
    // 감지 영역 관찰 시작
    observer.observe(sentinelElement);
    
    // 정리 함수
    return () => {
      observer.unobserve(sentinelElement);
      observer.disconnect();
      
      // 디바운스 타이머 정리
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [enabled, hasMore, loading, threshold, debouncedLoadMore]);
  
  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);
  
  return {
    sentinelRef,
    triggerLoadMore
  };
}

export default useInfiniteScroll;