import { useState } from 'react';
import Card from '~/components/ui/Card';
import Button from '~/components/ui/Button';
import Textarea from '~/components/ui/Textarea';
import CommentItem from '~/components/comment/CommentItem';
import { useComments } from '~/hooks/useComments';
import { getAnalytics } from '~/hooks/useAnalytics';
import type { Comment } from '~/types';

interface CommentSectionProps {
  postSlug: string;
  comments: Comment[];
  onCommentAdded: () => void;
  pageType?: 'board' | 'property_information' | 'expert_tips' | 'moving_services';
  subtype?: 'inquiry' | 'review' | 'service_inquiry' | 'service_review';
  className?: string;
}

const CommentSection = ({ postSlug, comments, onCommentAdded, pageType = 'board', subtype, className = "" }: CommentSectionProps) => {
  const [newComment, setNewComment] = useState('');
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [isPublic, setIsPublic] = useState(true); // 문의 공개 여부
  
  // subtype에 따른 텍스트 설정
  const getCommentText = () => {
    if (pageType === 'moving_services') {
      switch (subtype) {
        case 'service_inquiry':
          return { label: '문의', placeholder: '업체에 대한 문의사항을 입력하세요...', submitText: '문의 등록' };
        case 'service_review':
          return { label: '후기', placeholder: '서비스 이용 후기를 상세히 작성해주세요...', submitText: '후기 등록' };
        default:
          return { label: '댓글', placeholder: '댓글을 작성해주세요...', submitText: '댓글 작성' };
      }
    }
    return { label: '댓글', placeholder: '댓글을 작성해주세요...', submitText: '댓글 작성' };
  };
  
  const commentText = getCommentText();
  
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
    // 후기인 경우 별점이 필수
    if (subtype === 'service_review' && rating === 0) {
      alert('별점을 선택해주세요.');
      return;
    }
    
    // 디버깅 로그 추가
    console.log('🔍 CommentSection - 댓글 작성 시도:', {
      subtype,
      rating,
      isPublic,
      content: newComment.substring(0, 50) + '...'
    });
    
    const success = await submitComment(newComment, subtype, rating > 0 ? rating : undefined, isPublic);
    if (success) {
      setNewComment('');
      setRating(0);
      setHoveredRating(0);
      setIsPublic(true);
      // 작성 후 즉시 데이터 새로고침
      onCommentAdded();
      
      // GA4 이벤트 추적 (페이지 타입 및 subtype별로 구분)
      if (typeof window !== 'undefined') {
        const analytics = getAnalytics();
        
        // moving_services 페이지에서 subtype별 추적
        if (pageType === 'moving_services' && subtype) {
          switch (subtype) {
            case 'service_inquiry':
              analytics.trackServiceInquiryComment(postSlug, 'new_comment');
              break;
            case 'service_review':
              analytics.trackServiceReviewComment(postSlug, 'new_comment');
              break;
            default:
              analytics.trackCommentCreate(postSlug, 'new_comment', pageType);
          }
        } else {
          // 기존 페이지별 추적
          switch (pageType) {
            case 'board':
              analytics.trackBoardComment(postSlug, 'new_comment');
              break;
            case 'property_information':
              analytics.trackPropertyInfoComment(postSlug, 'new_comment');
              break;
            case 'expert_tips':
              analytics.trackExpertTipComment(postSlug, 'new_comment');
              break;
            default:
              analytics.trackCommentCreate(postSlug, 'new_comment', pageType);
          }
        }
      }
    }
  };

  // CommentItem 핸들러들
  const handleReply = async (parentId: string, content: string) => {
    const success = await submitReply(parentId, content);
    
    // GA4 이벤트 추적 (페이지 타입 및 subtype별로 구분)
    if (success && typeof window !== 'undefined') {
      const analytics = getAnalytics();
      
      // moving_services 페이지에서 subtype별 추적
      if (pageType === 'moving_services' && subtype) {
        switch (subtype) {
          case 'service_inquiry':
            analytics.trackServiceInquiryComment(postSlug, parentId);
            break;
          case 'service_review':
            analytics.trackServiceReviewComment(postSlug, parentId);
            break;
          default:
            analytics.trackCommentCreate(postSlug, parentId, pageType);
        }
      } else {
        // 기존 페이지별 추적
        switch (pageType) {
          case 'board':
            analytics.trackBoardComment(postSlug, parentId);
            break;
          case 'property_information':
            analytics.trackPropertyInfoComment(postSlug, parentId);
            break;
          case 'expert_tips':
            analytics.trackExpertTipComment(postSlug, parentId);
            break;
          default:
            analytics.trackCommentCreate(postSlug, parentId, pageType);
        }
      }
    }
  };

  const handleEdit = async (commentId: string, content: string) => {
    await editComment(commentId, content);
  };

  const handleDelete = async (commentId: string) => {
    await deleteComment(commentId);
  };

  const handleReaction = (commentId: string, type: 'like' | 'dislike') => {
    reactToComment(commentId, type);
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
    isArray: Array.isArray(comments),
    pageType,
    subtype,
    // 서비스 댓글의 메타데이터 확인
    serviceComments: comments?.filter(c => c.metadata).map(c => ({
      id: c.id,
      metadata: c.metadata,
      content: c.content
    }))
  });

  return (
    <div className={className}>
      {/* 서비스 페이지가 아닌 경우에만 헤더 표시 */}
      {pageType !== 'moving_services' && (
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">
            {commentText.label} <span className="text-blue-600">{comments?.length || 0}</span>개
          </h3>
        </div>
      )}

      {/* 서비스 페이지가 아닌 경우 입력란을 위에 표시 */}
      {pageType !== 'moving_services' && user && (
        <div className="space-y-3 mb-6">
          <Textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={commentText.placeholder}
            rows={3}
          />
          <div className="flex justify-end">
            <Button
              onClick={handleSubmitComment}
              disabled={!newComment.trim() || isSubmitting}
              loading={isSubmitting}
            >
              {commentText.submitText}
            </Button>
          </div>
        </div>
      )}

      {/* 댓글 목록 - 참조 디자인 스타일 적용 */}
      <div className={pageType === 'moving_services' ? 'comments-list space-y-4' : 'space-y-4'}>
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
            pageType={pageType}
            subtype={subtype}
          />
        ))}

        {(!comments || comments.length === 0) && (
          <div className="text-center py-8 text-gray-500">
            {pageType === 'moving_services' && commentText.label === '문의' 
              ? '아직 문의가 없습니다.' 
              : pageType === 'moving_services' && commentText.label === '후기'
              ? '아직 후기가 없습니다.'
              : '아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!'
            }
          </div>
        )}
      </div>

      {/* 서비스 페이지인 경우 입력란을 목록 아래에 표시 */}
      {pageType === 'moving_services' && user && (
        <div className={subtype === 'service_review' ? 'review-form' : 'comment-form mt-6'}>
          {subtype === 'service_review' && (
            <h4 className="form-label" style={{ marginBottom: '16px', fontSize: '16px' }}>후기 작성</h4>
          )}
          
          {/* 문의인 경우 공개/비공개 선택 */}
          {subtype === 'service_inquiry' && (
            <div className="form-group">
              <label className="form-label">
                공개 설정 *
              </label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="visibility"
                    value="public"
                    checked={isPublic}
                    onChange={() => setIsPublic(true)}
                    className="text-blue-600"
                  />
                  <span className="text-sm">공개 (모든 사용자가 볼 수 있음)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="visibility"
                    value="private"
                    checked={!isPublic}
                    onChange={() => setIsPublic(false)}
                    className="text-blue-600"
                  />
                  <span className="text-sm">비공개 (업체와 본인만 볼 수 있음)</span>
                </label>
              </div>
            </div>
          )}
          
          {/* 후기인 경우 별점 입력 */}
          {subtype === 'service_review' && (
            <div className="form-group">
              <label className="form-label">
                별점 평가 *
              </label>
              <div className="rating-input flex items-center gap-1">
                {/* 5개 별이 항상 표시, 선택한 개수만큼 노란색 */}
                {[1, 2, 3, 4, 5].map((starNumber) => {
                  const isHovered = hoveredRating > 0;
                  const isStarActive = isHovered 
                    ? starNumber <= hoveredRating 
                    : (rating > 0 && starNumber <= rating);
                  
                  console.log(`🌟 별 ${starNumber}: rating=${rating}, hoveredRating=${hoveredRating}, isActive=${isStarActive}`);
                  
                  return (
                    <span
                      key={starNumber}
                      onClick={() => {
                        console.log(`🌟 별점 클릭 - ${starNumber}점 선택`);
                        setRating(starNumber);
                      }}
                      onMouseEnter={() => setHoveredRating(starNumber)}
                      onMouseLeave={() => setHoveredRating(0)}
                      className="cursor-pointer text-2xl transition-colors duration-200"
                      style={{
                        color: isStarActive ? '#FBBF24' : '#E5E7EB'
                      }}
                    >
                      ⭐
                    </span>
                  );
                })}
              </div>
              <div style={{ fontSize: '14px', color: '#64748b', marginTop: '8px' }}>
                <div>현재 선택: {rating > 0 ? `${rating}점` : '0점'}</div>
                <div>마우스 호버: {hoveredRating > 0 ? `${hoveredRating}점` : '없음'}</div>
                <div>디버그: rating={rating}, hoveredRating={hoveredRating}</div>
              </div>
            </div>
          )}
          
          <div className={subtype === 'service_review' ? 'form-group' : ''}>
            {subtype === 'service_review' && (
              <label className="form-label">후기 내용 *</label>
            )}
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder={commentText.placeholder}
              rows={4}
              className={subtype === 'service_review' ? 'form-input' : 'comment-textarea w-full min-h-[100px] p-3 border border-gray-300 rounded-lg resize-vertical focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500'}
              style={subtype === 'service_review' ? { minHeight: '100px', resize: 'vertical' } : {}}
            />
          </div>
          
          <div className={subtype === 'service_review' ? 'form-group' : 'comment-form-actions flex justify-center mt-3'} style={{ display: 'flex', justifyContent: 'center' }}>
            <button
              onClick={handleSubmitComment}
              disabled={
                !newComment.trim() || 
                isSubmitting || 
                (subtype === 'service_review' && rating === 0)
              }
              className={subtype === 'service_review' ? 'btn-primary' : 'comment-submit bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed'}
            >
              {isSubmitting ? '등록 중...' : commentText.submitText}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommentSection;