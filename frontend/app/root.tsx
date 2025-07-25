import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
  useLocation,
} from "@remix-run/react";
import type { LinksFunction, MetaFunction } from "@remix-run/node";
import { useEffect, useState } from "react";

import "./tailwind.css";
import "./styles/service-comments.css";
import { AuthProvider } from "~/contexts/AuthContext";
import { NotificationProvider } from "~/contexts/NotificationContext";
import { ThemeProvider } from "~/contexts/ThemeContext";
import { SentryErrorBoundary } from "~/components/errors/SentryErrorBoundary";
import { getAnalytics } from "~/hooks/useAnalytics";
import { sentryService } from "~/lib/sentry-service";
import { getNodeEnv, validateAndGetEnvironment } from "~/utils/env";
import { setupGlobalErrorHandlers } from "~/utils/errorReporter";

// 빌드 정보 타입 정의
interface BuildInfo {
  version: string;
  environment: string;
  deploymentId?: string;
  commitSha?: string;
  deploymentUrl?: string;
  gitBranch?: string;
}

// 서버 사이드에서 환경변수를 안전하게 로드
export async function loader() {
  // VITE_NODE_ENV로 통일된 환경 설정
  const environment = process.env.VITE_NODE_ENV;
  
  // 환경변수가 명시적으로 설정되지 않은 경우 에러
  if (!environment) {
    throw new Error("❌ 서버 환경변수 VITE_NODE_ENV가 설정되지 않았습니다. 환경변수 파일에서 설정해주세요.");
  }
  
  const buildInfo: BuildInfo = {
    version: process.env.npm_package_version || "unknown",
    environment: environment,
    deploymentId: process.env.VERCEL_DEPLOYMENT_ID,
    commitSha: process.env.VERCEL_GIT_COMMIT_SHA,
    deploymentUrl: process.env.VERCEL_URL,
    gitBranch: process.env.VERCEL_GIT_COMMIT_REF,
  };

  // Sentry 설정 정보 (클라이언트에서 사용하기 위해)
  const sentryConfig = {
    dsn: process.env.SENTRY_DSN,
    environment: environment,
    tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || "1.0"),
    sendDefaultPii: process.env.SENTRY_SEND_DEFAULT_PII === "true",
    debug: process.env.SENTRY_DEBUG === "true" || environment === "development",
  };
  
  // Vercel 환경변수 콘솔 출력 (staging, production에서)
  if (environment === "staging" || environment === "production") {
    console.log("=== Vercel Environment Variables ===");
    console.log("VITE_NODE_ENV:", process.env.VITE_NODE_ENV);
    console.log("VERCEL_ENV:", process.env.VERCEL_ENV);
    console.log("VERCEL_GIT_COMMIT_SHA:", process.env.VERCEL_GIT_COMMIT_SHA);
    console.log("VERCEL_DEPLOYMENT_ID:", process.env.VERCEL_DEPLOYMENT_ID);
    console.log("VERCEL_URL:", process.env.VERCEL_URL);
    console.log("====================================");
  }
  
  return { buildInfo, sentryConfig };
}

// Google Analytics 초기화 함수
declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

export const meta: MetaFunction<typeof loader> = ({ data }) => [
  { title: "XAI 아파트 커뮤니티" },
  { name: "description", content: "함께 만들어가는 우리 아파트 소통공간" },
  // 서버에서 로드한 빌드 정보를 메타태그에 포함
  { name: "build-version", content: data?.buildInfo.version || "unknown" },
  { name: "build-environment", content: data?.buildInfo.environment || "unknown" },
];

