import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate } from "@remix-run/react";
import { useState, useEffect } from "react";
import AppLayout from "~/components/layout/AppLayout";
import Card from "~/components/ui/Card";
import Button from "~/components/ui/Button";
import Input from "~/components/ui/Input";
import Select from "~/components/ui/Select";
import Textarea from "~/components/ui/Textarea";
import PostCard from "~/components/post/PostCard";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { formatNumber, getMethodColor, getStatusColor } from "~/lib/utils";
import { API_TEST_ENDPOINTS } from "~/lib/constants";
import apiClient from "~/lib/api";
import type { DashboardStats, ApiEndpoint, ApiTestRequest, Post, PaginatedResponse } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "대시보드 | FastAPI UI" },
    { name: "description", content: "FastAPI 개발 현황 및 API 테스트" },
  ];
};

export const loader: LoaderFunction = async () => {
  // 실제 환경에서는 API에서 데이터를 가져옴
  const stats: DashboardStats = {
    completedApis: 14,
    inProgressApis: 3,
    totalProgress: 85,
    testCases: 42,
  };

  const apiEndpoints: ApiEndpoint[] = API_TEST_ENDPOINTS.map(endpoint => ({
    ...endpoint,
    isExpanded: false,
  }));

  return json({ stats, apiEndpoints });
};

