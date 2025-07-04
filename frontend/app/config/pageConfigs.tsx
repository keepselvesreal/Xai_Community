import { useNavigate } from '@remix-run/react';
import type { ListPageConfig } from '~/types/listTypes';
import type { Post, Tip, InfoItem, ContentType } from '~/types';
import { convertPostToInfoItem, infoFilterFunction, infoSortFunction } from '~/types';
import type { Service } from '~/types/service-types';
import { formatRelativeTime, formatNumber } from '~/lib/utils';
import { convertPostToService } from '~/types/service-types';

// 게시판 카드 렌더러
const PostCardRenderer = ({ post }: { post: Post }) => {
  
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
    <div className="post-item flex items-start">
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
              {post.author?.display_name || post.author?.user_handle || post.author?.name || '익명'}
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
        console.log('🚀 Direct navigation to:', `/moving-services/${targetSlug}`);
        
        // 강제로 페이지 이동
        window.location.href = `/moving-services/${targetSlug}`;
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
        {service.services && service.services.length > 0 ? service.services.map((item, idx: number) => (
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
        )) : (
          <div className="text-gray-500 text-sm">서비스 정보가 없습니다</div>
        )}
      </div>

      {/* 연락처 */}
      {service.contact && (
        <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
          {service.contact.phone && (
            <div className="flex items-center gap-1">
              <span className="text-pink-500">📞</span>
              <span>{service.contact.phone}</span>
            </div>
          )}
          {service.contact.hours && (
            <div className="flex items-center gap-1">
              <span className="text-orange-500">⏰</span>
              <span>{service.contact.hours}</span>
            </div>
          )}
        </div>
      )}

      {/* 사용자 반응 표시 */}
      <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1" title={`service.serviceStats?.views: ${service.serviceStats?.views}, service.stats?.view_count: ${service.stats?.view_count}`}>
            👁️ {(() => {
              const views = service.serviceStats?.views || service.stats?.view_count || 0;
              console.log(`🔍 ${service.name} 조회수:`, {
                serviceStats_views: service.serviceStats?.views,
                stats_view_count: service.stats?.view_count,
                final_views: views
              });
              return views;
            })()}
          </span>
          <span className="flex items-center gap-1" title={`service.bookmarks: ${service.bookmarks}, service.serviceStats?.bookmarks: ${service.serviceStats?.bookmarks}, service.stats?.bookmark_count: ${service.stats?.bookmark_count}`}>
            관심 {(() => {
              const bookmarks = service.bookmarks || service.serviceStats?.bookmarks || service.stats?.bookmark_count || 0;
              console.log(`🔍 ${service.name} 북마크:`, {
                service_bookmarks: service.bookmarks,
                serviceStats_bookmarks: service.serviceStats?.bookmarks,
                stats_bookmark_count: service.stats?.bookmark_count,
                final_bookmarks: bookmarks
              });
              return bookmarks;
            })()}
          </span>
          <span className="flex items-center gap-1" title={`service.serviceStats?.inquiries: ${service.serviceStats?.inquiries}`}>
            문의 {(() => {
              const inquiries = service.serviceStats?.inquiries || service.stats?.comment_count || 0;
              console.log(`🔍 ${service.name} 문의:`, {
                serviceStats_inquiries: service.serviceStats?.inquiries,
                stats_comment_count: service.stats?.comment_count,
                final_inquiries: inquiries
              });
              return inquiries;
            })()}
          </span>
          <span className="flex items-center gap-1" title={`service.serviceStats?.reviews: ${service.serviceStats?.reviews}, service.stats?.comment_count: ${service.stats?.comment_count}`}>
            후기 {(() => {
              const reviews = service.serviceStats?.reviews || service.stats?.comment_count || 0;
              console.log(`🔍 ${service.name} 후기:`, {
                serviceStats_reviews: service.serviceStats?.reviews,
                stats_comment_count: service.stats?.comment_count,
                final_reviews: reviews
              });
              return reviews;
            })()}
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

// 서비스 데이터 변환 함수 (실시간 통계 반영)
const transformPostsToServices = (posts: Post[]): Service[] => {
  console.log('🔍 API에서 받은 posts 데이터:', posts);
  console.log('📊 posts 개수:', posts?.length || 0);
  
  if (!posts || posts.length === 0) {
    console.warn('⚠️ API에서 받은 데이터가 비어있습니다!');
    console.warn('💡 게시글 작성 시 type을 "moving services"로 설정했는지 확인하세요.');
    return [];
  }

  const services = posts
    .map((post, index) => {
      console.log(`🔄 Post ${index + 1} 변환 시작:`, {
        title: post.title,
        view_count: post.view_count,
        comment_count: post.comment_count,
        bookmark_count: post.bookmark_count,
        stats: post.stats
      });
      
      const service = convertPostToService(post);
      if (service) {
        console.log(`✅ Service 변환 성공: ${service.name}`);
        
        // 실시간 통계 적용 (API 응답의 service_stats 또는 stats 필드 활용)
        if (post.service_stats) {
          // 🚀 백엔드에서 제공하는 service_stats 사용 (문의/후기 구분됨)
          service.serviceStats = {
            views: post.service_stats.views || post.view_count || 0,
            inquiries: post.service_stats.inquiries || 0,
            reviews: post.service_stats.reviews || 0,
            bookmarks: post.service_stats.bookmarks || post.bookmark_count || 0
          };
          
          // 북마크 수도 동기화
          service.bookmarks = post.service_stats.bookmarks || post.bookmark_count || 0;
          
          console.log(`📊 service_stats 필드 기반 통계 적용:`, service.serviceStats);
        } else if (post.stats) {
          // 기존 stats 필드 사용 (문의/후기 구분 안됨)
          service.serviceStats = {
            views: post.stats.view_count || post.view_count || 0,
            inquiries: post.stats.comment_count || post.comment_count || 0, // 문의는 댓글로 처리
            reviews: post.stats.comment_count || post.comment_count || 0,   // 후기도 댓글로 처리
            bookmarks: post.stats.bookmark_count || post.bookmark_count || 0
          };
          
          // 북마크 수도 동기화
          service.bookmarks = post.stats.bookmark_count || post.bookmark_count || 0;
          
          console.log(`📊 stats 필드 기반 통계 적용:`, service.serviceStats);
        } else {
          // stats가 없으면 기본 필드 사용
          service.serviceStats = {
            views: post.view_count || 0,
            inquiries: post.comment_count || 0,
            reviews: post.comment_count || 0,
            bookmarks: post.bookmark_count || 0
          };
          service.bookmarks = post.bookmark_count || 0;
          console.log(`📊 기본 필드 기반 통계 적용:`, service.serviceStats);
        }
        
        console.log(`🎯 최종 service.serviceStats:`, service.serviceStats);
        console.log(`🎯 최종 service.bookmarks:`, service.bookmarks);
      } else {
        console.log(`❌ Service 변환 실패 for post: ${post.title}`);
      }
      return service;
    })
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
  
  // API 설정 - 기본 posts API 사용하되 확장 통계 반영
  apiEndpoint: '/api/posts',
  apiFilters: {
    metadata_type: 'moving services',
    page: 1,
    size: 50,
    sortBy: 'created_at'
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
  
  // 빈 상태 설정
  emptyState: {
    icon: '⏳',
    title: '서비스 정보를 불러오는 중입니다',
    description: '입주 업체 서비스 데이터를 준비하고 있습니다.\n잠시만 기다려주시면 곧 표시됩니다.',
    actionLabel: ''
  },
  
  // 데이터 변환 함수
  transformData: transformPostsToServices,
  
  // 렌더링 함수
  renderCard: (service) => <ServiceCardRenderer service={service} />,
  filterFn: servicesFilterFunction,
  sortFn: servicesSortFunction
};

// 팁 카드 렌더러
const TipCardRenderer = ({ tip }: { tip: Tip }) => {
  const navigate = useNavigate();
  
  const getTipTagColor = (category: string) => {
    switch (category) {
      case '청소/정리':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case '인테리어':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case '생활':
        return 'bg-green-100 text-green-700 border-green-200';
      case '절약':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      case '반려동물':
        return 'bg-pink-100 text-pink-700 border-pink-200';
      case '원예':
        return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const formatDateSimple = (dateString: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  const isNew = new Date().getTime() - new Date(tip.created_at).getTime() < 24 * 60 * 60 * 1000;

  return (
    <div 
      className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer h-full flex flex-col"
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        navigate(`/expert-tips/${tip.slug}`);
      }}
    >
      {/* 상단: 카테고리 태그와 NEW 뱃지 */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getTipTagColor(tip.category)}`}>
          {tip.category}
        </span>
        {isNew && (
          <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
            NEW
          </span>
        )}
      </div>

      {/* 제목 */}
      <h3 className="text-xl font-bold text-gray-900 mb-3 line-clamp-2 leading-tight">
        {tip.title}
      </h3>

      {/* 전문가 소개 (자기소개 필드) */}
      <div className="text-gray-600 text-sm mb-4 line-clamp-2">
        <span className="font-medium text-green-600">💡 </span>
        {tip.expert_title || '전문가 정보 없음'}
      </div>

      {/* 작성 시간 & 통계 데이터 - 같은 줄에 표시 */}
      <div className="text-gray-500 text-sm mb-4 flex items-center justify-between">
        <div className="flex items-center gap-1">
          <span className="text-gray-400">📅</span>
          <span>{formatDateSimple(tip.created_at)}</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <span>👁️</span>
            <span>{formatNumber(tip.views_count || 0)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span>👍</span>
            <span>{formatNumber(tip.likes_count || 0)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span>👎</span>
            <span>{formatNumber(tip.dislikes_count || 0)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span>💬</span>
            <span>{formatNumber(tip.comments_count || 0)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span>🔖</span>
            <span>{formatNumber(tip.saves_count || 0)}</span>
          </span>
        </div>
      </div>

      {/* 태그 */}
      {tip.tags && tip.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-auto">
          {tip.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded-md font-medium"
            >
              {tag.startsWith('#') ? tag : `#${tag}`}
            </span>
          ))}
          {tip.tags.length > 3 && (
            <span className="text-xs text-gray-400 px-1 py-1">
              +{tip.tags.length - 3}개 더
            </span>
          )}
        </div>
      )}
    </div>
  );
};

