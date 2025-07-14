import React, { useState, useEffect } from 'react';
import { AnalyticsService } from '~/lib/analytics-service';

interface GA4TestPanelProps {
  className?: string;
}

export default function GA4TestPanel({ className }: GA4TestPanelProps) {
  const [eventName, setEventName] = useState('test_event');
  const [eventParams, setEventParams] = useState('{"category": "test", "action": "click"}');
  const [lastEvent, setLastEvent] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsService | null>(null);

  useEffect(() => {
    const analyticsService = new AnalyticsService();
    setAnalytics(analyticsService);
  }, []);

  const handleSendEvent = () => {
    if (!analytics) return;
    
    try {
      const params = JSON.parse(eventParams);
      analytics.trackEvent(eventName, params);
      setLastEvent(`${eventName}: ${JSON.stringify(params)}`);
    } catch (error) {
      console.error('이벤트 전송 오류:', error);
      setLastEvent(`오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    }
  };

  const handleSendPredefinedEvents = () => {
    if (!analytics) return;

    // 사용자 참여 이벤트 테스트
    analytics.trackUserEngagement(3000);

    // 페이지 뷰 이벤트 테스트
    analytics.trackPageView(window.location.pathname, document.title);

    // 커스텀 이벤트 테스트
    analytics.trackEvent('custom_interaction', {
      event_category: 'GA4_Test',
      event_label: 'Test_Button_Click',
      value: 1
    });

    setLastEvent('사전 정의된 이벤트 3개 전송 완료');
  };

  const handleSendConversionEvents = () => {
    if (!analytics) return;

    // 전환 이벤트 테스트
    analytics.trackSignUpConversion('test_user_123', 'email');
    analytics.trackLoginConversion('test_user_123', 'email');
    analytics.trackPostCreationConversion('test_post_456', 'board');

    setLastEvent('전환 이벤트 3개 전송 완료');
  };

  const handleSendFunnelEvents = () => {
    if (!analytics) return;

    // 퍼널 분석 이벤트 테스트
    analytics.trackFunnelStep('user_signup', 'email_input', 1);
    analytics.trackFunnelStep('user_signup', 'email_verification', 2);
    analytics.trackFunnelComplete('user_signup', 3, 120000);

    setLastEvent('퍼널 이벤트 3개 전송 완료');
  };

  const isConnected = analytics?.isConnected() || false;

  return (
    <div className={`p-6 border rounded-lg bg-white shadow-sm ${className}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-800">GA4 테스트 패널</h3>
      
      {/* 연결 상태 표시 */}
      <div className="mb-4 p-3 rounded-lg bg-gray-50">
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="font-medium">
            GA4 연결 상태: {isConnected ? '연결됨' : '연결 안됨'}
          </span>
        </div>
        <div className="text-sm text-gray-600">
          측정 ID: {analytics?.getMeasurementId() || '설정되지 않음'}
        </div>
      </div>

      {/* 이벤트 전송 폼 */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            이벤트 이름
          </label>
          <input
            type="text"
            value={eventName}
            onChange={(e) => setEventName(e.target.value)}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="이벤트 이름"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            이벤트 매개변수 (JSON)
          </label>
          <textarea
            value={eventParams}
            onChange={(e) => setEventParams(e.target.value)}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            placeholder='{"category": "test", "action": "click"}'
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          <button
            onClick={handleSendEvent}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            이벤트 전송
          </button>
          <button
            onClick={handleSendPredefinedEvents}
            className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
          >
            기본 이벤트 전송
          </button>
          <button
            onClick={handleSendConversionEvents}
            className="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors"
          >
            전환 이벤트 전송
          </button>
          <button
            onClick={handleSendFunnelEvents}
            className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
          >
            퍼널 이벤트 전송
          </button>
        </div>

        {/* 마지막 이벤트 표시 */}
        {lastEvent && (
          <div className="mt-4 p-3 bg-gray-100 rounded-md">
            <div className="text-sm font-medium text-gray-700 mb-1">마지막 전송된 이벤트:</div>
            <div className="text-sm text-gray-600 font-mono break-all">{lastEvent}</div>
          </div>
        )}

        {/* 사용법 안내 */}
        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h4 className="font-medium text-blue-800 mb-2">GA4 실시간 확인 방법</h4>
          <ol className="text-sm text-blue-700 space-y-1">
            <li>1. Google Analytics 4 (analytics.google.com) 접속</li>
            <li>2. 왼쪽 메뉴에서 "보고서" → "실시간" 클릭</li>
            <li>3. 위 버튼들을 클릭하여 이벤트 전송</li>
            <li>4. 실시간 보고서에서 이벤트 확인</li>
          </ol>
        </div>
      </div>
    </div>
  );
}