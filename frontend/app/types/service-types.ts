/**
 * ServicePost 관련 타입 정의 (TDD REFACTOR 단계)
 * 
 * 구조화된 서비스-가격 데이터를 위한 타입 정의 및 유틸리티 함수
 */

import type { ServiceItem, ServiceStats } from './index';
import type { BaseListItem, ItemStats } from './listTypes';

// 업체 정보 타입
export interface CompanyInfo {
  /** 업체명 */
  name: string;
  /** 연락처 (전화번호) */
  contact: string;
  /** 문의 가능 시간 */
  availableHours: string;
  /** 업체 설명 */
  description: string;
}

// 서비스 아이템 타입 (가격 정보 포함)
export interface ServiceItemWithPrice {
  /** 서비스명 */
  name: string;
  /** 기본 가격 (문자열로 저장하여 정밀도 보장) */
  price: string;
  /** 특가 (문자열로 저장하여 정밀도 보장, 선택사항) */
  specialPrice?: string;
  /** 서비스 설명 (선택사항) */
  description?: string;
}

// 서비스 게시글 구조화된 데이터 타입
export interface ServicePost {
  /** 업체 정보 */
  company: CompanyInfo;
  /** 서비스 목록 */
  services: ServiceItemWithPrice[];
}

// 서비스 카테고리 타입
export type ServiceCategory = "이사" | "청소" | "에어컨";

// UI에 필요한 모든 필드를 포함한 완전한 서비스 타입
export interface Service extends ServicePost, BaseListItem {
  /** 업체명 (company.name의 편의 필드) */
  name: string;
  /** URL 슬러그 (네비게이션용) */
  slug?: string;
  /** 서비스 카테고리 */
  category: ServiceCategory;
  /** 업체 평점 (0-5) */
  rating: number;
  /** 업체 설명 (company.description의 편의 필드) */
  description: string;
  /** 통계 정보 (BaseListItem과 호환) */
  stats?: ItemStats;
  /** 서비스별 통계 정보 */
  serviceStats?: ServiceStats;
  /** 좋아요 수 */
  likes?: number;
  /** 싫어요 수 */
  dislikes?: number;
  /** 북마크 수 */
  bookmarks?: number;
  /** 인증 여부 */
  verified: boolean;
  /** 연락처 정보 (확장된 형태) */
  contact: ServiceContactInfo;
  /** 고객 후기 */
  reviews: ServiceReview[];
  /** 원본 Post ID (상세 페이지 네비게이션용) */
  postId?: string;
  /** 수정일 */
  updated_at?: string;
  
  // 🔑 작성자 정보 필드들 (Post에서 가져옴)
  /** 작성자 정보 (객체) */
  author?: any;
  /** 작성자 ID */
  author_id?: string;
  /** 사용자 ID */
  user_id?: string;
  /** 생성자 ID */
  created_by?: string;
}

// ServiceStats는 index.ts에서 import됨 (중복 제거)

// 확장된 연락처 정보
export interface ServiceContactInfo {
  /** 전화번호 */
  phone: string;
  /** 운영시간 */
  hours: string;
  /** 주소 */
  address: string;
  /** 이메일 */
  email: string;
  /** 웹사이트 (선택사항) */
  website?: string;
}

// 고객 후기 타입
export interface ServiceReview {
  /** 작성자 */
  author: string;
  /** 평점 (1-5) */
  rating: number;
  /** 후기 내용 */
  text: string;
  /** 작성일 */
  date?: string;
}

// 입력 검증 함수
function validateServicePost(data: any): data is ServicePost {
  console.log('🔍 Validating ServicePost data:', data);
  
  if (!data || typeof data !== 'object') {
    console.error('❌ Data is not an object:', data);
    return false;
  }
  
  // company 검증
  if (!data.company || typeof data.company !== 'object') {
    console.error('❌ Company is missing or not an object:', data.company);
    return false;
  }
  if (typeof data.company.name !== 'string' || !data.company.name.trim()) {
    console.error('❌ Company name is invalid:', data.company.name);
    return false;
  }
  if (typeof data.company.contact !== 'string' || !data.company.contact.trim()) {
    console.error('❌ Company contact is invalid:', data.company.contact);
    return false;
  }
  if (typeof data.company.availableHours !== 'string' || !data.company.availableHours.trim()) {
    console.error('❌ Company availableHours is invalid:', data.company.availableHours);
    return false;
  }
  if (typeof data.company.description !== 'string') {
    console.error('❌ Company description is invalid:', data.company.description);
    return false;
  }
  
  // services 배열 검증
  if (!Array.isArray(data.services) || data.services.length === 0) {
    console.error('❌ Services is not a valid array:', data.services);
    return false;
  }
  
  for (const service of data.services) {
    if (!service || typeof service !== 'object') {
      console.error('❌ Service item is not an object:', service);
      return false;
    }
    if (typeof service.name !== 'string' || !service.name.trim()) {
      console.error('❌ Service name is invalid:', service.name);
      return false;
    }
    // 가격이 유효한 숫자 문자열인지 확인
    if (typeof service.price !== 'string' || !/^\d+$/.test(service.price)) {
      console.error('❌ Service price is invalid (should be numeric string):', service.price);
      return false;
    }
    if (service.specialPrice !== undefined && 
        (typeof service.specialPrice !== 'string' || !/^\d+$/.test(service.specialPrice))) {
      console.error('❌ Service specialPrice is invalid (should be numeric string):', service.specialPrice);
      return false;
    }
    if (service.description !== undefined && typeof service.description !== 'string') {
      console.error('❌ Service description is invalid:', service.description);
      return false;
    }
  }
  
  console.log('✅ ServicePost validation passed');
  return true;
}

