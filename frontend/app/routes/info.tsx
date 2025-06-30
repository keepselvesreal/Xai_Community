import { useState, useEffect, useRef } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import type { MockInfoItem } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "정보 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 주민들을 위한 유용한 정보" },
  ];
};

export const loader: LoaderFunction = async () => {
  // 8개 정보 Mock 데이터 (이미지 참조)
  const infoItems = [
    {
      id: 1,
      title: "2024년 아파트 시세 동향 분석",
      author: "부동산 전문가",
      time: "1일 전",
      timeValue: 1,
      tag: "tag1",
      tagText: "태그1",
      views: 324,
      likes: 42,
      dislikes: 3,
      comments: 18,
      bookmarks: 25,
      isNew: true,
      content: "2024년 아파트 시세 전망과 동향을 분석한 전문 자료입니다..."
    },
    {
      id: 2,
      title: "전세 계약 시 체크해야 할 필수 사항",
      author: "법무 전문가",
      time: "2일 전",
      timeValue: 2,
      tag: "tag2",
      tagText: "태그2",
      views: 256,
      likes: 35,
      dislikes: 2,
      comments: 12,
      bookmarks: 19,
      isNew: false,
      content: "전세 계약 전 반드시 확인해야 할 사항들을 정리했습니다..."
    },
    {
      id: 3,
      title: "입주 후 각종 신고 및 등록 절차 안내",
      author: "행정 담당자",
      time: "3일 전",
      timeValue: 3,
      tag: "tag3",
      tagText: "태그3",
      views: 189,
      likes: 28,
      dislikes: 1,
      comments: 9,
      bookmarks: 14,
      isNew: false,
      content: "새로 입주하신 분들을 위한 각종 행정 절차 안내입니다..."
    },
    {
      id: 4,
      title: "아파트 관리비 절약하는 방법",
      author: "관리사무소",
      time: "4일 전",
      timeValue: 4,
      tag: "tag1",
      tagText: "태그1",
      views: 278,
      likes: 51,
      dislikes: 2,
      comments: 23,
      bookmarks: 31,
      isNew: false,
      content: "관리비를 효율적으로 절약할 수 있는 실용적인 방법들..."
    },
    {
      id: 5,
      title: "층간소음 문제 해결 가이드",
      author: "소음 전문가",
      time: "5일 전",
      timeValue: 5,
      tag: "tag2",
      tagText: "태그2",
      views: 145,
      likes: 19,
      dislikes: 4,
      comments: 15,
      bookmarks: 8,
      isNew: false,
      content: "층간소음 문제 발생 시 대처 방법과 해결책 안내..."
    },
    {
      id: 6,
      title: "아파트 보안 시설 이용 안내",
      author: "보안 담당자",
      time: "6일 전",
      timeValue: 6,
      tag: "tag3",
      tagText: "태그3",
      views: 98,
      likes: 12,
      dislikes: 0,
      comments: 6,
      bookmarks: 7,
      isNew: false,
      content: "CCTV, 출입통제시스템 등 보안 시설 이용 방법..."
    },
    {
      id: 7,
      title: "공동주택 화재 대피 요령",
      author: "안전 관리자",
      time: "1주 전",
      timeValue: 7,
      tag: "tag1",
      tagText: "태그1",
      views: 167,
      likes: 24,
      dislikes: 1,
      comments: 8,
      bookmarks: 16,
      isNew: false,
      content: "화재 발생 시 안전한 대피 방법과 주의사항..."
    },
    {
      id: 8,
      title: "재활용 분리배출 완벽 가이드",
      author: "환경 담당자",
      time: "1주 전",
      timeValue: 8,
      tag: "tag2",
      tagText: "태그2",
      views: 134,
      likes: 16,
      dislikes: 0,
      comments: 7,
      bookmarks: 11,
      isNew: false,
      content: "올바른 재활용 분리배출 방법과 일정 안내..."
    }
  ];

  return json({ infoItems });
};

const categories = [
  { value: "all", label: "전체" },
  { value: "tag1", label: "태그1" },
  { value: "tag2", label: "태그2" },
  { value: "tag3", label: "태그3" }
];

const sortOptions = [
  { value: "latest", label: "최신순" },
  { value: "views", label: "조회수" },
  { value: "likes", label: "추천수" },
  { value: "comments", label: "댓글수" }
];

