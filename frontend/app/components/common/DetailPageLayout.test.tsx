import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { expect, describe, it, vi, beforeEach } from 'vitest';
import { MemoryRouter } from '@remix-run/react';
import DetailPageLayout from './DetailPageLayout';
import type { Post, User, Comment } from '~/types';

// Mock dependencies
vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    logout: vi.fn(),
  }),
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showError: vi.fn(),
    showSuccess: vi.fn(),
  }),
}));

vi.mock('~/components/comment/CommentSection', () => ({
  default: ({ postSlug, comments, onCommentAdded }: any) => (
    <div data-testid="comment-section">
      <h3>댓글 {comments.length}개</h3>
      <button onClick={onCommentAdded}>Add Comment</button>
    </div>
  ),
}));

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
    tags: ['React', 'TypeScript', 'Testing'],
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

const mockUser: User = {
  id: 'author1',
  user_handle: 'testuser',
  display_name: 'Test User',
  email: 'test@example.com',
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

const defaultProps = {
  post: mockPost,
  comments: mockComments,
  onReactionChange: vi.fn(),
  onCommentAdded: vi.fn(),
  isLoading: false,
  pendingReactions: new Set<string>(),
  userReactions: {
    liked: false,
    disliked: false,
    bookmarked: false,
  },
};

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter>
      {ui}
    </MemoryRouter>
  );
};

