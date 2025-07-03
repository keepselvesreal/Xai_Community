import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import { useState, useEffect } from "react";
import AppLayout from "~/components/layout/AppLayout";
import Card from "~/components/ui/Card";
import { PostCardSkeleton } from "~/components/common/PostCardSkeleton";
import { useAuth } from "~/contexts/AuthContext";
import { apiClient } from "~/lib/api";
import { CacheManager, CACHE_KEYS } from "~/lib/cache";
import type { Post } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "XAI 아파트 커뮤니티" },
    { name: "description", content: "함께 만들어가는 우리 아파트 소통공간" },
  ];
};

export const loader: LoaderFunction = async () => {
  // 서버에서 최신 게시글 미리 로딩 (미래 SSR 적용 대비)
  return json({
    initialData: null // 현재는 클라이언트에서 로딩, 추후 서버 데이터로 변경
  });
};

export default function Home() {
  // 테스트 환경에서는 loader 데이터가 없을 수 있음
  let initialData = null;
  try {
    initialData = useLoaderData<typeof loader>()?.initialData;
  } catch {
    // 테스트 환경에서는 useLoaderData가 실패할 수 있음
  }
  
  const { user, logout } = useAuth();
  const [recentPosts, setRecentPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState(true);

  // 최근 게시글 로드 (캐싱 적용)
  const loadRecentPosts = async () => {
    // 캐시된 데이터 먼저 확인
    const cachedPosts = CacheManager.getFromCache<Post[]>(CACHE_KEYS.RECENT_POSTS);
    if (cachedPosts) {
      setRecentPosts(cachedPosts);
      setPostsLoading(false);
      
      // 백그라운드에서 최신 데이터 업데이트
      updateRecentPostsInBackground();
      return;
    }

    // 캐시가 없으면 로딩 상태로 API 호출
    setPostsLoading(true);
    await fetchAndCacheRecentPosts();
  };

  const fetchAndCacheRecentPosts = async () => {
    try {
      const response = await apiClient.getPosts({ 
        page: 1, 
        size: 4, 
        sortBy: 'created_at',
        service: 'residential_community' // 올바른 서비스 타입 지정
      });
      if (response.success && response.data) {
        const posts = response.data.items;
        setRecentPosts(posts);
        
        // 캐시에 저장 (5분 TTL)
        CacheManager.saveToCache(CACHE_KEYS.RECENT_POSTS, posts, 5 * 60 * 1000);
      }
    } catch (error) {
      console.error('최근 게시글 로드 실패:', error);
    } finally {
      setPostsLoading(false);
    }
  };

  const updateRecentPostsInBackground = async () => {
    try {
      const response = await apiClient.getPosts({ 
        page: 1, 
        size: 4, 
        sortBy: 'created_at',
        service: 'residential_community' // 올바른 서비스 타입 지정
      });
      if (response.success && response.data) {
        const newPosts = response.data.items;
        
        // 새로운 데이터가 있으면 부드럽게 업데이트
        setRecentPosts(newPosts);
        CacheManager.saveToCache(CACHE_KEYS.RECENT_POSTS, newPosts, 5 * 60 * 1000);
      }
    } catch (error) {
      console.warn('백그라운드 업데이트 실패:', error);
    }
  };

  useEffect(() => {
    // 앱 시작 시 기존 캐시 정리 (한 번만 실행)
    const hasCleanedCache = sessionStorage.getItem('cache-cleaned');
    if (!hasCleanedCache) {
      CacheManager.clearPageCaches();
      sessionStorage.setItem('cache-cleaned', 'true');
      console.log('✨ 기존 캐시 정리 완료');
    }
    
    loadRecentPosts();
  }, []);

  const mainServices = [
    {
      title: '정보',
      description: '아파트 관련 유용한 정보',
      icon: 'ℹ️',
      href: '/info',
      color: 'bg-blue-50 hover:bg-blue-100'
    },
    {
      title: '입주 업체 서비스',
      description: '우리 아파트 업체 소개',
      icon: '🏢',
      href: '/services',
      color: 'bg-green-50 hover:bg-green-100'
    },
    {
      title: '전문가 꿀정보',
      description: '검증된 생활 팁',
      icon: '💡',
      href: '/tips',
      color: 'bg-yellow-50 hover:bg-yellow-100'
    }
  ];

  return (
    <AppLayout 
      title="XAI 아파트 커뮤니티" 
      subtitle="함께 만들어가는 우리 아파트 소통공간"
      user={user}
      onLogout={logout}
    >
      {/* 환영 메시지 */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🏠 XAI 아파트 커뮤니티에 오신 것을 환영합니다
        </h1>
        <p className="text-xl text-gray-600">
          우리 아파트의 모든 정보와 소통이 한 곳에
        </p>
      </div>

      {/* 주요 서비스 */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">📋 주요 서비스</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {mainServices.map((service) => (
            <Link
              key={service.title}
              to={service.href}
              className={`block p-6 rounded-xl border-2 border-transparent transition-all duration-200 ${service.color} hover:border-gray-200 hover:shadow-lg`}
            >
              <div className="text-center">
                <div className="text-4xl mb-3">{service.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {service.title}
                </h3>
                <p className="text-gray-600">{service.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* 최근 게시글 */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">📝 최근 게시글</h2>
          <Link 
            to="/board" 
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            모든 게시글 보기 →
          </Link>
        </div>

        {postsLoading ? (
          <PostCardSkeleton count={4} />
        ) : recentPosts.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {recentPosts.map((post) => (
              <Card key={post.id} className="hover:shadow-md transition-shadow">
                <Card.Content>
                  <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                    {post.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                    {post.content}
                  </p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{post.author?.display_name || '익명'}</span>
                    <span>{new Date(post.created_at).toLocaleDateString()}</span>
                  </div>
                </Card.Content>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <Card.Content className="text-center py-12">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                아직 게시글이 없습니다
              </h3>
              <p className="text-gray-600 mb-4">
                첫 번째 게시글을 작성해보세요!
              </p>
              <Link 
                to="/posts/create"
                className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                게시글 작성하기
              </Link>
            </Card.Content>
          </Card>
        )}
      </div>

      {/* 커뮤니티 정보 */}
      <div className="bg-gray-50 rounded-xl p-6 text-center">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          💬 함께 소통해요
        </h3>
        <p className="text-gray-600">
          궁금한 것이 있으시면 언제든지 게시판에 올려주세요. 
          이웃들이 친절하게 답변해드릴게요!
        </p>
      </div>
    </AppLayout>
  );
}