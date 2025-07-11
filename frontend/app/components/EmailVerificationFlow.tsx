/**
 * Email verification flow component for signup process
 */

import { useState, useEffect } from 'react';
import Card from '~/components/ui/Card';
import Input from '~/components/ui/Input';
import Button from '~/components/ui/Button';
import { validateEmail } from '~/lib/utils';
import { apiClient } from '~/lib/api';
import type { 
  EmailVerificationRequest,
  EmailVerificationResponse,
  EmailVerificationCodeRequest,
  EmailVerificationCodeResponse 
} from '~/types';

interface EmailVerificationFlowProps {
  onComplete: (result: { email: string; verified: boolean }) => void;
  resendCooldown?: number; // seconds
}

type VerificationStep = 'email' | 'code' | 'completed';

interface VerificationState {
  step: VerificationStep;
  email: string;
  code: string;
  isLoading: boolean;
  error: string;
  canResend: boolean;
  resendTimer: number;
  expiresInMinutes: number;
}

export default function EmailVerificationFlow({ 
  onComplete, 
  resendCooldown = 60 
}: EmailVerificationFlowProps) {
  const [state, setState] = useState<VerificationState>({
    step: 'email',
    email: '',
    code: '',
    isLoading: false,
    error: '',
    canResend: false,
    resendTimer: 0,
    expiresInMinutes: 0,
  });

  // Countdown timer for resend button
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (state.resendTimer > 0) {
      interval = setInterval(() => {
        setState(prev => ({
          ...prev,
          resendTimer: prev.resendTimer - 1,
          canResend: prev.resendTimer <= 1,
        }));
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [state.resendTimer]);

  const validateEmailInput = (email: string): string => {
    if (!email.trim()) {
      return '이메일을 입력해주세요.';
    }
    if (!validateEmail(email)) {
      return '올바른 이메일 주소를 입력해주세요.';
    }
    return '';
  };

  const validateCodeInput = (code: string): string => {
    if (!code.trim()) {
      return '인증번호를 입력해주세요.';
    }
    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
      return '6자리 숫자를 입력해주세요.';
    }
    return '';
  };

  const sendVerificationEmail = async () => {
    const emailError = validateEmailInput(state.email);
    if (emailError) {
      setState(prev => ({ ...prev, error: emailError }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: '' }));

    try {
      const request: EmailVerificationRequest = { email: state.email };
      const response = await apiClient.sendVerificationEmail(request);

      if (response.success && response.data) {
        const data = response.data;
        setState(prev => ({
          ...prev,
          step: 'code',
          isLoading: false,
          error: '',
          expiresInMinutes: data.expires_in_minutes,
          canResend: false,
          resendTimer: resendCooldown,
        }));
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: response.error || '이메일 전송에 실패했습니다.',
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: '이메일 전송 중 오류가 발생했습니다.',
      }));
    }
  };

  const verifyEmailCode = async () => {
    const codeError = validateCodeInput(state.code);
    if (codeError) {
      setState(prev => ({ ...prev, error: codeError }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: '' }));

    try {
      const request: EmailVerificationCodeRequest = {
        email: state.email,
        code: state.code,
      };
      const response = await apiClient.verifyEmailCode(request);

      if (response.success && response.data) {
        const data = response.data;
        if (data.verified) {
          setState(prev => ({
            ...prev,
            step: 'completed',
            isLoading: false,
            error: '',
          }));
          onComplete({ email: state.email, verified: true });
        } else {
          setState(prev => ({
            ...prev,
            isLoading: false,
            error: data.message || '인증에 실패했습니다.',
          }));
        }
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: response.error || '인증에 실패했습니다.',
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: '인증 확인 중 오류가 발생했습니다.',
      }));
    }
  };

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendVerificationEmail();
  };

  const handleCodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    verifyEmailCode();
  };

  const handleResend = () => {
    setState(prev => ({
      ...prev,
      resendTimer: resendCooldown,
      canResend: false,
    }));
    sendVerificationEmail();
  };

  // Step progress indicator
  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      <div className="flex items-center space-x-4">
        <div 
          data-testid="step-1"
          className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
            state.step === 'email' ? 'bg-blue-600 text-white active' : 
            state.step === 'code' || state.step === 'completed' ? 'bg-green-600 text-white' : 
            'bg-gray-300 text-gray-600'
          }`}
        >
          1
        </div>
        <div className="w-16 h-0.5 bg-gray-300">
          <div 
            className={`h-full transition-all duration-300 ${
              state.step === 'code' || state.step === 'completed' ? 'bg-green-600 w-full' : 'bg-gray-300 w-0'
            }`}
          />
        </div>
        <div 
          data-testid="step-2"
          className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
            state.step === 'code' ? 'bg-blue-600 text-white active' : 
            state.step === 'completed' ? 'bg-green-600 text-white' : 
            'bg-gray-300 text-gray-600'
          }`}
        >
          2
        </div>
      </div>
    </div>
  );

  // Email input step
  const renderEmailStep = () => (
    <Card className="w-full max-w-md mx-auto">
      <div className="p-8">
        {renderStepIndicator()}
        
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            이메일 인증
          </h2>
          <p className="text-gray-600">
            이메일 인증을 진행해주세요
          </p>
        </div>

        <form onSubmit={handleEmailSubmit} className="space-y-4">
          <div>
            <Input
              type="email"
              label="이메일 주소"
              value={state.email}
              onChange={(e) => setState(prev => ({ ...prev, email: e.target.value, error: '' }))}
              placeholder="your@email.com"
              required
              disabled={state.isLoading}
            />
          </div>

          {state.error && (
            <div className="text-red-600 text-sm mt-2">
              {state.error}
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={state.isLoading || !state.email.trim()}
            isLoading={state.isLoading}
            loadingText="전송 중..."
          >
            인증하기
          </Button>
        </form>
      </div>
    </Card>
  );

  // Code verification step
  const renderCodeStep = () => (
    <Card className="w-full max-w-md mx-auto">
      <div className="p-8">
        {renderStepIndicator()}
        
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            인증번호 입력
          </h2>
          <p className="text-gray-600">
            <span className="font-medium">{state.email}</span>로 전송된<br />
            인증번호를 입력해주세요
          </p>
          {state.expiresInMinutes > 0 && (
            <p className="text-sm text-gray-500 mt-2">
              인증번호는 {state.expiresInMinutes}분 후 만료됩니다
            </p>
          )}
        </div>

        <form onSubmit={handleCodeSubmit} className="space-y-4">
          <div>
            <Input
              type="text"
              label="인증번호"
              value={state.code}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                setState(prev => ({ ...prev, code: value, error: '' }));
              }}
              placeholder="123456"
              maxLength={6}
              required
              disabled={state.isLoading}
              className="text-center text-lg tracking-widest"
            />
          </div>

          {state.error && (
            <div className="text-red-600 text-sm mt-2">
              {state.error}
            </div>
          )}

          <div className="space-y-3">
            <Button
              type="submit"
              className="w-full"
              disabled={state.isLoading || state.code.length !== 6}
              isLoading={state.isLoading}
              loadingText="확인 중..."
            >
              확인
            </Button>

            <div className="text-center">
              <Button
                type="button"
                variant="outline"
                onClick={handleResend}
                disabled={!state.canResend || state.isLoading}
                className="text-sm"
              >
                {state.resendTimer > 0 
                  ? `${state.resendTimer}초 후 재전송 가능` 
                  : '재전송'
                }
              </Button>
            </div>
          </div>
        </form>
      </div>
    </Card>
  );

  // Render based on current step
  switch (state.step) {
    case 'email':
      return renderEmailStep();
    case 'code':
      return renderCodeStep();
    case 'completed':
      return (
        <Card className="w-full max-w-md mx-auto">
          <div className="p-8 text-center">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                인증 완료
              </h2>
              <p className="text-gray-600">
                이메일 인증이 성공적으로 완료되었습니다
              </p>
            </div>
          </div>
        </Card>
      );
    default:
      return null;
  }
}