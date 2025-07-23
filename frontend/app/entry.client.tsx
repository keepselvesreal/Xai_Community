/**
 * 작업 시간: 2025-07-23
 * 작업 버전: MVP 단계 Sentry 모니터링 시스템 구성
 * 
 * 주요 컴포넌트들:
 * - Sentry 초기화 (initSentry)
 * - 환경별 DSN 설정
 * - 사용자 컨텍스트 설정
 * - RemixBrowser 컴포넌트 렌더링
 * 
 * 함수 정보:
 * - initSentry() : Sentry SDK 초기화 및 환경 설정 (15-50줄)
 * - startTransition() : React 18 concurrent 렌더링 (52-58줄)
 * 
 * 관련 파일:
 * - backend/nadle_backend/services/sentry_monitoring_service.py : 백엔드 Sentry 서비스
 * - .env.development : 개발환경 DSN 설정
 */

import { RemixBrowser } from "@remix-run/react";
import { startTransition, StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import * as React from "react";
import * as Sentry from "@sentry/react";

// MVP 단계 Sentry 초기화
function initSentry() {
  // 환경별 DSN 설정
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  const environment = import.meta.env.VITE_NODE_ENV || 'development';
  
  if (!dsn) {
    console.warn('⚠️ Sentry DSN이 설정되지 않았습니다. 환경변수 VITE_SENTRY_DSN을 확인하세요.');
    return;
  }

  Sentry.init({
    dsn: dsn,
    environment: environment,
    
    // 환경별 샘플링 비율
    tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
    
    // MVP: 기본 설정만 사용 (복잡한 integrations 제거)
    // 기본 브라우저 에러 수집 자동 활성화
    
    // 개인정보 전송 설정 (개발환경에서만)
    sendDefaultPii: environment === 'development',
    
    // 에러 필터링 (불필요한 에러 제외)
    beforeSend(event, hint) {
      // 개발 환경에서 console 경고 제외
      if (event.exception) {
        const error = hint.originalException;
        if (error && error.message && error.message.includes('Warning:')) {
          return null;
        }
      }
      return event;
    }
  });

  console.log(`✅ Sentry 초기화 완료 (환경: ${environment})`);
  
  // 전역에서 Sentry 접근 가능하도록 설정 (개발 및 테스트용)
  if (typeof window !== 'undefined') {
    (window as any).Sentry = Sentry;
  }
}

// Sentry 초기화 실행
initSentry();

startTransition(() => {
  hydrateRoot(
    document,
    <StrictMode>
      <RemixBrowser />
    </StrictMode>
  );
});
