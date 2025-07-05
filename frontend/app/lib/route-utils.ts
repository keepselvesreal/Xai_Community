/**
 * Phase 6: URL과 페이지 타입 간 변환 유틸리티
 * 매핑 테이블 제거로 완전 단순화된 변환 로직
 */

import type { DbPageType } from '~/types';

/**
 * 페이지 타입을 URL 세그먼트로 변환
 * DB 타입의 underscore를 hyphen으로 변환
 * 
 * @param pageType - DB 페이지 타입 (예: 'moving_services')
 * @returns URL 세그먼트 (예: 'moving-services')
 */
export function pageTypeToUrlSegment(pageType: DbPageType): string {
  return pageType.replace(/_/g, '-');
}

/**
 * URL 세그먼트를 페이지 타입으로 변환
 * URL의 hyphen을 underscore로 변환
 * 
 * @param urlSegment - URL 세그먼트 (예: 'moving-services')
 * @returns DB 페이지 타입 또는 null (예: 'moving_services')
 */
export function urlSegmentToPageType(urlSegment: string): DbPageType | null {
  const pageType = urlSegment.replace(/-/g, '_') as DbPageType;
  
  // 유효한 DB 타입 체크
  const validTypes: DbPageType[] = ['board', 'property_information', 'expert_tips', 'moving_services'];
  return validTypes.includes(pageType) ? pageType : null;
}

/**
 * 페이지 타입과 슬러그로 라우트 경로 생성
 * 
 * @param pageType - DB 페이지 타입
 * @param slug - 게시글 슬러그
 * @returns 라우트 경로 (예: '/moving-services/test-slug')
 */
export function generateRoutePath(pageType: DbPageType, slug: string): string {
  const urlSegment = pageTypeToUrlSegment(pageType);
  return `/${urlSegment}/${slug}`;
}

/**
 * 라우트 경로에서 페이지 타입 추출
 * 
 * @param routePath - 라우트 경로 (예: '/moving-services/test-slug')
 * @returns DB 페이지 타입 또는 null
 */
export function extractPageTypeFromRoute(routePath: string): DbPageType | null {
  if (!routePath) return null;
  
  const segments = routePath.split('/').filter(Boolean);
  if (segments.length < 2) return null;
  
  return urlSegmentToPageType(segments[0]);
}

/**
 * 페이지 타입별 표시 정보 가져오기
 * 
 * @param pageType - DB 페이지 타입
 * @returns 페이지 표시 정보 (아이콘, 제목, 이름)
 */
export function getPageTypeDisplayInfo(pageType: DbPageType) {
  const displayInfo = {
    board: { icon: '📝', title: '📝 게시판', name: '게시판' },
    property_information: { icon: '📋', title: '📋 부동산 정보', name: '부동산 정보' },
    expert_tips: { icon: '💡', title: '💡 전문가 꿀정보', name: '전문가 꿀정보' },
    moving_services: { icon: '🏢', title: '🏢 입주 업체 서비스', name: '입주 업체 서비스' }
  };
  
  return displayInfo[pageType] || { icon: '📄', title: '알 수 없음', name: '알 수 없음' };
}

/**
 * 모든 유효한 페이지 타입 목록
 */
export const ALL_PAGE_TYPES: DbPageType[] = ['board', 'property_information', 'expert_tips', 'moving_services'];

/**
 * 페이지 타입 유효성 검사
 * 
 * @param value - 검사할 값
 * @returns 유효한 페이지 타입인지 여부
 */
export function isValidPageType(value: string): value is DbPageType {
  return ALL_PAGE_TYPES.includes(value as DbPageType);
}