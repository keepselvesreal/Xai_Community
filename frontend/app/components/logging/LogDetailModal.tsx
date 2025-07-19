/**
 * 로그 상세 정보 모달 컴포넌트
 * 
 * 로그의 상세 정보를 모달로 표시하는 컴포넌트
 */
import React from 'react';
import { LogDetailModalProps, LOG_LEVEL_CONFIG, SERVICE_TYPE_CONFIG, LOG_SOURCE_CONFIG } from '~/types/logging';
import { dataUtils, timeUtils } from '~/lib/logging-api';
import Modal from '~/components/ui/Modal';

export function LogDetailModal({
  log,
  isOpen,
  onClose,
  className = ''
}: LogDetailModalProps) {
  if (!log) return null;

  const levelConfig = LOG_LEVEL_CONFIG[log.level];
  const serviceConfig = SERVICE_TYPE_CONFIG[log.service];
  const sourceConfig = LOG_SOURCE_CONFIG[log.source];

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      className={`max-w-4xl ${className}`}
    >
      <div className="p-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">📄</span>
            <h2 className="text-xl font-semibold text-gray-900">로그 상세 정보</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {/* 기본 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                🕐 시간
              </label>
              <div className="text-sm text-gray-900">
                {timeUtils.formatTimestamp(log.timestamp)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {timeUtils.formatRelativeTime(log.timestamp)}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📊 레벨
              </label>
              <div className="flex items-center space-x-2">
                <span className="text-lg">{levelConfig.icon}</span>
                <span className={`text-sm px-3 py-1 rounded ${levelConfig.bgColor} ${levelConfig.textColor} font-medium`}>
                  {levelConfig.label}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                🔧 서비스
              </label>
              <div className="flex items-center space-x-2">
                <span className="text-lg">{serviceConfig.icon}</span>
                <span className={`text-sm px-3 py-1 rounded ${serviceConfig.bgColor} ${serviceConfig.textColor} font-medium`}>
                  {serviceConfig.label}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                🌐 소스
              </label>
              <div className="flex items-center space-x-2">
                <span className="text-lg">{sourceConfig.icon}</span>
                <span className={`text-sm px-3 py-1 rounded ${sourceConfig.bgColor} ${sourceConfig.textColor} font-medium`}>
                  {sourceConfig.label}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📝 메시지
              </label>
              <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded border max-h-32 overflow-y-auto">
                {log.message}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                🆔 로그 ID
              </label>
              <div className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded border">
                {log.id}
              </div>
            </div>
          </div>
        </div>

        {/* 컨텍스트 정보 */}
        {log.context && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              👤 사용자 정보
            </label>
            <div className="bg-gray-50 p-4 rounded border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {log.context.user_id && (
                  <div>
                    <span className="text-xs text-gray-500">User ID:</span>
                    <div className="text-sm text-gray-900">{log.context.user_id}</div>
                  </div>
                )}
                {log.context.ip_address && (
                  <div>
                    <span className="text-xs text-gray-500">IP Address:</span>
                    <div className="text-sm text-gray-900">{log.context.ip_address}</div>
                  </div>
                )}
                {log.context.user_agent && (
                  <div className="md:col-span-2">
                    <span className="text-xs text-gray-500">User Agent:</span>
                    <div className="text-sm text-gray-900 break-all">{log.context.user_agent}</div>
                  </div>
                )}
                {log.context.session_id && (
                  <div>
                    <span className="text-xs text-gray-500">Session ID:</span>
                    <div className="text-sm text-gray-900 font-mono">{log.context.session_id}</div>
                  </div>
                )}
                {log.context.request_id && (
                  <div>
                    <span className="text-xs text-gray-500">Request ID:</span>
                    <div className="text-sm text-gray-900 font-mono">{log.context.request_id}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 요청 정보 */}
        {log.context && (log.context.endpoint || log.context.method || log.context.status_code || log.context.response_time) && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              🌐 요청 정보
            </label>
            <div className="bg-gray-50 p-4 rounded border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {log.context.method && (
                  <div>
                    <span className="text-xs text-gray-500">Method:</span>
                    <div className="text-sm text-gray-900 font-semibold">{log.context.method}</div>
                  </div>
                )}
                {log.context.endpoint && (
                  <div>
                    <span className="text-xs text-gray-500">Endpoint:</span>
                    <div className="text-sm text-gray-900 font-mono">{log.context.endpoint}</div>
                  </div>
                )}
                {log.context.status_code && (
                  <div>
                    <span className="text-xs text-gray-500">Status Code:</span>
                    <div className={`text-sm font-semibold ${
                      log.context.status_code >= 400 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {log.context.status_code}
                    </div>
                  </div>
                )}
                {log.context.response_time && (
                  <div>
                    <span className="text-xs text-gray-500">Response Time:</span>
                    <div className={`text-sm font-semibold ${
                      log.context.response_time > 1000 ? 'text-yellow-600' : 'text-blue-600'
                    }`}>
                      {timeUtils.formatDuration(log.context.response_time)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 인프라 정보 */}
        {log.context && (log.context.infrastructure || log.context.instance_id || log.context.region || log.context.version) && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              🏗️ 인프라 정보
            </label>
            <div className="bg-gray-50 p-4 rounded border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {log.context.infrastructure && (
                  <div>
                    <span className="text-xs text-gray-500">Infrastructure:</span>
                    <div className="text-sm text-gray-900">{log.context.infrastructure}</div>
                  </div>
                )}
                {log.context.instance_id && (
                  <div>
                    <span className="text-xs text-gray-500">Instance ID:</span>
                    <div className="text-sm text-gray-900 font-mono">{log.context.instance_id}</div>
                  </div>
                )}
                {log.context.region && (
                  <div>
                    <span className="text-xs text-gray-500">Region:</span>
                    <div className="text-sm text-gray-900">{log.context.region}</div>
                  </div>
                )}
                {log.context.version && (
                  <div>
                    <span className="text-xs text-gray-500">Version:</span>
                    <div className="text-sm text-gray-900">{log.context.version}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 메타데이터 */}
        {log.metadata && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              🏷️ 메타데이터
            </label>
            <div className="bg-gray-50 p-4 rounded border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {log.metadata.tags && log.metadata.tags.length > 0 && (
                  <div className="md:col-span-2">
                    <span className="text-xs text-gray-500">Tags:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {log.metadata.tags.map((tag, index) => (
                        <span key={index} className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {log.metadata.severity && (
                  <div>
                    <span className="text-xs text-gray-500">Severity:</span>
                    <div className="text-sm text-gray-900">{log.metadata.severity}</div>
                  </div>
                )}
                {log.metadata.error_code && (
                  <div>
                    <span className="text-xs text-gray-500">Error Code:</span>
                    <div className="text-sm text-gray-900">{log.metadata.error_code}</div>
                  </div>
                )}
                {log.metadata.correlation_id && (
                  <div>
                    <span className="text-xs text-gray-500">Correlation ID:</span>
                    <div className="text-sm text-gray-900 font-mono">{log.metadata.correlation_id}</div>
                  </div>
                )}
                {log.metadata.cloud_trace_id && (
                  <div>
                    <span className="text-xs text-gray-500">Cloud Trace ID:</span>
                    <div className="text-sm text-gray-900 font-mono">{log.metadata.cloud_trace_id}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 스택 트레이스 */}
        {log.stack_trace && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              📋 스택 트레이스
            </label>
            <div className="bg-gray-900 text-green-400 p-4 rounded border font-mono text-sm overflow-x-auto max-h-80 overflow-y-auto">
              <pre className="whitespace-pre-wrap">{log.stack_trace}</pre>
            </div>
          </div>
        )}

        {/* 액션 버튼 */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={() => {
              navigator.clipboard.writeText(JSON.stringify(log, null, 2));
              // TODO: 토스트 알림 추가
            }}
            className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
          >
            JSON 복사
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </Modal>
  );
}