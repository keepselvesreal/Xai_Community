/**
 * 모니터링 대시보드 메인 컴포넌트
 * 
 * API 성능 모니터링 데이터를 시각화하는 대시보드
 */
import { useState, useEffect } from 'react';
import type { MonitoringDashboardProps, MonitoringData } from '~/types/monitoring';
import { getMonitoringDashboardData, logMonitoringApiError } from '~/lib/monitoring-api';
import { HealthStatusCard } from './HealthStatusCard';
import { MetricsChart } from './MetricsChart';
import { PopularEndpointsChart } from './PopularEndpointsChart';
import { SlowRequestsList } from './SlowRequestsList';
import LoadingSpinner from '~/components/common/LoadingSpinner';

export function MonitoringDashboard({
  autoRefresh = false,
  refreshInterval = 30000, // 30초
  initialLoading = true,
  className = '',
}: MonitoringDashboardProps) {
  const [data, setData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(initialLoading);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);

  /**
   * 모니터링 데이터 로드
   */
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await getMonitoringDashboardData();
      
      if (result.success && result.data) {
        setData(result.data);
        setLastUpdate(Date.now());
      } else {
        const errorMessage = result.error?.message || 'Failed to load monitoring data';
        setError(errorMessage);
        logMonitoringApiError(result.error, 'MonitoringDashboard.loadData');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Dashboard data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 수동 새로고침
   */
  const handleRefresh = () => {
    loadData();
  };

  /**
   * 초기 데이터 로드
   */
  useEffect(() => {
    loadData();
  }, []);

  /**
   * 자동 새로고침 설정
   */
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  /**
   * 타임스탬프 포맷팅
   */
  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  /**
   * 데이터가 비어있는지 확인
   */
  const isEmpty = (data: MonitoringData | null) => {
    if (!data || !data.data) return true;
    
    const { metrics, health, popular_endpoints, slow_requests } = data.data;
    
    return (
      (!metrics || (Object.keys(metrics.endpoints).length === 0 && Object.keys(metrics.status_codes).length === 0)) &&
      !health &&
      popular_endpoints.length === 0 &&
      slow_requests.length === 0
    );
  };

  // 로딩 상태
  if (loading && !data) {
    return (
      <div className={`monitoring-dashboard ${className}`}>
        <div className="flex items-center justify-center min-h-96">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">모니터링 데이터 로딩 중...</span>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error && !data) {
    return (
      <div className={`monitoring-dashboard ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            모니터링 데이터 로딩 실패
          </h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  // 빈 데이터 상태
  if (isEmpty(data)) {
    return (
      <div className={`monitoring-dashboard ${className}`}>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-gray-600 mb-2">
            모니터링 데이터가 없습니다
          </h3>
          <p className="text-gray-500 mb-4">
            시스템에 아직 충분한 활동이 없거나 데이터 수집이 시작되지 않았습니다.
          </p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            새로고침
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`monitoring-dashboard space-y-6 ${className}`}>
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            API 모니터링 대시보드
          </h1>
          {lastUpdate && (
            <p className="text-sm text-gray-500">
              마지막 업데이트: {formatTimestamp(lastUpdate)}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {autoRefresh && (
            <span className="text-sm text-green-600 bg-green-100 px-2 py-1 rounded">
              자동 새로고침 활성
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className={`px-4 py-2 rounded transition-colors ${
              loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? '로딩 중...' : '새로고침'}
          </button>
        </div>
      </div>

      {/* 헬스 상태 카드 */}
      <HealthStatusCard health={data?.data?.health || null} loading={loading} />

      {/* 메트릭 차트 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 엔드포인트 요청 수 차트 */}
        <MetricsChart
          metrics={data?.data?.metrics || null}
          type="endpoints"
          loading={loading}
        />

        {/* 상태코드 분포 차트 */}
        <MetricsChart
          metrics={data?.data?.metrics || null}
          type="status_codes"
          loading={loading}
        />
      </div>

      {/* 인기 엔드포인트와 느린 요청 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 인기 엔드포인트 차트 */}
        <PopularEndpointsChart
          popularEndpoints={data?.data?.popular_endpoints || []}
          loading={loading}
          maxItems={10}
        />

        {/* 느린 요청 목록 */}
        <SlowRequestsList
          slowRequests={data?.data?.slow_requests || []}
          loading={loading}
          maxItems={10}
        />
      </div>

      {/* 에러 알림 (데이터가 있지만 에러가 있는 경우) */}
      {error && data && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-800">
                일부 데이터를 불러오는 중 문제가 발생했습니다: {error}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}