export default function Dashboard() {
  const { stats, apiEndpoints: initialEndpoints } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showSuccess, showError } = useNotification();
  const navigate = useNavigate();
  
  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>(initialEndpoints);
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [recentPosts, setRecentPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState(true);

  const toggleEndpoint = (endpointId: string) => {
    setEndpoints(prev => 
      prev.map(endpoint => 
        endpoint.id === endpointId 
          ? { ...endpoint, isExpanded: !endpoint.isExpanded }
          : endpoint
      )
    );
  };

  const handleApiTest = async (endpoint: ApiEndpoint, formData: FormData) => {
    const body: any = {};
    const headers: Record<string, string> = {};

    // 폼 데이터에서 파라미터 추출
    for (const [key, value] of formData.entries()) {
      if (key === 'authorization' && value) {
        headers['Authorization'] = value as string;
      } else if (value) {
        body[key] = value;
      }
    }

    const request: ApiTestRequest = {
      method: endpoint.method,
      endpoint: endpoint.path,
      headers,
      body: endpoint.method !== 'GET' ? body : undefined,
      queryParams: endpoint.method === 'GET' ? body : undefined,
    };

    try {
      const result = await apiClient.testApiCall(request);
      setTestResults(prev => ({ ...prev, [endpoint.id]: result }));
      showSuccess(`${endpoint.name} API 테스트 완료!`);
    } catch (error) {
      showError(`${endpoint.name} API 테스트 실패`);
    }
  };

  const clearTestResult = (endpointId: string) => {
    setTestResults(prev => {
      const { [endpointId]: _, ...rest } = prev;
      return rest;
    });
  };

  // 최근 게시글 로드
  const loadRecentPosts = async () => {
    setPostsLoading(true);
    try {
      const response = await apiClient.getPosts({ page: 1, size: 6, sortBy: 'created_at' });
      if (response.success && response.data) {
        setRecentPosts(response.data.items);
      }
    } catch (error) {
      console.error('최근 게시글 로드 실패:', error);
    } finally {
      setPostsLoading(false);
    }
  };

  useEffect(() => {
    loadRecentPosts();
  }, []);

  return (
    <AppLayout 
      title="대시보드" 
      subtitle="API 개발 현황 및 테스트"
      user={user}
      onLogout={logout}
    >
      {/* 통계 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="text-center">
          <div className="text-4xl mb-3">✅</div>
          <div className="text-sm text-gray-500 mb-1">완료된 API</div>
          <div className="text-3xl font-bold text-gray-900">{stats.completedApis}</div>
        </Card>

        <Card className="text-center">
          <div className="text-4xl mb-3">⏳</div>
          <div className="text-sm text-gray-500 mb-1">진행중 API</div>
          <div className="text-3xl font-bold text-gray-900">{stats.inProgressApis}</div>
        </Card>

        <Card className="text-center">
          <div className="text-4xl mb-3">📊</div>
          <div className="text-sm text-gray-500 mb-1">전체 진행률</div>
          <div className="text-3xl font-bold text-gray-900">{stats.totalProgress}%</div>
        </Card>

        <Card className="text-center">
          <div className="text-4xl mb-3">🧪</div>
          <div className="text-sm text-gray-500 mb-1">테스트 케이스</div>
          <div className="text-3xl font-bold text-gray-900">{stats.testCases}</div>
        </Card>
      </div>

      {/* 빠른 액션 섹션 */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">🚀 빠른 액션</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/posts')}>
            <Card.Content className="text-center py-6">
              <div className="text-3xl mb-3">📄</div>
              <div className="font-semibold text-gray-900">게시글 목록</div>
              <div className="text-sm text-gray-500 mt-1">모든 게시글 보기</div>
            </Card.Content>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/posts/create')}>
            <Card.Content className="text-center py-6">
              <div className="text-3xl mb-3">✍️</div>
              <div className="font-semibold text-gray-900">게시글 작성</div>
              <div className="text-sm text-gray-500 mt-1">새 게시글 작성하기</div>
            </Card.Content>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/auth/login')}>
            <Card.Content className="text-center py-6">
              <div className="text-3xl mb-3">🔐</div>
              <div className="font-semibold text-gray-900">{user ? '내 프로필' : '로그인'}</div>
              <div className="text-sm text-gray-500 mt-1">{user ? '프로필 관리' : '계정에 로그인'}</div>
            </Card.Content>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })}>
            <Card.Content className="text-center py-6">
              <div className="text-3xl mb-3">🧪</div>
              <div className="font-semibold text-gray-900">API 테스트</div>
              <div className="text-sm text-gray-500 mt-1">API 엔드포인트 테스트</div>
            </Card.Content>
          </Card>
        </div>
      </div>

      {/* 최근 게시글 섹션 */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">📝 최근 게시글</h2>
          <Button variant="outline" onClick={() => navigate('/posts')}>
            모든 게시글 보기
          </Button>
        </div>

        {postsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, index) => (
              <Card key={index} className="animate-pulse">
                <Card.Content>
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded mb-2 w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </Card.Content>
              </Card>
            ))}
          </div>
        ) : recentPosts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recentPosts.map((post) => (
              <PostCard
                key={post.id}
                post={post}
                onClick={(post) => navigate(`/posts/${post.slug}`)}
              />
            ))}
          </div>
        ) : (
          <Card>
            <Card.Content className="text-center py-12">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">아직 게시글이 없습니다</h3>
              <p className="text-gray-600 mb-4">첫 번째 게시글을 작성해보세요!</p>
              <Button onClick={() => navigate('/posts/create')}>
                게시글 작성하기
              </Button>
            </Card.Content>
          </Card>
        )}
      </div>

      {/* API 테스트 섹션 */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">🧪 API 테스트</h2>
        </div>

        {/* API 엔드포인트 그룹 */}
        <div className="space-y-4">
          {/* 인증 API */}
          <Card padding="none">
            <Card.Header className="px-6 py-4">
              <Card.Title level={3}>🔐 인증 API</Card.Title>
            </Card.Header>
            
            <div className="divide-y divide-gray-200">
              {endpoints
                .filter(endpoint => endpoint.id.startsWith('auth'))
                .map(endpoint => (
                  <ApiEndpointTest
                    key={endpoint.id}
                    endpoint={endpoint}
                    isExpanded={endpoint.isExpanded}
                    testResult={testResults[endpoint.id]}
                    onToggle={() => toggleEndpoint(endpoint.id)}
                    onTest={(formData) => handleApiTest(endpoint, formData)}
                    onClear={() => clearTestResult(endpoint.id)}
                  />
                ))}
            </div>
          </Card>

          {/* 게시글 API */}
          <Card padding="none">
            <Card.Header className="px-6 py-4">
              <Card.Title level={3}>📝 게시글 API</Card.Title>
            </Card.Header>
            
            <div className="divide-y divide-gray-200">
              {endpoints
                .filter(endpoint => endpoint.id.startsWith('posts'))
                .map(endpoint => (
                  <ApiEndpointTest
                    key={endpoint.id}
                    endpoint={endpoint}
                    isExpanded={endpoint.isExpanded}
                    testResult={testResults[endpoint.id]}
                    onToggle={() => toggleEndpoint(endpoint.id)}
                    onTest={(formData) => handleApiTest(endpoint, formData)}
                    onClear={() => clearTestResult(endpoint.id)}
                  />
                ))}
            </div>
          </Card>

          {/* 댓글 API */}
          <Card padding="none">
            <Card.Header className="px-6 py-4">
              <Card.Title level={3}>💬 댓글 API</Card.Title>
            </Card.Header>
            
            <div className="divide-y divide-gray-200">
              {endpoints
                .filter(endpoint => endpoint.id.startsWith('comments'))
                .map(endpoint => (
                  <ApiEndpointTest
                    key={endpoint.id}
                    endpoint={endpoint}
                    isExpanded={endpoint.isExpanded}
                    testResult={testResults[endpoint.id]}
                    onToggle={() => toggleEndpoint(endpoint.id)}
                    onTest={(formData) => handleApiTest(endpoint, formData)}
                    onClear={() => clearTestResult(endpoint.id)}
                  />
                ))}
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}

