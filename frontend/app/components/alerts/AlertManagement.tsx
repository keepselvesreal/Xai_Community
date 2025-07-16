import React, { useState, useEffect, useCallback } from 'react';
import { useNotification } from '~/contexts/NotificationContext';
import type { AlertRule, AlertStatistics, AlertSeverity } from '~/types';
import api from '~/lib/api';

interface AlertManagementProps {
  className?: string;
}

const AlertManagement: React.FC<AlertManagementProps> = ({ className = '' }) => {
  const { showSuccess, showError } = useNotification();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [statistics, setStatistics] = useState<AlertStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedRule, setSelectedRule] = useState<AlertRule | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [availableMetrics, setAvailableMetrics] = useState<any[]>([]);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);

  // 폼 상태
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    condition: 'greater_than',
    threshold: {
      metric: '',
      value: 0,
      duration_minutes: 5
    },
    severity: 'medium' as AlertSeverity,
    channels: [] as string[],
    cooldown_minutes: 30,
    escalation_minutes: 60,
    enabled: true,
    tags: {} as Record<string, string>
  });

  // 메트릭 데이터 로드
  const loadMetrics = useCallback(async () => {
    try {
      setMetricsLoading(true);
      const response = await api.getAvailableMetrics();
      if (response.success && response.data) {
        setAvailableMetrics(response.data.metrics || []);
      }
    } catch (err) {
      console.error('메트릭 목록 로드 실패:', err);
    } finally {
      setMetricsLoading(false);
    }
  }, []);

  // 시스템 헬스체크
  const checkSystemHealth = useCallback(async () => {
    try {
      setHealthLoading(true);
      const response = await api.getAlertSystemHealth();
      if (response.success && response.data) {
        setSystemHealth(response.data);
      }
    } catch (err) {
      console.error('시스템 헬스체크 실패:', err);
      showError('시스템 상태 확인 중 오류가 발생했습니다');
    } finally {
      setHealthLoading(false);
    }
  }, [showError]);

  // 시스템 테스트
  const testAlertSystem = useCallback(async () => {
    try {
      setTestLoading(true);
      const response = await api.testAlertSystem();
      if (response.success && response.data) {
        if (response.data.test_status === 'success') {
          showSuccess('알림 시스템 테스트가 성공적으로 완료되었습니다');
        } else {
          showError(`알림 시스템 테스트 실패: ${response.data.error || '알 수 없는 오류'}`);
        }
      } else {
        showError('알림 시스템 테스트 실패');
      }
    } catch (err) {
      console.error('알림 시스템 테스트 실패:', err);
      showError('알림 시스템 테스트 중 오류가 발생했습니다');
    } finally {
      setTestLoading(false);
    }
  }, [showSuccess, showError]);

  // 데이터 로드
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [rulesResponse, statsResponse] = await Promise.all([
        api.getAlertRules(),
        api.getAlertStatistics()
      ]);

      if (rulesResponse.success && rulesResponse.data) {
        setRules(rulesResponse.data.rules || []);
      }

      if (statsResponse.success && statsResponse.data) {
        setStatistics(statsResponse.data);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류';
      setError(errorMessage);
      
      if (errorMessage.includes('Network')) {
        showError('네트워크 연결을 확인해주세요');
      } else {
        showError('알림 규칙을 불러오는 중 오류가 발생했습니다');
      }
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadData();
    loadMetrics();
    checkSystemHealth();
  }, [loadData, loadMetrics, checkSystemHealth]);

  // 필터링된 규칙 목록
  const filteredRules = rules.filter(rule => {
    const matchesSearch = rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         rule.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = severityFilter === 'all' || rule.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && rule.enabled) ||
                         (statusFilter === 'inactive' && !rule.enabled);
    
    return matchesSearch && matchesSeverity && matchesStatus;
  });

  // 폼 초기화
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      condition: 'greater_than',
      threshold: {
        metric: '',
        value: 0,
        duration_minutes: 5
      },
      severity: 'medium' as AlertSeverity,
      channels: [],
      cooldown_minutes: 30,
      escalation_minutes: 60,
      enabled: true,
      tags: {}
    });
  };

  // 채널 선택 토글
  const toggleChannel = (channel: string) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  // 선택된 메트릭 정보 가져오기
  const getSelectedMetricInfo = (metricName: string) => {
    return availableMetrics.find(m => m.name === metricName);
  };

  // 규칙 생성
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.createAlertRule(formData);
      if (response.success) {
        showSuccess('알림 규칙이 생성되었습니다');
        setShowCreateModal(false);
        resetForm();
        loadData();
      } else {
        showError('알림 규칙 생성에 실패했습니다');
      }
    } catch (err) {
      showError('알림 규칙 생성 중 오류가 발생했습니다');
    }
  };

  // 규칙 수정
  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRule) return;
    
    try {
      const response = await api.updateAlertRule(selectedRule.id, formData);
      if (response.success) {
        showSuccess('알림 규칙이 수정되었습니다');
        setShowEditModal(false);
        resetForm();
        setSelectedRule(null);
        loadData();
      } else {
        showError('알림 규칙 수정에 실패했습니다');
      }
    } catch (err) {
      showError('알림 규칙 수정 중 오류가 발생했습니다');
    }
  };

  // 규칙 삭제
  const handleDelete = async () => {
    if (!selectedRule) return;
    
    try {
      const response = await api.deleteAlertRule(selectedRule.id);
      if (response.success) {
        showSuccess('알림 규칙이 삭제되었습니다');
        setShowDeleteModal(false);
        setSelectedRule(null);
        loadData();
      } else {
        showError('알림 규칙 삭제에 실패했습니다');
      }
    } catch (err) {
      showError('알림 규칙 삭제 중 오류가 발생했습니다');
    }
  };

  // 수정 모달 열기
  const openEditModal = (rule: AlertRule) => {
    setSelectedRule(rule);
    setFormData({
      name: rule.name,
      description: rule.description,
      condition: rule.condition,
      threshold: rule.threshold,
      severity: rule.severity,
      channels: rule.channels,
      cooldown_minutes: rule.cooldown_minutes,
      escalation_minutes: rule.escalation_minutes,
      enabled: rule.enabled,
      tags: rule.tags
    });
    setShowEditModal(true);
  };

  // 삭제 모달 열기
  const openDeleteModal = (rule: AlertRule) => {
    setSelectedRule(rule);
    setShowDeleteModal(true);
  };

  // 심각도 색상 클래스
  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">알림 규칙을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error.includes('Network') ? '네트워크 연결을 확인해주세요' : '알림 규칙을 불러오는 중 오류가 발생했습니다'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">알림 관리</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          새 알림 규칙
        </button>
      </div>

      {/* 통계 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">총 규칙 수</div>
            <div className="text-2xl font-bold text-gray-900">{statistics.total_rules}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">활성 규칙</div>
            <div className="text-2xl font-bold text-green-600">{statistics.active_rules}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">총 알림</div>
            <div className="text-2xl font-bold text-blue-600">{statistics.total_alerts}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">오늘 전송된 알림</div>
            <div className="text-2xl font-bold text-purple-600">{statistics.alerts_sent_today}</div>
          </div>
        </div>
      )}

      {/* 시스템 상태 및 점검 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">🔧 시스템 상태 점검</h3>
          <div className="flex space-x-2">
            <button
              onClick={checkSystemHealth}
              disabled={healthLoading}
              className="px-4 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50"
            >
              {healthLoading ? '확인 중...' : '상태 확인'}
            </button>
            <button
              onClick={testAlertSystem}
              disabled={testLoading}
              className="px-4 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50"
            >
              {testLoading ? '테스트 중...' : '시스템 테스트'}
            </button>
          </div>
        </div>

        {systemHealth ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 전체 상태 */}
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">전체 상태</h4>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.status === 'healthy' ? 'bg-green-500' :
                  systemHealth.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm font-medium capitalize">{systemHealth.status}</span>
                <span className="text-xs text-gray-500">({systemHealth.service})</span>
              </div>
              {systemHealth.last_check && (
                <p className="text-xs text-gray-500">
                  마지막 확인: {new Date(systemHealth.last_check).toLocaleString('ko-KR')}
                </p>
              )}
            </div>

            {/* 서비스별 상태 */}
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">서비스별 상태</h4>
              <div className="space-y-2">
                {systemHealth.services && Object.entries(systemHealth.services).map(([service, status]) => (
                  <div key={service} className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{service.replace('_', ' ')}</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        status === 'healthy' ? 'bg-green-500' :
                        status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></div>
                      <span className={`text-xs capitalize ${
                        status === 'healthy' ? 'text-green-700' :
                        status === 'degraded' ? 'text-yellow-700' : 'text-red-700'
                      }`}>{status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 시스템 메트릭 */}
            {systemHealth.metrics && (
              <div className="md:col-span-2 space-y-3">
                <h4 className="font-medium text-gray-900">시스템 메트릭</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(systemHealth.metrics).map(([key, value]) => (
                    <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-lg font-semibold text-gray-900">{String(value)}</div>
                      <div className="text-xs text-gray-600">{key.replace('_', ' ')}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="animate-pulse">시스템 상태를 확인하는 중...</div>
          </div>
        )}

        {/* 점검 가이드 */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">📋 알림 시스템 점검 가이드</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>상태 확인:</strong> 시스템 구성 요소들의 실시간 상태를 점검합니다</li>
            <li>• <strong>시스템 테스트:</strong> 테스트 알림 규칙으로 전체 시스템 기능을 검증합니다</li>
            <li>• <strong>정기 점검:</strong> 매일 오전에 상태를 확인하여 문제를 조기에 발견하세요</li>
            <li>• <strong>문제 발생 시:</strong> 빨간색 상태가 표시되면 시스템 관리자에게 문의하세요</li>
          </ul>
        </div>
      </div>

      {/* 필터 */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <input
              type="text"
              placeholder="알림 규칙 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity | 'all')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="심각도 필터"
            >
              <option value="all">모든 심각도</option>
              <option value="low">낮음</option>
              <option value="medium">보통</option>
              <option value="high">높음</option>
              <option value="critical">긴급</option>
            </select>
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="상태 필터"
            >
              <option value="all">모든 상태</option>
              <option value="active">활성</option>
              <option value="inactive">비활성</option>
            </select>
          </div>
        </div>
      </div>

      {/* 규칙 목록 */}
      <div className="bg-white rounded-lg shadow">
        {filteredRules.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-gray-500">
              <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-lg font-medium">설정된 알림 규칙이 없습니다</p>
              <p className="text-sm mt-2">첫 번째 알림 규칙을 생성해보세요!</p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">규칙 이름</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">설명</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">심각도</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">채널</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{rule.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 max-w-xs truncate">{rule.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(rule.severity)}`}>
                        {rule.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {rule.enabled ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {rule.channels.map((channel) => (
                          <span key={channel} className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                            {channel}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => openEditModal(rule)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => openDeleteModal(rule)}
                        className="text-red-600 hover:text-red-900"
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 생성 모달 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">알림 규칙 생성</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">규칙 이름</label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  required
                />
              </div>
              <div>
                <label htmlFor="condition" className="block text-sm font-medium text-gray-700 mb-1">조건</label>
                <select
                  id="condition"
                  value={formData.condition}
                  onChange={(e) => setFormData({...formData, condition: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="greater_than">보다 큰</option>
                  <option value="less_than">보다 작은</option>
                  <option value="equals">같음</option>
                </select>
              </div>
              <div>
                <label htmlFor="metric" className="block text-sm font-medium text-gray-700 mb-1">메트릭</label>
                <select
                  id="metric"
                  value={formData.threshold.metric}
                  onChange={(e) => setFormData({...formData, threshold: {...formData.threshold, metric: e.target.value}})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={metricsLoading}
                >
                  <option value="">메트릭을 선택하세요</option>
                  {availableMetrics.map((metric) => (
                    <option key={metric.name} value={metric.name}>
                      {metric.display_name} ({metric.unit})
                    </option>
                  ))}
                </select>
                {formData.threshold.metric && getSelectedMetricInfo(formData.threshold.metric) && (
                  <p className="text-xs text-gray-500 mt-1">
                    {getSelectedMetricInfo(formData.threshold.metric)?.description}
                  </p>
                )}
              </div>
              <div>
                <label htmlFor="value" className="block text-sm font-medium text-gray-700 mb-1">임계값</label>
                <input
                  type="number"
                  id="value"
                  value={formData.threshold.value}
                  onChange={(e) => setFormData({...formData, threshold: {...formData.threshold, value: Number(e.target.value)}})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label htmlFor="severity" className="block text-sm font-medium text-gray-700 mb-1">심각도</label>
                <select
                  id="severity"
                  value={formData.severity}
                  onChange={(e) => setFormData({...formData, severity: e.target.value as AlertSeverity})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">낮음</option>
                  <option value="medium">보통</option>
                  <option value="high">높음</option>
                  <option value="critical">긴급</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">알림 채널</label>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="email-channel"
                      checked={formData.channels.includes('email')}
                      onChange={() => toggleChannel('email')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="email-channel" className="ml-2 text-sm text-gray-700 flex items-center">
                      📧 이메일 알림
                      <span className="ml-2 text-xs text-gray-500">(실시간 이메일 발송)</span>
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="discord-channel"
                      checked={formData.channels.includes('discord')}
                      onChange={() => toggleChannel('discord')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="discord-channel" className="ml-2 text-sm text-gray-700 flex items-center">
                      💬 디스코드 알림
                      <span className="ml-2 text-xs text-gray-500">(디스코드 웹훅 발송)</span>
                    </label>
                  </div>
                </div>
                {formData.channels.length === 0 && (
                  <p className="text-xs text-red-500 mt-1">최소 하나의 알림 채널을 선택해주세요</p>
                )}
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={formData.channels.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  생성
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 수정 모달 */}
      {showEditModal && selectedRule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">알림 규칙 수정</h3>
            <form onSubmit={handleEdit} className="space-y-4">
              <div>
                <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700 mb-1">규칙 이름</label>
                <input
                  type="text"
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label htmlFor="edit-description" className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                <textarea
                  id="edit-description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  required
                />
              </div>
              <div>
                <label htmlFor="edit-condition" className="block text-sm font-medium text-gray-700 mb-1">조건</label>
                <select
                  id="edit-condition"
                  value={formData.condition}
                  onChange={(e) => setFormData({...formData, condition: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="greater_than">보다 큰</option>
                  <option value="less_than">보다 작은</option>
                  <option value="equals">같음</option>
                </select>
              </div>
              <div>
                <label htmlFor="edit-metric" className="block text-sm font-medium text-gray-700 mb-1">메트릭</label>
                <select
                  id="edit-metric"
                  value={formData.threshold.metric}
                  onChange={(e) => setFormData({...formData, threshold: {...formData.threshold, metric: e.target.value}})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={metricsLoading}
                >
                  <option value="">메트릭을 선택하세요</option>
                  {availableMetrics.map((metric) => (
                    <option key={metric.name} value={metric.name}>
                      {metric.display_name} ({metric.unit})
                    </option>
                  ))}
                </select>
                {formData.threshold.metric && getSelectedMetricInfo(formData.threshold.metric) && (
                  <p className="text-xs text-gray-500 mt-1">
                    {getSelectedMetricInfo(formData.threshold.metric)?.description}
                  </p>
                )}
              </div>
              <div>
                <label htmlFor="edit-value" className="block text-sm font-medium text-gray-700 mb-1">임계값</label>
                <input
                  type="number"
                  id="edit-value"
                  value={formData.threshold.value}
                  onChange={(e) => setFormData({...formData, threshold: {...formData.threshold, value: Number(e.target.value)}})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label htmlFor="edit-severity" className="block text-sm font-medium text-gray-700 mb-1">심각도</label>
                <select
                  id="edit-severity"
                  value={formData.severity}
                  onChange={(e) => setFormData({...formData, severity: e.target.value as AlertSeverity})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">낮음</option>
                  <option value="medium">보통</option>
                  <option value="high">높음</option>
                  <option value="critical">긴급</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">알림 채널</label>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="edit-email-channel"
                      checked={formData.channels.includes('email')}
                      onChange={() => toggleChannel('email')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="edit-email-channel" className="ml-2 text-sm text-gray-700 flex items-center">
                      📧 이메일 알림
                      <span className="ml-2 text-xs text-gray-500">(실시간 이메일 발송)</span>
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="edit-discord-channel"
                      checked={formData.channels.includes('discord')}
                      onChange={() => toggleChannel('discord')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="edit-discord-channel" className="ml-2 text-sm text-gray-700 flex items-center">
                      💬 디스코드 알림
                      <span className="ml-2 text-xs text-gray-500">(디스코드 웹훅 발송)</span>
                    </label>
                  </div>
                </div>
                {formData.channels.length === 0 && (
                  <p className="text-xs text-red-500 mt-1">최소 하나의 알림 채널을 선택해주세요</p>
                )}
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedRule(null);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={formData.channels.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  수정
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 삭제 모달 */}
      {showDeleteModal && selectedRule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">알림 규칙 삭제</h3>
            <p className="text-gray-600 mb-4">정말로 이 알림 규칙을 삭제하시겠습니까?</p>
            <div className="bg-gray-50 p-3 rounded-lg mb-4">
              <p className="font-medium">{selectedRule.name}</p>
              <p className="text-sm text-gray-600">{selectedRule.description}</p>
            </div>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setSelectedRule(null);
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertManagement;