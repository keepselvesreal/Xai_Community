/**
 * Tests for email verification component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import EmailVerificationFlow from '~/components/EmailVerificationFlow';

// Mock API client
vi.mock('~/lib/api', () => ({
  apiClient: {
    sendVerificationEmail: vi.fn(),
    verifyEmailCode: vi.fn(),
  },
}));

describe('EmailVerificationFlow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders initial email input step', () => {
    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    expect(screen.getByLabelText(/이메일 주소/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /인증하기/i })).toBeInTheDocument();
    expect(screen.getByText(/이메일 인증을 진행해주세요/i)).toBeInTheDocument();
  });

  test('validates email format', async () => {
    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    const submitButton = screen.getByRole('button', { name: /인증하기/i });

    // Test invalid email
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/올바른 이메일 주소를 입력해주세요/i)).toBeInTheDocument();
    });

    expect(mockApiClient.sendVerificationEmail).not.toHaveBeenCalled();
  });

  test('sends verification email successfully', async () => {
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        code_sent: true,
        expires_in_minutes: 5,
        message: '인증 코드가 전송되었습니다.'
      }
    });

    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    const submitButton = screen.getByRole('button', { name: /인증하기/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockApiClient.sendVerificationEmail).toHaveBeenCalledWith({
        email: 'test@example.com'
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/인증번호를 입력해주세요/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/인증번호/i)).toBeInTheDocument();
    });
  });

  test('handles email sending failure', async () => {
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: false,
      error: '이메일 전송에 실패했습니다.'
    });

    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    const submitButton = screen.getByRole('button', { name: /인증하기/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/이메일 전송에 실패했습니다/i)).toBeInTheDocument();
    });
  });

  test('verifies email code successfully', async () => {
    // First, setup email sent state
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        code_sent: true,
        expires_in_minutes: 5
      }
    });

    (await import('~/lib/api')).apiClient.verifyEmailCode.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        verified: true,
        can_proceed: true,
        message: '이메일 인증이 완료되었습니다.'
      }
    });

    const onComplete = vi.fn();
    render(<EmailVerificationFlow onComplete={onComplete} />);
    
    // Send email first
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /인증하기/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/인증번호/i)).toBeInTheDocument();
    });

    // Verify code
    const codeInput = screen.getByLabelText(/인증번호/i);
    const verifyButton = screen.getByRole('button', { name: /확인/i });

    fireEvent.change(codeInput, { target: { value: '123456' } });
    fireEvent.click(verifyButton);

    await waitFor(() => {
      expect(mockApiClient.verifyEmailCode).toHaveBeenCalledWith({
        email: 'test@example.com',
        code: '123456'
      });
    });

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith({
        email: 'test@example.com',
        verified: true
      });
    });
  });

  test('handles wrong verification code', async () => {
    // Setup email sent state
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        code_sent: true,
        expires_in_minutes: 5
      }
    });

    (await import('~/lib/api')).apiClient.verifyEmailCode.mockResolvedValue({
      success: false,
      error: '잘못된 인증 코드입니다.'
    });

    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    // Send email first
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /인증하기/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/인증번호/i)).toBeInTheDocument();
    });

    // Try wrong code
    const codeInput = screen.getByLabelText(/인증번호/i);
    const verifyButton = screen.getByRole('button', { name: /확인/i });

    fireEvent.change(codeInput, { target: { value: 'wrong123' } });
    fireEvent.click(verifyButton);

    await waitFor(() => {
      expect(screen.getByText(/잘못된 인증 코드입니다/i)).toBeInTheDocument();
    });
  });

  test('validates verification code format', async () => {
    // Setup email sent state
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        code_sent: true,
        expires_in_minutes: 5
      }
    });

    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    // Send email first
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /인증하기/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/인증번호/i)).toBeInTheDocument();
    });

    // Test invalid code length
    const codeInput = screen.getByLabelText(/인증번호/i);
    const verifyButton = screen.getByRole('button', { name: /확인/i });

    fireEvent.change(codeInput, { target: { value: '123' } }); // Too short
    fireEvent.click(verifyButton);

    await waitFor(() => {
      expect(screen.getByText(/6자리 숫자를 입력해주세요/i)).toBeInTheDocument();
    });

    expect(mockApiClient.verifyEmailCode).not.toHaveBeenCalled();
  });

  test('shows loading states', async () => {
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    const submitButton = screen.getByRole('button', { name: /인증하기/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/전송 중.../i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  test('allows resending verification email after timeout', async () => {
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        code_sent: true,
        expires_in_minutes: 5
      }
    });

    render(<EmailVerificationFlow onComplete={() => {}} resendCooldown={1} />);
    
    // Send initial email
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /인증하기/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/인증번호/i)).toBeInTheDocument();
    });

    // Resend button should be disabled initially
    const resendButton = screen.getByRole('button', { name: /재전송/i });
    expect(resendButton).toBeDisabled();

    // Wait for cooldown (1 second in test)
    await waitFor(() => {
      expect(resendButton).not.toBeDisabled();
    }, { timeout: 2000 });

    fireEvent.click(resendButton);

    await waitFor(() => {
      expect(mockApiClient.sendVerificationEmail).toHaveBeenCalledTimes(2);
    });
  });

  test('displays countdown timer for resend', async () => {
    (await import('~/lib/api')).apiClient.sendVerificationEmail.mockResolvedValue({
      success: true,
      data: {
        email: 'test@example.com',
        code_sent: true,
        expires_in_minutes: 5
      }
    });

    render(<EmailVerificationFlow onComplete={() => {}} resendCooldown={5} />);
    
    // Send initial email
    const emailInput = screen.getByLabelText(/이메일 주소/i);
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /인증하기/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/인증번호/i)).toBeInTheDocument();
    });

    // Should show countdown
    expect(screen.getByText(/5초 후 재전송 가능/i)).toBeInTheDocument();
  });

  test('shows step progress indicator', () => {
    render(<EmailVerificationFlow onComplete={() => {}} />);
    
    // Should show step 1 of 2
    expect(screen.getByText(/1/)).toBeInTheDocument();
    expect(screen.getByText(/2/)).toBeInTheDocument();
    
    // Current step should be highlighted
    expect(screen.getByTestId('step-1')).toHaveClass('active');
    expect(screen.getByTestId('step-2')).not.toHaveClass('active');
  });
});