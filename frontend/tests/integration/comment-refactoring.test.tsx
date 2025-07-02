import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, test, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import BoardPostDetail from '~/routes/board-post.$slug';
import { AuthContext } from '~/contexts/AuthContext';
import { NotificationContext } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';
import type { User, AuthContextType } from '~/types';

// Mock API client
vi.mock('~/lib/api', () => {
  const mockApiClient = {
    getPost: vi.fn(),
    getComments: vi.fn(),
    createComment: vi.fn(),
    likePost: vi.fn(),
    dislikePost: vi.fn(),
    bookmarkPost: vi.fn(),
    deletePost: vi.fn()
  };
  
  return {
    apiClient: mockApiClient
  };
});

// Mock useParams
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useParams: () => ({ slug: 'test-post-slug' }),
    useNavigate: () => vi.fn()
  };
});

// Mock 데이터
const mockUser: User = {
  id: 'user-1',
  email: 'test@example.com',
  user_handle: 'testuser',
  full_name: 'Test User',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z'
};

const mockPost = {
  id: 'post-1',
  title: 'Test Post',
  content: 'This is a test post content',
  slug: 'test-post-slug',
  author: {
    id: 'author-1',
    display_name: 'Post Author',
    user_handle: 'postauthor',
    email: 'author@example.com'
  },
  author_id: 'author-1',
  service: 'residential_community',
  metadata: {
    type: 'board',
    category: '자유게시판'
  },
  created_at: '2025-01-01T10:00:00Z',
  updated_at: '2025-01-01T10:00:00Z',
  stats: {
    view_count: 100,
    like_count: 10,
    dislike_count: 2,
    comment_count: 3,
    bookmark_count: 5
  }
};

const mockComments = [
  {
    id: 'comment-1',
    author_id: 'author-1',
    author: {
      id: 'author-1',
      name: 'Comment Author 1',
      email: 'author1@example.com',
      user_handle: 'author1',
      display_name: 'Comment Author 1',
      bio: null,
      avatar_url: null,
      status: 'active',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    },
    content: 'First comment',
    parent_comment_id: null,
    status: 'active',
    like_count: 5,
    dislike_count: 1,
    reply_count: 0,
    user_reaction: null,
    created_at: '2025-01-01T12:00:00Z',
    updated_at: '2025-01-01T12:00:00Z',
    replies: []
  },
  {
    id: 'comment-2',
    author_id: 'author-2',
    author: {
      id: 'author-2',
      name: 'Comment Author 2',
      email: 'author2@example.com',
      user_handle: 'author2',
      display_name: 'Comment Author 2',
      bio: null,
      avatar_url: null,
      status: 'active',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z'
    },
    content: 'Second comment',
    parent_comment_id: null,
    status: 'active',
    like_count: 3,
    dislike_count: 0,
    reply_count: 1,
    user_reaction: null,
    created_at: '2025-01-01T13:00:00Z',
    updated_at: '2025-01-01T13:00:00Z',
    replies: []
  }
];

