/**
 * Rate Limiting 상태 카드 컴포넌트
 * 
 * Rate Limiting 요약 정보를 표시하는 대시보드 카드
 */
import { useState, useEffect } from 'react';
import type { RateLimitingCardProps, RateLimitSummary } from '~/types/monitoring';
import { getRateLimitingSummary } from '~/lib/monitoring-api';
import LoadingSpinner from '~/components/common/LoadingSpinner';

export function RateLimitingCard({ summary, loading: externalLoading }: RateLimitingCardProps) {
  const [localSummary, setLocalSummary] = useState<RateLimitSummary | null>(summary);
  const [localLoading, setLocalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // external summary가 제공되지 않은 경우 자체적으로 데이터 로드
  useEffect(() => {
    if (!summary) {
      loadSummaryData();
    }
  }, [summary]);

  const loadSummaryData = async () => {
    try {
      setLocalLoading(true);
      setError(null);
      
      const result = await getRateLimitingSummary();
      
      if (result.success && result.data) {
        setLocalSummary(result.data);
      } else {
        setError(result.error?.message || 'Rate limiting 데이터 로딩 실패');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLocalLoading(false);
    }
  };

  const loading = externalLoading || localLoading;
  const summaryData = summary || localSummary;

  /**
   * 상태에 따른 색상 클래스 반환
   */
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  /**
   * 상태 텍스트 반환
   */
  const getStatusText = (status: string) => {
    switch (status) {
      case 'normal':
        return '정상';
      case 'warning':
        return '주의';
      case 'critical':
        return '위험';
      default:
        return '알 수 없음';
    }
  };

  /**
   * 수치를 포맷팅하는 함수
   */
  const formatNumber = (num: number) => {
    return num.toLocaleString('ko-KR');
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">Rate Limiting 데이터 로딩 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️</div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">데이터 로딩 실패</h3>
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={loadSummaryData}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (!summaryData) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <div className="text-2xl mb-2">📊</div>
          <p>Rate Limiting 데이터가 없습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Rate Limiting 상태</h3>
        <span 
          className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(summaryData.status)}`}
        >
          {getStatusText(summaryData.status)}
        </span>
      </div>

      {/* 주요 지표 그리드 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* 24시간 총 차단 수 */}
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900 mb-1">
            {formatNumber(summaryData.total_blocks_24h)}
          </div>
          <div className="text-sm text-gray-600">24시간 차단</div>
        </div>

        {/* 최근 1시간 차단 수 */}
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600 mb-1">
            {formatNumber(summaryData.recent_hour_blocks)}
          </div>
          <div className="text-sm text-gray-600">최근 1시간</div>
        </div>

        {/* 전체 차단율 */}
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600 mb-1">
            {summaryData.overall_block_rate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">차단율</div>
        </div>

        {/* 차단된 엔드포인트 수 */}
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600 mb-1">
            {summaryData.top_blocked_endpoints.length}
          </div>
          <div className="text-sm text-gray-600">차단 엔드포인트</div>
        </div>
      </div>

      {/* 상위 차단된 엔드포인트 목록 */}
      {summaryData.top_blocked_endpoints.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">상위 차단 엔드포인트</h4>
          <div className="space-y-2">
            {summaryData.top_blocked_endpoints.slice(0, 3).map((endpoint, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {endpoint.endpoint}
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatNumber(endpoint.total_requests)} 요청 중 {formatNumber(endpoint.blocks)} 차단
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-red-600">
                    {endpoint.block_rate.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 상태별 메시지 */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          {summaryData.status === 'critical' && '⚠️ 높은 차단율이 감지되었습니다. 정책 검토가 필요합니다.'}
          {summaryData.status === 'warning' && '⚠️ 차단율이 증가하고 있습니다. 모니터링을 강화하세요.'}
          {summaryData.status === 'normal' && '✅ Rate Limiting이 정상적으로 작동하고 있습니다.'}
        </div>
      </div>
    </div>
  );
}