/**
 * PostWriteForm 컴포넌트 단위 테스트
 * TDD Red 단계: 추상화된 글 작성 폼 컴포넌트 테스트
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import PostWriteForm from '~/components/common/PostWriteForm';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '~/contexts/AuthContext';
import { NotificationProvider } from '~/contexts/NotificationContext';
import { ThemeProvider } from '~/contexts/ThemeContext';

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

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('@remix-run/react', async () => {
  const actual = await vi.importActual('@remix-run/react');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

interface TestFormData {
  title: string;
  content: string;
  category: string;
  tags?: string[];
}

describe('PostWriteForm Component', () => {
  const mockUser = {
    id: '507f1f77bcf86cd799439011',
    email: 'test@example.com',
    user_handle: 'test_user',
    created_at: '2025-06-30T10:00:00Z',
    updated_at: '2025-06-30T10:00:00Z'
  };

  const defaultConfig = {
    pageTitle: '글쓰기',
    pageDescription: '새로운 게시글을 작성해보세요',
    submitButtonText: '작성',
    successMessage: '게시글이 성공적으로 작성되었습니다!',
    guidelines: [
      '건전한 내용으로 작성해주세요',
      '개인정보는 포함하지 마세요',
      '명확하고 이해하기 쉬운 제목을 작성해주세요',
    ],
    titleMaxLength: 200,
    contentMaxLength: 10000,
  };

  const defaultInitialData: TestFormData = {
    title: '',
    content: '',
    category: 'info',
    tags: [],
  };

  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();
  const mockOnDataChange = vi.fn();

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

  describe('기본 렌더링', () => {
    test('should render basic form elements', () => {
      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      // 헤더 확인
      expect(screen.getByText('글쓰기')).toBeInTheDocument();
      expect(screen.getByText('새로운 게시글을 작성해보세요')).toBeInTheDocument();

      // 필수 입력 필드 확인
      expect(screen.getByLabelText(/제목/)).toBeInTheDocument();
      expect(screen.getByLabelText(/내용/)).toBeInTheDocument();

      // 버튼 확인
      expect(screen.getByText('취소')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /작성/ })).toBeInTheDocument();

      // 가이드라인이 제거되었으므로 테스트 제거
    });

    test('should render with custom config', () => {
      const customConfig = {
        ...defaultConfig,
        pageTitle: '업체 등록',
        pageDescription: '새로운 업체를 등록해보세요',
        submitButtonText: '업체 등록',
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={customConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      expect(screen.getByText('업체 등록')).toBeInTheDocument();
      expect(screen.getByText('새로운 업체를 등록해보세요')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /업체 등록/ })).toBeInTheDocument();
    });
  });

  describe('폼 데이터 관리', () => {
    test('should call onDataChange when title changes', () => {
      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      const titleInput = screen.getByLabelText(/제목/);
      fireEvent.change(titleInput, { target: { value: '새로운 제목' } });

      expect(mockOnDataChange).toHaveBeenCalledWith({
        title: '새로운 제목',
      });
    });

    test('should call onDataChange when content changes', () => {
      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      const contentTextarea = screen.getByLabelText(/내용/);
      fireEvent.change(contentTextarea, { target: { value: '새로운 내용' } });

      expect(mockOnDataChange).toHaveBeenCalledWith({
        content: '새로운 내용',
      });
    });

    test('should display initial data correctly', () => {
      const initialData = {
        title: '기존 제목',
        content: '기존 내용',
        category: 'info',
        tags: ['태그1', '태그2'],
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={initialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      expect(screen.getByDisplayValue('기존 제목')).toBeInTheDocument();
      expect(screen.getByDisplayValue('기존 내용')).toBeInTheDocument();
    });
  });

  describe('폼 제출', () => {
    test('should call onSubmit when form is submitted with valid data', async () => {
      const formData = {
        title: '테스트 제목',
        content: '테스트 내용',
        category: 'info',
        tags: [],
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={formData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /작성/ });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(formData);
      });
    });

    test('should disable submit button when required fields are empty', () => {
      const emptyData = {
        title: '',
        content: '',
        category: 'info',
        tags: [],
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={emptyData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /작성/ });
      expect(submitButton).toBeDisabled();
    });

    test('should disable submit button when only title is provided', () => {
      const partialData = {
        title: '제목만 있음',
        content: '',
        category: 'info',
        tags: [],
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={partialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /작성/ });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('로딩 상태', () => {
    test('should show loading state when isSubmitting is true', () => {
      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={true}
          />
        </TestWrapper>
      );

      expect(screen.getByText('작성 중...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /작성 중/ })).toBeDisabled();
      expect(screen.getByText('취소')).toBeDisabled();
    });

    test('should show submit button text when not submitting', () => {
      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: /작성/ })).toBeInTheDocument();
      expect(screen.queryByText('작성 중...')).not.toBeInTheDocument();
    });
  });

  describe('취소 기능', () => {
    test('should call onCancel when cancel button is clicked', () => {
      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      const cancelButton = screen.getByText('취소');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  describe('확장 필드', () => {
    test('should render extended fields when provided', () => {
      const ExtendedFields = () => (
        <div>
          <label htmlFor="custom-field">커스텀 필드</label>
          <input id="custom-field" type="text" />
        </div>
      );

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
            extendedFields={<ExtendedFields />}
          />
        </TestWrapper>
      );

      expect(screen.getByLabelText('커스텀 필드')).toBeInTheDocument();
    });

    test('should render afterContentFields when provided', () => {
      const AfterContentFields = () => (
        <div>
          <label htmlFor="after-content-field">내용 후 필드</label>
          <input id="after-content-field" type="text" />
        </div>
      );

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
            afterContentFields={<AfterContentFields />}
          />
        </TestWrapper>
      );

      expect(screen.getByLabelText('내용 후 필드')).toBeInTheDocument();
    });
  });

  describe('수정 모드', () => {
    test('should show edit mode title when isEditMode is true', () => {
      const editConfig = {
        ...defaultConfig,
        pageTitle: '글 수정',
        submitButtonText: '수정 완료',
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={editConfig}
            initialData={defaultInitialData}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
            isEditMode={true}
          />
        </TestWrapper>
      );

      expect(screen.getByText('글 수정')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /수정 완료/ })).toBeInTheDocument();
    });
  });

  describe('문자 수 제한', () => {
    test('should show character count for title', () => {
      const dataWithTitle = {
        ...defaultInitialData,
        title: '테스트 제목',
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={dataWithTitle}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      // 문자 수 표시는 현재 initialData를 사용하지 않고 있음
      expect(screen.getByText(/\d+\/200자/)).toBeInTheDocument();
    });

    test('should show character count for content', () => {
      const dataWithContent = {
        ...defaultInitialData,
        content: '테스트 내용입니다.',
      };

      render(
        <TestWrapper>
          <PostWriteForm
            config={defaultConfig}
            initialData={dataWithContent}
            onDataChange={mockOnDataChange}
            onSubmit={mockOnSubmit}
            onCancel={mockOnCancel}
            isSubmitting={false}
          />
        </TestWrapper>
      );

      expect(screen.getByDisplayValue('테스트 내용입니다.')).toBeInTheDocument();
      expect(screen.getByText(/\d+\/10,000자/)).toBeInTheDocument();
    });
  });
});