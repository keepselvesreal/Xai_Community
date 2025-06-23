import { redirect, type ActionFunction, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { Form, useActionData, useNavigation } from "@remix-run/react";
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
    } catch (error) {
      showError(error instanceof Error ? error.message : ERROR_MESSAGES.UNKNOWN_ERROR);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800">
      <div className="w-full max-w-md p-6">
        <Card>
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">🚀</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">로그인</h1>
            <p className="text-gray-600 mt-2">계정에 로그인하세요</p>
          </div>

          <Form method="post" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <Input
                type="email"
                name="email"
                label="이메일"
                placeholder="example@email.com"
                defaultValue="test@test.com"
                required
                error={actionData?.errors?.email}
              />

              <Input
                type="password"
                name="password"
                label="비밀번호"
                placeholder="비밀번호"
                defaultValue="password123"
                required
                error={actionData?.errors?.password}
              />

              <Button
                type="submit"
                className="w-full"
                loading={isSubmitting}
                disabled={isSubmitting}
              >
                로그인
              </Button>
            </div>
          </Form>

          <div className="mt-6 text-center text-sm text-gray-600">
            계정이 없으신가요?{" "}
            <Link 
              to="/auth/register" 
              className="text-blue-600 hover:text-blue-500 font-medium"
            >
              회원가입
            </Link>
          </div>

          {/* 개발용 안내 */}
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
            <strong>개발용 계정:</strong><br />
            이메일: test@test.com<br />
            비밀번호: password123
          </div>
        </Card>
      </div>
    </div>
  );
}