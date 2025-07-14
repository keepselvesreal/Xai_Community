import { type ActionFunction, type MetaFunction } from "@remix-run/node";
import { Form, useActionData, useNavigation } from "@remix-run/react";
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
    { name: "description", content: "새 계정을 만드세요" },
  ];
};

export const action: ActionFunction = async ({ request }) => {
  const formData = await request.formData();
  const email = formData.get("email") as string;
  const userHandle = formData.get("user_handle") as string;
  const displayName = formData.get("display_name") as string;
  const password = formData.get("password") as string;
  const confirmPassword = formData.get("confirm_password") as string;

  // 서버사이드 유효성 검사
  const errors: Record<string, string> = {};

  if (!email) {
    errors.email = "이메일을 입력해주세요.";
  } else if (!validateEmail(email)) {
    errors.email = "올바른 이메일 주소를 입력해주세요.";
  }

  if (!userHandle) {
    errors.user_handle = "사용자 핸들을 입력해주세요.";
  } else if (!validateUserHandle(userHandle)) {
    errors.user_handle = "사용자 핸들은 3-20자의 영문, 숫자, 언더스코어만 사용할 수 있습니다.";
  }

  if (!password) {
    errors.password = "비밀번호를 입력해주세요.";
  } else {
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
      errors.password = passwordValidation.errors[0];
    }
  }

  if (!confirmPassword) {
    errors.confirm_password = "비밀번호 확인을 입력해주세요.";
  } else if (password !== confirmPassword) {
    errors.confirm_password = "비밀번호가 일치하지 않습니다.";
  }

  if (Object.keys(errors).length > 0) {
    return { errors };
  }

  // 여기서는 클라이언트 사이드에서 처리하므로 null 반환
  return null;
};

export default function Register() {
  const actionData = useActionData<typeof action>();
  const navigation = useNavigation();
  const { register } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [redirectToLogin, setRedirectToLogin] = useState(false);
  const [email, setEmail] = useState("");
  const [userHandle, setUserHandle] = useState("");
  const [isHandleEditing, setIsHandleEditing] = useState(false);

  const isSubmitting = navigation.state === "submitting";


  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const userData: RegisterRequest = {
      email: email,
      user_handle: userHandle,
      password: formData.get("password") as string,
    };

    // 퍼널 분석 - 회원가입 시도 단계
    if (typeof window !== 'undefined') {
      const analytics = getAnalytics();
      analytics.trackFunnelStep('user_signup', 'form_submit', 3);
    }

    try {
      await register(userData);
      showSuccess(SUCCESS_MESSAGES.REGISTER_SUCCESS);
      
      // 퍼널 분석 - 회원가입 완료 및 전환 이벤트
      if (typeof window !== 'undefined') {
        const analytics = getAnalytics();
        analytics.trackFunnelComplete('user_signup', 3, Date.now());
        analytics.trackSignUpConversion(userHandle, 'email');
      }
      
      // 회원가입 성공 시 바로 로그인 페이지로 이동
      window.location.href = "/auth/login";
    } catch (error) {
      showError(error instanceof Error ? error.message : ERROR_MESSAGES.UNKNOWN_ERROR);
    }
  };

  // 페이지 로드 시 퍼널 시작 이벤트
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const analytics = getAnalytics();
      analytics.trackFunnelStep('user_signup', 'page_load', 1);
    }
  }, []);

  // 이메일이 변경되면 아이디 자동 설정
  useEffect(() => {
    if (email) {
      // 이메일에서 @ 앞부분만 추출하고 유효한 문자만 남김
      const emailPart = email.split('@')[0];
      const validHandle = emailPart.replace(/[^a-zA-Z0-9_]/g, '').toLowerCase();
      setUserHandle(validHandle);
      setIsHandleEditing(false);
      
      // 퍼널 분석 - 이메일 입력 완료 단계
      if (typeof window !== 'undefined') {
        const analytics = getAnalytics();
        analytics.trackFunnelStep('user_signup', 'email_input', 2);
      }
    }
  }, [email]);


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
              <p className="text-var-muted text-sm">새 계정을 만드세요</p>
            </div>

            <Form method="post" onSubmit={handleSubmit}>
              <div className="space-y-5">
                <div>
                  <label className="block text-var-secondary font-medium mb-2 text-sm">
                    이메일
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="이메일을 입력하세요"
                    required
                    className="form-input"
                  />
                  {actionData?.errors?.email && (
                    <p className="text-red-500 text-sm mt-1">{actionData.errors.email}</p>
                  )}
                </div>

                <div>
                  <label className="block text-var-secondary font-medium mb-2 text-sm">
                    아이디
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      name="user_handle"
                      value={userHandle}
                      onChange={(e) => setUserHandle(e.target.value)}
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
                  {actionData?.errors?.user_handle && (
                    <p className="text-red-500 text-sm mt-1">{actionData.errors.user_handle}</p>
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
                    name="password"
                    placeholder="비밀번호를 입력하세요"
                    required
                    className="form-input"
                  />
                  {actionData?.errors?.password && (
                    <p className="text-red-500 text-sm mt-1">{actionData.errors.password}</p>
                  )}
                </div>

                <div>
                  <label className="block text-var-secondary font-medium mb-2 text-sm">
                    비밀번호 확인
                  </label>
                  <input
                    type="password"
                    name="confirm_password"
                    placeholder="비밀번호를 다시 입력하세요"
                    required
                    className="form-input"
                  />
                  {actionData?.errors?.confirm_password && (
                    <p className="text-red-500 text-sm mt-1">{actionData.errors.confirm_password}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-auth"
                >
                  {isSubmitting ? '가입 중...' : '회원가입'}
                </button>
              </div>
            </Form>

            <div className="text-center text-var-muted text-sm border-t border-var-light pt-6 mt-6">
              <span>이미 계정이 있으신가요? </span>
              <Link 
                to="/auth/login" 
                className="text-accent-primary hover:text-accent-hover font-medium transition-colors"
              >
                로그인
              </Link>
            </div>

            {/* 비밀번호 요구사항 안내 */}
            <div className="mt-6 p-4 bg-var-section border border-var-light rounded-xl text-sm text-var-secondary">
              <strong className="text-accent-primary">비밀번호 요구사항:</strong>
              <ul className="mt-2 space-y-1">
                <li>• 최소 8자 이상</li>
                <li>• 대문자, 소문자, 숫자 포함</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}