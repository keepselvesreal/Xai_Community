import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { expect, describe, it, vi } from 'vitest';
import { MemoryRouter } from '@remix-run/react';
import DetailPageLayout from './DetailPageLayout';
import type { Post, User, Comment } from '~/types';

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
};

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <MemoryRouter>
      {ui}
    </MemoryRouter>
  );
};

describe('DetailPageLayout - Final Tests', () => {
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
    
    expect(screen.getByText('댓글 1개')).toBeInTheDocument();
    expect(screen.getByText('Test comment')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithRouter(<DetailPageLayout {...defaultProps} isLoading={true} />);
    
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('shows author controls for author', () => {
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

  it('calls onReactionChange when reaction buttons are clicked', () => {
    const mockOnReactionChange = vi.fn();
    renderWithRouter(
      <DetailPageLayout 
        {...defaultProps} 
        onReactionChange={mockOnReactionChange}
      />
    );
    
    const likeButton = screen.getByLabelText('좋아요');
    fireEvent.click(likeButton);
    
    expect(mockOnReactionChange).toHaveBeenCalledWith('like');
  });

  it('calls onCommentAdded when comment button is clicked', () => {
    const mockOnCommentAdded = vi.fn();
    renderWithRouter(
      <DetailPageLayout 
        {...defaultProps} 
        onCommentAdded={mockOnCommentAdded}
      />
    );
    
    const commentButton = screen.getByText('작성');
    fireEvent.click(commentButton);
    
    expect(mockOnCommentAdded).toHaveBeenCalled();
  });

  it('renders custom sections correctly', () => {
    const beforeContentSection = <div data-testid="before-content">Before Content</div>;
    const afterContentSection = <div data-testid="after-content">After Content</div>;

    renderWithRouter(
      <DetailPageLayout 
        {...defaultProps}
        sections={{
          beforeContent: [beforeContentSection],
          afterContent: [afterContentSection],
        }}
      />
    );
    
    expect(screen.getByTestId('before-content')).toBeInTheDocument();
    expect(screen.getByTestId('after-content')).toBeInTheDocument();
  });
});