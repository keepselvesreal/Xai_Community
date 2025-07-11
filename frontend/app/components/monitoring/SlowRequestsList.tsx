/**
 * 느린 요청 목록 컴포넌트
 * 
 * 응답시간이 긴 API 요청들을 목록으로 표시
 */
import type { SlowRequestsListProps } from '~/types/monitoring';

export function SlowRequestsList({ 
  slowRequests, 
  loading = false, 
  maxItems = 10 
}: SlowRequestsListProps) {
  /**
   * 응답시간에 따른 심각도 색상 반환
   */
  const getSeverityColor = (responseTime: number) => {
    if (responseTime >= 5.0) return 'text-red-600 bg-red-100'; // 5초 이상 - 심각
    if (responseTime >= 3.0) return 'text-orange-600 bg-orange-100'; // 3초 이상 - 경고
    if (responseTime >= 2.0) return 'text-yellow-600 bg-yellow-100'; // 2초 이상 - 주의
    return 'text-blue-600 bg-blue-100'; // 2초 미만 - 정보
  };

  /**
   * 응답시간 포맷팅
   */
  const formatResponseTime = (time: number) => {
    return `${time.toFixed(2)}초`;
  };

  /**
   * 상대 시간 포맷팅
   */
  const formatRelativeTime = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}일 전`;
    if (hours > 0) return `${hours}시간 전`;
    if (minutes > 0) return `${minutes}분 전`;
    return '방금 전';
  };

  /**
   * HTTP 메서드에 따른 색상 반환
   */
  const getMethodColor = (endpoint: string) => {
    if (endpoint.startsWith('GET:')) return 'bg-blue-500 text-white';
    if (endpoint.startsWith('POST:')) return 'bg-green-500 text-white';
    if (endpoint.startsWith('PUT:')) return 'bg-yellow-500 text-white';
    if (endpoint.startsWith('DELETE:')) return 'bg-red-500 text-white';
    if (endpoint.startsWith('PATCH:')) return 'bg-purple-500 text-white';
    return 'bg-gray-500 text-white';
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
   * 상태코드에 따른 색상 반환
   */
  const getStatusCodeColor = (statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) return 'text-green-600';
    if (statusCode >= 300 && statusCode < 400) return 'text-blue-600';
    if (statusCode >= 400 && statusCode < 500) return 'text-yellow-600';
    if (statusCode >= 500) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-32 mb-4"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="border border-gray-200 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="h-4 bg-gray-300 rounded w-48"></div>
                  <div className="h-4 bg-gray-300 rounded w-16"></div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="h-3 bg-gray-300 rounded w-12"></div>
                  <div className="h-3 bg-gray-300 rounded w-20"></div>
                  <div className="h-3 bg-gray-300 rounded w-16"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const displayData = slowRequests.slice(0, maxItems);

  if (displayData.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">느린 요청 목록</h3>
        <div className="text-center text-gray-500 py-8">
          <svg className="h-12 w-12 mx-auto mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p>느린 요청이 감지되지 않았습니다</p>
          <p className="text-sm mt-1">모든 요청이 정상적인 응답시간을 보이고 있습니다 ✨</p>
        </div>
      </div>
    );
  }

  // 응답시간 기준 통계 계산
  const avgResponseTime = displayData.reduce((sum, item) => sum + item.response_time, 0) / displayData.length;
  const maxResponseTime = Math.max(...displayData.map(item => item.response_time));

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">느린 요청 목록</h3>
        <span className="text-sm text-gray-500">
          {displayData.length}개 항목
        </span>
      </div>

      {/* 요청 목록 */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {displayData.map((request, index) => {
          const method = getMethod(request.endpoint);
          const path = getPath(request.endpoint);
          const severityColor = getSeverityColor(request.response_time);
          
          return (
            <div key={`${request.endpoint}-${request.timestamp}-${index}`} 
                 className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
              {/* 첫 번째 줄: 엔드포인트와 응답시간 */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2 flex-1 min-w-0">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getMethodColor(request.endpoint)}`}>
                    {method}
                  </span>
                  <span className="text-sm text-gray-700 truncate flex-1" title={path}>
                    {path}
                  </span>
                </div>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${severityColor}`}>
                  {formatResponseTime(request.response_time)}
                </span>
              </div>
              
              {/* 두 번째 줄: 상태코드, 시간, 추가 정보 */}
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-3">
                  <span className={`font-medium ${getStatusCodeColor(request.status_code)}`}>
                    {request.status_code}
                  </span>
                  <span>
                    {formatRelativeTime(request.timestamp)}
                  </span>
                  {request.client_ip && (
                    <span className="truncate max-w-24" title={request.client_ip}>
                      {request.client_ip}
                    </span>
                  )}
                </div>
                
                {/* 응답시간 바 (상대적 길이) */}
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full ${request.response_time >= 5.0 ? 'bg-red-500' : 
                        request.response_time >= 3.0 ? 'bg-orange-500' : 
                        request.response_time >= 2.0 ? 'bg-yellow-500' : 'bg-blue-500'}`}
                      style={{ width: `${(request.response_time / maxResponseTime) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 통계 요약 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">평균 응답시간:</span>
            <span className="ml-2 font-medium text-gray-900">
              {formatResponseTime(avgResponseTime)}
            </span>
          </div>
          <div>
            <span className="text-gray-500">최고 응답시간:</span>
            <span className="ml-2 font-medium text-gray-900">
              {formatResponseTime(maxResponseTime)}
            </span>
          </div>
        </div>
      </div>

      {/* 심각도 범례 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex flex-wrap gap-3 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-red-100 border border-red-300 rounded"></div>
            <span>5초+ (심각)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-orange-100 border border-orange-300 rounded"></div>
            <span>3-5초 (경고)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-100 border border-yellow-300 rounded"></div>
            <span>2-3초 (주의)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-blue-100 border border-blue-300 rounded"></div>
            <span>2초 미만</span>
          </div>
        </div>
      </div>

      {/* 권장사항 */}
      {displayData.length > 0 && avgResponseTime > 3.0 && (
        <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
          <p className="text-sm text-orange-800">
            <strong>주의:</strong> 평균 응답시간이 {formatResponseTime(avgResponseTime)}로 높습니다. 
            성능 최적화를 고려해보세요.
          </p>
        </div>
      )}
    </div>
  );
}