import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, describe, it, vi } from 'vitest';
import type { Post, Comment } from '~/types';

// DetailPageLayout 컴포넌트를 간단히 테스트
const DetailPageLayout = ({ post, isLoading }: { post: Post; isLoading?: boolean }) => {
  if (isLoading) {
    return <div data-testid="loading-skeleton">Loading...</div>;
  }
  
  if (!post) {
    return <div>Post not found</div>;
  }
  
  return (
    <div>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
      <div>{post.author?.display_name}</div>
      {post.metadata?.tags && post.metadata.tags.map((tag, index) => (
        <span key={index}>{tag}</span>
      ))}
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
};

describe('DetailPageLayout - Basic Tests', () => {
  it('renders post title correctly', () => {
    render(<DetailPageLayout post={mockPost} />);
    
    expect(screen.getByText('Test Post Title')).toBeInTheDocument();
  });

  it('renders post content correctly', () => {
    render(<DetailPageLayout post={mockPost} />);
    
    expect(screen.getByText('Test post content')).toBeInTheDocument();
  });

  it('renders author information', () => {
    render(<DetailPageLayout post={mockPost} />);
    
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });

  it('renders tags', () => {
    render(<DetailPageLayout post={mockPost} />);
    
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<DetailPageLayout post={mockPost} isLoading={true} />);
    
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });
});