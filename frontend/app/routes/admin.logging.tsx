/**
 * 관리자 로깅 페이지
 * 
 * 로그 관리 및 모니터링을 위한 관리자 전용 페이지
 */
import type { LoaderFunction, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { useState, useEffect } from "react";
import { LoggingDashboard } from "~/components/logging";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import AppLayout from "~/components/layout/AppLayout";

export const meta: MetaFunction = () => {
  return [
    { title: "로그 관리 | XAI Community Admin" },
    { name: "description", content: "시스템 로그 관리 및 모니터링 대시보드" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  // TODO: 실제 환경에서는 관리자 권한 확인 필요
  // const user = await getUser(request);
  // if (!user || !user.isAdmin) {
  //   throw redirect("/auth/login");
  // }

  return json({
    timestamp: new Date().toISOString(),
  });
};

export default function AdminLogging() {
  const { timestamp } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();

  // 관리자 권한 확인 (클라이언트 사이드) - 모니터링 페이지와 동일한 방식
  const isAdmin = user?.is_admin === true || user?.email === "admin@example.com" || user?.role === "admin";

  useEffect(() => {
    if (user && !isAdmin) {
      showError("관리자 권한이 필요합니다.");
      return;
    }
  }, [user, isAdmin, showError]);

  if (!user) {
    return (
      <AppLayout 
        title="로깅 대시보드"
        subtitle="로그인이 필요합니다"
        user={null}
        onLogout={logout}
      >
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-4xl mb-4">🔐</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">로그인이 필요합니다</h2>
            <p className="text-gray-600">관리자 대시보드에 접근하려면 로그인해주세요.</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (!isAdmin) {
    return (
      <AppLayout 
        title="로깅 대시보드"
        subtitle="접근 권한이 없습니다"
        user={user}
        onLogout={logout}
      >
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-4xl mb-4">🚫</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">접근 권한이 없습니다</h2>
            <p className="text-gray-600">관리자 권한이 필요한 페이지입니다.</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout 
      title="시스템 로깅 대시보드"
      subtitle=""
      user={user}
      onLogout={logout}
    >
      <div className="space-y-6">


        {/* 로깅 대시보드 컴포넌트 */}
        <LoggingDashboard
          autoRefresh={false}
          refreshInterval={30000}
          initialLoading={true}
          className="w-full"
        />

      </div>
    </AppLayout>
  );
}

/**
 * 에러 바운더리
 */
export function ErrorBoundary() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="text-6xl mb-4">🚨</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          로깅 페이지 오류
        </h1>
        <p className="text-gray-600 mb-6">
          로깅 대시보드를 불러오는 중 오류가 발생했습니다.
        </p>
        <div className="space-x-4">
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            새로고침
          </button>
          <a
            href="/admin/dashboard"
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            관리자 대시보드로 돌아가기
          </a>
        </div>
      </div>
    </div>
  );
}