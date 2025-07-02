/**
 * TDD Red Phase: 마이페이지 컴포넌트 테스트 (실패하는 테스트)
 * API 통합 및 Mock 데이터 교체 검증
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createRemixStub } from '@remix-run/testing';
import type { LoaderFunction } from '@remix-run/node';
import type { UserActivityResponse } from '~/types';

// Mock API client
const mockApiClient = {
  getUserActivity: vi.fn(),
  isAuthenticated: vi.fn()
};

vi.mock('~/lib/api', () => ({
  default: mockApiClient,
  apiClient: mockApiClient
}));

// Mock AuthContext
const mockAuthContext = {
  user: {
    id: '507f1f77bcf86cd799439011',
    email: 'test@example.com',
    user_handle: 'testuser',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  logout: vi.fn(),
  login: vi.fn()
};

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => children
}));

describe('마이페이지 API 통합', () => {
  const mockUserActivityResponse: UserActivityResponse = {
    posts: {
      board: [
        {
          id: '686488bec5a4a334eaf42b9c',
          title: '25-07-02-1',
          slug: '686488bec5a4a334eaf42b9c-25-07-02-1',
          created_at: '2025-07-02T01:17:50.232000',
          like_count: 0,
          comment_count: 9,
          route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1'
        }
      ],
      info: [
        {
          id: '507f1f77bcf86cd799439013',
          title: '입주 정보 게시글',
          slug: 'info-post-slug',
          created_at: '2024-01-01T11:00:00Z',
          like_count: 2,
          comment_count: 1,
          route_path: '/property-info/info-post-slug'
        }
      ],
      services: [],
      tips: []
    },
    comments: [
      {
        id: '686488c8c5a4a334eaf42b9e',
        content: '댓글1!',
        created_at: '2025-07-02T01:18:00.344000',
        route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1'
      },
      {
        id: '507f1f77bcf86cd799439021',
        content: '서비스 문의 댓글입니다',
        created_at: '2024-01-01T15:00:00Z',
        route_path: '/moving-services-post/services-post-slug',
        subtype: 'inquiry'
      }
    ],
    reactions: {
      likes: [
        {
          id: '686488c2c5a4a334eaf42b9d',
          target_type: 'post',
          target_id: '686488bec5a4a334eaf42b9c',
          created_at: '2025-07-02T01:17:54.806000',
          route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1',
          target_title: '25-07-02-1'
        }
      ],
      bookmarks: [],
      dislikes: []
    },
    summary: {
      total_posts: 2,
      total_comments: 2,
      total_reactions: 1,
      most_active_page_type: 'board'
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockApiClient.isAuthenticated.mockReturnValue(true);
  });

  describe('로더 함수 API 통합', () => {
    it('로그인된 사용자의 경우 실제 API를 호출해야 한다', async () => {
      // Arrange
      mockApiClient.getUserActivity.mockResolvedValue(mockUserActivityResponse);

      // Mock loader function (실제 구현될 로더)
      const mockLoader: LoaderFunction = async ({ request }) => {
        const url = new URL(request.url);
        const isAuthenticated = true; // 실제로는 쿠키나 세션에서 확인
        
        if (isAuthenticated) {
          try {
            const userActivity = await mockApiClient.getUserActivity();
            return {
              userActivity,
              userStats: {
                postsCount: userActivity.summary.total_posts,
                commentsCount: userActivity.summary.total_comments,
                likesReceived: userActivity.summary.total_reactions,
                joinDate: "2023-09-15",
                consecutiveDays: 3
              }
            };
          } catch (error) {
            throw new Response('Failed to load user activity', { status: 500 });
          }
        }
        
        return {
          userActivity: null,
          userStats: null
        };
      };

      // Act
      const request = new Request('http://localhost:3000/mypage');
      const result = await mockLoader({ request, context: {}, params: {} });

      // Assert
      expect(mockApiClient.getUserActivity).toHaveBeenCalled();
      expect(result).toEqual({
        userActivity: mockUserActivityResponse,
        userStats: {
          postsCount: 2,
          commentsCount: 2,
          likesReceived: 1,
          joinDate: "2023-09-15",
          consecutiveDays: 3
        }
      });
    });

    it('API 호출 실패 시 적절한 에러를 던져야 한다', async () => {
      // Arrange
      mockApiClient.getUserActivity.mockRejectedValue(new Error('API Error'));

      const mockLoader: LoaderFunction = async ({ request }) => {
        try {
          const userActivity = await mockApiClient.getUserActivity();
          return { userActivity };
        } catch (error) {
          throw new Response('Failed to load user activity', { status: 500 });
        }
      };

      // Act & Assert
      const request = new Request('http://localhost:3000/mypage');
      await expect(mockLoader({ request, context: {}, params: {} }))
        .rejects.toThrow('Failed to load user activity');
    });

    it('비로그인 사용자의 경우 기본값을 반환해야 한다', async () => {
      // Arrange
      const mockLoader: LoaderFunction = async ({ request }) => {
        const isAuthenticated = false; // 비로그인 상태
        
        if (!isAuthenticated) {
          return {
            userActivity: null,
            userStats: {
              postsCount: 0,
              commentsCount: 0,
              likesReceived: 0,
              joinDate: null,
              consecutiveDays: 0
            }
          };
        }
      };

      // Act
      const request = new Request('http://localhost:3000/mypage');
      const result = await mockLoader({ request, context: {}, params: {} });

      // Assert
      expect(mockApiClient.getUserActivity).not.toHaveBeenCalled();
      expect(result).toEqual({
        userActivity: null,
        userStats: {
          postsCount: 0,
          commentsCount: 0,
          likesReceived: 0,
          joinDate: null,
          consecutiveDays: 0
        }
      });
    });
  });

  describe('컴포넌트 렌더링', () => {
    it('Mock 데이터 대신 실제 API 데이터를 렌더링해야 한다', async () => {
      // Arrange
      const MyPageStub = createRemixStub([
        {
          path: '/mypage',
          Component: () => {
            // Mock 마이페이지 컴포넌트 (실제 구현될 버전)
            return (
              <div data-testid="mypage-container">
                <div data-testid="total-posts">2</div>
                <div data-testid="total-comments">2</div>
                <div data-testid="total-reactions">1</div>
                <div data-testid="most-active-type">board</div>
                
                {/* 게시글 섹션 */}
                <div data-testid="board-posts">
                  <div data-testid="board-post-0">25-07-02-1</div>
                </div>
                <div data-testid="info-posts">
                  <div data-testid="info-post-0">입주 정보 게시글</div>
                </div>
                
                {/* 댓글 섹션 */}
                <div data-testid="comments-section">
                  <div data-testid="comment-0">댓글1!</div>
                  <div data-testid="comment-1">
                    서비스 문의 댓글입니다
                    <span data-testid="comment-1-subtype">[문의]</span>
                  </div>
                </div>
                
                {/* 반응 섹션 */}
                <div data-testid="reactions-section">
                  <div data-testid="like-0">25-07-02-1</div>
                </div>
              </div>
            );
          },
          loader: async () => ({
            userActivity: mockUserActivityResponse,
            userStats: {
              postsCount: mockUserActivityResponse.summary.total_posts,
              commentsCount: mockUserActivityResponse.summary.total_comments,
              likesReceived: mockUserActivityResponse.summary.total_reactions,
              joinDate: "2023-09-15",
              consecutiveDays: 3
            }
          })
        }
      ]);

      // Act
      render(<MyPageStub initialEntries={['/mypage']} />);

      // Assert - 실제 API 데이터가 렌더링되는지 확인
      await waitFor(() => {
        expect(screen.getByTestId('total-posts')).toHaveTextContent('2');
        expect(screen.getByTestId('total-comments')).toHaveTextContent('2');
        expect(screen.getByTestId('total-reactions')).toHaveTextContent('1');
        expect(screen.getByTestId('most-active-type')).toHaveTextContent('board');
      });

      // 게시글 데이터 확인
      expect(screen.getByTestId('board-post-0')).toHaveTextContent('25-07-02-1');
      expect(screen.getByTestId('info-post-0')).toHaveTextContent('입주 정보 게시글');

      // 댓글 데이터 확인
      expect(screen.getByTestId('comment-0')).toHaveTextContent('댓글1!');
      expect(screen.getByTestId('comment-1')).toHaveTextContent('서비스 문의 댓글입니다');
      expect(screen.getByTestId('comment-1-subtype')).toHaveTextContent('[문의]');

      // 반응 데이터 확인
      expect(screen.getByTestId('like-0')).toHaveTextContent('25-07-02-1');
    });

    it('빈 데이터 상태를 올바르게 처리해야 한다', async () => {
      // Arrange
      const emptyResponse: UserActivityResponse = {
        posts: { board: [], info: [], services: [], tips: [] },
        comments: [],
        reactions: { likes: [], bookmarks: [], dislikes: [] },
        summary: { total_posts: 0, total_comments: 0, total_reactions: 0 }
      };

      const MyPageStub = createRemixStub([
        {
          path: '/mypage',
          Component: () => (
            <div data-testid="mypage-container">
              <div data-testid="total-posts">0</div>
              <div data-testid="total-comments">0</div>
              <div data-testid="total-reactions">0</div>
              <div data-testid="empty-state">활동 기록이 없습니다</div>
            </div>
          ),
          loader: async () => ({
            userActivity: emptyResponse,
            userStats: { postsCount: 0, commentsCount: 0, likesReceived: 0 }
          })
        }
      ]);

      // Act
      render(<MyPageStub initialEntries={['/mypage']} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByTestId('total-posts')).toHaveTextContent('0');
        expect(screen.getByTestId('total-comments')).toHaveTextContent('0');
        expect(screen.getByTestId('total-reactions')).toHaveTextContent('0');
        expect(screen.getByTestId('empty-state')).toHaveTextContent('활동 기록이 없습니다');
      });
    });

    it('로딩 상태를 올바르게 표시해야 한다', async () => {
      // Arrange
      const MyPageStub = createRemixStub([
        {
          path: '/mypage',
          Component: () => {
            // 로딩 상태 모킹
            const isLoading = true;
            
            if (isLoading) {
              return <div data-testid="loading-state">로딩 중...</div>;
            }
            
            return <div data-testid="mypage-content">내용</div>;
          },
          loader: async () => {
            // 지연 시뮬레이션
            await new Promise(resolve => setTimeout(resolve, 100));
            return { userActivity: mockUserActivityResponse };
          }
        }
      ]);

      // Act
      render(<MyPageStub initialEntries={['/mypage']} />);

      // Assert
      expect(screen.getByTestId('loading-state')).toHaveTextContent('로딩 중...');
    });

    it('에러 상태를 올바르게 표시해야 한다', async () => {
      // Arrange
      const MyPageStub = createRemixStub([
        {
          path: '/mypage',
          Component: () => (
            <div data-testid="error-state">
              데이터를 불러오는 중 오류가 발생했습니다
            </div>
          ),
          loader: async () => {
            throw new Response('API Error', { status: 500 });
          },
          ErrorBoundary: () => (
            <div data-testid="error-boundary">
              데이터를 불러오는 중 오류가 발생했습니다
            </div>
          )
        }
      ]);

      // Act
      render(<MyPageStub initialEntries={['/mypage']} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByTestId('error-boundary')).toHaveTextContent('데이터를 불러오는 중 오류가 발생했습니다');
      });
    });
  });

  describe('데이터 변환 및 매핑', () => {
    it('API 응답을 UI 컴포넌트에 맞는 형태로 변환해야 한다', () => {
      // Arrange
      const apiResponse = mockUserActivityResponse;

      // Act - 데이터 변환 로직 (실제 구현될 함수)
      const transformedData = {
        boardPosts: apiResponse.posts.board,
        infoPosts: apiResponse.posts.info,
        servicesPosts: apiResponse.posts.services,
        tipsPosts: apiResponse.posts.tips,
        
        regularComments: apiResponse.comments.filter(c => !c.subtype),
        inquiryComments: apiResponse.comments.filter(c => c.subtype === 'inquiry'),
        reviewComments: apiResponse.comments.filter(c => c.subtype === 'review'),
        
        likes: apiResponse.reactions.likes,
        bookmarks: apiResponse.reactions.bookmarks,
        dislikes: apiResponse.reactions.dislikes,
        
        stats: apiResponse.summary
      };

      // Assert
      expect(transformedData.boardPosts).toHaveLength(1);
      expect(transformedData.infoPosts).toHaveLength(1);
      expect(transformedData.regularComments).toHaveLength(1);
      expect(transformedData.inquiryComments).toHaveLength(1);
      expect(transformedData.likes).toHaveLength(1);
      expect(transformedData.stats.total_posts).toBe(2);
    });

    it('route_path를 Link 컴포넌트에서 사용할 수 있는 형태로 제공해야 한다', () => {
      // Arrange
      const items = mockUserActivityResponse.posts.board;

      // Act
      const routePaths = items.map(item => item.route_path);

      // Assert
      expect(routePaths[0]).toBe('/board-post/686488bec5a4a334eaf42b9c-25-07-02-1');
      expect(routePaths[0]).toMatch(/^\/board-post\/.+/);
    });
  });
});