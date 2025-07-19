/**
 * 로그 필터링 패널 컴포넌트
 * 
 * 로그 검색 및 필터링을 위한 UI 컴포넌트
 */
import React, { useState } from 'react';
import { 
  LogFilterPanelProps, 
  LogLevel, 
  ServiceType, 
  LogSource,
  SERVICE_OPTIONS,
  SOURCE_OPTIONS,
  REGION_OPTIONS,
  INFRASTRUCTURE_OPTIONS
} from '~/types/logging';
import { logLevelUtils, serviceTypeUtils, logSourceUtils, timeUtils } from '~/lib/logging-api';

export function LogFilterPanel({
  filter,
  onFilterChange,
  loading = false,
  className = ''
}: LogFilterPanelProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(filter.search_query || '');

  const handleTimeRangeChange = (hours: number) => {
    const timeRange = timeUtils.getTimeRange(hours);
    onFilterChange({
      ...filter,
      start_time: timeRange.start_time,
      end_time: timeRange.end_time
    });
  };

  const handleLevelChange = (level: LogLevel, checked: boolean) => {
    const currentLevels = filter.levels || [];
    const newLevels = checked
      ? [...currentLevels, level]
      : currentLevels.filter(l => l !== level);
    
    onFilterChange({
      ...filter,
      levels: newLevels.length > 0 ? newLevels : undefined
    });
  };

  const handleServiceChange = (service: ServiceType, checked: boolean) => {
    const currentServices = filter.services || [];
    const newServices = checked
      ? [...currentServices, service]
      : currentServices.filter(s => s !== service);
    
    onFilterChange({
      ...filter,
      services: newServices.length > 0 ? newServices : undefined
    });
  };

  const handleSourceChange = (source: LogSource, checked: boolean) => {
    const currentSources = filter.sources || [];
    const newSources = checked
      ? [...currentSources, source]
      : currentSources.filter(s => s !== source);
    
    onFilterChange({
      ...filter,
      sources: newSources.length > 0 ? newSources : undefined
    });
  };

  const handleRegionChange = (region: string, checked: boolean) => {
    const currentRegions = filter.regions || [];
    const newRegions = checked
      ? [...currentRegions, region]
      : currentRegions.filter(r => r !== region);
    
    onFilterChange({
      ...filter,
      regions: newRegions.length > 0 ? newRegions : undefined
    });
  };

  const handleInfrastructureChange = (infrastructure: string, checked: boolean) => {
    const currentInfra = filter.infrastructure_types || [];
    const newInfra = checked
      ? [...currentInfra, infrastructure]
      : currentInfra.filter(i => i !== infrastructure);
    
    onFilterChange({
      ...filter,
      infrastructure_types: newInfra.length > 0 ? newInfra : undefined
    });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({
      ...filter,
      search_query: localSearchQuery.trim() || undefined,
      page: 1 // 검색 시 첫 페이지로 리셋
    });
  };

  const clearAllFilters = () => {
    setLocalSearchQuery('');
    onFilterChange({
      page: 1,
      page_size: filter.page_size,
      ...timeUtils.getTimeRange(24) // 기본 24시간으로 리셋
    });
  };

  const hasActiveFilters = !!(
    filter.levels?.length ||
    filter.services?.length ||
    filter.sources?.length ||
    filter.search_query ||
    filter.user_id ||
    filter.endpoint ||
    filter.regions?.length ||
    filter.infrastructure_types?.length ||
    filter.status_codes?.length ||
    filter.instance_ids?.length ||
    filter.deployment_ids?.length
  );

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🔍</span>
          <h3 className="text-lg font-semibold text-gray-900">필터링</h3>
        </div>
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="text-sm text-red-600 hover:text-red-700 font-medium"
            disabled={loading}
          >
            모든 필터 지우기
          </button>
        )}
      </div>

      <div className="space-y-6">
        {/* 검색 쿼리 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            키워드 검색
          </label>
          <form onSubmit={handleSearchSubmit} className="flex space-x-2">
            <input
              type="text"
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              placeholder="로그 메시지 또는 스택 트레이스 검색..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              검색
            </button>
          </form>
        </div>

        {/* 시간 범위 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            시간 범위
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { label: '1시간', hours: 1 },
              { label: '6시간', hours: 6 },
              { label: '24시간', hours: 24 },
              { label: '7일', hours: 168 }
            ].map(({ label, hours }) => (
              <button
                key={hours}
                onClick={() => handleTimeRangeChange(hours)}
                disabled={loading}
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* 로그 레벨 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            로그 레벨
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {logLevelUtils.all.map((level) => (
              <label key={level} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filter.levels?.includes(level) || false}
                  onChange={(e) => handleLevelChange(level, e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{level}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 서비스 타입 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            서비스
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {SERVICE_OPTIONS.map((service) => (
              <label key={service.value} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filter.services?.includes(service.value) || false}
                  onChange={(e) => handleServiceChange(service.value, e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-lg">{service.icon}</span>
                <span className="text-sm text-gray-700">
                  {service.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* 로그 소스 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            소스
          </label>
          <div className="grid grid-cols-2 gap-2">
            {SOURCE_OPTIONS.map((source) => (
              <label key={source.value} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filter.sources?.includes(source.value) || false}
                  onChange={(e) => handleSourceChange(source.value, e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-lg">{source.icon}</span>
                <span className="text-sm text-gray-700">{source.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 지역 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            지역
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {REGION_OPTIONS.map((region) => (
              <label key={region.value} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filter.regions?.includes(region.value) || false}
                  onChange={(e) => handleRegionChange(region.value, e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-lg">{region.icon}</span>
                <span className="text-sm text-gray-700">{region.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 인프라 타입 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            인프라 타입
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {INFRASTRUCTURE_OPTIONS.map((infra) => (
              <label key={infra.value} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filter.infrastructure_types?.includes(infra.value) || false}
                  onChange={(e) => handleInfrastructureChange(infra.value, e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-lg">{infra.icon}</span>
                <span className="text-sm text-gray-700">{infra.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 추가 필터 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              사용자 ID
            </label>
            <input
              type="text"
              value={filter.user_id || ''}
              onChange={(e) => onFilterChange({
                ...filter,
                user_id: e.target.value.trim() || undefined
              })}
              placeholder="특정 사용자 ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              엔드포인트
            </label>
            <input
              type="text"
              value={filter.endpoint || ''}
              onChange={(e) => onFilterChange({
                ...filter,
                endpoint: e.target.value.trim() || undefined
              })}
              placeholder="예: /api/users"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            />
          </div>
        </div>
      </div>

      {/* 활성 필터 표시 */}
      {hasActiveFilters && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm text-blue-700">
            <strong>활성 필터:</strong>
            {filter.levels?.length && (
              <span className="ml-2">레벨: {filter.levels.join(', ')}</span>
            )}
            {filter.services?.length && (
              <span className="ml-2">서비스: {filter.services.join(', ')}</span>
            )}
            {filter.sources?.length && (
              <span className="ml-2">소스: {filter.sources.join(', ')}</span>
            )}
            {filter.search_query && (
              <span className="ml-2">검색: "{filter.search_query}"</span>
            )}
            {filter.user_id && (
              <span className="ml-2">사용자: {filter.user_id}</span>
            )}
            {filter.endpoint && (
              <span className="ml-2">엔드포인트: {filter.endpoint}</span>
            )}
            {filter.regions?.length && (
              <span className="ml-2">지역: {filter.regions.join(', ')}</span>
            )}
            {filter.infrastructure_types?.length && (
              <span className="ml-2">인프라: {filter.infrastructure_types.join(', ')}</span>
            )}
            {filter.status_codes?.length && (
              <span className="ml-2">상태코드: {filter.status_codes.join(', ')}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}