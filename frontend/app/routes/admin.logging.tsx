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
import { RateLimitingCard } from "~/components/monitoring/RateLimitingCard";
import { RateLimitingChart } from "~/components/monitoring/RateLimitingChart";
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
      subtitle="실시간 로그 모니터링 및 분석"
      user={user}
      onLogout={logout}
    >
      <div className="space-y-6">
        {/* 대시보드 헤더 */}
        <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">🔍 시스템 로깅 대시보드</h1>
              <p className="text-green-100">실시간 로그 모니터링 및 분석, 에러 추적 및 성능 분석</p>
              <div className="mt-4 text-sm text-green-100">
                마지막 업데이트: {new Date(timestamp).toLocaleString('ko-KR')}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-green-100">관리자</div>
                <div className="font-medium">{user?.email}</div>
              </div>
            </div>
          </div>
        </div>

        {/* 관리자 네비게이션 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🚀 관리자 메뉴</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <a
              href="/admin/monitoring"
              className="group bg-blue-50 border border-blue-200 rounded-lg p-4 hover:bg-blue-100 transition-colors cursor-pointer"
            >
              <div className="text-blue-600 text-xl mb-2">🖥️</div>
              <h3 className="font-semibold text-blue-900 group-hover:text-blue-700">모니터링</h3>
              <p className="text-sm text-blue-700 mt-1">시스템 상태 및 성능 모니터링</p>
            </a>
            
            <div className="group bg-green-50 border border-green-200 rounded-lg p-4 bg-green-100">
              <div className="text-green-600 text-xl mb-2">🔍</div>
              <h3 className="font-semibold text-green-900">로그 관리</h3>
              <p className="text-sm text-green-700 mt-1">시스템 로그 조회 및 분석</p>
              <div className="text-xs text-green-600 mt-2 font-medium">현재 페이지</div>
            </div>

            <a
              href="/admin/alerts"
              className="group bg-purple-50 border border-purple-200 rounded-lg p-4 hover:bg-purple-100 transition-colors cursor-pointer"
            >
              <div className="text-purple-600 text-xl mb-2">🚨</div>
              <h3 className="font-semibold text-purple-900 group-hover:text-purple-700">알림 관리</h3>
              <p className="text-sm text-purple-700 mt-1">알림 시스템 설정 및 관리</p>
            </a>

            <div className="group bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="text-orange-600 text-xl mb-2">⚙️</div>
              <h3 className="font-semibold text-orange-900">시스템 설정</h3>
              <p className="text-sm text-orange-700 mt-1">시스템 구성 및 설정 관리</p>
              <div className="text-xs text-orange-600 mt-2">개발 예정</div>
            </div>
          </div>
        </div>

        {/* 로깅 대시보드 컴포넌트 */}
        <LoggingDashboard
          autoRefresh={false}
          refreshInterval={30000}
          initialLoading={true}
          className="w-full"
        />

        {/* Rate Limiting 로그 분석 섹션 */}
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-orange-500 to-red-600 text-white p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold mb-2">🛡️ Rate Limiting 로그 분석</h2>
                <p className="text-orange-100">API 요청 제한 관련 로그 및 차단 이벤트 분석</p>
              </div>
              <div className="text-right">
                <div className="text-sm text-orange-100">로그 기반 분석</div>
                <div className="font-medium">실시간 모니터링</div>
              </div>
            </div>
          </div>
          
          {/* Rate Limiting 통계 카드 */}
          <div className="mb-6">
            <RateLimitingCard summary={null} loading={false} />
          </div>
          
          {/* Rate Limiting 상세 분석 차트 */}
          <RateLimitingChart metrics={null} loading={false} />
          
          {/* 추가 로그 분석 정보 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Rate Limiting 로그 분석 정보</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-blue-600 text-xl mb-2">🔍</div>
                <h4 className="font-semibold text-blue-900">로그 검색</h4>
                <p className="text-sm text-blue-700 mt-1">Rate limiting 관련 로그를 검색하고 분석합니다.</p>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="text-yellow-600 text-xl mb-2">⚠️</div>
                <h4 className="font-semibold text-yellow-900">차단 패턴</h4>
                <p className="text-sm text-yellow-700 mt-1">반복적인 차단 패턴을 분석하여 이상 활동을 감지합니다.</p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="text-red-600 text-xl mb-2">🚨</div>
                <h4 className="font-semibold text-red-900">알림 설정</h4>
                <p className="text-sm text-red-700 mt-1">임계값 초과 시 자동 알림을 설정할 수 있습니다.</p>
              </div>
            </div>
          </div>
        </div>
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