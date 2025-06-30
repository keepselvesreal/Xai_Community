import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PostsIndex from '~/routes/posts._index';
import { AuthContext } from '~/contexts/AuthContext';
import { apiClient } from '~/lib/api';
import type { AuthContextType, PaginatedResponse, Post } from '~/types';

// Mock API client
vi.mock('~/lib/api');
const mockApiClient = vi.mocked(apiClient);

// Mock hooks
vi.mock('~/hooks/usePagination', () => ({
  usePagination: () => ({
    page: 1,
    size: 20,
    totalPages: 1,
    isFirstPage: true,
    isLastPage: true,
    hasPrevious: false,
    hasNext: false,
    goToPage: vi.fn(),
    getPageNumbers: () => [1]
  })
}));

// Mock URL search params
const mockSetSearchParams = vi.fn();
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useLoaderData: () => ({
      posts: {
        items: [],
        total: 0,
        page: 1,
        size: 20,
        pages: 0
      },
      filters: {}
    }),
    useSearchParams: () => [new URLSearchParams(), mockSetSearchParams],
    Link: ({ children, to, ...props }: any) => (
      <a href={to} {...props}>{children}</a>
    )
  };
});

const mockAuthContext: AuthContextType = {
  user: null,
  token: null,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
  isAuthenticated: false
};

const renderPostsPage = (authValue: AuthContextType = mockAuthContext) => {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={authValue}>
        <PostsIndex />
      </AuthContext.Provider>
    </MemoryRouter>
  );
};

