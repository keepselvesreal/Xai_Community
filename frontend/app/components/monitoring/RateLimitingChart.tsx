/**
 * Rate Limiting 상세 차트 컴포넌트
 * 
 * Rate Limiting 메트릭을 시각화하는 차트 컴포넌트
 */
import { useState, useEffect } from 'react';
import type { RateLimitingChartProps, RateLimitMetrics } from '~/types/monitoring';
import { getRateLimitingMetrics } from '~/lib/monitoring-api';
import LoadingSpinner from '~/components/common/LoadingSpinner';

export function RateLimitingChart({ metrics, loading: externalLoading }: RateLimitingChartProps) {
  const [localMetrics, setLocalMetrics] = useState<RateLimitMetrics | null>(metrics);
  const [localLoading, setLocalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // external metrics가 제공되지 않은 경우 자체적으로 데이터 로드
  useEffect(() => {
    if (!metrics) {
      loadMetricsData();
    }
  }, [metrics]);

  const loadMetricsData = async () => {
    try {
      setLocalLoading(true);
      setError(null);
      
      const result = await getRateLimitingMetrics();
      
      if (result.success && result.data) {
        setLocalMetrics(result.data);
      } else {
        setError(result.error?.message || 'Rate limiting 메트릭 로딩 실패');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLocalLoading(false);
    }
  };

  const loading = externalLoading || localLoading;
  const metricsData = metrics || localMetrics;

  /**
   * 수치를 포맷팅하는 함수
   */
  const formatNumber = (num: number) => {
    return num.toLocaleString('ko-KR');
  };

  /**
   * 차단율에 따른 색상 반환
   */
  const getBlockRateColor = (rate: number) => {
    if (rate >= 50) return 'text-red-600 bg-red-100';
    if (rate >= 20) return 'text-yellow-600 bg-yellow-100';
    if (rate >= 10) return 'text-orange-600 bg-orange-100';
    return 'text-green-600 bg-green-100';
  };

  /**
   * 시간별 차트 막대의 높이 계산
   */
  const getBarHeight = (blocks: number, maxBlocks: number) => {
    if (maxBlocks === 0) return '0%';
    return `${Math.max(2, (blocks / maxBlocks) * 100)}%`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">Rate Limiting 차트 로딩 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">📊</div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">차트 로딩 실패</h3>
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={loadMetricsData}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (!metricsData || metricsData.total_blocks === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Rate Limiting 상세 정보</h3>
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">🛡️</div>
          <p className="text-lg mb-2">차단된 요청이 없습니다</p>
          <p className="text-sm">모든 요청이 정상적으로 처리되고 있습니다.</p>
        </div>
      </div>
    );
  }

  // 시간별 차트용 최대값 계산
  const maxHourlyBlocks = Math.max(...metricsData.hourly_blocks.map(h => h.blocks));

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Rate Limiting 상세 정보</h3>
        <div className="text-sm text-gray-500">
          총 {formatNumber(metricsData.total_blocks)}건 차단 | {metricsData.block_rate.toFixed(1)}% 차단율
        </div>
      </div>

      {/* 엔드포인트별 차단 통계 */}
      {metricsData.endpoints.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-semibold text-gray-700 mb-4">엔드포인트별 차단 통계</h4>
          <div className="space-y-3">
            {metricsData.endpoints.slice(0, 5).map((endpoint, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900 truncate flex-1 mr-2">
                    {endpoint.endpoint}
                  </span>
                  <span 
                    className={`px-2 py-1 rounded text-xs font-medium ${getBlockRateColor(endpoint.block_rate)}`}
                  >
                    {endpoint.block_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>차단: {formatNumber(endpoint.blocks)}건</span>
                  <span>전체: {formatNumber(endpoint.total_requests)}건</span>
                </div>
                {/* 진행률 바 */}
                <div className="mt-2 bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      endpoint.block_rate >= 50 ? 'bg-red-500' :
                      endpoint.block_rate >= 20 ? 'bg-yellow-500' :
                      endpoint.block_rate >= 10 ? 'bg-orange-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(100, endpoint.block_rate)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 시간별 차단 트렌드 (최근 12시간) */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-4">시간별 차단 트렌드 (최근 12시간)</h4>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-end justify-between h-32 space-x-1">
            {metricsData.hourly_blocks.slice(-12).map((hourData, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                {/* 막대 */}
                <div className="w-full bg-gray-200 rounded-t flex items-end" style={{ height: '80px' }}>
                  {hourData.blocks > 0 && (
                    <div 
                      className="w-full bg-red-400 rounded-t transition-all duration-300 hover:bg-red-500"
                      style={{ height: getBarHeight(hourData.blocks, maxHourlyBlocks) }}
                      title={`${hourData.hour}: ${formatNumber(hourData.blocks)}건 차단`}
                    />
                  )}
                </div>
                {/* 시간 라벨 */}
                <div className="text-xs text-gray-500 mt-1 transform -rotate-45 origin-center">
                  {hourData.hour}
                </div>
                {/* 수치 */}
                {hourData.blocks > 0 && (
                  <div className="text-xs font-medium text-gray-700 mt-1">
                    {hourData.blocks}
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-500 text-center mt-2">
            시간대별 차단 요청 수
          </div>
        </div>
      </div>

      {/* 새로고침 버튼 */}
      <div className="mt-6 text-center">
        <button
          onClick={loadMetricsData}
          disabled={loading}
          className={`px-4 py-2 rounded text-sm transition-colors ${
            loading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </div>
    </div>
  );
}