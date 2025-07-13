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
  commit: string;
  environment: string;
  deploymentId: string;
}

// 서버 사이드에서 환경변수를 안전하게 로드
export async function loader() {
  const buildInfo: BuildInfo = {
    version: process.env.npm_package_version || "unknown",
    commit: process.env.VERCEL_GIT_COMMIT_SHA || "unknown", 
    environment: process.env.NODE_ENV || "development",
    deploymentId: process.env.VERCEL_DEPLOYMENT_ID || "unknown",
  };
  
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
  { name: "build-commit", content: data?.buildInfo.commit || "unknown" },
  { name: "build-environment", content: data?.buildInfo.environment || "unknown" },
  { name: "vercel-deployment", content: data?.buildInfo.deploymentId || "unknown" },
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
  
  // Google Analytics 페이지 변경 추적
  useEffect(() => {
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
  }, [location]);
  
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ErrorBoundary>
          <AuthProvider>
            <NotificationProvider>
              <Outlet />
              {/* 개발 환경에서만 빌드 정보 표시 */}
              {buildInfo?.environment === "development" && (
                <div 
                  id="build-info-dev" 
                  style={{
                    position: "fixed",
                    bottom: "10px",
                    right: "10px", 
                    background: "rgba(0, 0, 0, 0.8)",
                    color: "white",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontFamily: "monospace",
                    zIndex: 9999,
                    maxWidth: "300px"
                  }}
                >
                  <div><strong>Build Info:</strong></div>
                  <div>Version: {buildInfo?.version || "unknown"}</div>
                  <div>Commit: {buildInfo?.commit?.slice(0, 8) || "unknown"}</div>
                  <div>Environment: {buildInfo?.environment || "unknown"}</div>
                  <div>Deployment: {buildInfo?.deploymentId?.slice(0, 12) || "unknown"}</div>
                </div>
              )}
            </NotificationProvider>
          </AuthProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