// Test wrapper 컴포넌트
const TestWrapper = ({ children, user = mockUser }: { children: React.ReactNode; user?: User | null }) => {
  const authContextValue: AuthContextType = {
    user,
    token: user ? 'fake-token' : null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
    isAuthenticated: !!user
  };

  const notificationContextValue = {
    notifications: [],
    showSuccess: vi.fn(),
    showError: vi.fn(),
    showInfo: vi.fn(),
    showWarning: vi.fn(),
    clearNotification: vi.fn(),
    clearAllNotifications: vi.fn()
  };

  return (
    <BrowserRouter>
      <AuthContext.Provider value={authContextValue}>
        <NotificationContext.Provider value={notificationContextValue}>
          {children}
        </NotificationContext.Provider>
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('Comment Refactoring Integration Tests', () => {
  const mockApiClient = vi.mocked(apiClient);
  
  beforeEach(() => {
    vi.clearAllMocks();
    
    // 기본 API 응답 설정
    mockApiClient.getPost.mockResolvedValue({
      success: true,
      data: mockPost
    });
    
    mockApiClient.getComments.mockResolvedValue({
      success: true,
      data: {
        comments: mockComments,
        pagination: {
          page: 1,
          limit: 20,
          total: 2,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('현재 구현 테스트', () => {
    test('댓글 목록이 올바르게 표시된다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Post')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('First comment')).toBeInTheDocument();
        expect(screen.getByText('Second comment')).toBeInTheDocument();
      });
    });

    test('댓글 작성자가 올바르게 표시된다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Comment Author 1')).toBeInTheDocument();
        expect(screen.getByText('Comment Author 2')).toBeInTheDocument();
      });
    });

    test('댓글 작성 폼이 로그인한 사용자에게 표시된다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('댓글을 작성해주세요...')).toBeInTheDocument();
        expect(screen.getByText('댓글 작성')).toBeInTheDocument();
      });
    });

    test('로그인하지 않은 사용자에게는 댓글 작성 폼이 표시되지 않는다', async () => {
      render(
        <TestWrapper user={null}>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Post')).toBeInTheDocument();
      });

      expect(screen.queryByPlaceholderText('댓글을 작성해주세요...')).not.toBeInTheDocument();
    });

    test('댓글 수가 올바르게 표시된다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/댓글.*2.*개/)).toBeInTheDocument();
      });
    });
  });

  describe('댓글 작성 기능', () => {
    test('새 댓글을 작성할 수 있다', async () => {
      mockApiClient.createComment.mockResolvedValue({
        success: true,
        data: {
          id: 'new-comment',
          content: 'New test comment'
        }
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('댓글을 작성해주세요...')).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText('댓글을 작성해주세요...');
      const submitButton = screen.getByText('댓글 작성');

      fireEvent.change(textarea, { target: { value: 'New test comment' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiClient.createComment).toHaveBeenCalledWith('test-post-slug', {
          content: 'New test comment'
        });
      });
    });

    test('빈 댓글은 작성할 수 없다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('댓글 작성')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('댓글 작성');
      expect(submitButton).toBeDisabled();
    });

    test('댓글 작성 중에는 버튼이 비활성화된다', async () => {
      // API 호출을 지연시켜 로딩 상태 테스트
      mockApiClient.createComment.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('댓글을 작성해주세요...')).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText('댓글을 작성해주세요...');
      const submitButton = screen.getByText('댓글 작성');

      fireEvent.change(textarea, { target: { value: 'Test comment' } });
      fireEvent.click(submitButton);

      // 버튼이 비활성화되고 로딩 상태가 표시되어야 함
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('에러 처리', () => {
    test('게시글 로딩 실패 시 에러 메시지가 표시된다', async () => {
      mockApiClient.getPost.mockRejectedValue(new Error('Failed to load post'));

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('게시글을 찾을 수 없습니다')).toBeInTheDocument();
      });
    });

    test('댓글 로딩 실패 시에도 게시글은 표시된다', async () => {
      mockApiClient.getComments.mockRejectedValue(new Error('Failed to load comments'));

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Post')).toBeInTheDocument();
      });

      // 댓글이 없는 경우의 메시지가 표시되어야 함
      await waitFor(() => {
        expect(screen.getByText('아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!')).toBeInTheDocument();
      });
    });

    test('댓글 작성 실패 시 에러 처리된다', async () => {
      mockApiClient.createComment.mockResolvedValue({
        success: false,
        error: 'Comment creation failed'
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('댓글을 작성해주세요...')).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText('댓글을 작성해주세요...');
      const submitButton = screen.getByText('댓글 작성');

      fireEvent.change(textarea, { target: { value: 'Test comment' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiClient.createComment).toHaveBeenCalled();
      });

      // 에러가 처리되고 텍스트가 지워지지 않아야 함
      expect(textarea).toHaveValue('Test comment');
    });
  });

  describe('데이터 타입 호환성', () => {
    test('백엔드 CommentDetail 응답 구조와 호환된다', async () => {
      const backendStyleComments = [
        {
          id: 'comment-backend-1',
          author_id: 'author-backend-1',
          author: {
            id: 'author-backend-1',
            name: 'Backend Author',
            email: 'backend@example.com',
            user_handle: 'backend_author',
            display_name: 'Backend Display Name',
            bio: 'Backend author bio',
            avatar_url: 'https://example.com/avatar.jpg',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          },
          content: 'Backend style comment',
          parent_comment_id: null,
          status: 'active',
          like_count: 10,
          dislike_count: 2,
          reply_count: 0,
          user_reaction: { liked: true, disliked: false },
          created_at: '2025-01-01T14:00:00Z',
          updated_at: '2025-01-01T14:00:00Z',
          replies: []
        }
      ];

      mockApiClient.getComments.mockResolvedValue({
        success: true,
        data: {
          comments: backendStyleComments,
          pagination: {
            page: 1,
            limit: 20,
            total: 1,
            total_pages: 1,
            has_next: false,
            has_prev: false
          }
        }
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Backend Display Name')).toBeInTheDocument();
        expect(screen.getByText('Backend style comment')).toBeInTheDocument();
      });
    });

    test('display_name이 없을 때 user_handle로 fallback된다', async () => {
      const commentWithoutDisplayName = [
        {
          ...mockComments[0],
          author: {
            ...mockComments[0].author,
            display_name: null
          }
        }
      ];

      mockApiClient.getComments.mockResolvedValue({
        success: true,
        data: {
          comments: commentWithoutDisplayName,
          pagination: {
            page: 1,
            limit: 20,
            total: 1,
            total_pages: 1,
            has_next: false,
            has_prev: false
          }
        }
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('author1')).toBeInTheDocument(); // user_handle
      });
    });

    test('모든 작성자 정보가 없을 때 익명으로 표시된다', async () => {
      const commentWithoutAuthor = [
        {
          ...mockComments[0],
          author: null
        }
      ];

      mockApiClient.getComments.mockResolvedValue({
        success: true,
        data: {
          comments: commentWithoutAuthor,
          pagination: {
            page: 1,
            limit: 20,
            total: 1,
            total_pages: 1,
            has_next: false,
            has_prev: false
          }
        }
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('익명')).toBeInTheDocument();
      });
    });
  });
});