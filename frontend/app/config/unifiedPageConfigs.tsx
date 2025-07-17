import type { ListPageConfig } from '~/types/listTypes';
import type { Post } from '~/types';
import { UnifiedPostList } from '~/components/common/UnifiedPostList';

// 새로운 통합 렌더러 - 모든 페이지에서 동일한 레이아웃 사용
const UnifiedPostRenderer = ({ post, onClick }: { post: Post; onClick?: (post: Post) => void }) => {
  return <UnifiedPostListItem post={post} onClick={onClick} />;
};

// 게시판 필터 함수 (기존과 동일)
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

// 게시판 정렬 함수 (기존과 동일)
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

// 통합 게시판 설정 (NEW)
export const unifiedBoardConfig: ListPageConfig<Post> = {
  // 페이지 기본 설정
  title: '게시판 (통합 레이아웃)',
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
  
  // 빈 상태 설정
  emptyState: {
    icon: '📝',
    title: '게시글이 없습니다',
    description: '아직 작성된 게시글이 없어요.\n첫 번째 게시글을 작성해보세요!',
    actionLabel: '글쓰기'
  },
  
  // 새로운 통합 렌더러 사용
  renderCard: (post) => <UnifiedPostRenderer post={post} />,
  filterFn: boardFilterFunction,
  sortFn: boardSortFunction
};

// 정보 페이지 필터 함수
const infoFilterFunction = (post: Post, category: string, query: string): boolean => {
  // 카테고리 필터
  if (category !== 'all') {
    const categoryMapping: { [key: string]: string[] } = {
      'market_analysis': ['시세분석'],
      'legal_info': ['법률정보'],
      'move_in_guide': ['입주가이드'],
      'investment_trend': ['투자동향']
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

// 정보 페이지 정렬 함수 (게시판과 동일)
const infoSortFunction = boardSortFunction;

// 통합 정보 페이지 설정 (NEW)
export const unifiedInfoConfig: ListPageConfig<Post> = {
  // 페이지 기본 설정
  title: '정보 (통합 레이아웃)',
  writeButtonText: '📊 정보 제공',
  writeButtonLink: '/info/suggest',
  searchPlaceholder: '부동산 정보 검색...',
  
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
  
  cardLayout: 'list',
  
  // 빈 상태 설정
  emptyState: {
    icon: '📋',
    title: '등록된 정보가 없습니다',
    description: '아직 등록된 부동산 정보가 없어요.\n곧 유용한 정보들을 제공해드릴게요!',
    actionLabel: ''
  },
  
  // 동일한 통합 렌더러 사용
  renderCard: (post) => <UnifiedPostRenderer post={post} />,
  filterFn: infoFilterFunction,
  sortFn: infoSortFunction
};