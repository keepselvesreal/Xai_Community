import { useState } from 'react';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';

interface UseCommentsProps {
  postSlug: string;
  onCommentAdded: () => void;
}

export const useComments = ({ postSlug, onCommentAdded }: UseCommentsProps) => {
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 댓글 작성
  const submitComment = async (content: string) => {
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
      console.log('🔄 useComments - API 호출 시작:', { postSlug, contentLength: content.trim().length });
      const response = await apiClient.createComment(postSlug, {
        content: content.trim(),
      });

      console.log('🔍 useComments - API 응답:', {
        success: response.success,
        hasData: !!response.data,
        error: response.error
      });

      if (response.success) {
        console.log('✅ useComments - 댓글 작성 성공, onCommentAdded 호출');
        onCommentAdded();
        showSuccess('댓글이 작성되었습니다');
        return true;
      } else {
        console.log('❌ useComments - 댓글 작성 실패:', response.error);
        showError(response.error || '댓글 작성에 실패했습니다');
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
        onCommentAdded(); // 댓글 목록 새로고침
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
        onCommentAdded(); // 댓글 목록 새로고침
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
  const reactToComment = async (commentId: string, type: 'like' | 'dislike') => {
    if (!user) {
      showError('로그인이 필요합니다');
      return false;
    }

    console.log('useComments reactToComment:', { postSlug, commentId, type });

    try {
      let response;
      if (type === 'like') {
        response = await apiClient.likeComment(postSlug, commentId);
      } else {
        response = await apiClient.dislikeComment(postSlug, commentId);
      }

      console.log('반응 API 응답:', response);

      if (response.success) {
        onCommentAdded(); // 댓글 목록 새로고침 (반응 수 업데이트)
        return true;
      } else {
        showError(response.error || '반응 처리에 실패했습니다');
        return false;
      }
    } catch (error) {
      console.error('반응 처리 오류:', error);
      showError('반응 처리 중 오류가 발생했습니다');
      return false;
    }
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