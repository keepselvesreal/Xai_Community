/**
 * 헬스 상태 카드 컴포넌트
 * 
 * 시스템의 전반적인 건강 상태를 표시
 */
import type { HealthStatusCardProps } from '~/types/monitoring';

export function HealthStatusCard({ health, loading = false }: HealthStatusCardProps) {
  /**
   * 헬스 상태에 따른 스타일 클래스 반환
   */
  const getStatusStyles = (status?: string) => {
    switch (status) {
      case 'healthy':
        return {
          bg: 'bg-green-50 border-green-200',
          text: 'text-green-800',
          badge: 'bg-green-100 text-green-800',
          icon: 'text-green-500',
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50 border-yellow-200',
          text: 'text-yellow-800',
          badge: 'bg-yellow-100 text-yellow-800',
          icon: 'text-yellow-500',
        };
      case 'critical':
        return {
          bg: 'bg-red-50 border-red-200',
          text: 'text-red-800',
          badge: 'bg-red-100 text-red-800',
          icon: 'text-red-500',
        };
      default:
        return {
          bg: 'bg-gray-50 border-gray-200',
          text: 'text-gray-800',
          badge: 'bg-gray-100 text-gray-800',
          icon: 'text-gray-500',
        };
    }
  };

  /**
   * 헬스 상태 텍스트 변환
   */
  const getStatusText = (status?: string) => {
    switch (status) {
      case 'healthy':
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
   * 백분율 포맷팅
   */
  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  /**
   * 헬스 상태 아이콘
   */
  const StatusIcon = ({ status, className }: { status?: string; className: string }) => {
    switch (status) {
      case 'healthy':
        return (
          <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        );
      case 'warning':
        return (
          <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        );
      case 'critical':
        return (
          <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        );
      default:
        return (
          <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-6 bg-gray-300 rounded w-24"></div>
            <div className="h-6 bg-gray-300 rounded w-16"></div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="h-12 bg-gray-300 rounded"></div>
            <div className="h-12 bg-gray-300 rounded"></div>
            <div className="h-12 bg-gray-300 rounded"></div>
            <div className="h-12 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">
          <StatusIcon status={undefined} className="h-8 w-8 mx-auto mb-2" />
          <p>헬스 상태 정보를 불러올 수 없습니다</p>
        </div>
      </div>
    );
  }

  const styles = getStatusStyles(health.status);
  const statusText = getStatusText(health.status);

  return (
    <div className={`border rounded-lg p-6 ${styles.bg}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <StatusIcon status={health.status} className={`h-6 w-6 ${styles.icon}`} />
          <h2 className={`text-lg font-semibold ${styles.text}`}>시스템 상태</h2>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles.badge}`}>
          {statusText}
        </span>
      </div>

      {/* 메트릭 그리드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* 총 요청 수 */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-gray-900">
            {health.total_requests.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 mt-1">총 요청</div>
        </div>

        {/* 성공 요청 수 */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-green-600">
            {health.success_requests.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 mt-1">성공 요청</div>
        </div>

        {/* 에러 요청 수 */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-red-600">
            {health.error_requests.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 mt-1">에러 요청</div>
        </div>

        {/* 가용성 */}
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="text-2xl font-bold text-blue-600">
            {formatPercentage(health.availability)}
          </div>
          <div className="text-sm text-gray-500 mt-1">가용성</div>
        </div>
      </div>

      {/* 추가 상세 정보 */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">에러율:</span>
          <span className={`font-medium ${
            health.error_rate > 0.05 ? 'text-red-600' : 
            health.error_rate > 0.01 ? 'text-yellow-600' : 'text-green-600'
          }`}>
            {formatPercentage(health.error_rate)}
          </span>
        </div>
        <div className="flex justify-between items-center text-sm mt-2">
          <span className="text-gray-600">마지막 업데이트:</span>
          <span className="text-gray-800">
            {new Date(health.timestamp).toLocaleTimeString('ko-KR')}
          </span>
        </div>
      </div>

      {/* 상태별 권장사항 */}
      {health.status === 'warning' && (
        <div className="mt-4 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>주의:</strong> 에러율이 증가하고 있습니다. 시스템을 모니터링하고 필요시 조치를 취하세요.
          </p>
        </div>
      )}

      {health.status === 'critical' && (
        <div className="mt-4 p-3 bg-red-100 border border-red-300 rounded-lg">
          <p className="text-sm text-red-800">
            <strong>위험:</strong> 높은 에러율이 감지되었습니다. 즉시 시스템을 점검하고 문제를 해결하세요.
          </p>
        </div>
      )}
    </div>
  );
}