/**
 * 게시글 수정 페이지 통합 테스트 - TDD RED/GREEN 단계
 * 수정 페이지의 기능을 테스트하는 통합 테스트
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { AuthProvider } from '~/contexts/AuthContext';
import { NotificationProvider } from '~/contexts/NotificationContext';
import { ThemeProvider } from '~/contexts/ThemeContext';
import { apiClient } from '~/lib/api';
import PostEdit from '~/routes/posts.$slug.edit';

// Mock the API client
vi.mock('~/lib/api', async () => {
  const actual = await vi.importActual('~/lib/api');
  return {
    ...actual,
    apiClient: {
      getPost: vi.fn(),
      updatePost: vi.fn(),
      getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
    },
  };
});

// Mock useNavigate and useParams
const mockNavigate = vi.fn();
const mockParams = { slug: 'test-post-slug' };

vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockParams,
  };
});

// Mock AuthContext to provide authenticated user
vi.mock('~/contexts/AuthContext', async () => {
  const actual = await vi.importActual('~/contexts/AuthContext');
  return {
    ...actual,
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
  };
});

// Mock NotificationContext
vi.mock('~/contexts/NotificationContext', async () => {
  const actual = await vi.importActual('~/contexts/NotificationContext');
  return {
    ...actual,
    useNotification: () => ({
      showSuccess: vi.fn(),
      showError: vi.fn(),
    }),
  };
});

describe('게시글 수정 페이지 통합 테스트', () => {
  const mockUser = {
    id: '507f1f77bcf86cd799439011',
    email: 'test@example.com',
    user_handle: 'test_user',
    name: 'Test User',
    created_at: '2025-06-30T10:00:00Z',
    updated_at: '2025-06-30T10:00:00Z'
  };

  const mockPost = {
    id: 'test-post-id',
    title: '테스트 게시글',
    content: '테스트 내용입니다.',
    slug: 'test-post-slug',
    service: 'residential_community',
    metadata: {
      type: 'board',
      category: '입주정보',
      tags: ['태그1', '태그2']
    },
    author_id: '507f1f77bcf86cd799439011',
    author: mockUser,
    status: 'published',
    created_at: '2025-06-30T10:00:00Z',
    updated_at: '2025-06-30T10:00:00Z',
    published_at: '2025-06-30T10:00:00Z'
  };

  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={['/posts/test-post-slug/edit']}>
      <ThemeProvider>
        <AuthProvider>
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    
    // 기본적으로 성공적인 API 응답 설정
    vi.mocked(apiClient.getPost).mockResolvedValue({
      success: true,
      data: mockPost,
      timestamp: new Date().toISOString()
    });
    vi.mocked(apiClient.updatePost).mockResolvedValue({
      success: true,
      data: mockPost,
      timestamp: new Date().toISOString()
    });

    // 사용자 인증 상태 모킹
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => 'fake-token'),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });
  });

  describe('페이지 로드 시', () => {
    it('게시글 수정 페이지가 렌더링되어야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      // 게시글 수정 페이지가 렌더링되는지 확인
      await waitFor(() => {
        expect(screen.getByText('게시글 수정')).toBeInTheDocument();
      });
    });

    it('기존 게시글 데이터가 폼에 로드되어야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      // 제목이 로드되는지 확인
      await waitFor(() => {
        const titleInput = screen.getByDisplayValue('테스트 게시글');
        expect(titleInput).toBeInTheDocument();
      });

      // 내용이 로드되는지 확인
      await waitFor(() => {
        const contentTextarea = screen.getByDisplayValue('테스트 내용입니다.');
        expect(contentTextarea).toBeInTheDocument();
      });
    });

    it('권한이 없는 사용자는 접근할 수 없어야 한다', async () => {
      vi.mocked(apiClient.getPost).mockResolvedValue({
        success: false,
        error: '권한이 없습니다',
        timestamp: new Date().toISOString()
      });

      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      // 에러 처리 확인
      await waitFor(() => {
        expect(screen.getByText('게시글을 찾을 수 없습니다')).toBeInTheDocument();
      });
    });
  });

  describe('폼 기능 테스트', () => {
    it('제목을 수정할 수 있어야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        const titleInput = screen.getByDisplayValue('테스트 게시글');
        fireEvent.change(titleInput, { target: { value: '수정된 제목' } });
        expect(screen.getByDisplayValue('수정된 제목')).toBeInTheDocument();
      });
    });

    it('내용을 수정할 수 있어야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        const contentTextarea = screen.getByDisplayValue('테스트 내용입니다.');
        fireEvent.change(contentTextarea, { target: { value: '수정된 내용' } });
        expect(screen.getByDisplayValue('수정된 내용')).toBeInTheDocument();
      });
    });

    it('카테고리를 변경할 수 있어야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        const categorySelect = screen.getByDisplayValue('입주정보');
        fireEvent.change(categorySelect, { target: { value: 'life' } });
        expect(screen.getByDisplayValue('생활정보')).toBeInTheDocument();
      });
    });
  });

  describe('수정 완료 시', () => {
    it('수정 버튼을 클릭하면 updatePost API가 호출되어야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      // 폼이 로드될 때까지 대기
      await waitFor(() => {
        expect(screen.getByDisplayValue('테스트 게시글')).toBeInTheDocument();
      });

      // 수정 버튼 클릭
      const submitButton = screen.getByText('✏️ 게시글 수정');
      fireEvent.click(submitButton);

      // updatePost API가 호출되는지 확인
      await waitFor(() => {
        expect(apiClient.updatePost).toHaveBeenCalledWith('test-post-slug', expect.any(Object));
      });
    });

    it('수정 완료 후 게시글 상세페이지로 이동해야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('테스트 게시글')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('✏️ 게시글 수정');
      fireEvent.click(submitButton);

      // 성공 후 navigation 확인
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/board-post/test-post-slug');
      });
    });
  });

  describe('취소 시', () => {
    it('취소 버튼을 클릭하면 게시글 상세페이지로 이동해야 한다', async () => {
      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('테스트 게시글')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('취소');
      fireEvent.click(cancelButton);

      expect(mockNavigate).toHaveBeenCalledWith('/board-post/test-post-slug');
    });
  });

  describe('에러 처리', () => {
    it('게시글 로드 실패 시 에러 메시지를 표시해야 한다', async () => {
      vi.mocked(apiClient.getPost).mockRejectedValue(new Error('네트워크 오류'));

      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('게시글을 찾을 수 없습니다')).toBeInTheDocument();
      });
    });

    it('게시글 수정 실패 시 에러 처리가 되어야 한다', async () => {
      vi.mocked(apiClient.updatePost).mockRejectedValue(new Error('수정 실패'));

      render(
        <TestWrapper>
          <PostEdit />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('테스트 게시글')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('✏️ 게시글 수정');
      fireEvent.click(submitButton);

      // 에러 처리 후에도 폼이 유지되어야 함
      await waitFor(() => {
        expect(screen.getByDisplayValue('테스트 게시글')).toBeInTheDocument();
      });
    });
  });
});