// 팁 필터 함수
const tipsFilterFunction = (tip: Tip, category: string, query: string): boolean => {
  // 카테고리 필터
  if (category !== 'all') {
    const categoryMapping: { [key: string]: string[] } = {
      'cleaning': ['청소/정리'],
      'interior': ['인테리어'], 
      'lifestyle': ['생활'],
      'saving': ['절약'],
      'pets': ['반려동물'],
      'gardening': ['원예']
    };
    
    const tipCategory = tip.category;
    if (!tipCategory) return false;
    
    const acceptedCategories = categoryMapping[category];
    if (!acceptedCategories || !acceptedCategories.includes(tipCategory)) {
      return false;
    }
  }
  
  // 검색 필터
  if (query && query.trim()) {
    const searchLower = query.toLowerCase();
    return (
      tip.title.toLowerCase().includes(searchLower) ||
      tip.content.toLowerCase().includes(searchLower) ||
      tip.expert_name.toLowerCase().includes(searchLower) ||
      tip.tags.some(tag => tag.toLowerCase().includes(searchLower))
    );
  }
  
  return true;
};

// 팁 정렬 함수
const tipsSortFunction = (a: Tip, b: Tip, sortBy: string): number => {
  switch(sortBy) {
    case 'latest':
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    case 'views':
      return b.views_count - a.views_count;
    case 'likes':
      return b.likes_count - a.likes_count;
    case 'comments':
      return Math.floor(b.views_count * 0.1) - Math.floor(a.views_count * 0.1);
    case 'saves':
      return b.saves_count - a.saves_count;
    default:
      return 0;
  }
};

