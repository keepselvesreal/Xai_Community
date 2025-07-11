/**
 * 개발용 이메일 인증 페이지
 * 현재 auth.register.tsx 디자인을 기반으로 한 독립적인 이메일 인증 테스트 페이지
 */

import { type MetaFunction } from "@remix-run/node";
import { useState } from "react";
import { Link } from "@remix-run/react";
import EmailVerificationFlow from "~/components/EmailVerificationFlow";
import Card from "~/components/ui/Card";
import Input from "~/components/ui/Input";
import Button from "~/components/ui/Button";
import { validateUserHandle, validatePassword } from "~/lib/utils";
import { ERROR_MESSAGES } from "~/lib/constants";

export const meta: MetaFunction = () => {
  return [
    { title: "이메일 인증 개발 테스트 | XAI Community" },
    { name: "description", content: "이메일 인증 기능 개발 테스트 페이지" },
  ];
};

interface RegistrationData {
  email: string;
  userHandle: string;
  displayName: string;
  password: string;
  confirmPassword: string;
}

export default function EmailVerificationDev() {
  const [emailVerified, setEmailVerified] = useState(false);
  const [verifiedEmail, setVerifiedEmail] = useState("");
  const [registrationData, setRegistrationData] = useState<RegistrationData>({
    email: "",
    userHandle: "",
    displayName: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleEmailVerificationComplete = (result: { email: string; verified: boolean }) => {
    if (result.verified) {
      setEmailVerified(true);
      setVerifiedEmail(result.email);
      setRegistrationData(prev => ({ ...prev, email: result.email }));
    }
  };

  const validateRegistrationForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // 사용자 핸들 검증
    if (!registrationData.userHandle.trim()) {
      newErrors.userHandle = "사용자 핸들을 입력해주세요.";
    } else if (!validateUserHandle(registrationData.userHandle)) {
      newErrors.userHandle = "사용자 핸들은 3-20자의 영문, 숫자, 언더스코어만 사용할 수 있습니다.";
    }

    // 비밀번호 검증
    if (!registrationData.password) {
      newErrors.password = "비밀번호를 입력해주세요.";
    } else {
      const passwordValidation = validatePassword(registrationData.password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.errors[0];
      }
    }

    // 비밀번호 확인 검증
    if (!registrationData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호 확인을 입력해주세요.";
    } else if (registrationData.password !== registrationData.confirmPassword) {
      newErrors.confirmPassword = "비밀번호가 일치하지 않습니다.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRegistrationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateRegistrationForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // 실제 회원가입 API 호출 (여기서는 시뮬레이션)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert(`회원가입 성공! 
      이메일: ${registrationData.email}
      핸들: ${registrationData.userHandle}
      닉네임: ${registrationData.displayName || registrationData.userHandle}`);
      
    } catch (error) {
      console.error('Registration error:', error);
      alert('회원가입 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof RegistrationData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRegistrationData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
    
    // 해당 필드 에러 제거
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // 이메일 인증이 완료되지 않은 경우
  if (!emailVerified) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">
              개발 테스트
            </h1>
            <p className="mt-2 text-gray-600">
              이메일 인증 기능 테스트 페이지
            </p>
          </div>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <EmailVerificationFlow 
            onComplete={handleEmailVerificationComplete}
            resendCooldown={5} // 개발용으로 5초로 단축
          />
          
          <div className="mt-6 text-center">
            <Link 
              to="/auth/register" 
              className="text-blue-600 hover:text-blue-500 text-sm"
            >
              실제 회원가입 페이지로 이동
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 이메일 인증이 완료된 경우 - 회원가입 폼 표시
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            회원가입 완료
          </h1>
          <p className="mt-2 text-gray-600">
            이메일 인증이 완료되었습니다. 나머지 정보를 입력해주세요.
          </p>
          <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            {verifiedEmail} 인증 완료
          </div>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card>
          <div className="p-8">
            <form onSubmit={handleRegistrationSubmit} className="space-y-6">
              {/* 이메일 (읽기 전용) */}
              <div>
                <Input
                  type="email"
                  label="이메일"
                  value={registrationData.email}
                  disabled
                  className="bg-gray-50"
                />
              </div>

              {/* 사용자 핸들 */}
              <div>
                <Input
                  type="text"
                  label="사용자 핸들"
                  value={registrationData.userHandle}
                  onChange={handleInputChange('userHandle')}
                  placeholder="user_handle"
                  required
                  error={errors.userHandle}
                />
                <p className="mt-1 text-sm text-gray-500">
                  3-20자, 영문/숫자/언더스코어만 사용 가능
                </p>
              </div>

              {/* 닉네임 (선택사항) */}
              <div>
                <Input
                  type="text"
                  label="닉네임 (선택사항)"
                  value={registrationData.displayName}
                  onChange={handleInputChange('displayName')}
                  placeholder="표시될 이름을 입력하세요"
                />
                <p className="mt-1 text-sm text-gray-500">
                  미입력시 사용자 핸들이 사용됩니다
                </p>
              </div>

              {/* 비밀번호 */}
              <div>
                <Input
                  type="password"
                  label="비밀번호"
                  value={registrationData.password}
                  onChange={handleInputChange('password')}
                  placeholder="비밀번호를 입력하세요"
                  required
                  error={errors.password}
                />
              </div>

              {/* 비밀번호 확인 */}
              <div>
                <Input
                  type="password"
                  label="비밀번호 확인"
                  value={registrationData.confirmPassword}
                  onChange={handleInputChange('confirmPassword')}
                  placeholder="비밀번호를 다시 입력하세요"
                  required
                  error={errors.confirmPassword}
                />
              </div>

              {/* 제출 버튼 */}
              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting}
                isLoading={isSubmitting}
                loadingText="가입 중..."
              >
                회원가입 완료
              </Button>
            </form>

            <div className="mt-6 text-center space-y-2">
              <button
                type="button"
                onClick={() => {
                  setEmailVerified(false);
                  setVerifiedEmail("");
                  setRegistrationData({
                    email: "",
                    userHandle: "",
                    displayName: "",
                    password: "",
                    confirmPassword: "",
                  });
                  setErrors({});
                }}
                className="text-blue-600 hover:text-blue-500 text-sm underline"
              >
                다른 이메일로 다시 인증하기
              </button>
              
              <div>
                <Link 
                  to="/auth/register" 
                  className="text-gray-600 hover:text-gray-500 text-sm"
                >
                  실제 회원가입 페이지로 이동
                </Link>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}