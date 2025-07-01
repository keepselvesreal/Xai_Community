import { Link } from '@remix-run/react';
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
    }
  };

  return (
    <div className="flex justify-center items-center gap-4 mb-6">
      <Link
        to={writeButtonLink}
        className="w-full max-w-xs px-6 py-3 bg-var-card border border-var-color rounded-full hover:border-accent-primary hover:bg-var-hover transition-all duration-200 font-medium text-var-primary flex items-center justify-center gap-2"
      >
        {writeButtonText}
      </Link>
      
      <div className="flex items-center gap-3 bg-var-card border border-var-color rounded-full px-4 py-3 w-full max-w-xs">
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