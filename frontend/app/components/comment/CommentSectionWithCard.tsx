import CommentSection from './CommentSection';
import type { Comment } from '~/types';

interface CommentSectionWithCardProps {
  postSlug: string;
  comments: Comment[];
  onCommentAdded: () => void;
  className?: string;
}

/**
 * Card로 감싸진 댓글 섹션 컴포넌트
 * 페이지별로 다른 스타일링이 필요한 경우 사용
 */
const CommentSectionWithCard = ({ 
  postSlug, 
  comments, 
  onCommentAdded, 
  className = ""
}: CommentSectionWithCardProps) => {
  return (
    <div className={`bg-white border border-gray-200 rounded-2xl p-6 ${className}`}>
      <CommentSection
        postSlug={postSlug}
        comments={comments}
        onCommentAdded={onCommentAdded}
      />
    </div>
  );
};

export default CommentSectionWithCard;