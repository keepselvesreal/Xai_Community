/**
 * ServicePost 관련 타입 정의 (TDD REFACTOR 단계)
 * 
 * 구조화된 서비스-가격 데이터를 위한 타입 정의 및 유틸리티 함수
 */

import type { MockService, ServiceItem } from './index';

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
  /** 기본 가격 (원) */
  price: number;
  /** 특가 (원, 선택사항) */
  specialPrice?: number;
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

// 입력 검증 함수
function validateServicePost(data: any): data is ServicePost {
  if (!data || typeof data !== 'object') return false;
  
  // company 검증
  if (!data.company || typeof data.company !== 'object') return false;
  if (typeof data.company.name !== 'string' || !data.company.name.trim()) return false;
  if (typeof data.company.contact !== 'string' || !data.company.contact.trim()) return false;
  if (typeof data.company.availableHours !== 'string' || !data.company.availableHours.trim()) return false;
  if (typeof data.company.description !== 'string') return false;
  
  // services 배열 검증
  if (!Array.isArray(data.services) || data.services.length === 0) return false;
  
  for (const service of data.services) {
    if (!service || typeof service !== 'object') return false;
    if (typeof service.name !== 'string' || !service.name.trim()) return false;
    if (typeof service.price !== 'number' || service.price < 0) return false;
    if (service.specialPrice !== undefined && 
        (typeof service.specialPrice !== 'number' || service.specialPrice < 0)) return false;
    if (service.description !== undefined && typeof service.description !== 'string') return false;
  }
  
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
    const parsed = JSON.parse(content);
    
    if (!validateServicePost(parsed)) {
      throw new Error('Invalid ServicePost data structure');
    }
    
    return parsed;
  } catch (error) {
    if (error instanceof SyntaxError) {
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
  
  return JSON.stringify(servicePost, null, 2);
}

/**
 * MockService를 ServicePost로 변환
 * @param mockService MockService 객체
 * @returns ServicePost 객체
 */
export function convertMockServiceToServicePost(mockService: MockService): ServicePost {
  return {
    company: {
      name: mockService.name,
      contact: mockService.contact.phone,
      availableHours: mockService.contact.hours,
      description: mockService.description
    },
    services: mockService.services.map(service => ({
      name: service.name,
      price: parseInt(service.price.replace(/[^\d]/g, '')) || 0,
      specialPrice: service.originalPrice ? 
        parseInt(service.originalPrice.replace(/[^\d]/g, '')) : undefined,
      description: service.description
    }))
  };
}

/**
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
): MockService {
  return {
    id,
    name: servicePost.company.name,
    category,
    rating: 0, // 기본값
    description: servicePost.company.description,
    services: servicePost.services.map(service => ({
      name: service.name,
      price: `${service.price.toLocaleString()}원`,
      originalPrice: service.specialPrice ? `${service.specialPrice.toLocaleString()}원` : undefined,
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
        price: parseInt(service.price) || 0,
        specialPrice: service.hasSpecialPrice && service.specialPrice ? 
          parseInt(service.specialPrice) : undefined,
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
    service.price,
    service.specialPrice || service.price
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
  
  const prices = servicePost.services.map(service => service.price);
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