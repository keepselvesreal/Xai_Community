interface PostCardSkeletonProps {
  count?: number;
  className?: string;
}

export function PostCardSkeleton({ count = 1, className = '' }: PostCardSkeletonProps) {
  const skeletons = Array.from({ length: count }, (_, index) => (
    <div
      key={index}
      data-testid="post-card-skeleton"
      className={`bg-white rounded-lg border border-gray-200 shadow-sm p-6 animate-pulse ${className}`}
    >
      {/* 제목 스켈레톤 */}
      <div 
        data-testid="skeleton-title"
        className="h-4 bg-gray-200 rounded mb-2"
      />
      
      {/* 내용 스켈레톤 */}
      <div 
        data-testid="skeleton-content"
        className="h-3 bg-gray-200 rounded mb-2 w-3/4"
      />
      <div className="h-3 bg-gray-200 rounded mb-3 w-1/2" />
      
      {/* 메타 정보 스켈레톤 */}
      <div className="flex items-center justify-between">
        <div 
          data-testid="skeleton-meta"
          className="h-3 bg-gray-200 rounded w-20"
        />
        <div className="h-3 bg-gray-200 rounded w-16" />
      </div>
    </div>
  ));

  if (count === 1) {
    return skeletons[0];
  }

  return (
    <div 
      data-testid="post-card-skeleton-container"
      className="grid grid-cols-1 md:grid-cols-2 gap-6"
    >
      {skeletons}
    </div>
  );
}