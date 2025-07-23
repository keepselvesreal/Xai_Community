/**
 * 작업 시간: 2025-07-23
 * 작업 버전: MVP 단계 Sentry 모니터링 시스템 구성
 * 
 * 주요 컴포넌트들:
 * - SentryErrorBoundary: Sentry 통합 에러 바운더리
 * - ErrorFallback: 에러 발생 시 표시할 UI
 * 
 * 함수 정보:
 * - ErrorFallback({ error, resetError }) : 에러 UI 컴포넌트 (17-65줄)
 * - SentryErrorBoundary.tsx : Sentry 통합 래퍼 컴포넌트 (67-85줄)
 * 
 * 관련 파일:
 * - app/entry.client.tsx : Sentry 초기화
 * - app/root.tsx : 전체 앱에 적용될 컴포넌트
 */

import * as React from "react";
import * as Sentry from "@sentry/react";

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

function ErrorFallback({ error, resetError }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg 
                className="h-6 w-6 text-red-600" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.732 15.5c-.77.833.192 2.5 1.732 2.5z" 
                />
              </svg>
            </div>
            
            <h2 className="mt-4 text-lg font-medium text-gray-900">
              앱 오류가 발생했습니다
            </h2>
            
            <p className="mt-2 text-sm text-gray-600">
              예상치 못한 오류가 발생했습니다. 오류가 자동으로 보고되었습니다.
            </p>
            
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-4 text-left">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                  개발자 정보 (개발환경에서만 표시)
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded-md">
                  <pre className="text-xs text-red-600 whitespace-pre-wrap">
                    {error.message}
                    {error.stack && (
                      <>
                        {'\n\n'}
                        {error.stack}
                      </>
                    )}
                  </pre>
                </div>
              </details>
            )}
            
            <div className="mt-6 flex space-x-3">
              <button
                type="button"
                onClick={resetError}
                className="flex-1 bg-indigo-600 border border-transparent rounded-md py-2 px-4 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                다시 시도
              </button>
              
              <button
                type="button"
                onClick={() => window.location.href = '/'}
                className="flex-1 bg-white border border-gray-300 rounded-md py-2 px-4 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                홈으로 이동
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface SentryErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
}

export function SentryErrorBoundary({ 
  children, 
  fallback: FallbackComponent = ErrorFallback 
}: SentryErrorBoundaryProps) {
  return (
    <Sentry.ErrorBoundary 
      fallback={FallbackComponent}
      beforeCapture={(scope, error, hint) => {
        // 에러 발생 시 추가 컨텍스트 정보 설정
        scope.setTag("errorBoundary", "react");
        scope.setLevel("error");
        
        // 현재 URL 정보 추가
        scope.setContext("location", {
          pathname: window.location.pathname,
          search: window.location.search,
          hash: window.location.hash,
          href: window.location.href
        });
        
        console.error("React Error Boundary에서 에러를 캐치했습니다:", error);
      }}
    >
      {children}
    </Sentry.ErrorBoundary>
  );
}

export default SentryErrorBoundary;