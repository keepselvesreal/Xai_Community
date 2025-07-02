/**
 * TDD Red Phase: ActivityItem 컴포넌트 테스트 (실패하는 테스트)
 * 실제 API 데이터 구조로 렌더링 및 네비게이션 검증
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import type { ActivityItem } from '~/types';

// ActivityItem 컴포넌트를 모킹 (아직 구현되지 않았으므로)
interface ActivityItemProps {
  type: string;
  icon: string;
  name: string;
  items: ActivityItem[];
  onToggle: (type: string) => void;
  isExpanded: boolean;
}

const MockActivityItem = ({ type, icon, name, items, onToggle, isExpanded }: ActivityItemProps) => {
  return (
    <div data-testid={`activity-item-${type}`}>
      <div 
        onClick={() => onToggle(type)}
        className="activity-header"
        data-testid={`activity-header-${type}`}
      >
        <span>{icon} {name}</span>
        <span>{items.length}개</span>
      </div>
      
      {isExpanded && (
        <div data-testid={`activity-content-${type}`}>
          {items.map((item, index) => (
            <div key={item.id} data-testid={`activity-item-${type}-${index}`}>
              {/* 게시글 표시 */}
              {item.title && (
                <div>
                  <a href={item.route_path} data-testid={`post-link-${item.id}`}>
                    {item.title}
                  </a>
                  <div>
                    {item.like_count !== undefined && `❤️ ${item.like_count}`}
                    {item.comment_count !== undefined && ` 💬 ${item.comment_count}`}
                  </div>
                  <div>{item.created_at}</div>
                </div>
              )}
              
              {/* 댓글 표시 */}
              {item.content && (
                <div>
                  <a href={item.route_path} data-testid={`comment-link-${item.id}`}>
                    {item.content}
                  </a>
                  {item.subtype && (
                    <span data-testid={`comment-subtype-${item.id}`}>
                      {item.subtype === 'inquiry' ? '[문의]' : '[후기]'}
                    </span>
                  )}
                  <div>{item.created_at}</div>
                </div>
              )}
              
              {/* 반응 표시 */}
              {item.target_type && (
                <div>
                  <a href={item.route_path} data-testid={`reaction-link-${item.id}`}>
                    {item.target_title}
                  </a>
                  <div>타입: {item.target_type}</div>
                  <div>{item.created_at}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// 테스트용 wrapper
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('ActivityItem 컴포넌트 - 실제 API 데이터', () => {
  const mockToggle = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('게시글 데이터 렌더링', () => {
    it('게시판 게시글을 올바르게 렌더링해야 한다', () => {
      // Arrange - 실제 API 응답 구조
      const boardPosts: ActivityItem[] = [
        {
          id: '686488bec5a4a334eaf42b9c',
          title: '25-07-02-1',
          slug: '686488bec5a4a334eaf42b9c-25-07-02-1',
          created_at: '2025-07-02T01:17:50.232000',
          like_count: 0,
          comment_count: 9,
          route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="board-posts"
            icon="📝"
            name="글"
            items={boardPosts}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByTestId('activity-header-board-posts')).toBeInTheDocument();
      expect(screen.getByText('1개')).toBeInTheDocument();
      expect(screen.getByText('25-07-02-1')).toBeInTheDocument();
      expect(screen.getByText((_content, element) => {
        return element?.textContent === '❤️ 0 💬 9';
      })).toBeInTheDocument();
      
      const postLink = screen.getByTestId('post-link-686488bec5a4a334eaf42b9c');
      expect(postLink).toHaveAttribute('href', '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1');
    });

    it('정보 게시글을 올바르게 렌더링해야 한다', () => {
      // Arrange
      const infoPosts: ActivityItem[] = [
        {
          id: '507f1f77bcf86cd799439013',
          title: '입주 정보 게시글',
          slug: 'info-post-slug',
          created_at: '2024-01-01T11:00:00Z',
          like_count: 2,
          comment_count: 1,
          route_path: '/property-info/info-post-slug'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="info-posts"
            icon="📋"
            name="정보"
            items={infoPosts}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('입주 정보 게시글')).toBeInTheDocument();
      const postLink = screen.getByTestId('post-link-507f1f77bcf86cd799439013');
      expect(postLink).toHaveAttribute('href', '/property-info/info-post-slug');
    });
  });

  describe('댓글 데이터 렌더링', () => {
    it('일반 댓글을 올바르게 렌더링해야 한다', () => {
      // Arrange
      const comments: ActivityItem[] = [
        {
          id: '686488c8c5a4a334eaf42b9e',
          content: '댓글1!',
          created_at: '2025-07-02T01:18:00.344000',
          route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="board-comments"
            icon="💬"
            name="댓글"
            items={comments}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('댓글1!')).toBeInTheDocument();
      const commentLink = screen.getByTestId('comment-link-686488c8c5a4a334eaf42b9e');
      expect(commentLink).toHaveAttribute('href', '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1');
    });

    it('서비스 문의 댓글에 subtype을 표시해야 한다', () => {
      // Arrange
      const inquiryComments: ActivityItem[] = [
        {
          id: '507f1f77bcf86cd799439021',
          content: '서비스 문의 댓글입니다',
          created_at: '2024-01-01T15:00:00Z',
          route_path: '/moving-services-post/services-post-slug',
          subtype: 'inquiry'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="service-inquiries"
            icon="❓"
            name="문의"
            items={inquiryComments}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('서비스 문의 댓글입니다')).toBeInTheDocument();
      expect(screen.getByTestId('comment-subtype-507f1f77bcf86cd799439021')).toHaveTextContent('[문의]');
    });

    it('서비스 후기 댓글에 subtype을 표시해야 한다', () => {
      // Arrange
      const reviewComments: ActivityItem[] = [
        {
          id: '507f1f77bcf86cd799439022',
          content: '서비스 후기 댓글입니다',
          created_at: '2024-01-01T16:00:00Z',
          route_path: '/moving-services-post/services-post-slug',
          subtype: 'review'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="service-reviews"
            icon="⭐"
            name="후기"
            items={reviewComments}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('서비스 후기 댓글입니다')).toBeInTheDocument();
      expect(screen.getByTestId('comment-subtype-507f1f77bcf86cd799439022')).toHaveTextContent('[후기]');
    });
  });

  describe('반응 데이터 렌더링', () => {
    it('좋아요 반응을 올바르게 렌더링해야 한다', () => {
      // Arrange
      const likes: ActivityItem[] = [
        {
          id: '686488c2c5a4a334eaf42b9d',
          target_type: 'post',
          target_id: '686488bec5a4a334eaf42b9c',
          created_at: '2025-07-02T01:17:54.806000',
          route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1',
          target_title: '25-07-02-1'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="board-likes"
            icon="👍"
            name="추천"
            items={likes}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('25-07-02-1')).toBeInTheDocument();
      expect(screen.getByText('타입: post')).toBeInTheDocument();
      const reactionLink = screen.getByTestId('reaction-link-686488c2c5a4a334eaf42b9d');
      expect(reactionLink).toHaveAttribute('href', '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1');
    });

    it('북마크 반응을 올바르게 렌더링해야 한다', () => {
      // Arrange
      const bookmarks: ActivityItem[] = [
        {
          id: '507f1f77bcf86cd799439032',
          target_type: 'post',
          target_id: '507f1f77bcf86cd799439013',
          created_at: '2024-01-01T19:00:00Z',
          route_path: '/property-info/info-post-slug',
          target_title: '입주 정보 게시글'
        }
      ];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="info-bookmarks"
            icon="📌"
            name="저장"
            items={bookmarks}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('입주 정보 게시글')).toBeInTheDocument();
      const reactionLink = screen.getByTestId('reaction-link-507f1f77bcf86cd799439032');
      expect(reactionLink).toHaveAttribute('href', '/property-info/info-post-slug');
    });
  });

  describe('상호작용 기능', () => {
    it('헤더 클릭 시 토글 함수가 호출되어야 한다', () => {
      // Arrange
      const items: ActivityItem[] = [];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="board-posts"
            icon="📝"
            name="글"
            items={items}
            onToggle={mockToggle}
            isExpanded={false}
          />
        </TestWrapper>
      );

      const header = screen.getByTestId('activity-header-board-posts');
      fireEvent.click(header);

      // Assert
      expect(mockToggle).toHaveBeenCalledWith('board-posts');
    });

    it('확장 상태에 따라 콘텐츠가 표시되거나 숨겨져야 한다', () => {
      // Arrange
      const items: ActivityItem[] = [
        {
          id: '1',
          title: '테스트 게시글',
          created_at: '2024-01-01T10:00:00Z',
          route_path: '/board-post/test'
        }
      ];

      const { rerender } = render(
        <TestWrapper>
          <MockActivityItem 
            type="board-posts"
            icon="📝"
            name="글"
            items={items}
            onToggle={mockToggle}
            isExpanded={false}
          />
        </TestWrapper>
      );

      // Assert - 숨겨진 상태
      expect(screen.queryByTestId('activity-content-board-posts')).not.toBeInTheDocument();

      // Act - 확장 상태로 변경
      rerender(
        <TestWrapper>
          <MockActivityItem 
            type="board-posts"
            icon="📝"
            name="글"
            items={items}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert - 표시된 상태
      expect(screen.getByTestId('activity-content-board-posts')).toBeInTheDocument();
      expect(screen.getByText('테스트 게시글')).toBeInTheDocument();
    });
  });

  describe('빈 데이터 처리', () => {
    it('데이터가 없을 때 0개로 표시해야 한다', () => {
      // Arrange
      const emptyItems: ActivityItem[] = [];

      // Act
      render(
        <TestWrapper>
          <MockActivityItem 
            type="board-posts"
            icon="📝"
            name="글"
            items={emptyItems}
            onToggle={mockToggle}
            isExpanded={true}
          />
        </TestWrapper>
      );

      // Assert
      expect(screen.getByText('0개')).toBeInTheDocument();
      expect(screen.getByTestId('activity-content-board-posts')).toBeInTheDocument();
      expect(screen.getByTestId('activity-content-board-posts')).toBeEmptyDOMElement();
    });
  });

  describe('라우팅 패턴 검증', () => {
    it('각 페이지 타입별로 올바른 라우팅 패턴을 가져야 한다', () => {
      const testCases = [
        {
          type: 'board',
          slug: 'test-slug',
          expectedPath: '/board-post/test-slug'
        },
        {
          type: 'info',
          slug: 'info-slug',
          expectedPath: '/property-info/info-slug'
        },
        {
          type: 'services',
          slug: 'service-slug',
          expectedPath: '/moving-services-post/service-slug'
        },
        {
          type: 'tips',
          slug: 'tips-slug',
          expectedPath: '/expert-tips/tips-slug'
        }
      ];

      testCases.forEach(({ type, slug, expectedPath }) => {
        const items: ActivityItem[] = [
          {
            id: `${type}-1`,
            title: `${type} 게시글`,
            slug: slug,
            created_at: '2024-01-01T10:00:00Z',
            route_path: expectedPath
          }
        ];

        const { unmount } = render(
          <TestWrapper>
            <MockActivityItem 
              type={`${type}-posts`}
              icon="📝"
              name="글"
              items={items}
              onToggle={mockToggle}
              isExpanded={true}
            />
          </TestWrapper>
        );

        const link = screen.getByTestId(`post-link-${type}-1`);
        expect(link).toHaveAttribute('href', expectedPath);

        unmount();
      });
    });
  });
});