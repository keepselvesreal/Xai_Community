import { type MetaFunction, type LoaderFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData, useRouteError, isRouteErrorResponse, useNavigation } from "@remix-run/react";
import { ListPage } from "~/components/common/ListPage";
import { servicesConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";
import { apiClient } from "~/lib/api";
import { useEffect, useState } from "react";

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 입주 업체 서비스" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  try {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const size = parseInt(url.searchParams.get('size') || '10');
    
    // 서버에서 입주업체 서비스 데이터 미리 로드
    const response = await apiClient.getPosts({
      metadata_type: 'moving services',  // 기존 DB 형식 사용
      page,
      size,
      sortBy: 'created_at'
    });
    
    if (response.success && response.data) {
      return json({
        initialData: response.data,
        timestamp: new Date().toISOString(),
        isServerRendered: true
      });
    } else {
      return json({
        initialData: null,
        error: response.error || 'Failed to load data',
        timestamp: new Date().toISOString(),
        isServerRendered: true
      });
    }
  } catch (error) {
    console.error('SSR Loader Error (services):', error);
    return json({
      initialData: null,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
      isServerRendered: true
    });
  }
};

export default function Services() {
  const { user, logout } = useAuth();
  const navigation = useNavigation();
  // useLoaderData는 항상 호출되어야 함 - React Hook 규칙
  const loaderData = useLoaderData<typeof loader>();
  
  // 로딩 상태 확인
  if (navigation.state === "loading") {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-2 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }
  
  return (
    <ListPage
      config={servicesConfig}
      user={user || undefined}
      onLogout={logout}
      initialData={loaderData?.initialData || null}
      isServerRendered={loaderData?.isServerRendered || false}
    />
  );
}

export function ErrorBoundary() {
  const error = useRouteError();
  
  console.error('Services route error:', error);
  
  if (isRouteErrorResponse(error)) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">
            {error.status} {error.statusText}
          </h1>
          <p className="text-gray-600">{error.data}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-4">서비스 오류</h1>
        <p className="text-gray-600 mb-4">
          {error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'}
        </p>
        <button 
          onClick={() => window.location.reload()} 
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          새로고침
        </button>
      </div>
    </div>
  );
}