/**
 * 작업 시간: 2025-01-23 20:00 (한국 시간)
 * 작업 버전: v2.0
 * 주요 컴포넌트: 간소화된 로그 필터링 패널 (드롭다운 기반)
 * 
 * 주요 컴포넌트 구성:
 * - LogFilterPanel: 메인 필터링 컴포넌트 (라인 20-200)
 * - 드롭다운 필터들: 시간 범위, 로그 레벨, 서비스, 인프라 타입 (라인 50-150)
 * - 검색 기능: 키워드 검색 (라인 30-50)
 * 
 * 관련 파일:
 * - ~/types/logging.ts: 타입 정의
 * - ~/lib/logging-api.ts: API 및 유틸리티 함수
 */
import React, { useState } from 'react';
import { 
  LogFilterPanelProps, 
  LogLevel, 
  ServiceType, 
  SERVICE_OPTIONS,
  INFRASTRUCTURE_OPTIONS
} from '~/types/logging';
import { logLevelUtils, serviceTypeUtils, timeUtils } from '~/lib/logging-api';

export function LogFilterPanel({
  filter,
  onFilterChange,
  loading = false,
  className = ''
}: LogFilterPanelProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(filter.search_query || '');

  // 시간 범위 옵션
  const timeRangeOptions = [
    { label: '1시간', hours: 1 },
    { label: '6시간', hours: 6 },
    { label: '24시간', hours: 24 },
    { label: '7일', hours: 168 }
  ];

  // 현재 선택된 시간 범위 찾기
  const getCurrentTimeRange = () => {
    const now = new Date();
    const startTime = filter.start_time ? new Date(filter.start_time) : null;
    
    if (!startTime) return 24; // 기본값
    
    const diffHours = Math.round((now.getTime() - startTime.getTime()) / (1000 * 60 * 60));
    return timeRangeOptions.find(option => option.hours === diffHours)?.hours || 24;
  };

  const handleTimeRangeChange = (hours: number) => {
    const timeRange = timeUtils.getTimeRange(hours);
    onFilterChange({
      ...filter,
      start_time: timeRange.start_time,
      end_time: timeRange.end_time
    });
  };

  const handleLevelChange = (level: string) => {
    const newLevels = level === 'all' ? undefined : [level as LogLevel];
    onFilterChange({
      ...filter,
      levels: newLevels
    });
  };

  const handleServiceChange = (service: string) => {
    const newServices = service === 'all' ? undefined : [service as ServiceType];
    onFilterChange({
      ...filter,
      services: newServices
    });
  };

  const handleInfrastructureChange = (infrastructure: string) => {
    const newInfra = infrastructure === 'all' ? undefined : [infrastructure];
    onFilterChange({
      ...filter,
      infrastructure_types: newInfra
    });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({
      ...filter,
      search_query: localSearchQuery.trim() || undefined,
      page: 1
    });
  };

  const clearAllFilters = () => {
    setLocalSearchQuery('');
    onFilterChange({
      page: 1,
      page_size: filter.page_size,
      ...timeUtils.getTimeRange(24)
    });
  };

  const hasActiveFilters = !!(
    filter.levels?.length ||
    filter.services?.length ||
    filter.search_query ||
    filter.user_id ||
    filter.endpoint ||
    filter.infrastructure_types?.length ||
    filter.status_codes?.length ||
    filter.instance_ids?.length ||
    filter.deployment_ids?.length
  );

  return (
    <div className={`bg-white border-b border-gray-200 p-4 ${className}`}>
      <div className="space-y-3">
        {/* 첫 번째 줄: 검색 */}
        <div className="flex items-center space-x-4">
          <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
            <input
              type="text"
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              placeholder="키워드 검색..."
              className="w-64 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              검색
            </button>
          </form>
        </div>

        {/* 두 번째 줄: 시간, 레벨, 서비스, 인프라 */}
        <div className="flex flex-wrap items-center gap-4">
          {/* 시간 범위 드롭다운 */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">시간:</label>
            <select
              value={getCurrentTimeRange()}
              onChange={(e) => handleTimeRangeChange(Number(e.target.value))}
              disabled={loading}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {timeRangeOptions.map(option => (
                <option key={option.hours} value={option.hours}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* 로그 레벨 드롭다운 */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">레벨:</label>
            <select
              value={filter.levels?.[0] || 'all'}
              onChange={(e) => handleLevelChange(e.target.value)}
              disabled={loading}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">전체</option>
              {logLevelUtils.all.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </div>

          {/* 서비스 드롭다운 */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">서비스:</label>
            <select
              value={filter.services?.[0] || 'all'}
              onChange={(e) => handleServiceChange(e.target.value)}
              disabled={loading}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">전체</option>
              {SERVICE_OPTIONS.map((service) => (
                <option key={service.value} value={service.value}>
                  {service.label}
                </option>
              ))}
            </select>
          </div>

          {/* 인프라 타입 드롭다운 */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">인프라:</label>
            <select
              value={filter.infrastructure_types?.[0] || 'all'}
              onChange={(e) => handleInfrastructureChange(e.target.value)}
              disabled={loading}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">전체</option>
              {INFRASTRUCTURE_OPTIONS.map((infra) => (
                <option key={infra.value} value={infra.value}>
                  {infra.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 세 번째 줄: 사용자 ID, 엔드포인트, 초기화 버튼 */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={filter.user_id || ''}
              onChange={(e) => onFilterChange({
                ...filter,
                user_id: e.target.value.trim() || undefined
              })}
              placeholder="사용자 ID"
              className="w-32 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={filter.endpoint || ''}
              onChange={(e) => onFilterChange({
                ...filter,
                endpoint: e.target.value.trim() || undefined
              })}
              placeholder="엔드포인트"
              className="w-32 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={loading}
            />
          </div>

          {/* 필터 초기화 */}
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="px-3 py-2 text-sm text-red-600 hover:text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
              disabled={loading}
            >
              초기화
            </button>
          )}
        </div>
      </div>
    </div>
  );
}