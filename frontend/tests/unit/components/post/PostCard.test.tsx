import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PostCard from '~/components/post/PostCard';
import type { Post } from '~/types';

// PostCard 컴포넌트를 wrapping하는 유틸리티 함수
const renderPostCard = (post: Post) => {
  return render(
    <MemoryRouter>
      <PostCard post={post} />
    </MemoryRouter>
  );
};

describe('PostCard Component', () => {
  describe('author field processing', () => {
    it('should display author display_name when available', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        author: {
          id: 'user1',
          email: 'test@example.com',
          user_handle: 'testuser',
          display_name: 'Test User Display',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        },
        metadata: {
          type: '자유게시판',
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      expect(screen.getByText(/작성자: Test User Display/)).toBeInTheDocument();
    });

    it('should display author user_handle when display_name is not available', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        author: {
          id: 'user1',
          email: 'test@example.com',
          user_handle: 'testhandle',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        },
        metadata: {
          type: '자유게시판',
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      expect(screen.getByText(/작성자: testhandle/)).toBeInTheDocument();
    });

    it('should display "익명" when author information is not available', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '자유게시판',
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      expect(screen.getByText(/작성자: 익명/)).toBeInTheDocument();
    });

    it('should handle author_id based display when only author_id is available', () => {
      // Arrange - 백엔드 API 응답 구조 (author_id만 있는 경우)
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        author_id: 'user123',
        metadata: {
          type: '자유게시판',
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      // author_id만 있는 경우 user123 또는 적절한 fallback이 표시되어야 함
      expect(screen.getByText(/작성자: user123|익명/)).toBeInTheDocument();
    });
  });

  describe('metadata.tags access', () => {
    it('should display tags from metadata.tags', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '자유게시판',
          tags: ['React', 'TypeScript', 'API'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      expect(screen.getByText('#React')).toBeInTheDocument();
      expect(screen.getByText('#TypeScript')).toBeInTheDocument();
      expect(screen.getByText('#API')).toBeInTheDocument();
    });

    it('should limit tags display to 3 tags max', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '자유게시판',
          tags: ['Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      expect(screen.getByText('#Tag1')).toBeInTheDocument();
      expect(screen.getByText('#Tag2')).toBeInTheDocument();
      expect(screen.getByText('#Tag3')).toBeInTheDocument();
      expect(screen.getByText('+2 more')).toBeInTheDocument();
    });

    it('should not display tags section when no tags are available', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '자유게시판',
          tags: [],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      const tagElements = screen.queryAllByText(/^#/);
      expect(tagElements).toHaveLength(0);
    });
  });

  describe('metadata.type access', () => {
    it('should display type from metadata.type', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '질문답변',
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      expect(screen.getByText('질문답변')).toBeInTheDocument();
    });

    it('should handle missing metadata.type gracefully', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      // 컴포넌트가 에러 없이 렌더링되어야 함
      expect(screen.getByText('Test Post')).toBeInTheDocument();
    });
  });

  describe('post stats display', () => {
    it('should display stats with proper formatting', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '자유게시판',
          tags: ['test'],
          editor_type: 'plain'
        },
        stats: {
          views: 1234,
          likes: 56,
          dislikes: 3,
          comments: 12,
          bookmarks: 8
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      // 통계 정보가 올바르게 표시되는지 확인
      expect(screen.getByText('1.2K')).toBeInTheDocument(); // views formatted
      expect(screen.getByText('56')).toBeInTheDocument(); // likes
      expect(screen.getByText('3')).toBeInTheDocument(); // dislikes
      expect(screen.getByText('12')).toBeInTheDocument(); // comments
      expect(screen.getByText('8')).toBeInTheDocument(); // bookmarks
    });

    it('should handle missing stats gracefully', () => {
      // Arrange
      const post: Post = {
        id: '1',
        title: 'Test Post',
        content: 'Test content',
        slug: 'test-post',
        service: 'residential_community',
        metadata: {
          type: '자유게시판',
          tags: ['test'],
          editor_type: 'plain'
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      // Act
      renderPostCard(post);

      // Assert
      // 0 값들이 표시되어야 함
      expect(screen.getAllByText('0')).toHaveLength(5); // views, likes, dislikes, comments, bookmarks 모두 0
    });
  });
});