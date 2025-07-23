import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { useEffect } from "react";
import AppLayout from "~/components/layout/AppLayout";
import { UnifiedMonitoringDashboard } from "~/components/monitoring/UnifiedMonitoringDashboard";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";

export const meta: MetaFunction = () => {
  return [
    { title: "모니터링 대시보드 | 관리자" },
    { name: "description", content: "시스템 모니터링 및 성능 분석 대시보드" },
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

export default function AdminMonitoring() {
  const { timestamp } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError } = useNotification();

  // 관리자 권한 확인 (클라이언트 사이드)
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
        title="모니터링 대시보드"
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
        title="모니터링 대시보드"
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
      title="시스템 모니터링 대시보드"
      user={user}
      onLogout={logout}
    >
      <div className="space-y-6">
        {/* 모니터링 대시보드 컴포넌트 */}
        <UnifiedMonitoringDashboard timestamp={timestamp} />



      </div>
    </AppLayout>
  );
}