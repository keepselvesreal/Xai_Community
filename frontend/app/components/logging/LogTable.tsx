/**
 * 로그 테이블 컴포넌트
 * 
 * 로그 목록을 테이블 형태로 표시하는 컴포넌트
 */
import React from 'react';
import { LogTableProps, LOG_LEVEL_CONFIG, SERVICE_TYPE_CONFIG, LOG_SOURCE_CONFIG } from '~/types/logging';
import { dataUtils, timeUtils } from '~/lib/logging-api';
import LoadingSpinner from '~/components/common/LoadingSpinner';

export function LogTable({
  logs,
  loading = false,
  className = '',
  onLogClick
}: LogTableProps) {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
        <div className="p-6">
          <div className="flex items-center justify-center">
            <LoadingSpinner />
            <span className="ml-2 text-gray-600">로그 데이터 로딩 중...</span>
          </div>
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
        <div className="p-8 text-center">
          <div className="text-4xl mb-4">📋</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">로그가 없습니다</h3>
          <p className="text-gray-600">선택한 조건에 맞는 로그가 없습니다.</p>
          <p className="text-sm text-gray-500 mt-1">필터 조건을 조정해보세요.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                시간
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                레벨
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                서비스
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                소스
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                지역/인스턴스
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                메시지
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                액션
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs.map((log) => {
              const levelConfig = LOG_LEVEL_CONFIG[log.level];
              const serviceConfig = SERVICE_TYPE_CONFIG[log.service];
              const sourceConfig = LOG_SOURCE_CONFIG[log.source];
              const isRecent = new Date(log.timestamp).getTime() > Date.now() - 5 * 60 * 1000; // 5분 이내
              const hasError = log.level === 'ERROR';
              const hasStackTrace = !!log.stack_trace;

              return (
                <tr
                  key={log.id}
                  className={`hover:bg-gray-50 transition-colors ${
                    hasError ? 'bg-red-50' : ''
                  } ${isRecent ? 'border-l-4 border-l-blue-500' : ''}`}
                >
                  {/* 시간 */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {(() => {
                          // timeUtils의 공통 함수 사용
                          const parts = log.timestamp.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
                          if (!parts) return log.timestamp;
                          
                          const [, year, month, day, utcHour, minute, second] = parts;
                          let koreaHour = parseInt(utcHour) + 9;
                          
                          // 24시간을 넘으면 다음날로
                          if (koreaHour >= 24) {
                            koreaHour -= 24;
                          }
                          
                          // 오전/오후 계산
                          const ampm = koreaHour >= 12 ? '오후' : '오전';
                          const displayHour = koreaHour === 0 ? 12 : (koreaHour > 12 ? koreaHour - 12 : koreaHour);
                          
                          return `${ampm} ${displayHour.toString().padStart(2, '0')}:${minute}:${second}`;
                        })()}
                      </span>
                      <span className="text-xs text-gray-500">
                        {(() => {
                          // UTC 날짜를 한국 시간으로 직접 계산
                          const parts = log.timestamp.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
                          if (!parts) return log.timestamp;
                          
                          const [, year, month, day, utcHour] = parts;
                          let koreaDay = parseInt(day);
                          let koreaMonth = parseInt(month);
                          let koreaYear = parseInt(year);
                          
                          // UTC 시간에 9시간을 더해서 다음날이 되는지 확인
                          if (parseInt(utcHour) + 9 >= 24) {
                            koreaDay += 1;
                            
                            // 월말 처리 (간단한 버전)
                            const daysInMonth = new Date(koreaYear, koreaMonth, 0).getDate();
                            if (koreaDay > daysInMonth) {
                              koreaDay = 1;
                              koreaMonth += 1;
                              if (koreaMonth > 12) {
                                koreaMonth = 1;
                                koreaYear += 1;
                              }
                            }
                          }
                          
                          return `${koreaYear}. ${koreaMonth.toString().padStart(2, '0')}. ${koreaDay.toString().padStart(2, '0')}.`;
                        })()}
                      </span>
                    </div>
                    {isRecent && (
                      <div className="text-xs text-blue-600 font-medium mt-1">
                        방금 전
                      </div>
                    )}
                  </td>

                  {/* 레벨 */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{levelConfig.icon}</span>
                      <span className={`text-xs px-2 py-1 rounded ${levelConfig.bgColor} ${levelConfig.textColor} font-medium`}>
                        {levelConfig.label}
                      </span>
                    </div>
                  </td>

                  {/* 서비스 */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{serviceConfig.icon}</span>
                      <span className={`text-xs px-2 py-1 rounded ${serviceConfig.bgColor} ${serviceConfig.textColor} font-medium`}>
                        {serviceConfig.label}
                      </span>
                    </div>
                  </td>

                  {/* 소스 */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{sourceConfig.icon}</span>
                      <span className={`text-xs px-2 py-1 rounded ${sourceConfig.bgColor} ${sourceConfig.textColor} font-medium`}>
                        {sourceConfig.label}
                      </span>
                    </div>
                  </td>

                  {/* 지역/인스턴스 */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="space-y-1">
                      {log.context?.region && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-500">지역:</span>
                          <span className="text-xs font-medium">
                            {log.context.region === 'asia-northeast3' ? '🇰🇷 Seoul' :
                             log.context.region === 'asia-northeast1' ? '🇯🇵 Tokyo' :
                             log.context.region === 'us-central1' ? '🇺🇸 US Central' :
                             log.context.region === 'europe-west1' ? '🇪🇺 Europe West' :
                             `❓ ${log.context.region}`}
                          </span>
                        </div>
                      )}
                      {log.context?.instance_id && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-500">인스턴스:</span>
                          <span className="text-xs font-mono bg-gray-100 px-1 rounded">
                            {log.context.instance_id.slice(-8)}
                          </span>
                        </div>
                      )}
                      {log.context?.infrastructure && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-500">인프라:</span>
                          <span className="text-xs font-medium">
                            {log.context.infrastructure === 'gcp' ? '☁️ GCP' :
                             log.context.infrastructure === 'vercel' ? '🚀 Vercel' :
                             log.context.infrastructure === 'upstash' ? '⚡ Upstash' :
                             log.context.infrastructure === 'atlas' ? '🗄️ Atlas' :
                             log.context.infrastructure === 'local' ? '🏠 Local' :
                             log.context.infrastructure}
                          </span>
                        </div>
                      )}
                      {log.metadata?.vercel_deployment_id && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs text-gray-500">배포:</span>
                          <span className="text-xs font-mono bg-blue-100 px-1 rounded">
                            {log.metadata.vercel_deployment_id.slice(-8)}
                          </span>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* 메시지 */}
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-md">
                    <div className="space-y-1">
                      <p className="line-clamp-2">
                        {dataUtils.truncateText(log.message, 120)}
                      </p>
                      
                      {/* 컨텍스트 정보 */}
                      {log.context && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {log.context.endpoint && (
                            <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                              {log.context.method || 'GET'} {log.context.endpoint}
                            </span>
                          )}
                          {log.context.status_code && (
                            <span className={`text-xs px-2 py-1 rounded ${
                              log.context.status_code >= 400 
                                ? 'bg-red-100 text-red-700' 
                                : 'bg-green-100 text-green-700'
                            }`}>
                              {log.context.status_code}
                            </span>
                          )}
                          {log.context.response_time && (
                            <span className={`text-xs px-2 py-1 rounded ${
                              log.context.response_time > 1000 
                                ? 'bg-yellow-100 text-yellow-700' 
                                : 'bg-blue-100 text-blue-700'
                            }`}>
                              {timeUtils.formatDuration(log.context.response_time)}
                            </span>
                          )}
                          {log.context.user_id && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                              User: {log.context.user_id}
                            </span>
                          )}
                          {log.context.session_id && (
                            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                              Session: {log.context.session_id.slice(-8)}
                            </span>
                          )}
                          {log.context.request_id && (
                            <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                              ReqID: {log.context.request_id.slice(-8)}
                            </span>
                          )}
                        </div>
                      )}

                      {/* 메타데이터 태그 */}
                      {log.metadata?.tags && log.metadata.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {log.metadata.tags.slice(0, 3).map((tag, index) => (
                            <span key={index} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                          {log.metadata.tags.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{log.metadata.tags.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </td>

                  {/* 액션 */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => onLogClick?.(log)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        상세보기
                      </button>
                      {hasStackTrace && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                          Stack Trace
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}