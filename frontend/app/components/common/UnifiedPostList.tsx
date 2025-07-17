import { useState, useEffect } from 'react';
import type { Post } from '~/types';
import { UnifiedPostListItem } from './UnifiedPostListItem';
import { UnifiedPagination } from './UnifiedPagination';

interface UnifiedPostListProps {
  posts: Post[];
  onItemClick?: (post: Post) => void;
  postsPerPage?: number;
}

export function UnifiedPostList({ posts, onItemClick, postsPerPage = 10 }: UnifiedPostListProps) {
  const [currentPage, setCurrentPage] = useState(1);
  
  // 페이지 변경 시 맨 위로 스크롤
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [currentPage]);

  if (posts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-12">
        <div className="text-6xl mb-4">📝</div>
        <h3 className="text-var-primary font-semibold text-lg mb-2">
          게시글이 없습니다
        </h3>
        <p className="text-var-secondary mb-4">
          아직 작성된 게시글이 없어요.
        </p>
      </div>
    );
  }

  // 페이지네이션 계산
  const totalPages = Math.ceil(posts.length / postsPerPage);
  const startIndex = (currentPage - 1) * postsPerPage;
  const endIndex = startIndex + postsPerPage;
  const currentPosts = posts.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <>
      <div className="post-list">
        {currentPosts.map((post) => (
          <UnifiedPostListItem
            key={post.id}
            post={post}
            onClick={onItemClick}
          />
        ))}
      </div>
      
      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <UnifiedPagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </>
  );
}