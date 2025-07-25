/*
작업 시간: 2025-07-25 12:45:00 KST
작업 버전: v2.2.0
주요 컴포넌트들: RegisterWithVerification (이메일 인증 포함 회원가입)
주요 함수들:
- handleEmailSubmit: 이메일 인증 요청 전송 (L95-120)
- handleRegisterSubmit: 회원가입 처리 (표시이름 제거) (L140-165)
- checkVerificationStatus: 이메일 인증 상태 확인 (L167-183)
- startPolling: 실시간 상태 업데이트를 위한 폴링 시작 (L185-205)
- resetVerification: 인증 상태 초기화 (L207-213)
- handleEmailChange: 이메일 변경 및 자동 아이디 생성 (L215-225)
- handleUserHandleBlur: 아이디 유효성 검사 (L228-237)
- handlePasswordBlur: 비밀번호 유효성 검사 (L239-249)
- handleConfirmPasswordBlur: 비밀번호 확인 검사 (L251-257)
관련 파일들:
- auth.register.tsx: 기본 회원가입 페이지 (환경변수에 따른 라우팅)
- .env.development: EMAIL_VERIFICATION_ENABLED 설정
변경사항 v2.0.0:
- 아이디 필드를 기본 페이지와 동일하게 수정 (수정 버튼 포함)
- 표시이름 필드 제거
- 유효성 검사를 기본 페이지와 동일하게 적용
- 비밀번호 요구사항 안내 추가
변경사항 v2.1.0:
- 이메일 인증 버튼 로딩 시간 최적화
- 즉시 pending 상태로 변경 및 성공 메시지 표시
- 폴링 주기를 2.5초로 단축 및 첫 체크를 500ms 후 실행
- UI 메시지 개선 (스팸함 확인 안내 추가)
- 버튼 텍스트 명확화
변경사항 v2.2.0:
- "전송 중..." 상태 완전 제거 (API 응답 기다리지 않음)
- 버튼 클릭 즉시 pending 상태로 변경
- 백그라운드에서 API 호출 처리
- 폴링 첫 체크를 200ms로 단축 및 주기를 2초로 개선
- 사용자 경험 대폭 개선 (즉시 응답성)
- contexts/AuthContext: 인증 컨텍스트
- lib/utils: 유틸리티 함수들
*/

import { type ActionFunction, type MetaFunction } from "@remix-run/node";
import { Form, useActionData, useNavigation, useSearchParams } from "@remix-run/react";
import { useState, useEffect } from "react";
import { Link } from "@remix-run/react";
import Card from "~/components/ui/Card";
import Input from "~/components/ui/Input";
import Button from "~/components/ui/Button";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { getAnalytics } from "~/hooks/useAnalytics";
import { validateEmail, validatePassword, validateUserHandle } from "~/lib/utils";
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from "~/lib/constants";
import type { RegisterRequest } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "회원가입 | FastAPI UI" },
    { name: "description", content: "이메일 인증으로 새 계정을 만드세요" },
  ];
};

export const action: ActionFunction = async ({ request }) => {
  // 서버사이드에서는 기본 검증만 수행
  return null;
};

type VerificationStatus = 'idle' | 'sending' | 'pending' | 'verified' | 'error';

