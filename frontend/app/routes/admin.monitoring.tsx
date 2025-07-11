import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { useState, useEffect } from "react";
import AppLayout from "~/components/layout/AppLayout";
import { MonitoringDashboard } from "~/components/monitoring/MonitoringDashboard";
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
  const { showError, showSuccess } = useNotification();

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
      subtitle="실시간 시스템 상태 및 성능 분석"
      user={user}
      onLogout={logout}
    >
      <div className="space-y-6">
        {/* 대시보드 헤더 */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-lg">
          <h1 className="text-2xl font-bold mb-2">🖥️ 시스템 모니터링 대시보드</h1>
          <p className="text-blue-100">실시간 API 성능, 에러 추적, 시스템 상태를 한눈에 확인하세요</p>
          <div className="mt-4 text-sm text-blue-100">
            마지막 업데이트: {new Date(timestamp).toLocaleString('ko-KR')}
          </div>
        </div>

        {/* 사용 안내 */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <div className="text-yellow-600 text-lg mr-2">💡</div>
            <h3 className="font-semibold text-yellow-800">대시보드 사용 안내</h3>
          </div>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• 모든 데이터는 실시간으로 자동 업데이트됩니다</li>
            <li>• 느린 요청은 2초 이상 소요되는 API 호출을 의미합니다</li>
            <li>• 에러율이 5% 이상일 경우 시스템 상태가 '위험'으로 표시됩니다</li>
            <li>• 차트를 클릭하면 상세 정보를 확인할 수 있습니다</li>
          </ul>
        </div>

        {/* 모니터링 대시보드 컴포넌트 */}
        <MonitoringDashboard />

        {/* 추가 관리자 도구 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🔧 관리자 도구</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-blue-600 text-xl mb-2">📊</div>
              <h3 className="font-semibold text-blue-900">상세 분석</h3>
              <p className="text-sm text-blue-700 mt-1">API 성능 상세 분석 및 보고서</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-green-600 text-xl mb-2">⚡</div>
              <h3 className="font-semibold text-green-900">성능 최적화</h3>
              <p className="text-sm text-green-700 mt-1">시스템 성능 최적화 권장사항</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="text-purple-600 text-xl mb-2">🚨</div>
              <h3 className="font-semibold text-purple-900">알림 설정</h3>
              <p className="text-sm text-purple-700 mt-1">지능형 알림 시스템 관리</p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}