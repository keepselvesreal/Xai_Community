import { vitePlugin as remix } from "@remix-run/dev";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

declare module "@remix-run/node" {
  interface Future {
    v3_singleFetch: true;
  }
}

export default defineConfig({
  plugins: [
    remix({
      future: {
        v3_fetcherPersist: true,
        v3_relativeSplatPath: true,
        v3_throwAbortReason: true,
        v3_singleFetch: true,
        v3_lazyRouteDiscovery: true,
      },
      routes(defineRoutes) {
        return defineRoutes((route) => {
          // 정적 라우트를 먼저 정의하여 우선순위 확보
          route("/services", "routes/services.tsx");
          route("/tips", "routes/tips.tsx");
          route("/info", "routes/info.tsx");
          route("/board", "routes/board._index.tsx");
          route("/mypage", "routes/mypage.tsx");
          
          // 동적 라우트들 (정적 라우트 다음에 정의)
          route("/board/:slug", "routes/board.$slug.tsx");
          route("/posts/:slug/edit", "routes/posts.$slug.edit.tsx");
          route("/posts/create", "routes/posts.create.tsx");
          route("/services/write", "routes/services_.write.tsx");
          route("/tips/write", "routes/tips_.write.tsx");
          route("/board/write", "routes/board_.write.tsx");
          
          // 나머지 라우트들은 기본 파일 기반 라우팅 사용
        });
      },
    }),
    tsconfigPaths(),
  ],
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
    'process.env.VERCEL_ENV': JSON.stringify(process.env.VERCEL_ENV),
  },
});