/**
 * JSON 문자열을 ServicePost 객체로 파싱
 * @param content JSON 문자열
 * @returns 파싱된 ServicePost 객체
 * @throws Error 잘못된 JSON 형식이거나 유효하지 않은 ServicePost 데이터인 경우
 */
export function parseServicePost(content: string): ServicePost {
  try {
    console.log('📝 Parsing content:', content);
    const parsed = JSON.parse(content);
    console.log('🔍 Parsed JSON:', parsed);
    
    // 가격을 문자열로 정규화하여 정밀도 보장
    if (parsed.services && Array.isArray(parsed.services)) {
      parsed.services = parsed.services.map((service: any) => ({
        ...service,
        price: String(service.price || '0'), // 문자열로 보장하여 정밀도 보장
        specialPrice: service.specialPrice ? String(service.specialPrice) : undefined
      }));
    }
    
    if (!validateServicePost(parsed)) {
      console.error('❌ ServicePost validation failed for:', parsed);
      throw new Error('Invalid ServicePost data structure');
    }
    
    console.log('✅ ServicePost validation successful');
    return parsed;
  } catch (error) {
    console.error('🚨 parseServicePost error:', error);
    if (error instanceof SyntaxError) {
      console.error('📝 Content that failed to parse:', content);
      throw new Error('Invalid ServicePost JSON format');
    }
    throw error;
  }
}

/**
 * ServicePost 객체를 JSON 문자열로 직렬화
 * @param servicePost ServicePost 객체
 * @returns JSON 문자열
 */
export function serializeServicePost(servicePost: ServicePost): string {
  // 입력 검증
  if (!validateServicePost(servicePost)) {
    throw new Error('Invalid ServicePost data structure');
  }
  
  // 가격을 문자열로 유지하여 정밀도 보장
  const safeServicePost = {
    ...servicePost,
    services: servicePost.services.map(service => ({
      ...service,
      price: String(service.price), // 문자열로 보장하여 정밀도 보장
      specialPrice: service.specialPrice ? String(service.specialPrice) : undefined
    }))
  };
  
  return JSON.stringify(safeServicePost, null, 2);
}

/**
 * @deprecated - MockService는 더 이상 사용되지 않음. 실제 Service 타입을 사용하세요.
 * MockService를 ServicePost로 변환
 * @param mockService MockService 객체
 * @returns ServicePost 객체
 */
export function convertMockServiceToServicePost(mockService: any): ServicePost {
  return {
    company: {
      name: mockService.name,
      contact: mockService.contact.phone,
      availableHours: mockService.contact.hours,
      description: mockService.description
    },
    services: mockService.services.map((service: any) => ({
      name: service.name,
      price: service.price.replace(/[^\d]/g, '') || '0', // 숫자만 추출하여 문자열로 저장
      specialPrice: service.originalPrice ? 
        service.originalPrice.replace(/[^\d]/g, '') : undefined, // 숫자만 추출하여 문자열로 저장
      description: service.description
    }))
  };
}

/**
 * @deprecated - MockService는 더 이상 사용되지 않음. 실제 Service 타입을 사용하세요.
 * ServicePost를 MockService 호환 형식으로 변환
 * @param servicePost ServicePost 객체
 * @param id 서비스 ID
 * @param category 서비스 카테고리
 * @returns MockService 호환 객체
 */
