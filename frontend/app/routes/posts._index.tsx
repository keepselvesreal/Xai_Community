import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useSearchParams } from "@remix-run/react";
import { useState, useEffect } from "react";
import { Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import PostCard from "~/components/post/PostCard";
import PostFilters from "~/components/post/PostFilters";
import Button from "~/components/ui/Button";
import { useAuth } from "~/contexts/AuthContext";
import { usePagination } from "~/hooks/usePagination";
import { PAGINATION } from "~/lib/constants";
import type { Post, PostFilters as PostFiltersType, PaginatedResponse } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "게시글 목록 | FastAPI UI" },
    { name: "description", content: "모든 게시글을 확인하세요" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  // URL 파라미터에서 필터 정보 추출
  const filters: PostFiltersType = {
    type: searchParams.get("type") || undefined,
    service: searchParams.get("service") || undefined,
    sortBy: (searchParams.get("sortBy") as any) || "created_at",
    search: searchParams.get("search") || undefined,
    page: parseInt(searchParams.get("page") || "1"),
    size: parseInt(searchParams.get("size") || PAGINATION.DEFAULT_SIZE.toString()),
  };

  // 모의 게시글 데이터
  const mockPosts: Post[] = [
    {
      id: 1,
      title: "FastAPI 개발 가이드",
      content: "FastAPI를 사용한 효율적인 API 개발 방법에 대해 설명합니다. 이 가이드에서는 기본적인 설정부터 고급 기능까지 다양한 내용을 다룹니다.",
      slug: "fastapi-development-guide",
      author: "developer1",
      type: "자유게시판",
      service: "community",
      created_at: "2024-01-15T14:30:00Z",
      updated_at: "2024-01-15T14:30:00Z",
      stats: { views: 124, likes: 15, dislikes: 2, comments: 8, bookmarks: 12 },
      tags: ["FastAPI", "Python", "API", "개발"]
    },
    {
      id: 2,
      title: "UI 컴포넌트 디자인 패턴",
      content: "재사용 가능한 UI 컴포넌트 설계에 대한 모범 사례를 소개합니다. React와 TypeScript를 활용한 효율적인 컴포넌트 개발 방법을 알아보세요.",
      slug: "ui-component-design-patterns",
      author: "designer1",
      type: "질문답변",
      service: "community",
      created_at: "2024-01-14T09:15:00Z",
      updated_at: "2024-01-14T09:15:00Z",
      stats: { views: 89, likes: 12, dislikes: 1, comments: 5, bookmarks: 8 },
      tags: ["React", "TypeScript", "UI", "디자인패턴"]
    },
    {
      id: 3,
      title: "API 테스트 자동화",
      content: "API 테스트를 자동화하는 방법과 도구들을 소개합니다. Jest, Supertest, Postman을 활용한 효과적인 테스트 전략을 알아보세요.",
      slug: "api-test-automation",
      author: "tester1",
      type: "공지사항",
      service: "community",
      created_at: "2024-01-13T16:45:00Z",
      updated_at: "2024-01-13T16:45:00Z",
      stats: { views: 67, likes: 9, dislikes: 0, comments: 3, bookmarks: 5 },
      tags: ["테스트", "자동화", "API", "Jest"]
    },
    {
      id: 4,
      title: "데이터베이스 최적화 팁",
      content: "PostgreSQL과 MongoDB 성능 최적화를 위한 실전 팁들을 공유합니다. 인덱싱, 쿼리 최적화, 스키마 설계 등 다양한 주제를 다룹니다.",
      slug: "database-optimization-tips",
      author: "dba1",
      type: "후기",
      service: "community",
      created_at: "2024-01-12T11:20:00Z",
      updated_at: "2024-01-12T11:20:00Z",
      stats: { views: 156, likes: 22, dislikes: 1, comments: 12, bookmarks: 18 },
      tags: ["데이터베이스", "PostgreSQL", "MongoDB", "최적화"]
    },
    {
      id: 5,
      title: "React 19 새로운 기능들",
      content: "React 19에서 추가된 새로운 기능들과 개선사항들을 살펴봅니다. Server Components, Concurrent Features 등의 변화점을 알아보세요.",
      slug: "react-19-new-features",
      author: "frontend_dev",
      type: "자유게시판",
      service: "community",
      created_at: "2024-01-11T08:30:00Z",
      updated_at: "2024-01-11T08:30:00Z",
      stats: { views: 203, likes: 28, dislikes: 3, comments: 15, bookmarks: 25 },
      tags: ["React", "Frontend", "JavaScript", "업데이트"]
    }
  ];

  // 필터 적용
  let filteredPosts = mockPosts;

  if (filters.type) {
    filteredPosts = filteredPosts.filter(post => post.type === filters.type);
  }

  if (filters.service) {
    filteredPosts = filteredPosts.filter(post => post.service === filters.service);
  }

  if (filters.search) {
    const searchLower = filters.search.toLowerCase();
    filteredPosts = filteredPosts.filter(post => 
      post.title.toLowerCase().includes(searchLower) ||
      post.content.toLowerCase().includes(searchLower)
    );
  }

  // 정렬
  if (filters.sortBy === "views") {
    filteredPosts.sort((a, b) => b.stats.views - a.stats.views);
  } else if (filters.sortBy === "likes") {
    filteredPosts.sort((a, b) => b.stats.likes - a.stats.likes);
  } else {
    filteredPosts.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }

  // 페이지네이션
  const total = filteredPosts.length;
  const startIndex = (filters.page! - 1) * filters.size!;
  const paginatedPosts = filteredPosts.slice(startIndex, startIndex + filters.size!);

  const response: PaginatedResponse<Post> = {
    items: paginatedPosts,
    total,
    page: filters.page!,
    size: filters.size!,
    pages: Math.ceil(total / filters.size!)
  };

  return json({ posts: response, filters });
};