// API 엔드포인트 테스트 컴포넌트
interface ApiEndpointTestProps {
  endpoint: ApiEndpoint;
  isExpanded: boolean;
  testResult?: any;
  onToggle: () => void;
  onTest: (formData: FormData) => Promise<void>;
  onClear: () => void;
}

function ApiEndpointTest({ 
  endpoint, 
  isExpanded, 
  testResult, 
  onToggle, 
  onTest, 
  onClear 
}: ApiEndpointTestProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<'response' | 'headers' | 'request'>('response');

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    
    try {
      const formData = new FormData(event.currentTarget);
      await onTest(formData);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClear = () => {
    onClear();
    if (document) {
      const form = document.getElementById(`form-${endpoint.id}`) as HTMLFormElement;
      form?.reset();
    }
  };

  return (
    <div>
      {/* 엔드포인트 헤더 */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-3">
          <span className={`px-2 py-1 text-xs font-semibold rounded ${getMethodColor(endpoint.method)}`}>
            {endpoint.method}
          </span>
          <span className="font-mono text-sm text-gray-700">{endpoint.path}</span>
          <span className="text-2xl">✅</span>
        </div>
        <span className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
          ▶
        </span>
      </div>

      {/* 테스트 패널 */}
      {isExpanded && (
        <div className="px-6 pb-6 bg-gray-50">
          <form id={`form-${endpoint.id}`} onSubmit={handleSubmit} className="space-y-4">
            {/* 파라미터 입력 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {endpoint.parameters?.map(param => (
                <div key={param.name}>
                  {param.type === 'string' && (
                    <Input
                      name={param.name}
                      label={param.name}
                      placeholder={param.description}
                      required={param.required}
                      defaultValue={param.defaultValue}
                    />
                  )}
                  {param.type === 'number' && (
                    <Input
                      type="number"
                      name={param.name}
                      label={param.name}
                      placeholder={param.description}
                      required={param.required}
                      defaultValue={param.defaultValue}
                    />
                  )}
                </div>
              ))}
              
              {/* Authorization 헤더 (POST 요청용) */}
              {endpoint.method !== 'GET' && (
                <Input
                  name="authorization"
                  label="Authorization Header"
                  placeholder="Bearer your_token_here"
                />
              )}
            </div>

            {/* 요청 본문 (POST/PUT용) */}
            {(endpoint.method === 'POST' || endpoint.method === 'PUT') && (
              <Textarea
                name="content"
                label="요청 본문"
                placeholder="게시글 내용 등..."
                rows={3}
              />
            )}

            {/* 액션 버튼 */}
            <div className="flex space-x-3">
              <Button type="submit" loading={isSubmitting}>
                🚀 API 호출
              </Button>
              <Button type="button" variant="outline" onClick={handleClear}>
                지우기
              </Button>
            </div>
          </form>

          {/* 응답 결과 */}
          {testResult && (
            <div className="mt-6 space-y-3">
              {/* 응답 탭 */}
              <div className="flex space-x-1">
                {(['response', 'headers', 'request'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 py-1 text-sm font-medium rounded-t ${
                      activeTab === tab
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {tab === 'response' ? '응답' : tab === 'headers' ? '헤더' : '요청'}
                  </button>
                ))}
              </div>

              {/* 응답 내용 */}
              <div className="bg-gray-900 text-gray-100 p-4 rounded-b rounded-tr text-sm font-mono overflow-auto max-h-80">
                <div className="flex items-center justify-between mb-2">
                  <span className={`font-semibold ${getStatusColor(testResult.status)}`}>
                    Status: {testResult.status}
                  </span>
                  <span className="text-gray-400">
                    {testResult.duration}ms
                  </span>
                </div>
                <pre className="whitespace-pre-wrap">
                  {activeTab === 'response' && JSON.stringify(testResult.data, null, 2)}
                  {activeTab === 'headers' && JSON.stringify(testResult.headers, null, 2)}
                  {activeTab === 'request' && JSON.stringify({ 
                    method: endpoint.method, 
                    path: endpoint.path,
                    timestamp: testResult.timestamp
                  }, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}