import { useState } from "react";
import Button from "~/components/ui/Button";
import Textarea from "~/components/ui/Textarea";
import ReportModal from "~/components/common/ReportModal";
import { formatRelativeTime, formatNumber } from "~/lib/utils";
import { apiClient } from "~/lib/api";
import type { Comment, User } from "~/types";

interface CommentItemProps {
  comment: Comment;
  currentUser?: User | null;
  onReply?: (parentId: string, content: string) => Promise<void>;
  onEdit?: (commentId: string, content: string) => Promise<void>;
  onDelete?: (commentId: string) => Promise<void>;
  onReaction?: (commentId: string, type: "like" | "dislike") => void;
  depth?: number;
  maxDepth?: number;
  pageType?: 'board' | 'property_information' | 'expert_tips' | 'moving_services';
  subtype?: 'inquiry' | 'review' | 'service_inquiry' | 'service_review';
}

const CommentItem = ({ 
  comment, 
  currentUser, 
  onReply, 
  onEdit, 
  onDelete, 
  onReaction,
  depth = 0,
  maxDepth = 3,
  pageType = 'board',
  subtype
}: CommentItemProps) => {
  const [isReplying, setIsReplying] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  const [editContent, setEditContent] = useState(comment.content);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // 신고 모달 상태
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  // 소유자 권한 체크
  const isOwner = () => {
    if (!currentUser || !comment.author) {
      return false;
    }
    
    const currentUserId = currentUser.id || currentUser._id;
    const commentAuthorId = comment.author.id || comment.author._id;
    
    const userIdMatch = currentUserId && commentAuthorId && 
      String(commentAuthorId) === String(currentUserId);
    
    const emailMatch = comment.author.email && currentUser.email && 
      comment.author.email.trim().toLowerCase() === currentUser.email.trim().toLowerCase();
    
    return userIdMatch || emailMatch;
  };

  const indentClass = depth > 0 ? `ml-${Math.min(depth * 4, 12)}` : "";

  // 편집 핸들러
  const handleEdit = async () => {
    if (!onEdit || !editContent.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onEdit(comment.id, editContent.trim());
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to edit comment:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 답글 핸들러
  const handleReply = async () => {
    if (!onReply || !replyContent.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onReply(comment.id, replyContent.trim());
      setIsReplying(false);
      setReplyContent("");
    } catch (error) {
      console.error("Failed to reply:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 삭제 핸들러
  const handleDelete = async () => {
    if (!onDelete) return;
    
    if (window.confirm("정말로 삭제하시겠습니까?")) {
      try {
        await onDelete(comment.id);
      } catch (error) {
        console.error("Failed to delete comment:", error);
      }
    }
  };

  // 반응 핸들러
  const handleReaction = (type: "like" | "dislike") => {
    if (!onReaction) return;
    
    console.log('🔍 댓글 반응 클릭:', {
      commentId: comment.id,
      type,
      currentUserReaction: comment.user_reaction,
      hasCurrentUser: !!currentUser
    });
    
    onReaction(comment.id, type);
  };

  // 신고 제출 핸들러
  const handleReportSubmit = async (content: string) => {
    setReportLoading(true);
    try {
      const response = await apiClient.reportComment(comment.id, content);
      if (response.success) {
        alert('신고가 접수되었습니다. 검토 후 조치하겠습니다.');
        setIsReportModalOpen(false);
      } else {
        throw new Error(response.error || '신고 접수에 실패했습니다.');
      }
    } catch (error) {
      console.error('신고 실패:', error);
      alert('신고 접수 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setReportLoading(false);
    }
  };

  // 서비스 페이지용 스타일 클래스
  const getItemClass = () => {
    if (pageType === 'moving_services') {
      return depth > 0 ? 'comment-reply' : 'comment-item';
    }
    return `${indentClass} ${depth > 0 ? 'pl-4' : ''}`;
  };

  const getHeaderClass = () => {
    return pageType === 'moving_services' ? 'comment-header' : 'flex items-center justify-between mb-2';
  };

  const getContentClass = () => {
    return pageType === 'moving_services' ? 'comment-content' : 'text-gray-700 mb-3 whitespace-pre-wrap';
  };

  const getAuthorClass = () => {
    return pageType === 'moving_services' ? 'comment-author' : 'font-medium text-gray-900';
  };

  const getDateClass = () => {
    return pageType === 'moving_services' ? 'comment-date' : 'text-sm text-gray-500';
  };

  // 서비스 페이지에서 렌더링 (답글/수정/삭제 기능 활성화)
  if (pageType === 'moving_services') {
    return (
      <div className={getItemClass()}>
        <div className={getHeaderClass()}>
          <div className="comment-author-info">
            <span className={getAuthorClass()}>
              {comment.author?.display_name || comment.author?.user_handle || comment.author?.name || '익명'}
            </span>
            {depth === 0 && subtype === 'service_inquiry' && (
              <span className={`comment-badge ${comment.metadata?.isPublic === true ? 'public' : 'private'}`}>
                {comment.metadata?.isPublic === true ? '공개' : '비공개'}
              </span>
            )}
            {depth === 0 && subtype === 'service_review' && (
              <span className="comment-badge public">공개</span>
            )}
            {/* 후기인 경우 별점 표시 */}
            {subtype === 'service_review' && depth === 0 && (
              <div className="flex items-center gap-1 ml-2">
                {comment.metadata?.rating ? (
                  <>
                    {Array.from({ length: 5 }, (_, i) => {
                      const rating = Number(comment.metadata.rating);
                      const starNumber = i + 1; // 1부터 5까지
                      const isActive = starNumber <= rating; // 별점 이하면 활성화
                      return (
                        <span 
                          key={i} 
                          className={`${isActive ? "text-yellow-400" : "text-gray-300"} text-base`}
                        >
                          ★
                        </span>
                      );
                    })}
                    <span className="text-xs text-gray-600 ml-1">
                      ({comment.metadata.rating}점)
                    </span>
                  </>
                ) : (
                  <span className="text-xs text-gray-500">별점 없음</span>
                )}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <span className={getDateClass()}>
              {formatRelativeTime(comment.created_at)}
            </span>
            
            {/* 본인 댓글인 경우 수정/삭제 버튼 표시 */}
            {isOwner() && (
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="text-xs text-gray-500 hover:text-blue-600"
                >
                  수정
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  className="text-xs text-gray-500 hover:text-red-600"
                >
                  삭제
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* 댓글 내용 */}
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
          <div className={getContentClass()}>
            {/* 비공개 문의인 경우 내용 마스킹 처리 (작성자 포함) */}
            {subtype === 'service_inquiry' && 
             comment.metadata?.isPublic !== true ? 
              '[비공개 문의입니다]' : 
              comment.content
            }
          </div>
        )}

        {/* 액션 버튼들 (답글, 좋아요/싫어요) */}
        <div className="flex items-center space-x-4 text-sm mt-2">
          {onReaction && (
            <>
              {/* 디버깅용 로그 */}
              {console.log('🔍 댓글 반응 버튼 렌더링:', {
                commentId: comment.id,
                user_reaction: comment.user_reaction,
                liked: comment.user_reaction?.liked,
                disliked: comment.user_reaction?.disliked,
                like_count: comment.like_count,
                dislike_count: comment.dislike_count
              }) || null}
              <button
                type="button"
                onClick={() => handleReaction("like")}
                className={`flex items-center space-x-1 transition-colors ${
                  comment.user_reaction?.liked 
                    ? 'text-gray-900 font-bold !text-gray-900' 
                    : 'text-gray-500 hover:text-green-600'
                }`}
                disabled={!currentUser}
              >
                <span>👍</span>
                <span>{formatNumber(comment.like_count || comment.stats?.like_count || 0)}</span>
              </button>
              <button
                type="button"
                onClick={() => handleReaction("dislike")}
                className={`flex items-center space-x-1 transition-colors ${
                  comment.user_reaction?.disliked 
                    ? 'text-gray-900 font-bold !text-gray-900' 
                    : 'text-gray-500 hover:text-red-600'
                }`}
                disabled={!currentUser}
              >
                <span>👎</span>
                <span>{formatNumber(comment.dislike_count || comment.stats?.dislike_count || 0)}</span>
              </button>
            </>
          )}
          
          {onReply && depth < maxDepth && (
            <button
              type="button"
              onClick={() => setIsReplying(!isReplying)}
              className="text-gray-500 hover:text-blue-600"
            >
              답글
            </button>
          )}
          
          <button
            type="button"
            onClick={() => setIsReportModalOpen(true)}
            className="text-gray-500 hover:text-red-600"
          >
            신고
          </button>
        </div>

        {/* 답글 작성 폼 */}
        {isReplying && (
          <div className="mt-3 pl-4">
            <Textarea
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder="답글을 작성해주세요..."
              rows={2}
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

        {/* 대댓글 표시 (서비스 페이지에서도 모든 기능 활성화) */}
        {comment.replies && comment.replies.map((reply) => (
          <CommentItem
            key={reply.id}
            comment={reply}
            currentUser={currentUser}
            onReply={onReply} // 답글 기능 활성화
            onEdit={onEdit} // 수정 기능 활성화
            onDelete={onDelete} // 삭제 기능 활성화
            onReaction={onReaction} // 반응 기능 활성화
            depth={depth + 1}
            maxDepth={maxDepth}
            pageType={pageType}
            subtype={subtype}
          />
        ))}
      </div>
    );
  }

  // 일반 게시글 페이지 렌더링
  return (
    <div className={getItemClass()}>
      <div className="border-t border-gray-100 py-4">
        <div className={getHeaderClass()}>
          <div className="flex items-center space-x-2">
            <span className={getAuthorClass()}>
              {comment.author?.display_name || comment.author?.user_handle || comment.author?.name || '익명'}
            </span>
            <span className={getDateClass()}>
              {formatRelativeTime(comment.created_at)}
            </span>
            {comment.updated_at !== comment.created_at && (
              <span className="text-xs text-gray-400">(편집됨)</span>
            )}
          </div>
          
          {isOwner() && (
            <div className="flex space-x-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsEditing(true)}
              >
                수정
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleDelete}
              >
                삭제
              </Button>
            </div>
          )}
        </div>

        {/* 댓글 내용 */}
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
          <div className={getContentClass()}>
            {/* 비공개 문의인 경우 내용 마스킹 처리 (작성자 포함) */}
            {subtype === 'service_inquiry' && 
             comment.metadata?.isPublic !== true ? 
              '[비공개 문의입니다]' : 
              comment.content
            }
          </div>
        )}

        {/* 액션 버튼들 */}
        <div className="flex items-center space-x-4 text-sm">
          {onReaction && (
            <>
              {/* 디버깅용 로그 - 일반 페이지 */}
              {console.log('🔍 댓글 반응 버튼 렌더링 (일반):', {
                commentId: comment.id,
                user_reaction: comment.user_reaction,
                liked: comment.user_reaction?.liked,
                disliked: comment.user_reaction?.disliked,
                like_count: comment.like_count,
                dislike_count: comment.dislike_count
              }) || null}
              <button
                type="button"
                onClick={() => handleReaction("like")}
                className={`flex items-center space-x-1 transition-colors ${
                  comment.user_reaction?.liked 
                    ? 'text-gray-900 font-bold !text-gray-900' 
                    : 'text-gray-500 hover:text-green-600'
                }`}
                disabled={!currentUser}
              >
                <span>👍</span>
                <span>{formatNumber(comment.like_count || comment.stats?.like_count || 0)}</span>
              </button>
              <button
                type="button"
                onClick={() => handleReaction("dislike")}
                className={`flex items-center space-x-1 transition-colors ${
                  comment.user_reaction?.disliked 
                    ? 'text-gray-900 font-bold !text-gray-900' 
                    : 'text-gray-500 hover:text-red-600'
                }`}
                disabled={!currentUser}
              >
                <span>👎</span>
                <span>{formatNumber(comment.dislike_count || comment.stats?.dislike_count || 0)}</span>
              </button>
            </>
          )}
          
          {onReply && depth < maxDepth && (
            <button
              type="button"
              onClick={() => setIsReplying(!isReplying)}
              className="text-gray-500 hover:text-blue-600"
            >
              답글
            </button>
          )}
          
          <button
            type="button"
            onClick={() => setIsReportModalOpen(true)}
            className="text-gray-500 hover:text-red-600"
          >
            신고
          </button>
        </div>

        {/* 답글 작성 폼 */}
        {isReplying && (
          <div className="mt-3 pl-4">
            <Textarea
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder="답글을 작성해주세요..."
              rows={2}
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

        {/* 대댓글 표시 */}
        {comment.replies && comment.replies.map((reply) => (
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
            pageType={pageType}
            subtype={subtype}
          />
        ))}
      </div>

      {/* 신고 모달 */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        targetType="comment"
        targetId={comment.id}
        onSubmit={handleReportSubmit}
        isLoading={reportLoading}
      />
    </div>
  );
};

export default CommentItem;