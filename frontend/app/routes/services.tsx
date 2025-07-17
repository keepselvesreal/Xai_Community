import { type MetaFunction } from "@remix-run/node";
import { useNavigate } from "@remix-run/react";
import GridPageLayout from "~/components/common/GridPageLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useListData } from "~/hooks/useListData";
import { servicesConfig } from "~/config/pageConfigs";
import { convertPostToService } from "~/types/service-types";
import type { Service } from "~/types/service-types";

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 | XAI 아파트 커뮤니티" },
    { name: "description", content: "아파트 입주 업체 서비스" },
  ];
};

export default function Services() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // useListData 훅으로 API 통합 및 상태 관리
  const {
    items: rawItems,
    loading,
    currentFilter,
    sortBy,
    searchQuery,
    handleCategoryFilter,
    handleSort,
    handleSearch
  } = useListData(servicesConfig);

  // useListData에서 이미 변환된 Service 데이터 사용
  const services: Service[] = rawItems;

  // 검색 핸들러
  const handleSearchChange = (query: string) => {
    handleSearch(query);
  };

  // 필터 핸들러
  const handleFilter = (category: string) => {
    // UI 카테고리를 API 카테고리로 매핑
    const categoryMapping: { [key: string]: string } = {
      '전체': 'all',
      '이사': 'moving',
      '청소': 'cleaning',
      '에어컨': 'aircon',
      '가전': 'appliance',
      '인테리어': 'interior',
      '방충망': 'screen'
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

  // 액션 버튼 핸들러 (업체 등록)
  const handleActionClick = () => {
    navigate('/services/write');
  };

  // 서비스 카테고리 정의
  const categories = ['전체', '이사', '청소', '에어컨', '가전', '인테리어', '방충망'];
  
  return (
    <GridPageLayout
      pageType="moving-services"
      items={services}
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

