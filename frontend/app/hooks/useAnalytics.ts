import { useEffect, useState } from 'react';
import { AnalyticsService } from '~/lib/analytics-service';

let analyticsInstance: AnalyticsService | null = null;

export function useAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsService | null>(null);

  useEffect(() => {
    if (!analyticsInstance) {
      analyticsInstance = new AnalyticsService();
    }
    setAnalytics(analyticsInstance);
  }, []);

  return analytics;
}

// 전역 인스턴스 직접 접근을 위한 함수
export function getAnalytics(): AnalyticsService {
  if (!analyticsInstance) {
    analyticsInstance = new AnalyticsService();
  }
  return analyticsInstance;
}