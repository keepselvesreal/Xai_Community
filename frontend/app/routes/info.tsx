import type { MetaFunction, LoaderFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { ListPage } from "~/components/common/ListPage";
import { infoConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";
import { apiClient } from "~/lib/api";

export const meta: MetaFunction = () => {
  return [
    { title: "정보 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 주민들을 위한 유용한 정보" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  try {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const size = parseInt(url.searchParams.get('size') || '10');
    
    // 서버에서 정보 페이지 데이터 미리 로드
    const response = await apiClient.getPosts({
      metadata_type: 'property_information',  // 기존 DB 형식 사용
      page,
      size,
      sortBy: 'created_at'
    });
    
    console.log('🔍 정보 페이지 로더 응답:', {
      success: response.success,
      dataExists: !!response.data,
      itemsCount: response.data?.items?.length || 0,
      error: response.error,
      fullResponse: response.data
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
    console.error('SSR Loader Error (info):', error);
    return json({
      initialData: null,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
      isServerRendered: true
    });
  }
};

export default function Info() {
  const { user, logout } = useAuth();
  const loaderData = useLoaderData<typeof loader>();

  return (
    <ListPage 
      config={infoConfig}
      user={user || undefined}
      onLogout={logout}
      initialData={loaderData?.initialData}
      isServerRendered={loaderData?.isServerRendered}
    />
  );
}