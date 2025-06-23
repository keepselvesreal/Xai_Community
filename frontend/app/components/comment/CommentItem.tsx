import { useState } from "react";
import Button from "~/components/ui/Button";
import Textarea from "~/components/ui/Textarea";
import { formatRelativeTime, formatNumber } from "~/lib/utils";
import type { Comment, User } from "~/types";

interface CommentItemProps {
  comment: Comment;
  currentUser?: User | null;
  onReply?: (parentId: number, content: string) => Promise<void>;
  onEdit?: (commentId: number, content: string) => Promise<void>;
  onDelete?: (commentId: number) => Promise<void>;
  onReaction?: (commentId: number, type: "like" | "dislike") => Promise<void>;
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

  const isOwner = currentUser && comment.author === currentUser.email;
  const canReply = depth < maxDepth && currentUser;
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
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async () => {
    if (!editContent.trim() || !onEdit) return;

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
            <span className="font-medium text-gray-900">{comment.author}</span>
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
            <span>{formatNumber(comment.likes)}</span>
          </button>
          
          <button
            onClick={() => handleReaction("dislike")}
            className="flex items-center space-x-1 text-gray-500 hover:text-red-600 transition-colors"
            disabled={!currentUser}
          >
            <span>👎</span>
            <span>{formatNumber(comment.dislikes)}</span>
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

          {/* Edit/Delete buttons for owner */}
          {isOwner && !isEditing && (
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
          <div className="mt-4">
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