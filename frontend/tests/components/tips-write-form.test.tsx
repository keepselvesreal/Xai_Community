import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TipsWriteForm from '~/routes/tips_.write';

// Mock 함수들
const mockNavigate = vi.fn();
const mockShowToast = vi.fn();

vi.mock('@remix-run/react', () => ({
  useNavigate: () => mockNavigate,
  Form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
  Link: ({ children, to, ...props }: any) => <a href={to} {...props}>{children}</a>,
}));

vi.mock('~/contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: mockShowToast,
    showError: mockShowToast,
  }),
}));

vi.mock('~/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'test', email: 'test@test.com', display_name: '테스트사용자' },
    logout: vi.fn(),
  }),
}));

vi.mock('~/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: vi.fn(),
  }),
}));

vi.mock('~/lib/api', () => ({
  apiClient: {
    createPost: vi.fn(),
  },
}));

describe('TipsWriteForm - PostWriteForm 리팩토링 테스트', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('기본 렌더링 테스트', () => {
    it('페이지 제목과 설명이 올바르게 표시되어야 한다', () => {
      render(<TipsWriteForm />);
      
      expect(screen.getByText('전문가 꿀정보 작성')).toBeInTheDocument();
      expect(screen.getByText('당신만의 전문 노하우와 꿀팁을 공유해보세요')).toBeInTheDocument();
    });

    it('기본 필드들이 올바르게 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      expect(screen.getByPlaceholderText('제목을 입력하세요')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('내용을 입력하세요')).toBeInTheDocument();
    });

    it('자기소개 확장 필드가 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      expect(screen.getByText('자기소개')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('간단한 자기소개를 작성해주세요')).toBeInTheDocument();
    });

    it('카테고리 선택 필드가 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      expect(screen.getByText('전문 분야')).toBeInTheDocument();
      expect(screen.getByDisplayValue('청소/정리')).toBeInTheDocument();
    });

    it('태그 입력 필드가 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      expect(screen.getByText('태그 (최대 5개)')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('태그를 입력하세요')).toBeInTheDocument();
    });
  });

  describe('자기소개 필드 유효성 검사', () => {
    it('자기소개가 비어있으면 에러 메시지를 표시해야 한다', async () => {
      render(<TipsWriteForm />);
      
      const titleInput = screen.getByPlaceholderText('제목을 입력하세요');
      const contentInput = screen.getByPlaceholderText('내용을 입력하세요');
      const submitButton = screen.getByText('게시하기');

      fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
      fireEvent.change(contentInput, { target: { value: '테스트 내용' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockShowToast).toHaveBeenCalledWith(
          '자기소개를 입력해주세요.'
        );
      });
    });

    it('자기소개가 200자를 초과하면 에러 메시지를 표시해야 한다', async () => {
      render(<TipsWriteForm />);
      
      const introductionInput = screen.getByPlaceholderText('간단한 자기소개를 작성해주세요');
      const longIntroduction = 'a'.repeat(201);

      fireEvent.change(introductionInput, { target: { value: longIntroduction } });

      expect(screen.getByText('200자를 초과할 수 없습니다')).toBeInTheDocument();
    });

    it('자기소개 글자 수가 실시간으로 표시되어야 한다', () => {
      render(<TipsWriteForm />);
      
      const introductionInput = screen.getByPlaceholderText('간단한 자기소개를 작성해주세요');
      fireEvent.change(introductionInput, { target: { value: '테스트 자기소개' } });

      expect(screen.getByText('7/200')).toBeInTheDocument();
    });
  });

  describe('폼 제출 테스트', () => {
    it('모든 필수 필드가 채워지면 제출이 가능해야 한다', async () => {
      const { apiClient } = await import('~/lib/api');
      (apiClient.createPost as any).mockResolvedValue({ success: true });

      render(<TipsWriteForm />);
      
      const titleInput = screen.getByPlaceholderText('제목을 입력하세요');
      const contentInput = screen.getByPlaceholderText('내용을 입력하세요');
      const introductionInput = screen.getByPlaceholderText('간단한 자기소개를 작성해주세요');
      const submitButton = screen.getByText('게시하기');

      fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
      fireEvent.change(contentInput, { target: { value: '테스트 내용' } });
      fireEvent.change(introductionInput, { target: { value: '테스트 자기소개' } });

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.createPost).toHaveBeenCalledWith(
          expect.objectContaining({
            title: '테스트 제목',
            content: JSON.stringify({
              introduction: '테스트 자기소개',
              content: '테스트 내용'
            }),
            metadata: expect.objectContaining({
              type: 'expert_tips',
              category: '청소/정리'
            })
          })
        );
      });
    });

    it('태그가 포함된 게시글을 제출할 수 있어야 한다', async () => {
      const { apiClient } = await import('~/lib/api');
      (apiClient.createPost as any).mockResolvedValue({ success: true });

      render(<TipsWriteForm />);
      
      const titleInput = screen.getByPlaceholderText('제목을 입력하세요');
      const contentInput = screen.getByPlaceholderText('내용을 입력하세요');
      const introductionInput = screen.getByPlaceholderText('간단한 자기소개를 작성해주세요');
      const tagInput = screen.getByPlaceholderText('태그를 입력하세요');
      const submitButton = screen.getByText('게시하기');

      fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
      fireEvent.change(contentInput, { target: { value: '테스트 내용' } });
      fireEvent.change(introductionInput, { target: { value: '테스트 자기소개' } });
      fireEvent.change(tagInput, { target: { value: '청소,정리' } });
      fireEvent.keyDown(tagInput, { key: 'Enter' });

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.createPost).toHaveBeenCalledWith(
          expect.objectContaining({
            metadata: expect.objectContaining({
              tags: ['청소', '정리']
            })
          })
        );
      });
    });
  });

  describe('카테고리 선택 테스트', () => {
    it('카테고리를 변경할 수 있어야 한다', () => {
      render(<TipsWriteForm />);
      
      const categorySelect = screen.getByDisplayValue('청소/정리');
      fireEvent.change(categorySelect, { target: { value: '인테리어' } });

      expect(screen.getByDisplayValue('인테리어')).toBeInTheDocument();
    });

    it('선택된 카테고리가 API 호출에 포함되어야 한다', async () => {
      const { apiClient } = await import('~/lib/api');
      (apiClient.createPost as any).mockResolvedValue({ success: true });

      render(<TipsWriteForm />);
      
      const titleInput = screen.getByPlaceholderText('제목을 입력하세요');
      const contentInput = screen.getByPlaceholderText('내용을 입력하세요');
      const introductionInput = screen.getByPlaceholderText('간단한 자기소개를 작성해주세요');
      const categorySelect = screen.getByDisplayValue('청소/정리');
      const submitButton = screen.getByText('게시하기');

      fireEvent.change(titleInput, { target: { value: '테스트 제목' } });
      fireEvent.change(contentInput, { target: { value: '테스트 내용' } });
      fireEvent.change(introductionInput, { target: { value: '테스트 자기소개' } });
      fireEvent.change(categorySelect, { target: { value: '생활' } });

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.createPost).toHaveBeenCalledWith(
          expect.objectContaining({
            metadata: expect.objectContaining({
              category: '생활'
            })
          })
        );
      });
    });
  });

  describe('취소 기능 테스트', () => {
    it('취소 버튼을 클릭하면 목록 페이지로 이동해야 한다', () => {
      render(<TipsWriteForm />);
      
      const cancelButton = screen.getByText('취소');
      fireEvent.click(cancelButton);

      expect(mockNavigate).toHaveBeenCalledWith('/tips');
    });
  });

  describe('PostWriteForm 통합 테스트', () => {
    it('PostWriteForm 컴포넌트가 올바른 config으로 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      // PostWriteForm의 기본 구조 확인
      expect(screen.getByText('전문가 꿀정보 작성')).toBeInTheDocument();
      expect(screen.getByText('게시하기')).toBeInTheDocument();
      expect(screen.getByText('취소')).toBeInTheDocument();
    });

    it('extendedFields가 올바르게 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      // 카테고리와 자기소개가 제목 앞에 표시되어야 함
      const pageContent = screen.getByTestId('post-write-form');
      const fieldsOrder = Array.from(pageContent.querySelectorAll('label')).map(
        label => label.textContent
      );
      
      expect(fieldsOrder.indexOf('전문 분야')).toBeLessThan(fieldsOrder.indexOf('제목'));
      expect(fieldsOrder.indexOf('자기소개')).toBeLessThan(fieldsOrder.indexOf('제목'));
    });

    it('afterContentFields가 올바르게 렌더링되어야 한다', () => {
      render(<TipsWriteForm />);
      
      // 태그 입력이 내용 뒤에 표시되어야 함
      const pageContent = screen.getByTestId('post-write-form');
      const fieldsOrder = Array.from(pageContent.querySelectorAll('label')).map(
        label => label.textContent
      );
      
      expect(fieldsOrder.indexOf('내용')).toBeLessThan(fieldsOrder.indexOf('태그 (최대 5개)'));
    });
  });
});