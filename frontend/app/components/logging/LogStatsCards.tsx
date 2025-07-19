/**
 * 로그 통계 카드 컴포넌트
 * 
 * ERROR, WARN, INFO, DEBUG 레벨별 로그 통계를 카드 형태로 표시
 */
import React from 'react';
import { LogStatsCardsProps, LOG_LEVEL_CONFIG } from '~/types/logging';
import { dataUtils } from '~/lib/logging-api';
import LoadingSpinner from '~/components/common/LoadingSpinner';

export function LogStatsCards({
  stats,
  loading = false,
  className = ''
}: LogStatsCardsProps) {
  if (loading) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="bg-gray-50 border border-gray-200 rounded-lg p-4 animate-pulse"
          >
            <div className="flex items-center justify-between">
              <div className="w-16 h-6 bg-gray-300 rounded"></div>
              <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
            </div>
            <div className="mt-2 w-12 h-8 bg-gray-300 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  const cardData = [
    {
      level: 'ERROR',
      count: stats.error_count,
      config: LOG_LEVEL_CONFIG.ERROR
    },
    {
      level: 'WARN',
      count: stats.warn_count,
      config: LOG_LEVEL_CONFIG.WARN
    },
    {
      level: 'INFO',
      count: stats.info_count,
      config: LOG_LEVEL_CONFIG.INFO
    },
    {
      level: 'DEBUG',
      count: stats.debug_count,
      config: LOG_LEVEL_CONFIG.DEBUG
    }
  ];

  return (
    <div className={`grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
      {cardData.map(({ level, count, config }) => (
        <div
          key={level}
          className={`${config.bgColor} border ${config.borderColor} rounded-lg p-4 hover:shadow-md transition-shadow`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xl">{config.icon}</span>
              <span className={`text-sm font-medium ${config.textColor}`}>
                {config.label}
              </span>
            </div>
            <div className={`text-2xl font-bold ${config.textColor}`}>
              {dataUtils.formatNumber(count)}
            </div>
          </div>
          
          {/* 비율 표시 */}
          <div className="mt-2">
            <div className="text-xs text-gray-600">
              전체 대비 {dataUtils.formatPercentage(count, stats.total_count)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}