// Post를 Tip으로 변환하는 함수
const convertPostToTip = (post: Post): Tip => {
  console.log('🔍 Post 변환 중:', {
    post_id: post.id,
    title: post.title,
    content: post.content,
    metadata: post.metadata,
    author: post.author
  });
  
  // JSON content 파싱 시도
  let parsedContent = null;
  let introduction = '전문가';
  let actualContent = post.content;
  
  try {
    parsedContent = JSON.parse(post.content);
    if (parsedContent && typeof parsedContent === 'object') {
      introduction = parsedContent.introduction || '전문가';
      actualContent = parsedContent.content || post.content;
    }
  } catch (error) {
    // JSON 파싱 실패 시 기존 방식으로 fallback
    console.log('⚠️ JSON 파싱 실패, 기존 방식 사용:', error);
    introduction = post.metadata?.expert_title || '전문가';
    actualContent = post.content;
  }
  
  const tip = {
    id: post.id || `tip-${Date.now()}-${Math.random()}`, // 문자열 그대로 사용
    title: post.title,
    content: actualContent,
    slug: post.slug || post.id, // slug가 없으면 id를 사용
    expert_name: post.author?.display_name || post.metadata?.expert_name || '익명 전문가',
    expert_title: introduction,
    created_at: post.created_at,
    category: post.metadata?.category || '생활',
    tags: post.metadata?.tags || [],
    views_count: post.stats?.view_count || 0,
    likes_count: post.stats?.like_count || 0,
    dislikes_count: post.stats?.dislike_count || 0,
    comments_count: post.stats?.comment_count || 0,
    saves_count: post.stats?.bookmark_count || 0,
    is_new: new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000
  };

  console.log('✅ 변환된 Tip:', {
    id: tip.id,
    expert_title: tip.expert_title,
    category: tip.category,
    parsed_content: parsedContent
  });

  return tip;
};

