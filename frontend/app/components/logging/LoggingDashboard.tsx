/**
 * 작업 시간: 2025-01-23 20:00 (한국 시간)
 * 작업 버전: v2.0
 * 주요 컴포넌트: 통합 로깅 대시보드 (필터와 로그 목록 통합)
 * 
 * 주요 컴포넌트 구성:
 * - LoggingDashboard: 메인 대시보드 컴포넌트 (라인 17-330)
 * - 로그 통계 카드: LogStatsCards (라인 220-230)
 * - 최근 에러 목록: LogErrorTopList (라인 233-239)
 * - 통합 로그 목록: 필터 + 테이블 + 페이지네이션 (라인 242-300)
 * - 로그 상세 모달: LogDetailModal (라인 302-306)
 * 
 * 관련 파일:
 * - LogFilterPanel.tsx: 드롭다운 기반 필터 패널
 * - LogTable.tsx: 로그 테이블 컴포넌트
 * - LogDetailModal.tsx: 로그 상세보기 모달
 */
import React, { useState, useEffect } from 'react';
import { LoggingDashboardProps, LogFilter, LogEntry, LogDashboardResponse } from '~/types/logging';
import { loggingApi, handleApiError, stateUtils, timeUtils } from '~/lib/logging-api';
import { LogStatsCards } from './LogStatsCards';
import { LogErrorTopList } from './LogErrorTopList';
import { LogFilterPanel } from './LogFilterPanel';
import { LogTable } from './LogTable';
import { LogDetailModal } from './LogDetailModal';
import LoadingSpinner from '~/components/common/LoadingSpinner';
import { useNotification } from '~/contexts/NotificationContext';

export function LoggingDashboard({
  autoRefresh = false,
  refreshInterval = 30000,
  initialLoading = true,
  className = ''
}: LoggingDashboardProps) {
  // 상태 관리
  const [dashboardData, setDashboardData] = useState<LogDashboardResponse | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filter, setFilter] = useState<LogFilter>(stateUtils.createInitialFilter());
  const [loading, setLoading] = useState(initialLoading);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const { showError, showSuccess } = useNotification();

  // 대시보드 데이터 로드
  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await loggingApi.getDashboard(24);
      
      if (response.success && response.data) {
        setDashboardData(response.data);
        setLastUpdated(new Date());
      } else {
        const errorMessage = handleApiError(response.error);
        setError(errorMessage);
        showError(`대시보드 로드 실패: ${errorMessage}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류';
      setError(errorMessage);
      showError(`대시보드 로드 실패: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  // 로그 검색
  const searchLogs = async (currentFilter: LogFilter) => {
    try {
      setSearchLoading(true);
      setError(null);

      const response = await loggingApi.searchLogs(currentFilter);
      
      if (response.success && response.data) {
        setLogs(response.data.logs);
        setTotalCount(response.data.total_count);
        setHasNext(response.data.has_next);
        setHasPrev(response.data.has_prev);
      } else {
        const errorMessage = handleApiError(response.error);
        setError(errorMessage);
        showError(`로그 검색 실패: ${errorMessage}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류';
      setError(errorMessage);
      showError(`로그 검색 실패: ${errorMessage}`);
    } finally {
      setSearchLoading(false);
    }
  };

  // 필터 변경 처리
  const handleFilterChange = (newFilter: LogFilter) => {
    setFilter(newFilter);
  };

  // 로그 클릭 처리
  const handleLogClick = (log: LogEntry) => {
    setSelectedLog(log);
    setIsModalOpen(true);
  };

  // 모달 닫기
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedLog(null);
  };

  // 수동 새로고침
  const handleRefresh = async () => {
    await Promise.all([
      loadDashboard(),
      searchLogs(filter)
    ]);
    showSuccess('데이터가 새로고침되었습니다');
  };

  // 페이지 변경
  const handlePageChange = (page: number) => {
    const newFilter = { ...filter, page };
    setFilter(newFilter);
  };

  // 초기 데이터 로드
  useEffect(() => {
    const loadInitialData = async () => {
      await Promise.all([
        loadDashboard(),
        searchLogs(filter)
      ]);
    };
    
    loadInitialData();
  }, []);

  // 필터 변경 시 로그 검색
  useEffect(() => {
    if (filter !== stateUtils.createInitialFilter()) {
      searchLogs(filter);
    }
  }, [filter]);

  // 자동 새로고침 설정
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      handleRefresh();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, filter]);

  // 로딩 상태
  if (loading && !dashboardData) {
    return (
      <div className={`logging-dashboard ${className}`}>
        <div className="flex items-center justify-center min-h-96">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">로깅 대시보드 로딩 중...</span>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error && !dashboardData) {
    return (
      <div className={`logging-dashboard ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            로깅 대시보드 로딩 실패
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

  return (
    <div className={`logging-dashboard space-y-6 ${className}`}>
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            로그 목록
          </h1>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              마지막 업데이트: {timeUtils.formatTimestamp(lastUpdated.toISOString())}
            </span>
          )}
          {autoRefresh && (
            <span className="text-sm text-green-600 bg-green-100 px-2 py-1 rounded">
              자동 새로고침 활성
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading || searchLoading}
            className={`px-4 py-2 rounded transition-colors ${
              loading || searchLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading || searchLoading ? '로딩 중...' : '새로고침'}
          </button>
        </div>
      </div>

      {/* 요약 통계 */}
      {dashboardData && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            📊 요약 통계 (최근 24시간)
          </h2>
          <LogStatsCards
            stats={dashboardData.stats}
            loading={loading}
          />
        </div>
      )}

      {/* 최근 에러 TOP 5 */}
      {dashboardData && (
        <LogErrorTopList
          errors={dashboardData.recent_errors}
          loading={loading}
          maxItems={5}
        />
      )}

      {/* 로그 목록 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {/* 통합된 헤더와 필터 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900">
              📋 로그 목록
            </h2>
            <span className="text-sm text-gray-500">
              총 {totalCount.toLocaleString()}개
            </span>
            <span className="text-sm text-gray-500">
              페이지: {filter.page || 1}
            </span>
          </div>
        </div>
        
        {/* 필터링 패널 */}
        <LogFilterPanel
          filter={filter}
          onFilterChange={handleFilterChange}
          loading={searchLoading}
        />

        {/* 로그 테이블 */}
        <LogTable
          logs={logs}
          loading={searchLoading}
          onLogClick={handleLogClick}
        />

        {/* 페이지네이션 */}
        {totalCount > 0 && (
          <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-500">
              {((filter.page || 1) - 1) * (filter.page_size || 50) + 1} - {Math.min((filter.page || 1) * (filter.page_size || 50), totalCount)} / {totalCount}
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange((filter.page || 1) - 1)}
                disabled={!hasPrev || searchLoading}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                이전
              </button>
              <span className="text-sm text-gray-600">
                {filter.page || 1}
              </span>
              <button
                onClick={() => handlePageChange((filter.page || 1) + 1)}
                disabled={!hasNext || searchLoading}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                다음
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 로그 상세 모달 */}
      <LogDetailModal
        log={selectedLog}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />

      {/* 에러 알림 (데이터가 있지만 에러가 있는 경우) */}
      {error && dashboardData && (
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