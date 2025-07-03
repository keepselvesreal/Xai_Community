import React from 'react';

interface ActivityItemSkeletonProps {
  count?: number;
  className?: string;
}

export function ActivityItemSkeleton({ count = 3, className = '' }: ActivityItemSkeletonProps) {
  const items = Array.from({ length: count }, (_, index) => (
    <div key={index} data-testid="activity-item-skeleton">
      {/* Activity Item 스켈레톤 */}
      <div 
        className="flex justify-between items-center p-4 bg-var-section rounded-lg border border-var-light animate-pulse"
      >
        <span className="font-medium text-sm flex items-center gap-2">
          {/* 아이콘 스켈레톤 */}
          <div className="w-4 h-4 bg-gray-200 rounded" />
          {/* 활동명 스켈레톤 */}
          <div className="h-4 bg-gray-200 rounded w-16" />
        </span>
        <span className="font-semibold text-sm flex items-center gap-2">
          {/* 개수 스켈레톤 */}
          <div className="h-4 bg-gray-200 rounded w-8" />
          {/* 보기/숨기기 텍스트 스켈레톤 */}
          <div className="h-3 bg-gray-200 rounded w-10" />
        </span>
      </div>

      {/* 확장된 활동 내용 스켈레톤 (일부만 표시) */}
      {index < 2 && (
        <div className="ml-4 mt-2 space-y-2">
          <div className="bg-white border border-var-light rounded-lg p-4">
            <div className="space-y-3">
              {Array.from({ length: 2 }, (_, itemIndex) => (
                <div key={itemIndex} className="border-b border-var-light pb-3 last:border-b-0 last:pb-0">
                  <div className="block p-2">
                    {/* 제목 스켈레톤 */}
                    <div className="h-4 bg-gray-200 rounded mb-2 w-3/4 animate-pulse" />
                    
                    {/* 통계 정보 스켈레톤 */}
                    <div className="flex items-center gap-2 text-xs">
                      <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
                      <div className="w-1 h-1 bg-gray-200 rounded-full animate-pulse" />
                      <div className="h-3 bg-gray-200 rounded w-8 animate-pulse" />
                      <div className="h-3 bg-gray-200 rounded w-8 animate-pulse" />
                      <div className="h-3 bg-gray-200 rounded w-8 animate-pulse" />
                      <div className="h-3 bg-gray-200 rounded w-8 animate-pulse" />
                      <div className="w-1 h-1 bg-gray-200 rounded-full animate-pulse" />
                      <div className="h-3 bg-gray-200 rounded w-12 animate-pulse" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  ));

  return (
    <div 
      data-testid="activity-item-skeleton-container"
      className={`space-y-6 ${className}`}
    >
      {items}
    </div>
  );
}