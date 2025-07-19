/**
 * 최근 에러 TOP 리스트 컴포넌트
 * 
 * 발생 빈도가 높은 에러들을 목록으로 표시
 */
import React from 'react';
import { LogErrorTopListProps, SERVICE_TYPE_CONFIG } from '~/types/logging';
import { dataUtils, timeUtils } from '~/lib/logging-api';
import LoadingSpinner from '~/components/common/LoadingSpinner';

export function LogErrorTopList({
  errors,
  loading = false,
  className = '',
  maxItems = 5
}: LogErrorTopListProps) {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-xl">🚨</span>
          <h3 className="text-lg font-semibold text-gray-900">최근 에러 TOP {maxItems}</h3>
        </div>
        <div className="space-y-3">
          {Array.from({ length: maxItems }).map((_, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg animate-pulse">
              <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
              <div className="flex-1">
                <div className="w-3/4 h-4 bg-gray-300 rounded mb-2"></div>
                <div className="w-1/2 h-3 bg-gray-300 rounded"></div>
              </div>
              <div className="w-16 h-6 bg-gray-300 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const displayErrors = errors.slice(0, maxItems);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🚨</span>
          <h3 className="text-lg font-semibold text-gray-900">최근 에러 TOP {maxItems}</h3>
        </div>
        <div className="text-sm text-gray-500">
          {errors.length > maxItems && `+${errors.length - maxItems}개 더`}
        </div>
      </div>

      {displayErrors.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">🎉</div>
          <p className="text-gray-600">최근 에러가 없습니다!</p>
          <p className="text-sm text-gray-500 mt-1">시스템이 안정적으로 운영되고 있습니다.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayErrors.map((error, index) => {
            const serviceConfig = SERVICE_TYPE_CONFIG[error.service];
            const isRecent = new Date(error.last_seen).getTime() > Date.now() - 60 * 60 * 1000; // 1시간 이내

            return (
              <div
                key={error.id}
                className={`flex items-center space-x-3 p-3 rounded-lg border transition-all hover:shadow-sm ${
                  isRecent ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
                }`}
              >
                {/* 순위 */}
                <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-red-600">{index + 1}</span>
                </div>

                {/* 서비스 아이콘 */}
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${serviceConfig.bgColor}`}>
                    <span className="text-sm">{serviceConfig.icon}</span>
                  </div>
                </div>

                {/* 에러 정보 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs px-2 py-1 rounded ${serviceConfig.bgColor} ${serviceConfig.textColor}`}>
                      {serviceConfig.label}
                    </span>
                    {error.endpoint && (
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {error.endpoint}
                      </span>
                    )}
                    {isRecent && (
                      <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
                        최근 발생
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate mt-1">
                    {dataUtils.truncateText(error.sample_message, 80)}
                  </p>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-xs text-gray-500">
                      마지막 발생: {timeUtils.formatRelativeTime(error.last_seen)}
                    </span>
                    <span className="text-xs text-gray-500">
                      첫 발생: {timeUtils.formatRelativeTime(error.first_seen)}
                    </span>
                  </div>
                </div>

                {/* 발생 횟수 */}
                <div className="flex-shrink-0 text-right">
                  <div className="text-lg font-bold text-red-600">
                    {dataUtils.formatNumber(error.count)}
                  </div>
                  <div className="text-xs text-gray-500">건</div>
                </div>

                {/* 해결 상태 */}
                <div className="flex-shrink-0">
                  {error.is_resolved ? (
                    <div className="w-3 h-3 bg-green-500 rounded-full" title="해결됨"></div>
                  ) : (
                    <div className="w-3 h-3 bg-red-500 rounded-full" title="미해결"></div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 더 보기 버튼 */}
      {errors.length > maxItems && (
        <div className="mt-4 text-center">
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            모든 에러 보기 ({errors.length}개)
          </button>
        </div>
      )}
    </div>
  );
}