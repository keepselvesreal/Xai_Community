/**
 * 라우팅 패턴 정의 및 타입 힌트
 * 
 * 모든 페이지는 다음 패턴을 따라야 합니다:
 * - 목록 페이지: /{pageName}.tsx → /{pageName}
 * - 상세 페이지: /{pageName}-post.$slug.tsx → /{pageName}-post/{slug}
 */

// 지원되는 페이지 타입 정의
export type PageType = 'board' | 'services' | 'tips' | 'info' | 'notices' | 'events';

// 라우팅 패턴 타입
export type RoutePattern = {
  listRoute: string;      // 목록 페이지 경로
  detailRoute: string;    // 상세 페이지 경로
  fileName: string;       // 파일명 패턴
};

/**
 * 페이지별 라우팅 패턴 매핑
 */
export const ROUTING_PATTERNS: Record<PageType, RoutePattern> = {
  board: {
    listRoute: '/board',
    detailRoute: '/board-post',
    fileName: 'board-post.$slug.tsx'
  },
  services: {
    listRoute: '/services', 
    detailRoute: '/moving-services-post',
    fileName: 'moving-services-post.$slug.tsx'
  },
  tips: {
    listRoute: '/tips',
    detailRoute: '/expert-tips', 
    fileName: 'expert-tips.$slug.tsx'
  },
  info: {
    listRoute: '/info',
    detailRoute: '/property-info',
    fileName: 'property-info.$slug.tsx'
  },
  notices: {
    listRoute: '/notices',
    detailRoute: '/notices-post',
    fileName: 'notices-post.$slug.tsx'
  },
  events: {
    listRoute: '/events',
    detailRoute: '/events-post',
    fileName: 'events-post.$slug.tsx'
  }
} as const;

/**
 * 라우팅 패턴 생성기
 */
export class RoutingPatternGenerator {
  /**
   * 새로운 페이지 타입의 라우팅 패턴 생성
   */
  static generatePattern(pageName: string): RoutePattern {
    return {
      listRoute: `/${pageName}`,
      detailRoute: `/${pageName}-post`,
      fileName: `${pageName}-post.$slug.tsx`
    };
  }

  /**
   * 페이지 타입으로 라우팅 패턴 가져오기
   */
  static getPattern(pageType: PageType): RoutePattern {
    return ROUTING_PATTERNS[pageType];
  }

  /**
   * 상세 페이지 URL 생성
   */
  static generateDetailUrl(pageType: PageType, slug: string): string {
    const pattern = this.getPattern(pageType);
    return `${pattern.detailRoute}/${slug}`;
  }

  /**
   * 목록 페이지 URL 생성
   */
  static generateListUrl(pageType: PageType): string {
    const pattern = this.getPattern(pageType);
    return pattern.listRoute;
  }
}

/**
 * 라우팅 패턴 검증
 */
export function validateRoutingPattern(pageName: string): boolean {
  const pattern = RoutingPatternGenerator.generatePattern(pageName);
  
  // 패턴 검증 로직
  const isValidListRoute = pattern.listRoute.startsWith('/') && !pattern.listRoute.includes('-post');
  const isValidDetailRoute = pattern.detailRoute.includes('-post');
  const isValidFileName = pattern.fileName.endsWith('-post.$slug.tsx');
  
  return isValidListRoute && isValidDetailRoute && isValidFileName;
}

/**
 * 메타데이터 타입별 페이지 타입 매핑
 */
export const METADATA_TYPE_TO_PAGE_TYPE: Record<string, PageType> = {
  'board': 'board',
  'moving services': 'services',
  'expert_tips': 'tips',
  'property_information': 'info',
  'notices': 'notices',
  'events': 'events'
} as const;

/**
 * ListPageConfig에서 사용할 라우팅 헬퍼
 */
export function getNavigationUrl(metadataType: string, slug: string): string {
  const pageType = METADATA_TYPE_TO_PAGE_TYPE[metadataType];
  if (!pageType) {
    console.warn(`Unknown metadata type: ${metadataType}, defaulting to board`);
    return RoutingPatternGenerator.generateDetailUrl('board', slug);
  }
  return RoutingPatternGenerator.generateDetailUrl(pageType, slug);
}

/**
 * 타입 안전한 네비게이션 함수 타입
 */
export type NavigateFunction = (url: string) => void;

/**
 * 라우팅 패턴 체크리스트 (개발자 가이드)
 */
export const ROUTING_CHECKLIST = [
  '✅ 목록 페이지: /{pageName}.tsx',
  '✅ 상세 페이지: /{pageName}-post.$slug.tsx', 
  '✅ 목록 URL: /{pageName}',
  '✅ 상세 URL: /{pageName}-post/{slug}',
  '✅ 메타데이터 타입 매핑 추가',
  '✅ ListPageConfig에서 올바른 네비게이션 사용'
] as const;