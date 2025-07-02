import { useNavigate } from '@remix-run/react';
import { useListData } from '~/hooks/useListData';
import AppLayout from '~/components/layout/AppLayout';
import LoadingSpinner from '~/components/common/LoadingSpinner';
import EmptyState from '~/components/common/EmptyState';
import { SearchAndFilters } from './SearchAndFilters';
import { FilterAndSort } from './FilterAndSort';
import { ItemList } from './ItemList';
import type { ListPageProps, BaseListItem } from '~/types/listTypes';
import { getNavigationUrl } from '~/types/routingTypes';
import { createStandardNavigationHandler } from '~/utils/routingHelpers';

export function ListPage<T extends BaseListItem>({ 
  config, 
  user, 
  onLogout 
}: ListPageProps<T>) {
  const navigate = useNavigate();
  const {
    items,
    loading,
    error,
    currentFilter,
    sortBy,
    searchQuery,
    handleCategoryFilter,
    handleSort,
    handleSearch,
    handleSearchSubmit,
    refetch
  } = useListData(config);

  // Handle item click navigation using type-safe routing
  const handleItemClick = (item: T) => {
    console.log('🔥🔥🔥 ListPage handleItemClick called!', item);
    
    const targetSlug = (item as any).slug || item.id;
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
      
      {/* 로딩 상태 */}
      {loading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
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
      
      {/* 아이템 목록 */}
      {!loading && !error && items.length > 0 && (
        <ItemList
          items={items}
          layout={config.cardLayout}
          renderCard={config.renderCard}
          onItemClick={handleItemClick}
        />
      )}
      
      {/* 빈 상태 */}
      {!loading && !error && items.length === 0 && (
        <EmptyState
          icon={config.emptyState?.icon || "💡"}
          title={config.emptyState?.title || "전문가 꿀정보가 없습니다"}
          description={config.emptyState?.description || "아직 등록된 전문가 꿀정보가 없어요. 첫 번째 전문가가 되어보세요!"}
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