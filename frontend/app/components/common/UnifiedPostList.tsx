import type { Post } from '~/types';
import { UnifiedPostListItem } from './UnifiedPostListItem';

interface UnifiedPostListProps {
  posts: Post[];
  onItemClick?: (post: Post) => void;
}

export function UnifiedPostList({ posts, onItemClick }: UnifiedPostListProps) {
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

  return (
    <div className="post-list">
      {posts.map((post) => (
        <UnifiedPostListItem
          key={post.id}
          post={post}
          onClick={onItemClick}
        />
      ))}
    </div>
  );
}