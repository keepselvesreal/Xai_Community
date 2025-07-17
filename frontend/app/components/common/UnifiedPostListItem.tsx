import type { Post } from '~/types';
import { formatRelativeTime, formatNumber } from '~/lib/utils';

interface UnifiedPostListItemProps {
  post: Post;
  onClick?: (post: Post) => void;
}

export function UnifiedPostListItem({ post, onClick }: UnifiedPostListItemProps) {
  // 카테고리별 태그 색상 결정
  const getTagColor = (category: string) => {
    switch (category) {
      case '입주 정보':
      case '입주정보':
      case 'info': 
        return 'post-tag-info';
      case '생활 정보':
      case '생활정보':
      case 'life': 
        return 'post-tag-life';
      case '이야기':
      case 'story': 
        return 'post-tag-story';
      default: 
        return 'post-tag-info';
    }
  };

  // NEW 배지 표시 여부 결정 (24시간 이내)
  const isNew = new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000;

  // 클릭 핸들러
  const handleClick = () => {
    if (onClick) {
      onClick(post);
    }
  };

  return (
    <div className="post-item" onClick={handleClick}>
      {/* 카테고리 영역 - 고정 크기 */}
      <div className="post-category-area">
        <span className={`post-tag ${getTagColor(post.metadata?.category || 'info')}`}>
          {post.metadata?.category || '일반'}
        </span>
      </div>
      
      {/* 제목 영역 - 한 줄 고정 */}
      <div className="post-title-area">
        <span className="post-title-text">
          {post.title}
        </span>
      </div>
      
      {/* 배지 영역 - NEW 배지 */}
      <div className="post-badge-area">
        {isNew && (
          <span className="badge-new">NEW</span>
        )}
      </div>
      
      {/* 태그 영역 - 최대 2개 + 카운터 */}
      <div className="post-tags-area">
        <div className="user-tags-container">
          {post.metadata?.tags && post.metadata.tags.length > 0 ? (
            <>
              {post.metadata.tags.slice(0, 2).map((tag, index) => (
                <span key={index} className="user-tag">
                  #{tag}
                </span>
              ))}
              {post.metadata.tags.length > 2 && (
                <span className="tag-counter">
                  +{post.metadata.tags.length - 2}
                </span>
              )}
            </>
          ) : null}
        </div>
      </div>
      
      {/* 메타 정보 영역 - 작성자, 시간, 통계 */}
      <div className="post-meta-area">
        <span className="author-name">
          {post.author?.display_name || post.author?.user_handle || post.author?.name || '익명'}
        </span>
        <span className="meta-separator">·</span>
        <span className="time-info">
          {formatRelativeTime(post.created_at)}
        </span>
        <span className="meta-separator">·</span>
        <span className="stat-icon">
          👁️ {formatNumber(post.stats?.view_count || post.stats?.views || 0)}
        </span>
        <span className="stat-icon">
          👍 {formatNumber(post.stats?.like_count || post.stats?.likes || 0)}
        </span>
        <span className="stat-icon">
          👎 {formatNumber(post.stats?.dislike_count || post.stats?.dislikes || 0)}
        </span>
        <span className="stat-icon">
          💬 {formatNumber(post.stats?.comment_count || post.stats?.comments || 0)}
        </span>
        <span className="stat-icon">
          🔖 {formatNumber(post.stats?.bookmark_count || post.stats?.bookmarks || 0)}
        </span>
      </div>
    </div>
  );
}