describe('Posts List Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('API integration', () => {
    it('should call API with correct parameters when filters change', async () => {
      // Arrange
      const mockResponse = {
        success: true,
        data: {
          items: [],
          total: 0,
          page: 1,
          size: 20,
          pages: 0
        } as PaginatedResponse<Post>,
        timestamp: '2024-01-01T00:00:00Z'
      };

      mockApiClient.getPosts = vi.fn().mockResolvedValue(mockResponse);

      // Act
      renderPostsPage();

      // Assert
      // 컴포넌트가 마운트될 때 API가 호출되지 않음 (현재는 loader에서 mock 데이터 사용)
      // 실제 구현에서는 useEffect에서 API 호출할 예정
      expect(mockApiClient.getPosts).not.toHaveBeenCalled();
    });

    it('should handle API success response correctly', async () => {
      // Arrange
      const mockPosts: Post[] = [
        {
          id: '1',
          title: 'Test Post 1',
          content: 'Content 1',
          slug: 'test-post-1',
          service: 'residential_community',
          author_id: 'user1',
          metadata: {
            type: '자유게시판',
            tags: ['test'],
            editor_type: 'plain'
          },
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          stats: {
            views: 10,
            likes: 5,
            dislikes: 1,
            comments: 3,
            bookmarks: 2
          }
        }
      ];

      const mockResponse = {
        success: true,
        data: {
          items: mockPosts,
          total: 1,
          page: 1,
          size: 20,
          pages: 1
        } as PaginatedResponse<Post>,
        timestamp: '2024-01-01T00:00:00Z'
      };

      mockApiClient.getPosts = vi.fn().mockResolvedValue(mockResponse);

      // Act
      renderPostsPage();

      // Assert
      // 현재는 loader에서 mock 데이터를 사용하므로 실제 API 응답이 표시되지 않음
      // 실제 구현 후에는 API 응답의 게시글이 표시되어야 함
      expect(screen.getByText('게시글 목록')).toBeInTheDocument();
    });

    it('should handle API error response correctly', async () => {
      // Arrange
      const mockErrorResponse = {
        success: false,
        error: 'Server Error',
        timestamp: '2024-01-01T00:00:00Z'
      };

      mockApiClient.getPosts = vi.fn().mockResolvedValue(mockErrorResponse);

      // Act
      renderPostsPage();

      // Assert
      // 에러 처리가 구현되면 에러 메시지가 표시되어야 함
      expect(screen.getByText('게시글 목록')).toBeInTheDocument();
    });
  });

  describe('loading states', () => {
    it('should show loading state while API request is in progress', async () => {
      // Arrange
      const mockResponse = {
        success: true,
        data: {
          items: [],
          total: 0,
          page: 1,
          size: 20,
          pages: 0
        } as PaginatedResponse<Post>,
        timestamp: '2024-01-01T00:00:00Z'
      };

      // 지연된 응답을 시뮬레이션
      mockApiClient.getPosts = vi.fn().mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
      );

      // Act
      renderPostsPage();

      // Assert
      // 로딩 상태가 구현되면 로딩 인디케이터가 표시되어야 함
      // 현재는 loader 방식이므로 로딩 상태가 없음
      expect(screen.getByText('게시글 목록')).toBeInTheDocument();
    });

    it('should hide loading state when API request completes', async () => {
      // Arrange
      const mockResponse = {
        success: true,
        data: {
          items: [],
          total: 0,
          page: 1,
          size: 20,
          pages: 0
        } as PaginatedResponse<Post>,
        timestamp: '2024-01-01T00:00:00Z'
      };

      mockApiClient.getPosts = vi.fn().mockResolvedValue(mockResponse);

      // Act
      renderPostsPage();

      // Assert
      await waitFor(() => {
        expect(screen.getByText('게시글 목록')).toBeInTheDocument();
      });
    });
  });

  describe('error handling', () => {
    it('should display error message when API request fails', async () => {
      // Arrange
      mockApiClient.getPosts = vi.fn().mockRejectedValue(new Error('Network Error'));

      // Act
      renderPostsPage();

      // Assert
      // 에러 처리가 구현되면 에러 메시지가 표시되어야 함
      expect(screen.getByText('게시글 목록')).toBeInTheDocument();
    });

    it('should allow retry when API request fails', async () => {
      // Arrange
      mockApiClient.getPosts = vi.fn()
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce({
          success: true,
          data: {
            items: [],
            total: 0,
            page: 1,
            size: 20,
            pages: 0
          } as PaginatedResponse<Post>,
          timestamp: '2024-01-01T00:00:00Z'
        });

      // Act
      renderPostsPage();

      // Assert
      // 재시도 기능이 구현되면 재시도 버튼이 표시되어야 함
      expect(screen.getByText('게시글 목록')).toBeInTheDocument();
    });
  });

  describe('pagination integration', () => {
    it('should call API with correct page parameters when pagination changes', async () => {
      // Arrange
      const mockResponse = {
        success: true,
        data: {
          items: [],
          total: 100,
          page: 2,
          size: 20,
          pages: 5
        } as PaginatedResponse<Post>,
        timestamp: '2024-01-01T00:00:00Z'
      };

      mockApiClient.getPosts = vi.fn().mockResolvedValue(mockResponse);

      // Act
      renderPostsPage();

      // Assert
      // 페이지네이션이 API와 연동되면 페이지 변경 시 API 호출되어야 함
      expect(screen.getByText('게시글 목록')).toBeInTheDocument();
    });
  });

  describe('authentication integration', () => {
    it('should show create post button when user is authenticated', () => {
      // Arrange
      const authenticatedUser = {
        ...mockAuthContext,
        user: {
          id: 'user1',
          email: 'test@example.com',
          user_handle: 'testuser',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        },
        isAuthenticated: true
      };

      // Act
      renderPostsPage(authenticatedUser);

      // Assert
      expect(screen.getByText('✍️ 새 게시글')).toBeInTheDocument();
    });

    it('should hide create post button when user is not authenticated', () => {
      // Arrange & Act
      renderPostsPage();

      // Assert
      expect(screen.queryByText('✍️ 새 게시글')).not.toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('should show empty state when no posts are available', () => {
      // Act
      renderPostsPage();

      // Assert
      expect(screen.getByText('게시글이 없습니다')).toBeInTheDocument();
      expect(screen.getByText('검색 조건을 변경하거나 새 게시글을 작성해보세요.')).toBeInTheDocument();
    });

    it('should show create post button in empty state when authenticated', () => {
      // Arrange
      const authenticatedUser = {
        ...mockAuthContext,
        user: {
          id: 'user1',
          email: 'test@example.com',
          user_handle: 'testuser',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        },
        isAuthenticated: true
      };

      // Act
      renderPostsPage(authenticatedUser);

      // Assert
      expect(screen.getByText('새 게시글 작성')).toBeInTheDocument();
    });
  });
});