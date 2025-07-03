import React from 'react';

interface UserInfoSkeletonProps {
  className?: string;
}

export function UserInfoSkeleton({ className = '' }: UserInfoSkeletonProps) {
  return (
    <div data-testid="user-info-skeleton" className={`card p-0 overflow-hidden ${className}`}>
      {/* 헤더 스켈레톤 */}
      <div className="bg-gray-200 p-6 animate-pulse">
        <div className="h-6 bg-gray-300 rounded w-20" />
      </div>
      
      <div className="p-8 space-y-8">
        {/* 아이디 섹션 스켈레톤 */}
        <div className="flex justify-between items-start py-4">
          <div className="flex-1">
            <div className="h-3 bg-gray-200 rounded mb-2 w-12 animate-pulse" />
            <div className="h-5 bg-gray-200 rounded mb-2 w-40 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-32 animate-pulse" />
          </div>
          <div className="px-4 py-2 border rounded-lg">
            <div className="h-4 bg-gray-200 rounded w-8 animate-pulse" />
          </div>
        </div>

        {/* 이메일 섹션 스켈레톤 */}
        <div className="flex justify-between items-start py-4">
          <div className="flex-1">
            <div className="h-3 bg-gray-200 rounded mb-2 w-12 animate-pulse" />
            <div className="h-5 bg-gray-200 rounded mb-2 w-48 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-40 animate-pulse" />
          </div>
          <div className="px-4 py-2 border rounded-lg">
            <div className="h-4 bg-gray-200 rounded w-8 animate-pulse" />
          </div>
        </div>

        {/* 비밀번호 섹션 스켈레톤 */}
        <div className="flex justify-between items-start py-4">
          <div className="flex-1">
            <div className="h-3 bg-gray-200 rounded mb-2 w-16 animate-pulse" />
            <div className="h-5 bg-gray-200 rounded mb-2 w-20 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-36 animate-pulse" />
          </div>
          <div className="px-4 py-2 border rounded-lg">
            <div className="h-4 bg-gray-200 rounded w-8 animate-pulse" />
          </div>
        </div>

        {/* 수정 버튼 스켈레톤 */}
        <div className="w-full py-4 rounded-xl bg-gray-200 animate-pulse">
          <div className="h-5 bg-gray-300 rounded w-12 mx-auto" />
        </div>

        {/* 보안 설정 링크들 스켈레톤 */}
        <div className="flex justify-center gap-6 pt-6 border-t border-var-light">
          <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-20 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-24 animate-pulse" />
        </div>
      </div>
    </div>
  );
}