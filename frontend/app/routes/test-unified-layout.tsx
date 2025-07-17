import { type MetaFunction } from "@remix-run/node";
import { UnifiedPostList } from "~/components/common/UnifiedPostList";
import { SearchAndFilters } from "~/components/common/SearchAndFilters";
import { FilterAndSort } from "~/components/common/FilterAndSort";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { generateMockPosts } from "~/utils/mockData";
import { useState, useMemo } from "react";

export const meta: MetaFunction = () => {
  return [
    { title: "통합 레이아웃 테스트 | XAI 아파트 커뮤니티" },
    { name: "description", content: "새로운 통합 레이아웃 테스트 페이지" },
  ];
};

export default function TestUnifiedLayout() {
  const { user, logout } = useAuth();
  
  // 150개의 테스트 데이터 생성
  const mockPosts = useMemo(() => generateMockPosts(150), []);
  
  // 필터 및 검색 상태
  const [currentFilter, setCurrentFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('latest');
  
  // 필터링 및 정렬된 게시글
  const filteredPosts = useMemo(() => {
    let filtered = mockPosts;
    
    // 카테고리 필터
    if (currentFilter !== 'all') {
      const categoryMapping: { [key: string]: string[] } = {
        'info': ['입주 정보', '입주정보'],
        'life': ['생활 정보', '생활정보'], 
        'story': ['이야기']
      };
      
      const acceptedCategories = categoryMapping[currentFilter] || [];
      filtered = filtered.filter(post => 
        acceptedCategories.includes(post.metadata?.category || '')
      );
    }
    
    // 검색 필터
    if (searchQuery.trim()) {
      const searchLower = searchQuery.toLowerCase();
      filtered = filtered.filter(post =>
        post.title.toLowerCase().includes(searchLower) ||
        post.content.toLowerCase().includes(searchLower) ||
        post.author?.display_name?.toLowerCase().includes(searchLower)
      );
    }
    
    // 정렬
    filtered.sort((a, b) => {
      switch(sortBy) {
        case 'latest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'views':
          return (b.stats?.view_count || 0) - (a.stats?.view_count || 0);
        case 'likes':
          return (b.stats?.like_count || 0) - (a.stats?.like_count || 0);
        case 'comments':
          return (b.stats?.comment_count || 0) - (a.stats?.comment_count || 0);
        case 'saves':
          return (b.stats?.bookmark_count || 0) - (a.stats?.bookmark_count || 0);
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [mockPosts, currentFilter, searchQuery, sortBy]);
  
  // 핸들러들
  const handleCategoryFilter = (category: string) => {
    setCurrentFilter(category);
  };
  
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };
  
  const handleSort = (sortOption: string) => {
    setSortBy(sortOption);
  };
  
  const handleItemClick = (post: any) => {
    console.log('클릭된 게시글:', post);
    alert(`"${post.title}" 게시글을 클릭했습니다!`);
  };
  
  return (
    <AppLayout user={user} onLogout={logout}>
      <div className="container mx-auto p-4">
        {/* 테스트 설명 섹션 */}
        <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-xl">
          <h1 className="text-2xl font-bold text-blue-900 mb-4">🧪 통합 레이아웃 테스트 ({filteredPosts.length}개 게시글)</h1>
          <div className="text-blue-800 space-y-2">
            <p><strong>테스트 목적:</strong> 카테고리, 제목 길이, 태그 개수에 관계없이 일관된 게시글 레이아웃 검증</p>
            <p><strong>핵심 기능:</strong></p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>모든 게시글 항목이 88px 고정 높이 유지</li>
              <li>카테고리 태그: 100px × 24px 고정 크기</li>
              <li>제목: 한 줄 고정 (ellipsis 처리)</li>
              <li>사용자 태그: 최대 2개 표시 + 카운터</li>
              <li>통계 정보: 고정 크기 아이콘들</li>
              <li>페이지네이션: 10개씩 표시</li>
            </ul>
            <div className="mt-4 p-3 bg-white border border-blue-300 rounded-lg">
              <p className="font-semibold text-blue-900">확인할 점:</p>
              <p className="text-sm">다양한 카테고리와 제목 길이에서도 모든 항목이 동일한 높이를 유지하는지 확인하세요.</p>
            </div>
          </div>
        </div>

        {/* 검색 및 글쓰기 섹션 */}
        <SearchAndFilters
          writeButtonText="✏️ 글쓰기"
          writeButtonLink="/board/write"
          searchPlaceholder="게시글 검색..."
          searchQuery={searchQuery}
          onSearch={handleSearch}
          isSearching={false}
        />
        
        {/* 필터 및 정렬 */}
        <FilterAndSort
          categories={[
            { value: 'all', label: '전체' },
            { value: 'info', label: '입주 정보' },
            { value: 'life', label: '생활 정보' },
            { value: 'story', label: '이야기' }
          ]}
          sortOptions={[
            { value: 'latest', label: '최신순' },
            { value: 'views', label: '조회수' },
            { value: 'likes', label: '추천수' },
            { value: 'comments', label: '댓글수' },
            { value: 'saves', label: '저장수' }
          ]}
          currentFilter={currentFilter}
          sortBy={sortBy}
          onCategoryFilter={handleCategoryFilter}
          onSort={handleSort}
        />

        {/* 통합 레이아웃 테스트 */}
        <UnifiedPostList
          posts={filteredPosts}
          onItemClick={handleItemClick}
          postsPerPage={10}
        />
        
        {/* 테스트 결과 안내 */}
        <div className="mt-8 p-6 bg-green-50 border border-green-200 rounded-xl">
          <h2 className="text-xl font-bold text-green-900 mb-4">✅ 테스트 검증 포인트</h2>
          <div className="text-green-800 space-y-2">
            <p><strong>레이아웃 일관성:</strong></p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>모든 게시글 항목의 높이가 정확히 동일한가?</li>
              <li>긴 제목이 한 줄을 넘어가지 않는가?</li>
              <li>카테고리 태그 크기가 일정한가?</li>
              <li>태그가 많아도 레이아웃이 깨지지 않는가?</li>
              <li>사용자명이 길어도 고정 영역을 유지하는가?</li>
              <li>페이지네이션이 제대로 작동하는가?</li>
            </ul>
          </div>
          
          <div className="mt-4 p-3 bg-white border border-green-300 rounded-lg">
            <p className="font-semibold text-green-900">다음 단계:</p>
            <p className="text-sm">이 레이아웃이 만족스럽다면 기존 게시판과 정보 페이지에 적용할 예정입니다.</p>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}