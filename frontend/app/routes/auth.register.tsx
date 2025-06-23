import { type ActionFunction, type MetaFunction } from "@remix-run/node";
import { Form, useActionData, useNavigation } from "@remix-run/react";
import { useState } from "react";
import { Link } from "@remix-run/react";
import Card from "~/components/ui/Card";
import Input from "~/components/ui/Input";
import Button from "~/components/ui/Button";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
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

  const isSubmitting = navigation.state === "submitting";

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    const formData = new FormData(event.currentTarget);
    const userData: RegisterRequest = {
      email: formData.get("email") as string,
      user_handle: formData.get("user_handle") as string,
      display_name: formData.get("display_name") as string || undefined,
      password: formData.get("password") as string,
    };

    try {
      await register(userData);
      showSuccess(SUCCESS_MESSAGES.REGISTER_SUCCESS);
      setRedirectToLogin(true);
      // 3초 후 로그인 페이지로 리다이렉트
      setTimeout(() => {
        window.location.href = "/auth/login";
      }, 3000);
    } catch (error) {
      showError(error instanceof Error ? error.message : ERROR_MESSAGES.UNKNOWN_ERROR);
    }
  };

  if (redirectToLogin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800">
        <div className="w-full max-w-md p-6">
          <Card className="text-center">
            <div className="text-6xl mb-4">✅</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">회원가입 완료!</h1>
            <p className="text-gray-600 mb-4">
              회원가입이 성공적으로 완료되었습니다.<br />
              잠시 후 로그인 페이지로 이동합니다.
            </p>
            <Link to="/auth/login">
              <Button className="w-full">
                로그인 페이지로 이동
              </Button>
            </Link>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800">
      <div className="w-full max-w-md p-6">
        <Card>
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">📝</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">회원가입</h1>
            <p className="text-gray-600 mt-2">새 계정을 만드세요</p>
          </div>

          <Form method="post" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <Input
                type="email"
                name="email"
                label="이메일"
                placeholder="example@email.com"
                required
                error={actionData?.errors?.email}
              />

              <Input
                type="text"
                name="user_handle"
                label="사용자 핸들"
                placeholder="user_handle"
                required
                error={actionData?.errors?.user_handle}
              />

              <Input
                type="text"
                name="display_name"
                label="표시 이름"
                placeholder="표시 이름 (선택사항)"
                error={actionData?.errors?.display_name}
              />

              <Input
                type="password"
                name="password"
                label="비밀번호"
                placeholder="비밀번호"
                required
                error={actionData?.errors?.password}
              />

              <Input
                type="password"
                name="confirm_password"
                label="비밀번호 확인"
                placeholder="비밀번호 확인"
                required
                error={actionData?.errors?.confirm_password}
              />

              <Button
                type="submit"
                className="w-full"
                loading={isSubmitting}
                disabled={isSubmitting}
              >
                회원가입
              </Button>
            </div>
          </Form>

          <div className="mt-6 text-center text-sm text-gray-600">
            이미 계정이 있으신가요?{" "}
            <Link 
              to="/auth/login" 
              className="text-blue-600 hover:text-blue-500 font-medium"
            >
              로그인
            </Link>
          </div>

          {/* 비밀번호 요구사항 안내 */}
          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600">
            <strong>비밀번호 요구사항:</strong>
            <ul className="mt-1 space-y-1">
              <li>• 최소 8자 이상</li>
              <li>• 대문자, 소문자, 숫자 포함</li>
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
}