describe('DetailPageLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders post title correctly', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('Test Post Title')).toBeInTheDocument();
    });

    it('renders post content correctly', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('Test post content')).toBeInTheDocument();
    });

    it('renders author information', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    it('renders formatted date', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      // 날짜 형식 확인 (한국어 형식)
      expect(screen.getByText(/2025년 1월 16일/)).toBeInTheDocument();
    });
  });

  describe('Post Meta Information', () => {
    it('displays post category from metadata', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('board')).toBeInTheDocument();
    });

    it('displays view count', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('156')).toBeInTheDocument();
    });

    it('displays like count', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('24')).toBeInTheDocument();
    });

    it('displays dislike count', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('displays bookmark count', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('8')).toBeInTheDocument();
    });

    it('displays comment count', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('12')).toBeInTheDocument();
    });
  });

  describe('Tags Section', () => {
    it('renders tags when available', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
      expect(screen.getByText('Testing')).toBeInTheDocument();
    });

    it('does not render tags section when no tags', () => {
      const postWithoutTags = {
        ...mockPost,
        metadata: {
          ...mockPost.metadata,
          tags: [],
        },
      };

      renderWithRouter(<DetailPageLayout {...defaultProps} post={postWithoutTags} />);
      
      expect(screen.queryByText('React')).not.toBeInTheDocument();
    });
  });

  describe('Reaction Buttons', () => {
    it('renders all reaction buttons', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      const likeButton = screen.getByText('👍').closest('button');
      const dislikeButton = screen.getByText('👎').closest('button');
      const bookmarkButton = screen.getByText('🔖').closest('button');
      
      expect(likeButton).toBeInTheDocument();
      expect(dislikeButton).toBeInTheDocument();
      expect(bookmarkButton).toBeInTheDocument();
    });

    it('calls onReactionChange when like button is clicked', () => {
      const mockOnReactionChange = vi.fn();
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          onReactionChange={mockOnReactionChange}
        />
      );
      
      const likeButton = screen.getByText('👍').closest('button');
      fireEvent.click(likeButton!);
      
      expect(mockOnReactionChange).toHaveBeenCalledWith('like');
    });

    it('calls onReactionChange when dislike button is clicked', () => {
      const mockOnReactionChange = vi.fn();
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          onReactionChange={mockOnReactionChange}
        />
      );
      
      const dislikeButton = screen.getByText('👎').closest('button');
      fireEvent.click(dislikeButton!);
      
      expect(mockOnReactionChange).toHaveBeenCalledWith('dislike');
    });

    it('calls onReactionChange when bookmark button is clicked', () => {
      const mockOnReactionChange = vi.fn();
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          onReactionChange={mockOnReactionChange}
        />
      );
      
      const bookmarkButton = screen.getByText('🔖').closest('button');
      fireEvent.click(bookmarkButton!);
      
      expect(mockOnReactionChange).toHaveBeenCalledWith('bookmark');
    });

    it('shows active state for liked post', () => {
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          userReactions={{
            liked: true,
            disliked: false,
            bookmarked: false,
          }}
        />
      );
      
      const likeButton = screen.getByText('👍').closest('button');
      expect(likeButton).toHaveClass('active');
    });

    it('disables buttons when pending reactions', () => {
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          pendingReactions={new Set(['like'])}
        />
      );
      
      const likeButton = screen.getByText('👍').closest('button');
      expect(likeButton).toBeDisabled();
    });
  });

  describe('Author Controls', () => {
    it('shows edit and delete buttons for author', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} user={mockUser} />);
      
      expect(screen.getByText('수정')).toBeInTheDocument();
      expect(screen.getByText('삭제')).toBeInTheDocument();
    });

    it('does not show author controls for non-author', () => {
      const nonAuthorUser = {
        ...mockUser,
        id: 'different-user',
      };

      renderWithRouter(<DetailPageLayout {...defaultProps} user={nonAuthorUser} />);
      
      expect(screen.queryByText('수정')).not.toBeInTheDocument();
      expect(screen.queryByText('삭제')).not.toBeInTheDocument();
    });

    it('calls onEditPost when edit button is clicked', () => {
      const mockOnEditPost = vi.fn();
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          user={mockUser}
          onEditPost={mockOnEditPost}
        />
      );
      
      const editButton = screen.getByText('수정');
      fireEvent.click(editButton);
      
      expect(mockOnEditPost).toHaveBeenCalled();
    });

    it('calls onDeletePost when delete button is clicked', () => {
      const mockOnDeletePost = vi.fn();
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          user={mockUser}
          onDeletePost={mockOnDeletePost}
        />
      );
      
      const deleteButton = screen.getByText('삭제');
      fireEvent.click(deleteButton);
      
      expect(mockOnDeletePost).toHaveBeenCalled();
    });
  });

  describe('Custom Sections', () => {
    it('renders custom sections in correct positions', () => {
      const beforeContentSection = <div data-testid="before-content">Before Content</div>;
      const afterContentSection = <div data-testid="after-content">After Content</div>;
      const afterTagsSection = <div data-testid="after-tags">After Tags</div>;
      const afterReactionsSection = <div data-testid="after-reactions">After Reactions</div>;

      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps}
          sections={{
            beforeContent: [beforeContentSection],
            afterContent: [afterContentSection],
            afterTags: [afterTagsSection],
            afterReactions: [afterReactionsSection],
          }}
        />
      );
      
      expect(screen.getByTestId('before-content')).toBeInTheDocument();
      expect(screen.getByTestId('after-content')).toBeInTheDocument();
      expect(screen.getByTestId('after-tags')).toBeInTheDocument();
      expect(screen.getByTestId('after-reactions')).toBeInTheDocument();
    });
  });

  describe('Comment Section Integration', () => {
    it('integrates CommentSection component', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      expect(screen.getByTestId('comment-section')).toBeInTheDocument();
      expect(screen.getByText('댓글 1개')).toBeInTheDocument();
    });

    it('passes correct props to CommentSection', () => {
      const mockOnCommentAdded = vi.fn();
      renderWithRouter(
        <DetailPageLayout 
          {...defaultProps} 
          onCommentAdded={mockOnCommentAdded}
        />
      );
      
      const addCommentButton = screen.getByText('Add Comment');
      fireEvent.click(addCommentButton);
      
      expect(mockOnCommentAdded).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('shows loading skeleton when isLoading is true', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} isLoading={true} />);
      
      // 로딩 상태에서는 스켈레톤 UI를 표시
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    });

    it('shows content when isLoading is false', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} isLoading={false} />);
      
      expect(screen.getByText('Test Post Title')).toBeInTheDocument();
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles missing post data gracefully', () => {
      const propsWithoutPost = {
        ...defaultProps,
        post: undefined as any,
      };

      expect(() => {
        renderWithRouter(<DetailPageLayout {...propsWithoutPost} />);
      }).not.toThrow();
    });

    it('handles missing stats gracefully', () => {
      const postWithoutStats = {
        ...mockPost,
        stats: undefined,
      };

      renderWithRouter(<DetailPageLayout {...defaultProps} post={postWithoutStats} />);
      
      // 기본값이 표시되어야 함
      expect(screen.getByText('0')).toBeInTheDocument(); // view count 기본값
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Test Post Title');
    });

    it('has proper button roles', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('has proper aria labels for reaction buttons', () => {
      renderWithRouter(<DetailPageLayout {...defaultProps} />);
      
      const likeButton = screen.getByLabelText('좋아요');
      const dislikeButton = screen.getByLabelText('싫어요');
      const bookmarkButton = screen.getByLabelText('북마크');
      
      expect(likeButton).toBeInTheDocument();
      expect(dislikeButton).toBeInTheDocument();
      expect(bookmarkButton).toBeInTheDocument();
    });
  });
});