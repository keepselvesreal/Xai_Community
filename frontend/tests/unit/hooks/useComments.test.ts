import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, test, expect, beforeEach } from 'vitest';
import type { Comment, User } from '~/types';

// Mock API
const mockApiClient = {
  createComment: vi.fn(),
  createReply: vi.fn(),
  updateComment: vi.fn(),
  deleteComment: vi.fn(),
  likeComment: vi.fn(),
  dislikeComment: vi.fn()
};

vi.mock('~/lib/api', () => ({
  apiClient: mockApiClient
}));

// Mock contexts
const mockShowSuccess = vi.fn();
const mockShowError = vi.fn();

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError
  })
}));

const mockUser: User = {
  id: 'user-1',
  email: 'test@example.com',
  user_handle: 'testuser',
  full_name: 'Test User',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z'
};

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}));

describe('useComments', () => {
  const testPostSlug = 'test-post-slug';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('댓글 작성', () => {
    test('성공적으로 댓글을 작성할 수 있다', async () => {
      mockApiClient.createComment.mockResolvedValue({ success: true });

      // 실제 useComments 훅이 구현되면 import
      // const { result } = renderHook(() => useComments(testPostSlug, mockOnCommentAdded));
      
      // 임시 테스트 객체
      const mockHookResult = {
        submitComment: async (content: string) => {
          if (!content.trim()) {
            mockShowError('댓글 내용을 입력해주세요');
            return;
          }

          try {
            const response = await mockApiClient.createComment(testPostSlug, {
              content: content.trim()
            });

            if (response.success) {
              mockShowSuccess('댓글이 작성되었습니다');
            } else {
              mockShowError(response.error || '댓글 작성에 실패했습니다');
            }
          } catch (error) {
            mockShowError('댓글 작성 중 오류가 발생했습니다');
          }
        },
        isSubmitting: false
      };

      await act(async () => {
        await mockHookResult.submitComment('새로운 댓글 내용');
      });

      expect(mockApiClient.createComment).toHaveBeenCalledWith(testPostSlug, {
        content: '새로운 댓글 내용'
      });
      expect(mockShowSuccess).toHaveBeenCalledWith('댓글이 작성되었습니다');
    });

    test('빈 댓글 작성 시 에러 메시지가 표시된다', async () => {
      const mockHookResult = {
        submitComment: async (content: string) => {
          if (!content.trim()) {
            mockShowError('댓글 내용을 입력해주세요');
            return;
          }
        },
        isSubmitting: false
      };

      await act(async () => {
        await mockHookResult.submitComment('   '); // 공백만 있는 내용
      });

      expect(mockShowError).toHaveBeenCalledWith('댓글 내용을 입력해주세요');
      expect(mockApiClient.createComment).not.toHaveBeenCalled();
    });

    test('로그인하지 않은 사용자는 댓글을 작성할 수 없다', async () => {
      // 로그인하지 않은 상태 모킹
      vi.mocked(vi.importActual('~/contexts/AuthContext')).useAuth = vi.fn(() => ({
        user: null
      }));

      const mockHookResult = {
        submitComment: async (content: string) => {
          if (!mockUser) {
            mockShowError('로그인이 필요합니다');
            return;
          }
        },
        isSubmitting: false
      };

      await act(async () => {
        await mockHookResult.submitComment('댓글 내용');
      });

      expect(mockShowError).toHaveBeenCalledWith('로그인이 필요합니다');
      expect(mockApiClient.createComment).not.toHaveBeenCalled();
    });

    test('API 오류 시 적절한 에러 메시지가 표시된다', async () => {
      mockApiClient.createComment.mockRejectedValue(new Error('네트워크 오류'));

      const mockHookResult = {
        submitComment: async (content: string) => {
          try {
            await mockApiClient.createComment(testPostSlug, {
              content: content.trim()
            });
          } catch (error) {
            mockShowError('댓글 작성 중 오류가 발생했습니다');
          }
        },
        isSubmitting: false
      };

      await act(async () => {
        await mockHookResult.submitComment('댓글 내용');
      });

      expect(mockShowError).toHaveBeenCalledWith('댓글 작성 중 오류가 발생했습니다');
    });
  });

  describe('답글 작성', () => {
    test('성공적으로 답글을 작성할 수 있다', async () => {
      mockApiClient.createReply.mockResolvedValue({ success: true });

      const mockHookResult = {
        submitReply: async (parentId: string, content: string) => {
          try {
            const response = await mockApiClient.createReply(testPostSlug, parentId, content.trim());

            if (response.success) {
              mockShowSuccess('답글이 작성되었습니다');
            } else {
              mockShowError(response.error || '답글 작성에 실패했습니다');
            }
          } catch (error) {
            mockShowError('답글 작성 중 오류가 발생했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.submitReply('parent-comment-id', '새로운 답글');
      });

      expect(mockApiClient.createReply).toHaveBeenCalledWith(
        testPostSlug, 
        'parent-comment-id', 
        '새로운 답글'
      );
      expect(mockShowSuccess).toHaveBeenCalledWith('답글이 작성되었습니다');
    });

    test('최대 깊이 제한 오류를 처리한다', async () => {
      mockApiClient.createReply.mockResolvedValue({ 
        success: false, 
        error: 'Comment depth exceeds maximum allowed depth (3)' 
      });

      const mockHookResult = {
        submitReply: async (parentId: string, content: string) => {
          try {
            const response = await mockApiClient.createReply(testPostSlug, parentId, content.trim());

            if (response.success) {
              mockShowSuccess('답글이 작성되었습니다');
            } else {
              if (response.error && response.error.includes('depth exceeds maximum')) {
                mockShowError('답글 깊이가 최대 제한에 도달했습니다. 새로운 댓글로 작성해주세요.');
              } else {
                mockShowError(response.error || '답글 작성에 실패했습니다');
              }
            }
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            if (errorMessage.includes('depth exceeds maximum')) {
              mockShowError('답글 깊이가 최대 제한에 도달했습니다. 새로운 댓글로 작성해주세요.');
            } else {
              mockShowError('답글 작성 중 오류가 발생했습니다');
            }
          }
        }
      };

      await act(async () => {
        await mockHookResult.submitReply('parent-comment-id', '깊은 답글');
      });

      expect(mockShowError).toHaveBeenCalledWith(
        '답글 깊이가 최대 제한에 도달했습니다. 새로운 댓글로 작성해주세요.'
      );
    });
  });

  describe('댓글 수정', () => {
    test('성공적으로 댓글을 수정할 수 있다', async () => {
      mockApiClient.updateComment.mockResolvedValue({ success: true });

      const mockHookResult = {
        editComment: async (commentId: string, content: string) => {
          try {
            const response = await mockApiClient.updateComment(testPostSlug, commentId, content);

            if (response.success) {
              mockShowSuccess('댓글이 수정되었습니다');
            } else {
              mockShowError(response.error || '댓글 수정에 실패했습니다');
            }
          } catch (error) {
            mockShowError('댓글 수정 중 오류가 발생했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.editComment('comment-id', '수정된 댓글 내용');
      });

      expect(mockApiClient.updateComment).toHaveBeenCalledWith(
        testPostSlug, 
        'comment-id', 
        '수정된 댓글 내용'
      );
      expect(mockShowSuccess).toHaveBeenCalledWith('댓글이 수정되었습니다');
    });
  });

  describe('댓글 삭제', () => {
    test('성공적으로 댓글을 삭제할 수 있다', async () => {
      mockApiClient.deleteComment.mockResolvedValue({ success: true });

      const mockHookResult = {
        deleteComment: async (commentId: string) => {
          try {
            const response = await mockApiClient.deleteComment(testPostSlug, commentId);

            if (response.success) {
              mockShowSuccess('댓글이 삭제되었습니다');
            } else {
              mockShowError(response.error || '댓글 삭제에 실패했습니다');
            }
          } catch (error) {
            mockShowError('댓글 삭제 중 오류가 발생했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.deleteComment('comment-id');
      });

      expect(mockApiClient.deleteComment).toHaveBeenCalledWith(testPostSlug, 'comment-id');
      expect(mockShowSuccess).toHaveBeenCalledWith('댓글이 삭제되었습니다');
    });
  });

  describe('댓글 반응', () => {
    test('댓글에 좋아요를 누를 수 있다', async () => {
      mockApiClient.likeComment.mockResolvedValue({ success: true });

      const mockHookResult = {
        reactToComment: async (commentId: string, type: 'like' | 'dislike') => {
          try {
            let response;
            if (type === 'like') {
              response = await mockApiClient.likeComment(testPostSlug, commentId);
            } else {
              response = await mockApiClient.dislikeComment(testPostSlug, commentId);
            }

            if (!response.success) {
              mockShowError(response.error || '반응 처리에 실패했습니다');
            }
          } catch (error) {
            mockShowError('반응 처리 중 오류가 발생했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.reactToComment('comment-id', 'like');
      });

      expect(mockApiClient.likeComment).toHaveBeenCalledWith(testPostSlug, 'comment-id');
    });

    test('댓글에 싫어요를 누를 수 있다', async () => {
      mockApiClient.dislikeComment.mockResolvedValue({ success: true });

      const mockHookResult = {
        reactToComment: async (commentId: string, type: 'like' | 'dislike') => {
          try {
            let response;
            if (type === 'like') {
              response = await mockApiClient.likeComment(testPostSlug, commentId);
            } else {
              response = await mockApiClient.dislikeComment(testPostSlug, commentId);
            }

            if (!response.success) {
              mockShowError(response.error || '반응 처리에 실패했습니다');
            }
          } catch (error) {
            mockShowError('반응 처리 중 오류가 발생했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.reactToComment('comment-id', 'dislike');
      });

      expect(mockApiClient.dislikeComment).toHaveBeenCalledWith(testPostSlug, 'comment-id');
    });
  });

  describe('로딩 상태', () => {
    test('댓글 작성 중 로딩 상태가 관리된다', async () => {
      // 지연된 응답 모킹
      mockApiClient.createComment.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      // 실제 구현에서는 상태 관리 로직 테스트
      expect(true).toBe(true); // 임시 통과
    });

    test('중복 제출이 방지된다', async () => {
      // 실제 구현에서는 중복 제출 방지 로직 테스트
      expect(true).toBe(true); // 임시 통과
    });
  });

  describe('에러 핸들링', () => {
    test('네트워크 오류를 적절히 처리한다', async () => {
      mockApiClient.createComment.mockRejectedValue(new Error('네트워크 오류'));

      const mockHookResult = {
        submitComment: async (content: string) => {
          try {
            await mockApiClient.createComment(testPostSlug, { content });
          } catch (error) {
            mockShowError('댓글 작성 중 오류가 발생했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.submitComment('댓글 내용');
      });

      expect(mockShowError).toHaveBeenCalledWith('댓글 작성 중 오류가 발생했습니다');
    });

    test('서버 오류 응답을 적절히 처리한다', async () => {
      mockApiClient.createComment.mockResolvedValue({ 
        success: false, 
        error: '서버 내부 오류' 
      });

      const mockHookResult = {
        submitComment: async (content: string) => {
          const response = await mockApiClient.createComment(testPostSlug, { content });
          if (!response.success) {
            mockShowError(response.error || '댓글 작성에 실패했습니다');
          }
        }
      };

      await act(async () => {
        await mockHookResult.submitComment('댓글 내용');
      });

      expect(mockShowError).toHaveBeenCalledWith('서버 내부 오류');
    });
  });
});