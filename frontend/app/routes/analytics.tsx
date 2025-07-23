import { useState, useEffect } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { 
  analyticsDashboardService,
  type UserStats,
  type ConversionRate,
  type EventStats,
  type BounceRate,
  type RealtimeActivity
} from "~/lib/analytics-dashboard-service";

export const meta: MetaFunction = () => {
  return [
    { title: "사용자 분석 대시보드 | XAI 아파트 커뮤니티" },
    { name: "description", content: "사용자 행동 분석 및 커뮤니티 활동 통계" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  return json({
    timestamp: new Date().toISOString(),
  });
};

export default function Analytics() {
  const { timestamp } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();

  // 상태 관리
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [conversionRate, setConversionRate] = useState<ConversionRate | null>(null);
  const [eventStats, setEventStats] = useState<EventStats | null>(null);
  const [bounceRate, setBounceRate] = useState<BounceRate | null>(null);
  const [realtimeActivity, setRealtimeActivity] = useState<RealtimeActivity[]>([]);
  const [loading, setLoading] = useState(false);

  // 관리자 권한 확인 (클라이언트 사이드)
  const isAdmin = user?.is_admin === true || user?.email === "admin@example.com" || user?.role === "admin";

  // 모든 데이터 로드 함수
  const loadAllData = async () => {
    setLoading(true);
    
    try {
      const [userStatsData, conversionData, eventStatsData, bounceRateData, activityData] = await Promise.all([
        analyticsDashboardService.getUserStats(),
        analyticsDashboardService.getConversionRate(),
        analyticsDashboardService.getEventStats(),
        analyticsDashboardService.getBounceRate(),
        analyticsDashboardService.getRealtimeActivity(5)
      ]);

      setUserStats(userStatsData);
      setConversionRate(conversionData);
      setEventStats(eventStatsData);
      setBounceRate(bounceRateData);
      setRealtimeActivity(activityData);
      console.log('🔍 실시간 활동 피드 데이터:', activityData);
      
      showSuccess('분석 데이터를 성공적으로 업데이트했습니다.');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '데이터 로드 중 오류가 발생했습니다.';
      showError(errorMessage);
      console.error('Analytics data load error:', error);
    } finally {
      setLoading(false);
    }
  };


  // 권한 확인 및 초기 데이터 로드
  useEffect(() => {
    if (user && !isAdmin) {
      showError("관리자 권한이 필요합니다.");
      return;
    }

    if (user && isAdmin) {
      loadAllData();
    }
  }, [user, isAdmin]);

  // 5초마다 자동 새로고침
  useEffect(() => {
    if (!user || !isAdmin) return;

    const interval = setInterval(() => {
      loadAllData();
    }, 5000);

    return () => clearInterval(interval);
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
      subtitle=""
      user={user}
      onLogout={logout}
    >
      <div className="space-y-6">

        {/* 로딩 상태 */}
        {loading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
              <span className="text-blue-800 font-medium">분석 데이터를 불러오는 중...</span>
            </div>
          </div>
        )}

        {/* 주요 사용자 지표 */}
        {userStats && bounceRate ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">✨ 주요 사용자 지표</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* 신규 사용자 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-blue-900">👥 신규 사용자</h3>
                  <div className="text-2xl">👥</div>
                </div>
                <div className="space-y-1">
                  <div className="text-lg font-bold text-blue-900">
                    오늘: +{userStats.new_users_today}명
                  </div>
                  <div className="text-sm text-blue-700">
                    최근 7일: +{userStats.new_users_weekly}명
                  </div>
                </div>
              </div>

              {/* 일일 활성 사용자 */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-green-900">⚡ 일일 활성 사용자</h3>
                  <div className="text-2xl">⚡</div>
                </div>
                <div className="text-2xl font-bold text-green-900">
                  {userStats.daily_active_users}명
                </div>
                <div className="text-sm text-green-700">(오늘)</div>
              </div>

              {/* 총 사용자 */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-purple-900">📊 총 사용자</h3>
                  <div className="text-2xl">📊</div>
                </div>
                <div className="text-2xl font-bold text-purple-900">
                  {userStats.total_users}명
                </div>
                <div className="text-sm text-purple-700">(전체)</div>
              </div>

              {/* 전체 사이트 이탈률 */}
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-red-900">📉 전체 사이트 이탈률</h3>
                  <div className="text-2xl">📉</div>
                </div>
                <div className="text-2xl font-bold text-red-900">
                  {bounceRate.site_bounce_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-red-700">(평균)</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">✨ 주요 사용자 지표</h2>
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-3">📊</div>
              <div className="text-gray-600 font-medium">사용자 지표 데이터를 불러오는 중...</div>
              <div className="text-gray-500 text-sm mt-2">관리자 권한으로 로그인되어 있는지 확인해주세요.</div>
            </div>
          </div>
        )}

        {/* 가입 전환율 */}
        {conversionRate ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">🎯 가입 전환율</h2>
            <div className="flex items-center justify-center space-x-8">
              <div className="text-center">
                <div className="text-sm text-blue-700 mb-2">방문자 (오늘)</div>
                <div className="text-3xl font-bold text-blue-900">{conversionRate.visitors_today}명</div>
              </div>
              
              <div className="text-3xl text-gray-400">→</div>
              
              <div className="text-center">
                <div className="text-sm text-green-700 mb-2">가입자 (오늘)</div>
                <div className="text-3xl font-bold text-green-900">{conversionRate.signups_today}명</div>
              </div>

              <div className="bg-purple-100 border border-purple-300 rounded-lg px-4 py-2">
                <div className="text-lg font-bold text-purple-900">
                  {conversionRate.conversion_rate_today.toFixed(1)}%
                </div>
              </div>
            </div>
            
            <div className="mt-4 text-center">
              <span className="text-lg font-medium text-gray-700">
                📈 어제 대비: 
                <span className={`ml-2 ${conversionRate.conversion_rate_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {conversionRate.conversion_rate_change >= 0 ? '+' : ''}
                  {conversionRate.conversion_rate_change.toFixed(1)}%
                </span>
                <span className="ml-2 text-gray-500 text-base">
                  (어제: {conversionRate.conversion_rate_yesterday.toFixed(1)}%)
                </span>
              </span>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">🎯 가입 전환율</h2>
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-3">📊</div>
              <div className="text-gray-600 font-medium">가입 전환율 데이터를 불러오는 중...</div>
              <div className="text-gray-500 text-sm mt-2">잠시 후 다시 시도해보세요.</div>
            </div>
          </div>
        )}

        {/* 주요 이벤트 활동 */}
        {eventStats ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">🎮 주요 이벤트 활동</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl mb-2">📝</div>
                <div className="text-sm text-gray-600 mb-1">게시글 작성</div>
                <div className="text-2xl font-bold text-gray-900">{eventStats.post_creation.today}건</div>
                <div className="text-sm text-gray-500">
                  {eventStats.post_creation.yesterday_change >= 0 ? '+' : ''}
                  {eventStats.post_creation.yesterday_change} vs 어제
                </div>
              </div>

              <div className="text-center">
                <div className="text-3xl mb-2">👍</div>
                <div className="text-sm text-gray-600 mb-1">게시글 추천</div>
                <div className="text-2xl font-bold text-gray-900">{eventStats.post_likes.today}건</div>
                <div className="text-sm text-gray-500">
                  {eventStats.post_likes.yesterday_change >= 0 ? '+' : ''}
                  {eventStats.post_likes.yesterday_change} vs 어제
                </div>
              </div>

              <div className="text-center">
                <div className="text-3xl mb-2">💾</div>
                <div className="text-sm text-gray-600 mb-1">게시글 저장</div>
                <div className="text-2xl font-bold text-gray-900">{eventStats.post_bookmarks.today}건</div>
                <div className="text-sm text-gray-500">
                  {eventStats.post_bookmarks.yesterday_change >= 0 ? '+' : ''}
                  {eventStats.post_bookmarks.yesterday_change} vs 어제
                </div>
              </div>

              <div className="text-center">
                <div className="text-3xl mb-2">💬</div>
                <div className="text-sm text-gray-600 mb-1">댓글 작성</div>
                <div className="text-2xl font-bold text-gray-900">{eventStats.comment_creation.today}건</div>
                <div className="text-sm text-gray-500">
                  {eventStats.comment_creation.yesterday_change >= 0 ? '+' : ''}
                  {eventStats.comment_creation.yesterday_change} vs 어제
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">🎮 주요 이벤트 활동</h2>
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-3">🎮</div>
              <div className="text-gray-600 font-medium">이벤트 활동 데이터를 불러오는 중...</div>
              <div className="text-gray-500 text-sm mt-2">사용자 활동이 없거나 데이터가 준비 중입니다.</div>
            </div>
          </div>
        )}

        {/* 실시간 활동 피드 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">📊 실시간 활동 피드</h2>
          {realtimeActivity.length > 0 ? (
            <div className="space-y-3">
              {realtimeActivity.map((activity, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-500">
                    {new Date(activity.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="flex-1 text-sm text-gray-700">
                    <span className="font-medium">{activity.user_name}</span>가 {activity.description}
                  </div>
                  <div className="text-xs text-gray-400 capitalize">
                    {activity.activity_type}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-3">📋</div>
              <div className="text-gray-600 font-medium">아직 활동이 없습니다</div>
              <div className="text-gray-500 text-sm mt-2">사용자가 게시글이나 댓글을 작성하면 여기에 표시됩니다.</div>
            </div>
          )}
        </div>

      </div>
    </AppLayout>
  );
}