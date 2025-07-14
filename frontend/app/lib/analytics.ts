// GA4 글로벌 타입 정의
declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

// GA4 측정 ID 가져오기
export const GA_MEASUREMENT_ID = typeof window !== 'undefined' 
  ? import.meta.env.VITE_GA_MEASUREMENT_ID_DEV
  : process.env.VITE_GA_MEASUREMENT_ID_DEV;

// GA4 초기화
export function initializeGA4() {
  if (typeof window === 'undefined' || !GA_MEASUREMENT_ID) {
    console.warn('GA4: 초기화 실패 - 측정 ID가 없거나 서버 환경입니다.');
    return;
  }

  try {
    // gtag 함수 사용
    if (window.gtag) {
      window.gtag('config', GA_MEASUREMENT_ID, {
        page_title: document.title,
        page_location: window.location.href,
        debug_mode: process.env.NODE_ENV === 'development',
      });

      console.log('GA4 초기화 완료:', GA_MEASUREMENT_ID);
    } else {
      console.warn('GA4: gtag 함수가 로드되지 않았습니다.');
    }
  } catch (error) {
    console.error('GA4 초기화 오류:', error);
  }
}

// 페이지 뷰 이벤트 전송
export function trackPageView(pagePath: string, pageTitle?: string) {
  if (typeof window === 'undefined' || !GA_MEASUREMENT_ID) {
    console.warn('GA4: 페이지 뷰 추적 실패 - 측정 ID가 없거나 서버 환경입니다.');
    return;
  }

  try {
    if (window.gtag) {
      window.gtag('config', GA_MEASUREMENT_ID, {
        page_title: pageTitle || document.title,
        page_location: window.location.href,
        page_path: pagePath,
      });

      console.log('GA4 페이지 뷰 전송:', pagePath);
    } else {
      console.warn('GA4: gtag 함수가 로드되지 않았습니다.');
    }
  } catch (error) {
    console.error('GA4 페이지 뷰 전송 오류:', error);
  }
}

// 커스텀 이벤트 전송
export function trackEvent(
  eventName: string,
  eventParameters?: { [key: string]: any }
) {
  if (typeof window === 'undefined' || !GA_MEASUREMENT_ID) {
    console.warn('GA4: 이벤트 추적 실패 - 측정 ID가 없거나 서버 환경입니다.');
    return;
  }

  try {
    if (window.gtag) {
      window.gtag('event', eventName, {
        ...eventParameters,
        // 기본 매개변수 추가
        timestamp: new Date().toISOString(),
        page_location: window.location.href,
        page_path: window.location.pathname,
      });

      console.log('GA4 이벤트 전송:', eventName, eventParameters);
    } else {
      console.warn('GA4: gtag 함수가 로드되지 않았습니다.');
    }
  } catch (error) {
    console.error('GA4 이벤트 전송 오류:', error);
  }
}

// GA4 연결 상태 확인
export function isGA4Connected(): boolean {
  return typeof window !== 'undefined' && !!GA_MEASUREMENT_ID;
}