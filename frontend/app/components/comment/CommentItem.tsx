import { useState } from "react";
import Button from "~/components/ui/Button";
import Textarea from "~/components/ui/Textarea";
import { formatRelativeTime, formatNumber } from "~/lib/utils";
import type { Comment, User } from "~/types";

interface CommentItemProps {
  comment: Comment;
  currentUser?: User | null;
  onReply?: (parentId: string, content: string) => Promise<void>;
  onEdit?: (commentId: string, content: string) => Promise<void>;
  onDelete?: (commentId: string) => Promise<void>;
  onReaction?: (commentId: string, type: "like" | "dislike") => Promise<void>;
  depth?: number;
  maxDepth?: number;
}

const CommentItem = ({ 
  comment, 
  currentUser, 
  onReply, 
  onEdit, 
  onDelete, 
  onReaction,
  depth = 0,
  maxDepth = 3
}: CommentItemProps) => {
  const [isReplying, setIsReplying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [editContent, setEditContent] = useState(comment.content);
  const [isSubmitting, setIsSubmitting] = useState(false);

  
  // 소유자 권한 체크
  const isOwner = () => {
    if (!currentUser || !comment.author) {
      return false;
    }
    
    // 1. ID 비교 (가장 정확한 방법)
    const currentUserId = currentUser.id || currentUser._id;
    const commentAuthorId = comment.author.id || comment.author._id;
    
    const userIdMatch = currentUserId && commentAuthorId && 
      String(commentAuthorId) === String(currentUserId);
    
    // 2. 이메일 비교 (둘 다 있을 때만)
    const emailMatch = comment.author.email && currentUser.email && 
      comment.author.email.trim().toLowerCase() === currentUser.email.trim().toLowerCase();
    
    // 3. user_handle 비교 (둘 다 있을 때만)
    const handleMatch = comment.author.user_handle && currentUser.user_handle &&
      comment.author.user_handle.trim() === currentUser.user_handle.trim();
    
    return userIdMatch || emailMatch || handleMatch;
  };
  
  const ownerStatus = isOwner();
  const canReply = depth < maxDepth && currentUser;
  const isMaxDepthReached = depth >= maxDepth;
  const indentClass = depth > 0 ? `ml-${Math.min(depth * 4, 12)}` : "";

  const handleReply = async () => {
    if (!replyContent.trim() || !onReply) return;

    setIsSubmitting(true);
    try {
      await onReply(comment.id, replyContent);
      setReplyContent("");
      setIsReplying(false);
    } catch (error) {
      console.error("Failed to reply:", error);
      // 깊이 제한 에러인지 확인하고 적절한 메시지 표시
      if (error instanceof Error && error.message.includes("depth exceeds maximum")) {
        alert("답글 깊이가 최대 제한에 도달했습니다. 새로운 댓글로 작성해주세요.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async () => {
    if (!editContent.trim() || !onEdit) return;

    console.log('CommentItem handleEdit 호출:', { 
      commentId: comment.id, 
      depth,
      commentData: comment 
    });

    setIsSubmitting(true);
    try {
      await onEdit(comment.id, editContent);
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to edit comment:", error);
      setEditContent(comment.content); // 실패시 원래 내용으로 복원
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!onDelete) return;
    
    console.log('CommentItem handleDelete 호출:', { 
      commentId: comment.id, 
      depth,
      commentData: comment 
    });
    
    if (window.confirm("정말 이 댓글을 삭제하시겠습니까?")) {
      try {
        await onDelete(comment.id);
      } catch (error) {
        console.error("Failed to delete comment:", error);
      }
    }
  };

  const handleReaction = async (type: "like" | "dislike") => {
    if (!onReaction) return;
    
    console.log('CommentItem handleReaction 호출:', { 
      commentId: comment.id, 
      type, 
      depth,
      commentData: comment 
    });
    
    try {
      await onReaction(comment.id, type);
    } catch (error) {
      console.error("Failed to react:", error);
    }
  };

  return (
    <div className={`${indentClass} ${depth > 0 ? 'border-l-2 border-gray-200 pl-4' : ''}`}>
      <div className="py-4 border-b border-gray-100 last:border-b-0">
        {/* Comment header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="font-medium text-gray-900">
              {comment.author?.display_name || comment.author?.user_handle || comment.author?.name || '익명'}
            </span>
            <span className="text-sm text-gray-500">
              {formatRelativeTime(comment.created_at)}
            </span>
            {comment.updated_at !== comment.created_at && (
              <span className="text-xs text-gray-400">(편집됨)</span>
            )}
          </div>
        </div>

        {/* Comment content */}
        {isEditing ? (
          <div className="mb-3">
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={3}
              className="mb-2"
            />
            <div className="flex space-x-2">
              <Button
                size="sm"
                onClick={handleEdit}
                loading={isSubmitting}
                disabled={!editContent.trim()}
              >
                저장
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setIsEditing(false);
                  setEditContent(comment.content);
                }}
              >
                취소
              </Button>
            </div>
          </div>
        ) : (
          <p className="text-gray-700 mb-3 whitespace-pre-wrap">{comment.content}</p>
        )}

        {/* Comment actions */}
        <div className="flex items-center space-x-4 text-sm">
          {/* Reactions */}
          <button
            onClick={() => handleReaction("like")}
            className="flex items-center space-x-1 text-gray-500 hover:text-green-600 transition-colors"
            disabled={!currentUser}
          >
            <span>👍</span>
            <span>{formatNumber(comment.like_count || comment.likes || 0)}</span>
          </button>
          
          <button
            onClick={() => handleReaction("dislike")}
            className="flex items-center space-x-1 text-gray-500 hover:text-red-600 transition-colors"
            disabled={!currentUser}
          >
            <span>👎</span>
            <span>{formatNumber(comment.dislike_count || comment.dislikes || 0)}</span>
          </button>

          {/* Reply button */}
          {canReply && (
            <button
              onClick={() => setIsReplying(!isReplying)}
              className="text-gray-500 hover:text-blue-600 transition-colors"
            >
              답글
            </button>
          )}
          
          {/* Max depth reached message */}
          {isMaxDepthReached && currentUser && (
            <span className="text-xs text-gray-400">
              (최대 답글 깊이에 도달했습니다)
            </span>
          )}

          {/* Edit/Delete buttons for owner */}
          {ownerStatus && !isEditing && (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="text-gray-500 hover:text-blue-600 transition-colors"
              >
                편집
              </button>
              <button
                onClick={handleDelete}
                className="text-gray-500 hover:text-red-600 transition-colors"
              >
                삭제
              </button>
            </>
          )}
        </div>

        {/* Reply form */}
        {isReplying && (
          <div className="mt-3 pl-4 border-l-2 border-blue-200">
            <Textarea
              placeholder="답글을 작성해주세요..."
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              rows={3}
              className="mb-2"
            />
            <div className="flex space-x-2">
              <Button
                size="sm"
                onClick={handleReply}
                loading={isSubmitting}
                disabled={!replyContent.trim()}
              >
                답글 작성
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setIsReplying(false);
                  setReplyContent("");
                }}
              >
                취소
              </Button>
            </div>
          </div>
        )}

        {/* Nested replies */}
        {comment.replies && comment.replies.length > 0 && (
          <div className="mt-4 border-l-2 border-gray-200 pl-4">
            <div className="text-xs text-gray-500 mb-2">
              {comment.replies.length}개의 답글
            </div>
            {comment.replies.map((reply) => (
              <CommentItem
                key={reply.id}
                comment={reply}
                currentUser={currentUser}
                onReply={onReply}
                onEdit={onEdit}
                onDelete={onDelete}
                onReaction={onReaction}
                depth={depth + 1}
                maxDepth={maxDepth}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CommentItem;