export function convertServicePostToMockService(
  servicePost: ServicePost, 
  id: number, 
  category: ServiceCategory
): any {
  return {
    id,
    name: servicePost.company.name,
    category,
    rating: 0, // 기본값
    description: servicePost.company.description,
    services: servicePost.services.map(service => ({
      name: service.name,
      price: `${formatPrice(service.price)}원`, // formatPrice 함수 사용
      originalPrice: service.specialPrice ? `${formatPrice(service.specialPrice)}원` : undefined,
      description: service.description || ''
    })),
    stats: {
      views: 0,
      inquiries: 0,
      reviews: 0
    },
    verified: false,
    contact: {
      phone: servicePost.company.contact,
      hours: servicePost.company.availableHours,
      address: '', // 기본값
      email: '' // 기본값
    },
    reviews: []
  };
}

/**
 * 카테고리 문자열을 ServiceCategory 타입으로 매핑
 * @param category 카테고리 문자열
 * @returns ServiceCategory 또는 undefined
 */
export function mapCategoryToServiceCategory(category: string): ServiceCategory | undefined {
  const categoryMap: Record<string, ServiceCategory> = {
    'moving': '이사',
    'cleaning': '청소', 
    'aircon': '에어컨',
    '이사': '이사',
    '청소': '청소',
    '에어컨': '에어컨'
  };
  
  return categoryMap[category.toLowerCase()];
}

/**
 * ServiceCategory를 영문 카테고리로 변환
 * @param category ServiceCategory
 * @returns 영문 카테고리 문자열
 */
export function mapServiceCategoryToEnglish(category: ServiceCategory): string {
  const categoryMap: Record<ServiceCategory, string> = {
    '이사': 'moving',
    '청소': 'cleaning',
    '에어컨': 'aircon'
  };
  
  return categoryMap[category];
}

/**
 * 폼 데이터를 ServicePost로 변환
 * @param formData 폼 데이터
 * @param services 서비스 배열
 * @returns ServicePost 객체
 */
export function convertFormDataToServicePost(
  formData: {
    companyName: string;
    contact: string;
    availableHours: string;
    description: string;
  },
  services: Array<{
    serviceName: string;
    price: string;
    specialPrice?: string;
    hasSpecialPrice?: boolean;
  }>
): ServicePost {
  return {
    company: {
      name: formData.companyName.trim(),
      contact: formData.contact.trim(),
      availableHours: formData.availableHours.trim(),
      description: formData.description.trim()
    },
    services: services
      .filter(s => s.serviceName.trim() && s.price.trim())
      .map(service => ({
        name: service.serviceName.trim(),
        price: service.price.trim() || '0', // 문자열로 유지하여 정밀도 보장
        specialPrice: service.hasSpecialPrice && service.specialPrice ? 
          service.specialPrice.trim() : undefined, // 문자열로 유지하여 정밀도 보장
        description: undefined // 폼에서는 서비스별 설명이 없음
      }))
  };
}

/**
 * ServicePost의 총 서비스 개수 반환
 * @param servicePost ServicePost 객체
 * @returns 서비스 개수
 */
export function getServiceCount(servicePost: ServicePost): number {
  return servicePost.services.length;
}

/**
 * ServicePost의 최저 가격 반환
 * @param servicePost ServicePost 객체
 * @returns 최저 가격 (특가 포함)
 */
export function getMinPrice(servicePost: ServicePost): number {
  if (servicePost.services.length === 0) return 0;
  
  const prices = servicePost.services.flatMap(service => [
    parseInt(service.price) || 0,
    service.specialPrice ? parseInt(service.specialPrice) || 0 : parseInt(service.price) || 0
  ]);
  
  return Math.min(...prices);
}

/**
 * ServicePost의 최고 가격 반환
 * @param servicePost ServicePost 객체
 * @returns 최고 가격
 */
export function getMaxPrice(servicePost: ServicePost): number {
  if (servicePost.services.length === 0) return 0;
  
  const prices = servicePost.services.map(service => parseInt(service.price) || 0);
  return Math.max(...prices);
}

/**
 * ServicePost에서 특가가 있는 서비스 개수 반환
 * @param servicePost ServicePost 객체
 * @returns 특가가 있는 서비스 개수
 */
export function getSpecialPriceCount(servicePost: ServicePost): number {
  return servicePost.services.filter(service => service.specialPrice !== undefined).length;
}

/**
 * 가격 문자열을 표시용으로 포맷팅 (첫 단위 콤마 추가)
 * @param priceString 가격 문자열
 * @returns 포맷팅된 가격 문자열
 */
export function formatPrice(priceString: string): string {
  if (!priceString || priceString === '') return '0';
  // 숫자만 추출하여 첫 단위 콤마 추가
  const numericValue = parseInt(priceString) || 0;
  return numericValue.toLocaleString();
}

/**
 * 포맷팅된 가격에서 숫자만 추출
 * @param formattedPrice 포맷팅된 가격 문자열
 * @returns 순수 숫자 문자열
 */
export function parseFormattedPrice(formattedPrice: string): string {
  return formattedPrice.replace(/[^\d]/g, '');
}

