import { useState } from 'react';
import Card from '~/components/ui/Card';
import Button from '~/components/ui/Button';
import Textarea from '~/components/ui/Textarea';
import CommentItem from '~/components/comment/CommentItem';
import { useComments } from '~/hooks/useComments';
import type { Comment } from '~/types';

interface CommentSectionProps {
  postSlug: string;
  comments: Comment[];
  onCommentAdded: () => void;
  className?: string;
}

const CommentSection = ({ postSlug, comments, onCommentAdded, className = "" }: CommentSectionProps) => {
  const [newComment, setNewComment] = useState('');
  
  const {
    user,
    isSubmitting,
    submitComment,
    submitReply,
    editComment,
    deleteComment,
    reactToComment
  } = useComments({ postSlug, onCommentAdded });

  const handleSubmitComment = async () => {
    const success = await submitComment(newComment);
    if (success) {
      setNewComment('');
    }
  };

  // CommentItem 핸들러들
  const handleReply = async (parentId: string, content: string) => {
    await submitReply(parentId, content);
  };

  const handleEdit = async (commentId: string, content: string) => {
    await editComment(commentId, content);
  };

  const handleDelete = async (commentId: string) => {
    await deleteComment(commentId);
  };

  const handleReaction = async (commentId: string, type: 'like' | 'dislike') => {
    await reactToComment(commentId, type);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Seoul', // 한국 시간대 명시적 설정
    });
  };

  // 디버깅용 로그
  console.log('CommentSection 렌더링:', { 
    postSlug, 
    commentsCount: comments?.length, 
    hasComments: !!comments,
    commentsData: comments,
    commentsType: typeof comments,
    isArray: Array.isArray(comments)
  });

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 🔍 STAGING DEBUG: 강제 디버깅 정보 표시 */}
      <div style={{
        background: '#ff0000',
        color: 'white',
        padding: '10px',
        borderRadius: '5px',
        fontSize: '12px',
        fontFamily: 'monospace',
        border: '3px solid #ffffff',
        zIndex: 9999,
        position: 'relative'
      }}>
        <div><strong>🔍 STAGING DEBUG INFO:</strong></div>
        <div>PostSlug: {postSlug}</div>
        <div>Comments Count: {comments?.length || 0}</div>
        <div>Comments Type: {typeof comments}</div>
        <div>Is Array: {Array.isArray(comments) ? 'YES' : 'NO'}</div>
        <div>Comments Data: {JSON.stringify(comments?.slice(0, 2))}</div>
        <div>Environment: {typeof window !== 'undefined' ? (import.meta.env.MODE || 'unknown') : 'server'}</div>
        <div>VITE_API_URL: {typeof window !== 'undefined' ? (import.meta.env.VITE_API_URL || 'undefined') : 'server'}</div>
        <div>Timestamp: {new Date().toISOString()}</div>
      </div>
      
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          댓글 <span className="text-blue-600">{comments?.length || 0}</span>개
        </h3>
      </div>

      {/* 댓글 작성 폼 */}
      {user && (
        <Card>
          <Card.Content>
            <div className="space-y-4">
              <Textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="댓글을 작성해주세요..."
                rows={3}
              />
              <div className="flex justify-end">
                <Button
                  onClick={handleSubmitComment}
                  disabled={!newComment.trim() || isSubmitting}
                  loading={isSubmitting}
                >
                  댓글 작성
                </Button>
              </div>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* 댓글 목록 */}
      <div className="space-y-4">
        {comments?.map((comment) => (
          <CommentItem
            key={comment.id}
            comment={comment}
            currentUser={user}
            onReply={handleReply}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onReaction={handleReaction}
            depth={0}
            maxDepth={3}
          />
        ))}

        {(!comments || comments.length === 0) && (
          <div className="text-center py-8 text-gray-500">
            아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentSection;