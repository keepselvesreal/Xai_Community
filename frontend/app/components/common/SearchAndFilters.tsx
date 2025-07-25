import { Link } from '@remix-run/react';
import { getAnalytics } from '~/hooks/useAnalytics';
import type { SearchAndFiltersProps } from '~/types/listTypes';

export function SearchAndFilters({
  writeButtonText,
  writeButtonLink,
  searchPlaceholder,
  searchQuery,
  onSearch,
  isSearching = false
}: SearchAndFiltersProps) {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      
      // GA4 검색 이벤트 추적
      if (typeof window !== 'undefined' && searchQuery.trim()) {
        const analytics = getAnalytics();
        analytics.trackSearchQuery(searchQuery.trim(), 0); // 결과 수는 나중에 업데이트
      }
    }
  };

  // 버튼이 없으면 검색창만 가운데 정렬
  const hasWriteButton = writeButtonText && writeButtonLink;

  return (
    <div className={`flex items-center gap-4 mb-6 ${hasWriteButton ? 'justify-center' : 'justify-center'}`}>
      {hasWriteButton && (
        <Link
          to={writeButtonLink}
          className="w-full max-w-xs px-6 py-3 bg-var-card border border-[#52C41A] rounded-full hover:border-[#52C41A] hover:bg-var-hover transition-all duration-200 font-medium text-var-primary flex items-center justify-center gap-2"
        >
          {writeButtonText}
        </Link>
      )}
      
      <div className={`flex items-center gap-3 bg-var-card border border-[#52C41A] rounded-full px-4 py-3 w-full max-w-xs ${!hasWriteButton ? 'mx-auto' : ''}`}>
        {isSearching ? (
          <div 
            data-testid="search-loading"
            className="w-4 h-4 border-2 border-accent-primary border-t-transparent rounded-full animate-spin" 
          />
        ) : (
          <span className="text-var-muted">🔍</span>
        )}
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearch(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={searchPlaceholder}
          disabled={isSearching}
          className="flex-1 bg-transparent border-none outline-none text-var-primary placeholder-var-muted disabled:opacity-50"
        />
      </div>
    </div>
  );
}