export default function Info() {
  const { infoItems: initialInfoItems } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const { showError } = useNotification();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  const [filteredInfoItems, setFilteredInfoItems] = useState(initialInfoItems);
  const [sortedInfoItems, setSortedInfoItems] = useState(initialInfoItems);
  const [currentFilter, setCurrentFilter] = useState("all");
  const [sortBy, setSortBy] = useState("latest");
  const [searchQuery, setSearchQuery] = useState("");
  const [scrollCounter, setScrollCounter] = useState("1-5 / 8개 정보");
  const [visibleItemsCount, setVisibleItemsCount] = useState(5);
  const [hasMoreItems, setHasMoreItems] = useState(true);

  // HTML 원본과 동일한 필터링 로직
  const handleCategoryFilter = (filterValue: string) => {
    setCurrentFilter(filterValue);
    
    let filtered;
    if (filterValue === 'all') {
      filtered = [...initialInfoItems];
    } else {
      filtered = initialInfoItems.filter((item: MockInfoItem) => item.tag === filterValue);
    }
    
    setFilteredInfoItems(filtered);
    applySortToFilteredItems(filtered, sortBy);
  };

  // HTML 원본과 동일한 정렬 로직
  const applySortToFilteredItems = (items: MockInfoItem[], sortOption: string) => {
    let sorted;
    switch(sortOption) {
      case 'latest':
        sorted = [...items].sort((a, b) => a.timeValue - b.timeValue);
        break;
      case 'views':
        sorted = [...items].sort((a, b) => b.views - a.views);
        break;
      case 'likes':
        sorted = [...items].sort((a, b) => b.likes - a.likes);
        break;
      case 'comments':
        sorted = [...items].sort((a, b) => b.comments - a.comments);
        break;
      default:
        sorted = [...items];
    }
    
    setSortedInfoItems(sorted);
    updateScrollCounter(sorted.length);
  };

  const handleSort = (sortOption: string) => {
    setSortBy(sortOption);
    applySortToFilteredItems(filteredInfoItems, sortOption);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const filtered = initialInfoItems.filter((item: MockInfoItem) =>
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.content.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredInfoItems(filtered);
      applySortToFilteredItems(filtered, sortBy);
    } else {
      setFilteredInfoItems(initialInfoItems);
      applySortToFilteredItems(initialInfoItems, sortBy);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(e as React.FormEvent);
    }
  };

  const updateScrollCounter = (totalCount: number) => {
    const maxVisible = Math.min(visibleItemsCount, totalCount);
    setScrollCounter(`1-${maxVisible} / ${totalCount}개 정보`);
    setHasMoreItems(totalCount > visibleItemsCount);
  };

  // 스크롤 이벤트 핸들러
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    
    // 스크롤 진행률 계산
    const scrollPercent = scrollTop / (scrollHeight - clientHeight);
    
    // 현재 보이는 아이템 수 계산 (대략적)
    const estimatedVisible = Math.min(
      Math.ceil((scrollTop / scrollHeight) * sortedInfoItems.length) + 5,
      sortedInfoItems.length
    );
    
    if (estimatedVisible !== visibleItemsCount) {
      setVisibleItemsCount(estimatedVisible);
      updateScrollCounter(sortedInfoItems.length);
    }
  };

  const getTagColor = (tag: string) => {
    switch (tag) {
      case 'tag1': return 'post-tag-info';
      case 'tag2': return 'post-tag-life';
      case 'tag3': return 'post-tag-story';
      default: return 'post-tag-info';
    }
  };

  useEffect(() => {
    setVisibleItemsCount(5); // 초기값 리셋
    updateScrollCounter(sortedInfoItems.length);
  }, [sortedInfoItems]);

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      {/* 검색창 */}
      <div className="flex justify-center items-center mb-4">
        <div className="flex items-center gap-3 bg-var-card border border-var-color rounded-full px-4 py-3 w-full max-w-xs">
          <span className="text-var-muted">🔍</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="정보 검색..."
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

      {/* 정보 목록 */}
      <div className="post-list mt-4">
        {/* 스크롤 인디케이터 */}
        <div className="flex justify-between items-center mb-4 text-sm text-var-muted">
          <span>{scrollCounter}</span>
          <div className="flex-1 mx-4 h-1 bg-var-section rounded-full overflow-hidden">
            <div 
              className="h-full bg-accent-primary transition-all duration-300"
              style={{ width: `${Math.min(100, (visibleItemsCount / Math.max(1, sortedInfoItems.length)) * 100)}%` }}
            />
          </div>
        </div>
        
        {/* 정보 컨테이너 (고정 높이) */}
        <div 
          ref={scrollContainerRef}
          className="posts-scroll-container relative h-[600px] overflow-y-auto overflow-x-hidden border border-var-light rounded-xl mb-4 bg-var-card"
          onScroll={handleScroll}
        >
          <div>
            {sortedInfoItems.length > 0 ? (
              sortedInfoItems.map((item: MockInfoItem) => (
                <Link key={item.id} to={`/info/${item.id}`}>
                  <div className="post-item flex items-start cursor-pointer">
                    <div className="flex-1">
                      <div className="post-title flex items-center gap-2 mb-1">
                        <span className={`post-tag ${
                          item.tag === 'tag1' 
                            ? 'post-tag-info'
                            : item.tag === 'tag2'
                            ? 'post-tag-life'
                            : 'post-tag-story'
                        }`}>
                          {item.tagText}
                        </span>
                        <span className="text-var-primary font-medium text-lg">
                          {item.title}
                        </span>
                        {item.isNew && (
                          <span className="badge-new">NEW</span>
                        )}
                      </div>
                      
                      <div className="post-meta">
                        <span className="text-var-muted text-sm">{item.author} · {item.time}</span>
                        <div className="flex items-center gap-3">
                          <span className="stat-icon text-var-muted">
                            👁️ {item.views}
                          </span>
                          <span className="stat-icon text-var-muted">
                            👍 {item.likes}
                          </span>
                          <span className="stat-icon text-var-muted">
                            👎 {item.dislikes}
                          </span>
                          <span className="stat-icon text-var-muted">
                            💬 {item.comments}
                          </span>
                          <span className="stat-icon text-var-muted">
                            🔖 {item.bookmarks}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center p-8">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-var-primary font-semibold text-lg mb-2">
                  정보가 없습니다
                </h3>
                <p className="text-var-secondary">
                  {searchQuery ? '검색 결과가 없습니다. 다른 키워드로 검색해보세요.' : '정보가 등록되지 않았습니다.'}
                </p>
              </div>
            )}
          </div>
          
          {/* 페이드 그라디언트 오버레이 */}
          <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-var-primary to-transparent pointer-events-none" />
        </div>
        
        {/* 하단 안내 배너 */}
        {hasMoreItems && (
          <div className="text-center text-var-muted text-sm py-3 rounded-lg" style={{ backgroundColor: '#f0f8e8' }}>
            👇 아래로 스크롤하여 더 많은 정보를 확인하세요
          </div>
        )}
      </div>
    </AppLayout>
  );
}