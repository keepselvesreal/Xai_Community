import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { useState, useEffect } from "react";
import AppLayout from "~/components/layout/AppLayout";
import { MonitoringDashboard } from "~/components/monitoring/MonitoringDashboard";
import { UnifiedMonitoringDashboard } from "~/components/monitoring/UnifiedMonitoringDashboard";
import ReportManagement from "~/components/admin/ReportManagement";
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
  const [useNewDashboard, setUseNewDashboard] = useState(true);

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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">🖥️ 시스템 모니터링 대시보드</h1>
              <p className="text-blue-100">환경별 실시간 시스템 상태, 외부/애플리케이션/인프라 모니터링</p>
              <div className="mt-4 text-sm text-blue-100">
                마지막 업데이트: {new Date(timestamp).toLocaleString('ko-KR')}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setUseNewDashboard(!useNewDashboard)}
                className="bg-white/20 hover:bg-white/30 transition-colors text-white px-4 py-2 rounded-lg text-sm"
              >
                {useNewDashboard ? '기존 대시보드' : '새 대시보드'}
              </button>
            </div>
          </div>
        </div>


        {/* 모니터링 대시보드 컴포넌트 */}
        {useNewDashboard ? (
          <UnifiedMonitoringDashboard />
        ) : (
          <MonitoringDashboard />
        )}

        {/* 관리자 네비게이션 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🚀 관리자 메뉴</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <a
              href="/admin/monitoring"
              className="group bg-blue-50 border border-blue-200 rounded-lg p-4 hover:bg-blue-100 transition-colors cursor-pointer"
            >
              <div className="text-blue-600 text-xl mb-2">🖥️</div>
              <h3 className="font-semibold text-blue-900 group-hover:text-blue-700">모니터링</h3>
              <p className="text-sm text-blue-700 mt-1">시스템 상태 및 성능 모니터링</p>
            </a>
            
            <a
              href="/admin/logging"
              className="group bg-green-50 border border-green-200 rounded-lg p-4 hover:bg-green-100 transition-colors cursor-pointer"
            >
              <div className="text-green-600 text-xl mb-2">🔍</div>
              <h3 className="font-semibold text-green-900 group-hover:text-green-700">로그 관리</h3>
              <p className="text-sm text-green-700 mt-1">시스템 로그 조회 및 분석</p>
            </a>

            <a
              href="/admin/alerts"
              className="group bg-purple-50 border border-purple-200 rounded-lg p-4 hover:bg-purple-100 transition-colors cursor-pointer"
            >
              <div className="text-purple-600 text-xl mb-2">🚨</div>
              <h3 className="font-semibold text-purple-900 group-hover:text-purple-700">알림 관리</h3>
              <p className="text-sm text-purple-700 mt-1">알림 시스템 설정 및 관리</p>
            </a>

            <div className="group bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-red-600 text-xl mb-2">📝</div>
              <h3 className="font-semibold text-red-900">신고 관리</h3>
              <p className="text-sm text-red-700 mt-1">사용자 신고 처리 및 관리</p>
            </div>

            <div className="group bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="text-orange-600 text-xl mb-2">⚙️</div>
              <h3 className="font-semibold text-orange-900">시스템 설정</h3>
              <p className="text-sm text-orange-700 mt-1">시스템 구성 및 설정 관리</p>
              <div className="text-xs text-orange-600 mt-2">개발 예정</div>
            </div>
          </div>
        </div>

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

        {/* 신고 관리 섹션 */}
        <ReportManagement />
      </div>
    </AppLayout>
  );
}