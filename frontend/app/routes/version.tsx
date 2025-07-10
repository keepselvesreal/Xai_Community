import type { LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";

// Vercel 환경변수에서 빌드 정보 가져오기
export async function loader({ request }: LoaderFunctionArgs) {
  const buildInfo = {
    version: process.env.npm_package_version || "unknown",
    commit_hash: process.env.VERCEL_GIT_COMMIT_SHA || "unknown",
    build_time: new Date().toISOString(),
    environment: process.env.NODE_ENV || "unknown",
    service: "xai-community-frontend",
    vercel_url: process.env.VERCEL_URL || "unknown",
    deployment_id: process.env.VERCEL_DEPLOYMENT_ID || "unknown"
  };

  return json(buildInfo);
}

export const meta: MetaFunction = () => [
  { title: "버전 정보 - XAI 커뮤니티" },
  { name: "description", content: "XAI 커뮤니티 프론트엔드 빌드 및 버전 정보" },
];

export default function VersionPage() {
  const buildInfo = useLoaderData<typeof loader>();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">🔧 버전 정보</h1>
        
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">프론트엔드 빌드 정보</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="font-medium text-gray-600">서비스명:</span>
              <span className="text-gray-900">{buildInfo.service}</span>
            </div>
            
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="font-medium text-gray-600">버전:</span>
              <span className="text-gray-900 font-mono">{buildInfo.version}</span>
            </div>
            
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="font-medium text-gray-600">커밋 해시:</span>
              <span className="text-gray-900 font-mono text-sm">
                {buildInfo.commit_hash.substring(0, 8)}...
              </span>
            </div>
            
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="font-medium text-gray-600">빌드 시간:</span>
              <span className="text-gray-900">{buildInfo.build_time}</span>
            </div>
            
            <div className="flex items-center justify-between py-2 border-b border-gray-200">
              <span className="font-medium text-gray-600">환경:</span>
              <span className={`px-2 py-1 rounded text-sm font-medium ${
                buildInfo.environment === 'production' 
                  ? 'bg-green-100 text-green-800'
                  : buildInfo.environment === 'development'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {buildInfo.environment}
              </span>
            </div>

            {buildInfo.vercel_url !== "unknown" && (
              <div className="flex items-center justify-between py-2 border-b border-gray-200">
                <span className="font-medium text-gray-600">Vercel URL:</span>
                <span className="text-gray-900 text-sm">{buildInfo.vercel_url}</span>
              </div>
            )}

            {buildInfo.deployment_id !== "unknown" && (
              <div className="flex items-center justify-between py-2 border-b border-gray-200">
                <span className="font-medium text-gray-600">배포 ID:</span>
                <span className="text-gray-900 font-mono text-sm">{buildInfo.deployment_id}</span>
              </div>
            )}
          </div>
          
          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-500 text-center">
              이 페이지는 롤백 및 버전 확인을 위해 제공됩니다.
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <a 
            href="/" 
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            ← 홈으로 돌아가기
          </a>
        </div>
      </div>
    </div>
  );
}