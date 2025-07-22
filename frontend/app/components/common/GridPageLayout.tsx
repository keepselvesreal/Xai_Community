import { useState, useEffect } from 'react';
import { useNavigate } from '@remix-run/react';
import AppLayout from '~/components/layout/AppLayout';
import LoadingSpinner from '~/components/common/LoadingSpinner';
import type { User } from '~/types';
import '~/styles/grid-layout.css';

interface GridPageLayoutProps {
  pageType: 'moving-services' | 'expert-tips';
  items: any[];
  onSearch: (query: string) => void;
  onFilter: (category: string) => void;
  onSort: (sortBy: string) => void;
  onLoadMore: () => void;
  onActionClick: () => void;
  loading?: boolean;
  hasMore?: boolean;
  user?: User;
  onLogout?: () => void;
  searchQuery?: string;
  activeFilter?: string;
  activeSortBy?: string;
  categories?: string[];
}

const GridPageLayout: React.FC<GridPageLayoutProps> = ({
  pageType,
  items,
  onSearch,
  onFilter,
  onSort,
  onLoadMore,
  onActionClick,
  loading = false,
  hasMore = false,
  user,
  onLogout,
  searchQuery = '',
  activeFilter = 'all',
  activeSortBy = 'latest',
  categories = []
}) => {
  const navigate = useNavigate();
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);
  
  useEffect(() => {
    setLocalSearchQuery(searchQuery);
  }, [searchQuery]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocalSearchQuery(value);
    onSearch(value);
  };

  const getActionButtonText = () => {
    return pageType === 'moving-services' ? '📝 업체 등록하기' : '✏️ 글쓰기';
  };

  // 글쓰기 권한 체크 함수
  const hasWritePermission = () => {
    if (!user) return false;
    if (user.is_admin) return true;
    
    if (pageType === 'moving-services') {
      return user.can_write_moving_services || false;
    } else if (pageType === 'expert-tips') {
      return user.can_write_expert_tips || false;
    }
    
    return false;
  };

  const getSearchPlaceholder = () => {
    return pageType === 'moving-services' ? '서비스 검색...' : '전문가 꿀정보를 검색하세요...';
  };

  const getDefaultCategories = () => {
    if (pageType === 'moving-services') {
      return ['전체', '이사', '청소', '에어컨', '가전', '인테리어', '방충망'];
    } else {
      return ['전체', '청소/정리', '인테리어', '생활', '절약', '반려동물', '원예'];
    }
  };

  const getSortOptions = () => {
    if (pageType === 'moving-services') {
      return [
        { value: 'latest', label: '최신순' },
        { value: 'views', label: '조회수' },
        { value: 'bookmarks', label: '관심순' },
        { value: 'reviews', label: '후기순' }
      ];
    } else {
      return [
        { value: 'latest', label: '최신순' },
        { value: 'views', label: '조회수' },
        { value: 'likes', label: '추천수' },
        { value: 'comments', label: '댓글수' },
        { value: 'bookmarks', label: '저장수' }
      ];
    }
  };

  // 행별 색상 클래스 계산
  const getRowColorClass = (rowIndex: number) => {
    const colors = [
      'row-1', 'row-2', 'row-3', 'row-4', 'row-5', 'row-6'
    ];
    return colors[rowIndex % colors.length];
  };

  const renderCard = (item: any, index: number) => {
    const rowIndex = Math.floor(index / 3);
    const colorClass = getRowColorClass(rowIndex);

    if (pageType === 'moving-services') {
      return (
        <div 
          key={item.id || item.slug || index}
          className={`service-card ${colorClass} bg-white border-2 rounded-lg p-5 cursor-pointer transition-all duration-300 hover:transform hover:-translate-y-2 hover:shadow-lg`}
          onClick={() => {
            const targetSlug = item.slug || item.id;
            console.log('🔗 Service card clicked:', targetSlug);
            navigate(`/moving-services/${targetSlug}`);
          }}
        >
          {/* 카테고리와 경험有 */}
          <div className="flex items-center gap-2 mb-2">
            <span className="category-tag px-4 py-2 rounded-full text-sm font-bold">
              {item.category || item.metadata?.category || '서비스'}
            </span>
            {item.verified && (
              <span className="bg-amber-500 text-white px-4 py-2 rounded-full text-sm font-bold">
                경험有
              </span>
            )}
          </div>

          {/* 업체명 */}
          <h3 className="text-lg font-bold text-gray-900 mb-3">
            {item.title || item.name} ⭐
          </h3>

          {/* 서비스 목록 */}
          <div className="services-section flex-1">
            <div className="services-list space-y-2 min-h-[140px] max-h-[140px] overflow-hidden">
              {item.services?.slice(0, 3).map((service: any, serviceIndex: number) => (
                <div key={serviceIndex} className="flex justify-between items-center py-2 px-3 rounded-md bg-blue-50">
                  <span className="text-gray-700 text-base font-medium">{service.name}</span>
                  <div className="flex items-center gap-2">
                    {service.specialPrice && (
                      <span className="text-gray-400 line-through text-sm">
                        {service.price?.toLocaleString()}원
                      </span>
                    )}
                    <span className="text-red-500 font-semibold text-base">
                      {service.specialPrice ? 
                        service.specialPrice.toLocaleString() : 
                        service.price?.toLocaleString()}원
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 연락처 */}
          <div className="flex items-center justify-center gap-4 mb-2 text-sm text-gray-600 -mt-4">
            <div className="flex items-center gap-1">
              <span className="text-pink-500">📞</span>
              <span>{item.contact?.phone || item.metadata?.phone || '문의'}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-orange-500">⏰</span>
              <span>{item.contact?.hours || item.metadata?.hours || '상담시간'}</span>
            </div>
          </div>

          {/* 통계 */}
          <div className="stats-section border-t pt-2 mt-auto">
            <div className="flex items-center justify-center text-sm text-gray-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  👁️ {item.serviceStats?.views || item.stats?.view_count || item.view_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  관심 {item.serviceStats?.bookmarks || item.stats?.bookmark_count || item.bookmark_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  문의 {item.serviceStats?.inquiries || item.stats?.comment_count || item.comment_count || 0}
                </span>
                <span className="flex items-center gap-1">
                  후기 {item.serviceStats?.reviews || Math.floor((item.stats?.comment_count || item.comment_count || 0) / 2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      );
    } else if (pageType === 'expert-tips') {
      return (
        <div 
          key={item.id || item.slug || index}
          className={`tip-card ${colorClass} bg-white rounded-2xl overflow-hidden shadow-lg transition-all duration-300 hover:-translate-y-2 hover:shadow-xl cursor-pointer h-[360px] flex flex-col`}
          onClick={() => {
            const targetSlug = item.slug || item.id;
            console.log('🔗 Expert tip card clicked:', targetSlug);
            navigate(`/expert-tips/${targetSlug}`);
          }}
        >
          {/* 카드 헤더 */}
          <div className="card-header h-[120px] p-5 flex flex-col justify-between relative text-white">
            <div className="category-badge bg-white bg-opacity-95 backdrop-blur-sm px-5 py-2 rounded-full text-base font-bold inline-block w-fit border-2 border-white border-opacity-40 shadow-lg">
              {item.category || item.metadata?.category || '생활'}
            </div>
            {item.isNew && (
              <div className="new-badge bg-red-500 text-white px-2 py-1 rounded-xl text-xs font-semibold absolute top-4 right-4">
                NEW
              </div>
            )}
          </div>

          {/* 카드 본문 */}
          <div className="card-content p-5 flex-1 flex flex-col">
            <h3 className="tip-title">
              {item.title}
            </h3>
            
            <div className="expert-info flex items-center gap-2 mb-3 text-gray-600 text-base font-medium">
              <span className="expert-icon text-lg">
                {item.expertIcon || '👨‍🔬'}
              </span>
              <span>{item.expertName || item.author || '전문가'}</span>
            </div>

            {/* 전문가 소개 */}
            <div className="expert-intro text-gray-600 text-sm mb-4 line-clamp-2">
              {item.expertIntro || item.description || '전문가의 경험을 공유합니다'}
            </div>

            <div className="tags-container flex flex-wrap gap-2 mb-4">
              {item.tags?.slice(0, 3).map((tag: string, tagIndex: number) => (
                <span 
                  key={tagIndex} 
                  className="tag bg-gray-100 text-gray-600 px-3 py-2 rounded-full text-sm font-semibold border border-gray-200 hover:bg-gray-200 transition-colors"
                >
                  {tag.startsWith('#') ? tag : `#${tag}`}
                </span>
              ))}
            </div>

            <div className="stats-row flex justify-center items-center gap-3 mt-auto pt-4 border-t border-gray-100 text-sm text-gray-500">
              <div className="stat-item flex items-center gap-1">
                <span>👁️</span>
                <span>{item.stats?.views || item.view_count || 0}</span>
              </div>
              <div className="stat-item flex items-center gap-1">
                <span>👍</span>
                <span>{item.stats?.likes || item.like_count || 0}</span>
              </div>
              <div className="stat-item flex items-center gap-1">
                <span>👎</span>
                <span>{item.stats?.dislikes || item.dislike_count || 0}</span>
              </div>
              <div className="stat-item flex items-center gap-1">
                <span>💬</span>
                <span>{item.stats?.comments || item.comment_count || 0}</span>
              </div>
              <div className="stat-item flex items-center gap-1">
                <span>🔖</span>
                <span>{item.stats?.bookmarks || item.bookmark_count || 0}</span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <AppLayout user={user} onLogout={onLogout}>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 액션 버튼 + 검색창 섹션 */}
        <div className={`flex justify-center items-center gap-4 mb-6 ${!hasWritePermission() ? 'justify-center' : ''}`}>
          {hasWritePermission() && (
            <button 
              onClick={onActionClick}
              className="w-full max-w-xs px-6 py-3 bg-white border border-gray-300 rounded-full hover:border-blue-500 hover:bg-gray-50 transition-all duration-200 font-medium text-gray-700 flex items-center justify-center gap-2"
            >
              {getActionButtonText()}
            </button>
          )}
          
          <div className={`flex items-center gap-3 bg-white border border-gray-300 rounded-full px-4 py-3 w-full max-w-xs ${!hasWritePermission() ? 'mx-auto' : ''}`}>
            <span className="text-gray-500">🔍</span>
            <input
              type="text"
              placeholder={getSearchPlaceholder()}
              value={localSearchQuery}
              onChange={handleSearchChange}
              className="flex-1 bg-transparent border-none outline-none text-gray-700 placeholder-gray-400"
            />
          </div>
        </div>

        {/* 필터링 + 정렬 섹션 */}
        <div className="flex justify-between items-center mb-4">
          {/* 필터 바 */}
          <div className="flex gap-2 flex-wrap">
            {(categories.length > 0 ? categories : getDefaultCategories()).map((category) => (
              <button
                key={category}
                onClick={() => onFilter(category)}
                className={`px-4 py-2 border rounded-full text-sm font-medium transition-all duration-200 ${
                  activeFilter === category || (category === '전체' && activeFilter === 'all')
                    ? 'border-blue-500 bg-blue-500 text-white'
                    : 'border-gray-300 bg-white text-gray-600 hover:border-blue-500 hover:text-blue-500'
                }`}
              >
                {category}
              </button>
            ))}
          </div>

          {/* 정렬 옵션 */}
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-sm">정렬:</span>
            <select
              value={activeSortBy}
              onChange={(e) => onSort(e.target.value)}
              className="bg-white border border-gray-300 rounded-lg px-3 py-1 text-sm text-gray-700"
            >
              {getSortOptions().map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 아이템 그리드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {items.map((item, index) => renderCard(item, index))}
        </div>

        {/* 로딩 상태 */}
        {loading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        )}

        {/* 더보기 버튼 */}
        {hasMore && !loading && (
          <div className="flex justify-center mt-8">
            <button
              onClick={onLoadMore}
              className="load-more-btn"
            >
              더보기
            </button>
          </div>
        )}

        {/* 빈 상태 */}
        {!loading && items.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-600 mb-2">
              {pageType === 'moving-services' ? '등록된 서비스가 없습니다' : '작성된 꿀정보가 없습니다'}
            </h3>
            <p className="text-gray-500 mb-4">
              {hasWritePermission() 
                ? (pageType === 'moving-services' ? '첫 번째 서비스를 등록해보세요!' : '첫 번째 꿀정보를 작성해보세요!')
                : (pageType === 'moving-services' ? '아직 등록된 서비스가 없습니다' : '아직 작성된 꿀정보가 없습니다')
              }
            </p>
            {hasWritePermission() && (
              <button
                onClick={onActionClick}
                className="px-6 py-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
              >
                {getActionButtonText()}
              </button>
            )}
          </div>
        )}
      </main>
    </AppLayout>
  );
};

export default GridPageLayout;