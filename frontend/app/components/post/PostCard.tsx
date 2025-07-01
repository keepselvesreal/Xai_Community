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
      {/* Category and Title */}
      <div className="flex items-center gap-2 mb-3">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {post.metadata?.type || '일반'}
        </span>
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 flex-1">
          {post.title}
        </h3>
      </div>


      {/* Post content preview */}
      <p className="text-gray-600 text-sm line-clamp-3 mb-4">
        {post.content}
      </p>

      {/* Post stats with tags, author, time and stats */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        {/* Left: User Tags */}
        <div className="flex items-center gap-1">
          {post.metadata?.tags && post.metadata.tags.length > 0 ? (
            <>
              {post.metadata.tags.slice(0, 3).map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-200"
                >
                  #{tag}
                </span>
              ))}
              {post.metadata.tags.length > 3 && (
                <span className="text-xs text-gray-500 px-1">
                  +{post.metadata.tags.length - 3}
                </span>
              )}
            </>
          ) : (
            <div></div>
          )}
        </div>
        
        {/* Right: Author, Time and Stats */}
        <div className="flex items-center gap-2">
          <span className="text-gray-600">
            {post.author?.display_name || post.author?.user_handle || '익명'}
          </span>
          <span>·</span>
          <span>{formatRelativeTime(post.created_at)}</span>
          <span>·</span>
          <span className="text-gray-500">
            👁 {formatNumber(post.stats?.view_count || post.stats?.views || 0)}
          </span>
          <span className="text-gray-500">
            👍 {formatNumber(post.stats?.like_count || post.stats?.likes || 0)}
          </span>
          <span className="text-gray-500">
            👎 {formatNumber(post.stats?.dislike_count || post.stats?.dislikes || 0)}
          </span>
          <span className="text-gray-500">
            💬 {formatNumber(post.stats?.comment_count || post.stats?.comments || 0)}
          </span>
          <span className="text-gray-500">
            🔖 {formatNumber(post.stats?.bookmark_count || post.stats?.bookmarks || 0)}
          </span>
        </div>
      </div>
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