export default function RegisterWithVerification() {
  const actionData = useActionData<typeof action>();
  const navigation = useNavigation();
  const [searchParams] = useSearchParams();
  const { register } = useAuth();
  const { showSuccess, showError } = useNotification();
  
  // Email verification states
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>('idle');
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  
  // Account creation states (shown only after email verification)
  const [showAccountFields, setShowAccountFields] = useState(false);
  const [userHandle, setUserHandle] = useState("");
  const [isHandleEditing, setIsHandleEditing] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");
  const [userHandleError, setUserHandleError] = useState("");
  
  const isSubmitting = navigation.state === "submitting";

  // Check URL params for verification result
  useEffect(() => {
    const verified = searchParams.get('verified');
    const message = searchParams.get('message');
    const urlEmail = searchParams.get('email');
    
    if (verified === 'true') {
      setVerificationStatus('verified');
      setShowAccountFields(true);
      
      // Set email from URL param if available
      if (urlEmail) {
        setEmail(urlEmail);
      }
      
      // Auto-generate user handle from verified email
      const emailToUse = urlEmail || email;
      if (emailToUse && !userHandle) {
        const emailPart = emailToUse.split('@')[0];
        const validHandle = emailPart.replace(/[^a-zA-Z0-9_]/g, '').toLowerCase();
        setUserHandle(validHandle);
        setIsHandleEditing(false);
      }
      
      showSuccess(message || "이메일 인증이 완료되었습니다!");
    } else if (verified === 'false') {
      setVerificationStatus('error');
      showError(message || "이메일 인증에 실패했습니다.");
    }
  }, [searchParams, showSuccess, showError, email, userHandle]);

  // Email submission handler
  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateEmail(email)) {
      setEmailError("올바른 이메일 주소를 입력해주세요.");
      return;
    }
    
    setEmailError("");
    
    // 즉시 pending 상태로 변경하고 성공 메시지 표시 (API 응답 기다리지 않음)
    setVerificationStatus('pending');
    showSuccess("인증 이메일을 전송하고 있습니다. 잠시만 기다려주세요.");
    
    // 폴링을 바로 시작
    startPolling();
    
    // 백그라운드에서 API 호출
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/send-verification-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      const result = await response.json();
      
      if (result.success) {
        // API 성공시 메시지 업데이트 (상태는 이미 pending)
        showSuccess("인증 이메일이 전송되었습니다. 이메일을 확인해주세요.");
      } else {
        // API 실패시에만 에러 상태로 변경
        setVerificationStatus('error');
        showError(result.message || "이메일 전송에 실패했습니다.");
      }
    } catch (error) {
      // 네트워크 오류시에만 에러 상태로 변경
      setVerificationStatus('error');
      showError("이메일 전송 중 오류가 발생했습니다. 다시 시도해주세요.");
    }
  };

  // Account registration handler (final step)
  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const errors: string[] = [];
    
    if (!validateUserHandle(userHandle)) {
      errors.push("사용자 핸들은 3-20자의 영문, 숫자, 언더스코어만 사용할 수 있습니다.");
    }
    
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      errors.push(passwordValidation.errors[0]);
    }
    
    if (password !== confirmPassword) {
      errors.push("비밀번호가 일치하지 않습니다.");
    }
    
    if (errors.length > 0) {
      showError(errors[0]);
      return;
    }

    const userData: RegisterRequest = {
      email: email,
      user_handle: userHandle,
      password: password,
    };

    try {
      await register(userData);
      showSuccess(SUCCESS_MESSAGES.REGISTER_SUCCESS);
      window.location.href = "/auth/login";
    } catch (error) {
      showError(error instanceof Error ? error.message : ERROR_MESSAGES.UNKNOWN_ERROR);
    }
  };

  // Polling function to check verification status
  const checkVerificationStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/check-verification-status/${encodeURIComponent(email)}`);
      const result = await response.json();
      
      if (result.is_verified) {
        setVerificationStatus('verified');
        setShowAccountFields(true);
        
        // Auto-generate user handle from verified email
        if (email && !userHandle) {
          const emailPart = email.split('@')[0];
          const validHandle = emailPart.replace(/[^a-zA-Z0-9_]/g, '').toLowerCase();
          setUserHandle(validHandle);
          setIsHandleEditing(false);
        }
        
        showSuccess("이메일 인증이 완료되었습니다!");
        return true; // Stop polling
      }
      return false; // Continue polling
    } catch (error) {
      console.error('Failed to check verification status:', error);
      return false;
    }
  };

  // Start polling for verification status
  const startPolling = () => {
    let attempts = 0;
    const maxAttempts = 120; // 5 minutes total
    
    // 첫 번째 체크를 매우 빠르게 실행 (200ms 후)
    setTimeout(async () => {
      const verified = await checkVerificationStatus();
      if (verified) return;
    }, 200);
    
    const pollInterval = setInterval(async () => {
      attempts++;
      
      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        setVerificationStatus('error');
        showError("인증 시간이 만료되었습니다. 다시 시도해주세요.");
        return;
      }
      
      const verified = await checkVerificationStatus();
      if (verified) {
        clearInterval(pollInterval);
      }
    }, 2000); // Check every 2 seconds for faster response
  };

  // Reset verification state
  const resetVerification = () => {
    setVerificationStatus('idle');
    setShowAccountFields(false);
    setEmail("");
    setEmailError("");
  };

  // Email change handler with auto-generate handle
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEmail = e.target.value;
    setEmail(newEmail);
    
    if (newEmail && validateEmail(newEmail)) {
      const emailPart = newEmail.split('@')[0];
      const validHandle = emailPart.replace(/[^a-zA-Z0-9_]/g, '').toLowerCase();
      setUserHandle(validHandle);
      setIsHandleEditing(false);
    }
  };

  // User handle validation handler
  const handleUserHandleBlur = () => {
    if (userHandle) {
      if (!validateUserHandle(userHandle)) {
        setUserHandleError("사용자 핸들은 3-20자의 영문, 숫자, 언더스코어만 사용할 수 있습니다.");
      } else {
        setUserHandleError("");
      }
    }
  };

  // Password validation handlers
  const handlePasswordBlur = () => {
    if (password) {
      const validation = validatePassword(password);
      if (!validation.isValid) {
        setPasswordError(validation.errors.join(" "));
      } else {
        setPasswordError("");
      }
    }
  };

  const handleConfirmPasswordBlur = () => {
    if (confirmPassword && password !== confirmPassword) {
      setConfirmPasswordError("비밀번호가 일치하지 않습니다.");
    } else {
      setConfirmPasswordError("");
    }
  };

  return (
    <div className="min-h-screen bg-var-primary">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-var-primary mb-2">XAI 아파트 커뮤니티</h1>
          <p className="text-var-secondary">함께 만들어가는 우리 아파트 소통공간</p>
        </div>

        <div className="max-w-md mx-auto">
          <div className="bg-var-card rounded-2xl shadow-var-card border border-var-color p-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-var-primary mb-2">회원가입</h2>
              <p className="text-var-muted text-sm">이메일 인증으로 새 계정을 만드세요</p>
            </div>

            {/* Step 1: Email Verification */}
            {!showAccountFields && (
              <form onSubmit={handleEmailSubmit}>
                <div className="space-y-5">
                  <div>
                    <label className="block text-var-secondary font-medium mb-2 text-sm">
                      이메일
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={handleEmailChange}
                      placeholder="이메일을 입력하세요 (예: user@example.com)"
                      required
                      disabled={verificationStatus === 'pending'}
                      className="form-input"
                    />
                    {emailError && (
                      <p className="text-red-500 text-sm mt-1">{emailError}</p>
                    )}
                  </div>


                  {verificationStatus === 'error' && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-red-800 text-sm">
                        인증에 실패했습니다. 다시 시도해주세요.
                      </p>
                    </div>
                  )}

                  <Button
                    type="submit"
                    disabled={verificationStatus === 'pending'}
                    className="w-full"
                  >
                    {verificationStatus === 'pending' ? '인증 대기 중...' : '인증 이메일 전송'}
                  </Button>

                  {verificationStatus === 'pending' && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetVerification}
                      className="w-full"
                    >
                      이메일 다시 전송
                    </Button>
                  )}
                </div>
              </form>
            )}

            {/* Step 2: Account Information (shown after email verification) */}
            {showAccountFields && (
              <>
                {/* Verification Success Message */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-green-800 text-sm font-medium">인증 완료</p>
                      <p className="text-green-700 text-sm">{email}</p>
                    </div>
                  </div>
                </div>

                <form onSubmit={handleRegisterSubmit}>
                  <div className="space-y-5">
                    <div>
                      <label className="block text-var-secondary font-medium mb-2 text-sm">
                        아이디
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={userHandle}
                          onChange={(e) => setUserHandle(e.target.value)}
                          onBlur={handleUserHandleBlur}
                          placeholder="아이디 (영문, 숫자, _)"
                          required
                          disabled={!isHandleEditing}
                          className={`form-input flex-1 ${!isHandleEditing ? 'bg-gray-50' : ''}`}
                        />
                        <button
                          type="button"
                          onClick={() => setIsHandleEditing(!isHandleEditing)}
                          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm whitespace-nowrap"
                        >
                          {isHandleEditing ? '완료' : '수정'}
                        </button>
                      </div>
                      {userHandleError && (
                        <p className="text-red-500 text-sm mt-1">{userHandleError}</p>
                      )}
                      {!isHandleEditing && (
                        <p className="text-xs text-gray-500 mt-1">
                          기본값으로 이메일에서 추출한 아이디가 설정되었습니다. 수정 버튼을 눌러 변경할 수 있습니다.
                        </p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        영문자, 숫자, 언더스코어(_)만 사용 가능합니다.
                      </p>
                    </div>

                    <div>
                      <label className="block text-var-secondary font-medium mb-2 text-sm">
                        비밀번호
                      </label>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onBlur={handlePasswordBlur}
                        placeholder="비밀번호를 입력하세요"
                        required
                        className="form-input"
                      />
                      {passwordError && (
                        <p className="text-red-500 text-sm mt-1">{passwordError}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-var-secondary font-medium mb-2 text-sm">
                        비밀번호 확인
                      </label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        onBlur={handleConfirmPasswordBlur}
                        placeholder="비밀번호를 다시 입력하세요"
                        required
                        className="form-input"
                      />
                      {confirmPasswordError && (
                        <p className="text-red-500 text-sm mt-1">{confirmPasswordError}</p>
                      )}
                    </div>

                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full"
                    >
                      {isSubmitting ? '가입 중...' : '회원가입 완료'}
                    </Button>
                  </div>
                </form>

                {/* 비밀번호 요구사항 안내 - 기본 페이지와 동일하게 */}
                <div className="mt-6 p-4 bg-var-section border border-var-light rounded-xl text-sm text-var-secondary">
                  <strong className="text-accent-primary">비밀번호 요구사항:</strong>
                  <ul className="mt-2 space-y-1">
                    <li>• 최소 6자 이상</li>
                    <li>• 소문자와 숫자 포함</li>
                    <li className="text-gray-400">• 대문자는 선택사항</li>
                  </ul>
                </div>
              </>
            )}

            <div className="mt-6 text-center">
              <p className="text-var-muted text-sm">
                이미 계정이 있으신가요?{" "}
                <Link
                  to="/auth/login"
                  className="text-var-accent hover:text-var-accent-hover underline transition-colors"
                >
                  로그인
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}