/**
 * Post를 Service로 직접 변환 (단순화된 변환)
 * @param post Post 객체
 * @returns Service 객체 또는 null (파싱 실패 시)
 */
export function convertPostToService(post: any): Service | null {
  try {
    console.log('Converting post to service:', post);
    console.log('Post content:', post.content);
    console.log('Post metadata:', post.metadata);
    
    // 🚨 확장 통계 데이터 상세 디버깅
    console.log('📊 Extended stats conversion debug:', {
      extended_stats: post.extended_stats,
      stats: post.stats,
      view_count: post.view_count,
      comment_count: post.comment_count,
      bookmark_count: post.bookmark_count
    });
    
    // metadata.type이 "moving services" 또는 "moving_services"인지 확인
    if (post.metadata?.type !== 'moving services' && post.metadata?.type !== 'moving_services') {
      console.warn('Post metadata.type is not "moving services" or "moving_services":', post.metadata?.type);
      return null;
    }
    
    // Post의 content를 ServicePost로 파싱
    console.log('Attempting to parse service post content...');
    let serviceData: ServicePost;
    
    try {
      // JSON 형태인지 확인
      if (post.content.trim().startsWith('{')) {
        serviceData = parseServicePost(post.content);
        console.log('Parsed service data:', serviceData);
      } else {
        throw new Error('Content is not JSON format');
      }
    } catch (parseError) {
      console.error('Failed to parse service content, using fallback:', parseError);
      
      // Fallback: 마크다운 형태일 때 기본 구조로 서비스 데이터 생성
      serviceData = {
        company: {
          name: post.title || '서비스 업체',
          contact: '010-0000-0000',
          availableHours: '09:00-18:00',
          description: post.content || '서비스 설명 없음'
        },
        services: [{
          name: '기본 서비스',
          price: '50000', // 문자열로 처리
          description: '자세한 서비스 정보는 업체에 문의해주세요'
        }]
      };
    }
    
    const category = (post.metadata?.category as ServiceCategory) || '이사';
    
    // ID 처리 - MongoDB _id나 id 필드 사용
    const serviceId = post._id || post.id || `service-${Date.now()}-${Math.random()}`;
    
    console.log('🔍 Post author info for service conversion:', {
      post_author: post.author,
      post_author_id: post.author_id,
      post_user_id: post.user_id,
      post_created_by: post.created_by
    });

    return {
      // ServicePost 필드들
      company: serviceData.company,
      services: serviceData.services,
      
      // 추가 UI 필드들
      id: String(serviceId), // 문자열로 확실히 변환
      title: serviceData.company.name, // BaseListItem 호환성을 위한 title 필드
      name: serviceData.company.name,
      slug: post.slug, // 게시판과 동일한 슬러그 사용
      category,
      rating: 0, // 기본값 (추후 실제 평점 시스템 구현 시 수정)
      description: serviceData.company.description,
      
      // 🔑 작성자 정보 추가 (여러 가능한 필드로)
      author: post.author,
      author_id: post.author_id,
      user_id: post.user_id,
      created_by: post.created_by,
      
      stats: {
        view_count: post.view_count || 0,
        like_count: post.like_count || 0,
        dislike_count: post.dislike_count || 0,
        comment_count: post.comment_count || 0,
        bookmark_count: post.bookmark_count || 0,
        // 확장 통계 추가
        inquiry_count: post.extended_stats?.inquiry_count || post.stats?.inquiry_count || 0,
        review_count: post.extended_stats?.review_count || post.stats?.review_count || 0
      },
      serviceStats: {
        views: post.view_count || 0,
        inquiries: post.extended_stats?.inquiry_count || post.stats?.inquiry_count || 0, // 확장 통계 사용 (백업 경로 추가)
        reviews: post.extended_stats?.review_count || post.stats?.review_count || 0,    // 확장 통계 사용 (백업 경로 추가)
        bookmarks: post.bookmark_count || 0  // 북마크 수 추가
      },
      // 실제 반응 데이터 매핑
      likes: post.like_count || 0,
      dislikes: post.dislike_count || 0,
      bookmarks: post.bookmark_count || 0,
      verified: false, // 기본값 (추후 인증 시스템 구현 시 수정)
      contact: {
        phone: serviceData.company.contact,
        hours: serviceData.company.availableHours,
        address: '', // 기본값
        email: '' // 기본값
      },
      reviews: [], // 기본값 (추후 후기 시스템 구현 시 수정)
      postId: serviceId,
      created_at: post.created_at,
      updated_at: post.updated_at
    };
  } catch (error) {
    console.warn('Failed to convert post to service:', post._id || post.id, error);
    return null;
  }
}