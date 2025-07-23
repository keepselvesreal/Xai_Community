/**
 * 작업 시간: 2025-07-23
 * 작업 버전: MVP 단계 Sentry 모니터링 시스템 구성
 * 
 * 주요 컴포넌트들:
 * - SentryStatusCard: Sentry 에러 통계 표시 카드
 * - SentryTestActions: Sentry 테스트 액션 버튼들
 * 
 * 함수 정보:
 * - fetchSentryStats() : 백엔드에서 Sentry 통계 조회 (20-35줄)
 * - handleSingleError() : 단일 테스트 에러 생성 (37-50줄)
 * - handleMultipleErrors() : 다중 테스트 에러 생성 (52-70줄)
 * - SentryStatusCard() : 메인 컴포넌트 (72-200줄)
 * 
 * 관련 파일:
 * - backend/nadle_backend/routers/monitoring.py : Sentry API 엔드포인트
 * - app/components/monitoring/UnifiedMonitoringDashboard.tsx : 상위 대시보드
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
  const response = await fetch(`${apiUrl}/api/monitoring/sentry/statistics`);
  
  if (!response.ok) {
    throw new Error('Sentry 통계 조회 실패');
  }
  
  return response.json();
};

const handleSingleError = async () => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/monitoring/test/sentry/error`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  
  if (!response.ok) {
    throw new Error('단일 테스트 에러 생성 실패');
  }
  
  return response.json();
};

const handleMultipleErrors = async (count: number = 3) => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiUrl}/api/monitoring/test/sentry/multiple-errors?count=${count}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  
  if (!response.ok) {
    throw new Error('다중 테스트 에러 생성 실패');
  }
  
  return response.json();
};

const handleFrontendError = async () => {
  try {
    // 더 강력한 방법으로 프론트엔드 에러 생성
    const error = new Error('프론트엔드 테스트 에러 - MVP Sentry 시스템 테스트');
    
    // Sentry가 초기화되어 있는지 확인
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      // 컨텍스트 정보 추가
      (window as any).Sentry.withScope((scope: any) => {
        scope.setTag('test_error', true);
        scope.setTag('source', 'frontend');
        scope.setTag('environment', 'development');
        scope.setTag('user_action', true);
        scope.setLevel('error');
        scope.setContext('test_info', {
          component: 'SentryStatusCard',
          action: 'manual_test',
          timestamp: new Date().toISOString(),
          url: window.location.href,
          userAgent: navigator.userAgent
        });
        scope.setContext('error_details', {
          type: 'frontend_test_error',
          source: 'user_triggered',
          category: 'monitoring_test'
        });
        
        // 사용자 정보 설정 (테스트용)
        scope.setUser({
          id: 'test_user',
          username: '테수',
          email: 'test@example.com'
        });
        
        // fingerprint로 그룹핑 개선
        scope.setFingerprint(['frontend-test-error', 'sentry-status-card']);
        
        // 에러 전송
        (window as any).Sentry.captureException(error);
      });
      
      console.log('✅ 프론트엔드 테스트 에러가 Sentry에 전송되었습니다 (고급 컨텍스트 포함)');
      
      // 강제로 Sentry flush (즉시 전송)
      if ((window as any).Sentry.flush) {
        console.log('🔄 Sentry flush 실행 중...');
        await (window as any).Sentry.flush(5000); // 5초로 늘림
        console.log('✅ Sentry flush 완료');
      }
      
      // 백엔드에서도 프론트엔드 에러를 기록하도록 알림
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        await fetch(`${apiUrl}/api/monitoring/sentry/frontend-error`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: error.message,
            source: 'frontend',
            timestamp: new Date().toISOString(),
            url: window.location.href
          })
        });
        console.log('✅ 백엔드에도 프론트엔드 에러 기록 완료');
      } catch (backendError) {
        console.warn('⚠️ 백엔드 에러 기록 실패:', backendError);
      }
      
    } else {
      // Sentry가 없으면 실제 에러를 발생시켜서 Error Boundary가 잡도록 함
      console.error('⚠️ Sentry가 초기화되지 않았습니다. 실제 에러 발생시킵니다.');
      throw error;
    }
    
    return Promise.resolve({ success: true });
  } catch (err) {
    console.error('프론트엔드 에러 전송 실패:', err);
    // 에러를 다시 throw해서 Error Boundary가 잡도록 함
    throw err;
  }
};

export function SentryStatusCard({ timestamp }: SentryStatusCardProps) {
  const [stats, setStats] = useState<SentryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState<string | null>(null);

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

  const handleTestAction = async (action: () => Promise<any>, type: string) => {
    try {
      setTestLoading(type);
      await action();
      
      // 테스트 후 통계 새로고침
      setTimeout(() => {
        loadStats();
      }, 1000);
      
    } catch (err) {
      console.error(`${type} 실패:`, err);
    } finally {
      setTestLoading(null);
    }
  };

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
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-end mb-4">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(stats?.status || 'unknown')}`}>
          {getStatusText(stats?.status || 'unknown')}
        </span>
      </div>

      {stats && (
        <div className="space-y-4">
          {/* 에러 통계 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.last_hour_errors}</div>
              <div className="text-xs text-gray-500">최근 1시간</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.last_24h_errors}</div>
              <div className="text-xs text-gray-500">최근 24시간</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{stats.last_3d_errors}</div>
              <div className="text-xs text-gray-500">최근 3일</div>
            </div>
          </div>

          {/* 에러율 및 환경 정보 */}
          <div className="flex justify-between text-sm text-gray-600">
            <span>에러율: {stats.error_rate_per_hour}/시간</span>
            <span>환경: {stats.environment}</span>
          </div>

          {/* 최근 에러 목록 */}
          {stats.recent_errors && stats.recent_errors.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">최근 에러</h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {stats.recent_errors.slice(0, 3).map((error, index) => (
                  <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                    <div className="font-medium text-red-600">{error.error_type}</div>
                    <div className="text-gray-600 truncate">{error.message}</div>
                    <div className="text-gray-400">
                      {new Date(error.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 테스트 액션 버튼들 */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">테스트 액션</h4>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleTestAction(() => handleSingleError(), 'single')}
                disabled={testLoading === 'single'}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
              >
                {testLoading === 'single' ? '전송 중...' : '단일 에러'}
              </button>
              
              <button
                onClick={() => handleTestAction(() => handleMultipleErrors(3), 'multiple')}
                disabled={testLoading === 'multiple'}
                className="px-3 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200 disabled:opacity-50"
              >
                {testLoading === 'multiple' ? '전송 중...' : '다중 에러'}
              </button>
              
              <button
                onClick={() => handleTestAction(() => handleFrontendError(), 'frontend')}
                disabled={testLoading === 'frontend'}
                className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
              >
                {testLoading === 'frontend' ? '생성 중...' : '프론트 에러'}
              </button>
              
              <button
                onClick={loadStats}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                새로고침
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SentryStatusCard;