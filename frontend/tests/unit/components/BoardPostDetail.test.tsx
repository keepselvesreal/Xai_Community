/**
 * BoardPostDetail (board-post.$slug.tsx) 컴포넌트 단위 테스트
 * 수정 버튼 및 권한 체크 기능 테스트
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import { apiClient } from '~/lib/api';
import BoardPostDetail from '~/routes/board-post.$slug';
import { ThemeProvider } from '~/contexts/ThemeContext';

// Mock API client
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPost: vi.fn(),
    getComments: vi.fn(),
    likePost: vi.fn(),
    dislikePost: vi.fn(),
    bookmarkPost: vi.fn(),
    deletePost: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ slug: 'test-post-slug' }),
  };
});

// Mock contexts
vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: '507f1f77bcf86cd799439011',
      email: 'test@example.com',
      user_handle: 'test_user',
      name: 'Test User',
    },
    isAuthenticated: true,
    logout: vi.fn(),
  }),
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
  }),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('BoardPostDetail - 수정 버튼 기능 테스트', () => {
  const mockUser = {
    id: '507f1f77bcf86cd799439011',
    email: 'test@example.com',
    user_handle: 'test_user',
    name: 'Test User',
  };

  const mockPost = {
    id: 'test-post-id',
    title: '테스트 게시글',
    content: '테스트 내용입니다.',
    slug: 'test-post-slug',
    service: 'residential_community',
    type: 'board',
    metadata: {
      type: 'board',
      category: '입주정보',
      tags: ['태그1', '태그2']
    },
    author_id: '507f1f77bcf86cd799439011', // 같은 사용자
    author: mockUser,
    status: 'published',
    created_at: '2025-06-30T10:00:00Z',
    updated_at: '2025-06-30T10:00:00Z',
    published_at: '2025-06-30T10:00:00Z',
    view_count: 10,
    like_count: 5,
    dislike_count: 1,
    comment_count: 3,
    bookmark_count: 2,
    stats: {
      view_count: 10,
      like_count: 5,
      dislike_count: 1,
      comment_count: 3,
      bookmark_count: 2,
    }
  };

  const mockComments = {
    comments: [],
    total: 0,
    page: 1,
    page_size: 20,
    pages: 1
  };

  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={['/board-post/test-post-slug']}>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </MemoryRouter>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    
    // API 응답 설정
    vi.mocked(apiClient.getPost).mockResolvedValue({
      success: true,
      data: mockPost,
      timestamp: new Date().toISOString()
    });
    
    vi.mocked(apiClient.getComments).mockResolvedValue({
      success: true,
      data: mockComments,
      timestamp: new Date().toISOString()
    });
  });

  describe('작성자 권한 체크', () => {
    it('작성자인 경우 수정 버튼이 표시되어야 한다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      // 게시글이 로드될 때까지 대기
      await waitFor(() => {
        expect(screen.getAllByText('테스트 게시글')[0]).toBeInTheDocument();
      });

      // 수정 버튼이 있는지 확인
      await waitFor(() => {
        const editButton = screen.getByRole('button', { name: /수정/ });
        expect(editButton).toBeInTheDocument();
      });
    });

    it('작성자가 아닌 경우 수정 버튼이 표시되지 않아야 한다', async () => {
      // 다른 사용자의 게시글로 설정
      const otherUserPost = {
        ...mockPost,
        author_id: 'other-user-id',
        author: {
          id: 'other-user-id',
          email: 'other@example.com',
          user_handle: 'other_user',
          name: 'Other User',
        }
      };

      vi.mocked(apiClient.getPost).mockResolvedValue({
        success: true,
        data: otherUserPost,
        timestamp: new Date().toISOString()
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      // 게시글이 로드될 때까지 대기
      await waitFor(() => {
        expect(screen.getAllByText('테스트 게시글')[0]).toBeInTheDocument();
      });

      // 수정 버튼이 없는지 확인
      expect(screen.queryByRole('button', { name: /수정/ })).not.toBeInTheDocument();
    });
  });

  describe('수정 버튼 클릭', () => {
    it('수정 버튼 클릭 시 수정 페이지로 이동해야 한다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      // 게시글이 로드될 때까지 대기
      await waitFor(() => {
        expect(screen.getAllByText('테스트 게시글')[0]).toBeInTheDocument();
      });

      // 수정 버튼 클릭
      await waitFor(() => {
        const editButton = screen.getByRole('button', { name: /수정/ });
        fireEvent.click(editButton);
      });

      // navigate가 올바른 경로로 호출되었는지 확인
      expect(mockNavigate).toHaveBeenCalledWith('/posts/test-post-slug/edit');
    });
  });

  describe('삭제 버튼 기능', () => {
    it('작성자인 경우 삭제 버튼이 표시되어야 한다', async () => {
      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('테스트 게시글')[0]).toBeInTheDocument();
      });

      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /삭제/ });
        expect(deleteButton).toBeInTheDocument();
      });
    });

    it('삭제 버튼 클릭 시 확인 창이 표시되어야 한다', async () => {
      // confirm 모킹
      const mockConfirm = vi.fn().mockReturnValue(false);
      Object.defineProperty(window, 'confirm', {
        value: mockConfirm,
        writable: true,
      });

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('테스트 게시글')[0]).toBeInTheDocument();
      });

      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /삭제/ });
        fireEvent.click(deleteButton);
      });

      expect(mockConfirm).toHaveBeenCalledWith('정말로 삭제하시겠습니까?');
    });
  });

  describe('에러 처리', () => {
    it('게시글 로드 실패 시 에러 페이지를 표시해야 한다', async () => {
      vi.mocked(apiClient.getPost).mockRejectedValue(new Error('네트워크 오류'));

      render(
        <TestWrapper>
          <BoardPostDetail />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('게시글을 찾을 수 없습니다')).toBeInTheDocument();
      });
    });
  });
});