/**
 * 게시글 작성 폼 통합 테스트
 * TDD Red 단계: 폼 제출과 API 호출의 통합 테스트
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import BoardWrite from '~/routes/board_.write';
import { AuthProvider } from '~/contexts/AuthContext';
import { NotificationProvider } from '~/contexts/NotificationContext';
import { ThemeProvider } from '~/contexts/ThemeContext';
import { apiClient } from '~/lib/api';

// Mock the API client
vi.mock('~/lib/api', () => ({
  apiClient: {
    createPost: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the hooks
vi.mock('~/hooks/useTagInput', () => ({
  useTagInput: () => ({
    tags: [],
    currentTagInput: '',
    handleTagInput: vi.fn(),
    handleTagKeyDown: vi.fn(),
    removeTag: vi.fn(),
    canAddMore: true,
  }),
}));

describe('Board Write Integration', () => {
  const mockUser = {
    id: '507f1f77bcf86cd799439011',
    email: 'test@example.com',
    user_handle: 'test_user',
    created_at: '2025-06-30T10:00:00Z',
    updated_at: '2025-06-30T10:00:00Z'
  };

  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>
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
  });

  test('should transform form data to correct API format on submit', async () => {
    // Arrange
    const mockCreatePost = vi.mocked(apiClient.createPost);
    mockCreatePost.mockResolvedValue({
      success: true,
      data: {
        id: '507f1f77bcf86cd799439011',
        title: '테스트 제목',
        content: '테스트 내용',
        slug: 'test-slug',
        service: 'residential_community',
        metadata: {
          type: 'board',
          category: '입주정보'
        },
        author_id: 'user123',
        status: 'published',
        created_at: '2025-06-30T10:00:00Z',
        updated_at: '2025-06-30T10:00:00Z'
      },
      timestamp: '2025-06-30T10:00:00Z'
    });

    render(
      <TestWrapper>
        <BoardWrite />
      </TestWrapper>
    );

    // Act: 폼 작성
    const categorySelect = screen.getByLabelText('카테고리');
    const titleInput = screen.getByLabelText(/제목/);
    const contentTextarea = screen.getByLabelText(/내용/);
    const submitButton = screen.getByRole('button', { name: /작성/ });

    fireEvent.change(categorySelect, { target: { value: 'info' } });
    fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
    fireEvent.change(contentTextarea, { target: { value: '테스트 내용' } });

    // Act: 폼 제출
    fireEvent.click(submitButton);

    // Assert: API가 올바른 형식으로 호출되었는지 확인
    await waitFor(() => {
      expect(mockCreatePost).toHaveBeenCalledWith({
        title: '테스트 제목',
        content: '테스트 내용',
        service: 'residential_community',
        metadata: {
          type: 'board',
          category: '입주정보', // 'info' value가 '입주정보' label로 변환되어야 함
        }
      });
    });

    // 성공 후 페이지 이동 확인
    expect(mockNavigate).toHaveBeenCalledWith('/board');
  });

  test('should handle different category selections correctly', async () => {
    // Arrange
    const mockCreatePost = vi.mocked(apiClient.createPost);
    mockCreatePost.mockResolvedValue({
      success: true,
      data: {} as any,
      timestamp: '2025-06-30T10:00:00Z'
    });

    render(
      <TestWrapper>
        <BoardWrite />
      </TestWrapper>
    );

    const categorySelect = screen.getByLabelText('카테고리');
    const titleInput = screen.getByLabelText(/제목/);
    const contentTextarea = screen.getByLabelText(/내용/);
    const submitButton = screen.getByRole('button', { name: /작성/ });

    // Act & Assert: 각 카테고리별로 테스트
    const categoryTests = [
      { value: 'info', expectedLabel: '입주정보' },
      { value: 'life', expectedLabel: '생활정보' },
      { value: 'story', expectedLabel: '이야기' }
    ];

    for (const { value, expectedLabel } of categoryTests) {
      vi.clearAllMocks();
      
      fireEvent.change(categorySelect, { target: { value } });
      fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
      fireEvent.change(contentTextarea, { target: { value: '테스트 내용' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockCreatePost).toHaveBeenCalledWith(
          expect.objectContaining({
            metadata: expect.objectContaining({
              category: expectedLabel
            })
          })
        );
      });
    }
  });

  test('should handle API errors gracefully', async () => {
    // Arrange
    const mockCreatePost = vi.mocked(apiClient.createPost);
    mockCreatePost.mockResolvedValue({
      success: false,
      error: 'Server Error: database connection failed',
      timestamp: '2025-06-30T10:00:00Z'
    });

    render(
      <TestWrapper>
        <BoardWrite />
      </TestWrapper>
    );

    // Act: 유효한 데이터로 폼 제출하지만 서버 오류 발생
    const titleInput = screen.getByLabelText(/제목/);
    const contentTextarea = screen.getByLabelText(/내용/);
    const submitButton = screen.getByRole('button', { name: /작성/ });

    fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
    fireEvent.change(contentTextarea, { target: { value: '테스트 내용' } });
    fireEvent.click(submitButton);

    // Assert: 에러가 처리되고 페이지 이동이 없어야 함
    await waitFor(() => {
      expect(mockCreatePost).toHaveBeenCalled();
    });

    // 에러 발생 시 페이지 이동하지 않음
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('should show loading state during form submission', async () => {
    // Arrange
    const mockCreatePost = vi.mocked(apiClient.createPost);
    
    // Promise가 resolve되지 않도록 하여 로딩 상태 테스트
    let resolvePromise: (value: any) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    
    mockCreatePost.mockReturnValue(pendingPromise as any);

    render(
      <TestWrapper>
        <BoardWrite />
      </TestWrapper>
    );

    // Act: 폼 제출
    const titleInput = screen.getByLabelText(/제목/);
    const contentTextarea = screen.getByLabelText(/내용/);
    const submitButton = screen.getByRole('button', { name: /작성/ });

    fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
    fireEvent.change(contentTextarea, { target: { value: '테스트 내용' } });
    fireEvent.click(submitButton);

    // Assert: 로딩 상태 확인
    await waitFor(() => {
      expect(screen.getByText('작성 중...')).toBeInTheDocument();
    });

    expect(submitButton).toBeDisabled();

    // Cleanup: Promise resolve
    resolvePromise!({
      success: true,
      data: {} as any,
      timestamp: '2025-06-30T10:00:00Z'
    });
  });

  test('should prevent form submission with empty required fields', async () => {
    // Arrange
    const mockCreatePost = vi.mocked(apiClient.createPost);
    
    render(
      <TestWrapper>
        <BoardWrite />
      </TestWrapper>
    );

    // Act: 빈 필드로 제출 시도
    const submitButton = screen.getByRole('button', { name: /작성/ });
    
    // Assert: 버튼이 비활성화되어 있어야 함
    expect(submitButton).toBeDisabled();
    
    // 클릭해도 API 호출되지 않음
    fireEvent.click(submitButton);
    expect(mockCreatePost).not.toHaveBeenCalled();
  });
});

// Note: 이 테스트들은 현재 구현이 없으므로 실패할 것입니다.
// TDD Red 단계: 실제 API 호출 로직을 구현해야 합니다.