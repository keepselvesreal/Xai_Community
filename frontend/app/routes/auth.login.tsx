import { redirect, type ActionFunction, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { Form, useActionData, useNavigation, useNavigate } from "@remix-run/react";
import { useEffect } from "react";
import { Link } from "@remix-run/react";
import Card from "~/components/ui/Card";
import Input from "~/components/ui/Input";
import Button from "~/components/ui/Button";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { validateEmail } from "~/lib/utils";
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from "~/lib/constants";
import type { LoginRequest } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "로그인 | FastAPI UI" },
    { name: "description", content: "계정에 로그인하세요" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  // 이미 로그인된 사용자는 대시보드로 리다이렉트
  // 실제 환경에서는 세션/쿠키 확인
  return null;
};

export const action: ActionFunction = async ({ request }) => {
  const formData = await request.formData();
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  // 서버사이드 유효성 검사
  const errors: Record<string, string> = {};

  if (!email) {
    errors.email = "이메일을 입력해주세요.";
  } else if (!validateEmail(email)) {
    errors.email = "올바른 이메일 주소를 입력해주세요.";
  }

  if (!password) {
    errors.password = "비밀번호를 입력해주세요.";
  }

  if (Object.keys(errors).length > 0) {
    return { errors };
  }

  // 여기서는 클라이언트 사이드에서 처리하므로 null 반환
  return null;
};

export default function Login() {
  const actionData = useActionData<typeof action>();
  const navigation = useNavigation();
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const { showSuccess, showError } = useNotification();

  const isSubmitting = navigation.state === "submitting";

  // 로그인 성공 시 대시보드로 리다이렉트
  useEffect(() => {
    if (isAuthenticated) {
      window.location.href = "/dashboard";
    }
  }, [isAuthenticated]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    const formData = new FormData(event.currentTarget);
    const credentials: LoginRequest = {
      email: formData.get("email") as string,
      password: formData.get("password") as string,
    };

    try {
      await login(credentials);
      showSuccess(SUCCESS_MESSAGES.LOGIN_SUCCESS);
      // SPA 방식으로 대시보드로 이동 (페이지 새로고침 없음)
      navigate("/dashboard");
    } catch (error) {
      showError(error instanceof Error ? error.message : ERROR_MESSAGES.UNKNOWN_ERROR);
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
              <h2 className="text-3xl font-bold text-var-primary mb-2">로그인</h2>
              <p className="text-var-muted text-sm">커뮤니티에 참여하세요</p>
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

                <div className="flex items-center gap-2 mb-6">
                  <input
                    type="checkbox"
                    id="remember"
                    className="w-4 h-4 accent-[var(--accent-primary)]"
                  />
                  <label htmlFor="remember" className="text-var-secondary text-sm cursor-pointer">
                    로그인 상태 유지
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-auth"
                >
                  {isSubmitting ? '로그인 중...' : '로그인'}
                </button>
              </div>
            </Form>

            <div className="text-center text-var-muted text-sm border-t border-var-light pt-6 mt-6">
              <span>계정이 없으신가요? </span>
              <Link 
                to="/auth/register" 
                className="text-accent-primary hover:text-accent-hover font-medium transition-colors"
              >
                회원가입
              </Link>
            </div>

            <div className="text-center mt-4">
              <Link 
                to="/auth/forgot-password" 
                className="text-var-muted hover:text-accent-primary text-sm transition-colors"
              >
                비밀번호를 잊으셨나요?
              </Link>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}