export default function PostsIndex() {
  const { posts, filters: initialFilters } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentFilters, setCurrentFilters] = useState<PostFiltersType>(initialFilters);

  const pagination = usePagination({
    initialPage: posts.page,
    initialSize: posts.size,
    totalItems: posts.total,
  });

  // URL 업데이트
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (currentFilters.type) params.set("type", currentFilters.type);
    if (currentFilters.service) params.set("service", currentFilters.service);
    if (currentFilters.sortBy && currentFilters.sortBy !== "created_at") {
      params.set("sortBy", currentFilters.sortBy);
    }
    if (currentFilters.search) params.set("search", currentFilters.search);
    if (pagination.page !== 1) params.set("page", pagination.page.toString());
    if (pagination.size !== PAGINATION.DEFAULT_SIZE) params.set("size", pagination.size.toString());

    setSearchParams(params);
  }, [currentFilters, pagination.page, pagination.size, setSearchParams]);

  const handleFiltersChange = (newFilters: PostFiltersType) => {
    setCurrentFilters(newFilters);
    pagination.goToPage(newFilters.page || 1);
  };

  const handlePageChange = (page: number) => {
    pagination.goToPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
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

      {/* 게시글 목록 */}
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

      {/* 페이지네이션 */}
      {posts.pages > 1 && (
        <div className="flex justify-center">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(1)}
              disabled={pagination.isFirstPage}
            >
              처음
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={!pagination.hasPrevious}
            >
              이전
            </Button>

            {pagination.getPageNumbers().map(pageNum => (
              <Button
                key={pageNum}
                variant={pageNum === pagination.page ? "primary" : "outline"}
                size="sm"
                onClick={() => handlePageChange(pageNum)}
              >
                {pageNum}
              </Button>
            ))}

            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={!pagination.hasNext}
            >
              다음
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.totalPages)}
              disabled={pagination.isLastPage}
            >
              마지막
            </Button>
          </div>
        </div>
      )}
    </AppLayout>
  );
}