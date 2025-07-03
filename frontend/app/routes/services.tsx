import { type MetaFunction, type LoaderFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { ListPage } from "~/components/common/ListPage";
import { servicesConfig } from "~/config/pageConfigs";
import { useAuth } from "~/contexts/AuthContext";
import { apiClient } from "~/lib/api";

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
  const loaderData = useLoaderData<typeof loader>();
  
  return (
    <ListPage
      config={servicesConfig}
      user={user}
      onLogout={logout}
      initialData={loaderData?.initialData}
      isServerRendered={loaderData?.isServerRendered}
    />
  );
}