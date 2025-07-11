/**
 * 인기 엔드포인트 차트 컴포넌트
 * 
 * 가장 많이 호출되는 API 엔드포인트들을 시각화
 */
import type { PopularEndpointsChartProps } from '~/types/monitoring';

export function PopularEndpointsChart({ 
  popularEndpoints, 
  loading = false, 
  maxItems = 10 
}: PopularEndpointsChartProps) {
  /**
   * HTTP 메서드에 따른 색상 반환
   */
  const getMethodColor = (endpoint: string) => {
    if (endpoint.startsWith('GET:')) return 'bg-blue-500';
    if (endpoint.startsWith('POST:')) return 'bg-green-500';
    if (endpoint.startsWith('PUT:')) return 'bg-yellow-500';
    if (endpoint.startsWith('DELETE:')) return 'bg-red-500';
    if (endpoint.startsWith('PATCH:')) return 'bg-purple-500';
    return 'bg-gray-500';
  };

  /**
   * HTTP 메서드 추출
   */
  const getMethod = (endpoint: string) => {
    const parts = endpoint.split(':');
    return parts[0] || '';
  };

  /**
   * 경로 추출 (메서드 제외)
   */
  const getPath = (endpoint: string) => {
    const parts = endpoint.split(':');
    return parts.slice(1).join(':') || '';
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
          <div className="h-6 bg-gray-300 rounded w-36 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-3">
                <div className="h-6 bg-gray-300 rounded w-16"></div>
                <div className="flex-1 h-4 bg-gray-300 rounded"></div>
                <div className="h-4 bg-gray-300 rounded w-12"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const displayData = popularEndpoints.slice(0, maxItems);
  const totalRequests = displayData.reduce((sum, item) => sum + item.requests, 0);

  if (displayData.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">인기 엔드포인트</h3>
        <div className="text-center text-gray-500 py-8">
          <svg className="h-12 w-12 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <p>인기 엔드포인트 데이터가 없습니다</p>
        </div>
      </div>
    );
  }

  // 최대값을 기준으로 바 너비 계산
  const maxRequests = Math.max(...displayData.map(item => item.requests));

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">인기 엔드포인트</h3>
        <span className="text-sm text-gray-500">
          총 {totalRequests.toLocaleString()}건
        </span>
      </div>

      {/* 차트 */}
      <div className="space-y-3">
        {displayData.map((item, index) => {
          const barWidth = (item.requests / maxRequests) * 100;
          const percentage = calculatePercentage(item.requests, totalRequests);
          const method = getMethod(item.endpoint);
          const path = getPath(item.endpoint);
          
          return (
            <div key={item.endpoint} className="group">
              {/* 순위와 메서드 */}
              <div className="flex items-center space-x-2 mb-1">
                <span className="flex items-center justify-center w-6 h-6 bg-gray-100 text-gray-600 text-xs font-bold rounded-full">
                  {index + 1}
                </span>
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium text-white ${getMethodColor(item.endpoint)}`}>
                  {method}
                </span>
                <span className="text-sm text-gray-700 truncate flex-1" title={path}>
                  {path}
                </span>
              </div>
              
              {/* 프로그레스 바와 통계 */}
              <div className="flex items-center space-x-3 ml-8">
                <div className="flex-1 bg-gray-200 rounded-full h-4 relative overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${getMethodColor(item.endpoint)}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                
                <div className="flex items-center space-x-2 text-sm">
                  <span className="font-medium text-gray-900">
                    {item.requests.toLocaleString()}
                  </span>
                  <span className="text-gray-500">
                    ({percentage.toFixed(1)}%)
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 요약 통계 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">가장 인기:</span>
            <span className="ml-2 font-medium text-gray-900">
              {displayData[0]?.requests.toLocaleString() || 0}건
            </span>
          </div>
          <div>
            <span className="text-gray-500">평균 요청:</span>
            <span className="ml-2 font-medium text-gray-900">
              {displayData.length > 0 
                ? Math.round(totalRequests / displayData.length).toLocaleString()
                : 0}건
            </span>
          </div>
        </div>
      </div>

      {/* HTTP 메서드 범례 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex flex-wrap gap-3 text-xs">
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

      {/* 인사이트 */}
      {displayData.length > 0 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>인사이트:</strong> 
            {displayData[0] && ` 가장 인기 있는 엔드포인트는 "${getPath(displayData[0].endpoint)}"이며 전체 요청의 ${calculatePercentage(displayData[0].requests, totalRequests).toFixed(1)}%를 차지합니다.`}
          </p>
        </div>
      )}
    </div>
  );
}