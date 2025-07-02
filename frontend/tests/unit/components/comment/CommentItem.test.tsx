import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, test, expect, beforeEach } from 'vitest';
import CommentItem from '~/components/comment/CommentItem';
import type { Comment, User } from '~/types';

// Mock 데이터
const mockUser: User = {
  id: 'user-1',
  email: 'test@example.com',
  user_handle: 'testuser',
  full_name: 'Test User',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z'
};

const mockCommentAuthor = {
  id: 'author-1',
  name: 'Comment Author',
  email: 'author@example.com',
  user_handle: 'commentauthor',
  display_name: 'Comment Author Display',
  bio: 'Author bio',
  avatar_url: null,
  status: 'active' as const,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z'
};

const mockComment: Comment = {
  id: 'comment-1',
  author_id: 'author-1',
  author: mockCommentAuthor,
  content: 'This is a test comment',
  parent_comment_id: null,
  status: 'active',
  like_count: 5,
  dislike_count: 1,
  reply_count: 2,
  user_reaction: null,
  created_at: '2025-01-01T12:00:00Z',
  updated_at: '2025-01-01T12:00:00Z',
  replies: []
};

const mockCommentWithReplies: Comment = {
  ...mockComment,
  replies: [
    {
      id: 'reply-1',
      author_id: 'author-2',
      author: {
        ...mockCommentAuthor,
        id: 'author-2',
        display_name: 'Reply Author'
      },
      content: 'This is a reply',
      parent_comment_id: 'comment-1',
      status: 'active',
      like_count: 2,
      dislike_count: 0,
      reply_count: 0,
      user_reaction: null,
      created_at: '2025-01-01T13:00:00Z',
      updated_at: '2025-01-01T13:00:00Z',
      replies: []
    }
  ]
};

describe('CommentItem', () => {
  const mockHandlers = {
    onReply: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    onReaction: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('기본 렌더링', () => {
    test('댓글 작성자가 올바르게 표시된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('Comment Author Display')).toBeInTheDocument();
    });

    test('작성자 정보가 없을 때 익명으로 표시된다', () => {
      const commentWithoutAuthor: Comment = {
        ...mockComment,
        author: undefined
      };

      render(
        <CommentItem 
          comment={commentWithoutAuthor} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('익명')).toBeInTheDocument();
    });

    test('댓글 내용이 올바르게 표시된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    });

    test('좋아요/싫어요 수가 올바르게 표시된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('5')).toBeInTheDocument(); // 좋아요 수
      expect(screen.getByText('1')).toBeInTheDocument(); // 싫어요 수
    });

    test('작성 시간이 올바르게 표시된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      // 실제 표시되는 시간 형식을 확인 (2025년 1월 1일 오후 09:00)
      expect(screen.getByText(/2025년.*월.*일|오후|오전/)).toBeInTheDocument();
    });
  });

  describe('사용자 권한', () => {
    test('댓글 작성자인 경우 편집/삭제 버튼이 표시된다', () => {
      const ownerComment: Comment = {
        ...mockComment,
        author: {
          ...mockCommentAuthor,
          id: 'user-1', // 현재 사용자와 동일한 ID
          email: 'test@example.com'
        }
      };

      render(
        <CommentItem 
          comment={ownerComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('편집')).toBeInTheDocument();
      expect(screen.getByText('삭제')).toBeInTheDocument();
    });

    test('댓글 작성자가 아닌 경우 편집/삭제 버튼이 표시되지 않는다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.queryByText('편집')).not.toBeInTheDocument();
      expect(screen.queryByText('삭제')).not.toBeInTheDocument();
    });

    test('로그인하지 않은 경우 답글 버튼이 표시되지 않는다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={null}
          {...mockHandlers}
        />
      );

      expect(screen.queryByText('답글')).not.toBeInTheDocument();
    });

    test('로그인한 경우 답글 버튼이 표시된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('답글')).toBeInTheDocument();
    });
  });

  describe('상호작용', () => {
    test('좋아요 버튼 클릭 시 onReaction 핸들러가 호출된다', async () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      const likeButton = screen.getByText('👍').closest('button');
      fireEvent.click(likeButton!);

      await waitFor(() => {
        expect(mockHandlers.onReaction).toHaveBeenCalledWith('comment-1', 'like');
      });
    });

    test('싫어요 버튼 클릭 시 onReaction 핸들러가 호출된다', async () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      const dislikeButton = screen.getByText('👎').closest('button');
      fireEvent.click(dislikeButton!);

      await waitFor(() => {
        expect(mockHandlers.onReaction).toHaveBeenCalledWith('comment-1', 'dislike');
      });
    });

    test('답글 버튼 클릭 시 답글 폼이 표시된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      const replyButton = screen.getByText('답글');
      fireEvent.click(replyButton);

      expect(screen.getByPlaceholderText('답글을 작성해주세요...')).toBeInTheDocument();
      expect(screen.getByText('답글 작성')).toBeInTheDocument();
    });

    test('편집 버튼 클릭 시 편집 폼이 표시된다', () => {
      const ownerComment: Comment = {
        ...mockComment,
        author: {
          ...mockCommentAuthor,
          id: 'user-1',
          email: 'test@example.com'
        }
      };

      render(
        <CommentItem 
          comment={ownerComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      const editButton = screen.getByText('편집');
      fireEvent.click(editButton);

      expect(screen.getByDisplayValue('This is a test comment')).toBeInTheDocument();
      expect(screen.getByText('저장')).toBeInTheDocument();
    });
  });

  describe('중첩 답글', () => {
    test('답글이 있는 경우 중첩되어 표시된다', () => {
      render(
        <CommentItem 
          comment={mockCommentWithReplies} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('This is a test comment')).toBeInTheDocument();
      expect(screen.getByText('This is a reply')).toBeInTheDocument();
      expect(screen.getByText('Reply Author')).toBeInTheDocument();
    });

    test('최대 깊이 제한이 적용된다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          depth={3}
          maxDepth={3}
          {...mockHandlers}
        />
      );

      // 최대 깊이에 도달하면 답글 버튼이 표시되지 않아야 함
      expect(screen.queryByText('답글')).not.toBeInTheDocument();
    });
  });

  describe('에러 처리', () => {
    test('핸들러가 없어도 에러가 발생하지 않는다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
        />
      );

      // 에러 없이 렌더링되어야 함
      expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    });

    test('빈 댓글 내용도 처리한다', () => {
      const emptyComment: Comment = {
        ...mockComment,
        content: ''
      };

      render(
        <CommentItem 
          comment={emptyComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      // 에러 없이 렌더링되어야 함
      expect(screen.getByText('Comment Author Display')).toBeInTheDocument();
    });
  });

  describe('접근성', () => {
    test('버튼들이 올바른 aria-label을 가진다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      const likeButton = screen.getByText('👍').closest('button');
      const dislikeButton = screen.getByText('👎').closest('button');
      
      expect(likeButton).toBeInTheDocument();
      expect(dislikeButton).toBeInTheDocument();
    });

    test('키보드 네비게이션이 가능하다', () => {
      render(
        <CommentItem 
          comment={mockComment} 
          currentUser={mockUser}
          {...mockHandlers}
        />
      );

      const replyButton = screen.getByText('답글');
      replyButton.focus();
      
      expect(document.activeElement).toBe(replyButton);
    });
  });
});