import { useState, useEffect, useRef } from "react";
import { type MetaFunction } from "@remix-run/node";
import { Link, useNavigate } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import LoadingSpinner from "~/components/common/LoadingSpinner";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import { formatRelativeTime, formatNumber } from "~/lib/utils";
import type { Post, PaginatedResponse, PostFilters } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "게시판 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 주민들의 소통 공간" },
  ];
};

// Client-side data fetching으로 변경 (loader 제거)

const categories = [
  { value: "all", label: "전체" },
  { value: "info", label: "입주 정보" },
  { value: "life", label: "생활 정보" },
  { value: "story", label: "이야기" }
];

const sortOptions = [
  { value: "latest", label: "최신순" },
  { value: "views", label: "조회수" },
  { value: "likes", label: "추천수" },
  { value: "comments", label: "댓글수" }
];

export default function Board() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError } = useNotification();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  // State for data and UI
  const [posts, setPosts] = useState<PaginatedResponse<Post>>({
    items: [],
    total: 0,
    page: 1,
    size: 50, // 한 번에 많은 데이터 가져오기
    pages: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [filteredPosts, setFilteredPosts] = useState<Post[]>([]);
  const [sortedPosts, setSortedPosts] = useState<Post[]>([]);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [sortBy, setSortBy] = useState("latest");
  const [searchQuery, setSearchQuery] = useState("");
  const [scrollCounter, setScrollCounter] = useState("0 / 0개 게시글");
  const [visiblePostsCount, setVisiblePostsCount] = useState(5);
  const [hasMorePosts, setHasMorePosts] = useState(true);

  // API 호출 함수
  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filters: PostFilters = {
        service: "residential_community",
        sortBy: "created_at",
        page: 1,
        size: 50
      };
      
      const response = await apiClient.getPosts(filters);
      
      if (response.success && response.data) {
        console.log('Board: API response data:', response.data);
        console.log('Board: First post:', response.data.items[0]);
        setPosts(response.data);
        setFilteredPosts(response.data.items);
        applySortToFilteredPosts(response.data.items, sortBy);
      } else {
        setError(response.error || 'Failed to fetch posts');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // 초기 데이터 로드
  useEffect(() => {
    fetchPosts();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // HTML 원본과 동일한 필터링 로직 (API 데이터 기반으로 수정)
  const handleCategoryFilter = (filterValue: string) => {
    setCurrentFilter(filterValue);
    
    let filtered;
    if (filterValue === 'all') {
      filtered = [...posts.items];
    } else {
      // category 필드를 사용하여 필터링
      const categoryMapping: { [key: string]: string[] } = {
        'info': ['입주 정보', '입주정보'],
        'life': ['생활 정보', '생활정보'], 
        'story': ['이야기']
      };
      
      filtered = posts.items.filter((post: Post) => {
        const postCategory = post.metadata?.category;
        if (!postCategory) return false;
        
        const acceptedCategories = categoryMapping[filterValue];
        return acceptedCategories && acceptedCategories.includes(postCategory);
      });
    }
    
    setFilteredPosts(filtered);
    applySortToFilteredPosts(filtered, sortBy);
  };

  // API 데이터에 맞게 수정된 정렬 로직
  const applySortToFilteredPosts = (postsToSort: Post[], sortOption: string) => {
    let sorted;
    switch(sortOption) {
      case 'latest':
        sorted = [...postsToSort].sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        break;
      case 'views':
        sorted = [...postsToSort].sort((a, b) => 
          (b.stats?.view_count || b.stats?.views || 0) - (a.stats?.view_count || a.stats?.views || 0)
        );
        break;
      case 'likes':
        sorted = [...postsToSort].sort((a, b) => 
          (b.stats?.like_count || b.stats?.likes || 0) - (a.stats?.like_count || a.stats?.likes || 0)
        );
        break;
      case 'comments':
        sorted = [...postsToSort].sort((a, b) => 
          (b.stats?.comment_count || b.stats?.comments || 0) - (a.stats?.comment_count || a.stats?.comments || 0)
        );
        break;
      default:
        sorted = [...postsToSort];
    }
    
    setSortedPosts(sorted);
    updateScrollCounter(sorted.length);
  };

  const handleSort = (sortOption: string) => {
    setSortBy(sortOption);
    applySortToFilteredPosts(filteredPosts, sortOption);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const filtered = posts.items.filter((post: Post) =>
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredPosts(filtered);
      applySortToFilteredPosts(filtered, sortBy);
    } else {
      setFilteredPosts(posts.items);
      applySortToFilteredPosts(posts.items, sortBy);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(e as React.FormEvent);
    }
  };

  const updateScrollCounter = (totalCount: number) => {
    const maxVisible = Math.min(visiblePostsCount, totalCount);
    setScrollCounter(`1-${maxVisible} / ${totalCount}개 게시글`);
    setHasMorePosts(totalCount > visiblePostsCount);
  };

  // 스크롤 이벤트 핸들러
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    
    // 스크롤 진행률 계산
    const scrollPercent = scrollTop / (scrollHeight - clientHeight);
    
    // 현재 보이는 게시글 수 계산 (대략적)
    const estimatedVisible = Math.min(
      Math.ceil((scrollTop / scrollHeight) * sortedPosts.length) + 5,
      sortedPosts.length
    );
    
    if (estimatedVisible !== visiblePostsCount) {
      setVisiblePostsCount(estimatedVisible);
      updateScrollCounter(sortedPosts.length);
    }
  };

  const getTagColor = (category: string) => {
    switch (category) {
      case '입주 정보':
      case '입주정보':
      case 'info': 
        return 'post-tag-info';
      case '생활 정보':
      case '생활정보':
      case 'life': 
        return 'post-tag-life';
      case '이야기':
      case 'story': 
        return 'post-tag-story';
      default: 
        return 'post-tag-info';
    }
  };

  useEffect(() => {
    if (sortedPosts.length > 0) {
      setVisiblePostsCount(5); // 초기값 리셋
      updateScrollCounter(sortedPosts.length);
    }
  }, [sortedPosts.length]); // 길이만 의존성으로 변경

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      {/* 글쓰기 버튼과 검색창 - 나란히 배치 */}
      <div className="flex justify-center items-center gap-4 mb-4">
        <Link
          to="/board/write"
          className="w-full max-w-xs px-6 py-3 bg-var-card border border-var-color rounded-full hover:border-accent-primary hover:bg-var-hover transition-all duration-200 font-medium text-var-primary flex items-center justify-center gap-2"
        >
          ✏️ 글쓰기
        </Link>
        
        <div className="flex items-center gap-3 bg-var-card border border-var-color rounded-full px-4 py-3 w-full max-w-xs">
          <span className="text-var-muted">🔍</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="게시글 검색..."
            className="flex-1 bg-transparent border-none outline-none text-var-primary placeholder-var-muted"
          />
        </div>
      </div>

      {/* 필터바와 정렬 옵션 */}
      <div className="flex justify-between items-center mb-4">
        {/* 필터 바 */}
        <div className="flex gap-2">
          {categories.map((category) => (
            <button
              key={category.value}
              onClick={() => handleCategoryFilter(category.value)}
              className={`px-4 py-2 border rounded-full text-sm font-medium transition-all duration-200 ${
                currentFilter === category.value
                  ? 'border-accent-primary bg-accent-primary text-white'
                  : 'border-var-color bg-var-card text-var-secondary hover:border-accent-primary hover:text-accent-primary'
              }`}
            >
              {category.label}
            </button>
          ))}
        </div>

        {/* 정렬 옵션 */}
        <div className="flex items-center gap-2">
          <span className="text-var-muted text-sm">정렬:</span>
          <select
            value={sortBy}
            onChange={(e) => handleSort(e.target.value)}
            className="bg-var-card border border-var-color rounded-lg px-3 py-1 text-sm text-var-primary"
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

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
          <button
            onClick={fetchPosts}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            다시 시도
          </button>
        </div>
      )}

      {/* 자유게시판 */}
      {!loading && !error && (
        <div className="post-list mt-4">
          {/* 스크롤 인디케이터 */}
          <div className="flex justify-between items-center mb-4 text-sm text-var-muted">
            <span>{scrollCounter}</span>
            <div className="flex-1 mx-4 h-1 bg-var-section rounded-full overflow-hidden">
              <div 
                className="h-full bg-accent-primary transition-all duration-300"
                style={{ width: `${Math.min(100, (visiblePostsCount / Math.max(1, sortedPosts.length)) * 100)}%` }}
              />
            </div>
          </div>
          
          {/* 게시글 컨테이너 (고정 높이) */}
          <div 
            ref={scrollContainerRef}
            className="posts-scroll-container relative h-[600px] overflow-y-auto overflow-x-hidden border border-var-light rounded-xl mb-4 bg-var-card"
            onScroll={handleScroll}
            style={{ pointerEvents: 'auto' }}
          >
            <div>
              {sortedPosts.length > 0 ? (
                sortedPosts.map((post: Post) => {
                  console.log(`Board: Post ${post.id} slug:`, post.slug);
                  return (
                    <div 
                      key={post.id}
                      className="post-item flex items-start cursor-pointer"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Post clicked, navigating to:', `/posts/${post.slug}`);
                        navigate(`/posts/${post.slug}`);
                      }}
                    >
                      <div className="flex-1">
                        {/* 카테고리와 제목 (같은 줄) */}
                        <div className="post-title flex items-center gap-2 mb-2">
                          <span className={`post-tag ${getTagColor(post.metadata?.category || 'info')}`}>
                            {post.metadata?.category || '일반'}
                          </span>
                          <span className="text-var-primary font-medium text-lg">
                            {post.title}
                          </span>
                          {/* 새 게시글 표시 (24시간 이내) */}
                          {new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000 && (
                            <span className="badge-new">NEW</span>
                          )}
                        </div>
                        
                        {/* 하단: 태그 및 작성자/시간/통계 */}
                        <div className="post-meta flex items-center justify-between text-sm text-var-muted">
                          {/* 좌측: 사용자 태그 */}
                          <div className="flex items-center gap-1">
                            {post.metadata?.tags && post.metadata.tags.length > 0 ? (
                              <>
                                {post.metadata.tags.slice(0, 3).map((tag, index) => (
                                  <span
                                    key={index}
                                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-200"
                                  >
                                    #{tag}
                                  </span>
                                ))}
                                {post.metadata.tags.length > 3 && (
                                  <span className="text-xs text-var-muted px-1">
                                    +{post.metadata.tags.length - 3}
                                  </span>
                                )}
                              </>
                            ) : (
                              <div></div>
                            )}
                          </div>
                          
                          {/* 우측: 작성자, 시간, 통계 */}
                          <div className="flex items-center gap-2">
                            <span className="text-var-secondary">
                              {post.author?.display_name || post.author?.user_handle || '익명'}
                            </span>
                            <span>·</span>
                            <span>{formatRelativeTime(post.created_at)}</span>
                            <span>·</span>
                            <span className="stat-icon text-var-muted">
                              👁️ {formatNumber(post.stats?.view_count || post.stats?.views || 0)}
                            </span>
                            <span className="stat-icon text-var-muted">
                              👍 {formatNumber(post.stats?.like_count || post.stats?.likes || 0)}
                            </span>
                            <span className="stat-icon text-var-muted">
                              👎 {formatNumber(post.stats?.dislike_count || post.stats?.dislikes || 0)}
                            </span>
                            <span className="stat-icon text-var-muted">
                              💬 {formatNumber(post.stats?.comment_count || post.stats?.comments || 0)}
                            </span>
                            <span className="stat-icon text-var-muted">
                              🔖 {formatNumber(post.stats?.bookmark_count || post.stats?.bookmarks || 0)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center p-8">
                  <div className="text-6xl mb-4">📝</div>
                  <h3 className="text-var-primary font-semibold text-lg mb-2">
                    게시글이 없습니다
                  </h3>
                  <p className="text-var-secondary">
                    {searchQuery ? '검색 결과가 없습니다. 다른 키워드로 검색해보세요.' : '첫 번째 게시글을 작성해보세요!'}
                  </p>
                </div>
              )}
            </div>
            
            {/* 페이드 그라디언트 오버레이 */}
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-var-primary to-transparent pointer-events-none" />
          </div>
          
          {/* 하단 안내 배너 */}
          {hasMorePosts && (
            <div className="text-center text-var-muted text-sm py-3 rounded-lg" style={{ backgroundColor: '#f0f8e8' }}>
              👇 아래로 스크롤하여 더 많은 게시글을 확인하세요
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}