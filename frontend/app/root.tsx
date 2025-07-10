import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "@remix-run/react";
import type { LinksFunction, MetaFunction } from "@remix-run/node";

import "./tailwind.css";
import { AuthProvider } from "~/contexts/AuthContext";
import { NotificationProvider } from "~/contexts/NotificationContext";
import { ThemeProvider } from "~/contexts/ThemeContext";
import ErrorBoundary from "~/components/common/ErrorBoundary";

export const meta: MetaFunction = () => [
  { title: "XAI 아파트 커뮤니티" },
  { name: "description", content: "함께 만들어가는 우리 아파트 소통공간" },
  // 빌드 정보를 메타태그에 포함
  { name: "build-version", content: process.env.npm_package_version || "unknown" },
  { name: "build-commit", content: process.env.VERCEL_GIT_COMMIT_SHA || "unknown" },
  { name: "build-environment", content: process.env.NODE_ENV || "unknown" },
  { name: "vercel-deployment", content: process.env.VERCEL_DEPLOYMENT_ID || "unknown" },
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
  return (
    <html lang="ko">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
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
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ErrorBoundary>
          <AuthProvider>
            <NotificationProvider>
              <Outlet />
            </NotificationProvider>
          </AuthProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
