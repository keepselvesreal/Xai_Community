import { useNavigate } from '@remix-run/react';
import type { ListPageConfig } from '~/types/listTypes';
import type { Post, MockTip } from '~/types';
import type { Service } from '~/types/service-types';
import { formatRelativeTime, formatNumber } from '~/lib/utils';
import { convertPostToService } from '~/types/service-types';

// 게시판 카드 렌더러
const PostCardRenderer = ({ post }: { post: Post }) => {
  const navigate = useNavigate();
  
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

  const isNew = new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000;

  return (
    <div 
      className="post-item flex items-start cursor-pointer"
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        navigate(`/board-post/${post.slug}`);
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
          {isNew && (
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
};

// 게시판 필터 함수
const boardFilterFunction = (post: Post, category: string, query: string): boolean => {
  // 카테고리 필터
  if (category !== 'all') {
    const categoryMapping: { [key: string]: string[] } = {
      'info': ['입주 정보', '입주정보'],
      'life': ['생활 정보', '생활정보'], 
      'story': ['이야기']
    };
    
    const postCategory = post.metadata?.category;
    if (!postCategory) return false;
    
    const acceptedCategories = categoryMapping[category];
    if (!acceptedCategories || !acceptedCategories.includes(postCategory)) {
      return false;
    }
  }
  
  // 검색 필터
  if (query && query.trim()) {
    const searchLower = query.toLowerCase();
    return (
      post.title.toLowerCase().includes(searchLower) ||
      post.content.toLowerCase().includes(searchLower)
    );
  }
  
  return true;
};

// 게시판 정렬 함수
const boardSortFunction = (a: Post, b: Post, sortBy: string): number => {
  switch(sortBy) {
    case 'latest':
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    case 'views':
      return (b.stats?.view_count || b.stats?.views || 0) - (a.stats?.view_count || a.stats?.views || 0);
    case 'likes':
      return (b.stats?.like_count || b.stats?.likes || 0) - (a.stats?.like_count || a.stats?.likes || 0);
    case 'comments':
      return (b.stats?.comment_count || b.stats?.comments || 0) - (a.stats?.comment_count || a.stats?.comments || 0);
    case 'saves':
      return (b.stats?.bookmark_count || b.stats?.bookmarks || 0) - (a.stats?.bookmark_count || a.stats?.bookmarks || 0);
    default:
      return 0;
  }
};

// 게시판 설정
export const boardConfig: ListPageConfig<Post> = {
  // 페이지 기본 설정
  title: '게시판',
  writeButtonText: '✏️ 글쓰기',
  writeButtonLink: '/board/write',
  searchPlaceholder: '게시글 검색...',
  
  // API 설정
  apiEndpoint: '/api/posts',
  apiFilters: {
    service: 'residential_community',
    metadata_type: 'board',
    sortBy: 'created_at'
  },
  
  // UI 설정
  categories: [
    { value: 'all', label: '전체' },
    { value: 'info', label: '입주 정보' },
    { value: 'life', label: '생활 정보' },
    { value: 'story', label: '이야기' }
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    { value: 'likes', label: '추천수' },
    { value: 'comments', label: '댓글수' },
    { value: 'saves', label: '저장수' }
  ],
  
  cardLayout: 'list',
  
  // 렌더링 함수
  renderCard: (post) => <PostCardRenderer post={post} />,
  filterFn: boardFilterFunction,
  sortFn: boardSortFunction
};

// 서비스 카드 렌더러
const ServiceCardRenderer = ({ service }: { service: Service }) => {
  const navigate = useNavigate();
  
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  console.log('🎨 ServiceCardRenderer rendering for service:', service.name);
  
  return (
    <div 
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={(e) => {
        console.log('🎯 DIRECT ServiceCard CLICKED!!!', service.name);
        e.preventDefault();
        e.stopPropagation();
        
        const targetSlug = service.slug || service.id;
        console.log('🚀 Direct navigation to:', `/moving-services-post/${targetSlug}`);
        
        // 강제로 페이지 이동
        window.location.href = `/moving-services-post/${targetSlug}`;
      }}
    >
      {/* 카테고리와 인증 */}
      <div className="flex items-center gap-2 mb-3">
        <span className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm font-medium">
          {service.category}
        </span>
        {service.verified && (
          <span className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium">
            인증
          </span>
        )}
      </div>

      {/* 업체명 */}
      <h3 className="text-lg font-bold text-gray-900 mb-4">{service.name}</h3>

      {/* 서비스 목록 */}
      <div className="space-y-2 mb-4">
        {service.services.map((item, idx: number) => (
          <div key={idx} className="flex justify-between items-center">
            <span className="text-gray-700 text-sm">{item.name}</span>
            <div className="flex items-center gap-2">
              {item.specialPrice && (
                <span className="text-gray-400 line-through text-sm">{item.price.toLocaleString()}원</span>
              )}
              <span className="text-red-500 font-medium text-sm">
                {item.specialPrice ? item.specialPrice.toLocaleString() : item.price.toLocaleString()}원
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 연락처 */}
      <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <span className="text-pink-500">📞</span>
          <span>{service.contact.phone}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-orange-500">⏰</span>
          <span>{service.contact.hours}</span>
        </div>
      </div>

      {/* 사용자 반응 표시 */}
      <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            👁️ {service.serviceStats?.views || service.stats?.view_count || 0}
          </span>
          <span className="flex items-center gap-1">
            👍 {service.likes || service.stats?.like_count || 0}
          </span>
          <span className="flex items-center gap-1">
            👎 {service.dislikes || service.stats?.dislike_count || 0}
          </span>
          <span className="flex items-center gap-1">
            🔖 {service.bookmarks || service.stats?.bookmark_count || 0}
          </span>
          <span className="flex items-center gap-1">
            문의 {service.serviceStats?.inquiries || 0}
          </span>
          <span className="flex items-center gap-1">
            후기 {service.serviceStats?.reviews || service.stats?.comment_count || 0}
          </span>
        </div>
      </div>
    </div>
  );
};

// 서비스 필터 함수
const servicesFilterFunction = (service: Service, category: string, query: string): boolean => {
  // 카테고리 필터
  if (category !== 'all') {
    const categoryMapping: { [key: string]: string } = {
      'moving': '이사',
      'cleaning': '청소',
      'aircon': '에어컨'
    };
    
    const targetCategory = categoryMapping[category];
    if (service.category !== targetCategory) {
      return false;
    }
  }
  
  // 검색 필터
  if (query && query.trim()) {
    const searchLower = query.toLowerCase();
    return (
      service.name.toLowerCase().includes(searchLower) ||
      service.category.toLowerCase().includes(searchLower) ||
      service.description.toLowerCase().includes(searchLower)
    );
  }
  
  return true;
};

// 서비스 정렬 함수
const servicesSortFunction = (a: Service, b: Service, sortBy: string): number => {
  switch(sortBy) {
    case 'latest':
      // created_at 기준으로 최신순
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    case 'views':
      return (b.serviceStats?.views || b.stats?.view_count || 0) - (a.serviceStats?.views || a.stats?.view_count || 0);
    case 'saves':
      return (b.bookmarks || b.stats?.bookmark_count || 0) - (a.bookmarks || a.stats?.bookmark_count || 0);
    case 'reviews':
      return (b.serviceStats?.reviews || b.stats?.comment_count || 0) - (a.serviceStats?.reviews || a.stats?.comment_count || 0);
    case 'inquiries':
      return (b.serviceStats?.inquiries || 0) - (a.serviceStats?.inquiries || 0);
    default:
      return 0;
  }
};

// 서비스 데이터 변환 함수
const transformPostsToServices = (posts: Post[]): Service[] => {
  console.log('🔍 API에서 받은 posts 데이터:', posts);
  console.log('📊 posts 개수:', posts?.length || 0);
  
  if (!posts || posts.length === 0) {
    console.warn('⚠️ API에서 받은 데이터가 비어있습니다!');
    console.warn('💡 게시글 작성 시 type을 "moving services"로 설정했는지 확인하세요.');
    return [];
  }

  const services = posts
    .map(convertPostToService)
    .filter((service): service is Service => service !== null);

  console.log('✅ 변환된 서비스 개수:', services.length);
  
  // API에서 서비스 데이터가 없으면 빈 배열 반환 (fallback 제거)
  if (services.length === 0) {
    console.warn('⚠️ posts가 있지만 변환 가능한 서비스가 없습니다!');
    console.warn('💡 metadata.type이 "moving services"인지 확인하세요.');
    return [];
  }

  return services;
};

export const servicesConfig: ListPageConfig<Service> = {
  // 페이지 기본 설정
  title: '입주업체서비스',
  writeButtonText: '📝 업체 등록',
  writeButtonLink: '/services/write',
  searchPlaceholder: '서비스 검색...',
  
  // API 설정
  apiEndpoint: '/api/posts',
  apiFilters: {
    service: 'residential_community',
    metadata_type: 'moving services',
    page: 1,
    size: 50
  },
  
  // UI 설정
  categories: [
    { value: 'all', label: '전체' },
    { value: 'moving', label: '이사' },
    { value: 'cleaning', label: '청소' },
    { value: 'aircon', label: '에어컨' }
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    { value: 'saves', label: '저장수' },
    { value: 'reviews', label: '후기수' },
    { value: 'inquiries', label: '문의수' }
  ],
  
  cardLayout: 'grid',
  
  // 데이터 변환 함수
  transformData: transformPostsToServices,
  
  // 렌더링 함수
  renderCard: (service) => <ServiceCardRenderer service={service} />,
  filterFn: servicesFilterFunction,
  sortFn: servicesSortFunction
};

// 추후 구현될 팁 설정 예시
// export const tipsConfig: ListPageConfig<MockTip> = { ... };