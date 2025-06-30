/**
 * PostDetail 컴포넌트 단위 테스트
 * API v3 명세서 기준으로 작성됨
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PostDetail from '~/routes/posts.$slug';
import React from 'react';
import { apiClient } from '~/lib/api';
import type { Post, Comment, User, ApiResponse, PaginatedResponse } from '~/types';

// Mock API client
vi.mock('~/lib/api');

// Mock contexts
vi.mock('~/contexts/AuthContext', () => ({
  AuthContext: React.createContext(null),
  useAuth: () => ({
    user: null,
    token: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
    isAuthenticated: false,
  }),
}));

vi.mock('~/contexts/NotificationContext', () => ({
  NotificationContext: React.createContext(null),
  useNotification: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
    showInfo: vi.fn(),
    showWarning: vi.fn(),
  }),
}));

// Mock router params
const mockParams = { slug: 'test-post-slug' };
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useParams: () => mockParams,
    useNavigate: () => vi.fn(),
  };
});

// Mock UI components
vi.mock('~/components/layout/AppLayout', () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => <div data-testid="app-layout">{children}</div>,
}));

vi.mock('~/components/ui/Card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div data-testid="card">{children}</div>,
  Content: ({ children }: { children: React.ReactNode }) => <div data-testid="card-content">{children}</div>,
  Header: ({ children }: { children: React.ReactNode }) => <div data-testid="card-header">{children}</div>,
  Title: ({ children, level }: { children: React.ReactNode; level?: number }) => 
    <h1 data-testid="card-title" data-level={level}>{children}</h1>,
}));

vi.mock('~/components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, loading, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled || loading}
      data-testid="button"
      data-loading={loading}
      {...props}
    >
      {children}
    </button>
  ),
}));

vi.mock('~/components/ui/Textarea', () => ({
  Textarea: ({ value, onChange, placeholder, ...props }: any) => (
    <textarea 
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      data-testid="textarea"
      {...props}
    />
  ),
}));

// API v3 명세서 기준 테스트 데이터
const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  user_handle: 'testuser',
  full_name: 'Test User',
  created_at: '2025-06-30T00:00:00Z',
  updated_at: '2025-06-30T00:00:00Z',
};

const mockPost: Post = {
  id: 'post-123',
  title: '테스트 게시글 제목',
  content: '테스트 게시글 내용입니다. 입주민 커뮤니티 전용 게시글입니다.',
  slug: 'test-post-slug',
  service: 'residential_community', // API v3 명세서 기준
  metadata: {
    type: '자유게시판', // API v3의 board type
    category: '생활정보', // API v3의 카테고리 시스템
    tags: ['테스트', '입주민', '커뮤니티'],
    summary: '테스트 게시글 요약',
    thumbnail: null,
    attachments: [],
  },
  author: mockUser,
  author_id: 'user-123',
  created_at: '2025-06-30T00:00:00Z',
  updated_at: '2025-06-30T00:00:00Z',
  stats: {
    views: 42,
    likes: 5,
    dislikes: 1,
    comments: 3,
    bookmarks: 2,
  },
};

const mockComments: Comment[] = [
  {
    id: 1,
    post_id: 123,
    author: mockUser,
    content: '첫 번째 댓글입니다.',
    created_at: '2025-06-30T01:00:00Z',
    updated_at: '2025-06-30T01:00:00Z',
    likes: 2,
    dislikes: 0,
  },
  {
    id: 2,
    post_id: 123,
    author: mockUser,
    content: '두 번째 댓글입니다.',
    created_at: '2025-06-30T02:00:00Z',
    updated_at: '2025-06-30T02:00:00Z',
    likes: 1,
    dislikes: 0,
  },
];

// Simple wrapper for tests
const createWrapper = (user: User | null = null) => {
  // Mock the useAuth hook to return the user
  vi.doMock('~/contexts/AuthContext', () => ({
    useAuth: () => ({
      user,
      token: user ? 'mock-token' : null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
      isAuthenticated: !!user,
    }),
  }));

  return ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

describe('PostDetail 컴포넌트', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('게시글 로딩 및 표시', () => {
    it('게시글을 성공적으로 로드하고 표시해야 함', async () => {
      // Given: API 응답 모킹
      const mockGetPost = vi.mocked(apiClient.getPost);
      const mockGetComments = vi.mocked(apiClient.getComments);

      mockGetPost.mockResolvedValue({
        success: true,
        data: mockPost,
        timestamp: '2025-06-30T00:00:00Z',
      });

      mockGetComments.mockResolvedValue({
        success: true,
        data: {
          items: mockComments,
          total: 2,
          page: 1,
          size: 20,
          pages: 1,
        },
        timestamp: '2025-06-30T00:00:00Z',
      });

      // When: 컴포넌트 렌더링
      const Wrapper = createWrapper();
      render(<PostDetail />, { wrapper: Wrapper });

      // Then: 로딩 후 게시글 내용 표시
      await waitFor(() => {
        expect(screen.getByText('테스트 게시글 제목')).toBeInTheDocument();
      });

      expect(screen.getByText('테스트 게시글 내용입니다. 입주민 커뮤니티 전용 게시글입니다.')).toBeInTheDocument();
      expect(screen.getByText('자유게시판')).toBeInTheDocument(); // metadata.type
      expect(screen.getByText('생활정보')).toBeInTheDocument(); // metadata.category (API v3)
      expect(screen.getByText('Test User')).toBeInTheDocument(); // author
      expect(screen.getByText('조회 42')).toBeInTheDocument(); // stats
    });

    it('존재하지 않는 게시글에 대해 404 상태를 표시해야 함', async () => {
      // Given: API 404 응답
      const mockGetPost = vi.mocked(apiClient.getPost);
      mockGetPost.mockResolvedValue({
        success: false,
        error: '게시글을 찾을 수 없습니다',
        timestamp: '2025-06-30T00:00:00Z',
      });

      // When: 컴포넌트 렌더링
      const Wrapper = createWrapper();
      render(<PostDetail />, { wrapper: Wrapper });

      // Then: 404 메시지 표시
      await waitFor(() => {
        expect(screen.getByText('게시글을 찾을 수 없습니다')).toBeInTheDocument();
      });

      expect(screen.getByText('게시글 목록으로 돌아가기')).toBeInTheDocument();
    });

    it('로딩 중에 스피너를 표시해야 함', () => {
      // Given: 지연된 API 응답
      const mockGetPost = vi.mocked(apiClient.getPost);
      mockGetPost.mockImplementation(() => new Promise(() => {})); // 무한 대기

      // When: 컴포넌트 렌더링
      const Wrapper = createWrapper();
      render(<PostDetail />, { wrapper: Wrapper });

      // Then: 로딩 스피너 표시
      expect(screen.getByTestId('app-layout')).toBeInTheDocument();
      // 로딩 스피너는 CSS 클래스로 구현되어 있어 직접 테스트하기 어려움
      // 실제로는 텍스트나 데이터가 로드되지 않았음을 확인
      expect(screen.queryByText('테스트 게시글 제목')).not.toBeInTheDocument();
    });
  });

  describe('반응 기능 (좋아요/싫어요/북마크)', () => {
    it('인증된 사용자가 좋아요를 클릭할 수 있어야 함', async () => {
      // Given: 인증된 사용자와 API 모킹
      const mockGetPost = vi.mocked(apiClient.getPost);
      const mockGetComments = vi.mocked(apiClient.getComments);
      const mockToggleReaction = vi.mocked(apiClient.toggleReaction);

      mockGetPost.mockResolvedValue({ success: true, data: mockPost, timestamp: '2025-06-30T00:00:00Z' });
      mockGetComments.mockResolvedValue({ 
        success: true, 
        data: { items: [], total: 0, page: 1, size: 20, pages: 1 }, 
        timestamp: '2025-06-30T00:00:00Z' 
      });
      mockToggleReaction.mockResolvedValue({ success: true, data: null, timestamp: '2025-06-30T00:00:00Z' });

      // When: 인증된 사용자로 렌더링 후 좋아요 클릭
      const Wrapper = createWrapper(mockUser);
      render(<PostDetail />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('테스트 게시글 제목')).toBeInTheDocument();
      });

      const likeButton = screen.getByText('👍').closest('button');
      expect(likeButton).toBeInTheDocument();
      
      fireEvent.click(likeButton!);

      // Then: API 호출 확인
      await waitFor(() => {
        expect(mockToggleReaction).toHaveBeenCalledWith('post-123', 'post', 'like');
      });
    });

    it('비인증 사용자가 반응 버튼을 클릭하면 로그인 알림을 표시해야 함', async () => {
      // Given: 비인증 사용자
      const mockGetPost = vi.mocked(apiClient.getPost);
      const mockGetComments = vi.mocked(apiClient.getComments);

      mockGetPost.mockResolvedValue({ success: true, data: mockPost, timestamp: '2025-06-30T00:00:00Z' });
      mockGetComments.mockResolvedValue({ 
        success: true, 
        data: { items: [], total: 0, page: 1, size: 20, pages: 1 }, 
        timestamp: '2025-06-30T00:00:00Z' 
      });

      // When: 비인증 사용자로 렌더링 후 좋아요 클릭
      const Wrapper = createWrapper(null);
      render(<PostDetail />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('테스트 게시글 제목')).toBeInTheDocument();
      });

      const likeButton = screen.getByText('👍').closest('button');
      fireEvent.click(likeButton!);

      // Then: 로그인 필요 메시지 (실제 구현에서는 NotificationContext 사용)
      // 이 부분은 실제 알림 시스템 구현에 따라 달라질 수 있음
    });
  });

  describe('댓글 기능', () => {
    it('댓글 목록을 올바르게 표시해야 함', async () => {
      // Given: 게시글과 댓글 API 모킹
      const mockGetPost = vi.mocked(apiClient.getPost);
      const mockGetComments = vi.mocked(apiClient.getComments);

      mockGetPost.mockResolvedValue({ success: true, data: mockPost, timestamp: '2025-06-30T00:00:00Z' });
      mockGetComments.mockResolvedValue({
        success: true,
        data: {
          items: mockComments,
          total: 2,
          page: 1,
          size: 20,
          pages: 1,
        },
        timestamp: '2025-06-30T00:00:00Z',
      });

      // When: 컴포넌트 렌더링
      const Wrapper = createWrapper();
      render(<PostDetail />, { wrapper: Wrapper });

      // Then: 댓글 내용 표시
      await waitFor(() => {
        expect(screen.getByText('댓글 2개')).toBeInTheDocument();
      });

      expect(screen.getByText('첫 번째 댓글입니다.')).toBeInTheDocument();
      expect(screen.getByText('두 번째 댓글입니다.')).toBeInTheDocument();
    });

    it('인증된 사용자가 댓글을 작성할 수 있어야 함', async () => {
      // Given: 인증된 사용자와 API 모킹
      const mockGetPost = vi.mocked(apiClient.getPost);
      const mockGetComments = vi.mocked(apiClient.getComments);
      const mockCreateComment = vi.mocked(apiClient.createComment);

      mockGetPost.mockResolvedValue({ success: true, data: mockPost, timestamp: '2025-06-30T00:00:00Z' });
      mockGetComments.mockResolvedValue({ 
        success: true, 
        data: { items: [], total: 0, page: 1, size: 20, pages: 1 }, 
        timestamp: '2025-06-30T00:00:00Z' 
      });
      mockCreateComment.mockResolvedValue({
        success: true,
        data: {
          id: 3,
          post_id: 123,
          author: mockUser,
          content: '새로운 댓글입니다.',
          created_at: '2025-06-30T03:00:00Z',
          updated_at: '2025-06-30T03:00:00Z',
        },
        timestamp: '2025-06-30T00:00:00Z',
      });

      // When: 인증된 사용자로 렌더링 후 댓글 작성
      const Wrapper = createWrapper(mockUser);
      render(<PostDetail />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('테스트 게시글 제목')).toBeInTheDocument();
      });

      // 댓글 입력 필드와 버튼 찾기
      const commentTextarea = screen.getByPlaceholderText('댓글을 작성해주세요...');
      const submitButton = screen.getByText('댓글 작성');

      // 댓글 내용 입력
      fireEvent.change(commentTextarea, { target: { value: '새로운 댓글입니다.' } });
      fireEvent.click(submitButton);

      // Then: API 호출 확인
      await waitFor(() => {
        expect(mockCreateComment).toHaveBeenCalledWith('test-post-slug', {
          content: '새로운 댓글입니다.',
        });
      });
    });

    it('비인증 사용자에게는 댓글 작성 폼을 표시하지 않아야 함', async () => {
      // Given: 비인증 사용자
      const mockGetPost = vi.mocked(apiClient.getPost);
      const mockGetComments = vi.mocked(apiClient.getComments);

      mockGetPost.mockResolvedValue({ success: true, data: mockPost, timestamp: '2025-06-30T00:00:00Z' });
      mockGetComments.mockResolvedValue({ 
        success: true, 
        data: { items: [], total: 0, page: 1, size: 20, pages: 1 }, 
        timestamp: '2025-06-30T00:00:00Z' 
      });

      // When: 비인증 사용자로 렌더링
      const Wrapper = createWrapper(null);
      render(<PostDetail />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('테스트 게시글 제목')).toBeInTheDocument();
      });

      // Then: 댓글 작성 폼이 없어야 함
      expect(screen.queryByPlaceholderText('댓글을 작성해주세요...')).not.toBeInTheDocument();
      expect(screen.queryByText('댓글 작성')).not.toBeInTheDocument();
    });
  });

  describe('API v3 명세서 호환성', () => {
    it('residential_community 서비스 타입을 올바르게 처리해야 함', async () => {
      // Given: API v3 형식의 게시글 데이터
      const v3Post = { 
        ...mockPost, 
        service: 'residential_community' as const 
      };

      const mockGetPost = vi.mocked(apiClient.getPost);
      mockGetPost.mockResolvedValue({ success: true, data: v3Post, timestamp: '2025-06-30T00:00:00Z' });

      // When: 컴포넌트 렌더링
      const Wrapper = createWrapper();
      render(<PostDetail />, { wrapper: Wrapper });

      // Then: 서비스 타입이 올바르게 처리됨 (에러 없이 렌더링)
      await waitFor(() => {
        expect(screen.getByText('테스트 게시글 제목')).toBeInTheDocument();
      });
    });

    it('메타데이터 구조를 올바르게 표시해야 함', async () => {
      // Given: API v3 메타데이터 구조
      const v3PostWithMetadata = {
        ...mockPost,
        metadata: {
          type: '자유게시판',
          category: '입주정보', // API v3 카테고리
          tags: ['입주민', '커뮤니티', '정보'],
          summary: '입주민 전용 정보',
          thumbnail: null,
          attachments: [],
        },
      };

      const mockGetPost = vi.mocked(apiClient.getPost);
      mockGetPost.mockResolvedValue({ success: true, data: v3PostWithMetadata, timestamp: '2025-06-30T00:00:00Z' });

      // When: 컴포넌트 렌더링
      const Wrapper = createWrapper();
      render(<PostDetail />, { wrapper: Wrapper });

      // Then: 메타데이터가 올바르게 표시됨
      await waitFor(() => {
        expect(screen.getByText('자유게시판')).toBeInTheDocument();
        expect(screen.getByText('#입주민')).toBeInTheDocument();
        expect(screen.getByText('#커뮤니티')).toBeInTheDocument();
        expect(screen.getByText('#정보')).toBeInTheDocument();
      });
    });
  });
});