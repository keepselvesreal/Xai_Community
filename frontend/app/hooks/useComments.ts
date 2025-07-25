import { useState } from 'react';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';

interface UseCommentsProps {
  postSlug: string;
  onCommentAdded: () => void;
  onCommentReaction?: () => void; // 댓글 반응 전용 콜백
}

export const useComments = ({ postSlug, onCommentAdded, onCommentReaction }: UseCommentsProps) => {
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 댓글 작성 (subtype 지원)
  const submitComment = async (content: string, subtype?: string, rating?: number, isPublic?: boolean) => {
    console.log('🚀 useComments - submitComment 호출:', { postSlug, content: content.substring(0, 50) + '...' });
    
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!content.trim()) {
      showError('댓글 내용을 입력해주세요');
      return;
    }

    setIsSubmitting(true);
    try {
      console.log('🔄 useComments - API 호출 시작:', { postSlug, contentLength: content.trim().length, subtype, rating, isPublic });
      
      let response;
      if (subtype === 'service_inquiry') {
        response = await apiClient.createServiceInquiry(postSlug, {
          content: content.trim(),
          metadata: { 
            subtype,
            isPublic: isPublic !== undefined ? isPublic : true
          }
        });
      } else if (subtype === 'service_review') {
        response = await apiClient.createServiceReview(postSlug, {
          content: content.trim(),
          metadata: { 
            subtype,
            rating: rating 
          }
        });
      } else {
        const metadata = subtype ? { subtype, rating, isPublic } : undefined;
        console.log('🔍 useComments - 댓글 생성 요청 데이터:', {
          postSlug,
          content: content.trim().substring(0, 50) + '...',
          metadata
        });
        
        response = await apiClient.createComment(postSlug, {
          content: content.trim(),
          metadata
        });
      }

      console.log('🔍 useComments - API 응답:', {
        success: response.success,
        hasData: !!response.data,
        error: response.error
      });

      if (response.success) {
        console.log('✅ useComments - 댓글 작성 성공, onCommentAdded 호출');
        onCommentAdded();
        
        // subtype에 따른 성공 메시지
        if (subtype === 'service_inquiry') {
          showSuccess('문의가 등록되었습니다');
        } else if (subtype === 'service_review') {
          showSuccess('후기가 등록되었습니다');
        } else {
          showSuccess('댓글이 작성되었습니다');
        }
        return true;
      } else {
        console.log('❌ useComments - 댓글 작성 실패:', response.error);
        
        // subtype에 따른 오류 메시지
        if (subtype === 'service_inquiry') {
          showError(response.error || '문의 등록에 실패했습니다');
        } else if (subtype === 'service_review') {
          showError(response.error || '후기 등록에 실패했습니다');
        } else {
          showError(response.error || '댓글 작성에 실패했습니다');
        }
        return false;
      }
    } catch (error) {
      console.error('🚨 useComments - 댓글 작성 예외:', error);
      showError('댓글 작성 중 오류가 발생했습니다');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  // 답글 작성
  const submitReply = async (parentId: string, content: string) => {
    if (!user) {
      showError('로그인이 필요합니다');
      return false;
    }

    try {
      const response = await apiClient.createReply(postSlug, parentId, content.trim());

      if (response.success) {
        onCommentAdded(); // 전체 댓글 목록 새로고침
        showSuccess('답글이 작성되었습니다');
        return true;
      } else {
        // 깊이 제한 에러 체크
        if (response.error && response.error.includes('depth exceeds maximum')) {
          showError('답글 깊이가 최대 제한에 도달했습니다. 새로운 댓글로 작성해주세요.');
        } else {
          showError(response.error || '답글 작성에 실패했습니다');
        }
        return false;
      }
    } catch (error) {
      console.error('답글 작성 오류:', error);
      // 에러 메시지에서 깊이 제한 확인
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('depth exceeds maximum')) {
        showError('답글 깊이가 최대 제한에 도달했습니다. 새로운 댓글로 작성해주세요.');
      } else {
        showError('답글 작성 중 오류가 발생했습니다');
      }
      return false;
    }
  };

  // 댓글 수정
  const editComment = async (commentId: string, content: string) => {
    console.log('useComments editComment:', { postSlug, commentId, content });
    
    try {
      const response = await apiClient.updateComment(postSlug, commentId, content);

      console.log('편집 API 응답:', response);

      if (response.success) {
        await onCommentAdded(); // 댓글 목록 새로고침
        showSuccess('댓글이 수정되었습니다');
        return true;
      } else {
        showError(response.error || '댓글 수정에 실패했습니다');
        return false;
      }
    } catch (error) {
      console.error('편집 처리 오류:', error);
      showError('댓글 수정 중 오류가 발생했습니다');
      return false;
    }
  };

  // 댓글 삭제
  const deleteComment = async (commentId: string) => {
    console.log('useComments deleteComment:', { postSlug, commentId });
    
    try {
      const response = await apiClient.deleteComment(postSlug, commentId);

      console.log('삭제 API 응답:', response);

      if (response.success) {
        await onCommentAdded(); // 댓글 목록 새로고침
        showSuccess('댓글이 삭제되었습니다');
        return true;
      } else {
        showError(response.error || '댓글 삭제에 실패했습니다');
        return false;
      }
    } catch (error) {
      console.error('삭제 처리 오류:', error);
      showError('댓글 삭제 중 오류가 발생했습니다');
      return false;
    }
  };

  // 댓글 반응 (좋아요/싫어요)
  const reactToComment = (commentId: string, type: 'like' | 'dislike') => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    console.log('useComments reactToComment:', { postSlug, commentId, type });

    // API 호출은 하지만 응답을 기다리지 않음 (즉시 반응)
    const callApi = async () => {
      try {
        let response;
        if (type === 'like') {
          response = await apiClient.likeComment(postSlug, commentId);
        } else {
          response = await apiClient.dislikeComment(postSlug, commentId);
        }

        console.log('반응 API 응답:', response);

        if (response.success) {
          console.log('✅ 댓글 반응 API 성공, 콜백 호출 중...');
          // 댓글 반응 전용 콜백이 있으면 사용, 없으면 기본 콜백 사용
          if (onCommentReaction) {
            console.log('📞 onCommentReaction 콜백 호출');
            onCommentReaction();
          } else {
            console.log('📞 onCommentAdded 콜백 호출');
            onCommentAdded();
          }
        } else {
          console.log('❌ 댓글 반응 API 실패:', response.error);
          showError(response.error || '반응 처리에 실패했습니다');
        }
      } catch (error) {
        console.error('반응 처리 오류:', error);
        showError('반응 처리 중 오류가 발생했습니다');
      }
    };

    callApi();
  };

  return {
    // 상태
    isSubmitting,
    user,
    
    // 기능
    submitComment,
    submitReply,
    editComment,
    deleteComment,
    reactToComment,
  };
};

export default useComments;