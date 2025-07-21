import { type MetaFunction } from "@remix-run/node";
import { useNavigate } from "@remix-run/react";
import GridPageLayout from "~/components/common/GridPageLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { useListData } from "~/hooks/useListData";
import { tipsConfig } from "~/config/pageConfigs";
import type { Post, Tip } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "전문가 꿀정보 | XAI 아파트 커뮤니티" },
    { name: "description", content: "전문가들이 제공하는 검증된 생활 꿀팁" },
  ];
};

// Post를 GridPageLayout에서 사용할 수 있는 형태로 변환
const convertTipForGrid = (tip: Tip) => ({
  id: tip.id,
  slug: tip.slug,
  title: tip.title,
  description: tip.content?.substring(0, 100) + '...' || '',
  category: tip.category,
  isNew: tip.is_new,
  expertIcon: getExpertIcon(tip.category),
  expertName: tip.expert_name,
  expertIntro: tip.expert_title,
  tags: tip.tags || [],
  stats: {
    views: tip.views_count || 0,
    likes: tip.likes_count || 0,
    dislikes: tip.dislikes_count || 0,
    comments: tip.comments_count || 0,
    bookmarks: tip.saves_count || 0
  }
});

// 카테고리별 전문가 아이콘 반환
function getExpertIcon(category?: string) {
  const iconMap: Record<string, string> = {
    '청소/정리': '👨‍🔬',
    '인테리어': '💡',
    '생활': '⚡',
    '절약': '🏠',
    '반려동물': '🐕',
    '원예': '🌱'
  };
  return iconMap[category || '생활'] || '👨‍🔬';
}

export default function Tips() {
  const { user, logout } = useAuth();
  const { showError } = useNotification();
  const navigate = useNavigate();
  
  // useListData 훅으로 API 통합 및 상태 관리
  const {
    items: tips,
    loading,
    currentFilter,
    sortBy,
    searchQuery,
    handleCategoryFilter,
    handleSort,
    handleSearch
  } = useListData(tipsConfig);

  // Tip 데이터를 GridPageLayout에서 사용할 수 있는 형태로 변환
  const gridTips = tips.map(convertTipForGrid);

  // 검색 핸들러
  const handleSearchChange = (query: string) => {
    handleSearch(query);
  };

  // 필터 핸들러
  const handleFilter = (category: string) => {
    // UI 카테고리를 API 카테고리로 매핑
    const categoryMapping: { [key: string]: string } = {
      '전체': 'all',
      '청소/정리': 'cleaning',
      '인테리어': 'interior',
      '생활': 'lifestyle',
      '절약': 'saving',
      '반려동물': 'pets',
      '원예': 'gardening'
    };
    
    const mappedCategory = categoryMapping[category] || category;
    handleCategoryFilter(mappedCategory);
  };

  // 정렬 핸들러
  const handleSortChange = (sortBy: string) => {
    handleSort(sortBy);
  };

  // 더보기 핸들러 (현재는 페이징 없음)
  const handleLoadMore = () => {
    // 추후 페이징 구현 시 사용
  };

  // 글쓰기 권한 체크 함수
  const hasWritePermission = () => {
    if (!user) return false;
    if (user.is_admin) return true;
    return user.can_write_expert_tips || false;
  };

  // 액션 버튼 핸들러 (글쓰기)
  const handleActionClick = () => {
    if (!user) {
      showError("로그인이 필요합니다.");
      navigate("/auth/login");
      return;
    }

    if (!hasWritePermission()) {
      showError("전문가 꿀정보를 작성할 권한이 없습니다. 관리자에게 문의해주세요.");
      return;
    }

    navigate('/tips/write');
  };

  // 꿀정보 카테고리 정의
  const categories = ['전체', '청소/정리', '인테리어', '생활', '절약', '반려동물', '원예'];
  
  return (
    <GridPageLayout
      pageType="expert-tips"
      items={gridTips}
      onSearch={handleSearchChange}
      onFilter={handleFilter}
      onSort={handleSortChange}
      onLoadMore={handleLoadMore}
      onActionClick={handleActionClick}
      loading={loading}
      hasMore={false} // 현재는 페이징 없음
      user={user || undefined}
      onLogout={logout}
      searchQuery={searchQuery}
      activeFilter={currentFilter}
      activeSortBy={sortBy}
      categories={categories}
    />
  );
}