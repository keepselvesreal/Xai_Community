/**
 * 라우팅 패턴 정의 및 타입 힌트 (DB 원시 타입 통일)
 * 
 * 모든 페이지는 다음 패턴을 따라야 합니다:
 * - 목록 페이지: /{pageName}.tsx → /{pageName}
 * - 상세 페이지: /{db-type}.$slug.tsx → /{db-type}/{slug}
 */

// 지원되는 페이지 타입 정의 (DB 원시 타입과 통일)
export type PageType = 'board' | 'moving-services' | 'expert-tips' | 'property-information' | 'notices' | 'events';

// 라우팅 패턴 타입
export type RoutePattern = {
  listRoute: string;      // 목록 페이지 경로
  detailRoute: string;    // 상세 페이지 경로 (DB 타입과 동일)
  fileName: string;       // 파일명 패턴
};

/**
 * 페이지별 라우팅 패턴 매핑 (DB 원시 타입 통일)
 */
export const ROUTING_PATTERNS: Record<PageType, RoutePattern> = {
  board: {
    listRoute: '/board',
    detailRoute: '/board',
    fileName: 'board.$slug.tsx'
  },
  'moving-services': {
    listRoute: '/services', 
    detailRoute: '/moving-services',
    fileName: 'moving-services.$slug.tsx'
  },
  'expert-tips': {
    listRoute: '/tips',
    detailRoute: '/expert-tips', 
    fileName: 'expert-tips.$slug.tsx'
  },
  'property-information': {
    listRoute: '/info',
    detailRoute: '/property-information',
    fileName: 'property-information.$slug.tsx'
  },
  notices: {
    listRoute: '/notices',
    detailRoute: '/notices',
    fileName: 'notices.$slug.tsx'
  },
  events: {
    listRoute: '/events',
    detailRoute: '/events',
    fileName: 'events.$slug.tsx'
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
 * 메타데이터 타입별 페이지 타입 매핑 (DB 원시 타입 통일)
 */
export const METADATA_TYPE_TO_PAGE_TYPE: Record<string, PageType> = {
  'board': 'board',
  'moving services': 'moving-services',
  'expert_tips': 'expert-tips',
  'property_information': 'property-information',
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
 * 라우팅 패턴 체크리스트 (개발자 가이드) - DB 원시 타입 통일
 */
export const ROUTING_CHECKLIST = [
  '✅ 목록 페이지: /{pageName}.tsx',
  '✅ 상세 페이지: /{db-type}.$slug.tsx', 
  '✅ 목록 URL: /{pageName}',
  '✅ 상세 URL: /{db-type}/{slug}',
  '✅ 메타데이터 타입 매핑 추가',
  '✅ DB 원시 타입과 라우트 파일명 완전 통일',
  '✅ ListPageConfig에서 올바른 네비게이션 사용'
] as const;