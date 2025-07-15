/**
 * 통합 모니터링 대시보드 컴포넌트
 * 
 * 환경별 선택과 계층별 모니터링을 통합한 메인 대시보드
 */
import { useState, useEffect } from 'react';
import { EnvironmentSelector, type Environment } from './EnvironmentSelector';
import { LayeredMonitoring } from './LayeredMonitoring';
import { getUnifiedDashboardData, logMonitoringError } from '~/lib/unified-monitoring-api';
import type { UnifiedMonitoringData } from '~/types/unified-monitoring';


interface UnifiedMonitoringDashboardProps {
  className?: string;
}

export function UnifiedMonitoringDashboard({
  className = ''
}: UnifiedMonitoringDashboardProps) {
  const [selectedEnvironment, setSelectedEnvironment] = useState<Environment>('development');
  const [data, setData] = useState<UnifiedMonitoringData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [redisStatus, setRedisStatus] = useState<string>('unknown');

  /**
   * 환경별 Redis 상태 확인
   * - 개발환경: 로컬 Redis 상태 확인
   * - 스테이징/프로덕션: Upstash Redis 상태 확인
   */
  const loadRedisStatus = async () => {
    try {
      const nodeEnv = import.meta.env.VITE_NODE_ENV || 'development';
      let apiEndpoint = '';
      
      if (nodeEnv === 'development') {
        // 개발환경: 로컬 Redis 상태 확인
        apiEndpoint = `${import.meta.env.VITE_API_URL}/api/monitoring/health/cache`;
      } else if (nodeEnv === 'staging' || nodeEnv === 'production') {
        // 스테이징/프로덕션: Upstash Redis 상태 확인
        apiEndpoint = `${import.meta.env.VITE_API_URL}/api/monitoring/infrastructure/upstash/status`;
      }
      
      if (apiEndpoint) {
        const response = await fetch(apiEndpoint);
        const data = await response.json();
        
        if (nodeEnv === 'development') {
          // 로컬 Redis 응답 처리
          setRedisStatus(data.status || 'unknown');
        } else {
          // Upstash Redis 응답 처리
          setRedisStatus(data.status || 'unknown');
        }
      } else {
        setRedisStatus('unknown');
      }
    } catch (error) {
      console.error('Redis 상태 확인 실패:', error);
      setRedisStatus('unhealthy');
    }
  };

  /**
   * 환경별 모니터링 데이터 로드
   */
  const loadData = async (environment: Environment) => {
    try {
      setLoading(true);
      setError(null);
      
      // 새로운 통합 API 클라이언트 사용
      const result = await getUnifiedDashboardData(environment);
      
      if (result.success && result.data) {
        setData(result.data);
      } else {
        const errorMessage = result.error?.message || 'Failed to load monitoring data';
        setError(errorMessage);
        logMonitoringError(result.error, 'UnifiedMonitoringDashboard.loadData');
      }
      
      // 모든 환경에서 Redis 상태 확인 (환경별로 다른 Redis 사용)
      await loadRedisStatus();
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      logMonitoringError(err, 'UnifiedMonitoringDashboard.loadData');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 환경 변경 핸들러
   */
  const handleEnvironmentChange = (environment: Environment) => {
    setSelectedEnvironment(environment);
    loadData(environment);
  };

  /**
   * 새로고침 핸들러
   */
  const handleRefresh = () => {
    loadData(selectedEnvironment);
  };

  /**
   * 초기 데이터 로드
   */
  useEffect(() => {
    loadData(selectedEnvironment);
  }, []);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 환경 선택 */}
      <EnvironmentSelector
        selectedEnvironment={selectedEnvironment}
        onEnvironmentChange={handleEnvironmentChange}
      />
      
      {/* 계층별 모니터링 */}
      <LayeredMonitoring
        environment={selectedEnvironment}
        data={data}
        loading={loading}
        error={error}
        onRefresh={handleRefresh}
        redisStatus={redisStatus}
      />
    </div>
  );
}

export default UnifiedMonitoringDashboard;