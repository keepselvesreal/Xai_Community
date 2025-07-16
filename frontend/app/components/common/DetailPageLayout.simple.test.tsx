import { render, screen } from '@testing-library/react';
import { expect, describe, it, vi } from 'vitest';
import { MemoryRouter } from '@remix-run/react';
import DetailPageLayout from './DetailPageLayout';
import type { Post, Comment } from '~/types';

// Mock CommentSection 컴포넌트
vi.mock('~/components/comment/CommentSection', () => ({
  default: ({ postSlug, comments }: { postSlug: string; comments: Comment[] }) => (
    <div data-testid="comment-section">
      <h3>댓글 {comments.length}개</h3>
      <div>Post: {postSlug}</div>
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

const defaultProps = {
  post: mockPost,
  comments: mockComments,
  onReactionChange: vi.fn(),
  onCommentAdded: vi.fn(),
};

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter>
      {ui}
    </MemoryRouter>
  );
};

describe('DetailPageLayout - Simple Tests', () => {
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

  it('renders tags', () => {
    renderWithRouter(<DetailPageLayout {...defaultProps} />);
    
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });

  it('renders comment section', () => {
    renderWithRouter(<DetailPageLayout {...defaultProps} />);
    
    expect(screen.getByTestId('comment-section')).toBeInTheDocument();
    expect(screen.getByText('댓글 1개')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithRouter(<DetailPageLayout {...defaultProps} isLoading={true} />);
    
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });
});