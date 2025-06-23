import { Link } from "@remix-run/react";
import Card from "~/components/ui/Card";
import { formatRelativeTime, formatNumber } from "~/lib/utils";
import type { Post } from "~/types";

interface PostCardProps {
  post: Post;
  onClick?: (post: Post) => void;
  className?: string;
}

const PostCard = ({ post, onClick, className }: PostCardProps) => {
  const handleClick = () => {
    if (onClick) {
      onClick(post);
    }
  };

  const content = (
    <Card hover className={className}>
      {/* Post meta info */}
      <div className="flex items-center gap-3 mb-3 text-sm text-gray-500">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {post.type}
        </span>
        <span>•</span>
        <span>{formatRelativeTime(post.created_at)}</span>
        <span>•</span>
        <span>작성자: {post.author?.display_name || post.author?.user_handle || '익명'}</span>
      </div>

      {/* Post title */}
      <h3 className="text-lg font-semibold text-gray-900 mb-3 line-clamp-2">
        {post.title}
      </h3>

      {/* Post content preview */}
      <p className="text-gray-600 text-sm line-clamp-3 mb-4">
        {post.content}
      </p>

      {/* Post stats */}
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <span>👁</span>
          <span>{formatNumber(post.stats?.views || 0)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>👍</span>
          <span>{formatNumber(post.stats?.likes || 0)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>👎</span>
          <span>{formatNumber(post.stats?.dislikes || 0)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>💬</span>
          <span>{formatNumber(post.stats?.comments || 0)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>🔖</span>
          <span>{formatNumber(post.stats?.bookmarks || 0)}</span>
        </div>
      </div>

      {/* Tags */}
      {post.tags && post.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {post.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600"
            >
              #{tag}
            </span>
          ))}
          {post.tags.length > 3 && (
            <span className="text-xs text-gray-500">
              +{post.tags.length - 3} more
            </span>
          )}
        </div>
      )}
    </Card>
  );

  if (onClick) {
    return (
      <div onClick={handleClick} className="cursor-pointer">
        {content}
      </div>
    );
  }

  return (
    <Link to={`/posts/${post.slug}`} className="block">
      {content}
    </Link>
  );
};

export default PostCard;