/**
 * 메트릭 차트 컴포넌트
 * 
 * 엔드포인트별 요청 수 또는 상태코드 분포를 차트로 표시
 */
import type { MetricsChartProps } from '~/types/monitoring';

export function MetricsChart({ metrics, type, loading = false }: MetricsChartProps) {
  /**
   * 차트 제목 반환
   */
  const getChartTitle = () => {
    switch (type) {
      case 'endpoints':
        return '엔드포인트별 요청 수';
      case 'status_codes':
        return '응답 상태코드 분포';
      default:
        return '메트릭 차트';
    }
  };

  /**
   * 데이터 변환 및 정렬
   */
  const getChartData = () => {
    if (!metrics) return [];

    const data = type === 'endpoints' ? metrics.endpoints : metrics.status_codes;
    
    return Object.entries(data)
      .map(([key, value]) => ({ key, value }))
      .sort((a, b) => b.value - a.value) // 내림차순 정렬
      .slice(0, 10); // 상위 10개만 표시
  };

  /**
   * 상태코드에 따른 색상 반환
   */
  const getStatusCodeColor = (statusCode: string) => {
    const code = parseInt(statusCode);
    if (code >= 200 && code < 300) return 'bg-green-500';
    if (code >= 300 && code < 400) return 'bg-blue-500';
    if (code >= 400 && code < 500) return 'bg-yellow-500';
    if (code >= 500) return 'bg-red-500';
    return 'bg-gray-500';
  };

  /**
   * 엔드포인트에 따른 색상 반환 (메서드별)
   */
  const getEndpointColor = (endpoint: string) => {
    if (endpoint.startsWith('GET:')) return 'bg-blue-500';
    if (endpoint.startsWith('POST:')) return 'bg-green-500';
    if (endpoint.startsWith('PUT:')) return 'bg-yellow-500';
    if (endpoint.startsWith('DELETE:')) return 'bg-red-500';
    if (endpoint.startsWith('PATCH:')) return 'bg-purple-500';
    return 'bg-gray-500';
  };

  /**
   * 바 색상 반환
   */
  const getBarColor = (key: string) => {
    return type === 'status_codes' ? getStatusCodeColor(key) : getEndpointColor(key);
  };

  /**
   * 백분율 계산
   */
  const calculatePercentage = (value: number, total: number) => {
    return total > 0 ? (value / total) * 100 : 0;
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-48 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-3">
                <div className="h-4 bg-gray-300 rounded w-32"></div>
                <div className="flex-1 h-6 bg-gray-300 rounded"></div>
                <div className="h-4 bg-gray-300 rounded w-12"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const chartData = getChartData();
  const totalRequests = chartData.reduce((sum, item) => sum + item.value, 0);

  if (!metrics || chartData.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{getChartTitle()}</h3>
        <div className="text-center text-gray-500 py-8">
          <svg className="h-12 w-12 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p>데이터가 없습니다</p>
        </div>
      </div>
    );
  }

  // 최대값을 기준으로 바 너비 계산
  const maxValue = Math.max(...chartData.map(item => item.value));

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{getChartTitle()}</h3>
        <span className="text-sm text-gray-500">
          총 {totalRequests.toLocaleString()}건
        </span>
      </div>

      {/* 차트 */}
      <div className="space-y-3">
        {chartData.map((item, index) => {
          const barWidth = (item.value / maxValue) * 100;
          const percentage = calculatePercentage(item.value, totalRequests);
          
          return (
            <div key={item.key} className="flex items-center space-x-3">
              {/* 라벨 */}
              <div className="w-32 text-sm text-gray-700 truncate" title={item.key}>
                {type === 'status_codes' ? `${item.key}` : item.key.replace(/^[A-Z]+:/, '')}
              </div>
              
              {/* 프로그레스 바 */}
              <div className="flex-1 bg-gray-200 rounded-full h-6 relative overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${getBarColor(item.key)}`}
                  style={{ width: `${barWidth}%` }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-medium text-white mix-blend-difference">
                    {percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
              
              {/* 값 */}
              <div className="w-16 text-sm text-gray-900 text-right font-medium">
                {item.value.toLocaleString()}
              </div>
            </div>
          );
        })}
      </div>

      {/* 범례 (상태코드 차트용) */}
      {type === 'status_codes' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span>2xx 성공</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-blue-500 rounded"></div>
              <span>3xx 리다이렉트</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span>4xx 클라이언트 에러</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span>5xx 서버 에러</span>
            </div>
          </div>
        </div>
      )}

      {/* 범례 (엔드포인트 차트용) */}
      {type === 'endpoints' && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-blue-500 rounded"></div>
              <span>GET</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span>POST</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span>PUT</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span>DELETE</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-purple-500 rounded"></div>
              <span>PATCH</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}