// 팁 데이터 변환 함수
const transformPostsToTips = (posts: Post[]): Tip[] => {
  console.log('🔍 API에서 받은 posts 데이터:', posts);
  console.log('📊 posts 개수:', posts?.length || 0);
  
  if (!posts || posts.length === 0) {
    console.warn('⚠️ API에서 받은 데이터가 비어있습니다!');
    console.warn('💡 게시글 작성 시 type을 "expert_tips"로 설정했는지 확인하세요.');
    return [];
  }

  const tips = posts
    .map(convertPostToTip)
    .filter((tip): tip is Tip => tip !== null);

  console.log('✅ 변환된 팁 개수:', tips.length);
  
  if (tips.length === 0) {
    console.warn('⚠️ posts가 있지만 변환 가능한 팁이 없습니다!');
    console.warn('💡 metadata.type이 "expert_tips"인지 확인하세요.');
    return [];
  }

  return tips;
};

// 정보 카드 렌더러
const InfoCardRenderer = ({ info }: { info: InfoItem }) => {
  const navigate = useNavigate();
  
  const getContentTypeLabel = (contentType: ContentType) => {
    switch (contentType) {
      case 'interactive_chart':
        return '인터렉티브 차트';
      case 'ai_article':
        return 'AI 생성 글';
      case 'data_visualization':
        return '데이터 시각화';
      case 'mixed_content':
        return '혼합 콘텐츠';
      default:
        return 'AI 생성 글';
    }
  };

  const getContentTypeColor = (contentType: ContentType) => {
    switch (contentType) {
      case 'interactive_chart':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'ai_article':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'data_visualization':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'mixed_content':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      default:
        return 'bg-green-100 text-green-700 border-green-200';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'market_analysis':
        return '시세분석';
      case 'legal_info':
        return '법률정보';
      case 'move_in_guide':
        return '입주가이드';
      case 'investment_trend':
        return '투자동향';
      default:
        return category;
    }
  };

  const isNew = new Date().getTime() - new Date(info.created_at).getTime() < 24 * 60 * 60 * 1000;

  return (
    <div 
      className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow h-full cursor-pointer"
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        navigate(`/property-information/${info.slug}`);
      }}
    >
      {/* 상단: 콘텐츠 타입 배지 */}
      <div className="flex items-center gap-2 mb-3">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getContentTypeColor(info.content_type)}`}>
          {getContentTypeLabel(info.content_type)}
        </span>
        {info.metadata?.category && (
          <span className="bg-blue-100 text-blue-600 px-3 py-1 rounded-full text-sm font-medium">
            {getCategoryLabel(info.metadata.category)}
          </span>
        )}
        {isNew && (
          <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
            NEW
          </span>
        )}
      </div>

      {/* 제목 */}
      <h3 className="text-var-primary font-bold text-lg mb-3 line-clamp-2">
        {info.title}
      </h3>

      {/* 데이터 소스 정보 (있는 경우) */}
      {info.metadata?.data_source && (
        <div className="mb-3">
          <span className="text-xs text-var-muted bg-gray-100 px-2 py-1 rounded">
            📊 {info.metadata.data_source}
          </span>
        </div>
      )}

      {/* 요약 (있는 경우) */}
      {info.metadata?.summary && (
        <p className="text-var-secondary text-sm mb-4 line-clamp-2">
          {info.metadata.summary}
        </p>
      )}

      {/* 태그 */}
      {info.metadata?.tags && info.metadata.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {info.metadata.tags.slice(0, 3).map((tag: string, index: number) => (
            <span key={index} className="px-3 py-1 bg-gray-50 text-gray-700 text-xs rounded-full font-medium">
              #{tag}
            </span>
          ))}
          {info.metadata.tags.length > 3 && (
            <span className="text-xs text-var-muted px-1">
              +{info.metadata.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* 하단: 통계 및 날짜 */}
      <div className="flex items-center justify-between text-var-muted text-sm mt-auto">
        <span className="text-var-secondary font-medium">
          {formatRelativeTime(info.created_at)}
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            👁️ {formatNumber(info.stats?.view_count || 0)}
          </span>
          <span className="flex items-center gap-1">
            👍 {formatNumber(info.stats?.like_count || 0)}
          </span>
          <span className="flex items-center gap-1">
            👎 {formatNumber(info.stats?.dislike_count || 0)}
          </span>
          <span className="flex items-center gap-1">
            💬 {formatNumber(info.stats?.comment_count || 0)}
          </span>
          <span className="flex items-center gap-1">
            🔖 {formatNumber(info.stats?.bookmark_count || 0)}
          </span>
        </div>
      </div>
    </div>
  );
};

// Post를 InfoItem으로 변환하는 함수
const transformPostsToInfoItems = (posts: Post[]): InfoItem[] => {
  if (!posts || posts.length === 0) {
    return [];
  }

  // 백엔드에서 이미 필터링된 데이터이므로 모든 posts를 변환
  const infoItems = posts
    .map(convertPostToInfoItem)
    .filter((item): item is InfoItem => item !== null);

  return infoItems;
};

export const infoConfig: ListPageConfig<InfoItem> = {
  // 페이지 기본 설정
  title: '정보',
  writeButtonText: '', // 관리자만 직접 데이터 입력하므로 빈 값
  writeButtonLink: '', // 관리자만 직접 데이터 입력하므로 빈 값
  searchPlaceholder: '정보 검색...',
  
  // API 설정
  apiEndpoint: '/api/posts',
  apiFilters: {
    metadata_type: 'property_information',
    page: 1,
    size: 50
  },
  
  // UI 설정
  categories: [
    { value: 'all', label: '전체' },
    { value: 'market_analysis', label: '시세분석' },
    { value: 'legal_info', label: '법률정보' },
    { value: 'move_in_guide', label: '입주가이드' },
    { value: 'investment_trend', label: '투자동향' }
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    { value: 'likes', label: '추천수' },
    { value: 'comments', label: '댓글수' },
    { value: 'saves', label: '저장수' }
  ],
  
  cardLayout: 'grid',
  
  // 빈 상태 설정
  emptyState: {
    icon: '⏳',
    title: '정보를 불러오는 중입니다',
    description: '서버에서 데이터를 준비하고 있습니다. 잠시만 기다려주세요.\n데이터 로딩이 완료되면 자동으로 표시됩니다.',
    actionLabel: ''  // 관리자만 입력 가능하므로 빈 값
  },
  
  // 데이터 변환 함수
  transformData: transformPostsToInfoItems,
  
  // 렌더링 함수
  renderCard: (info) => <InfoCardRenderer info={info} />,
  filterFn: infoFilterFunction,
  sortFn: infoSortFunction
};

export const tipsConfig: ListPageConfig<Tip> = {
  // 페이지 기본 설정
  title: '전문가 꿀정보',
  writeButtonText: '✏️ 글쓰기',
  writeButtonLink: '/tips/write',
  searchPlaceholder: '전문가 꿀정보를 검색하세요...',
  
  // API 설정
  apiEndpoint: '/api/posts',
  apiFilters: {
    metadata_type: 'expert_tips',
    page: 1,
    size: 50
  },
  
  // UI 설정
  categories: [
    { value: 'all', label: '전체' },
    { value: 'cleaning', label: '청소/정리' },
    { value: 'interior', label: '인테리어' },
    { value: 'lifestyle', label: '생활' },
    { value: 'saving', label: '절약' },
    { value: 'pets', label: '반려동물' },
    { value: 'gardening', label: '원예' }
  ],
  
  sortOptions: [
    { value: 'latest', label: '최신순' },
    { value: 'views', label: '조회수' },
    { value: 'likes', label: '추천수' },
    { value: 'comments', label: '댓글수' },
    { value: 'saves', label: '저장수' }
  ],
  
  cardLayout: 'grid',
  
  // 빈 상태 설정
  emptyState: {
    icon: '⏳',
    title: '전문가 꿀정보를 불러오는 중입니다',
    description: '전문가들의 검증된 생활 팁을 준비하고 있습니다.\n잠시만 기다려주시면 곧 표시됩니다.',
    actionLabel: ''
  },
  
  // 데이터 변환 함수
  transformData: transformPostsToTips,
  
  // 렌더링 함수
  renderCard: (tip) => <TipCardRenderer tip={tip} />,
  filterFn: tipsFilterFunction,
  sortFn: tipsSortFunction
};