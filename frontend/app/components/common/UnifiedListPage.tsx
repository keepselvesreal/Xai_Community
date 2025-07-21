import { useNavigate } from '@remix-run/react';
import { useEffect } from 'react';
import { useListData } from '~/hooks/useListData';
import AppLayout from '~/components/layout/AppLayout';
import LoadingSpinner from '~/components/common/LoadingSpinner';
import { PostCardSkeleton } from '~/components/common/PostCardSkeleton';
import EmptyState from '~/components/common/EmptyState';
import { SearchAndFilters } from './SearchAndFilters';
import { FilterAndSort } from './FilterAndSort';
import { UnifiedPostList } from './UnifiedPostList';
import { UnifiedPagination } from './UnifiedPagination';
import type { ListPageConfig } from '~/types/listTypes';
import type { Post } from '~/types';
import { getNavigationUrl } from '~/types/routingTypes';

interface UnifiedListPageProps {
  config: ListPageConfig<Post>;
  user: any;
  onLogout: () => void;
  initialData?: Post[];
  isServerRendered?: boolean;
}

export function UnifiedListPage({ 
  config, 
  user, 
  onLogout,
  initialData,
  isServerRendered 
}: UnifiedListPageProps) {
  const navigate = useNavigate();
  const {
    items,
    loading,
    error,
    currentPage,
    totalPages,
    totalItems,
    pageSize,
    currentFilter,
    sortBy,
    searchQuery,
    isSearching,
    handleCategoryFilter,
    handleSort,
    handleSearch,
    handleSearchSubmit,
    handlePageChange,
    refetch
  } = useListData(config, initialData, isServerRendered);

  // 페이지 변경 시 스크롤 맨 위로
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [currentPage]);

  // Handle item click navigation using type-safe routing
  const handleItemClick = (item: Post) => {
    console.log('🔥🔥🔥 UnifiedListPage handleItemClick called!', item);
    
    const targetSlug = item.slug || item.id;
    const metadataType = config.apiFilters?.metadata_type || 'board';
    
    console.log('🚀 Target slug for navigation:', targetSlug);
    console.log('📍 Metadata type:', metadataType);
    
    // Use type-safe navigation helper
    const url = getNavigationUrl(metadataType, targetSlug);
    console.log('🏢 Generated URL:', url);
    
    try {
      navigate(url);
      console.log('✅ Navigate function called');
    } catch (error) {
      console.error('❌ Navigate error:', error);
      window.location.href = url;
    }
  };

  return (
    <AppLayout user={user} onLogout={onLogout}>
      {/* 검색 및 글쓰기 섹션 */}
      <SearchAndFilters
        writeButtonText={config.writeButtonText}
        writeButtonLink={config.writeButtonLink}
        searchPlaceholder={config.searchPlaceholder}
        searchQuery={searchQuery}
        onSearch={handleSearch}
        isSearching={isSearching}
      />
      
      {/* 필터 및 정렬 */}
      <FilterAndSort
        categories={config.categories}
        sortOptions={config.sortOptions}
        currentFilter={currentFilter}
        sortBy={sortBy}
        onCategoryFilter={handleCategoryFilter}
        onSort={handleSort}
      />
      
      {/* 로딩 상태 - 스켈레톤 UI 사용 */}
      {(loading || isSearching) && (
        <PostCardSkeleton count={6} />
      )}
      
      {/* 에러 상태 */}
      {error && !loading && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-red-600 mb-2">오류가 발생했습니다</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            다시 시도
          </button>
        </div>
      )}
      
      {/* 통합 게시글 목록 */}
      {!loading && !isSearching && !error && items.length > 0 && (
        <>
          <UnifiedPostList
            posts={items as Post[]}
            onItemClick={handleItemClick}
          />
          
          {/* 페이지네이션 */}
          <UnifiedPagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        </>
      )}
      
      {/* 빈 상태 */}
      {!loading && !isSearching && !error && items.length === 0 && (
        <EmptyState
          icon={config.emptyState?.icon || "💡"}
          title={config.emptyState?.title || "게시글이 없습니다"}
          description={config.emptyState?.description || "아직 작성된 게시글이 없어요."}
          action={
            config.emptyState?.actionLabel && config.writeButtonLink
              ? {
                  label: config.emptyState.actionLabel,
                  onClick: () => navigate(config.writeButtonLink)
                }
              : undefined
          }
        />
      )}
    </AppLayout>
  );
}