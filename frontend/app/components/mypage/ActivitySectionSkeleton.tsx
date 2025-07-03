import React from 'react';

interface ActivitySectionSkeletonProps {
  className?: string;
}

export function ActivitySectionSkeleton({ className = '' }: ActivitySectionSkeletonProps) {
  return (
    <div data-testid="activity-section-skeleton" className={`card p-0 overflow-hidden ${className}`}>
      {/* 헤더 스켈레톤 */}
      <div className="bg-gray-200 p-6 animate-pulse">
        <div className="h-6 bg-gray-300 rounded w-16" />
      </div>

      <div className="p-8">
        {/* 탭 네비게이션 스켈레톤 */}
        <div className="flex gap-4 mb-8">
          <div className="flex-1 px-6 py-3 rounded-xl bg-gray-200 animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-12 mx-auto" />
          </div>
          <div className="flex-1 px-6 py-3 rounded-xl bg-gray-200 animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-12 mx-auto" />
          </div>
        </div>

        {/* 활동 내용 스켈레톤 */}
        <div className="space-y-6">
          {/* 페이지 타입별 활동 섹션들 */}
          {Array.from({ length: 3 }, (_, sectionIndex) => (
            <div key={sectionIndex}>
              {/* 섹션 제목 스켈레톤 */}
              <div className="h-5 bg-gray-200 rounded mb-3 w-24 animate-pulse" />
              
              {/* 활동 아이템들 스켈레톤 */}
              <div className="space-y-2">
                {Array.from({ length: 2 }, (_, itemIndex) => (
                  <div 
                    key={itemIndex}
                    className="flex justify-between items-center p-4 bg-var-section rounded-lg border border-var-light animate-pulse"
                  >
                    <span className="font-medium text-sm flex items-center gap-2">
                      {/* 아이콘 스켈레톤 */}
                      <div className="w-4 h-4 bg-gray-200 rounded" />
                      {/* 활동명 스켈레톤 */}
                      <div className="h-4 bg-gray-200 rounded w-8" />
                    </span>
                    <span className="font-semibold text-sm flex items-center gap-2">
                      {/* 개수 스켈레톤 */}
                      <div className="h-4 bg-gray-200 rounded w-6" />
                      {/* 보기/숨기기 텍스트 스켈레톤 */}
                      <div className="h-3 bg-gray-200 rounded w-8" />
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* 활동이 없을 때의 빈 상태도 스켈레톤으로 표시 */}
          <div className="text-center py-8">
            <div className="h-4 bg-gray-200 rounded w-32 mx-auto animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}