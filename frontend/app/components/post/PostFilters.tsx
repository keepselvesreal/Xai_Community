import { useState, useEffect } from "react";
import Select from "~/components/ui/Select";
import Input from "~/components/ui/Input";
import Button from "~/components/ui/Button";
import { POST_TYPES, SERVICE_TYPES, SORT_OPTIONS } from "~/lib/constants";
import { debounce } from "~/lib/utils";
import type { PostFilters as PostFiltersType } from "~/types";

interface PostFiltersProps {
  filters: PostFiltersType;
  onFiltersChange: (filters: PostFiltersType) => void;
  className?: string;
}

const PostFilters = ({ filters, onFiltersChange, className }: PostFiltersProps) => {
  const [localSearch, setLocalSearch] = useState(filters.search || "");

  // 검색어 디바운스 처리
  const debouncedSearch = debounce((searchTerm: string) => {
    onFiltersChange({ ...filters, search: searchTerm, page: 1 });
  }, 500);

  useEffect(() => {
    debouncedSearch(localSearch);
  }, [localSearch]);

  const handleFilterChange = (key: keyof PostFiltersType, value: any) => {
    onFiltersChange({ 
      ...filters, 
      [key]: value === "" ? undefined : value,
      page: 1 // 필터 변경시 첫 페이지로 이동
    });
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSearch(event.target.value);
  };

  const handleReset = () => {
    setLocalSearch("");
    onFiltersChange({ page: 1, size: filters.size });
  };

  const hasActiveFilters = filters.type || filters.service || filters.search;

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 타입 필터 */}
        <Select
          label="타입"
          placeholder="전체"
          value={filters.type || ""}
          options={[
            { value: "", label: "전체" },
            ...POST_TYPES.map(type => ({ value: type.value, label: type.label }))
          ]}
          onChange={(e) => handleFilterChange("type", e.target.value)}
        />

        {/* 서비스 필터 */}
        <Select
          label="서비스"
          placeholder="전체"
          value={filters.service || ""}
          options={[
            { value: "", label: "전체" },
            ...SERVICE_TYPES.map(service => ({ value: service.value, label: service.label }))
          ]}
          onChange={(e) => handleFilterChange("service", e.target.value)}
        />

        {/* 정렬 옵션 */}
        <Select
          label="정렬"
          value={filters.sortBy || "created_at"}
          options={SORT_OPTIONS.map(option => ({ value: option.value, label: option.label }))}
          onChange={(e) => handleFilterChange("sortBy", e.target.value)}
        />

        {/* 검색 */}
        <div className="flex flex-col space-y-2">
          <Input
            label="검색"
            placeholder="제목 검색..."
            value={localSearch}
            onChange={handleSearchChange}
          />
          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="self-start"
            >
              필터 초기화
            </Button>
          )}
        </div>
      </div>

      {/* 활성 필터 표시 */}
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-500">활성 필터:</span>
            
            {filters.type && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                타입: {POST_TYPES.find(t => t.value === filters.type)?.label}
                <button
                  onClick={() => handleFilterChange("type", undefined)}
                  className="ml-1 text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            )}
            
            {filters.service && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                서비스: {SERVICE_TYPES.find(s => s.value === filters.service)?.label}
                <button
                  onClick={() => handleFilterChange("service", undefined)}
                  className="ml-1 text-green-600 hover:text-green-800"
                >
                  ×
                </button>
              </span>
            )}
            
            {filters.search && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                검색: "{filters.search}"
                <button
                  onClick={() => {
                    setLocalSearch("");
                    handleFilterChange("search", undefined);
                  }}
                  className="ml-1 text-purple-600 hover:text-purple-800"
                >
                  ×
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PostFilters;