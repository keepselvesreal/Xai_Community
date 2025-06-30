import { type MetaFunction } from "@remix-run/node";
import { useSearchParams } from "@remix-run/react";
import { useState, useEffect } from "react";
import { Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import PostCard from "~/components/post/PostCard";
import PostFilters from "~/components/post/PostFilters";
import Button from "~/components/ui/Button";
import LoadingSpinner from "~/components/common/LoadingSpinner";
import { useAuth } from "~/contexts/AuthContext";
import { usePagination } from "~/hooks/usePagination";
import { PAGINATION } from "~/lib/constants";
import { apiClient } from "~/lib/api";
import type { Post, PostFilters as PostFiltersType, PaginatedResponse } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "게시글 목록 | FastAPI UI" },
    { name: "description", content: "모든 게시글을 확인하세요" },
  ];
};

// Client-side data fetching으로 변경 (loader 제거)

export default function PostsIndex() {
  const { user, logout } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State for data and UI
  const [posts, setPosts] = useState<PaginatedResponse<Post>>({
    items: [],
    total: 0,
    page: 1,
    size: PAGINATION.DEFAULT_SIZE,
    pages: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Extract filters from URL params
  const getFiltersFromParams = (): PostFiltersType => ({
    type: searchParams.get("type") || undefined,
    service: searchParams.get("service") || "residential_community", // 기본값 설정
    sortBy: (searchParams.get("sortBy") as any) || "created_at",
    search: searchParams.get("search") || undefined,
    page: parseInt(searchParams.get("page") || "1"),
    size: parseInt(searchParams.get("size") || PAGINATION.DEFAULT_SIZE.toString()),
  });

  const [currentFilters, setCurrentFilters] = useState<PostFiltersType>(getFiltersFromParams());

  const pagination = usePagination({
    initialPage: currentFilters.page || 1,
    initialSize: currentFilters.size || PAGINATION.DEFAULT_SIZE,
    totalItems: posts.total,
  });

  // API 호출 함수
  const fetchPosts = async (filters: PostFiltersType) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.getPosts(filters);
      
      if (response.success && response.data) {
        setPosts(response.data);
        // Update pagination with new data
        pagination.goToPage(response.data.page);
      } else {
        setError(response.error || 'Failed to fetch posts');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Load posts when filters change
  useEffect(() => {
    fetchPosts(currentFilters);
  }, [currentFilters]);

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (currentFilters.type) params.set("type", currentFilters.type);
    if (currentFilters.service) params.set("service", currentFilters.service);
    if (currentFilters.sortBy && currentFilters.sortBy !== "created_at") {
      params.set("sortBy", currentFilters.sortBy);
    }
    if (currentFilters.search) params.set("search", currentFilters.search);
    if (currentFilters.page && currentFilters.page !== 1) params.set("page", currentFilters.page.toString());
    if (currentFilters.size && currentFilters.size !== PAGINATION.DEFAULT_SIZE) params.set("size", currentFilters.size.toString());

    setSearchParams(params);
  }, [currentFilters, setSearchParams]);

  // Update filters when URL params change
  useEffect(() => {
    const newFilters = getFiltersFromParams();
    setCurrentFilters(newFilters);
  }, [searchParams]);

  const handleFiltersChange = (newFilters: PostFiltersType) => {
    setCurrentFilters({ ...newFilters, page: 1 }); // Reset to first page on filter change
  };

  const handlePageChange = (page: number) => {
    setCurrentFilters({ ...currentFilters, page });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRetry = () => {
    fetchPosts(currentFilters);
  };

  return (
    <AppLayout 
      title="게시글 목록" 
      subtitle="모든 게시글을 확인하세요"
      user={user}
      onLogout={logout}
    >
      {/* 헤더 액션 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">게시글 목록</h1>
          <p className="text-gray-600 mt-1">
            총 {posts.total}개의 게시글
          </p>
        </div>
        
        {user && (
          <Link to="/posts/create">
            <Button>
              ✍️ 새 게시글
            </Button>
          </Link>
        )}
      </div>

      {/* 필터 */}
      <PostFilters
        filters={currentFilters}
        onFiltersChange={handleFiltersChange}
        className="mb-6"
      />

      {/* 로딩 상태 */}
      {loading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {/* 에러 상태 */}
      {error && !loading && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-red-600 mb-2">오류가 발생했습니다</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={handleRetry} variant="outline">
            다시 시도
          </Button>
        </div>
      )}

      {/* 게시글 목록 */}
      {!loading && !error && (
        <div className="space-y-4 mb-8">
          {posts.items.length > 0 ? (
            posts.items.map(post => (
              <PostCard key={post.id} post={post} />
            ))
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📄</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">게시글이 없습니다</h3>
              <p className="text-gray-600 mb-4">
                검색 조건을 변경하거나 새 게시글을 작성해보세요.
              </p>
              {user && (
                <Link to="/posts/create">
                  <Button>
                    새 게시글 작성
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>
      )}

      {/* 페이지네이션 */}
      {!loading && !error && posts.pages > 1 && (
        <div className="flex justify-center">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(1)}
              disabled={posts.page <= 1}
            >
              처음
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(posts.page - 1)}
              disabled={posts.page <= 1}
            >
              이전
            </Button>

            {/* 간단한 페이지 번호 표시 */}
            {Array.from({ length: Math.min(5, posts.pages) }, (_, i) => {
              const startPage = Math.max(1, posts.page - 2);
              const pageNum = startPage + i;
              if (pageNum > posts.pages) return null;
              
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === posts.page ? "primary" : "outline"}
                  size="sm"
                  onClick={() => handlePageChange(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}

            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(posts.page + 1)}
              disabled={posts.page >= posts.pages}
            >
              다음
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(posts.pages)}
              disabled={posts.page >= posts.pages}
            >
              마지막
            </Button>
          </div>
        </div>
      )}
    </AppLayout>
  );
}