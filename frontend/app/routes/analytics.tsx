import { useState, useEffect } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { analyticsDashboardService } from "~/lib/analytics-dashboard-service";
import GA4Analytics from "~/components/analytics/GA4Analytics";
import CommunityAnalytics from "~/components/analytics/CommunityAnalytics";
import BusinessInsights from "~/components/analytics/BusinessInsights";
import type { 
  AnalyticsDashboard, 
  DateRangeFilter, 
  AnalyticsLoadingState 
} from "~/types/analytics";

export const meta: MetaFunction = () => {
  return [
    { title: "사용자 분석 대시보드 | XAI 아파트 커뮤니티" },
    { name: "description", content: "사용자 행동 분석 및 커뮤니티 활동 통계" },
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

export default function Analytics() {
  const { timestamp } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();

  // 상태 관리
  const [dateRange, setDateRange] = useState<DateRangeFilter>('7days');
  const [dashboardData, setDashboardData] = useState<AnalyticsDashboard | null>(null);
  const [loadingState, setLoadingState] = useState<AnalyticsLoadingState>({
    isLoading: false,
    error: null,
    lastFetch: null
  });

  // 관리자 권한 확인 (클라이언트 사이드)
  const isAdmin = user?.is_admin === true || user?.email === "admin@example.com" || user?.role === "admin";

  // 데이터 로드 함수
  const loadDashboardData = async (selectedRange: DateRangeFilter = dateRange) => {
    setLoadingState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const data = await analyticsDashboardService.getDashboardData(selectedRange);
      setDashboardData(data);
      setLoadingState(prev => ({
        ...prev,
        isLoading: false,
        lastFetch: new Date().toISOString()
      }));
      showSuccess('분석 데이터를 업데이트했습니다.');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '데이터 로드 중 오류가 발생했습니다.';
      setLoadingState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }));
      showError(errorMessage);
    }
  };

  // 기간 변경 핸들러
  const handleDateRangeChange = (newRange: DateRangeFilter) => {
    setDateRange(newRange);
    loadDashboardData(newRange);
  };

  // 권한 확인 및 초기 데이터 로드
  useEffect(() => {
    if (user && !isAdmin) {
      showError("관리자 권한이 필요합니다.");
      return;
    }

    if (user && isAdmin) {
      loadDashboardData();
    }
  }, [user, isAdmin]);

  // 로그인이 필요한 경우
  if (!user) {
    return (
      <AppLayout 
        title="사용자 분석 대시보드"
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

  // 권한이 없는 경우
  if (!isAdmin) {
    return (
      <AppLayout 
        title="사용자 분석 대시보드"
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
      title="사용자 분석 대시보드"
      subtitle="사용자 행동 분석 및 커뮤니티 활동 통계"
      user={user}
      onLogout={logout}
    >
      <div className="space-y-6">
        {/* 대시보드 헤더 */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">📊 사용자 분석 대시보드</h1>
              <p className="text-indigo-100">GA4 분석 및 커뮤니티 활동 인사이트</p>
              <div className="mt-4 text-sm text-indigo-100">
                마지막 업데이트: {loadingState.lastFetch 
                  ? new Date(loadingState.lastFetch).toLocaleString('ko-KR')
                  : '업데이트 필요'
                }
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* 기간 선택 */}
              <div className="flex bg-white/20 rounded-lg p-1">
                {[
                  { value: 'all' as DateRangeFilter, label: '전체' },
                  { value: '7days' as DateRangeFilter, label: '최근 7일' },
                  { value: '3days' as DateRangeFilter, label: '최근 3일' }
                ].map(({ value, label }) => (
                  <button
                    key={value}
                    onClick={() => handleDateRangeChange(value)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      dateRange === value
                        ? 'bg-white text-indigo-600'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              
              {/* 새로고침 버튼 */}
              <button
                onClick={() => loadDashboardData()}
                disabled={loadingState.isLoading}
                className="bg-white/20 hover:bg-white/30 transition-colors text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50"
              >
                {loadingState.isLoading ? '로딩 중...' : '새로고침'}
              </button>
            </div>
          </div>
        </div>

        {/* 에러 메시지 */}
        {loadingState.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="text-red-500 text-xl mr-3">⚠️</div>
              <div>
                <h3 className="font-semibold text-red-800">데이터 로드 오류</h3>
                <p className="text-red-600 text-sm mt-1">{loadingState.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 로딩 상태 */}
        {loadingState.isLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-8">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-4"></div>
              <span className="text-blue-800 font-medium">분석 데이터를 불러오는 중...</span>
            </div>
          </div>
        )}

        {/* 대시보드 컨텐츠 */}
        {dashboardData && !loadingState.isLoading && (
          <div className="space-y-8">
            {/* 주요 지표 카드 섹션 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* 총 사용자 수 */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">총 사용자</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardData.ga4Analytics.totalUsers.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-3xl">👥</div>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  신규: {dashboardData.ga4Analytics.newUsers.toLocaleString()}명
                </div>
              </div>

              {/* 페이지뷰 */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">페이지뷰</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardData.ga4Analytics.pageViews.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-3xl">📄</div>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  세션: {dashboardData.ga4Analytics.sessions.toLocaleString()}
                </div>
              </div>

              {/* 총 게시글 */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">총 게시글</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardData.communityAnalytics.totalStats.totalPosts.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-3xl">📝</div>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  댓글: {dashboardData.communityAnalytics.totalStats.totalComments.toLocaleString()}개
                </div>
              </div>

              {/* 활성 사용자 */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">활성 사용자</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardData.communityAnalytics.totalStats.activeUsers.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-3xl">⚡</div>
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  이탈률: {dashboardData.ga4Analytics.bounceRate.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* GA4 분석 섹션 */}
            <GA4Analytics data={dashboardData.ga4Analytics} />

            {/* 커뮤니티 활동 분석 섹션 */}
            <CommunityAnalytics data={dashboardData.communityAnalytics} />

            {/* 비즈니스 인사이트 섹션 */}
            <BusinessInsights data={dashboardData.businessInsights} />

            {/* 디버깅용 데이터 표시 (개발 환경에서만) */}
            {process.env.NODE_ENV === 'development' && (
              <details className="bg-gray-100 rounded-lg p-4">
                <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                  디버깅: 로드된 데이터 (개발 환경에서만 표시)
                </summary>
                <pre className="text-xs text-gray-600 overflow-auto max-h-64">
                  {JSON.stringify(dashboardData, null, 2)}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* 추가 도구 섹션 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🔧 분석 도구</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-blue-600 text-xl mb-2">📊</div>
              <h3 className="font-semibold text-blue-900">GA4 실시간 분석</h3>
              <p className="text-sm text-blue-700 mt-1">Google Analytics 4 실시간 데이터</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-green-600 text-xl mb-2">👥</div>
              <h3 className="font-semibold text-green-900">커뮤니티 활동</h3>
              <p className="text-sm text-green-700 mt-1">사용자 참여도 및 컨텐츠 성과</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="text-purple-600 text-xl mb-2">💡</div>
              <h3 className="font-semibold text-purple-900">비즈니스 인사이트</h3>
              <p className="text-sm text-purple-700 mt-1">전환율 및 성장 지표 분석</p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}