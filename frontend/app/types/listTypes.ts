// 통합 목록 페이지를 위한 타입 정의

import type { User, Tip } from './index';

/**
 * 모든 목록 아이템의 기본 인터페이스
 * Post, MockService, Tip 등 모든 목록 아이템이 이 인터페이스를 구현해야 함
 */
export interface BaseListItem {
  id: string;
  title: string;
  created_at: string;
  stats?: ItemStats;
}

/**
 * 아이템 통계 정보
 * 모든 목록 아이템에서 공통으로 사용하는 통계 필드
 */
export interface ItemStats {
  view_count?: number;    // 조회수
  like_count?: number;    // 좋아요
  dislike_count?: number; // 싫어요
  comment_count?: number; // 댓글수
  bookmark_count?: number; // 북마크수
}

/**
 * 카테고리 옵션
 */
export interface CategoryOption {
  value: string;
  label: string;
}

/**
 * 정렬 옵션
 */
export interface SortOption {
  value: string;
  label: string;
}

/**
 * 빈 상태 설정
 */
export interface EmptyStateConfig {
  icon: string;
  title: string;
  description: string;
  actionLabel: string;
}

/**
 * 목록 페이지 설정
 * 각 페이지별로 이 설정을 정의하여 통합 컴포넌트에서 사용
 */
export interface ListPageConfig<T extends BaseListItem> {
  // 페이지 기본 설정
  title: string;
  writeButtonText: string;
  writeButtonLink: string;
  searchPlaceholder: string;
  
  // API 설정
  apiEndpoint: string;
  apiFilters: Record<string, any>;
  
  // UI 설정
  categories: CategoryOption[];
  sortOptions: SortOption[];
  cardLayout: 'list' | 'grid' | 'card';
  emptyState?: EmptyStateConfig;
  
  // 데이터 변환 함수 (API 응답을 T 타입으로 변환)
  transformData?: (rawData: any[]) => T[];
  
  // 렌더링 함수
  renderCard: (item: T) => JSX.Element;
  filterFn: (item: T, category: string, query: string) => boolean;
  sortFn: (a: T, b: T, sortBy: string) => number;
}

/**
 * 목록 페이지 props
 */
export interface ListPageProps<T extends BaseListItem> {
  config: ListPageConfig<T>;
  user?: User;
  onLogout?: () => void;
}

/**
 * 검색 및 필터 컴포넌트 props
 */
export interface SearchAndFiltersProps {
  writeButtonText: string;
  writeButtonLink: string;
  searchPlaceholder: string;
  searchQuery: string;
  onSearch: (query: string) => void;
  isSearching?: boolean;
}

/**
 * 필터 및 정렬 컴포넌트 props
 */
export interface FilterAndSortProps {
  categories: CategoryOption[];
  sortOptions: SortOption[];
  currentFilter: string;
  sortBy: string;
  onCategoryFilter: (category: string) => void;
  onSort: (sortBy: string) => void;
  isFiltering?: boolean;
}

/**
 * 아이템 목록 컴포넌트 props
 */
export interface ItemListProps<T extends BaseListItem> {
  items: T[];
  layout: 'list' | 'grid' | 'card';
  renderCard: (item: T) => JSX.Element;
  onItemClick?: (item: T) => void;
}

/**
 * 타입 변환 유틸리티
 */

// Post를 BaseListItem으로 변환
export function postToBaseListItem(post: any): BaseListItem {
  return {
    id: post.id,
    title: post.title,
    created_at: post.created_at,
    stats: post.stats
  };
}

// MockService를 BaseListItem으로 변환
export function serviceToBaseListItem(service: any): BaseListItem {
  // postId가 있으면 우선 사용, 없으면 id 사용
  const itemId = service.postId || service.id.toString();
  
  return {
    id: itemId,
    title: service.name,
    created_at: service.created_at || new Date().toISOString(),
    stats: {
      view_count: service.stats?.views || 0,
      like_count: Math.floor((service.stats?.views || 0) * 0.15),
      dislike_count: Math.floor((service.stats?.views || 0) * 0.03),
      comment_count: service.stats?.reviews || 0,
      bookmark_count: Math.floor((service.stats?.views || 0) * 0.12)
    }
  };
}

// Tip을 BaseListItem으로 변환
export function tipToBaseListItem(tip: Tip): BaseListItem {
  return {
    id: tip.id.toString(),
    title: tip.title,
    created_at: tip.created_at || new Date().toISOString(),
    stats: {
      view_count: tip.views_count || 0,
      like_count: tip.likes_count || 0,
      dislike_count: Math.floor((tip.likes_count || 0) * 0.2),
      comment_count: Math.floor((tip.views_count || 0) * 0.1),
      bookmark_count: tip.saves_count || 0
    }
  };
}

/**
 * 날짜 변환 유틸리티
 * "2일 전" 같은 상대 시간을 ISO 날짜로 변환
 */
export function parseRelativeDate(relativeDate: string): string {
  const now = new Date();
  
  if (relativeDate.includes('방금')) {
    return now.toISOString();
  }
  
  const match = relativeDate.match(/(\d+)\s*(분|시간|일|주)/);
  if (!match) {
    return now.toISOString();
  }
  
  const [, amount, unit] = match;
  const value = parseInt(amount);
  
  switch (unit) {
    case '분':
      now.setMinutes(now.getMinutes() - value);
      break;
    case '시간':
      now.setHours(now.getHours() - value);
      break;
    case '일':
      now.setDate(now.getDate() - value);
      break;
    case '주':
      now.setDate(now.getDate() - (value * 7));
      break;
  }
  
  return now.toISOString();
}