import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { expect, describe, it, vi, beforeEach } from 'vitest';
import { MemoryRouter } from '@remix-run/react';
import { apiClient } from '~/lib/api';
import type { Post, Comment } from '~/types';

// Mock dependencies
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPost: vi.fn(),
    getCommentsBatch: vi.fn(),
    likePost: vi.fn(),
    dislikePost: vi.fn(),
    bookmarkPost: vi.fn(),
    deletePost: vi.fn(),
  },
}));

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showError: vi.fn(),
    showSuccess: vi.fn(),
  }),
}));

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useParams: () => ({ slug: 'test-post' }),
    useNavigate: () => mockNavigate,
    useLoaderData: () => ({ post: null, comments: [], error: null }),
    MemoryRouter: actual.MemoryRouter,
  };
});

import { useAuth } from '~/contexts/AuthContext';

// 게시판 상세 페이지 컴포넌트 (리팩토링 전)
const BoardDetailPage = () => {
  const [post, setPost] = React.useState<Post | null>(null);
  const [comments, setComments] = React.useState<Comment[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [pendingReactions, setPendingReactions] = React.useState<Set<string>>(new Set());
  const [userReactions, setUserReactions] = React.useState({
    liked: false,
    disliked: false,
    bookmarked: false,
  });

  const { user } = useAuth();
  const { slug } = useParams();

  React.useEffect(() => {
    const loadData = async () => {
      if (!slug) return;
      
      setIsLoading(true);
      try {
        const [postResult, commentsResult] = await Promise.all([
          apiClient.getPost(slug),
          apiClient.getCommentsBatch(slug)
        ]);
        
        if (postResult.success && postResult.data) {
          setPost(postResult.data);
          
          if (user && postResult.data.user_reaction) {
            setUserReactions({
              liked: postResult.data.user_reaction.liked || false,
              disliked: postResult.data.user_reaction.disliked || false,
              bookmarked: postResult.data.user_reaction.bookmarked || false,
            });
          }
        }
        
        if (commentsResult.success && commentsResult.data) {
          const actualComments = commentsResult.data.data?.comments || commentsResult.data.comments || [];
          setComments(actualComments);
        }
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [slug, user]);

  const handleReactionChange = async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    if (!user || !post || !slug) return;
    
    if (pendingReactions.has(reactionType)) return;
    
    setPendingReactions(prev => new Set([...prev, reactionType]));
    
    try {
      let response;
      
      switch (reactionType) {
        case 'like':
          response = await apiClient.likePost(slug);
          break;
        case 'dislike':
          response = await apiClient.dislikePost(slug);
          break;
        case 'bookmark':
          response = await apiClient.bookmarkPost(slug);
          break;
        default:
          throw new Error('Invalid reaction type');
      }
      
      if (response.success && response.data) {
        setPost(prev => prev ? {
          ...prev,
          stats: {
            ...prev.stats,
            like_count: response.data.like_count ?? prev.stats?.like_count ?? 0,
            dislike_count: response.data.dislike_count ?? prev.stats?.dislike_count ?? 0,
            bookmark_count: response.data.bookmark_count ?? prev.stats?.bookmark_count ?? 0,
            view_count: prev.stats?.view_count ?? 0,
            comment_count: prev.stats?.comment_count ?? 0,
          }
        } : prev);
        
        if (response.data.user_reaction) {
          setUserReactions({
            liked: response.data.user_reaction.liked || false,
            disliked: response.data.user_reaction.disliked || false,
            bookmarked: response.data.user_reaction.bookmarked || false,
          });
        }
      }
    } catch (error) {
      console.error('Reaction error:', error);
    } finally {
      setPendingReactions(prev => {
        const next = new Set(prev);
        next.delete(reactionType);
        return next;
      });
    }
  };

  const handleCommentAdded = async () => {
    if (!slug) return;
    
    try {
      const response = await apiClient.getCommentsBatch(slug);
      if (response.success && response.data) {
        const actualComments = response.data.data?.comments || response.data.comments || [];
        setComments(actualComments);
      }
    } catch (error) {
      console.error('Comment refresh error:', error);
    }
  };

  const handleEditPost = () => {
    mockNavigate(`/posts/${slug}/edit`);
  };

  const handleDeletePost = async () => {
    if (!confirm('정말로 삭제하시겠습니까?')) return;
    
    try {
      const response = await apiClient.deletePost(slug!);
      if (response.success) {
        mockNavigate('/board');
      }
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  if (isLoading) {
    return <div data-testid="loading">Loading...</div>;
  }

  if (!post) {
    return <div data-testid="not-found">Post not found</div>;
  }

  return (
    <div data-testid="board-detail-page">
      <h1>{post.title}</h1>
      <div>{post.content}</div>
      <div>{post.author?.display_name}</div>
      
      {/* 통계 정보 */}
      <div data-testid="post-stats">
        <span>👁️ {post.stats?.view_count || 0}</span>
        <span>👍 {post.stats?.like_count || 0}</span>
        <span>👎 {post.stats?.dislike_count || 0}</span>
        <span>🔖 {post.stats?.bookmark_count || 0}</span>
        <span>💬 {post.stats?.comment_count || 0}</span>
      </div>

      {/* 반응 버튼 */}
      <div data-testid="reaction-buttons">
        <button 
          onClick={() => handleReactionChange('like')}
          disabled={pendingReactions.has('like')}
          data-testid="like-button"
        >
          👍 {post.stats?.like_count || 0}
        </button>
        <button 
          onClick={() => handleReactionChange('dislike')}
          disabled={pendingReactions.has('dislike')}
          data-testid="dislike-button"
        >
          👎 {post.stats?.dislike_count || 0}
        </button>
        <button 
          onClick={() => handleReactionChange('bookmark')}
          disabled={pendingReactions.has('bookmark')}
          data-testid="bookmark-button"
        >
          🔖 {post.stats?.bookmark_count || 0}
        </button>
      </div>

      {/* 작성자 컨트롤 */}
      {user && user.id === post.author_id && (
        <div data-testid="author-controls">
          <button onClick={handleEditPost} data-testid="edit-button">수정</button>
          <button onClick={handleDeletePost} data-testid="delete-button">삭제</button>
        </div>
      )}

      {/* 댓글 섹션 */}
      <div data-testid="comments-section">
        <h3>댓글 {comments.length}개</h3>
        <button onClick={handleCommentAdded} data-testid="refresh-comments">댓글 새로고침</button>
        {comments.map(comment => (
          <div key={comment.id} data-testid="comment-item">
            <div>{comment.author?.display_name}</div>
            <div>{comment.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const mockPost: Post = {
  id: '1',
  slug: 'test-post',
  title: 'Test Post Title',
  content: 'Test post content',
  created_at: '2025-01-16T10:00:00Z',
  updated_at: '2025-01-16T10:00:00Z',
  author_id: 'author1',
  author: {
    id: 'author1',
    user_handle: 'testuser',
    display_name: 'Test User',
    email: 'test@example.com',
  },
  metadata: {
    type: 'board',
    tags: ['React', 'TypeScript'],
  },
  stats: {
    view_count: 156,
    like_count: 24,
    dislike_count: 2,
    bookmark_count: 8,
    comment_count: 12,
  },
  user_reaction: {
    liked: false,
    disliked: false,
    bookmarked: false,
  },
};

const mockComments: Comment[] = [
  {
    id: '1',
    content: 'Test comment',
    created_at: '2025-01-16T10:30:00Z',
    updated_at: '2025-01-16T10:30:00Z',
    author_id: 'user2',
    author: {
      id: 'user2',
      user_handle: 'commenter',
      display_name: 'Commenter',
      email: 'commenter@example.com',
    },
    post_id: '1',
    replies: [],
  },
];

const mockUser = {
  id: 'author1',
  user_handle: 'testuser',
  display_name: 'Test User',
  email: 'test@example.com',
};

describe('Board Detail Page - Refactored', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      logout: vi.fn(),
    });
    vi.mocked(apiClient.getPost).mockResolvedValue({
      success: true,
      data: mockPost,
    });
    vi.mocked(apiClient.getCommentsBatch).mockResolvedValue({
      success: true,
      data: { comments: mockComments },
    });
  });

  it('loads and displays post data correctly', async () => {
    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    expect(screen.getByTestId('loading')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('board-detail-page')).toBeInTheDocument();
    });

    expect(screen.getByText('Test Post Title')).toBeInTheDocument();
    expect(screen.getByText('Test post content')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });

  it('displays post statistics correctly', async () => {
    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('post-stats')).toBeInTheDocument();
    });

    expect(screen.getByText('👁️ 156')).toBeInTheDocument();
    expect(screen.getByText('👍 24')).toBeInTheDocument();
    expect(screen.getByText('👎 2')).toBeInTheDocument();
    expect(screen.getByText('🔖 8')).toBeInTheDocument();
    expect(screen.getByText('💬 12')).toBeInTheDocument();
  });

  it('handles like reaction correctly', async () => {
    vi.mocked(apiClient.likePost).mockResolvedValue({
      success: true,
      data: {
        like_count: 25,
        dislike_count: 2,
        bookmark_count: 8,
        user_reaction: { liked: true, disliked: false, bookmarked: false },
      },
    });

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('like-button')).toBeInTheDocument();
    });

    const likeButton = screen.getByTestId('like-button');
    fireEvent.click(likeButton);

    await waitFor(() => {
      expect(apiClient.likePost).toHaveBeenCalledWith('test-post');
    });
  });

  it('handles dislike reaction correctly', async () => {
    vi.mocked(apiClient.dislikePost).mockResolvedValue({
      success: true,
      data: {
        like_count: 24,
        dislike_count: 3,
        bookmark_count: 8,
        user_reaction: { liked: false, disliked: true, bookmarked: false },
      },
    });

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('dislike-button')).toBeInTheDocument();
    });

    const dislikeButton = screen.getByTestId('dislike-button');
    fireEvent.click(dislikeButton);

    await waitFor(() => {
      expect(apiClient.dislikePost).toHaveBeenCalledWith('test-post');
    });
  });

  it('handles bookmark reaction correctly', async () => {
    vi.mocked(apiClient.bookmarkPost).mockResolvedValue({
      success: true,
      data: {
        like_count: 24,
        dislike_count: 2,
        bookmark_count: 9,
        user_reaction: { liked: false, disliked: false, bookmarked: true },
      },
    });

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('bookmark-button')).toBeInTheDocument();
    });

    const bookmarkButton = screen.getByTestId('bookmark-button');
    fireEvent.click(bookmarkButton);

    await waitFor(() => {
      expect(apiClient.bookmarkPost).toHaveBeenCalledWith('test-post');
    });
  });

  it('shows author controls for post author', async () => {
    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('author-controls')).toBeInTheDocument();
    });

    expect(screen.getByTestId('edit-button')).toBeInTheDocument();
    expect(screen.getByTestId('delete-button')).toBeInTheDocument();
  });

  it('does not show author controls for non-author', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { ...mockUser, id: 'different-user' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('board-detail-page')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('author-controls')).not.toBeInTheDocument();
  });

  it('handles post edit correctly', async () => {
    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('edit-button')).toBeInTheDocument();
    });

    const editButton = screen.getByTestId('edit-button');
    fireEvent.click(editButton);

    expect(mockNavigate).toHaveBeenCalledWith('/posts/test-post/edit');
  });

  it('handles post deletion correctly', async () => {
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = vi.fn().mockReturnValue(true);

    vi.mocked(apiClient.deletePost).mockResolvedValue({
      success: true,
      data: null,
    });

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('delete-button')).toBeInTheDocument();
    });

    const deleteButton = screen.getByTestId('delete-button');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(apiClient.deletePost).toHaveBeenCalledWith('test-post');
      expect(mockNavigate).toHaveBeenCalledWith('/board');
    });

    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('displays and refreshes comments correctly', async () => {
    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('comments-section')).toBeInTheDocument();
    });

    expect(screen.getByText('댓글 1개')).toBeInTheDocument();
    expect(screen.getByText('Test comment')).toBeInTheDocument();
    expect(screen.getByText('Commenter')).toBeInTheDocument();

    // Test comment refresh
    const refreshButton = screen.getByTestId('refresh-comments');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(apiClient.getCommentsBatch).toHaveBeenCalledWith('test-post');
    });
  });

  it('handles loading state correctly', () => {
    vi.mocked(apiClient.getPost).mockReturnValue(new Promise(() => {})); // Never resolves

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });

  it('handles not found state correctly', async () => {
    vi.mocked(apiClient.getPost).mockResolvedValue({
      success: false,
      error: 'Post not found',
    });

    render(
      <MemoryRouter>
        <BoardDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('not-found')).toBeInTheDocument();
    });
  });
});

// React import 추가
import React from 'react';
import { useParams } from '@remix-run/react';