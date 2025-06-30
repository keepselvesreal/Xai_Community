import { useState, useEffect, useRef } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import type { MockPost } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "게시판 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 주민들의 소통 공간" },
  ];
};

export const loader: LoaderFunction = async () => {
  // 15개 게시글 Mock 데이터
  const posts = [
    {
      id: 1,
      title: "새로 이사오신 분들 환영합니다! 🏠",
      author: "관리사무소",
      time: "1시간 전",
      timeValue: 1,
      tag: "info",
      tagText: "입주정보",
      views: 127,
      likes: 15,
      dislikes: 0,
      comments: 8,
      bookmarks: 3,
      isNew: true,
      content: "안녕하세요! 새로 이사오신 주민 여러분을 환영합니다. 입주 관련 필요한 절차와 정보를 안내드립니다..."
    },
    {
      id: 2,
      title: "엘리베이터 정기점검 안내 📢",
      author: "관리사무소",
      time: "3시간 전",
      timeValue: 3,
      tag: "info",
      tagText: "입주정보",
      views: 89,
      likes: 12,
      dislikes: 1,
      comments: 5,
      bookmarks: 7,
      isNew: true,
      content: "다음 주 화요일 오전 10시부터 12시까지 엘리베이터 정기점검이 있습니다..."
    },
    {
      id: 3,
      title: "겨울철 난방비 절약 꿀팁 공유 ❄️",
      author: "절약왕303호",
      time: "5시간 전",
      timeValue: 5,
      tag: "life",
      tagText: "생활정보",
      views: 234,
      likes: 45,
      dislikes: 2,
      comments: 23,
      bookmarks: 18,
      isNew: false,
      content: "겨울철 난방비를 30% 절약할 수 있는 실용적인 방법들을 공유합니다..."
    },
    {
      id: 4,
      title: "우리 아파트 반려동물 친구들 🐕🐱",
      author: "펫러버501호",
      time: "1일 전",
      timeValue: 24,
      tag: "story",
      tagText: "이야기",
      views: 156,
      likes: 67,
      dislikes: 0,
      comments: 34,
      bookmarks: 12,
      isNew: false,
      content: "우리 아파트 귀여운 반려동물 친구들을 소개합니다! 산책 친구도 구해요..."
    },
    {
      id: 5,
      title: "주차장 에티켓 지켜주세요 🚗",
      author: "주차지킴이",
      time: "1일 전",
      timeValue: 25,
      tag: "life",
      tagText: "생활정보",
      views: 98,
      likes: 8,
      dislikes: 3,
      comments: 12,
      bookmarks: 5,
      isNew: false,
      content: "최근 주차 관련 불편 사항이 늘고 있습니다. 서로 배려하는 주차 문화를 만들어요..."
    },
    {
      id: 6,
      title: "아이들 놀이터 안전 점검 완료 ✅",
      author: "관리사무소",
      time: "2일 전",
      timeValue: 48,
      tag: "info",
      tagText: "입주정보",
      views: 67,
      likes: 14,
      dislikes: 0,
      comments: 3,
      bookmarks: 9,
      isNew: false,
      content: "어린이 놀이터 안전 점검이 완료되었습니다. 모든 시설이 안전함을 확인했습니다..."
    },
    {
      id: 7,
      title: "층간소음 신고 관련 안내 🔇",
      author: "관리사무소",
      time: "3일 전",
      timeValue: 72,
      tag: "info",
      tagText: "입주정보",
      views: 203,
      likes: 19,
      dislikes: 5,
      comments: 28,
      bookmarks: 15,
      isNew: false,
      content: "층간소음 신고 절차와 해결 방안에 대해 안내드립니다..."
    },
    {
      id: 8,
      title: "봄맞이 화단 정리 자원봉사 모집 🌸",
      author: "꽃사랑회",
      time: "4일 전",
      timeValue: 96,
      tag: "story",
      tagText: "이야기",
      views: 134,
      likes: 28,
      dislikes: 1,
      comments: 16,
      bookmarks: 6,
      isNew: false,
      content: "봄을 맞아 아파트 화단을 예쁘게 꾸밀 자원봉사자를 모집합니다..."
    },
    {
      id: 9,
      title: "택배 보관함 이용 안내 📦",
      author: "관리사무소",
      time: "5일 전",
      timeValue: 120,
      tag: "info",
      tagText: "입주정보",
      views: 95,
      likes: 11,
      dislikes: 0,
      comments: 6,
      bookmarks: 11,
      isNew: false,
      content: "택배 보관함 이용 방법과 주의사항을 안내드립니다..."
    },
    {
      id: 10,
      title: "공동 구매 제안 - 생필품 🛒",
      author: "알뜰주부202호",
      time: "5일 전",
      timeValue: 125,
      tag: "story",
      tagText: "이야기",
      views: 178,
      likes: 32,
      dislikes: 2,
      comments: 19,
      bookmarks: 8,
      isNew: false,
      content: "생필품 공동구매로 비용을 절약해보아요! 참여하실 분들 댓글 남겨주세요..."
    },
    {
      id: 11,
      title: "헬스장 운영시간 변경 안내 💪",
      author: "관리사무소",
      time: "6일 전",
      timeValue: 144,
      tag: "info",
      tagText: "입주정보",
      views: 142,
      likes: 8,
      dislikes: 4,
      comments: 11,
      bookmarks: 4,
      isNew: false,
      content: "헬스장 운영시간이 변경됩니다. 새로운 이용시간을 확인해주세요..."
    },
    {
      id: 12,
      title: "분리수거 요일 변경 ♻️",
      author: "관리사무소",
      time: "1주 전",
      timeValue: 168,
      tag: "info",
      tagText: "입주정보",
      views: 201,
      likes: 16,
      dislikes: 1,
      comments: 7,
      bookmarks: 10,
      isNew: false,
      content: "분리수거 배출 요일이 변경됩니다. 새로운 일정을 확인해주세요..."
    },
    {
      id: 13,
      title: "우리 아파트 독서모임 📚",
      author: "책사랑404호",
      time: "1주 전",
      timeValue: 172,
      tag: "story",
      tagText: "이야기",
      views: 87,
      likes: 23,
      dislikes: 0,
      comments: 14,
      bookmarks: 2,
      isNew: false,
      content: "독서를 좋아하시는 분들과 함께 모임을 만들어보고 싶어요..."
    },
    {
      id: 14,
      title: "겨울철 배관 동파 방지 안내 🧊",
      author: "관리사무소",
      time: "1주 전",
      timeValue: 180,
      tag: "life",
      tagText: "생활정보",
      views: 165,
      likes: 21,
      dislikes: 0,
      comments: 9,
      bookmarks: 13,
      isNew: false,
      content: "겨울철 배관 동파 방지를 위한 주의사항을 안내드립니다..."
    },
    {
      id: 15,
      title: "커뮤니티 공간 예약 방법 🏢",
      author: "관리사무소",
      time: "1주 전",
      timeValue: 185,
      tag: "info",
      tagText: "입주정보",
      views: 112,
      likes: 13,
      dislikes: 0,
      comments: 4,
      bookmarks: 1,
      isNew: false,
      content: "커뮤니티 공간 예약 방법과 이용 규칙을 안내드립니다..."
    }
  ];

  return json({ posts });
};

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
  const { posts: initialPosts } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError } = useNotification();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  const [filteredPosts, setFilteredPosts] = useState(initialPosts);
  const [sortedPosts, setSortedPosts] = useState(initialPosts);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [sortBy, setSortBy] = useState("latest");
  const [searchQuery, setSearchQuery] = useState("");
  const [scrollCounter, setScrollCounter] = useState("1-5 / 15개 게시글");
  const [visiblePostsCount, setVisiblePostsCount] = useState(5); // 표시되는 게시글 수
  const [hasMorePosts, setHasMorePosts] = useState(true);

  // HTML 원본과 동일한 필터링 로직
  const handleCategoryFilter = (filterValue: string) => {
    setCurrentFilter(filterValue);
    
    let filtered;
    if (filterValue === 'all') {
      filtered = [...initialPosts];
    } else {
      filtered = initialPosts.filter((post: MockPost) => post.tag === filterValue);
    }
    
    setFilteredPosts(filtered);
    applySortToFilteredPosts(filtered, sortBy);
  };

  // HTML 원본과 동일한 정렬 로직
  const applySortToFilteredPosts = (posts: MockPost[], sortOption: string) => {
    let sorted;
    switch(sortOption) {
      case 'latest':
        sorted = [...posts].sort((a, b) => a.timeValue - b.timeValue);
        break;
      case 'views':
        sorted = [...posts].sort((a, b) => b.views - a.views);
        break;
      case 'likes':
        sorted = [...posts].sort((a, b) => b.likes - a.likes);
        break;
      case 'comments':
        sorted = [...posts].sort((a, b) => b.comments - a.comments);
        break;
      default:
        sorted = [...posts];
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
      const filtered = initialPosts.filter((post: MockPost) =>
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredPosts(filtered);
      applySortToFilteredPosts(filtered, sortBy);
    } else {
      setFilteredPosts(initialPosts);
      applySortToFilteredPosts(initialPosts, sortBy);
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

  const getTagColor = (tag: string) => {
    switch (tag) {
      case 'info': return 'post-tag-info';
      case 'life': return 'post-tag-life';
      case 'story': return 'post-tag-story';
      default: return 'post-tag-info';
    }
  };

  useEffect(() => {
    setVisiblePostsCount(5); // 초기값 리셋
    updateScrollCounter(sortedPosts.length);
  }, [sortedPosts]);

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

      {/* 자유게시판 */}
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
        >
          <div>
            {sortedPosts.length > 0 ? (
              sortedPosts.map((post: MockPost) => (
                <Link key={post.id} to={`/posts/${post.id}`}>
                  <div className="post-item flex items-start cursor-pointer">
                    <div className="flex-1">
                      <div className="post-title flex items-center gap-2 mb-1">
                        <span className={`post-tag ${
                          post.tag === 'info' 
                            ? 'post-tag-info'
                            : post.tag === 'life'
                            ? 'post-tag-life'
                            : 'post-tag-story'
                        }`}>
                          {post.tagText}
                        </span>
                        <span className="text-var-primary font-medium text-lg">
                          {post.title}
                        </span>
                        {post.isNew && (
                          <span className="badge-new">NEW</span>
                        )}
                      </div>
                      
                      <div className="post-meta">
                        <span className="text-var-muted text-sm">{post.author} · {post.time}</span>
                        <div className="flex items-center gap-3">
                          <span className="stat-icon text-var-muted">
                            👁️ {post.views}
                          </span>
                          <span className="stat-icon text-var-muted">
                            👍 {post.likes}
                          </span>
                          <span className="stat-icon text-var-muted">
                            👎 {post.dislikes}
                          </span>
                          <span className="stat-icon text-var-muted">
                            💬 {post.comments}
                          </span>
                          <span className="stat-icon text-var-muted">
                            🔖 {post.bookmarks}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))
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
    </AppLayout>
  );
}