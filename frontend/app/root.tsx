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
import { useEffect } from "react";

import "./tailwind.css";
import { AuthProvider } from "~/contexts/AuthContext";
import { NotificationProvider } from "~/contexts/NotificationContext";
import { ThemeProvider } from "~/contexts/ThemeContext";
import ErrorBoundary from "~/components/common/ErrorBoundary";

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
  // 환경변수 우선순위: ENVIRONMENT > NODE_ENV
  const environment = process.env.ENVIRONMENT || process.env.NODE_ENV || "development";
  
  const buildInfo: BuildInfo = {
    version: process.env.npm_package_version || "unknown",
    environment: environment,
    deploymentId: process.env.VERCEL_DEPLOYMENT_ID,
    commitSha: process.env.VERCEL_GIT_COMMIT_SHA,
    deploymentUrl: process.env.VERCEL_URL,
    gitBranch: process.env.VERCEL_GIT_COMMIT_REF,
  };
  
  // Vercel 환경변수 콘솔 출력 (staging, production에서)
  if (environment === "staging" || environment === "production") {
    console.log("=== Vercel Environment Variables ===");
    console.log("NODE_ENV:", process.env.NODE_ENV);
    console.log("ENVIRONMENT:", process.env.ENVIRONMENT);
    console.log("VERCEL_ENV:", process.env.VERCEL_ENV);
    console.log("VERCEL_GIT_COMMIT_SHA:", process.env.VERCEL_GIT_COMMIT_SHA);
    console.log("VERCEL_DEPLOYMENT_ID:", process.env.VERCEL_DEPLOYMENT_ID);
    console.log("VERCEL_URL:", process.env.VERCEL_URL);
    console.log("====================================");
  }
  
  return { buildInfo };
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
    ? import.meta.env.VITE_GA_MEASUREMENT_ID 
    : process.env.VITE_GA_MEASUREMENT_ID;

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
  const location = useLocation();
  
  // 클라이언트사이드에서 올바른 환경 판단
  const clientEnvironment = typeof window !== "undefined" 
    ? import.meta.env.VITE_NODE_ENV || 'development'
    : buildInfo?.environment || 'development';
  
  // 환경정보 콘솔 출력 및 Google Analytics 페이지 변경 추적
  useEffect(() => {
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
    
    const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;
    
    if (typeof window !== "undefined" && window.gtag && GA_MEASUREMENT_ID && GA_MEASUREMENT_ID !== "G-XXXXXXXXX") {
      window.gtag("config", GA_MEASUREMENT_ID, {
        page_title: document.title,
        page_location: window.location.href,
      });
      
      // 페이지뷰 이벤트 전송
      window.gtag("event", "page_view", {
        page_title: document.title,
        page_location: window.location.href,
        page_path: location.pathname,
      });
    }
  }, [location, buildInfo]);
  
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ErrorBoundary>
          <AuthProvider>
            <NotificationProvider>
              <Outlet />
              
              {/* 모든 환경에서 환경 정보 표시 */}
              {buildInfo && (
                <div 
                  id="environment-info" 
                  style={{
                    position: "fixed",
                    bottom: "10px",
                    right: "10px", 
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
                  <div><strong>환경 정보:</strong></div>
                  <div>Environment: <strong>{clientEnvironment}</strong></div>
                  <div>Version: {buildInfo.version || "unknown"}</div>
                  
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
        </ErrorBoundary>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
