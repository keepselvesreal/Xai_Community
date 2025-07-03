interface ListSkeletonProps {
  count?: number;
  className?: string;
}

export function ListSkeleton({ count = 3, className = '' }: ListSkeletonProps) {
  const items = Array.from({ length: count }, (_, index) => (
    <div
      key={index}
      data-testid="list-skeleton-item"
      className="flex items-center p-4 border-b border-gray-100 last:border-b-0"
    >
      {/* 아바타 스켈레톤 */}
      <div 
        data-testid="skeleton-avatar"
        className="w-10 h-10 bg-gray-200 rounded-full animate-pulse"
      />
      
      {/* 텍스트 영역 */}
      <div 
        data-testid="skeleton-text-area"
        className="flex-1 ml-3"
      >
        {/* 제목 스켈레톤 */}
        <div 
          data-testid="skeleton-list-title"
          className="h-4 bg-gray-200 rounded mb-2 animate-pulse"
        />
        
        {/* 설명 스켈레톤 */}
        <div 
          data-testid="skeleton-list-description"
          className="h-3 bg-gray-200 rounded w-2/3 animate-pulse"
        />
      </div>
      
      {/* 액션 버튼 스켈레톤 */}
      <div 
        data-testid="skeleton-action"
        className="w-8 h-8 bg-gray-200 rounded animate-pulse"
      />
    </div>
  ));

  return (
    <div 
      data-testid="list-skeleton"
      className={`bg-white rounded-lg border border-gray-200 animate-pulse ${className}`}
    >
      {items}
    </div>
  );
}