export const links: LinksFunction = () => [
  { rel: "preconnect", href: "https://cdn.jsdelivr.net" },
  {
    rel: "stylesheet",
    href: "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css",
  },
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect", 
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const GA_MEASUREMENT_ID = typeof window !== "undefined" 
    ? import.meta.env.VITE_GA_MEASUREMENT_ID_DEV 
    : process.env.VITE_GA_MEASUREMENT_ID_DEV;

  return (
    <html lang="ko">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
        
        {/* Google Analytics */}
        {GA_MEASUREMENT_ID && GA_MEASUREMENT_ID !== "G-XXXXXXXXX" && (
          <>
            <script
              async
              src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
            />
            <script
              dangerouslySetInnerHTML={{
                __html: `
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${GA_MEASUREMENT_ID}', {
                    page_title: document.title,
                    page_location: window.location.href,
                    debug_mode: ${process.env.NODE_ENV === 'development'}
                  });
                `,
              }}
            />
          </>
        )}
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  const data = useLoaderData<typeof loader>();
  const buildInfo = data?.buildInfo;
  const sentryConfig = data?.sentryConfig;
  const location = useLocation();
  
  // Hydration 불일치 방지를 위해 상태로 관리
  const [clientEnvironment, setClientEnvironment] = useState(buildInfo?.environment || 'development');
  const [sentryInitialized, setSentryInitialized] = useState(false);
  
  // Sentry 초기화 useEffect (최우선)
  useEffect(() => {
    if (typeof window !== "undefined" && !sentryInitialized) {
      try {
        // Vite 환경변수에서 직접 로드
        const nodeEnv = getNodeEnv();
        const finalConfig = {
          dsn: import.meta.env.VITE_SENTRY_DSN,
          environment: nodeEnv,
          tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '1.0'),
          sendDefaultPii: import.meta.env.VITE_SENTRY_SEND_DEFAULT_PII === 'true',
          debug: import.meta.env.VITE_SENTRY_DEBUG === 'true' || nodeEnv === 'development',
        };

        console.log('🚨 프론트엔드 Sentry 초기화 시도:', {
          environment: finalConfig.environment,
          hasDsn: !!finalConfig.dsn,
          debug: finalConfig.debug,
          dsn: finalConfig.dsn ? finalConfig.dsn.substring(0, 30) + '...' : 'None'
        });

        if (finalConfig.dsn) {
          // Sentry 초기화
          sentryService.initialize(finalConfig);
          setSentryInitialized(true);

          console.log('✅ 프론트엔드 Sentry 초기화 완료');
          
          // 전역에 노출 (디버깅용)
          (window as any).sentryService = sentryService;
          
          // 전역 에러 핸들러 등록 (Sentry 초기화 후)
          setupGlobalErrorHandlers();
          console.log('✅ 전역 에러 핸들러 등록 완료');
        } else {
          console.warn('⚠️ VITE_SENTRY_DSN이 설정되지 않아 Sentry 초기화를 건너뜁니다.');
          // Sentry 없이도 에러 핸들러는 등록
          setupGlobalErrorHandlers();
          console.log('✅ 전역 에러 핸들러 등록 완료 (Sentry 없음)');
        }
      } catch (error) {
        console.error('❌ 프론트엔드 Sentry 초기화 실패:', error);
        // 초기화 실패해도 에러 핸들러는 등록
        setupGlobalErrorHandlers();
      }
    }
  }, [sentryInitialized]);

  // 환경정보 콘솔 출력 및 Google Analytics 페이지 변경 추적
  useEffect(() => {
    // 클라이언트에서 환경 설정 검증 및 설정
    if (typeof window !== "undefined") {
      try {
        // 모든 환경에서 백엔드-프론트엔드 환경값 일치 검증
        const validatedEnv = validateAndGetEnvironment(buildInfo?.environment);
        setClientEnvironment(validatedEnv);
        
        console.log(`✅ 환경 검증 성공: ${validatedEnv}`);
      } catch (error) {
        // 환경 불일치 시 사용자에게 명확한 오류 표시
        console.error('환경 검증 실패:', error);
        
        if (error instanceof Error) {
          // 사용자에게 친화적인 오류 메시지 표시
          alert(error.message);
        }
        
        // 오류를 다시 던져서 애플리케이션 로딩 중단
        throw error;
      }
    }
    
    // 환경정보 콘솔 출력 (클라이언트 사이드)
    if (buildInfo && typeof window !== "undefined") {
      console.log("=== 클라이언트 환경 정보 ===");
      console.log("Environment:", buildInfo.environment);
      console.log("Version:", buildInfo.version);
      console.log("Current URL:", window.location.href);
      if (buildInfo.deploymentId) {
        console.log("=== Vercel 배포 정보 ===");
        console.log("Deployment ID:", buildInfo.deploymentId);
        console.log("Commit SHA:", buildInfo.commitSha);
        console.log("Git Branch:", buildInfo.gitBranch);
        console.log("Deployment URL:", buildInfo.deploymentUrl);
      }
      console.log("========================");
    }
    
    // 새로운 analytics 라이브러리 사용
    if (typeof window !== 'undefined') {
      const analytics = getAnalytics();
      analytics.trackPageView(location.pathname, document.title);
    }
  }, [location, buildInfo]);
  
  return (
    <SentryErrorBoundary>
      <ThemeProvider>
        <SentryErrorBoundary>
          <AuthProvider>
            <NotificationProvider>
              <Outlet />
              
              {/* 모든 환경에서 환경 정보 표시 */}
              {buildInfo && (
                <div 
                  id="environment-info" 
                  style={{
                    position: "fixed",
                    top: "4px",
                    right: "4px", 
                    background: clientEnvironment === "production" 
                      ? "rgba(220, 38, 38, 0.9)" 
                      : clientEnvironment === "staging" 
                      ? "rgba(245, 158, 11, 0.9)" 
                      : "rgba(0, 0, 0, 0.8)",
                    color: "white",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontFamily: "monospace",
                    zIndex: 9999,
                    maxWidth: "300px",
                    border: clientEnvironment === "production" 
                      ? "2px solid #dc2626" 
                      : clientEnvironment === "staging" 
                      ? "2px solid #f59e0b" 
                      : "1px solid #374151"
                  }}
                >
                  <div>Environment: <strong>{clientEnvironment}</strong></div>
                  
                  {/* Vercel 배포 정보 표시 */}
                  {buildInfo.deploymentId && (
                    <>
                      <div style={{ marginTop: "8px", borderTop: "1px solid rgba(255,255,255,0.3)", paddingTop: "8px" }}>
                        <strong>Vercel 배포:</strong>
                      </div>
                      <div>Deploy ID: {buildInfo.deploymentId.slice(0, 12)}...</div>
                      {buildInfo.commitSha && (
                        <div>Commit: {buildInfo.commitSha.slice(0, 8)}</div>
                      )}
                      {buildInfo.gitBranch && (
                        <div>Branch: {buildInfo.gitBranch}</div>
                      )}
                      {buildInfo.deploymentUrl && (
                        <div style={{ fontSize: "10px", marginTop: "4px", wordBreak: "break-all" }}>
                          URL: {buildInfo.deploymentUrl}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </NotificationProvider>
          </AuthProvider>
        </SentryErrorBoundary>
      </ThemeProvider>
    </SentryErrorBoundary>
  );
}
