/**
 * 작업 시간: 2025-07-23 20:15:00 KST
 * 작업 버전: 정제된 Sentry 모니터링 시스템 (테스트 기능 제거됨)
 * 
 * 주요 컴포넌트들:
 * - SentryStatusCard: 실제 Sentry 에러 통계 및 최근 에러 표시 카드
 * 
 * 함수 정보:
 * - fetchSentryStats() : 백엔드에서 실제 Sentry 에러 정보 조회 (46-55줄)
 * - SentryStatusCard() : 메인 컴포넌트 (58-192줄)
 * - loadStats() : 통계 데이터 로딩 (63-74줄)
 * - getStatusColor() : 상태별 색상 클래스 반환 (81-87줄)
 * - getStatusText() : 상태별 텍스트 반환 (89-97줄)
 * 
 * 코드 라인 정보:
 * - 인터페이스 및 설정: 1-60
 * - 메인 컴포넌트: 58-192
 * - 데이터 로딩: 63-78
 * - UI 렌더링: 99-192
 * 
 * 관련 파일:
 * - backend/nadle_backend/routers/monitoring.py : Sentry API 엔드포인트
 * - backend/nadle_backend/monitoring/sentry_config.py : 개선된 Sentry 필터링
 * - app/components/monitoring/LayeredMonitoring.tsx : 상위 모니터링 대시보드
 */

import { useState, useEffect } from "react";

interface SentryErrorInfo {
  message: string;
  timestamp: string;
  error_type: string;
  file_path?: string;
  line_number?: number;
}

interface SentryStats {
  last_hour_errors: number;
  last_24h_errors: number;
  last_3d_errors: number;
  error_rate_per_hour: number;
  status: string;
  last_error_time?: string;
  environment: string;
  total_events: number;
  recent_errors: SentryErrorInfo[];
}

interface SentryStatusCardProps {
  timestamp?: string;
}

const fetchSentryStats = async (): Promise<SentryStats> => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/monitoring/sentry/errors`);
  
  if (!response.ok) {
    throw new Error('Sentry 에러 정보 조회 실패');
  }
  
  return response.json();
};


export function SentryStatusCard({ timestamp }: SentryStatusCardProps) {
  const [stats, setStats] = useState<SentryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSentryStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [timestamp]);


  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      case 'unconfigured': return 'text-gray-600 bg-gray-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return '정상';
      case 'warning': return '주의';
      case 'critical': return '심각';
      case 'unconfigured': return '미설정';
      case 'error': return '오류';
      default: return status;
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-red-600 text-sm">
          {error}
        </div>
        <button
          onClick={loadStats}
          className="mt-2 text-blue-600 text-sm hover:text-blue-800"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-3">
      <div className="flex justify-end mb-2">
        <span className={`px-1.5 py-0.5 text-xs font-medium rounded-full ${getStatusColor(stats?.status || 'unknown')}`}>
          {getStatusText(stats?.status || 'unknown')}
        </span>
      </div>

      {stats && (
        <div className="space-y-2">
          {/* 에러 통계 */}
          <div className="grid grid-cols-3 gap-2">
            <div className="text-center">
              <div className="text-base font-bold text-red-600">{stats.last_hour_errors}</div>
              <div className="text-xs text-gray-500">최근 1시간</div>
            </div>
            <div className="text-center">
              <div className="text-base font-bold text-orange-600">{stats.last_24h_errors}</div>
              <div className="text-xs text-gray-500">최근 24시간</div>
            </div>
            <div className="text-center">
              <div className="text-base font-bold text-gray-600">{stats.last_3d_errors}</div>
              <div className="text-xs text-gray-500">최근 3일</div>
            </div>
          </div>

          {/* 에러율 및 환경 정보 */}
          <div className="flex justify-between text-xs text-gray-600">
            <span>에러율: {stats.error_rate_per_hour}/시간</span>
            <span>환경: {stats.environment}</span>
          </div>

          {/* 최근 에러 목록 */}
          {stats.recent_errors && stats.recent_errors.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-1">최근 에러</h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {stats.recent_errors.slice(0, 10).map((error, index) => (
                  <div key={index} className="text-xs bg-gray-50 p-1.5 rounded">
                    <div className="font-medium text-red-600 text-xs">{error.error_type}</div>
                    <div className="text-gray-600 truncate text-xs">{error.message}</div>
                    <div className="text-gray-400 text-xs">
                      {new Date(error.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 새로고침 버튼 */}
          <div className="border-t pt-2 flex justify-end">
            <button
              onClick={loadStats}
              className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              새로고침
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default SentryStatusCard;