import type { FilterAndSortProps } from '~/types/listTypes';

export function FilterAndSort({
  categories,
  sortOptions,
  currentFilter,
  sortBy,
  onCategoryFilter,
  onSort,
  isFiltering = false
}: FilterAndSortProps) {
  return (
    <div className="flex justify-between items-center mb-4">
      {/* 필터 바 */}
      <div className="flex gap-2">
        {categories.map((category) => (
          <button
            key={category.value}
            onClick={() => onCategoryFilter(category.value)}
            disabled={isFiltering}
            className={`px-4 py-2 border rounded-full text-sm font-medium transition-all duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${
              currentFilter === category.value
                ? 'border-accent-primary bg-accent-primary text-white'
                : 'border-var-color bg-var-card text-var-secondary hover:border-accent-primary hover:text-accent-primary'
            }`}
          >
            {isFiltering && currentFilter === category.value && (
              <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
            )}
            {category.label}
          </button>
        ))}
      </div>

      {/* 정렬 옵션 */}
      <div className="flex items-center gap-2">
        <span className="text-var-muted text-sm">정렬:</span>
        <select
          value={sortBy}
          onChange={(e) => onSort(e.target.value)}
          className="bg-var-card border border-var-color rounded-lg px-3 py-1 text-sm text-var-primary"
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}